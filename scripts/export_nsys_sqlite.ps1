<#
.SYNOPSIS
    Export all .nsys-rep files in a directory tree to .sqlite.

.DESCRIPTION
    Recursively searches for .nsys-rep files under the given root directory
    and runs 'nsys export --type sqlite' for each one.

    The .sqlite file is placed in the same directory as the .nsys-rep file.

.PARAMETER ResultsDir
    Root directory to search for .nsys-rep files.

.EXAMPLE
    .\scripts\export_nsys_sqlite.ps1 -ResultsDir "nsys_results"
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ResultsDir
)

Write-Host "============================================"
Write-Host "[export_nsys_sqlite] NSYS SQLite Export"
Write-Host "============================================"
Write-Host "  Search dir: $ResultsDir"

# ---- Find all .nsys-rep files ----
$NsysRepFiles = Get-ChildItem -Path $ResultsDir -Recurse -Filter "*.nsys-rep" -File

if ($NsysRepFiles.Count -eq 0) {
    Write-Host "[export_nsys_sqlite] WARNING: No .nsys-rep files found under $ResultsDir"
    exit 0
}

Write-Host "[export_nsys_sqlite] Found $($NsysRepFiles.Count) .nsys-rep file(s)"
Write-Host ""

$Exported = 0
$Failed = 0

foreach ($RepFile in $NsysRepFiles) {
    $RepPath = $RepFile.FullName
    $RepDir = $RepFile.DirectoryName
    $BaseName = $RepFile.BaseName

    $SqlitePath = Join-Path $RepDir "$BaseName.sqlite"

    Write-Host "----------------------------------------"
    Write-Host "[export_nsys_sqlite] Exporting: $RepPath"
    Write-Host "  Output: $SqlitePath"

    # Check if sqlite already exists
    if (Test-Path $SqlitePath) {
        Write-Host "  WARNING: .sqlite already exists, overwriting..."
        Remove-Item $SqlitePath -Force
    }

    # Run nsys export
    nsys export --type sqlite --output "$SqlitePath" "$RepPath"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "  SUCCESS"
        $Exported++
    } else {
        Write-Host "  FAILED (exit code: $LASTEXITCODE)"
        $Failed++
    }
}

Write-Host ""
Write-Host "============================================"
Write-Host "[export_nsys_sqlite] DONE"
Write-Host "  Exported: $Exported"
Write-Host "  Failed:   $Failed"
Write-Host "============================================"
