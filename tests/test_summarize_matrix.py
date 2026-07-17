#!/usr/bin/env python3
"""Matrix-level tests for summarize_matrix.py (exposedpath-v2)."""

import json, math, sys, tempfile
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.summarize_matrix import (
    sample_std, percentile, _agg, cv_pct,
    _latency_stability, _component_is_significant,
    _phase_b_stats, _build_rerun_candidates,
    load_accounting, validate_workload, extract_workload,
    METRIC_VERSION, B_DIST_KEYS, ALL_INVALID_REASONS,
    SMALL_COMPONENT_PCT_THRESHOLD, SMALL_COMPONENT_MS_THRESHOLD,
)


def _make_minimal_accounting(workload_id="w01", version=METRIC_VERSION,
                              git_commit="abc123", repeats=5,
                              a_host_prefill=36.0, **kwargs):
    rr = []
    for ri in range(repeats):
        # prefill
        rr.append({
            "workload_id": workload_id, "request_id": ri + 1, "repeat_id": ri + 1,
            "phase": "prefill",
            "A_host_path_ms": a_host_prefill + ri * 0.1,
            "A_cuda_api_ms": 88.0, "A_device_wait_ms": 27.0,
            "A_sync_residual_ms": 33.0, "A_unattributed_ms": 0,
            "A_host_path_pct": 20.0, "A_cuda_api_pct": 48.0,
            "A_device_wait_pct": 15.0, "A_sync_residual_pct": 17.0, "A_unattributed_pct": 0,
            "window_duration_ms": 185.0, "conservation_error_pct": 0.0,
            "O_api_gpu": 0.32, "O_hostpath_gpu": 0.40,
            "B_valid_count": 2, "B_invalid_count": 0, "sync_supported_count": 2, "B_valid_coverage": 1.0,
            "memcpy_count": 1, "cuda_api_count": 100, "kernel_count": 50, "gpu_active_ratio": 0.5,
            "boundary_valid": True, "tokens_in_phase": 128,
            "ttft_proxy_ms": 185.0,
        })
        # decode
        rr.append({
            "workload_id": workload_id, "request_id": ri + 1, "repeat_id": ri + 1,
            "phase": "decode",
            "A_host_path_ms": 480.0, "A_cuda_api_ms": 1160.0,
            "A_device_wait_ms": 260.0, "A_sync_residual_ms": 270.0, "A_unattributed_ms": 0,
            "A_host_path_pct": 22.0, "A_cuda_api_pct": 53.0,
            "A_device_wait_pct": 12.0, "A_sync_residual_pct": 13.0, "A_unattributed_pct": 0,
            "window_duration_ms": 2180.0, "conservation_error_pct": 0.0,
            "O_api_gpu": 0.32, "O_hostpath_gpu": 0.35,
            "B_valid_count": 15, "B_invalid_count": 0, "sync_supported_count": 15, "B_valid_coverage": 1.0,
            "memcpy_count": 0, "cuda_api_count": 200, "kernel_count": 100, "gpu_active_ratio": 0.45,
            "boundary_valid": True, "tokens_in_phase": 16,
            "tpot_proxy_ms": 145.0,
        })
        # full_request
        rr.append({
            "workload_id": workload_id, "request_id": ri + 1, "repeat_id": ri + 1,
            "phase": "full_request",
            "A_host_path_ms": 520.0, "A_cuda_api_ms": 1250.0,
            "A_device_wait_ms": 290.0, "A_sync_residual_ms": 300.0, "A_unattributed_ms": 0,
            "A_host_path_pct": 22.0, "A_cuda_api_pct": 53.0,
            "A_device_wait_pct": 12.0, "A_sync_residual_pct": 13.0, "A_unattributed_pct": 0,
            "window_duration_ms": 2370.0, "conservation_error_pct": 0.0,
            "O_api_gpu": 0.32, "O_hostpath_gpu": 0.37,
            "B_valid_count": 17, "B_invalid_count": 0, "sync_supported_count": 17, "B_valid_coverage": 1.0,
            "memcpy_count": 1, "cuda_api_count": 300, "kernel_count": 150, "gpu_active_ratio": 0.46,
            "boundary_valid": True, "tokens_in_phase": 144,
        })

    bd = []
    for i in range(repeats * 17):
        ph = "prefill" if i % 17 < 2 else "decode"
        bd.append({
            "physical_sync_uid": f"corr={100+i}:start={i*1000}:end={i*1000+500}",
            "sync_id": i, "request_id": (i // 17) + 1, "phase": ph,
            "B_valid": True, "wait_set_valid": True,
            "terminal_type": "kernel" if i < 75 else "memcpy",
            "terminal_ownership_valid": True, "cross_phase_wait_flag": False,
            "wait_set_external_count": 0, "wait_set_unassigned_count": 0,
            "timestamp_tolerance_applied": False,
            "sync_type": "stream" if i % 17 < 2 else "device",
            "B_predecessor_ms": 0.01, "B_stream_gap_ms": 0.02, "B_self_ms": 0.5,
            "sync_return_tail_ms": 0.03, "device_overlap_with_sync_ms": 0.01, "wait_set_size": 10,
            "invalid_reason": "",
        })
    # Add some invalid syncs
    for i in range(3):
        bd.append({
            "physical_sync_uid": f"corr=999{i}:start={999000+i}:end={999500+i}",
            "sync_id": 999 + i, "request_id": 1, "phase": "decode",
            "B_valid": False, "wait_set_valid": False,
            "terminal_type": "", "terminal_ownership_valid": False,
            "cross_phase_wait_flag": False,
            "wait_set_external_count": 0, "wait_set_unassigned_count": 0,
            "timestamp_tolerance_applied": False,
            "sync_type": "device",
            "B_predecessor_ms": None, "B_stream_gap_ms": None, "B_self_ms": None,
            "sync_return_tail_ms": None, "device_overlap_with_sync_ms": None, "wait_set_size": 0,
            "invalid_reason": "TRACE_ORDERING_ERROR" if i == 0 else ("MULTI_TERMINAL" if i == 1 else "NO_PENDING_ACTIVITY"),
        })

    return {
        "metric_definition_version": version,
        "metadata": {
            "workload_id": workload_id, "gpu_name": "Test GPU",
            "prompt_len": 128, "batch_size": 1, "output_len": 16,
            "git_commit": git_commit, "parser_version": METRIC_VERSION,
            "schema_version": "3.24.8", "nsys_product_version": "2025.6.3.541",
        },
        "trace_quality": {
            "correlation_coverage": 1.0, "conservation_error_max": 0.0,
            "dropped_records_status": "unknown",
            "global_api_assignment_coverage": 0.62,
            "in_request_api_assignment_coverage": 0.9999,
        },
        "repeat_results": rr,
        "b_sync_details": bd,
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestThroughput:
    def test_field_names_no_double_prefix(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert "prefill_input_tokens_per_second" in flat
        assert "decode_output_tokens_per_second" in flat
        assert "full_request_total_tokens_per_second" in flat
        # Old double-prefix names must not exist
        assert "prefill_prefill" not in str(flat.keys())

    def test_throughput_ratio_of_sums(self):
        """Ratio-of-sums: sum(tokens) / sum(latency_s)."""
        # Set uniform latency: 5 repeats × 200ms = 1s total, 128 tokens/repeat = 640 tokens total
        acc = _make_minimal_accounting()
        for r in acc["repeat_results"]:
            r["tokens_in_phase"] = 128 if r["phase"] == "prefill" else None
            if r["phase"] == "prefill":
                r["window_duration_ms"] = 200.0
        flat = extract_workload(acc, "w01")
        # ratio-of-sums: 5×128 / (5×0.2s) = 640/1.0 = 640
        assert flat["prefill_input_tokens_per_second"] == 640.0

    def test_throughput_positive(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat.get("prefill_input_tokens_per_second", 0) > 0


class TestPhaseB:
    def test_prefill_and_decode_b_are_separate(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["prefill_physical_sync_count"] == 10  # 5×2
        assert flat["decode_physical_sync_count"] == 78   # 5×15 + 3 invalid
        assert "prefill_B_self_ms_median" in flat
        assert "decode_B_self_ms_median" in flat
        assert "prefill_B_predecessor_ms_p90" in flat
        assert "decode_B_stream_gap_ms_p95" in flat

    def test_phase_b_terminal_types(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["prefill_terminal_kernel_count"] >= 5
        assert flat["decode_terminal_kernel_count"] >= 50
        assert "prefill_terminal_kernel_share" in flat
        assert "decode_terminal_memcpy_share" in flat

    def test_phase_b_sync_types(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["prefill_stream_sync_count"] == 10
        assert flat["decode_device_sync_count"] > 0

    def test_global_b_still_exists(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["physical_sync_count"] == 88  # 85 valid + 3 invalid

    def test_b_invalid_reason_counts(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["decode_B_invalid_TRACE_ORDERING_ERROR_count"] == 1
        assert flat["decode_B_invalid_MULTI_TERMINAL_count"] == 1
        assert flat["decode_B_invalid_NO_PENDING_ACTIVITY_count"] == 1
        # Prefill has no invalid
        assert flat["prefill_B_invalid_TRACE_ORDERING_ERROR_count"] == 0


class TestQuality:
    def test_latency_stability_ignores_decomp_cv(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        # Latency should be stable (CV near 0 for synthetic data)
        assert flat["latency_stability_status"] == "stable"
        assert flat["latency_stability_max_CV"] is not None

    def test_small_component_high_cv_ignored(self):
        assert _component_is_significant(0.001, 0.5) is False   # <1ms, <5%
        assert _component_is_significant(0.001, 10.0) is True   # >=5%
        assert _component_is_significant(5.0, 0.1) is True      # >=1ms
        assert _component_is_significant(10.0, 10.0) is True    # both

    def test_large_component_high_cv_counts(self):
        assert _component_is_significant(20.0, 15.0) is True

    def test_hard_gate_failure_overrides(self):
        acc = _make_minimal_accounting()
        # Add duplicate
        acc["b_sync_details"].append(acc["b_sync_details"][0].copy())
        flat = extract_workload(acc, "w01")
        assert flat["hard_gate_status"] == "fail"
        assert flat["overall_quality_status"] == "fail"

    def test_rerun_candidates_based_on_latency_cv(self):
        acc = _make_minimal_accounting()
        # Artificially increase CV
        for r in acc["repeat_results"]:
            if r["phase"] == "prefill":
                r["window_duration_ms"] = 200.0 + r["request_id"] * 50  # High variance
        flat = extract_workload(acc, "w01")
        # CV should be high
        candidates = _build_rerun_candidates([flat])
        if flat["prefill_latency_ms_CV"] is not None and flat["prefill_latency_ms_CV"] > 10:
            assert len(candidates) > 0

    def test_overall_quality_pass_for_stable(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["overall_quality_status"] == "pass"
        assert not flat["rerun_recommended"]


class TestMetadata:
    def test_gpu_api_correlation_field_name(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert "gpu_api_correlation_coverage" in flat
        assert flat["gpu_api_correlation_coverage"] == 1.0

    def test_missing_metadata_is_null(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["profiling_overhead_pct"] is None
        assert flat["profiling_overhead_measured"] is False

    def test_schema_and_nsys_versions_present(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        assert flat["schema_version"] == "3.24.8"
        assert flat["nsys_product_version"] == "2025.6.3.541"


class TestValidation:
    def test_git_commit_required_in_strict(self):
        acc = _make_minimal_accounting(git_commit=None)
        errors, warns = validate_workload(acc, strict=True)
        assert any("git_commit" in e for e in errors)

    def test_git_commit_warns_non_strict(self):
        acc = _make_minimal_accounting(git_commit=None)
        errors, warns = validate_workload(acc, strict=False)
        assert len(errors) == 0
        assert any("git_commit" in w for w in warns)


class TestIntegration:
    def test_full_extract_has_all_quality_levels(self):
        acc = _make_minimal_accounting()
        flat = extract_workload(acc, "w01")
        for key in ["hard_gate_status", "latency_stability_status",
                     "decomposition_stability_status", "overall_quality_status",
                     "rerun_recommended"]:
            assert key in flat, f"Missing {key}"


# ===================================================================
def run_tests():
    classes = [TestThroughput, TestPhaseB, TestQuality, TestMetadata,
               TestValidation, TestIntegration]
    total = passed = failed = 0
    errors = []
    for tc in classes:
        inst = tc()
        for name in dir(inst):
            if name.startswith("test_"):
                total += 1
                try:
                    getattr(inst, name)()
                    passed += 1
                    print(f"  ✓ {tc.__name__}.{name}")
                except Exception as e:
                    failed += 1
                    msg = f"  ✗ {tc.__name__}.{name}: {e}"
                    print(msg)
                    errors.append(msg)
    print(f"\n{'='*50}")
    print(f"  Results: {passed}/{total} passed, {failed} failed")
    if errors:
        for err in errors:
            print(f"    {err}")
    print(f"{'='*50}")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
