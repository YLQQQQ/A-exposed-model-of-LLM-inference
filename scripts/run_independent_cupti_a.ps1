param()
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if ($args.Count -ne 0) {throw 'Stage A only; no collection switch is available'}
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$Driver=Join-Path $PSScriptRoot 'independent_cupti_stage.py'
$Support=Join-Path $PSScriptRoot 'micro_support.py'
if ((Get-FileHash -LiteralPath $Driver -Algorithm SHA256).Hash -ine $Config.bootstrap_sha256 -or
    (Get-FileHash -LiteralPath $Support -Algorithm SHA256).Hash -ine $Config.support_sha256) {
    throw 'Bootstrap/support identity conflict; STOP'
}
& $Config.python -I $Driver --package $PSScriptRoot
if ($LASTEXITCODE -ne 0) {throw 'Stage A failed; preserve new receipt; no retry, cleanup or GPU execution'}
