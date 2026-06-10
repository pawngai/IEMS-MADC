param(
    [switch]$Strict
)

$ErrorActionPreference = "Stop"

$dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
if (-not $dockerCmd) {
    Write-Warning "Docker CLI is not installed or not in PATH."
    Write-Host "Install Docker Desktop (Windows) or Docker Engine, then retry docker-based commands."
    Write-Host "Fallback: use local dev scripts ./start-dev.ps1 and rely on CI docker job for image validation."
    if ($Strict) {
        exit 1
    }
    exit 0
}

try {
    $version = docker --version
    Write-Host $version
    Write-Host "Docker CLI preflight: OK"
    exit 0
} catch {
    Write-Warning "Docker CLI exists but failed to run: $($_.Exception.Message)"
    if ($Strict) {
        exit 1
    }
    exit 0
}
