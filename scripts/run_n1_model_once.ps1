param([switch]$ReviewedFeasibilityAuthorized)
$ErrorActionPreference='Stop'
if (!$ReviewedFeasibilityAuthorized) { throw 'Coordinator review and explicit CUDA/model/Nsight authorization required' }
$C=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw | ConvertFrom-Json
$Code=$C.code_root; $Target=$C.commit; $Parent=$C.prerequisite
$Bundle=Join-Path $PSScriptRoot $C.bundle
if ((Get-Item -LiteralPath $Bundle).Length -ne $C.bundle_bytes -or (Get-FileHash -LiteralPath $Bundle).Hash -ne $C.bundle_sha256) { throw 'Bundle identity conflict' }
$Remaining=$null -ne $C.PSObject.Properties['variants']
$Prefix=if ($Remaining) {'n1_remaining_'} else {'n1_model_'}
if ($Remaining -and (@($C.variants) -join ',') -ne 'Vmarker,V16') { throw 'Only reviewed remaining Vmarker/V16 allowed' }
$Out=Join-Path $C.server_root ('evidence\gate10\'+$Prefix+$Target.Substring(0,7)+'_once')
$Zip=Join-Path $C.server_root ('transfer\'+$Prefix+$Target.Substring(0,7)+'_once.zip')
if ((Test-Path -LiteralPath $Out) -or (Test-Path -LiteralPath $Zip)) { throw 'No resume, overwrite or retry' }
New-Item -ItemType Directory -Path $Out | Out-Null
Copy-Item -LiteralPath $PSCommandPath -Destination (Join-Path $Out 'executed.ps1')
Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Destination (Join-Path $Out 'delivery.json')
Start-Transcript -LiteralPath (Join-Path $Out 'transcript.txt') | Out-Null
$Status='BLOCKED'; $Failure=$null
function Run([string]$Exe,[string[]]$Argv,[string]$Name) {
    $Saved=$ErrorActionPreference
    try { $ErrorActionPreference='Continue'; $global:LASTEXITCODE=$null; $Lines=& $Exe @Argv 2>&1; $Exit=$LASTEXITCODE }
    finally { $ErrorActionPreference=$Saved }
    $Lines | Out-File -LiteralPath (Join-Path $Out ($Name+'.log')) -Encoding utf8
    [ordered]@{argv=$Argv;exit_code=$Exit} | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out ($Name+'.exit.json')) -Encoding utf8
    if ($Exit -ne 0) { throw ($Name+' failed; no retry; exit='+$Exit) }
}
function Tree([string]$Want) {
    $H=& git -C $Code rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $H -ne $Want) { throw 'HEAD mismatch' }
    $S=@(& git -C $Code status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $S.Count -ne 0) { throw 'Dirty tree' }
}
try {
    Tree $Parent
    Set-Location -LiteralPath $Code
    Run 'git' @('bundle','verify',$Bundle) '01_bundle'
    Run 'git' @('fetch',$Bundle,'refs/heads/main:refs/remotes/n1-model-delivery/main') '02_fetch'
    $H=& git rev-parse refs/remotes/n1-model-delivery/main
    if ($LASTEXITCODE -ne 0 -or $H -ne $Target) { throw 'Fetched commit conflict' }
    Run 'git' @('-c','core.autocrlf=false','checkout','--detach',$Target) '03_checkout'
    Tree $Target
    foreach ($F in $C.source_hashes.PSObject.Properties) {
        if ((Get-FileHash -LiteralPath (Join-Path $Code $F.Name)).Hash -ne $F.Value) { throw ('Source bytes mismatch: '+$F.Name) }
    }
    $Python=Join-Path $Code '.venv\Scripts\python.exe'
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID'; $env:CUDA_VISIBLE_DEVICES='-1'
    Run $Python (@('-m','pytest','-q','-p','no:cacheprovider')+@($C.tests)) '04_cpu'
    Tree $Target
    $env:CUDA_VISIBLE_DEVICES='3'; $env:HF_HUB_OFFLINE='1'; $env:TRANSFORMERS_OFFLINE='1'
    if ((Get-FileHash -LiteralPath $C.nsys).Hash -ne $C.nsys_sha256) { throw 'Nsight binary changed' }
    Run $C.nsys @('--version') '05_nsys'
    $Identity=@'
import sys,json,torch,transformers
assert sys.version_info[:3]==(3,11,16)
assert torch.__version__=='2.6.0+cu124' and torch.version.cuda=='12.4'
assert transformers.__version__=='5.17.0'
print(json.dumps(dict(python=sys.version,executable=sys.executable,torch=torch.__version__,cuda=torch.version.cuda,transformers=transformers.__version__)))
'@
    Run $Python @('-c',$Identity) '06_environment'
    $Gpu=@(& nvidia-smi '--id=3' '--query-gpu=index,uuid,pci.bus_id,name,driver_version' '--format=csv,noheader,nounits')
    if ($LASTEXITCODE -ne 0 -or $Gpu.Count -ne 1) { throw 'GPU query failed' }
    $Gpu | Out-File -LiteralPath (Join-Path $Out 'gpu_identity.txt') -Encoding utf8
    $G=@($Gpu[0].Split(',') | ForEach-Object {$_.Trim()})
    if ($G[0] -ne '3' -or $G[1] -ne $C.gpu_uuid -or $G[2] -ine $C.gpu_pci_bus_id -or $G[4] -ne '555.99') { throw 'GPU/driver conflict' }
    $Prompt=Join-Path $PSScriptRoot 'prompt_tokens.json'
    $Inventory=Join-Path $PSScriptRoot 'model_sha256.csv'
    if ((Get-FileHash -LiteralPath $Prompt).Hash -ne $C.prompt_sha256 -or (Get-FileHash -LiteralPath $Inventory).Hash -ne $C.inventory_sha256) { throw 'Sealed input conflict' }
    $C | Add-Member -NotePropertyName prompt -NotePropertyValue $Prompt -Force
    $C | Add-Member -NotePropertyName inventory -NotePropertyValue $Inventory -Force
    if ($Remaining) {
        foreach ($Name in @('baseline_reference.json','baseline_review.json')) {
            Copy-Item -LiteralPath (Join-Path $PSScriptRoot $Name) -Destination (Join-Path $Out $Name)
        }
        $C | Add-Member -NotePropertyName baseline_reference -NotePropertyValue (Join-Path $Out 'baseline_reference.json') -Force
        $C | Add-Member -NotePropertyName baseline_review -NotePropertyValue (Join-Path $Out 'baseline_review.json') -Force
    }
    $Config=Join-Path $Out 'run_config.json'
    $C | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $Config -Encoding utf8
    Run $Python @('scripts/n1_model_feasibility.py','--config',$Config,'--output',(Join-Path $Out 'batch'),'--execute-reviewed-feasibility') '07_batch'
    $R=Get-Content -LiteralPath (Join-Path $Out 'batch\batch_report.json') -Raw | ConvertFrom-Json
    $Expected=if ($Remaining) {'Vmarker,V16'} else {'V0,Vmarker,V16'}
    $Count=if ($Remaining) {2} else {3}
    if ($R.status -ne 'BATCH_COMPLETE_PENDING_REVIEW' -or $R.groups.Count -ne $Count -or (@($R.groups | ForEach-Object {$_.variant}) -join ',') -ne $Expected) { throw 'Machine batch report not complete' }
    Tree $Target
    $Status='COLLECTED_PENDING_N1_MODEL_REVIEW'
} catch { $Failure=$_.ToString(); Write-Host ('STOP: '+$Failure) }
finally {
    try { Tree $Target } catch { $Status='BLOCKED'; $Failure=([string]$Failure+'; '+$_.ToString()) }
    [ordered]@{status=$Status;error=$Failure;commit=$Target;n1_model_feasibility='NOT_RUN';gate10_g1='PASS';automatic_retry=$false} | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $Out 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
}
foreach ($P in @(Get-ChildItem -LiteralPath $Out -Recurse -File -Filter 'process.json')) {
    $V=Get-Content -LiteralPath $P.FullName -Raw | ConvertFrom-Json
    if ($V.descendant_exit_status -eq 'UNKNOWN_STOP_AND_INSPECT_NO_RETRY') { throw 'Possible live writer: stop packaging, consult coordinator, do not retry' }
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
if ($Status -eq 'BLOCKED') { throw 'Return the single ZIP; do not retry' }
