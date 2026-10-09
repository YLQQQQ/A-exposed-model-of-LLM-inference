param([Parameter(Mandatory=$true)][string]$PlanPath,[switch]$DeleteReviewedFiles)
# Only AFTER batch review and archive verification. No recursive directory delete.
$ErrorActionPreference='Stop'
# Pin built-in modules to this PowerShell, including when a Python caller
# inherits a different PowerShell version's PSModulePath.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management\Microsoft.PowerShell.Management.psd1') -ErrorAction Stop
$P=Get-Content -LiteralPath $PlanPath -Raw | ConvertFrom-Json
if ($P.schema_version -ne 'gate13-reviewed-cleanup-plan/0.1' -or $P.automatic_delete -ne $false -or $P.raw_delete -ne $false -or $P.review.status -ne 'BATCH_REVIEWED_ARCHIVE_VERIFIED') {throw 'Unreviewed cleanup plan'}
$Root=[IO.Path]::GetFullPath($P.root).TrimEnd('\')+'\'
function CheckPathChain([string]$Path) {
    # Include the allowed root itself and its ancestors: a replaced root or
    # ancestor junction must not redirect even byte-identical archived files.
    $Current=[IO.Path]::GetFullPath($Path)
    while ($Current) {
        if ((Get-Item -LiteralPath $Current).Attributes -band [IO.FileAttributes]::ReparsePoint) {throw 'Reparse path chain'}
        $Parent=Split-Path -Parent $Current
        if (!$Parent -or $Parent -eq $Current) {break}
        $Current=$Parent
    }
}
CheckPathChain $Root.TrimEnd('\')
if (Test-Path -LiteralPath (Join-Path $Root '.active')) {throw 'Active writer; never clean'}
if ((Get-FileHash -LiteralPath $P.archive).Hash -ne $P.archive_sha256 -or $P.archive_sha256 -ne $P.review.archive_sha256) {throw 'Archive changed'}
$Seen=@{};$Rows=@()
foreach ($F in $P.files) {
    $Path=[IO.Path]::GetFullPath((Join-Path $Root $F.path))
    if ([IO.Path]::IsPathRooted($F.path) -or !$Path.StartsWith($Root,[StringComparison]::OrdinalIgnoreCase) -or $Seen.ContainsKey($Path)) {throw 'Unsafe/duplicate path'}
    if ($F.path -notmatch '/collection/analyzed/(canonical/(nvtx|cuda_api|cuda_sync|device_activity|cuda_event|context|stream|diagnostic)\.jsonl\.gz|projection/scope\.json)$') {throw 'Not an approved reconstructible intermediate'}
    $Seen[$Path]=$true
    CheckPathChain $Path
    $I=Get-Item -LiteralPath $Path
    if (($I.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $I.Length -ne [long]$F.bytes -or (Get-FileHash -LiteralPath $Path).Hash -ne $F.sha256) {throw 'Current file identity conflict'}
    $Rows+=[ordered]@{path=$Path;bytes=$I.Length;sha256=$F.sha256;archive_member=$F.path;deleted=$false}
}
$Rows | Format-Table
if (!$DeleteReviewedFiles) {Write-Host 'DRY RUN ONLY; no deletion';exit 0}
$Receipt=$PlanPath+'.cleanup_receipt.json'
if (Test-Path -LiteralPath $Receipt) {throw 'Receipt already exists; no repeat'}
function SaveReceipt { [ordered]@{plan_sha256=(Get-FileHash -LiteralPath $PlanPath).Hash;archive=$P.archive;archive_sha256=$P.archive_sha256;review=$P.review;recoverable_from_archive=$true;files=$Rows} | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Receipt -Encoding utf8 }
SaveReceipt
try {
    foreach ($F in $Rows) {
        CheckPathChain $F.path
        if (Test-Path -LiteralPath (Join-Path $Root '.active')) {throw 'Writer became active'}
        $Current=Get-Item -LiteralPath $F.path
        if (($Current.Attributes -band [IO.FileAttributes]::ReparsePoint) -or $Current.Length -ne $F.bytes -or (Get-FileHash -LiteralPath $F.path).Hash -ne $F.sha256) {throw 'File changed after plan validation'}
        Remove-Item -LiteralPath $F.path
        $F.deleted=$true;SaveReceipt
    }
} finally {SaveReceipt}
Write-Host ('CLEANUP_RECEIPT='+$Receipt)
