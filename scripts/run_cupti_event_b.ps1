param([switch]$RunReviewedEvent,[string]$ReviewedAReceiptSha256)
$ErrorActionPreference='Stop'
if (-not $RunReviewedEvent -or $ReviewedAReceiptSha256 -notmatch '^[a-fA-F0-9]{64}$') {
    throw 'Explicit reviewed event switch and A receipt SHA256 required; STOP'
}
function SHA([string]$Path) {
    $File=[IO.File]::OpenRead($Path);$Digest=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($Digest.ComputeHash($File))).Replace('-','').ToLowerInvariant()}
    finally {$Digest.Dispose();$File.Dispose()}
}
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
foreach($Item in $Config.bootstrap_files) {
    if ($Item.path -notmatch '^[a-zA-Z0-9_.-]+$' -or (SHA (Join-Path $PSScriptRoot $Item.path)) -ne $Item.sha256) {
        throw 'Bootstrap identity conflict; STOP'
    }
}
if($ReviewedAReceiptSha256 -ine $Config.reviewed_a_receipt_sha256){throw 'Reviewed A receipt conflict; STOP'}
& $Config.python -I -B -X utf8 (Join-Path $PSScriptRoot 'cupti_event_b.py') --package $PSScriptRoot `
    --run-reviewed-event --reviewed-a-receipt-sha256 $ReviewedAReceiptSha256.ToLowerInvariant()
if($LASTEXITCODE -ne 0){throw 'Event probe stopped; preserve evidence; no retry, cleanup or model'}
