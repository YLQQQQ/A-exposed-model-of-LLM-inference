param([switch]$CollectReviewedB2,[string]$ReviewedStaticReceiptSHA256='')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Driver=Join-Path $PSScriptRoot 'memset_prefill_stage.py'
if ((Get-FileHash -LiteralPath $Driver -Algorithm SHA256).Hash -ine $Config.bootstrap_sha256) {throw 'Bootstrap identity conflict'}
$StageArguments=@('-I',$Driver,'stage-a',$PSScriptRoot)
if ($CollectReviewedB2) {
    if ($ReviewedStaticReceiptSHA256 -notmatch '^[0-9a-fA-F]{64}$') {throw 'Explicit reviewed new Stage A receipt hash required'}
    $StageArguments=@('-I',$Driver,'stage-b',$PSScriptRoot,'--reviewed-static-sha256',$ReviewedStaticReceiptSHA256)
} elseif ($ReviewedStaticReceiptSHA256) {throw 'A receipt hash alone cannot enable collection'}
& $Config.python @StageArguments
if ($LASTEXITCODE -ne 0) {throw 'STOP; preserve new receipt and all old evidence; no retry/resume/cleanup'}
