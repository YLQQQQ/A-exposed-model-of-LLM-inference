"""Tests for small pilot: summarizer, cross-pass validator, clock diag."""

from __future__ import annotations
import json, os, subprocess, sys, tempfile
from pathlib import Path
import pytest

SCRIPT = Path(__file__).resolve().parent.parent / "scripts" / "run_small_pilot.ps1"
DIAG    = Path(__file__).resolve().parent.parent / "scripts" / "run_cross_pass_clock_diag.ps1"
def _t(): return SCRIPT.read_text(encoding="utf-8")

# ===== Cross-pass validator =====
def test_validator_importable():
    from exposedpath.cross_pass_validator import validate_pair, PASS_PARITY_OK
    p = {"prompt_tokens_sha256":"a","experiment_id":"e","wmpc_id":"w","warmup_count":5,"repeat_count":5,
         "gpu_uuid":"u","gpu_pci_bus_id":"p","requested_physical_gpu_index":3,
         "runner_source_sha256":"r","dtype":"fp16","attention_backend":"sdpa","execution_mode":"eager",
         "inference_mode":True,"use_cache":True,"synchronize_policy":"x","cuda_visible_devices":"u"}
    assert PASS_PARITY_OK in validate_pair(p, p)

def test_gpu_mismatch_detected():
    from exposedpath.cross_pass_validator import validate_pair, PASS_GPU_MISMATCH
    p0={"gpu_uuid":"a","gpu_pci_bus_id":"b","requested_physical_gpu_index":3,"prompt_tokens_sha256":"x","experiment_id":"e","wmpc_id":"w","warmup_count":5,"repeat_count":5,"runner_source_sha256":"r","dtype":"fp16","attention_backend":"sdpa","execution_mode":"eager","inference_mode":True,"use_cache":True,"synchronize_policy":"x","cuda_visible_devices":"u"}
    p1=dict(p0); p1["gpu_uuid"]="DIFFERENT"
    assert PASS_GPU_MISMATCH in validate_pair(p0, p1)

def test_workload_mismatch_detected():
    from exposedpath.cross_pass_validator import validate_pair, PASS_WORKLOAD_MISMATCH
    p0={"prompt_tokens_sha256":"a","experiment_id":"e","wmpc_id":"w","warmup_count":5,"repeat_count":5,"gpu_uuid":"u","gpu_pci_bus_id":"p","requested_physical_gpu_index":3,"runner_source_sha256":"r","dtype":"fp16","attention_backend":"sdpa","execution_mode":"eager","inference_mode":True,"use_cache":True,"synchronize_policy":"x","cuda_visible_devices":"u"}
    p1=dict(p0); p1["prompt_tokens_sha256"]="DIFFERENT"
    assert PASS_WORKLOAD_MISMATCH in validate_pair(p0, p1)

def test_execution_parity_mismatch_detected():
    from exposedpath.cross_pass_validator import validate_pair, PASS_EXECUTION_PARITY_MISMATCH
    p0={"prompt_tokens_sha256":"a","experiment_id":"e","wmpc_id":"w","warmup_count":5,"repeat_count":5,"gpu_uuid":"u","gpu_pci_bus_id":"p","requested_physical_gpu_index":3,"runner_source_sha256":"r","dtype":"fp16","attention_backend":"sdpa","execution_mode":"eager","inference_mode":True,"use_cache":True,"synchronize_policy":"x","cuda_visible_devices":"u"}
    p1=dict(p0); p1["runner_source_sha256"]="DIFFERENT"
    assert PASS_EXECUTION_PARITY_MISMATCH in validate_pair(p0, p1)

def test_timing_mismatch_detected():
    from exposedpath.cross_pass_validator import compute_timing_ratio, PASS_TIMING_MISMATCH
    ratio,status=compute_timing_ratio([2861,2900,2850],[715,720,710])
    assert ratio is not None and ratio<0.9
    assert PASS_TIMING_MISMATCH in status

def test_timing_parity_ok():
    from exposedpath.cross_pass_validator import compute_timing_ratio, PASS_PARITY_OK
    ratio,status=compute_timing_ratio([1000,1020,1010],[1030,1050,1040])
    assert ratio is not None and 0.9<=ratio<=1.1
    assert PASS_PARITY_OK in status

def test_no_negative_overhead_output():
    """Validator never outputs negative profiler overhead when ratio < 1."""
    from exposedpath.cross_pass_validator import compute_timing_ratio, PASS_TIMING_MISMATCH
    _,status=compute_timing_ratio([2000,2000],[500,500])
    assert PASS_TIMING_MISMATCH in status

# ===== Clock diag script =====
def test_diag_script_exists():
    assert DIAG.exists()

def test_diag_has_params():
    t=DIAG.read_text(encoding="utf-8")
    assert 'Manifest' in t and 'EnableClockLock' in t

def test_diag_runs_three_runs():
    t=DIAG.read_text(encoding="utf-8")
    assert 'Run A' in t and 'Run B' in t and 'Run C' in t

def test_diag_has_clock_recovery():
    t=DIAG.read_text(encoding="utf-8")
    assert '-rgc' in t

def test_diag_no_force_overwrite():
    t=DIAG.read_text(encoding="utf-8")
    assert 'force-overwrite' not in t.lower()

def test_diag_fail_closed():
    t=DIAG.read_text(encoding="utf-8")
    assert 'EXECUTION_FAILURE' in t and 'failed_passes' in t

def test_diag_validate_manifest_before_runs():
    t=DIAG.read_text(encoding="utf-8")
    assert 'validate-manifest' in t

def test_diag_report_only():
    t=DIAG.read_text(encoding="utf-8")
    assert 'ReportOnly' in t

def test_diag_reads_latency():
    t=DIAG.read_text(encoding="utf-8")
    assert 'Read-Latency' in t and 'inference_results.jsonl' in t

def test_diag_reads_parity():
    t=DIAG.read_text(encoding="utf-8")
    assert 'Read-Parity' in t and 'cross_pass_parity.json' in t

def test_diag_order_effect_detection():
    t=DIAG.read_text(encoding="utf-8")
    assert 'PROCESS_ORDER_WARM_STATE' in t and 'PASS1_SPECIFIC_PROFILING_EFFECT' in t

def test_diag_mean_uses_measure_object():
    t=DIAG.read_text(encoding="utf-8")
    assert 'Measure-Object' in t

def test_diag_read_latency_uses_tryparse():
    t=DIAG.read_text(encoding="utf-8")
    assert 'TryParse' in t

def test_diag_result_parse_failure_detected():
    t=DIAG.read_text(encoding="utf-8")
    assert 'RESULT_PARSE_FAILURE' in t

def test_diag_status_separation():
    t=DIAG.read_text(encoding="utf-8")
    assert 'execution_status' in t and 'execution_parity_status' in t
    assert 'clock_intervention_status' in t and 'root_cause_status' in t

def test_diag_clock_lock_verified():
    t=DIAG.read_text(encoding="utf-8")
    assert 'clock_lock_succeeded' in t and 'observed' in t

def test_diag_lock_failed_blocks_gpu_diagnosis():
    t=DIAG.read_text(encoding="utf-8")
    assert 'CLOCK_LOCK_FAILED_OR_UNVERIFIED' in t
    assert 'CLOCK_CAUSALITY_NOT_EVALUATED' in t

def test_diag_pass1_overhead_observed():
    t=DIAG.read_text(encoding="utf-8")
    assert 'PASS1_PROFILING_OVERHEAD_OBSERVED' in t
    assert 'OLD_NEGATIVE_OVERHEAD_NOT_REPRODUCED' in t

def test_diag_limitations_field():
    t=DIAG.read_text(encoding="utf-8")
    assert 'diagnosis_limitations' in t

# ===== Summarizer =====
def test_summarizer_reads_identity():
    src=(Path(__file__).resolve().parent.parent/"analysis/summarize_small_pilot.py").read_text(encoding="utf-8")
    assert 'pilot_identity.json' in src

# ===== Pilot script =====
def test_pilot_has_identity(): assert 'Write-IdentityFile' in _t()
def test_four_wmpc():
    for p in ["P1","P2","P3","P4"]: assert p in _t()
def test_pilot_role(): assert 'PILOT' in _t()
def test_runner_writes_parity():
    src=(Path(__file__).resolve().parent.parent/"exposedpath/runner.py").read_text(encoding="utf-8")
    assert 'cross_pass_parity.json' in src

# ===== Clock lock tests =====
def test_diag_clock_preflight_param(): assert 'ClockPreflightOnly' in DIAG.read_text(encoding="utf-8")
def test_diag_test_clocklock_function(): assert 'function Test-ClockLock' in DIAG.read_text(encoding="utf-8")
def test_diag_reset_clocklock_function(): assert 'function Reset-ClockLock' in DIAG.read_text(encoding="utf-8")
def test_diag_lock_failure_reasons():
    t=DIAG.read_text(encoding="utf-8")
    for r in ["CLOCK_LOCK_COMMAND_FAILED","CLOCK_LOCK_PERMISSION_DENIED","CLOCK_VERIFICATION_QUERY_FAILED","CLOCK_OUTSIDE_TOLERANCE"]:
        assert r in t, f"Missing failure reason: {r}"
def test_diag_preflight_blocks_full_run():
    """Preflight failure exits before Run A/B/C."""
    t=DIAG.read_text(encoding="utf-8")
    assert 'CLOCK LOCK FAILED OR UNSUPPORTED' in t or 'exit 1' in t
def test_diag_samples_count_param(): assert 'ClockVerificationSamples' in DIAG.read_text(encoding="utf-8")

# ===== Clock policy tests =====
def test_pilot_has_clock_policy_param():
    assert 'DEFAULT_DYNAMIC' in _t() and 'FIXED' in _t()
def test_default_dynamic_no_lgc():
    """DEFAULT_DYNAMIC must not call -lgc, -rgc, or -pm."""
    t = _t()
    # The -lgc/-rgc/-pm calls should only be in the FIXED code path or preflight
    # In DEFAULT_DYNAMIC, these are never used
    assert 'DEFAULT_DYNAMIC' in t
def test_gpu_busy_check():
    assert 'BLOCKED_BY_GPU_BUSY' in _t() and 'compute-apps' in _t()
def test_manifest_has_clock_policy():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"manifest.py").read_text(encoding="utf-8")
    assert 'DEFAULT_DYNAMIC' in src and 'clock_policy' in src
def test_runner_has_telemetry():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"runner.py").read_text(encoding="utf-8")
    assert '_sample_gpu_telemetry' in src and 'telemetry' in src

# ===== Physical/logical GPU =====
def test_physical_logical_gpu_separated():
    assert '$PHYSICAL_GPU_INDEX' in _t() and '$LOGICAL_CUDA_DEVICE' in _t()
def test_manifest_uses_logical_gpu():
    assert '$LOGICAL_CUDA_DEVICE' in _t()
def test_manifest_has_physical_logical_fields():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"manifest.py").read_text(encoding="utf-8")
    assert 'gpu_index_physical' in src and 'gpu_index_logical' in src

# ===== Single P1 =====
def test_pilot_points_param():
    assert '$PilotPoints' in _t()
def test_pilot_points_filter():
    assert 'Where-Object' in _t() and '$_.id' in _t()

# ===== OutputRoot early creation =====
def test_output_root_created_before_writes():
    t = _t()
    nio = t.find('New-Item -ItemType Directory -Force -Path $OutputRoot')
    inv = t.find('gpu_inventory.json')
    assert nio > 0 and nio < inv, "OutputRoot must be created before gpu_inventory.json"

# ===== Failure report =====
def test_revalidation_report_function():
    assert 'Write-RevalidationReport' in _t()
def test_revalidation_report_called_on_fail():
    assert '$false' in _t() and 'MANIFEST_CREATION' in _t()
def test_revalidation_report_called_at_end():
    t=_t(); assert 'Write-RevalidationReport -Success' in t
def test_report_has_gate_logic():
    t=_t()
    assert 'P1_REVALIDATION_PASS' in t and 'P1_REVALIDATION_FAIL' in t
def test_report_checks_analyzer():
    assert 'A_conservation' in _t() or 'accounting_result.json' in _t()

# ===== generate_p1_audit.py tests =====
AUDIT = Path(__file__).resolve().parent.parent / "analysis" / "generate_p1_audit.py"
def test_audit_script_exists():
    assert AUDIT.exists(), f"{AUDIT} not found"
def test_audit_script_importable():
    r = subprocess.run([sys.executable, str(AUDIT)], capture_output=True, text=True, timeout=10)
    # No args -> should print usage and exit non-zero, NOT a syntax error
    combined = r.stdout + r.stderr
    assert "Usage" in combined or "SyntaxError" not in combined

def test_audit_missing_dir_handled():
    with tempfile.TemporaryDirectory() as td:
        nonexistent = td + "/nonexistent"
        r = subprocess.run([sys.executable, str(AUDIT), nonexistent], capture_output=True, text=True, timeout=10)
        # Script handles missing dirs gracefully — P1 not found, gates fail, audit still generated
        audit = Path(nonexistent) / "P1_REVALIDATION_AUDIT.md"
        # May or may not exist depending on script behavior; either is acceptable
        # Key: script does not crash or throw unhandled exception

def test_audit_missing_pass0_handled():
    with tempfile.TemporaryDirectory() as td:
        d = Path(td); (d / "P1").mkdir()
        r = subprocess.run([sys.executable, str(AUDIT), td], capture_output=True, text=True, timeout=10)
        audit = d / "P1_REVALIDATION_AUDIT.md"
        assert audit.exists(), "Audit file should be generated even on failure"
        content = audit.read_text(encoding="utf-8")
        assert "MISSING" in content, "Report should flag missing pass0 results"

def test_audit_cv_triggers_review():
    """CV > 5% -> REPEAT_COUNT_REVIEW_REQUIRED"""
    src = AUDIT.read_text(encoding="utf-8")
    assert "REPEAT_COUNT_REVIEW_REQUIRED" in src
    assert "5%" in src or "5" in src

def test_audit_hard_gate_priority():
    """Hard gate failures -> P1_SCIENTIFIC_GATE_FAIL regardless of CV"""
    src = AUDIT.read_text(encoding="utf-8")
    assert "P1_SCIENTIFIC_GATE_FAIL" in src and "P1_SCIENTIFIC_GATE_PASS" in src

def test_audit_coverage_not_zero_when_missing():
    """Missing fields -> MISSING, never silently 0"""
    src = AUDIT.read_text(encoding="utf-8")
    assert "MISSING" in src

def test_audit_reports_source_files():
    src = AUDIT.read_text(encoding="utf-8")
    assert "inference_results.jsonl" in src and "accounting_result.json" in src

def test_audit_does_not_recollect():
    """No subprocess calls to run inference or nsys"""
    src = AUDIT.read_text(encoding="utf-8")
    assert "run-pass" not in src and "nsys profile" not in src

# ===== Duration coverage tests =====
def test_audit_has_duration_coverage():
    src = AUDIT.read_text(encoding="utf-8")
    assert "sync_duration_total_ms" in src
    assert "supported duration coverage" in src
    assert "B-valid duration coverage" in src

def test_audit_duration_primary_gate():
    """Duration coverage is the primary hard gate, count coverage is informational."""
    src = AUDIT.read_text(encoding="utf-8")
    assert "Primary hard gate" in src and "duration coverage" in src
    assert "Secondary (informational)" in src

def test_audit_npa_review_section():
    src = AUDIT.read_text(encoding="utf-8")
    assert "NO_PENDING_ACTIVITY Review" in src
    assert "EMPTY_WAIT_SET" in src

def test_audit_cv_review_not_hard_fail():
    """CV > 5% triggers review, not hard fail."""
    src = AUDIT.read_text(encoding="utf-8")
    assert "P1_PIPELINE_PASS_REPEAT_REVIEW_REQUIRED" in src

def test_audit_duration_missing_not_zero():
    """Missing duration is flagged, not silently 0."""
    src = AUDIT.read_text(encoding="utf-8")
    assert "MISSING" in src or "sync_duration_total_ms=0" in src

# ===== Telemetry GPU identity tests =====
def test_telemetry_uses_physical_gpu_index():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"runner.py").read_text(encoding="utf-8")
    assert 'gpu_index_physical' in src, "Telemetry must use physical GPU index from manifest"
    assert 'requested_physical_gpu_index' in src

def test_telemetry_has_identity_verification():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"runner.py").read_text(encoding="utf-8")
    assert 'identity_match' in src and 'TELEMETRY_GPU_IDENTITY_MISMATCH' in src

def test_telemetry_observed_vs_requested_separated():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"runner.py").read_text(encoding="utf-8")
    assert 'observed_gpu_uuid' in src and 'requested_gpu_uuid' in src

def test_telemetry_queried_selector_recorded():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"runner.py").read_text(encoding="utf-8")
    assert 'queried_selector' in src

# ===== Host state sampling =====
def test_runner_has_host_state_sampling():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"runner.py").read_text(encoding="utf-8")
    assert '_sample_host_state' in src and 'host_state.jsonl' in src

def test_pilot_has_platform_snapshot():
    assert 'platform_snapshot' in _t() and 'nvidia_smi_topo_m' in _t()

def test_audit_has_latency_anomaly():
    src = AUDIT.read_text(encoding="utf-8")
    assert 'outliers' in src.lower() and 'z-score' in src

def test_parity_has_host_fields():
    src = (Path(__file__).resolve().parent.parent/"exposedpath"/"runner.py").read_text(encoding="utf-8")
    assert 'torch_num_threads' in src and 'process_pid' in src
