"""只读检查 Nsight SQLite 是否满足 v1.4.1 observation contract。"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__


REPORT_SCHEMA_VERSION = "exposedpath.observation-report/0.3.0"
CONTRACT_VERSION = "exposedpath-v1.4.1-draft-0.1"
STRUCTURED_NVTX_PREFIX = "EXPOSEDPATH_JSON_V1:"
SUPPORTED_EXPORT_SCHEMAS = {
    ("2026.1.1.204", "3.24.14"),
    ("2026.2.1.210", "3.25.0"),
}

CORE_REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "META_DATA_CAPTURE": ("name", "value"),
    "META_DATA_EXPORT": ("name", "value"),
    "StringIds": ("id", "value"),
    "NVTX_EVENTS": (
        "start", "end", "eventType", "rangeId", "category", "color", "text",
        "globalTid", "endGlobalTid", "textId", "domainId", "jsonText",
    ),
    "CUPTI_ACTIVITY_KIND_RUNTIME": (
        "start", "end", "eventClass", "globalTid", "correlationId", "nameId",
        "returnValue", "callchainId",
    ),
    "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION": (
        "start", "end", "deviceId", "contextId", "greenContextId", "streamId",
        "correlationId", "globalPid", "syncType", "eventId", "eventSyncId",
    ),
    "CUPTI_ACTIVITY_KIND_KERNEL": (
        "start", "end", "deviceId", "contextId", "greenContextId", "streamId",
        "correlationId", "globalPid", "demangledName", "shortName", "graphNodeId",
        "graphId",
    ),
    "ENUM_CUPTI_SYNC_TYPE": ("id", "name", "label"),
    "TARGET_INFO_CUDA_CONTEXT_INFO": (
        "nullStreamId", "hwId", "vmId", "processId", "deviceId", "contextId",
        "parentContextId", "isGreenContext",
    ),
    "TARGET_INFO_CUDA_STREAM": (
        "streamId", "hwId", "vmId", "processId", "contextId", "priority", "flag",
    ),
    "TARGET_INFO_GPU": ("id", "name"),
    "DIAGNOSTIC_EVENT": ("timestamp", "source", "severity", "text"),
}

OPTIONAL_ACTIVITY_COLUMNS: dict[str, tuple[str, ...]] = {
    "CUPTI_ACTIVITY_KIND_MEMCPY": (
        "start", "end", "deviceId", "contextId", "greenContextId", "streamId",
        "correlationId", "globalPid", "bytes", "copyKind", "srcKind", "dstKind",
        "graphNodeId",
    ),
    "CUPTI_ACTIVITY_KIND_MEMSET": (
        "start", "end", "deviceId", "contextId", "greenContextId", "streamId",
        "correlationId", "globalPid", "value", "bytes", "graphNodeId", "memKind",
    ),
    "CUPTI_ACTIVITY_KIND_CUDA_EVENT": (
        "timestamp", "deviceId", "contextId", "greenContextId", "streamId",
        "correlationId", "globalPid", "eventId", "eventSyncId",
    ),
}

COUNT_TABLES = (
    "NVTX_EVENTS",
    "CUPTI_ACTIVITY_KIND_RUNTIME",
    "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION",
    "CUPTI_ACTIVITY_KIND_KERNEL",
    "CUPTI_ACTIVITY_KIND_MEMCPY",
    "CUPTI_ACTIVITY_KIND_MEMSET",
    "CUPTI_ACTIVITY_KIND_CUDA_EVENT",
    "DIAGNOSTIC_EVENT",
)

DROPPED_RECORD_PATTERNS = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"dropped\s+(record|event)",
        r"lost\s+(record|event)",
        r"events?\s+may\s+be\s+missing",
        r"reached\s+the\s+size\s+limit",
        r"buffer\s+overflow",
        r"couldn.?t\s+allocate\s+cupti\s+buf",
    )
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _validate_sha256(value: str | None, field_name: str) -> str | None:
    if value is None:
        return None
    normalized = value.strip().upper()
    if not re.fullmatch(r"[0-9A-F]{64}", normalized):
        raise ValueError(f"{field_name} 必须是 64 位十六进制 SHA-256")
    return normalized


def _open_readonly(path: Path) -> sqlite3.Connection:
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    connection = sqlite3.connect(uri, uri=True)
    connection.text_factory = lambda value: value.decode("utf-8", errors="replace")
    connection.execute("PRAGMA query_only = ON")
    return connection


def _table_columns(connection: sqlite3.Connection, table: str) -> list[str]:
    escaped = table.replace('"', '""')
    return [row[1] for row in connection.execute(f'PRAGMA table_info("{escaped}")')]


def _metadata(connection: sqlite3.Connection, table: str) -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for name, value in connection.execute(f'SELECT name, value FROM "{table}"'):
        result.setdefault(str(name), []).append("" if value is None else str(value))
    return result


def _first(metadata: dict[str, list[str]], key: str) -> str | None:
    values = metadata.get(key, [])
    return values[0] if values else None


def _issue(level: str, code: str, detail: Any) -> dict[str, Any]:
    return {"level": level, "code": code, "detail": detail}


def _global_parts(global_id: int | None) -> tuple[int | None, int | None]:
    if global_id is None:
        return None, None
    value = int(global_id)
    return (value >> 24) & 0xFFFFFF, value & 0xFFFFFF


def _resolve_q0_target_request_scope(
    connection: sqlite3.Connection,
    table_usable: dict[str, bool],
    source_manifest: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if not source_manifest or source_manifest.get("experiment_id") != "exposedpath-q0":
        return None
    request_id = source_manifest.get("q0_case_id")
    if not isinstance(request_id, str) or not request_id:
        return {"status": "UNRESOLVED", "reason": "MISSING_Q0_CASE_ID"}
    if not (
        table_usable.get("NVTX_EVENTS") and table_usable.get("StringIds")
    ):
        return {
            "status": "UNRESOLVED",
            "request_id": request_id,
            "reason": "NVTX_TABLE_UNUSABLE",
        }

    request_rows: list[dict[str, Any]] = []
    malformed_structured_count = 0
    for rowid, start, end, text in connection.execute(
        """
        SELECT n.rowid, n.start, n.end, COALESCE(n.text, s.value, '')
        FROM NVTX_EVENTS AS n
        LEFT JOIN StringIds AS s ON s.id = n.textId
        ORDER BY n.start, n.rowid
        """
    ):
        label = str(text)
        if not label.startswith(STRUCTURED_NVTX_PREFIX):
            continue
        try:
            payload = json.loads(label[len(STRUCTURED_NVTX_PREFIX) :])
        except (json.JSONDecodeError, TypeError):
            malformed_structured_count += 1
            continue
        if not isinstance(payload, dict):
            malformed_structured_count += 1
            continue
        if payload.get("kind") != "request":
            continue
        request_rows.append(
            {"source_rowid": rowid, "start_ns": start, "end_ns": end, "identity": payload}
        )

    identity_fields = (
        "experiment_id", "wmpc_id", "run_id", "run_role", "pass_id", "repeat_id"
    )
    matching = [
        row
        for row in request_rows
        if row["identity"].get("request_id") == request_id
        and row["identity"].get("phase") == "full_request"
        and all(
            source_manifest.get(field) is not None
            and row["identity"].get(field) == source_manifest.get(field)
            for field in identity_fields
        )
        and isinstance(row["start_ns"], int)
        and isinstance(row["end_ns"], int)
        and row["end_ns"] >= row["start_ns"]
    ]
    if malformed_structured_count:
        return {
            "status": "UNRESOLVED",
            "request_id": request_id,
            "reason": "STRUCTURED_NVTX_MALFORMED",
            "malformed_structured_count": malformed_structured_count,
            "structured_request_count": len(request_rows),
            "matching_request_count": len(matching),
        }
    if len(request_rows) != 1 or len(matching) != 1:
        return {
            "status": "UNRESOLVED",
            "request_id": request_id,
            "reason": "TARGET_REQUEST_NOT_UNIQUE",
            "structured_request_count": len(request_rows),
            "matching_request_count": len(matching),
        }
    target = matching[0]
    return {
        "status": "RESOLVED",
        "request_id": request_id,
        "start_ns": target["start_ns"],
        "end_ns": target["end_ns"],
        "nvtx_source_rowid": target["source_rowid"],
    }


def _sync_observation_scope(
    sync_start_ns: int, target_request_scope: dict[str, Any] | None
) -> str:
    if target_request_scope and target_request_scope.get("status") == "RESOLVED":
        if sync_start_ns >= target_request_scope["end_ns"]:
            return "HARNESS_OUTSIDE_REQUEST"
        return "TARGET_REQUEST"
    return "GLOBAL_TRACE"


def inspect_sqlite(
    sqlite_path: Path,
    data_role: str,
    raw_sha256: str | None = None,
    collector_version: str | None = None,
    source_manifest: Path | None = None,
) -> dict[str, Any]:
    sqlite_path = sqlite_path.resolve()
    if not sqlite_path.is_file():
        raise ValueError(f"SQLite 不存在: {sqlite_path}")
    if data_role not in {"Prototype", "Engineering", "Pilot", "Formal"}:
        raise ValueError(f"不支持的数据角色: {data_role}")

    raw_sha256 = _validate_sha256(raw_sha256, "raw_sha256")
    manifest_sha256 = None
    manifest_name = None
    source_manifest_data: dict[str, Any] | None = None
    if source_manifest is not None:
        source_manifest = source_manifest.resolve()
        if not source_manifest.is_file():
            raise ValueError(f"source manifest 不存在: {source_manifest}")
        loaded_manifest = json.loads(source_manifest.read_text(encoding="utf-8"))
        if not isinstance(loaded_manifest, dict):
            raise ValueError("source manifest 必须是 JSON 对象")
        source_manifest_data = loaded_manifest
        manifest_sha256 = _sha256(source_manifest)
        manifest_name = source_manifest.name

    issues: list[dict[str, Any]] = []
    with _open_readonly(sqlite_path) as connection:
        table_names = {
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        required_table_checks: dict[str, dict[str, Any]] = {}
        optional_table_checks: dict[str, dict[str, Any]] = {}
        table_usable: dict[str, bool] = {}
        for table, required in CORE_REQUIRED_COLUMNS.items():
            actual = _table_columns(connection, table) if table in table_names else []
            missing = [column for column in required if column not in actual]
            required_table_checks[table] = {
                "present": table in table_names,
                "missing_columns": missing,
            }
            table_usable[table] = table in table_names and not missing
            if table not in table_names:
                issues.append(_issue("invalid", "MISSING_REQUIRED_TABLE", table))
            elif missing:
                issues.append(
                    _issue(
                        "invalid",
                        "MISSING_REQUIRED_COLUMNS",
                        {"table": table, "columns": missing},
                    )
                )
        for table, required in OPTIONAL_ACTIVITY_COLUMNS.items():
            actual = _table_columns(connection, table) if table in table_names else []
            missing = (
                [column for column in required if column not in actual]
                if table in table_names
                else []
            )
            optional_table_checks[table] = {
                "present": table in table_names,
                "missing_columns": missing,
            }
            table_usable[table] = table in table_names and not missing
            if table in table_names and missing:
                issues.append(
                    _issue(
                        "invalid",
                        "MISSING_REQUIRED_COLUMNS",
                        {"table": table, "columns": missing},
                    )
                )

        counts: dict[str, int | None] = {}
        for table in COUNT_TABLES:
            if table in table_names:
                counts[table] = int(
                    connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
                )
            elif table in OPTIONAL_ACTIVITY_COLUMNS:
                counts[table] = 0
            else:
                counts[table] = None

        export_metadata = (
            _metadata(connection, "META_DATA_EXPORT")
            if table_usable.get("META_DATA_EXPORT")
            else {}
        )
        capture_metadata = (
            _metadata(connection, "META_DATA_CAPTURE")
            if table_usable.get("META_DATA_CAPTURE")
            else {}
        )

        export_schema_pair = (
            _first(export_metadata, "EXPORT_PRODUCT_VERSION"),
            _first(export_metadata, "EXPORT_SCHEMA_VERSION"),
        )
        if (
            table_usable.get("META_DATA_EXPORT")
            and export_schema_pair not in SUPPORTED_EXPORT_SCHEMAS
        ):
            issues.append(
                _issue(
                    "invalid",
                    "UNSUPPORTED_EXPORT_SCHEMA",
                    {
                        "product_version": export_schema_pair[0],
                        "schema_version": export_schema_pair[1],
                    },
                )
            )

        gpu_rows = []
        if table_usable.get("TARGET_INFO_GPU"):
            gpu_rows = [
                {"device_id": row[0], "name": row[1]}
                for row in connection.execute(
                    "SELECT id, name FROM TARGET_INFO_GPU ORDER BY id"
                )
            ]

        phase_counts: dict[str, int] = {}
        if table_usable.get("NVTX_EVENTS") and table_usable.get("StringIds"):
            query = """
                SELECT COALESCE(n.text, s.value, ''), COUNT(*)
                FROM NVTX_EVENTS AS n
                LEFT JOIN StringIds AS s ON s.id = n.textId
                WHERE COALESCE(n.text, s.value, '') IN ('full_request', 'prefill', 'decode')
                GROUP BY COALESCE(n.text, s.value, '')
                ORDER BY 1
            """
            phase_counts = {str(name): int(count) for name, count in connection.execute(query)}

        target_request_scope = _resolve_q0_target_request_scope(
            connection, table_usable, source_manifest_data
        )
        if target_request_scope and target_request_scope.get("status") != "RESOLVED":
            issues.append(
                _issue("invalid", "TARGET_REQUEST_SCOPE_UNRESOLVED", target_request_scope)
            )

        sync_check: dict[str, Any] = {
            "total": counts.get("CUPTI_ACTIVITY_KIND_SYNCHRONIZATION"),
            "missing_correlation": None,
            "non_unique_runtime_mapping": None,
            "non_unique_runtime_mapping_details": [],
            "harness_outside_request_issue_count": 0,
        }
        if (
            table_usable.get("CUPTI_ACTIVITY_KIND_SYNCHRONIZATION")
            and table_usable.get("CUPTI_ACTIVITY_KIND_RUNTIME")
            and table_usable.get("StringIds")
        ):
            missing_details: list[dict[str, Any]] = []
            offending: list[dict[str, Any]] = []
            sync_rows = connection.execute(
                """
                SELECT rowid, start, end, deviceId, contextId, streamId,
                       correlationId, globalPid, syncType, eventId, eventSyncId
                FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION
                ORDER BY start, end, rowid
                """
            )
            for sync_row in sync_rows:
                correlation_id = sync_row[6]
                sync_detail = {
                    "sync_source_rowid": sync_row[0],
                    "start_ns": sync_row[1],
                    "end_ns": sync_row[2],
                    "device_id": sync_row[3],
                    "context_id": sync_row[4],
                    "stream_id": sync_row[5],
                    "correlation_id": correlation_id,
                    "global_pid": sync_row[7],
                    "sync_type": sync_row[8],
                    "event_id": sync_row[9],
                    "event_sync_id": sync_row[10],
                    "scope": _sync_observation_scope(sync_row[1], target_request_scope),
                }
                if correlation_id is None:
                    missing_details.append(sync_detail)
                    continue
                runtime_rows = list(
                    connection.execute(
                        """
                        SELECT r.rowid, r.start, r.end, r.eventClass, r.globalTid,
                               r.correlationId, r.nameId, COALESCE(s.value, ''),
                               r.returnValue, r.callchainId
                        FROM CUPTI_ACTIVITY_KIND_RUNTIME AS r
                        LEFT JOIN StringIds AS s ON s.id = r.nameId
                        WHERE r.correlationId = ?
                        ORDER BY r.start, r.end, r.rowid
                        """,
                        (correlation_id,),
                    )
                )
                if len(runtime_rows) == 1:
                    continue
                candidates = []
                for runtime_row in runtime_rows:
                    process_id, thread_id = _global_parts(runtime_row[4])
                    candidates.append(
                        {
                            "source_rowid": runtime_row[0],
                            "start_ns": runtime_row[1],
                            "end_ns": runtime_row[2],
                            "event_class": runtime_row[3],
                            "global_tid": runtime_row[4],
                            "process_id": process_id,
                            "thread_id": thread_id,
                            "correlation_id": runtime_row[5],
                            "name_id": runtime_row[6],
                            "api_name": str(runtime_row[7]),
                            "return_value": runtime_row[8],
                            "callchain_id": runtime_row[9],
                        }
                    )
                offending.append(
                    {
                        **sync_detail,
                        "runtime_match_count": len(runtime_rows),
                        "runtime_candidates": candidates,
                    }
                )
            missing_correlation = len(missing_details)
            non_unique = len(offending)
            target_missing = [
                row for row in missing_details
                if row["scope"] != "HARNESS_OUTSIDE_REQUEST"
            ]
            harness_missing = [
                row for row in missing_details
                if row["scope"] == "HARNESS_OUTSIDE_REQUEST"
            ]
            target_non_unique = [
                row for row in offending
                if row["scope"] != "HARNESS_OUTSIDE_REQUEST"
            ]
            harness_non_unique = [
                row for row in offending
                if row["scope"] == "HARNESS_OUTSIDE_REQUEST"
            ]
            sync_check["missing_correlation"] = missing_correlation
            sync_check["non_unique_runtime_mapping"] = non_unique
            sync_check["non_unique_runtime_mapping_details"] = offending
            sync_check["harness_outside_request_issue_count"] = (
                len(harness_missing) + len(harness_non_unique)
            )
            if target_missing:
                issues.append(
                    _issue(
                        "invalid",
                        "SYNC_CORRELATION_MISSING",
                        {"count": len(target_missing), "offending": target_missing},
                    )
                )
            if harness_missing:
                issues.append(
                    _issue(
                        "warning",
                        "HARNESS_SYNC_CORRELATION_MISSING",
                        {"count": len(harness_missing), "offending": harness_missing},
                    )
                )
            if target_non_unique:
                issues.append(
                    _issue(
                        "invalid",
                        "SYNC_RUNTIME_MAPPING_NOT_UNIQUE",
                        {"count": len(target_non_unique), "offending": target_non_unique},
                    )
                )
            if harness_non_unique:
                issues.append(
                    _issue(
                        "warning",
                        "HARNESS_SYNC_RUNTIME_MAPPING_NOT_UNIQUE",
                        {"count": len(harness_non_unique), "offending": harness_non_unique},
                    )
                )

        dropped_evidence: list[dict[str, Any]] = []
        if table_usable.get("DIAGNOSTIC_EVENT"):
            for timestamp, severity, source, text in connection.execute(
                "SELECT timestamp, severity, source, text FROM DIAGNOSTIC_EVENT ORDER BY timestamp"
            ):
                message = str(text)
                if any(pattern.search(message) for pattern in DROPPED_RECORD_PATTERNS):
                    dropped_evidence.append(
                        {
                            "timestamp": timestamp,
                            "severity": severity,
                            "source": source,
                            "text": message,
                        }
                    )
        if dropped_evidence:
            issues.append(
                _issue("invalid", "DROPPED_OR_MISSING_RECORD_EVIDENCE", dropped_evidence)
            )

        if _first(export_metadata, "EXPORT_PARAM_LAZY") == "true":
            issues.append(
                _issue(
                    "warning",
                    "LAZY_EXPORT",
                    "历史导出采用 lazy=true；核心必需表仍须实际存在。",
                )
            )

        observed_facts = {
            "sqlite": {
                "name": sqlite_path.name,
                "size_bytes": sqlite_path.stat().st_size,
                "sha256": _sha256(sqlite_path),
            },
            "raw": {
                "sha256": raw_sha256,
                "collector_version": collector_version,
            },
            "source_manifest": {
                "name": manifest_name,
                "sha256": manifest_sha256,
            },
            "export": {
                "product_name": _first(export_metadata, "EXPORT_PRODUCT_NAME"),
                "product_version": _first(export_metadata, "EXPORT_PRODUCT_VERSION"),
                "schema_version": _first(export_metadata, "EXPORT_SCHEMA_VERSION"),
                "platform": _first(export_metadata, "EXPORT_PLATFORM"),
                "lazy": _first(export_metadata, "EXPORT_PARAM_LAZY"),
            },
            "capture": {
                "event_types": capture_metadata.get("CAPTURE_EVENT_TYPE", []),
            },
            "gpus": gpu_rows,
            "row_counts": counts,
            "phase_label_counts": phase_counts,
        }

    if raw_sha256 is None:
        issues.append(_issue("ambiguous", "MISSING_RAW_SHA256", None))
    if not collector_version:
        issues.append(_issue("ambiguous", "MISSING_COLLECTOR_VERSION", None))
    if source_manifest is None:
        level = "invalid" if data_role in {"Pilot", "Formal"} else "ambiguous"
        issues.append(_issue(level, "MISSING_SOURCE_MANIFEST", None))

    issue_levels = {item["level"] for item in issues}
    if "invalid" in issue_levels:
        validity_status = "invalid"
    elif "ambiguous" in issue_levels:
        validity_status = "ambiguous"
    else:
        validity_status = "valid"

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "contract_version": CONTRACT_VERSION,
        "analyzer_version": __version__,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_role": data_role,
        "observed_facts": observed_facts,
        "derived_checks": {
            "supported_export_schemas": [
                {"product_version": product, "schema_version": schema}
                for product, schema in sorted(SUPPORTED_EXPORT_SCHEMAS)
            ],
            "required_tables": required_table_checks,
            "optional_activity_tables": optional_table_checks,
            "target_request_scope": target_request_scope,
            "sync_correlation": sync_check,
            "dropped_record_evidence": dropped_evidence,
        },
        "validity": {
            "status": validity_status,
            "issues": issues,
        },
        "research_eligibility": {
            "formal_evidence": False,
            "blocking_reasons": [
                "ANALYZER_SCOPE_OBSERVATION_ONLY",
                "Q0_NOT_RUN",
            ],
            "q0_status": "NOT_RUN",
        },
    }


def write_report_new(output_dir: Path, report: dict[str, Any]) -> Path:
    output_dir = output_dir.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "observation_report.json"
    if output_path.exists():
        raise FileExistsError(f"拒绝覆盖已有输出: {output_path}")

    content = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    file_descriptor, temporary_name = tempfile.mkstemp(
        prefix=".observation_report_", suffix=".json", dir=output_dir
    )
    try:
        with os.fdopen(file_descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, output_path)
    except BaseException:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise
    return output_path
