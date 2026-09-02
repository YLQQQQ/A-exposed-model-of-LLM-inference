<#
.SYNOPSIS
    Run a complete WMPC Pilot: Pass 0 + Pass 1 (nsys) for a single manifest.

.DESCRIPTION
    Convenience script that:
      1. Validates the manifest
      2. Runs Pass 0 (no profiler)
      3. Runs Pass 1 (nsys profiling)

.PARAMETER Manifest
    Path to wmpc_manifest.json.

.PARAMETER NsysPath
    Path to nsys.exe directory.

.PARAMETER SkipPass0
    Skip Pass 0 (run only Pass 1 nsys).

.PARAMETER SkipPass1
    Skip Pass 1 (run only Pass 0).

.PARAMETER PythonExe
    Python executable (default: python).

.EXAMPLE
    .\scripts\run_wmpc_pilot.ps1 `
        -Manifest ".\runs\pilot\wmpc-abc123\run-20260721T120000Z-a1b2c3d4\wmpc_manifest.json" `
        -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2025.6\target-windows-x64"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Manifest,

    [string]$NsysPath = "",

    [switch]$SkipPass0,

    [switch]$SkipPass1,

    [string]$PythonExe = "python"
)

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Pass0Script = Join-Path $ScriptDir "run_pass0.ps1"
$Pass1Script = Join-Path $ScriptDir "run_pass1_nsys.ps1"

$ManifestPath = (Resolve-Path $Manifest).Path

Write-Host "=" * 70
Write-Host "  WMPC PILOT RUN"
Write-Host "=" * 70
Write-Host "  Manifest: $ManifestPath"

# ---- Step 0: Validate ----
Write-Host ""
Write-Host "--- Step 0: Validate Manifest ---"
& $PythonExe -m exposedpath validate-manifest --manifest "$ManifestPath"
if ($LASTEXITCODE -ne 0) {
    Write-Host "FATAL: Manifest validation failed. Aborting."
    exit 1
}

$TotalStart = Get-Date

# ---- Step 1: Pass 0 ----
if (-not $SkipPass0) {
    Write-Host ""
    Write-Host "--- Step 1: Pass 0 (no profiler) ---"
    $Pass0Start = Get-Date
    & powershell -ExecutionPolicy Bypass -File "$Pass0Script" -Manifest "$ManifestPath" -PythonExe $PythonExe
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Pass 0 failed (exit $LASTEXITCODE). Continuing..."
    }
    $Pass0Elapsed = [math]::Round(((Get-Date) - $Pass0Start).TotalMinutes, 1)
    Write-Host "  Pass 0 duration: $Pass0Elapsed min"
} else {
    Write-Host "  Pass 0 SKIPPED"
}

# ---- Step 2: Pass 1 ----
if (-not $SkipPass1) {
    Write-Host ""
    Write-Host "--- Step 2: Pass 1 (nsys profiling) ---"
    $Pass1Start = Get-Date
    & powershell -ExecutionPolicy Bypass -File "$Pass1Script" -Manifest "$ManifestPath" -NsysPath "$NsysPath" -PythonExe $PythonExe
    if ($LASTEXITCODE -ne 0) {
        Write-Host "WARNING: Pass 1 failed (exit $LASTEXITCODE)."
    }
    $Pass1Elapsed = [math]::Round(((Get-Date) - $Pass1Start).TotalMinutes, 1)
    Write-Host "  Pass 1 duration: $Pass1Elapsed min"
} else {
    Write-Host "  Pass 1 SKIPPED"
}

$TotalElapsed = [math]::Round(((Get-Date) - $TotalStart).TotalMinutes, 1)
Write-Host ""
Write-Host "=" * 70
Write-Host "  WMPC PILOT COMPLETE ($TotalElapsed min)"
Write-Host "=" * 70
