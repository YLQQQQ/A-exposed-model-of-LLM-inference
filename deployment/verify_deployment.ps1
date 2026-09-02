<#
.SYNOPSIS
    Verify an ExposedPath v3 Pilot server deployment.

.DESCRIPTION
    Checks every file in SERVER_SYNC_MANIFEST.json:
      - file exists on disk
      - SHA-256 matches expected value
      - Python packages importable
      - PowerShell scripts parseable

    NEVER modifies files.  Returns non-zero on any failure.

.PARAMETER ProjectRoot
    Absolute path to the deployed project root.

.EXAMPLE
    .\deployment\verify_deployment.ps1 -ProjectRoot "D:\A-exposed-model-of-LLM-inference"
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot
)

$ErrorActionPreference = "Continue"
$DeployRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = Split-Path -Parent $DeployRoot
$ManifestFile = Join-Path $PackageRoot "SERVER_SYNC_MANIFEST.json"

if (-not (Test-Path $ProjectRoot -PathType Container)) {
    Write-Host "ERROR: ProjectRoot does not exist: $ProjectRoot"
    exit 1
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

if (-not (Test-Path $ManifestFile)) {
    Write-Host "ERROR: SERVER_SYNC_MANIFEST.json not found at: $ManifestFile"
    exit 1
}

$Manifest = Get-Content $ManifestFile -Raw | ConvertFrom-Json
$AllOk = $true
$Checked = 0
$Failed = 0

Write-Host "============================================"
Write-Host "  ExposedPath v3 Pilot — Deployment Verification"
Write-Host "============================================"
Write-Host "  ProjectRoot: $ProjectRoot"
Write-Host ""

function Check-Entry {
    param($Entry, [string]$Kind)
    $relPath  = $Entry.path
    $expected = $Entry.sha256
    $dst = Join-Path $ProjectRoot $relPath

    $Checked++
    if (-not (Test-Path $dst)) {
        Write-Host "  MISSING [$Kind] $relPath"
        $script:Failed++
        $script:AllOk = $false
        return
    }
    $actual = (Get-FileHash -Path $dst -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $expected) {
        Write-Host "  SHA MISMATCH [$Kind] $relPath"
        Write-Host "    expected: $expected"
        Write-Host "    actual:   $actual"
        $script:Failed++
        $script:AllOk = $false
    } else {
        Write-Host "  OK [$Kind] $relPath"
    }
}

if ($Manifest.modified) { foreach ($e in $Manifest.modified) { Check-Entry $e "MODIFIED" } }
if ($Manifest.added)   { foreach ($e in $Manifest.added)   { Check-Entry $e "ADDED" } }
if ($Manifest.renamed) { foreach ($e in $Manifest.renamed) { Check-Entry $e "RENAMED" } }

Write-Host ""
Write-Host "  Files checked: $Checked, Failed: $Failed"

# ---- Python import ----
Write-Host ""
Write-Host "--- Python import check ---"
Push-Location $ProjectRoot
$import_out = & python -c "import exposedpath; print('exposedpath', exposedpath.__version__)" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  exposedpath: OK ($import_out)"
} else {
    Write-Host "  exposedpath: FAILED"
    $AllOk = $false
}
Pop-Location

# ---- PowerShell syntax ----
Write-Host ""
Write-Host "--- PowerShell syntax check ---"
$PsScripts = @(
    "scripts\run_pass0.ps1", "scripts\run_pass1_nsys.ps1",
    "scripts\run_server_smoke_test.ps1", "scripts\run_wmpc_pilot.ps1",
    "scripts\verify_pilot_install.ps1"
)
foreach ($ps in $PsScripts) {
    $psPath = Join-Path $ProjectRoot $ps
    if (Test-Path $psPath) {
        # Load script to check for parse errors
        $err = $null
        try { $null = [System.Management.Automation.Language.Parser]::ParseFile($psPath, [ref]$null, [ref]$err) }
        catch { $err = $_.Exception.Message }
        if ($err) {
            Write-Host "  $ps : PARSE ERROR — $err"
            $AllOk = $false
        } else {
            Write-Host "  $ps : OK"
        }
    }
}

Write-Host ""
Write-Host "============================================"
if ($AllOk) {
    Write-Host "  VERIFICATION: PASS"
} else {
    Write-Host "  VERIFICATION: FAIL"
}
Write-Host "============================================"

if (-not $AllOk) { exit 1 }
exit 0
