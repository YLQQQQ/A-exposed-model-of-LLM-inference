"""Regression coverage for physical-to-logical CUDA device identity."""

from __future__ import annotations

from pathlib import Path

import pytest

from exposedpath import manifest


SMOKE_SCRIPT = (
    Path(__file__).resolve().parent.parent / "scripts" / "run_server_smoke_test.ps1"
)


def test_resolver_maps_single_visible_physical_gpu_to_logical_zero():
    resolver = getattr(manifest, "resolve_logical_cuda_index", None)
    assert resolver is not None, "manifest must expose the shared pure CUDA index resolver"
    assert resolver(physical_gpu_index=3, cuda_visible_devices="3") == 0


def test_resolver_rejects_explicit_empty_visible_device_mask():
    with pytest.raises(ValueError, match="does not expose any GPU"):
        manifest.resolve_logical_cuda_index(
            physical_gpu_index=3,
            cuda_visible_devices="",
        )


@pytest.mark.parametrize("mask", ["-1", "garbage", "4,GPU-test-uuid"])
def test_resolver_rejects_invalid_or_mixed_opaque_masks(mask):
    with pytest.raises(ValueError, match="malformed"):
        manifest.resolve_logical_cuda_index(
            physical_gpu_index=3,
            cuda_visible_devices=mask,
            declared_logical_index=0,
        )


def test_manifest_queries_logical_gpu_but_preserves_physical_identity(monkeypatch):
    queried_indices = []
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "3")
    monkeypatch.setattr(manifest.torch.cuda, "is_available", lambda: True)
    monkeypatch.setattr(
        manifest.torch.cuda,
        "get_device_name",
        lambda index: queried_indices.append(index) or "NVIDIA GeForce RTX 4090",
    )
    monkeypatch.setattr(manifest, "_read_model_config", lambda _path: {})
    monkeypatch.setattr(manifest, "_get_nvidia_driver", lambda: "test-driver")
    monkeypatch.setattr(manifest, "_get_git_commit", lambda **kwargs: "test-commit")
    monkeypatch.setattr(manifest, "_get_git_dirty", lambda **kwargs: False)

    result = manifest.create_manifest(
        experiment_id="gpu-index-regression",
        run_role="PILOT",
        model_path="test-model",
        prompt_tokens_file="prompt_tokens.json",
        batch_size=1,
        fixed_output_tokens=1,
        gpu=3,
    )

    assert queried_indices == [0]
    assert result["gpu"] == 3
    assert result["gpu_index"] == 3
    assert result["gpu_index_physical"] == 3
    assert result["gpu_index_logical"] == 0
    assert result["gpu_name"] == "NVIDIA GeForce RTX 4090"


def test_explicit_physical_identity_controls_manifest_gpu_index(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "GPU-test-uuid")
    monkeypatch.setattr(manifest, "_read_model_config", lambda _path: {})
    monkeypatch.setattr(manifest, "_get_nvidia_driver", lambda: "test-driver")
    monkeypatch.setattr(manifest, "_get_git_commit", lambda **kwargs: "test-commit")
    monkeypatch.setattr(manifest, "_get_git_dirty", lambda **kwargs: False)

    result = manifest.create_manifest(
        experiment_id="explicit-gpu-identities",
        run_role="PILOT",
        model_path="test-model",
        prompt_tokens_file="prompt_tokens.json",
        batch_size=1,
        fixed_output_tokens=1,
        gpu=0,
        gpu_index_physical=3,
        gpu_index_logical=0,
        gpu_name="NVIDIA GeForce RTX 4090",
    )

    assert result["gpu"] == 0
    assert result["gpu_index"] == 3
    assert result["gpu_index_physical"] == 3
    assert result["gpu_index_logical"] == 0


def test_manifest_rejects_logical_index_that_conflicts_with_numeric_mask(monkeypatch):
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "3")

    with pytest.raises(ValueError, match="logical GPU index 1 conflicts"):
        manifest.create_manifest(
            experiment_id="conflicting-gpu-identities",
            run_role="PILOT",
            model_path="test-model",
            prompt_tokens_file="prompt_tokens.json",
            batch_size=1,
            fixed_output_tokens=1,
            gpu=3,
            gpu_index_physical=3,
            gpu_index_logical=1,
            gpu_name="NVIDIA GeForce RTX 4090",
        )


def test_smoke_cuda_check_and_manifest_use_shared_resolver():
    source = SMOKE_SCRIPT.read_text(encoding="utf-8")
    shared_import = (
        "from exposedpath.manifest import create_manifest, finalize_manifest, "
        "resolve_logical_cuda_index, save_manifest"
    )

    assert source.count("resolve_logical_cuda_index") >= 3
    assert shared_import in source
    assert "torch.cuda.get_device_name($GpuId)" not in source
    assert '$cuda_check_script = Join-Path $LogDir "07_cuda_check.py"' in source
    assert '@("-c",$cuda_code)' not in source
    assert "$a = @('\"' + $cuda_check_script + '\"')" in source
