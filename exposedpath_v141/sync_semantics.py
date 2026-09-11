"""ExposedPath S 层：Canonical Raw 加载与同步语义分类。"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .canonical_raw import load_canonical_raw_schema


class SyncSemanticsError(ValueError):
    """S 层输入或语义证据不满足冻结合同。"""


_REGISTRY_PATH = Path("docs") / "v1_4_1" / "contracts" / "sync_semantics_registry_v0_2.json"
_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
_ABI_SUFFIX = re.compile(r"_v[0-9]+$")
_ROLE_BY_UNIVERSE = {
    "SUPPORTED_PHYSICAL_BLOCKING_SYNC": "HOST_BLOCKING_SYNC",
    "DEVICE_DEPENDENCY_EDGE": "DEPENDENCY_EDGE",
    "IN_UNIVERSE_UNSUPPORTED": "UNSUPPORTED",
    "NON_BLOCKING_QUERY": "NON_SYNC",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_sync_registry(root: Path | None = None) -> dict[str, Any]:
    if root is None:
        root = Path(__file__).resolve().parents[1]
    registry = json.loads((root / _REGISTRY_PATH).read_text(encoding="utf-8"))
    if registry.get("registry_version") != "exposedpath-sync-registry-0.2.0":
        raise SyncSemanticsError("sync registry 版本不匹配")
    if registry.get("contract_version") != "exposedpath-measurement-contract-0.2.0":
        raise SyncSemanticsError("sync registry 与 Measurement Contract 不匹配")
    return registry


def _normalized_api_name(name: str) -> str:
    return _ABI_SUFFIX.sub("", name)


def classify_cuda_api(
    api_name: str,
    registry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """仅根据冻结 registry 与 runtime API 名称分类，不读取 CUPTI syncType。"""

    if registry is None:
        registry = load_sync_registry()
    original = str(api_name)
    normalized = _normalized_api_name(original)
    for rule in registry["rules"]:
        aliases = rule["aliases"]
        if original in aliases or any(normalized == _normalized_api_name(alias) for alias in aliases):
            universe = rule["universe_class"]
            return {
                "original_api_name": original,
                "normalized_api_name": normalized,
                "role": _ROLE_BY_UNIVERSE[universe],
                "universe_class": universe,
                "sync_kind": rule["sync_kind"],
                "completion_scope": rule["completion_scope"],
                "registry_rule_id": rule["registry_rule_id"],
                "required_evidence": list(rule["required_evidence"]),
            }
    return {
        "original_api_name": original,
        "normalized_api_name": normalized,
        "role": "UNCLASSIFIED",
        "universe_class": "UNCLASSIFIED_CUDA_API",
        "sync_kind": None,
        "completion_scope": None,
        "registry_rule_id": None,
        "required_evidence": [],
    }


def _validate_loaded_record(
    kind: str,
    record: Mapping[str, Any],
    schema: Mapping[str, Any],
) -> None:
    spec = schema["record_types"][kind]
    non_null = set(spec["required_non_null_fields"])
    nullable = set(spec["nullable_fields"])
    expected = non_null | nullable
    if set(record) != expected:
        raise SyncSemanticsError(f"{kind} 记录字段集合不匹配")
    if any(record[field] is None for field in non_null):
        raise SyncSemanticsError(f"{kind} 记录必需非空字段为空")


def load_canonical_bundle(manifest_path: Path) -> dict[str, Any]:
    """验证并加载 Canonical Raw bundle；不接触 Nsight SQLite。"""

    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_file():
        raise SyncSemanticsError(f"Canonical manifest 不存在: {manifest_path}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    schema = load_canonical_raw_schema()
    if manifest.get("schema_version") != schema["schema_version"]:
        raise SyncSemanticsError("Canonical schema_version 不匹配")
    if manifest.get("measurement_contract_version") != schema["measurement_contract_version"]:
        raise SyncSemanticsError("Measurement Contract 版本不匹配")
    source_sha = manifest.get("source", {}).get("sqlite", {}).get("sha256")
    if not isinstance(source_sha, str) or not _SHA256_PATTERN.fullmatch(source_sha):
        raise SyncSemanticsError("source SQLite SHA-256 非法")

    file_entries = manifest.get("files")
    if not isinstance(file_entries, dict) or set(file_entries) != set(schema["record_types"]):
        raise SyncSemanticsError("Canonical 文件集合不匹配")
    root = manifest_path.parent
    records: dict[str, list[dict[str, Any]]] = {}
    for kind, spec in schema["record_types"].items():
        entry = file_entries[kind]
        if entry.get("filename") != spec["filename"]:
            raise SyncSemanticsError(f"{kind} 文件名与 schema 不匹配")
        path = (root / entry["filename"]).resolve()
        if path.parent != root:
            raise SyncSemanticsError(f"{kind} 文件路径越界")
        if not path.is_file():
            raise SyncSemanticsError(f"{kind} 文件不存在")
        if _sha256(path) != entry.get("sha256"):
            raise SyncSemanticsError(f"{kind} SHA-256 不匹配")
        if path.stat().st_size != entry.get("size_bytes"):
            raise SyncSemanticsError(f"{kind} 文件大小不匹配")
        loaded: list[dict[str, Any]] = []
        try:
            with gzip.open(path, "rt", encoding="utf-8") as handle:
                for line_number, line in enumerate(handle, start=1):
                    record = json.loads(line)
                    if not isinstance(record, dict):
                        raise SyncSemanticsError(f"{kind}:{line_number} 不是对象")
                    _validate_loaded_record(kind, record, schema)
                    loaded.append(record)
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise SyncSemanticsError(f"{kind} 文件无法读取: {exc}") from exc
        if len(loaded) != entry.get("record_count"):
            raise SyncSemanticsError(f"{kind} 记录数不匹配")
        records[kind] = loaded
    return {"manifest": manifest, "records": records, "schema": schema}
