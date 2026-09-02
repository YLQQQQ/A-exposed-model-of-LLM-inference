<#
.SYNOPSIS
    [LEGACY — use run_wmpc_pilot.ps1 per-manifest instead]
    Run nsys profile for every workload in a YAML matrix.

.DESCRIPTION
    LEGACY SCRIPT: This iterates over a workload YAML and calls run_nsys_single.ps1.
    For new Pilot runs, use run_wmpc_pilot.ps1 with individual WMPC manifests.
    This script is kept for backward compatibility only.
    Reads a workload YAML file and runs run_nsys_single.ps1 for each entry.
    Failures in one workload do NOT stop the remaining ones.

.PARAMETER ModelPath
    Path to local model directory.

.PARAMETER WorkloadYaml
    Path to workload YAML file.

.PARAMETER OutputRoot
    Root directory for all nsys outputs.

.PARAMETER WarmupIters
    Number of warmup iterations per workload.

.PARAMETER RepeatIters
    Number of benchmark repeats per workload.

.PARAMETER Gpu
    GPU device ID.

.EXAMPLE
    .\scripts\run_nsys_matrix.ps1 `
        -ModelPath "D:\models\Qwen2.5-3B-Instruct" `
        -WorkloadYaml "configs\workloads_test.yaml" `
        -OutputRoot "nsys_results"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ModelPath,

    [Parameter(Mandatory=$true)]
    [string]$WorkloadYaml,

    [Parameter(Mandatory=$true)]
    [string]$OutputRoot,

    [int]$WarmupIters = 5,

    [int]$RepeatIters = 10,

    [int]$Gpu = 0,

    [switch]$Streaming,

    [switch]$Reverse
)

# ---- Resolve paths ----
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $ScriptDir
$NsysSingleScript = Join-Path $ScriptDir "run_nsys_single.ps1"
$BenchScript = Join-Path $ProjectDir "bench_eager.py"

$Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$MatrixDir = Join-Path $OutputRoot "nsys_matrix_$Timestamp"

Write-Host "============================================"
Write-Host "[run_nsys_matrix] NSYS Profiling Matrix"
Write-Host "============================================"
Write-Host "  Project dir:     $ProjectDir"
Write-Host "  Model path:      $ModelPath"
Write-Host "  Workload YAML:   $WorkloadYaml"
Write-Host "  Output root:     $MatrixDir"
Write-Host ""

# ---- Create output directory ----
New-Item -ItemType Directory -Force -Path $MatrixDir | Out-Null

# ---- Read workload YAML using Python (robust YAML parsing) ----
$YamlPath = $WorkloadYaml -replace '\\', '/'
$WorkloadsJson = python -c "import yaml,json,sys; data=yaml.safe_load(open('$YamlPath','r',encoding='utf-8')); workloads=data.get('workloads',[]); print(json.dumps(workloads))"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[run_nsys_matrix] ERROR: Failed to parse YAML file: $WorkloadYaml"
    exit 1
}

$Workloads = $WorkloadsJson | ConvertFrom-Json
$Total = $Workloads.Count

# ---- Reverse order if requested ----
if ($Reverse) {
    [Array]::Reverse($Workloads)
    Write-Host "[run_nsys_matrix] Reverse order enabled — workloads reversed"
}

Write-Host "[run_nsys_matrix] Loaded $Total workload(s)"
Write-Host ""

# ---- Pre-flight check: verify bench_eager.py works before running full matrix ----
Write-Host "============================================"
Write-Host "[run_nsys_matrix] PRE-FLIGHT CHECK"
Write-Host "============================================"
$FirstWorkload = $Workloads[0]
$PyExe = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $PyExe) { $PyExe = "python" }
$PreFlightArgs = @(
    $BenchScript,
    "--model-path", $ModelPath,
    "--batch-size", $FirstWorkload.batch_size,
    "--output-len", $FirstWorkload.output_len,
    "--warmup-iters", 0,
    "--repeat-iters", 1,
    "--gpu", $Gpu,
    "--output-dir", $MatrixDir
)
if ($FirstWorkload.prompt) {
    $PreFlightArgs += @("--prompt", $FirstWorkload.prompt)
} elseif ($FirstWorkload.prompt_len) {
    $PreFlightArgs += @("--prompt-len", $FirstWorkload.prompt_len)
}
if ($Streaming) {
    $PreFlightArgs += "--streaming"
}

Write-Host "  Running: $PyExe $($PreFlightArgs -join ' ')"
Write-Host "  (Quick sanity check before launching full nsys matrix...)"
$PreFlightOut = & $PyExe $PreFlightArgs 2>&1
$PreFlightRC = $LASTEXITCODE

if ($PreFlightRC -ne 0) {
    Write-Host ""
    Write-Host "============================================"
    Write-Host "  PRE-FLIGHT CHECK FAILED (exit code: $PreFlightRC)"
    Write-Host "  bench_eager.py crashed before any nsys profiling."
    Write-Host "  Fix the error below, then re-run the matrix."
    Write-Host "============================================"
    Write-Host ""
    Write-Host "--- bench_eager.py output ---"
    $PreFlightOut | ForEach-Object { Write-Host "  $_" }
    Write-Host "--- end ---"
    Write-Host ""
    Write-Host "Common causes:"
    Write-Host "  1. Model path does not exist: $ModelPath"
    Write-Host "  2. PyTorch not installed with CUDA support"
    Write-Host "  3. GPU $Gpu not available or insufficient VRAM"
    Write-Host "  4. Missing Python dependencies (transformers, accelerate, etc.)"
    exit 1
}

Write-Host "  PRE-FLIGHT CHECK PASSED"
Write-Host ""

# ---- Run each workload ----
$Succeeded = @()
$Failed = @()

for ($i = 0; $i -lt $Total; $i++) {
    $w = $Workloads[$i]
    $Idx = $i + 1

    Write-Host "=" * 60
    Write-Host "[run_nsys_matrix] Workload $Idx / $Total : $($w.id)"
    Write-Host "[run_nsys_matrix]   prompt_len=$($w.prompt_len), batch_size=$($w.batch_size), output_len=$($w.output_len)"
    Write-Host "=" * 60

    $RunOutDir = Join-Path $MatrixDir $w.id

    $StartTime = Get-Date

    # Call run_nsys_single.ps1
    $NsysArgs = @(
        "-ModelPath", $ModelPath,
        "-PromptLen", $w.prompt_len,
        "-BatchSize", $w.batch_size,
        "-OutputLen", $w.output_len,
        "-OutDir", $RunOutDir,
        "-RunName", $w.id,
        "-WarmupIters", $WarmupIters,
        "-RepeatIters", $RepeatIters,
        "-Gpu", $Gpu,
        "-ProjectDir", $ProjectDir
    )
    if ($Streaming) {
        $NsysArgs += "-Streaming"
    }

    & powershell -ExecutionPolicy Bypass -File "$NsysSingleScript" @NsysArgs
    $ExitCode = $LASTEXITCODE

    $Elapsed = ((Get-Date) - $StartTime).TotalSeconds

    if ($ExitCode -eq 0) {
        Write-Host "[run_nsys_matrix] $($w.id): SUCCESS ($([math]::Round($Elapsed, 1))s)"
        $Succeeded += @{
            id = $w.id
            elapsed_s = [math]::Round($Elapsed, 1)
            output_dir = $RunOutDir
        }
    } else {
        Write-Host "[run_nsys_matrix] $($w.id): FAILED (rc=$ExitCode, $([math]::Round($Elapsed, 1))s)"
        $Failed += @{
            id = $w.id
            returncode = $ExitCode
            elapsed_s = [math]::Round($Elapsed, 1)
            output_dir = $RunOutDir
        }
    }

    Write-Host ""
}

# ---- Summary ----
Write-Host "=" * 60
Write-Host "[run_nsys_matrix] MATRIX COMPLETE"
Write-Host "  Succeeded: $($Succeeded.Count) / $Total"
Write-Host "  Failed:    $($Failed.Count) / $Total"
Write-Host "=" * 60

$MatrixSummary = @{
    timestamp = $Timestamp
    workload_file = (Resolve-Path $WorkloadYaml).Path
    model_path = $ModelPath
    total = $Total
    succeeded_count = $Succeeded.Count
    failed_count = $Failed.Count
    succeeded = $Succeeded
    failed = $Failed
}

$SummaryPath = Join-Path $MatrixDir "nsys_matrix_summary.json"
$MatrixSummary | ConvertTo-Json -Depth 4 | Out-File -FilePath $SummaryPath -Encoding utf8
Write-Host "[run_nsys_matrix] Summary: $SummaryPath"

if ($Failed.Count -gt 0) {
    $FailedPath = Join-Path $MatrixDir "nsys_failed_workloads.json"
    $Failed | ConvertTo-Json -Depth 3 | Out-File -FilePath $FailedPath -Encoding utf8
    Write-Host "[run_nsys_matrix] Failed list: $FailedPath"
}

Write-Host "[run_nsys_matrix] Done."
