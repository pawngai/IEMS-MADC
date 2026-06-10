param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [string]$BackendHost = "127.0.0.1",
    [string]$JwtSecret = "",
    [string]$MongoUrl = "mongodb://localhost:27017",
    [string]$DbName = "iems_db",
    [switch]$ForceStop,
    [switch]$EnableReload,
    [switch]$SkipMongoBootstrap
)

$ErrorActionPreference = "Stop"

function New-RandomJwtSecret {
    return ([Guid]::NewGuid().ToString("N") + [Guid]::NewGuid().ToString("N"))
}

function Resolve-JwtSecret {
    param(
        [string]$ExplicitValue
    )

    if (-not [string]::IsNullOrWhiteSpace($ExplicitValue)) {
        return [pscustomobject]@{
            Value = $ExplicitValue
            Source = "parameter"
        }
    }

    foreach ($envKey in @("JWT_SECRET", "JWT_SECRET_KEY")) {
        $candidate = [Environment]::GetEnvironmentVariable($envKey)
        if (-not [string]::IsNullOrWhiteSpace($candidate)) {
            return [pscustomobject]@{
                Value = $candidate
                Source = "environment:$envKey"
            }
        }
    }

    return [pscustomobject]@{
        Value = New-RandomJwtSecret
        Source = "generated"
    }
}

function Resolve-CanonicalRolePassword {
    param(
        [string]$EnvKey,
        [string]$DefaultValue
    )

    $candidate = [Environment]::GetEnvironmentVariable($EnvKey)
    if (-not [string]::IsNullOrWhiteSpace($candidate)) {
        return [pscustomobject]@{
            Value = $candidate
            Source = "environment:$EnvKey"
        }
    }

    return [pscustomobject]@{
        Value = $DefaultValue
        Source = "default"
    }
}

function Get-ListeningProcessInfo {
    param(
        [int]$Port
    )

    $listeners = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $listeners) {
        return $null
    }

    $procId = ($listeners | Select-Object -First 1 -ExpandProperty OwningProcess)
    if (-not $procId) {
        return [pscustomobject]@{
            Port = $Port
            Pid = "unknown"
            ProcessName = "unknown"
        }
    }

    $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
    $procName = if ($proc) { $proc.ProcessName } else { "unknown" }

    return [pscustomobject]@{
        Port = $Port
        Pid = $procId
        ProcessName = $procName
    }
}

function Get-ProcessCommandLine {
    param(
        [int]$ProcessId
    )

    if (-not $ProcessId -or $ProcessId -le 0) {
        return ""
    }

    try {
        $procInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $ProcessId" -ErrorAction SilentlyContinue
        if ($procInfo -and $procInfo.CommandLine) {
            return [string]$procInfo.CommandLine
        }
    } catch {
    }

    return ""
}

function Try-ReclaimBackendGhostListener {
    param(
        [int]$Port,
        [string]$ProjectRoot,
        [int]$MaxAttempts = 6,
        [int]$DelayMs = 350
    )

    $listener = Get-ListeningProcessInfo -Port $Port
    if (-not $listener) {
        return $true
    }

    $owningPid = [int]$listener.Pid
    if (-not $owningPid -or $owningPid -le 0) {
        return $false
    }

    $proc = Get-Process -Id $owningPid -ErrorAction SilentlyContinue
    $procName = if ($proc) { $proc.ProcessName } else { "" }
    $commandLine = Get-ProcessCommandLine -ProcessId $owningPid

    $isLikelyBackendGhost = $false
    if ($procName -match '^(python|python3|powershell|pwsh|cmd)$') {
        if ($commandLine -match '(?i)uvicorn|app\.main:app|backend|MyIEMS') {
            $isLikelyBackendGhost = $true
        }
    }

    if (-not $isLikelyBackendGhost) {
        return $false
    }

    Write-Warning (
        "Detected stale backend listener on port {0} by PID {1} ({2}). Reclaiming port..." -f
        $Port,
        $owningPid,
        $listener.ProcessName
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            Stop-Process -Id $owningPid -Force -ErrorAction Stop
        } catch {
            try {
                $null = & cmd /c "taskkill /PID $owningPid /T /F" 2>$null
            } catch {
            }
        }

        Start-Sleep -Milliseconds $DelayMs
        $stillListening = Get-ListeningProcessInfo -Port $Port
        if (-not $stillListening) {
            Write-Host "Reclaimed backend port $Port."
            return $true
        }

        $owningPid = [int]$stillListening.Pid
        if (-not $owningPid -or $owningPid -le 0) {
            break
        }
    }

    return -not (Get-ListeningProcessInfo -Port $Port)
}

function Wait-ForPortRelease {
    param(
        [int]$Port,
        [int]$MaxAttempts = 12,
        [int]$DelayMs = 500
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        $listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
        if (-not $listener) {
            return $true
        }

        $owningPid = $listener.OwningProcess
        if ($owningPid -and $owningPid -gt 0) {
            try {
                Stop-Process -Id $owningPid -Force -ErrorAction Stop
            } catch {
                try {
                    $null = & cmd /c "taskkill /PID $owningPid /T /F" 2>$null
                } catch {
                }
            }
        }

        Start-Sleep -Milliseconds $DelayMs
    }

    return $false
}

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendAppDir = Join-Path $projectRoot "backend"
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
$stopScript = Join-Path $projectRoot "stop-dev.ps1"
$mongoBootstrapScript = Join-Path $projectRoot "start-mongo-local.ps1"

if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found at $pythonExe. Create the venv first."
}

$frontendPackage = Join-Path $projectRoot "frontend\package.json"
if (-not (Test-Path $frontendPackage)) {
    Write-Error "Frontend package.json not found at $frontendPackage."
}

$npmCheck = Get-Command npm -ErrorAction SilentlyContinue
if (-not $npmCheck) {
    Write-Error "npm is not available in PATH. Install Node.js first."
}

$jwtSecretState = Resolve-JwtSecret -ExplicitValue $JwtSecret
$JwtSecret = $jwtSecretState.Value
if ($jwtSecretState.Source -eq "generated") {
    Write-Warning "JWT secret was not provided via -JwtSecret or environment. Generated an ephemeral dev secret for this run only."
} else {
    Write-Host "Using JWT secret from $($jwtSecretState.Source)."
}

$workflowAccounts = @(
    @{ Email = "global.dataentry@madc.gov.in"; PasswordState = (Resolve-CanonicalRolePassword -EnvKey "IEMS_E2E_DE_PASSWORD" -DefaultValue "dataentry123"); Name = "Global Data Entry"; PasswordEnv = "IEMS_E2E_DE_PASSWORD"; EmailEnv = "IEMS_E2E_DE_EMAIL" },
    @{ Email = "verifier@madc.gov.in"; PasswordState = (Resolve-CanonicalRolePassword -EnvKey "IEMS_E2E_VERIFIER_PASSWORD" -DefaultValue "verifier123"); Name = "Verifier Officer"; PasswordEnv = "IEMS_E2E_VERIFIER_PASSWORD"; EmailEnv = "IEMS_E2E_VERIFIER_EMAIL" },
    @{ Email = "hoo@madc.gov.in"; PasswordState = (Resolve-CanonicalRolePassword -EnvKey "IEMS_E2E_HOO_PASSWORD" -DefaultValue "hoo123"); Name = "Approving Authority"; PasswordEnv = "IEMS_E2E_HOO_PASSWORD"; EmailEnv = "IEMS_E2E_HOO_EMAIL" },
    @{ Email = "dealing.clerk@madc.gov.in"; PasswordState = (Resolve-CanonicalRolePassword -EnvKey "IEMS_E2E_DEALING_PASSWORD" -DefaultValue "dealing123"); Name = "Dealing Clerk"; PasswordEnv = "IEMS_E2E_DEALING_PASSWORD"; EmailEnv = "IEMS_E2E_DEALING_EMAIL" },
    @{ Email = "auditor@madc.gov.in"; PasswordState = (Resolve-CanonicalRolePassword -EnvKey "IEMS_E2E_AUDITOR_PASSWORD" -DefaultValue "auditor123"); Name = "Auditor"; PasswordEnv = "IEMS_E2E_AUDITOR_PASSWORD"; EmailEnv = "IEMS_E2E_AUDITOR_EMAIL" }
)

$backendPortConflict = Get-ListeningProcessInfo -Port $BackendPort
$frontendPortConflict = Get-ListeningProcessInfo -Port $FrontendPort
$resolvedBackendPort = $BackendPort

if ($backendPortConflict) {
    $reclaimed = Try-ReclaimBackendGhostListener -Port $BackendPort -ProjectRoot $projectRoot
    if ($reclaimed) {
        $backendPortConflict = Get-ListeningProcessInfo -Port $BackendPort
    }
}

if ($backendPortConflict -or $frontendPortConflict) {
    if ($ForceStop) {
        if (-not (Test-Path $stopScript)) {
            Write-Error "-ForceStop requested but stop script not found at $stopScript"
        }
        Write-Host "Ports in use detected. Running stop-dev.ps1 for ports $BackendPort and $FrontendPort..."
        & $stopScript -BackendPort $BackendPort -FrontendPort $FrontendPort -RetryCount 8 -RetryDelayMs 500
        Start-Sleep -Milliseconds 500

        $backendReleased = Wait-ForPortRelease -Port $BackendPort -MaxAttempts 10 -DelayMs 400
        $frontendReleased = Wait-ForPortRelease -Port $FrontendPort -MaxAttempts 10 -DelayMs 400
        if (-not $backendReleased) {
            Write-Warning "Backend port $BackendPort is still in use after forced stop attempts."
        }
        if (-not $frontendReleased) {
            Write-Warning "Frontend port $FrontendPort is still in use after forced stop attempts."
        }

        $backendPortConflict = Get-ListeningProcessInfo -Port $BackendPort
        $frontendPortConflict = Get-ListeningProcessInfo -Port $FrontendPort
    }

    if ($backendPortConflict) {
        Write-Error (
            "Backend port {0} is already in use by PID {1} ({2}). " +
            "Run ./stop-dev.ps1 (or retry with -ForceStop) and retry." -f
            $backendPortConflict.Port,
            $backendPortConflict.Pid,
            $backendPortConflict.ProcessName
        )
    }

    if ($frontendPortConflict) {
        Write-Error (
            "Frontend port {0} is already in use by PID {1} ({2}). " +
            "Run ./stop-dev.ps1 (or free the port) and retry." -f
            $frontendPortConflict.Port,
            $frontendPortConflict.Pid,
            $frontendPortConflict.ProcessName
        )
    }
}

$mongoListening = $false
try {
    $mongoListening = [bool](Get-NetTCPConnection -LocalPort 27017 -State Listen -ErrorAction SilentlyContinue)
} catch {
    $mongoListening = $false
}

if (-not $mongoListening) {
    if (-not $SkipMongoBootstrap -and (Test-Path $mongoBootstrapScript)) {
        Write-Host "MongoDB not detected on localhost:27017. Attempting local Mongo bootstrap..."
        try {
            & $mongoBootstrapScript -Port 27017
            Start-Sleep -Milliseconds 500
            $mongoListening = [bool](Get-NetTCPConnection -LocalPort 27017 -State Listen -ErrorAction SilentlyContinue)
        } catch {
            Write-Warning "Mongo bootstrap attempt failed: $($_.Exception.Message)"
            $mongoListening = $false
        }
    }

    if (-not $mongoListening) {
        Write-Warning "MongoDB does not appear to be listening on localhost:27017. Login will fail until MongoDB is available."
    }
}

$reloadArg = if ($EnableReload) { " --reload" } else { "" }
$workflowEnvAssignments = @()
foreach ($account in $workflowAccounts) {
    $workflowEnvAssignments += "`$env:$($account.PasswordEnv)='$($account.PasswordState.Value)'"
    $workflowEnvAssignments += "`$env:$($account.EmailEnv)='$($account.Email)'"
}
$workflowEnvSegment = $workflowEnvAssignments -join "; "
$backendCommand = "Set-Location '$projectRoot'; `$env:JWT_SECRET='$JwtSecret'; `$env:MONGO_URL='$MongoUrl'; `$env:DB_NAME='$DbName'; $workflowEnvSegment; & '$pythonExe' -m uvicorn app.main:app --app-dir '$backendAppDir' --host $BackendHost --port $resolvedBackendPort$reloadArg"
$frontendCommand = "Set-Location '$projectRoot\\frontend'; `$env:REACT_APP_BACKEND_URL='http://$BackendHost`:$resolvedBackendPort'; npm run dev -- --host 0.0.0.0 --port $FrontendPort"

Start-Process powershell -WorkingDirectory $projectRoot -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $backendCommand) | Out-Null
Start-Process powershell -WorkingDirectory (Join-Path $projectRoot "frontend") -ArgumentList @("-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $frontendCommand) | Out-Null

Write-Host "Backend starting at http://$BackendHost`:$resolvedBackendPort"
Write-Host "Frontend starting at http://localhost:$FrontendPort"
Write-Host "Backend env: MONGO_URL=$MongoUrl; DB_NAME=$DbName"
foreach ($account in $workflowAccounts) {
    Write-Host "$($account.Name) login: $($account.Email) / $($account.PasswordState.Value)"
}
if ($jwtSecretState.Source -eq "generated") {
    Write-Host "Backend auth: using generated per-run JWT secret"
}
Write-Host "Two new PowerShell windows were opened for both servers."
