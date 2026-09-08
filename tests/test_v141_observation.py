import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from exposedpath_v141.observation import inspect_sqlite, write_report_new


SCHEMA = """
CREATE TABLE META_DATA_CAPTURE(name TEXT NOT NULL, value TEXT);
CREATE TABLE META_DATA_EXPORT(name TEXT NOT NULL, value TEXT);
CREATE TABLE StringIds(id INTEGER NOT NULL, value TEXT);
CREATE TABLE NVTX_EVENTS(start INTEGER NOT NULL, end INTEGER, eventType INTEGER NOT NULL,
 text TEXT, textId INTEGER, globalTid INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(start INTEGER NOT NULL, end INTEGER NOT NULL,
 globalTid INTEGER, correlationId INTEGER, nameId INTEGER NOT NULL, returnValue INTEGER NOT NULL);
CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, streamId INTEGER NOT NULL,
 correlationId INTEGER, globalPid INTEGER, syncType INTEGER NOT NULL,
 eventId INTEGER NOT NULL, eventSyncId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, streamId INTEGER NOT NULL,
 correlationId INTEGER, globalPid INTEGER, demangledName INTEGER NOT NULL, shortName INTEGER NOT NULL);
CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, streamId INTEGER NOT NULL,
 correlationId INTEGER, globalPid INTEGER, bytes INTEGER NOT NULL, copyKind INTEGER NOT NULL);
CREATE TABLE CUPTI_ACTIVITY_KIND_MEMSET(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, streamId INTEGER NOT NULL,
 correlationId INTEGER, globalPid INTEGER, bytes INTEGER NOT NULL);
CREATE TABLE ENUM_CUPTI_SYNC_TYPE(id INTEGER NOT NULL, name TEXT, label TEXT);
CREATE TABLE TARGET_INFO_CUDA_CONTEXT_INFO(nullStreamId INTEGER NOT NULL, processId INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL);
CREATE TABLE TARGET_INFO_CUDA_STREAM(streamId INTEGER NOT NULL, processId INTEGER NOT NULL,
 contextId INTEGER NOT NULL);
CREATE TABLE TARGET_INFO_GPU(id INTEGER NOT NULL, name TEXT);
CREATE TABLE DIAGNOSTIC_EVENT(timestamp INTEGER NOT NULL, source INTEGER NOT NULL,
 severity INTEGER NOT NULL, text TEXT NOT NULL);
"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _make_sqlite(path: Path, diagnostic: str | None = None) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(SCHEMA)
    connection.executemany(
        "INSERT INTO META_DATA_EXPORT(name,value) VALUES (?,?)",
        [
            ("EXPORT_PRODUCT_NAME", "NVIDIA Nsight Systems"),
            ("EXPORT_PRODUCT_VERSION", "2026.1.1.204"),
            ("EXPORT_SCHEMA_VERSION", "3.24.14"),
            ("EXPORT_PLATFORM", "test-platform"),
            ("EXPORT_PARAM_LAZY", "false"),
        ],
    )
    connection.executemany(
        "INSERT INTO META_DATA_CAPTURE(name,value) VALUES (?,?)",
        [("CAPTURE_EVENT_TYPE", "Cuda"), ("CAPTURE_EVENT_TYPE", "NvtxEvents")],
    )
    connection.execute("INSERT INTO StringIds VALUES (1, 'cudaStreamSynchronize')")
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (10,20,1,7,1,0)"
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION "
        "VALUES (11,19,0,1,2,7,1,3,4294967295,4294967295)"
    )
    connection.execute("INSERT INTO TARGET_INFO_GPU VALUES (0, 'test-gpu')")
    for index, label in enumerate(("full_request", "prefill", "decode"), start=1):
        connection.execute(
            "INSERT INTO NVTX_EVENTS(start,end,eventType,text,textId,globalTid) "
            "VALUES (?,?,?,?,?,?)",
            (index, index + 1, 59, label, None, 1),
        )
    if diagnostic:
        connection.execute(
            "INSERT INTO DIAGNOSTIC_EVENT VALUES (1,1,2,?)", (diagnostic,)
        )
    connection.commit()
    connection.close()


def _make_manifest(path: Path) -> None:
    path.write_text('{"run_id":"synthetic"}\n', encoding="utf-8")


def test_valid_fixture_and_input_is_unchanged(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _make_manifest(manifest)
    before = _sha256(database)

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    assert report["validity"]["status"] == "valid"
    assert report["derived_checks"]["sync_correlation"]["non_unique_runtime_mapping"] == 0
    assert report["observed_facts"]["phase_label_counts"] == {
        "decode": 1,
        "full_request": 1,
        "prefill": 1,
    }
    assert _sha256(database) == before


def test_missing_manifest_is_ambiguous_for_engineering(tmp_path):
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="B" * 64,
        collector_version="synthetic",
    )

    assert report["validity"]["status"] == "ambiguous"
    assert "MISSING_SOURCE_MANIFEST" in {
        item["code"] for item in report["validity"]["issues"]
    }


def test_missing_required_table_is_invalid(tmp_path):
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION")
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert any(
        item["code"] == "MISSING_REQUIRED_TABLE"
        and item["detail"] == "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION"
        for item in report["validity"]["issues"]
    )


def test_dropped_record_diagnostic_is_invalid(tmp_path):
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database, "CUPTI events may be missing because a buffer overflow occurred")

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert report["derived_checks"]["dropped_record_evidence"]


def test_report_writer_refuses_overwrite(tmp_path):
    output_dir = tmp_path / "derived"
    report = {"validity": {"status": "valid"}}
    output_path = write_report_new(output_dir, report)
    assert json.loads(output_path.read_text(encoding="utf-8")) == report

    with pytest.raises(FileExistsError):
        write_report_new(output_dir, report)


def test_invalid_utf8_metadata_does_not_abort_inspection(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _make_manifest(manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO META_DATA_EXPORT(name,value) "
        "VALUES ('EXPORT_TIME_LOCAL', CAST(X'80' AS TEXT))"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="C" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    assert report["validity"]["status"] == "valid"


def test_observation_only_never_grants_formal_eligibility(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _make_manifest(manifest)

    report = inspect_sqlite(
        database,
        data_role="Formal",
        raw_sha256="D" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    assert report["validity"]["status"] == "valid"
    assert report["research_eligibility"]["formal_evidence"] is False
    assert report["research_eligibility"]["q0_status"] == "NOT_RUN"


def test_unknown_export_schema_is_invalid(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _make_manifest(manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='unknown' "
        "WHERE name='EXPORT_SCHEMA_VERSION'"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="E" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    assert report["validity"]["status"] == "invalid"
    assert "UNSUPPORTED_EXPORT_SCHEMA" in {
        item["code"] for item in report["validity"]["issues"]
    }
