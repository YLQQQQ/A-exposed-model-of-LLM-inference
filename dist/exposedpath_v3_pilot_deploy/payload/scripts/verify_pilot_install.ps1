<#
.SYNOPSIS
    Verify that the Pilot environment is correctly installed.

.DESCRIPTION
    Checks:
      - Python version (3.10+)
      - Required packages (torch, transformers, pyyaml)
      - CUDA availability
      - nsys in PATH (optional)
      - exposedpath package importable
      - Existing tests pass (optional)

.PARAMETER SkipTests
    Skip running the test suite.

.PARAMETER PythonExe
    Python executable (default: python).

.EXAMPLE
    .\scripts\verify_pilot_install.ps1
#>

param(
    [switch]$SkipTests,

    [string]$PythonExe = "python"
)

$AllOk = $true

Write-Host "=" * 60
Write-Host "  ExposedPath v3 Pilot — Environment Verification"
Write-Host "=" * 60

# ---- Python version ----
Write-Host ""
Write-Host "--- Python ---"
& $PythonExe --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL: Python not found"
    $AllOk = $false
}

# ---- Packages ----
Write-Host ""
Write-Host "--- Required Packages ---"
$Pkgs = @("torch", "transformers", "yaml", "exposedpath")
foreach ($pkg in $Pkgs) {
    $result = & $PythonExe -c "import ${pkg}; print(f'  ${pkg}: {getattr(${pkg}, \"__version__\", \"ok\")}')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host $result
    } else {
        Write-Host "  ${pkg}: NOT FOUND"
        $AllOk = $false
    }
}

# ---- CUDA ----
Write-Host ""
Write-Host "--- CUDA ---"
& $PythonExe -c "import torch; print(f'  CUDA available: {torch.cuda.is_available()}'); print(f'  GPU count: {torch.cuda.device_count()}'); [print(f'  GPU {i}: {torch.cuda.get_device_name(i)}') for i in range(torch.cuda.device_count())]"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  FAIL: CUDA check failed"
    $AllOk = $false
}

# ---- nsys ----
Write-Host ""
Write-Host "--- Nsight Systems ---"
$NsysExe = (Get-Command nsys -ErrorAction SilentlyContinue).Source
if ($NsysExe) {
    & nsys --version 2>&1 | Select-Object -First 1
    Write-Host "  nsys: $NsysExe"
} else {
    Write-Host "  WARNING: nsys not in PATH (required for Pass 1)"
    Write-Host "  Add Nsight Systems target-windows-x64 to PATH before Pass 1."
}

# ---- Tests ----
if (-not $SkipTests) {
    Write-Host ""
    Write-Host "--- Tests ---"
    & $PythonExe -m pytest -q --tb=short
    if ($LASTEXITCODE -ne 0) {
        Write-Host "  WARNING: Some tests failed"
        $AllOk = $false
    }
} else {
    Write-Host ""
    Write-Host "--- Tests SKIPPED ---"
}

# ---- Summary ----
Write-Host ""
Write-Host "=" * 60
if ($AllOk) {
    Write-Host "  VERIFICATION PASSED"
} else {
    Write-Host "  VERIFICATION: SOME CHECKS FAILED"
}
Write-Host "=" * 60

if (-not $AllOk) {
    exit 1
}
exit 0
