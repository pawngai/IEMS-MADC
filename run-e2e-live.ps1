param(
    [string]$BackendHost = "127.0.0.1",
    [int]$BackendPort = 8000,
    [string]$MongoUrl = "mongodb://localhost:27017",
    [string]$DbName = "iems_db",
    [string]$E2EScript = "test_e2e_workflow.py",
    [int]$WaitSeconds = 45,
    [switch]$ForceStop,
    [switch]$AutoFallbackTo8001,
    [switch]$VerbosePortDiagnostics,
    [switch]$SkipCredentialPrecheck,
    [switch]$AutoProvisionE2EUsers,
    [switch]$BootstrapAdminFromDb,
    [string]$SeedAdminEmail = "admin@madc.gov.in",
    [string]$SeedAdminPassword = "",
    [switch]$KeepBackend
)

$ErrorActionPreference = "Stop"

function Get-ListenerPids {
    param([int]$Port)
    return @(Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique)
}

function Get-ListenerProcessDetails {
    param([int]$Port)

    $pids = Get-ListenerPids -Port $Port
    $details = @()
    foreach ($procId in $pids) {
        $name = "<unknown>"
        $commandLine = "<unavailable>"

        try {
            $proc = Get-CimInstance Win32_Process -Filter "ProcessId = $procId" -ErrorAction Stop
            if ($proc.Name) {
                $name = $proc.Name
            }
            if ($proc.CommandLine) {
                $commandLine = $proc.CommandLine
            }
        } catch {
        }

        if ($name -eq "<unknown>") {
            try {
                $procBasic = Get-Process -Id $procId -ErrorAction Stop
                if ($procBasic.ProcessName) {
                    $name = $procBasic.ProcessName
                }
            } catch {
            }
        }

        $details += [PSCustomObject]@{
            ProcessId = $procId
            Name = $name
            CommandLine = $commandLine
        }
    }

    return $details
}

function Write-PortOwnerDiagnostics {
    param(
        [int]$Port,
        [switch]$IncludeCommandLine
    )

    $details = Get-ListenerProcessDetails -Port $Port
    if ($details.Count -eq 0) {
        return
    }

    Write-Host "Port $Port is currently owned by:"
    foreach ($entry in $details) {
        if ($IncludeCommandLine) {
            Write-Host " - PID=$($entry.ProcessId) Name=$($entry.Name) Cmd=$($entry.CommandLine)"
        } else {
            Write-Host " - PID=$($entry.ProcessId) Name=$($entry.Name)"
        }
    }
}

function New-RandomPassword {
    return "Iems!" + [Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N").Substring(0, 8)
}

function Resolve-SecretValue {
    param(
        [string]$ExplicitValue,
        [string[]]$EnvKeys,
        [string]$Label,
        [switch]$GenerateIfMissing,
        [switch]$AllowEmpty
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitValue)) {
        return $ExplicitValue
    }

    foreach ($envKey in $EnvKeys) {
        $candidate = [Environment]::GetEnvironmentVariable($envKey)
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            return $candidate
        }
    }

    if ($GenerateIfMissing) {
        return New-RandomPassword
    }

    if ($AllowEmpty) {
        return ""
    }

    throw "$Label is required. Provide it as a parameter or set one of: $($EnvKeys -join ', ')."
}

function Test-ApiLogin {
    param(
        [string]$BaseUrl,
        [string]$Email,
        [string]$Password
    )

    try {
        $payload = @{ email = $Email; password = $Password } | ConvertTo-Json
        $resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/login" -Body $payload -ContentType "application/json" -TimeoutSec 8
        return [bool]($resp.access_token)
    } catch {
        return $false
    }
}

function Get-ApiAccessToken {
    param(
        [string]$BaseUrl,
        [string]$Email,
        [string]$Password
    )

    try {
        $payload = @{ email = $Email; password = $Password } | ConvertTo-Json
        $resp = Invoke-RestMethod -Method Post -Uri "$BaseUrl/auth/login" -Body $payload -ContentType "application/json" -TimeoutSec 8
        return $resp.access_token
    } catch {
        return $null
    }
}

function Ensure-E2EUsers {
    param(
        [string]$BaseUrl,
        [string]$AccessToken,
        [array]$Users
    )

    $headers = @{ Authorization = "Bearer $AccessToken" }

    $existingUsers = Invoke-RestMethod -Method Get -Uri "$BaseUrl/users/?skip=0&limit=500" -Headers $headers -TimeoutSec 12
    $byEmail = @{}
    foreach ($u in @($existingUsers)) {
        if ($u.email) {
            $byEmail[$u.email.ToLower()] = $u
        }
    }

    foreach ($user in $Users) {
        $emailKey = $user.Email.ToLower()
        $existing = $byEmail[$emailKey]
        if ($null -eq $existing) {
            $createBody = @{
                email = $user.Email
                password = $user.Password
                name = $user.Name
                authorities = @($user.Authority)
                employee_id = $user.EmployeeId
                department_code = $user.DepartmentCode
                office_code = $user.OfficeCode
            } | ConvertTo-Json

            try {
                $created = Invoke-RestMethod -Method Post -Uri "$BaseUrl/users/" -Headers $headers -Body $createBody -ContentType "application/json" -TimeoutSec 12
                $existing = $created
                $byEmail[$emailKey] = $created
                Write-Host "Provisioned user: $($user.Email)"
            } catch {
                throw "Failed provisioning user $($user.Email): $($_.Exception.Message)"
            }
        } else {
            Write-Host "User exists; normalizing account: $($user.Email)"
        }

        $updateBody = @{
            name = $user.Name
            authorities = @($user.Authority)
            employee_id = $user.EmployeeId
            department_code = $user.DepartmentCode
            office_code = $user.OfficeCode
            is_active = $true
        } | ConvertTo-Json

        try {
            Invoke-RestMethod -Method Put -Uri "$BaseUrl/users/$($existing.id)" -Headers $headers -Body $updateBody -ContentType "application/json" -TimeoutSec 12 | Out-Null
        } catch {
            $response = $_.Exception.Response
            if ($response -and [int]$response.StatusCode -eq 400) {
                Write-Host "Skipped profile normalization for $($user.Email) due to role constraints (400)."
            } else {
                throw "Failed updating user profile for $($user.Email): $($_.Exception.Message)"
            }
        }

        $passwordBody = @{ new_password = $user.Password } | ConvertTo-Json
        try {
            Invoke-RestMethod -Method Put -Uri "$BaseUrl/users/$($existing.id)/password" -Headers $headers -Body $passwordBody -ContentType "application/json" -TimeoutSec 12 | Out-Null
        } catch {
            throw "Failed setting password for $($user.Email): $($_.Exception.Message)"
        }
    }
}

function Ensure-SeedAdminViaDb {
    param(
        [string]$PythonExe,
        [string]$ProjectRoot,
        [string]$MongoUrl,
        [string]$DbName,
        [string]$AdminEmail,
        [string]$AdminPassword
    )

    $tempScript = Join-Path $ProjectRoot ".tmp_seed_admin_user.py"
    $py = @'
import os
import uuid
from datetime import datetime, timezone

import bcrypt
from pymongo import MongoClient

mongo_url = os.environ["IEMS_BOOTSTRAP_MONGO_URL"]
db_name = os.environ["IEMS_BOOTSTRAP_DB_NAME"]
admin_email = os.environ["IEMS_BOOTSTRAP_ADMIN_EMAIL"].strip().lower()
admin_password = os.environ["IEMS_BOOTSTRAP_ADMIN_PASSWORD"]

now = datetime.now(timezone.utc).isoformat()
password_hash = bcrypt.hashpw(admin_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

client = MongoClient(mongo_url)
db = client[db_name]

for email in [admin_email]:
    db.users.update_one(
        {"email": email},
        {
            "$set": {
                "email": email,
                "name": "System Administrator",
                "authorities": ["SYSTEM_ADMIN"],
                "employee_id": "ADMIN-001",
                "department_code": "",
                "office_code": "",
                "is_active": True,
                "updated_at": now,
                "password_hash": password_hash,
            },
            "$setOnInsert": {
                "id": str(uuid.uuid4()),
                "created_at": now,
                "created_by": "run-e2e-live.ps1",
            },
        },
        upsert=True,
    )

print("BOOTSTRAP_ADMIN_OK")
'@

    Set-Content -Path $tempScript -Value $py -Encoding UTF8
    try {
        $env:IEMS_BOOTSTRAP_MONGO_URL = $MongoUrl
        $env:IEMS_BOOTSTRAP_DB_NAME = $DbName
        $env:IEMS_BOOTSTRAP_ADMIN_EMAIL = $AdminEmail
        $env:IEMS_BOOTSTRAP_ADMIN_PASSWORD = $AdminPassword

        & $PythonExe $tempScript
        if ($LASTEXITCODE -ne 0) {
            throw "Python bootstrap script failed with exit code $LASTEXITCODE"
        }
    } finally {
        Remove-Item -Path $tempScript -Force -ErrorAction SilentlyContinue
        Remove-Item Env:IEMS_BOOTSTRAP_MONGO_URL -ErrorAction SilentlyContinue
        Remove-Item Env:IEMS_BOOTSTRAP_DB_NAME -ErrorAction SilentlyContinue
        Remove-Item Env:IEMS_BOOTSTRAP_ADMIN_EMAIL -ErrorAction SilentlyContinue
        Remove-Item Env:IEMS_BOOTSTRAP_ADMIN_PASSWORD -ErrorAction SilentlyContinue
    }
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$backendAppDir = Join-Path $projectRoot "backend"
$e2eScript = if ([System.IO.Path]::IsPathRooted($E2EScript)) {
    $E2EScript
} else {
    Join-Path $projectRoot $E2EScript
}
$isCurrentDefaultWorkflow = [System.IO.Path]::GetFileName($e2eScript) -eq "test_e2e_workflow.py"

if ($isCurrentDefaultWorkflow -and -not $AutoProvisionE2EUsers -and -not $BootstrapAdminFromDb) {
    $SkipCredentialPrecheck = $true
}

if (-not (Test-Path $pythonExe)) {
    throw "Python executable not found at $pythonExe"
}
if (-not (Test-Path $e2eScript)) {
    throw "E2E script not found at $e2eScript"
}

$mongoHostPort = "localhost:27017"
$mongoListening = [bool](Get-NetTCPConnection -LocalPort 27017 -State Listen -ErrorAction SilentlyContinue)
if (-not $mongoListening) {
    throw "MongoDB is not listening on $mongoHostPort. Start MongoDB and retry."
}

$candidatePorts = @($BackendPort)
if ($AutoFallbackTo8001 -and $BackendPort -eq 8000) {
    $candidatePorts += 8001
}

$selectedPort = $null
foreach ($candidatePort in $candidatePorts) {
    $listenerPids = Get-ListenerPids -Port $candidatePort
    if ($listenerPids.Count -gt 0) {
        Write-PortOwnerDiagnostics -Port $candidatePort -IncludeCommandLine:$VerbosePortDiagnostics

        if (-not $ForceStop) {
            if ($candidatePort -eq $candidatePorts[-1]) {
                throw "Backend port $candidatePort is in use by PID(s): $($listenerPids -join ', '). Re-run with -ForceStop or stop the process manually."
            }
            continue
        }

        foreach ($procId in $listenerPids) {
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
        Start-Sleep -Milliseconds 500

        $remainingListeners = Get-ListenerPids -Port $candidatePort
        if ($remainingListeners.Count -gt 0) {
            Write-PortOwnerDiagnostics -Port $candidatePort -IncludeCommandLine:$VerbosePortDiagnostics
            if ($candidatePort -eq $candidatePorts[-1]) {
                throw "Unable to free backend port $candidatePort. Remaining PID(s): $($remainingListeners -join ', ')."
            }
            continue
        }
    }

    $selectedPort = $candidatePort
    break
}

if ($null -eq $selectedPort) {
    throw "Unable to prepare a backend port from candidates: $($candidatePorts -join ', ')."
}

if ($selectedPort -ne $BackendPort) {
    Write-Host "Falling back backend port from $BackendPort to $selectedPort"
}
$BackendPort = $selectedPort

$jwtSecret = Resolve-SecretValue -ExplicitValue "" -EnvKeys @("JWT_SECRET", "JWT_SECRET_KEY") -Label "JWT secret" -GenerateIfMissing
$generateRolePasswords = $AutoProvisionE2EUsers
$requireRolePasswords = $generateRolePasswords -or (-not $SkipCredentialPrecheck)
$requireAdminPassword = $generateRolePasswords -or $BootstrapAdminFromDb -or (-not $SkipCredentialPrecheck)
$SeedAdminPassword = Resolve-SecretValue `
    -ExplicitValue $SeedAdminPassword `
    -EnvKeys @("IEMS_E2E_ADMIN_PASSWORD") `
    -Label "Admin password" `
    -GenerateIfMissing:($generateRolePasswords -or $BootstrapAdminFromDb) `
    -AllowEmpty:(-not $requireAdminPassword)

$requiredAccounts = @(
    @{ Email = "global.dataentry@madc.gov.in"; Password = (Resolve-SecretValue -ExplicitValue "" -EnvKeys @("IEMS_E2E_DE_PASSWORD") -Label "E2E data entry password" -GenerateIfMissing:$generateRolePasswords -AllowEmpty:(-not $requireRolePasswords)); Name = "Global Data Entry"; Authority = "GLOBAL_DATA_ENTRY"; EmployeeId = "DE-001"; DepartmentCode = "ADMIN"; OfficeCode = "HQ"; EmailEnv = "IEMS_E2E_DE_EMAIL"; PasswordEnv = "IEMS_E2E_DE_PASSWORD" },
    @{ Email = "verifier@madc.gov.in"; Password = (Resolve-SecretValue -ExplicitValue "" -EnvKeys @("IEMS_E2E_VERIFIER_PASSWORD") -Label "E2E verifier password" -GenerateIfMissing:$generateRolePasswords -AllowEmpty:(-not $requireRolePasswords)); Name = "Verifier Officer"; Authority = "VERIFIER"; EmployeeId = "VER-001"; DepartmentCode = "ADMIN"; OfficeCode = "HQ"; EmailEnv = "IEMS_E2E_VERIFIER_EMAIL"; PasswordEnv = "IEMS_E2E_VERIFIER_PASSWORD" },
    @{ Email = "hoo@madc.gov.in"; Password = (Resolve-SecretValue -ExplicitValue "" -EnvKeys @("IEMS_E2E_HOO_PASSWORD") -Label "E2E approving-authority password" -GenerateIfMissing:$generateRolePasswords -AllowEmpty:(-not $requireRolePasswords)); Name = "Approving Authority"; Authority = "APPROVING_AUTHORITY"; EmployeeId = "HOO-001"; DepartmentCode = "ADMIN"; OfficeCode = "HQ"; EmailEnv = "IEMS_E2E_HOO_EMAIL"; PasswordEnv = "IEMS_E2E_HOO_PASSWORD" },
    @{ Email = "dealing.clerk@madc.gov.in"; Password = (Resolve-SecretValue -ExplicitValue "" -EnvKeys @("IEMS_E2E_DEALING_PASSWORD") -Label "E2E dealing-assistant password" -GenerateIfMissing:$generateRolePasswords -AllowEmpty:(-not $requireRolePasswords)); Name = "Dealing Clerk"; Authority = "DEALING_ASSISTANT"; EmployeeId = "DA-001"; DepartmentCode = "ADMIN"; OfficeCode = "HQ"; EmailEnv = "IEMS_E2E_DEALING_EMAIL"; PasswordEnv = "IEMS_E2E_DEALING_PASSWORD" },
    @{ Email = $SeedAdminEmail; Password = $SeedAdminPassword; Name = "System Administrator"; Authority = "SYSTEM_ADMIN"; EmployeeId = "ADMIN-001"; DepartmentCode = ""; OfficeCode = ""; EmailEnv = "IEMS_E2E_ADMIN_EMAIL"; PasswordEnv = "IEMS_E2E_ADMIN_PASSWORD" }
)

$env:JWT_SECRET = $jwtSecret
$env:JWT_SECRET_KEY = $jwtSecret
$env:MONGO_URL = $MongoUrl
$env:DB_NAME = $DbName
$env:IEMS_E2E_EXPOSE_TEMP_PASSWORD = "1"
$env:IEMS_E2E_BASE = "http://$BackendHost`:$BackendPort/api"
$env:IEMS_E2E_MONGO_URL = $MongoUrl
$env:IEMS_E2E_DB_NAME = $DbName
$env:IEMS_E2E_ADMIN_EMAIL = $SeedAdminEmail
$env:IEMS_E2E_ADMIN_PASSWORD = $SeedAdminPassword

foreach ($account in $requiredAccounts) {
    [Environment]::SetEnvironmentVariable($account.EmailEnv, $account.Email)
    [Environment]::SetEnvironmentVariable($account.PasswordEnv, $account.Password)
}

$backendOut = Join-Path $projectRoot ".e2e-backend.out.log"
$backendErr = Join-Path $projectRoot ".e2e-backend.err.log"
if (Test-Path $backendOut) { Remove-Item $backendOut -Force }
if (Test-Path $backendErr) { Remove-Item $backendErr -Force }

$backendProc = Start-Process -FilePath $pythonExe `
    -ArgumentList @("-m", "uvicorn", "app.main:app", "--app-dir", $backendAppDir, "--host", $BackendHost, "--port", "$BackendPort") `
    -WorkingDirectory $projectRoot `
    -RedirectStandardOutput $backendOut `
    -RedirectStandardError $backendErr `
    -PassThru

Write-Host "Started backend PID=$($backendProc.Id) at http://$BackendHost`:$BackendPort"

$ready = $false
$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    if ($backendProc.HasExited) {
        break
    }

    try {
        $resp = Invoke-WebRequest -Uri "http://$BackendHost`:$BackendPort/docs" -UseBasicParsing -TimeoutSec 2
        if ($resp.StatusCode -ge 200 -and $resp.StatusCode -lt 500) {
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 700
    }
}

if (-not $ready) {
    $msg = "Backend did not become ready within $WaitSeconds seconds."
    if (Test-Path $backendErr) {
        $errTail = Get-Content $backendErr -Tail 40 -ErrorAction SilentlyContinue
        if ($errTail) {
            $msg += "`n--- backend stderr tail ---`n" + ($errTail -join "`n")
        }
    }

    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    throw $msg
}

$ownerPids = Get-ListenerPids -Port $BackendPort
if ($ownerPids.Count -eq 0) {
    if ($backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
    throw "Backend readiness check failed: no listener found on port $BackendPort after startup."
}

if ($ownerPids -notcontains $backendProc.Id) {
    $ownerText = $ownerPids -join ', '
    Write-Host "Warning: Port $BackendPort is owned by PID(s) $ownerText (starter PID was $($backendProc.Id)). Continuing because port was clean before startup."
}

Write-Host "Backend ready. Running live E2E workflow script..."

$baseApi = "http://$BackendHost`:$BackendPort/api"

if ($AutoProvisionE2EUsers) {
    $seedToken = Get-ApiAccessToken -BaseUrl $baseApi -Email $SeedAdminEmail -Password $SeedAdminPassword
    if (-not $seedToken) {
        if ($BootstrapAdminFromDb) {
            Write-Host "Admin login failed; bootstrapping SYSTEM_ADMIN user directly in MongoDB..."
            Ensure-SeedAdminViaDb -PythonExe $pythonExe -ProjectRoot $projectRoot -MongoUrl $MongoUrl -DbName $DbName -AdminEmail $SeedAdminEmail -AdminPassword $SeedAdminPassword
            $seedToken = Get-ApiAccessToken -BaseUrl $baseApi -Email $SeedAdminEmail -Password $SeedAdminPassword
        }
    }

    if (-not $seedToken) {
        if ($backendProc -and -not $backendProc.HasExited -and -not $KeepBackend) {
            Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped backend PID=$($backendProc.Id)"
        }
        throw "Auto-provision requested but admin login failed for $SeedAdminEmail. Provide a valid admin password with -SeedAdminPassword or IEMS_E2E_ADMIN_PASSWORD, or use -BootstrapAdminFromDb."
    }

    Write-Host "Auto-provisioning missing E2E role users via /api/users/..."
    Ensure-E2EUsers -BaseUrl $baseApi -AccessToken $seedToken -Users $requiredAccounts
}

if (-not $SkipCredentialPrecheck) {
    $precheckAdminToken = Get-ApiAccessToken -BaseUrl $baseApi -Email $SeedAdminEmail -Password $SeedAdminPassword
    if (-not $precheckAdminToken) {
        if ($backendProc -and -not $backendProc.HasExited -and -not $KeepBackend) {
            Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped backend PID=$($backendProc.Id)"
        }

        throw (
            "Credential precheck failed. Admin login failed for $SeedAdminEmail." +
            "`nProvide a valid admin password with -SeedAdminPassword or IEMS_E2E_ADMIN_PASSWORD," +
            " or run with -AutoProvisionE2EUsers -BootstrapAdminFromDb."
        )
    }

    $preHeaders = @{ Authorization = "Bearer $precheckAdminToken" }
    $preUsers = Invoke-RestMethod -Method Get -Uri "$baseApi/users/?skip=0&limit=500" -Headers $preHeaders -TimeoutSec 12
    $availableEmails = @{}
    foreach ($u in @($preUsers)) {
        if ($u.email) {
            $availableEmails[$u.email.ToLower()] = $true
        }
    }

    $missing = @()
    foreach ($acct in $requiredAccounts) {
        if (-not $availableEmails.ContainsKey($acct.Email.ToLower())) {
            $missing += $acct.Email
        }
    }

    if ($missing.Count -gt 0) {
        if ($backendProc -and -not $backendProc.HasExited -and -not $KeepBackend) {
            Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped backend PID=$($backendProc.Id)"
        }

        throw (
            "Credential precheck failed. Missing seed accounts: " + ($missing -join ", ") +
            "`nSeed/provision the required users, then re-run." +
            "`nTip: If you intentionally want to skip this check, pass -SkipCredentialPrecheck."
        )
    }
}

$e2eExitCode = 1
try {
    & $pythonExe $e2eScript
    $e2eExitCode = $LASTEXITCODE
} finally {
    if (-not $KeepBackend) {
        if ($backendProc -and -not $backendProc.HasExited) {
            Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped backend PID=$($backendProc.Id)"
        }
    } else {
        Write-Host "Keeping backend running (PID=$($backendProc.Id)) due to -KeepBackend"
    }
}

if ($e2eExitCode -ne 0) {
    Write-Host "E2E script failed with exit code $e2eExitCode"
    Write-Host "Backend logs: $backendOut, $backendErr"
    exit $e2eExitCode
}

Write-Host "E2E script completed successfully."
exit 0
