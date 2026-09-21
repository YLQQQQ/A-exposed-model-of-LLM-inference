"""
Result recording: inference results and exclusion log.

Gate 7 (EP-G7-09) freezes the machine-readable attempt provenance:

  - every attempt records its identity -- ``repeat_index`` (planned slot),
    ``retry_index`` (0 = first attempt), ``is_retry``, ``attempt_uid`` and
    ``retry_of_attempt_uid``;
  - every attempt records the run-mode identity (``data_role``, ``run_role``,
    ``study_mode``) and the frozen attempt-plan / phase-boundary identity, so
    Pass 0 / Pass 1 parity can be checked mechanically instead of by eye;
  - exclusions record a frozen ``exclusion_reason`` code plus the structured
    ``early_eos`` / ``oom`` / output-token-count evidence.

Required provenance is never defaulted or zero-filled: a missing role, an
unknown exclusion code, or a retry without its parent attempt raises instead of
being written as ``null`` / ``0``.
"""

import json
from pathlib import Path
from typing import Any, Dict, Optional

from exposedpath.ids import generate_attempt_uid

# ---- Frozen attempt status ----
ATTEMPT_STATUS_SUCCESS = "success"
ATTEMPT_STATUS_EXCLUDED = "excluded"

# ---- Frozen exclusion reasons (machine-readable; free-form codes are rejected) ----
EXCLUSION_REASON_OOM = "OOM"
EXCLUSION_REASON_EARLY_EOS = "EARLY_EOS"
EXCLUSION_REASON_OUTPUT_TOKEN_COUNT_MISMATCH = "OUTPUT_TOKEN_COUNT_MISMATCH"
EXCLUSION_REASON_CUDA_ERROR = "CUDA_ERROR"
EXCLUSION_REASON_RUNTIME_ERROR = "RUNTIME_ERROR"
EXCLUSION_REASONS = frozenset({
    EXCLUSION_REASON_OOM,
    EXCLUSION_REASON_EARLY_EOS,
    EXCLUSION_REASON_OUTPUT_TOKEN_COUNT_MISMATCH,
    EXCLUSION_REASON_CUDA_ERROR,
    EXCLUSION_REASON_RUNTIME_ERROR,
})

# ---- Frozen Gate 7 phase / completion identity (single source of truth) ----
# The runner stamps these into attempt records and cross_pass_parity.json;
# exposedpath.cross_pass_validator compares them field by field.
PHASE_BOUNDARY_POLICY_VERSION = "exposedpath-phase-boundary/0.1.0"
TOKEN_READY_MECHANISM = "device_to_host_token_ids"
TOKEN_READY_ORIGIN_NATURAL = "natural_token_ready"
TOKEN_READY_ORIGIN_N1 = "n1_intervention"
PHASE_BOUNDARY_POLICY = {
    "request_start": "after_request_start_drain",
    "prefill_end": "token_index_0_host_readable",
    "decode_step_end": "token_ready_host_readable",
    "full_request_end": "final_token_ready_host_readable",
    "cleanup_inside_measured_window": False,
}

# ---- Frozen attempt plan / retry identity ----
ATTEMPT_PLAN_VERSION = "exposedpath-attempt-plan/0.1.0"
RETRY_POLICY = "EXACTLY_ONE_ATTEMPT_PER_PLANNED_REPEAT_INDEX_NO_AUTO_RETRY"


def _require_provenance(data_role, run_role, study_mode) -> None:
    """Fail closed instead of writing a default/zero provenance value."""
    for name, value in (
        ("data_role", data_role),
        ("run_role", run_role),
        ("study_mode", study_mode),
    ):
        if not isinstance(value, str) or not value:
            raise ValueError(f"{name} is required for a machine-readable attempt record")


def _attempt_identity(
    *,
    run_id: str,
    repeat_index: int,
    retry_index: int,
    retry_of_attempt_uid: Optional[str],
) -> Dict[str, Any]:
    if not isinstance(repeat_index, int) or isinstance(repeat_index, bool) or repeat_index < 0:
        raise ValueError("repeat_index must be a non-negative integer")
    if not isinstance(retry_index, int) or isinstance(retry_index, bool) or retry_index < 0:
        raise ValueError("retry_index must be a non-negative integer")
    if retry_index > 0 and not retry_of_attempt_uid:
        raise ValueError("a retry attempt must record retry_of_attempt_uid")
    return {
        "repeat_index": repeat_index,
        "attempt_plan_version": ATTEMPT_PLAN_VERSION,
        "retry_index": retry_index,
        "is_retry": retry_index > 0,
        "attempt_uid": generate_attempt_uid(run_id, repeat_index, retry_index),
        "retry_of_attempt_uid": retry_of_attempt_uid,
    }


def _mode_identity(*, data_role: str, run_role: str, study_mode: str) -> Dict[str, Any]:
    return {
        "data_role": data_role,
        "run_role": run_role,
        "study_mode": study_mode,
        "phase_boundary_policy_version": PHASE_BOUNDARY_POLICY_VERSION,
    }


def record_success(
    output_dir: Path,
    run_id: str,
    repeat_index: int,
    inference_start_ns: int,
    inference_end_ns: int,
    prefill_latency_ms: float,
    decode_latency_ms: float,
    actual_input_tokens: int,
    actual_output_tokens: int,
    batch_size: int,
    *,
    data_role: str,
    run_role: str,
    study_mode: str,
    retry_index: int = 0,
    retry_of_attempt_uid: Optional[str] = None,
    output_len_expected: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict:
    """Record a successful attempt to inference_results.jsonl."""
    _require_provenance(data_role, run_role, study_mode)
    record = {
        **_attempt_identity(
            run_id=run_id,
            repeat_index=repeat_index,
            retry_index=retry_index,
            retry_of_attempt_uid=retry_of_attempt_uid,
        ),
        **_mode_identity(data_role=data_role, run_role=run_role, study_mode=study_mode),
        "attempt_status": ATTEMPT_STATUS_SUCCESS,
        "run_id": run_id,
        "inference_start_ns": inference_start_ns,
        "inference_end_ns": inference_end_ns,
        "inference_e2e_latency_ms": (inference_end_ns - inference_start_ns) / 1_000_000.0,
        "prefill_latency_ms": round(prefill_latency_ms, 3),
        "decode_latency_ms": round(decode_latency_ms, 3),
        "actual_input_tokens": actual_input_tokens,
        "actual_output_tokens": actual_output_tokens,
        "output_len_expected": output_len_expected,
        "batch_size": batch_size,
        "early_eos": False,
        "oom": False,
        "exclusion_reason": None,
    }
    if extra:
        record.update(extra)

    _append_jsonl(output_dir / "inference_results.jsonl", record)
    return record


def record_exclusion(
    output_dir: Path,
    run_id: str,
    repeat_index: int,
    reason: str,
    exception: Optional[str] = None,
    *,
    exclusion_reason: str,
    data_role: str,
    run_role: str,
    study_mode: str,
    retry_index: int = 0,
    retry_of_attempt_uid: Optional[str] = None,
    early_eos: bool = False,
    oom: bool = False,
    output_len_expected: Optional[int] = None,
    output_len_actual: Optional[int] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Dict:
    """Record a failed/excluded attempt to exclusion_log.jsonl."""
    _require_provenance(data_role, run_role, study_mode)
    if exclusion_reason not in EXCLUSION_REASONS:
        raise ValueError(
            f"unknown exclusion_reason {exclusion_reason!r}; "
            f"expected one of {sorted(EXCLUSION_REASONS)}"
        )
    if not isinstance(reason, str) or not reason:
        raise ValueError("a human-readable exclusion reason is required")
    record = {
        **_attempt_identity(
            run_id=run_id,
            repeat_index=repeat_index,
            retry_index=retry_index,
            retry_of_attempt_uid=retry_of_attempt_uid,
        ),
        **_mode_identity(data_role=data_role, run_role=run_role, study_mode=study_mode),
        "attempt_status": ATTEMPT_STATUS_EXCLUDED,
        "run_id": run_id,
        "invalid_reason": reason,
        "exclusion_reason": exclusion_reason,
        "exception": exception,
        "early_eos": bool(early_eos),
        "oom": bool(oom),
        "output_len_expected": output_len_expected,
        "output_len_actual": output_len_actual,
    }
    if extra:
        record.update(extra)

    _append_jsonl(output_dir / "exclusion_log.jsonl", record)
    return record


def _append_jsonl(path: Path, record: Dict) -> None:
    """Append a JSON record to a .jsonl file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
