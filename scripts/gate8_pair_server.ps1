param(
    [ValidateSet('Static','Pair')][string]$Stage='Static',
    [switch]$DeployCpuAuthorized,
    [switch]$PairAuthorizedAfterCpuReview,
    [string]$ServerRoot, [string]$CodeRoot, [string]$Target,
    [string]$Bundle, [long]$BundleBytes, [string]$BundleSha256,
    [string]$TargetPython, [string]$SiteRoot, [string]$Model,
    [string]$Inputs, [string]$Nsys, [string]$ExpectedGpuUuid, [string]$ExpectedPci,
    [string]$DeliveryWrapper
)
# Parameters are pinned by a separately hashed, machine-local delivery wrapper.
if (($Stage -eq 'Static' -and !$DeployCpuAuthorized) -or
    ($Stage -eq 'Pair' -and !$PairAuthorizedAfterCpuReview)) { throw 'STAGE_AUTHORIZATION_REQUIRED' }
$ErrorActionPreference='Stop'
if ($Target -notmatch '^[0-9a-f]{40}$' -or !$CodeRoot -or !$ServerRoot) { throw 'Fixed delivery identity required' }
$Parent='db9f028b1a7ceac40b9a110bfaacf6d613319638'
$PythonExe=Join-Path $CodeRoot '.venv\Scripts\python.exe'
$Batch=Join-Path $ServerRoot ('evidence\gate8\pair_'+$Target.Substring(0,12)+'_delivery1')
$Part=Join-Path $Batch $Stage.ToLowerInvariant()
if (Test-Path -LiteralPath $Part) { throw 'Existing stage forbidden; no resume or retry' }
if ($Stage -eq 'Pair') {
    $Cpu=Join-Path $Batch 'static\receipt.json'
    $Prior=Get-Content -LiteralPath $Cpu -Raw | ConvertFrom-Json
    if ($Prior.status -ne 'STATIC_PASS' -or $Prior.commit -ne $Target) { throw 'CPU receipt not accepted' }
    $CpuRows=Import-Csv -LiteralPath (Join-Path $Batch 'static\artifact_sha256.csv')
    foreach ($R in $CpuRows) {
        $P=Join-Path (Join-Path $Batch 'static') $R.path
        if ((Get-Item -LiteralPath $P).Length -ne [long]$R.bytes -or (Get-FileHash -LiteralPath $P).Hash -ne $R.sha256) { throw 'CPU evidence changed' }
    }
}
New-Item -ItemType Directory -Path $Part | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $Part 'executed_driver.ps1')
if ($DeliveryWrapper) { Copy-Item -LiteralPath $DeliveryWrapper -Destination (Join-Path $Part 'executed_wrapper.ps1') }
Start-Transcript -LiteralPath (Join-Path $Part 'transcript.txt') | Out-Null
$Status='BLOCKED'; $Failure=$null
function Checked([string]$Exe,[string[]]$Argv,[string]$Label) {
    $Saved=$ErrorActionPreference
    try { $ErrorActionPreference='Continue'; $global:LASTEXITCODE=$null; $Lines=& $Exe @Argv 2>&1; $Exit=$LASTEXITCODE }
    finally { $ErrorActionPreference=$Saved }
    $Lines | Out-File -LiteralPath (Join-Path $Part ($Label+'.log')) -Encoding utf8
    $Lines | ForEach-Object { Write-Host $_ }
    [ordered]@{executable=$Exe;argv=$Argv;exit_code=$Exit} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Part ($Label+'.exit.json')) -Encoding utf8
    if ($Exit -ne 0) { throw ($Label+' exit='+$Exit) }
}
function CheckTree([string]$Expected) {
    $H=& git -C $CodeRoot rev-parse HEAD; $E=$LASTEXITCODE
    $S=@(& git -C $CodeRoot status --porcelain)
    if ($E -ne 0 -or $LASTEXITCODE -ne 0 -or $H -ne $Expected -or $S.Count -ne 0) { throw 'Code identity/clean conflict' }
}
try {
    Set-Location -LiteralPath $CodeRoot
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID'; $env:CUDA_VISIBLE_DEVICES='-1'
    $env:HF_HUB_OFFLINE='1'; $env:TRANSFORMERS_OFFLINE='1'
    if ($Stage -eq 'Static') {
        CheckTree $Parent
        if ((Get-Item -LiteralPath $Bundle).Length -ne $BundleBytes -or (Get-FileHash -LiteralPath $Bundle).Hash -ne $BundleSha256) { throw 'Bundle bytes/hash conflict' }
        Checked 'git' @('bundle','verify',$Bundle) '01_bundle'
        $Ref='refs/remotes/gate8-pair-'+$Target.Substring(0,12)+'/main'
        Checked 'git' @('fetch',$Bundle,('refs/heads/main:'+$Ref)) '02_fetch'
        $Fetched=& git rev-parse $Ref
        if ($LASTEXITCODE -ne 0 -or $Fetched -ne $Target) { throw 'Bundle ref conflict' }
        Checked 'git' @('checkout','--detach',$Target) '03_checkout'
        Checked $PythonExe @('-c','import sys; print(sys.executable,sys.version); assert sys.version_info[:3]==(3,11,16)') '04_python'
        Checked $PythonExe @('-m','pytest','-q','-p','no:cacheprovider','tests/test_gate8_git_path_lists.py','tests/test_gate8_isolated_preflight.py','tests/test_gate8_pair.py','tests/test_gate8_conditional_a.py','tests/test_gate8_diagnostic_collect.py') '05_targeted'
        Checked $PythonExe @('-m','compileall','-q','exposedpath/gate8_isolated_preflight.py','exposedpath/gate8_diagnostic.py','exposedpath_v141/gate8_engineering_scope.py','exposedpath_v141/gate8_warning_assumption.py','scripts/gate8_pair.py','scripts/gate8_diagnostic_collect.py') '06_compile'
        Checked 'git' @('diff','--check',$Parent,$Target) '07_diff'
        CheckTree $Target
        $Status='STATIC_PASS'
    } else {
        CheckTree $Target
        $VsRoot='C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools'
        Import-Module -Name (Join-Path $VsRoot 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll') -ErrorAction Stop
        Enter-VsDevShell -VsInstallPath $VsRoot -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.38'
        Set-Location -LiteralPath $CodeRoot
        $Cl=(Get-Command cl.exe -CommandType Application | Select-Object -First 1).Source
        if ($Cl -ine (Join-Path $VsRoot 'VC\Tools\MSVC\14.38.33130\bin\Hostx64\x64\cl.exe') -or
            (Get-Item -LiteralPath $Cl).VersionInfo.FileVersion -notlike '19.38.33135*' -or
            $env:VSCMD_ARG_HOST_ARCH -ne 'x64' -or $env:VSCMD_ARG_TGT_ARCH -ne 'x64') { throw 'Compiler conflict' }
        $env:CUDA_VISIBLE_DEVICES='3'
        if ((Get-FileHash -LiteralPath $Nsys).Hash -ne 'B26707E479540314EBE4931B687B149C6A2D8A86EB6075A0C98169BEFC6E7417') { throw 'Nsight changed' }
        Checked $Nsys @('--version') '10_nsys_version'
        $GpuLines=@(& nvidia-smi '--id=3' '--query-gpu=index,uuid,pci.bus_id,name,driver_version' '--format=csv,noheader,nounits')
        if ($LASTEXITCODE -ne 0 -or $GpuLines.Count -ne 1) { throw 'GPU query failed' }
        $Gpu=@($GpuLines[0].Split(',') | ForEach-Object {$_.Trim()})
        if (!$ExpectedGpuUuid -or !$ExpectedPci -or $Gpu[0] -ne '3' -or $Gpu[1] -ne $ExpectedGpuUuid -or $Gpu[2] -ine $ExpectedPci -or $Gpu[4] -ne '555.99') { throw 'GPU identity conflict' }
        Checked $TargetPython @('-I','-S','-c',"import sys;sys.path[:0]=sys.argv[1:3];import torch,transformers;print(sys.executable,sys.version,torch.__version__,torch.version.cuda,transformers.__version__);assert sys.version_info[:3]==(3,11,16) and torch.__version__=='2.6.0+cu124' and torch.version.cuda=='12.4' and transformers.__version__=='5.17.0'",$CodeRoot,$SiteRoot) '11_versions'
        [ordered]@{commit=$Target;gpu=$GpuLines;target_python=$TargetPython;site_root=$SiteRoot;cl=$Cl;cuda_device_order=$env:CUDA_DEVICE_ORDER;cuda_visible_devices=$env:CUDA_VISIBLE_DEVICES;role='ENGINEERING_PAIR_ONLY'} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Part 'environment.json') -Encoding utf8
        $PairId='pair-'+$Target.Substring(0,12)+'-'+[guid]::NewGuid().ToString('N')
        foreach ($Pass in @('pass0','pass1')) {
            $Prepared=Join-Path $Part ('prepared_'+$Pass); $Output=Join-Path $Part $Pass
            Checked $PythonExe @('-m','exposedpath.gate8_diagnostic','prepare','--output-dir',$Prepared,'--model-path',$Model,'--inventory-path',(Join-Path $Inputs 'model_sha256.csv'),'--inventory-sha256','72465C906BAEB0CFA4FD94D21EF6C69C1CD8046BB68C61A94C02A1580D2541F9','--prompt-path',(Join-Path $Inputs 'prompt_tokens.json'),'--prompt-sha256','4DFFD0DDCBD3185C656AE4A27EFAF5AAB302FEBBA6EAD5DF4D37D903A2091920','--expected-commit',$Target,'--physical-gpu','3','--engineering-attention-backend','sdpa','--target-python',$TargetPython,'--site-root',$SiteRoot,'--pair-id',$PairId,'--pair-pass',$Pass) ('12_prepare_'+$Pass)
            $M=Get-Content -LiteralPath (Join-Path $Prepared 'manifest.json') -Raw | ConvertFrom-Json
            if ($M.runner_git_commit -ne $Target -or $M.runner_git_dirty -ne $false -or $M.gpu_uuid -ne $Gpu[1] -or $M.fixed_input_tokens -ne 32 -or $M.fixed_output_tokens -ne 2 -or $M.batch_size -ne 1 -or $M.warmup_count -ne 1 -or $M.repeat_count -ne 1 -or $M.attention_backend -ne 'sdpa' -or $M.engineering_pair.pass_id -ne $Pass) { throw 'Prepared contract conflict' }
            if ($Pass -eq 'pass0') {
                Checked $PythonExe @('scripts/gate8_pair.py','baseline','--python',$TargetPython,'--prepared',$Prepared,'--output',$Output,'--execute-engineering-baseline') '13_baseline'
            } else {
                Checked $PythonExe @('scripts/gate8_diagnostic_collect.py','--nsys',$Nsys,'--python',$TargetPython,'--prepared',$Prepared,'--output',$Output,'--execute-engineering-diagnostic','--engineering-a-only') '14_profile'
                # Formal output remains immutable. Validate eligibility, not conditional A, here.
                $Check=@'
import sys,json
from pathlib import Path
from exposedpath_v141.gate8_warning_assumption import select_assumed_warnings,ASSUMPTION
p=Path(sys.argv[1]); read=lambda p:json.loads(p.read_text(encoding='utf-8'))
r=read(p/'collection_report.json'); a=read(p/'analyzed/engineering_a.json')
if r.get('error') not in (None,'MODEL_A_SCOPE_BLOCKED'): raise ValueError('Non-warning collection error')
if a['status']=='BLOCKED':
    if not all(x['reasons']==['ENGINEERING_SCOPE_DIAGNOSTIC_IMPACT_UNBOUNDED'] for x in a['requests']): raise ValueError('Other formal failure')
    proof=select_assumed_warnings(read(p/'analyzed/diagnostics.json'),a['diagnostic_dispositions'],ASSUMPTION)
    print('CONDITIONAL_ANALYSIS_PENDING_LOCAL; scope_proven=',proof['scope_proven'])
elif a['status']!='A_SCOPE_ENGINEERING_ONLY': raise ValueError('Unexpected A status')
'@
                Checked $PythonExe @('-c',$Check,$Output) '15_eligibility_only'
            }
        }
        Checked $PythonExe @('scripts/gate8_pair.py','summarize','--pass0',(Join-Path $Part 'pass0'),'--pass1',(Join-Path $Part 'pass1'),'--output',(Join-Path $Part 'pair_observation.json')) '16_pair_summary'
        $Status='PAIR_COLLECTED_PENDING_LOCAL_A_AUDIT'
    }
} catch { $Failure=$_.ToString(); Write-Host ('STOP: '+$Failure) }
finally {
    $env:CUDA_VISIBLE_DEVICES='3'
    try { CheckTree $Target } catch { $Status='BLOCKED'; $Failure=([string]$Failure+'; '+$_.ToString()) }
    $ActualHead=& git -C $CodeRoot rev-parse HEAD
    if ($LASTEXITCODE -ne 0) { $ActualHead=$null }
    [ordered]@{status=$Status;error=$Failure;commit=$Target;actual_commit=$ActualHead;stage=$Stage;gate8='NOT_RUN';warning_scope_proven=$false;automatic_retry=$false} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Part 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
}
# Never pack while a timed-out process may still be writing; no process-name kill.
foreach ($P in @(Get-ChildItem -LiteralPath $Batch -Recurse -File -Filter 'process.json')) {
    $V=Get-Content -LiteralPath $P.FullName -Raw | ConvertFrom-Json
    if ($V.descendant_exit_status -eq 'UNKNOWN_STOP_AND_INSPECT_NO_RETRY') { throw 'Potential live writer: stop before packaging; no retry' }
}
$StageFiles=@(Get-ChildItem -LiteralPath $Part -Recurse -File)
$StageRows=@($StageFiles | ForEach-Object {[pscustomobject]@{path=$_.FullName.Substring($Part.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
$StageRows | Export-Csv -LiteralPath (Join-Path $Part 'artifact_sha256.csv') -NoTypeInformation -Encoding utf8
$Files=@(Get-ChildItem -LiteralPath $Batch -Recurse -File)
$Rows=@($Files | ForEach-Object {[pscustomobject]@{path=$_.FullName.Substring($Batch.Length+1);bytes=$_.Length;sha256=(Get-FileHash -LiteralPath $_.FullName).Hash}})
$Index=Join-Path $Batch ('artifact_'+$Stage.ToLowerInvariant()+'.csv')
if (Test-Path -LiteralPath $Index) { throw 'Refuse index overwrite' }
$Rows | Export-Csv -LiteralPath $Index -NoTypeInformation -Encoding utf8
foreach ($R in $Rows) {
    $P=Join-Path $Batch $R.path
    if ((Get-Item -LiteralPath $P).Length -ne $R.bytes -or (Get-FileHash -LiteralPath $P).Hash -ne $R.sha256) { throw 'Evidence changed; do not package' }
}
$Zip=Join-Path $ServerRoot ('transfer\pair_'+$Target.Substring(0,12)+'_'+$Stage.ToLowerInvariant()+'.zip')
if (Test-Path -LiteralPath $Zip) { throw 'Refuse ZIP overwrite' }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[IO.Compression.ZipFile]::CreateFromDirectory($Batch,$Zip,[IO.Compression.CompressionLevel]::Optimal,$false)
Write-Host ('STATUS='+$Status); Write-Host ('ZIP='+$Zip)
Write-Host ('ZIP_BYTES='+(Get-Item -LiteralPath $Zip).Length)
Write-Host ('ZIP_SHA256='+(Get-FileHash -LiteralPath $Zip).Hash)
Write-Host ('MANIFEST_SHA256='+(Get-FileHash -LiteralPath $Index).Hash)
if ($Status -eq 'BLOCKED') { throw 'Stopped; return only this ZIP for review, do not retry' }
