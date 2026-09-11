"""S 层 Canonical bundle 与同步 registry 测试。"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from exposedpath_v141.canonical_raw import load_canonical_raw_schema
from exposedpath_v141.sync_semantics import (
    SyncSemanticsError,
    classify_cuda_api,
    load_canonical_bundle,
    load_sync_registry,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_empty_bundle(path: Path) -> Path:
    path.mkdir()
    schema = load_canonical_raw_schema()
    files = {}
    for kind, spec in schema["record_types"].items():
        file_path = path / spec["filename"]
        with file_path.open("xb") as raw_handle:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0):
                pass
        files[kind] = {
            "filename": spec["filename"],
            "record_count": 0,
            "sha256": _sha256(file_path),
            "size_bytes": file_path.stat().st_size,
        }
    manifest = {
        "schema_version": schema["schema_version"],
        "measurement_contract_version": schema["measurement_contract_version"],
        "adapter_id": schema["adapter_id"],
        "analyzer_version": "test",
        "generated_at_utc": "2026-09-11T00:00:00+00:00",
        "data_role": "Engineering",
        "source": {"sqlite": {"sha256": "A" * 64}},
        "clock": schema["clock_model"],
        "identity": {"status": "VALID"},
        "execution_context": {"default_stream_mode": "PER_THREAD", "selected_device_id": 0},
        "files": files,
        "observation_validity": {"status": "valid", "issues": []},
        "research_eligibility": {"formal_evidence": False, "q0_status": "NOT_RUN"},
    }
    manifest_path = path / "canonical_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_canonical_bundle_loader_validates_all_files(tmp_path):
    manifest_path = _write_empty_bundle(tmp_path / "bundle")

    bundle = load_canonical_bundle(manifest_path)

    assert set(bundle["records"]) == set(load_canonical_raw_schema()["record_types"])
    assert all(not rows for rows in bundle["records"].values())


def test_canonical_bundle_rejects_schema_hash_and_count_mismatch(tmp_path):
    manifest_path = _write_empty_bundle(tmp_path / "schema")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "unknown"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SyncSemanticsError, match="schema_version"):
        load_canonical_bundle(manifest_path)

    manifest_path = _write_empty_bundle(tmp_path / "hash")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["cuda_api"]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SyncSemanticsError, match="SHA-256"):
        load_canonical_bundle(manifest_path)

    manifest_path = _write_empty_bundle(tmp_path / "count")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["cuda_api"]["record_count"] = 1
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(SyncSemanticsError, match="记录数"):
        load_canonical_bundle(manifest_path)


@pytest.mark.parametrize(
    ("api_name", "role", "sync_kind", "rule_id"),
    [
        ("cudaStreamSynchronize", "HOST_BLOCKING_SYNC", "STREAM", "SYNC-STREAM-RUNTIME-001"),
        ("cudaStreamSynchronize_v3020", "HOST_BLOCKING_SYNC", "STREAM", "SYNC-STREAM-RUNTIME-001"),
        ("cuCtxSynchronize_v2", "HOST_BLOCKING_SYNC", "CONTEXT", "SYNC-CONTEXT-DRIVER-001"),
        ("cudaStreamWaitEvent", "DEPENDENCY_EDGE", "STREAM_WAIT_EVENT", "EDGE-STREAM-WAIT-EVENT-001"),
        ("cudaEventRecord", "DEPENDENCY_EDGE", "EVENT_RECORD", "EDGE-EVENT-RECORD-001"),
        ("cudaEventQuery", "NON_SYNC", "QUERY", "NON-SYNC-QUERY-001"),
        ("cudaMemcpy", "UNSUPPORTED", "SYNCHRONOUS_COPY_OR_IMPLICIT_BLOCK", "SYNC-COPY-IMPLICIT-001"),
        ("mysteryCudaWait", "UNCLASSIFIED", None, None),
    ],
)
def test_registry_classification_uses_runtime_api_name(api_name, role, sync_kind, rule_id):
    result = classify_cuda_api(api_name, load_sync_registry())

    assert result["role"] == role
    assert result["sync_kind"] == sync_kind
    assert result["registry_rule_id"] == rule_id
    assert result["original_api_name"] == api_name
