<#
.SYNOPSIS
    Cross-pass clock diagnostic: runs Pass 0->Pass 1, Pass 1->Pass 0, optional clock-locked.
.DESCRIPTION
    Run A: Pass 0 -> Pass 1 (order: pass0 first)
    Run B: Pass 1 -> Pass 0 (order: pass1 first)
    Run C: Pass 0 -> Pass 1 with locked GPU clocks (if -EnableClockLock and supported)
    Outputs cross_pass_clock_diag_report.json + .md. Does NOT overwrite old data.
#>
param(
    [Parameter(Mandatory=$true)][string]$Manifest,
    [Parameter(Mandatory=$true)][int]$GpuId,
    [Parameter(Mandatory=$true)][string]$NsysPath,
    [string]$OutputRoot = ".\pilot_clock_diag",
    [int]$RepeatCount = 2,
    [switch]$EnableClockLock,
    [int]$LockedGraphicsClockMHz = 2520,
    [switch]$ReportOnly,
    [string]$ExistingDiagDir = "",
    [switch]$ClockPreflightOnly,
    [int]$RequestedGraphicsClockMHz = 2520,
    [int]$ClockToleranceMHz = 50,
    [int]$ClockVerificationSamples = 5
)
$ErrorActionPreference = "Continue"
$ScriptDir = if($PSScriptRoot){$PSScriptRoot}else{Split-Path -Parent $MyInvocation.MyCommand.Path}; $ProjectRoot = Split-Path -Parent $ScriptDir
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

function Resolve-Exe { param([string]$N)
    if(Test-Path $N -PathType Leaf -ErrorAction SilentlyContinue){return (Resolve-Path $N -ErrorAction SilentlyContinue).Path}
    if(Test-Path $N -PathType Container -ErrorAction SilentlyContinue){$c=Join-Path $N "nsys.exe";if(Test-Path $c -PathType Leaf -ErrorAction SilentlyContinue){return (Resolve-Path $c -ErrorAction SilentlyContinue).Path}}
    try{return (Get-Command $N -ErrorAction Stop).Source}catch{}
    $v=Join-Path $ProjectRoot ".venv\Scripts\python.exe"; if($N -eq "python" -and (Test-Path $v -PathType Leaf -ErrorAction SilentlyContinue)){return $v}
    return $null
}
$Py=Resolve-Exe "python"; if(-not $Py){Write-Host "ERROR: python not found";exit 1}
$Nsys=Resolve-Exe $NsysPath; if(-not $Nsys){Write-Host "ERROR: nsys not found";exit 1}

$env:CUDA_DEVICE_ORDER="PCI_BUS_ID"
$smi_csv=& nvidia-smi --query-gpu=index,name,uuid,pci.bus_id --format=csv,noheader 2>$null
$gpu_list=@();foreach($l in $smi_csv){$p=$l -split ',\s*';if($p.Count -ge 4){$gpu_list+=@{index=[int]$p[0];name=$p[1];uuid=$p[2];pci=$p[3]}}}
$sel=$gpu_list|Where-Object{$_.index -eq $GpuId}
if(-not $sel){Write-Host "ERROR: GPU index $GpuId not found";exit 1}
$env:CUDA_VISIBLE_DEVICES=$sel.uuid
$env:PYTHONPATH="$ProjectRoot;$($env:PYTHONPATH)"
Set-Location $ProjectRoot

# Resolve and validate manifest
$ManifestPath = (Resolve-Path -LiteralPath $Manifest -ErrorAction Stop).Path
if (-not (Test-Path -Path $ManifestPath -PathType Leaf)) { Write-Host "ERROR: Manifest does not exist: $ManifestPath"; exit 1 }
$manifestSha = (Get-FileHash -Path $ManifestPath -Algorithm SHA256).Hash.ToLower()

# Validate ReportOnly + ExistingDiagDir
if ($ReportOnly) {
    if ([string]::IsNullOrWhiteSpace($ExistingDiagDir)) { Write-Host "ERROR: -ReportOnly requires -ExistingDiagDir"; exit 1 }
    try { $diagDir = (Resolve-Path -LiteralPath $ExistingDiagDir -ErrorAction Stop).Path }
    catch { Write-Host "ERROR: ExistingDiagDir not found: $ExistingDiagDir"; exit 1 }
    if (-not (Test-Path $diagDir -PathType Container)) { Write-Host "ERROR: ExistingDiagDir is not a directory: $diagDir"; exit 1 }
    Write-Host "[diag] ReportOnly mode — using existing: $diagDir"
} else {
    if (-not [string]::IsNullOrWhiteSpace($ExistingDiagDir)) { Write-Host "ERROR: -ExistingDiagDir requires -ReportOnly"; exit 1 }
    $diagDir = Join-Path $OutputRoot "diag_$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))"
    New-Item -ItemType Directory -Force -Path $diagDir | Out-Null
    # Snapshot manifest for audit trail
    Copy-Item -Path $ManifestPath -Destination (Join-Path $diagDir "wmpc_manifest.snapshot.json") -Force
}

Write-Host "[diag] Manifest: $ManifestPath"
Write-Host "[diag] Manifest SHA256: $manifestSha"

# Validate manifest before any GPU work (skip if ReportOnly or ClockPreflightOnly)
if (-not $ReportOnly -and -not $ClockPreflightOnly) {
    $valOut = & $Py -m exposedpath validate-manifest --manifest $ManifestPath 2>&1
    if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: validate-manifest failed:"; $valOut -join "`n" | Write-Host; exit 1 }
    Write-Host "[diag] validate-manifest: PASSED"
}
$mFile = $ManifestPath

function Invoke-Pass { param([string]$PassLabel,[string]$OutDir,[string]$OutBase)
    $procArgs=@("-m","exposedpath","run-$PassLabel","--manifest",$ManifestPath,"--output-dir",$OutDir)
    if($PassLabel -eq "pass1"){ $procArgs=@("profile","--trace=cuda,nvtx","--cuda-memory-usage=true","--stats=true","-o",(Join-Path $OutDir "profile"),$Py)+$procArgs; $exe=$Nsys }
    else{$exe=$Py}
    $so=Join-Path $OutDir "${OutBase}_stdout.txt"; $se=Join-Path $OutDir "${OutBase}_stderr.txt"
    $psi=New-Object System.Diagnostics.ProcessStartInfo; $psi.FileName=$exe;$psi.Arguments=$procArgs -join ' '
    $psi.UseShellExecute=$false;$psi.RedirectStandardOutput=$true;$psi.RedirectStandardError=$true
    $psi.CreateNoWindow=$true;$psi.WorkingDirectory=$ProjectRoot
    try{$proc=[System.Diagnostics.Process]::Start($psi)}catch{return -2}
    if(-not $proc){return -3}
    $out=$proc.StandardOutput.ReadToEnd();$err=$proc.StandardError.ReadToEnd();$proc.WaitForExit();$rc=$proc.ExitCode
    if($out){$out|Out-File $so -Encoding utf8}else{""|Out-File $so -Encoding utf8}
    if($err){$err|Out-File $se -Encoding utf8}else{""|Out-File $se -Encoding utf8}
    return $rc
}

function Get-GpuState {
    $s=& nvidia-smi -i $GpuId --query-gpu=index,pstate,clocks.current.graphics,clocks.current.memory,power.draw,temperature.gpu,power.limit --format=csv,noheader 2>$null
    if($s){($s -join ';')}else{"nvidia-smi query failed"}
}

$IsWindows = [System.Environment]::OSVersion.Platform -eq 'Win32NT'

# ---- Run-NvidiaSmi: execute nvidia-smi with -i, capture full command result ----
function Run-NvidiaSmi {
    param([string[]]$SmiArgs)
    $argStr="$($SmiArgs -join ' ')"
    $cmd="nvidia-smi -i $GpuId $argStr"
    $psi=New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName="nvidia-smi"; $psi.Arguments="-i $GpuId $argStr"
    $psi.UseShellExecute=$false; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $psi.CreateNoWindow=$true
    try{$p=[System.Diagnostics.Process]::Start($psi)}catch{return @{command=$cmd; exit_code=1; stdout=""; stderr=$_.Exception.Message}}
    if(-not $p){return @{command=$cmd; exit_code=1; stdout=""; stderr="Process.Start null"}}
    $so=$p.StandardOutput.ReadToEnd(); $se=$p.StandardError.ReadToEnd(); $p.WaitForExit(); $rc=$p.ExitCode
    return @{command=$cmd; exit_code=$rc; stdout=$so; stderr=$se}
}

# ---- Test-ClockLock: verify GPU clock lock with multiple samples ----
function Test-ClockLock {
    param([int]$ReqMHz, [int]$TolMHz, [int]$Samples, [string]$LogDir)
    $result=@{
        requested_mhz=$ReqMHz; tolerance_mhz=$TolMHz; succeeded=$false; failure_reason=""
        persistence_mode_status=""; pm_cmd=$null; lgc_cmd=$null
        samples=@(); verify_cmds=@()
    }
    # OS-aware persistence: Windows = NA, Linux = required
    if($IsWindows){
        $result.persistence_mode_status="NOT_APPLICABLE_WINDOWS"
        Write-Host "  [ClockLock] Windows: persistence mode skipped"
    }else{
        $pm=Run-NvidiaSmi @("-pm","1"); $result.pm_cmd=$pm
        if($pm.exit_code -ne 0){ $result.failure_reason=Classify-LockFailure "pm" $pm; return $result }
        $result.persistence_mode_status="OK"
    }
    # Step: lock graphics clock
    $lgc=Run-NvidiaSmi @("-lgc","$ReqMHz"); $result.lgc_cmd=$lgc
    if($lgc.exit_code -ne 0){ $result.failure_reason=Classify-LockFailure "lgc" $lgc; return $result }
    # Warmup
    $warmupCode="import torch; torch.cuda.is_available() and torch.cuda.synchronize(); print('warmup_ok')"
    try{ $null=& $Py -c $warmupCode 2>$null }catch{}
    Start-Sleep -Seconds 1
    # Sample actual clock
    for($i=0;$i -lt $Samples;$i++){
        $q=Run-NvidiaSmi @("--query-gpu=clocks.current.graphics","--format=csv,noheader,nounits"); $result.verify_cmds+=$q
        if($q.exit_code -ne 0 -or -not $q.stdout){ $result.failure_reason="CLOCK_VERIFICATION_QUERY_FAILED"; return $result }
        $v=0; [int]::TryParse(($q.stdout.Trim() -replace '[^0-9]',''),[ref]$v)|Out-Null
        if($v -eq 0){ $result.failure_reason="CLOCK_VERIFICATION_QUERY_FAILED: cannot parse clock value"; return $result }
        $result.samples+=$v; Start-Sleep -Milliseconds 500
    }
    if($result.samples.Count -lt $Samples){ $result.failure_reason="CLOCK_VERIFICATION_INSUFFICIENT_SAMPLES: got $($result.samples.Count), need $Samples"; return $result }
    # Check tolerance
    foreach($s in $result.samples){
        if($s -lt ($ReqMHz - $TolMHz) -or $s -gt ($ReqMHz + $TolMHz)){
            $result.failure_reason="CLOCK_OUTSIDE_TOLERANCE: sample=$s MHz, range=[$($ReqMHz-$TolMHz), $($ReqMHz+$TolMHz)]"
            return $result
        }
    }
    $result.succeeded=$true
    $result|ConvertTo-Json -Depth 5|Out-File (Join-Path $LogDir "clock_lock_verification.json") -Encoding utf8
    return $result
}

function Classify-LockFailure {
    param([string]$Step, $CmdResult)
    $out=($CmdResult.stdout+$CmdResult.stderr).ToLower()
    if($out -match 'permission|denied|administrator|root|access'){ return "CLOCK_LOCK_PERMISSION_DENIED" }
    if($out -match 'not supported|unsupported|not available'){ return "CLOCK_LOCK_UNSUPPORTED" }
    if($out -match 'invalid.*clock|clock.*invalid|unsupported.*clock|clock.*out of range|clock.*not valid'){ return "REQUESTED_CLOCK_UNSUPPORTED" }
    return "CLOCK_LOCK_COMMAND_FAILED: nvidia-smi -i $GpuId -$Step exit=$($CmdResult.exit_code)"
}

function Reset-ClockLock {
    $r=Run-NvidiaSmi @("-rgc")
    if($IsWindows){ return @{reset_exit=$r.exit_code; reset_cmd=$r; pm_reset_skipped=$true} }
    $pm2=Run-NvidiaSmi @("-pm","0")
    return @{reset_exit=$r.exit_code; reset_cmd=$r; pm_reset_cmd=$pm2; pm_reset_skipped=$false}
}

$report=@{runs=@();diagnosis=@();diagnosis_status="PENDING";failed_passes=@()}

# --- ReportOnly mode: skip runs, analyze existing data ---
if($ReportOnly){
    Write-Host "[diag] ReportOnly mode — analyzing existing data in $diagDir"
    # Populate runs from existing directory structure
    $dirs=Get-ChildItem $diagDir -Directory|Where-Object{$_.Name -match '^run(A|B|C)_(pass0|pass1)$'}
    $seenRuns=@{}
    foreach($d in $dirs){
        $n=$d.Name; $rid=$n.Substring(0,4); $pk=$n.Substring(5)
        if(-not $seenRuns[$rid]){ $seenRuns[$rid]=@{}; $report.runs+=@{id=$rid; pass0=@{}; pass1=@{}; order=""} }
        $seenRuns[$rid][$pk]=$d.FullName
        # Check stderr for exit code
        $stderrFile=Join-Path $d.FullName "${pk}_stderr.txt"
        $rc=0; if(Test-Path $stderrFile){ $content=Get-Content $stderrFile -Raw; if($content -notmatch 'exit'){$rc=0} }
        ($report.runs|Where-Object{$_.id -eq $rid}).$pk=@{exit_code=0; dir=$d.FullName}
    }
    if($report.runs.Count -gt 0){
        $report.runs|Where-Object{$_.id -eq "runA"}|ForEach-Object{$_.order="pass0_first"}
        $report.runs|Where-Object{$_.id -eq "runB"}|ForEach-Object{$_.order="pass1_first"}
        $report.runs|Where-Object{$_.id -eq "runC"}|ForEach-Object{$_.order="pass0_first_locked"}
    }
} else {
# --- NOT ReportOnly: dispatch ClockPreflight vs full A/B/C ---
if($ClockPreflightOnly){
    Write-Host "===== CLOCK PREFLIGHT ====="
    Write-Host "  Requested: $RequestedGraphicsClockMHz MHz  Tolerance: $ClockToleranceMHz MHz  Samples: $ClockVerificationSamples"
    $preflightDir=Join-Path $OutputRoot "clock_preflight_$((Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssZ'))"
    New-Item -ItemType Directory -Force -Path $preflightDir|Out-Null
    $supClocks=& nvidia-smi -i $GpuId -q -d SUPPORTED_CLOCKS 2>&1; $supClocks|Out-File (Join-Path $preflightDir "supported_clocks.txt")
    $lockResult=Test-ClockLock -ReqMHz $RequestedGraphicsClockMHz -TolMHz $ClockToleranceMHz -Samples $ClockVerificationSamples -LogDir $preflightDir
    Write-Host "  Lock succeeded: $($lockResult.succeeded)  Failure: $($lockResult.failure_reason)  Samples: $($lockResult.samples -join ', ')"
    $resetResult=Reset-ClockLock; Write-Host "  Reset exit: $($resetResult.reset_exit)"
    $lockResult|Add-Member -NotePropertyName reset_exit -NotePropertyValue $resetResult.reset_exit -Force
    $lockResult|Add-Member -NotePropertyName reset_cmd -NotePropertyValue $resetResult.reset_cmd -Force
    $lockResult|ConvertTo-Json -Depth 5|Out-File (Join-Path $preflightDir "clock_preflight_result.json") -Encoding utf8
    Write-Host "===== PREFLIGHT COMPLETE ====="
    if($lockResult.succeeded){ Write-Host "  CLOCK LOCK SUPPORTED AND VERIFIED"; exit 0 }
    else{ Write-Host "  CLOCK LOCK FAILED OR UNSUPPORTED"; exit 1 }
}

# Run A: Pass 0 -> Pass 1
Write-Host "===== Run A: Pass0->Pass1 ====="
$ra0d=Join-Path $diagDir "runA_pass0";$ra1d=Join-Path $diagDir "runA_pass1"
New-Item -ItemType Directory -Force -Path $ra0d,$ra1d|Out-Null
$report.runs+=@{id="runA";order="pass0_first";pass0={};pass1={}}
(Get-GpuState)|Out-File (Join-Path $ra0d "gpu_state_before.txt")
$rc=Invoke-Pass -PassLabel "pass0" -OutDir $ra0d -OutBase "pass0"
(Get-GpuState)|Out-File (Join-Path $ra0d "gpu_state_after.txt")
$report.runs[-1].pass0=@{exit_code=$rc}
(Get-GpuState)|Out-File (Join-Path $ra1d "gpu_state_before.txt")
$rc=Invoke-Pass -PassLabel "pass1" -OutDir $ra1d -OutBase "pass1"
(Get-GpuState)|Out-File (Join-Path $ra1d "gpu_state_after.txt")
$report.runs[-1].pass1=@{exit_code=$rc}

# Run B: Pass 1 -> Pass 0
Write-Host "===== Run B: Pass1->Pass0 ====="
$rb1d=Join-Path $diagDir "runB_pass1";$rb0d=Join-Path $diagDir "runB_pass0"
New-Item -ItemType Directory -Force -Path $rb1d,$rb0d|Out-Null
$report.runs+=@{id="runB";order="pass1_first";pass0={};pass1={}}
(Get-GpuState)|Out-File (Join-Path $rb1d "gpu_state_before.txt")
$rc=Invoke-Pass -PassLabel "pass1" -OutDir $rb1d -OutBase "pass1"
(Get-GpuState)|Out-File (Join-Path $rb1d "gpu_state_after.txt")
$report.runs[-1].pass1=@{exit_code=$rc}
(Get-GpuState)|Out-File (Join-Path $rb0d "gpu_state_before.txt")
$rc=Invoke-Pass -PassLabel "pass0" -OutDir $rb0d -OutBase "pass0"
(Get-GpuState)|Out-File (Join-Path $rb0d "gpu_state_after.txt")
$report.runs[-1].pass0=@{exit_code=$rc}

# Run C: clock-locked (only if requested)
$clockLockRequested=$false; $clockLockSucceeded=$false
$clockLockResult=$null; $clockResetExit=0
if($EnableClockLock){
    $clockLockRequested=$true
    Write-Host "===== Run C: Clock-locked ====="
    # Use proper verification with multiple samples
    $clockLockResult=Test-ClockLock -ReqMHz $RequestedGraphicsClockMHz -TolMHz $ClockToleranceMHz -Samples $ClockVerificationSamples -LogDir $diagDir
    $clockLockSucceeded=$clockLockResult.succeeded
    Write-Host "  Clock lock: requested=$RequestedGraphicsClockMHz MHz, samples=$($clockLockResult.samples -join ','), success=$clockLockSucceeded"
    if(-not $clockLockSucceeded){
        Write-Host "  FAILED: $($clockLockResult.failure_reason)"
    }
    # Always run Run C passes (locked or not — but mark accordingly)
    $rc0d=Join-Path $diagDir "runC_pass0";$rc1d=Join-Path $diagDir "runC_pass1"
    New-Item -ItemType Directory -Force -Path $rc0d,$rc1d|Out-Null
    $runCOrder = if($clockLockSucceeded){"pass0_first_locked"}else{"pass0_first_lock_attempted"}
    $report.runs+=@{id="runC";order=$runCOrder;pass0={};pass1={};clock_lock_requested=$true;clock_lock_succeeded=$clockLockSucceeded}
    (Get-GpuState)|Out-File (Join-Path $rc0d "gpu_state_before.txt")
    $rc=Invoke-Pass -PassLabel "pass0" -OutDir $rc0d -OutBase "pass0"
    (Get-GpuState)|Out-File (Join-Path $rc0d "gpu_state_after.txt")
    $report.runs[-1].pass0=@{exit_code=$rc}
    (Get-GpuState)|Out-File (Join-Path $rc1d "gpu_state_before.txt")
    $rc=Invoke-Pass -PassLabel "pass1" -OutDir $rc1d -OutBase "pass1"
    (Get-GpuState)|Out-File (Join-Path $rc1d "gpu_state_after.txt")
    $report.runs[-1].pass1=@{exit_code=$rc}
    # Reset in finally-style (best effort)
    $resetResult=Reset-ClockLock; $clockResetExit=$resetResult.reset_exit
    Write-Host "  Clock reset exit: $clockResetExit"
    # Save clock metadata
    $report.clock_lock_requested=$true
    $report.clock_lock_succeeded=$clockLockSucceeded
    $report.clock_reset_succeeded=($clockResetExit -eq 0)
    $report.requested_graphics_clock_mhz=$RequestedGraphicsClockMHz
    $report.lock_command="nvidia-smi -pm 1; nvidia-smi -lgc $RequestedGraphicsClockMHz"
    $report.lock_command_exit_code=$clockLockResult.pm_exit
    $report.lock_command_stdout=$clockLockResult.cmd_stdout
    $report.clock_verification_status=if($clockLockSucceeded){"VERIFIED"}else{"FAILED_OR_UNVERIFIED"}
    $report.observed_graphics_clock_samples_mhz=$clockLockResult.samples
    $report.clock_tolerance_mhz=$ClockToleranceMHz
    $report.clock_lock_failure_reason=$clockLockResult.failure_reason
    $report.reset_command_exit_code=$clockResetExit
} else {
    # Run C without clock lock
    Write-Host "===== Run C: No clock lock ====="
    $rc0d=Join-Path $diagDir "runC_pass0";$rc1d=Join-Path $diagDir "runC_pass1"
    New-Item -ItemType Directory -Force -Path $rc0d,$rc1d|Out-Null
    $report.runs+=@{id="runC";order="pass0_first";pass0={};pass1={};clock_lock_requested=$false;clock_lock_succeeded=$false}
    (Get-GpuState)|Out-File (Join-Path $rc0d "gpu_state_before.txt")
    $rc=Invoke-Pass -PassLabel "pass0" -OutDir $rc0d -OutBase "pass0"
    (Get-GpuState)|Out-File (Join-Path $rc0d "gpu_state_after.txt")
    $report.runs[-1].pass0=@{exit_code=$rc}
    (Get-GpuState)|Out-File (Join-Path $rc1d "gpu_state_before.txt")
    $rc=Invoke-Pass -PassLabel "pass1" -OutDir $rc1d -OutBase "pass1"
    (Get-GpuState)|Out-File (Join-Path $rc1d "gpu_state_after.txt")
    $report.runs[-1].pass1=@{exit_code=$rc}
}

}  # end of if(-not $ReportOnly) / else block

# ===================================================================
# Post-run analysis: read actual results and parity files
# ===================================================================
function Read-Latency {
    param([string]$ResultsFile)
    if(-not (Test-Path $ResultsFile -PathType Leaf)){ return $null }
    try {
        $vals=@(Get-Content $ResultsFile | Where-Object{$_.Trim()} | ForEach-Object{
            $r=$_|ConvertFrom-Json
            if($r.attempt_status -eq "success"){
                $v=0.0; if([double]::TryParse("$($r.inference_e2e_latency_ms)",[ref]$v)){ $v }
            }
        })
        if($vals.Count -eq 0){ return $null }
        return ,$vals  # unary comma: return as single array, not unrolled
    }catch{ return $null }
}
function Read-Parity {
    param([string]$Dir)
    $pf=Join-Path $Dir "cross_pass_parity.json"
    if(-not (Test-Path $pf)){ return $null }
    try{ return Get-Content $pf -Raw | ConvertFrom-Json }catch{ return $null }
}
function Mean {
    param([object]$V)
    if($null -eq $V){ return $null }
    # Flatten: handle nested arrays, convert to scalars
    $numbers=@($V|ForEach-Object{
        if($_ -is [array]){ $_|ForEach-Object{ $v=0.0; if([double]::TryParse("$_",[ref]$v)){$v} } }
        else{ $v=0.0; if([double]::TryParse("$_",[ref]$v)){$v} }
    })
    if($numbers.Count -eq 0){ return $null }
    return [double](($numbers|Measure-Object -Average).Average)
}

# Map run directory patterns: runA_pass0, runA_pass1, runB_pass1, runB_pass0, runC_pass0, runC_pass1
$runDirs=@{}
$dirs=Get-ChildItem $diagDir -Directory|Where-Object{$_.Name -match '^run(A|B|C)_(pass0|pass1)$'}
foreach($d in $dirs){
    $n=$d.Name; $runId=$n.Substring(0,4); $pk=$n.Substring(5)
    if(-not $runDirs[$runId]){$runDirs[$runId]=@{}}
    $runDirs[$runId][$pk]=$d.FullName
}

$failed=@(); $diagnosis=@()
foreach($runId in @("runA","runB","runC")){
    if(-not $runDirs[$runId]){ continue }
    $rd=$runDirs[$runId]
    $p0d=$rd["pass0"]; $p1d=$rd["pass1"]
    if(-not $p0d -or -not $p1d){ $diagnosis+="$runId missing pass dirs"; continue }

    $p0lat=Read-Latency (Join-Path $p0d "inference_results.jsonl")
    $p1lat=Read-Latency (Join-Path $p1d "inference_results.jsonl")
    $p0par=Read-Parity $p0d; $p1par=Read-Parity $p1d

    $p0mean=Mean $p0lat; $p1mean=Mean $p1lat
    $ratio=if($p0mean -and $p1mean -and $p0mean -gt 0){[math]::Round($p1mean/$p0mean,4)}else{$null}

    $parityStatus="OK"; $parityReasons=@()
    if(-not $p0par){$parityReasons+="pass0 parity missing"}; if(-not $p1par){$parityReasons+="pass1 parity missing"}
    if($p0par -and $p1par){
        if($p0par.gpu_uuid -ne $p1par.gpu_uuid){$parityReasons+="GPU UUID mismatch"}
        if($p0par.runner_source_sha256 -ne $p1par.runner_source_sha256){$parityReasons+="runner SHA mismatch"}
        if($p0par.prompt_tokens_sha256 -ne $p1par.prompt_tokens_sha256){$parityReasons+="prompt SHA mismatch"}
    }
    if($parityReasons.Count -gt 0){$parityStatus="MISMATCH: "+($parityReasons -join '; ')}

    $report.runs|Where-Object{$_.id -eq $runId}|ForEach-Object{
        $_.pass0_mean_e2e_ms=$p0mean
        $_.pass1_mean_e2e_ms=$p1mean
        $_.pass1_over_pass0_ratio=$ratio
        $_.parity_status=$parityStatus
        $_.parity_reasons=$parityReasons
        $_.pass0_latency_count=if($p0lat){$p0lat.Count}else{0}
        $_.pass1_latency_count=if($p1lat){$p1lat.Count}else{0}
    }

    if($null -eq $p0lat -or $null -eq $p1lat){ $diagnosis+="$runId RESULT_PARSE_FAILURE" }
    if([int]($report.runs|Where-Object{$_.id -eq $runId}).pass0.exit_code -ne 0){$failed+="$runId/pass0"}
    if([int]($report.runs|Where-Object{$_.id -eq $runId}).pass1.exit_code -ne 0){$failed+="$runId/pass1"}
}

# Cross-run diagnosis
$ra=$report.runs|Where-Object{$_.id -eq "runA"}; $rb=$report.runs|Where-Object{$_.id -eq "runB"}; $rc=$report.runs|Where-Object{$_.id -eq "runC"}
$ra_ratio=$ra.pass1_over_pass0_ratio; $rb_ratio=$rb.pass1_over_pass0_ratio; $rc_ratio=$rc.pass1_over_pass0_ratio
$report.ratios=@{runA=$ra_ratio; runB=$rb_ratio; runC=$rc_ratio}

# Execution status
$report.execution_status = if($failed.Count -gt 0){"EXECUTION_FAILURE"}else{"COMPLETE"}
$report.failed_passes=$failed

# Parity status
$parityIssues=@(); foreach($r in $report.runs){if($r.parity_status -ne "OK"){$parityIssues+=$r.parity_status}}
$report.execution_parity_status = if($parityIssues.Count -gt 0){"MISMATCH: $($parityIssues -join '; ')"}else{"OK"}

# Clock intervention status
if($clockLockRequested){
    $report.clock_intervention_status = if($clockLockSucceeded){"VERIFIED"}else{"FAILED_OR_UNVERIFIED"}
}else{
    $report.clock_intervention_status = "NOT_REQUESTED"
}

# Root cause diagnosis
$diagnosis=@()
# Order effect: Run A (P0 first, P1 second) vs Run B (P1 first, P0 second)
$p1SlowerInA = ($ra_ratio -and $ra_ratio -gt 1.0)  # P1 slower when run second in A
$p0SlowerInB = ($rb_ratio -and $rb_ratio -gt 1.0)  # P0 slower when run second in B
$orderFlipped = ($p1SlowerInA -and $p0SlowerInB)   # Second pass always slower = warm state

if($ra_ratio -and $rb_ratio){
    if($ra_ratio -gt 1.0 -and $rb_ratio -gt 1.0){
        $diagnosis+="PASS1_PROFILING_OVERHEAD_OBSERVED"
        $diagnosis+="PROCESS_ORDER_EFFECT_NOT_SUPPORTED"
    }
    if($ra_ratio -lt 0.9 -and $rb_ratio -lt 0.9){ $diagnosis+="PASS1_SPECIFIC_PROFILING_EFFECT" }
    if($ra_ratio -lt 0.9 -and $rb_ratio -gt 1.1){ $diagnosis+="PROCESS_ORDER_WARM_STATE" }
}
if($ra_ratio -gt 1.0){ $diagnosis+="OLD_NEGATIVE_OVERHEAD_NOT_REPRODUCED" }

# Clock causality
if($clockLockSucceeded){
    if($rc_ratio -and $rc_ratio -ge 0.9 -and $rc_ratio -le 1.1){
        $diagnosis+="GPU_CLOCK_POWER_CAUSE_CONFIRMED"
    }elseif($rc_ratio){
        $diagnosis+="GPU_CLOCK_NOT_SUFFICIENT"
    }
}else{
    if($clockLockRequested){ $diagnosis+="CLOCK_LOCK_FAILED_OR_UNVERIFIED" }
    $diagnosis+="CLOCK_CAUSALITY_NOT_EVALUATED"
}

$report.root_cause_status = if($diagnosis -contains "GPU_CLOCK_POWER_CAUSE_CONFIRMED"){"CONFIRMED"}else{"UNRESOLVED"}

if($diagnosis.Count -eq 0){ $diagnosis+="INCONCLUSIVE -- no ratio data available" }
$report.diagnosis=$diagnosis

# Overall status
$report.diagnosis_status = if($failed.Count -gt 0){"EXECUTION_FAILURE"}elseif($diagnosis -contains "CLOCK_CAUSALITY_NOT_EVALUATED"){"PARTIAL"}else{"COMPLETE"}
$report.diagnosis_limitations = @()
if(-not $clockLockSucceeded -and $clockLockRequested){ $report.diagnosis_limitations += @("CLOCK_LOCK_FAILED_OR_UNVERIFIED","CLOCK_CAUSALITY_NOT_EVALUATED") }

# Save report
$report|ConvertTo-Json -Depth 5|Out-File (Join-Path $diagDir "cross_pass_clock_diag_report.json") -Encoding utf8
$clockSect=""
if($clockLockRequested){
    $clockSect=@"

## Clock Lock
- **Requested**: $LockedGraphicsClockMHz MHz
- **Succeeded**: $clockLockSucceeded
- **Observed**: $obsClock MHz
- **Tolerance**: +/- $tolerance MHz
- **Lock cmd exit**: $clockLockCmdExit
- **Reset cmd exit**: $clockResetExit
- **Failure reason**: $($report.clock_lock_failure_reason)
"@
}
$md=@"
# Cross-Pass Clock Diagnostic Report
- **Diag Dir**: $diagDir
- **Manifest**: $ManifestPath (SHA256=$manifestSha)
- **GPU**: $($sel.name) (UUID=$($sel.uuid))
- **Execution**: $($report.execution_status)
- **Parity**: $($report.execution_parity_status)
- **Clock Intervention**: $($report.clock_intervention_status)
- **Root Cause**: $($report.root_cause_status)
- **Overall**: $($report.diagnosis_status)
## Ratios
- **Run A (P0->P1)**: $ra_ratio
- **Run B (P1->P0)**: $rb_ratio
- **Run C**: $rc_ratio (locked=$clockLockSucceeded)
## Parity Status
$($report.runs|ForEach-Object{"- $($_.id): $($_.parity_status)"}|Out-String)
$clockSect
## Diagnosis
$($report.diagnosis -join ', ')
## Limitations
$($report.diagnosis_limitations -join ', ')
## Failed Passes
$($report.failed_passes -join ', ')
"@
$md|Out-File (Join-Path $diagDir "cross_pass_clock_diag_report.md") -Encoding utf8
Write-Host "";Write-Host "===== DIAG COMPLETE =====";Write-Host "  $diagDir"
Write-Host "  Execution: $($report.execution_status)"
Write-Host "  Parity:    $($report.execution_parity_status)"
Write-Host "  Clock:     $($report.clock_intervention_status)"
Write-Host "  RootCause: $($report.root_cause_status)"
if($failed.Count -gt 0){ Write-Host "  Failed: $($failed -join ', ')"; exit 1 }
exit 0
