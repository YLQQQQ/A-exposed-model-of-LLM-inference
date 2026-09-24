"""
WMPC Manifest loading, validation, and generation.
"""

import json
import os
import platform
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

import torch

from exposedpath.ids import generate_run_id, generate_wmpc_id
from exposedpath.validation import (
    compute_prompt_tokens_sha256,
    validate_manifest_core,
    validate_manifest_wmpc_stability,
    validate_prompt_tokens_sha256_match,
)


def resolve_logical_cuda_index(
    *,
    physical_gpu_index: int,
    cuda_visible_devices: Optional[str],
    declared_logical_index: Optional[int] = None,
) -> int:
    """Map a physical GPU index to its process-local CUDA index.

    This is a pure identity mapping.  It deliberately does not inspect torch
    or device_count because those expose only the process-local CUDA view.
    """
    if physical_gpu_index < 0:
        raise ValueError("physical_gpu_index must be non-negative")
    if declared_logical_index is not None and declared_logical_index < 0:
        raise ValueError("declared_logical_index must be non-negative")

    if cuda_visible_devices is None:
        expected_logical_index = physical_gpu_index
        if (
            declared_logical_index is not None
            and declared_logical_index != expected_logical_index
        ):
            raise ValueError(
                f"logical GPU index {declared_logical_index} conflicts with "
                f"unmasked physical GPU index {physical_gpu_index}"
            )
        return expected_logical_index
    if not cuda_visible_devices.strip():
        raise ValueError("CUDA_VISIBLE_DEVICES does not expose any GPU")

    visible_devices = [item.strip() for item in cuda_visible_devices.split(",")]
    if any(not identity for identity in visible_devices):
        raise ValueError(f"CUDA_VISIBLE_DEVICES is malformed: {cuda_visible_devices!r}")
    physical_identity = str(physical_gpu_index)
    matches = [index for index, identity in enumerate(visible_devices) if identity == physical_identity]
    if len(matches) == 1:
        expected_logical_index = matches[0]
        if (
            declared_logical_index is not None
            and declared_logical_index != expected_logical_index
        ):
            raise ValueError(
                f"logical GPU index {declared_logical_index} conflicts with "
                f"physical GPU index {physical_gpu_index} mapped to "
                f"logical index {expected_logical_index}"
            )
        return expected_logical_index
    if len(matches) > 1:
        raise ValueError(
            f"physical GPU index {physical_gpu_index} is not uniquely visible in "
            f"CUDA_VISIBLE_DEVICES={cuda_visible_devices!r}"
        )
    if all(identity.isdecimal() for identity in visible_devices):
        raise ValueError(
            f"physical GPU index {physical_gpu_index} is not visible in "
            f"CUDA_VISIBLE_DEVICES={cuda_visible_devices!r}"
        )
    if not all(identity.startswith(("GPU-", "MIG-")) for identity in visible_devices):
        raise ValueError(f"CUDA_VISIBLE_DEVICES is malformed: {cuda_visible_devices!r}")
    if declared_logical_index is None or declared_logical_index >= len(visible_devices):
        raise ValueError(
            f"physical GPU index {physical_gpu_index} cannot be mapped uniquely from "
            f"CUDA_VISIBLE_DEVICES={cuda_visible_devices!r}"
        )
    return declared_logical_index


def create_manifest(
    *,
    experiment_id: str,
    run_role: str,
    model_path: str,
    prompt_tokens_file: str,
    batch_size: int,
    fixed_output_tokens: int,
    warmup_count: int = 5,
    repeat_count: int = 10,
    gpu: int = 0,
    gpu_index_physical: Optional[int] = None,
    gpu_index_logical: Optional[int] = None,
    gpu_uuid: Optional[str] = None,
    gpu_pci_bus_id: Optional[str] = None,
    gpu_name: Optional[str] = None,
    clock_policy: str = "DEFAULT_DYNAMIC",
    clock_control_requested: bool = False,
    clock_control_applied: bool = False,
    clock_control_status: str = "NOT_REQUESTED",
    clock_causality_status: str = "NOT_EVALUATED",
    clock_preflight_required: bool = False,
    environment_sharing_mode: str = "SHARED",
    data_role: str = "PILOT",
    study_mode: str = "G1_NATURAL",
    n1_intervention: Optional[Dict] = None,
    eligible_for_final_statistics: bool = False,
    sampling_config: Optional[Dict] = None,
    model_revision: str = "unknown",
    output_root: str = ".",
    # Fields user must fill manually if not auto-detected:
    cpu_model: Optional[str] = None,
    cpu_affinity_spec: Optional[str] = None,
    numa_binding_policy: Optional[str] = None,
    framework_threading_config: Optional[str] = None,
    gpu_power_persistence_policy: Optional[str] = None,
    external_cuda_workload_policy: Optional[str] = None,
    require_git_identity: bool = False,
    git_worktree: Optional[Path] = None,
) -> Dict:
    """Create a new WMPC manifest dict from auto-detected + user-provided values.

    The caller is responsible for saving the manifest to disk and computing
    the wmpc_id after filling in any unknown fields.
    Gate7 passes require_git_identity=True and an explicit git_worktree: query
    errors then propagate with their original reason instead of becoming null.
    """
    # ---- Hardware auto-detect ----
    physical_gpu_index = gpu if gpu_index_physical is None else gpu_index_physical
    logical_gpu_index = resolve_logical_cuda_index(
        physical_gpu_index=physical_gpu_index,
        cuda_visible_devices=os.environ.get("CUDA_VISIBLE_DEVICES"),
        declared_logical_index=gpu_index_logical,
    )
    detected_gpu_name = (
        gpu_name
        if gpu_name is not None
        else torch.cuda.get_device_name(logical_gpu_index)
        if torch.cuda.is_available()
        else "unknown"
    )
    cuda_ver = torch.version.cuda or "unknown"
    torch_ver = torch.__version__

    try:
        import transformers
        tf_ver = transformers.__version__
    except ImportError:
        tf_ver = "unknown"

    # Attempt to read model config
    model_config = _read_model_config(model_path)

    manifest: Dict = {
        # ---- W ----
        "prompt_tokens_file": str(Path(prompt_tokens_file).resolve()),
        "fixed_input_tokens": None,  # filled from prompt_tokens
        "fixed_output_tokens": fixed_output_tokens,
        "batch_size": batch_size,
        "sampling_config": sampling_config or {"do_sample": False},

        # ---- M ----
        "model_id": str(Path(model_path).resolve()),
        "revision": model_revision,
        "model_type": model_config.get("model_type", "unknown"),
        "dtype_and_quantization": "fp16",
        "num_parameters": model_config.get("num_parameters"),
        "num_hidden_layers": model_config.get("num_hidden_layers"),
        "hidden_size": model_config.get("hidden_size"),
        "num_attention_heads": model_config.get("num_attention_heads"),
        "num_key_value_heads": model_config.get("num_key_value_heads"),
        "intermediate_size": model_config.get("intermediate_size"),
        "max_position_embeddings": model_config.get("max_position_embeddings"),

        # ---- P ----
        "cpu_model": cpu_model or platform.processor() or "unknown",
        "gpu_model": detected_gpu_name,
        "platform_snapshot_file": None,

        # ---- C ----
        "os_distribution_version": platform.platform() or "unknown",
        "nvidia_driver_version": _get_nvidia_driver(),
        "cuda_version_used": cuda_ver,
        "inference_framework_version": f"torch{torch_ver}",
        "runtime_version": f"python{platform.python_version()}",
        "attention_backend": "sdpa",
        "execution_mode": "eager",

        # ---- Run control ----
        "experiment_id": experiment_id,
        "wmpc_id": None,  # computed after prompt_tokens loaded
        "run_id": generate_run_id(),
        "run_role": run_role,
        "study_mode": study_mode,
        "n1_intervention": n1_intervention,
        "gpu": gpu,
        "gpu_index": physical_gpu_index,
        "gpu_index_physical": physical_gpu_index,
        "gpu_index_logical": logical_gpu_index,
        "gpu_uuid": gpu_uuid,
        "gpu_pci_bus_id": gpu_pci_bus_id,
        "gpu_name": detected_gpu_name,
        "clock_policy": clock_policy,
        "clock_control_requested": clock_control_requested,
        "clock_control_applied": clock_control_applied,
        "clock_control_status": clock_control_status,
        "clock_causality_status": clock_causality_status,
        "clock_preflight_required": clock_preflight_required,
        "environment_sharing_mode": environment_sharing_mode,
        "data_role": data_role,
        "eligible_for_final_statistics": eligible_for_final_statistics,
        "warmup_count": warmup_count,
        "repeat_count": repeat_count,
        "cpu_affinity_spec": cpu_affinity_spec,
        "numa_binding_policy": numa_binding_policy,
        "framework_threading_config": framework_threading_config,
        "gpu_power_persistence_policy": gpu_power_persistence_policy,
        "external_cuda_workload_policy": external_cuda_workload_policy,

        # ---- Runner metadata ----
        "runner_git_commit": _get_git_commit(required=require_git_identity, worktree=git_worktree),
        "runner_git_dirty": _get_git_dirty(required=require_git_identity, worktree=git_worktree),
        "pass0_command": None,
        "pass1_nsys_command": None,
    }
    return manifest


def finalize_manifest(manifest: Dict, prompt_tokens_data: Dict, prompt_tokens_path: Optional[Path] = None) -> Dict:
    """Fill in remaining fields from prompt_tokens and compute wmpc_id.

    If *prompt_tokens_path* is provided, computes and stores the real
    SHA-256 of that file.  Otherwise the caller must set
    ``prompt_tokens_sha256`` themselves.
    """
    manifest["fixed_input_tokens"] = prompt_tokens_data["fixed_input_tokens"]

    if prompt_tokens_path is not None and prompt_tokens_path.is_file():
        manifest["prompt_tokens_sha256"] = compute_prompt_tokens_sha256(prompt_tokens_path)
    elif "prompt_tokens_sha256" not in manifest or manifest["prompt_tokens_sha256"] is None:
        # Don't write a placeholder — the validator will reject it
        manifest["prompt_tokens_sha256"] = None

    manifest["wmpc_id"] = generate_wmpc_id(manifest)
    return manifest


def save_manifest(manifest: Dict, output_path: Path) -> None:
    """Save manifest to disk as JSON using atomic write (write-temp-then-rename).

    The caller is responsible for ensuring prompt_tokens_sha256 is a real
    hash — this function does not fill placeholders.
    """
    output_path = output_path.resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = json.dumps(manifest, indent=2, ensure_ascii=False, default=str)

    # Atomic write: write to a temp file in the same directory, then rename
    tmp_fd, tmp_path = tempfile.mkstemp(
        suffix=".json",
        prefix=".wmpc_manifest_",
        dir=str(output_path.parent),
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, str(output_path))  # atomic on Windows + POSIX
    except BaseException:
        # Clean up temp file on failure
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise


def load_manifest(path: Path) -> Dict:
    """Load and validate a manifest JSON file (structure only, no SHA-256 check)."""
    if not path.is_file():
        raise FileNotFoundError(f"Manifest file not found: {path}")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {path}: {e}")

    errors = validate_manifest_core(data)
    if errors:
        raise ValueError(f"Manifest validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    return data


def update_prompt_sha(manifest_path: Path) -> Dict:
    """Load manifest, recompute prompt_tokens_sha256 from the referenced file, and save atomically.

    Returns the updated manifest dict.
    """
    manifest = load_manifest(manifest_path)

    pt_path_str = manifest.get("prompt_tokens_file")
    if not pt_path_str:
        raise ValueError("Manifest has no prompt_tokens_file field")
    pt_path = Path(pt_path_str)
    if not pt_path.is_file():
        raise FileNotFoundError(f"prompt_tokens file not found: {pt_path}")

    new_sha = compute_prompt_tokens_sha256(pt_path)
    manifest["prompt_tokens_sha256"] = new_sha
    save_manifest(manifest, manifest_path)
    return manifest


# ---- Helpers ----

def _read_model_config(model_path: str) -> Dict:
    """Try to read config.json from a local model directory."""
    try:
        config_path = Path(model_path) / "config.json"
        if config_path.is_file():
            raw = json.loads(config_path.read_text(encoding="utf-8"))
            return {
                "model_type": raw.get("model_type", "unknown"),
                "num_parameters": None,  # not reliably in config.json
                "num_hidden_layers": raw.get("num_hidden_layers"),
                "hidden_size": raw.get("hidden_size"),
                "num_attention_heads": raw.get("num_attention_heads"),
                "num_key_value_heads": raw.get("num_key_value_heads"),
                "intermediate_size": raw.get("intermediate_size"),
                "max_position_embeddings": raw.get("max_position_embeddings"),
            }
    except Exception:
        pass
    return {}


def _get_nvidia_driver() -> str:
    """Try to get NVIDIA driver version via nvidia-smi."""
    from exposedpath import platform_adapter

    try:
        out = platform_adapter.nvidia_smi(
            ["--query-gpu=driver_version", "--format=csv,noheader"], timeout=10,
        )
        return out.strip().split("\n")[0].strip()
    except Exception:
        return "unknown"


def _get_git_commit(*, required=False, worktree=None) -> Optional[str]:
    """Get current git commit hash."""
    from exposedpath import platform_adapter

    try:
        prefix = ["-C", str(worktree)] if worktree is not None else []
        out = platform_adapter.git([*prefix, "rev-parse", "HEAD"], timeout=5)
        return out.strip()
    except Exception:
        if required:
            raise
        return None


def _get_git_dirty(*, required=False, worktree=None) -> Optional[bool]:
    """Check if git working tree is dirty."""
    from exposedpath import platform_adapter

    try:
        prefix = ["-C", str(worktree)] if worktree is not None else []
        out = platform_adapter.git([*prefix, "status", "--porcelain"], timeout=5)
        return len(out.strip()) > 0
    except Exception:
        if required:
            raise
        return None
