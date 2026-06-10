param(
    [string]$ProjectId = "erudite-acre-415118",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "iems-app-vm",
    [string]$RepoRootOnVm = "/home/kenne/MyIEMS",
    [string]$ComposeFile = "deploy/gcp/docker-compose.vm.yml",
    [string]$RemoteBackupRoot = "/home/kenne/iems-backups",
    [string]$LocalDownloadDir = "",
    [switch]$TunnelThroughIap,
    [switch]$SkipDownload,
    [switch]$DryRun
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

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$remoteBackupDir = "$RemoteBackupRoot/$timestamp"
$remoteArchive = "$RemoteBackupRoot/iems-backup-$timestamp.tgz"

$remoteScriptLines = @(
    "set -euo pipefail",
    "cd '$RepoRootOnVm'",
    "mkdir -p '$remoteBackupDir'",
    ('compose() { if sudo docker compose version >/dev/null 2>&1; then sudo docker compose -f ''' + $ComposeFile + ''' "$@"; else sudo docker-compose -f ''' + $ComposeFile + ''' "$@"; fi; }'),
    'MONGO_CTR=$(compose ps -q mongo)',
    'BACKEND_CTR=$(compose ps -q backend)',
    'test -n "${MONGO_CTR}" || { echo ''Mongo container not found''; exit 1; }',
    'test -n "${BACKEND_CTR}" || { echo ''Backend container not found''; exit 1; }',
    ('sudo docker exec "${MONGO_CTR}" mongodump --db iems_db --archive --gzip > ''' + $remoteBackupDir + '/mongo-iems_db.archive.gz'''),
    ('sudo docker run --rm --volumes-from "${BACKEND_CTR}" -v ''' + $remoteBackupDir + ':/backup'' alpine:3.20 tar -czf /backup/uploads.tar.gz -C /app/uploads .'),
    "tar -czf '$remoteArchive' -C '$RemoteBackupRoot' '$timestamp'",
    "sha256sum '$remoteArchive' > '$remoteArchive.sha256'",
    "echo '$remoteArchive'"
)

$remoteCommand = [string]::Join("; ", $remoteScriptLines)
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

if ($DryRun) {
    Write-Host "DRY RUN: would create VM backup at $remoteArchive"
    Write-Host "DRY RUN: remote command:"
    Write-Host $remoteCommand
    if (-not $SkipDownload) {
        $downloadTarget = $LocalDownloadDir
        if ([string]::IsNullOrWhiteSpace($downloadTarget)) {
            $downloadTarget = Join-Path (Get-Location) "backups"
        }
        Write-Host "DRY RUN: would download $remoteArchive and $remoteArchive.sha256 to $downloadTarget"
    }
    exit 0
}

$gcloudPath = Resolve-GcloudCommand
Write-Host "Creating VM backup at $remoteArchive..."
Invoke-Gcloud -GcloudPath $gcloudPath -Arguments $sshArgs

if (-not $SkipDownload) {
    if ([string]::IsNullOrWhiteSpace($LocalDownloadDir)) {
        $LocalDownloadDir = Join-Path (Get-Location) "backups"
    }
    New-Item -ItemType Directory -Path $LocalDownloadDir -Force | Out-Null

    $scpArgs = @(
        "compute",
        "scp",
        "$InstanceName`:$remoteArchive",
        $LocalDownloadDir,
        "--project=$ProjectId",
        "--zone=$Zone"
    )
    if ($TunnelThroughIap) {
        $scpArgs += "--tunnel-through-iap"
    }
    Invoke-Gcloud -GcloudPath $gcloudPath -Arguments $scpArgs

    $hashScpArgs = @(
        "compute",
        "scp",
        "$InstanceName`:$remoteArchive.sha256",
        $LocalDownloadDir,
        "--project=$ProjectId",
        "--zone=$Zone"
    )
    if ($TunnelThroughIap) {
        $hashScpArgs += "--tunnel-through-iap"
    }
    Invoke-Gcloud -GcloudPath $gcloudPath -Arguments $hashScpArgs
}

Write-Host "Backup completed: $remoteArchive"