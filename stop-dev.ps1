param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 3000,
    [int]$RetryCount = 6,
    [int]$RetryDelayMs = 500
)

$ErrorActionPreference = "SilentlyContinue"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

function Stop-ProcessTree {
    param(
        [int]$ProcessId
    )

    if (-not $ProcessId -or $ProcessId -le 0) {
        return
    }

    try {
        Stop-Process -Id $ProcessId -Force -ErrorAction Stop
        return
    } catch {
        try {
            $null = & cmd /c "taskkill /PID $ProcessId /T /F" 2>$null
        } catch {
        }
    }
}

function Stop-ServerOnPort {
    param(
        [int]$Port,
        [string]$Name
    )

    for ($attempt = 1; $attempt -le $RetryCount; $attempt++) {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
        if (-not $connections) {
            if ($attempt -eq 1) {
                Write-Host "$Name not running on port $Port"
            }
            return
        }

        $processIds = $connections | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($processId in $processIds) {
            if ($processId -and $processId -gt 0) {
                Stop-ProcessTree -ProcessId $processId
                Write-Host "Stopped $Name on port $Port (PID $processId)"
            }
        }

        Start-Sleep -Milliseconds $RetryDelayMs
    }

    $remaining = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if ($remaining) {
        $remainingPids = $remaining | Select-Object -ExpandProperty OwningProcess -Unique
        Write-Warning "$Name still listening on port $Port after retries. PIDs: $($remainingPids -join ', ')"
    }
}

function Stop-BackendProcessByCommandLine {
    param(
        [string]$ProjectRoot,
        [int]$RetryCount = 3,
        [int]$RetryDelayMs = 400
    )

    $escapedProjectRoot = [Regex]::Escape($ProjectRoot)
    for ($attempt = 1; $attempt -le $RetryCount; $attempt++) {
        $candidates = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
            Where-Object {
                $cmd = [string]($_.CommandLine)
                if (-not $cmd) { return $false }
                return ($cmd -match '(?i)uvicorn\s+app\.main:app') -and ($cmd -match $escapedProjectRoot)
            }

        if (-not $candidates) {
            return
        }

        foreach ($proc in $candidates) {
            $procId = [int]$proc.ProcessId
            if ($procId -gt 0) {
                Stop-ProcessTree -ProcessId $procId
                Write-Host "Stopped backend process by command line match (PID $procId)"
            }
        }

        Start-Sleep -Milliseconds $RetryDelayMs
    }
}

Stop-ServerOnPort -Port $BackendPort -Name "Backend"
Stop-ServerOnPort -Port $FrontendPort -Name "Frontend"
Stop-BackendProcessByCommandLine -ProjectRoot $projectRoot -RetryCount $RetryCount -RetryDelayMs $RetryDelayMs
