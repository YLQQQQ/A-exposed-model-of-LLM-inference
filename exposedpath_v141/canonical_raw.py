"""Canonical Raw v0.2 schema；SQLite 转换在后续任务实现。"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


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
        required = _list(spec.get("required_fields"), f"record_types.{kind}.required_fields")
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
        structured.get("required_identity_fields"),
        "structured_nvtx.required_identity_fields",
    )
    _ensure_unique(identity_fields, "structured identity")
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
