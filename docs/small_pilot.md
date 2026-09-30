# Small Pilot — ExposedPath v3

> 历史v3入口，不适用于当前v1.4.1路线；不要执行下列旧命令、点集或阈值。
> 当前Gate11仅本地准备，见[既有计划中的7.111 Pilot准备](v1_4_1/gate10_workload_plan_v0_1.md#gate11-local-preparation)。
> 本页保留追溯，不代表Pilot已运行或当前服务器方案。

## Purpose

Estimate variance, profiler overhead, coverage, trace size, and runtime for 4
representative WMPC points.  **Pilot data must NOT enter formal paper statistics.**

## WMPC Points

| ID | input_tokens | output_tokens | batch_size |
|----|-------------|---------------|------------|
| P1 | 32          | 8             | 1          |
| P2 | 512         | 8             | 1          |
| P3 | 32          | 128           | 1          |
| P4 | 512         | 128           | 1          |

All: eager, PILOT role, warmup=5, repeat=5 (configurable), no streaming.

## Commands

### Full Pilot (Pass 0 + Pass 1 + Analyzer)

```powershell
.\scripts\run_small_pilot.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -GpuId 2 `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe" `
    -OutputRoot "C:\Users\Wsn1\YLQ_test\pilot_results" `
    -WarmupCount 5 `
    -RepeatCount 5
```

### Pass 0 Only

```powershell
.\scripts\run_small_pilot.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -GpuId 2 `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe" `
    -OutputRoot "C:\Users\Wsn1\YLQ_test\pilot_results" `
    -WarmupCount 5 `
    -RepeatCount 5 `
    -Pass0Only
```

### Resume (skip completed steps)

```powershell
.\scripts\run_small_pilot.ps1 ... -Resume
```

### Summarize

```powershell
python analysis\summarize_small_pilot.py --pilot-root "C:\Users\Wsn1\YLQ_test\pilot_results"
```

## Output

```
pilot_results/
  P1/
    prompt_tokens.json
    wmpc_manifest.json
    pass0/  (inference_results.jsonl)
    pass1/  (.nsys-rep, .sqlite)
    analysis/<analysis_run_id>/  (accounting_result.json)
  P2/ ... P3/ ... P4/
  pilot_summary.json
  pilot_summary.csv
  PILOT_REPORT.md
```

## Summary Metrics (per WMPC)

- Pass 0 / Pass 1 count, latency mean/median/std/CV/min/max
- Throughput (ratio-of-sums)
- Profiler overhead ratio
- REP / SQLite file sizes
- sync count/duration coverage
- A conservation status

## Repeat Advice Rules (Pilot Engineering — NOT final thresholds)

| Condition | Advice |
|-----------|--------|
| Pass 0 CV <= 3% | PASS0_5_LIKELY_ENOUGH |
| 3% < CV <= 5% | CONSIDER_PASS0_10 |
| CV > 5% | CONSIDER_PASS0_20 |
| duration_coverage < 90% | DATA_QUALITY_BLOCKED |
| exclusion_rate > 5% | DATA_QUALITY_BLOCKED |

## Nsight Systems Path Validation

The script checks that the parent directory of nsys.exe contains "Nsight Systems".
Nsight Compute directories are rejected.
