param(
    [ValidateSet('prepare','execute','verify')][string]$Action = 'prepare',
    [Parameter(Mandatory=$true)][string]$DeliveryIndexSha256
)
$ErrorActionPreference = 'Stop'
if ($DeliveryIndexSha256 -notmatch '^[0-9a-fA-F]{64}$') { throw 'Invalid reviewed index hash; STOP' }
$Index = Join-Path $PSScriptRoot 'file_index.json'
if ((Get-FileHash -LiteralPath $Index -Algorithm SHA256).Hash -ne $DeliveryIndexSha256) {
    throw 'Repair delivery index conflict; STOP'
}
$Value = Get-Content -LiteralPath $Index -Raw | ConvertFrom-Json
if ($Value.schema_version -cne 'coe-controlled-repair-index/0.1.1') { throw 'Repair index version conflict; STOP' }
foreach ($Name in @('coe_controlled_deployment.py','original/delivery.json')) {
    $Rows = @($Value.files | Where-Object { $_.path -ceq $Name })
    if ($Rows.Count -ne 1) { throw 'Required entry/config identity missing or duplicated; STOP' }
    $Path = Join-Path $PSScriptRoot $Name
    if ((Get-Item -LiteralPath $Path).Length -ne $Rows[0].bytes -or
        (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Rows[0].sha256) {
        throw 'Repair entry/config identity conflict; STOP'
    }
}
$Original = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'original/delivery.json') -Raw | ConvertFrom-Json
$Python = $Original.target_python
$Entry = Join-Path $PSScriptRoot 'coe_controlled_deployment.py'
# No encoding conversion, Python import override, CUDA initialization or automatic next action here.
& $Python -I -S -B $Entry $Action --index-sha256 ($DeliveryIndexSha256.ToLowerInvariant())
if ($LASTEXITCODE -ne 0) {
    throw 'Repair attempt failed; preserve old/new evidence; no retry, replacement, cleanup or automatic execute'
}
