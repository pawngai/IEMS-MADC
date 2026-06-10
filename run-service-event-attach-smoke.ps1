param(
    [string]$EmployeeRef = "MADC-1992-R0001",
    [string]$ServiceEventId = "",
    [string]$DataEntryPassword = "",
    [switch]$KeepBackend,
    [switch]$ForceStop
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $projectRoot

$previousPassword = [Environment]::GetEnvironmentVariable("IEMS_E2E_DE_PASSWORD")
$previousEmployeeRef = [Environment]::GetEnvironmentVariable("IEMS_E2E_SERVICE_EVENT_EMPLOYEE_REF")
$previousServiceEventId = [Environment]::GetEnvironmentVariable("IEMS_E2E_SERVICE_EVENT_ID")

try {
    $resolvedPassword = $DataEntryPassword
    if ([string]::IsNullOrWhiteSpace($resolvedPassword)) {
        $resolvedPassword = $previousPassword
    }
    if ([string]::IsNullOrWhiteSpace($resolvedPassword)) {
        $resolvedPassword = "dataentry123"
    }

    $env:IEMS_E2E_DE_PASSWORD = $resolvedPassword
    $env:IEMS_E2E_SERVICE_EVENT_EMPLOYEE_REF = $EmployeeRef

    if ([string]::IsNullOrWhiteSpace($ServiceEventId)) {
        Remove-Item Env:IEMS_E2E_SERVICE_EVENT_ID -ErrorAction SilentlyContinue
    } else {
        $env:IEMS_E2E_SERVICE_EVENT_ID = $ServiceEventId
    }

    $runnerArgs = @{
        SkipCredentialPrecheck = $true
        E2EScript = "test_e2e_service_event_document_attach.py"
    }

    if ($ForceStop) {
        $runnerArgs.ForceStop = $true
    }
    if ($KeepBackend) {
        $runnerArgs.KeepBackend = $true
    }

    & (Join-Path $projectRoot "run-e2e-live.ps1") @runnerArgs
    exit $LASTEXITCODE
} finally {
    if ($null -eq $previousPassword) {
        Remove-Item Env:IEMS_E2E_DE_PASSWORD -ErrorAction SilentlyContinue
    } else {
        $env:IEMS_E2E_DE_PASSWORD = $previousPassword
    }

    if ($null -eq $previousEmployeeRef) {
        Remove-Item Env:IEMS_E2E_SERVICE_EVENT_EMPLOYEE_REF -ErrorAction SilentlyContinue
    } else {
        $env:IEMS_E2E_SERVICE_EVENT_EMPLOYEE_REF = $previousEmployeeRef
    }

    if ($null -eq $previousServiceEventId) {
        Remove-Item Env:IEMS_E2E_SERVICE_EVENT_ID -ErrorAction SilentlyContinue
    } else {
        $env:IEMS_E2E_SERVICE_EVENT_ID = $previousServiceEventId
    }

    Pop-Location
}