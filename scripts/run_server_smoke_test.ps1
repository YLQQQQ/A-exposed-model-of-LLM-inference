<#
.SYNOPSIS
    Server-side end-to-end Smoke Test for ExposedPath v3 Pilot.
.DESCRIPTION
    Steps: 0-Params 1-Env 2-PromptTokens 3-Manifest 4-Pass0 5-Pass1 6-Analyzer 7-Report.
    gate7-legacy-analyzer/1 accepts fresh attempts only; resume flags are rejected.
    All subprocess success/failure is gated ONLY by exit code (never by stderr content).
.EXAMPLE
    .\scripts\run_server_smoke_test.ps1 -ModelPath "D:\models\..." -GpuId 0 -NsysPath "C:\...\nsys.exe"
#>
param(
    [Parameter(Mandatory=$true)][string]$ModelPath,
    [Parameter(Mandatory=$true)][int]$GpuId,
    [Parameter(Mandatory=$true)][string]$NsysPath,
    [string]$OutputRoot = ".\smoke_test",
    [string]$ExperimentId = "smoke_v3",
    [int]$FixedInputTokens = 32,
    [int]$FixedOutputTokens = 2,
    [int]$WarmupCount = 1,
    [int]$RepeatCount = 2,
    [string]$PythonExe = "python",
    [ValidateSet("Validate","Prompt","Manifest","Pass0","Pass1","Analyzer")][string]$ResumeFrom = "",
    [string]$ExistingSmokeDir = "",
    [switch]$SkipStaticTests,
    [switch]$DryRun
)
$ErrorActionPreference = "Continue"
$ScriptStart = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# ---- Project root ----
if ($PSScriptRoot) { $ProjectRoot = Split-Path -Parent $PSScriptRoot }
else { $ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path) }
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

# ---- Resolve executables to absolute paths (PATH, venv, spaces-safe) ----
function Resolve-Executable {
    param([string]$Name)
    if (-not $Name) { return $null }
    # 1) Already an absolute path that exists
    try { if (Test-Path -Path $Name -PathType Leaf -ErrorAction SilentlyContinue) { return (Resolve-Path -Path $Name -ErrorAction SilentlyContinue).Path } } catch {}
    # 2) Directory + nsys.exe heuristic
    try {
        if (Test-Path -Path $Name -PathType Container -ErrorAction SilentlyContinue) {
            $candidate = Join-Path $Name "nsys.exe"
            if (Test-Path -Path $candidate -PathType Leaf -ErrorAction SilentlyContinue) { return (Resolve-Path -Path $candidate -ErrorAction SilentlyContinue).Path }
        }
    } catch {}
    # 3) Search PATH via Get-Command
    try { $cmd = Get-Command $Name -ErrorAction Stop; return $cmd.Source } catch {}
    # 4) Last resort: .venv python
    $venv_python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    if ($Name -eq "python") { try { if (Test-Path -Path $venv_python -PathType Leaf -ErrorAction SilentlyContinue) { return $venv_python } } catch {} }
    return $null
}

$PythonExe = Resolve-Executable $PythonExe
if (-not $PythonExe) { Write-Host "ERROR: Cannot resolve PythonExe. Check PATH or activate .venv."; exit 1 }

$NsysExePath = Resolve-Executable $NsysPath
if (-not $NsysExePath) { Write-Host "ERROR: Cannot resolve NsysPath: $NsysPath"; exit 1 }

# ---- Startup info ----
Write-Host "============================================"
Write-Host "  ExposedPath v3 Smoke Test"
Write-Host "============================================"
Write-Host "  ScriptRoot:   $(if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path })"
Write-Host "  ProjectRoot:  $ProjectRoot"
Write-Host "  PythonExe:    $PythonExe"
Write-Host "  NsysExe:      $NsysExePath"
Write-Host "  CWD:          $(Get-Location)"
Write-Host ""

# ---- Validate project structure ----
foreach ($sub in @("exposedpath","scripts","analysis","tests")) {
    $p = Join-Path $ProjectRoot $sub
    if (-not (Test-Path $p -PathType Container)) { Write-Host "ERROR: Required directory missing: $p"; exit 1 }
}
$OriginalPythonPath = $env:PYTHONPATH
if ($OriginalPythonPath) { $env:PYTHONPATH = "$ProjectRoot;$OriginalPythonPath" }
else                     { $env:PYTHONPATH = "$ProjectRoot" }
Set-Location $ProjectRoot

# ---- ResumeFrom ----
$RESUME_LEVELS = @{ Validate=1; Prompt=2; Manifest=3; Pass0=4; Pass1=5; Analyzer=6 }
$ResumeLevel = 0
if ($ResumeFrom) {
    $ResumeLevel = $RESUME_LEVELS[$ResumeFrom]
    if (-not $ExistingSmokeDir) { Write-Host "ERROR: -ResumeFrom requires -ExistingSmokeDir"; exit 1 }
    if (-not (Test-Path $ExistingSmokeDir -PathType Container)) { Write-Host "ERROR: ExistingSmokeDir not found"; exit 1 }
}

# ---- Smoke directory ----
if ($ExistingSmokeDir) { $SmokeDir = (Resolve-Path $ExistingSmokeDir).Path }
else {
    $SmokeTimestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $SmokeDir = Join-Path $OutputRoot "smoke_${SmokeTimestamp}"
}
$LogDir = Join-Path $SmokeDir "logs"
if ($ExistingSmokeDir) {
    $PriorMachineReport = Join-Path -Path $SmokeDir -ChildPath "smoke_test_report.json"
    if (Test-Path -LiteralPath $PriorMachineReport -PathType Leaf) {
        Write-Host "ERROR: Refusing to resume a finalized attempt or overwrite its machine report: $PriorMachineReport"
        exit 1
    }
    Write-Host "ERROR: gate7-legacy-analyzer/1 requires a fresh attempt; historical evidence cannot be reaccepted"
    exit 1
}

# ---- Report skeleton ----
$Report = @{
    analyzer_acceptance_version="gate7-legacy-analyzer/1"
    gate_decision="UNKNOWN"; started_at=$ScriptStart
    paths=@{ project_root=$ProjectRoot; smoke_dir=$SmokeDir; model_path=$ModelPath; nsys_exe=$NsysExePath }
    environment=@{}; pass0=@{}; pass1=@{}; analyzer=@{}; errors=@()
}
function Save-Report {
    $Report | ConvertTo-Json -Depth 9 | Out-File (Join-Path $SmokeDir "smoke_test_report.json") -Encoding utf8
    $md = Join-Path $SmokeDir "SMOKE_TEST_REPORT.md"
    $md_content = @"
# ExposedPath v3 Smoke Test Report
- **Gate**: $($Report.gate_decision) | **Started**: $($Report.started_at) | **Finished**: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')
- **Project**: $($Report.paths.project_root) | **Model**: $($Report.paths.model_path) | **Smoke**: $($Report.paths.smoke_dir)
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
"@
    $md_content | Out-File $md -Encoding utf8
}
function Set-GateFailure { param([string]$Gate,[string]$Reason)
    $Report.gate_decision=$Gate; $Report.errors+="[$Gate] $Reason"
    Write-Host ""; Write-Host "="*60; Write-Host "  BLOCKED: $Gate"; Write-Host "  $Reason"; Write-Host "="*60
    Save-Report
    if ($OriginalPythonPath -ne $null) { $env:PYTHONPATH = $OriginalPythonPath } else { Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue }
    exit 1
}

# ---- Recover-Pass0State: validate existing Pass 0 results from disk ----
function Recover-Pass0State {
    param([string]$Dir, [int]$ExpectedCount, [int]$ExpectedInput, [int]$ExpectedOutput, [int]$ExpectedBatch)
    $rf = Join-Path -Path $Dir -ChildPath "inference_results.jsonl"
    $ef = Join-Path -Path $Dir -ChildPath "exclusion_log.jsonl"
    if (-not (Test-Path $rf)) { return $false, "inference_results.jsonl missing: $rf" }
    try {
        $results = @(Get-Content $rf | ForEach-Object { $_ | ConvertFrom-Json })
    } catch { return $false, "JSON parse error in $rf" }
    $exclusions = @()
    if (Test-Path $ef) {
        try { $exclusions = @(Get-Content $ef | ForEach-Object { $_ | ConvertFrom-Json }) } catch {}
    }
    if ($results.Count -ne $ExpectedCount) { return $false, "success count $($results.Count) != expected $ExpectedCount" }
    $indices = @($results | ForEach-Object { $_.repeat_index } | Sort-Object)
    $expected_indices = @(0..($ExpectedCount - 1))
    if (($indices -join ',') -ne ($expected_indices -join ',')) { return $false, "repeat_index mismatch: $($indices -join ',')" }
    foreach ($r in $results) {
        if ($r.attempt_status -ne "success") { return $false, "attempt_status not success at index $($r.repeat_index)" }
        if ($r.inference_e2e_latency_ms -le 0) { return $false, "e2e_latency <= 0 at index $($r.repeat_index)" }
        if ($r.actual_input_tokens -ne $ExpectedInput) { return $false, "input_tokens $($r.actual_input_tokens) != $ExpectedInput" }
        if ($r.actual_output_tokens -ne $ExpectedOutput) { return $false, "output_tokens $($r.actual_output_tokens) != $ExpectedOutput" }
        if ($r.batch_size -ne $ExpectedBatch) { return $false, "batch_size $($r.batch_size) != $ExpectedBatch" }
    }
    # Populate Report
    $Report.pass0["status"] = "PASS"
    $Report.pass0["validation_status"] = "PASS"
    $Report.pass0["success_count"] = $results.Count
    $Report.pass0["exclusion_count"] = $exclusions.Count
    $Report.pass0["repeat_count"] = $ExpectedCount
    $Report.pass0["results"] = @()
    foreach ($r in $results) {
        $Report.pass0.results += @{ repeat_index=$r.repeat_index; prefill_latency_ms=$r.prefill_latency_ms;
            decode_latency_ms=$r.decode_latency_ms; actual_input_tokens=$r.actual_input_tokens;
            actual_output_tokens=$r.actual_output_tokens; batch_size=$r.batch_size }
    }
    return $true, "OK"
}

# ---- Recover-Pass1State: validate existing Pass 1 nsys output from disk ----
function Recover-Pass1State {
    param([string]$Dir)
    $rep = Join-Path -Path $Dir -ChildPath "pass1_profile.nsys-rep"
    $sql = Join-Path -Path $Dir -ChildPath "pass1_profile.sqlite"
    if (-not (Test-Path $rep)) { return $false, ".nsys-rep missing: $rep" }
    if ((Get-Item $rep).Length -eq 0) { return $false, ".nsys-rep empty: $rep" }
    if (-not (Test-Path $sql)) { return $false, ".sqlite missing: $sql" }
    if ((Get-Item $sql).Length -eq 0) { return $false, ".sqlite empty: $sql" }
    $postprocessPath = Join-Path -Path $Dir -ChildPath "pass1_postprocess_report.json"
    if (-not (Test-Path -LiteralPath $postprocessPath -PathType Leaf)) { return $false, "post-processing report missing" }
    try {
        $postprocess = Get-Content -LiteralPath $postprocessPath -Raw | ConvertFrom-Json
        $successfulAttempt = [int]$postprocess.successful_attempt
        if ($postprocess.status -ne "PASS" -or $postprocess.analyzer_allowed -ne $true -or
            $successfulAttempt -notin @(1,2) -or [int]$postprocess.attempt_count -lt $successfulAttempt) {
            return $false, "post-processing acceptance identity invalid"
        }
        if ([System.IO.Path]::GetFullPath($postprocess.rep_path) -ne [System.IO.Path]::GetFullPath($rep) -or
            [System.IO.Path]::GetFullPath($postprocess.canonical_sqlite_path) -ne [System.IO.Path]::GetFullPath($sql)) {
            return $false, "post-processing REP/SQLite path identity mismatch"
        }
        $successful = @($postprocess.attempts | Where-Object { [int]$_.number -eq $successfulAttempt })
        if ($successful.Count -ne 1 -or $successful[0].status -ne "PASS") {
            return $false, "successful export attempt identity missing"
        }
        $expectedAttemptPath = Join-Path -Path $Dir -ChildPath ("pass1_profile.export_attempt{0}.sqlite" -f $successfulAttempt)
        if (-not (Test-Path -LiteralPath $expectedAttemptPath -PathType Leaf) -or
            [System.IO.Path]::GetFullPath($successful[0].output_path) -ne [System.IO.Path]::GetFullPath($expectedAttemptPath)) {
            return $false, "successful export attempt file/path mismatch"
        }
        $repHash = (Get-FileHash -LiteralPath $rep -Algorithm SHA256).Hash
        $sqlHash = (Get-FileHash -LiteralPath $sql -Algorithm SHA256).Hash
        $attemptHash = (Get-FileHash -LiteralPath $expectedAttemptPath -Algorithm SHA256).Hash
        if ($repHash -ne $postprocess.rep_sha256 -or $repHash -ne $successful[0].rep_sha256 -or
            $sqlHash -ne $postprocess.canonical_sqlite_sha256 -or $sqlHash -ne $successful[0].sqlite_sha256 -or
            $attemptHash -ne $sqlHash) {
            return $false, "post-processing REP/SQLite SHA256 mismatch"
        }
    } catch {
        return $false, "post-processing report unreadable/invalid: $($_.Exception.Message)"
    }
    $Script:NsysRepFile = $rep
    $Script:NsysSqliteFile = $sql
    $Report.pass1["sqlite_export"] = $postprocess
    $Report.pass1["status"] = "PASS"
    $Report.pass1["nsys_rep"] = $rep
    $Report.pass1["sqlite"] = $sql
    $Report.pass1["rep_size_mb"] = [math]::Round((Get-Item $rep).Length/1MB,2)
    $Report.pass1["sqlite_size_mb"] = [math]::Round((Get-Item $sql).Length/1MB,2)
    return $true, "OK"
}

# ===================================================================
# Invoke-Native: robust subprocess via System.Diagnostics.Process.
# ALL parameters are named — positional binding is disabled.
# ===================================================================
function Invoke-Native {
    param(
        [Parameter(Mandatory=$true)][string]$Executable,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [Parameter(Mandatory=$true)][string]$OutBase,
        [Parameter(Mandatory=$true)][string]$WorkingDirectory,
        [string]$Label = ""
    )
    # --- Validate WorkingDirectory ---
    if (-not (Test-Path $WorkingDirectory -PathType Container)) {
        $msg = "WorkingDirectory not a directory: $WorkingDirectory"
        Write-Host "    FATAL: $msg"
        $err_file = Join-Path $LogDir "${OutBase}_stderr.txt"
        New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
        $msg | Out-File -FilePath $err_file -Encoding utf8
        return @{ ExitCode = -1; Stdout = ""; Stderr = $msg; StderrNonEmpty = $true }
    }
    $WorkingDirectory = (Resolve-Path $WorkingDirectory).Path

    $stdout_file = Join-Path $LogDir "${OutBase}_stdout.txt"
    $stderr_file = Join-Path $LogDir "${OutBase}_stderr.txt"
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null

    if ($Label) { Write-Host "  [$Label]" } else { Write-Host "  [$OutBase]" }

    # --- Resolve executable ---
    $resolved = Resolve-Executable $Executable
    if (-not $resolved) {
        $msg = "Executable not found: $Executable"
        Write-Host "    LAUNCH ERROR: $msg"
        $msg | Out-File -FilePath $stderr_file -Encoding utf8
        return @{ ExitCode = -1; Stdout = ""; Stderr = $msg; StderrNonEmpty = $true }
    }
    $Executable = $resolved

    Write-Host "    exe:  $Executable"
    Write-Host "    wd:   $WorkingDirectory"
    Write-Host "    args: $($Arguments -join ' ')"

    # --- Start process ---
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Executable
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.Arguments = $Arguments -join ' '

    try {
        $proc = [System.Diagnostics.Process]::Start($psi)
    } catch {
        $launch_err = Join-Path $LogDir "${OutBase}_launch_error.txt"
        $err_msg = "Process.Start FAILED`n  Exception: $($_.Exception.GetType().Name)`n  Message: $($_.Exception.Message)`n  FileName: $Executable`n  WorkingDir: $WorkingDirectory`n  Arguments: $($psi.Arguments)"
        $err_msg | Out-File -FilePath $launch_err -Encoding utf8
        Write-Host "    LAUNCH ERROR (see $launch_err)"
        Write-Host $err_msg
        return @{ ExitCode = -2; Stdout = ""; Stderr = $err_msg; StderrNonEmpty = $true }
    }

    if (-not $proc) {
        Write-Host "    LAUNCH ERROR: Process.Start returned null"
        return @{ ExitCode = -3; Stdout = ""; Stderr = "Process.Start returned null"; StderrNonEmpty = $true }
    }

    $stdout = $proc.StandardOutput.ReadToEnd()
    $stderr = $proc.StandardError.ReadToEnd()
    $proc.WaitForExit()
    $rc = $proc.ExitCode

    if ($stdout) { $stdout | Out-File -FilePath $stdout_file -Encoding utf8 } else { "" | Out-File -FilePath $stdout_file -Encoding utf8 }
    if ($stderr) { $stderr | Out-File -FilePath $stderr_file -Encoding utf8 } else { "" | Out-File -FilePath $stderr_file -Encoding utf8 }
    $stderr_nonempty = ($stderr -and $stderr.Trim().Length -gt 0)

    if ($rc -ne 0) {
        $tail = ($stderr -split "`n") | Select-Object -Last 20
        Write-Host "    FAIL (exit=$rc)  stderr: $stderr_file  stdout: $stdout_file"
        if ($tail) { foreach ($l in $tail) { Write-Host "      $l" } }
    } else {
        $note = if ($stderr_nonempty) { " (stderr non-empty, ignored)" } else { "" }
        Write-Host "    OK (exit=0)$note"
    }
    return @{ ExitCode = $rc; Stdout = $stdout; Stderr = $stderr; StderrNonEmpty = $stderr_nonempty }
}

# ---- Dry-run ----
if ($DryRun) {
    Write-Host "===== SMOKE TEST PLAN (DryRun) ====="
    Write-Host "  ModelPath=$ModelPath  GpuId=$GpuId  NsysExe=$NsysExePath  SmokeDir=$SmokeDir"
    Write-Host "  ResumeFrom=$ResumeFrom  SkipStaticTests=$SkipStaticTests"
    exit 0
}

# ===================================================================
# STEP 0: Validate params + create dir
# ===================================================================
Write-Host "===== STEP 0: Parameter Validation ====="
if (-not (Test-Path $ModelPath -PathType Container)) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "ModelPath: $ModelPath" }
if (-not (Test-Path (Join-Path $ModelPath "config.json"))) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "config.json missing" }
if (-not (Test-Path $NsysExePath -PathType Leaf)) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "nsys.exe not found: $NsysExePath" }

if ($ResumeLevel -eq 0) {
    if (Test-Path $SmokeDir) {
        Write-Host "ERROR: Smoke dir already exists: $SmokeDir"
        exit 1
    }
    New-Item -ItemType Directory -Force -Path $SmokeDir | Out-Null
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
} else {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}
Write-Host "  SmokeDir: $SmokeDir"

# ===================================================================
# STEP 1: Environment
# ===================================================================
if ($ResumeLevel -le 1) {
    Write-Host ""; Write-Host "===== STEP 1: Environment ====="
    $WD = $ProjectRoot

    $a = @("--version"); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "01_python_version" -WorkingDirectory $WD -Label "python --version"
    $Report.environment["python_version"] = ($r.Stdout -join " ").Trim()

    $a = @("-m","exposedpath","--help"); Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "02_exposedpath_help" -WorkingDirectory $WD -Label "exposedpath --help" | Out-Null

    if (-not $SkipStaticTests) {
        $a = @("-m","pytest","-q","-p","no:cacheprovider"); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "03_pytest" -WorkingDirectory $WD -Label "pytest"
        $Report.environment["pytest"] = if ($r.ExitCode -eq 0) { "PASS" } else { "FAIL (exit=$($r.ExitCode))" }
        $Report.environment["pytest_stderr_nonempty"] = $r.StderrNonEmpty

        $a = @("-m","compileall","-q","exposedpath","analysis","exposedpath_v141"); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "04_compileall" -WorkingDirectory $WD -Label "compileall"
        $Report.environment["compileall"] = if ($r.ExitCode -eq 0) { "PASS" } else { "FAIL (exit=$($r.ExitCode))" }
    } else {
        $Report.environment["pytest"] = "SKIPPED"; $Report.environment["compileall"] = "SKIPPED"
    }

    $smi_file = Join-Path $LogDir "05_nvidia_smi.txt"
    try   { $smi = & nvidia-smi 2>&1; $smi -join "`n" | Out-File $smi_file -Encoding utf8 }
    catch { $_.Exception.Message | Out-File $smi_file -Encoding utf8 }
    $Report.environment["nvidia_smi"] = "OK"

    $a = @("--version"); $r = Invoke-Native -Executable $NsysExePath -Arguments $a -OutBase "06_nsys_version" -WorkingDirectory $WD -Label "nsys --version"
    if ($r.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "nsys --version failed (exit=$($r.ExitCode))" }
    $Report.environment["nsys_version"] = ($r.Stdout -join " ").Trim()

    $cuda_code = @"
import os, json, subprocess
import torch
from exposedpath.manifest import resolve_logical_cuda_index

physical = $GpuId
logical = resolve_logical_cuda_index(
    physical_gpu_index=physical,
    cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
)
available = torch.cuda.is_available()
print('torch', torch.__version__)
print('cuda', available)
print('physical', physical)
print('logical', logical)
print('count', torch.cuda.device_count() if available else 0)
if not available:
    raise RuntimeError('CUDA unavailable')
print('name', torch.cuda.get_device_name(logical))
gpu = subprocess.run(
    ['nvidia-smi', '-i', str(physical), '--query-gpu=index,uuid,pci.bus_id',
     '--format=csv,noheader,nounits'], capture_output=True, text=True, check=True,
)
fields = [item.strip() for item in gpu.stdout.strip().split(',')]
if len(fields) != 3 or int(fields[0]) != physical or not fields[1] or not fields[2]:
    raise RuntimeError('preflight GPU identity incomplete or mismatched')
print('GPU_IDENTITY_JSON:' + json.dumps({
    'physical_gpu_index': physical, 'logical_gpu_index': logical,
    'gpu_uuid': fields[1], 'gpu_pci_bus_id': fields[2],
}))
"@
    $cuda_check_script = Join-Path $LogDir "07_cuda_check.py"
    [System.IO.File]::WriteAllText($cuda_check_script, $cuda_code, [System.Text.UTF8Encoding]::new($false))
    $a = @('"' + $cuda_check_script + '"'); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "07_cuda_check" -WorkingDirectory $WD -Label "CUDA check"
    $Report.environment["cuda"] = ($r.Stdout -join "`n")
    if ($r.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "CUDA/PyTorch check failed. GPU $GpuId not ready." }
    $gpuIdentityLine = @($r.Stdout -split "`n" | Where-Object { $_ -match '^GPU_IDENTITY_JSON:' })
    if ($gpuIdentityLine.Count -ne 1) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "Preflight GPU identity missing" }
    $PreflightGpuIdentityPath = Join-Path $SmokeDir "preflight_gpu_identity.json"
    $gpuIdentityLine[0].Substring('GPU_IDENTITY_JSON:'.Length) | Out-File $PreflightGpuIdentityPath -Encoding utf8
    $Report.environment["preflight_gpu_identity"] = Get-Content $PreflightGpuIdentityPath -Raw | ConvertFrom-Json

    $VerifyScript = Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "scripts") -ChildPath "verify_pilot_install.ps1"
    $Report.environment["verify_pilot_install"] = "FAIL (script missing)"
    if (Test-Path $VerifyScript) {
        $a = @("-ExecutionPolicy","Bypass","-File",$VerifyScript,"-SkipTests","-PythonExe",$PythonExe); $r = Invoke-Native -Executable "powershell" -Arguments $a -OutBase "08_verify_pilot" -WorkingDirectory $ProjectRoot -Label "verify_pilot_install"
        if ($r.ExitCode -eq 0) {
            $Report.environment["verify_pilot_install"] = "PASS"
        } else {
            $Report.environment["verify_pilot_install"] = "FAIL (exit=$($r.ExitCode))"
        }
    }
    Write-Host "  Environment done."
} else { Write-Host ""; Write-Host "===== STEP 1: Environment SKIPPED =====" }

# ===================================================================
# STEP 2: prompt_tokens.json
# ===================================================================
$PtFile = Join-Path $SmokeDir "prompt_tokens.json"
if ($ResumeLevel -le 2) {
    Write-Host ""; Write-Host "===== STEP 2: prompt_tokens.json ====="
    if ($ResumeLevel -eq 2 -and (Test-Path $PtFile)) {
        Write-Host "  Using existing: $PtFile"
        $pt_sha = (Get-FileHash -Path $PtFile -Algorithm SHA256).Hash.ToLower()
    } else {
        $prep_args = @("--model-path",$ModelPath,"--fixed-input-tokens",$FixedInputTokens,"--num-samples",4,"--output",$PtFile)
        $a = @("-m","exposedpath","prepare-prompt-tokens") + $prep_args
        $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "09_prepare_prompt_tokens" -WorkingDirectory $ProjectRoot -Label "prepare-prompt-tokens"
        if ($r.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "prepare-prompt-tokens failed (exit=$($r.ExitCode))" }
        if (-not (Test-Path $PtFile)) { Set-GateFailure "BLOCKED_BY_ENVIRONMENT" "prompt_tokens.json not created" }
        $pt_sha = ""; foreach ($l in ($r.Stdout -split "`n")) { if ($l -match "SHA-256:\s*([a-f0-9]{64})") { $pt_sha = $Matches[1]; break } }
        if (-not $pt_sha) { $pt_sha = (Get-FileHash -Path $PtFile -Algorithm SHA256).Hash.ToLower() }
    }
    $Report.environment["prompt_tokens_sha256"] = $pt_sha
    Write-Host "  SHA-256: $pt_sha"
} else {
    Write-Host ""; Write-Host "===== STEP 2: prompt_tokens.json SKIPPED ====="
    if (-not (Test-Path $PtFile)) { Set-GateFailure "BLOCKED_BY_RUNNER" "prompt_tokens.json missing: $PtFile" }
    $pt_sha = (Get-FileHash -Path $PtFile -Algorithm SHA256).Hash.ToLower()
}

# ===================================================================
# STEP 3: WMPC Manifest
# ===================================================================
$ManifestPath = Join-Path $SmokeDir "wmpc_manifest.json"
if ($ResumeLevel -le 3) {
    Write-Host ""; Write-Host "===== STEP 3: WMPC Manifest ====="
    if ($ResumeLevel -eq 3 -and (Test-Path $ManifestPath)) {
        Write-Host "  Using existing: $ManifestPath"
    } else {
        $manifest_py = @"
import sys; sys.path.insert(0, r'$ProjectRoot')
import os
from exposedpath.manifest import create_manifest, finalize_manifest, resolve_logical_cuda_index, save_manifest
from exposedpath.workload import load_prompt_tokens
from pathlib import Path
pt_path = Path(r'$PtFile'); pt = load_prompt_tokens(pt_path)
physical_gpu_index = $GpuId
logical_gpu_index = resolve_logical_cuda_index(
    physical_gpu_index=physical_gpu_index,
    cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),
)
m = create_manifest(experiment_id='$ExperimentId', run_role='PILOT', data_role='Engineering', model_path=r'$ModelPath',
    prompt_tokens_file=str(pt_path.resolve()), batch_size=1, fixed_output_tokens=$FixedOutputTokens,
    warmup_count=$WarmupCount, repeat_count=$RepeatCount, gpu=physical_gpu_index,
    gpu_index_physical=physical_gpu_index, gpu_index_logical=logical_gpu_index,
    external_cuda_workload_policy='none')
m = finalize_manifest(m, pt, prompt_tokens_path=pt_path)
out_dir = Path(r'$SmokeDir'); save_manifest(m, out_dir / 'wmpc_manifest.json')
print('MANIFEST_PATH:' + str(out_dir / 'wmpc_manifest.json'))
print('WMPC_ID:' + m['wmpc_id']); print('RUN_ID:' + m['run_id']); print('SHA256:' + m['prompt_tokens_sha256'])
"@
        $manifest_script = Join-Path $LogDir "10_create_manifest.py"
        [System.IO.File]::WriteAllText($manifest_script, $manifest_py, [System.Text.UTF8Encoding]::new($false))
        $a = @($manifest_script); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "10_create_manifest" -WorkingDirectory $ProjectRoot -Label "create_manifest"
        if ($r.ExitCode -ne 0) {
            $trace = ($r.Stderr -split "`n" | Where-Object { $_ -match "Error|Traceback|raise|Exception" }) -join "`n"
            if (-not $trace) { $trace = ($r.Stderr -split "`n" | Select-Object -Last 20) -join "`n" }
            Set-GateFailure "BLOCKED_BY_RUNNER" "Manifest creation failed (exit=$($r.ExitCode)).`n$trace"
        }
        $ManifestPath = ""; $WmpcId = ""; $RunId = ""
        foreach ($l in ($r.Stdout -split "`n")) {
            if ($l -match "^MANIFEST_PATH:(.*)") { $ManifestPath = $Matches[1].Trim() }
            if ($l -match "^WMPC_ID:(.*)")       { $WmpcId = $Matches[1].Trim() }
            if ($l -match "^RUN_ID:(.*)")         { $RunId = $Matches[1].Trim() }
            if ($l -match "^SHA256:(.*)")         { $Report.environment["manifest_sha256"] = $Matches[1].Trim() }
        }
        if (-not $ManifestPath -or -not (Test-Path $ManifestPath)) { Set-GateFailure "BLOCKED_BY_RUNNER" "Manifest not created" }
    }
    $Report.paths["manifest"] = $ManifestPath; $Report.paths["wmpc_id"] = $WmpcId; $Report.paths["run_id"] = $RunId
    Write-Host "  Manifest: $ManifestPath  wmpc_id=$WmpcId  run_id=$RunId"

    Write-Host "  Validating manifest..."
    $a = @("-m","exposedpath","validate-manifest","--manifest",$ManifestPath); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "11_validate_manifest" -WorkingDirectory $ProjectRoot -Label "validate-manifest"
    if ($r.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_RUNNER" "validate-manifest failed (exit=$($r.ExitCode))" }
    Write-Host "  validate-manifest: PASSED"
} else {
    Write-Host ""; Write-Host "===== STEP 3: WMPC Manifest SKIPPED ====="
    if (-not (Test-Path $ManifestPath)) { Set-GateFailure "BLOCKED_BY_RUNNER" "Manifest missing: $ManifestPath" }
    $a = @("-m","exposedpath","validate-manifest","--manifest",$ManifestPath); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "11_validate_manifest" -WorkingDirectory $ProjectRoot -Label "validate-manifest"
    if ($r.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_RUNNER" "validate-manifest failed (exit=$($r.ExitCode))" }
    Write-Host "  Manifest validated: $ManifestPath"
}

# ===================================================================
# STEP 4: Pass 0
# ===================================================================
$Pass0Dir = Join-Path $SmokeDir "pass0"
if ($ResumeLevel -le 4) {
    Write-Host ""; Write-Host "===== STEP 4: Pass 0 ====="
    $RESULTS_FILE = Join-Path $Pass0Dir "inference_results.jsonl"
    $rerun_pass0 = $true

    if ($ResumeLevel -eq 4 -and (Test-Path $RESULTS_FILE)) {
        Write-Host "  Existing results found — validating..."
        $results = @(Get-Content $RESULTS_FILE | ForEach-Object { $_ | ConvertFrom-Json })
        $exclusions = @()
        if (Test-Path (Join-Path $Pass0Dir "exclusion_log.jsonl")) {
            $exclusions = @(Get-Content (Join-Path $Pass0Dir "exclusion_log.jsonl") | ForEach-Object { $_ | ConvertFrom-Json })
        }
        if ($results.Count -eq $RepeatCount) { $rerun_pass0 = $false; Write-Host "  Reusing existing Pass 0: $($results.Count) results." }
        else { Write-Host "  Existing results incomplete ($($results.Count)/$RepeatCount), re-running." }
    }

    if ($rerun_pass0) {
        New-Item -ItemType Directory -Force -Path $Pass0Dir | Out-Null
        "$PythonExe -m exposedpath run-pass0 --manifest `"$ManifestPath`" --output-dir `"$Pass0Dir`"" | Out-File (Join-Path $Pass0Dir "pass0_command.txt") -Encoding utf8

        $a = @("-m","exposedpath","run-pass0","--manifest",$ManifestPath,"--output-dir",$Pass0Dir); $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "20_pass0" -WorkingDirectory $ProjectRoot -Label "Pass 0"
        $Report.pass0["process_exit_code"] = $r.ExitCode
        $Report.pass0["stderr_nonempty"] = $r.StderrNonEmpty
        $Report.pass0["stderr_log"] = Join-Path $LogDir "20_pass0_stderr.txt"
        $Report.pass0["stdout_log"] = Join-Path $LogDir "20_pass0_stdout.txt"

        if ($r.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0 exit=$($r.ExitCode). See logs/20_pass0_*" }
        if (-not (Test-Path $RESULTS_FILE)) { Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0: no inference_results.jsonl" }
        $results = @(Get-Content $RESULTS_FILE | ForEach-Object { $_ | ConvertFrom-Json })
        $exclusions = @()
        if (Test-Path (Join-Path $Pass0Dir "exclusion_log.jsonl")) {
            $exclusions = @(Get-Content (Join-Path $Pass0Dir "exclusion_log.jsonl") | ForEach-Object { $_ | ConvertFrom-Json })
        }
    }

    $Report.pass0["status"] = "PASS"
    $Report.pass0["success_count"] = $results.Count
    $Report.pass0["exclusion_count"] = $exclusions.Count
    $Report.pass0["repeat_count"] = $RepeatCount
    $Report.pass0["results"] = @()
    $Report.pass0["validation_status"] = "OK"
    $pass0_ok = $true
    if ($results.Count -ne $RepeatCount) { $Report.pass0["validation_status"] = "count_mismatch"; $pass0_ok = $false }
    $rep_indices = @($results | ForEach-Object { $_.repeat_index } | Sort-Object)
    if (($rep_indices -join ',') -ne ((0..($RepeatCount - 1)) -join ',')) { $Report.pass0["validation_status"] = "index_mismatch"; $pass0_ok = $false }
    foreach ($r in $results) {
        $Report.pass0.results += @{ repeat_index=$r.repeat_index; prefill_latency_ms=$r.prefill_latency_ms;
            decode_latency_ms=$r.decode_latency_ms; actual_input_tokens=$r.actual_input_tokens;
            actual_output_tokens=$r.actual_output_tokens; batch_size=$r.batch_size }
        if ($r.actual_input_tokens -ne $FixedInputTokens)   { $pass0_ok=$false }
        if ($r.actual_output_tokens -ne $FixedOutputTokens) { $pass0_ok=$false }
        if ($r.batch_size -ne 1)                             { $pass0_ok=$false }
        if ($r.prefill_latency_ms -le 0)                     { $pass0_ok=$false }
    }
    if (-not $pass0_ok) { Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0 validation failed." }
    Write-Host "  Pass 0: $($results.Count)/$RepeatCount successes, $($exclusions.Count) exclusions"
} else {
    Write-Host ""; Write-Host "===== STEP 4: Pass 0 SKIPPED ====="
    $p0ok, $p0msg = Recover-Pass0State -Dir $Pass0Dir -ExpectedCount $RepeatCount -ExpectedInput $FixedInputTokens -ExpectedOutput $FixedOutputTokens -ExpectedBatch 1
    if (-not $p0ok) { Set-GateFailure "BLOCKED_BY_RUNNER" "Pass 0 recovery failed: $p0msg" }
    Write-Host "  Pass 0 recovered: $p0msg"
}

# ===================================================================
# STEP 5: Pass 1 (nsys)
# ===================================================================
$Pass1Dir = Join-Path $SmokeDir "pass1"
if ($ResumeLevel -le 5) {
    Write-Host ""; Write-Host "===== STEP 5: Pass 1 (nsys) ====="
    New-Item -ItemType Directory -Force -Path $Pass1Dir | Out-Null
    $nsys_profile = Join-Path $Pass1Dir "pass1_profile"
    $NsysRepFile = "$nsys_profile.nsys-rep"
    $NsysSqliteFile = "$nsys_profile.sqlite"
    if ((Test-Path $NsysRepFile) -or (Test-Path $NsysSqliteFile)) {
        Set-GateFailure "BLOCKED_BY_NSYS" "Nsight output already exists: $nsys_profile"
    }

    # Pre-build nsys arguments as a single array (NO inline + concatenation in call!)
    $nsysArgs = @(
        "profile",
        "--trace=cuda,nvtx",
        "--sample=none",
        "--cpuctxsw=none",
        "--cuda-memory-usage=false",
        "--cuda-trace-scope=process-tree",
        "--isr=false",
        "--stats=false",
        "-o", $nsys_profile,
        $PythonExe,
        "-m", "exposedpath", "run-pass1",
        "--manifest", $ManifestPath,
        "--output-dir", $Pass1Dir
    )

    # --- Pass 1 assertions ---
    $argsStr = $nsysArgs -join ' '
    if ($argsStr -notmatch '-m.*exposedpath.*run-pass1') {
        Set-GateFailure "BLOCKED_BY_NSYS" "Pass 1 args missing -m exposedpath run-pass1: $argsStr"
    }
    if ($argsStr -notmatch '--manifest') {
        Set-GateFailure "BLOCKED_BY_NSYS" "Pass 1 args missing --manifest: $argsStr"
    }
    if ($argsStr -notmatch '--output-dir') {
        Set-GateFailure "BLOCKED_BY_NSYS" "Pass 1 args missing --output-dir: $argsStr"
    }
    if ($PythonExe -notmatch '^[A-Za-z]:\\' -and $PythonExe -notmatch '^\\\\') {
        Set-GateFailure "BLOCKED_BY_NSYS" "PythonExe is not an absolute path: $PythonExe"
    }
    if ((Test-Path $ProjectRoot -PathType Container) -eq $false) {
        Set-GateFailure "BLOCKED_BY_NSYS" "ProjectRoot not a directory: $ProjectRoot"
    }

    # Log full nsys command
    $fullNsysCmd = "$NsysExePath $argsStr"
    $fullNsysCmd | Out-File (Join-Path $Pass1Dir "pass1_nsys_command.txt") -Encoding utf8
    $Report.pass1["observation_profile"] = @{
        nsys_exe=$NsysExePath; nsys_version=$Report.environment["nsys_version"]
        nsys_argv=$nsysArgs; trace="cuda,nvtx"; sample="none"; cpuctxsw="none"
        cuda_memory_usage=$false; cuda_trace_scope="process-tree"; isr=$false
        collection_stats=$false; sqlite_policy="bounded_export_after_stable_hashed_rep"
        nvtx_stats_policy="not_run_during_acceptance"
    }
    $Report.pass1["observation_profile"] | ConvertTo-Json -Depth 5 |
        Out-File (Join-Path $Pass1Dir "pass1_observation_profile.json") -Encoding utf8
    Write-Host "  Command: $fullNsysCmd"
    Write-Host "  Launching nsys..."

    $r = Invoke-Native -Executable $NsysExePath -Arguments $nsysArgs -OutBase "30_pass1_nsys" -WorkingDirectory $ProjectRoot -Label "Pass 1 nsys"
    $Report.pass1["process_exit_code"] = $r.ExitCode
    $Report.pass1["stderr_nonempty"] = $r.StderrNonEmpty
    $Report.pass1["stderr_log"] = Join-Path $LogDir "30_pass1_nsys_stderr.txt"
    $Report.pass1["stdout_log"] = Join-Path $LogDir "30_pass1_nsys_stdout.txt"
    if ($r.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_NSYS" "Pass 1 nsys exit=$($r.ExitCode)" }

    if (-not (Test-Path $NsysRepFile) -or (Get-Item $NsysRepFile).Length -eq 0) { Set-GateFailure "BLOCKED_BY_NSYS" ".nsys-rep empty/missing" }
    if (Test-Path $NsysSqliteFile) { Set-GateFailure "BLOCKED_BY_NSYS" "SQLite output already exists: $NsysSqliteFile" }
    Write-Host "  Bounded SQLite post-processing..."
    $PostprocessScript = Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "scripts") -ChildPath "gate7_nsys_postprocess.py"
    $PostprocessReport = Join-Path -Path $Pass1Dir -ChildPath "pass1_postprocess_report.json"
    if (Test-Path -LiteralPath $PostprocessReport) {
        Set-GateFailure "BLOCKED_BY_NSYS" "SQLite post-processing report already exists: $PostprocessReport"
    }
    $a = @(
        ('"' + $PostprocessScript + '"'),
        "--nsys", ('"' + $NsysExePath + '"'),
        "--rep", ('"' + $NsysRepFile + '"'),
        "--canonical-sqlite", ('"' + $NsysSqliteFile + '"'),
        "--report", ('"' + $PostprocessReport + '"')
    )
    $pr = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "31_nsys_postprocess" -WorkingDirectory $ProjectRoot -Label "bounded nsys export"
    $Report.pass1["sqlite_postprocess_process_exit_code"] = $pr.ExitCode
    $Report.pass1["sqlite_postprocess_report_path"] = $PostprocessReport
    if (-not (Test-Path $PostprocessReport -PathType Leaf)) {
        Set-GateFailure "BLOCKED_BY_NSYS" "SQLite post-processing report missing (exit=$($pr.ExitCode))"
    }
    try {
        $PostprocessResult = Get-Content -LiteralPath $PostprocessReport -Raw | ConvertFrom-Json
    } catch {
        Set-GateFailure "BLOCKED_BY_NSYS" "SQLite post-processing report unreadable: $($_.Exception.Message)"
    }
    $Report.pass1["sqlite_export"] = $PostprocessResult
    if ($pr.ExitCode -ne 0 -or $PostprocessResult.status -ne "PASS" -or $PostprocessResult.analyzer_allowed -ne $true) {
        Set-GateFailure "BLOCKED_BY_NSYS" "SQLite post-processing failed (exit=$($pr.ExitCode); status=$($PostprocessResult.status))"
    }
    if (-not (Test-Path $NsysSqliteFile -PathType Leaf) -or (Get-Item $NsysSqliteFile).Length -eq 0) {
        Set-GateFailure "BLOCKED_BY_NSYS" "Promoted SQLite missing/empty"
    }
    $rep_mb = [math]::Round((Get-Item $NsysRepFile).Length/1MB,2)
    $sql_mb = if (Test-Path $NsysSqliteFile) { [math]::Round((Get-Item $NsysSqliteFile).Length/1MB,2) } else { 0 }
    $Report.pass1["status"]="PASS"; $Report.pass1["nsys_rep"]=$NsysRepFile; $Report.pass1["sqlite"]=if(Test-Path $NsysSqliteFile){$NsysSqliteFile}else{"NOT GENERATED"}
    $Report.pass1["rep_size_mb"]=$rep_mb; $Report.pass1["sqlite_size_mb"]=$sql_mb
    Write-Host "  .nsys-rep: $NsysRepFile (${rep_mb}MB)  .sqlite: $NsysSqliteFile (${sql_mb}MB)"

} else {
    Write-Host ""; Write-Host "===== STEP 5: Pass 1 SKIPPED ====="
    $p1ok, $p1msg = Recover-Pass1State -Dir $Pass1Dir
    if (-not $p1ok) { Set-GateFailure "BLOCKED_BY_NSYS" "Pass 1 recovery failed: $p1msg" }
    Write-Host "  Pass 1 recovered: $p1msg"
}

# ===================================================================
# STEP 6: Analyzer
# ===================================================================
if ($ResumeLevel -le 6) {
    Write-Host ""; Write-Host "===== STEP 6: Analyzer ====="
    if (-not (Test-Path $NsysSqliteFile -PathType Leaf)) { Set-GateFailure "BLOCKED_BY_ANALYZER" "No SQLite" }
    $ValidationScript = Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "scripts") -ChildPath "gate7_smoke_validation.py"
    $a = @(('"' + $ValidationScript + '"'),"sqlite","--sqlite",('"' + $NsysSqliteFile + '"'))
    $rSql = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "31_sqlite_validate" -WorkingDirectory $ProjectRoot -Label "Canonical SQLite integrity/schema check"
    $Report.pass1["sqlite_validation"] = if ($rSql.ExitCode -eq 0) { "PASS" } else { "FAIL" }
    if ($rSql.ExitCode -ne 0) { Set-GateFailure "BLOCKED_BY_NSYS" "Canonical SQLite integrity/schema invalid" }
    $ats = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $asfx = -join ((48..57)+(97..122)|Get-Random -Count 8|ForEach-Object{[char]$_})
    $aid = "analysis-${ats}-${asfx}"
    $AnalysisRoot = Join-Path -Path $SmokeDir -ChildPath "analysis"
    $AnalysisDir = Join-Path -Path $AnalysisRoot -ChildPath $aid
    New-Item -ItemType Directory -Force -Path $AnalysisDir | Out-Null
    $apy = Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "analysis") -ChildPath "exposed_accounting.py"
    $cmdFile = Join-Path -Path $AnalysisDir -ChildPath "analysis_command.txt"
    "$PythonExe $apy --sqlite `"$NsysSqliteFile`" --output-dir `"$AnalysisDir`"" | Out-File $cmdFile -Encoding utf8

    $a = @(('"' + $apy + '"'),"--sqlite",('"' + $NsysSqliteFile + '"'),"--output-dir",('"' + $AnalysisDir + '"'))
    $r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "40_analyzer" -WorkingDirectory $ProjectRoot -Label "Analyzer"
    $Report.analyzer["process_exit_code"] = $r.ExitCode
    $Report.analyzer["analysis_run_id"]=$aid
    $Report.analyzer["output_dir"]=$AnalysisDir

    # --- Analyzer validation: must pass ALL gates ---
    $analysis_ok=$false; $cons="unknown"; $cov="unknown"; $dcov="unknown"
    $gate_errors = @()

    if ($r.ExitCode -ne 0) {
        $gate_errors += "Analyzer exit=$($r.ExitCode)"
    } elseif (-not (Test-Path $AnalysisDir -PathType Container)) {
        $gate_errors += "analysis dir missing: $AnalysisDir"
    } else {
        $ar_file = Join-Path -Path $AnalysisDir -ChildPath "accounting_result.json"
        if (-not (Test-Path $ar_file)) {
            $gate_errors += "accounting_result.json missing"
        } else {
            try {
                $a = @(('"' + $ValidationScript + '"'),"analyzer","--result",('"' + $ar_file + '"'),"--sqlite",('"' + $NsysSqliteFile + '"'),"--manifest",('"' + $ManifestPath + '"'))
                $rAcceptance = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "41_analyzer_acceptance" -WorkingDirectory $ProjectRoot -Label "Gate7 legacy-only acceptance"
                $acceptance = $rAcceptance.Stdout | ConvertFrom-Json -ErrorAction Stop
                $Report.analyzer["acceptance"] = $acceptance
                if (($rAcceptance.ExitCode -ne 0) -or ($acceptance.status -ne "PASS") -or
                    ($acceptance.acceptance_version -ne "gate7-legacy-analyzer/1")) {
                    $gate_errors += "Legacy analyzer acceptance failed: $($acceptance.issues -join '; ')"
                } else {
                    $cons="VALIDATED_STRUCTURE_ONLY"
                    # Unknown is explicit, not a fabricated numerator/denominator.
                    $cov="unknown"; $dcov="unknown"
                }
                if ($gate_errors.Count -eq 0) { $analysis_ok=$true }
            } catch {
                $gate_errors += "JSON parse failed: $($_.Exception.Message)"
            }
        }
    }

    $Report.analyzer["status"]=if($analysis_ok){"PASS"}else{"INCOMPLETE"}
    $Report.analyzer["conservation_status"]=$cons; $Report.analyzer["count_coverage"]=$cov; $Report.analyzer["duration_coverage"]=$dcov
    Write-Host "  Analyzer: $(if($analysis_ok){'PASS'}else{'INCOMPLETE'})"
    if (-not $analysis_ok) {
        $Report.errors += "[BLOCKED_BY_ANALYZER] $($gate_errors -join '; ')"
        Write-Host "  Analyzer gate failures: $($gate_errors -join ', ')"
    }
} else { Write-Host ""; Write-Host "===== STEP 6: Analyzer SKIPPED =====" }

# ===================================================================
# FINAL
# ===================================================================
Write-Host ""; Write-Host "===== FINAL: Gate Decision ====="

# Recover identity from manifest if resuming
if ((-not $WmpcId) -or (-not $RunId)) {
    if (Test-Path $ManifestPath) {
        try {
            $m = Get-Content $ManifestPath -Raw | ConvertFrom-Json
            if (-not $WmpcId) { $WmpcId = $m.wmpc_id }
            if (-not $RunId)  { $RunId  = $m.run_id }
            $Report.paths["wmpc_id"] = $WmpcId; $Report.paths["run_id"] = $RunId
        } catch {}
    }
}

# Compute final gate
$allGatesOk = $true
$finalErrors = @()

# Static preflight checks are mandatory for a closeout verdict.  Missing,
# skipped, or failed checks must fail closed.
$staticPreflightOk = `
    ($Report.environment["pytest"] -eq "PASS") -and `
    ($Report.environment["compileall"] -eq "PASS") -and `
    ($Report.environment["verify_pilot_install"] -eq "PASS")
if (-not $staticPreflightOk) {
    $allGatesOk = $false
    $finalErrors += "Static preflight not PASS (pytest=$($Report.environment['pytest']); compileall=$($Report.environment['compileall']); verify_pilot_install=$($Report.environment['verify_pilot_install']))"
}

# Pass 0 check
$p0_ok = ($Report.pass0["status"] -eq "PASS") -or ($Report.pass0["validation_status"] -eq "OK")
if (-not $p0_ok) { $allGatesOk = $false; $finalErrors += "Pass0 not OK" }
if ($Report.pass1["status"] -ne "PASS") { $allGatesOk = $false; $finalErrors += "Pass1 not PASS" }

# Re-read runner output and telemetry.  The machine report is not a substitute
# for validating all frozen cross-pass identities and attempt accounting.
$ValidationScript = Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "scripts") -ChildPath "gate7_smoke_validation.py"
$PreflightGpuIdentityPath = Join-Path $SmokeDir "preflight_gpu_identity.json"
$a = @(('"' + $ValidationScript + '"'),"evidence","--manifest",('"' + $ManifestPath + '"'),"--preflight",('"' + $PreflightGpuIdentityPath + '"'),"--pass0",('"' + $Pass0Dir + '"'),"--pass1",('"' + $Pass1Dir + '"'))
$r = Invoke-Native -Executable $PythonExe -Arguments $a -OutBase "50_gate7_evidence_validation" -WorkingDirectory $ProjectRoot -Label "Gate7 parity/telemetry"
$Report.environment["gate7_evidence_validation"] = if ($r.ExitCode -eq 0) { "PASS" } else { "FAIL" }
$Report.environment["gate7_evidence_validation_output"] = $r.Stdout
if ($r.ExitCode -ne 0) { $allGatesOk = $false; $finalErrors += "Pass0/Pass1 parity, attempt accounting or GPU telemetry invalid" }

# nsys-rep check
if ((-not (Test-Path $NsysRepFile)) -or ((Get-Item $NsysRepFile).Length -eq 0)) {
    $allGatesOk = $false; $finalErrors += ".nsys-rep missing/empty"
}

# SQLite check
if ((-not (Test-Path $NsysSqliteFile)) -or ((Get-Item $NsysSqliteFile).Length -eq 0)) {
    $allGatesOk = $false; $finalErrors += ".sqlite missing/empty"
}

# Analyzer check
$a_ok = ($Report.analyzer["status"] -eq "PASS")
if (-not $a_ok) { $allGatesOk = $false; $finalErrors += "Analyzer not PASS" }

# Identity check
if (-not $WmpcId) { $allGatesOk = $false; $finalErrors += "wmpc_id empty" }
if (-not $RunId)  { $allGatesOk = $false; $finalErrors += "run_id empty" }
if (-not $aid)    { $allGatesOk = $false; $finalErrors += "analysis_run_id empty" }

# Errors array check
if ($Report.errors.Count -gt 0) { $allGatesOk = $false; $finalErrors += "$($Report.errors.Count) previous errors" }

if ($allGatesOk) {
    $Report.gate_decision = "READY_FOR_SMALL_PILOT"
    Write-Host ""; Write-Host "="*60; Write-Host "  SMOKE TEST: READY_FOR_SMALL_PILOT"; Write-Host "="*60
} else {
    $Report.gate_decision = "BLOCKED"
    $Report.errors += "[FINAL] Gate failures: $($finalErrors -join '; ')"
    Write-Host ""; Write-Host "="*60; Write-Host "  SMOKE TEST: BLOCKED"; Write-Host "="*60
    Write-Host "  Failures: $($finalErrors -join ', ')"
}

$Report.finished_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
Save-Report
if ($OriginalPythonPath -ne $null) { $env:PYTHONPATH = $OriginalPythonPath } else { Remove-Item Env:\PYTHONPATH -ErrorAction SilentlyContinue }
Write-Host "  Smoke dir: $SmokeDir"; Write-Host "  wmpc_id: $WmpcId"; Write-Host "  run_id: $RunId"; Write-Host ""
if ($allGatesOk) { exit 0 }
exit 1
