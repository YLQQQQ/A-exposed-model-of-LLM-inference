# One-shot archived duplicate removal. No recursion, process query or experiment.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$SourceRoot,
    [Parameter(Mandatory=$true)][string]$Archive,
    [Parameter(Mandatory=$true)][string]$CandidateCsv,
    [Parameter(Mandatory=$true)][string]$ForensicReceipt,
    [Parameter(Mandatory=$true)][string]$InventoryRoot,
    [Parameter(Mandatory=$true)][string]$ReceiptDirectory,
    [Parameter(Mandatory=$true)][string]$ArchiveSHA256,
    [Parameter(Mandatory=$true)][string]$ManifestSHA256,
    [Parameter(Mandatory=$true)][string]$CandidatesSHA256,
    [Parameter(Mandatory=$true)][string]$ForensicReceiptSHA256,
    [switch]$Apply,
    [switch]$NoActiveAnalysisConfirmed
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0
Add-Type -AssemblyName System.IO.Compression
function Require([bool]$OK, [string]$Reason) { if (-not $OK) { throw ('CLEANUP_' + $Reason) } }
function Full([string]$Path) {
    Require ([IO.Path]::IsPathRooted($Path)) ('NON_ABSOLUTE_PATH:' + $Path)
    return [IO.Path]::GetFullPath($Path).TrimEnd('\')
}
function Inside([string]$Path, [string]$Root) {
    return $Path.Equals($Root, [StringComparison]::OrdinalIgnoreCase) -or
        $Path.StartsWith($Root + '\', [StringComparison]::OrdinalIgnoreCase)
}
function NoReparse([string]$Path) {
    $Cursor = Full $Path
    while ($Cursor) {
        if (Test-Path -LiteralPath $Cursor) {
            Require (((Get-Item -LiteralPath $Cursor -Force).Attributes -band
                [IO.FileAttributes]::ReparsePoint) -eq 0) ('REPARSE:' + $Cursor)
        }
        $Parent = [IO.Path]::GetDirectoryName($Cursor)
        if ($Parent -eq $Cursor) { break }
        $Cursor = $Parent
    }
}
function HashStream([IO.Stream]$Stream) {
    $SHA = [Security.Cryptography.SHA256]::Create()
    try { return ([BitConverter]::ToString($SHA.ComputeHash($Stream))).Replace('-', '').ToLowerInvariant() }
    finally { $SHA.Dispose() }
}
function HashFile([string]$Path) {
    $Stream = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    try { return HashStream $Stream } finally { $Stream.Dispose() }
}
function ReadText([IO.Stream]$Stream) {
    $Reader = New-Object IO.StreamReader($Stream, (New-Object Text.UTF8Encoding($false,$true)))
    try { return $Reader.ReadToEnd() } finally { $Reader.Dispose() }
}
function InventoryIssues([string]$Root) {
    # Bounded existing inventory only. Supported shapes are explicit; unknown => STOP.
    NoReparse $Root
    $Results = New-Object Collections.Generic.List[object]
    foreach ($File in @(Get-ChildItem -LiteralPath $Root -File | Sort-Object Name)) {
        if ($File.Name -notmatch '(?i)(error|issue|skip)' -and $File.Name -ne 'summary.json') { continue }
        NoReparse $File.FullName
        Require ($File.Length -le 1048576) ('INVENTORY_REPORT_TOO_LARGE:' + $File.Name)
        $Rows = @()
        if ($File.Extension -eq '.csv') { $Rows = @(Import-Csv -LiteralPath $File.FullName -Encoding UTF8) }
        elseif ($File.Extension -eq '.json') {
            $Value = Get-Content -LiteralPath $File.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($Value -is [Array]) { $Rows = @($Value) }
            else {
                foreach ($Key in @('errors','issues','skipped')) {
                    $Property = $Value.PSObject.Properties[$Key]
                    if ($null -ne $Property -and $Property.Value -is [Array]) { $Rows += @($Property.Value) }
                }
            }
        } else { continue }
        foreach ($Row in $Rows) {
            $P = $null; $E = $null
            foreach ($Key in @('path','full_path','FullName')) {
                if ($null -ne $Row.PSObject.Properties[$Key]) { $P = [string]$Row.$Key; break }
            }
            foreach ($Key in @('error','message','reason')) {
                if ($null -ne $Row.PSObject.Properties[$Key]) { $E = [string]$Row.$Key; break }
            }
            Require (-not [string]::IsNullOrWhiteSpace($P) -and -not [string]::IsNullOrWhiteSpace($E)) 'INVENTORY_ISSUE_SCOPE_UNKNOWN'
            $Results.Add([ordered]@{path=(Full $P); error=$E; report=$File.FullName; report_sha256=(HashFile $File.FullName)})
        }
    }
    Require ($Results.Count -eq 2) ('INVENTORY_TWO_ISSUES_NOT_IDENTIFIED:' + $Results.Count)
    return $Results.ToArray()
}

$SourceRoot = Full $SourceRoot; $Archive = Full $Archive
$CandidateCsv = Full $CandidateCsv; $ForensicReceipt = Full $ForensicReceipt
$InventoryRoot = Full $InventoryRoot; $ReceiptDirectory = Full $ReceiptDirectory
Require (-not (Inside $ReceiptDirectory $SourceRoot)) 'RECEIPT_INSIDE_ORIGINAL'
NoReparse $ReceiptDirectory
Require (-not (Test-Path -LiteralPath $ReceiptDirectory)) 'NO_OVERWRITE_RESUME_RETRY'
New-Item -ItemType Directory -Path $ReceiptDirectory | Out-Null
$ReportFile = Join-Path $ReceiptDirectory 'cleanup_receipt.json'
$Report = [ordered]@{version='gate13-archived-domain-cleanup/0.1'; started_utc=[DateTime]::UtcNow.ToString('o');
    status='PRECHECK'; error=$null; source=$SourceRoot; archive=$Archive; archive_sha256=$ArchiveSHA256;
    manifest_sha256=$ManifestSHA256; forensic_receipt_sha256=$ForensicReceiptSHA256; candidates_sha256=$CandidatesSHA256;
    original_reports_modified=$false; historical_writer_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY';
    absence_of_all_writers_proven=$false; no_active_analysis_operator_confirmation=[bool]$NoActiveAnalysisConfirmed;
    deleted_count=0; deleted_bytes=[long]0; targets=@(); inventory_issues=@(); remaining_count=30}
function SaveReport { [IO.File]::WriteAllText($ReportFile, ($Report | ConvertTo-Json -Depth 10), (New-Object Text.UTF8Encoding($false))) }
$Handles = New-Object Collections.Generic.List[object]
$ArchiveStream = $null; $Zip = $null
try {
    SaveReport
    Require (-not $Apply -or $NoActiveAnalysisConfirmed) 'CONFIRM_CURRENT_ANALYSIS_AND_COLLECTION_STOPPED'
    foreach ($Path in @($SourceRoot,$Archive,$CandidateCsv,$ForensicReceipt,$InventoryRoot)) {
        NoReparse $Path
        Require (Test-Path -LiteralPath $Path) ('MISSING_INPUT:' + $Path)
    }
    foreach ($Path in @($Archive,$CandidateCsv,$ForensicReceipt,$InventoryRoot)) {
        Require (-not (Inside $Path $SourceRoot)) ('CONTROL_OR_ARCHIVE_INSIDE_ORIGINAL:' + $Path)
    }
    Require ((HashFile $CandidateCsv) -eq $CandidatesSHA256) 'CANDIDATES_HASH'
    $Rows = @(Import-Csv -LiteralPath $CandidateCsv -Encoding UTF8)
    Require ($Rows.Count -eq 30) 'EXACT_THIRTY_TARGETS_REQUIRED'
    $Report.targets = @($Rows | ForEach-Object {
        [ordered]@{path=[string]$_.server_absolute_path; archive_member=[string]$_.archive_member;
            expected_bytes=[string]$_.bytes; expected_sha256=[string]$_.sha256;
            actual_bytes=$null; actual_sha256=$null; status='NOT_YET_CHECKED'}
    })
    SaveReport
    Require ((HashFile $ForensicReceipt) -eq $ForensicReceiptSHA256) 'FORENSIC_RECEIPT_HASH'
    $Old = Get-Content -LiteralPath $ForensicReceipt -Raw -Encoding UTF8 | ConvertFrom-Json
    Require ($Old.status -eq 'FORENSIC_BYTE_COPY_VERIFIED_NOT_ACCEPTANCE' -and $null -eq $Old.error) 'FORENSIC_RECEIPT_TERMINAL'
    # Legacy receipt escaped each separator twice. Normalize locator only; receipt bytes remain pinned.
    Require ((Full $Old.source.Replace('\\','\')) -eq $SourceRoot -and
             (Full $Old.archive.Replace('\\','\')) -eq $Archive) 'FORENSIC_RECEIPT_PATH_BINDING'
    Require ($Old.archive_sha256 -eq $ArchiveSHA256 -and $Old.manifest_sha256 -eq $ManifestSHA256 -and
             $Old.archive_length -eq (Get-Item -LiteralPath $Archive).Length) 'FORENSIC_RECEIPT_ARCHIVE_BINDING'
    $Report.inventory_issues = @(InventoryIssues $InventoryRoot)
    $ArchiveStream = [IO.File]::Open($Archive, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
    Require ((HashStream $ArchiveStream) -eq $ArchiveSHA256) 'ARCHIVE_BYTES_CHANGED'
    $ArchiveStream.Position = 0
    $Zip = New-Object IO.Compression.ZipArchive($ArchiveStream, [IO.Compression.ZipArchiveMode]::Read, $true)
    $Members = @{}
    foreach ($Entry in $Zip.Entries) {
        Require ($Entry.FullName -notmatch '(^/|\\|(^|/)\.\.(/|$)|^[A-Za-z]:)') 'ARCHIVE_UNSAFE_PATH'
        Require (-not $Members.ContainsKey($Entry.FullName)) 'ARCHIVE_DUPLICATE_MEMBER'
        $Members[$Entry.FullName] = $Entry
    }
    Require ($Members.ContainsKey('forensic_manifest.json')) 'ARCHIVE_MANIFEST_MISSING'
    $Stream = $Members['forensic_manifest.json'].Open()
    try { Require ((HashStream $Stream) -eq $ManifestSHA256) 'ARCHIVE_MANIFEST_HASH' } finally { $Stream.Dispose() }
    $Manifest = ReadText ($Members['forensic_manifest.json'].Open()) | ConvertFrom-Json
    Require ($Manifest.version -eq 'gate13-forensic-byte-copy/0.1') 'ARCHIVE_MANIFEST_VERSION'
    $Index = @{}
    foreach ($Entry in $Manifest.entries) {
        Require (-not $Index.ContainsKey($Entry.path)) 'MANIFEST_DUPLICATE_MEMBER'
        $Index[$Entry.path] = $Entry
    }
    $Seen = @{}
    $TargetOrdinal = 0
    foreach ($Row in $Rows) {
        $Target = $Report.targets[$TargetOrdinal]; $TargetOrdinal++
        $Relative = [string]$Row.server_relative_path
        Require ($Relative -match '^batch/formal-99f3bae966f2-20261010-sixblock-b[1-6]-(G32|G512|N0|Nm|N16)-pass1/collection/analyzed/domain\.json$') 'TARGET_OUTSIDE_CLOSED_ALLOWLIST'
        Require (-not $Seen.ContainsKey($Relative)) 'DUPLICATE_TARGET'
        $Seen[$Relative] = $true
        $Path = Full $Row.server_absolute_path
        Require ((Inside $Path $SourceRoot) -and $Path -eq (Full (Join-Path $SourceRoot $Relative))) 'TARGET_PATH_CONFLICT'
        NoReparse $Path
        Require (Test-Path -LiteralPath $Path -PathType Leaf) ('TARGET_MISSING:' + $Path)
        $Member = 'source/' + $Relative
        Require ($Row.archive_member -eq $Member -and $Row.classification -eq 'EXACT_ARCHIVED_DERIVED_COPY') 'TARGET_ARCHIVE_ROLE'
        Require ($Members.ContainsKey($Member) -and $Index.ContainsKey($Member)) 'TARGET_NOT_IN_ARCHIVE'
        $ExpectedLength = [long]$Row.bytes; $ExpectedHash = [string]$Row.sha256
        Require ($ExpectedLength -gt 0 -and $ExpectedHash -cmatch '^[a-f0-9]{64}$') 'TARGET_IDENTITY_FORMAT'
        Require ($Index[$Member].length -eq $ExpectedLength -and $Index[$Member].sha256 -eq $ExpectedHash -and
                 $Members[$Member].Length -eq $ExpectedLength) 'TARGET_ARCHIVE_IDENTITY'
        $Target.path = $Path; $Target.expected_bytes = $ExpectedLength; $Target.status = 'PRECHECK_PENDING'
        $Stream = $Members[$Member].Open()
        try { Require ((HashStream $Stream) -eq $ExpectedHash) ('ARCHIVE_TARGET_BYTES:' + $Member) } finally { $Stream.Dispose() }
        # Deny concurrent write/delete while ALL candidate prechecks complete.
        $File = [IO.File]::Open($Path, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::Read)
        $Handles.Add($File)
        $Target.actual_bytes = $File.Length; $Target.actual_sha256 = HashStream $File
        Require ($Target.actual_bytes -eq $ExpectedLength -and $Target.actual_sha256 -eq $ExpectedHash) ('TARGET_BYTES_CHANGED:' + $Path)
        $Target.status = 'PRECHECK_PASS'
        Write-Output ('PRECHECK ' + $TargetOrdinal + '/30 ' + $Relative)
    }
    foreach ($Issue in $Report.inventory_issues) {
        $Related = @($Report.targets | Where-Object { (Inside $_.path $Issue.path) -or (Inside $Issue.path $_.path) })
        $Issue['candidate_matches'] = @($Related | ForEach-Object { $_.path })
        $Issue['disposition'] = if ($Related.Count) { 'ONLY_NAMED_TARGETS_RESOLVED_BY_DIRECT_LOCKED_BYTE_CHECK' } else { 'OUTSIDE_TARGET_SCOPE_NOT_CHANGED' }
    }
    $Report.status = 'PRECHECK_PASS_NO_DELETION'; SaveReport
    if ($Apply) {
        for ($I=0; $I -lt $Report.targets.Count; $I++) {
            $Target = $Report.targets[$I]
            NoReparse $Target.path
            $Target.status = 'DELETE_PENDING'; SaveReport
            $Handles[$I].Dispose()
            Require ((Get-Item -LiteralPath $Target.path).Length -eq $Target.expected_bytes -and
                     (HashFile $Target.path) -eq $Target.expected_sha256) ('TARGET_CHANGED_BEFORE_DELETE:' + $Target.path)
            Remove-Item -LiteralPath $Target.path -ErrorAction Stop
            Require (-not (Test-Path -LiteralPath $Target.path)) 'DELETE_NOT_CONFIRMED'
            $Target.status = 'DELETED'; $Report.deleted_count++; $Report.remaining_count--
            $Report.deleted_bytes += $Target.expected_bytes
            SaveReport
        }
        $Report.status = 'CLEANED_ARCHIVED_DERIVED_COPIES'
        $Report['recovery'] = 'Original bytes remain at archive_member in the pinned, retained ZIP; expanded source is no longer a complete copy.'
    }
} catch {
    $Report.status = 'STOPPED'; $Report.error = $_.Exception.ToString()
    throw
} finally {
    foreach ($Handle in $Handles) { $Handle.Dispose() }
    if ($null -ne $Zip) { $Zip.Dispose() }
    if ($null -ne $ArchiveStream) { $ArchiveStream.Dispose() }
    $Report['ended_utc'] = [DateTime]::UtcNow.ToString('o')
    $Report['not_deleted_paths'] = @($Report.targets | Where-Object { $_.status -ne 'DELETED' } | ForEach-Object { $_.path })
    SaveReport
    Write-Output ('CLEANUP_RECEIPT: ' + $ReportFile)
}
