# Change Summary — ExposedPath v3 Pilot Refactoring

## 1. Modified Files

| File | Reason | Key Changes | Overwrite on Server |
|------|--------|-------------|---------------------|
| `analysis/accounting_utils.py` | v3 NVTX support | Added `NVTX_INVOCATION_PREFIX`, `NVTX_PHASE_PREFIX`, `is_v3_invocation_label()`, `is_v3_phase_label()`, `normalize_phase_name()`, `OUTPUT_SCHEMA_VERSION` | Yes |
| `analysis/exposed_accounting.py` | v3 NVTX support | `build_nvtx_windows` now calls `normalize_phase_name`; added `_parse_v3_invocation_label()` | Yes |
| `bench_eager.py` | Legacy marker | Added `[LEGACY]` docstring header; added local path check before `from_pretrained` | Yes |
| `run_matrix.py` | Legacy marker | Added `[LEGACY]` docstring header | Yes |
| `run_one.py` | Legacy marker | Added `[LEGACY]` docstring header | Yes |
| `scripts/run_nsys_single.ps1` | Legacy marker | Added `[LEGACY]` header in synopsis; added stderr capture on failure | Yes |
| `scripts/run_nsys_matrix.ps1` | Legacy marker | Added `[LEGACY]` header; added pre-flight check before matrix loop | Yes |
| `scripts/run_all_nsys_matrix.ps1` | Legacy marker | Added `[LEGACY]` header | Yes |
| `README.md` | Rewrite for v3 | Complete rewrite for Pilot v3 workflow, directory structure, CLI commands | Yes |
| `tests/test_exposed_accounting.py` | Test fix | Updated `test_api_assignment` to expect normalized `decode` instead of `decode_step_1` | Yes |
| `exposedpath/validation.py` | SHA-256 integrity | Added `validate_sha256_string()`, `validate_prompt_tokens_sha256_match()`, `SHA256_HEX_PATTERN`, `PLACEHOLDER_SHA_VALUES`. Hard-fails on null, empty, placeholder, bad-format, or mismatched SHA-256. | Yes |
| `exposedpath/manifest.py` | SHA-256 integrity | `finalize_manifest` now computes real SHA-256 from file. `save_manifest` uses atomic write (tempfile + rename). Added `update_prompt_sha()`. Removed placeholder SHA from `finalize_manifest`. | Yes |
| `exposedpath/runner.py` | SHA-256 pre-model check | `execute_pass` now calls `validate_prompt_tokens_sha256_match` BEFORE loading model. | Yes |
| `exposedpath/cli.py` | SHA-256 CLI | `cmd_validate_manifest`: hard SHA-256 check. `cmd_run_pass`: SHA-256 check before execute_pass. `cmd_prepare_prompt_tokens`: atomic write + SHA-256 print. New `cmd_update_prompt_sha` + `update-prompt-sha` subcommand. | Yes |
| `tests/test_exposedpath_v3.py` | SHA-256 tests | Added 13 new tests: SHA-256 string validation (6), match/integrity (5), update-prompt-sha (2). Total: 33 tests. | Yes |

## 2. Added Files

| File | Purpose | Server Target | Must Deploy |
|------|---------|---------------|-------------|
| `exposedpath/__init__.py` | Package init, version (`3.0.0-pilot`) | `<project>/exposedpath/__init__.py` | Yes |
| `exposedpath/__main__.py` | `python -m exposedpath` entry point | `<project>/exposedpath/__main__.py` | Yes |
| `exposedpath/cli.py` | CLI: validate-manifest, prepare-prompt-tokens, update-prompt-sha, run-pass0, run-pass1 | `<project>/exposedpath/cli.py` | Yes |
| `exposedpath/ids.py` | WMPC identity: experiment_id, wmpc_id, run_id generation | `<project>/exposedpath/ids.py` | Yes |
| `exposedpath/manifest.py` | WMPC manifest creation, loading, atomic save, update_prompt_sha | `<project>/exposedpath/manifest.py` | Yes |
| `exposedpath/nvtx.py` | NVTX label construction and parsing (v3 format) | `<project>/exposedpath/nvtx.py` | Yes |
| `exposedpath/results.py` | Result recording: inference_results.jsonl, exclusion_log.jsonl | `<project>/exposedpath/results.py` | Yes |
| `exposedpath/runner.py` | Runner: Pass 0 / Pass 1 inference (SHA-256 check before model load) | `<project>/exposedpath/runner.py` | Yes |
| `exposedpath/validation.py` | Validation: prompt_tokens, manifest, SHA-256 integrity, batch distinctness | `<project>/exposedpath/validation.py` | Yes |
| `exposedpath/workload.py` | Fixed input loading and batch extraction from prompt_tokens.json | `<project>/exposedpath/workload.py` | Yes |
| `schemas/prompt_tokens.schema.json` | JSON Schema for prompt_tokens.json | `<project>/schemas/prompt_tokens.schema.json` | Yes |
| `schemas/wmpc_manifest.schema.json` | JSON Schema for wmpc_manifest.json | `<project>/schemas/wmpc_manifest.schema.json` | Yes |
| `scripts/run_pass0.ps1` | Pass 0 (no profiler) PowerShell wrapper | `<project>/scripts/run_pass0.ps1` | Yes |
| `scripts/run_pass1_nsys.ps1` | Pass 1 (nsys-wrapped) PowerShell wrapper | `<project>/scripts/run_pass1_nsys.ps1` | Yes |
| `scripts/run_wmpc_pilot.ps1` | Pass 0 + Pass 1 orchestration | `<project>/scripts/run_wmpc_pilot.ps1` | Yes |
| `scripts/verify_pilot_install.ps1` | Environment verification (Python, CUDA, nsys, tests) | `<project>/scripts/verify_pilot_install.ps1` | Yes |
| `docs/pilot_runner_contract.md` | Pilot measurement contract specification | `<project>/docs/pilot_runner_contract.md` | Yes |
| `tests/test_exposedpath_v3.py` | 33 tests for v3 validation, IDs, NVTX, results, SHA-256 integrity | `<project>/tests/test_exposedpath_v3.py` | Yes |
| `CHANGE_MANIFEST.md` | This file | `<project>/CHANGE_MANIFEST.md` | Yes |
| `SERVER_SYNC_MANIFEST.json` | Machine-readable sync manifest | `<project>/SERVER_SYNC_MANIFEST.json` | Yes |

## 3. Deleted Files

None.

## 4. Renamed or Moved Files

None.

## 5. Server Deployment Order

1. **Backup**: Copy the entire project directory before any changes.
2. **Create directories**: `mkdir exposedpath`, `mkdir schemas` (if not exist).
3. **Upload new files**: Copy all files listed in §2 to their server target paths.
4. **Overwrite modified files**: Copy all files listed in §1 to their server paths.
5. **Renames**: None needed.
6. **Delete deprecated files**: None. Legacy scripts are kept with `[LEGACY]` markers.
7. **Update Python dependencies**: `pip install -r requirements.txt` (no changes to requirements).
8. **Run tests**: `python -m pytest -q`
9. **Smoke test**: `python -m exposedpath --help`
10. **Rollback**: Restore from backup created in step 1.

## 6. Dependency Changes

None. `requirements.txt` is unchanged (torch, transformers>=4.35.0, accelerate>=0.20.0, pyyaml>=6.0).

## 7. Configuration Required on Server

The following MUST be configured by the user — do NOT hardcode paths:

| Item | Where to set | Example |
|------|-------------|---------|
| Model path | CLI `--model-path` or manifest `model_id` | `C:\Users\Wsn1\YLQ_test\models\Qwen2.5-1.5B-Instruct` |
| GPU ID | CLI `--gpu` or manifest creation code | `0` (6000 Ada) or `1` (4090) |
| Nsight Systems path | `-NsysPath` on `run_pass1_nsys.ps1` | `C:\Program Files\NVIDIA Corporation\Nsight Systems 2025.6\target-windows-x64` |
| `output_root` | CLI `--output-root` or manifest creation code | `.` or a dedicated results directory |
| `warmup_count` | Manifest creation | `5` |
| `repeat_count` | Manifest creation | `10` |
| `batch_size` | Manifest creation | `1`, `2`, `4`, or `8` |
| `fixed_output_tokens` | Manifest creation | `16` |
| `fixed_input_tokens` | `prepare-prompt-tokens --fixed-input-tokens` | `128` |

## 8. Commands to Verify

Run on the server after deployment:

```powershell
# 1. Verify environment
.\scripts\verify_pilot_install.ps1

# 2. Package import check
python -c "import exposedpath; print(exposedpath.__version__)"

# 3. CLI help
python -m exposedpath --help

# 4. Run all tests
python -m pytest -q

# 5. Compile check
python -m compileall exposedpath analysis
```

## 9. Test Results

```
pytest:        114 passed in 7.61s
compileall:    exposedpath + analysis — clean, no errors
git diff --check:  clean, no whitespace issues
```

81 existing + 33 new v3 tests = 114 total.
New SHA-256 tests cover: valid SHA, null/empty/placeholder/bad-format failures, match pass, file-content-changed failure, file-not-found failure, placeholder-in-match failure, update-prompt-sha explicit command, update-prompt-sha missing file failure.

## 10. Known Limitations

| Limitation | Reason | Mitigation |
|-----------|--------|------------|
| No GPU testing for new runner | No GPU available in test environment | Run Pilot on server with real GPU |
| `prepare-prompt-tokens` generates synthetic IDs | Real text tokenization needs model access | Use real tokenizer on server |
| Analyzer `_parse_v3_invocation_label` returns empty dict on parse failure | Malformed labels should produce clear errors | Add explicit error for unparseable labels in later version |
| Event sync always `MISSING_EVENT_MAP` on CUDA 12.1 | Hardware limitation | Upgrade to CUDA 12.3+ |
| No automatic experiment matrix runner | Pilot scope: single-manifest workflow | Create manifests individually per WMPC condition |
| `run_role` PILOT/FORMAL distinction not fully enforced in runner | Pilot scope | FORMAL enforcement added in later version |
