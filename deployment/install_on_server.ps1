<#
.SYNOPSIS
    Install ExposedPath v3 Pilot files onto a Windows GPU server.

.DESCRIPTION
    Reads SERVER_SYNC_MANIFEST.json from the deployment package, backs up any
    existing files that would be overwritten, copies all payload files while
    preserving relative paths, and verifies every SHA-256 after copy.

    After installation, runs (unless -SkipTests):
      - python -m exposedpath --help
      - python -m pytest -q
      - python -m compileall exposedpath analysis
      - .\scripts\verify_pilot_install.ps1

    NEVER deletes any files on the server.  All modifications are additive.
    Historical results/, model files, DOCX, traces, and SQLite are untouched.

.PARAMETER ProjectRoot
    Absolute path to the existing project root on the server.

.PARAMETER BackupRoot
    Directory for backups.  Defaults to <ProjectRoot>_backup_<UTC> one level
    above ProjectRoot.

.PARAMETER SkipTests
    Skip pytest and compileall after installation (SHA-256 verification still runs).

.EXAMPLE
    .\deployment\install_on_server.ps1 `
        -ProjectRoot "D:\A-exposed-model-of-LLM-inference"

.EXAMPLE
    .\deployment\install_on_server.ps1 `
        -ProjectRoot "D:\A-exposed-model-of-LLM-inference" `
        -BackupRoot "E:\backups" -SkipTests
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectRoot,

    [string]$BackupRoot = "",

    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$DeployRoot = Split-Path -Parent $MyInvocation.MyCommand.Path  # deployment/
$PackageRoot = Split-Path -Parent $DeployRoot                   # dist/.../
$PayloadDir = Join-Path $PackageRoot "payload"
$ManifestFile = Join-Path $PackageRoot "SERVER_SYNC_MANIFEST.json"

# ---- Validate ProjectRoot ----
if (-not (Test-Path $ProjectRoot -PathType Container)) {
    Write-Host "ERROR: ProjectRoot does not exist: $ProjectRoot"
    Write-Host "  Create the project directory and clone/populate it first, then re-run."
    exit 1
}
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

# ---- Validate manifest ----
if (-not (Test-Path $ManifestFile)) {
    Write-Host "ERROR: SERVER_SYNC_MANIFEST.json not found at: $ManifestFile"
    exit 1
}
$Manifest = Get-Content $ManifestFile -Raw | ConvertFrom-Json

# ---- Backup directory ----
if (-not $BackupRoot) {
    $Parent = Split-Path -Parent $ProjectRoot
    $Ts = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
    $BackupRoot = Join-Path $Parent "${Ts}_backup"
}
New-Item -ItemType Directory -Force -Path $BackupRoot | Out-Null

# ---- Logging ----
$LogPath = Join-Path $BackupRoot "deploy_$(Get-Date -Format 'yyyyMMdd_HHmmss').log"
function Write-Log { param([string]$Msg); Write-Host $Msg; $Msg | Out-File -Append -FilePath $LogPath -Encoding utf8 }

Write-Log "============================================"
Write-Log "ExposedPath v3 Pilot — Server Installation"
Write-Log "============================================"
Write-Log "  ProjectRoot: $ProjectRoot"
Write-Log "  PackageRoot: $PackageRoot"
Write-Log "  BackupRoot:  $BackupRoot"
Write-Log "  Started:     $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
Write-Log ""

# ---- Helper: classify a manifest entry ----
function Copy-FileEntry {
    param($Entry, [string]$Kind)
    $relPath   = $Entry.path
    $expected  = $Entry.sha256
    $action    = $Entry.server_action

    $src  = Join-Path $PayloadDir $relPath
    $dst  = Join-Path $ProjectRoot $relPath

    if (-not (Test-Path $src)) {
        Write-Log "  MISSING in payload: $relPath"
        exit 2
    }

    # ---- Backup existing ----
    if (Test-Path $dst) {
        $backupDst = Join-Path $BackupRoot $relPath
        $backupDir = Split-Path -Parent $backupDst
        New-Item -ItemType Directory -Force -Path $backupDir | Out-Null
        Copy-Item -Path $dst -Destination $backupDst -Force
        Write-Log "  BACKED UP: $relPath -> $backupDst"
    }

    # ---- Create parent directory ----
    $dstDir = Split-Path -Parent $dst
    if (-not (Test-Path $dstDir)) {
        New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
    }

    # ---- Copy ----
    Copy-Item -Path $src -Destination $dst -Force

    # ---- Verify SHA-256 ----
    $actual = (Get-FileHash -Path $dst -Algorithm SHA256).Hash.ToLower()
    if ($actual -ne $expected) {
        Write-Log "  FATAL: SHA-256 MISMATCH for $relPath"
        Write-Log "    expected: $expected"
        Write-Log "    actual:   $actual"
        Write-Log "  Restore from: $BackupRoot"
        exit 3
    }
    Write-Log "  OK [$Kind] $relPath"
}

# ---- Process all entries ----
$Total = 0
if ($Manifest.modified) {
    foreach ($entry in $Manifest.modified) { Copy-FileEntry $entry "MODIFIED"; $Total++ }
}
if ($Manifest.added) {
    foreach ($entry in $Manifest.added)   { Copy-FileEntry $entry "ADDED"; $Total++ }
}
if ($Manifest.renamed) {
    foreach ($entry in $Manifest.renamed) { Copy-FileEntry $entry "RENAMED"; $Total++ }
}

Write-Log ""
Write-Log "  All $Total files copied and verified."

# ---- Post-install verification ----
Write-Log ""
Write-Log "============================================"
Write-Log "Post-install checks"
Write-Log "============================================"

Push-Location $ProjectRoot

# 1) CLI help
Write-Log ""
Write-Log "--- python -m exposedpath --help ---"
$help_out = & python -m exposedpath --help 2>&1
$help_rc = $LASTEXITCODE
$help_out -join "`n" | Out-File -Append -FilePath $LogPath -Encoding utf8
Write-Log "  CLI help: $(if ($help_rc -eq 0) { 'PASS' } else { "FAIL (rc=$help_rc)" })"

# 2) pytest
if (-not $SkipTests) {
    Write-Log ""
    Write-Log "--- python -m pytest -q ---"
    $pytest_out = & python -m pytest -q 2>&1
    $pytest_rc = $LASTEXITCODE
    $pytest_out -join "`n" | Out-File -Append -FilePath $LogPath -Encoding utf8
    Write-Log "  pytest: $(if ($pytest_rc -eq 0) { 'PASS' } else { "FAIL (rc=$pytest_rc)" })"

    Write-Log ""
    Write-Log "--- python -m compileall exposedpath analysis ---"
    & python -m compileall -q exposedpath analysis 2>&1 | Out-File -Append -FilePath $LogPath -Encoding utf8
    Write-Log "  compileall: $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { 'FAIL' })"
}

# 3) verify script
if (Test-Path (Join-Path $ProjectRoot "scripts\verify_pilot_install.ps1")) {
    Write-Log ""
    Write-Log "--- verify_pilot_install.ps1 ---"
    $vArgs = @("-ExecutionPolicy", "Bypass", "-File", ".\scripts\verify_pilot_install.ps1")
    if ($SkipTests) { $vArgs += "-SkipTests" }
    & powershell @vArgs 2>&1 | Out-File -Append -FilePath $LogPath -Encoding utf8
    Write-Log "  verify_pilot_install: $(if ($LASTEXITCODE -eq 0) { 'PASS' } else { "WARN (rc=$LASTEXITCODE)" })"
}

Pop-Location

# ---- Summary ----
Write-Log ""
Write-Log "============================================"
Write-Log "INSTALLATION COMPLETE"
Write-Log "============================================"
Write-Log "  ProjectRoot: $ProjectRoot"
Write-Log "  Backup:      $BackupRoot"
Write-Log "  Log:         $LogPath"
Write-Log ""
Write-Log "  Rollback command:"
Write-Log "    robocopy `"$BackupRoot`" `"$ProjectRoot`" /E /IS /IT"
Write-Log ""
Write-Log "  Verify deployment:"
Write-Log "    .\deployment\verify_deployment.ps1 -ProjectRoot `"$ProjectRoot`""
Write-Log ""
Write-Log "  Smoke test (dry run):"
Write-Log "    .\scripts\run_server_smoke_test.ps1 -ModelPath `"<model>`" -GpuId 0 -NsysPath `"<nsys>`" -DryRun"

exit 0
