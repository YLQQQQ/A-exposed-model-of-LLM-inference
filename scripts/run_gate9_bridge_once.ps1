param([switch]$ReviewedControlledCollectionAuthorized)
$ErrorActionPreference='Stop'
if (!$ReviewedControlledCollectionAuthorized) { throw 'Coordinator review and explicit controlled CUDA/Nsight authorization required' }
$C=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'delivery.json') -Raw | ConvertFrom-Json
$Code=$C.code_root; $Target=$C.commit; $Parent=$C.prerequisite
$Bundle=Join-Path $PSScriptRoot $C.bundle
if ((Get-Item -LiteralPath $Bundle).Length -ne $C.bundle_bytes -or (Get-FileHash -LiteralPath $Bundle).Hash -ne $C.bundle_sha256) { throw 'Bundle identity conflict' }
$Out=Join-Path $C.server_root ('evidence\gate9\bridge_'+$Target.Substring(0,7)+'_once')
$Zip=Join-Path $C.server_root ('transfer\gate9_bridge_'+$Target.Substring(0,7)+'_once.zip')
if ((Test-Path -LiteralPath $Out) -or (Test-Path -LiteralPath $Zip)) { throw 'No overwrite/resume/automatic retry' }
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
    if ($Exit -ne 0) { throw ($Name+' failed; stop without retry; exit='+$Exit) }
}
function Tree([string]$Want) {
    $Head=& git -C $Code rev-parse HEAD
    if ($LASTEXITCODE -ne 0 -or $Head -ne $Want) { throw 'HEAD mismatch' }
    $S=@(& git -C $Code status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $S.Count -ne 0) { throw 'Tree not clean' }
}
try {
    Tree $Parent
    Set-Location -LiteralPath $Code
    Run 'git' @('bundle','verify',$Bundle) '01_bundle'
    Run 'git' @('fetch',$Bundle,'refs/heads/main:refs/remotes/gate9-bridge/main') '02_fetch'
    $Ref=& git rev-parse refs/remotes/gate9-bridge/main
    if ($LASTEXITCODE -ne 0 -or $Ref -ne $Target) { throw 'Fetched identity conflict' }
    Run 'git' @('-c','core.autocrlf=false','checkout','--detach',$Target) '03_checkout'
    Tree $Target
    foreach ($F in $C.source_hashes.PSObject.Properties) {
        if ((Get-FileHash -LiteralPath (Join-Path $Code $F.Name)).Hash -ne $F.Value) { throw ('Source bytes mismatch: '+$F.Name) }
    }
    $Python=Join-Path $Code '.venv\Scripts\python.exe'
    $Site=Join-Path $Code '.venv\Lib\site-packages'
    $env:CUDA_DEVICE_ORDER='PCI_BUS_ID'; $env:CUDA_VISIBLE_DEVICES='-1'
    Run $Python (@('-m','pytest','-q','-p','no:cacheprovider')+@($C.tests)) '04_cpu'
    Run $Python @('-m','compileall','-q','exposedpath/gate9_stream_bridge.py','exposedpath_v141/gate9_domain.py','exposedpath_v141/gate9_n1.py','exposedpath_v141/gate9_bridge_oracle.py','scripts/gate9_bridge_target.py','scripts/gate9_bridge_run.py') '05_compile'
    Tree $Target
    # Explicit VS initialization; zero-byte compatibility markers are not executed.
    Import-Module -Name (Join-Path $C.vs_root 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll')
    Enter-VsDevShell -VsInstallPath $C.vs_root -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.38'
    $Cl=(Get-Command cl.exe -ErrorAction Stop).Source
    $WantCl=Join-Path $C.vs_root 'VC\Tools\MSVC\14.38.33130\bin\Hostx64\x64\cl.exe'
    if ($Cl -ne $WantCl -or (Get-Item -LiteralPath $Cl).VersionInfo.FileVersion -notmatch '^19\.38\.33135' -or
        $env:VSCMD_ARG_HOST_ARCH -ne 'x64' -or $env:VSCMD_ARG_TGT_ARCH -ne 'x64' -or $env:VCToolsVersion.TrimEnd('\') -ne '14.38.33130') { throw 'MSVC identity conflict' }
    $Markers=@(foreach ($Name in @('vcvarsall.bat','vcvars64.bat')) {
        $F=Get-Item -LiteralPath (Join-Path $C.vs_root ('VC\Auxiliary\Build\'+$Name))
        if ($F.Length -ne 0) { throw 'Compatibility marker changed' }
        [pscustomobject]@{path=$F.FullName;bytes=$F.Length;sha256=(Get-FileHash -LiteralPath $F.FullName).Hash}
    })
    if (!(Test-Path -LiteralPath (Join-Path $C.nvtx_include 'nvtx3\nvToolsExt.h') -PathType Leaf)) { throw 'NVTX header missing' }
    Run $C.nvcc @('--version') '06_nvcc'
    if ((Get-Content -LiteralPath (Join-Path $Out '06_nvcc.log') -Raw) -notmatch 'V12\.4\.131') { throw 'CUDA build version conflict' }
    $Build=Join-Path $Out 'build'; New-Item -ItemType Directory -Path $Build | Out-Null
    $Library=Join-Path $Build 'gate9_bridge_token.dll'
    Push-Location -LiteralPath $Build
    try { Run $C.nvcc @('-std=c++17','-shared','--cudart','shared','--default-stream','legacy','-I',$C.nvtx_include,'-o',$Library,(Join-Path $Code 'scripts\gate9_bridge_token.cu')) '07_build' }
    finally { Pop-Location }
    [ordered]@{cl=$Cl;cl_version=(Get-Item -LiteralPath $Cl).VersionInfo.FileVersion;markers=$Markers;
        nvtx_header_sha256=(Get-FileHash -LiteralPath (Join-Path $C.nvtx_include 'nvtx3\nvToolsExt.h')).Hash;
        library_sha256=(Get-FileHash -LiteralPath $Library).Hash;default_stream_build='legacy';measured_stream='explicit_nonblocking_not_default'} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out 'build_identity.json') -Encoding utf8
    Set-Location -LiteralPath $Code
    $env:CUDA_VISIBLE_DEVICES='3'
    # One real CUDA/Nsight execution, NOT CPU-only; no model, retry or old probe.
    Run $Python @('-m','scripts.gate9_bridge_run','--python',$C.target_python,'--site',$Site,'--nsys',$C.nsys,
        '--library',$Library,'--commit',$Target,'--uuid',$C.gpu_uuid,'--pci',$C.gpu_pci,
        '--output',(Join-Path $Out 'collection'),'--execute-controlled') '08_bridge'
    $Report=Get-Content -LiteralPath (Join-Path $Out 'collection\collection_report.json') -Raw | ConvertFrom-Json
    if ($Report.status -ne 'BRIDGE_MATCH_REVIEW_REQUIRED' -or $Report.gate9_verdict -ne 'NOT_RUN') { throw 'Machine report not eligible for review' }
    Tree $Target
    $Status='BRIDGE_MATCH_REVIEW_REQUIRED_NOT_GATE9_PASS'
} catch { $Failure=$_.ToString() }
finally {
    [ordered]@{status=$Status;error=$Failure;execution_commit=$Target;prerequisite=$Parent;retry=$false} |
        ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $Out 'receipt.json') -Encoding utf8
    Stop-Transcript | Out-Null
    $All=@(Get-ChildItem -LiteralPath $Out -File -Recurse)
    $Rows=@(foreach ($F in $All) {
        [pscustomobject]@{path=$F.FullName.Substring($Out.Length+1);bytes=$F.Length;sha256=(Get-FileHash -LiteralPath $F.FullName).Hash}
    })
    $Rows | Export-Csv -LiteralPath (Join-Path $Out 'artifact_sha256.csv') -NoTypeInformation -Encoding UTF8
    Compress-Archive -LiteralPath @(Get-ChildItem -LiteralPath $Out | ForEach-Object {$_.FullName}) -DestinationPath $Zip
    Write-Host ('ZIP='+$Zip)
    Write-Host ('ZIP_BYTES='+(Get-Item -LiteralPath $Zip).Length)
    Write-Host ('ZIP_SHA256='+(Get-FileHash -LiteralPath $Zip).Hash)
    Write-Host ('STATUS='+$Status)
}
if ($Status -ne 'BRIDGE_MATCH_REVIEW_REQUIRED_NOT_GATE9_PASS') { throw $Failure }
