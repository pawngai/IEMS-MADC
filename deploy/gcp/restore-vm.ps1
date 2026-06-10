param(
    [string]$ProjectId = "erudite-acre-415118",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "iems-app-vm",
    [string]$RepoRootOnVm = "/home/kenne/MyIEMS",
    [string]$ComposeFile = "deploy/gcp/docker-compose.vm.yml",
    [string]$RemoteBackupArchive = "",
    [string]$LocalBackupArchive = "",
    [string]$RemoteRestoreRoot = "/home/kenne/iems-restore",
    [switch]$TunnelThroughIap,
    [switch]$Force,
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

if ([string]::IsNullOrWhiteSpace($RemoteBackupArchive) -and [string]::IsNullOrWhiteSpace($LocalBackupArchive)) {
    throw "Provide -RemoteBackupArchive or -LocalBackupArchive."
}

if (-not $Force -and -not $DryRun) {
    throw "Restore is destructive. Re-run with -Force after taking a fresh backup and confirming the target VM."
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$remoteArchive = $RemoteBackupArchive

if ($DryRun -and -not [string]::IsNullOrWhiteSpace($LocalBackupArchive) -and [string]::IsNullOrWhiteSpace($RemoteBackupArchive)) {
    $remoteArchive = "$RemoteRestoreRoot/$(Split-Path -Leaf $LocalBackupArchive)"
}

if (-not [string]::IsNullOrWhiteSpace($LocalBackupArchive)) {
    if (-not (Test-Path $LocalBackupArchive)) {
        throw "Local backup archive not found: $LocalBackupArchive"
    }
    $remoteArchive = "$RemoteRestoreRoot/$(Split-Path -Leaf $LocalBackupArchive)"
    $scpArgs = @(
        "compute",
        "scp",
        $LocalBackupArchive,
        "$InstanceName`:$remoteArchive",
        "--project=$ProjectId",
        "--zone=$Zone"
    )
    if ($TunnelThroughIap) {
        $scpArgs += "--tunnel-through-iap"
    }

    $prepArgs = @(
        "compute",
        "ssh",
        $InstanceName,
        "--project=$ProjectId",
        "--zone=$Zone",
        "--command",
        "mkdir -p '$RemoteRestoreRoot'"
    )
    if ($TunnelThroughIap) {
        $prepArgs += "--tunnel-through-iap"
    }
    if (-not $DryRun) {
        $gcloudPath = Resolve-GcloudCommand
        Invoke-Gcloud -GcloudPath $gcloudPath -Arguments $prepArgs
        Invoke-Gcloud -GcloudPath $gcloudPath -Arguments $scpArgs
    }
}

$restoreDir = "$RemoteRestoreRoot/$timestamp"
$remoteScriptLines = @(
    "set -euo pipefail",
    "cd '$RepoRootOnVm'",
    "test -f '$remoteArchive' || { echo 'Backup archive not found: $remoteArchive'; exit 1; }",
    "mkdir -p '$restoreDir'",
    "tar -xzf '$remoteArchive' -C '$restoreDir' --strip-components=1",
    "test -f '$restoreDir/mongo-iems_db.archive.gz' || { echo 'Mongo archive missing from backup'; exit 1; }",
    "test -f '$restoreDir/uploads.tar.gz' || { echo 'Uploads archive missing from backup'; exit 1; }",
    ('compose() { if sudo docker compose version >/dev/null 2>&1; then sudo docker compose -f ''' + $ComposeFile + ''' "$@"; else sudo docker-compose -f ''' + $ComposeFile + ''' "$@"; fi; }'),
    'MONGO_CTR=$(compose ps -q mongo)',
    'BACKEND_CTR=$(compose ps -q backend)',
    'test -n "${MONGO_CTR}" || { echo ''Mongo container not found''; exit 1; }',
    'test -n "${BACKEND_CTR}" || { echo ''Backend container not found''; exit 1; }',
    "compose stop backend",
    ('cat ''' + $restoreDir + '/mongo-iems_db.archive.gz'' | sudo docker exec -i "${MONGO_CTR}" mongorestore --db iems_db --archive --gzip --drop'),
    ('sudo docker run --rm --volumes-from "${BACKEND_CTR}" -v ''' + $restoreDir + ':/restore'' alpine:3.20 sh -c ''rm -rf /app/uploads/* && tar -xzf /restore/uploads.tar.gz -C /app/uploads'''),
    "compose up -d backend",
    "compose ps"
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
    Write-Host "DRY RUN: would restore VM from $remoteArchive"
    if (-not [string]::IsNullOrWhiteSpace($LocalBackupArchive)) {
        Write-Host "DRY RUN: would upload $LocalBackupArchive to $remoteArchive"
    }
    Write-Host "DRY RUN: remote command:"
    Write-Host $remoteCommand
    exit 0
}

$gcloudPath = Resolve-GcloudCommand
Write-Host "Restoring VM from $remoteArchive..."
Invoke-Gcloud -GcloudPath $gcloudPath -Arguments $sshArgs
Write-Host "Restore completed. Run smoke tests before reopening traffic."