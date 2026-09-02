# ExposedPath v3 Pilot Runner Contract

## 1. Measurement Boundaries

- `full_request` NVTX range defines the measurement window
- Tokenizer/detokenizer are **OUTSIDE** the measurement boundary
- Final device synchronization (`torch.cuda.synchronize()`) MUST be inside `full_request`
- No per-token synchronization between decode steps
- No streaming callbacks inside the timing path

## 2. Fixed Input

- Input tokens come from a pre-generated `prompt_tokens.json`, NOT from runtime tokenization
- Every sample's `input_ids` length == `fixed_input_tokens`
- Batch uses the first `batch_size` distinct samples -- NO cloning/expanding a single sample
- **FORMAL** mode: cloned batch samples -> hard failure
- **PILOT** mode: cloned batch samples -> also fails by default (strict)

## 3. Batch Semantics

- `batch_size` = number of parallel samples in one invocation
- Different sample indices = genuinely different `input_ids`
- No repeated `expand`/`clone` to fake batch

## 4. Output Token Semantics

- `fixed_output_tokens` = exact number of output tokens the model must generate
- Prefill produces the first output token (TTFT)
- Decode produces tokens 2..`fixed_output_tokens`
- `output_len=1`: decode phase is empty but must be handled consistently (documented)
- Early EOS -> exclusion (not success)
- Wrong output token count -> exclusion

## 5. Pass 0 and Pass 1

- **Pass 0**: benchmark-only, no profiler, no NVTX. `python -m exposedpath run-pass0`
- **Pass 1**: nsys-wrapped, NVTX on. Wrapped by `run_pass1_nsys.ps1`
- Both passes read the same `wmpc_manifest.json` and `prompt_tokens.json`
- Both use the same `warmup_count` and `repeat_count`
- Identical `repeat_index` plan for both passes

## 6. NVTX Contract

- **Invocation**: `EXPOSEDPATH_INVOCATION:<experiment_id>:<wmpc_id>:<run_id>:<pass>:<repeat_index>`
- **Phases**: `EXPOSEDPATH_PHASE:full_request`, `EXPOSEDPATH_PHASE:prefill`, `EXPOSEDPATH_PHASE:decode`
- `full_request` contains `prefill` then `decode`
- Warmup has NO formal NVTX ranges
- `prepare_input` / tokenization NOT inside `full_request`

## 7. Attempt / Exclusion

- `repeat_count` = PLANNED attempts, not successful count
- Failed attempts -> `exclusion_log.jsonl` with `repeat_index` and reason
- Successful attempts -> `inference_results.jsonl`
- No silent auto-retry to fill success quota
- Reasons: OOM, early EOS, wrong output count, CUDA error, runtime exception

## 8. Directory Identity

```
<output_root>/<experiment_id>/<wmpc_id>/<run_id>/
  wmpc_manifest.json
  prompt_tokens.json (or reference + SHA-256)
  commands/
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
  logs/
  analysis/
    <analysis_run_id>/
```

## 9. Currently Supported

- PyTorch eager mode
- Single GPU inference
- Fixed `prompt_tokens.json` input
- fp16
- WMPC manifest identity system
- Pass 0 (no profiler) and Pass 1 (nsys)
- A-layer wall-clock decomposition (from legacy analyzer)
- B-layer per-sync diagnostics (from legacy analyzer)
- Windows Server + PowerShell

## 10. NOT Yet Supported (Pilot Scope)

- `torch.compile` / CUDA Graph
- vLLM or other serving frameworks
- Multi-model matrix experiments
- Continuous batching / concurrency
- Streaming token delivery
- MoE / quantization variants
- Formal `experiment_analysis.sqlite`
- Bootstrap/repeat-level statistical tests
- Resource audit periodic sampling
- Full event synchronization recovery

## 11. Pilot Run Example

```powershell
# 1. Prepare prompt tokens (offline)
python -m exposedpath prepare-prompt-tokens `
    --model-path "C:\Users\...\models\Qwen2.5-1.5B-Instruct" `
    --fixed-input-tokens 128 --num-samples 16 `
    --output ".\prompt_tokens.json"

# 2. Create manifest (use Python API)
python -c "
from exposedpath.manifest import create_manifest, finalize_manifest, save_manifest
from exposedpath.workload import load_prompt_tokens
m = create_manifest(experiment_id='pilot_test', run_role='PILOT',
    model_path='...', prompt_tokens_file='.\prompt_tokens.json',
    batch_size=1, fixed_output_tokens=16)
pt = load_prompt_tokens('prompt_tokens.json')
m = finalize_manifest(m, pt)
save_manifest(m, 'wmpc_manifest.json')
"

# 3. Validate
python -m exposedpath validate-manifest --manifest wmpc_manifest.json

# 4. Run Pass 0
.\scripts\run_pass0.ps1 -Manifest wmpc_manifest.json

# 5. Run Pass 1 (nsys)
.\scripts\run_pass1_nsys.ps1 -Manifest wmpc_manifest.json -NsysPath "C:\...\Nsight Systems...\target-windows-x64"

# Or both at once:
.\scripts\run_wmpc_pilot.ps1 -Manifest wmpc_manifest.json -NsysPath "..."
```

## 12. Legacy Commands

Old scripts (`run_nsys_single.ps1`, `run_nsys_matrix.ps1`, `run_all_nsys_matrix.ps1`, `bench_eager.py --streaming`) are **LEGACY** and no longer the primary entry point. They are kept for backward compatibility with existing results but will NOT be updated for new features.
