param([switch]$CollectReviewed1024Sources,[string]$ReviewedStaticReceiptSHA256='',[switch]$AcceptReviewedSamplingRisk)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Driver=Join-Path $PSScriptRoot 'memset_callsite_stage.py'
if ((Get-FileHash -LiteralPath $Driver -Algorithm SHA256).Hash -ine $Config.bootstrap_sha256) {throw 'Bootstrap identity conflict'}
$StageArguments=@('-I',$Driver,'stage-a',$PSScriptRoot)
if ($CollectReviewed1024Sources) {
    if ($ReviewedStaticReceiptSHA256 -notmatch '^[0-9a-fA-F]{64}$' -or -not $AcceptReviewedSamplingRisk) {
        throw 'Reviewed new A receipt and explicit sampling-risk acceptance required'
    }
    $StageArguments=@('-I',$Driver,'stage-b',$PSScriptRoot,'--reviewed-static-sha256',$ReviewedStaticReceiptSHA256,'--accept-reviewed-sampling-risk')
} elseif ($ReviewedStaticReceiptSHA256 -or $AcceptReviewedSamplingRisk) {throw 'Explicit collection switch required'}
& $Config.python @StageArguments
if ($LASTEXITCODE -ne 0) {throw 'Source diagnostic stopped; preserve new evidence; no retry/resume/cleanup'}
