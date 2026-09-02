"""
NVTX label construction and parsing for ExposedPath v3.

Format:
  Invocation: EXPOSEDPATH_INVOCATION:<experiment_id>:<wmpc_id>:<run_id>:<pass_label>:<repeat_index>
  Phase:      EXPOSEDPATH_PHASE:<phase_name>
"""

import re
from dataclasses import dataclass
from typing import Optional, Tuple

INVOCATION_PREFIX = "EXPOSEDPATH_INVOCATION"
PHASE_PREFIX = "EXPOSEDPATH_PHASE"

VALID_PHASES = {"full_request", "prefill", "decode"}


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
