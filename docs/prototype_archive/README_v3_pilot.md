# ExposedPath v3 — LLM Inference Exposed-Latency Accounting (Pilot)

> 历史README原文归档；以下“current”/部署/运行指令均非当前入口。请从根README和research_progress进入；Gate7已PASS，Gate8未启动。

> PyTorch eager + NVTX + nsys → A/B layer exposed-latency attribution
> Version: v3.0.0-pilot

## Project Structure

```
project/
  exposedpath/                            # NEW: Pilot Python package
    __init__.py, __main__.py, cli.py      #   CLI entry points
    ids.py                                #   experiment/wmpc/run ID generation
    manifest.py                           #   WMPC manifest creation & validation
    workload.py                           #   prompt_tokens.json loading & validation
    validation.py                         #   Validation helpers
    nvtx.py                               #   NVTX label construction & parsing
    runner.py                             #   Pass 0 / Pass 1 inference execution
    results.py                            #   Result recording & exclusion logging
  schemas/                                # NEW: JSON schemas
    prompt_tokens.schema.json             #   Fixed input contract
    wmpc_manifest.schema.json             #   WMPC manifest schema
  scripts/
    run_pass0.ps1                         # NEW: Pass 0 (no profiler)
    run_pass1_nsys.ps1                    # NEW: Pass 1 (nsys-wrapped)
    run_wmpc_pilot.ps1                    # NEW: Pass 0 + Pass 1 together
    verify_pilot_install.ps1              # NEW: Environment verification
    run_nsys_single.ps1                   # [LEGACY]
    run_nsys_matrix.ps1                   # [LEGACY]
    run_all_nsys_matrix.ps1               # [LEGACY]
    batch_accounting.ps1                  # A/B accounting + matrix summary
    export_nsys_sqlite.ps1                # .nsys-rep → .sqlite export
  analysis/
    exposed_accounting.py                 # A/B layer exposed-latency accounting
    accounting_utils.py                   # Interval algorithms, NVTX parsing
    summarize_matrix.py                   # Matrix result aggregation
    parse_nsys_sqlite.py                  # SQLite → CSV/JSON (diagnostic)
  configs/
    workloads_16group.yaml                # [LEGACY] 16 groups — RTX 6000 Ada
    workloads_16group_4090.yaml           # [LEGACY] 16 groups — RTX 4090
  docs/
    exposedpath_metric_spec_v2.md         # Metric definition (v2, still current)
    pilot_runner_contract.md              # NEW: Pilot measurement contract
  tests/
    test_exposed_accounting.py            # Existing analyzer tests
    test_summarize_matrix.py              # Existing matrix tests
    test_exposedpath_v3.py                # NEW: v3 runner/validation tests
  bench_eager.py                          # [LEGACY] Old benchmark script
  run_one.py                              # [LEGACY] Old single-run wrapper
  run_matrix.py                           # [LEGACY] Old matrix runner
  requirements.txt
  README.md
  README_NVTX_DETAIL_USAGE.md
```

---

## 1. Environment Setup

### 1.1 Prerequisites

- Windows Server / 10 / 11 + PowerShell
- Python 3.10+, CUDA Toolkit, NVIDIA Nsight Systems 2025.6+
- GPU: RTX 6000 Ada (48 GB) or RTX 4090 (24 GB)

### 1.2 Nsight Systems PATH

```powershell
$nsysDir = "<your Nsight Systems path>\target-windows-x64"
$env:Path = "$nsysDir;$env:Path"
nsys --version
```

### 1.3 Virtual Environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install torch --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python -c "import torch; print(torch.cuda.is_available())"
```

### 1.4 Verify Installation

```powershell
.\scripts\verify_pilot_install.ps1
```

---

## 2. Pilot Workflow (v3)

### Step 1: Prepare prompt_tokens.json (offline, no inference)

```powershell
python -m exposedpath prepare-prompt-tokens `
    --model-path "<MODEL_DIR>" `
    --fixed-input-tokens 128 `
    --num-samples 16 `
    --output ".\prompt_tokens.json"
```

### Step 2: Create WMPC Manifest

```powershell
python -c @"
from exposedpath.manifest import create_manifest, finalize_manifest, save_manifest
from exposedpath.workload import load_prompt_tokens

m = create_manifest(
    experiment_id='pilot_6000ada_test',
    run_role='PILOT',
    model_path='C:\\Users\\...\\models\\Qwen2.5-1.5B-Instruct',
    prompt_tokens_file='.\\prompt_tokens.json',
    batch_size=1,
    fixed_output_tokens=16,
    warmup_count=5,
    repeat_count=10,
    gpu=0,
)

pt = load_prompt_tokens('.\\prompt_tokens.json')
m = finalize_manifest(m, pt)
save_manifest(m, 'wmpc_manifest.json')
print(f'Manifest saved. wmpc_id={m[\"wmpc_id\"]}, run_id={m[\"run_id\"]}')
"@
```

### Step 3: Validate

```powershell
python -m exposedpath validate-manifest --manifest ".\wmpc_manifest.json"
```

### Step 4: Run Pass 0 (no profiler)

```powershell
.\scripts\run_pass0.ps1 -Manifest ".\wmpc_manifest.json"
```

### Step 5: Run Pass 1 (nsys profiling)

```powershell
.\scripts\run_pass1_nsys.ps1 `
    -Manifest ".\wmpc_manifest.json" `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2025.6\target-windows-x64"
```

### Step 6: Both Passes at Once

```powershell
.\scripts\run_wmpc_pilot.ps1 `
    -Manifest ".\wmpc_manifest.json" `
    -NsysPath "C:\Program Files\NVIDIA Corporation\Nsight Systems 2025.6\target-windows-x64"
```

---

## 3. Output Directory Structure

```
<output_root>/
  <experiment_id>/
    <wmpc_id>/
      <run_id>/
        wmpc_manifest.json
        pass0/
          inference_results.jsonl
          exclusion_log.jsonl
          pass0_command.txt
        pass1/
          inference_results.jsonl
          exclusion_log.jsonl
          pass1_profile.nsys-rep
          pass1_profile.sqlite
          pass1_nsys_command.txt
          nsys_console.log
        analysis/
          <analysis_run_id>/
            accounting_result.json
            accounting_summary.csv
            b_sync_detail.csv
```

---

## 4. NVTX Label Structure (v3)

```
EXPOSEDPATH_INVOCATION:<experiment_id>:<wmpc_id>:<run_id>:pass1:<repeat_index>
  EXPOSEDPATH_PHASE:full_request
    EXPOSEDPATH_PHASE:prefill
    EXPOSEDPATH_PHASE:decode
```

- Warmup has **no** formal NVTX ranges
- Tokenization / prepare_input is **outside** full_request
- Final device sync is **inside** full_request
- **No** per-token synchronize() between decode steps

---

## 5. Key Design Decisions (v3)

- **Fixed input**: prompt_tokens.json generated offline, NO tokenizer in timing path
- **Batch semantics**: batch uses distinct samples, cloning is rejected
- **No streaming**: no per-token sync, no streaming callbacks
- **Exact output count**: early EOS or wrong token count → exclusion
- **repeat_count = plan**: NOT successful count; no silent auto-retry
- **Pass 0 and Pass 1**: identical repeat_index plan, same manifest + prompt_tokens
- **Directory safety**: existing non-empty run directories cause hard failure
- **wmpc_id**: stable hash of W/M/P/C only (no timestamp, no run metadata)

---

## 6. Legacy Commands

The following are kept for backward compatibility but are NOT the primary Pilot entry point:

```powershell
# [LEGACY] Old single-run nsys profiling
.\scripts\run_nsys_single.ps1 -ModelPath "..." -PromptLen 128 -BatchSize 1 -OutputLen 16 ...

# [LEGACY] Old matrix profiling
.\scripts\run_nsys_matrix.ps1 -ModelPath "..." -WorkloadYaml "configs\workloads_16group.yaml" ...

# [LEGACY] Old all-in-one matrix
.\scripts\run_all_nsys_matrix.ps1 -ModelPath "..." -WorkloadYaml "..." ...
```

---

## 7. Analyzer

The existing A/B layer analyzer (`analysis/exposed_accounting.py`) supports both legacy and v3 NVTX labels. Use with:

```powershell
.\scripts\batch_accounting.ps1 -ResultsDir "<run_dir>"
```

---

## 8. Unsupported in Pilot

- torch.compile / CUDA Graph
- vLLM or serving frameworks
- Continuous batching / concurrency
- Streaming token delivery
- MoE / quantization experiments
- Formal statistical tests / bootstrap
- Full experiment_analysis.sqlite

---

## 9. Common Issues

| Symptom | Cause | Solution |
|---------|-------|----------|
| `Manifest missing required field` | Incomplete manifest | Use `create_manifest()` to generate |
| `Directory exists and is not empty` | Reusing run_id | Generate a new run_id for each collection |
| `sample[0] and sample[1] have identical input_ids` | Cloned samples in batch | Generate distinct samples with different seeds |
| `fixed_input_tokens mismatch` | Wrong prompt_tokens | Regenerate with correct --fixed-input-tokens |
| `nsys not found` | Nsight not in PATH | Provide -NsysPath to scripts |
