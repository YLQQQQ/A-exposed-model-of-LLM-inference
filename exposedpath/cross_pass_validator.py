"""Cross-pass parity validator for Pass 0 vs Pass 1 timing comparison."""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from exposedpath.results import ATTEMPT_STATUS_EXCLUDED, ATTEMPT_STATUS_SUCCESS


# ---- Status enumerations ----
PASS_WORKLOAD_MISMATCH           = "PASS_WORKLOAD_MISMATCH"
PASS_EXECUTION_PARITY_MISMATCH   = "PASS_EXECUTION_PARITY_MISMATCH"
PASS_GPU_MISMATCH                = "PASS_GPU_MISMATCH"
PASS_TIMING_MISMATCH             = "PASS_TIMING_MISMATCH"
PROFILER_OVERHEAD_EXCEEDED       = "PROFILER_OVERHEAD_EXCEEDED"
PASS_PARITY_OK                   = "PASS_PARITY_OK"
# EP-G7-09: a required parity identity field is absent on at least one side.
# Missing identity is never treated as equality — it fails closed.
PASS_PARITY_IDENTITY_MISSING     = "PASS_PARITY_IDENTITY_MISSING"
# EP-G7-09: planned/success/exclusion/retry accounting differs between passes.
PASS_ATTEMPT_ACCOUNTING_MISMATCH = "PASS_ATTEMPT_ACCOUNTING_MISMATCH"

# ---- Frozen Pass 0 / Pass 1 parity identity (EP-G7-09) ----
# Every field below must be present on both sides. A field that is absent is
# reported as PASS_PARITY_IDENTITY_MISSING and never silently compared as null.
PARITY_WORKLOAD_FIELDS = (
    "prompt_tokens_sha256",
    "experiment_id",
    "wmpc_id",
    "fixed_input_tokens",
    "fixed_output_tokens",
    "batch_size",
    "sampling_config",
    "warmup_count",
    "repeat_count",
)
PARITY_GPU_FIELDS = (
    "gpu_uuid",
    "gpu_pci_bus_id",
    "requested_physical_gpu_index",
)
PARITY_EXECUTION_FIELDS = (
    "runner_source_sha256",
    "dtype",
    "attention_backend",
    "execution_mode",
    "inference_mode",
    "use_cache",
    "synchronize_policy",
    "study_mode",
    "n1_intervention",
    "cuda_visible_devices",
)
PARITY_PHASE_BOUNDARY_FIELDS = (
    "phase_boundary_policy_version",
    "phase_boundary_policy",
    "token_ready_mechanism",
    "token_ready_origin",
)
PARITY_ENVIRONMENT_FIELDS = (
    "data_role",
    "run_role",
    "python_version",
    "pytorch_version",
    "transformers_version",
    "cuda_runtime_version",
    "nvidia_driver_version",
    "cuda_device_order",
    "torch_num_threads",
    "torch_num_interop_threads",
    "omp_num_threads",
    "mkl_num_threads",
    "cpu_affinity",
)
PARITY_ATTEMPT_PLAN_FIELDS = (
    "attempt_plan_version",
    "retry_policy",
    "planned_warmup_count",
    "planned_repeat_count",
)

# (status reported when the group is present but different, group fields)
PARITY_STATUS_GROUPS = (
    (PASS_WORKLOAD_MISMATCH, PARITY_WORKLOAD_FIELDS),
    (PASS_GPU_MISMATCH, PARITY_GPU_FIELDS),
    (PASS_EXECUTION_PARITY_MISMATCH, PARITY_EXECUTION_FIELDS),
    (PASS_EXECUTION_PARITY_MISMATCH, PARITY_PHASE_BOUNDARY_FIELDS),
    (PASS_EXECUTION_PARITY_MISMATCH, PARITY_ENVIRONMENT_FIELDS),
    (PASS_EXECUTION_PARITY_MISMATCH, PARITY_ATTEMPT_PLAN_FIELDS),
)

# Attempt records written before EP-G7-09 have no machine-readable identity.
# Any absence below fails closed rather than being counted as a valid attempt.
ATTEMPT_IDENTITY_FIELDS = (
    "repeat_index",
    "retry_index",
    "attempt_uid",
    "attempt_plan_version",
    "data_role",
    "phase_boundary_policy_version",
)

ATTEMPT_ACCOUNTING_REQUIRED_FIELDS = (
    "planned_warmup_count",
    "planned_repeat_count",
    "success_count",
    "exclusion_count",
    "success_repeat_indexes",
    "exclusion_repeat_indexes",
    "exclusion_reasons_by_repeat_index",
    "retry_count",
    "retried_repeat_indexes",
    "missing_repeat_indexes",
    "unexpected_repeat_indexes",
    "duplicate_repeat_indexes",
    "records_missing_attempt_identity",
)

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
    """Compare two parity dicts. Returns list of status codes.

    A field that is absent on either side is reported as
    ``PASS_PARITY_IDENTITY_MISSING`` (together with the owning group's mismatch
    status) and is never compared as if it were null: missing provenance must
    fail closed instead of making two passes look equivalent.
    """
    issues: List[str] = []
    if not p0 or not p1:
        issues.append(EXECUTION_PARITY_FAILURE)
        return issues

    missing_fields: List[str] = []
    for status, fields in PARITY_STATUS_GROUPS:
        absent = [k for k in fields if k not in p0 or k not in p1]
        if absent:
            missing_fields.extend(absent)
            if status not in issues:
                issues.append(status)
            continue
        if any(p0[k] != p1[k] for k in fields):
            if status not in issues:
                issues.append(status)

    if missing_fields:
        issues.append(PASS_PARITY_IDENTITY_MISSING)

    if not issues:
        issues.append(PASS_PARITY_OK)
    return issues


# ---------------------------------------------------------------------------
# Attempt / exclusion / retry accounting parity (EP-G7-09)
# ---------------------------------------------------------------------------

def summarize_attempt_records(
    successes: List[Dict],
    exclusions: List[Dict],
    *,
    planned_warmup_count: int,
    planned_repeat_count: int,
) -> Dict:
    """Summarize existing inference_results / exclusion_log records.

    Consumes the records the runner already writes; it creates no new artifact
    and never repairs a gap: missing, duplicate or out-of-plan repeat indexes
    are reported as such.
    """
    planned_indexes = tuple(range(planned_repeat_count))
    pairs = [(ATTEMPT_STATUS_SUCCESS, r) for r in successes]
    pairs += [(ATTEMPT_STATUS_EXCLUDED, r) for r in exclusions]

    identity_missing: List[Dict] = []
    attempt_keys: List[tuple] = []
    success_indexes: List[Optional[int]] = []
    exclusion_indexes: List[Optional[int]] = []
    exclusion_reasons_by_index: Dict[str, List[str]] = {}
    exclusion_reason_counts: Dict[str, int] = {}
    retried_indexes: List[Optional[int]] = []
    retry_count = 0

    for status, record in pairs:
        absent = sorted(k for k in ATTEMPT_IDENTITY_FIELDS if record.get(k) in (None, ""))
        if absent:
            identity_missing.append(
                {"attempt_uid": record.get("attempt_uid"), "missing_fields": absent}
            )
        repeat_index = record.get("repeat_index")
        retry_index = record.get("retry_index")
        attempt_keys.append((repeat_index, retry_index))
        if isinstance(retry_index, int) and retry_index > 0:
            retry_count += 1
            retried_indexes.append(repeat_index)
        if status == ATTEMPT_STATUS_SUCCESS:
            success_indexes.append(repeat_index)
        else:
            exclusion_indexes.append(repeat_index)
            reason = record.get("exclusion_reason")
            exclusion_reasons_by_index.setdefault(str(repeat_index), []).append(reason)
            key = str(reason)
            exclusion_reason_counts[key] = exclusion_reason_counts.get(key, 0) + 1

    for values in exclusion_reasons_by_index.values():
        values.sort(key=lambda v: "" if v is None else str(v))

    first_attempt_indexes = [
        repeat_index
        for repeat_index, retry_index in attempt_keys
        if retry_index == 0 and isinstance(repeat_index, int)
    ]
    covered_indexes = sorted({i for i in first_attempt_indexes})
    duplicate_indexes = sorted(
        {i for i in set(first_attempt_indexes) if first_attempt_indexes.count(i) > 1}
    )

    return {
        "planned_warmup_count": planned_warmup_count,
        "planned_repeat_count": planned_repeat_count,
        "attempt_count": len(pairs),
        "success_count": len(success_indexes),
        "exclusion_count": len(exclusion_indexes),
        "covered_repeat_indexes": covered_indexes,
        "success_repeat_indexes": sorted(i for i in success_indexes if isinstance(i, int)),
        "exclusion_repeat_indexes": sorted(i for i in exclusion_indexes if isinstance(i, int)),
        "exclusion_reasons_by_repeat_index": exclusion_reasons_by_index,
        "exclusion_reason_counts": exclusion_reason_counts,
        "retry_count": retry_count,
        "retried_repeat_indexes": sorted(
            {i for i in retried_indexes if isinstance(i, int)}
        ),
        "missing_repeat_indexes": [i for i in planned_indexes if i not in covered_indexes],
        "unexpected_repeat_indexes": [i for i in covered_indexes if i not in planned_indexes],
        "duplicate_repeat_indexes": duplicate_indexes,
        "records_missing_attempt_identity": identity_missing,
    }


def _read_jsonl(path: Path) -> List[Dict]:
    if not path.is_file():
        return []
    records: List[Dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            records.append({"unparsable_line": line})
    return records


def load_attempt_accounting(
    pass_dir: Path,
    *,
    planned_warmup_count: int,
    planned_repeat_count: int,
) -> Dict:
    """Load the accounting summary for one pass directory.

    ``inference_results.jsonl`` must exist — a missing results file is an
    execution failure, not an empty pass. ``exclusion_log.jsonl`` legitimately
    does not exist when nothing was excluded; that state is recorded explicitly.
    """
    pass_dir = Path(pass_dir)
    results_path = pass_dir / "inference_results.jsonl"
    if not results_path.is_file():
        raise FileNotFoundError(f"missing pass results artifact: {results_path}")
    exclusions_path = pass_dir / "exclusion_log.jsonl"
    accounting = summarize_attempt_records(
        _read_jsonl(results_path),
        _read_jsonl(exclusions_path),
        planned_warmup_count=planned_warmup_count,
        planned_repeat_count=planned_repeat_count,
    )
    accounting["exclusion_log_present"] = exclusions_path.is_file()
    accounting["inference_results_path"] = str(results_path)
    return accounting


def validate_attempt_accounting(p0: Dict, p1: Dict) -> List[str]:
    """Compare Pass 0 / Pass 1 planned/success/exclusion/retry accounting."""
    issues: List[str] = []
    if not p0 or not p1:
        return [PASS_ATTEMPT_ACCOUNTING_MISMATCH]

    if any(k not in p0 or k not in p1 for k in ATTEMPT_ACCOUNTING_REQUIRED_FIELDS):
        return [PASS_PARITY_IDENTITY_MISSING, PASS_ATTEMPT_ACCOUNTING_MISMATCH]

    if (
        p0["planned_warmup_count"] != p1["planned_warmup_count"]
        or p0["planned_repeat_count"] != p1["planned_repeat_count"]
    ):
        issues.append(PASS_EXECUTION_PARITY_MISMATCH)

    incomplete = any(
        (
            p0["missing_repeat_indexes"],
            p1["missing_repeat_indexes"],
            p0["unexpected_repeat_indexes"],
            p1["unexpected_repeat_indexes"],
            p0["duplicate_repeat_indexes"],
            p1["duplicate_repeat_indexes"],
        )
    )
    if incomplete:
        issues.append(PASS_ATTEMPT_ACCOUNTING_MISMATCH)

    if p0["records_missing_attempt_identity"] or p1["records_missing_attempt_identity"]:
        issues.append(PASS_PARITY_IDENTITY_MISSING)
        if PASS_ATTEMPT_ACCOUNTING_MISMATCH not in issues:
            issues.append(PASS_ATTEMPT_ACCOUNTING_MISMATCH)

    for key in (
        "success_count",
        "exclusion_count",
        "success_repeat_indexes",
        "exclusion_repeat_indexes",
        "exclusion_reasons_by_repeat_index",
        "exclusion_reason_counts",
        "retry_count",
        "retried_repeat_indexes",
    ):
        if p0.get(key) != p1.get(key):
            if PASS_ATTEMPT_ACCOUNTING_MISMATCH not in issues:
                issues.append(PASS_ATTEMPT_ACCOUNTING_MISMATCH)
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
