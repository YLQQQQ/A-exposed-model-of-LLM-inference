<#
.SYNOPSIS
    Run Pass 0 (benchmark-only, no profiler) for a WMPC manifest.

.DESCRIPTION
    Executes python -m exposedpath run-pass0 against a wmpc_manifest.json.
    Pass 0 generates warmup and repeat inference results without nsys profiling.
    Does NOT use NVTX ranges (those are for Pass 1 nsys only).

.PARAMETER Manifest
    Path to wmpc_manifest.json.

.PARAMETER OutputDir
    Directory for Pass 0 results (default: derived from manifest run_dir/pass0).

.PARAMETER PythonExe
    Python executable (default: python).

.EXAMPLE
    .\scripts\run_pass0.ps1 -Manifest ".\runs\my_experiment\wmpc-abc123\run-20260721T120000Z-abcdef01\wmpc_manifest.json"

.NOTES
    Do NOT wrap this script with nsys profile. For nsys profiling, use run_pass1_nsys.ps1.
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Manifest,

    [string]$OutputDir = "",

    [string]$PythonExe = "python"
)

$ManifestPath = (Resolve-Path $Manifest).Path

if (-not $OutputDir) {
    $ManifestDir = Split-Path -Parent $ManifestPath
    $OutputDir = Join-Path $ManifestDir "pass0"
}

Write-Host "============================================"
Write-Host "[run_pass0] PASS 0 — Benchmark Only (no profiler)"
Write-Host "============================================"
Write-Host "  Manifest:   $ManifestPath"
Write-Host "  Output dir: $OutputDir"
Write-Host ""

# Ensure output directory is new/empty
if (Test-Path $OutputDir) {
    $Existing = Get-ChildItem -Path $OutputDir -ErrorAction SilentlyContinue
    if ($Existing.Count -gt 0) {
        Write-Host "ERROR: Output directory exists and is not empty: $OutputDir"
        Write-Host "  Pass 0 does not overwrite existing results. Use a new run_id."
        exit 1
    }
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

# Save command
$CmdLog = Join-Path $OutputDir "pass0_command.txt"
@"
$PythonExe -m exposedpath run-pass0 --manifest "$ManifestPath" --output-dir "$OutputDir"
"@ | Out-File -FilePath $CmdLog -Encoding utf8

# Execute
& $PythonExe -m exposedpath run-pass0 --manifest "$ManifestPath" --output-dir "$OutputDir"
$ExitCode = $LASTEXITCODE

if ($ExitCode -eq 0) {
    Write-Host "[run_pass0] PASS 0 COMPLETE"
} else {
    Write-Host "[run_pass0] PASS 0 FAILED (exit code: $ExitCode)"
}

exit $ExitCode
