"""Navigation-only D and Exposure Signature projections from validated A/B bundles."""

from __future__ import annotations

import gzip
import hashlib
import json
import os
import shutil
import tempfile
from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, ValidationError

from .ab_bundle import ABBundleError, load_ab_bundle


class DerivedBundleError(ValueError):
    """A derived bundle is malformed, unverifiable, or exceeds its A/B-only scope."""


_SCHEMA_PATH = Path("docs") / "v1_4_1" / "contracts" / "derived_schema_v0_2.json"
_RECORD_FILES = {
    "d_window_records": "d_window_records.jsonl.gz",
    "exposure_signature_records": "exposure_signature_records.jsonl.gz",
}
_QUALIFICATION = {
    "formal_evidence": False,
    "q0_status": "NOT_RUN",
    "scope": "DERIVED_FROM_A_B_ONLY",
}
_A_VECTOR_FIELDS = (
    "A_host_path_ns",
    "A_cuda_api_ns",
    "A_device_wait_ns",
    "A_sync_residual_ns",
    "A_unattributed_ns",
    "A_cuda_api_submit_ns",
    "A_cuda_api_non_submit_ns",
    "A_device_wait_kernel_only_ns",
    "A_device_wait_memop_only_ns",
    "A_device_wait_kernel_memop_mixed_ns",
)
_TIMING_FIELDS = (
    "wait_set_hidden_union_ns",
    "wait_set_exposed_union_ns",
    "terminal_pre_sync_ns",
    "terminal_overlap_sync_ns",
    "sync_return_tail_ns",
)
_IDENTITY_FIELDS = (
    "window_id", "experiment_id", "wmpc_id", "run_id", "run_role", "pass_id",
    "request_id", "repeat_id", "phase",
)
_STATUSES = ("B_VALID", "B_NOT_APPLICABLE", "B_AMBIGUOUS", "B_INVALID")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise DerivedBundleError(f"{label} 必须是对象")
    return value


def _schema(root: Path | None = None, *, version="exposedpath-derived/0.2.0") -> dict[str, Any]:
    if version not in ("exposedpath-derived/0.2.0", "exposedpath-derived/0.3.0"):
        raise DerivedBundleError("Derived schema VERSION_UNSUPPORTED")
    root = Path(__file__).resolve().parents[1] if root is None else Path(root)
    try:
        path = _SCHEMA_PATH if version.endswith("/0.2.0") else _SCHEMA_PATH.with_name("derived_schema_v0_3.json")
        schema = json.loads((root / path).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)
    except (OSError, UnicodeError, json.JSONDecodeError, ValidationError) as exc:
        raise DerivedBundleError(f"Derived schema 无法加载: {exc}") from exc
    if schema.get("schema_version") != version:
        raise DerivedBundleError("Derived schema 版本不匹配")
    return schema


def _validate_schema(schema: Mapping[str, Any], definition: str, record: Mapping[str, Any], label: str) -> None:
    try:
        # Validate via the schema root so nested local references retain their scope.
        validator_schema = {"$defs": schema["$defs"], "$ref": f"#/$defs/{definition}"}
        Draft202012Validator(validator_schema).validate(dict(record))
    except (KeyError, ValidationError) as exc:
        message = exc.message if isinstance(exc, ValidationError) else str(exc)
        raise DerivedBundleError(f"{label} 不符合冻结 Derived schema: {message}") from exc


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


def _identity(record: Mapping[str, Any]) -> dict[str, Any]:
    return {field: record[field] for field in _IDENTITY_FIELDS}


def _median(values: Sequence[int]) -> float | int | None:
    if not values:
        return None
    ordered = sorted(values)
    midpoint = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[midpoint]
    return (ordered[midpoint - 1] + ordered[midpoint]) / 2


def _nearest_rank_p90(values: Sequence[int]) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[(9 * len(ordered) + 9) // 10 - 1]


def _distribution(values: Sequence[int | None]) -> list[dict[str, int | None]]:
    counts = Counter(values)
    return [
        {"value_ns": value, "count": counts[value]}
        for value in sorted(counts, key=lambda item: (item is not None, item if item is not None else -1))
    ]


def _timing_summary(values: Sequence[int | None]) -> dict[str, float | int | None]:
    numeric = [value for value in values if value is not None]
    return {"median": _median(numeric), "p90": _nearest_rank_p90(numeric)}


def _group_sort_key(key: tuple[Any, Any, Any, Any]) -> tuple[tuple[int, str], ...]:
    return tuple((value is not None, "" if value is None else str(value)) for value in key)


def _build_signature(a_record: Mapping[str, Any], b_records: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    vector = {field: a_record[field] for field in _A_VECTOR_FIELDS}
    denominator = a_record["T_window_ns"]
    ratios = {
        field.removesuffix("_ns") + "_ratio": (None if denominator == 0 else value / denominator)
        for field, value in vector.items()
    }
    matching = [
        record for record in b_records
        if record["request_id"] == a_record["request_id"]
        and record["repeat_id"] == a_record["repeat_id"]
        and record["sync_owner_phase"] == a_record["phase"]
    ]
    groups: dict[tuple[Any, Any, Any, Any], list[Mapping[str, Any]]] = defaultdict(list)
    for record in matching:
        groups[(record["sync_owner_phase"], record["sync_kind"], record["sync_origin"], record["callsite_id"])].append(record)
    summarized_groups: list[dict[str, Any]] = []
    for key in sorted(groups, key=_group_sort_key):
        records = sorted(groups[key], key=lambda record: str(record["sync_id"]))
        valid = [record for record in records if record["validity"] == "B_VALID"]
        # Completion-boundary terminals intentionally have no activity timing;
        # distributions contain only observed numeric B_VALID timing samples.
        values_by_field = {
            field: [record[field] for record in valid if record[field] is not None]
            for field in _TIMING_FIELDS
        }
        terminal_counts = Counter(record["terminal"]["kind"] for record in valid)
        summarized_groups.append({
            "phase": key[0],
            "sync_kind": key[1],
            "sync_origin": key[2],
            "callsite_id": key[3],
            "status_counts": {status: sum(record["validity"] == status for record in records) for status in _STATUSES},
            "valid_timing_statistics_ns": {field: _timing_summary(values_by_field[field]) for field in _TIMING_FIELDS},
            "valid_timing_distributions_ns": {field: _distribution(values_by_field[field]) for field in _TIMING_FIELDS},
            "terminal_kind_counts": {
                "ACTIVITY": terminal_counts["ACTIVITY"],
                "COMPLETION_BOUNDARY": terminal_counts["COMPLETION_BOUNDARY"],
            },
        })
    return {**_identity(a_record), "A_vector_ns": vector, "A_window_ratios": ratios, "b_groups": summarized_groups}


def _build_d_record(a_record: Mapping[str, Any]) -> dict[str, Any]:
    device_wait = a_record["A_device_wait_ns"]
    host_and_api = a_record["A_host_path_ns"] + a_record["A_cuda_api_ns"]
    denominator = device_wait + host_and_api
    margin = device_wait - host_and_api
    return {**_identity(a_record), "D_margin_ns": margin, "D_score": None if denominator == 0 else margin / denominator}


def _validate_signature_semantics(record: Mapping[str, Any]) -> None:
    """Check schema-inexpressible count/sample consistency without changing A/B facts."""

    for group in record["b_groups"]:
        counts = _mapping(group["status_counts"], "Signature status_counts")
        valid_count = counts["B_VALID"]
        terminals = _mapping(group["terminal_kind_counts"], "Signature terminal_kind_counts")
        if terminals["ACTIVITY"] + terminals["COMPLETION_BOUNDARY"] != valid_count:
            raise DerivedBundleError("Signature terminal kind count 与 B_VALID 不一致")
        distributions = _mapping(group["valid_timing_distributions_ns"], "Signature distributions")
        statistics = _mapping(group["valid_timing_statistics_ns"], "Signature statistics")
        for field in _TIMING_FIELDS:
            samples = distributions[field]
            expected_count = valid_count if field in {
                "wait_set_hidden_union_ns", "wait_set_exposed_union_ns", "sync_return_tail_ns",
            } else terminals["ACTIVITY"]
            if sum(item["count"] for item in samples) != expected_count:
                raise DerivedBundleError("Signature timing distribution sample count 与有效数值样本不一致")
            values: list[int | None] = []
            for item in samples:
                values.extend([item["value_ns"]] * item["count"])
            summary = _timing_summary(values)
            if statistics[field] != summary:
                raise DerivedBundleError("Signature timing summary 与 distribution 不一致")


def _validate_record_semantics(definition: str, record: Mapping[str, Any]) -> None:
    if definition == "exposure_signature_record":
        _validate_signature_semantics(record)
    elif definition != "d_window_record":
        raise DerivedBundleError(f"未知 Derived record 定义: {definition}")


def _load_records(
    manifest_path: Path, entry: Mapping[str, Any], expected_filename: str,
    schema: Mapping[str, Any], definition: str,
) -> tuple[dict[str, Any], ...]:
    if entry.get("filename") != expected_filename:
        raise DerivedBundleError(f"{expected_filename} 文件名不匹配")
    for field in ("record_count", "size_bytes"):
        value = entry.get(field)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise DerivedBundleError(f"{expected_filename} {field} 非法")
    expected_hash = entry.get("sha256")
    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        raise DerivedBundleError(f"{expected_filename} SHA-256 非法")
    record_path = (manifest_path.parent / expected_filename).resolve()
    if record_path.parent != manifest_path.parent.resolve() or not record_path.is_file():
        raise DerivedBundleError(f"{expected_filename} 不存在或路径越界")
    if record_path.stat().st_size != entry["size_bytes"] or _sha256(record_path) != expected_hash.upper():
        raise DerivedBundleError(f"{expected_filename} SHA-256 或文件大小不匹配")
    records: list[dict[str, Any]] = []
    try:
        with gzip.open(record_path, "rt", encoding="utf-8", newline="") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.endswith("\n") or not line.strip():
                    raise DerivedBundleError(f"{expected_filename} 第 {line_number} 行不是规范 JSONL")
                record = dict(_mapping(json.loads(line), f"{expected_filename} 第 {line_number} 行"))
                _validate_schema(schema, definition, record, f"{expected_filename} 第 {line_number} 行")
                _validate_record_semantics(definition, record)
                records.append(record)
    except DerivedBundleError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DerivedBundleError(f"{expected_filename} 无法读取") from exc
    if len(records) != entry["record_count"]:
        raise DerivedBundleError(f"{expected_filename} 记录数不匹配")
    return tuple(records)


def _validate_current_qualification(manifest: Mapping[str, Any]) -> None:
    eligibility = _mapping(manifest.get("research_eligibility"), "Derived research_eligibility")
    if any(eligibility.get(field) != value for field, value in _QUALIFICATION.items()):
        raise DerivedBundleError("Derived current qualification policy rejects unsupported qualification claims")


def _validate_external_lineage(manifest: Mapping[str, Any], ab_manifest: Path | None) -> None:
    if ab_manifest is None:
        return
    ab_manifest = Path(ab_manifest).resolve()
    if not ab_manifest.is_file():
        raise DerivedBundleError("A/B manifest 无法读取")
    try:
        bundle = load_ab_bundle(ab_manifest)
    except ABBundleError as exc:
        raise DerivedBundleError(f"A/B manifest 不可验证: {exc}") from exc
    source = _mapping(manifest.get("source"), "Derived source")
    if source.get("ab_manifest_name") != ab_manifest.name or source.get("ab_manifest_sha256") != _sha256(ab_manifest):
        raise DerivedBundleError("Derived A/B manifest lineage 不匹配")
    source_files = _mapping(bundle["manifest"].get("files"), "A/B files")
    if manifest.get("input_schema_version") != bundle["manifest"].get("schema_version"):
        raise DerivedBundleError("Derived A/B input VERSION_MISMATCH")
    if (
        source.get("a_window_records_sha256") != source_files["a_window_records"]["sha256"]
        or source.get("b_sync_records_sha256") != source_files["b_sync_records"]["sha256"]
        or manifest.get("data_role") != bundle["manifest"].get("data_role")
    ):
        raise DerivedBundleError("Derived A/B record lineage 或 data_role 不匹配")


def load_derived_bundle(manifest_path: Path, *, ab_manifest: Path | None = None) -> dict[str, Any]:
    """Strictly load a self-verifying derived bundle; optional A/B path rechecks lineage."""

    manifest_path = Path(manifest_path).resolve()
    if manifest_path.name != "derived_manifest.json" or not manifest_path.is_file():
        raise DerivedBundleError(f"Derived manifest 不存在或名称错误: {manifest_path}")
    try:
        manifest = dict(_mapping(json.loads(manifest_path.read_text(encoding="utf-8")), "Derived manifest"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise DerivedBundleError("Derived manifest 无法读取") from exc
    schema = _schema(version=manifest.get("schema_version"))
    _validate_schema(schema, "manifest", manifest, "Derived manifest")
    _validate_current_qualification(manifest)
    files = _mapping(manifest.get("files"), "Derived files")
    if set(files) != set(_RECORD_FILES):
        raise DerivedBundleError("Derived files 集合不匹配")
    d_records = _load_records(manifest_path, _mapping(files["d_window_records"], "D 文件条目"), _RECORD_FILES["d_window_records"], schema, "d_window_record")
    signatures = _load_records(manifest_path, _mapping(files["exposure_signature_records"], "Signature 文件条目"), _RECORD_FILES["exposure_signature_records"], schema, "exposure_signature_record")
    summary = _mapping(manifest.get("summary"), "Derived summary")
    if summary.get("d_window_count") != len(d_records) or summary.get("exposure_signature_count") != len(signatures):
        raise DerivedBundleError("Derived summary 计数与记录不匹配")
    d_ids = {record["window_id"] for record in d_records}
    signature_ids = {record["window_id"] for record in signatures}
    if len(d_ids) != len(d_records) or len(signature_ids) != len(signatures) or d_ids != signature_ids:
        raise DerivedBundleError("Derived window identity 集合不匹配")
    _validate_external_lineage(manifest, ab_manifest)
    return {"manifest": manifest, "d_window_records": d_records, "exposure_signature_records": signatures}


def derive_exposure(ab_manifest: Path, output_dir: Path) -> Path:
    """Create an atomic, immutable D/Signature bundle from one validated A/B bundle."""

    ab_manifest = Path(ab_manifest).resolve()
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(f"拒绝覆盖已有输出目录: {output_dir}")
    try:
        ab_bundle = load_ab_bundle(ab_manifest)
    except (ABBundleError, OSError, ValueError, json.JSONDecodeError) as exc:
        raise DerivedBundleError(f"A/B 输入不可验证: {exc}") from exc
    input_version = ab_bundle["manifest"]["schema_version"]
    if input_version not in ('exposedpath-ab/0.2.0','exposedpath-ab/0.3.0'):
        raise ValueError('DERIVED_INPUT_VERSION_UNSUPPORTED: ownership profile not qualified')
    schema = _schema(version={"exposedpath-ab/0.2.0":"exposedpath-derived/0.2.0",
                              "exposedpath-ab/0.3.0":"exposedpath-derived/0.3.0"}[input_version])
    a_records = sorted(ab_bundle["a_window_records"], key=lambda record: str(record["window_id"]))
    b_records = ab_bundle["b_sync_records"]
    if input_version == 'exposedpath-ab/0.3.0' and (
        ab_bundle['manifest']['quality']['status'] != 'VALID'
        or any(r['primary_reason'] is not None or r['A_unattributed_ns'] != 0 for r in a_records)
        or any(r['validity'] not in ('B_VALID','B_NOT_APPLICABLE') for r in b_records)
    ):
        raise DerivedBundleError('DERIVED_UPSTREAM_NOT_QUALIFIED')
    d_records = tuple(_build_d_record(record) for record in a_records)
    signatures = tuple(_build_signature(record, b_records) for record in a_records)
    for record in d_records:
        _validate_schema(schema, "d_window_record", record, "D 记录")
    for record in signatures:
        _validate_schema(schema, "exposure_signature_record", record, "Exposure Signature 记录")
        _validate_signature_semantics(record)

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output_dir.name}_", dir=output_dir.parent))
    try:
        files = {
            "d_window_records": _write_records(staging / _RECORD_FILES["d_window_records"], d_records),
            "exposure_signature_records": _write_records(staging / _RECORD_FILES["exposure_signature_records"], signatures),
        }
        ab_files = _mapping(ab_bundle["manifest"].get("files"), "A/B files")
        manifest = {
            "schema_version": schema["schema_version"],
            "measurement_contract_version": schema["measurement_contract_version"],
            "input_schema_version": ab_bundle["manifest"]["schema_version"],
            "analyzer_version": ab_bundle["manifest"]["analyzer_version"],
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "data_role": ab_bundle["manifest"]["data_role"],
            "source": {
                "ab_manifest_name": ab_manifest.name,
                "ab_manifest_sha256": _sha256(ab_manifest),
                "a_window_records_sha256": ab_files["a_window_records"]["sha256"],
                "b_sync_records_sha256": ab_files["b_sync_records"]["sha256"],
            },
            "files": files,
            "summary": {"d_window_count": len(d_records), "exposure_signature_count": len(signatures)},
            "research_eligibility": dict(_QUALIFICATION),
        }
        if input_version == 'exposedpath-ab/0.3.0':
            manifest['validation_role'] = ab_bundle['manifest']['validation_role']
            manifest['measurement_validity'] = ab_bundle['manifest']['measurement_validity']
        _validate_schema(schema, "manifest", manifest, "Derived manifest")
        manifest_path = staging / "derived_manifest.json"
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
    return output_dir / "derived_manifest.json"
