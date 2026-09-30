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
    analyze_semantic_inventory,
    analyze_sync_semantics,
    build_semantic_inventory,
    classify_cuda_api,
    load_canonical_bundle,
    load_sync_registry,
    ownership_supported,
    recover_wait_set,
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


def _activity_marker(
    record_id: str,
    start: int,
    end: int,
    phase: str = "decode",
    *,
    global_tid: int = 2002,
    callsite_id: str = "KERNEL_A",
    **identity_updates,
) -> dict:
    identity = _identity(phase)
    identity.update(kind="marker", callsite_id=callsite_id)
    identity.update(identity_updates)
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "global_tid": global_tid,
        "text": "EXPOSEDPATH_JSON_V1:" + json.dumps(identity, sort_keys=True),
        "structured_identity": identity,
    }


def _sync_nvtx(record_id: str, start: int, end: int, phase: str = "decode") -> dict:
    identity = _identity(phase)
    identity.update(
        kind="sync", callsite_id="decode.token_ready",
        sync_origin="natural_token_ready", sync_ordinal=0,
    )
    return {
        "record_id": record_id, "start_ns": start, "end_ns": end,
        "global_tid": 1001, "structured_identity": identity,
        "text": "EXPOSEDPATH_JSON_V1:" + json.dumps(identity, sort_keys=True),
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


def _bundle(
    *, nvtx, cuda_api, activities, syncs, identity_status="VALID", cuda_events=None,
    contexts=None, streams=None
) -> dict:
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
            "cuda_event": cuda_events or [],
            "context": contexts or [],
            "stream": streams or [],
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


def test_activity_marker_on_enqueue_thread_proves_cross_thread_phase_ownership():
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    bundle = _bundle(
        nvtx=[
            _nvtx("range:req", 0, 100, "full_request"),
            _nvtx("range:decode", 10, 90, "decode"),
            _activity_marker("marker:kernel", 15, 35),
        ],
        cuda_api=[worker_api],
        activities=[_activity()],
        syncs=[],
    )

    activity = build_semantic_inventory(bundle)["activities"][0]

    assert activity["ownership_status"] == "VALID"
    assert activity["request_id"] == "req-0"
    assert activity["origin_phase"] == "decode"
    assert activity["ownership_range_record_ids"] == ["marker:kernel"]


def test_cross_thread_activity_marker_can_feed_existing_stream_wait_set_semantics():
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    bundle = _bundle(
        nvtx=[
            _nvtx("range:req", 0, 120, "full_request"),
            _nvtx("range:decode", 10, 120, "decode"),
            _activity_marker("marker:kernel", 15, 35),
            _sync_nvtx("marker:sync", 50, 100),
        ],
        cuda_api=[worker_api],
        activities=[_activity(start=40)],
        syncs=[_sync(start=50, end=100)],
    )

    inventory = build_semantic_inventory(bundle)
    result = analyze_sync_semantics(inventory, inventory["syncs"][0])

    assert result["validity"] == "VALID_NONEMPTY"
    assert result["wait_set_activity_ids"] == ["activity:1"]
    assert result["activity_origin_phases"] == {"activity:1": "decode"}


def test_activity_ownership_accepts_nested_markers_only_when_identity_and_phase_agree():
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    # Gate 6 Unified Marker Ownership amendment：marker authority 必须落在 matching
    # request/phase 的 cross-thread temporal containment 内。
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                _nvtx("range:req", 0, 100, "full_request"),
                _nvtx("range:decode", 5, 95, "decode"),
                _activity_marker("marker:outer", 10, 40, callsite_id="WORKER"),
                _activity_marker("marker:inner", 15, 35, callsite_id="KERNEL_A"),
            ],
            cuda_api=[worker_api],
            activities=[_activity()],
            syncs=[],
        )
    )

    activity = inventory["activities"][0]
    assert activity["ownership_status"] == "VALID"
    assert activity["origin_phase"] == "decode"
    assert activity["ownership_range_record_ids"] == ["marker:inner", "marker:outer"]


def test_activity_marker_without_matching_request_range_fails_closed():
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                _nvtx("range:decode", 5, 95, "decode"),
                _activity_marker("marker:kernel", 15, 35),
            ],
            cuda_api=[worker_api],
            activities=[_activity()],
            syncs=[],
        )
    )

    activity = inventory["activities"][0]
    assert activity["ownership_status"] == "INVALID"
    assert activity["ownership_reasons"] == ["INVOCATION_BOUNDARY_INVALID"]


def _request_nvtx(
    record_id: str,
    start: int,
    end: int,
    *,
    kind: str = "request",
    global_tid: int = 1001,
    **identity_updates,
) -> dict:
    identity = _identity("full_request")
    identity.update(kind=kind, **identity_updates)
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "global_tid": global_tid,
        "text": "EXPOSEDPATH_JSON_V1:" + json.dumps(identity, sort_keys=True),
        "structured_identity": identity,
    }


@pytest.mark.parametrize(
    ("marker_interval", "api_interval", "expected_reason"),
    [
        ((25, 40), (26, 38), "INVOCATION_BOUNDARY_INVALID"),
        ((140, 150), (141, 149), "INVOCATION_BOUNDARY_INVALID"),
    ],
)
def test_launch_marker_outside_request_boundary_fails_closed(
    marker_interval, api_interval, expected_reason
):
    marker = _activity_marker(
        "marker:launch", marker_interval[0], marker_interval[1], callsite_id="K_EXTERNAL"
    )
    launch = _api("api:launch", start=api_interval[0], end=api_interval[1])
    launch["global_tid"] = 2002
    bundle = _bundle(
        nvtx=[
            marker,
            _request_nvtx("range:req", 30, 130),
            _nvtx("range:decode", 30, 130, "decode"),
        ],
        cuda_api=[launch],
        activities=[_activity(start=40)],
        syncs=[],
    )

    activity = build_semantic_inventory(bundle)["activities"][0]

    assert activity["ownership_status"] == "INVALID"
    assert activity["ownership_reasons"] == [expected_reason]


def test_launch_marker_before_request_with_activity_in_scope_is_external():
    marker = _activity_marker("marker:external", 10, 20, callsite_id="K_EXTERNAL")
    launch = _api("api:external", start=11, end=19)
    launch["global_tid"] = 2002
    sync_nvtx = _sync_nvtx("marker:sync", 80, 120)
    sync = _sync(start=80, end=120, runtime_api_name="cudaDeviceSynchronize")
    sync_api = _api("api:sync", correlation_id=77, start=80, end=120)
    sync_api["api_name"] = "cudaDeviceSynchronize"
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                marker,
                _request_nvtx("range:req", 30, 130),
                _nvtx("range:decode", 30, 130, "decode"),
                sync_nvtx,
            ],
            cuda_api=[launch, sync_api],
            activities=[_activity(start=40)],
            syncs=[sync],
        )
    )

    activity = inventory["activities"][0]
    assert activity["ownership_status"] == "INVALID"
    assert activity["ownership_reasons"] == ["EXTERNAL_OWNERSHIP_IN_SCOPE"]
    assert activity["origin_phase"] is None

    result = analyze_sync_semantics(inventory, inventory["syncs"][0])
    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "EXTERNAL_OWNERSHIP_IN_SCOPE"
    assert result["wait_set_status"] == "INVALID"
    assert result["wait_set_activity_ids"] == []
    assert result["terminal"] == {
        "status": "INVALID",
        "kind": "NONE",
        "activity_id": None,
        "end_ns": None,
        "clock_domain_id": None,
    }


def test_launch_marker_before_request_without_scope_overlap_is_not_external():
    marker = _activity_marker("marker:completed", 10, 20, callsite_id="K_OLD")
    launch = _api("api:old", start=11, end=19)
    launch["global_tid"] = 2002
    completed = _activity(start=21)
    completed["end_ns"] = 25
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                marker,
                _request_nvtx("range:req", 30, 130),
                _nvtx("range:decode", 30, 130, "decode"),
            ],
            cuda_api=[launch],
            activities=[completed],
            syncs=[],
        )
    )

    activity = inventory["activities"][0]
    assert activity["ownership_status"] == "INVALID"
    assert activity["ownership_reasons"] == ["INVOCATION_BOUNDARY_INVALID"]


def test_launch_marker_with_multiple_matching_requests_is_ambiguous():
    marker = _activity_marker("marker:launch", 10, 20, callsite_id="K_DUP")
    launch = _api("api:launch", start=11, end=19)
    launch["global_tid"] = 2002
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                marker,
                _request_nvtx("range:req-a", 30, 130),
                _request_nvtx("range:req-b", 132, 200),
            ],
            cuda_api=[launch],
            activities=[_activity(start=40)],
            syncs=[],
        )
    )

    activity = inventory["activities"][0]
    assert activity["ownership_status"] == "AMBIGUOUS"
    assert activity["ownership_reasons"] == ["INVOCATION_OWNERSHIP_AMBIGUOUS"]


def test_worker_thread_sync_marker_propagates_ownership_cross_thread():
    sync_marker = _sync_nvtx("marker:worker-sync", 60, 95)
    sync_marker["global_tid"] = 3003
    sync = _sync(start=60, end=95)
    sync["runtime_global_tid"] = 3003
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                _request_nvtx("range:req", 0, 100),
                _nvtx("range:decode", 0, 100, "decode"),
                sync_marker,
            ],
            cuda_api=[],
            activities=[],
            syncs=[sync],
        )
    )

    normalized = inventory["syncs"][0]
    assert normalized["ownership_status"] == "VALID"
    assert normalized["request_id"] == "req-0"
    assert normalized["repeat_id"] == "r0"
    assert normalized["sync_owner_phase"] == "decode"
    assert normalized["sync_origin"] == "natural_token_ready"

    result = analyze_sync_semantics(inventory, normalized)
    assert result["primary_reason"] is None
    assert result["secondary_reasons"] == []
    assert result["validity"] == "VALID_EMPTY"


def test_worker_thread_sync_marker_outside_request_fails_closed():
    sync_marker = _sync_nvtx("marker:worker-sync", 120, 160)
    sync_marker["global_tid"] = 3003
    sync = _sync(start=120, end=160)
    sync["runtime_global_tid"] = 3003
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                _request_nvtx("range:req", 0, 100),
                _nvtx("range:decode", 0, 100, "decode"),
                sync_marker,
            ],
            cuda_api=[],
            activities=[],
            syncs=[sync],
        )
    )

    normalized = inventory["syncs"][0]
    assert normalized["ownership_status"] == "INVALID"
    assert normalized["request_id"] is None
    assert normalized["sync_owner_phase"] is None


def test_event_record_ownership_uses_trusted_marker_inside_request():
    event_marker = _activity_marker(
        "marker:event-record", 20, 30, callsite_id="EVENT_RECORD_THREAD_A"
    )
    event_marker["global_tid"] = 3003
    record_api = _api("api:event-record", correlation_id=8, start=21, end=29)
    record_api["global_tid"] = 3003
    record_api["api_name"] = "cudaEventRecord"
    event = {
        "record_id": "event:1", "correlation_id": 8, "timestamp_ns": 25,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "event_id": 7, "event_sync_id": 70,
    }
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                _request_nvtx("range:req", 0, 100),
                _nvtx("range:decode", 0, 100, "decode"),
                event_marker,
            ],
            cuda_api=[record_api],
            activities=[],
            syncs=[],
            cuda_events=[event],
        )
    )

    normalized = inventory["event_records"][0]
    assert normalized["ownership_status"] == "VALID"
    assert normalized["request_id"] == "req-0"
    assert normalized["host_start_ns"] == 21


@pytest.mark.parametrize(
    ("marker", "expected_status", "expected_reason"),
    [
        (
            _activity_marker("marker:ends-before", 10, 19),
            "INVALID",
            "INVOCATION_BOUNDARY_INVALID",
        ),
        (
            _activity_marker("marker:partial", 25, 35),
            "INVALID",
            "INVOCATION_BOUNDARY_INVALID",
        ),
        (
            _activity_marker("marker:wrong-thread", 10, 40, global_tid=3003),
            "INVALID",
            "INVOCATION_BOUNDARY_INVALID",
        ),
    ],
)
def test_activity_marker_must_be_same_thread_and_fully_cover_enqueue(
    marker, expected_status, expected_reason
):
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002

    activity = build_semantic_inventory(
        _bundle(nvtx=[marker], cuda_api=[worker_api], activities=[_activity()], syncs=[])
    )["activities"][0]

    assert activity["ownership_status"] == expected_status
    assert activity["ownership_reasons"] == [expected_reason]


@pytest.mark.parametrize("fault", ["missing_identity", "text_mismatch"])
def test_covering_incomplete_activity_marker_fails_closed_even_with_valid_marker(fault):
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    invalid = _activity_marker("marker:invalid", 10, 40, callsite_id="BAD")
    if fault == "missing_identity":
        invalid["structured_identity"].pop("repeat_id")
        invalid["text"] = "EXPOSEDPATH_JSON_V1:" + json.dumps(
            invalid["structured_identity"], sort_keys=True
        )
    else:
        payload = dict(invalid["structured_identity"])
        payload["request_id"] = "spoofed-request"
        invalid["text"] = "EXPOSEDPATH_JSON_V1:" + json.dumps(payload, sort_keys=True)

    activity = build_semantic_inventory(
        _bundle(
            nvtx=[_activity_marker("marker:valid", 15, 35), invalid],
            cuda_api=[worker_api],
            activities=[_activity()],
            syncs=[],
        )
    )["activities"][0]

    assert activity["ownership_status"] == "INVALID"
    assert activity["ownership_reasons"] == ["INVOCATION_BOUNDARY_INVALID"]


@pytest.mark.parametrize("fault", ["unclosed_before", "unclosed_inside", "partial_overlap"])
def test_temporally_incomplete_activity_marker_fails_closed_even_with_valid_marker(fault):
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    invalid = _activity_marker("marker:invalid-time", 10, 40, callsite_id="BAD")
    if fault == "unclosed_before":
        invalid["end_ns"] = None
    elif fault == "unclosed_inside":
        invalid["start_ns"] = 25
        invalid["end_ns"] = None
    else:
        invalid["start_ns"] = 25

    activity = build_semantic_inventory(
        _bundle(
            nvtx=[_activity_marker("marker:valid", 15, 35), invalid],
            cuda_api=[worker_api],
            activities=[_activity()],
            syncs=[],
        )
    )["activities"][0]

    assert activity["ownership_status"] == "INVALID"
    assert activity["ownership_reasons"] == ["INVOCATION_BOUNDARY_INVALID"]


def test_covering_activity_markers_with_conflicting_invocations_are_ambiguous():
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    activity = build_semantic_inventory(
        _bundle(
            nvtx=[
                _activity_marker("marker:target", 10, 40),
                _activity_marker("marker:other", 15, 35, request_id="req-other"),
            ],
            cuda_api=[worker_api],
            activities=[_activity()],
            syncs=[],
        )
    )["activities"][0]

    assert activity["ownership_status"] == "AMBIGUOUS"
    assert activity["ownership_reasons"] == ["INVOCATION_OWNERSHIP_AMBIGUOUS"]


def test_covering_activity_markers_with_conflicting_phases_are_ambiguous():
    worker_api = _api(start=20, end=30)
    worker_api["global_tid"] = 2002
    activity = build_semantic_inventory(
        _bundle(
            nvtx=[
                _activity_marker("marker:decode", 10, 40, phase="decode"),
                _activity_marker("marker:prefill", 15, 35, phase="prefill"),
            ],
            cuda_api=[worker_api],
            activities=[_activity()],
            syncs=[],
        )
    )["activities"][0]

    assert activity["ownership_status"] == "AMBIGUOUS"
    assert activity["ownership_reasons"] == ["PHASE_OWNERSHIP_AMBIGUOUS"]


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
    assert inventory["activity_count_observed"] == 1
    assert inventory["activities"] == []


def test_ambiguous_input_fails_closed_without_reconstructing_a_plausible_wait_set():
    inventory = _semantic_inventory([_owned_activity("a:plausible", 2, 20, 80)])
    inventory["input_status"] = "AMBIGUOUS"
    inventory["input_reasons"] = ["INVOCATION_OWNERSHIP_AMBIGUOUS"]

    result = analyze_sync_semantics(
        inventory, _owned_sync("STREAM", 50, 90, stream_id=2)
    )

    assert result["wait_set_activity_ids"] == []
    assert result["validity"] == "AMBIGUOUS"
    assert result["primary_reason"] == "INVOCATION_OWNERSHIP_AMBIGUOUS"


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


def test_sync_identity_comes_from_unique_structured_sync_marker():
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                _nvtx("range:decode", 0, 100, "decode"),
                _sync_nvtx("range:sync", 50, 80),
            ],
            cuda_api=[], activities=[], syncs=[_sync()],
        )
    )

    sync = inventory["syncs"][0]
    assert sync["sync_identity_status"] == "VALID"
    assert sync["sync_origin"] == "natural_token_ready"
    assert sync["callsite_id"] == "decode.token_ready"
    assert sync["sync_ordinal"] == 0


def test_inventory_maps_cuda_event_record_and_stream_wait_edge_from_canonical_facts():
    event_api = _api("api:event-record", correlation_id=8, start=20, end=25)
    event_api["api_name"] = "cudaEventRecord"
    wait = _sync(
        start=30,
        end=35,
        runtime_api_name="cudaStreamWaitEvent",
        correlation_id=9,
        event_id=7,
        event_sync_id=70,
        stream_id=4,
    )
    event = {
        "record_id": "event:1", "correlation_id": 8, "timestamp_ns": 40,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "event_id": 7, "event_sync_id": 70,
    }
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[_nvtx("range:decode", 0, 100, "decode")],
            cuda_api=[event_api], activities=[], syncs=[wait], cuda_events=[event],
        )
    )

    assert inventory["syncs"] == []
    assert inventory["dependency_events"][0]["sync_kind"] == "STREAM_WAIT_EVENT"
    assert inventory["event_records"][0]["host_start_ns"] == 20
    assert inventory["event_records"][0]["event_sync_id"] == 70


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
    ("activity_start", "enqueue_start", "enqueue_end", "sync_start", "status", "proof"),
    [
        (49, 10, 70, 50, "PROVEN", "GPU_STARTED_BEFORE_SYNC"),
        (70, 10, 50, 50, "PROVEN", "ENQUEUE_COMPLETED_BEFORE_SYNC"),
        (70, 10, 60, 50, "AMBIGUOUS", None),
        (70, 50, 60, 50, "NOT_PRECEDING", None),
    ],
)
def test_submission_requires_gpu_start_or_enqueue_end(
    activity_start, enqueue_start, enqueue_end, sync_start, status, proof
):
    activity = {
        "start_ns": activity_start,
        "enqueue_start_ns": enqueue_start,
        "enqueue_end_ns": enqueue_end,
    }
    sync = {"host_start_ns": sync_start}

    result = submission_evidence(activity, sync)

    assert result["status"] == status
    assert result["proof"] == proof
    assert result["reason"] == (
        "SUBMISSION_ORDER_AMBIGUOUS" if status == "AMBIGUOUS" else None
    )


def _owned_activity(
    record_id: str,
    stream_id: int,
    start: int,
    end: int,
    *,
    context_id: int = 1,
    device_id: int = 0,
    enqueue_start: int | None = None,
    enqueue_end: int | None = None,
    phase: str = "decode",
    request_id: str = "req-0",
) -> dict:
    enqueue_start = start - 20 if enqueue_start is None else enqueue_start
    enqueue_end = start - 10 if enqueue_end is None else enqueue_end
    identity = _identity(phase, request_id=request_id)
    return {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "device_id": device_id,
        "context_id": context_id,
        "stream_id": stream_id,
        "enqueue_record_id": f"api:{record_id}",
        "enqueue_start_ns": enqueue_start,
        "enqueue_end_ns": enqueue_end,
        "request_id": request_id,
        "repeat_id": "r0",
        "origin_phase": phase,
        "invocation_identity": identity,
        "ownership_status": "VALID",
        "ownership_reasons": [],
    }


def _owned_sync(
    kind: str,
    start: int,
    end: int,
    *,
    stream_id: int | None = 2,
    context_id: int | None = 1,
    device_id: int | None = 0,
    event_id: int | None = None,
    event_sync_id: int | None = None,
    phase: str = "decode",
) -> dict:
    identity = _identity(phase)
    return {
        "record_id": "sync:target",
        "role": "HOST_BLOCKING_SYNC",
        "sync_kind": kind,
        "host_start_ns": start,
        "host_end_ns": end,
        "stream_id": stream_id,
        "context_id": context_id,
        "device_id": device_id,
        "event_id": event_id,
        "event_sync_id": event_sync_id,
        "request_id": "req-0",
        "repeat_id": "r0",
        "sync_owner_phase": phase,
        "sync_origin": "natural_token_ready",
        "callsite_id": "decode.token_ready",
        "sync_ordinal": 0,
        "invocation_identity": identity,
        "ownership_status": "VALID",
        "ownership_reasons": [],
    }


def _semantic_inventory(activities, *, event_records=None, dependency_events=None, mode="PER_THREAD"):
    return {
        "input_status": "VALID",
        "input_reasons": [],
        "execution_context": {"default_stream_mode": mode, "selected_device_id": 0},
        "activities": activities,
        "event_records": event_records or [],
        "dependency_events": dependency_events or [],
        "contexts": [{"context_id": 1, "device_id": 0, "null_stream_id": 0}],
        "streams": [
            {"context_id": 1, "stream_id": 0, "flag": 0},
            {"context_id": 1, "stream_id": 2, "flag": 0},
            {"context_id": 1, "stream_id": 3, "flag": 1},
        ],
    }


def test_stream_scope_keeps_completed_predecessor_and_rejects_unrelated_overlap():
    completed = _owned_activity("a:completed", 2, 10, 30)
    active = _owned_activity("a:active", 2, 35, 90)
    unrelated = _owned_activity("a:unrelated", 4, 55, 95)

    result = recover_wait_set(
        _semantic_inventory([completed, active, unrelated]),
        _owned_sync("STREAM", 50, 100),
    )

    assert result["wait_set_activity_ids"] == ["a:completed", "a:active"]
    assert "a:unrelated" not in result["wait_set_activity_ids"]
    assert result["dependency_closure_status"] == "COMPLETE"


def test_device_and_context_scopes_use_completion_semantics_not_overlap():
    ctx1_a = _owned_activity("a:ctx1-s2", 2, 10, 70)
    ctx1_b = _owned_activity("a:ctx1-s4", 4, 20, 90)
    ctx2 = _owned_activity("a:ctx2", 8, 30, 95, context_id=2)
    device_result = recover_wait_set(
        _semantic_inventory([ctx1_a, ctx1_b, ctx2]),
        _owned_sync("DEVICE", 50, 100, stream_id=None, context_id=None),
    )
    context_result = recover_wait_set(
        _semantic_inventory([ctx1_a, ctx1_b, ctx2]),
        _owned_sync("CONTEXT", 50, 100, stream_id=None),
    )

    assert device_result["wait_set_activity_ids"] == ["a:ctx1-s2", "a:ctx1-s4", "a:ctx2"]
    assert context_result["wait_set_activity_ids"] == ["a:ctx1-s2", "a:ctx1-s4"]


def test_event_sync_uses_exact_record_capture_and_excludes_post_record_activity():
    before = _owned_activity("a:before", 2, 10, 40, enqueue_start=10, enqueue_end=20)
    after = _owned_activity("a:after", 2, 45, 90, enqueue_start=35, enqueue_end=45)
    event_record = {
        "record_id": "event:record-1",
        "event_id": 9,
        "event_sync_id": 90,
        "device_id": 0,
        "context_id": 1,
        "stream_id": 2,
        "host_start_ns": 25,
        "host_end_ns": 30,
        "request_id": "req-0",
        "repeat_id": "r0",
        "ownership_status": "VALID",
        "invocation_identity": _identity("decode"),
    }
    sync = _owned_sync("EVENT", 60, 80, event_id=9, event_sync_id=90, stream_id=None)

    result = recover_wait_set(
        _semantic_inventory([before, after], event_records=[event_record]), sync
    )

    assert result["wait_set_activity_ids"] == ["a:before"]
    assert result["event_record_id"] == "event:record-1"


@pytest.mark.parametrize(
    ("second_record", "sync_updates"),
    [
        (
            {
                "record_id": "event:duplicate", "event_id": 9,
                "event_sync_id": 90, "device_id": 0, "context_id": 1,
                "stream_id": 2, "host_start_ns": 26, "host_end_ns": 31,
                "request_id": "req-0", "repeat_id": "r0",
                "ownership_status": "VALID",
                "invocation_identity": _identity("decode"),
            },
            {},
        ),
        (None, {"event_id": 10}),
        (None, {"context_id": 2}),
        (None, {"device_id": 1}),
    ],
)
def test_event_sync_requires_one_record_matching_event_scope(second_record, sync_updates):
    producer = _owned_activity("a:event-producer", 2, 10, 40)
    event_record = {
        "record_id": "event:unique", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "host_start_ns": 25, "host_end_ns": 30,
        "request_id": "req-0", "repeat_id": "r0",
        "ownership_status": "VALID", "ownership_reasons": [],
        "invocation_identity": _identity("decode"),
    }
    records = [event_record] + ([second_record] if second_record else [])
    sync = _owned_sync(
        "EVENT", 60, 80, stream_id=None, event_id=9, event_sync_id=90
    )
    sync.update(sync_updates)

    result = analyze_sync_semantics(
        _semantic_inventory([producer], event_records=records), sync
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "MISSING_EVENT_RECORD"
    assert result["event_record_id"] is None


def test_stream_wait_event_adds_cross_stream_producer_to_consumer_closure():
    producer = _owned_activity("a:producer", 2, 10, 40, enqueue_start=10, enqueue_end=20)
    consumer = _owned_activity("a:consumer", 4, 50, 90, enqueue_start=40, enqueue_end=45)
    event_record = {
        "record_id": "event:record-1", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "host_start_ns": 25, "host_end_ns": 30,
        "request_id": "req-0", "repeat_id": "r0", "ownership_status": "VALID",
        "invocation_identity": _identity("decode"),
    }
    wait = {
        "record_id": "edge:wait", "sync_kind": "STREAM_WAIT_EVENT", "role": "DEPENDENCY_EDGE",
        "event_id": 9, "event_sync_id": 90, "device_id": 0,
        "context_id": 1, "stream_id": 4,
        "host_start_ns": 32, "host_end_ns": 35, "ownership_status": "VALID",
        "request_id": "req-0", "repeat_id": "r0", "invocation_identity": _identity("decode"),
    }

    result = recover_wait_set(
        _semantic_inventory([producer, consumer], event_records=[event_record], dependency_events=[wait]),
        _owned_sync("STREAM", 60, 100, stream_id=4),
    )

    assert result["wait_set_activity_ids"] == ["a:producer", "a:consumer"]
    assert {edge["edge_type"] for edge in result["dependency_edges"]} >= {
        "EVENT_RECORD_CAPTURE", "STREAM_WAIT_EVENT"
    }


@pytest.mark.parametrize(
    ("wait_updates", "sync_updates"),
    [
        ({"event_id": 10}, {}),
        ({"context_id": 2}, {"context_id": 2}),
        ({"device_id": 1}, {"device_id": 1}),
    ],
)
def test_stream_wait_requires_event_record_scope_match(wait_updates, sync_updates):
    producer = _owned_activity("a:wait-producer", 2, 10, 40)
    event_record = {
        "record_id": "event:wait-scope", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "host_start_ns": 25, "host_end_ns": 30,
        "request_id": "req-0", "repeat_id": "r0",
        "ownership_status": "VALID", "ownership_reasons": [],
        "invocation_identity": _identity("decode"),
    }
    wait = {
        "record_id": "edge:bad-scope", "sync_kind": "STREAM_WAIT_EVENT",
        "role": "DEPENDENCY_EDGE", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 4,
        "host_start_ns": 32, "host_end_ns": 35,
        "ownership_status": "VALID", "ownership_reasons": [],
        "request_id": "req-0", "repeat_id": "r0",
        "invocation_identity": _identity("decode"),
    }
    wait.update(wait_updates)
    sync = _owned_sync("STREAM", 60, 100, stream_id=4)
    sync.update(sync_updates)

    result = analyze_sync_semantics(
        _semantic_inventory(
            [producer], event_records=[event_record], dependency_events=[wait]
        ),
        sync,
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "MISSING_EVENT_RECORD"
    assert result["wait_set_activity_ids"] == []


def test_default_stream_mode_is_required_only_when_default_stream_is_observed():
    default = _owned_activity("a:default", 0, 10, 40, enqueue_start=10, enqueue_end=20)
    blocking = _owned_activity("a:blocking", 2, 45, 90, enqueue_start=30, enqueue_end=40)

    unknown = recover_wait_set(
        _semantic_inventory([default, blocking], mode=None),
        _owned_sync("STREAM", 60, 100, stream_id=2),
    )
    no_default = recover_wait_set(
        _semantic_inventory([blocking], mode=None),
        _owned_sync("STREAM", 60, 100, stream_id=2),
    )

    assert unknown["dependency_closure_status"] == "AMBIGUOUS"
    assert unknown["reasons"] == ["DEFAULT_STREAM_MODE_UNKNOWN"]
    assert no_default["dependency_closure_status"] == "COMPLETE"


def test_opt_in_nonblocking_scope_keeps_complete_prefix_without_unrelated_default():
    default = _owned_activity('setup:default',0,1,8,enqueue_start=0,enqueue_end=1,request_id='setup')
    first = _owned_activity('measured:first',3,10,30,enqueue_start=9,enqueue_end=10)
    last = _owned_activity('measured:last',3,40,90,enqueue_start=32,enqueue_end=35)
    inventory = _semantic_inventory([default,first,last],mode=None)
    inventory['isolated_nonblocking_scope'] = (None,0,1,3)
    sync = _owned_sync('STREAM',60,100,stream_id=3)
    result = recover_wait_set(inventory,sync)
    assert result['dependency_closure_status']=='COMPLETE'
    assert result['wait_set_activity_ids']==['measured:first','measured:last']
    assert result['reasons']==[]
    assert inventory['execution_context']['default_stream_mode'] is None
    assert len(inventory['activities'])==3  # No Raw/physical-prefix erasure.


@pytest.mark.parametrize('kind',['STREAM','CONTEXT'])
def test_scoped_nonblocking_proof_does_not_apply_to_another_scope(kind):
    default = _owned_activity('default',0,1,8,enqueue_start=0,enqueue_end=1)
    other = _owned_activity('other',2,10,90,enqueue_start=9,enqueue_end=10)
    inventory = _semantic_inventory([default,other],mode=None)
    inventory['isolated_nonblocking_scope'] = (None,0,1,3)
    result = recover_wait_set(inventory,_owned_sync(kind,60,100,stream_id=2))
    assert 'DEFAULT_STREAM_MODE_UNKNOWN' in result['reasons']


@pytest.mark.parametrize('event_present',[False,True])
def test_incoming_event_dependency_prevents_isolated_nonblocking_shortcut(event_present):
    default = _owned_activity('default',0,10,40,enqueue_start=1,enqueue_end=5)
    consumer = _owned_activity('consumer',3,50,90,enqueue_start=40,enqueue_end=45)
    event = dict(record_id='event:1',event_id=9,event_sync_id=90,device_id=0,context_id=1,
        stream_id=0,host_start_ns=25,host_end_ns=30,request_id='req-0',repeat_id='r0',
        ownership_status='VALID',invocation_identity=_identity('decode'))
    wait = dict(event,record_id='edge:1',role='DEPENDENCY_EDGE',sync_kind='STREAM_WAIT_EVENT',
        stream_id=3,host_start_ns=32,host_end_ns=35)
    inventory = _semantic_inventory([default,consumer],mode=None,
        event_records=[event] if event_present else [],dependency_events=[wait])
    inventory['isolated_nonblocking_scope'] = (None,0,1,3)
    result = recover_wait_set(inventory,_owned_sync('STREAM',60,100,stream_id=3))
    assert 'DEFAULT_STREAM_MODE_UNKNOWN' in result['reasons']
    if not event_present: assert 'MISSING_EVENT_RECORD' in result['reasons']
    assert result['dependency_closure_status']!='COMPLETE'


def test_unknown_incoming_event_order_cannot_be_treated_as_no_dependency():
    default = _owned_activity('default',0,10,40,enqueue_start=1,enqueue_end=5)
    consumer = _owned_activity('consumer',3,50,90,enqueue_start=40,enqueue_end=45)
    wait = dict(record_id='edge:unknown',role='DEPENDENCY_EDGE',event_sync_id=90,
        context_id=1,stream_id=3,host_start_ns=32,host_end_ns=None)
    inventory = _semantic_inventory([default,consumer],mode=None,dependency_events=[wait])
    inventory['isolated_nonblocking_scope'] = (None,0,1,3)
    result = recover_wait_set(inventory,_owned_sync('STREAM',60,100,stream_id=3))
    assert result['dependency_closure_status']=='AMBIGUOUS'
    assert 'DEFAULT_STREAM_MODE_UNKNOWN' in result['reasons']


def test_legacy_default_stream_adds_only_blocking_stream_edges_while_ptds_does_not():
    default = _owned_activity("a:default", 0, 10, 40, enqueue_start=10, enqueue_end=20)
    blocking = _owned_activity("a:blocking", 2, 45, 90, enqueue_start=30, enqueue_end=40)
    nonblocking = _owned_activity("a:nonblocking", 3, 42, 92, enqueue_start=25, enqueue_end=35)

    legacy = recover_wait_set(
        _semantic_inventory([default, blocking, nonblocking], mode="LEGACY"),
        _owned_sync("STREAM", 60, 100, stream_id=2),
    )
    ptds = recover_wait_set(
        _semantic_inventory([default, blocking, nonblocking], mode="PER_THREAD"),
        _owned_sync("STREAM", 60, 100, stream_id=2),
    )

    assert legacy["wait_set_activity_ids"] == ["a:default", "a:blocking"]
    assert ptds["wait_set_activity_ids"] == ["a:blocking"]
    assert "a:nonblocking" not in legacy["wait_set_activity_ids"]


def test_no_default_stream_observed_manifest_conflicts_with_observed_null_stream():
    default = _owned_activity("a:default", 0, 10, 40)
    blocking = _owned_activity("a:blocking", 2, 45, 90)

    result = recover_wait_set(
        _semantic_inventory([default, blocking], mode="NO_DEFAULT_STREAM_OBSERVED"),
        _owned_sync("STREAM", 60, 100, stream_id=2),
    )

    assert result["dependency_closure_status"] == "AMBIGUOUS"
    assert result["reasons"] == ["DEFAULT_STREAM_MODE_UNKNOWN"]


def test_legacy_default_cross_thread_enqueue_overlap_is_ambiguous():
    default = _owned_activity(
        "a:default", 0, 10, 40, enqueue_start=10, enqueue_end=40
    )
    blocking = _owned_activity(
        "a:blocking", 2, 45, 90, enqueue_start=30, enqueue_end=50
    )

    result = recover_wait_set(
        _semantic_inventory([default, blocking], mode="LEGACY"),
        _owned_sync("STREAM", 60, 100, stream_id=2),
    )

    assert result["dependency_closure_status"] == "AMBIGUOUS"
    assert result["reasons"] == ["DEPENDENCY_CLOSURE_AMBIGUOUS"]


def test_future_default_stream_overlap_does_not_poison_earlier_stream_sync():
    future_default = _owned_activity(
        "a:future-default", 0, 80, 110, enqueue_start=70, enqueue_end=90
    )
    future_blocking = _owned_activity(
        "a:future-blocking", 2, 90, 120, enqueue_start=80, enqueue_end=100
    )

    result = analyze_sync_semantics(
        _semantic_inventory([future_default, future_blocking], mode="LEGACY"),
        _owned_sync("STREAM", 50, 60, stream_id=2),
    )

    assert result["validity"] == "VALID_EMPTY"
    assert result["primary_reason"] is None


def test_legacy_external_default_predecessor_fails_closed():
    external_default = _owned_activity(
        "a:external-default", 0, 10, 40, request_id="req-old",
        enqueue_start=10, enqueue_end=20,
    )
    target = _owned_activity(
        "a:target", 2, 45, 90, enqueue_start=30, enqueue_end=40
    )

    result = analyze_sync_semantics(
        _semantic_inventory([external_default, target], mode="LEGACY"),
        _owned_sync("STREAM", 60, 100, stream_id=2),
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "INVOCATION_BLEED"


def test_submission_race_makes_closure_ambiguous_without_guessing_membership():
    racing = _owned_activity(
        "a:racing", 2, 70, 90, enqueue_start=45, enqueue_end=60
    )

    result = recover_wait_set(
        _semantic_inventory([racing]), _owned_sync("STREAM", 50, 100, stream_id=2)
    )

    assert result["wait_set_activity_ids"] == []
    assert result["dependency_closure_status"] == "AMBIGUOUS"
    assert result["reasons"] == ["SUBMISSION_ORDER_AMBIGUOUS"]
    assert result["submission_evidence"]["a:racing"]["status"] == "AMBIGUOUS"


def test_definitely_post_sync_activity_is_excluded_without_poisoning_closure():
    later = _owned_activity(
        "a:later", 2, 80, 100, enqueue_start=60, enqueue_end=70
    )

    result = recover_wait_set(
        _semantic_inventory([later]), _owned_sync("STREAM", 50, 90, stream_id=2)
    )

    assert result["wait_set_activity_ids"] == []
    assert result["dependency_closure_status"] == "COMPLETE"


def test_cross_phase_activity_remains_in_wait_set_with_provenance():
    prefill = _owned_activity("a:prefill", 2, 40, 80, phase="prefill")

    result = recover_wait_set(
        _semantic_inventory([prefill]),
        _owned_sync("STREAM", 60, 90, stream_id=2, phase="decode"),
    )

    assert result["wait_set_activity_ids"] == ["a:prefill"]
    assert result["activity_origin_phases"] == {"a:prefill": "prefill"}
    assert result["cross_phase_dependency"] is True


def test_unrelated_broken_event_evidence_does_not_poison_stream_sync():
    target = _owned_activity("a:target", 2, 20, 80)
    unrelated_broken_event = {
        "record_id": "event:broken", "event_id": 99, "event_sync_id": None,
        "context_id": 2, "stream_id": 9, "ownership_status": "INVALID",
        "ownership_reasons": ["MISSING_EVENT_RECORD"],
    }

    result = recover_wait_set(
        _semantic_inventory([target], event_records=[unrelated_broken_event]),
        _owned_sync("STREAM", 50, 90, stream_id=2),
    )

    assert result["dependency_closure_status"] == "COMPLETE"
    assert result["reasons"] == []


def test_missing_activity_correlation_is_invalid_not_generic_ownership_ambiguity():
    from exposedpath_v141.q0_oracle import load_oracle_bundle

    expected = next(
        case for case in load_oracle_bundle()["cases"]
        if case["case_id"] == "Q0-MISSING-CORR-001"
    )["expected"]["syncs"][0]
    missing = _owned_activity("a:missing-corr", 2, 20, 80)
    missing.update(
        enqueue_record_id=None,
        enqueue_start_ns=None,
        enqueue_end_ns=None,
        request_id=None,
        repeat_id=None,
        invocation_identity=None,
        ownership_status="INVALID",
        ownership_reasons=["MISSING_ACTIVITY_CORRELATION"],
    )

    result = analyze_sync_semantics(
        _semantic_inventory([missing]), _owned_sync("STREAM", 50, 90, stream_id=2)
    )

    assert result["validity"] == expected["validity"]
    assert result["primary_reason"] == expected["primary_reason"]


def test_missing_correlation_remains_invalid_when_submission_order_is_also_unknown():
    missing = _owned_activity("a:missing-racing", 2, 70, 90)
    missing.update(
        enqueue_record_id=None,
        enqueue_start_ns=None,
        enqueue_end_ns=None,
        request_id=None,
        repeat_id=None,
        invocation_identity=None,
        ownership_status="INVALID",
        ownership_reasons=["MISSING_ACTIVITY_CORRELATION"],
    )

    result = analyze_sync_semantics(
        _semantic_inventory([missing]), _owned_sync("STREAM", 50, 100, stream_id=2)
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "MISSING_ACTIVITY_CORRELATION"
    assert "SUBMISSION_ORDER_AMBIGUOUS" in result["secondary_reasons"]


def _missing_correlation_activity(record_id: str, stream_id: int) -> dict:
    activity = _owned_activity(record_id, stream_id, 70, 90)
    activity.update(
        enqueue_record_id=None,
        enqueue_start_ns=None,
        enqueue_end_ns=None,
        request_id=None,
        repeat_id=None,
        invocation_identity=None,
        ownership_status="INVALID",
        ownership_reasons=["MISSING_ACTIVITY_CORRELATION"],
    )
    return activity


def _valid_event_record(record_id: str = "event:missing-corr") -> dict:
    return {
        "record_id": record_id, "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "host_start_ns": 25, "host_end_ns": 30,
        "request_id": "req-0", "repeat_id": "r0",
        "ownership_status": "VALID", "ownership_reasons": [],
        "invocation_identity": _identity("decode"),
    }


def test_event_prefix_missing_correlation_is_invalid_not_only_ambiguous():
    result = analyze_sync_semantics(
        _semantic_inventory(
            [_missing_correlation_activity("a:event-missing-corr", 2)],
            event_records=[_valid_event_record()],
        ),
        _owned_sync(
            "EVENT", 60, 100, stream_id=None, event_id=9, event_sync_id=90
        ),
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "MISSING_ACTIVITY_CORRELATION"
    assert "SUBMISSION_ORDER_AMBIGUOUS" in result["secondary_reasons"]


def test_stream_wait_producer_missing_correlation_is_invalid_not_only_ambiguous():
    wait = {
        "record_id": "edge:missing-corr", "sync_kind": "STREAM_WAIT_EVENT",
        "role": "DEPENDENCY_EDGE", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 4,
        "host_start_ns": 32, "host_end_ns": 35,
        "ownership_status": "VALID", "ownership_reasons": [],
        "request_id": "req-0", "repeat_id": "r0",
        "invocation_identity": _identity("decode"),
    }
    result = analyze_sync_semantics(
        _semantic_inventory(
            [_missing_correlation_activity("a:wait-missing-corr", 2)],
            event_records=[_valid_event_record("event:wait-missing-corr")],
            dependency_events=[wait],
        ),
        _owned_sync("STREAM", 60, 100, stream_id=4),
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "MISSING_ACTIVITY_CORRELATION"


def test_legacy_default_predecessor_missing_correlation_is_invalid():
    missing_default = _missing_correlation_activity("a:default-missing-corr", 0)
    target = _owned_activity(
        "a:legacy-target", 2, 40, 80, enqueue_start=20, enqueue_end=30
    )

    result = analyze_sync_semantics(
        _semantic_inventory([missing_default, target], mode="LEGACY"),
        _owned_sync("STREAM", 50, 100, stream_id=2),
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "MISSING_ACTIVITY_CORRELATION"


def test_stream_wait_event_without_consumer_still_exposes_producer_to_stream_sync():
    producer = _owned_activity("a:producer-only", 2, 10, 45)
    event_record = {
        "record_id": "event:producer-only", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "host_start_ns": 25, "host_end_ns": 30,
        "request_id": "req-0", "repeat_id": "r0", "ownership_status": "VALID",
        "invocation_identity": _identity("decode"),
    }
    wait = {
        "record_id": "edge:last-wait", "sync_kind": "STREAM_WAIT_EVENT",
        "role": "DEPENDENCY_EDGE", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 4,
        "host_start_ns": 32, "host_end_ns": 35,
        "ownership_status": "VALID", "request_id": "req-0", "repeat_id": "r0",
        "invocation_identity": _identity("decode"),
    }

    result = analyze_sync_semantics(
        _semantic_inventory(
            [producer], event_records=[event_record], dependency_events=[wait]
        ),
        _owned_sync("STREAM", 60, 100, stream_id=4),
    )

    assert result["wait_set_activity_ids"] == ["a:producer-only"]
    assert result["terminal"]["activity_id"] == "a:producer-only"
    assert result["validity"] == "VALID_NONEMPTY"


def test_external_event_predecessor_is_not_filtered_before_ownership_check():
    from exposedpath_v141.q0_oracle import load_oracle_bundle

    expected = next(
        case for case in load_oracle_bundle()["cases"]
        if case["case_id"] == "Q0-INVOCATION-BLEED-001"
    )["expected"]["syncs"][0]
    producer = _owned_activity(
        "a:external-producer", 2, 10, 45, request_id="req-old"
    )
    event_record = {
        "record_id": "event:external", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 2,
        "host_start_ns": 25, "host_end_ns": 30,
        "request_id": "req-old", "repeat_id": "r0", "ownership_status": "VALID",
        "invocation_identity": _identity("decode", request_id="req-old"),
    }
    wait = {
        "record_id": "edge:current-wait", "sync_kind": "STREAM_WAIT_EVENT",
        "role": "DEPENDENCY_EDGE", "event_id": 9, "event_sync_id": 90,
        "device_id": 0, "context_id": 1, "stream_id": 4,
        "host_start_ns": 32, "host_end_ns": 35,
        "ownership_status": "VALID", "request_id": "req-0", "repeat_id": "r0",
        "invocation_identity": _identity("decode"),
    }

    result = analyze_sync_semantics(
        _semantic_inventory(
            [producer], event_records=[event_record], dependency_events=[wait]
        ),
        _owned_sync("STREAM", 60, 100, stream_id=4),
    )

    assert result["validity"] == expected["validity"]
    assert result["primary_reason"] == expected["primary_reason"]


def test_static_dependency_graph_is_reused_for_repeated_syncs_in_same_scope(monkeypatch):
    import exposedpath_v141.sync_semantics as semantics

    inventory = _semantic_inventory([
        _owned_activity("a:first", 2, 10, 30),
        _owned_activity("a:second", 2, 35, 80),
    ])
    calls = 0
    original = semantics._build_same_stream_edges

    def counted(*args, **kwargs):
        nonlocal calls
        calls += 1
        return original(*args, **kwargs)

    monkeypatch.setattr(semantics, "_build_same_stream_edges", counted)
    analyze_sync_semantics(inventory, _owned_sync("STREAM", 50, 90, stream_id=2))
    analyze_sync_semantics(inventory, _owned_sync("STREAM", 60, 100, stream_id=2))

    assert calls == 1


def test_terminal_comes_from_semantic_frontier_and_completed_before_remains_nonempty():
    first = _owned_activity("a:first", 2, 10, 30)
    terminal = _owned_activity("a:terminal", 2, 35, 45)
    result = analyze_sync_semantics(
        _semantic_inventory([first, terminal]),
        _owned_sync("STREAM", 50, 80, stream_id=2),
    )

    assert result["wait_set_activity_ids"] == ["a:first", "a:terminal"]
    assert result["terminal"] == {
        "status": "VALID",
        "kind": "ACTIVITY",
        "activity_id": "a:terminal",
        "end_ns": 45,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
    }
    assert result["validity"] == "VALID_NONEMPTY"


def test_multiple_frontiers_use_unique_latest_completion_only_in_shared_clock():
    early = _owned_activity("a:early", 2, 10, 70)
    late = _owned_activity("a:late", 4, 20, 90)
    result = analyze_sync_semantics(
        _semantic_inventory([early, late]),
        _owned_sync("DEVICE", 50, 100, stream_id=None, context_id=None),
    )

    assert result["terminal"]["activity_id"] == "a:late"
    assert result["semantic_frontier_activity_ids"] == ["a:early", "a:late"]
    assert result["validity"] == "VALID_NONEMPTY"


def test_equal_latest_frontiers_are_ambiguous_with_zero_tolerance():
    left = _owned_activity("a:left", 2, 10, 90)
    right = _owned_activity("a:right", 4, 20, 90)
    result = analyze_sync_semantics(
        _semantic_inventory([left, right]),
        _owned_sync("DEVICE", 50, 100, stream_id=None, context_id=None),
    )

    assert result["terminal"]["status"] == "AMBIGUOUS"
    assert result["validity"] == "AMBIGUOUS"
    assert result["primary_reason"] == "TERMINAL_TIE"


def test_terminal_after_sync_return_is_invalid():
    activity = _owned_activity("a:late-terminal", 2, 20, 110)
    result = analyze_sync_semantics(
        _semantic_inventory([activity]), _owned_sync("STREAM", 50, 100, stream_id=2)
    )

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "TERMINAL_AFTER_SYNC_END"


def test_observable_empty_scope_is_valid_empty():
    result = analyze_sync_semantics(
        _semantic_inventory([]), _owned_sync("STREAM", 50, 80, stream_id=2)
    )

    assert result["wait_set_activity_ids"] == []
    assert result["terminal"] == {
        "status": "NOT_APPLICABLE", "kind": "NONE", "activity_id": None,
        "end_ns": None, "clock_domain_id": None,
    }
    assert result["validity"] == "VALID_EMPTY"
    assert result["primary_reason"] is None

    from exposedpath_v141.s_bundle import load_s_layer_schema
    assert set(result) == set(load_s_layer_schema()["sync_record_fields"])


def test_reason_priority_is_contract_order_not_discovery_order():
    racing = _owned_activity("a:racing", 2, 70, 90, enqueue_start=45, enqueue_end=60)
    event_sync = _owned_sync(
        "EVENT", 50, 100, stream_id=None, event_id=9, event_sync_id=90
    )
    result = analyze_sync_semantics(_semantic_inventory([racing]), event_sync)

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "MISSING_EVENT_RECORD"


def test_unsupported_physical_sync_fails_closed():
    sync = _owned_sync("SYNCHRONOUS_COPY_OR_IMPLICIT_BLOCK", 50, 100)
    sync["role"] = "UNSUPPORTED"
    result = analyze_sync_semantics(_semantic_inventory([]), sync)

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "UNSUPPORTED_SYNC_API"


@pytest.mark.parametrize(
    "case_id",
    ["Q0-STREAM-001", "Q0-COMPLETED-001", "Q0-EMPTY-001", "Q0-TERMINAL-TIE-001"],
)
def test_s_layer_matches_frozen_q0_expected_for_core_cases(case_id):
    from exposedpath_v141.q0_oracle import load_oracle_bundle

    case = next(item for item in load_oracle_bundle()["cases"] if item["case_id"] == case_id)
    construction = case["construction"]
    sync_spec = construction["syncs"][0]
    expected = case["expected"]["syncs"][0]
    wait_labels = set(expected["wait_set_activity_labels"])
    activities = []
    for index, spec in enumerate(construction["activities"]):
        stream = 2 if spec["activity_label"] in wait_labels else 4
        if sync_spec["sync_kind"] in {"DEVICE", "CONTEXT"}:
            stream = 2 + index
        activities.append(
            _owned_activity(
                spec["activity_label"], stream, spec["start_ns"], spec["end_ns"],
                enqueue_start=max(0, spec["start_ns"] - 10),
                enqueue_end=max(0, min(spec["start_ns"], sync_spec["start_ns"] - 1)),
            )
        )
    sync = _owned_sync(
        sync_spec["sync_kind"], sync_spec["start_ns"], sync_spec["end_ns"],
        stream_id=2 if sync_spec["sync_kind"] == "STREAM" else None,
        context_id=None if sync_spec["sync_kind"] == "DEVICE" else 1,
    )

    result = analyze_sync_semantics(_semantic_inventory(activities), sync)

    assert result["wait_set_activity_ids"] == expected["wait_set_activity_labels"]
    assert result["validity"] == expected["validity"]
    if expected["terminal"]["status"] == "VALID":
        assert result["terminal"]["activity_id"] == expected["terminal"]["activity_label"]
    else:
        assert result["terminal"]["status"] == expected["terminal"]["status"]


# Gate 6 Sync Projection Amendment v0.1：registry-role-preserving semantic sync 投影。


def _cuda_api_row(
    record_id: str,
    api_name: str,
    start: int,
    end: int,
    *,
    global_tid: int = 1001,
    source_table: str | None = "CUPTI_ACTIVITY_KIND_RUNTIME",
    source_rowid: int | None = 12,
) -> dict:
    """Canonical `cuda_api` 行：`source_table`/`source_rowid` 是 API-backed `sync_id` 的唯一依据。"""

    row: dict = {
        "record_id": record_id,
        "start_ns": start,
        "end_ns": end,
        "global_tid": global_tid,
        "correlation_id": 99,
        "api_name": api_name,
    }
    if source_table is not None:
        row["source_table"] = source_table
    if source_rowid is not None:
        row["source_rowid"] = source_rowid
    return row


def _sync_request_and_phase_ranges() -> list[dict]:
    return [
        _request_nvtx("range:req", 0, 100),
        _nvtx("range:decode", 0, 100, "decode"),
    ]


def test_non_sync_query_is_excluded_from_semantic_sync_universe():
    """`cudaEventQuery`（`NON_BLOCKING_QUERY`）不得进入 `inventory["syncs"]` 或 S 记录。"""

    query = _sync(start=20, end=40, runtime_api_name="cudaEventQuery_v3020")
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                *_sync_request_and_phase_ranges(),
                _activity_marker("marker:query", 19, 41, global_tid=1001, callsite_id="Q_EVENT"),
            ],
            cuda_api=[_cuda_api_row("api:query", "cudaEventQuery_v3020", 20, 40)],
            activities=[],
            syncs=[query],
        )
    )

    assert inventory["syncs"] == []
    assert inventory["dependency_events"] == []
    assert analyze_semantic_inventory(inventory) == []


def test_unsupported_api_without_physical_row_builds_api_backed_semantic_sync():
    """UNSUPPORTED 调用无 mapped `cuda_sync` 时，由 runtime API 区间 + 唯一 `kind=sync` marker 构造。"""

    from exposedpath_v141.s_bundle import load_s_layer_schema

    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                *_sync_request_and_phase_ranges(),
                _sync_nvtx("nvtx:sync:copy", 10, 85),
            ],
            cuda_api=[_cuda_api_row("api:copy", "cudaMemcpy_v3020", 10, 85)],
            activities=[],
            syncs=[],
        )
    )

    assert [record["record_id"] for record in inventory["syncs"]] == [
        "cuda_api_sync:CUPTI_ACTIVITY_KIND_RUNTIME:12"
    ]
    record = inventory["syncs"][0]
    assert record["host_start_ns"] == 10
    assert record["host_end_ns"] == 85
    assert record["registry_rule_id"] == "SYNC-COPY-IMPLICIT-001"
    assert record["universe_class"] == "IN_UNIVERSE_UNSUPPORTED"
    assert record["role"] == "UNSUPPORTED"
    assert record["sync_kind"] == "SYNCHRONOUS_COPY_OR_IMPLICIT_BLOCK"
    assert record["request_id"] == "req-0"
    assert record["repeat_id"] == "r0"
    assert record["sync_owner_phase"] == "decode"
    assert record["callsite_id"] == "decode.token_ready"
    assert (
        record["device_id"],
        record["context_id"],
        record["stream_id"],
        record["event_id"],
        record["event_sync_id"],
    ) == (None, None, None, None, None)

    result = analyze_sync_semantics(inventory, record)

    assert set(result) == set(load_s_layer_schema()["sync_record_fields"])
    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == "UNSUPPORTED_SYNC_API"
    assert result["wait_set_activity_ids"] == []
    assert result["terminal"] == {
        "status": "INVALID",
        "kind": "NONE",
        "activity_id": None,
        "end_ns": None,
        "clock_domain_id": None,
    }


def test_unsupported_api_with_mapped_physical_row_is_not_duplicated():
    """有 mapped `cuda_sync` 行时 physical row 是唯一权威，绝不追加 API-backed 记录。"""

    physical = _sync(start=10, end=85, runtime_api_name="cudaMemcpy_v3020")
    physical["record_id"] = "cuda_sync:CUPTI_ACTIVITY_KIND_SYNCHRONIZATION:9"
    physical["runtime_record_id"] = "api:copy"
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                *_sync_request_and_phase_ranges(),
                _sync_nvtx("nvtx:sync:copy", 10, 85),
            ],
            cuda_api=[_cuda_api_row("api:copy", "cudaMemcpy_v3020", 10, 85)],
            activities=[],
            syncs=[physical],
        )
    )

    assert [record["record_id"] for record in inventory["syncs"]] == [
        "cuda_sync:CUPTI_ACTIVITY_KIND_SYNCHRONIZATION:9"
    ]
    assert not any(
        str(record["record_id"]).startswith("cuda_api_sync:") for record in inventory["syncs"]
    )


def test_api_backed_sync_is_not_fabricated_without_sync_marker():
    """完全没有包围/相交的 `kind=sync` marker 时不构造记录，不伪造同步事实。"""

    inventory = build_semantic_inventory(
        _bundle(
            nvtx=_sync_request_and_phase_ranges(),
            cuda_api=[_cuda_api_row("api:copy", "cudaMemcpy_v3020", 10, 85)],
            activities=[],
            syncs=[],
        )
    )

    assert inventory["syncs"] == []


def test_api_backed_sync_without_canonical_row_identity_is_not_fabricated():
    """缺少 Canonical record identity 时不得猜 `sync_id`，因此不构造记录。"""

    inventory = build_semantic_inventory(
        _bundle(
            nvtx=[
                *_sync_request_and_phase_ranges(),
                _sync_nvtx("nvtx:sync:copy", 10, 85),
            ],
            cuda_api=[
                _cuda_api_row(
                    "api:copy",
                    "cudaMemcpy_v3020",
                    10,
                    85,
                    source_table=None,
                    source_rowid=None,
                )
            ],
            activities=[],
            syncs=[],
        )
    )

    assert inventory["syncs"] == []


@pytest.mark.parametrize(
    ("markers", "expected_reason"),
    [
        # 重复覆盖：identity 不唯一
        ([("nvtx:sync:a", 10, 85), ("nvtx:sync:b", 10, 85)], "INVOCATION_BOUNDARY_INVALID"),
        # 仅部分相交：不得使用任何 label
        ([("nvtx:sync:partial", 5, 60)], "INVOCATION_BOUNDARY_INVALID"),
        # 只有跨线程 marker：同线程覆盖不存在
        ([("nvtx:sync:worker", 10, 85, 3003)], "INVOCATION_BOUNDARY_INVALID"),
    ],
)
def test_api_backed_sync_marker_conflicts_fail_closed(markers, expected_reason):
    nvtx = _sync_request_and_phase_ranges()
    for marker in markers:
        record_id, start, end = str(marker[0]), int(marker[1]), int(marker[2])
        marker_record = _sync_nvtx(record_id, start, end)
        if len(marker) == 4:
            marker_record["global_tid"] = int(marker[3])
        nvtx.append(marker_record)
    inventory = build_semantic_inventory(
        _bundle(
            nvtx=nvtx,
            cuda_api=[_cuda_api_row("api:copy", "cudaMemcpy_v3020", 10, 85)],
            activities=[],
            syncs=[],
        )
    )

    assert len(inventory["syncs"]) == 1
    record = inventory["syncs"][0]
    assert record["sync_identity_status"] == "AMBIGUOUS"
    assert record["callsite_id"] is None

    result = analyze_sync_semantics(inventory, record)

    assert result["validity"] == "INVALID"
    assert result["primary_reason"] == expected_reason
    assert result["wait_set_activity_ids"] == []
    assert result["terminal"]["status"] == "INVALID"
