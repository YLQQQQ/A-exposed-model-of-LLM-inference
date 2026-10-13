param([Parameter(Mandatory=$true)][string]$PackageRoot)
$ErrorActionPreference = 'Stop'
$PackageRoot = [IO.Path]::GetFullPath($PackageRoot)
$ConfigPath = Join-Path $PackageRoot 'config.json'
$Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Config.schema_version -ne 'exposedpath-native-vs-check/0.1.0' -or
    $Config.model_process_budget -ne 0 -or $Config.profile_budget -ne 0) { throw 'Invalid inspection role/budget' }
if ((Test-Path -LiteralPath $Config.output_root) -or (Test-Path -LiteralPath $Config.return_zip)) {
    throw 'No overwrite/resume/retry'
}
$Worker = Join-Path $PackageRoot 'native_vs_precheck.py'
$Bootstrap = Join-Path $PackageRoot 'native_stage1.py'
if ((Get-FileHash -LiteralPath $Worker -Algorithm SHA256).Hash -ne $Config.worker_sha256 -or
    (Get-FileHash -LiteralPath $Bootstrap -Algorithm SHA256).Hash -ne $Config.bootstrap_sha256) {
    throw 'Inspector/bootstrap content conflict'
}
# Inspect only: no DevShell changes, configure/build, CUDA, model or installer.
& $Config.base_python -I $Worker inspect --config $ConfigPath --package $PackageRoot --root $Config.output_root
$InspectExit = $LASTEXITCODE
if (-not (Test-Path -LiteralPath $Config.output_root)) { throw 'Inspection stopped before output creation; preserve console error' }
& $Config.base_python -I $Bootstrap pack --root $Config.output_root --archive $Config.return_zip
if ($LASTEXITCODE -ne 0) { throw 'Diagnostic packaging failed; preserve new root; no retry' }
Write-Host ('RETURN_ZIP='+$Config.return_zip)
Write-Host ('ZIP_BYTES='+(Get-Item -LiteralPath $Config.return_zip).Length)
Write-Host ('ZIP_SHA256='+(Get-FileHash -LiteralPath $Config.return_zip -Algorithm SHA256).Hash)
Write-Host ('INSPECT_EXIT='+$InspectExit)
Write-Host 'STOP for facts review. Do not run stage1/precheck automatically.'
if ($InspectExit -ne 0) { throw 'Read-only inspection BLOCKED; return diagnostic ZIP; no retry' }
