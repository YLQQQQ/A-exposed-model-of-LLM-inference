# Test-only: execute the actual parsed launcher with external process boundaries
# replaced. No production test flag, actual Git mutation, CUDA, nsys or model.
$ErrorActionPreference='Stop'
# The host may be PS7. Load PS5.1's own real cmdlets, never inherited PS7 modules.
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1') -ErrorAction Stop
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management\Microsoft.PowerShell.Management.psd1') -ErrorAction Stop
$Launcher=$env:COE_TEST_LAUNCHER
$Source=[IO.File]::ReadAllText($Launcher)
$Tokens=$null;$Errors=$null
$Ast=[System.Management.Automation.Language.Parser]::ParseInput($Source,[ref]$Tokens,[ref]$Errors)
if ($Errors.Count) {throw 'Actual launcher parse failed'}
$TopTry=@($Ast.EndBlock.Statements | Where-Object {$_ -is [System.Management.Automation.Language.TryStatementAst]})
if ($TopTry.Count -ne 1) {throw 'Test boundary does not match actual launcher'}
$Boundary=@'
$Python=$env:COE_TEST_LOCAL_PYTHON
$script:CpuHead=$C.prerequisite
if ($CollectReviewedPilot) {$script:CpuHead=$Target}
function global:git {
    $A=@($args);$global:LASTEXITCODE=0
    if ($A -contains 'rev-parse') {
        if ($A -contains 'refs/remotes/coe-pilot/execution') {$Target} else {$script:CpuHead}
    } elseif ($A -notcontains 'status') {throw 'Unexpected direct Git command in CPU boundary'}
}
function Run([string]$Exe,[string[]]$Argv,[string]$Name) {
    if ($Name -in @('01_bundle','02_fetch','03_checkout','04_cpu_changed_wiring','05_compile_changed_wiring','07_nsys_version')) {
        if ($Name -eq '03_checkout') {$script:CpuHead=$Target}
        if ($Name -eq '04_cpu_changed_wiring' -and
            (($Argv[-2..-1] -join '|') -ne 'tests/test_coe_startup_storage.py|tests/test_coe_delivery_resources.py')) {throw 'Unexpected/repeated CPU test set'}
        if ($Name -eq '05_compile_changed_wiring' -and
            (($Argv -join '|') -ne '-X|utf8|-m|py_compile|scripts/coe_startup_storage.py|scripts/coe_delivery_reuse.py')) {throw 'Unexpected compile scope'}
        if ($Name -eq '07_nsys_version' -and ($Argv -join '|') -ne '--version') {throw 'Unexpected collector execution'}
        Write-Host ('CPU_PROCESS_BOUNDARY '+$Name)
    } elseif ($Name -eq 'component_reuse') {
        & $Python @Argv
        if ($LASTEXITCODE -ne 0) {throw 'CPU real component_reuse failed'}
    } elseif ($Name -eq 'storage') {
        & $Python $env:COE_TEST_STORAGE_BOUNDARY @($Argv | Select-Object -Skip 3)
        if ($LASTEXITCODE -ne 0) {throw 'CPU real storage failed'}
    } elseif ($Name -eq '08_nine_p1') {
        $Expected=@('-X','utf8','-u','scripts/coe_pilot_batch.py','--config',(Join-Path $Out 'run_config.json'),
            '--output',(Join-Path $Out 'experiment'),'--collect-reviewed-coe-pilot')
        if (($Argv -join '|') -ne ($Expected -join '|')) {throw 'Unexpected batch command'}
        $Cfg=Get-Content -LiteralPath (Join-Path $Out 'run_config.json') -Raw | ConvertFrom-Json
        if ($Cfg.commit -ne $Target -or $Cfg.analysis_commit -ne $Target -or
            $Cfg.profile_budget -ne 9 -or $Cfg.model_process_budget -ne 9) {throw 'CPU batch identity conflict'}
        [IO.File]::WriteAllText((Join-Path $C.server_root 'collector_was_called'),'CPU_BOUNDARY_ONLY')
        $P=Join-Path $Out 'experiment/batch';New-Item -ItemType Directory -Path $P | Out-Null
        @{status='FIXED_NINE_COMPLETE_STOP_FOR_REVIEW';runs=@(1..9);blocks=@(1..3)} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $P 'batch_report.json') -Encoding utf8
        Write-Host 'CPU_NINE_SLOT_BOUNDARY_NOT_MODEL_EXECUTION'
    } else {throw ('Unexpected external process in CPU boundary: '+$Name)}
}
'@
$Source=$Source.Insert($TopTry[0].Extent.StartOffset,$Boundary+"`n")
$Context="`n`$PSScriptRoot='"+([IO.Path]::GetDirectoryName($Launcher).Replace("'","''"))+"'`n`$PSCommandPath='"+$Launcher.Replace("'","''")+"'`n"
$ReuseFunction=@($Ast.FindAll({param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Reuse'},$true))
# A ScriptBlock created from text has no file-backed automatic variables inside
# functions. Restore ONLY that file location context, not any branch or check.
if ($ReuseFunction.Count -ne 1) {throw 'Test function context does not match launcher'}
$Source=$Source.Insert($ReuseFunction[0].Body.Extent.StartOffset+1,$Context)
$Source=$Source.Insert($Ast.ParamBlock.Extent.EndOffset,$Context)
$env:COE_TEST_STORAGE_BOUNDARY=Join-Path $PSScriptRoot 'coe_storage_boundary.py'
$Params=@{}
if ($env:COE_TEST_COLLECT -eq '1') {$Params.CollectReviewedPilot=$true;$Params.ReviewedStaticReceiptSHA256=$env:COE_TEST_REVIEWED}
& ([scriptblock]::Create($Source)) @Params
