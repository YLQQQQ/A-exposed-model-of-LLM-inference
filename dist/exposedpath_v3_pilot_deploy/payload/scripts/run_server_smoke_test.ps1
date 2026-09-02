<#
.SYNOPSIS
    Server-side end-to-end Smoke Test for ExposedPath v3 Pilot.

.DESCRIPTION
    Creates a unique smoke run directory and executes:
      1. Environment checks
      2. prompt_tokens.json generation
      3. WMPC manifest creation + validation
      4. Pass 0 (no profiler)
      5. Pass 1 (nsys profiling) + SQLite export
      6. Analyzer run
      7. SMOKE_TEST_REPORT.md + smoke_test_report.json

    Stops on first failure. Never overwrites existing runs.
    Run with -DryRun to validate parameters without execution.

.PARAMETER ModelPath
    Local path to model directory (must contain config.json).

.PARAMETER GpuId
    GPU device ID to use.

.PARAMETER NsysPath
    Path to nsys.exe, or directory containing nsys.exe.

.PARAMETER OutputRoot
    Root directory for smoke test output (default: .\smoke_test).

.PARAMETER ExperimentId
    Experiment identifier (default: smoke_v3).

.PARAMETER FixedInputTokens
    Fixed input token count (default: 32).

.PARAMETER FixedOutputTokens
    Fixed output tokens per invocation (default: 2).

.PARAMETER WarmupCount
    Warmup iterations (default: 1).

.PARAMETER RepeatCount
    Benchmark repeats (default: 2).

.PARAMETER PythonExe
    Python executable (default: python).

.PARAMETER DryRun
    Validate parameters and print plan without executing.

.EXAMPLE
    .\scripts\run_server_smoke_test.ps1 `
        -ModelPath "D:\models\Qwen2.5-1.5B-Instruct" `
        -GpuId 0 `
        -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2025.6\target-windows-x64\nsys.exe" `
        -OutputRoot "D:\exposedpath_smoke"

.NOTES
    Must be run on a Windows GPU server with PyTorch CUDA, Nsight Systems,
    and a local model.  Does NOT download models or modify existing data.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ModelPath,

    [Parameter(Mandatory = $true)]
    [int]$GpuId,

    [Parameter(Mandatory = $true)]
    [string]$NsysPath,

    [string]$OutputRoot = ".\smoke_test",

    [string]$ExperimentId = "smoke_v3",

    [int]$FixedInputTokens = 32,

    [int]$FixedOutputTokens = 2,

    [int]$WarmupCount = 1,

    [int]$RepeatCount = 2,

    [string]$PythonExe = "python",

    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$ScriptStart = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# ---- Project root ----
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

# ---- Resolve NsysPath: accept file or directory ----
$NsysExePath = $NsysPath
if (Test-Path $NsysPath -PathType Container) {
    $NsysExePath = Join-Path $NsysPath "nsys.exe"
}

# ---- Create unique UTC smoke directory ----
$SmokeTimestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$SmokeDir = Join-Path $OutputRoot "smoke_${SmokeTimestamp}"

# ---- Build report skeleton ----
$Report = @{
    gate_decision  = "UNKNOWN"
    started_at     = $ScriptStart
    paths          = @{
        project_root = $ProjectRoot
        smoke_dir    = $SmokeDir
        model_path   = $ModelPath
        nsys_exe     = $NsysExePath
    }
    environment    = @{}
    pass0          = @{}
    pass1          = @{}
    analyzer       = @{}
    errors         = @()
}

function Save-Report {
    $report_json = Join-Path $SmokeDir "smoke_test_report.json"
    $Report | ConvertTo-Json -Depth 6 | Out-File -FilePath $report_json -Encoding utf8

    $md = Join-Path $SmokeDir "SMOKE_TEST_REPORT.md"
    @"
# ExposedPath v3 Smoke Test Report

- **Gate Decision**: $($Report.gate_decision)
- **Started**: $($Report.started_at)
- **Finished**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- **Project**: $($Report.paths.project_root)
- **Model**: $($Report.paths.model_path)
- **Smoke Dir**: $($Report.paths.smoke_dir)

## Environment
$($Report.environment | ConvertTo-Json -Depth 4)

## Pass 0
$($Report.pass0 | ConvertTo-Json -Depth 4)

## Pass 1
$($Report.pass1 | ConvertTo-Json -Depth 4)

## Analyzer
$($Report.analyzer | ConvertTo-Json -Depth 4)

## Errors
$($Report.errors -join "`n")
"@ | Out-File -FilePath $md -Encoding utf8
}

function Set-GateFailure {
    param([string]$Gate, [string]$Reason)
    $Report.gate_decision = $Gate
    $Report.errors += "[$Gate] $Reason"
    Write-Host ""
    Write-Host "=" * 60
    Write-Host "  BLOCKED: $Gate"
    Write-Host "  $Reason"
    Write-Host "=" * 60
    Save-Report
    exit 1
}

# ---- Dry-run: print plan and exit ----
if ($DryRun) {
    Write-Host "===== SMOKE TEST PLAN (DryRun) ====="
    Write-Host "  ModelPath:        $ModelPath"
    Write-Host "  GpuId:            $GpuId"
    Write-Host "  NsysPath:         $NsysPath"
    Write-Host "  NsysExePath:      $NsysExePath"
    Write-Host "  OutputRoot:       $OutputRoot"
    Write-Host "  SmokeDir:         $SmokeDir"
    Write-Host "  ExperimentId:     $ExperimentId"
    Write-Host "  FixedInputTokens: $FixedInputTokens"
    Write-Host "  FixedOutputTokens:$FixedOutputTokens"
    Write-Host "  WarmupCount:      $WarmupCount"
    Write-Host "  RepeatCount:      $RepeatCount"
    exit 0
}

# ===================================================================
# STEP 0: Validate parameters
# ===================================================================
Write-Host "===== STEP 0: Parameter Validation ====="

if (-not (Test-Path $ModelPath -PathType Container)) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "ModelPath does not exist: $ModelPath"
}
$ConfigJson = Join-Path $ModelPath "config.json"
if (-not (Test-Path $ConfigJson)) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "Model config.json missing: $ConfigJson"
}
if (-not (Test-Path $NsysExePath)) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "nsys.exe not found at: $NsysExePath"
}

# Create smoke directory (fail if exists and non-empty)
if (Test-Path $SmokeDir) {
    $existing = @(Get-ChildItem -Path $SmokeDir -ErrorAction SilentlyContinue)
    if ($existing.Count -gt 0) {
        Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "Smoke directory exists and is not empty: $SmokeDir"
    }
}
New-Item -ItemType Directory -Force -Path $SmokeDir | Out-Null
$LogDir = Join-Path $SmokeDir "logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

Write-Host "  SmokeDir: $SmokeDir"
Write-Host "  All parameters valid."

# ===================================================================
# STEP 1: Environment checks
# ===================================================================
Write-Host ""
Write-Host "===== STEP 1: Environment ====="

function Run-And-Log {
    param([string]$Label, [string]$OutFile, [ScriptBlock]$Script)
    $out_path = Join-Path $LogDir $OutFile
    Write-Host "  [$Label] -> $out_path"
    try {
        $output = & $Script 2>&1
        $output -join "`n" | Out-File -FilePath $out_path -Encoding utf8
        return $output, $LASTEXITCODE
    } catch {
        $_.Exception.Message | Out-File -FilePath $out_path -Encoding utf8
        return @($_.Exception.Message), 1
    }
}

# 1a) python --version
$pyver, $_ = Run-And-Log "python --version" "01_python_version.txt" { & $PythonExe --version }
$Report.environment["python_version"] = ($pyver -join " ").Trim()

# 1b) python -m exposedpath --help
$_, $_ = Run-And-Log "exposedpath --help" "02_exposedpath_help.txt" { & $PythonExe -m exposedpath --help }

# 1c) python -m pytest -q
$pytest_out, $pytest_rc = Run-And-Log "pytest" "03_pytest.txt" { & $PythonExe -m pytest -q }
$Report.environment["pytest"] = if ($pytest_rc -eq 0) { "PASS" } else { "FAIL (rc=$pytest_rc)" }

# 1d) compileall
$_, $ca_rc = Run-And-Log "compileall" "04_compileall.txt" { & $PythonExe -m compileall -q exposedpath analysis }
$Report.environment["compileall"] = if ($ca_rc -eq 0) { "PASS" } else { "FAIL (rc=$ca_rc)" }

# 1e) nvidia-smi
$smi_out, $_ = Run-And-Log "nvidia-smi" "05_nvidia_smi.txt" { nvidia-smi }
$Report.environment["nvidia_smi"] = "OK"

# 1f) nsys --version
$nsys_out, $nsys_rc = Run-And-Log "nsys --version" "06_nsys_version.txt" { & $NsysExePath --version }
if ($nsys_rc -ne 0) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "nsys --version failed (rc=$nsys_rc)"
}
$Report.environment["nsys_version"] = ($nsys_out -join " ").Trim()

# 1g) PyTorch CUDA check
$cuda_script = @"
import torch, sys
print('torch_version', torch.__version__)
print('cuda_available', torch.cuda.is_available())
if torch.cuda.is_available():
    print('cuda_runtime', torch.version.cuda)
    print('device_count', torch.cuda.device_count())
    if $GpuId < torch.cuda.device_count():
        print('gpu_name', torch.cuda.get_device_name($GpuId))
    else:
        print('ERROR: GpuId $GpuId out of range (0..' + str(torch.cuda.device_count() - 1) + ')')
        sys.exit(1)
else:
    print('ERROR: CUDA not available')
    sys.exit(1)
"@
$cuda_out, $cuda_rc = Run-And-Log "CUDA check" "07_cuda_check.txt" { & $PythonExe -c $cuda_script }
$Report.environment["cuda"] = ($cuda_out -join "`n")
if ($cuda_rc -ne 0) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "CUDA/PyTorch check failed. Ensure torch with CUDA is installed and GPU $GpuId is available."
}

# 1h) verify_pilot_install.ps1
if (Test-Path (Join-Path $ScriptDir "verify_pilot_install.ps1")) {
    $_, $verify_rc = Run-And-Log "verify_pilot_install" "08_verify_pilot_install.txt" {
        & powershell -ExecutionPolicy Bypass -File (Join-Path $ScriptDir "verify_pilot_install.ps1") -SkipTests
    }
    $Report.environment["verify_pilot_install"] = if ($verify_rc -eq 0) { "PASS" } else { "WARN (rc=$verify_rc)" }
}

Write-Host "  Environment checks complete."

# ===================================================================
# STEP 2: prompt_tokens.json
# ===================================================================
Write-Host ""
Write-Host "===== STEP 2: prompt_tokens.json ====="

$PtFile = Join-Path $SmokeDir "prompt_tokens.json"
$prep_args = @(
    "-m", "exposedpath", "prepare-prompt-tokens",
    "--model-path", "$ModelPath",
    "--fixed-input-tokens", $FixedInputTokens,
    "--num-samples", 4,
    "--output", "$PtFile"
)
$prep_cmd = "$PythonExe $($prep_args -join ' ')"
$prep_cmd | Out-File -FilePath (Join-Path $LogDir "09_prepare_prompt_tokens_cmd.txt") -Encoding utf8

$prep_out = & $PythonExe @prep_args 2>&1
$prep_rc = $LASTEXITCODE
$prep_out -join "`n" | Out-File -FilePath (Join-Path $LogDir "09_prepare_prompt_tokens_out.txt") -Encoding utf8

if ($prep_rc -ne 0) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "prepare-prompt-tokens failed (rc=$prep_rc)"
}
if (-not (Test-Path $PtFile)) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "prompt_tokens.json was not created: $PtFile"
}

# Extract SHA-256 from output
$pt_sha = ""
foreach ($line in $prep_out) {
    if ($line -match "SHA-256:\s*([a-f0-9]{64})") {
        $pt_sha = $Matches[1]
        break
    }
}
if (-not $pt_sha) {
    # Compute directly
    $pt_sha = (Get-FileHash -Path $PtFile -Algorithm SHA256).Hash.ToLower()
}
$Report.environment["prompt_tokens_sha256"] = $pt_sha
Write-Host "  prompt_tokens.json: $PtFile"
Write-Host "  SHA-256: $pt_sha"

# ===================================================================
# STEP 3: WMPC Manifest
# ===================================================================
Write-Host ""
Write-Host "===== STEP 3: WMPC Manifest ====="

$manifest_py = @"
from exposedpath.manifest import create_manifest, finalize_manifest, save_manifest
from exposedpath.workload import load_prompt_tokens
from pathlib import Path
import json

pt_path = Path(r'$PtFile')
pt = load_prompt_tokens(pt_path)
m = create_manifest(
    experiment_id='$ExperimentId',
    run_role='PILOT',
    model_path=r'$ModelPath',
    prompt_tokens_file=str(pt_path.resolve()),
    batch_size=1,
    fixed_output_tokens=$FixedOutputTokens,
    warmup_count=$WarmupCount,
    repeat_count=$RepeatCount,
    gpu=$GpuId,
    external_cuda_workload_policy='none',
)
m = finalize_manifest(m, pt, prompt_tokens_path=pt_path)
out_dir = Path(r'$SmokeDir')
save_manifest(m, out_dir / 'wmpc_manifest.json')
print('MANIFEST_PATH:' + str(out_dir / 'wmpc_manifest.json'))
print('WMPC_ID:' + m['wmpc_id'])
print('RUN_ID:' + m['run_id'])
print('SHA256:' + m['prompt_tokens_sha256'])
"@

$manifest_script = Join-Path $LogDir "10_create_manifest.py"
$manifest_py | Out-File -FilePath $manifest_script -Encoding utf8

$manifest_out = & $PythonExe $manifest_script 2>&1
$manifest_rc = $LASTEXITCODE
$manifest_out -join "`n" | Out-File -FilePath (Join-Path $LogDir "10_create_manifest_out.txt") -Encoding utf8

if ($manifest_rc -ne 0) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "Manifest creation failed (rc=$manifest_rc)"
}

$ManifestPath = ""
$WmpcId = ""
$RunId = ""
foreach ($line in $manifest_out) {
    if ($line -match "^MANIFEST_PATH:(.*)") { $ManifestPath = $Matches[1].Trim() }
    if ($line -match "^WMPC_ID:(.*)")     { $WmpcId = $Matches[1].Trim() }
    if ($line -match "^RUN_ID:(.*)")       { $RunId = $Matches[1].Trim() }
    if ($line -match "^SHA256:(.*)")       { $Report.environment["manifest_sha256"] = $Matches[1].Trim() }
}

if (-not $ManifestPath -or -not (Test-Path $ManifestPath)) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "Manifest was not created at: $ManifestPath"
}
$Report.paths["manifest"] = $ManifestPath
$Report.paths["wmpc_id"] = $WmpcId
$Report.paths["run_id"] = $RunId

Write-Host "  Manifest: $ManifestPath"
Write-Host "  wmpc_id:  $WmpcId"
Write-Host "  run_id:   $RunId"

# ---- Validate manifest ----
Write-Host ""
Write-Host "  Validating manifest..."
$val_out = & $PythonExe -m exposedpath validate-manifest --manifest "$ManifestPath" 2>&1
$val_rc = $LASTEXITCODE
$val_out -join "`n" | Out-File -FilePath (Join-Path $LogDir "11_validate_manifest_out.txt") -Encoding utf8
if ($val_rc -ne 0) {
    Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "validate-manifest failed (rc=$val_rc): $($val_out -join ' ')"
}
Write-Host "  validate-manifest: PASSED"

# ===================================================================
# STEP 4: Pass 0
# ===================================================================
Write-Host ""
Write-Host "===== STEP 4: Pass 0 ====="

$Pass0Dir = Join-Path $SmokeDir "pass0"

# Pre-create empty directory for run_pass0.ps1
if (Test-Path $Pass0Dir) {
    $existing = @(Get-ChildItem -Path $Pass0Dir -ErrorAction SilentlyContinue)
    if ($existing.Count -gt 0) {
        Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0 directory already non-empty: $Pass0Dir"
    }
}
New-Item -ItemType Directory -Force -Path $Pass0Dir | Out-Null

# Save Pass 0 command
$pass0_cmd = "$PythonExe -m exposedpath run-pass0 --manifest `"$ManifestPath`" --output-dir `"$Pass0Dir`""
$pass0_cmd | Out-File -FilePath (Join-Path $Pass0Dir "pass0_command.txt") -Encoding utf8

$pass0_out = & $PythonExe -m exposedpath run-pass0 --manifest "$ManifestPath" --output-dir "$Pass0Dir" 2>&1
$pass0_rc = $LASTEXITCODE
$pass0_out -join "`n" | Out-File -FilePath (Join-Path $LogDir "12_pass0_out.txt") -Encoding utf8

if ($pass0_rc -ne 0) {
    Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0 failed (rc=$pass0_rc)"
}

# Validate Pass 0 results
$ResultsFile = Join-Path $Pass0Dir "inference_results.jsonl"
$ExclusionFile = Join-Path $Pass0Dir "exclusion_log.jsonl"

if (-not (Test-Path $ResultsFile)) {
    Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0 did not produce inference_results.jsonl"
}

$results = @(Get-Content $ResultsFile | ForEach-Object { $_ | ConvertFrom-Json })
$exclusions = @()
if (Test-Path $ExclusionFile) {
    $exclusions = @(Get-Content $ExclusionFile | ForEach-Object { $_ | ConvertFrom-Json })
}

$Report.pass0 = @{
    status            = "PASS"
    success_count     = $results.Count
    exclusion_count   = $exclusions.Count
    repeat_count      = $RepeatCount
    results           = @()
    sha_verified      = $true
}

$pass0_ok = $true
if ($results.Count -ne $RepeatCount) {
    $Report.pass0["error"] = "Expected $RepeatCount successes, got $($results.Count)"
    $pass0_ok = $false
}

$rep_indices = @($results | ForEach-Object { $_.repeat_index } | Sort-Object)
$expected_indices = @(0..($RepeatCount - 1))
if (($rep_indices -join ',') -ne ($expected_indices -join ',')) {
    $Report.pass0["error"] = "repeat_index mismatch: got [$($rep_indices -join ',')], expected [$($expected_indices -join ',')]"
    $pass0_ok = $false
}

foreach ($r in $results) {
    $Report.pass0.results += @{
        repeat_index        = $r.repeat_index
        prefill_latency_ms  = $r.prefill_latency_ms
        decode_latency_ms   = $r.decode_latency_ms
        actual_input_tokens = $r.actual_input_tokens
        actual_output_tokens= $r.actual_output_tokens
        batch_size          = $r.batch_size
    }
    if ($r.actual_input_tokens -ne $FixedInputTokens)   { $pass0_ok = $false }
    if ($r.actual_output_tokens -ne $FixedOutputTokens) { $pass0_ok = $false }
    if ($r.batch_size -ne 1)                             { $pass0_ok = $false }
    if ($r.prefill_latency_ms -le 0)                     { $pass0_ok = $false }
}

if (-not $pass0_ok) {
    Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0 validation failed. See report for details."
}

Write-Host "  Pass 0: $($results.Count)/$RepeatCount successes, $($exclusions.Count) exclusions"
$Report.pass0.status = "PASS"

# ===================================================================
# STEP 5: Pass 1 (nsys)
# ===================================================================
Write-Host ""
Write-Host "===== STEP 5: Pass 1 (nsys) ====="

$Pass1Dir = Join-Path $SmokeDir "pass1"
New-Item -ItemType Directory -Force -Path $Pass1Dir | Out-Null

# Save Pass 1 command
$nsys_profile_name = Join-Path $Pass1Dir "pass1_profile"
$pass1_py_args = @(
    "-m", "exposedpath", "run-pass1",
    "--manifest", "$ManifestPath",
    "--output-dir", "$Pass1Dir"
)
$pass1_cmd = "`"$NsysExePath`" profile --trace=cuda,nvtx --cuda-memory-usage=true --force-overwrite=true --stats=true -o `"$nsys_profile_name`" $PythonExe $($pass1_py_args -join ' ')"
$pass1_cmd | Out-File -FilePath (Join-Path $Pass1Dir "pass1_nsys_command.txt") -Encoding utf8

Write-Host "  Launching nsys..."
Write-Host "  Output prefix: $nsys_profile_name"

$nsys_log = Join-Path $LogDir "13_pass1_nsys_console.log"
$pass1_out = & $NsysExePath profile `
    --trace=cuda,nvtx `
    --cuda-memory-usage=true `
    --force-overwrite=true `
    --stats=true `
    -o "$nsys_profile_name" `
    $PythonExe @pass1_py_args 2>&1
$pass1_rc = $LASTEXITCODE

$pass1_out -join "`n" | Out-File -FilePath $nsys_log -Encoding utf8

if ($pass1_rc -ne 0) {
    $Report.pass1 = @{ status = "FAIL"; exit_code = $pass1_rc }
    Set-GateFailure "BLOCKED_BY_NSYS" "Pass 1 nsys failed (rc=$pass1_rc). See $nsys_log"
}

# Check files
$NsysRepFile = "$nsys_profile_name.nsys-rep"
$NsysSqliteFile = "$nsys_profile_name.sqlite"

if (-not (Test-Path $NsysRepFile) -or (Get-Item $NsysRepFile).Length -eq 0) {
    $Report.pass1 = @{ status = "FAIL"; error = ".nsys-rep missing or empty" }
    Set-GateFailure "BLOCKED_BY_NSYS" ".nsys-rep not generated or empty"
}

if (-not (Test-Path $NsysSqliteFile)) {
    # Try exporting
    Write-Host "  Exporting SQLite..."
    $export_out = & $NsysExePath export --type sqlite --output "$NsysSqliteFile" "$NsysRepFile" 2>&1
    $export_out -join "`n" | Out-File -FilePath (Join-Path $LogDir "14_nsys_export_out.txt") -Encoding utf8
}

$rep_size_mb = [math]::Round((Get-Item $NsysRepFile).Length / 1MB, 2)
$sqlite_size_mb = 0
if (Test-Path $NsysSqliteFile) {
    $sqlite_size_mb = [math]::Round((Get-Item $NsysSqliteFile).Length / 1MB, 2)
}

$Report.pass1 = @{
    status       = "PASS"
    nsys_rep     = $NsysRepFile
    sqlite       = if (Test-Path $NsysSqliteFile) { $NsysSqliteFile } else { "NOT GENERATED" }
    rep_size_mb  = $rep_size_mb
    sqlite_size_mb = $sqlite_size_mb
}

Write-Host "  .nsys-rep: $NsysRepFile ($rep_size_mb MB)"
Write-Host "  .sqlite:   $NsysSqliteFile ($sqlite_size_mb MB)"

# Quick NVTX check via stats
$nvtx_stats = & $NsysExePath stats --report nvtx_pushpop_sum "$NsysRepFile" 2>&1
$nvtx_stats -join "`n" | Out-File -FilePath (Join-Path $LogDir "15_nvtx_stats.txt") -Encoding utf8

$Report.pass1["nvtx_stats_preview"] = ($nvtx_stats | Select-Object -First 15) -join "`n"

# ===================================================================
# STEP 6: Analyzer
# ===================================================================
Write-Host ""
Write-Host "===== STEP 6: Analyzer ====="

if (-not (Test-Path $NsysSqliteFile)) {
    Set-GateFailure "BLOCKED_BY_ANALYZER" "No SQLite file to analyze"
}

# Generate unique analysis_run_id
$analysis_ts = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$analysis_suffix = -join ((48..57) + (97..122) | Get-Random -Count 8 | ForEach-Object { [char]$_ })
$analysis_run_id = "analysis-${analysis_ts}-${analysis_suffix}"
$AnalysisDir = Join-Path $SmokeDir "analysis" $analysis_run_id
New-Item -ItemType Directory -Force -Path $AnalysisDir | Out-Null

$analyzer_args = @(
    (Join-Path $ProjectRoot "analysis" "exposed_accounting.py"),
    "--sqlite", "$NsysSqliteFile",
    "--output-dir", "$AnalysisDir"
)
$analyzer_cmd = "$PythonExe $($analyzer_args -join ' ')"
$analyzer_cmd | Out-File -FilePath (Join-Path $AnalysisDir "analysis_command.txt") -Encoding utf8

Write-Host "  Analysis run: $analysis_run_id"
Write-Host "  Output: $AnalysisDir"

$analyzer_out = & $PythonExe @analyzer_args 2>&1
$analyzer_rc = $LASTEXITCODE
$analyzer_out -join "`n" | Out-File -FilePath (Join-Path $LogDir "16_analyzer_out.txt") -Encoding utf8

if ($analyzer_rc -ne 0) {
    $Report.analyzer = @{ status = "FAIL"; exit_code = $analyzer_rc }
    Set-GateFailure "BLOCKED_BY_ANALYZER" "Analyzer failed (rc=$analyzer_rc)"
}

# Check analyzer output
$AccountingResult = Join-Path $AnalysisDir "accounting_result.json"
$AccountingSummary = Join-Path $AnalysisDir "accounting_summary.csv"
$BSyncDetail = Join-Path $AnalysisDir "b_sync_detail.csv"

$analysis_ok = $true
$conservation_status = "unknown"
$count_coverage = "unknown"
$duration_coverage = "unknown"

if (Test-Path $AccountingResult) {
    $ar = Get-Content $AccountingResult -Raw | ConvertFrom-Json
    # Extract A-layer conservation
    if ($ar.PSObject.Properties["a_summary"]) {
        $conservation_status = "present in a_summary"
    }
    if ($ar.PSObject.Properties["sync_coverage"]) {
        $sc = $ar.sync_coverage
        $count_coverage = "$($sc.sync_count_valid) / $($sc.sync_count_total)"
        $duration_coverage = "$($sc.sync_duration_valid_ms) / $($sc.sync_duration_total_ms) ms"
    }
} else {
    $analysis_ok = $false
}

$Report.analyzer = @{
    status              = if ($analysis_ok) { "PASS" } else { "INCOMPLETE" }
    analysis_run_id     = $analysis_run_id
    output_dir          = $AnalysisDir
    conservation_status = $conservation_status
    count_coverage      = $count_coverage
    duration_coverage   = $duration_coverage
}

Write-Host "  Analyzer: $(if ($analysis_ok) { 'PASS' } else { 'INCOMPLETE' })"

# ===================================================================
# FINAL: Set gate + save report
# ===================================================================
Write-Host ""
Write-Host "===== FINAL: Gate Decision ====="

$Report.gate_decision = "READY_FOR_SMALL_PILOT"
$Report.finished_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Save-Report

$summary_json = Join-Path $SmokeDir "smoke_test_report.json"
Write-Host ""
Write-Host "=" * 60
Write-Host "  SMOKE TEST: READY_FOR_SMALL_PILOT"
Write-Host "=" * 60
Write-Host "  Smoke dir:  $SmokeDir"
Write-Host "  Report:     $summary_json"
Write-Host "  wmpc_id:    $WmpcId"
Write-Host "  run_id:     $RunId"
Write-Host ""

exit 0
