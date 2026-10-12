param([switch]$CollectReviewedEngineering)
# Prospective Engineering only. Default stage A never queries CUDA or launches a model.
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management\Microsoft.PowerShell.Management.psd1') -ErrorAction Stop
$ConfigPath=Join-Path $PSScriptRoot 'delivery.json'
$C=Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
$Remaining=$C.schema_version -eq 'completion-path-remaining-delivery/0.1'
$Budget=if ($Remaining) {1} else {2}
if ($C.schema_version -notin @('completion-path-delivery/0.1','completion-path-remaining-delivery/0.1') -or $C.model_process_budget -ne $Budget -or $C.profile_budget -ne $Budget) {throw 'Closed Engineering delivery conflict'}
function Hash([string]$P) {
    $S=[IO.File]::OpenRead($P);$H=[Security.Cryptography.SHA256]::Create()
    try {return ([BitConverter]::ToString($H.ComputeHash($S))).Replace('-','').ToLowerInvariant()}
    finally {$S.Dispose();$H.Dispose()}
}
function Safe([string]$Root,[string]$Relative) {
    $Base=[IO.Path]::GetFullPath($Root).TrimEnd('\')+'\'
    $P=[IO.Path]::GetFullPath((Join-Path $Base $Relative))
    if ([IO.Path]::IsPathRooted($Relative) -or !$P.StartsWith($Base,[StringComparison]::OrdinalIgnoreCase)) {throw 'Path escape'}
    $Check=$P
    while ($Check.Length -ge $Base.TrimEnd('\').Length) {
        if ((Test-Path -LiteralPath $Check) -and ((Get-Item -LiteralPath $Check -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Reparse path'}
        $Check=[IO.Path]::GetDirectoryName($Check)
    }
    return $P
}
function Manifest([string]$Root) {
    $Seen=@{};$Rows=@(Import-Csv -LiteralPath (Join-Path $Root 'artifact_sha256.csv'))
    if (!$Rows.Count) {throw 'Empty artifact manifest'}
    foreach ($R in $Rows) {
        $P=Safe $Root $R.path
        if ($Seen.ContainsKey($P) -or !(Test-Path -LiteralPath $P -PathType Leaf)) {throw 'Duplicate/missing artifact'}
        $Seen[$P]=$true
        if ((Get-Item -LiteralPath $P).Length -ne [long]$R.bytes -or (Hash $P) -ne $R.sha256) {throw ('Artifact conflict: '+$R.path)}
    }
    $Count=@(Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object {$_.FullName -ne (Join-Path $Root 'artifact_sha256.csv')}).Count
    if ($Count -ne $Rows.Count) {throw 'Unlisted artifacts'}
}
Manifest $PSScriptRoot
if ($Remaining) {
    $C | Add-Member -NotePropertyName c0_reference -NotePropertyValue (Safe $PSScriptRoot $C.c0_reference_filename)
}
$Code=$C.code_root;$Target=$C.commit;$Python=Join-Path $Code '.venv\Scripts\python.exe'
$Static=Join-Path $C.server_root ('logs\completion_path_'+$Target.Substring(0,12)+'_static')
$Kind=if ($CollectReviewedEngineering) {'engineering'} else {'static'}
$Out=if ($CollectReviewedEngineering) {Join-Path $C.server_root ('evidence\engineering\'+$C.batch_id)} else {$Static}
$Zip=Join-Path $C.server_root ('transfer\completion_path_'+$Target.Substring(0,12)+'_'+$Kind+'.zip')
if ((Test-Path -LiteralPath $Out) -or (Test-Path -LiteralPath $Zip)) {throw 'No overwrite/resume/retry'}
New-Item -ItemType Directory -Path $Out | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $Out 'executed.ps1')
Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $Out 'delivery.json')
Start-Transcript -LiteralPath (Join-Path $Out 'transcript.txt') | Out-Null
$Status='BLOCKED';$Failure=$null
function Run([string]$Exe,[string[]]$Argv,[string]$Name) {
    Write-Host ('[stage] '+$Name+' START')
    $Saved=$ErrorActionPreference
    try {
        $ErrorActionPreference='Continue';$global:LASTEXITCODE=$null
        & $Exe @Argv 2>&1 | Tee-Object -FilePath (Join-Path $Out ($Name+'.log')) | ForEach-Object {Write-Host $_}
        $Exit=$LASTEXITCODE
    } finally {$ErrorActionPreference=$Saved}
    [ordered]@{executable=$Exe;argv=$Argv;exit_code=$Exit} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out ($Name+'.exit.json')) -Encoding utf8
    if ($null -eq $Exit -or $Exit -ne 0) {throw ($Name+' failed; STOP; no retry; exit='+$Exit)}
    Write-Host ('[stage] '+$Name+' COMPLETE')
}
function Tree([string]$Want) {
    $Head=& git -C $Code rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $Head -ne $Want) {throw 'HEAD conflict'}
    $Dirty=@(& git -C $Code status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $Dirty.Count) {throw 'Dirty checkout'}
}
function Sources {
    $Rows=@()
    foreach ($F in $C.source_representations.PSObject.Properties) {
        $P=Safe $Code $F.Name
        if (!(Test-Path -LiteralPath $P -PathType Leaf)) {throw ('Missing source: '+$F.Name)}
        $Hash=Hash $P;$Bytes=(Get-Item -LiteralPath $P).Length
        $Match=@($F.Value | Where-Object {$_.sha256 -eq $Hash -and $_.bytes -eq $Bytes})
        $Rows+=[ordered]@{path=$F.Name;actual_sha256=$Hash;actual_bytes=$Bytes;expected=$F.Value;matched=$Match.Count -gt 0}
        $Rows | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out 'source_bytes.json') -Encoding utf8
        if (!$Match.Count) {throw ('Source byte conflict: '+$F.Name)}
    }
}
try {
    Set-Location -LiteralPath $Code
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID';$env:CUDA_VISIBLE_DEVICES='-1';$env:PYTHONDONTWRITEBYTECODE='1'
    $env:HF_HUB_OFFLINE='1';$env:TRANSFORMERS_OFFLINE='1'
    if (!$CollectReviewedEngineering) {
        Tree $C.prerequisite
        $Bundle=Safe $PSScriptRoot $C.bundle
        if ((Get-Item -LiteralPath $Bundle).Length -ne $C.bundle_bytes -or (Hash $Bundle) -ne $C.bundle_sha256) {throw 'Bundle conflict'}
        Run 'git' @('bundle','verify',$Bundle) '01_bundle'
        Run 'git' @('fetch',$Bundle,($C.bundle_ref+':refs/remotes/completion-path-delivery/execution')) '02_fetch'
        Run 'git' @('-c','core.autocrlf=false','checkout','--detach',$Target) '03_checkout'
        Tree $Target;Sources
        # Keep synthetic process/UNKNOWN negative fixtures outside the real receipt tree.
        $CpuTemp=Join-Path $C.server_root ('diagnostics\completion_path_'+$Target.Substring(0,12)+'_cpu_tmp')
        if (Test-Path -LiteralPath $CpuTemp) {throw 'CPU fixture directory exists; no overwrite'}
        $Tests=if ($Remaining) {@('tests/test_completion_path_report.py','tests/test_completion_path_reference.py','tests/test_completion_path_driver.py')} else {@('tests/test_completion_path.py','tests/test_completion_path_driver.py','tests/test_batch_load_diagnostic.py')}
        $CpuArgs=@('-X','utf8','-m','pytest','-q','-p','no:cacheprovider','--basetemp',$CpuTemp,
            '--junitxml',(Join-Path $Out 'cpu_results.xml'))+$Tests
        Run $Python $CpuArgs '04_cpu'
        Run $Python @('-X','utf8','-m','compileall','-q','exposedpath','exposedpath_v141','scripts/completion_path_diagnostic.py') '05_compile'
        if ($Remaining) {
            $ReferenceConfig=Join-Path $Out 'reference_config.json';$C | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $ReferenceConfig -Encoding utf8
            Run $Python @('-X','utf8','-u','scripts/completion_path_diagnostic.py','--config',$ReferenceConfig,
                '--output',(Join-Path $Out 'c0_reference'),'--review-c0-reference') '06_reference_cpu'
        }
        Tree $Target;$Status='STATIC_READY_FOR_COORDINATOR_REVIEW'
    } else {
        Tree $Target;Manifest $Static
        $R=Get-Content -LiteralPath (Join-Path $Static 'receipt.json') -Raw | ConvertFrom-Json
        if ($R.status -ne 'STATIC_READY_FOR_COORDINATOR_REVIEW' -or $R.execution_commit -ne $Target -or $R.delivery_sha256 -ne (Hash $ConfigPath)) {throw 'Static receipt conflict'}
        Copy-Item -LiteralPath $Static -Destination (Join-Path $Out 'static') -Recurse
        Sources
        if ([IO.DriveInfo]::new([IO.Path]::GetPathRoot($Out)).AvailableFreeSpace -lt 12GB) {throw '12GiB temporary free required; do not clear old evidence'}
        $env:CUDA_VISIBLE_DEVICES='3'
        if ((Hash $C.nsys) -ne $C.nsys_sha256) {throw 'Collector conflict'}
        Run $C.nsys @('--version') '06_nsys'
        $Identity=@'
import sys,json,torch,transformers
assert sys.version_info[:3]==(3,11,16)
assert torch.__version__=='2.6.0+cu124' and torch.version.cuda=='12.4'
assert transformers.__version__=='5.17.0'
print(json.dumps(dict(python=sys.version,executable=sys.executable,torch=torch.__version__,cuda=torch.version.cuda,transformers=transformers.__version__)))
'@
        Run $Python @('-X','utf8','-c',$Identity) '07_runtime'
        $Gpu=@(& nvidia-smi '--id=3' '--query-gpu=index,uuid,pci.bus_id,name,driver_version' '--format=csv,noheader,nounits')
        if ($LASTEXITCODE -ne 0 -or $Gpu.Count -ne 1) {throw 'GPU query failed'}
        $Gpu | Out-File -LiteralPath (Join-Path $Out 'gpu_identity.txt') -Encoding utf8
        $G=@($Gpu[0].Split(',') | ForEach-Object {$_.Trim()})
        if ($G[0] -ne '3' -or $G[1] -ne $C.gpu_uuid -or $G[2] -ine $C.gpu_pci_bus_id -or $G[4] -ne '555.99') {throw 'GPU/driver conflict'}
        foreach ($Name in @('prompt_512.json','model_sha256.csv')) {Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination (Join-Path $Out $Name)}
        $C | Add-Member -NotePropertyName seed_input -NotePropertyValue (Join-Path $Out 'prompt_512.json')
        $C | Add-Member -NotePropertyName inventory -NotePropertyValue (Join-Path $Out 'model_sha256.csv')
        $RunConfig=Join-Path $Out 'run_config.json';$C | ConvertTo-Json -Depth 16 | Set-Content -LiteralPath $RunConfig -Encoding utf8
        $Lock=Join-Path $Out '.active';Set-Content -LiteralPath $Lock -Value $PID
        try {Run $Python @('-X','utf8','-u','scripts/completion_path_diagnostic.py','--config',$RunConfig,
            '--output',(Join-Path $Out 'experiment'),'--execute-reviewed-completion-path') '08_batch'}
        finally {Remove-Item -LiteralPath $Lock}
        $BR=Get-Content -LiteralPath (Join-Path $Out 'experiment\batch\batch_report.json') -Raw | ConvertFrom-Json
        if ($Remaining) {
            if ($BR.status -ne 'BATCH_COMPLETE_STOP_FOR_REVIEW' -or $BR.runs.Count -ne 1 -or $BR.runs[0].binding.variant -ne 'Cpre') {throw 'Cpre-only machine report incomplete'}
        } else {
            if ($BR.status -ne 'BATCH_COMPLETE_STOP_FOR_REVIEW' -or $BR.runs.Count -ne 2) {throw 'Machine report incomplete'}
        }
        Tree $Target;$Status='BATCH_COMPLETE_STOP_FOR_REVIEW'
    }
} catch {$Failure=$_.ToString();Write-Host ('STOP: '+$Failure)}
finally {
    [ordered]@{status=$Status;error=$Failure;execution_commit=$Target;analysis_commit=$Target;delivery_sha256=(Hash $ConfigPath);
        role='Engineering';automatic_retry=$false;model_process_budget=$Budget;profile_budget=$Budget;measurement_validity='NOT_ASSESSED';dropped_records_status='UNKNOWN'} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Out 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
}
# Reuse existing archive-first guard; UNKNOWN descendants refuse packing. No cleanup here.
& $Python '-X' 'utf8' 'scripts/gate13_retention.py' 'pack' '--root' $Out '--archive' $Zip
if ($LASTEXITCODE -ne 0) {throw 'Packaging refused; preserve scene, no retry/cleanup'}
Write-Host ('ZIP='+$Zip)
if ($Status -eq 'BLOCKED') {throw 'Return failure ZIP; no retry/replacement'}
