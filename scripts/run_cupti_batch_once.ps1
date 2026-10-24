param(
    [ValidateSet('prepare','execute','verify')][string]$Action = 'prepare',
    [Parameter(Mandatory=$true)][string]$PackageManifestSha256,
    [switch]$ApprovePrepare,
    [switch]$ApproveModel,
    [switch]$SharedUseApproved,
    [string]$ReviewedPrepareSha256,
    [string]$ReviewedControlPublication,
    [string]$ReviewedControlPublicationSha256,
    [string]$OperatorReference
)
$ErrorActionPreference = 'Stop'
$Package = $PSScriptRoot
$Index = Join-Path $Package 'package_manifest.json'
if ((Get-FileHash -LiteralPath $Index -Algorithm SHA256).Hash -ne $PackageManifestSha256) {
    throw 'Package manifest conflict; STOP'
}
$Manifest = Get-Content -LiteralPath $Index -Raw -Encoding UTF8 | ConvertFrom-Json
foreach ($Name in @('delivery.json','cupti_batch_once_delivery.py')) {
    $Rows = @($Manifest.files | Where-Object { $_.path -ceq $Name })
    if ($Rows.Count -ne 1) { throw 'Missing/duplicate bootstrap identity; STOP' }
    $Path = Join-Path $Package $Name
    if ((Get-Item -LiteralPath $Path).Length -ne $Rows[0].bytes -or
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Rows[0].sha256) {
        throw 'Bootstrap bytes conflict; STOP'
    }
}
$Config = Get-Content -LiteralPath (Join-Path $Package 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (-not $PSBoundParameters.ContainsKey('Action') -and
    $Config.repair_profile.schema_version -ceq 'cupti-batch-publication-repair/0.1.0') {
    $Action = 'verify'
}
$Argv = @('-I','-S','-B','-X','utf8',(Join-Path $Package 'cupti_batch_once_delivery.py'),$Action,'--package',$Package)
if ($ApprovePrepare) { $Argv += '--approve-prepare' }
if ($ApproveModel) { $Argv += '--approve-model' }
if ($SharedUseApproved) { $Argv += '--shared-use-approved' }
if ($ReviewedPrepareSha256) { $Argv += @('--reviewed-prepare-sha256',$ReviewedPrepareSha256) }
if ($ReviewedControlPublication) { $Argv += @('--reviewed-control-publication',$ReviewedControlPublication) }
if ($ReviewedControlPublicationSha256) { $Argv += @('--reviewed-control-publication-sha256',$ReviewedControlPublicationSha256) }
if ($OperatorReference) { $Argv += @('--operator-reference',$OperatorReference) }
& $Config.python @Argv
$ActualExitCode = $LASTEXITCODE
if ($null -eq $ActualExitCode -or $ActualExitCode -ne 0) {
    throw ('Batch delivery stopped; preserve evidence; no retry/cleanup/automatic execution; exit=' + $ActualExitCode)
}
