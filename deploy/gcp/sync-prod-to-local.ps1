param(
    [string]$ProjectId = "erudite-acre-415118",
    [string]$Zone = "us-central1-a",
    [string]$InstanceName = "iems-app-vm",
    [string]$RepoRootOnVm = "/home/kenne/MyIEMS",
    [string]$ComposeFile = "deploy/gcp/docker-compose.vm.yml",
    [string]$RemoteBackupRoot = "/home/kenne/iems-backups",
    [string]$LocalDownloadDir = "",
    [string]$LocalBackupArchive = "",
    [string]$LocalMongoUri = "mongodb://127.0.0.1:27017",
    [string]$LocalDbName = "iems_db",
    [string]$LocalUploadsDir = "",
    [switch]$TunnelThroughIap,
    [switch]$SkipUploads,
    [switch]$KeepArchive,
    [switch]$Force,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

# Pulls the latest production state from the GCP VM and restores it into the
# local MongoDB instance. Destructive on the local DB (drops collections via
# mongorestore --drop) so -Force is required outside of -DryRun.

function Resolve-ToolPath {
    param(
        [string]$Name,
        [string[]]$Candidates
    )

    $cmd = Get-Command $Name -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -and (Test-Path $cmd.Source)) {
        return $cmd.Source
    }

    foreach ($candidate in $Candidates) {
        if ($candidate -and (Test-Path $candidate)) {
            return $candidate
        }
    }

    return $null
}

function Resolve-MongoRestore {
    $candidates = @(
        "C:\Program Files\MongoDB\Tools\100\bin\mongorestore.exe",
        "C:\Program Files\MongoDB\Server\8.2\bin\mongorestore.exe",
        "C:\Program Files\MongoDB\Server\8.0\bin\mongorestore.exe",
        "C:\Program Files\MongoDB\Server\7.0\bin\mongorestore.exe",
        "C:\Program Files\MongoDB\Server\6.0\bin\mongorestore.exe"
    )
    $resolved = Resolve-ToolPath -Name "mongorestore" -Candidates $candidates
    if (-not $resolved) {
        throw "mongorestore was not found. Install MongoDB Database Tools (https://www.mongodb.com/try/download/database-tools) and ensure mongorestore.exe is on PATH."
    }
    return $resolved
}

function Resolve-Tar {
    $candidates = @(
        (Join-Path $env:WINDIR "System32\tar.exe")
    )
    $resolved = Resolve-ToolPath -Name "tar" -Candidates $candidates
    if (-not $resolved) {
        throw "tar.exe was not found. Windows 10+ ships tar in System32; install bsdtar or add it to PATH."
    }
    return $resolved
}

if (-not $Force -and -not $DryRun) {
    throw "Restoring into the local DB '$LocalDbName' is destructive (mongorestore --drop). Re-run with -Force, or use -DryRun to preview."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$backupScript = Join-Path $scriptDir "backup-vm.ps1"

if ([string]::IsNullOrWhiteSpace($LocalDownloadDir)) {
    $LocalDownloadDir = Join-Path (Get-Location) "backups"
}

if ([string]::IsNullOrWhiteSpace($LocalUploadsDir)) {
    $LocalUploadsDir = Join-Path (Split-Path -Parent (Split-Path -Parent $scriptDir)) "uploads"
}

# ----- Step 1: obtain a backup archive on disk --------------------------------
$archivePath = $LocalBackupArchive
if ([string]::IsNullOrWhiteSpace($archivePath)) {
    if (-not (Test-Path $backupScript)) {
        throw "backup-vm.ps1 not found at $backupScript"
    }

    Write-Host "No -LocalBackupArchive provided. Triggering backup-vm.ps1 to fetch a fresh archive..."
    $backupArgs = @{
        ProjectId        = $ProjectId
        Zone             = $Zone
        InstanceName     = $InstanceName
        RepoRootOnVm     = $RepoRootOnVm
        ComposeFile      = $ComposeFile
        RemoteBackupRoot = $RemoteBackupRoot
        LocalDownloadDir = $LocalDownloadDir
    }
    if ($TunnelThroughIap) { $backupArgs.TunnelThroughIap = $true }
    if ($DryRun) { $backupArgs.DryRun = $true }

    & $backupScript @backupArgs
    if ($LASTEXITCODE -ne 0) {
        throw "backup-vm.ps1 failed with exit code $LASTEXITCODE."
    }

    if (-not $DryRun) {
        $latest = Get-ChildItem -Path $LocalDownloadDir -Filter "iems-backup-*.tgz" -File -ErrorAction Stop |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1
        if (-not $latest) {
            throw "No iems-backup-*.tgz archive found under $LocalDownloadDir after backup."
        }
        $archivePath = $latest.FullName
    } else {
        $archivePath = "(dry-run: backup not produced)"
    }
}
elseif (-not (Test-Path $archivePath)) {
    throw "Local backup archive not found: $archivePath"
}

Write-Host "Using archive: $archivePath"

# ----- Step 2: extract and restore --------------------------------------------
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$extractRoot = Join-Path $env:TEMP "iems-sync-$timestamp"

if ($DryRun) {
    Write-Host "DRY RUN: would extract '$archivePath' into '$extractRoot'"
    Write-Host "DRY RUN: would run mongorestore --uri='$LocalMongoUri' --nsInclude='$LocalDbName.*' --drop --gzip --archive=<extracted>/mongo-iems_db.archive.gz"
    if (-not $SkipUploads) {
        Write-Host "DRY RUN: would extract uploads.tar.gz into '$LocalUploadsDir' (clearing it first)"
    } else {
        Write-Host "DRY RUN: -SkipUploads set; uploads will not be restored"
    }
    if (-not $KeepArchive) {
        Write-Host "DRY RUN: would remove temp extract dir '$extractRoot' afterwards"
    }
    exit 0
}

$mongorestore = Resolve-MongoRestore
$tar = Resolve-Tar

New-Item -ItemType Directory -Path $extractRoot -Force | Out-Null

Write-Host "Extracting archive..."
& $tar -xzf $archivePath -C $extractRoot
if ($LASTEXITCODE -ne 0) {
    throw "tar failed to extract $archivePath (exit code $LASTEXITCODE)."
}

# backup-vm.ps1 tars '$timestamp' inside '$RemoteBackupRoot', so the extracted
# tree is a single timestamp directory containing mongo-iems_db.archive.gz and
# uploads.tar.gz.
$extractedRoots = Get-ChildItem -Path $extractRoot -Directory
if ($extractedRoots.Count -ne 1) {
    throw "Expected exactly one directory inside the archive, found $($extractedRoots.Count) in $extractRoot."
}
$payloadDir = $extractedRoots[0].FullName

$mongoArchive = Join-Path $payloadDir "mongo-iems_db.archive.gz"
$uploadsArchive = Join-Path $payloadDir "uploads.tar.gz"

if (-not (Test-Path $mongoArchive)) {
    throw "Mongo archive missing from backup: $mongoArchive"
}

Write-Host "Restoring '$LocalDbName' into $LocalMongoUri (with --drop)..."
& $mongorestore `
    --uri=$LocalMongoUri `
    --nsInclude="$LocalDbName.*" `
    --drop `
    --gzip `
    --archive=$mongoArchive
if ($LASTEXITCODE -ne 0) {
    throw "mongorestore failed with exit code $LASTEXITCODE."
}

if (-not $SkipUploads) {
    if (-not (Test-Path $uploadsArchive)) {
        Write-Warning "uploads.tar.gz not found in archive; skipping upload restore."
    } else {
        Write-Host "Restoring uploads into $LocalUploadsDir..."
        if (Test-Path $LocalUploadsDir) {
            Get-ChildItem -Path $LocalUploadsDir -Force | Remove-Item -Recurse -Force
        } else {
            New-Item -ItemType Directory -Path $LocalUploadsDir -Force | Out-Null
        }
        & $tar -xzf $uploadsArchive -C $LocalUploadsDir
        if ($LASTEXITCODE -ne 0) {
            throw "tar failed to extract uploads.tar.gz (exit code $LASTEXITCODE)."
        }
    }
} else {
    Write-Host "-SkipUploads set; uploads were not touched."
}

if (-not $KeepArchive) {
    try {
        Remove-Item -Path $extractRoot -Recurse -Force -ErrorAction Stop
    } catch {
        Write-Warning "Failed to clean up temp dir $extractRoot - $($_.Exception.Message)"
    }
}

Write-Host "Local DB '$LocalDbName' is now in sync with the VM backup at $archivePath."
