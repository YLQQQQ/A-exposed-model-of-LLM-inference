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
        "dependency_closure_status": "VALID",
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
        (lambda nvtx: nvtx.pop(), "WINDOW_DISCOVERY_INVALID"),
        (lambda nvtx: nvtx.append(deepcopy(nvtx[1])), "WINDOW_DISCOVERY_INVALID"),
        (lambda nvtx: nvtx.__setitem__(2, _nvtx("nvtx:NVTX_EVENTS:3", 59, 100, "decode", "phase")), "WINDOW_DISCOVERY_INVALID"),
    ],
)
def test_invalid_phase_boundaries_are_recorded_without_timestamp_order_inference(tmp_path, mutate, reason):
    canonical_manifest = _write_canonical(tmp_path / "canonical")
    manifest = json.loads(canonical_manifest.read_text(encoding="utf-8"))
    nvtx_path = canonical_manifest.parent / manifest["files"]["nvtx"]["filename"]
    with gzip.open(nvtx_path, "rt", encoding="utf-8") as handle:
        nvtx = [json.loads(line) for line in handle]
    mutate(nvtx)
    replacement = nvtx_path.with_name("replacement-nvtx.jsonl.gz")
    entry = _write_gzip_jsonl(replacement, nvtx)
    replacement.replace(nvtx_path)
    entry["filename"] = nvtx_path.name
    manifest["files"]["nvtx"] = entry
    canonical_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    s_manifest = _write_s_bundle(tmp_path / "s", canonical_manifest)

    assert discover_request_phase_windows(load_ab_inputs(canonical_manifest, s_manifest).canonical) == ()
    assert reason in load_ab_inputs(canonical_manifest, s_manifest).global_quality_reasons


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
