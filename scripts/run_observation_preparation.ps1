param([switch]$CollectReviewedEngineering,[switch]$CollectReviewedInputPilot,[string]$ReviewedStaticReceiptSHA256='')
# A is the default. B is never invoked by deployment, packing or failure recovery.
$ErrorActionPreference='Stop'
$C=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw | ConvertFrom-Json
$Midpoint=$C.schema_version -eq 'coe-input-pilot-delivery/0.2'
$Sensitivity=$C.schema_version -eq 'observation-preparation-delivery/0.2'
$InputPilot=$C.schema_version -in @('coe-input-pilot-delivery/0.1','coe-input-pilot-delivery/0.2')
$Budget=if ($Midpoint) {9} else {8}
$Collect=$CollectReviewedEngineering -or $CollectReviewedInputPilot
if (($InputPilot -and $CollectReviewedEngineering) -or (!$InputPilot -and $CollectReviewedInputPilot)) {throw 'Explicit role opt-in conflict'}
if ($C.schema_version -notin @('observation-preparation-delivery/0.1','observation-preparation-delivery/0.2','coe-input-pilot-delivery/0.1','coe-input-pilot-delivery/0.2') -or $C.commit -ne $C.analysis_commit -or
    $C.model_process_budget -ne $Budget -or $C.profile_budget -ne $Budget -or
    ($Midpoint -and $C.input_contract_version -ne 'COE-INPUT-P-PILOT/0.2') -or
    ($Sensitivity -and $C.observation_contract_version -ne 'OBSERVATION-PREPARATION-ENGINEERING/0.2')) {throw 'Delivery conflict'}
function Hash([string]$P) {return (Get-FileHash -LiteralPath $P -Algorithm SHA256).Hash.ToLowerInvariant()}
function Safe([string]$Root,[string]$Relative) {
    $Base=[IO.Path]::GetFullPath($Root).TrimEnd('\')+'\'
    $P=[IO.Path]::GetFullPath((Join-Path $Base $Relative))
    if ([IO.Path]::IsPathRooted($Relative) -or !$P.StartsWith($Base,[StringComparison]::OrdinalIgnoreCase)) {throw 'Path escape'}
    $Q=$P
    while ($Q -and $Q.Length -ge $Base.TrimEnd('\').Length) {
        if ((Test-Path -LiteralPath $Q) -and ((Get-Item -LiteralPath $Q -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) {throw 'Reparse path'}
        $Q=[IO.Path]::GetDirectoryName($Q)
    }
    return $P
}
function VerifyManifest([string]$Root) {
    $Seen=@{};$Rows=@(Import-Csv -LiteralPath (Join-Path $Root 'artifact_sha256.csv'))
    if (!$Rows.Count) {throw 'Empty manifest'}
    foreach ($R in $Rows) {
        $P=Safe $Root $R.path
        if ($Seen.ContainsKey($P) -or !(Test-Path -LiteralPath $P -PathType Leaf)) {throw 'Duplicate/missing artifact'}
        $Seen[$P]=$true
        if ((Get-Item -LiteralPath $P).Length -ne [long]$R.bytes -or (Hash $P) -ne $R.sha256) {throw ('Artifact conflict: '+$R.path)}
    }
    $Files=@(Get-ChildItem -LiteralPath $Root -Recurse -File | Where-Object {$_.FullName -ne (Join-Path $Root 'artifact_sha256.csv')})
    if ($Files.Count -ne $Rows.Count) {throw 'Unlisted artifact'}
}
VerifyManifest $PSScriptRoot
if ((Hash $PSCommandPath) -ne $C.launcher_sha256) {throw 'Launcher identity conflict'}
if (($InputPilot -or $Sensitivity) -and ((Hash (Join-Path $PSScriptRoot 'plan.json')) -ne $C.plan_sha256)) {throw 'Plan identity conflict'}
$Code=$C.code_root;$Target=$C.commit;$Python=Join-Path $Code '.venv\Scripts\python.exe'
$Prefix=if ($InputPilot) {'coe_input_'} else {'observation_'}
$Static=Safe $C.server_root ('logs\'+$Prefix+$Target.Substring(0,12)+'_static')
$Kind=if ($Collect) {if ($InputPilot) {'pilot'} else {'engineering'}} else {'static'}
$Evidence=if ($InputPilot) {'evidence\coe_input_pilot\'} else {'evidence\observation_preparation\'}
$Out=if ($Collect) {Safe $C.server_root ($Evidence+$C.batch_id)} else {$Static}
$Zip=Safe $C.server_root ('transfer\'+$Prefix+$Target.Substring(0,12)+'_'+$Kind+'.zip')
if ((Test-Path -LiteralPath $Out) -or (Test-Path -LiteralPath $Zip)) {throw 'No overwrite/resume/retry'}
if ($Collect) {
    if ($ReviewedStaticReceiptSHA256 -notmatch '^[0-9a-fA-F]{64}$' -or
        (Hash (Join-Path $Static 'receipt.json')) -ine $ReviewedStaticReceiptSHA256) {throw 'Reviewed Stage A receipt hash required'}
    VerifyManifest $Static
    $R=Get-Content -LiteralPath (Join-Path $Static 'receipt.json') -Raw | ConvertFrom-Json
    if ($R.status -ne 'STATIC_READY_FOR_REVIEW' -or $R.execution_commit -ne $Target -or $R.analysis_commit -ne $Target -or
        $R.delivery_sha256 -ne (Hash (Join-Path $PSScriptRoot 'delivery.json')) -or
        $R.storage_sha256 -ne (Hash (Join-Path $Static 'storage.json')) -or
        $R.source_bytes_sha256 -ne (Hash (Join-Path $Static 'source_bytes.json'))) {throw 'Static receipt conflict'}
    $S=Get-Content -LiteralPath (Join-Path $Static 'storage.json') -Raw | ConvertFrom-Json
    if ($S.status -ne 'STARTUP_RESOURCES_READY') {throw 'Static resource receipt conflict'}
}
New-Item -ItemType Directory -Path $Out | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $Out 'executed.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Destination (Join-Path $Out 'delivery.json')
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
    if ($null -eq $Exit -or $Exit -ne 0) {throw ($Name+' failed; no retry; exit='+$Exit)}
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
        $H=Hash $P;$N=(Get-Item -LiteralPath $P).Length
        $Match=@($F.Value | Where-Object {$_.sha256 -eq $H -and $_.bytes -eq $N})
        $Rows+=[ordered]@{path=$F.Name;actual_sha256=$H;actual_bytes=$N;expected=$F.Value;matched=$Match.Count -gt 0}
        $Rows | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $Out 'source_bytes.json') -Encoding utf8
        if (!$Match.Count) {throw ('Source conflict: '+$F.Name)}
    }
}
function Storage {
    if (!$env:TEMP -or !$env:TMP) {throw 'Inherited TEMP and TMP required'}
    $Argv=@('-X','utf8','scripts/coe_startup_storage.py','--output-directory',$Out,
        '--temporary-directory',$env:TEMP,'--temporary-directory',$env:TMP,
        '--archive',$Zip,'--receipt',(Join-Path $Out 'storage.json'))
    if ($env:TMPDIR) {$Argv+=@('--temporary-directory',$env:TMPDIR)}
    Run $Python $Argv 'storage'
}
try {
    Set-Location -LiteralPath $Code
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID';$env:CUDA_VISIBLE_DEVICES='-1';$env:PYTHONDONTWRITEBYTECODE='1'
    $env:HF_HUB_OFFLINE='1';$env:TRANSFORMERS_OFFLINE='1'
    if (!$Collect) {
        Tree $C.prerequisite
        $Bundle=Safe $PSScriptRoot $C.bundle
        if ((Hash $Bundle) -ne $C.bundle_sha256 -or (Get-Item -LiteralPath $Bundle).Length -ne $C.bundle_bytes) {throw 'Bundle conflict'}
        Run 'git' @('bundle','verify',$Bundle) '01_bundle'
        Run 'git' @('fetch',$Bundle,($C.bundle_ref+':refs/remotes/observation-preparation/execution')) '02_fetch'
        $Fetched=& git -C $Code rev-parse refs/remotes/observation-preparation/execution
        if ($LASTEXITCODE -ne 0 -or $Fetched -ne $Target) {throw 'Bundle target conflict'}
        Run 'git' @('-c','core.autocrlf=false','checkout','--detach',$Target) '03_checkout'
        Tree $Target;Sources;Storage
        $CpuTemp=Join-Path $C.server_root ('diagnostics\'+$Prefix+$Target.Substring(0,12)+'_cpu')
        if (Test-Path -LiteralPath $CpuTemp) {throw 'CPU output exists'}
        $Tests=if ($InputPilot) {@('tests/test_coe_input_pilot.py','tests/test_coe_input_delivery.py')} else {@('tests/test_observation_preparation.py','tests/test_observation_delivery.py')}
        if ($Midpoint) {$Tests+=@('tests/test_coe_input_midpoint.py','tests/test_coe_midpoint_delivery.py')}
        if ($Sensitivity) {$Tests=@('tests/test_observation_input_sensitivity.py','tests/test_observation_input_delivery.py')}
        Run $Python (@('-X','utf8','-m','pytest','-q','-ra','-p','no:cacheprovider','--basetemp',$CpuTemp,
            '--junitxml',(Join-Path $Out 'cpu_results.xml'))+$Tests) '04_cpu'
        $Compile=@('-X','utf8','-m','py_compile','exposedpath/observation_preparation.py',
            'analysis/observation_preparation.py','scripts/observation_preparation_batch.py')
        if ($InputPilot) {$Compile+=@('exposedpath/coe_input_pilot.py','analysis/coe_budget_preview.py')}
        Run $Python $Compile '05_compile'
        Tree $Target;$Status='STATIC_READY_FOR_REVIEW'
    } else {
        Tree $Target;Sources;Storage
        Copy-Item -LiteralPath $Static -Destination (Join-Path $Out 'static') -Recurse
        if ((Hash $C.nsys) -ne $C.nsys_sha256) {throw 'Collector conflict'}
        $env:CUDA_VISIBLE_DEVICES='3'
        Run $C.nsys @('--version') '06_nsys_version'
        foreach ($Name in @('prompt_512.json','model_sha256.csv')) {Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination (Join-Path $Out $Name)}
        $C | Add-Member -NotePropertyName seed_input -NotePropertyValue (Join-Path $Out 'prompt_512.json')
        $C | Add-Member -NotePropertyName inventory -NotePropertyValue (Join-Path $Out 'model_sha256.csv')
        $RunConfig=Join-Path $Out 'run_config.json';$C | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $RunConfig -Encoding utf8
        $Switch=if ($InputPilot) {'--collect-reviewed-input-pilot'} else {'--collect-reviewed-preparation'}
        $BatchStage=if ($Midpoint) {'07_nine_p1'} else {'07_eight_p1'}
        Run $Python @('-X','utf8','-u','scripts/observation_preparation_batch.py','--config',$RunConfig,
            '--output',(Join-Path $Out 'experiment'),$Switch) $BatchStage
        $BR=Get-Content -LiteralPath (Join-Path $Out 'experiment\batch\batch_report.json') -Raw | ConvertFrom-Json
        $ExpectedStatus=if ($InputPilot) {'FIXED_EIGHT_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW'} else {'FIXED_EIGHT_COMPLETE_STOP_FOR_REVIEW'}
        $ExpectedBlocks=if ($InputPilot) {4} else {2}
        if ($Midpoint) {$ExpectedStatus='FIXED_NINE_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW';$ExpectedBlocks=3}
        if ($BR.status -ne $ExpectedStatus -or $BR.runs.Count -ne $Budget -or $BR.blocks.Count -ne $ExpectedBlocks) {throw 'Incomplete batch'}
        Tree $Target;$Status=$ExpectedStatus
    }
} catch {$Failure=$_.ToString();Write-Host ('STOP: '+$Failure)}
finally {
    $StorageHash=if (Test-Path -LiteralPath (Join-Path $Out 'storage.json')) {Hash (Join-Path $Out 'storage.json')} else {$null}
    $SourceHash=if (Test-Path -LiteralPath (Join-Path $Out 'source_bytes.json')) {Hash (Join-Path $Out 'source_bytes.json')} else {$null}
    [ordered]@{status=$Status;error=$Failure;execution_commit=$Target;analysis_commit=$Target;
        delivery_sha256=(Hash (Join-Path $PSScriptRoot 'delivery.json'));role=$(if ($InputPilot) {'Pilot'} else {'Engineering'});automatic_retry=$false;
        storage_sha256=$StorageHash;source_bytes_sha256=$SourceHash;actual_phase=$Kind;
        historical_ylq_total_bytes=$null;long_term_status='UNKNOWN_NOT_PROVEN';long_term_target_exclusive_bytes=50000000000;
        stage_a_model_processes=0;stage_a_profiles=0;stage_a_cuda_initializations=0;
        model_process_budget=$Budget;profile_budget=$Budget;measurement_validity='NOT_ASSESSED';dropped_records_status='UNKNOWN'} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Out 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
}
# The existing guard rejects unknown/live descendants. Never force pack/cleanup.
& $Python '-X' 'utf8' 'scripts/gate13_retention.py' 'pack' '--root' $Out '--archive' $Zip
if ($LASTEXITCODE -ne 0) {throw 'Packaging refused; preserve scene; no cleanup/retry'}
Write-Host ('ZIP='+$Zip)
if ($Status -eq 'BLOCKED') {throw 'Return failure ZIP; STOP; no retry/replacement'}
