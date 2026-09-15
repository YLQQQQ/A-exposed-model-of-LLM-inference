"""ExposedPath S 层版本化产物。"""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import __version__
from .contract import load_contract_bundle
from .sync_semantics import (
    analyze_sync_semantics,
    build_semantic_inventory,
    load_canonical_bundle,
    load_sync_registry,
)


class SBundleError(ValueError):
    """S schema 或输出记录违反冻结合同。"""


_SCHEMA_PATH = Path("docs") / "v1_4_1" / "contracts" / "s_layer_schema_v0_2.json"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_s_layer_schema(root: Path | None = None) -> dict[str, Any]:
    if root is None:
        root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / _SCHEMA_PATH).read_text(encoding="utf-8"))
    validate_s_layer_schema(schema)
    return schema


def validate_s_layer_schema(schema: Mapping[str, Any]) -> None:
    if schema.get("schema_version") != "exposedpath-s-layer/0.2.0":
        raise SBundleError("S schema 版本不匹配")
    if schema.get("input_schema_version") != "exposedpath-canonical-raw/0.2.0":
        raise SBundleError("S schema 的 Canonical Raw 输入版本不匹配")
    contract = load_contract_bundle()["contract"]
    if schema.get("measurement_contract_version") != contract["contract_version"]:
        raise SBundleError("S schema 与 Measurement Contract 版本不匹配")
    fields = schema.get("sync_record_fields")
    if not isinstance(fields, list) or len(fields) != len(set(fields)):
        raise SBundleError("S sync 字段必须是无重复数组")
    missing = sorted(set(contract["s_layer"]["output_fields"]) - set(fields))
    if missing:
        raise SBundleError(f"S schema 缺少合同字段: {', '.join(missing)}")
    if set(schema.get("validity_states", [])) != {
        "VALID_NONEMPTY", "VALID_EMPTY", "AMBIGUOUS", "INVALID"
    }:
        raise SBundleError("S validity 状态集合不匹配")


def _write_records(path: Path, records: list[Mapping[str, Any]]) -> dict[str, Any]:
    with path.open("xb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as compressed:
            for record in records:
                line = json.dumps(
                    record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                ) + "\n"
                compressed.write(line.encode("utf-8"))
        raw_handle.flush()
        os.fsync(raw_handle.fileno())
    return {
        "filename": path.name,
        "record_count": len(records),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def analyze_canonical_to_s(canonical_manifest: Path, output_dir: Path) -> Path:
    """只读分析 Canonical Raw，写入不可覆盖的 S bundle。"""

    canonical_manifest = Path(canonical_manifest).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"拒绝覆盖已有输出目录: {output_dir}")
    schema = load_s_layer_schema()
    repository_root = Path(__file__).resolve().parents[1]
    registry_path = (
        repository_root / "docs" / "v1_4_1" / "contracts"
        / "sync_semantics_registry_v0_2.json"
    )
    registry = load_sync_registry(repository_root)
    bundle = load_canonical_bundle(canonical_manifest)
    inventory = build_semantic_inventory(bundle)
    records = [analyze_sync_semantics(inventory, sync) for sync in inventory["syncs"]]
    records.sort(
        key=lambda record: (
            record["host_start_ns"] is None,
            record["host_start_ns"] if record["host_start_ns"] is not None else 0,
            record["sync_id"],
        )
    )
    expected_fields = set(schema["sync_record_fields"])
    for record in records:
        if set(record) != expected_fields:
            missing = sorted(expected_fields - set(record))
            extra = sorted(set(record) - expected_fields)
            raise SBundleError(f"S 记录字段不匹配: missing={missing}, extra={extra}")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}_", dir=output_dir.parent))
    try:
        record_file = _write_records(staging / schema["sync_records_filename"], records)
        counts = Counter(record["validity"] for record in records)
        manifest = {
            "schema_version": schema["schema_version"],
            "measurement_contract_version": schema["measurement_contract_version"],
            "input_schema_version": schema["input_schema_version"],
            "analyzer_version": __version__,
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "data_role": bundle["manifest"]["data_role"],
            "source": {
                "canonical_manifest_name": canonical_manifest.name,
                "canonical_manifest_sha256": _sha256(canonical_manifest),
                "source_sqlite_sha256": bundle["manifest"]["source"]["sqlite"]["sha256"],
                "sync_registry": {
                    "version": registry["registry_version"],
                    "sha256": _sha256(registry_path),
                },
            },
            "input_validity": {
                "status": inventory["input_status"],
                "reasons": inventory["input_reasons"],
            },
            "files": {"sync_records": record_file},
            "summary": {
                "physical_sync_count": len(records),
                "valid_nonempty_count": counts["VALID_NONEMPTY"],
                "valid_empty_count": counts["VALID_EMPTY"],
                "ambiguous_count": counts["AMBIGUOUS"],
                "invalid_count": counts["INVALID"],
            },
            "research_eligibility": {
                "formal_evidence": False,
                "q0_status": "NOT_RUN",
                "scope": "S_LAYER_ONLY",
            },
        }
        manifest_path = staging / schema["manifest_filename"]
        manifest_path.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        staging.rename(output_dir)
        return output_dir / schema["manifest_filename"]
    except Exception:
        if staging.exists():
            shutil.rmtree(staging)
        raise
