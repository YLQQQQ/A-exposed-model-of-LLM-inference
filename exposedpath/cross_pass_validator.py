"""Cross-pass parity validator for Pass 0 vs Pass 1 timing comparison."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---- Status enumerations ----
PASS_WORKLOAD_MISMATCH           = "PASS_WORKLOAD_MISMATCH"
PASS_EXECUTION_PARITY_MISMATCH   = "PASS_EXECUTION_PARITY_MISMATCH"
PASS_GPU_MISMATCH                = "PASS_GPU_MISMATCH"
PASS_TIMING_MISMATCH             = "PASS_TIMING_MISMATCH"
PROFILER_OVERHEAD_EXCEEDED       = "PROFILER_OVERHEAD_EXCEEDED"
PASS_PARITY_OK                   = "PASS_PARITY_OK"

# Diagnostic verdicts
PROCESS_ORDER_WARM_STATE       = "PROCESS_ORDER_WARM_STATE"
PASS1_SPECIFIC_PROFILING_EFFECT = "PASS1_SPECIFIC_PROFILING_EFFECT"
GPU_CLOCK_POWER_CAUSE_CONFIRMED = "GPU_CLOCK_POWER_CAUSE_CONFIRMED"
GPU_CLOCK_NOT_SUFFICIENT        = "GPU_CLOCK_NOT_SUFFICIENT"
CLOCK_LOCK_UNSUPPORTED          = "CLOCK_LOCK_UNSUPPORTED"
EXECUTION_PARITY_FAILURE        = "EXECUTION_PARITY_FAILURE"
INCONCLUSIVE                    = "INCONCLUSIVE"


def _load_parity(path: Path) -> Optional[Dict]:
    if not path.is_file(): return None
    try: return json.loads(path.read_text())
    except: return None


def validate_pair(p0: Dict, p1: Dict) -> List[str]:
    """Compare two parity dicts. Returns list of status codes."""
    issues = []
    if not p0 or not p1:
        issues.append(EXECUTION_PARITY_FAILURE)
        return issues

    # Workload identity
    for k in ["prompt_tokens_sha256","experiment_id","wmpc_id","warmup_count","repeat_count"]:
        if p0.get(k) != p1.get(k):
            issues.append(PASS_WORKLOAD_MISMATCH)
            break

    # GPU identity
    for k in ["gpu_uuid","gpu_pci_bus_id","requested_physical_gpu_index"]:
        if p0.get(k) != p1.get(k):
            issues.append(PASS_GPU_MISMATCH)
            break

    # The Gate 7 mode identity is mandatory. Treat a legacy pair that omits the
    # fields on both sides as unknown, not as equal.
    required_mode_fields = ("study_mode", "n1_intervention")
    if any(k not in p0 or k not in p1 for k in required_mode_fields):
        issues.append(PASS_EXECUTION_PARITY_MISMATCH)

    # Execution parity
    for k in ["runner_source_sha256","dtype","attention_backend","execution_mode",
              "inference_mode","use_cache","synchronize_policy","study_mode",
              "n1_intervention","cuda_visible_devices"]:
        if p0.get(k) != p1.get(k):
            if PASS_EXECUTION_PARITY_MISMATCH not in issues:
                issues.append(PASS_EXECUTION_PARITY_MISMATCH)
            break

    if not issues:
        issues.append(PASS_PARITY_OK)
    return issues


def compute_timing_ratio(p0_latencies: List[float], p1_latencies: List[float]) -> Tuple[Optional[float], List[str]]:
    """Compute Pass1/Pass0 median ratio. Returns (ratio, status_codes)."""
    if not p0_latencies or not p1_latencies:
        return None, [INCONCLUSIVE]

    def _median(vals): s=sorted(vals); n=len(s); return (s[n//2]+s[(n-1)//2])/2
    m0=_median(p0_latencies); m1=_median(p1_latencies)
    if m0<=0: return None,[INCONCLUSIVE]
    ratio=m1/m0
    status=[]
    if ratio<0.9: status.append(PASS_TIMING_MISMATCH)
    elif ratio>1.1: status.append(PASS_TIMING_MISMATCH)
    elif ratio>1.0 and ratio<=1.1:
        overhead=(ratio-1)*100
        if overhead>10: status.append(PROFILER_OVERHEAD_EXCEEDED)
        else: status.append(PASS_PARITY_OK)
    else: status.append(PASS_PARITY_OK)
    return round(ratio,4), status


def diagnose_multi_run(run_a_ratio: Optional[float], run_b_ratio: Optional[float],
                       run_c_ratio: Optional[float], clock_locked: bool) -> str:
    """Apply cross-run diagnostic rules."""
    if clock_locked and run_c_ratio is not None:
        if 0.9<=run_c_ratio<=1.1: return GPU_CLOCK_POWER_CAUSE_CONFIRMED
        return GPU_CLOCK_NOT_SUFFICIENT
    if run_a_ratio is not None and run_b_ratio is not None:
        if 0.9<=run_a_ratio<=1.1 and 0.9<=run_b_ratio<=1.1: return PASS_PARITY_OK
    return INCONCLUSIVE
