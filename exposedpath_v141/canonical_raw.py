"""Canonical Raw v0.2 schema；SQLite 转换在后续任务实现。"""

from __future__ import annotations

import hashlib
import gzip
import io
import json
import os
import shutil
import sqlite3
import tempfile
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .observation import inspect_sqlite


class CanonicalRawSchemaError(ValueError):
    """Canonical Raw schema 内部不一致。"""


_SCHEMA_PATH = (
    Path("docs") / "v1_4_1" / "contracts" / "canonical_raw_schema_v0_2.json"
)
_REQUIRED_RECORD_KINDS = {
    "nvtx",
    "cuda_api",
    "physical_sync",
    "device_activity",
    "cuda_event",
    "context",
    "stream",
    "diagnostic",
}
_PLACEHOLDERS = ("todo", "tbd", "待定")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CanonicalRawSchemaError(f"{label} 必须是对象")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise CanonicalRawSchemaError(f"{label} 必须是数组")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CanonicalRawSchemaError(f"{label} 必须是非空字符串")
    return value


def _ensure_unique(values: list[str], label: str) -> None:
    duplicates = sorted({value for value in values if values.count(value) > 1})
    if duplicates:
        raise CanonicalRawSchemaError(f"{label} 字段重复: {', '.join(duplicates)}")


def _scan_placeholders(value: Any, path: str = "root") -> None:
    if isinstance(value, str):
        if any(token in value.casefold() for token in _PLACEHOLDERS):
            raise CanonicalRawSchemaError(f"发现占位文本: {path}")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            _scan_placeholders(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_placeholders(child, f"{path}[{index}]")


def validate_canonical_raw_schema(schema: Mapping[str, Any]) -> None:
    """校验 schema bundle 的研究边界与机器结构。"""

    schema = _mapping(schema, "schema")
    _text(schema.get("schema_version"), "schema_version")
    if schema.get("measurement_contract_version") != "exposedpath-measurement-contract-0.2.0":
        raise CanonicalRawSchemaError("Measurement Contract 版本不匹配")
    _text(schema.get("adapter_id"), "adapter_id")

    clock = _mapping(schema.get("clock_model"), "clock_model")
    if clock != {
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "unit": "ns",
        "comparison_scope": "SINGLE_SOURCE_TRACE_ONLY",
        "timestamp_normalization": "DISABLED",
    }:
        raise CanonicalRawSchemaError("时钟模型必须是单 trace 相对纳秒半开区间")

    record_identity = _mapping(schema.get("record_identity"), "record_identity")
    if record_identity.get("timestamp_order_is_identity") is not False:
        raise CanonicalRawSchemaError("不得以时间顺序充当记录身份")
    if record_identity.get("filename_is_experiment_identity") is not False:
        raise CanonicalRawSchemaError("不得以文件名充当实验身份")
    if record_identity.get("tuple") != [
        "source_sqlite_sha256",
        "source_table",
        "source_rowid",
    ]:
        raise CanonicalRawSchemaError("全局记录身份必须绑定 SQLite 哈希和 source row")

    adapters = _list(schema.get("source_adapters"), "source_adapters")
    if adapters != [
        {
            "adapter_id": "NSYS-SQLITE-2026.1.1-3.24.14",
            "export_product_version": "2026.1.1.204",
            "export_schema_version": "3.24.14",
        }
    ]:
        raise CanonicalRawSchemaError("Nsight source adapter 未锁定到已审查 schema")
    if schema.get("adapter_id") != adapters[0]["adapter_id"]:
        raise CanonicalRawSchemaError("adapter_id 与 source_adapters 不一致")

    manifest = _mapping(schema.get("bundle_manifest"), "bundle_manifest")
    _text(manifest.get("filename"), "bundle_manifest.filename")
    manifest_fields = _list(manifest.get("required_fields"), "bundle_manifest.required_fields")
    _ensure_unique(manifest_fields, "bundle manifest")
    if not {"source", "clock", "identity", "files", "observation_validity"} <= set(manifest_fields):
        raise CanonicalRawSchemaError("bundle manifest 缺少 lineage 或 validity 字段")

    base_fields = _list(schema.get("record_base_required_fields"), "record_base_required_fields")
    _ensure_unique(base_fields, "record base")
    record_types = _mapping(schema.get("record_types"), "record_types")
    if set(record_types) != _REQUIRED_RECORD_KINDS:
        missing = sorted(_REQUIRED_RECORD_KINDS - set(record_types))
        extra = sorted(set(record_types) - _REQUIRED_RECORD_KINDS)
        raise CanonicalRawSchemaError(f"record kind 不完整: missing={missing}, extra={extra}")

    forbidden = set(_list(schema.get("forbidden_semantic_fields"), "forbidden_semantic_fields"))
    filenames: list[str] = []
    for kind, raw_spec in record_types.items():
        spec = _mapping(raw_spec, f"record_types.{kind}")
        filenames.append(_text(spec.get("filename"), f"record_types.{kind}.filename"))
        required = _list(
            spec.get("required_non_null_fields"),
            f"record_types.{kind}.required_non_null_fields",
        )
        nullable = _list(spec.get("nullable_fields"), f"record_types.{kind}.nullable_fields")
        _ensure_unique(required, f"{kind}.required")
        _ensure_unique(nullable, f"{kind}.nullable")
        overlap = sorted(set(required) & set(nullable))
        if overlap:
            raise CanonicalRawSchemaError(f"{kind} 字段同时属于 required/nullable: {overlap}")
        if not set(base_fields) <= set(required):
            raise CanonicalRawSchemaError(f"{kind} 缺少 record base 字段")
        leaked = sorted((set(required) | set(nullable)) & forbidden)
        if leaked:
            raise CanonicalRawSchemaError(f"{kind} 出现 Raw 越层字段: {leaked}")
    if len(set(filenames)) != len(filenames):
        raise CanonicalRawSchemaError("record filename 重复")

    structured = _mapping(schema.get("structured_nvtx"), "structured_nvtx")
    if structured.get("prefix") != "EXPOSEDPATH_JSON_V1:":
        raise CanonicalRawSchemaError("结构化 NVTX 前缀不匹配")
    identity_fields = _list(
        structured.get("common_identity_fields"),
        "structured_nvtx.common_identity_fields",
    )
    _ensure_unique(identity_fields, "structured common identity")
    by_kind = _mapping(
        structured.get("required_fields_by_kind"),
        "structured_nvtx.required_fields_by_kind",
    )
    if set(by_kind) != set(structured.get("allowed_kinds", [])):
        raise CanonicalRawSchemaError("结构化 NVTX kind 与字段规则不一致")
    for kind, fields in by_kind.items():
        _ensure_unique(_list(fields, f"structured_nvtx.{kind}"), f"structured {kind}")
    if structured.get("legacy_label_policy") != "PRESERVE_AS_TEXT_WITHOUT_IDENTITY_INFERENCE":
        raise CanonicalRawSchemaError("旧 NVTX 标签不得推断实验身份")

    if schema.get("invalid_input_policy") != "REFUSE_CONVERSION":
        raise CanonicalRawSchemaError("invalid 输入必须拒绝转换")
    if schema.get("existing_output_policy") != "REFUSE_OVERWRITE":
        raise CanonicalRawSchemaError("已有输出必须拒绝覆盖")
    _scan_placeholders(schema)


def load_canonical_raw_schema(root: Path | None = None) -> dict[str, Any]:
    """加载并校验仓库中的 Canonical Raw schema。"""

    if root is None:
        root = Path(__file__).resolve().parents[1]
    with (root / _SCHEMA_PATH).open("r", encoding="utf-8") as handle:
        schema = json.load(handle)
    validate_canonical_raw_schema(schema)
    return schema


def _validate_record(kind: str, record: Mapping[str, Any], schema: Mapping[str, Any]) -> None:
    spec = schema["record_types"][kind]
    non_null = set(spec["required_non_null_fields"])
    nullable = set(spec["nullable_fields"])
    expected = non_null | nullable
    actual = set(record)
    if actual != expected:
        raise ValueError(
            f"{kind} 字段集合不匹配: missing={sorted(expected-actual)}, extra={sorted(actual-expected)}"
        )
    null_required = sorted(field for field in non_null if record[field] is None)
    if null_required:
        raise ValueError(f"{kind} 必需非空字段为空: {null_required}")
    if "start_ns" in record:
        start = record["start_ns"]
        end = record.get("end_ns")
        if not isinstance(start, int) or start < 0:
            raise ValueError(f"{kind} 时间区间非法")
        if end is not None and (not isinstance(end, int) or end < start):
            raise ValueError(f"{kind} 时间区间非法")
    if "timestamp_ns" in record:
        timestamp = record["timestamp_ns"]
        if not isinstance(timestamp, int) or timestamp < 0:
            raise ValueError(f"{kind} 时间区间非法")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _open_readonly(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path.resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
    connection.row_factory = sqlite3.Row
    connection.text_factory = lambda value: value.decode("utf-8", errors="replace")
    connection.execute("PRAGMA query_only = ON")
    return connection


def _global_parts(global_id: int | None) -> tuple[int | None, int | None]:
    if global_id is None:
        return None, None
    value = int(global_id)
    return (value >> 24) & 0xFFFFFF, value & 0xFFFFFF


def _process_part(global_pid: int | None) -> int | None:
    return _global_parts(global_pid)[0]


def _record_id(kind: str, table: str, rowid: int) -> str:
    return f"{kind}:{table}:{rowid}"


def _base(kind: str, table: str, rowid: int) -> dict[str, Any]:
    return {
        "record_id": _record_id(kind, table, rowid),
        "source_table": table,
        "source_rowid": rowid,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
    }


def _write_jsonl(path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    with path.open("xb") as raw_handle:
        with gzip.GzipFile(
            filename="", mode="wb", fileobj=raw_handle, mtime=0
        ) as gzip_handle:
            with io.TextIOWrapper(
                gzip_handle, encoding="utf-8", newline="\n"
            ) as text_handle:
                for record in records:
                    text_handle.write(
                        json.dumps(
                            record,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                    )
                    text_handle.write("\n")
        raw_handle.flush()
        os.fsync(raw_handle.fileno())
    return {
        "filename": path.name,
        "record_count": len(records),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def _fetch_rows(connection: sqlite3.Connection, table: str, order: str) -> list[sqlite3.Row]:
    return list(connection.execute(f'SELECT rowid AS source_rowid, * FROM "{table}" ORDER BY {order}'))


def _parse_structured_identity(
    text: str,
    record_id: str,
    structured_schema: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    prefix = structured_schema["prefix"]
    if not text.startswith(prefix):
        return None, None
    try:
        payload = json.loads(text[len(prefix) :])
    except json.JSONDecodeError as exc:
        return None, {
            "code": "MALFORMED_STRUCTURED_NVTX",
            "detail": {"record_id": record_id, "message": str(exc)},
        }
    if not isinstance(payload, dict):
        return None, {
            "code": "MALFORMED_STRUCTURED_NVTX",
            "detail": {"record_id": record_id, "message": "payload 不是对象"},
        }
    kind = payload.get("kind")
    if kind not in structured_schema["allowed_kinds"]:
        return None, {
            "code": "UNKNOWN_STRUCTURED_NVTX_KIND",
            "detail": {"record_id": record_id, "kind": kind},
        }
    required = list(structured_schema["common_identity_fields"])
    required.extend(structured_schema["required_fields_by_kind"][kind])
    missing = [
        field
        for field in required
        if field not in payload or payload[field] is None or payload[field] == ""
    ]
    if missing:
        return None, {
            "code": "INCOMPLETE_STRUCTURED_NVTX_IDENTITY",
            "detail": {"record_id": record_id, "missing_fields": missing},
        }
    return payload, None


def _extract_records(
    connection: sqlite3.Connection,
    schema: Mapping[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    strings = {
        int(row[0]): str(row[1])
        for row in connection.execute("SELECT id, value FROM StringIds")
    }
    result: dict[str, list[dict[str, Any]]] = {
        "nvtx": [],
        "cuda_api": [],
        "physical_sync": [],
        "device_activity": [],
        "cuda_event": [],
        "context": [],
        "stream": [],
        "diagnostic": [],
    }
    identity_issues: list[dict[str, Any]] = []
    structured_count = 0
    legacy_phase_count = 0

    for row in _fetch_rows(connection, "NVTX_EVENTS", "start, COALESCE(end,start), source_rowid"):
        pid, tid = _global_parts(row["globalTid"])
        end_pid, end_tid = _global_parts(row["endGlobalTid"])
        record = _base("nvtx", "NVTX_EVENTS", row["source_rowid"])
        text = row["text"] if row["text"] is not None else strings.get(row["textId"], "")
        structured_identity, identity_issue = _parse_structured_identity(
            text,
            record["record_id"],
            schema["structured_nvtx"],
        )
        if structured_identity is not None:
            structured_count += 1
        elif text in {"full_request", "prefill", "decode"}:
            legacy_phase_count += 1
        if identity_issue is not None:
            identity_issues.append(identity_issue)
        record.update(
            start_ns=row["start"], end_ns=row["end"], event_type=row["eventType"],
            range_id=row["rangeId"], category_id=row["category"], color=row["color"],
            text=text,
            global_tid=row["globalTid"], process_id=pid, thread_id=tid,
            end_global_tid=row["endGlobalTid"], end_process_id=end_pid, end_thread_id=end_tid,
            text_id=row["textId"], domain_id=row["domainId"], json_text=row["jsonText"],
            structured_identity=structured_identity,
        )
        result["nvtx"].append(record)

    runtime_by_correlation: dict[int, list[dict[str, Any]]] = {}
    for row in _fetch_rows(connection, "CUPTI_ACTIVITY_KIND_RUNTIME", "start, end, source_rowid"):
        pid, tid = _global_parts(row["globalTid"])
        record = _base("cuda_api", "CUPTI_ACTIVITY_KIND_RUNTIME", row["source_rowid"])
        record.update(
            start_ns=row["start"], end_ns=row["end"], event_class=row["eventClass"],
            global_tid=row["globalTid"], process_id=pid, thread_id=tid,
            correlation_id=row["correlationId"], name_id=row["nameId"],
            api_name=strings.get(row["nameId"], ""), return_value=row["returnValue"],
            callchain_id=row["callchainId"],
        )
        result["cuda_api"].append(record)
        if row["correlationId"] is not None:
            runtime_by_correlation.setdefault(int(row["correlationId"]), []).append(record)

    sync_enums = {
        int(row[0]): (row[1], row[2])
        for row in connection.execute("SELECT id, name, label FROM ENUM_CUPTI_SYNC_TYPE")
    }
    for row in _fetch_rows(
        connection, "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION", "start, end, source_rowid"
    ):
        mappings = runtime_by_correlation.get(row["correlationId"], [])
        runtime = mappings[0] if len(mappings) == 1 else None
        enum_name, enum_label = sync_enums.get(row["syncType"], (None, None))
        record = _base(
            "physical_sync", "CUPTI_ACTIVITY_KIND_SYNCHRONIZATION", row["source_rowid"]
        )
        record.update(
            start_ns=row["start"], end_ns=row["end"], device_id=row["deviceId"],
            context_id=row["contextId"], green_context_id=row["greenContextId"],
            stream_id=row["streamId"], correlation_id=row["correlationId"],
            global_pid=row["globalPid"], process_id=_process_part(row["globalPid"]),
            sync_type_id=row["syncType"], sync_type_name=enum_name, sync_type_label=enum_label,
            event_id=row["eventId"], event_sync_id=row["eventSyncId"],
            runtime_mapping_count=len(mappings),
            runtime_record_id=runtime["record_id"] if runtime else None,
            runtime_api_name=runtime["api_name"] if runtime else None,
            runtime_start_ns=runtime["start_ns"] if runtime else None,
            runtime_end_ns=runtime["end_ns"] if runtime else None,
            runtime_global_tid=runtime["global_tid"] if runtime else None,
            runtime_thread_id=runtime["thread_id"] if runtime else None,
        )
        result["physical_sync"].append(record)

    activity_specs = (
        ("CUPTI_ACTIVITY_KIND_KERNEL", "KERNEL"),
        ("CUPTI_ACTIVITY_KIND_MEMCPY", "MEMCPY"),
        ("CUPTI_ACTIVITY_KIND_MEMSET", "MEMSET"),
    )
    for table, activity_kind in activity_specs:
        for row in _fetch_rows(connection, table, "start, end, source_rowid"):
            if activity_kind == "KERNEL":
                name = strings.get(row["demangledName"], strings.get(row["shortName"], ""))
                attributes = {
                    "demangled_name_id": row["demangledName"],
                    "short_name_id": row["shortName"],
                }
                graph_id = row["graphId"]
            elif activity_kind == "MEMCPY":
                name = "MEMCPY"
                attributes = {
                    "bytes": row["bytes"], "copy_kind": row["copyKind"],
                    "src_kind": row["srcKind"], "dst_kind": row["dstKind"],
                }
                graph_id = None
            else:
                name = "MEMSET"
                attributes = {
                    "bytes": row["bytes"], "value": row["value"], "mem_kind": row["memKind"],
                }
                graph_id = None
            record = _base("device_activity", table, row["source_rowid"])
            record.update(
                activity_kind=activity_kind, start_ns=row["start"], end_ns=row["end"],
                device_id=row["deviceId"], context_id=row["contextId"],
                green_context_id=row["greenContextId"], stream_id=row["streamId"],
                correlation_id=row["correlationId"], global_pid=row["globalPid"],
                process_id=_process_part(row["globalPid"]), name=name, attributes=attributes,
                graph_node_id=row["graphNodeId"], graph_id=graph_id,
            )
            result["device_activity"].append(record)
    result["device_activity"].sort(
        key=lambda item: (item["start_ns"], item["end_ns"], item["source_table"], item["source_rowid"])
    )

    for row in _fetch_rows(connection, "CUPTI_ACTIVITY_KIND_CUDA_EVENT", "timestamp, source_rowid"):
        record = _base("cuda_event", "CUPTI_ACTIVITY_KIND_CUDA_EVENT", row["source_rowid"])
        record.update(
            timestamp_ns=row["timestamp"], device_id=row["deviceId"],
            context_id=row["contextId"], green_context_id=row["greenContextId"],
            stream_id=row["streamId"], correlation_id=row["correlationId"],
            global_pid=row["globalPid"], process_id=_process_part(row["globalPid"]),
            event_id=row["eventId"], event_sync_id=row["eventSyncId"],
        )
        result["cuda_event"].append(record)

    for row in _fetch_rows(connection, "TARGET_INFO_CUDA_CONTEXT_INFO", "processId, contextId, source_rowid"):
        record = _base("context", "TARGET_INFO_CUDA_CONTEXT_INFO", row["source_rowid"])
        record.update(
            process_id=row["processId"], device_id=row["deviceId"], context_id=row["contextId"],
            null_stream_id=row["nullStreamId"], hardware_id=row["hwId"], vm_id=row["vmId"],
            parent_context_id=row["parentContextId"], is_green_context=row["isGreenContext"],
        )
        result["context"].append(record)

    for row in _fetch_rows(connection, "TARGET_INFO_CUDA_STREAM", "processId, contextId, streamId, source_rowid"):
        record = _base("stream", "TARGET_INFO_CUDA_STREAM", row["source_rowid"])
        record.update(
            process_id=row["processId"], context_id=row["contextId"], stream_id=row["streamId"],
            hardware_id=row["hwId"], vm_id=row["vmId"], priority=row["priority"], flag=row["flag"],
        )
        result["stream"].append(record)

    for row in _fetch_rows(connection, "DIAGNOSTIC_EVENT", "timestamp, source_rowid"):
        record = _base("diagnostic", "DIAGNOSTIC_EVENT", row["source_rowid"])
        record.update(
            timestamp_ns=row["timestamp"], source_id=row["source"], severity_id=row["severity"],
            text=row["text"],
        )
        result["diagnostic"].append(record)
    if legacy_phase_count:
        identity_issues.append(
            {
                "code": "UNSTRUCTURED_EXPOSEDPATH_PHASE_LABEL",
                "detail": {"record_count": legacy_phase_count},
            }
        )
    if structured_count == 0 and legacy_phase_count == 0:
        identity_issues.append(
            {"code": "NO_STRUCTURED_EXPOSEDPATH_NVTX", "detail": {"record_count": 0}}
        )
    return result, identity_issues


def convert_sqlite_to_canonical(
    sqlite_path: Path,
    output_dir: Path,
    data_role: str,
    raw_sha256: str | None = None,
    collector_version: str | None = None,
    source_manifest: Path | None = None,
) -> Path:
    """只读转换 Nsight SQLite；返回最终 canonical manifest 路径。"""

    sqlite_path = Path(sqlite_path).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"拒绝覆盖已有输出目录: {output_dir}")
    schema = load_canonical_raw_schema()
    observation = inspect_sqlite(
        sqlite_path, data_role, raw_sha256, collector_version, source_manifest
    )
    if observation["validity"]["status"] == "invalid":
        raise ValueError("observation invalid，拒绝 Canonical Raw 转换")

    source_manifest_data: dict[str, Any] | None = None
    source_manifest_sha = None
    if source_manifest is not None:
        source_manifest = Path(source_manifest).resolve()
        source_manifest_data = json.loads(source_manifest.read_text(encoding="utf-8"))
        source_manifest_sha = _sha256(source_manifest)

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}_", dir=output_dir.parent))
    try:
        with _open_readonly(sqlite_path) as connection:
            records, nvtx_identity_issues = _extract_records(connection, schema)
        files: dict[str, dict[str, Any]] = {}
        for kind, spec in schema["record_types"].items():
            for record in records[kind]:
                _validate_record(kind, record, schema)
            files[kind] = _write_jsonl(staging / spec["filename"], records[kind])

        identity_fields = [
            "experiment_id", "wmpc_id", "run_id", "run_role", "pass_id", "repeat_id"
        ]
        identity_values = {
            field: source_manifest_data.get(field) if source_manifest_data else None
            for field in identity_fields
        }
        missing_identity = [field for field, value in identity_values.items() if value is None]
        identity_conflicts: list[dict[str, Any]] = []
        if source_manifest_data is not None:
            for nvtx_record in records["nvtx"]:
                structured_identity = nvtx_record["structured_identity"]
                if structured_identity is None:
                    continue
                mismatched = {
                    field: {
                        "manifest": source_manifest_data.get(field),
                        "nvtx": structured_identity.get(field),
                    }
                    for field in identity_fields
                    if source_manifest_data.get(field) is not None
                    and structured_identity.get(field) != source_manifest_data.get(field)
                }
                if mismatched:
                    identity_conflicts.append(
                        {
                            "record_id": nvtx_record["record_id"],
                            "fields": mismatched,
                        }
                    )
        if identity_conflicts:
            nvtx_identity_issues.append(
                {
                    "code": "MANIFEST_NVTX_IDENTITY_CONFLICT",
                    "detail": identity_conflicts,
                }
            )
        identity_status = (
            "VALID" if not missing_identity and not nvtx_identity_issues else "AMBIGUOUS"
        )
        source_fact = observation["observed_facts"]
        canonical_manifest = {
            "schema_version": schema["schema_version"],
            "measurement_contract_version": schema["measurement_contract_version"],
            "adapter_id": schema["adapter_id"],
            "analyzer_version": __version__,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "data_role": data_role,
            "source": {
                "sqlite": source_fact["sqlite"],
                "raw": source_fact["raw"],
                "source_manifest": {
                    "name": source_manifest.name if source_manifest else None,
                    "sha256": source_manifest_sha,
                },
                "export": source_fact["export"],
            },
            "clock": schema["clock_model"],
            "identity": {
                "status": identity_status,
                "values": identity_values,
                "missing_fields": missing_identity,
                "filename_inference_used": False,
                "nvtx_status": "VALID" if not nvtx_identity_issues else "AMBIGUOUS",
                "issues": nvtx_identity_issues,
            },
            "files": files,
            "observation_validity": observation["validity"],
            "research_eligibility": {
                "formal_evidence": False,
                "q0_status": "NOT_RUN",
                "blocking_reasons": ["CANONICAL_RAW_ONLY", "Q0_NOT_RUN"],
            },
        }
        manifest_path = staging / schema["bundle_manifest"]["filename"]
        with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(canonical_manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        staging.replace(output_dir)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return output_dir / schema["bundle_manifest"]["filename"]
