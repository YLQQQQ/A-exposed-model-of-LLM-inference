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
 rangeId INTEGER, category INTEGER, color INTEGER, text TEXT, globalTid INTEGER,
 endGlobalTid INTEGER, textId INTEGER, domainId INTEGER, jsonText TEXT);
CREATE TABLE CUPTI_ACTIVITY_KIND_RUNTIME(start INTEGER NOT NULL, end INTEGER NOT NULL,
 eventClass INTEGER NOT NULL, globalTid INTEGER, correlationId INTEGER,
 nameId INTEGER NOT NULL, returnValue INTEGER NOT NULL, callchainId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL,
 correlationId INTEGER, globalPid INTEGER, syncType INTEGER NOT NULL,
 eventId INTEGER NOT NULL, eventSyncId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL, correlationId INTEGER, globalPid INTEGER,
 demangledName INTEGER NOT NULL, shortName INTEGER NOT NULL,
 graphNodeId INTEGER, graphId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL, correlationId INTEGER, globalPid INTEGER,
 bytes INTEGER NOT NULL, copyKind INTEGER NOT NULL, srcKind INTEGER, dstKind INTEGER,
 graphNodeId INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_MEMSET(start INTEGER NOT NULL, end INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, greenContextId INTEGER,
 streamId INTEGER NOT NULL, correlationId INTEGER, globalPid INTEGER,
 value INTEGER NOT NULL, bytes INTEGER NOT NULL, graphNodeId INTEGER, memKind INTEGER);
CREATE TABLE CUPTI_ACTIVITY_KIND_CUDA_EVENT(timestamp INTEGER, deviceId INTEGER NOT NULL,
 contextId INTEGER NOT NULL, greenContextId INTEGER, streamId INTEGER NOT NULL,
 correlationId INTEGER,
 globalPid INTEGER, eventId INTEGER NOT NULL, eventSyncId INTEGER);
CREATE TABLE ENUM_CUPTI_SYNC_TYPE(id INTEGER NOT NULL, name TEXT, label TEXT);
CREATE TABLE TARGET_INFO_CUDA_CONTEXT_INFO(nullStreamId INTEGER NOT NULL,
 hwId INTEGER NOT NULL, vmId INTEGER NOT NULL, processId INTEGER NOT NULL,
 deviceId INTEGER NOT NULL, contextId INTEGER NOT NULL, parentContextId INTEGER,
 isGreenContext INTEGER);
CREATE TABLE TARGET_INFO_CUDA_STREAM(streamId INTEGER NOT NULL, hwId INTEGER NOT NULL,
 vmId INTEGER NOT NULL, processId INTEGER NOT NULL, contextId INTEGER NOT NULL,
 priority INTEGER NOT NULL, flag INTEGER NOT NULL);
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
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (10,20,0,1,7,1,0,NULL)"
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION "
        "VALUES (11,19,0,1,NULL,2,7,1,3,4294967295,4294967295)"
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


def _replace_with_q0_target_request(
    database: Path, manifest: Path, *, start_ns: int = 1, end_ns: int = 100
) -> None:
    identity = {
        "experiment_id": "exposedpath-q0",
        "wmpc_id": "q0-controlled",
        "run_id": "q0-test.q0-stream-001",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": "Q0-STREAM-001",
        "repeat_id": "repeat-0",
    }
    manifest.write_text(
        json.dumps(
            {
                **{key: value for key, value in identity.items() if key != "request_id"},
                "q0_case_id": identity["request_id"],
            }
        ),
        encoding="utf-8",
    )
    label = "EXPOSEDPATH_JSON_V1:" + json.dumps(
        {"kind": "request", **identity, "phase": "full_request"},
        separators=(",", ":"),
    )
    connection = sqlite3.connect(database)
    connection.execute("DELETE FROM NVTX_EVENTS")
    connection.execute(
        "INSERT INTO NVTX_EVENTS(start,end,eventType,text,textId,globalTid) "
        "VALUES (?,?,?,?,?,?)",
        (start_ns, end_ns, 59, label, None, 1),
    )
    connection.commit()
    connection.close()


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


def test_absent_optional_activity_tables_are_zero_records_not_invalid(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _make_manifest(manifest)
    connection = sqlite3.connect(database)
    for table in (
        "CUPTI_ACTIVITY_KIND_MEMCPY",
        "CUPTI_ACTIVITY_KIND_MEMSET",
        "CUPTI_ACTIVITY_KIND_CUDA_EVENT",
    ):
        connection.execute(f'DROP TABLE "{table}"')
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="F" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    assert report["validity"]["status"] == "valid"
    assert all(
        report["observed_facts"]["row_counts"][table] == 0
        for table in (
            "CUPTI_ACTIVITY_KIND_MEMCPY",
            "CUPTI_ACTIVITY_KIND_MEMSET",
            "CUPTI_ACTIVITY_KIND_CUDA_EVENT",
        )
    )
    assert report["derived_checks"]["optional_activity_tables"][
        "CUPTI_ACTIVITY_KIND_MEMCPY"
    ]["present"] is False
    assert report["derived_checks"]["optional_activity_tables"][
        "CUPTI_ACTIVITY_KIND_MEMCPY"
    ]["missing_columns"] == []


def test_present_optional_activity_table_with_missing_columns_is_invalid(tmp_path):
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_MEMCPY")
    connection.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_MEMCPY(start INTEGER, end INTEGER)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert any(
        item["code"] == "MISSING_REQUIRED_COLUMNS"
        and item["detail"]["table"] == "CUPTI_ACTIVITY_KIND_MEMCPY"
        for item in report["validity"]["issues"]
    )


def test_supported_lazy_export_without_kernel_table_normalizes_zero_rows(tmp_path):
    """捕获：把 lazy 导出的合法零 kernel 错判为缺少核心证据。"""
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _make_manifest(manifest)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_KERNEL")
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='2026.2.1.210' "
        "WHERE name='EXPORT_PRODUCT_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='3.25.0' "
        "WHERE name='EXPORT_SCHEMA_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='true' "
        "WHERE name='EXPORT_PARAM_LAZY'"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="2" * 64,
        collector_version="2026.2.1.210",
        source_manifest=manifest,
    )

    kernel = report["derived_checks"]["conditional_activity_tables"][
        "CUPTI_ACTIVITY_KIND_KERNEL"
    ]
    assert report["validity"]["status"] == "valid"
    assert report["observed_facts"]["row_counts"][
        "CUPTI_ACTIVITY_KIND_KERNEL"
    ] == 0
    assert kernel["present"] is False
    assert kernel["normalization"] == "ZERO_ROWS_LAZY_EXPORT"
    assert kernel["presence_evidence"] == []


def test_lazy_missing_kernel_table_with_target_launch_evidence_is_invalid(tmp_path):
    """捕获：有目标 request kernel launch 时仍把缺表伪装成零活动。"""
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_KERNEL")
    connection.execute("INSERT INTO StringIds VALUES (2, 'cudaLaunchKernel_v7000')")
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (30,40,0,1,8,2,0,NULL)"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='2026.2.1.210' "
        "WHERE name='EXPORT_PRODUCT_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='3.25.0' "
        "WHERE name='EXPORT_SCHEMA_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='true' "
        "WHERE name='EXPORT_PARAM_LAZY'"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="3" * 64,
        collector_version="2026.2.1.210",
        source_manifest=manifest,
    )

    issue = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "KERNEL_TABLE_ABSENT_WITH_PRESENCE_EVIDENCE"
    )
    evidence = issue["detail"]["presence_evidence"]
    assert report["validity"]["status"] == "invalid"
    assert report["observed_facts"]["row_counts"][
        "CUPTI_ACTIVITY_KIND_KERNEL"
    ] is None
    assert len(evidence) == 1
    assert evidence[0]["api_name"] == "cudaLaunchKernel_v7000"
    assert evidence[0]["scope"] == "TARGET_REQUEST"


@pytest.mark.parametrize(
    ("api_name", "start_ns", "expected_scope"),
    [
        ("cudaGraphLaunch_v10000", 30, "TARGET_REQUEST"),
        ("cudaLaunchKernel_ptsz_v7000", 30, "TARGET_REQUEST"),
        ("cuLaunchKernelEx_v12000", 30, "TARGET_REQUEST"),
        ("cuGraphLaunch_ptsz_v10000", 130, "HARNESS_OUTSIDE_REQUEST"),
    ],
)
def test_lazy_missing_kernel_table_rejects_all_launch_evidence_scopes(
    tmp_path, api_name, start_ns, expected_scope
):
    """潜在 kernel/graph launch 在 request 内外都阻止全 trace 零行规范化。"""
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_KERNEL")
    connection.execute("INSERT INTO StringIds VALUES (2, ?)", (api_name,))
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,1,8,2,0,NULL)",
        (start_ns, start_ns + 10),
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='2026.2.1.210' "
        "WHERE name='EXPORT_PRODUCT_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='3.25.0' "
        "WHERE name='EXPORT_SCHEMA_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='true' "
        "WHERE name='EXPORT_PARAM_LAZY'"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="4" * 64,
        collector_version="2026.2.1.210",
        source_manifest=manifest,
    )

    issue = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "KERNEL_TABLE_ABSENT_WITH_PRESENCE_EVIDENCE"
    )
    evidence = issue["detail"]["presence_evidence"]
    assert report["validity"]["status"] == "invalid"
    assert evidence[0]["api_name"] == api_name
    assert evidence[0]["scope"] == expected_scope


@pytest.mark.parametrize(
    ("metadata_name", "extra_value"),
    [
        ("EXPORT_PRODUCT_VERSION", "2026.2.1.210"),
        ("EXPORT_SCHEMA_VERSION", "3.25.0"),
        ("EXPORT_PARAM_LAZY", "false"),
    ],
)
def test_lazy_missing_kernel_requires_unique_export_metadata(
    tmp_path, metadata_name, extra_value
):
    """零行规范化所依赖的版本和 lazy 字段缺乏唯一值时必须 fail closed。"""
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_KERNEL")
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='2026.2.1.210' "
        "WHERE name='EXPORT_PRODUCT_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='3.25.0' "
        "WHERE name='EXPORT_SCHEMA_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='true' "
        "WHERE name='EXPORT_PARAM_LAZY'"
    )
    connection.execute(
        "INSERT INTO META_DATA_EXPORT(name,value) VALUES (?,?)",
        (metadata_name, extra_value),
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert report["observed_facts"]["row_counts"][
        "CUPTI_ACTIVITY_KIND_KERNEL"
    ] is None
    assert any(
        item["code"] == "EXPORT_METADATA_NOT_UNIQUE"
        and item["detail"]["name"] == metadata_name
        for item in report["validity"]["issues"]
    )


def test_export_lazy_metadata_requires_exact_boolean_text(tmp_path):
    """唯一但未知的 lazy 值也不能成为可接受的 observation 元数据。"""
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='TRUE' "
        "WHERE name='EXPORT_PARAM_LAZY'"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert any(
        item["code"] == "INVALID_EXPORT_METADATA_VALUE"
        and item["detail"]["name"] == "EXPORT_PARAM_LAZY"
        for item in report["validity"]["issues"]
    )


def test_nonlazy_export_without_kernel_table_remains_invalid(tmp_path):
    """捕获：把非 lazy 导出的结构缺表错误解释为零活动。"""
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_KERNEL")
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert any(
        item["code"] == "MISSING_REQUIRED_TABLE"
        and item["detail"] == "CUPTI_ACTIVITY_KIND_KERNEL"
        for item in report["validity"]["issues"]
    )


@pytest.mark.parametrize("missing_precondition", ["supported_schema", "cuda_capture"])
def test_lazy_missing_kernel_table_without_zero_evidence_remains_invalid(
    tmp_path, missing_precondition
):
    """缺少 schema 白名单或 CUDA capture 证明时不得采用零行规范化。"""
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_KERNEL")
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='true' "
        "WHERE name='EXPORT_PARAM_LAZY'"
    )
    if missing_precondition == "supported_schema":
        connection.execute(
            "UPDATE META_DATA_EXPORT SET value='unknown' "
            "WHERE name='EXPORT_SCHEMA_VERSION'"
        )
    else:
        connection.execute(
            "DELETE FROM META_DATA_CAPTURE WHERE value='Cuda'"
        )
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert report["observed_facts"]["row_counts"][
        "CUPTI_ACTIVITY_KIND_KERNEL"
    ] is None
    assert report["derived_checks"]["conditional_activity_tables"][
        "CUPTI_ACTIVITY_KIND_KERNEL"
    ]["normalization"] == "UNRESOLVED_MISSING_TABLE"


def test_present_kernel_table_with_missing_columns_remains_invalid(tmp_path):
    """捕获：条件化缺表策略意外放过实际存在但损坏的 KERNEL 表。"""
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute("DROP TABLE CUPTI_ACTIVITY_KIND_KERNEL")
    connection.execute(
        "CREATE TABLE CUPTI_ACTIVITY_KIND_KERNEL(start INTEGER, end INTEGER)"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='true' "
        "WHERE name='EXPORT_PARAM_LAZY'"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    assert report["validity"]["status"] == "invalid"
    assert any(
        item["code"] == "MISSING_REQUIRED_COLUMNS"
        and item["detail"]["table"] == "CUPTI_ACTIVITY_KIND_KERNEL"
        for item in report["validity"]["issues"]
    )


def test_reviewed_nsys_2026_2_schema_3_25_is_supported(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _make_manifest(manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='2026.2.1.210' "
        "WHERE name='EXPORT_PRODUCT_VERSION'"
    )
    connection.execute(
        "UPDATE META_DATA_EXPORT SET value='3.25.0' "
        "WHERE name='EXPORT_SCHEMA_VERSION'"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        data_role="Engineering",
        raw_sha256="1" * 64,
        collector_version="2026.2.1.210",
        source_manifest=manifest,
    )

    assert report["validity"]["status"] == "valid"
    assert {
        (item["product_version"], item["schema_version"])
        for item in report["derived_checks"]["supported_export_schemas"]
    } == {
        ("2026.1.1.204", "3.24.14"),
        ("2026.2.1.210", "3.25.0"),
    }


def test_non_unique_sync_runtime_mapping_keeps_fail_closed_details(tmp_path):
    database = tmp_path / "trace.sqlite"
    _make_sqlite(database)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO StringIds VALUES (2, 'cudaDeviceSynchronize')"
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (12,18,0,1,7,2,0,NULL)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(database, data_role="Engineering")

    issue = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "SYNC_RUNTIME_MAPPING_NOT_UNIQUE"
    )
    assert report["validity"]["status"] == "invalid"
    assert issue["detail"]["count"] == 1
    offending = issue["detail"]["offending"][0]
    assert offending["correlation_id"] == 7
    assert offending["runtime_match_count"] == 2
    assert {row["api_name"] for row in offending["runtime_candidates"]} == {
        "cudaStreamSynchronize",
        "cudaDeviceSynchronize",
    }
    assert all("source_rowid" in row for row in offending["runtime_candidates"])


def test_q0_target_request_unmatched_sync_remains_invalid(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(50,60,0,1,NULL,2,99,1,3,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    issue = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "SYNC_RUNTIME_MAPPING_NOT_UNIQUE"
    )
    assert report["validity"]["status"] == "invalid"
    assert issue["detail"]["offending"][0]["scope"] == "TARGET_REQUEST"


def test_q0_post_request_unmatched_sync_is_harness_warning(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(110,120,0,1,NULL,4294967295,99,1,4,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    warning = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "HARNESS_SYNC_RUNTIME_MAPPING_NOT_UNIQUE"
    )
    assert report["validity"]["status"] == "valid"
    assert warning["level"] == "warning"
    assert warning["detail"]["offending"][0]["scope"] == "HARNESS_OUTSIDE_REQUEST"
    assert report["schema_version"] == "exposedpath.observation-report/0.4.0"
    assert report["derived_checks"]["target_request_scope"] == {
        "status": "RESOLVED",
        "request_id": "Q0-STREAM-001",
        "start_ns": 1,
        "end_ns": 100,
        "nvtx_source_rowid": 1,
    }


def test_q0_target_request_with_mapped_sync_is_valid(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    assert report["validity"]["status"] == "valid"
    assert report["derived_checks"]["sync_correlation"][
        "non_unique_runtime_mapping"
    ] == 0


def test_q0_target_request_sync_without_correlation_remains_invalid(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(50,60,0,1,NULL,2,NULL,1,3,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    issue = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "SYNC_CORRELATION_MISSING"
    )
    assert report["validity"]["status"] == "invalid"
    assert issue["detail"]["offending"][0]["scope"] == "TARGET_REQUEST"


def test_q0_post_request_sync_without_correlation_is_harness_warning(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(110,120,0,1,NULL,4294967295,NULL,1,4,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    warning = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "HARNESS_SYNC_CORRELATION_MISSING"
    )
    assert report["validity"]["status"] == "valid"
    assert warning["detail"]["offending"][0]["scope"] == "HARNESS_OUTSIDE_REQUEST"


def test_q0_ambiguous_target_request_keeps_global_fail_closed(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    duplicate = connection.execute(
        "SELECT start,end,eventType,text,textId,globalTid FROM NVTX_EVENTS"
    ).fetchone()
    connection.execute(
        "INSERT INTO NVTX_EVENTS(start,end,eventType,text,textId,globalTid) "
        "VALUES (?,?,?,?,?,?)",
        duplicate,
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(110,120,0,1,NULL,4294967295,99,1,4,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    scope = report["derived_checks"]["target_request_scope"]
    codes = {item["code"] for item in report["validity"]["issues"]}
    issue = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "SYNC_RUNTIME_MAPPING_NOT_UNIQUE"
    )
    assert report["validity"]["status"] == "invalid"
    assert "TARGET_REQUEST_SCOPE_UNRESOLVED" in codes
    assert scope["reason"] == "TARGET_REQUEST_NOT_UNIQUE"
    assert scope["structured_request_count"] == 2
    assert scope["matching_request_count"] == 2
    assert issue["detail"]["offending"][0]["scope"] == "GLOBAL_TRACE"


def test_q0_prior_invocation_does_not_make_unique_target_ambiguous(tmp_path):
    """非目标 prior request 合法共存，且 target 后同步仍按 request 外规则分类。"""

    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest, start_ns=30, end_ns=100)
    prior_identity = {
        "kind": "request",
        "experiment_id": "exposedpath-q0",
        "wmpc_id": "q0-controlled",
        "run_id": "q0-test.q0-stream-001",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": "Q0-PRIOR-INVOCATION",
        "repeat_id": "repeat-0",
        "phase": "full_request",
    }
    prior_label = "EXPOSEDPATH_JSON_V1:" + json.dumps(
        prior_identity, separators=(",", ":")
    )
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO NVTX_EVENTS(start,end,eventType,text,textId,globalTid) "
        "VALUES (?,?,?,?,?,?)",
        (1, 20, 59, prior_label, None, 1),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(110,120,0,1,NULL,4294967295,131,1,4,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    scope = report["derived_checks"]["target_request_scope"]
    warning = next(
        issue for issue in report["validity"]["issues"]
        if issue["code"] == "HARNESS_SYNC_RUNTIME_MAPPING_NOT_UNIQUE"
    )
    assert report["validity"]["status"] == "valid"
    assert scope["status"] == "RESOLVED"
    assert scope["request_id"] == "Q0-STREAM-001"
    assert scope["start_ns"] == 30
    assert scope["end_ns"] == 100
    assert warning["detail"]["offending"][0]["correlation_id"] == 131
    assert warning["detail"]["offending"][0]["scope"] == "HARNESS_OUTSIDE_REQUEST"


def test_q0_zero_matching_target_request_remains_fail_closed(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    source_manifest = json.loads(manifest.read_text(encoding="utf-8"))
    source_manifest["q0_case_id"] = "Q0-NOT-PRESENT"
    manifest.write_text(json.dumps(source_manifest), encoding="utf-8")

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    scope = report["derived_checks"]["target_request_scope"]
    assert report["validity"]["status"] == "invalid"
    assert scope["reason"] == "TARGET_REQUEST_NOT_UNIQUE"
    assert scope["structured_request_count"] == 1
    assert scope["matching_request_count"] == 0


def test_q0_worker_marker_does_not_duplicate_request_and_teardown_stays_warning(
    tmp_path,
):
    """捕获 worker marker 被误计为第二个 request，导致 teardown 退回 GLOBAL_TRACE。"""

    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    worker_identity = {
        "kind": "marker",
        "experiment_id": "exposedpath-q0",
        "wmpc_id": "q0-controlled",
        "run_id": "q0-test.q0-stream-001",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": "Q0-STREAM-001",
        "repeat_id": "repeat-0",
        "phase": "decode",
        "callsite_id": "WORKER_PTDS_OTHER",
    }
    worker_label = "EXPOSEDPATH_JSON_V1:" + json.dumps(
        worker_identity, separators=(",", ":")
    )
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO NVTX_EVENTS(start,end,eventType,text,textId,globalTid) "
        "VALUES (?,?,?,?,?,?)",
        (10, 40, 59, worker_label, None, 2),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(110,120,0,1,NULL,4294967295,99,1,4,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    scope = report["derived_checks"]["target_request_scope"]
    warning = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "HARNESS_SYNC_RUNTIME_MAPPING_NOT_UNIQUE"
    )
    assert report["validity"]["status"] == "valid"
    assert scope["status"] == "RESOLVED"
    assert scope["nvtx_source_rowid"] == 1
    assert warning["detail"]["offending"][0]["scope"] == "HARNESS_OUTSIDE_REQUEST"


def test_q0_malformed_structured_nvtx_prevents_scope_exemption(tmp_path):
    database = tmp_path / "trace.sqlite"
    manifest = tmp_path / "manifest.json"
    _make_sqlite(database)
    _replace_with_q0_target_request(database, manifest)
    connection = sqlite3.connect(database)
    connection.execute(
        "INSERT INTO NVTX_EVENTS(start,end,eventType,text,textId,globalTid) "
        "VALUES (?,?,?,?,?,?)",
        (1, 100, 59, "EXPOSEDPATH_JSON_V1:{broken", None, 1),
    )
    connection.execute(
        "INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES "
        "(110,120,0,1,NULL,4294967295,99,1,4,4294967295,4294967295)"
    )
    connection.commit()
    connection.close()

    report = inspect_sqlite(
        database,
        "Engineering",
        raw_sha256="A" * 64,
        collector_version="synthetic",
        source_manifest=manifest,
    )

    scope = report["derived_checks"]["target_request_scope"]
    mapping_issue = next(
        item for item in report["validity"]["issues"]
        if item["code"] == "SYNC_RUNTIME_MAPPING_NOT_UNIQUE"
    )
    assert report["validity"]["status"] == "invalid"
    assert scope["status"] == "UNRESOLVED"
    assert scope["reason"] == "STRUCTURED_NVTX_MALFORMED"
    assert mapping_issue["detail"]["offending"][0]["scope"] == "GLOBAL_TRACE"
