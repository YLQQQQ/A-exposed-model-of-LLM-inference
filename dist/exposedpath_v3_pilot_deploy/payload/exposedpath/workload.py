"""
Workload / prompt_tokens loading and validation.

Provides the fixed-input contract: tokenizer runs OFFLINE, outside the timing
path.  The result is a ``prompt_tokens.json`` file validated before any
inference invocation.
"""

import json
from pathlib import Path
from typing import Any, Dict, List

from exposedpath.validation import (
    apply_default_attention_mask,
    check_batch_sample_distinctness,
    compute_prompt_tokens_sha256,
    validate_prompt_tokens,
)


def load_prompt_tokens(path: Path) -> Dict:
    """Load and validate a prompt_tokens.json file. Raises on failure."""
    if not path.is_file():
        raise FileNotFoundError(f"prompt_tokens file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

    errors = validate_prompt_tokens(data)
    if errors:
        raise ValueError(f"prompt_tokens validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    # Apply default attention masks
    fixed_len = data["fixed_input_tokens"]
    apply_default_attention_mask(data["samples"], fixed_len)

    return data


def get_batch_inputs(
    prompt_tokens: Dict,
    batch_size: int,
    run_role: str = "FORMAL",
) -> Dict:
    """Extract input_ids and attention_mask tensors for the given batch_size.

    Args:
        prompt_tokens: Loaded prompt_tokens.json data.
        batch_size: Number of samples to use in this batch.
        run_role: ``PILOT`` or ``FORMAL``. FORMAL enforces distinct-sample check.

    Returns:
        Dict with keys: input_ids (list of lists), attention_mask (list of lists),
        fixed_input_tokens, batch_size.

    Raises:
        ValueError: If not enough samples, or (in FORMAL mode) batch samples are clones.
    """
    samples = prompt_tokens["samples"]
    fixed_len = prompt_tokens["fixed_input_tokens"]

    if len(samples) < batch_size:
        raise ValueError(
            f"prompt_tokens has only {len(samples)} samples, "
            f"but batch_size={batch_size} requires at least {batch_size}"
        )

    ok, msg = check_batch_sample_distinctness(samples, batch_size)
    if not ok:
        if run_role == "FORMAL":
            raise ValueError(f"FORMAL mode: {msg}")
        elif run_role == "PILOT":
            # PILOT default: also fail
            raise ValueError(f"PILOT mode (strict): {msg}")

    selected = samples[:batch_size]
    input_ids = [s["input_ids"] for s in selected]
    attention_masks = [s.get("attention_mask", [1] * fixed_len) for s in selected]

    return {
        "input_ids": input_ids,
        "attention_mask": attention_masks,
        "fixed_input_tokens": fixed_len,
        "batch_size": batch_size,
    }
