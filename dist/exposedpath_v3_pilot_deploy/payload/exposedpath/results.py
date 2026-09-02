"""
Result recording: inference results and exclusion log.
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, Optional

from exposedpath.ids import generate_attempt_uid


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
    extra: Optional[Dict[str, Any]] = None,
) -> Dict:
    """Record a successful attempt to inference_results.jsonl."""
    record = {
        "repeat_index": repeat_index,
        "attempt_status": "success",
        "attempt_uid": generate_attempt_uid(run_id, repeat_index),
        "run_id": run_id,
        "inference_start_ns": inference_start_ns,
        "inference_end_ns": inference_end_ns,
        "inference_e2e_latency_ms": (inference_end_ns - inference_start_ns) / 1_000_000.0,
        "prefill_latency_ms": round(prefill_latency_ms, 3),
        "decode_latency_ms": round(decode_latency_ms, 3),
        "actual_input_tokens": actual_input_tokens,
        "actual_output_tokens": actual_output_tokens,
        "batch_size": batch_size,
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
    extra: Optional[Dict[str, Any]] = None,
) -> Dict:
    """Record a failed/excluded attempt to exclusion_log.jsonl."""
    record = {
        "repeat_index": repeat_index,
        "attempt_status": "excluded",
        "attempt_uid": generate_attempt_uid(run_id, repeat_index),
        "run_id": run_id,
        "invalid_reason": reason,
        "exception": exception,
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
