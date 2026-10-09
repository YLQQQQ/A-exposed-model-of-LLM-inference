param([switch]$CollectReviewedFormal)
# Delivered outside the frozen checkout. Default is deployment/CPU only.
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management\Microsoft.PowerShell.Management.psd1') -ErrorAction Stop
$ConfigPath=Join-Path $PSScriptRoot 'delivery.json'
$C=Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
if ($C.schema_version -ne 'gate13-signed-delivery/0.1' -or $C.model_process_budget -ne 60 -or $C.profile_budget -ne 30 -or $C.warmup_count -ne 3) { throw 'Closed delivery/budget conflict' }
function SafePath([string]$Base,[string]$Relative) {
    $Root=[IO.Path]::GetFullPath($Base).TrimEnd('\')+'\'
    $Path=[IO.Path]::GetFullPath((Join-Path $Root $Relative))
    if ([IO.Path]::IsPathRooted($Relative) -or !$Path.StartsWith($Root,[StringComparison]::OrdinalIgnoreCase)) { throw 'Path outside root' }
    return $Path
}
function CheckManifest([string]$Root) {
    $Rows=@(Import-Csv -LiteralPath (Join-Path $Root 'artifact_sha256.csv'));$Seen=@{}
    if (!$Rows.Count) { throw 'Empty manifest' }
    foreach ($F in $Rows) {
        $P=SafePath $Root $F.path
        if ($Seen.ContainsKey($P) -or !(Test-Path -LiteralPath $P -PathType Leaf)) { throw 'Duplicate/missing artifact' }
        $Seen[$P]=$true
        if ((Get-Item -LiteralPath $P).Length -ne [long]$F.bytes -or (Get-FileHash -LiteralPath $P).Hash -ne $F.sha256) { throw ('Artifact identity conflict: '+$F.path) }
    }
    if (@(Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object {$_.FullName -ne (Join-Path $Root 'artifact_sha256.csv')}).Count -ne $Rows.Count) { throw 'Unlisted artifacts' }
}
CheckManifest $PSScriptRoot
$Code=$C.code_root;$Target=$C.commit
$Static=Join-Path $C.server_root ('logs\gate13_'+$Target.Substring(0,12)+'_static')
$Out=if ($CollectReviewedFormal) {Join-Path $C.server_root ('evidence\gate13\'+$C.batch_id)} else {$Static}
$Kind=if ($CollectReviewedFormal) {'formal'} else {'static'}
$Zip=Join-Path $C.server_root ('transfer\gate13_'+$Target.Substring(0,12)+'_'+$Kind+'.zip')
if ((Test-Path -LiteralPath $Out) -or (Test-Path -LiteralPath $Zip)) { throw 'No resume/overwrite/retry' }
New-Item -ItemType Directory -Path $Out | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $Out 'executed.ps1')
Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $Out 'delivery.json')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'signed_release.json') -Destination (Join-Path $Out 'signed_release.json')
Start-Transcript -LiteralPath (Join-Path $Out 'transcript.txt') | Out-Null
$Status='BLOCKED';$Failure=$null;$StaticHash=$null
function Run([string]$Exe,[string[]]$Argv,[string]$Name) {
    $Saved=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue';$global:LASTEXITCODE=$null
        & $Exe @Argv 2>&1 | Tee-Object -FilePath (Join-Path $Out ($Name+'.log')) | ForEach-Object {Write-Host $_}
        $Exit=$LASTEXITCODE
    } finally {$ErrorActionPreference=$Saved}
    [ordered]@{executable=$Exe;argv=$Argv;exit_code=$Exit} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out ($Name+'.exit.json')) -Encoding utf8
    if ($null -eq $Exit -or $Exit -ne 0) { throw ($Name+' failed; STOP; no retry; exit='+$Exit) }
}
function Tree([string]$Want) {
    $H=& git -C $Code rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $H -ne $Want) {throw 'HEAD conflict'}
    $S=@(& git -C $Code status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $S.Count) {throw 'Dirty tree'}
}
function Sources {
    $Rows=@()
    foreach ($F in $C.source_representations.PSObject.Properties) {
        $P=SafePath $Code $F.Name
        if (!(Test-Path -LiteralPath $P -PathType Leaf)) {throw ('SOURCE_MISSING: '+$F.Name)}
        $Hash=(Get-FileHash -LiteralPath $P).Hash;$Bytes=(Get-Item -LiteralPath $P).Length
        $Match=@($F.Value | Where-Object {$_.sha256 -eq $Hash -and $_.bytes -eq $Bytes})
        $Rows+=[ordered]@{path=$F.Name;actual_sha256=$Hash;actual_bytes=$Bytes;expected=$F.Value;matched=$Match.Count -gt 0}
        $Rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out 'source_bytes.json') -Encoding utf8
        if (!$Match.Count) {throw ('SOURCE_BYTES_CONFLICT: '+$F.Name)}
    }
}
try {
    $Python=Join-Path $Code '.venv\Scripts\python.exe'
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID';$env:CUDA_VISIBLE_DEVICES='-1';$env:PYTHONDONTWRITEBYTECODE='1'
    Set-Location -LiteralPath $Code
    if (!$CollectReviewedFormal) {
        Tree $C.prerequisite
        $Bundle=SafePath $PSScriptRoot $C.bundle
        if ((Get-Item -LiteralPath $Bundle).Length -ne $C.bundle_bytes -or (Get-FileHash -LiteralPath $Bundle).Hash -ne $C.bundle_sha256) {throw 'Bundle identity conflict'}
        Run 'git' @('bundle','verify',$Bundle) '01_bundle'
        Run 'git' @('fetch',$Bundle,($C.bundle_ref+':refs/remotes/gate13-delivery/execution')) '02_fetch'
        Run 'git' @('-c','core.autocrlf=false','checkout','--detach',$Target) '03_checkout'
        Tree $Target;Sources
        Run $Python @('-X','utf8',(Join-Path $PSScriptRoot 'gate13_validate_delivery.py'),'--config',$ConfigPath) '04_cpu_delivery'
        Tree $Target
        $Status='STATIC_READY_FOR_COORDINATOR_REVIEW'
    } else {
        Tree $Target;CheckManifest $Static
        $R=Get-Content -LiteralPath (Join-Path $Static 'receipt.json') -Raw | ConvertFrom-Json
        if ($R.status -ne 'STATIC_READY_FOR_COORDINATOR_REVIEW' -or $R.execution_commit -ne $Target -or $R.delivery_sha256 -ne (Get-FileHash -LiteralPath $ConfigPath).Hash) {throw 'Static receipt conflict'}
        $StaticHash=(Get-FileHash -LiteralPath (Join-Path $Static 'receipt.json')).Hash
        Copy-Item -LiteralPath $Static -Destination (Join-Path $Out 'static') -Recurse
        Sources
        if ([IO.DriveInfo]::new([IO.Path]::GetPathRoot($Out)).AvailableFreeSpace -lt 90GB) {throw '90GB free required; never delete old evidence to proceed'}
        $env:CUDA_VISIBLE_DEVICES='3';$env:HF_HUB_OFFLINE='1';$env:TRANSFORMERS_OFFLINE='1'
        if ((Get-FileHash -LiteralPath $C.nsys).Hash -ne $C.nsys_sha256) {throw 'Collector binary changed'}
        Run $C.nsys @('--version') '05_nsys'
        $Identity=@'
import sys,json,torch,transformers
assert sys.version_info[:3]==(3,11,16)
assert torch.__version__=='2.6.0+cu124' and torch.version.cuda=='12.4'
assert transformers.__version__=='5.17.0'
print(json.dumps(dict(python=sys.version,executable=sys.executable,torch=torch.__version__,cuda=torch.version.cuda,transformers=transformers.__version__)))
'@
        Run $Python @('-X','utf8','-c',$Identity) '06_environment'
        $Gpu=@(& nvidia-smi '--id=3' '--query-gpu=index,uuid,pci.bus_id,name,driver_version' '--format=csv,noheader,nounits')
        if ($LASTEXITCODE -ne 0 -or $Gpu.Count -ne 1) {throw 'GPU query failure'}
        $Gpu | Out-File -LiteralPath (Join-Path $Out 'gpu_identity.txt') -Encoding utf8
        $G=@($Gpu[0].Split(',') | ForEach-Object {$_.Trim()})
        if ($G[0] -ne '3' -or $G[1] -ne $C.gpu_uuid -or $G[2] -ine $C.gpu_pci_bus_id -or $G[4] -ne '555.99') {throw 'GPU identity/driver conflict'}
        foreach ($Name in @('prompt_tokens.json','prompt_512.json','model_sha256.csv','gate13_formal_batch.py','gate13_retention.py')) {
            Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination (Join-Path $Out $Name)
        }
        $C | Add-Member -NotePropertyName prompt -NotePropertyValue (Join-Path $Out 'prompt_tokens.json')
        $C | Add-Member -NotePropertyName prompt_512 -NotePropertyValue (Join-Path $Out 'prompt_512.json')
        $C | Add-Member -NotePropertyName inventory -NotePropertyValue (Join-Path $Out 'model_sha256.csv')
        $C | Add-Member -NotePropertyName signed_release -NotePropertyValue (Join-Path $Out 'signed_release.json')
        $Config=Join-Path $Out 'run_config.json'
        $C | ConvertTo-Json -Depth 14 | Set-Content -LiteralPath $Config -Encoding utf8
        $Controller=Join-Path $Out 'gate13_formal_batch.py';$Batch=Join-Path $Out 'batch'
        # An activity lock prohibits all packing and cleaning until controlled exit.
        $Lock=Join-Path $Out '.active';Set-Content -LiteralPath $Lock -Value $PID
        try {
            Run $Python @('-X','utf8','-u',$Controller,'--config',$Config,'--output',$Batch,'--batch-id',$C.batch_id,'--execute-reviewed-signed-formal') '07_batch'
        } finally {Remove-Item -LiteralPath $Lock}
        $BR=Get-Content -LiteralPath (Join-Path $Batch 'batch_report.json') -Raw | ConvertFrom-Json
        if ($BR.status -ne 'FORMAL_BATCH_COMPLETE_STOP_FOR_REVIEW' -or $BR.runs.Count -ne 60 -or $BR.pairs.Count -ne 30) {throw 'Machine report incomplete'}
        Tree $Target
        $Status='FORMAL_BATCH_COMPLETE_STOP_FOR_REVIEW'
    }
} catch {$Failure=$_.ToString();Write-Host ('STOP: '+$Failure)}
finally {
    [ordered]@{status=$Status;error=$Failure;execution_commit=$Target;analysis_commit=$Target;delivery_sha256=(Get-FileHash -LiteralPath $ConfigPath).Hash;static_receipt_sha256=$StaticHash;gate12='PASS_LIMITED_ROUTE_A';gate13='NOT_RUN';automatic_retry=$false;model_process_budget=60;profile_budget=30;measurement_validity='NOT_ASSESSED';dropped_records_status='UNKNOWN'} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Out 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
}
# Full single ZIP, only after all recorded writers exited. Unknown descendants
# or a live recorded PID refuse packaging; never kill a name-wide process list.
& $Python '-X' 'utf8' (Join-Path $PSScriptRoot 'gate13_retention.py') 'pack' '--root' $Out '--archive' $Zip
if ($LASTEXITCODE -ne 0) {throw 'Packaging refused; preserve scene and report logs; no retry/cleanup'}
Write-Host ('ZIP='+$Zip)
if ($Status -eq 'BLOCKED') {throw 'Return failure ZIP; no retry or replacement run'}
