# ExposedPath v3 — LLM Inference Exposed-Latency Accounting

> PyTorch eager + NVTX + NVIDIA Nsight Systems → Raw → S → {A, B} exposed-latency accounting  
> Status: **Pilot engineering and measurement-validity qualification**  
> Updated: **2026-07-22**

## 1. Project Goal

ExposedPath studies local LLM inference latency under CUDA asynchronous execution. It reconstructs synchronization semantics and separates two analysis layers:

- **Raw**: CUDA Runtime/Driver APIs, kernels, MemOps, synchronization records, NVTX ranges, and timestamps.
- **S layer**: synchronization-scope and wait-set recovery.
- **A layer**: mutually exclusive, wall-clock-conserving phase/request accounting.
- **B layer**: per-synchronization terminal provenance and exposed/hidden execution analysis.

The project is currently a **Pilot**. Current data are suitable for runner validation, trace/parser validation, A/B accounting validation, telemetry validation, and repeat-count planning. They are **not yet eligible for final-paper statistics**.

---

## 2. Current Status

| Area | Status | Notes |
|---|---|---|
| Research protocol and metric specification | Complete for Pilot review | Formal Protocol Freeze is still pending |
| Fixed-token workload preparation | Implemented | Tokenization is outside the timed inference window |
| Four-level identity model | Implemented for Pilot | `experiment_id / wmpc_id / run_id / analysis_run_id` |
| Pass 0 runner | Implemented | Unprofiled performance collection |
| Pass 1 runner | Implemented | Nsight Systems structural collection |
| NVTX invocation/phase ranges | Implemented | `full_request / prefill / decode` |
| Physical/logical GPU identity separation | Implemented | Physical GPU 3 maps to process-local `cuda:0` |
| GPU busy preflight | Implemented | Pilot stops if the selected GPU already has compute processes |
| Clock policy | Implemented | `DEFAULT_DYNAMIC` is the current shared-server policy |
| GPU telemetry | Implemented | Identity, clocks, P-state, temperature, power, utilization |
| Host-state telemetry | Implemented | Per-repeat host-state snapshots for variability diagnosis |
| Platform topology snapshot | Implemented | GPU topology and runtime/threading context |
| Cross-pass parity checks | Implemented | GPU, prompt, manifest, timing, and repeat-plan identity |
| Nsight REP and SQLite export | Implemented | Verified in the P1 full-pipeline revalidation |
| Raw/S/A/B analyzer | Implemented for current Pilot scope | A conservation and B duration coverage verified on P1 |
| Scientific audit generator | Implemented | `analysis/generate_p1_audit.py` |
| Automated tests | **220 passed** | `compileall` also passes |
| P1 full-pipeline qualification | Pipeline hard gates passed | Repeat-count review remains |
| P1 Pass-0 repeat-count study | Completed with 20 repeats | CV = **5.27%**, still near the 5% review boundary |
| P2–P4 refreshed Small Pilot | Not started | Must wait for repeat policy review |
| Formal G1–G4 matrix | Not started | Must wait for Protocol Freeze |

---

## 3. Current Safety and Clock Policy

The current shared-server policy is:

```text
clock_policy = DEFAULT_DYNAMIC
clock_control_requested = false
clock_control_applied = false
clock_control_status = NOT_REQUESTED
environment_sharing_mode = SHARED
data_role = PILOT
eligible_for_final_statistics = false
```

Under `DEFAULT_DYNAMIC`, ExposedPath must not execute GPU state-changing commands:

- no `nvidia-smi -lgc`;
- no `nvidia-smi -rgc`;
- no persistence-mode change;
- no power-limit change;
- no memory-clock change;
- no GPU reset;
- no administrator elevation.

All GPU commands in this mode are read-only queries. A historical clock-lock permission failure is environment evidence only and must not block a dynamic-clock Pilot.

---

## 4. GPU Identity Contract

A selected physical GPU and the CUDA device visible inside the child process are distinct identifiers.

Current P1 example:

```text
gpu_index_physical = 3
gpu_index_logical = 0
gpu_uuid = GPU-0d8fafe6-a1e9-33cc-25fb-632316736455
gpu_pci_bus_id = 00000000:E1:00.0
gpu_name = NVIDIA GeForce RTX 4090
```

When `CUDA_VISIBLE_DEVICES=3` is used:

- `nvidia-smi` queries the physical selector `3`, UUID, or PCI Bus ID;
- PyTorch loads the model on process-local `cuda:0`;
- UUID and PCI Bus ID must match across the two views;
- any mismatch is a hard failure.

---

## 5. Main Project Components

```text
exposedpath/
  manifest.py             WMPC/run identity, clock policy, GPU identity
  runner.py               Pass 0/1 execution, GPU telemetry, host-state telemetry
  workload.py             Fixed prompt-token loading and validation
  validation.py           Manifest and run validation
  nvtx.py                 Invocation and phase NVTX labels
  results.py              Results and exclusion records

scripts/
  run_small_pilot.ps1     Current Small Pilot orchestrator
  run_pass0.ps1           Pass 0 execution
  run_pass1_nsys.ps1      Pass 1 under Nsight Systems
  run_wmpc_pilot.ps1      Combined WMPC workflow
  batch_accounting.ps1    Analyzer orchestration
  export_nsys_sqlite.ps1  REP to SQLite export

analysis/
  exposed_accounting.py   Raw/S/A/B accounting
  accounting_utils.py     Interval and trace utilities
  generate_p1_audit.py    P1 qualification and repeat-review audit
  summarize_matrix.py     Multi-point summary support

tests/
  test_small_pilot.py     Clock policy, identity, telemetry, audit, safety
  test_exposedpath_v3.py  Runner/manifest/workload validation
  test_exposed_accounting.py
  test_summarize_matrix.py
```

Legacy matrix scripts may remain in the repository, but they are not the current Pilot entry point.

---

## 6. Current Pilot Entry Points

### 6.1 Single P1 full-pipeline revalidation

```powershell
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputRoot = "C:\Users\Wsn1\YLQ_test\pilot_dynamic_revalidation_$stamp"

.\scripts\run_small_pilot.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -GpuId 3 `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe" `
    -OutputRoot $outputRoot `
    -WarmupCount 5 `
    -RepeatCount 5 `
    -ClockPolicy DEFAULT_DYNAMIC `
    -PilotPoints @("P1")
```

This mode runs Pass 0, Pass 1, Nsight export, analyzer, and audit for P1 only.

### 6.2 P1 Pass-0 repeat-count/host-state diagnosis

Always use a new output root.

```powershell
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$outputRoot = "C:\Users\Wsn1\YLQ_test\pilot_p1_pass0_hostdiag_$stamp"

.\scripts\run_small_pilot.ps1 `
    -ModelPath "C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct" `
    -GpuId 3 `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2026.2.1\target-windows-x64\nsys.exe" `
    -OutputRoot $outputRoot `
    -WarmupCount 5 `
    -RepeatCount 20 `
    -ClockPolicy DEFAULT_DYNAMIC `
    -PilotPoints @("P1") `
    -Pass0Only
```

### 6.3 Generate or refresh the P1 audit without recollection

```powershell
& ".\.venv\Scripts\python.exe" `
  ".\analysis\generate_p1_audit.py" `
  "C:\path\to\existing\pilot_output_root"
```

---

## 7. Output Contract

A current Pilot output root can contain:

```text
<output_root>/
  gpu_inventory.json
  platform_topology_snapshot.*
  P1_DYNAMIC_REVALIDATION_REPORT.md
  P1_REVALIDATION_AUDIT.md

  P1/
    prompt_tokens.json
    wmpc_manifest.json

    pass0/
      inference_results.jsonl
      exclusion_log.jsonl
      telemetry/
        pass0_gpu_telemetry.jsonl
        pass0_host_state.jsonl
        host_runtime_snapshot.json

    pass1/
      inference_results.jsonl
      exclusion_log.jsonl
      pass1_profile.nsys-rep
      pass1_profile.sqlite
      telemetry/
        pass1_gpu_telemetry.jsonl

    analysis/
      <analysis_run_id>/
        accounting_result.json
        accounting_summary.csv
        b_sync_detail.csv
```

Exact snapshot filenames may vary with the script revision, but missing data must never be silently converted to numeric zero.

---

## 8. Telemetry Contract

### 8.1 GPU telemetry

For each Pass, telemetry is sampled at:

- before warmup;
- after warmup;
- before every formal repeat;
- after every formal repeat;
- after the Pass.

For 20 repeats, the expected count is:

```text
1 + 1 + 20 + 20 + 1 = 43 samples per Pass
```

Each record includes run/pass/repeat identity, requested and observed GPU identity, query status, clocks, P-state, temperature, power, and utilization when supported.

### 8.2 Host-state telemetry

Host-state sampling is diagnostic and read-only. It is intended to identify variability related to:

- process/thread scheduling;
- CPU load;
- memory pressure;
- competing processes;
- runtime thread settings;
- affinity/NUMA configuration;
- host-state transitions around anomalous repeats.

Telemetry queries are outside the inference timing interval. Their overhead must not be added to `inference_e2e_latency_ms`.

---

## 9. Current P1 Evidence

### 9.1 Full-pipeline P1 revalidation

The five-repeat dynamic-clock P1 revalidation verified:

- 5/5 successful Pass 0 repeats;
- 5/5 successful Pass 1 repeats;
- exact input/output token counts;
- zero E2E timestamp recomputation error;
- Nsight REP and SQLite present;
- A-layer conservation error = 0%;
- supported sync-duration coverage = 99.9%;
- B-valid sync-duration coverage = 99.9%;
- five zero-pending-activity synchronizations classified as valid empty wait sets;
- Pass 1/Pass 0 median ratio = 1.4012;
- no negative-profiler-overhead anomaly.

Its final status was:

```text
P1_PIPELINE_PASS_REPEAT_REVIEW_REQUIRED
```

The only review item was Pass 0 CV = 12.1% with only five repeats.

### 9.2 Latest P1 Pass-0 host-diagnostic run

Current manifest:

```text
P1: input_tokens=32, output_tokens=8, batch_size=1
warmup_count=5
repeat_count=20
clock_policy=DEFAULT_DYNAMIC
GPU physical=3, logical=0
```

Observed latency summary:

| Metric | Value |
|---|---:|
| Successful repeats | 20 |
| Mean E2E latency | 411.258 ms |
| Median E2E latency | 416.327 ms |
| Sample standard deviation | 21.676 ms |
| CV | **5.271%** |
| Minimum | 353.288 ms |
| Maximum | 441.870 ms |
| CV excluding repeat 0 | 4.177% |
| Robust CV estimate (MAD-based) | about 3.79% |

The two lowest repeats were:

```text
repeat 0  = 353.288 ms
repeat 16 = 363.336 ms
```

Most other repeats were between approximately 394 ms and 442 ms.

GPU telemetry during formal repeats showed:

```text
graphics clock: 2820–2835 MHz
temperature:    32–34 °C
identity match: true
```

The pre-warmup sample was lower-clocked, while the post-warmup and formal-repeat samples were already in the high-performance range.

---

## 10. Why the CV Fell from 12.1% to 5.27%

The code did **not** lock clocks, alter the model, change P1 tokens, remove repeats, or edit latency values.

The major reasons are statistical and experimental:

1. **Five samples were too few.**  
   In the earlier run, one unusually fast repeat (`307.5 ms`) had very high leverage over the sample standard deviation.

2. **The new run used 20 independent formal repeats.**  
   The larger sample provides a more stable estimate of the latency distribution. More repeats do not mathematically guarantee a lower CV, but they reduce the chance that one observation dominates the estimate.

3. **Most new observations formed a tighter central cluster.**  
   The current median is about `416.3 ms`, and most repeats are near that value.

4. **Warmup and GPU state were auditable.**  
   Formal-repeat GPU clocks were nearly flat at `2820–2835 MHz`; the large prior CV is therefore not explained by obvious repeat-level GPU downclocking in the latest run.

5. **New diagnostics add observability, not a performance optimization.**  
   The recent changes added physical/logical GPU identity checks, host-state sampling, topology snapshots, and audit logic. These queries occur outside the timed inference window. They may change inter-repeat spacing slightly, so the run is not evidence that the underlying system became intrinsically faster or more stable.

The current CV is still slightly above the 5% engineering review boundary. Therefore, it should not be described as a resolved stability result.

---

## 11. Completed Engineering Work

- Safe `DEFAULT_DYNAMIC` clock policy.
- No administrator or GPU-state modification requirement.
- GPU busy check before Pilot execution.
- Physical GPU index and process-local CUDA index separation.
- UUID/PCI identity verification.
- New output-root creation before file writes.
- Single-point execution through `-PilotPoints @("P1")`.
- Pass-0-only diagnostic mode.
- Dynamic GPU telemetry.
- Host-state telemetry.
- Platform topology snapshot.
- Cross-pass parity checks.
- Nanosecond-to-millisecond timing validation.
- Exact token-count and exclusion validation.
- Failure and qualification report generation.
- Duration-based B-layer coverage audit.
- Empty-wait-set semantic review.
- Per-repeat latency breakdown and anomaly detection.
- 220 passing automated tests and successful `compileall`.

---

## 12. Work Not Yet Frozen

The following are not yet final:

- formal repeat count;
- handling policy for repeat-level performance anomalies;
- CPU affinity and NUMA policy;
- framework thread-count policy;
- formal randomization/blocking strategy;
- final dynamic-clock telemetry acceptance limits;
- P2–P4 refreshed Small Pilot results;
- `sync_semantics_registry v1.0`;
- formal G1–G4 WMPC matrix;
- final database ingestion and publication workflow;
- paper-level statistical inference and bootstrap configuration.

No current Pilot output should be mixed with future formal data.

---

## 13. Immediate Next Steps

1. Audit the two low-latency repeats in the 20-repeat host-diagnostic run against `pass0_host_state.jsonl`.
2. Determine whether they reflect host scheduling/state changes, a measurement-boundary issue, or ordinary system variability.
3. Freeze an engineering repeat policy only after the anomaly review:
   - keep all valid repeats unless a predeclared exclusion rule is violated;
   - do not remove repeats merely because they are fast or slow;
   - report both conventional and robust summaries during Pilot review.
4. Once P1 repeat policy is accepted, run refreshed P2–P4 Small Pilot points with the same identity, telemetry, and dynamic-clock contracts.
5. Complete Protocol Freeze.
6. Only then begin formal G1–G4 collection.

---

## 14. Qualification Rules

Primary hard gates currently include:

- complete GPU and workload identity;
- exact E2E time recomputation;
- required Pass artifacts;
- Analyzer completion;
- A-layer conservation;
- supported sync-duration coverage ≥ 95%;
- B-valid sync-duration coverage ≥ 90%;
- exact input/output token counts;
- no unexplained severe negative profiler overhead.

Count coverage is reported as secondary information. A valid zero-pending-activity synchronization is a supported empty wait set and does not require terminal-specific B fields.

Pass 0 CV is an engineering repeat-review signal, not by itself a scientific validity failure.

---

## 15. Data Governance

- Never overwrite a prior `run_id`.
- Recollection creates a new `run_id`.
- Reanalysis creates a new `analysis_run_id`.
- Preserve prior failed and diagnostic directories as evidence.
- Do not merge old P1–P4 results with refreshed Pilot results.
- Do not use Pilot data in final-paper statistics.
- Keep raw REP/SQLite evidence until the canonical database and archive workflow are frozen.

---

## 16. Current Bottom Line

ExposedPath has passed the P1 full-pipeline measurement-validity gates under the shared-server `DEFAULT_DYNAMIC` policy. The remaining immediate issue is **repeat-level Pass 0 variability**, not analyzer correctness, GPU identity, trace completeness, or A/B duration coverage.

The latest 20-repeat P1 run reduced the estimated CV from 12.1% to 5.27%, mainly because the earlier five-sample estimate was dominated by one unusually fast observation. The new result is encouraging but remains close to the engineering review boundary and requires host-state anomaly review before repeat-count freeze.
