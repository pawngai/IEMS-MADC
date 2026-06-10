param(
    [string]$HodEmail = "e2e.browser.1992@madc.gov.in",
    [string]$HodPassword = "",
    [switch]$KeepBackend,
    [switch]$ForceStop
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pythonExe = Join-Path $projectRoot ".venv\Scripts\python.exe"
Push-Location $projectRoot

$previousEmail = [Environment]::GetEnvironmentVariable("IEMS_E2E_HOD_EMAIL")
$previousPassword = [Environment]::GetEnvironmentVariable("IEMS_E2E_HOD_PASSWORD")

try {
    $resolvedPassword = $HodPassword
    if ([string]::IsNullOrWhiteSpace($resolvedPassword)) {
        $resolvedPassword = $previousPassword
    }
    if ([string]::IsNullOrWhiteSpace($resolvedPassword)) {
        $resolvedPassword = "employee123"
    }

    $env:IEMS_E2E_HOD_EMAIL = $HodEmail
    $env:IEMS_E2E_HOD_PASSWORD = $resolvedPassword

    if ($KeepBackend) {
        if (-not (Test-Path $pythonExe)) {
            throw "Python executable not found at $pythonExe"
        }

        & $pythonExe (Join-Path $projectRoot "test_e2e_leave_hod_cl_approval.py")
        exit $LASTEXITCODE
    }

    $runnerArgs = @{
        SkipCredentialPrecheck = $true
        E2EScript = "test_e2e_leave_hod_cl_approval.py"
    }

    if ($ForceStop) {
        $runnerArgs.ForceStop = $true
    }
    & (Join-Path $projectRoot "run-e2e-live.ps1") @runnerArgs
    exit $LASTEXITCODE
} finally {
    if ($null -eq $previousEmail) {
        Remove-Item Env:IEMS_E2E_HOD_EMAIL -ErrorAction SilentlyContinue
    } else {
        $env:IEMS_E2E_HOD_EMAIL = $previousEmail
    }

    if ($null -eq $previousPassword) {
        Remove-Item Env:IEMS_E2E_HOD_PASSWORD -ErrorAction SilentlyContinue
    } else {
        $env:IEMS_E2E_HOD_PASSWORD = $previousPassword
    }

    Pop-Location
}