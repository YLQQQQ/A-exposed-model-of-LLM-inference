param([switch]$CollectReviewedMicro,[string]$ReviewedStaticReceiptSHA256='')
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Driver=Join-Path $PSScriptRoot 'memset_micro.py'
if ((Get-FileHash -LiteralPath $Driver -Algorithm SHA256).Hash -ine $Config.bootstrap_sha256) {throw 'Bootstrap identity conflict'}
$Args=@('-I',$Driver,'stage-a',$PSScriptRoot)
if ($CollectReviewedMicro) {
    if ($ReviewedStaticReceiptSHA256 -notmatch '^[0-9a-fA-F]{64}$') {throw 'Explicit reviewed Stage A receipt SHA256 required'}
    $Args=@('-I',$Driver,'stage-b',$PSScriptRoot,'--reviewed-static-sha256',$ReviewedStaticReceiptSHA256)
} elseif ($ReviewedStaticReceiptSHA256) {throw 'Receipt hash cannot enable collection without the explicit switch'}
& $Config.python @Args
if ($LASTEXITCODE -ne 0) {throw 'STOP; preserve failure evidence; no retry/resume/cleanup'}
