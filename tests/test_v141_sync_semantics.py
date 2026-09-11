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
    build_semantic_inventory,
    classify_cuda_api,
    load_canonical_bundle,
    load_sync_registry,
    ownership_supported,
    submission_evidence,
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


def _identity(phase: str, request_id: str = "req-0", repeat_id: str = "r0") -> dict:
    return {
        "kind": "phase",
        "experiment_id": "exp",
        "wmpc_id": "w01",
        "run_id": "run-1",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": request_id,
        "repeat_id": repeat_id,
        "phase": phase,
    }


def _nvtx(record_id: str, start: int, end: int, phase: str, **identity_updates) -> dict:
    identity = _identity(phase)
    identity.update(identity_updates)
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "global_tid": 1001,
        "structured_identity": identity,
    }


def _api(record_id: str = "api:1", correlation_id: int = 7, start: int = 20, end: int = 30) -> dict:
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "global_tid": 1001,
        "correlation_id": correlation_id,
        "api_name": "cudaLaunchKernel",
    }


def _activity(record_id: str = "activity:1", correlation_id: int = 7, start: int = 40) -> dict:
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": start + 20,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "device_id": 0,
        "context_id": 1,
        "stream_id": 2,
        "correlation_id": correlation_id,
        "activity_kind": "KERNEL",
        "name": "kernel",
    }


def _sync(start: int = 50, end: int = 80, phase: str = "decode", **updates) -> dict:
    result = {
        "record_id": "sync:1",
        "runtime_record_id": "api:sync",
        "runtime_start_ns": start,
        "runtime_end_ns": end,
        "runtime_global_tid": 1001,
        "runtime_api_name": "cudaStreamSynchronize",
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "device_id": 0,
        "context_id": 1,
        "stream_id": 2,
        "event_id": None,
        "expected_phase": phase,
    }
    result.update(updates)
    return result


def _bundle(*, nvtx, cuda_api, activities, syncs, identity_status="VALID") -> dict:
    return {
        "manifest": {
            "identity": {"status": identity_status, "issues": []},
            "observation_validity": {"status": "valid", "issues": []},
            "clock": {"clock_domain_id": "NSYS_TRACE_RELATIVE_NS"},
            "execution_context": {"default_stream_mode": "PER_THREAD", "selected_device_id": 0},
        },
        "records": {
            "nvtx": nvtx,
            "cuda_api": cuda_api,
            "cuda_sync": syncs,
            "device_activity": activities,
            "cuda_event": [],
            "context": [],
            "stream": [],
            "diagnostic": [],
        },
    }


def test_inventory_resolves_unique_enqueue_and_innermost_structured_phase():
    bundle = _bundle(
        nvtx=[_nvtx("range:req", 0, 100, "full_request"), _nvtx("range:prefill", 10, 45, "prefill")],
        cuda_api=[_api()],
        activities=[_activity()],
        syncs=[],
    )

    inventory = build_semantic_inventory(bundle)

    activity = inventory["activities"][0]
    assert activity["enqueue_record_id"] == "api:1"
    assert activity["request_id"] == "req-0"
    assert activity["repeat_id"] == "r0"
    assert activity["origin_phase"] == "prefill"
    assert activity["ownership_status"] == "VALID"


@pytest.mark.parametrize(
    ("cuda_api", "expected_reason"),
    [
        ([], "MISSING_ACTIVITY_CORRELATION"),
        ([_api("api:1"), _api("api:2")], "MISSING_ACTIVITY_CORRELATION"),
    ],
)
def test_activity_requires_exactly_one_correlated_enqueue(cuda_api, expected_reason):
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[_nvtx("range:req", 0, 100, "full_request")],
            cuda_api=cuda_api,
            activities=[_activity()],
            syncs=[],
        )
    )

    activity = inventory["activities"][0]
    assert activity["ownership_status"] == "INVALID"
    assert activity["ownership_reasons"] == [expected_reason]


def test_conflicting_phase_ranges_are_ambiguous_and_missing_identity_is_invalid():
    conflicting = build_semantic_inventory(
        _bundle(
            nvtx=[
                _nvtx("range:a", 0, 100, "decode"),
                _nvtx("range:b", 0, 100, "prefill", request_id="req-1"),
            ],
            cuda_api=[_api()],
            activities=[_activity()],
            syncs=[],
        )
    )["activities"][0]
    missing = build_semantic_inventory(
        _bundle(nvtx=[], cuda_api=[_api()], activities=[_activity()], syncs=[])
    )["activities"][0]

    assert conflicting["ownership_status"] == "AMBIGUOUS"
    assert conflicting["ownership_reasons"] == ["INVOCATION_OWNERSHIP_AMBIGUOUS"]
    assert missing["ownership_status"] == "INVALID"
    assert missing["ownership_reasons"] == ["INVOCATION_BOUNDARY_INVALID"]


def test_manifest_identity_problem_is_propagated_before_local_ownership():
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[_nvtx("range:req", 0, 100, "full_request")],
            cuda_api=[_api()],
            activities=[_activity()],
            syncs=[],
            identity_status="AMBIGUOUS",
        )
    )

    assert inventory["input_status"] == "AMBIGUOUS"
    assert inventory["input_reasons"] == ["INVOCATION_OWNERSHIP_AMBIGUOUS"]


def test_sync_ownership_uses_runtime_interval_and_preserves_cross_phase_candidate():
    sync = _sync(start=55, end=75)
    bundle = _bundle(
        nvtx=[
            _nvtx("range:req", 0, 100, "full_request"),
            _nvtx("range:prefill", 10, 45, "prefill"),
            _nvtx("range:decode", 45, 100, "decode"),
        ],
        cuda_api=[_api()],
        activities=[_activity(start=35)],
        syncs=[sync],
    )

    inventory = build_semantic_inventory(bundle)
    activity = inventory["activities"][0]
    normalized_sync = inventory["syncs"][0]
    relation = ownership_supported(activity, normalized_sync)

    assert normalized_sync["host_start_ns"] == 55
    assert normalized_sync["sync_owner_phase"] == "decode"
    assert relation == {"supported": True, "cross_phase_dependency": True, "reason": None}


def test_cross_invocation_bleed_is_not_supported_for_strong_claim():
    activity = {
        "request_id": "req-0", "repeat_id": "r0", "origin_phase": "prefill",
        "ownership_status": "VALID",
        "invocation_identity": _identity("prefill", request_id="req-0"),
    }
    sync = {
        "request_id": "req-0", "repeat_id": "r0", "sync_owner_phase": "decode",
        "ownership_status": "VALID",
        "invocation_identity": _identity("decode", request_id="req-0") | {"run_id": "run-2"},
    }

    assert ownership_supported(activity, sync) == {
        "supported": False,
        "cross_phase_dependency": False,
        "reason": "INVOCATION_BLEED",
    }


@pytest.mark.parametrize(
    ("activity_start", "enqueue_end", "sync_start", "status", "proof"),
    [
        (49, 70, 50, "PROVEN", "GPU_STARTED_BEFORE_SYNC"),
        (70, 50, 50, "PROVEN", "ENQUEUE_COMPLETED_BEFORE_SYNC"),
        (70, 60, 50, "AMBIGUOUS", None),
    ],
)
def test_submission_requires_gpu_start_or_enqueue_end(
    activity_start, enqueue_end, sync_start, status, proof
):
    activity = {
        "start_ns": activity_start,
        "enqueue_start_ns": 10,
        "enqueue_end_ns": enqueue_end,
    }
    sync = {"host_start_ns": sync_start}

    result = submission_evidence(activity, sync)

    assert result["status"] == status
    assert result["proof"] == proof
    assert result["reason"] == (None if status == "PROVEN" else "SUBMISSION_ORDER_AMBIGUOUS")
