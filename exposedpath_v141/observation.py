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


REPORT_SCHEMA_VERSION = "exposedpath.observation-report/0.1.0"
CONTRACT_VERSION = "exposedpath-v1.4.1-draft-0.1"
SUPPORTED_EXPORT_SCHEMAS = {("2026.1.1.204", "3.24.14")}

REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "META_DATA_CAPTURE": ("name", "value"),
    "META_DATA_EXPORT": ("name", "value"),
    "StringIds": ("id", "value"),
    "NVTX_EVENTS": ("start", "end", "eventType", "text", "textId", "globalTid"),
    "CUPTI_ACTIVITY_KIND_RUNTIME": (
        "start", "end", "globalTid", "correlationId", "nameId", "returnValue",
    ),
    "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION": (
        "start", "end", "deviceId", "contextId", "streamId", "correlationId",
        "globalPid", "syncType", "eventId", "eventSyncId",
    ),
    "CUPTI_ACTIVITY_KIND_KERNEL": (
        "start", "end", "deviceId", "contextId", "streamId", "correlationId",
        "globalPid", "demangledName", "shortName",
    ),
    "CUPTI_ACTIVITY_KIND_MEMCPY": (
        "start", "end", "deviceId", "contextId", "streamId", "correlationId",
        "globalPid", "bytes", "copyKind",
    ),
    "CUPTI_ACTIVITY_KIND_MEMSET": (
        "start", "end", "deviceId", "contextId", "streamId", "correlationId",
        "globalPid", "bytes",
    ),
    "CUPTI_ACTIVITY_KIND_CUDA_EVENT": (
        "timestamp", "deviceId", "contextId", "streamId", "correlationId",
        "globalPid", "eventId", "eventSyncId",
    ),
    "ENUM_CUPTI_SYNC_TYPE": ("id", "name", "label"),
    "TARGET_INFO_CUDA_CONTEXT_INFO": (
        "processId", "deviceId", "contextId", "nullStreamId",
    ),
    "TARGET_INFO_CUDA_STREAM": ("processId", "contextId", "streamId"),
    "TARGET_INFO_GPU": ("id", "name"),
    "DIAGNOSTIC_EVENT": ("timestamp", "source", "severity", "text"),
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
    if source_manifest is not None:
        source_manifest = source_manifest.resolve()
        if not source_manifest.is_file():
            raise ValueError(f"source manifest 不存在: {source_manifest}")
        json.loads(source_manifest.read_text(encoding="utf-8"))
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
        table_checks: dict[str, dict[str, Any]] = {}
        for table, required in REQUIRED_COLUMNS.items():
            actual = _table_columns(connection, table) if table in table_names else []
            missing = [column for column in required if column not in actual]
            table_checks[table] = {
                "present": table in table_names,
                "missing_columns": missing,
            }
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

        counts: dict[str, int | None] = {}
        for table in COUNT_TABLES:
            counts[table] = (
                int(connection.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0])
                if table in table_names
                else None
            )

        export_metadata = (
            _metadata(connection, "META_DATA_EXPORT")
            if "META_DATA_EXPORT" in table_names
            else {}
        )
        capture_metadata = (
            _metadata(connection, "META_DATA_CAPTURE")
            if "META_DATA_CAPTURE" in table_names
            else {}
        )

        export_schema_pair = (
            _first(export_metadata, "EXPORT_PRODUCT_VERSION"),
            _first(export_metadata, "EXPORT_SCHEMA_VERSION"),
        )
        if (
            "META_DATA_EXPORT" in table_names
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
        if "TARGET_INFO_GPU" in table_names:
            gpu_rows = [
                {"device_id": row[0], "name": row[1]}
                for row in connection.execute(
                    "SELECT id, name FROM TARGET_INFO_GPU ORDER BY id"
                )
            ]

        phase_counts: dict[str, int] = {}
        if {"NVTX_EVENTS", "StringIds"}.issubset(table_names):
            query = """
                SELECT COALESCE(n.text, s.value, ''), COUNT(*)
                FROM NVTX_EVENTS AS n
                LEFT JOIN StringIds AS s ON s.id = n.textId
                WHERE COALESCE(n.text, s.value, '') IN ('full_request', 'prefill', 'decode')
                GROUP BY COALESCE(n.text, s.value, '')
                ORDER BY 1
            """
            phase_counts = {str(name): int(count) for name, count in connection.execute(query)}

        sync_check: dict[str, Any] = {
            "total": counts.get("CUPTI_ACTIVITY_KIND_SYNCHRONIZATION"),
            "missing_correlation": None,
            "non_unique_runtime_mapping": None,
        }
        if {
            "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION",
            "CUPTI_ACTIVITY_KIND_RUNTIME",
        }.issubset(table_names):
            missing_correlation = int(
                connection.execute(
                    "SELECT COUNT(*) FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION "
                    "WHERE correlationId IS NULL"
                ).fetchone()[0]
            )
            non_unique = int(
                connection.execute(
                    """
                    SELECT COUNT(*) FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION AS s
                    WHERE s.correlationId IS NOT NULL
                      AND (SELECT COUNT(*) FROM CUPTI_ACTIVITY_KIND_RUNTIME AS r
                           WHERE r.correlationId = s.correlationId) <> 1
                    """
                ).fetchone()[0]
            )
            sync_check["missing_correlation"] = missing_correlation
            sync_check["non_unique_runtime_mapping"] = non_unique
            if missing_correlation:
                issues.append(
                    _issue("invalid", "SYNC_CORRELATION_MISSING", missing_correlation)
                )
            if non_unique:
                issues.append(
                    _issue("invalid", "SYNC_RUNTIME_MAPPING_NOT_UNIQUE", non_unique)
                )

        dropped_evidence: list[dict[str, Any]] = []
        if "DIAGNOSTIC_EVENT" in table_names:
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
                    "历史导出采用 lazy=true；本次必需表均需实际存在。",
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
            "required_tables": table_checks,
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
