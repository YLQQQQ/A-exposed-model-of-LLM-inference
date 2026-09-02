<#
.SYNOPSIS
    [LEGACY — use run_wmpc_pilot.ps1 per-manifest instead]
    One-click: forward + reverse nsys matrix profiling for both GPUs (6000 Ada + 4090).

.DESCRIPTION
    LEGACY SCRIPT: Master orchestrator for the old run_nsys_matrix.ps1 workflow.
    For new Pilot runs, create individual WMPC manifests and use run_wmpc_pilot.ps1.
    This script is kept for backward compatibility only.
    Runs 4 matrix collections in sequence:
      1. RTX 6000 Ada (GPU 0) — forward order  (w01 → w16)
      2. RTX 6000 Ada (GPU 0) — reverse order  (w16 → w01)
      3. RTX 4090    (GPU 1) — forward order  (w01 → w16)
      4. RTX 4090    (GPU 1) — reverse order  (w16 → w01)

    Each collection: warmup=5, repeat=10, streaming, 16 workloads.
    Total: 4 × 16 = 64 nsys profiles.  Estimated wall-clock: 5-10 hours.

    No sqlite export or accounting is performed — pure nsys collection.

.PARAMETER ModelPath
    Path to local model directory (used for both GPUs).

.PARAMETER ModelPath4090
    Optional separate model path for RTX 4090. Defaults to -ModelPath.

.PARAMETER OutputRoot
    Root directory for all nsys outputs. Subdirectories are created automatically:
      <OutputRoot>/nsys_6000ada_forward_<ts>/
      <OutputRoot>/nsys_6000ada_reverse_<ts>/
      <OutputRoot>/nsys_4090_forward_<ts>/
      <OutputRoot>/nsys_4090_reverse_<ts>/

.PARAMETER WarmupIters
    Number of warmup iterations per workload (default: 5).

.PARAMETER RepeatIters
    Number of benchmark repeats per workload (default: 10).

.PARAMETER Skip6000Ada
    Skip RTX 6000 Ada (GPU 0) collections.

.PARAMETER Skip4090
    Skip RTX 4090 (GPU 1) collections.

.PARAMETER DryRun
    Print what would be executed without actually running.

.EXAMPLE
    # Run all 4 collections (both GPUs, forward + reverse)
    .\scripts\run_all_nsys_matrix.ps1 `
        -ModelPath "D:\models\Qwen2.5-3B-Instruct" `
        -OutputRoot ".\nsys_matrix"

.EXAMPLE
    # 6000 Ada only (forward + reverse)
    .\scripts\run_all_nsys_matrix.ps1 `
        -ModelPath "D:\models\Qwen2.5-3B-Instruct" `
        -OutputRoot ".\nsys_matrix" -Skip4090

.EXAMPLE
    # Dry run — see commands without executing
    .\scripts\run_all_nsys_matrix.ps1 `
        -ModelPath "D:\models\Qwen2.5-3B-Instruct" `
        -OutputRoot ".\nsys_matrix" -DryRun
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ModelPath,

    [string]$ModelPath4090 = "",

    [Parameter(Mandatory=$true)]
    [string]$OutputRoot,

    [int]$WarmupIters = 5,

    [int]$RepeatIters = 10,

    [switch]$Skip6000Ada,

    [switch]$Skip4090,

    [switch]$Streaming,

    [switch]$DryRun
)

# ---- Resolve paths ----
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$MatrixScript = Join-Path $ScriptDir "run_nsys_matrix.ps1"
$Config6000 = Join-Path $ProjectDir "configs\workloads_16group.yaml"
$Config4090 = Join-Path $ProjectDir "configs\workloads_16group_4090.yaml"

if (-not $ModelPath4090) {
    $ModelPath4090 = $ModelPath
}

# ---- Build the 4 job definitions ----
$Jobs = @()

if (-not $Skip6000Ada) {
    $Jobs += @{
        Label     = "RTX 6000 Ada FORWARD"
        Gpu       = 0
        Config    = $Config6000
        Model     = $ModelPath
        Reverse   = $false
    }
    $Jobs += @{
        Label     = "RTX 6000 Ada REVERSE"
        Gpu       = 0
        Config    = $Config6000
        Model     = $ModelPath
        Reverse   = $true
    }
}

if (-not $Skip4090) {
    $Jobs += @{
        Label     = "RTX 4090 FORWARD"
        Gpu       = 1
        Config    = $Config4090
        Model     = $ModelPath4090
        Reverse   = $false
    }
    $Jobs += @{
        Label     = "RTX 4090 REVERSE"
        Gpu       = 1
        Config    = $Config4090
        Model     = $ModelPath4090
        Reverse   = $true
    }
}

# ---- Print plan ----
$TotalJobs = $Jobs.Count
Write-Host ""
Write-Host "=" * 70
Write-Host "  RUN ALL NSYS MATRIX — MASTER PLAN"
Write-Host "=" * 70
Write-Host "  Project dir:    $ProjectDir"
Write-Host "  Model (6000):   $ModelPath"
Write-Host "  Model (4090):   $ModelPath4090"
Write-Host "  Output root:    $OutputRoot"
Write-Host "  Warmup iters:   $WarmupIters"
Write-Host "  Repeat iters:   $RepeatIters"
Write-Host "  Streaming:      $Streaming"
Write-Host "  Total jobs:     $TotalJobs"
Write-Host ""

for ($j = 0; $j -lt $TotalJobs; $j++) {
    $job = $Jobs[$j]
    $Idx = $j + 1
    Write-Host "  [$Idx/$TotalJobs] $($job.Label)"
    Write-Host "    GPU: $($job.Gpu)  |  Config: $(Split-Path -Leaf $job.Config)  |  Reverse: $($job.Reverse)"
}

if ($DryRun) {
    Write-Host ""
    Write-Host "[DRY RUN] No commands executed. Remove -DryRun to run."
    exit 0
}

Write-Host ""
Write-Host "  Estimated total wall-clock: 5-10 hours"
Write-Host "=" * 70
Write-Host ""

# ---- Confirm start ----
$ConfirmStart = Read-Host "Proceed with all $TotalJobs jobs? [Y/n]"
if ($ConfirmStart -and $ConfirmStart -notin @('Y','y','Yes','yes','YES')) {
    Write-Host "Aborted by user."
    exit 0
}

# ---- Run all jobs ----
$MasterStart = Get-Date
$JobResults = @()

for ($j = 0; $j -lt $TotalJobs; $j++) {
    $job = $Jobs[$j]
    $Idx = $j + 1

    Write-Host ""
    Write-Host "#" * 70
    Write-Host "#  JOB [$Idx/$TotalJobs] : $($job.Label)"
    Write-Host "#  Started at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    Write-Host "#" * 70
    Write-Host ""

    $JobStart = Get-Date

    # Build arguments
    $MatrixArgs = @(
        "-ModelPath", $job.Model,
        "-WorkloadYaml", $job.Config,
        "-OutputRoot", $OutputRoot,
        "-WarmupIters", $WarmupIters,
        "-RepeatIters", $RepeatIters,
        "-Gpu", $job.Gpu
    )
    if ($Streaming) {
        $MatrixArgs += "-Streaming"
    }
    if ($job.Reverse) {
        $MatrixArgs += "-Reverse"
    }

    # Execute
    & powershell -ExecutionPolicy Bypass -File "$MatrixScript" @MatrixArgs
    $ExitCode = $LASTEXITCODE

    $JobElapsed = ((Get-Date) - $JobStart).TotalMinutes

    $Result = @{
        Job       = $Idx
        Label     = $job.Label
        ExitCode  = $ExitCode
        Minutes   = [math]::Round($JobElapsed, 1)
    }
    $JobResults += $Result

    if ($ExitCode -eq 0) {
        Write-Host ""
        Write-Host "### JOB [$Idx/$TotalJobs] $($job.Label) — DONE ($([math]::Round($JobElapsed, 1)) min)"
    } else {
        Write-Host ""
        Write-Host "### JOB [$Idx/$TotalJobs] $($job.Label) — FAILED (exit $ExitCode, $([math]::Round($JobElapsed, 1)) min)"
    }
}

# ---- Master summary ----
$MasterElapsed = ((Get-Date) - $MasterStart).TotalMinutes

Write-Host ""
Write-Host "=" * 70
Write-Host "  ALL JOBS COMPLETE"
Write-Host "=" * 70
Write-Host "  Finished at: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Host "  Total wall-clock: $([math]::Round($MasterElapsed, 0)) min ($([math]::Round($MasterElapsed / 60, 1)) hr)"
Write-Host ""

$Succeeded = ($JobResults | Where-Object { $_.ExitCode -eq 0 }).Count
$Failed = ($JobResults | Where-Object { $_.ExitCode -ne 0 }).Count
Write-Host "  Succeeded: $Succeeded / $TotalJobs"
Write-Host "  Failed:    $Failed / $TotalJobs"
Write-Host ""

foreach ($r in $JobResults) {
    $Status = if ($r.ExitCode -eq 0) { "OK" } else { "FAIL (exit $($r.ExitCode))" }
    Write-Host "  [$($r.Job)/$TotalJobs] $($r.Label)"
    Write-Host "    Status: $Status  |  Duration: $($r.Minutes) min"
}

Write-Host ""
Write-Host "  Output file tree:"
Write-Host "    $OutputRoot"
$Subs = @(Get-ChildItem -Path $OutputRoot -Directory -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -like 'nsys_matrix_*' } |
    Sort-Object Name -Descending)
foreach ($s in $Subs) {
    Write-Host "      $($s.Name)/"
}

Write-Host ""
Write-Host "  Next steps (when ready to analyze):"
Write-Host "    .\scripts\export_nsys_sqlite.ps1 -ResultsDir `"<timestamp_dir>`""
Write-Host "    .\scripts\batch_accounting.ps1 -ResultsDir `"<timestamp_dir>`""
Write-Host "=" * 70

exit 0
