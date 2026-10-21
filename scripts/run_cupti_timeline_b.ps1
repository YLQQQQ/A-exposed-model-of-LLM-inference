param(
    [switch]$RunReviewedModel,
    [string]$ReviewedAReceiptSha256
)
$ErrorActionPreference = 'Stop'
if (-not $RunReviewedModel -or $ReviewedAReceiptSha256 -notmatch '^[a-fA-F0-9]{64}$') {
    throw 'Explicit reviewed model switch and A receipt SHA256 required; STOP'
}
$PackageRoot = $PSScriptRoot
function SHA([string]$Path) {
    $InputFile = [IO.File]::OpenRead($Path)
    $Digest = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($Digest.ComputeHash($InputFile))).Replace('-','').ToLowerInvariant() }
    finally { $Digest.Dispose(); $InputFile.Dispose() }
}
$Config = Get-Content -LiteralPath (Join-Path $PackageRoot 'delivery.json') -Raw | ConvertFrom-Json
foreach ($Item in $Config.bootstrap_files) {
    $Name = [string]$Item.path
    if ($Name -notmatch '^[a-zA-Z0-9_.-]+$' -or
        (SHA (Join-Path $PackageRoot $Name)) -ne $Item.sha256) {
        throw 'Bootstrap identity conflict; STOP'
    }
}
if ($ReviewedAReceiptSha256 -ine $Config.reviewed_a_receipt_sha256) {
    throw 'Reviewed A receipt conflict; STOP'
}
& $Config.python -I -B -X utf8 (Join-Path $PackageRoot 'cupti_timeline_b.py') `
    --package $PackageRoot --run-reviewed-model `
    --reviewed-a-receipt-sha256 $ReviewedAReceiptSha256
if ($LASTEXITCODE -ne 0) {
    throw 'Model diagnostic stopped; preserve new evidence; no retry/resume/cleanup'
}
