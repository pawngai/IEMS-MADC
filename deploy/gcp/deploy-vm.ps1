param(
    [string]$ProjectId = "erudite-acre-415118",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "iems-app-vm",
    [string]$RepoRootOnVm = "/home/kenne/MyIEMS",
    [string]$ComposeFile = "deploy/gcp/docker-compose.vm.yml",
    [string]$HealthUrl = "",
    [switch]$TunnelThroughIap,
    [switch]$SkipPull,
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

function Resolve-GcloudCommand {
    $command = Get-Command gcloud -ErrorAction SilentlyContinue
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        "C:\Program Files\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd",
        (Join-Path $env:LOCALAPPDATA "Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"),
        (Join-Path $env:USERPROFILE "AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd")
    )

    foreach ($candidate in $candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    throw "gcloud was not found. Install Google Cloud SDK or add gcloud.cmd to PATH."
}

function Invoke-Gcloud {
    param(
        [string]$GcloudPath,
        [string[]]$Arguments
    )

    & $GcloudPath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "gcloud command failed with exit code $LASTEXITCODE."
    }
}

$gcloudPath = Resolve-GcloudCommand
Write-Host "Using gcloud: $gcloudPath"

Invoke-Gcloud -GcloudPath $gcloudPath -Arguments @("--version")

$remoteScriptLines = @(
    "set -euo pipefail",
    "cd '$RepoRootOnVm'",
    ('compose() { if sudo docker compose version >/dev/null 2>&1; then sudo docker compose -f ''' + $ComposeFile + ''' "$@"; else sudo docker-compose -f ''' + $ComposeFile + ''' "$@"; fi; }')
)

if (-not $SkipPull) {
    $remoteScriptLines += 'compose pull'
}

$remoteScriptLines += @(
    'compose up -d',
    'compose ps'
)

$remoteCommand = [string]::Join("; ", $remoteScriptLines)

Write-Host "Deploying to $InstanceName in $Zone..."
$sshArgs = @(
    "compute",
    "ssh",
    $InstanceName,
    "--project=$ProjectId",
    "--zone=$Zone",
    "--command",
    $remoteCommand
)

if ($TunnelThroughIap) {
    $sshArgs += "--tunnel-through-iap"
}

Invoke-Gcloud -GcloudPath $gcloudPath -Arguments $sshArgs

if (-not $SkipHealthCheck -and -not [string]::IsNullOrWhiteSpace($HealthUrl)) {
    Write-Host "Waiting for health endpoint: $HealthUrl"
    $maxAttempts = 12
    for ($attempt = 1; $attempt -le $maxAttempts; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri $HealthUrl -TimeoutSec 10
            Write-Host "Health check OK: HTTP $($response.StatusCode)"
            exit 0
        } catch {
            if ($attempt -eq $maxAttempts) {
                throw "Health check failed after $maxAttempts attempts: $($_.Exception.Message)"
            }
            Start-Sleep -Seconds 5
        }
    }
}

Write-Host "Deploy completed."