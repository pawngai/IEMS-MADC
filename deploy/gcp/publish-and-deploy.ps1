param(
    [string]$ProjectId = "erudite-acre-415118",
    [string]$Region = "us-central1",
    [string]$Repository = "iems",
    [string]$ImageName = "myiems-backend",
    [string]$Tag = "latest",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "iems-app-vm",
    [string]$RepoRootOnVm = "/home/kenne/MyIEMS",
    [string]$ComposeFile = "deploy/gcp/docker-compose.vm.yml",
    [string]$HealthUrl = "",
    [switch]$SkipDockerAuth,
    [switch]$TunnelThroughIap,
    [switch]$SkipPull,
    [switch]$SkipHealthCheck
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$buildScript = Join-Path $scriptDir "build-and-push-image.ps1"
$deployScript = Join-Path $scriptDir "deploy-vm.ps1"

if (-not (Test-Path $buildScript)) {
    throw "Build script not found at $buildScript"
}

if (-not (Test-Path $deployScript)) {
    throw "Deploy script not found at $deployScript"
}

Write-Host "Publishing backend image..."

$buildArgs = @{
    ProjectId = $ProjectId
    Region = $Region
    Repository = $Repository
    ImageName = $ImageName
    Tag = $Tag
}

if ($SkipDockerAuth) {
    $buildArgs.SkipDockerAuth = $true
}

& $buildScript @buildArgs
if ($LASTEXITCODE -ne 0) {
    throw "Image publish failed with exit code $LASTEXITCODE."
}

Write-Host "Deploying published image to VM..."

$deployArgs = @{
    ProjectId = $ProjectId
    Zone = $Zone
    InstanceName = $InstanceName
    RepoRootOnVm = $RepoRootOnVm
    ComposeFile = $ComposeFile
}

if (-not [string]::IsNullOrWhiteSpace($HealthUrl)) {
    $deployArgs.HealthUrl = $HealthUrl
}

if ($TunnelThroughIap) {
    $deployArgs.TunnelThroughIap = $true
}

if ($SkipPull) {
    $deployArgs.SkipPull = $true
}

if ($SkipHealthCheck) {
    $deployArgs.SkipHealthCheck = $true
}

& $deployScript @deployArgs
if ($LASTEXITCODE -ne 0) {
    throw "VM deploy failed with exit code $LASTEXITCODE."
}

Write-Host "Publish-and-deploy completed."