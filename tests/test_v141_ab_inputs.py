"""Gate 5 Task 2：Canonical/S 严格联结和结构化窗口发现。"""

from __future__ import annotations

import gzip
import hashlib
import json
from copy import deepcopy
from pathlib import Path

import pytest

from exposedpath_v141.ab_inputs import (
    ABInputError,
    discover_request_phase_windows,
    load_ab_inputs,
)
from exposedpath_v141.a_accounting import calculate_a_windows
from exposedpath_v141.canonical_raw import load_canonical_raw_schema
from exposedpath_v141.s_bundle import load_s_layer_schema
from exposedpath_v141.sync_semantics import classify_cuda_api, load_sync_registry


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_gzip_jsonl(path: Path, rows: list[dict]) -> dict[str, object]:
    with path.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as compressed:
            for row in rows:
                compressed.write(
                    (json.dumps(row, sort_keys=True, separators=(",", ":")) + "\n").encode()
                )
    return {
        "filename": path.name,
        "record_count": len(rows),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def _identity(phase: str, kind: str) -> dict[str, object]:
    return {
        "kind": kind,
        "experiment_id": "exp-1",
        "wmpc_id": "wmpc-1",
        "run_id": "run-1",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": "request-1",
        "repeat_id": "repeat-1",
        "phase": phase,
    }


def _nvtx(record_id: str, start: int, end: int, phase: str, kind: str) -> dict:
    return {
        "record_id": record_id,
        "source_table": "NVTX_EVENTS",
        "source_rowid": int(record_id.rsplit(":", 1)[1]),
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "start_ns": start,
        "end_ns": end,
        "global_tid": 101,
        "process_id": 1,
        "thread_id": 1,
        "event_type": "NVTX_RANGE",
        "text": "EXPOSEDPATH_JSON_V1:" + json.dumps(_identity(phase, kind)),
        "structured_identity": _identity(phase, kind),
        "range_id": None,
        "category_id": None,
        "color": None,
        "end_global_tid": None,
        "end_process_id": None,
        "end_thread_id": None,
        "text_id": None,
        "domain_id": None,
        "json_text": None,
    }


def _nvtx_for_request(
    record_id: str, start: int, end: int, phase: str, kind: str, request_id: str
) -> dict:
    record = _nvtx(record_id, start, end, phase, kind)
    record["structured_identity"]["request_id"] = request_id
    record["text"] = "EXPOSEDPATH_JSON_V1:" + json.dumps(record["structured_identity"])
    return record


def _replace_nvtx(canonical_manifest: Path, rows: list[dict]) -> None:
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    replacement = nvtx_path.with_name("replacement-nvtx.jsonl.gz")
    entry = _write_gzip_jsonl(replacement, rows)
    replacement.replace(nvtx_path)
    entry["filename"] = nvtx_path.name
    manifest["files"]["nvtx"] = entry
    canonical_manifest.write_text(json.dumps(manifest), encoding="utf-8")


def _replace_cuda_api(canonical_manifest: Path, rows: list[dict]) -> None:
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    api_path = canonical_manifest.parent / manifest["files"]["cuda_api"]["filename"]
    replacement = api_path.with_name("replacement-cuda-api.jsonl.gz")
    entry = _write_gzip_jsonl(replacement, rows)
    replacement.replace(api_path)
    entry["filename"] = api_path.name
    manifest["files"]["cuda_api"] = entry
    canonical_manifest.write_text(json.dumps(manifest), encoding="utf-8")


def _cuda_sync() -> dict:
    return {
        "record_id": "cuda_sync:CUPTI_ACTIVITY_KIND_SYNCHRONIZATION:1",
        "source_table": "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION",
        "source_rowid": 1,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "start_ns": 70,
        "end_ns": 80,
        "device_id": 0,
        "context_id": 10,
        "stream_id": 11,
        "correlation_id": 7,
        "sync_type_id": 1,
        "sync_type_name": "STREAM_SYNCHRONIZE",
        "sync_type_label": "stream",
        "runtime_mapping_count": 1,
        "runtime_api_name": "cudaStreamSynchronize",
        "global_pid": None,
        "process_id": 1,
        "green_context_id": None,
        "event_id": None,
        "event_sync_id": None,
        "runtime_record_id": "cuda_api:CUPTI_ACTIVITY_KIND_RUNTIME:1",
        "runtime_start_ns": 70,
        "runtime_end_ns": 80,
        "runtime_global_tid": 101,
        "runtime_thread_id": 1,
    }


def _activity() -> dict:
    return {
        "record_id": "device_activity:CUPTI_ACTIVITY_KIND_KERNEL:1",
        "source_table": "CUPTI_ACTIVITY_KIND_KERNEL",
        "source_rowid": 1,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "activity_kind": "KERNEL",
        "start_ns": 50,
        "end_ns": 75,
        "device_id": 0,
        "context_id": 10,
        "stream_id": 11,
        "name": "kernel",
        "attributes": {},
        "correlation_id": 7,
        "global_pid": None,
        "process_id": 1,
        "green_context_id": None,
        "graph_node_id": None,
        "graph_id": None,
    }


def _cuda_api() -> dict:
    return {
        "record_id": "cuda_api:CUPTI_ACTIVITY_KIND_RUNTIME:1",
        "source_table": "CUPTI_ACTIVITY_KIND_RUNTIME",
        "source_rowid": 1,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "start_ns": 70,
        "end_ns": 80,
        "api_name": "cudaStreamSynchronize",
        "return_value": 0,
        "global_tid": 101,
        "process_id": 1,
        "thread_id": 1,
        "correlation_id": 7,
        "event_class": None,
        "name_id": None,
        "callchain_id": None,
    }


def _write_canonical(path: Path) -> Path:
    path.mkdir()
    schema = load_canonical_raw_schema()
    rows = {kind: [] for kind in schema["record_types"]}
    rows["nvtx"] = [
        _nvtx("nvtx:NVTX_EVENTS:1", 0, 100, "full_request", "request"),
        _nvtx("nvtx:NVTX_EVENTS:2", 0, 60, "prefill", "phase"),
        _nvtx("nvtx:NVTX_EVENTS:3", 60, 100, "decode", "phase"),
    ]
    rows["cuda_api"] = [_cuda_api()]
    rows["cuda_sync"] = [_cuda_sync()]
    rows["device_activity"] = [_activity()]
    files = {
        kind: _write_gzip_jsonl(path / spec["filename"], rows[kind])
        for kind, spec in schema["record_types"].items()
    }
    manifest = {
        "schema_version": schema["schema_version"],
        "measurement_contract_version": schema["measurement_contract_version"],
        "adapter_id": schema["adapter_id"],
        "analyzer_version": "test",
        "generated_at_utc": "2026-09-12T00:00:00+00:00",
        "data_role": "Engineering",
        "source": {"sqlite": {"sha256": "A" * 64}},
        "clock": schema["clock_model"],
        "identity": {"status": "VALID", "issues": []},
        "execution_context": {"default_stream_mode": "PER_THREAD", "selected_device_id": 0},
        "files": files,
        "observation_validity": {"status": "valid", "issues": []},
        "research_eligibility": {"formal_evidence": False, "q0_status": "NOT_RUN"},
    }
    manifest_path = path / "canonical_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _s_record() -> dict:
    sync = _cuda_sync()
    rule = classify_cuda_api("cudaStreamSynchronize")
    terminal = {
        "status": "VALID",
        "kind": "ACTIVITY",
        "activity_id": _activity()["record_id"],
        "end_ns": 75,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
    }
    return {
        "sync_id": sync["record_id"],
        "registry_rule_id": rule["registry_rule_id"],
        "sync_universe_class": rule["universe_class"],
        "sync_kind": rule["sync_kind"],
        "request_id": "request-1",
        "repeat_id": "repeat-1",
        "sync_owner_phase": "decode",
        "sync_origin": None,
        "callsite_id": None,
        "sync_ordinal": None,
        "host_start_ns": 70,
        "host_end_ns": 80,
        "device_id": 0,
        "context_id": 10,
        "stream_id": 11,
        "event_id": None,
        "completion_scope": rule["completion_scope"],
        "submission_evidence": [],
        "dependency_closure_status": "COMPLETE",
        "dependency_edges": [],
        "event_record_id": None,
        "wait_set_status": "VALID_NONEMPTY",
        "wait_set_activity_ids": [_activity()["record_id"]],
        "semantic_frontier_activity_ids": [_activity()["record_id"]],
        "terminal": terminal,
        "validity": "VALID_NONEMPTY",
        "primary_reason": None,
        "secondary_reasons": [],
        "activity_origin_phases": ["prefill"],
        "terminal_origin_phase": "prefill",
        "cross_phase_dependency": True,
        "invocation_bleed": False,
    }


def _write_s_bundle(path: Path, canonical_manifest: Path, records: list[dict] | None = None) -> Path:
    path.mkdir()
    schema = load_s_layer_schema()
    records = [_s_record()] if records is None else records
    assert all(set(record) == set(schema["sync_record_fields"]) for record in records)
    entry = _write_gzip_jsonl(path / schema["sync_records_filename"], records)
    registry_path = Path("docs/v1_4_1/contracts/sync_semantics_registry_v0_2.json")
    manifest = {
        "schema_version": schema["schema_version"],
        "measurement_contract_version": schema["measurement_contract_version"],
        "input_schema_version": schema["input_schema_version"],
        "analyzer_version": "test",
        "generated_at_utc": "2026-09-12T00:00:00+00:00",
        "data_role": "Engineering",
        "source": {
            "canonical_manifest_name": canonical_manifest.name,
            "canonical_manifest_sha256": _sha256(canonical_manifest),
            "source_sqlite_sha256": "A" * 64,
            "sync_registry": {
                "version": load_sync_registry()["registry_version"],
                "sha256": _sha256(registry_path),
            },
        },
        "input_validity": {"status": "VALID", "reasons": []},
        "files": {"sync_records": entry},
        "summary": {
            "physical_sync_count": len(records),
            "valid_nonempty_count": len(records),
            "valid_empty_count": 0,
            "ambiguous_count": 0,
            "invalid_count": 0,
        },
        "research_eligibility": {
            "formal_evidence": False,
            "q0_status": "NOT_RUN",
            "scope": "S_LAYER_ONLY",
        },
    }
    manifest_path = path / "s_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def test_loads_strict_dual_input_and_discovers_three_structured_windows(tmp_path):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)

    assert [window.phase for window in inputs.windows] == ["full_request", "prefill", "decode"]
    assert [(window.start_ns, window.end_ns) for window in inputs.windows] == [
        (0, 100), (0, 60), (60, 100),
    ]
    assert inputs.s_records[0]["wait_set_activity_ids"] == [
        "device_activity:CUPTI_ACTIVITY_KIND_KERNEL:1"
    ]
    assert inputs.global_quality_reasons == ()


@pytest.mark.parametrize("mutation", [
    "terminal_time", "terminal_clock", "terminal_not_in_wait_set", "empty_wait_set",
    "terminal_not_in_frontier", "wait_status", "closure_status", "valid_reason",
    "invalid_valid_terminal", "ambiguous_valid_terminal", "empty_nonempty_wait_set",
    "empty_valid_terminal", "boundary_after_sync", "boundary_no_clock", "boundary_wrong_clock",
    "boundary_with_activity", "valid_terminal_status", "invocation_bleed",
])
def test_strict_join_rejects_inconsistent_s_state_before_accounting(tmp_path, mutation):
    canonical = _write_canonical(tmp_path / "canonical")
    record = _s_record()
    if mutation == "terminal_time":
        record["terminal"]["end_ns"] = 74
    elif mutation == "terminal_clock":
        record["terminal"]["clock_domain_id"] = "other-clock"
    elif mutation in {"terminal_not_in_wait_set", "empty_wait_set"}:
        record["wait_set_activity_ids"] = []
        if mutation == "empty_wait_set":
            record["terminal"].update(kind="COMPLETION_BOUNDARY", activity_id=None)
        else:
            other = _activity()
            other["record_id"] = "device_activity:CUPTI_ACTIVITY_KIND_KERNEL:2"
            other["source_rowid"] = 2
            manifest = json.loads(canonical.read_text(encoding="utf-8"))
            activity_path = canonical.parent / manifest["files"]["device_activity"]["filename"]
            replacement = activity_path.with_name("replacement-activities.jsonl.gz")
            entry = _write_gzip_jsonl(replacement, [_activity(), other])
            replacement.replace(activity_path)
            entry["filename"] = activity_path.name
            manifest["files"]["device_activity"] = entry
            canonical.write_text(json.dumps(manifest), encoding="utf-8")
            record["wait_set_activity_ids"] = [other["record_id"]]
            record["semantic_frontier_activity_ids"] = [other["record_id"]]
    elif mutation == "terminal_not_in_frontier":
        record["semantic_frontier_activity_ids"] = []
    elif mutation == "wait_status":
        record["wait_set_status"] = "INVALID"
    elif mutation == "closure_status":
        record["dependency_closure_status"] = "AMBIGUOUS"
    elif mutation == "valid_reason":
        record["primary_reason"] = "TERMINAL_TIE"
    elif mutation in {"invalid_valid_terminal", "ambiguous_valid_terminal"}:
        record["validity"] = record["wait_set_status"] = mutation.split("_")[0].upper()
        record["primary_reason"] = "TERMINAL_TIE"
    elif mutation.startswith("empty_"):
        record["validity"] = record["wait_set_status"] = "VALID_EMPTY"
        if mutation == "empty_nonempty_wait_set":
            record["terminal"] = dict(status="NOT_APPLICABLE", kind="NONE", activity_id=None, end_ns=None, clock_domain_id=None)
        else:
            record["wait_set_activity_ids"] = []
            record["semantic_frontier_activity_ids"] = []
    elif mutation.startswith("boundary_"):
        record["terminal"].update(kind="COMPLETION_BOUNDARY", activity_id=None)
        if mutation == "boundary_after_sync":
            record["terminal"]["end_ns"] = 81
        elif mutation == "boundary_no_clock":
            record["terminal"]["clock_domain_id"] = None
        elif mutation == "boundary_wrong_clock":
            record["terminal"]["clock_domain_id"] = "other-clock"
        else:
            record["terminal"]["activity_id"] = _activity()["record_id"]
    elif mutation == "valid_terminal_status":
        record["terminal"]["status"] = "INVALID"
    else:
        record["invocation_bleed"] = True
    s_manifest = _write_s_bundle(tmp_path / "s", canonical, [record])
    with pytest.raises(ABInputError):
        load_ab_inputs(canonical, s_manifest)


@pytest.mark.parametrize("validity", ["VALID_NONEMPTY", "VALID_EMPTY", "INVALID", "AMBIGUOUS"])
def test_strict_join_preserves_consistent_boundary_and_nonvalid_states(tmp_path, validity):
    canonical = _write_canonical(tmp_path / "canonical")
    record = _s_record()
    record["validity"] = record["wait_set_status"] = validity
    if validity == "VALID_NONEMPTY":
        record["terminal"].update(kind="COMPLETION_BOUNDARY", activity_id=None)
    else:
        status = "NOT_APPLICABLE" if validity == "VALID_EMPTY" else validity
        record["terminal"] = dict(status=status, kind="NONE", activity_id=None, end_ns=None, clock_domain_id=None)
        if validity == "VALID_EMPTY":
            record["wait_set_activity_ids"] = []
            record["semantic_frontier_activity_ids"] = []
        else:
            record["primary_reason"] = "TERMINAL_TIE" if validity == "AMBIGUOUS" else "TERMINAL_AFTER_SYNC_END"
    s_manifest = _write_s_bundle(tmp_path / "s", canonical, [record])
    assert load_ab_inputs(canonical, s_manifest).s_records[0] == record


@pytest.mark.parametrize("second_start,expected_requests", [(50, ["request-3"]), (100, ["request-1", "request-2", "request-3"])])
def test_cross_invocation_overlap_rejects_only_affected_windows_and_allows_adjacency(tmp_path, second_start, expected_requests):
    canonical = _write_canonical(tmp_path / "canonical")
    rows = []
    for index, (request, start) in enumerate([("request-1", 0), ("request-2", second_start), ("request-3", 300)]):
        for offset, (phase, kind, begin, end) in enumerate([
            ("full_request", "request", start, start + 100),
            ("prefill", "phase", start, start + 60),
            ("decode", "phase", start + 60, start + 100),
        ]):
            rows.append(_nvtx_for_request(f"nvtx:NVTX_EVENTS:{index * 3 + offset + 1}", begin, end, phase, kind, request))
    _replace_nvtx(canonical, rows)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical)
    inputs = load_ab_inputs(canonical, s_manifest)
    assert sorted({w.request_id for w in inputs.windows}) == expected_requests
    assert sorted({row["request_id"] for row in calculate_a_windows(inputs)}) == expected_requests
    assert inputs.global_quality_reasons == ()
    if second_start == 50:
        assert {issue.request_id for issue in inputs.window_discovery_issues} == {"request-1", "request-2"}
        assert all("WINDOW_CROSS_INVOCATION_OVERLAP" in issue.reasons for issue in inputs.window_discovery_issues)
    else:
        assert inputs.window_discovery_issues == ()


@pytest.mark.parametrize("marker_only", [False, True])
def test_zero_window_discovery_has_machine_readable_issue(tmp_path, marker_only):
    canonical = _write_canonical(tmp_path / "canonical")
    rows = [_nvtx("nvtx:NVTX_EVENTS:1", 0, 100, "full_request", "marker")] if marker_only else []
    _replace_nvtx(canonical, rows)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical)
    inputs = load_ab_inputs(canonical, s_manifest)
    assert inputs.windows == ()
    assert len(inputs.window_discovery_issues) == 1
    issue = inputs.window_discovery_issues[0]
    assert "WINDOW_DISCOVERY_INVALID" in issue.reasons
    assert issue.source_nvtx_record_ids == (("nvtx:NVTX_EVENTS:1",) if marker_only else ())


def test_overlapping_full_request_with_missing_phase_still_invalidates_other_invocation(tmp_path):
    canonical = _write_canonical(tmp_path / "canonical")
    rows = [
        _nvtx("nvtx:NVTX_EVENTS:1", 0, 100, "full_request", "request"),
        _nvtx("nvtx:NVTX_EVENTS:2", 0, 60, "prefill", "phase"),
        _nvtx("nvtx:NVTX_EVENTS:3", 60, 100, "decode", "phase"),
        _nvtx_for_request("nvtx:NVTX_EVENTS:4", 50, 150, "full_request", "request", "request-2"),
    ]
    _replace_nvtx(canonical, rows)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical)
    inputs = load_ab_inputs(canonical, s_manifest)
    assert inputs.windows == ()
    assert {issue.request_id for issue in inputs.window_discovery_issues} == {"request-1", "request-2"}
    assert all("WINDOW_CROSS_INVOCATION_OVERLAP" in issue.reasons for issue in inputs.window_discovery_issues)


def test_worker_marker_does_not_define_windows_but_proves_multithread_api_union_after_real_discovery(tmp_path):
    """A marker proves worker ownership only; request/phase ranges remain the sole A windows."""

    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx_rows = [json.loads(line) for line in handle]
    worker_marker = _nvtx("nvtx:NVTX_EVENTS:4", 0, 100, "full_request", "marker")
    worker_marker["global_tid"] = 202
    nvtx_rows.append(worker_marker)
    _replace_nvtx(canonical_manifest, nvtx_rows)

    api_path = canonical_manifest.parent / manifest["files"]["cuda_api"]["filename"]
    with gzip.open(api_path, "rt", encoding="utf-8") as handle:
        api_rows = [json.loads(line) for line in handle]
    main_query = deepcopy(api_rows[0])
    main_query.update({
        "record_id": "cuda_api:CUPTI_ACTIVITY_KIND_RUNTIME:2",
        "source_rowid": 2,
        "start_ns": 10,
        "end_ns": 30,
        "api_name": "cudaEventQuery",
        "global_tid": 101,
        "thread_id": 1,
        "correlation_id": None,
    })
    worker_query = deepcopy(main_query)
    worker_query.update({
        "record_id": "cuda_api:CUPTI_ACTIVITY_KIND_RUNTIME:3",
        "source_rowid": 3,
        "start_ns": 20,
        "end_ns": 40,
        "global_tid": 202,
        "thread_id": 2,
    })
    _replace_cuda_api(canonical_manifest, [*api_rows, main_query, worker_query])
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)
    records = {record["phase"]: record for record in calculate_a_windows(inputs)}

    assert [(window.phase, window.start_ns, window.end_ns) for window in inputs.windows] == [
        ("full_request", 0, 100),
        ("prefill", 0, 60),
        ("decode", 60, 100),
    ]
    assert inputs.window_discovery_issues == ()
    assert records["full_request"]["A_cuda_api_ns"] == 30
    assert records["full_request"]["A_cuda_api_non_submit_ns"] == 30
    assert records["prefill"]["A_cuda_api_ns"] == 30
    assert records["decode"]["A_cuda_api_ns"] == 0


def test_spoofed_worker_marker_text_cannot_prove_api_ownership_after_real_discovery(tmp_path):
    """A marker text/cache conflict cannot turn an external worker API into current-request time."""

    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx_rows = [json.loads(line) for line in handle]
    worker_marker = _nvtx("nvtx:NVTX_EVENTS:4", 0, 100, "full_request", "marker")
    worker_marker["global_tid"] = 202
    external_marker_identity = _identity("full_request", "marker")
    external_marker_identity["request_id"] = "external-request"
    worker_marker["text"] = "EXPOSEDPATH_JSON_V1:" + json.dumps(external_marker_identity)
    nvtx_rows.append(worker_marker)
    _replace_nvtx(canonical_manifest, nvtx_rows)

    api_path = canonical_manifest.parent / manifest["files"]["cuda_api"]["filename"]
    with gzip.open(api_path, "rt", encoding="utf-8") as handle:
        api_rows = [json.loads(line) for line in handle]
    worker_query = deepcopy(api_rows[0])
    worker_query.update({
        "record_id": "cuda_api:CUPTI_ACTIVITY_KIND_RUNTIME:2",
        "source_rowid": 2,
        "start_ns": 20,
        "end_ns": 40,
        "api_name": "cudaEventQuery",
        "global_tid": 202,
        "thread_id": 2,
        "correlation_id": None,
    })
    _replace_cuda_api(canonical_manifest, [*api_rows, worker_query])
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)
    records = {record["phase"]: record for record in calculate_a_windows(inputs)}

    assert [window.phase for window in inputs.windows] == ["full_request", "prefill", "decode"]
    assert inputs.window_discovery_issues == ()
    assert records["full_request"]["A_cuda_api_ns"] == 0
    assert records["full_request"]["A_unattributed_ns"] == 20
    assert records["full_request"]["primary_reason"] == "CUDA_API_OWNERSHIP_EVIDENCE_INVALID"
    assert records["prefill"]["A_cuda_api_ns"] == 0
    assert records["prefill"]["A_unattributed_ns"] == 20


@pytest.mark.parametrize(
    ("path", "mutate", "message"),
    [
        ("canonical", lambda manifest: manifest.__setitem__("schema_version", "wrong"), "schema_version"),
        ("s", lambda manifest: manifest.__setitem__("measurement_contract_version", "wrong"), "Measurement Contract"),
        ("s", lambda manifest: manifest["source"].__setitem__("canonical_manifest_sha256", "B" * 64), "Canonical manifest SHA-256"),
        ("s", lambda manifest: manifest["source"].__setitem__("source_sqlite_sha256", "B" * 64), "source SQLite"),
    ],
)
def test_rejects_schema_contract_and_lineage_conflicts_before_any_ab_output(
    tmp_path, path, mutate, message
):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)
    target = canonical_manifest if path == "canonical" else s_manifest
    manifest = json.loads(target.read_text(encoding="utf-8"))
    mutate(manifest)
    target.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ABInputError, match=message):
        load_ab_inputs(canonical_manifest, s_manifest)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda record: record.__setitem__("host_end_ns", 81), "host_end_ns"),
        (lambda record: record.__setitem__("registry_rule_id", "wrong"), "registry_rule_id"),
        (lambda record: record.__setitem__("wait_set_activity_ids", ["missing-activity"]), "wait_set"),
        (lambda record: record["terminal"].__setitem__("activity_id", "missing-activity"), "terminal"),
    ],
)
def test_rejects_sync_identity_and_s_references_not_backfilled_from_raw(tmp_path, mutate, message):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    record = _s_record()
    mutate(record)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest, [record])

    with pytest.raises(ABInputError, match=message):
        load_ab_inputs(canonical_manifest, s_manifest)


@pytest.mark.parametrize(
    ("records", "message"),
    [([], "缺少"), ([_s_record(), _s_record()], "重复"), ([{**_s_record(), "sync_id": "extra"}], "多余")],
)
def test_requires_one_s_record_for_every_canonical_physical_sync(tmp_path, records, message):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest, deepcopy(records))

    with pytest.raises(ABInputError, match=message):
        load_ab_inputs(canonical_manifest, s_manifest)


@pytest.mark.parametrize(
    ("mutate", "reason"),
    [
        (lambda nvtx: nvtx.pop(), "WINDOW_PHASE_MISSING_OR_DUPLICATE"),
        (lambda nvtx: nvtx.append(deepcopy(nvtx[1])), "WINDOW_PHASE_MISSING_OR_DUPLICATE"),
        (lambda nvtx: nvtx.__setitem__(2, _nvtx("nvtx:NVTX_EVENTS:3", 59, 100, "decode", "phase")), "WINDOW_PHASE_BOUNDARY_INCONSISTENT"),
    ],
)
def test_invalid_phase_boundaries_are_recorded_without_timestamp_order_inference(tmp_path, mutate, reason):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx = [json.loads(line) for line in handle]
    mutate(nvtx)
    _replace_nvtx(canonical_manifest, nvtx)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)
    assert discover_request_phase_windows(inputs.canonical) == ()
    assert inputs.global_quality_reasons == ()
    assert inputs.window_discovery_issues[0].reasons == (reason,)


def test_global_invalid_evidence_is_preserved_as_quality_reason_not_a_loader_error(tmp_path):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    manifest["observation_validity"] = {
        "status": "invalid",
        "issues": [{"code": "DROPPED_CUPTI_RECORDS"}],
    }
    manifest["identity"] = {"status": "AMBIGUOUS", "issues": []}
    canonical_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)

    assert "TRACE_DROPPED_RECORDS" in inputs.global_quality_reasons
    assert "INVOCATION_OWNERSHIP_AMBIGUOUS" in inputs.global_quality_reasons


def test_text_identity_mismatch_becomes_identity_scoped_issue_without_spoofed_window(tmp_path):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx = [json.loads(line) for line in handle]
    nvtx[1]["structured_identity"]["request_id"] = "spoofed-request"
    _replace_nvtx(canonical_manifest, nvtx)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)

    assert inputs.windows == ()
    assert inputs.global_quality_reasons == ()
    assert len(inputs.window_discovery_issues) == 1
    assert inputs.window_discovery_issues[0].request_id == "request-1"
    assert inputs.window_discovery_issues[0].reasons == ("STRUCTURED_IDENTITY_TEXT_MISMATCH",)


def test_one_bad_logical_identity_does_not_make_other_windows_globally_invalid(tmp_path):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx = [json.loads(line) for line in handle]
    nvtx.pop(0)
    nvtx.extend(
        [
            _nvtx_for_request("nvtx:NVTX_EVENTS:4", 100, 200, "full_request", "request", "request-2"),
            _nvtx_for_request("nvtx:NVTX_EVENTS:5", 100, 150, "prefill", "phase", "request-2"),
            _nvtx_for_request("nvtx:NVTX_EVENTS:6", 150, 200, "decode", "phase", "request-2"),
        ]
    )
    _replace_nvtx(canonical_manifest, nvtx)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)

    assert [(window.request_id, window.phase) for window in inputs.windows] == [
        ("request-2", "full_request"),
        ("request-2", "prefill"),
        ("request-2", "decode"),
    ]
    assert inputs.global_quality_reasons == ()
    assert len(inputs.window_discovery_issues) == 1
    assert inputs.window_discovery_issues[0].request_id == "request-1"
    assert inputs.window_discovery_issues[0].reasons == ("WINDOW_PHASE_MISSING_OR_DUPLICATE",)


def test_missing_text_prefix_creates_unkeyed_issue_without_trusting_cached_identity(tmp_path):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx = [json.loads(line) for line in handle]
    nvtx[1]["text"] = "legacy-prefill"
    _replace_nvtx(canonical_manifest, nvtx)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)

    assert inputs.windows == ()
    assert inputs.global_quality_reasons == ()
    unkeyed = [issue for issue in inputs.window_discovery_issues if issue.request_id is None]
    assert len(unkeyed) == 1
    issue = unkeyed[0]
    assert issue.request_id is None
    assert issue.reasons == ("STRUCTURED_IDENTITY_TEXT_PREFIX_MISSING",)
    assert issue.source_nvtx_record_ids == ("nvtx:NVTX_EVENTS:2",)


def test_all_missing_text_prefixes_are_one_unkeyed_machine_readable_issue(tmp_path):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx = [json.loads(line) for line in handle]
    for record in nvtx:
        record["text"] = "legacy-unstructured-range"
    _replace_nvtx(canonical_manifest, nvtx)
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    inputs = load_ab_inputs(canonical_manifest, s_manifest)

    assert inputs.windows == ()
    assert inputs.global_quality_reasons == ()
    assert len(inputs.window_discovery_issues) == 1
    issue = inputs.window_discovery_issues[0]
    assert issue.request_id is None
    assert issue.reasons == ("STRUCTURED_IDENTITY_TEXT_PREFIX_MISSING",)
    assert issue.source_nvtx_record_ids == (
        "nvtx:NVTX_EVENTS:1",
        "nvtx:NVTX_EVENTS:2",
        "nvtx:NVTX_EVENTS:3",
    )
