"""Versioned, fail-closed A/B bundle serialization and loading."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from . import __version__
from .a_accounting import calculate_a_windows, validate_a_record
from .ab_inputs import ABInputError, load_ab_inputs
from .b_provenance import BProvenanceError, calculate_b_syncs, validate_b_record
from .time_representation import time_representation, LEGACY, SIGNED


class ABBundleError(ValueError):
    """A/B bundle is malformed, unverifiable, or violates frozen lineage."""


_SCHEMA_PATH = Path("docs") / "v1_4_1" / "contracts" / "ab_schema_v0_2.json"
_RECORD_FILES = {
    "a_window_records": "a_window_records.jsonl.gz",
    "b_sync_records": "b_sync_records.jsonl.gz",
}
_CURRENT_QUALIFICATION = {
    "formal_evidence": False,
    "q0_status": "NOT_RUN",
    "scope": "A_B_LAYER_ONLY",
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _schema(root: Path | None = None, *, version: str = LEGACY) -> dict[str, Any]:
    if version not in (LEGACY, SIGNED):
        raise ABBundleError("A/B schema VERSION_UNSUPPORTED")
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    try:
        path = _SCHEMA_PATH if version == LEGACY else _SCHEMA_PATH.with_name("ab_schema_v0_3.json")
        value = json.loads((root / path).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(value)
    except (OSError, json.JSONDecodeError, ValidationError) as exc:
        raise ABBundleError(f"A/B schema 无法加载: {exc}") from exc
    if value.get("schema_version") != version:
        raise ABBundleError("A/B schema 版本不匹配")
    return value


def _validate_schema(schema: Mapping[str, Any], definition: str, record: Mapping[str, Any], label: str) -> None:
    try:
        Draft202012Validator(schema["$defs"][definition]).validate(dict(record))
    except (KeyError, ValidationError) as exc:
        raise ABBundleError(f"{label} 不符合冻结 A/B schema: {exc.message if isinstance(exc, ValidationError) else exc}") from exc


def _validate_current_qualification(manifest: Mapping[str, Any]) -> None:
    """Reject unsupported qualification claims until Gate 6 supplies hashed proof."""

    eligibility = _mapping(manifest.get("research_eligibility"), "A/B research_eligibility")
    if any(eligibility.get(field) != value for field, value in _CURRENT_QUALIFICATION.items()):
        raise ABBundleError("A/B current qualification policy rejects unsupported qualification claims")


def _validate_record_semantics(definition: str, record: Mapping[str, Any], label: str) -> None:
    """Enforce frozen cross-field invariants that JSON Schema cannot express."""

    try:
        if definition == "a_window_record":
            validate_a_record(record)
        elif definition == "b_sync_record":
            validate_b_record(record)
        else:
            raise ABBundleError(f"未知 A/B record 定义: {definition}")
    except (BProvenanceError, ValueError) as exc:
        raise ABBundleError(f"{label} 违反冻结 A/B 运行时约束: {exc}") from exc


def _write_records(path: Path, records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    with path.open("xb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as compressed:
            for record in records:
                compressed.write(
                    (json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                )
        raw_handle.flush()
        os.fsync(raw_handle.fileno())
    return {
        "filename": path.name,
        "record_count": len(records),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ABBundleError(f"{label} 必须是对象")
    return value


def _load_records(
    manifest_path: Path,
    entry: Mapping[str, Any],
    expected_filename: str,
    schema: Mapping[str, Any],
    definition: str,
) -> tuple[dict[str, Any], ...]:
    if entry.get("filename") != expected_filename:
        raise ABBundleError(f"{expected_filename} 文件名不匹配")
    record_count = entry.get("record_count")
    size_bytes = entry.get("size_bytes")
    expected_hash = entry.get("sha256")
    if not isinstance(record_count, int) or isinstance(record_count, bool) or record_count < 0:
        raise ABBundleError(f"{expected_filename} record_count 非法")
    if not isinstance(size_bytes, int) or isinstance(size_bytes, bool) or size_bytes < 0:
        raise ABBundleError(f"{expected_filename} size_bytes 非法")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise ABBundleError(f"{expected_filename} SHA-256 非法")
    record_path = (manifest_path.parent / expected_filename).resolve()
    if record_path.parent != manifest_path.parent.resolve() or not record_path.is_file():
        raise ABBundleError(f"{expected_filename} 不存在或路径越界")
    if record_path.stat().st_size != size_bytes:
        raise ABBundleError(f"{expected_filename} 文件大小不匹配")
    if _sha256(record_path) != expected_hash.upper():
        raise ABBundleError(f"{expected_filename} SHA-256 不匹配")
    records: list[dict[str, Any]] = []
    try:
        with gzip.open(record_path, "rt", encoding="utf-8", newline="") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.endswith("\n") or not line.strip():
                    raise ABBundleError(f"{expected_filename} 第 {line_number} 行不是规范 JSONL")
                value = json.loads(line)
                record = dict(_mapping(value, f"{expected_filename} 第 {line_number} 行"))
                _validate_schema(schema, definition, record, f"{expected_filename} 第 {line_number} 行")
                with time_representation(schema["schema_version"]):
                    _validate_record_semantics(definition, record, f"{expected_filename} 第 {line_number} 行")
                records.append(record)
    except ABBundleError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ABBundleError(f"{expected_filename} 无法读取") from exc
    if len(records) != record_count:
        raise ABBundleError(f"{expected_filename} 记录数不匹配")
    return tuple(records)


def _validate_external_lineage(
    manifest: Mapping[str, Any], canonical_manifest: Path | None, s_manifest: Path | None
) -> None:
    """When callers retain source paths, verify every recorded lineage edge again."""

    source = _mapping(manifest.get("source"), "A/B source")
    if canonical_manifest is not None:
        canonical_manifest = Path(canonical_manifest).resolve()
        if not canonical_manifest.is_file():
            raise ABBundleError("A/B Canonical manifest 无法读取")
        if source.get("canonical_manifest_name") != canonical_manifest.name:
            raise ABBundleError("A/B Canonical manifest 名称与输入不匹配")
        if source.get("canonical_manifest_sha256") != _sha256(canonical_manifest):
            raise ABBundleError("A/B Canonical manifest SHA-256 与输入不匹配")
        try:
            canonical = json.loads(canonical_manifest.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ABBundleError("A/B Canonical manifest 无法读取") from exc
        if _mapping(canonical, "Canonical manifest").get("data_role") != manifest.get("data_role"):
            raise ABBundleError("A/B data_role 不得升级 Canonical 数据角色")
        if manifest['schema_version'] == SIGNED and source['pass_identity_sha256'] != canonical['gate8_sources']['pass_identity']['sha256'].upper():
            raise ABBundleError('A/B pass identity SOURCE_MISMATCH')
        sqlite = _mapping(_mapping(canonical, "Canonical manifest").get("source"), "Canonical source").get("sqlite")
        if _mapping(sqlite, "Canonical source.sqlite").get("sha256") != source.get("source_sqlite_sha256"):
            raise ABBundleError("A/B source SQLite SHA-256 与 Canonical 不匹配")
    if s_manifest is not None:
        s_manifest = Path(s_manifest).resolve()
        if not s_manifest.is_file():
            raise ABBundleError("A/B S manifest 无法读取")
        if source.get("s_manifest_name") != s_manifest.name:
            raise ABBundleError("A/B S manifest 名称与输入不匹配")
        if source.get("s_manifest_sha256") != _sha256(s_manifest):
            raise ABBundleError("A/B S manifest SHA-256 与输入不匹配")
        try:
            s = _mapping(json.loads(s_manifest.read_text(encoding="utf-8")), "S manifest")
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise ABBundleError("A/B S manifest 无法读取") from exc
        if s.get("data_role") != manifest.get("data_role"):
            raise ABBundleError("A/B data_role 不得升级 S 数据角色")
        s_source = _mapping(s.get("source"), "S source")
        if manifest['schema_version'] == SIGNED and source['scope_manifest_sha256'] != s_source.get('scope_manifest_sha256'):
            raise ABBundleError('A/B scope SOURCE_MISMATCH')
        if s_source.get("canonical_manifest_sha256") != source.get("canonical_manifest_sha256"):
            raise ABBundleError("A/B S-to-Canonical lineage 不匹配")
        if s_source.get("source_sqlite_sha256") != source.get("source_sqlite_sha256"):
            raise ABBundleError("A/B S source SQLite lineage 不匹配")
        s_registry = _mapping(s_source.get("sync_registry"), "S source.sync_registry")
        ab_registry = _mapping(source.get("sync_registry"), "A/B source.sync_registry")
        if (
            s_registry.get("version") != ab_registry.get("version")
            or s_registry.get("sha256") != ab_registry.get("sha256")
        ):
            raise ABBundleError("A/B sync registry lineage 不匹配")


def load_ab_bundle(
    manifest_path: Path,
    *,
    canonical_manifest: Path | None = None,
    s_manifest: Path | None = None,
) -> dict[str, Any]:
    """Strictly load a self-verifying A/B bundle without reclassifying records."""

    manifest_path = Path(manifest_path).resolve()
    if manifest_path.name != "ab_manifest.json" or not manifest_path.is_file():
        raise ABBundleError(f"A/B manifest 不存在或名称错误: {manifest_path}")
    try:
        manifest = dict(_mapping(json.loads(manifest_path.read_text(encoding="utf-8")), "A/B manifest"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ABBundleError("A/B manifest 无法读取") from exc
    schema = _schema(version=manifest.get("schema_version"))
    _validate_schema(schema, "manifest", manifest, "A/B manifest")
    _validate_current_qualification(manifest)
    files = _mapping(manifest.get("files"), "A/B files")
    if set(files) != set(_RECORD_FILES):
        raise ABBundleError("A/B files 集合不匹配")
    a_records = _load_records(
        manifest_path, _mapping(files["a_window_records"], "A 文件条目"),
        _RECORD_FILES["a_window_records"], schema, "a_window_record",
    )
    b_records = _load_records(
        manifest_path, _mapping(files["b_sync_records"], "B 文件条目"),
        _RECORD_FILES["b_sync_records"], schema, "b_sync_record",
    )
    summary = _mapping(manifest.get("summary"), "A/B summary")
    expected_counts = {
        "window_count": len(a_records),
        "physical_sync_count": len(b_records),
        "b_valid_count": sum(record["validity"] == "B_VALID" for record in b_records),
        "b_not_applicable_count": sum(record["validity"] == "B_NOT_APPLICABLE" for record in b_records),
        "b_ambiguous_count": sum(record["validity"] == "B_AMBIGUOUS" for record in b_records),
        "b_invalid_count": sum(record["validity"] == "B_INVALID" for record in b_records),
    }
    if any(summary.get(field) != value for field, value in expected_counts.items()):
        raise ABBundleError("A/B summary 计数与记录不匹配")
    if len({record["window_id"] for record in a_records}) != len(a_records):
        raise ABBundleError("A/B A window_id 重复")
    if len({record["sync_id"] for record in b_records}) != len(b_records):
        raise ABBundleError("A/B B sync_id 重复")
    _validate_external_lineage(manifest, canonical_manifest, s_manifest)
    return {
        "manifest": manifest,
        "a_window_records": a_records,
        "b_sync_records": b_records,
    }


def analyze_ab(canonical_manifest: Path, s_manifest: Path, output_dir: Path, *, scope_manifest: Path | None = None) -> Path:
    version = LEGACY if scope_manifest is None else SIGNED
    with time_representation(version):
        return _analyze_ab(canonical_manifest, s_manifest, output_dir, scope_manifest=scope_manifest, version=version)


def _analyze_ab(canonical_manifest, s_manifest, output_dir, *, scope_manifest, version):
    """Project trusted Canonical+S input into an atomic, immutable A/B bundle."""

    canonical_manifest = Path(canonical_manifest).resolve()
    s_manifest = Path(s_manifest).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"拒绝覆盖已有输出目录: {output_dir}")
    schema = _schema(version=version)
    try:
        if scope_manifest is None:
            inputs = load_ab_inputs(canonical_manifest, s_manifest)
        else:
            from dataclasses import replace
            from .gate8_scope import build_projected_ab_inputs
            from .ab_inputs import _load_s_records, _validate_lineage, _validate_s_join
            inputs = build_projected_ab_inputs(canonical_manifest, scope_manifest)
            sm, sr = _load_s_records(s_manifest)
            _validate_lineage(canonical_manifest, inputs.canonical, sm)
            _validate_s_join(inputs.canonical, sr)
            if (sm.get("observation_profile") != inputs.canonical.manifest.get("observation_profile")
                    or sm["source"].get("scope_manifest_sha256") != _sha256(Path(scope_manifest))
                    or {r["sync_id"]:r for r in sr} != {r["sync_id"]:r for r in inputs.s_records}):
                raise ABBundleError("S scope/record SOURCE_MISMATCH")
            inputs = replace(inputs, s_manifest=sm, s_records=sr)
        a_records = calculate_a_windows(inputs)
        b_records = calculate_b_syncs(inputs)
    except (ABInputError, BProvenanceError, ValueError, OSError, json.JSONDecodeError) as exc:
        raise ABBundleError(f"A/B 输入或计算失败: {exc}") from exc
    for record in a_records:
        validate_a_record(record)
        _validate_schema(schema, "a_window_record", record, "A 记录")
    for record in b_records:
        validate_b_record(record)
        _validate_schema(schema, "b_sync_record", record, "B 记录")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}_", dir=output_dir.parent))
    try:
        files = {
            "a_window_records": _write_records(staging / _RECORD_FILES["a_window_records"], a_records),
            "b_sync_records": _write_records(staging / _RECORD_FILES["b_sync_records"], b_records),
        }
        b_counts = Counter(record["validity"] for record in b_records)
        quality_reasons = list(dict.fromkeys((*inputs.global_quality_reasons, *("WINDOW_DISCOVERY_INVALID" for _ in inputs.window_discovery_issues))))
        source = inputs.s_manifest["source"]
        manifest = {
            "schema_version": schema["schema_version"],
            "measurement_contract_version": schema["measurement_contract_version"],
            "canonical_schema_version": inputs.canonical.manifest["schema_version"],
            "s_schema_version": inputs.s_manifest["schema_version"],
            "analyzer_version": __version__,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "data_role": inputs.canonical.manifest["data_role"],
            "source": {
                "canonical_manifest_name": canonical_manifest.name,
                "canonical_manifest_sha256": _sha256(canonical_manifest),
                "s_manifest_name": s_manifest.name,
                "s_manifest_sha256": _sha256(s_manifest),
                "source_sqlite_sha256": inputs.canonical.manifest["source"]["sqlite"]["sha256"],
                "sync_registry": dict(source["sync_registry"]),
            },
            "files": files,
            "quality": {
                "status": "FAIL_CLOSED" if quality_reasons else "VALID",
                "reasons": quality_reasons,
            },
            "summary": {
                "window_count": len(a_records),
                "physical_sync_count": len(b_records),
                "b_valid_count": b_counts["B_VALID"],
                "b_not_applicable_count": b_counts["B_NOT_APPLICABLE"],
                "b_ambiguous_count": b_counts["B_AMBIGUOUS"],
                "b_invalid_count": b_counts["B_INVALID"],
            },
            "research_eligibility": {
                "formal_evidence": False,
                "q0_status": "NOT_RUN",
                "scope": "A_B_LAYER_ONLY",
            },
        }
        if version == SIGNED:
            manifest['validation_role'] = 'LOCAL_DETERMINISTIC_ONLY'
            manifest['measurement_validity'] = 'NOT_ASSESSED'
            manifest['source']['scope_manifest_sha256'] = _sha256(Path(scope_manifest))
            manifest['source']['pass_identity_sha256'] = inputs.canonical.manifest['gate8_sources']['pass_identity']['sha256'].upper()
        _validate_schema(schema, "manifest", manifest, "A/B manifest")
        manifest_path = staging / "ab_manifest.json"
        with manifest_path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(manifest, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        staging.rename(output_dir)
    except BaseException:
        if staging.exists():
            shutil.rmtree(staging)
        raise
    return output_dir / "ab_manifest.json"
