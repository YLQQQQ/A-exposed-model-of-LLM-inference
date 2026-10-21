param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($args.Count -ne 0) {throw 'Stage A only; no collection switch is available'}
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Driver=Join-Path $PSScriptRoot 'cupti_timeline_stage.py'
$Support=Join-Path $PSScriptRoot 'micro_support.py'
$Parent=Join-Path $PSScriptRoot 'independent_cupti_stage.py'
function Get-ExactSHA256([string]$Path) {
    $Stream=[IO.File]::OpenRead($Path)
    $Digest=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($Digest.ComputeHash($Stream))).Replace('-','').ToLowerInvariant()}
    finally {$Digest.Dispose();$Stream.Dispose()}
}
if ((Get-ExactSHA256 $Driver) -ine $Config.bootstrap_sha256 -or
    (Get-ExactSHA256 $Support) -ine $Config.support_sha256 -or
    (Get-ExactSHA256 $Parent) -ine $Config.parent_stage_sha256) {
    throw 'Bootstrap/support identity conflict; STOP'
}
& $Config.python -I $Driver --package $PSScriptRoot
if ($LASTEXITCODE -ne 0) {throw 'Stage A failed; preserve new receipt; no retry, cleanup or GPU execution'}
