param([switch]$CollectReviewedPilot,[string]$ReviewedStaticReceiptSHA256='')
# Default A: deployment + CPU only. B requires a separately reviewed receipt hash.
$ErrorActionPreference='Stop'
$C=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw | ConvertFrom-Json
if ($C.schema_version -ne 'coe-pilot-delivery/0.1' -or $C.model_process_budget -ne 9 -or $C.profile_budget -ne 9 -or $C.commit -ne $C.analysis_commit) {throw 'Delivery conflict'}
if ($C.PSObject.Properties.Name -contains 'stage_a_only') {
    if ($C.stage_a_only -isnot [bool]) {throw 'STATIC_REPAIR_FLAG_TYPE'}
    if ($C.stage_a_only -and $CollectReviewedPilot) {throw 'STATIC_REPAIR_ONLY_NO_COLLECTION'}
}
if ($C.operational_revision -ne 'coe-startup-resources/0.1.0') {throw 'Operational revision conflict'}
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
$Code=$C.code_root;$Target=$C.commit;$Python=Join-Path $Code '.venv\Scripts\python.exe'
$Static=Safe $C.server_root ('logs\coe_'+$Target.Substring(0,12)+'_static')
$Kind=if ($CollectReviewedPilot) {'pilot'} else {'static'}
$Out=if ($CollectReviewedPilot) {Safe $C.server_root ('evidence\coe_pilot\'+$C.batch_id)} else {$Static}
$Zip=Safe $C.server_root ('transfer\coe_'+$Target.Substring(0,12)+'_'+$Kind+'.zip')
if ((Test-Path -LiteralPath $Out) -or (Test-Path -LiteralPath $Zip)) {throw 'No overwrite/resume/retry'}
if ($CollectReviewedPilot) {
    if ($ReviewedStaticReceiptSHA256 -notmatch '^[0-9a-fA-F]{64}$' -or
        (Hash (Join-Path $Static 'receipt.json')) -ine $ReviewedStaticReceiptSHA256) {throw 'Explicit reviewed Stage A receipt hash required'}
    VerifyManifest $Static
    $R=Get-Content -LiteralPath (Join-Path $Static 'receipt.json') -Raw | ConvertFrom-Json
    if ($R.status -ne 'STATIC_READY_FOR_REVIEW' -or $R.execution_commit -ne $Target -or $R.analysis_commit -ne $Target -or
        $R.operational_revision -ne $C.operational_revision -or $R.delivery_sha256 -ne (Hash (Join-Path $PSScriptRoot 'delivery.json')) -or
        $R.storage_sha256 -ne (Hash (Join-Path $Static 'storage.json')) -or
        $R.component_reuse_sha256 -ne (Hash (Join-Path $Static 'component_reuse.json'))) {throw 'Static receipt conflict'}
    $StorageReceipt=Get-Content -LiteralPath (Join-Path $Static 'storage.json') -Raw | ConvertFrom-Json
    $ReuseReceipt=Get-Content -LiteralPath (Join-Path $Static 'component_reuse.json') -Raw | ConvertFrom-Json
    if ($StorageReceipt.status -ne 'STARTUP_RESOURCES_READY' -or $ReuseReceipt.status -ne 'COMPONENT_REUSE_VERIFIED' -or
        $ReuseReceipt.execution_commit -ne $Target) {throw 'Static subreceipt conflict'}
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
    # Long-term target 50000000000 bytes stays UNKNOWN; not a startup census.
    if (!$env:TEMP -or !$env:TMP) {throw 'Explicit inherited TEMP and TMP required'}
    $Args=@('-X','utf8','scripts/coe_startup_storage.py','--output-directory',$Out,
        '--temporary-directory',$env:TEMP,'--temporary-directory',$env:TMP,
        '--archive',$Zip,'--receipt',(Join-Path $Out 'storage.json'))
    if ($env:TMPDIR) {$Args+=@('--temporary-directory',$env:TMPDIR)}
    Run $Python $Args 'storage'
}
function Reuse {
    Run $Python @('-X','utf8','scripts/coe_delivery_reuse.py','--delivery',(Join-Path $PSScriptRoot 'delivery.json'),
        '--sources',(Join-Path $Out 'source_bytes.json'),'--receipt',(Join-Path $Out 'component_reuse.json')) 'component_reuse'
    if ((Hash $PSCommandPath) -ne $C.launcher_sha256 -or
        (Hash (Join-Path $Code 'scripts\run_coe_candidate_pilot.ps1')) -ne $C.launcher_sha256) {throw 'New launcher identity conflict'}
}
try {
    Set-Location -LiteralPath $Code
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID';$env:CUDA_VISIBLE_DEVICES='-1';$env:PYTHONDONTWRITEBYTECODE='1'
    $env:HF_HUB_OFFLINE='1';$env:TRANSFORMERS_OFFLINE='1'
    if (!$CollectReviewedPilot) {
        Tree $C.prerequisite
        $Bundle=Safe $PSScriptRoot $C.bundle
        if ((Hash $Bundle) -ne $C.bundle_sha256 -or (Get-Item -LiteralPath $Bundle).Length -ne $C.bundle_bytes) {throw 'Bundle conflict'}
        Run 'git' @('bundle','verify',$Bundle) '01_bundle'
        Run 'git' @('fetch',$Bundle,($C.bundle_ref+':refs/remotes/coe-pilot/execution')) '02_fetch'
        $Fetched=& git -C $Code rev-parse refs/remotes/coe-pilot/execution
        if ($LASTEXITCODE -ne 0 -or $Fetched -ne $Target) {throw 'Bundle target conflict'}
        Run 'git' @('-c','core.autocrlf=false','checkout','--detach',$Target) '03_checkout'
        Tree $Target;Sources;Reuse;Storage
        $CpuTemp=Join-Path $C.server_root ('diagnostics\coe_'+$Target.Substring(0,12)+'_cpu')
        if (Test-Path -LiteralPath $CpuTemp) {throw 'CPU output exists'}
        $env:COE_REUSE_STATIC_ARCHIVE=Safe $PSScriptRoot $C.reuse_static_archive
        Run $Python @('-X','utf8','-m','pytest','-q','-ra','-p','no:cacheprovider','--basetemp',$CpuTemp,
            '--junitxml',(Join-Path $Out 'cpu_results.xml'),'tests/test_coe_startup_storage.py','tests/test_coe_delivery_resources.py') '04_cpu_changed_wiring'
        Run $Python @('-X','utf8','-m','py_compile','scripts/coe_startup_storage.py','scripts/coe_delivery_reuse.py') '05_compile_changed_wiring'
        Tree $Target
        $Status='STATIC_READY_FOR_REVIEW'
    } else {
        Tree $Target;Sources;Reuse;Storage
        Copy-Item -LiteralPath $Static -Destination (Join-Path $Out 'static') -Recurse
        if ((Hash $C.nsys) -ne $C.nsys_sha256) {throw 'Collector conflict'}
        $env:CUDA_VISIBLE_DEVICES='3'
        Run $C.nsys @('--version') '07_nsys_version'
        foreach ($Name in @('prompt_512.json','model_sha256.csv')) {Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination (Join-Path $Out $Name)}
        $C | Add-Member -NotePropertyName seed_input -NotePropertyValue (Join-Path $Out 'prompt_512.json')
        $C | Add-Member -NotePropertyName inventory -NotePropertyValue (Join-Path $Out 'model_sha256.csv')
        $RunConfig=Join-Path $Out 'run_config.json';$C | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $RunConfig -Encoding utf8
        Run $Python @('-X','utf8','-u','scripts/coe_pilot_batch.py','--config',$RunConfig,
            '--output',(Join-Path $Out 'experiment'),'--collect-reviewed-coe-pilot') '08_nine_p1'
        $BR=Get-Content -LiteralPath (Join-Path $Out 'experiment\batch\batch_report.json') -Raw | ConvertFrom-Json
        if ($BR.status -ne 'FIXED_NINE_COMPLETE_STOP_FOR_REVIEW' -or $BR.runs.Count -ne 9 -or $BR.blocks.Count -ne 3) {throw 'Incomplete batch'}
        Tree $Target;$Status='FIXED_NINE_COMPLETE_STOP_FOR_REVIEW'
    }
} catch {$Failure=$_.ToString();Write-Host ('STOP: '+$Failure)}
finally {
    $StorageHash=if (Test-Path -LiteralPath (Join-Path $Out 'storage.json')) {Hash (Join-Path $Out 'storage.json')} else {$null}
    $ReuseHash=if (Test-Path -LiteralPath (Join-Path $Out 'component_reuse.json')) {Hash (Join-Path $Out 'component_reuse.json')} else {$null}
    $ReusedCpu=if ($ReuseHash) {110} else {$null}
    [ordered]@{status=$Status;error=$Failure;execution_commit=$Target;analysis_commit=$Target;
        delivery_sha256=(Hash (Join-Path $PSScriptRoot 'delivery.json'));role='Pilot';automatic_retry=$false;
        operational_revision=$C.operational_revision;storage_sha256=$StorageHash;component_reuse_sha256=$ReuseHash;
        historical_ylq_total_bytes=$null;long_term_status='UNKNOWN_NOT_PROVEN';long_term_target_exclusive_bytes=50000000000;
        reused_cpu_count=$ReusedCpu;new_wiring_checks_only=$true;
        actual_phase=$Kind;stage_a_model_processes=0;stage_a_profiles=0;stage_a_cuda_initializations=0;
        model_process_budget=9;profile_budget=9;measurement_validity='NOT_ASSESSED';dropped_records_status='UNKNOWN'} |
        ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Out 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
}
# Guard refuses UNKNOWN descendants and live recorded writers; never force pack.
& $Python '-X' 'utf8' 'scripts/gate13_retention.py' 'pack' '--root' $Out '--archive' $Zip
if ($LASTEXITCODE -ne 0) {throw 'Packaging refused; preserve scene, no cleanup/retry'}
Write-Host ('ZIP='+$Zip)
if ($Status -eq 'BLOCKED') {throw 'Return failure ZIP; STOP; no retry/replacement'}
