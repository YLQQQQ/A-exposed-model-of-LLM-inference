"""Canonical Raw v0.2 数据合同与转换测试。"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import gzip
import json
from pathlib import Path
import sqlite3
import subprocess
import sys

import pytest

from exposedpath_v141.canonical_raw import (
    CanonicalRawSchemaError,
    convert_sqlite_to_canonical,
    load_canonical_raw_schema,
    validate_canonical_raw_schema,
)
from exposedpath_v141.cli import main
from scripts.verify_canonical_raw_boundary import check_source as check_downstream_source


SQLITE_SCHEMA = """
CREATE TABLE META_DATA_CAPTURE(name TEXT NOT NULL, value TEXT);
CREATE TABLE META_DATA_EXPORT(name TEXT NOT NULL, value TEXT);
CREATE TABLE StringIds(id INTEGER PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE NVTX_EVENTS(start INTEGER NOT NULL, end INTEGER, eventType INTEGER NOT NULL,
 rangeId INTEGER, category INTEGER, color INTEGER, text TEXT, globalTid INTEGER,
 endGlobalTid INTEGER, textId INTEGER, domainId INTEGER, jsonText TEXT);
CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(start INTEGER NOT NULL, end INTEGER NOT NULL,
 eventClass INTEGER NOT NULL, globalTid INTEGER, correlationId INTEGER, nameId INTEGER NOT NULL,
 returnValue INTEGER NOT NULL, callchainId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL, correlationId INTEGER, globalPid INTEGER,
 deprecatedSyncType INTEGER, syncType INTEGER NOT NULL, eventId INTEGER NOT NULL,
 eventSyncId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL, correlationId INTEGER, globalPid INTEGER,
 demangledName INTEGER NOT NULL, shortName INTEGER NOT NULL, graphNodeId INTEGER, graphId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL, correlationId INTEGER, globalPid INTEGER, bytes INTEGER NOT NULL,
 copyKind INTEGER NOT NULL, srcKind INTEGER, dstKind INTEGER, graphNodeId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_MEMSET(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL, correlationId INTEGER, globalPid INTEGER, value INTEGER NOT NULL,
 bytes INTEGER NOT NULL, graphNodeId INTEGER, memKind INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_CUDA_EVENT(timestamp INTEGER, deviceId INTEGER NOT NULL,
 contextId INTEGER NOT NULL, greenContextId INTEGER, streamId INTEGER NOT NULL,
 correlationId INTEGER, globalPid INTEGER, eventId INTEGER NOT NULL, eventSyncId INTEGER);
CREATE TABLE ENUM_CUPTI_SYNC_TYPE(id INTEGER NOT NULL, name TEXT, label TEXT);
CREATE TABLE TARGET_INFO_CUDA_CONTEXT_INFO(nullStreamId INTEGER NOT NULL, hwId INTEGER NOT NULL,
 vmId INTEGER NOT NULL, processId INTEGER NOT NULL, deviceId INTEGER NOT NULL,
 contextId INTEGER NOT NULL, parentContextId INTEGER, isGreenContext INTEGER);
CREATE TABLE TARGET_INFO_CUDA_STREAM(streamId INTEGER NOT NULL, hwId INTEGER NOT NULL,
 vmId INTEGER NOT NULL, processId INTEGER NOT NULL, contextId INTEGER NOT NULL,
 priority INTEGER NOT NULL, flag INTEGER NOT NULL);
CREATE TABLE TARGET_INFO_GPU(id INTEGER NOT NULL, name TEXT);
CREATE TABLE DIAGNOSTIC_EVENT(timestamp INTEGER NOT NULL, source INTEGER NOT NULL,
 severity INTEGER NOT NULL, text TEXT NOT NULL);
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _make_source_sqlite(path: Path) -> int:
    global_tid = (1 << 56) | (2 << 48) | (3 << 24) | 4
    global_pid = (1 << 56) | (2 << 48) | (3 << 24)
    connection = sqlite3.connect(path)
    connection.executescript(SQLITE_SCHEMA)
    connection.executemany(
        "INSERT INTO META_DATA_EXPORT VALUES (?,?)",
        [
            ("EXPORT_PRODUCT_VERSION", "2026.1.1.204"),
            ("EXPORT_SCHEMA_VERSION", "3.24.14"),
            ("EXPORT_PARAM_LAZY", "false"),
        ],
    )
    connection.executemany(
        "INSERT INTO META_DATA_CAPTURE VALUES (?,?)",
        [("CAPTURE_EVENT_TYPE", "Cuda"), ("CAPTURE_EVENT_TYPE", "NvtxEvents")],
    )
    connection.executemany(
        "INSERT INTO StringIds VALUES (?,?)",
        [(1, "cudaStreamSynchronize"), (2, "myKernel")],
    )
    connection.execute(
        "INSERT INTO NVTX_EVENTS VALUES (10,90,59,NULL,NULL,NULL,'full_request',?,NULL,NULL,NULL,NULL)",
        (global_tid,),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (40,80,0,?,7,1,0,NULL)",
        (global_tid,),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(45,75,0,1,NULL,2,7,?,NULL,3,4294967295,NULL)",
        (global_pid,),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES "
        "(20,70,0,1,NULL,2,6,?,2,2,NULL,NULL)",
        (global_pid,),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES "
        "(15,18,0,1,NULL,2,5,?,64,1,1,2,NULL)",
        (global_pid,),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_MEMSET VALUES "
        "(18,19,0,1,NULL,2,5,?,0,64,NULL,2)",
        (global_pid,),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_CUDA_EVENT VALUES "
        "(30,0,1,NULL,2,8,?,9,10)",
        (global_pid,),
    )
    connection.execute(
        "INSERT INTO ENUM_CUPTI_SYNC_TYPE VALUES (3,'STREAM_SYNCHRONIZE','Stream sync')"
    )
    connection.execute(
        "INSERT INTO TARGET_INFO_CUDA_CONTEXT_INFO VALUES (0,1,2,3,0,1,NULL,0)"
    )
    connection.execute(
        "INSERT INTO TARGET_INFO_CUDA_STREAM VALUES (2,1,2,3,1,0,0)"
    )
    connection.execute("INSERT INTO TARGET_INFO_GPU VALUES (0,'test-gpu')")
    connection.commit()
    connection.close()
    return global_tid


def _make_manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "experiment_id": "exp",
                "wmpc_id": "w01",
                "run_id": "run-1",
                "run_role": "Engineering",
                "pass_id": "Pass1",
                "repeat_id": "r0",
            }
        ),
        encoding="utf-8",
    )


def _read_jsonl(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def test_committed_canonical_raw_schema_is_valid():
    validate_canonical_raw_schema(load_canonical_raw_schema())


def test_all_required_record_kinds_are_frozen():
    schema = load_canonical_raw_schema()

    assert set(schema["record_types"]) == {
        "nvtx",
        "cuda_api",
        "cuda_sync",
        "device_activity",
        "cuda_event",
        "context",
        "stream",
        "diagnostic",
    }


def test_missing_record_kind_is_rejected():
    schema = deepcopy(load_canonical_raw_schema())
    del schema["record_types"]["cuda_sync"]

    with pytest.raises(CanonicalRawSchemaError, match="record kind"):
        validate_canonical_raw_schema(schema)


def test_duplicate_or_overlapping_fields_are_rejected():
    schema = deepcopy(load_canonical_raw_schema())
    schema["record_types"]["nvtx"]["required_non_null_fields"].append("record_id")

    with pytest.raises(CanonicalRawSchemaError, match="字段重复"):
        validate_canonical_raw_schema(schema)

    schema = deepcopy(load_canonical_raw_schema())
    schema["record_types"]["nvtx"]["nullable_fields"].append("record_id")

    with pytest.raises(CanonicalRawSchemaError, match="同时属于"):
        validate_canonical_raw_schema(schema)


@pytest.mark.parametrize(
    "forbidden",
    ["wait_set_activity_ids", "terminal", "A_device_wait_ns", "B_status"],
)
def test_raw_schema_rejects_s_or_accounting_fields(forbidden):
    schema = deepcopy(load_canonical_raw_schema())
    schema["record_types"]["cuda_sync"]["nullable_fields"].append(forbidden)

    with pytest.raises(CanonicalRawSchemaError, match="越层字段"):
        validate_canonical_raw_schema(schema)


def test_clock_and_source_identity_are_explicit():
    schema = load_canonical_raw_schema()

    assert schema["clock_model"] == {
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "unit": "ns",
        "comparison_scope": "SINGLE_SOURCE_TRACE_ONLY",
        "timestamp_normalization": "DISABLED",
    }
    assert schema["record_identity"]["tuple"] == [
        "source_sqlite_sha256",
        "source_table",
        "source_rowid",
    ]


def test_source_adapter_is_locked_to_reviewed_nsys_schema():
    schema = load_canonical_raw_schema()

    assert schema["source_adapters"] == [
        {
            "adapter_id": "NSYS-SQLITE-2026.1.1-3.24.14",
            "export_product_version": "2026.1.1.204",
            "export_schema_version": "3.24.14",
        }
    ]


def test_converter_preserves_input_and_writes_all_record_types(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)
    before = _sha256(database)

    manifest_path = convert_sqlite_to_canonical(
        database,
        tmp_path / "canonical",
        data_role="Engineering",
        raw_sha256="A" * 64,
        collector_version="2025.6.3",
        source_manifest=source_manifest,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert _sha256(database) == before
    assert set(manifest["files"]) == set(load_canonical_raw_schema()["record_types"])
    assert manifest["files"]["device_activity"]["record_count"] == 3
    assert manifest["files"]["cuda_sync"]["record_count"] == 1
    assert all((manifest_path.parent / item["filename"]).is_file() for item in manifest["files"].values())


def test_converter_resolves_names_ids_and_source_rows(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    global_tid = _make_source_sqlite(database)
    _make_manifest(source_manifest)

    manifest_path = convert_sqlite_to_canonical(
        database,
        tmp_path / "canonical",
        data_role="Engineering",
        raw_sha256="B" * 64,
        collector_version="synthetic",
        source_manifest=source_manifest,
    )
    cuda_api = _read_jsonl(manifest_path.parent / "cuda_api.jsonl.gz")[0]
    sync = _read_jsonl(manifest_path.parent / "cuda_sync.jsonl.gz")[0]
    activities = _read_jsonl(manifest_path.parent / "device_activity.jsonl.gz")

    assert cuda_api["api_name"] == "cudaStreamSynchronize"
    assert cuda_api["global_tid"] == global_tid
    assert (cuda_api["process_id"], cuda_api["thread_id"]) == (3, 4)
    assert sync["runtime_mapping_count"] == 1
    assert sync["runtime_api_name"] == "cudaStreamSynchronize"
    assert sync["record_id"] == "cuda_sync:CUPTI_ACTIVITY_KIND_SYNCHRONIZATION:1"
    assert [item["activity_kind"] for item in activities] == ["MEMCPY", "MEMSET", "KERNEL"]
    assert activities[-1]["name"] == "myKernel"


def test_record_files_are_deterministic_and_output_is_never_overwritten(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)

    first = convert_sqlite_to_canonical(
        database, tmp_path / "first", "Engineering", "C" * 64, "synthetic", source_manifest
    )
    second = convert_sqlite_to_canonical(
        database, tmp_path / "second", "Engineering", "C" * 64, "synthetic", source_manifest
    )
    first_manifest = json.loads(first.read_text(encoding="utf-8"))
    second_manifest = json.loads(second.read_text(encoding="utf-8"))

    assert first_manifest["files"] == second_manifest["files"]
    with pytest.raises(FileExistsError, match="拒绝覆盖"):
        convert_sqlite_to_canonical(
            database, tmp_path / "first", "Engineering", "C" * 64, "synthetic", source_manifest
        )


def test_structured_nvtx_identity_is_parsed_without_filename_inference(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)
    identity = {
        "kind": "phase",
        "experiment_id": "exp",
        "wmpc_id": "w01",
        "run_id": "run-1",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": "req-0",
        "repeat_id": "r0",
        "phase": "full_request",
    }
    connection = sqlite3.connect(database)
    connection.execute(
        "UPDATE NVTX_EVENTS SET text=?",
        ("EXPOSEDPATH_JSON_V1:" + json.dumps(identity, separators=(",", ":")),),
    )
    connection.commit()
    connection.close()

    manifest_path = convert_sqlite_to_canonical(
        database, tmp_path / "canonical", "Engineering", "D" * 64, "synthetic", source_manifest
    )
    nvtx = _read_jsonl(manifest_path.parent / "nvtx.jsonl.gz")[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert nvtx["structured_identity"] == identity
    assert manifest["identity"]["filename_inference_used"] is False
    assert manifest["identity"]["nvtx_status"] == "VALID"


def test_legacy_phase_label_is_preserved_but_identity_is_not_guessed(tmp_path):
    database = tmp_path / "source.sqlite"
    _make_source_sqlite(database)

    manifest_path = convert_sqlite_to_canonical(
        database, tmp_path / "canonical", "Engineering", "E" * 64, "synthetic"
    )
    nvtx = _read_jsonl(manifest_path.parent / "nvtx.jsonl.gz")[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert nvtx["text"] == "full_request"
    assert nvtx["structured_identity"] is None
    assert manifest["identity"]["status"] == "AMBIGUOUS"
    assert "UNSTRUCTURED_EXPOSEDPATH_PHASE_LABEL" in {
        issue["code"] for issue in manifest["identity"]["issues"]
    }
    assert "MISSING_SOURCE_MANIFEST" in {
        issue["code"] for issue in manifest["observation_validity"]["issues"]
    }


def test_malformed_structured_marker_is_preserved_and_marked_ambiguous(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)
    connection = sqlite3.connect(database)
    connection.execute("UPDATE NVTX_EVENTS SET text='EXPOSEDPATH_JSON_V1:{bad json'")
    connection.commit()
    connection.close()

    manifest_path = convert_sqlite_to_canonical(
        database, tmp_path / "canonical", "Engineering", "F" * 64, "synthetic", source_manifest
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["identity"]["nvtx_status"] == "AMBIGUOUS"
    assert "MALFORMED_STRUCTURED_NVTX" in {
        issue["code"] for issue in manifest["identity"]["issues"]
    }


def test_incomplete_structured_marker_does_not_receive_partial_identity(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "UPDATE NVTX_EVENTS SET text=?",
        (
            "EXPOSEDPATH_JSON_V1:"
            + json.dumps({"kind": "phase", "experiment_id": "exp", "phase": "prefill"}),
        ),
    )
    connection.commit()
    connection.close()

    manifest_path = convert_sqlite_to_canonical(
        database, tmp_path / "canonical", "Engineering", "0" * 64, "synthetic", source_manifest
    )
    nvtx = _read_jsonl(manifest_path.parent / "nvtx.jsonl.gz")[0]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert nvtx["structured_identity"] is None
    assert "INCOMPLETE_STRUCTURED_NVTX_IDENTITY" in {
        issue["code"] for issue in manifest["identity"]["issues"]
    }


def test_manifest_and_nvtx_identity_conflict_is_not_silently_accepted(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)
    identity = {
        "kind": "phase", "experiment_id": "exp", "wmpc_id": "w01",
        "run_id": "different-run", "run_role": "Engineering", "pass_id": "Pass1",
        "request_id": "req-0", "repeat_id": "r0", "phase": "full_request",
    }
    connection = sqlite3.connect(database)
    connection.execute(
        "UPDATE NVTX_EVENTS SET text=?",
        ("EXPOSEDPATH_JSON_V1:" + json.dumps(identity, separators=(",", ":")),),
    )
    connection.commit()
    connection.close()

    manifest_path = convert_sqlite_to_canonical(
        database, tmp_path / "canonical", "Engineering", "3" * 64, "synthetic", source_manifest
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["identity"]["status"] == "AMBIGUOUS"
    assert "MANIFEST_NVTX_IDENTITY_CONFLICT" in {
        issue["code"] for issue in manifest["identity"]["issues"]
    }


def test_cuda_event_linkage_is_preserved_separately_from_cuda_sync(tmp_path):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)

    manifest_path = convert_sqlite_to_canonical(
        database, tmp_path / "canonical", "Engineering", "1" * 64, "synthetic", source_manifest
    )
    event = _read_jsonl(manifest_path.parent / "cuda_event.jsonl.gz")[0]
    sync = _read_jsonl(manifest_path.parent / "cuda_sync.jsonl.gz")[0]

    assert (event["event_id"], event["event_sync_id"]) == (9, 10)
    assert event["record_id"].startswith("cuda_event:")
    assert sync["record_id"].startswith("cuda_sync:")


@pytest.mark.parametrize(
    ("mutation", "error_pattern"),
    [
        (
            "UPDATE META_DATA_EXPORT SET value='unknown' WHERE name='EXPORT_SCHEMA_VERSION'",
            "observation invalid",
        ),
        (
            "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (41,79,0,NULL,7,1,0,NULL)",
            "observation invalid",
        ),
        (
            "INSERT INTO DIAGNOSTIC_EVENT VALUES (1,1,2,'events may be missing')",
            "observation invalid",
        ),
        (
            "UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=80,end=70",
            "时间区间非法",
        ),
    ],
)
def test_invalid_evidence_refuses_conversion_and_leaves_no_output(
    tmp_path, mutation, error_pattern
):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)
    connection = sqlite3.connect(database)
    connection.execute(mutation)
    connection.commit()
    connection.close()
    output = tmp_path / "canonical"

    with pytest.raises(ValueError, match=error_pattern):
        convert_sqlite_to_canonical(
            database, output, "Engineering", "2" * 64, "synthetic", source_manifest
        )

    assert not output.exists()


def test_convert_sqlite_cli_reports_ambiguous_engineering_output(tmp_path, capsys):
    database = tmp_path / "source.sqlite"
    source_manifest = tmp_path / "run_manifest.json"
    _make_source_sqlite(database)
    _make_manifest(source_manifest)
    output = tmp_path / "canonical"

    return_code = main(
        [
            "convert-sqlite",
            "--sqlite", str(database),
            "--output-dir", str(output),
            "--data-role", "Engineering",
            "--raw-sha256", "4" * 64,
            "--collector-version", "synthetic",
            "--source-manifest", str(source_manifest),
        ]
    )
    printed = capsys.readouterr().out

    assert return_code == 2
    assert "identity_validity: AMBIGUOUS" in printed
    assert "q0_status: NOT_RUN" in printed
    assert (output / "canonical_manifest.json").is_file()


def test_downstream_boundary_rejects_direct_nsys_sqlite_access():
    source = """
import sqlite3

def recover_wait_set(connection):
    return connection.execute(\"SELECT * FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION\")
"""

    problems = check_downstream_source(source)

    assert "下游模块禁止导入 sqlite3" in problems
    assert any("CUPTI_ACTIVITY_KIND_" in problem for problem in problems)


def test_historical_regression_report_preserves_frozen_raw_identity():
    root = Path(__file__).resolve().parents[1]
    frozen = json.loads(
        (root / "docs" / "prototype_archive" / "raw_trace_manifest_v1.json")
        .read_text(encoding="utf-8")
    )
    regression = json.loads(
        (
            root
            / "engineering_evidence"
            / "canonical_raw_v0_2"
            / "historical_regression.json"
        ).read_text(encoding="utf-8")
    )
    frozen_by_path = {item["path"]: item["sha256"] for item in frozen["files"]}

    assert regression["verdict"] == "ENGINEERING_REGRESSION_PASS"
    assert regression["research_eligibility"]["q0"] == "NOT_RUN"
    assert len(regression["cases"]) == 3
    for case in regression["cases"]:
        raw = case["raw"]
        assert raw["sha256_before"] == frozen_by_path[raw["path"]]
        assert raw["sha256_after"] == raw["sha256_before"]
        assert case["canonical"]["observation_validity"] == "ambiguous"
        assert case["canonical"]["identity_validity"] == "AMBIGUOUS"
        assert case["canonical"]["compressed_record_bytes"] < case["sqlite"]["size_bytes"]


def test_repository_downstream_modules_obey_canonical_raw_boundary():
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_canonical_raw_boundary.py")],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "canonical_raw_boundary: PASS" in completed.stdout
