param(
    [string]$ProjectId = "erudite-acre-415118",
    [string]$Region = "us-central1",
    [string]$Repository = "iems",
    [string]$ImageName = "myiems-backend",
    [string]$Tag = "latest",
    [string]$Dockerfile = "deploy/gcp/Dockerfile.backend",
    [string]$BuildContext = ".",
    [switch]$SkipDockerAuth
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

function Resolve-DockerCommand {
    $command = Get-Command docker -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "docker was not found. Install Docker Desktop or add docker to PATH."
    }
    return $command.Source
}

$gcloudPath = Resolve-GcloudCommand
$dockerPath = Resolve-DockerCommand
$registryHost = "$Region-docker.pkg.dev"
$imageRef = "$registryHost/$ProjectId/$Repository/$ImageName`:$Tag"

Write-Host "Using gcloud: $gcloudPath"
Write-Host "Using docker: $dockerPath"
Write-Host "Target image: $imageRef"

Invoke-Gcloud -GcloudPath $gcloudPath -Arguments @("--version")

if (-not $SkipDockerAuth) {
    Write-Host "Configuring Docker auth for $registryHost"
    Invoke-Gcloud -GcloudPath $gcloudPath -Arguments @(
        "auth",
        "configure-docker",
        $registryHost,
        "--quiet"
    )
}

& $dockerPath "build" "-f" $Dockerfile "-t" $imageRef $BuildContext
if ($LASTEXITCODE -ne 0) {
    throw "docker build failed with exit code $LASTEXITCODE."
}

& $dockerPath "push" $imageRef
if ($LASTEXITCODE -ne 0) {
    throw "docker push failed with exit code $LASTEXITCODE."
}

Write-Host "Published image: $imageRef"