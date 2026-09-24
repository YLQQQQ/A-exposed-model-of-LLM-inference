# Server Smoke Test — ExposedPath v3 Pilot

> Gate7 current override (2026-09-24): `gate7-legacy-analyzer/1`, authorized in
> `docs/superpowers/plans/2026-09-20-gate7-execution-plan.md` §6, accepts only new
> Engineering attempts. Historical resume examples below are not valid for this
> revision. Do not use ResumeFrom/ExistingSmokeDir or SkipStaticTests for acceptance.
> Analyzer PASS means legacy-only integration, not scientific qualification.
> Inspect `analyzer.acceptance` and `logs/41_analyzer_acceptance_stdout.txt`:
> window coverage remains unknown/null with its reason; A structure validation is
> not conservation validation. Original diagnostics and artifact hashes remain
> available. Full real-workload v1.4.1 analysis belongs to Gate8, which is not started.
> This documentation does not authorize GPU smoke or real Nsight execution.

## 1. Server Prerequisites

- Windows Server / 10 / 11 + PowerShell 5.1+
- Python 3.10+ with PyTorch CUDA (`torch.cuda.is_available() == True`)
- NVIDIA Nsight Systems installed (`nsys --version`)
- Local model directory with `config.json`
- The full `exposedpath/` project deployed to the server

## 2. File Deployment

Ensure ALL files from the deployment manifest (`CHANGE_MANIFEST.md`, `SERVER_SYNC_MANIFEST.json`) are copied to the server:

- `exposedpath/` (entire package)
- `analysis/` (entire directory)
- `schemas/` (entire directory)
- `scripts/run_server_smoke_test.ps1` (this script)
- `scripts/run_pass0.ps1`
- `scripts/run_pass1_nsys.ps1`
- `scripts/verify_pilot_install.ps1`
- `tests/` (entire directory)

## 3. Invocation Example

```powershell
.\scripts\run_server_smoke_test.ps1 `
    -ModelPath "D:\models\<your-model>" `
    -GpuId 0 `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems <version>\target-windows-x64\nsys.exe" `
    -OutputRoot "D:\exposedpath_smoke"
```

Dry-run first to verify parameters:

```powershell
.\scripts\run_server_smoke_test.ps1 `
    -ModelPath "D:\models\<your-model>" `
    -GpuId 0 `
    -NsysPath "C:\...\nsys.exe" `
    -DryRun
```

## 4. Parameters

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `-ModelPath` | Yes | — | Local model directory (must contain `config.json`) |
| `-GpuId` | Yes | — | GPU device ID (0, 1, …) |
| `-NsysPath` | Yes | — | Path to `nsys.exe` or its parent directory |
| `-OutputRoot` | No | `.\smoke_test` | Root output directory |
| `-ExperimentId` | No | `smoke_v3` | Experiment identifier |
| `-FixedInputTokens` | No | `32` | Input token count per sample |
| `-FixedOutputTokens` | No | `2` | Output tokens per invocation |
| `-WarmupCount` | No | `1` | Warmup iterations |
| `-RepeatCount` | No | `2` | Benchmark repeats |
| `-PythonExe` | No | `python` | Python executable |
| `-DryRun` | No | — | Print plan and exit without running |

## 5. Output Location

```
<OutputRoot>/
  smoke_<UTC_timestamp>/
    wmpc_manifest.json
    prompt_tokens.json
    SMOKE_TEST_REPORT.md          # Human-readable report
    smoke_test_report.json        # Machine-readable report
    pass0/
      inference_results.jsonl
      exclusion_log.jsonl
      pass0_command.txt
    pass1/
      pass1_profile.nsys-rep
      pass1_profile.sqlite
      pass1_nsys_command.txt
    analysis/
      <analysis_run_id>/
        accounting_result.json
        accounting_summary.csv
        b_sync_detail.csv
        analysis_command.txt
    logs/
      01_python_version.txt
      02_exposedpath_help.txt
      03_pytest.txt
      ...
      16_analyzer_out.txt
```

## 6. Gate Decision Meanings

| Gate | Meaning |
|------|---------|
| `READY_FOR_SMALL_PILOT` | All 6 steps passed. Safe to run 5–10 repeat small-scale Pilot. |
| `BLOCKED_BY_ENVIRONMENT` | Missing PyTorch CUDA, nsys, model, or GPU. Fix environment first. |
| `BLOCKED_BY_RUNNER` | Pass 0 failed. Check `pass0/` and `logs/12_pass0_out.txt`. |
| `BLOCKED_BY_NSYS` | Pass 1 failed. Check `logs/13_pass1_nsys_console.log`. |
| `BLOCKED_BY_ANALYZER` | Analyzer failed. Check `logs/16_analyzer_out.txt`. |

The script stops at the FIRST failure — later steps are not run.

## 7. Retrieving Reports

Copy these files back to your local machine for analysis:

```
<smoke_dir>\SMOKE_TEST_REPORT.md
<smoke_dir>\smoke_test_report.json
<smoke_dir>\logs\            (all diagnostic logs)
<smoke_dir>\analysis\<analysis_run_id>\accounting_result.json
```

The JSON report is the primary machine-readable artifact for automated gate checks.
