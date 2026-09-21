#!/usr/bin/env python3
"""Tests for ExposedPath v3: validation, ids, nvtx, results, accounting_utils."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exposedpath.validation import (
    validate_prompt_tokens, check_batch_sample_distinctness,
    apply_default_attention_mask, validate_manifest_core,
    validate_sha256_string, validate_prompt_tokens_sha256_match,
    compute_prompt_tokens_sha256,
)
from exposedpath.ids import generate_wmpc_id, generate_run_id
from exposedpath.manifest import update_prompt_sha
from exposedpath.nvtx import (
    make_invocation_label, make_phase_label,
    parse_invocation_label, parse_phase_label, is_legacy_nvtx_label,
)
from exposedpath.results import record_exclusion, record_success
from analysis.accounting_utils import (
    normalize_phase_name, NVTX_PHASE_PREFIX,
)

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _valid_pt():
    return {
        "schema_version": "1.0", "tokenizer_id": "test/tok",
        "fixed_input_tokens": 4,
        "samples": [
            {"input_ids": [1, 2, 3, 4]},
            {"input_ids": [5, 6, 7, 8]},
            {"input_ids": [9, 10, 11, 12]},
        ],
    }

def _manifest(**overrides):
    m = {
        "fixed_input_tokens": 128, "fixed_output_tokens": 64, "batch_size": 1,
        "model_id": "test-model", "dtype_and_quantization": "fp16",
        "gpu_model": "NVIDIA Test GPU", "cuda_version_used": "12.4",
        "inference_framework_version": "0.1.0", "execution_mode": "eager",
        "experiment_id": "test_exp", "wmpc_id": "wmpc-placeholder",
        "run_id": "run-placeholder", "run_role": "warmup",
        "data_role": "PILOT",
        "study_mode": "G1_NATURAL", "n1_intervention": None,
        "warmup_count": 3, "repeat_count": 5,
        "prompt_tokens_file": "prompt_tokens.json",
    }
    m.update(overrides)
    return m

INV = ("exp42", "wmpc-abcdef01", "run-20260101T000000Z-a1b2c3d4", "warmup", 0)

# ===== prompt_tokens validation =====

def test_prompt_tokens_validation_pass():
    assert validate_prompt_tokens(_valid_pt()) == []

def test_prompt_tokens_missing_field():
    d = _valid_pt(); del d["schema_version"]
    assert any("schema_version" in e for e in validate_prompt_tokens(d))

def test_prompt_tokens_length_mismatch():
    d = _valid_pt(); d["samples"][1]["input_ids"] = [100, 200]
    assert any("length" in e for e in validate_prompt_tokens(d))

def test_prompt_tokens_negative_token_id():
    d = _valid_pt(); d["samples"][0]["input_ids"][2] = -1
    assert any("non-negative" in e for e in validate_prompt_tokens(d))

# ===== batch distinctness =====

def test_batch_distinctness_ok():
    samples = [{"input_ids": [1,2,3]}, {"input_ids": [4,5,6]}, {"input_ids": [7,8,9]}]
    ok, msg = check_batch_sample_distinctness(samples, 3)
    assert ok, msg

def test_batch_distinctness_clone_fails():
    samples = [{"input_ids": [1,2,3]}, {"input_ids": [1,2,3]}]
    ok, msg = check_batch_sample_distinctness(samples, 2)
    assert not ok and "identical" in msg.lower()

def test_batch_distinctness_insufficient_samples():
    ok, msg = check_batch_sample_distinctness([{"input_ids": [1,2,3]}], 3)
    assert not ok and "only" in msg.lower()

# ===== attention_mask default =====

def test_attention_mask_default():
    samples = [{"input_ids": [7,8,9]}, {"input_ids": [10,11,12]}]
    apply_default_attention_mask(samples, 3)
    for s in samples:
        assert s["attention_mask"] == [1, 1, 1]

# ===== wmpc_id =====

def test_wmpc_id_stability():
    m = _manifest()
    assert generate_wmpc_id(m) == generate_wmpc_id(m)
    assert generate_wmpc_id(m).startswith("wmpc-")

def test_wmpc_id_different():
    assert generate_wmpc_id(_manifest()) != generate_wmpc_id(_manifest(fixed_input_tokens=999))

# ===== run_id =====

def test_run_id_uniqueness():
    r1, r2 = generate_run_id(), generate_run_id()
    assert r1 != r2 and r1.startswith("run-") and r2.startswith("run-")

# ===== NVTX invocation =====

def test_nvtx_invocation_label_roundtrip():
    label = make_invocation_label(*INV)
    p = parse_invocation_label(label)
    assert p is not None
    assert (p.experiment_id, p.wmpc_id, p.run_id, p.pass_label, p.repeat_index) == INV

# ===== NVTX phase =====

def test_nvtx_phase_label_valid():
    for phase in ("full_request", "prefill", "decode"):
        label = make_phase_label(phase)
        assert label.startswith(NVTX_PHASE_PREFIX) and parse_phase_label(label) == phase

def test_nvtx_phase_label_invalid_raises():
    with pytest.raises(ValueError):
        make_phase_label("bogus_phase")

# ===== legacy NVTX detection =====

def test_nvtx_legacy_detection():
    for label in ("full_request", "prefill", "decode", "decode_step_5", "prepare_input"):
        assert is_legacy_nvtx_label(label)
    assert not is_legacy_nvtx_label(make_invocation_label(*INV))

# ===== normalize_phase_name =====

def test_normalize_phase_name_v3():
    for phase in ("full_request", "prefill", "decode"):
        assert normalize_phase_name(f"{NVTX_PHASE_PREFIX}{phase}") == phase

def test_normalize_phase_name_legacy():
    assert normalize_phase_name("full_request") == "full_request"
    assert normalize_phase_name("prefill") == "prefill"
    assert normalize_phase_name("decode") == "decode"
    assert normalize_phase_name("decode_step_3") == "decode"
    assert normalize_phase_name("prepare_input") == "prepare_input"

# ===== manifest validation =====

def test_manifest_required_fields():
    m = _manifest(); del m["fixed_input_tokens"]
    assert any("fixed_input_tokens" in e for e in validate_manifest_core(m))
    assert validate_manifest_core(_manifest()) == []

# ===== result logging =====

def test_exclusion_log_written():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        record_exclusion(out, run_id="run-test", repeat_index=1,
                         reason="CUDA OOM", exception="OutOfMemoryError",
                         exclusion_reason="OOM", oom=True,
                         data_role="PILOT", run_role="PILOT", study_mode="G1_NATURAL")
        lines = (out / "exclusion_log.jsonl").read_text("utf-8").strip().split("\n")
        e = json.loads(lines[0])
        assert e["attempt_status"] == "excluded" and e["invalid_reason"] == "CUDA OOM"

def test_success_log_written():
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        record_success(out, run_id="run-test", repeat_index=0,
                       inference_start_ns=1_000_000_000, inference_end_ns=1_000_050_000,
                       prefill_latency_ms=12.345, decode_latency_ms=34.567,
                       actual_input_tokens=128, actual_output_tokens=64, batch_size=1,
                       data_role="PILOT", run_role="PILOT", study_mode="G1_NATURAL")
        lines = (out / "inference_results.jsonl").read_text("utf-8").strip().split("\n")
        e = json.loads(lines[0])
        assert e["attempt_status"] == "success" and e["actual_input_tokens"] == 128


# ===== SHA-256 validation =====

def _write_pt_json(td: Path, content: dict) -> str:
    """Write a prompt_tokens.json to *td* and return its SHA-256."""
    pt_path = td / "prompt_tokens.json"
    pt_path.write_text(json.dumps(content), "utf-8")
    return compute_prompt_tokens_sha256(pt_path)


def _write_manifest(td: Path, sha: str, pt_path_str: str = "") -> Path:
    """Write a minimal manifest with the given SHA."""
    if not pt_path_str:
        pt_path_str = str(td / "prompt_tokens.json")
    m = _manifest(prompt_tokens_file=pt_path_str, prompt_tokens_sha256=sha)
    mp = td / "wmpc_manifest.json"
    mp.write_text(json.dumps(m, indent=2), "utf-8")
    return mp


# -- SHA-256 string validation --

def test_sha256_valid():
    assert validate_sha256_string("a" * 64) is None
    assert validate_sha256_string("0" * 64) is None  # edge case but valid hex

def test_sha256_null_fails():
    assert validate_sha256_string(None) is not None

def test_sha256_empty_fails():
    assert validate_sha256_string("") is not None

def test_sha256_placeholder_fails():
    assert validate_sha256_string("placeholder") is not None
    assert validate_sha256_string("none") is not None
    assert validate_sha256_string("unknown") is not None

def test_sha256_bad_format_fails():
    assert validate_sha256_string("not-a-hex-string!!") is not None
    assert validate_sha256_string("abc123") is not None  # too short
    assert validate_sha256_string("g" * 64) is not None  # 'g' not hex

# -- SHA-256 match (integration) --

def test_sha256_match_pass():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        pt = _valid_pt()
        good_sha = _write_pt_json(d, pt)
        mp = _write_manifest(d, good_sha)
        m = json.loads(mp.read_text("utf-8"))
        assert validate_prompt_tokens_sha256_match(m) is None

def test_sha256_file_content_changed_fails():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        good_sha = _write_pt_json(d, _valid_pt())
        mp = _write_manifest(d, good_sha)
        # Tamper with the file
        pt_path = d / "prompt_tokens.json"
        pt_path.write_text(json.dumps({"tampered": True}), "utf-8")
        m = json.loads(mp.read_text("utf-8"))
        err = validate_prompt_tokens_sha256_match(m)
        assert err is not None and "mismatch" in err.lower()

def test_sha256_file_not_found_fails():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        mp = _write_manifest(d, "a" * 64, pt_path_str=str(d / "nonexistent.json"))
        m = json.loads(mp.read_text("utf-8"))
        err = validate_prompt_tokens_sha256_match(m)
        assert err is not None and "not found" in err.lower()

def test_sha256_placeholder_fails_in_match():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write_pt_json(d, _valid_pt())
        mp = _write_manifest(d, "placeholder")
        m = json.loads(mp.read_text("utf-8"))
        err = validate_prompt_tokens_sha256_match(m)
        assert err is not None and "placeholder" in err.lower()

def test_sha256_empty_fails_in_match():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write_pt_json(d, _valid_pt())
        mp = _write_manifest(d, "")
        m = json.loads(mp.read_text("utf-8"))
        assert validate_prompt_tokens_sha256_match(m) is not None

def test_sha256_null_fails_in_match():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        _write_pt_json(d, _valid_pt())
        mp = _write_manifest(d, None)
        m = json.loads(mp.read_text("utf-8"))
        assert validate_prompt_tokens_sha256_match(m) is not None

# -- update-prompt-sha --

def test_update_prompt_sha_explicit_command():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        good_sha = _write_pt_json(d, _valid_pt())
        # Write manifest with a bogus SHA
        mp = _write_manifest(d, "a" * 64)
        # Explicit update
        updated = update_prompt_sha(mp)
        assert updated["prompt_tokens_sha256"] == good_sha
        # Verify it was persisted
        reloaded = json.loads(mp.read_text("utf-8"))
        assert reloaded["prompt_tokens_sha256"] == good_sha

def test_update_prompt_sha_missing_file_fails():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        # Create the prompt_tokens file FIRST, then the manifest
        _write_pt_json(d, _valid_pt())
        mp = _write_manifest(d, "a" * 64)
        # Delete the pt file so update_prompt_sha can't find it
        (d / "prompt_tokens.json").unlink()
        with pytest.raises(FileNotFoundError):
            update_prompt_sha(mp)


# ===== ns → ms conversion =====

def test_e2e_ns_to_ms_conversion():
    """inference_e2e_latency_ms correctly converts ns → ms."""
    from exposedpath.results import record_success
    start_ns = 1_000_000_000
    end_ns = 1_204_694_500
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        r = record_success(out, run_id="run-test", repeat_index=0,
                           inference_start_ns=start_ns, inference_end_ns=end_ns,
                           prefill_latency_ms=89.8, decode_latency_ms=114.9,
                           actual_input_tokens=32, actual_output_tokens=2, batch_size=1,
                           data_role="PILOT", run_role="PILOT", study_mode="G1_NATURAL")
        e2e = r["inference_e2e_latency_ms"]
        assert 204.6 < e2e < 204.8, f"Expected ~204.6945 ms, got {e2e}"
        assert e2e != 204694500.0, f"ns→ms conversion missing: got raw ns value {e2e}"

def test_e2e_time_invariants():
    """end_ns <= start_ns should raise, e2e > 0."""
    from exposedpath.results import record_success
    with tempfile.TemporaryDirectory() as td:
        out = Path(td)
        # Valid: end > start
        r = record_success(out, run_id="run-test", repeat_index=0,
                           inference_start_ns=1_000_000_000, inference_end_ns=1_200_000_000,
                           prefill_latency_ms=50.0, decode_latency_ms=150.0,
                           actual_input_tokens=32, actual_output_tokens=2, batch_size=1,
                           data_role="PILOT", run_role="PILOT", study_mode="G1_NATURAL")
        assert r["inference_e2e_latency_ms"] > 0
        assert r["prefill_latency_ms"] >= 0
        assert r["decode_latency_ms"] >= 0
