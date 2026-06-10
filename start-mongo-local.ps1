param(
    [int]$Port = 27017,
    [string]$BindIp = "127.0.0.1",
    [string]$DataRoot = ".mongo-local",
    [switch]$SkipServiceStart
)

$ErrorActionPreference = "Stop"

function Test-MongoPort {
    param([int]$TargetPort)

    try {
        $listener = Get-NetTCPConnection -LocalPort $TargetPort -State Listen -ErrorAction SilentlyContinue
        return [bool]$listener
    } catch {
        return $false
    }
}

function Get-MongodFromService {
    $svc = Get-CimInstance Win32_Service -Filter "Name='MongoDB'" -ErrorAction SilentlyContinue
    if (-not $svc -or -not $svc.PathName) {
        return $null
    }

    if ($svc.PathName -match '"([^"]*mongod\.exe)"') {
        return $matches[1]
    }

    if ($svc.PathName -match "^([^\s]+mongod\.exe)") {
        return $matches[1]
    }

    return $null
}

function Resolve-MongodPath {
    $fromService = Get-MongodFromService
    if ($fromService -and (Test-Path $fromService)) {
        return $fromService
    }

    $cmd = Get-Command mongod -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -and (Test-Path $cmd.Source)) {
        return $cmd.Source
    }

    $candidates = @(
        "C:\Program Files\MongoDB\Server\8.2\bin\mongod.exe",
        "C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe",
        "C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
        "C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    return $null
}

if (Test-MongoPort -TargetPort $Port) {
    Write-Host "MongoDB already listening on localhost:$Port"
    exit 0
}

if (-not $SkipServiceStart) {
    try {
        $mongoService = Get-Service -Name "MongoDB" -ErrorAction SilentlyContinue
        if ($mongoService -and $mongoService.Status -ne "Running") {
            Write-Host "Trying MongoDB Windows service start..."
            Start-Service -Name "MongoDB" -ErrorAction Stop
            Start-Sleep -Seconds 2
        }
    } catch {
        Write-Warning "MongoDB service start failed or not permitted. Falling back to local mongod process."
    }
}

if (Test-MongoPort -TargetPort $Port) {
    Write-Host "MongoDB listening on localhost:$Port"
    exit 0
}

$mongodExe = Resolve-MongodPath
if (-not $mongodExe) {
    throw "Unable to locate mongod.exe. Install MongoDB Server or add mongod to PATH."
}

$cwd = Get-Location
$dataRootPath = Join-Path $cwd $DataRoot
$dataPath = Join-Path $dataRootPath "data"
$logPath = Join-Path $dataRootPath "mongod.log"

New-Item -ItemType Directory -Force -Path $dataPath | Out-Null

Write-Host "Starting local mongod using $mongodExe"
Start-Process -FilePath $mongodExe -ArgumentList @(
    "--dbpath", $dataPath,
    "--bind_ip", $BindIp,
    "--port", "$Port",
    "--logpath", $logPath,
    "--logappend"
) -WorkingDirectory $cwd -WindowStyle Hidden | Out-Null

$maxAttempts = 20
for ($i = 1; $i -le $maxAttempts; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-MongoPort -TargetPort $Port) {
        Write-Host "MongoDB listening on localhost:$Port"
        Write-Host "Data path: $dataPath"
        Write-Host "Log path: $logPath"
        exit 0
    }
}

$tail = ""
if (Test-Path $logPath) {
    $tail = (Get-Content $logPath -Tail 25) -join [Environment]::NewLine
}

throw "MongoDB failed to start on localhost:$Port. Log tail:`n$tail"
