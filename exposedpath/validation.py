"""
Validation helpers for prompt_tokens, manifest, and directory rules.
"""

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---- SHA-256 constants ----

SHA256_HEX_PATTERN = re.compile(r"^[a-f0-9]{64}$")
PLACEHOLDER_SHA_VALUES = {"placeholder", "", "unknown", "none", "null", "undefined"}


def validate_sha256_string(sha: Optional[str]) -> Optional[str]:
    """Validate a SHA-256 hex string. Returns error message or None if valid."""
    if sha is None:
        return "prompt_tokens_sha256 is missing (null)"
    if not isinstance(sha, str):
        return f"prompt_tokens_sha256 must be a string, got {type(sha).__name__}"
    stripped = sha.strip().lower()
    if not stripped:
        return "prompt_tokens_sha256 is empty"
    if stripped in PLACEHOLDER_SHA_VALUES:
        return f"prompt_tokens_sha256 is a placeholder: '{sha}'"
    if not SHA256_HEX_PATTERN.match(stripped):
        return f"prompt_tokens_sha256 is not a valid 64-character hex string: '{sha[:32]}...'"
    return None


def validate_prompt_tokens_sha256_match(manifest: Dict) -> Optional[str]:
    """Verify that the manifest's prompt_tokens_sha256 matches the actual file.

    Returns an error message, or None if valid.
    """
    sha = manifest.get("prompt_tokens_sha256")
    # --- Step 1: Validate the SHA-256 string itself ---
    err = validate_sha256_string(sha)
    if err:
        return err

    # --- Step 2: Check file exists ---
    pt_path_str = manifest.get("prompt_tokens_file")
    if not pt_path_str:
        return "prompt_tokens_file is not set in manifest"
    pt_path = Path(pt_path_str)
    if not pt_path.is_file():
        return f"prompt_tokens file not found: {pt_path}"

    # --- Step 3: Compute and compare ---
    actual = compute_prompt_tokens_sha256(pt_path)
    expected = sha.strip().lower()
    if actual != expected:
        return (
            f"prompt_tokens_sha256 mismatch:\n"
            f"  manifest says: {expected}\n"
            f"  actual file:   {actual}\n"
            f"  file: {pt_path}"
        )
    return None


# ---- prompt_tokens validation ----

def validate_prompt_tokens(data: Dict) -> List[str]:
    """Validate prompt_tokens.json structure. Returns list of error messages (empty = valid)."""
    errors: List[str] = []

    # Required top-level fields
    for key in ["schema_version", "tokenizer_id", "fixed_input_tokens", "samples"]:
        if key not in data:
            errors.append(f"Missing required field: {key}")

    if "samples" not in data:
        return errors

    samples = data["samples"]
    if not isinstance(samples, list):
        errors.append(f"'samples' must be a list, got {type(samples).__name__}")
        return errors

    if len(samples) == 0:
        errors.append("'samples' must contain at least 1 sample")
        return errors

    fixed_len = data.get("fixed_input_tokens")
    if not isinstance(fixed_len, int) or fixed_len <= 0:
        errors.append(f"'fixed_input_tokens' must be a positive integer, got {fixed_len}")
        return errors

    for i, sample in enumerate(samples):
        if not isinstance(sample, dict):
            errors.append(f"sample[{i}]: must be a dict, got {type(sample).__name__}")
            continue
        if "input_ids" not in sample:
            errors.append(f"sample[{i}]: missing 'input_ids'")
            continue
        ids = sample["input_ids"]
        if not isinstance(ids, list):
            errors.append(f"sample[{i}].input_ids: must be a list")
            continue
        if len(ids) != fixed_len:
            errors.append(
                f"sample[{i}].input_ids: length {len(ids)} != fixed_input_tokens {fixed_len}"
            )
        for j, tid in enumerate(ids):
            if not isinstance(tid, int) or tid < 0:
                errors.append(f"sample[{i}].input_ids[{j}]: must be non-negative integer, got {tid}")
                break

        # attention_mask optional, defaults to all-1
        am = sample.get("attention_mask")
        if am is not None:
            if not isinstance(am, list):
                errors.append(f"sample[{i}].attention_mask: must be a list")
            elif len(am) != fixed_len:
                errors.append(
                    f"sample[{i}].attention_mask: length {len(am)} != fixed_input_tokens {fixed_len}"
                )

    return errors


def check_batch_sample_distinctness(samples: List[Dict], batch_size: int) -> Tuple[bool, str]:
    """Check that the first batch_size samples are distinct (not clones of each other).

    Returns (ok, message).
    """
    if batch_size <= 1:
        return True, "batch_size <= 1, distinctness check skipped"
    if len(samples) < batch_size:
        return False, f"only {len(samples)} samples available, need {batch_size}"

    selected = samples[:batch_size]
    for i in range(batch_size):
        for j in range(i + 1, batch_size):
            ids_i = selected[i].get("input_ids", [])
            ids_j = selected[j].get("input_ids", [])
            if ids_i == ids_j:
                return False, (
                    f"sample[{i}] and sample[{j}] have identical input_ids. "
                    f"Each sample in a batch must be distinct. "
                    f"Do not clone a single sample to pad batch_size."
                )
    return True, "all batch samples are distinct"


def compute_prompt_tokens_sha256(file_path: Path) -> str:
    """Compute SHA-256 of a prompt_tokens.json file."""
    content = file_path.read_bytes()
    return hashlib.sha256(content).hexdigest()


def apply_default_attention_mask(samples: List[Dict], fixed_input_tokens: int) -> None:
    """Fill missing attention_mask with all-1 tensors (list form)."""
    for sample in samples:
        if "attention_mask" not in sample or sample["attention_mask"] is None:
            sample["attention_mask"] = [1] * fixed_input_tokens


# ---- directory safety ----

def ensure_dir_empty_or_new(path: Path) -> None:
    """Raise FileExistsError if path exists and is non-empty."""
    if path.exists():
        if path.is_dir():
            contents = list(path.iterdir())
            if contents:
                raise FileExistsError(
                    f"Directory exists and is not empty: {path}. "
                    f"Cannot overwrite existing run data. Use a new run_id."
                )
        else:
            raise FileExistsError(f"Path exists and is not a directory: {path}")


# ---- manifest validation ----

MANIFEST_REQUIRED_CORE = [
    # W
    "fixed_input_tokens",
    "fixed_output_tokens",
    "batch_size",
    # M
    "model_id",
    "dtype_and_quantization",
    # P
    "gpu_model",
    # C
    "cuda_version_used",
    "inference_framework_version",
    "execution_mode",
    # run control
    "experiment_id",
    "wmpc_id",
    "run_id",
    "run_role",
    "study_mode",
    "warmup_count",
    "repeat_count",
]

MANIFEST_REQUIRED_PATHS = [
    "prompt_tokens_file",
]


def validate_manifest_core(manifest: Dict) -> List[str]:
    """Check manifest has all required core fields (non-empty)."""
    errors: List[str] = []
    for key in MANIFEST_REQUIRED_CORE:
        if key not in manifest or manifest[key] is None:
            errors.append(f"Manifest missing required field: {key}")
    for key in MANIFEST_REQUIRED_PATHS:
        if key not in manifest or not manifest[key]:
            errors.append(f"Manifest missing required path field: {key}")
    errors.extend(validate_study_mode(manifest))
    return errors


def validate_study_mode(manifest: Dict) -> List[str]:
    """Fail closed on mixed or incomplete G1/N1 run-mode identity."""
    if "study_mode" not in manifest:
        return []  # validate_manifest_core reports the required-field error.
    mode = manifest.get("study_mode")
    intervention = manifest.get("n1_intervention")
    if not isinstance(mode, str):
        return ["study_mode must be one string"]
    if mode == "G1_NATURAL":
        if intervention is not None:
            return ["G1_NATURAL forbids n1_intervention configuration"]
        return []
    if mode == "N1_INTERVENTION":
        if not isinstance(intervention, dict):
            return ["N1_INTERVENTION requires n1_intervention configuration"]
        required = ("intervention_variant_id", "callsite_id")
        missing = [field for field in required if not intervention.get(field)]
        if missing:
            return [
                "N1_INTERVENTION requires n1_intervention fields: "
                + ", ".join(missing)
            ]
        if intervention.get("sync_origin") != "n1_intervention":
            return ["N1_INTERVENTION requires sync_origin=n1_intervention"]
        return []
    return [f"unsupported study_mode: {mode}"]


def validate_manifest_wmpc_stability(manifest: Dict) -> Optional[str]:
    """Verify wmpc_id matches the current W/M/P/C fields. Returns None if ok, error msg otherwise."""
    from exposedpath.ids import generate_wmpc_id
    expected = generate_wmpc_id(manifest)
    actual = manifest.get("wmpc_id")
    if actual and actual != expected:
        return f"wmpc_id mismatch: manifest says '{actual}', computed '{expected}'"
    if not actual:
        return "wmpc_id is missing from manifest"
    return None
