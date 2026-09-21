"""
WMPC identity generators: experiment_id, wmpc_id, run_id.

- wmpc_id: stable hash of W/M/P/C conditions only (no timestamp, no run metadata).
- run_id: UTC timestamp + short random suffix for a single collection attempt.
"""

import datetime
import hashlib
import json
import secrets
from typing import Dict


def generate_experiment_id(short_name: str) -> str:
    """Generate a human-readable experiment identifier.

    Example: ``pilot_6000ada_202607``
    """
    return short_name


def generate_wmpc_id(manifest_dict: Dict) -> str:
    """Generate a stable wmpc_id from W/M/P/C fields only.

    The hash covers exclusively:
      W: fixed_input_tokens, fixed_output_tokens, batch_size, sampling_config
      M: model_id, revision, dtype_and_quantization, num_hidden_layers, hidden_size,
         num_attention_heads, num_key_value_heads, intermediate_size
      P: gpu_model, cpu_model
      C: cuda_version_used, inference_framework_version, execution_mode, attention_backend

    Timestamps, run_ids, analyzer versions, and environment snapshots are excluded.
    """
    # ---- Extract stable W/M/P/C fields ----
    w_keys = ["fixed_input_tokens", "fixed_output_tokens", "batch_size"]
    m_keys = [
        "model_id", "revision", "dtype_and_quantization",
        "num_hidden_layers", "hidden_size",
        "num_attention_heads", "num_key_value_heads", "intermediate_size",
    ]
    p_keys = ["gpu_model", "cpu_model"]
    c_keys = [
        "cuda_version_used", "inference_framework_version",
        "execution_mode", "attention_backend",
    ]

    stable: Dict = {}
    for group_name, keys in [("W", w_keys), ("M", m_keys), ("P", p_keys), ("C", c_keys)]:
        group: Dict = {}
        for k in keys:
            v = manifest_dict.get(k)
            if v is not None:
                group[k] = v
        # Only include non-empty groups
        if group:
            stable[group_name] = group

    # Include sampling_config if present
    sc = manifest_dict.get("sampling_config")
    if sc is not None:
        stable["W"]["sampling_config"] = sc

    payload = json.dumps(stable, sort_keys=True, ensure_ascii=True, default=str)
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]
    return f"wmpc-{digest}"


def generate_run_id() -> str:
    """Generate a unique run_id: UTC timestamp + short random suffix."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(4)
    return f"run-{ts}-{suffix}"


def generate_attempt_uid(run_id: str, repeat_index: int, retry_index: int = 0) -> str:
    """Generate an attempt uid.

    ``retry_index`` 0 is the first (planned) attempt and keeps the historical
    uid format.  Retries of the same planned repeat index get a distinct uid so
    attempt identity can never collide across retries.
    """
    base = f"{run_id}-rep{repeat_index:04d}"
    if retry_index <= 0:
        return base
    return f"{base}-retry{retry_index:02d}"


def generate_analysis_run_id() -> str:
    """Generate a unique analysis run identifier."""
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    suffix = secrets.token_hex(4)
    return f"analysis-{ts}-{suffix}"
