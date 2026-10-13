# Stage1 ONLY. No native model, GPU identity query, profile/export or cleanup.
param([string]$PackageRoot = $PSScriptRoot)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$ConfigPath = Join-Path $PackageRoot 'config.json'
$Config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($Config.schema_version -notin @('exposedpath-native-stage1/0.1.0','exposedpath-native-stage1/0.2.0') -or
    $Config.model_process_budget -ne 0 -or $Config.profile_budget -ne 0) { throw 'Stage1 contract conflict' }
$Root = $Config.output_root
$Archive = $Config.return_zip
if ((Test-Path -LiteralPath $Root) -or (Test-Path -LiteralPath $Archive)) { throw 'No overwrite/resume/retry' }
$ExpectedParent = [IO.Path]::GetFullPath((Join-Path $Config.server_root 'diagnostics')) + '\'
if (-not [IO.Path]::GetFullPath($Root).StartsWith($ExpectedParent,[StringComparison]::OrdinalIgnoreCase)) { throw 'Output scope conflict' }
if ([IO.DriveInfo]::new([IO.Path]::GetPathRoot($Root)).AvailableFreeSpace -lt 20GB) { throw 'Need 20GiB temporary free space; STOP' }
$Bootstrap = Join-Path $PackageRoot 'native_stage1.py'
$Manifest = Get-Content -LiteralPath (Join-Path $PackageRoot 'package_manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
$BootstrapRef = @($Manifest.files | Where-Object { $_.path -eq 'native_stage1.py' })
if ($BootstrapRef.Count -ne 1 -or (Get-FileHash -LiteralPath $Bootstrap -Algorithm SHA256).Hash.ToLowerInvariant() -ne $BootstrapRef[0].sha256) { throw 'Bootstrap conflict' }
& $Config.base_python -I $Bootstrap verify-package --package $PackageRoot
if ($LASTEXITCODE -ne 0) { throw 'Package verification failed' }
New-Item -ItemType Directory -Path $Root | Out-Null
Copy-Item -LiteralPath $ConfigPath -Destination (Join-Path $Root 'config.json')
Copy-Item -LiteralPath (Join-Path $PackageRoot 'package_manifest.json') -Destination (Join-Path $Root 'delivery_manifest.json')
Start-Transcript -LiteralPath (Join-Path $Root 'transcript.txt') | Out-Null
$Failed = $false
try {
    $env:CUDA_VISIBLE_DEVICES = '-1'
    $env:CUDA_DEVICE_ORDER = 'PCI_BUS_ID'
    $env:PYTHONUTF8 = '1'
    $env:HF_HUB_OFFLINE = '1'
    $env:TRANSFORMERS_OFFLINE = '1'
    if ($Config.schema_version -eq 'exposedpath-native-stage1/0.1.0') {
    $DevModule = Join-Path $Config.vs_root 'Common7\Tools\Microsoft.VisualStudio.DevShell.dll'
    if (-not (Test-Path -LiteralPath $DevModule)) { throw 'Existing VS2022 DevShell missing; no installation' }
    Import-Module $DevModule
    Enter-VsDevShell -VsInstallPath $Config.vs_root -SkipAutomaticLocation -DevCmdArguments '-arch=x64 -host_arch=x64 -vcvars_ver=14.38.33130'
    if ($env:VSCMD_ARG_HOST_ARCH -ne 'x64' -or $env:VSCMD_ARG_TGT_ARCH -ne 'x64' -or $env:VCToolsVersion -ne '14.38.33130') { throw 'MSVC environment conflict' }
    $Cl = (Get-Command cl.exe -CommandType Application).Source
    $ExpectedCl = Join-Path $Config.vs_root 'VC\Tools\MSVC\14.38.33130\bin\Hostx64\x64\cl.exe'
    if ($Cl -ne $ExpectedCl) { throw 'Actual cl.exe path conflict' }
    # Compiler version commands inspect CPU tools, not CUDA devices.
    $SavedPreference = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $ClText = (& $Cl 2>&1 | Out-String)
    $ClExit = $LASTEXITCODE
    $ErrorActionPreference = $SavedPreference
    if ($ClText -notmatch '19\.38\.33135' -or $ClExit -notin @(0,2)) { throw 'Compiler version conflict' }
    $Nvcc = Join-Path $Config.cuda_root 'bin\nvcc.exe'
    $NvccText = (& $Nvcc --version | Out-String)
    $NvccExit = $LASTEXITCODE
    if ($NvccExit -ne 0 -or $NvccText -notmatch 'V12\.4\.131') { throw 'Existing CUDA compiler conflict; no upgrade' }
    $RuntimeFiles = @()
    foreach ($Name in @('cudart64_12.dll','cublas64_12.dll','cublasLt64_12.dll')) {
        $Path = Join-Path (Join-Path $Config.cuda_root 'bin') $Name
        if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw ('Existing CUDA runtime file missing: '+$Name) }
        $Item = Get-Item -LiteralPath $Path
        $RuntimeFiles += [ordered]@{ name=$Name; path=$Path; bytes=$Item.Length;
            sha256=(Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash; file_version=$Item.VersionInfo.FileVersion }
    }
    $Toolchain = [ordered]@{ cl_path=$Cl; cl_sha256=(Get-FileHash -LiteralPath $Cl -Algorithm SHA256).Hash;
        cl_version_output=$ClText; cl_exit=$ClExit; nvcc_path=$Nvcc;
        nvcc_sha256=(Get-FileHash -LiteralPath $Nvcc -Algorithm SHA256).Hash;
        nvcc_version_output=$NvccText; nvcc_exit=$NvccExit;
        host_arch=$env:VSCMD_ARG_HOST_ARCH; target_arch=$env:VSCMD_ARG_TGT_ARCH;
        VCToolsVersion=$env:VCToolsVersion; device_query_invoked=$false; runtime_files=$RuntimeFiles }
    $Encoding = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((Join-Path $Root 'toolchain.json'),($Toolchain | ConvertTo-Json -Depth 8),$Encoding)
    } else {
        # Ninja adapter binds absolute tools/SDK and its own clean compile env.
        # Do not repair VS registration/default files or import a guessed toolset.
        Write-Host '[stage] explicit Ninja/MSVC14.38/SDK route; no VS metadata changes'
    }
    Write-Host '[stage] deploy START'
    & $Config.base_python -I $Bootstrap deploy --config $ConfigPath --package $PackageRoot --root $Root
    if ($LASTEXITCODE -ne 0) { throw 'Deployment failed; STOP' }
    Write-Host '[stage] deploy COMPLETE; CPU dependencies/build/conversion next; no native execution'
    # Controller reuses the verified repository JSON/schema dependencies.
    # 0.1 creates a private CPU env; 0.2 byte-binds the prior CPU env read-only.
    & $Config.test_python -I $Bootstrap run --config $ConfigPath --package $PackageRoot --root $Root
    if ($LASTEXITCODE -ne 0) { throw 'Stage1 failed; no retry; preserve outputs' }
} catch {
    $Failed = $true
    $Failure = [ordered]@{ status='BLOCKED'; error=$_.Exception.Message; automatic_retry=$false;
        native_model_invoked=$false; collector_invoked=$false; gpu_qualification='NOT_RUN' }
    $Encoding = New-Object Text.UTF8Encoding($false)
    [IO.File]::WriteAllText((Join-Path $Root 'launcher_failure.json'),($Failure | ConvertTo-Json -Depth 6),$Encoding)
    Write-Host ('STOP: '+$_.Exception.Message)
} finally {
    Stop-Transcript | Out-Null
}
# Review archive: metadata and finished logs ONLY, not GGUF/build/env/model.
# This verifies copy consistency, not absence of all descendants after timeout.
& $Config.base_python -I $Bootstrap pack --root $Root --archive $Archive
if ($LASTEXITCODE -ne 0) { throw 'Review packaging failed; preserve outputs, no cleanup' }
Write-Host ('RETURN_ZIP='+$Archive)
Write-Host ('ZIP_BYTES='+(Get-Item -LiteralPath $Archive).Length)
Write-Host ('ZIP_SHA256='+(Get-FileHash -LiteralPath $Archive -Algorithm SHA256).Hash)
if ($Failed) { throw 'Stage1 BLOCKED; return the one review ZIP; do not retry' }
Write-Host 'Stage1 completed; GPU/native qualification remains NOT_RUN. STOP before stage2.'
