<#
.SYNOPSIS
    One-click: exposed accounting on all .sqlite + matrix summary (v2).
    Accepts either the timestamp directory or the parent (auto-finds timestamp).

.PARAMETER ResultsDir
    Root or timestamp directory containing workload subdirectories with .sqlite files.

.PARAMETER DebugOutput
    Pass --debug to exposed_accounting.py for extra debug info.

.PARAMETER Force
    Overwrite existing accounting output directories.

.PARAMETER Strict
    Exit non-zero if any workload fails.
#>
param(
    [Parameter(Mandatory=$true)]
    [string]$ResultsDir,

    [switch]$DebugOutput,

    [switch]$Force,

    [switch]$Strict
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$AccountingPy = Join-Path $ProjectDir "analysis\exposed_accounting.py"
$SummarizePy = Join-Path $ProjectDir "analysis\summarize_matrix.py"

# ---- Resolve work dir (auto-find timestamp subdir if needed) ----
$WorkDir = $ResultsDir
$SqliteFiles = @(Get-ChildItem -Path $WorkDir -Recurse -Filter "*.sqlite" -File -ErrorAction SilentlyContinue)
if (@($SqliteFiles).Count -eq 0) {
    # Try to find a timestamp subdirectory
    $Subs = @(Get-ChildItem -Path $WorkDir -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -match '^\d{8}_\d{6}$' -or $_.Name -like 'nsys_matrix_*' } |
        Sort-Object Name -Descending)
    if ($Subs.Count -gt 0) {
        $WorkDir = $Subs[0].FullName
        Write-Host "Auto-detected timestamp dir: $WorkDir"
    }
}

$SqliteFiles = @(Get-ChildItem -Path $WorkDir -Recurse -Filter "*.sqlite" -File -ErrorAction SilentlyContinue)
if ($SqliteFiles.Count -eq 0) {
    Write-Host "ERROR: No .sqlite files found under $WorkDir"
    Write-Host "  Run export_nsys_sqlite.ps1 or run_nsys_matrix.ps1 first."
    exit 1
}

# Determine the common parent (timestamp dir)
$FirstParent = $SqliteFiles[0].Directory.Parent
if ($FirstParent) {
    $WorkDir = $FirstParent.FullName
}
Write-Host "============================================"
Write-Host "[batch] Exposed Accounting v2 (exposedpath-v2)"
Write-Host "============================================"
Write-Host "  Work dir: $WorkDir"
Write-Host "  Found $($SqliteFiles.Count) .sqlite file(s)"
Write-Host "  Force: $Force"
Write-Host "  Strict: $Strict"
Write-Host ""

# ===== Step 1: Accounting =====
Write-Host "============================================"
Write-Host "[batch] Step 1/2: Exposed Accounting"
Write-Host "============================================"

$OK = 0; $Fail = 0; $Total = $SqliteFiles.Count
$FailedWorkloads = @()
$LogLines = @()

foreach ($i in 0..($Total - 1)) {
    $f = $SqliteFiles[$i]
    $Idx = $i + 1
    $OutDir = Join-Path $f.DirectoryName "accounting"

    Write-Host "[$Idx/$Total] $($f.BaseName)"

    # Check if accounting already exists
    if ((Test-Path $OutDir) -and -not $Force) {
        $existingResult = Join-Path $OutDir "accounting_result.json"
        if (Test-Path $existingResult) {
            Write-Host "  SKIP (accounting already exists, use -Force to overwrite)"
            $OK++
            $LogLines += "[$Idx/$Total] $($f.BaseName) — SKIP (exists)"
            continue
        }
    }

    if ($Force -and (Test-Path $OutDir)) {
        Remove-Item -Path $OutDir -Recurse -Force -ErrorAction SilentlyContinue
    }

    $PyArgs = @(
        $AccountingPy,
        "--sqlite", $f.FullName,
        "--output-dir", $OutDir
    )
    if ($DebugOutput) {
        $PyArgs += "--debug"
    }

    $StartTime = Get-Date
    & python @PyArgs
    $ExitCode = $LASTEXITCODE
    $Elapsed = ((Get-Date) - $StartTime).TotalSeconds

    if ($ExitCode -eq 0) {
        Write-Host "  OK ($([math]::Round($Elapsed, 1))s)"
        $OK++
        $LogLines += "[$Idx/$Total] $($f.BaseName) — OK ($([math]::Round($Elapsed, 1))s)"
    } else {
        Write-Host "  FAILED (exit code: $ExitCode, $([math]::Round($Elapsed, 1))s)"
        $Fail++
        $FailedWorkloads += @{
            workload = $f.BaseName
            exit_code = $ExitCode
            elapsed_s = [math]::Round($Elapsed, 1)
        }
        $LogLines += "[$Idx/$Total] $($f.BaseName) — FAILED (exit $ExitCode)"
    }
    Write-Host ""
}

Write-Host "  Accounting: $OK/$Total OK, $Fail failed"

if ($FailedWorkloads.Count -gt 0) {
    Write-Host "  Failed workloads:"
    foreach ($fw in $FailedWorkloads) {
        Write-Host "    $($fw.workload) (exit $($fw.exit_code))"
    }
}

# ===== Step 2: Summarize =====
Write-Host ""
Write-Host "============================================"
Write-Host "[batch] Step 2/2: Matrix Summary (exposedpath-v2)"
Write-Host "============================================"

$SummaryJsonPath = Join-Path $WorkDir "matrix_summary.json"
$SummaryCsvPath = Join-Path $WorkDir "matrix_summary.csv"

$SummarizeArgs = @(
    $SummarizePy, $WorkDir, $SummaryJsonPath,
    "--accounting-dir-name", "accounting"
)
if ($Strict) {
    $SummarizeArgs += "--strict"
}

& python @SummarizeArgs
$SummarizeExit = $LASTEXITCODE

if ($SummarizeExit -eq 0) {
    Write-Host "  Summary JSON: $SummaryJsonPath"
    Write-Host "  Summary CSV:  $SummaryCsvPath"
} else {
    Write-Host "  Summarize FAILED (exit code: $SummarizeExit)"
}

# ===== Write log =====
$LogPath = Join-Path $WorkDir "accounting_batch.log"
$LogHeader = @"
============================================
batch_accounting.ps1 v2 (exposedpath-v2)
Work dir: $WorkDir
Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
Found: $Total .sqlite files
OK: $OK
Failed: $Fail
============================================
"@
$LogContent = @($LogHeader) + $LogLines -join "`n"
$LogContent | Out-File -FilePath $LogPath -Encoding utf8
Write-Host "  Log: $LogPath"

# ===== Final summary =====
Write-Host ""
Write-Host "============================================"
Write-Host "  ALL DONE"
Write-Host "  Workloads discovered: $Total"
Write-Host "  Workloads analyzed:   $($OK + $Fail)"
Write-Host "  Workloads succeeded:  $OK"
Write-Host "  Workloads failed:     $Fail"
Write-Host "  matrix_summary.json:  $SummaryJsonPath"
Write-Host "  matrix_summary.csv:   $SummaryCsvPath"
Write-Host "============================================"

if ($Strict -and ($Fail -gt 0 -or $SummarizeExit -ne 0)) {
    exit 1
}

exit 0
