<#
.SYNOPSIS
    Run Pass 1 nsys profiling for a WMPC manifest.

.DESCRIPTION
    Wraps python -m exposedpath run-pass1 with nsys profile.
    Pass 1 emits NVTX ranges for every repeat and must be wrapped by nsys.

.PARAMETER Manifest
    Path to wmpc_manifest.json.

.PARAMETER NsysPath
    Path to nsys.exe directory (will be added to PATH).

.PARAMETER PythonExe
    Python executable (default: python).

.PARAMETER ExtraNsysArgs
    Additional nsys profile arguments.

.EXAMPLE
    .\scripts\run_pass1_nsys.ps1 -Manifest ".\runs\...\wmpc_manifest.json" -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2025.6\target-windows-x64"

.NOTES
    This is the ONLY script that wraps the Python command with nsys profile.
    Do NOT manually add nsys profile to run_pass0.ps1.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Manifest,

    [string]$NsysPath = "",

    [string]$PythonExe = "python",

    [string[]]$ExtraNsysArgs = @(),

    [string]$OutputDir = ""
)

$ManifestPath = (Resolve-Path $Manifest).Path

if (-not $OutputDir) {
    $ManifestDir = Split-Path -Parent $ManifestPath
    $OutputDir = Join-Path $ManifestDir "pass1"
}

# Add nsys to PATH if provided
if ($NsysPath) {
    $env:Path = "$NsysPath;$env:Path"
}

# Verify nsys is available
$NsysExe = (Get-Command nsys -ErrorAction SilentlyContinue).Source
if (-not $NsysExe) {
    Write-Host "ERROR: nsys not found in PATH."
    Write-Host "  Provide -NsysPath or add Nsight Systems to PATH."
    exit 1
}

Write-Host "============================================"
Write-Host "[run_pass1_nsys] PASS 1 — NSYS Profiling"
Write-Host "============================================"
Write-Host "  Manifest:   $ManifestPath"
Write-Host "  Output dir: $OutputDir"
Write-Host "  nsys:        $NsysExe"
Write-Host ""

# Ensure output directory is new/empty
if (Test-Path $OutputDir) {
    $Existing = Get-ChildItem -Path $OutputDir -ErrorAction SilentlyContinue
    if ($Existing.Count -gt 0) {
        Write-Host "ERROR: Output directory exists and is not empty: $OutputDir"
        Write-Host "  Pass 1 does not overwrite existing results. Use a new run_id."
        exit 1
    }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Build the Python command for run-pass1
$PyArgs = @(
    "-m", "exposedpath", "run-pass1",
    "--manifest", "$ManifestPath",
    "--output-dir", "$OutputDir"
)

# Save full nsys command
$NsysOutput = Join-Path $OutputDir "pass1_profile"
$PyCmd = "$PythonExe $($PyArgs -join ' ')"

$FullCmd = @"
$NsysExe profile `
    --trace=cuda,nvtx `
    --cuda-memory-usage=true `
    --force-overwrite=true `
    --stats=true `
    -o "$NsysOutput" `
    $PyCmd
"@

$CmdLog = Join-Path $OutputDir "pass1_nsys_command.txt"
$FullCmd | Out-File -FilePath $CmdLog -Encoding utf8
Write-Host "  Command saved: $CmdLog"

# Execute nsys
Write-Host "[run_pass1_nsys] Launching nsys profile..."
$NsysLog = Join-Path $OutputDir "nsys_console.log"

$AllOutput = & $NsysExe profile `
    --trace=cuda,nvtx `
    --cuda-memory-usage=true `
    --force-overwrite=true `
    --stats=true `
    -o "$NsysOutput" `
    $PythonExe @PyArgs 2>&1

$ExitCode = $LASTEXITCODE

# Save console output
$AllOutput -join "`n" | Out-File -FilePath $NsysLog -Encoding utf8

if ($ExitCode -eq 0) {
    Write-Host "[run_pass1_nsys] PASS 1 COMPLETE"
    Write-Host "  .nsys-rep: $NsysOutput.nsys-rep"
    Write-Host "  .sqlite:   $NsysOutput.sqlite"
} else {
    Write-Host "[run_pass1_nsys] PASS 1 FAILED (exit code: $ExitCode)"
    Write-Host "  Log: $NsysLog"
}

exit $ExitCode
