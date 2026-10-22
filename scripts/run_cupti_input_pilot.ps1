param(
    [switch]$RunReviewedPilot,
    [string]$ReviewedStaticSha256,
    [string]$ReviewedAReceiptSha256,
    [string]$ReviewedEventReceiptSha256
)
$ErrorActionPreference='Stop'
function ExactSHA([string]$Path) {
    $InputFile=[IO.File]::OpenRead($Path)
    $Digest=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($Digest.ComputeHash($InputFile))).Replace('-','').ToLowerInvariant()}
    finally {$Digest.Dispose();$InputFile.Dispose()}
}
$Config=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Config.schema_version -ne 'CUPTI-INPUT-PILOT/0.1.0') {throw 'Pilot version conflict; STOP'}
$Seen=@{}
foreach ($Item in $Config.bootstrap_files) {
    $Name=[string]$Item.path
    if ($Name -notmatch '^[a-zA-Z0-9_.-]+$' -or $Seen.ContainsKey($Name.ToLowerInvariant())) {throw 'Bootstrap path conflict; STOP'}
    $Seen[$Name.ToLowerInvariant()]=$true
    if ((ExactSHA (Join-Path $PSScriptRoot $Name)) -ne $Item.sha256) {throw 'Bootstrap byte conflict; STOP'}
}
$Arguments=@('--package',$PSScriptRoot)
if ($RunReviewedPilot) {
    if ($ReviewedStaticSha256 -notmatch '^[a-fA-F0-9]{64}$' -or
        $ReviewedAReceiptSha256 -ine $Config.reviewed_a_receipt_sha256 -or
        $ReviewedEventReceiptSha256 -ine $Config.reviewed_event_receipt_sha256) {
        throw 'All reviewed receipt identities required; STOP'
    }
    $Arguments+=@('--run-reviewed-pilot','--reviewed-static-sha256',$ReviewedStaticSha256.ToLowerInvariant(),
        '--reviewed-a-receipt-sha256',$ReviewedAReceiptSha256.ToLowerInvariant(),
        '--reviewed-event-receipt-sha256',$ReviewedEventReceiptSha256.ToLowerInvariant())
} elseif ($ReviewedStaticSha256 -or $ReviewedAReceiptSha256 -or $ReviewedEventReceiptSha256) {
    throw 'Static default and collection arguments conflict; STOP'
}
& $Config.python -I -B -X utf8 (Join-Path $PSScriptRoot 'cupti_input_pilot.py') @Arguments
if ($LASTEXITCODE -ne 0) {throw 'Stopped; preserve returned diagnostic/scene; no retry/resume/cleanup'}
