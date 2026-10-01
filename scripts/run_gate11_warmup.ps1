param([switch]$RunReviewedWarmupControl)
# Default: fixed deployment and related CPU checks. Never model execution.
$ErrorActionPreference='Stop'
$ConfigPath=Join-Path $PSScriptRoot 'delivery.json'
$C=Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
if ($C.schema_version -ne 'gate11-warmup-delivery/0.1' -or $C.warmup_control_version -ne 'G11-WARMUP-CONTROL/0.1') { throw 'Unknown delivery version' }
$Code=$C.code_root; $Target=$C.commit
function SafePath([string]$Base,[string]$Relative) {
    $Root=[IO.Path]::GetFullPath($Base).TrimEnd('\')+'\'
    $Path=[IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if ([IO.Path]::IsPathRooted($Relative) -or !$Path.StartsWith($Root,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside allowed root' }
    return $Path
}
function CheckManifest([string]$Root) {
    $Rows=@(Import-Csv -LiteralPath (Join-Path $Root 'artifact_sha256.csv')); $Seen=@{}
    if (!$Rows.Count) { throw 'Empty file manifest' }
    foreach ($F in $Rows) {
        $P=SafePath $Root $F.path
        if ($Seen.ContainsKey($P) -or !(Test-Path -LiteralPath $P -PathType Leaf)) { throw ('Duplicate/missing file: '+$F.path) }
        $Seen[$P]=$true
        if ((Get-Item -LiteralPath $P).Length -ne [long]$F.bytes -or (Get-FileHash -LiteralPath $P).Hash -ne $F.sha256) { throw ('File identity conflict: '+$F.path) }
    }
    $Actual=@(Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object {$_.FullName -ne (Join-Path $Root 'artifact_sha256.csv')})
    if ($Actual.Count -ne $Rows.Count) { throw 'Unlisted delivery files' }
}
CheckManifest $PSScriptRoot
$Static=Join-Path $C.server_root ('logs\gate11_warmup_'+$Target.Substring(0,12)+'_static')
$Phase=if ($RunReviewedWarmupControl) {'warmup'} else {'static'}
$Out=if ($RunReviewedWarmupControl) {Join-Path $C.server_root ('evidence\gate11\'+$Target.Substring(0,12)+'_warmup_control')} else {$Static}
$Zip=Join-Path $C.server_root ('transfer\gate11_warmup_'+$Target.Substring(0,12)+'_'+$Phase+'.zip')
if ((Test-Path -LiteralPath $Out) -or (Test-Path -LiteralPath $Zip)) { throw 'No resume, overwrite or retry' }
New-Item -ItemType Directory -Path $Out | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $Out 'executed.ps1')
Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $Out 'delivery.json')
Start-Transcript -LiteralPath (Join-Path $Out 'transcript.txt') | Out-Null
$Status='BLOCKED'; $Failure=$null; $StaticHash=$null
function Run([string]$Exe,[string[]]$Argv,[string]$Name) {
    $Saved=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue'; $global:LASTEXITCODE=$null
        & $Exe @Argv 2>&1 | Tee-Object -FilePath (Join-Path $Out ($Name+'.log')) | ForEach-Object { Write-Host $_ }
        $Exit=$LASTEXITCODE
    } finally { $ErrorActionPreference=$Saved }
    [ordered]@{executable=$Exe;argv=$Argv;exit_code=$Exit} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out ($Name+'.exit.json')) -Encoding utf8
    if ($null -eq $Exit -or $Exit -ne 0) { throw ($Name+' failed; no retry; exit='+$Exit) }
}
function Tree([string]$Want) {
    $H=& git -C $Code rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $H -ne $Want) { throw 'HEAD mismatch' }
    $S=@(& git -C $Code status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $S.Count -ne 0) { throw 'Dirty tree' }
}
function Sources {
    $Rows=@()
    foreach ($F in $C.source_representations.PSObject.Properties) {
        $P=SafePath $Code $F.Name
        if (!(Test-Path -LiteralPath $P -PathType Leaf)) { throw ('SOURCE_MISSING: '+$F.Name) }
        $ActualHash=(Get-FileHash -LiteralPath $P).Hash; $ActualBytes=(Get-Item -LiteralPath $P).Length
        $Match=@($F.Value | Where-Object {$_.sha256 -eq $ActualHash -and $_.bytes -eq $ActualBytes})
        $Rows+=[ordered]@{path=$F.Name;actual_sha256=$ActualHash;actual_bytes=$ActualBytes;expected=$F.Value;matched=$Match.Count -gt 0}
        $Rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out 'source_bytes.json') -Encoding utf8
        if (!$Match.Count) { throw ('SOURCE_BYTES_CONFLICT: '+$F.Name) }
    }
}
try {
    $Python=Join-Path $Code '.venv\Scripts\python.exe'
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID'; $env:CUDA_VISIBLE_DEVICES='-1'
    Set-Location -LiteralPath $Code
    if (!$RunReviewedWarmupControl) {
        Tree $C.prerequisite
        $Bundle=SafePath $PSScriptRoot $C.bundle
        if ((Get-Item -LiteralPath $Bundle).Length -ne $C.bundle_bytes -or (Get-FileHash -LiteralPath $Bundle).Hash -ne $C.bundle_sha256) { throw 'Bundle conflict' }
        Run 'git' @('bundle','verify',$Bundle) '01_bundle'
        Run 'git' @('fetch',$Bundle,'refs/heads/main:refs/remotes/gate11-warmup/main') '02_fetch'
        $H=& git rev-parse refs/remotes/gate11-warmup/main
        if ($LASTEXITCODE -ne 0 -or $H -ne $Target) { throw 'Fetched commit conflict' }
        Run 'git' @('-c','core.autocrlf=false','checkout','--detach',$Target) '03_checkout'
        Tree $Target; Sources
        Run $Python (@('-m','pytest','-q','-p','no:cacheprovider')+@($C.tests)) '04_cpu'
        Tree $Target
        $Status='STATIC_READY_FOR_REVIEW'
    } else {
        Tree $Target; CheckManifest $Static
        $R=Get-Content -LiteralPath (Join-Path $Static 'receipt.json') -Raw | ConvertFrom-Json
        if ($R.status -ne 'STATIC_READY_FOR_REVIEW' -or $R.commit -ne $Target -or $R.delivery_sha256 -ne (Get-FileHash -LiteralPath $ConfigPath).Hash) { throw 'Reviewed static receipt mismatch' }
        $StaticHash=(Get-FileHash -LiteralPath (Join-Path $Static 'receipt.json')).Hash
        Copy-Item -LiteralPath $Static -Destination (Join-Path $Out 'static') -Recurse
        Sources
        if ([IO.DriveInfo]::new([IO.Path]::GetPathRoot($Out)).AvailableFreeSpace -lt 512MB) { throw 'Reserve at least 0.5GB; do not delete evidence' }
        $env:CUDA_VISIBLE_DEVICES='3'; $env:HF_HUB_OFFLINE='1'; $env:TRANSFORMERS_OFFLINE='1'
        $Identity=@'
import sys,json,torch,transformers
assert sys.version_info[:3]==(3,11,16)
assert torch.__version__=='2.6.0+cu124' and torch.version.cuda=='12.4'
assert transformers.__version__=='5.17.0'
print(json.dumps(dict(python=sys.version,executable=sys.executable,torch=torch.__version__,cuda=torch.version.cuda,transformers=transformers.__version__)))
'@
        Run $Python @('-c',$Identity) '05_environment'
        $Gpu=@(& nvidia-smi '--id=3' '--query-gpu=index,uuid,pci.bus_id,name,driver_version' '--format=csv,noheader,nounits')
        if ($LASTEXITCODE -ne 0 -or $Gpu.Count -ne 1) { throw 'GPU query failed' }
        $Gpu | Out-File -LiteralPath (Join-Path $Out 'gpu_identity.txt') -Encoding utf8
        $G=@($Gpu[0].Split(',') | ForEach-Object {$_.Trim()})
        if ($G[0] -ne '3' -or $G[1] -ne $C.gpu_uuid -or $G[2] -ine $C.gpu_pci_bus_id -or $G[4] -ne '555.99') { throw 'GPU/driver conflict' }
        foreach ($Name in @('prompt_tokens.json','prompt_512.json','model_sha256.csv')) {
            Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination (Join-Path $Out $Name)
        }
        $C | Add-Member -NotePropertyName prompt -NotePropertyValue (Join-Path $Out 'prompt_tokens.json')
        $C | Add-Member -NotePropertyName prompt_512 -NotePropertyValue (Join-Path $Out 'prompt_512.json')
        $C | Add-Member -NotePropertyName inventory -NotePropertyValue (Join-Path $Out 'model_sha256.csv')
        $Config=Join-Path $Out 'run_config.json'
        $C | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath $Config -Encoding utf8
        Run $Python @('-u','scripts/gate11_warmup_batch.py','--config',$Config,'--output',(Join-Path $Out 'batch'),'--batch-id',('warmup-'+$Target.Substring(0,12)+'-control'),'--execute-reviewed-warmup-control') '06_batch'
        $R=Get-Content -LiteralPath (Join-Path $Out 'batch\batch_report.json') -Raw | ConvertFrom-Json
        if ($R.status -ne 'WARMUP_BATCH_COMPLETE_STOP_FOR_REVIEW' -or $R.runs.Count -ne 30 -or $R.pairs.Count -ne 15 -or $R.gate11_verdict -ne 'BLOCKED') { throw 'Machine batch report not complete' }
        Tree $Target
        $Status='WARMUP_BATCH_COMPLETE_STOP_FOR_REVIEW'
    }
} catch { $Failure=$_.ToString(); Write-Host ('STOP: '+$Failure) }
finally {
    [ordered]@{status=$Status;error=$Failure;commit=$Target;delivery_sha256=(Get-FileHash -LiteralPath $ConfigPath).Hash;static_receipt_sha256=$StaticHash;gate11='BLOCKED';formal_eligible=$false;automatic_retry=$false;model_process_budget=30;profile_budget=0;overall_cap=60;additional_budget_authorized=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Out 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
}
foreach ($P in @(Get-ChildItem -LiteralPath $Out -Recurse -File -Filter 'process.json')) {
    $V=Get-Content -LiteralPath $P.FullName -Raw | ConvertFrom-Json
    if ($V.descendant_exit_status -eq 'UNKNOWN_STOP_AND_INSPECT_NO_RETRY') { throw 'Possible live writer: stop packaging; do not kill unrelated processes' }
}
$Files=@(Get-ChildItem -LiteralPath $Out -Recurse -File)
$Rows=@($Files | ForEach-Object {[pscustomobject]@{path=$_.FullName.Substring($Out.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
$Index=Join-Path $Out 'artifact_sha256.csv'
$Rows | Export-Csv -LiteralPath $Index -NoTypeInformation -Encoding utf8
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($Out,$Zip,[IO.Compression.CompressionLevel]::Optimal,$false)
Write-Host ('STATUS='+$Status); Write-Host ('ZIP='+$Zip)
Write-Host ('ZIP_BYTES='+(Get-Item -LiteralPath $Zip).Length)
Write-Host ('ZIP_SHA256='+(Get-FileHash -LiteralPath $Zip).Hash)
Write-Host ('MANIFEST_SHA256='+(Get-FileHash -LiteralPath $Index).Hash)
if ($Status -eq 'BLOCKED') { throw 'Return the single ZIP; no retry' }
