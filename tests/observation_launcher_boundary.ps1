# Test only: execute actual launcher branches/checks, replace external commands.
$ErrorActionPreference='Stop'
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Utility\Microsoft.PowerShell.Utility.psd1')
Import-Module (Join-Path $PSHOME 'Modules\Microsoft.PowerShell.Management\Microsoft.PowerShell.Management.psd1')
$Launcher=$env:OBS_TEST_LAUNCHER;$Source=[IO.File]::ReadAllText($Launcher)
$Tokens=$null;$Errors=$null
$Ast=[System.Management.Automation.Language.Parser]::ParseInput($Source,[ref]$Tokens,[ref]$Errors)
if ($Errors.Count) {throw 'Actual launcher parse failed'}
$TopTry=@($Ast.EndBlock.Statements | Where-Object {$_ -is [System.Management.Automation.Language.TryStatementAst]})
if ($TopTry.Count -ne 1) {throw 'CPU boundary mismatch'}
$Boundary=@'
$Python=$env:OBS_TEST_PYTHON
$script:CpuHead=$C.prerequisite
if ($CollectReviewedEngineering -or $CollectReviewedInputPilot) {$script:CpuHead=$Target}
function global:git {
    $A=@($args);$global:LASTEXITCODE=0
    if ($A -contains 'rev-parse') {
        if ($A -contains 'refs/remotes/observation-preparation/execution') {$Target} else {$script:CpuHead}
    } elseif ($A -notcontains 'status') {throw 'Unexpected direct Git in CPU boundary'}
}
function Run([string]$Exe,[string[]]$Argv,[string]$Name) {
    if ($Name -in @('01_bundle','02_fetch','03_checkout','04_cpu','05_compile','06_nsys_version')) {
        if ($Name -eq '03_checkout') {$script:CpuHead=$Target}
        $Tests=if ($InputPilot) {'tests/test_coe_input_pilot.py|tests/test_coe_input_delivery.py'} else {'tests/test_observation_preparation.py|tests/test_observation_delivery.py'}
        if ($Midpoint) {$Tests+='|tests/test_coe_input_midpoint.py|tests/test_coe_midpoint_delivery.py'}
        if ($Sensitivity) {$Tests='tests/test_observation_input_sensitivity.py|tests/test_observation_input_delivery.py'}
        if ($LowSide) {$Tests='tests/test_coe_input_low3.py|tests/test_coe_low3_delivery.py|tests/test_coe_helper_identity.py::test_pinned_source_provenance_and_real_isolated_python'}
        if ($Name -eq '04_cpu' -and ((@($Argv | Where-Object {$_ -like 'tests/*'}) -join '|') -ne $Tests)) {throw 'CPU check scope drift'}
        if ($Name -eq '06_nsys_version' -and ($Argv -join '|') -ne '--version') {throw 'Collector scope drift'}
        Write-Host ('CPU_PROCESS_BOUNDARY '+$Name)
    } elseif ($Name -in @('03_python_identity','03_target_python_identity')) {
        if (!$LowSide) {throw 'Unexpected Python identity stage'}
        & $Python @Argv
        if ($LASTEXITCODE -ne 0) {throw 'CPU Python identity failed'}
    } elseif ($Name -eq 'storage') {
        & $Python $env:OBS_TEST_STORAGE @($Argv | Select-Object -Skip 3)
        if ($LASTEXITCODE -ne 0) {throw 'CPU storage check failed'}
    } elseif ($Name -in @('07_eight_p1','07_nine_p1')) {
        if ((($Midpoint -or $LowSide) -and $Name -ne '07_nine_p1') -or (!$Midpoint -and !$LowSide -and $Name -ne '07_eight_p1')) {throw 'Batch stage conflict'}
        $Flag=if ($InputPilot) {'--collect-reviewed-input-pilot'} else {'--collect-reviewed-preparation'}
        $Expected=@('-X','utf8','-u','scripts/observation_preparation_batch.py','--config',(Join-Path $Out 'run_config.json'),
            '--output',(Join-Path $Out 'experiment'),$Flag)
        if (($Argv -join '|') -ne ($Expected -join '|')) {throw 'Unexpected batch argv'}
        [IO.File]::WriteAllText((Join-Path $C.server_root 'model_boundary_called'),'CPU_DOUBLE_NOT_MODEL')
        if ($env:OBS_TEST_SCENARIO -eq 'batch_fail') {throw 'CPU hard quality failure'}
        $P=Join-Path $Out 'experiment/batch';New-Item -ItemType Directory -Path $P | Out-Null
        $Status=if ($InputPilot) {'FIXED_EIGHT_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW'} else {'FIXED_EIGHT_COMPLETE_STOP_FOR_REVIEW'}
        $Count=if ($InputPilot) {4} else {2}
        $Slots=8
        if ($Midpoint) {$Status='FIXED_NINE_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW';$Count=3;$Slots=9}
        if ($LowSide) {$Status='FIXED_NINE_LOW3_PILOT_COMPLETE_STOP_FOR_REVIEW';$Count=3;$Slots=9}
        @{status=$Status;runs=@(1..$Slots);blocks=@(1..$Count)} |
            ConvertTo-Json | Set-Content -LiteralPath (Join-Path $P 'batch_report.json') -Encoding utf8
    } else {throw ('Unexpected process in CPU boundary: '+$Name)}
}
'@
$Source=$Source.Insert($TopTry[0].Extent.StartOffset,$Boundary+"`n")
$Context="`n`$PSScriptRoot='"+([IO.Path]::GetDirectoryName($Launcher).Replace("'","''"))+"'`n`$PSCommandPath='"+$Launcher.Replace("'","''")+"'`n"
$Source=$Source.Insert($Ast.ParamBlock.Extent.EndOffset,$Context)
$Params=@{}
if ($env:OBS_TEST_COLLECT -eq '1') {
    if ($env:OBS_TEST_INPUT_PILOT -eq '1') {$Params.CollectReviewedInputPilot=$true} else {$Params.CollectReviewedEngineering=$true}
    $Params.ReviewedStaticReceiptSHA256=$env:OBS_TEST_REVIEWED
}
& ([scriptblock]::Create($Source)) @Params
