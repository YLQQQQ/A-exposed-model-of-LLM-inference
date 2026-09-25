"""
NVTX label construction and parsing for ExposedPath v3.

Format:
  Invocation: EXPOSEDPATH_INVOCATION:<experiment_id>:<wmpc_id>:<run_id>:<pass_label>:<repeat_index>
  Phase:      EXPOSEDPATH_PHASE:<phase_name>
"""

import json
from exposedpath.gate8_identity import make_gate8_pass_identity, validate_shape
from exposedpath.gate8_boundary import Gate8BoundaryRecorder
import re
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

INVOCATION_PREFIX = "EXPOSEDPATH_INVOCATION"
PHASE_PREFIX = "EXPOSEDPATH_PHASE"
STRUCTURED_NVTX_PREFIX = "EXPOSEDPATH_JSON_V1:"

VALID_PHASES = {"full_request", "prefill", "decode"}

_COMMON_IDENTITY_FIELDS = (
    "experiment_id", "wmpc_id", "run_id", "run_role", "pass_id",
    "request_id", "repeat_id",
)


def _validated_identity_base(identity_base: Mapping) -> dict:
    if "attempt_id" in identity_base:
        validate_shape("identity", dict(identity_base))
        return dict(identity_base)
    missing = [field for field in _COMMON_IDENTITY_FIELDS if not identity_base.get(field)]
    if missing:
        raise ValueError(f"Structured NVTX identity missing fields: {', '.join(missing)}")
    return {field: identity_base[field] for field in _COMMON_IDENTITY_FIELDS}


def make_structured_nvtx_label(identity: Mapping) -> str:
    """Encode one frozen-contract structured NVTX identity."""
    return STRUCTURED_NVTX_PREFIX + json.dumps(
        dict(identity), sort_keys=True, separators=(",", ":"), ensure_ascii=True,
    )


def make_natural_token_ready_identity(
    identity_base: Mapping,
    *,
    phase: str,
    token_index: int,
    callsite_id: str,
    sync_ordinal: int,
    token_ready_mechanism: str,
) -> dict:
    """Build a G1 natural Token-ready identity from the frozen contract."""
    if phase not in {"prefill", "decode"}:
        raise ValueError(f"Invalid token-ready phase: {phase}")
    if token_index < 0 or sync_ordinal < 0:
        raise ValueError("token_index and sync_ordinal must be non-negative")
    if not callsite_id or not token_ready_mechanism:
        raise ValueError("callsite_id and token_ready_mechanism are required")
    return {
        **_validated_identity_base(identity_base),
        "kind": "sync",
        "phase": phase,
        "token_index": token_index,
        "callsite_id": callsite_id,
        "sync_origin": "natural_token_ready",
        "sync_ordinal": sync_ordinal,
        "token_ready_mechanism": token_ready_mechanism,
    }


def make_n1_intervention_identity(
    identity_base: Mapping,
    *,
    phase: str,
    callsite_id: str,
    sync_ordinal: int,
    intervention_variant_id: str,
    intervention_ordinal: int,
) -> dict:
    """Build an N1 intervention identity without executing an intervention."""
    if phase not in {"prefill", "decode"}:
        raise ValueError(f"Invalid intervention phase: {phase}")
    if sync_ordinal < 0 or intervention_ordinal < 0:
        raise ValueError("sync/intervention ordinals must be non-negative")
    if not callsite_id or not intervention_variant_id:
        raise ValueError("callsite_id and intervention_variant_id are required")
    return {
        **_validated_identity_base(identity_base),
        "kind": "sync",
        "phase": phase,
        "callsite_id": callsite_id,
        "sync_origin": "n1_intervention",
        "sync_ordinal": sync_ordinal,
        "intervention_variant_id": intervention_variant_id,
        "intervention_ordinal": intervention_ordinal,
    }


def make_invocation_label(
    experiment_id: str,
    wmpc_id: str,
    run_id: str,
    pass_label: str,
    repeat_index: int,
) -> str:
    """Construct a standard invocation NVTX label."""
    return f"{INVOCATION_PREFIX}:{experiment_id}:{wmpc_id}:{run_id}:{pass_label}:{repeat_index}"


def make_phase_label(phase_name: str) -> str:
    """Construct a standard phase NVTX label.

    Args:
        phase_name: One of 'full_request', 'prefill', 'decode'.
    """
    if phase_name not in VALID_PHASES:
        raise ValueError(f"Invalid phase name: {phase_name}. Must be one of {VALID_PHASES}")
    return f"{PHASE_PREFIX}:{phase_name}"


@dataclass
class ParsedInvocation:
    experiment_id: str
    wmpc_id: str
    run_id: str
    pass_label: str
    repeat_index: int


def parse_invocation_label(label: str) -> Optional[ParsedInvocation]:
    """Parse an EXPOSEDPATH_INVOCATION label. Returns None if not a match."""
    pattern = rf"^{INVOCATION_PREFIX}:([^:]+):([^:]+):([^:]+):([^:]+):(\d+)$"
    m = re.match(pattern, label)
    if not m:
        return None
    return ParsedInvocation(
        experiment_id=m.group(1),
        wmpc_id=m.group(2),
        run_id=m.group(3),
        pass_label=m.group(4),
        repeat_index=int(m.group(5)),
    )


def parse_phase_label(label: str) -> Optional[str]:
    """Parse an EXPOSEDPATH_PHASE label. Returns the phase name or None."""
    pattern = rf"^{PHASE_PREFIX}:(.+)$"
    m = re.match(pattern, label)
    if not m:
        return None
    phase = m.group(1)
    if phase not in VALID_PHASES:
        return None
    return phase


def is_legacy_nvtx_label(text: str) -> bool:
    """Detect legacy NVTX labels (full_request, prefill, decode, decode_step_i, prepare_input)."""
    legacy_patterns = [
        r"^full_request$",
        r"^prefill$",
        r"^decode$",
        r"^decode_step_\d+$",
        r"^prepare_input$",
    ]
    for pat in legacy_patterns:
        if re.match(pat, text):
            return True
    return False


def classify_nvtx_label(text: str) -> Tuple[str, dict]:
    """Classify an NVTX range text and return (kind, metadata).

    Returns:
        (kind, meta) where kind is one of:
          'invocation', 'phase', 'legacy_phase', 'legacy_invocation', 'other'
    """
    inv = parse_invocation_label(text)
    if inv:
        return ("invocation", {"parsed": inv})

    phase = parse_phase_label(text)
    if phase:
        return ("phase", {"phase_name": phase})

    if is_legacy_nvtx_label(text):
        if text in ("full_request",):
            return ("legacy_invocation", {"text": text})
        return ("legacy_phase", {"text": text})

    return ("other", {"text": text})
