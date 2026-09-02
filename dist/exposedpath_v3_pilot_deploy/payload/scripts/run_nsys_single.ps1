<#
.SYNOPSIS
    [LEGACY — use run_pass1_nsys.ps1 instead]
    Run nsys profile for a single benchmark configuration.

.DESCRIPTION
    LEGACY SCRIPT: This wraps the old bench_eager.py with nsys profile.
    For new Pilot runs, use run_pass1_nsys.ps1 with a WMPC manifest.

    This script is kept for backward compatibility with old results.
    It will NOT be updated for the new WMPC/exposedpath workflow.
    Wraps bench_eager.py with nsys profile to collect:
      - NVTX ranges
      - CUDA API calls
      - GPU kernels
      - Memcpy / memory operations
      - OS runtime events

.PARAMETER ModelPath
    Path to local model directory.

.PARAMETER PromptLen
    Prompt length (number of input tokens).

.PARAMETER BatchSize
    Batch size.

.PARAMETER OutputLen
    Number of tokens to generate.

.PARAMETER OutDir
    Directory to store nsys output (.nsys-rep).

.PARAMETER RunName
    Human-readable name for this run.

.PARAMETER WarmupIters
    Number of warmup iterations (default: 2).

.PARAMETER RepeatIters
    Number of benchmark repeats (default: 3).

.PARAMETER Gpu
    GPU device ID (default: 0).

.PARAMETER ProjectDir
    Root directory of the project (default: script directory parent).

.EXAMPLE
    .\scripts\run_nsys_single.ps1 `
        -ModelPath "D:\models\Qwen2.5-3B-Instruct" `
        -PromptLen 512 `
        -BatchSize 1 `
        -OutputLen 128 `
        -OutDir "nsys_results\test_run" `
        -RunName "test_512_b1_o128"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ModelPath,

    [int]$PromptLen = 0,

    [string]$Prompt = "",

    [Parameter(Mandatory=$true)]
    [int]$BatchSize,

    [Parameter(Mandatory=$true)]
    [int]$OutputLen,

    [Parameter(Mandatory=$true)]
    [string]$OutDir,

    [Parameter(Mandatory=$true)]
    [string]$RunName,

    [int]$WarmupIters = 5,

    [int]$RepeatIters = 10,

    [int]$Gpu = 0,

    [switch]$Streaming,

    [string]$ProjectDir = ""
)

# ---- Resolve project directory ----
if (-not $ProjectDir) {
    $ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
}
$BenchScript = Join-Path $ProjectDir "bench_eager.py"

Write-Host "============================================"
Write-Host "[run_nsys_single] NSYS Profiling Single Run"
Write-Host "============================================"
if ($Prompt) {
    $ConfigDisplay = "prompt='$($Prompt[0..[Math]::Min(40,$Prompt.Length)] -join '')...', batch_size=$BatchSize, output_len=$OutputLen, streaming=$Streaming"
} else {
    $ConfigDisplay = "prompt_len=$PromptLen, batch_size=$BatchSize, output_len=$OutputLen, streaming=$Streaming"
}
Write-Host "  Project dir:  $ProjectDir"
Write-Host "  Bench script: $BenchScript"
Write-Host "  Model path:   $ModelPath"
Write-Host "  Config:       $ConfigDisplay"
Write-Host "  Run name:     $RunName"
Write-Host "  Output dir:   $OutDir"

# ---- Create output directory ----
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null

# ---- Resolve absolute path for output ----
$AbsOutDir = (Resolve-Path $OutDir).Path
$NsysOutput = Join-Path $AbsOutDir $RunName

# ---- Build python arguments ----
$PyArgs = @("--model-path", $ModelPath,
            "--batch-size", $BatchSize,
            "--output-len", $OutputLen,
            "--warmup-iters", $WarmupIters,
            "--repeat-iters", $RepeatIters,
            "--gpu", $Gpu,
            "--output-dir", $AbsOutDir,
            "--run-name", $RunName)
if ($Prompt) {
    $PyArgs += @("--prompt", $Prompt)
} else {
    $PyArgs += @("--prompt-len", $PromptLen)
}
if ($Streaming) {
    $PyArgs += "--streaming"
}

# ---- Save command.txt ----
$CmdPy = "python `"$BenchScript`""
foreach ($a in $PyArgs) {
    $CmdPy += " ``" + "`n    $a"
}
$CmdTxt = @"
$CmdPy

nsys profile `
    --trace=cuda,nvtx `
    --cuda-memory-usage=true `
    --force-overwrite=true `
    --stats=true `
    -o "$NsysOutput" `
    python "$BenchScript" `
        $($PyArgs -join " `"`n        `"")
"@

$CmdTxtPath = Join-Path $AbsOutDir "command.txt"
$CmdTxt | Out-File -FilePath $CmdTxtPath -Encoding utf8
Write-Host "  Command saved: $CmdTxtPath"

# ---- Run nsys profile ----
Write-Host ""
Write-Host "[run_nsys_single] Launching nsys profile..."

# Save nsys console output (including profiled process stderr) to a log
$NsysLog = Join-Path $AbsOutDir "nsys_console.log"

# Capture all output to memory, then save to file (preserves $LASTEXITCODE)
$NsysOutput2 = & nsys profile `
    --trace=cuda,nvtx `
    --cuda-memory-usage=true `
    --force-overwrite=true `
    --stats=true `
    -o "$NsysOutput" `
    python "$BenchScript" @PyArgs 2>&1

$ExitCode = $LASTEXITCODE

# Save full output to log file
$NsysOutput2 -join "`n" | Out-File -FilePath $NsysLog -Encoding utf8
Write-Host "  nsys console log: $NsysLog"

# Display error clues if failed
if ($ExitCode -ne 0) {
    Write-Host ""
    # Search captured output for Python error patterns
    $ErrLines = @($NsysOutput2 | Where-Object {
        $_ -match "Error|error|Traceback|FATAL|OOM|out of memory|CUDA|ModuleNotFound|ImportError|FileNotFound|No such file|Cannot|
                   memory|exception|failed|assert|SIGABRT|SIGSEGV" })
    if ($ErrLines.Count -gt 0) {
        Write-Host "--- bench_eager.py error output ---"
        $Show = [Math]::Min($ErrLines.Count, 50)
        for ($li = 0; $li -lt $Show; $li++) {
            Write-Host "  $($ErrLines[$li])"
        }
        Write-Host "--- end (see full log: $NsysLog) ---"
    } else {
        Write-Host "  No obvious error patterns found in output."
        Write-Host "  Check full log: $NsysLog"
    }
}

Write-Host ""
if ($ExitCode -eq 0) {
    Write-Host "[run_nsys_single] SUCCESS"
    Write-Host "  .nsys-rep: $NsysOutput.nsys-rep"
    Write-Host "  Results:   $AbsOutDir"
} else {
    Write-Host "[run_nsys_single] FAILED (exit code: $ExitCode)"
    Write-Host ""
    Write-Host "  TROUBLESHOOTING — run this directly to see the live error:"
    Write-Host "    cd `"$ProjectDir`""
    Write-Host "    python bench_eager.py --model-path `"$ModelPath`" --prompt-len $PromptLen --batch-size $BatchSize --output-len $OutputLen --warmup-iters 1 --repeat-iters 1 --gpu $Gpu --streaming"
}

exit $ExitCode
