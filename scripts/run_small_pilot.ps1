<#
.SYNOPSIS
    Small-scale Pilot (4 WMPC points) for ExposedPath v3.
.DESCRIPTION
    P1: input=32,output=8  P2: input=512,output=8  P3: input=32,output=128  P4: input=512,output=128
    GPU bound by PCI bus ID UUID via CUDA_VISIBLE_DEVICES. Compatible with Windows PowerShell 5.1.
#>
param(
    [Parameter(Mandatory=$true)][string]$ModelPath,
    [Parameter(Mandatory=$true)][int]$GpuId,
    [Parameter(Mandatory=$true)][string]$NsysPath,
    [string]$OutputRoot = ".\pilot_results",
    [int]$WarmupCount = 5,
    [int]$RepeatCount = 5,
    [switch]$Pass0Only,
    [switch]$Resume,
    [ValidateSet("DEFAULT_DYNAMIC","FIXED")][string]$ClockPolicy = "DEFAULT_DYNAMIC",
    [string[]]$PilotPoints = @("P1","P2","P3","P4")
)
$ErrorActionPreference = "Continue"
$ScriptDir = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
$ProjectRoot = Split-Path -Parent $ScriptDir
$ProjectRoot = (Resolve-Path $ProjectRoot).Path

# ---- Resolve executables ----
function Resolve-Exe { param([string]$N)
    if (Test-Path -Path $N -PathType Leaf -ErrorAction SilentlyContinue) { return (Resolve-Path -Path $N -ErrorAction SilentlyContinue).Path }
    if (Test-Path -Path $N -PathType Container -ErrorAction SilentlyContinue) { $c = Join-Path -Path $N -ChildPath "nsys.exe"; if (Test-Path -Path $c -PathType Leaf -ErrorAction SilentlyContinue) { return (Resolve-Path -Path $c -ErrorAction SilentlyContinue).Path } }
    try { return (Get-Command $N -ErrorAction Stop).Source } catch {}
    $v = Join-Path -Path $ProjectRoot -ChildPath ".venv\Scripts\python.exe"
    if ($N -eq "python" -and (Test-Path -Path $v -PathType Leaf -ErrorAction SilentlyContinue)) { return $v }
    return $null
}
$Py = Resolve-Exe "python"; if (-not $Py) { Write-Host "ERROR: python not found"; exit 1 }
$Nsys = Resolve-Exe $NsysPath; if (-not $Nsys) { Write-Host "ERROR: nsys not found: $NsysPath"; exit 1 }
if (((Split-Path -Parent $Nsys) -replace '\\$','') -notmatch 'Nsight Systems') { Write-Host "ERROR: NsysPath parent not 'Nsight Systems'"; exit 1 }

# ---- Create OutputRoot before any file writes ----
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null

# ===================================================================
# DETERMINISTIC GPU BINDING
# ===================================================================
$env:CUDA_DEVICE_ORDER = "PCI_BUS_ID"
$smi_csv = & nvidia-smi --query-gpu=index,name,uuid,pci.bus_id,memory.total --format=csv,noheader 2>$null
if ($LASTEXITCODE -ne 0 -or -not $smi_csv) { Write-Host "ERROR: nvidia-smi query failed"; exit 1 }
$gpu_list = @(); foreach ($line in $smi_csv) { $parts = $line -split ',\s*'; if ($parts.Count -ge 5) { $gpu_list += @{index=[int]$parts[0]; name=$parts[1]; uuid=$parts[2]; pci=$parts[3]; mem=$parts[4]} } }
$gpu_list | ConvertTo-Json -Compress | Out-File (Join-Path -Path $OutputRoot -ChildPath "gpu_inventory.json") -Encoding utf8
$selected = $gpu_list | Where-Object { $_.index -eq $GpuId }
if (-not $selected) { Write-Host "ERROR: GPU index $GpuId not found. Available: $($gpu_list.index -join ', ')"; exit 1 }

# Physical/logical GPU identity
$PHYSICAL_GPU_INDEX = $GpuId
$GPU_UUID = $selected.uuid; $GPU_PCI = $selected.pci; $GPU_NAME = $selected.name
$env:CUDA_VISIBLE_DEVICES = $GPU_UUID  # exposes only this GPU to PyTorch
$LOGICAL_CUDA_DEVICE = 0  # PyTorch sees it as cuda:0

# Verify PyTorch sees the correct GPU at cuda:0
$vcode = @"
import torch,os,sys
print(os.environ.get('CUDA_DEVICE_ORDER',''))
print(os.environ.get('CUDA_VISIBLE_DEVICES',''))
name=torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'NONE'
print(name)
if '$GPU_NAME' != name: sys.exit(1)
"@
$vout = & $Py -c $vcode 2>&1; if ($LASTEXITCODE -ne 0) { Write-Host "ERROR: GPU name mismatch. nvidia-smi says '$GPU_NAME', torch says different."; exit 1 }

# ---- GPU busy check (read-only, no state change) ----
$procCheck = & nvidia-smi -i $GpuId --query-compute-apps=pid,process_name,used_memory --format=csv,noheader 2>$null
if ($procCheck -and $procCheck.Trim()) {
    Write-Host "BLOCKED_BY_GPU_BUSY: GPU $GpuId has running compute processes:"
    Write-Host $procCheck
    $reportFile = Join-Path $OutputRoot "BLOCKED_BY_GPU_BUSY.txt"
    "GPU $GpuId busy at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n$procCheck" | Out-File $reportFile -Encoding utf8
    exit 2
}
Write-Host "[GPU check] No compute processes on GPU $GpuId -- safe to proceed"

Write-Host "============================================"
Write-Host "  ExposedPath v3 Small Pilot"
Write-Host "============================================"
Write-Host "  clock_policy:            $ClockPolicy"
Write-Host "  physical_gpu_index:      $PHYSICAL_GPU_INDEX"
Write-Host "  logical_cuda_device:     $LOGICAL_CUDA_DEVICE"
Write-Host "  gpu_uuid:                $GPU_UUID"
Write-Host "  gpu_pci_bus_id:          $GPU_PCI"
Write-Host "  gpu_name:                $GPU_NAME"
Write-Host "  PilotPoints:             $($PilotPoints -join ', ')"
Write-Host "  Warmup: $WarmupCount  Repeat: $RepeatCount"
Write-Host ""

$env:PYTHONPATH = "$ProjectRoot;$($env:PYTHONPATH)"
Set-Location $ProjectRoot

$ALL_POINTS = @(
    @{id="P1"; input=32; output=8; batch=1},
    @{id="P2"; input=512; output=8; batch=1},
    @{id="P3"; input=32; output=128; batch=1},
    @{id="P4"; input=512; output=128; batch=1}
)
$POINTS = @($ALL_POINTS | Where-Object { $_.id -in $PilotPoints })

# ===================================================================
# GPU identity file management
# ===================================================================
function Write-IdentityFile {
    param([string]$Dir)
    $ident = @{ requested_gpu_index=$GpuId; gpu_uuid=$GPU_UUID; gpu_pci_bus_id=$GPU_PCI
                gpu_name=$GPU_NAME; logical_device="cuda:0"; created_utc=(Get-Date).ToUniversalTime().ToString("o") }
    $ident | ConvertTo-Json | Out-File (Join-Path -Path $Dir -ChildPath "pilot_identity.json") -Encoding utf8
}

function Test-ResumeIdentity {
    param([string]$Dir)
    $idFile = Join-Path -Path $Dir -ChildPath "pilot_identity.json"
    $manifestFile = Join-Path -Path $Dir -ChildPath "wmpc_manifest.json"
    if (Test-Path -Path $idFile -PathType Leaf) {
        try { $ident = Get-Content $idFile -Raw | ConvertFrom-Json } catch { return $false, "identity parse error, $idFile" }
        if ($ident.gpu_uuid -ne $GPU_UUID) { return $false, "GPU UUID mismatch: identity=$($ident.gpu_uuid) current=$GPU_UUID" }
        if ($ident.gpu_pci_bus_id -ne $GPU_PCI) { return $false, "GPU PCI mismatch: identity=$($ident.gpu_pci_bus_id) current=$GPU_PCI" }
        return $true, "identity match"
    }
    # No identity file -- try backfill from old manifest
    if (-not (Test-Path -Path $manifestFile -PathType Leaf)) { return $false, "no identity file, no manifest" }
    try { $m = Get-Content $manifestFile -Raw | ConvertFrom-Json } catch { return $false, "manifest parse error" }
    if ($m.gpu_index -and [int]$m.gpu_index -ne $GpuId) { return $false, "manifest gpu_index=$($m.gpu_index) != requested $GpuId" }
    # Check Pass 0 results exist and complete
    $p0r = Join-Path -Path $Dir -ChildPath "pass0\inference_results.jsonl"
    if (-not (Test-Path -Path $p0r -PathType Leaf)) { return $false, "no Pass 0 results to validate" }
    try {
        $recs = @(Get-Content $p0r | ForEach-Object { $_ | ConvertFrom-Json })
        if ($recs.Count -ne $RepeatCount) { return $false, "Pass 0 count $($recs.Count) != $RepeatCount" }
        foreach ($r in $recs) { if ($r.attempt_status -ne "success") { return $false, "Pass 0 has non-success attempt" } }
    } catch { return $false, "Pass 0 results parse error" }
    # All checks passed: backfill identity
    Write-IdentityFile -Dir $Dir
    Write-Host "  RESUME_IDENTITY_BACKFILLED: identity file written for $Dir"
    return $true, "backfilled"
}

# ===================================================================
# Invoke-Proc: Windows PowerShell 5.1 compatible process launcher
# ===================================================================
function Invoke-Proc {
    param([string]$Exe, [string[]]$ProcArgs, [string]$OutBase, [string]$WD, [int]$TimeoutSec = 600)
    $so = Join-Path -Path $WD -ChildPath "${OutBase}_stdout.txt"
    $se = Join-Path -Path $WD -ChildPath "${OutBase}_stderr.txt"
    $cmdFile = Join-Path -Path $WD -ChildPath "${OutBase}_command.txt"
    $argStr = $ProcArgs -join ' '
    if (-not $argStr.Trim()) { Write-Host "    LAUNCH ERROR: empty arguments"; return [pscustomobject]@{ ExitCode=-4; TimedOut=$false; Stdout=""; Stderr="empty args" } }
    "$Exe $argStr" | Out-File -FilePath $cmdFile -Encoding utf8
    Write-Host "    $Exe $argStr"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName=$Exe; $psi.UseShellExecute=$false; $psi.RedirectStandardOutput=$true; $psi.RedirectStandardError=$true
    $psi.CreateNoWindow=$true; $psi.WorkingDirectory=$ProjectRoot; $psi.Arguments=$argStr

    try { $proc = [System.Diagnostics.Process]::Start($psi) } catch { Write-Host "    LAUNCH ERROR: $($_.Exception.Message)"; return [pscustomobject]@{ ExitCode=-2; TimedOut=$false; Stdout=""; Stderr="Process.Start: $($_.Exception.Message)" } }
    if (-not $proc) { Write-Host "    LAUNCH ERROR: Process.Start returned null"; return [pscustomobject]@{ ExitCode=-3; TimedOut=$false; Stdout=""; Stderr="Process.Start null" } }
    $ChildPid = $proc.Id; Write-Host "    PID=$ChildPid"

    # Start async reads IMMEDIATELY (before WaitForExit) -- PS 5.1 compatible
    try { $outTask = $proc.StandardOutput.ReadToEndAsync() } catch { Write-Host "    ERROR: stdout ReadToEndAsync failed: $($_.Exception.Message)"; return [pscustomobject]@{ ExitCode=-6; TimedOut=$false; Stdout=""; Stderr="stdout ReadToEndAsync: $($_.Exception.Message)" } }
    try { $errTask = $proc.StandardError.ReadToEndAsync() } catch { Write-Host "    ERROR: stderr ReadToEndAsync failed: $($_.Exception.Message)"; return [pscustomobject]@{ ExitCode=-7; TimedOut=$false; Stdout=""; Stderr="stderr ReadToEndAsync: $($_.Exception.Message)" } }

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $completed = $proc.WaitForExit($TimeoutSec * 1000)

    if (-not $completed) {
        Write-Host "    TIMEOUT (${TimeoutSec}s), killing PID=$ChildPid..."
        try { & taskkill.exe /PID $ChildPid /T /F 2>$null } catch {}
        try { $null = $proc.Kill() } catch {}
        $null = $proc.WaitForExit(5000)
        try { $null = $outTask.Wait(5000) } catch {}; try { $null = $errTask.Wait(5000) } catch {}
        try { [string]$stdout = $outTask.Result } catch { [string]$stdout = "" }
        try { [string]$stderr = $errTask.Result } catch { [string]$stderr = "" }
        if ($stdout) { $stdout | Out-File -FilePath $so -Encoding utf8 } else { "" | Out-File -FilePath $so -Encoding utf8 }
        "TIMEOUT after ${TimeoutSec}s`n$stderr" | Out-File -FilePath $se -Encoding utf8
        return [pscustomobject]@{ ExitCode=-5; TimedOut=$true; Stdout=$stdout; Stderr="TIMEOUT ${TimeoutSec}s`n$stderr" }
    }

    # Wait for async reads to complete
    try { $null = $outTask.Wait(30000) } catch {}
    try { $null = $errTask.Wait(30000) } catch {}
    try { [string]$stdout = $outTask.Result } catch { [string]$stdout = "" }
    try { [string]$stderr = $errTask.Result } catch { [string]$stderr = "" }

    try { if ($stdout) { $stdout | Out-File -FilePath $so -Encoding utf8 } else { "" | Out-File -FilePath $so -Encoding utf8 } } catch { Write-Host "    WARN: stdout write failed" }
    try { if ($stderr) { $stderr | Out-File -FilePath $se -Encoding utf8 } else { "" | Out-File -FilePath $se -Encoding utf8 } } catch { Write-Host "    WARN: stderr write failed" }

    [int]$rc = $proc.ExitCode
    $tail = ($stderr -split "`n") | Select-Object -Last 10
    if ($rc -ne 0) { Write-Host "    FAIL (exit=$rc)  stderr: $se  stdout: $so"; if ($tail) { foreach ($l in $tail) { Write-Host "      $l" } } }
    else { $note = if ($stderr.Trim()) { " (stderr non-empty, ignored)" } else { "" }; Write-Host "    OK (exit=0)$note" }
    return [pscustomobject]@{ ExitCode=$rc; TimedOut=$false; Stdout=$stdout; Stderr=$stderr }
}

# ---- Revalidation report helper (called unconditionally at end) ----
function Write-RevalidationReport {
    param([bool]$Success, [string]$FailureStage, [string]$FailureReason)
    $reportPath = Join-Path $OutputRoot "P1_DYNAMIC_REVALIDATION_REPORT.md"
    # Gather evidence from output directory
    $p0file = Join-Path $OutputRoot "P1\pass0\inference_results.jsonl"
    $p1file = Join-Path $OutputRoot "P1\pass1\inference_results.jsonl"
    $repfile = Join-Path $OutputRoot "P1\pass1\pass1_profile.nsys-rep"
    $sqlfile = Join-Path $OutputRoot "P1\pass1\pass1_profile.sqlite"
    $telP0 = Join-Path $OutputRoot "P1\pass0\telemetry\pass0_gpu_telemetry.jsonl"
    $telP1 = Join-Path $OutputRoot "P1\pass1\telemetry\pass1_gpu_telemetry.jsonl"
    $aDirs = @(Get-ChildItem (Join-Path $OutputRoot "P1\analysis") -Directory -ErrorAction SilentlyContinue | Sort-Object Name -Descending)
    $aFile = if($aDirs){ Join-Path $aDirs[0].FullName "accounting_result.json" }else{""}

    $p0count=0; $p0mean=""; $p0median=""; $p0cv=""; $p1count=0; $p1mean=""; $p1median=""
    $ratio=""; $excl=0; $aCons=""; $covCnt=""; $covDur=""; $bValidCov=""; $unsup=""; $inv=""
    $telP0cnt=0; $telP1cnt=0; $clkRange=""; $tempRange=""; $pwrRange=""
    $gates=@(); $warns=@()

    if(Test-Path $p0file){ try{ $p0r=@(Get-Content $p0file|ForEach-Object{$_|ConvertFrom-Json}); $p0lat=@($p0r|Where-Object{$_.attempt_status -eq "success"}|ForEach-Object{$_.inference_e2e_latency_ms}); $p0count=$p0lat.Count; if($p0count){ $p0mean=[math]::Round(($p0lat|Measure-Object -Average).Average,3); $sorted=@($p0lat|Sort-Object); $p0median=[math]::Round($sorted[[math]::Floor($p0count/2)],3); $avg=($p0lat|Measure-Object -Average).Average; $std=0; foreach($v in $p0lat){$std+=($v-$avg)*($v-$avg)}; $std=[math]::Sqrt($std/($p0count-1)); $p0cv=if($avg -gt 0){[math]::Round($std/$avg*100,2)}else{""} } }catch{} }
    $exclFile=Join-Path $OutputRoot "P1\pass0\exclusion_log.jsonl"
    if(Test-Path $exclFile){ try{ $excl=@(Get-Content $exclFile).Count }catch{} }
    if(Test-Path $p1file){ try{ $p1r=@(Get-Content $p1file|ForEach-Object{$_|ConvertFrom-Json}); $p1lat=@($p1r|Where-Object{$_.attempt_status -eq "success"}|ForEach-Object{$_.inference_e2e_latency_ms}); $p1count=$p1lat.Count; if($p1count){ $p1mean=[math]::Round(($p1lat|Measure-Object -Average).Average,3); $sorted=@($p1lat|Sort-Object); $p1median=[math]::Round($sorted[[math]::Floor($p1count/2)],3) } }catch{} }
    if($p0median -and $p1median -and $p0median -gt 0){ $ratio=[math]::Round($p1median/$p0median,4) }
    # Analyzer
    if($aFile -and (Test-Path $aFile)){ try{ $ar=Get-Content $aFile -Raw|ConvertFrom-Json; $aCons=if($ar.A_summary){"present"}else{"missing"}; $bs=$ar.B_summary; if($bs.full_request){ $covCnt="$($bs.full_request.B_valid)/$($bs.full_request.total_syncs)"; $tot=$bs.full_request.total_syncs; if($tot -gt 0){ $bValidCov=[math]::Round($bs.full_request.B_valid/$tot*100,1) } } }catch{} }
    # Telemetry
    if(Test-Path $telP0){ try{ $telP0cnt=@(Get-Content $telP0).Count }catch{} }
    if(Test-Path $telP1){ try{ $telP1cnt=@(Get-Content $telP1).Count }catch{} }
    # Gates
    if(-not (Test-Path $repfile) -or (Get-Item $repfile).Length -eq 0){ $gates+="nsys-rep missing/empty" }
    if(-not (Test-Path $sqlfile) -or (Get-Item $sqlfile).Length -eq 0){ $gates+="sqlite missing/empty" }
    if($p0count -lt $RepeatCount){ $gates+="Pass0 count $p0count < $RepeatCount" }
    if($ratio -and $ratio -lt 0.9){ $gates+="SUSPICIOUS_NEGATIVE_PROFILER_OVERHEAD ratio=$ratio" }
    if($aCons -ne "present"){ $gates+="A conservation missing" }
    if($bValidCov -and $bValidCov -lt 90){ $gates+="B-valid coverage $bValidCov% < 90%" }
    $finalStatus = if($gates.Count -gt 0){"P1_REVALIDATION_FAIL"}else{"P1_REVALIDATION_PASS"}

    $rpt = @"
# P1 Dynamic Revalidation Report
- **status**: $finalStatus
- **output_root**: $OutputRoot
- **clock_policy**: $ClockPolicy
- **physical_gpu_index**: $PHYSICAL_GPU_INDEX
- **logical_cuda_device**: $LOGICAL_CUDA_DEVICE
- **gpu_uuid**: $GPU_UUID
- **gpu_pci_bus_id**: $GPU_PCI
- **gpu_name**: $GPU_NAME
## Pass 0
- count: $p0count, mean_ms: $p0mean, median_ms: $p0median, cv_pct: $p0cv
- exclusions: $excl
## Pass 1
- count: $p1count, mean_ms: $p1mean, median_ms: $p1median
- pass1/pass0_ratio: $ratio
## Analyzer
- A_conservation: $aCons
- B_count_coverage: $covCnt
- B_valid_coverage_pct: $bValidCov
## Telemetry
- pass0 samples: $telP0cnt, pass1 samples: $telP1cnt
## Artifacts
- nsys-rep: $(if(Test-Path $repfile){'present'}else{'MISSING'})
- sqlite: $(if(Test-Path $sqlfile){'present'}else{'MISSING'})
- analyzer_result: $(if($aFile -and (Test-Path $aFile)){$aFile}else{'MISSING'})
## Gates
$($gates -join "`n")
## Next Step
$(if($finalStatus -eq 'P1_REVALIDATION_FAIL'){"Fix gates above and re-run with identical command."}else{"P1 revalidation passed. Safe to proceed with P2-P4."})
"@
    $rpt | Out-File $reportPath -Encoding utf8
    Write-Host ""
    Write-Host "============================================"
    Write-Host "  Revalidation Report: $reportPath"
    Write-Host "  Status: $finalStatus"
    Write-Host "============================================"
}

# ---- Platform topology snapshot (before any inference) ----
Write-Host "  Collecting platform topology snapshot..."
$snapDir = Join-Path $OutputRoot "platform_snapshot"
New-Item -ItemType Directory -Force -Path $snapDir | Out-Null
& nvidia-smi topo -m 2>&1 | Out-File (Join-Path $snapDir "nvidia_smi_topo_m.txt") -Encoding utf8
& nvidia-smi -i $GpuId topo -c 2>&1 | Out-File (Join-Path $snapDir "nvidia_smi_topo_c.txt") -Encoding utf8
$pySnap = @"
import os, platform, torch, sys, json, datetime
snap = {
    'timestamp_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'python_version': platform.python_version(),
    'platform': platform.platform(),
    'processor': platform.processor(),
    'cpu_count_logical': os.cpu_count(),
    'torch_num_threads': torch.get_num_threads(),
    'torch_num_interop_threads': getattr(torch, 'get_num_interop_threads', lambda: None)(),
    'OMP_NUM_THREADS': os.environ.get('OMP_NUM_THREADS'),
    'MKL_NUM_THREADS': os.environ.get('MKL_NUM_THREADS'),
    'CUDA_VISIBLE_DEVICES': os.environ.get('CUDA_VISIBLE_DEVICES'),
    'CUDA_DEVICE_ORDER': os.environ.get('CUDA_DEVICE_ORDER'),
}
try:
    import psutil
    proc = psutil.Process()
    snap['pid'] = proc.pid
    snap['cpu_affinity'] = list(proc.cpu_affinity()) if hasattr(proc, 'cpu_affinity') else None
except: pass
print(json.dumps(snap, indent=2, default=str))
"@
$pySnap | & $Py -c $pySnap 2>&1 | Out-File (Join-Path $snapDir "host_runtime_snapshot.json") -Encoding utf8
Write-Host "  Platform snapshot saved to $snapDir"

# ===================================================================
# Main loop
# ===================================================================
$OverallOk = $true
foreach ($pt in $POINTS) {
    Write-Host ""; Write-Host ("="*60); Write-Host "  $($pt.id): input=$($pt.input) output=$($pt.output)"
    Write-Host ("="*60)
    $wDir = Join-Path -Path $OutputRoot -ChildPath $pt.id; New-Item -ItemType Directory -Force -Path $wDir | Out-Null

    # --- Resume identity check ---
    $doResume = $false
    if ($Resume) {
        $ok, $msg = Test-ResumeIdentity -Dir $wDir
        if (-not $ok) { Write-Host "  RESUME_MISMATCH: $msg -- will NOT reuse existing results" }
        else { $doResume = $true; Write-Host "  Resume identity: $msg" }
    }

    # --- Step 1: prompt_tokens ---
    $ptFile = Join-Path -Path $wDir -ChildPath "prompt_tokens.json"
    if ((-not (Test-Path $ptFile)) -or -not $doResume) {
        Write-Host "  [Step 1] prompt_tokens..."
        $r = Invoke-Proc -Exe $Py -ProcArgs @("-m","exposedpath","prepare-prompt-tokens","--model-path",$ModelPath,"--fixed-input-tokens",$pt.input,"--num-samples",4,"--output",$ptFile) -OutBase "01_prep" -WD $wDir
        if ([int]$r.ExitCode -ne 0) { Write-Host "  FAILED"; $OverallOk=$false; continue }
    } else { Write-Host "  [Step 1] prompt_tokens: existing, skip" }

    # --- Step 2: manifest ---
    $mFile = Join-Path -Path $wDir -ChildPath "wmpc_manifest.json"
    if ((-not (Test-Path $mFile)) -or -not $doResume) {
        Write-Host "  [Step 2] manifest..."
        $mpy = @"
import sys; sys.path.insert(0, r'$ProjectRoot')
from exposedpath.manifest import create_manifest, finalize_manifest, save_manifest
from exposedpath.workload import load_prompt_tokens
from pathlib import Path
pt_path = Path(r'$ptFile'); pt = load_prompt_tokens(pt_path)
m = create_manifest(experiment_id='pilot_v1', run_role='PILOT', model_path=r'$ModelPath',
    prompt_tokens_file=str(pt_path.resolve()), batch_size=$($pt.batch), fixed_output_tokens=$($pt.output),
    warmup_count=$WarmupCount, repeat_count=$RepeatCount, gpu=$LOGICAL_CUDA_DEVICE, gpu_uuid='$GPU_UUID',
    gpu_index_physical=$PHYSICAL_GPU_INDEX, gpu_index_logical=$LOGICAL_CUDA_DEVICE,
    gpu_pci_bus_id='$GPU_PCI', gpu_name='$GPU_NAME', external_cuda_workload_policy='none',
    clock_policy='$ClockPolicy', clock_control_requested=$false, clock_control_applied=$false,
    clock_control_status='NOT_REQUESTED', clock_causality_status='NOT_EVALUATED',
    clock_preflight_required=$false, environment_sharing_mode='SHARED', data_role='PILOT',
    eligible_for_final_statistics=$false)
m = finalize_manifest(m, pt, prompt_tokens_path=pt_path)
save_manifest(m, Path(r'$wDir') / 'wmpc_manifest.json')
print('OK:' + m['wmpc_id'])
"@
        $ms = Join-Path -Path $wDir -ChildPath "_create_manifest.py"
        [System.IO.File]::WriteAllText($ms, $mpy, [System.Text.UTF8Encoding]::new($false))
        $r = Invoke-Proc -Exe $Py -ProcArgs @($ms) -OutBase "02_manifest" -WD $wDir
        if ([int]$r.ExitCode -ne 0) { Write-Host "  MANIFEST CREATION FAILED"; Write-RevalidationReport $false "MANIFEST_CREATION" "manifest script exit=$($r.ExitCode)"; $OverallOk=$false; continue }
    } else { Write-Host "  [Step 2] manifest: existing, skip" }

    # Write identity after manifest exists
    Write-IdentityFile -Dir $wDir

    # Validate
    Write-Host "  [Validate]"
    $r = Invoke-Proc -Exe $Py -ProcArgs @("-m","exposedpath","validate-manifest","--manifest",$mFile) -OutBase "03_validate" -WD $wDir
    if ([int]$r.ExitCode -ne 0) { Write-Host "  VALIDATE FAILED"; Write-RevalidationReport $false "MANIFEST_VALIDATION" "exit=$($r.ExitCode)"; $OverallOk=$false; continue }

    # --- Pass 0 ---
    $p0Dir = Join-Path -Path $wDir -ChildPath "pass0"; $p0Results = Join-Path -Path $p0Dir -ChildPath "inference_results.jsonl"
    $runPass0 = $true
    if ($doResume -and (Test-Path $p0Results)) {
        try {
            $existing = @(Get-Content $p0Results | ForEach-Object { $_ | ConvertFrom-Json })
            if ($existing.Count -eq $RepeatCount) {
                $allOk = $true
                foreach ($e in $existing) { if ($e.attempt_status -ne "success" -or $e.actual_output_tokens -ne $pt.output) { $allOk=$false; break } }
                if ($allOk) { $runPass0=$false; Write-Host "  [Step 3] Pass 0: $($existing.Count) existing verified results, skip" }
            }
        } catch {}
    }
    if ($runPass0) {
        Write-Host "  [Step 3] Pass 0..."; New-Item -ItemType Directory -Force -Path $p0Dir | Out-Null
        $r = Invoke-Proc -Exe $Py -ProcArgs @("-m","exposedpath","run-pass0","--manifest",$mFile,"--output-dir",$p0Dir) -OutBase "04_pass0" -WD $p0Dir -TimeoutSec 1200
        if ([int]$r.ExitCode -ne 0) { Write-Host "  PASS 0 FAILED"; $OverallOk=$false; continue }
    }
    if (-not (Test-Path $p0Results)) { Write-Host "  PASS 0: no results"; $OverallOk=$false; continue }
    $p0r = @(Get-Content $p0Results | ForEach-Object { $_ | ConvertFrom-Json })
    if ($p0r.Count -ne $RepeatCount) { Write-Host "  PASS 0: count $($p0r.Count)/$RepeatCount"; $OverallOk=$false; continue }
    Write-Host "  Pass 0 OK: $($p0r.Count)/$RepeatCount"
    if ($Pass0Only) { Write-Host "  Pass0Only: done for $($pt.id)"; continue }

    # --- Pass 1 ---
    $p1Dir = Join-Path -Path $wDir -ChildPath "pass1"; $nsysRep = Join-Path -Path $p1Dir -ChildPath "pass1_profile.nsys-rep"
    $runPass1 = $true
    if ($doResume -and (Test-Path $nsysRep) -and (Get-Item $nsysRep).Length -gt 0) { $runPass1=$false; Write-Host "  [Step 4] Pass 1: existing .nsys-rep, skip" }
    if ($runPass1) {
        Write-Host "  [Step 4] Pass 1 (nsys)..."; New-Item -ItemType Directory -Force -Path $p1Dir | Out-Null
        $prof = Join-Path -Path $p1Dir -ChildPath "pass1_profile"
        $nsysArgs = @("profile","--trace=cuda,nvtx","--cuda-memory-usage=true","--stats=true","-o",$prof,$Py,"-m","exposedpath","run-pass1","--manifest",$mFile,"--output-dir",$p1Dir)
        $r = Invoke-Proc -Exe $Nsys -ProcArgs $nsysArgs -OutBase "05_pass1_nsys" -WD $p1Dir -TimeoutSec 3600
        if ([int]$r.ExitCode -ne 0) { Write-Host "  PASS 1 FAILED"; $OverallOk=$false; continue }
    }
    if (-not (Test-Path $nsysRep) -or (Get-Item $nsysRep).Length -eq 0) { Write-Host "  PASS 1: .nsys-rep missing"; $OverallOk=$false; continue }

    # Export SQLite / Analyzer
    $nsysSql = Join-Path -Path $p1Dir -ChildPath "pass1_profile.sqlite"
    if (-not (Test-Path $nsysSql)) { Invoke-Proc -Exe $Nsys -ProcArgs @("export","--type","sqlite","--output",$nsysSql,$nsysRep) -OutBase "06_export" -WD $p1Dir | Out-Null }
    Write-Host "  [Step 5] Analyzer..."
    $ats = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ"); $asfx = -join ((48..57)+(97..122)|Get-Random -Count 8|ForEach-Object{[char]$_})
    $aDir = Join-Path -Path $wDir -ChildPath "analysis"; New-Item -ItemType Directory -Force -Path $aDir | Out-Null
    $aRun = Join-Path -Path $aDir -ChildPath "analysis-${ats}-${asfx}"; New-Item -ItemType Directory -Force -Path $aRun | Out-Null
    $apy = Join-Path -Path $ProjectRoot -ChildPath "analysis\exposed_accounting.py"
    $r = Invoke-Proc -Exe $Py -ProcArgs @($apy,"--sqlite",$nsysSql,"--output-dir",$aRun) -OutBase "07_analyzer" -WD $aRun -TimeoutSec 600
    if ([int]$r.ExitCode -ne 0) { Write-Host "  ANALYZER WARNING" }
    Write-Host "  $($pt.id) COMPLETE"
}
Write-Host ""; Write-Host ("="*60)
Write-RevalidationReport -Success $OverallOk -FailureStage $(if($OverallOk){""}else{"see_gates"}) -FailureReason $(if($OverallOk){""}else{"gates above"})
# Generate full scientific audit via Python
$auditPy = Join-Path $ProjectRoot "analysis\generate_p1_audit.py"
if (Test-Path $auditPy) {
    Write-Host "  Generating P1_REVALIDATION_AUDIT.md..."
    & $Py $auditPy $OutputRoot 2>&1 | Write-Host
}
if ($OverallOk) { exit 0 } else { exit 1 }
