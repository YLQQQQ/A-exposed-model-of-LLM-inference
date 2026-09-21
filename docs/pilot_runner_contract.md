# ExposedPath v3 Pilot Runner Contract

## 1. Measurement Boundaries

- The frozen semantic endpoint of `full_request` is the final Host-readable Token-ready completion; `inference_end_ns` and the ordered structured Token-ready evidence record that endpoint
- Tokenizer/detokenizer are **OUTSIDE** the measurement boundary
- `request.start` is recorded after the request-start drain returns; that drain is outside `full_request`
- Every generated Token crosses the same blocking Host-readable boundary: the Token ID is copied/read on Host, then its completion timestamp is recorded
- The runner closes the legacy phase ranges immediately after the last structured Token-ready marker and before boundary validation or other cleanup; there is no trailing cleanup synchronization in the measured path
- G1 natural Token-ready completion uses `sync_origin=natural_token_ready`
- `inference_results.jsonl` records each successful attempt's ordered `token_ready_boundaries` (`token_index`, Host token IDs, `completed_ns`, origin, and mechanism)
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
- Prefill ends only after Token 0 is Host-readable; every later Decode step ends at the equivalent Host-readable boundary
- `output_len=1`: decode phase is empty but must be handled consistently (documented)
- Early EOS -> exclusion (not success)
- Wrong output token count -> exclusion

## 5. Pass 0 and Pass 1

- **Pass 0**: benchmark-only, no profiler, no NVTX. `python -m exposedpath run-pass0`
- **Pass 1**: nsys-wrapped, NVTX on. Wrapped by `run_pass1_nsys.ps1`
- Both passes read the same `wmpc_manifest.json` and `prompt_tokens.json`
- Both use the same `warmup_count` and `repeat_count`
- Identical `repeat_index` plan for both passes
- Both use the same study mode, generation control flow, Host-readable Token-ready operation, and synchronization policy; Pass 1 only adds structured NVTX markers and profiling
- Both passes write `cross_pass_parity.json` (schema `exposedpath-v3-cross-pass-2`) carrying the frozen parity identity: workload (`prompt_tokens_sha256`, `experiment_id`/`wmpc_id`, `fixed_input_tokens`, `fixed_output_tokens`, `batch_size`, `sampling_config`, `warmup_count`, `repeat_count`), GPU identity, execution strategy, phase boundary + Token-ready behavior, environment snapshot, and attempt-plan/retry identity
- A required parity field that is absent on either side is reported as `PASS_PARITY_IDENTITY_MISSING` and never treated as equality; a present-but-different field reports its group status (`PASS_WORKLOAD_MISMATCH`, `PASS_GPU_MISMATCH`, `PASS_EXECUTION_PARITY_MISMATCH`)

### 5.1 Cross-pass parity contract (EP-G7-09)

The parity decision is mechanical, not editorial. `exposedpath.cross_pass_validator` compares six frozen groups and fails closed:

| group | representative fields | status when different |
|---|---|---|
| workload | `prompt_tokens_sha256`, `experiment_id`, `wmpc_id`, `fixed_input_tokens`, `fixed_output_tokens`, `batch_size`, `sampling_config`, `warmup_count`, `repeat_count` | `PASS_WORKLOAD_MISMATCH` |
| GPU | `gpu_uuid`, `gpu_pci_bus_id`, `requested_physical_gpu_index` | `PASS_GPU_MISMATCH` |
| execution strategy | `runner_source_sha256`, `dtype`, `attention_backend`, `execution_mode`, `inference_mode`, `use_cache`, `synchronize_policy`, `study_mode`, `n1_intervention`, `cuda_visible_devices` | `PASS_EXECUTION_PARITY_MISMATCH` |
| phase boundary / Token-ready | `phase_boundary_policy_version`, `phase_boundary_policy`, `token_ready_mechanism`, `token_ready_origin` | `PASS_EXECUTION_PARITY_MISMATCH` |
| environment snapshot | `data_role`, `run_role`, `python_version`, `pytorch_version`, `transformers_version`, `cuda_runtime_version`, `nvidia_driver_version`, `cuda_device_order`, `torch_num_threads`, `torch_num_interop_threads`, `omp_num_threads`, `mkl_num_threads`, `cpu_affinity` | `PASS_EXECUTION_PARITY_MISMATCH` |
| attempt plan | `attempt_plan_version`, `retry_policy`, `planned_warmup_count`, `planned_repeat_count` | `PASS_EXECUTION_PARITY_MISMATCH` |

- Missing identity on either side: `PASS_PARITY_IDENTITY_MISSING` (fail closed; never silently equal)
- Attempt accounting (`validate_attempt_accounting`): planned counts, success/exclusion repeat indexes, exclusion reason per repeat index, and retry counts/indexes must match; any difference is `PASS_ATTEMPT_ACCOUNTING_MISMATCH`
- A planned repeat index that is missing, duplicated or outside the plan is `PASS_ATTEMPT_ACCOUNTING_MISMATCH`; records written before EP-G7-09 carry no machine-readable attempt identity and therefore also fail closed

## 6. NVTX Contract

- **Invocation**: `EXPOSEDPATH_INVOCATION:<experiment_id>:<wmpc_id>:<run_id>:<pass>:<repeat_index>`
- **Phases**: `EXPOSEDPATH_PHASE:full_request`, `EXPOSEDPATH_PHASE:prefill`, `EXPOSEDPATH_PHASE:decode`
- **Token-ready sync**: `EXPOSEDPATH_JSON_V1:<json>` with `kind=sync`, `sync_origin=natural_token_ready`, `token_index`, `token_ready_mechanism=device_to_host_token_ids`, `callsite_id`, and complete run/request/repeat identity
- **N1 intervention identity**: `kind=sync`, `sync_origin=n1_intervention`, distinct `callsite_id`, `intervention_variant_id`, and `intervention_ordinal`; EP-G7-08 validates this identity but does not execute N1
- `full_request` contains `prefill` then `decode`
- `completed_ns` is a Host monotonic timestamp and is not asserted numerically equal to an NVTX trace-clock timestamp; Pass 0 / Pass 1 phase-boundary parity is instead enforced through the frozen `phase_boundary_policy` / `token_ready_mechanism` / `token_ready_origin` parity identity (EP-G7-09)
- Warmup has NO formal NVTX ranges
- `prepare_input` / tokenization NOT inside `full_request`

## 7. Attempt / Exclusion

- `repeat_count` = PLANNED attempts, not successful count
- Failed attempts -> `exclusion_log.jsonl` with `repeat_index` and reason
- Successful attempts -> `inference_results.jsonl`
- No silent auto-retry to fill success quota
- Reasons: OOM, early EOS, wrong output count, CUDA error, runtime exception
- Retry policy is frozen and machine-readable: `EXACTLY_ONE_ATTEMPT_PER_PLANNED_REPEAT_INDEX_NO_AUTO_RETRY`; every planned repeat index must be accounted for exactly once across `inference_results.jsonl` + `exclusion_log.jsonl`, otherwise the pass fails closed before the parity file is written
- Every attempt record carries its identity: `repeat_index` (planned slot), `retry_index` (0 = first attempt), `is_retry`, `attempt_uid`, `retry_of_attempt_uid`, `attempt_plan_version`, plus the run-mode identity `data_role` / `run_role` / `study_mode` and `phase_boundary_policy_version`
- Every exclusion carries a frozen `exclusion_reason` code (`OOM`, `EARLY_EOS`, `OUTPUT_TOKEN_COUNT_MISMATCH`, `CUDA_ERROR`, `RUNTIME_ERROR`), the human-readable `invalid_reason`, and the structured `early_eos` / `oom` / `output_len_expected` / `output_len_actual` evidence
- Missing role provenance, an unknown exclusion code, or a retry without `retry_of_attempt_uid` raises instead of being written as `null` / `0`

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
- `study_mode=G1_NATURAL` with natural per-Token Host-readable completion
- Machine-readable, mutually exclusive G1/N1 mode configuration; N1 execution remains disabled and fails closed in Gate 7

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
