param([switch]$RunReviewedMicro,[string]$ReviewedAReceiptSha256)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($args.Count -ne 0 -or -not $RunReviewedMicro -or
    $ReviewedAReceiptSha256 -cne '67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0') {
    throw 'Explicit reviewed B and exact approved A receipt are required; STOP'
}
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Driver=Join-Path $PSScriptRoot 'independent_cupti_b.py'
if ((Get-FileHash -LiteralPath $Driver -Algorithm SHA256).Hash -ine $Config.controller_sha256) {
    throw 'B controller identity conflict; STOP'
}
& $Config.python -I $Driver --package $PSScriptRoot --run-reviewed-b --reviewed-a-receipt-sha256 $ReviewedAReceiptSha256
if ($LASTEXITCODE -ne 0) {throw 'B stopped; preserve new evidence; no retry, cleanup or model execution'}
