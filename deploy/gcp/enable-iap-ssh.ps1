param(
    [string]$ProjectId = "erudite-acre-415118",
    [string]$Network = "default",
    [string]$RuleName = "allow-iap-ssh",
    [string]$SourceRange = "35.235.240.0/20"
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

$existingRule = & $gcloudPath compute firewall-rules list --project=$ProjectId "--filter=name=$RuleName" '--format=value(name)'
if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace(($existingRule | Out-String).Trim())) {
    Write-Host "Firewall rule already exists: $RuleName"
    exit 0
}

Invoke-Gcloud -GcloudPath $gcloudPath -Arguments @(
    "compute",
    "firewall-rules",
    "create",
    $RuleName,
    "--project=$ProjectId",
    "--network=$Network",
    "--direction=INGRESS",
    "--priority=1000",
    "--action=ALLOW",
    "--rules=tcp:22",
    "--source-ranges=$SourceRange",
    "--description=Allow SSH over Identity-Aware Proxy"
)

Write-Host "Created firewall rule: $RuleName"
Write-Host "Ensure your user has IAP-secured Tunnel User access to the project or instance before using --tunnel-through-iap."