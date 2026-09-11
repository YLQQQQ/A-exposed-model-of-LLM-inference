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
_INVOCATION_FIELDS = (
    "experiment_id",
    "wmpc_id",
    "run_id",
    "run_role",
    "pass_id",
    "request_id",
    "repeat_id",
)


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


def _identity_key(identity: Mapping[str, Any]) -> tuple[Any, ...]:
    return tuple(identity.get(field) for field in _INVOCATION_FIELDS)


def _phase_ownership(
    start_ns: int,
    end_ns: int,
    global_tid: int | None,
    nvtx_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """用同线程结构化半开区间恢复 invocation 与 phase ownership。"""

    candidates: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    for record in nvtx_records:
        identity = record.get("structured_identity")
        if not isinstance(identity, Mapping) or identity.get("kind") not in {"request", "phase"}:
            continue
        if global_tid is None or record.get("global_tid") != global_tid:
            continue
        range_end = record.get("end_ns")
        if range_end is None:
            continue
        if record.get("start_ns") <= start_ns and end_ns <= range_end:
            candidates.append((record, identity))

    if not candidates:
        return {
            "status": "INVALID",
            "identity": None,
            "phase": None,
            "range_record_ids": [],
            "reasons": ["INVOCATION_BOUNDARY_INVALID"],
        }

    invocation_keys = {_identity_key(identity) for _, identity in candidates}
    if len(invocation_keys) != 1:
        return {
            "status": "AMBIGUOUS",
            "identity": None,
            "phase": None,
            "range_record_ids": sorted(str(record["record_id"]) for record, _ in candidates),
            "reasons": ["INVOCATION_OWNERSHIP_AMBIGUOUS"],
        }

    specific = [item for item in candidates if item[1].get("phase") != "full_request"]
    selectable = specific or candidates
    minimum_span = min(int(record["end_ns"]) - int(record["start_ns"]) for record, _ in selectable)
    innermost = [
        item
        for item in selectable
        if int(item[0]["end_ns"]) - int(item[0]["start_ns"]) == minimum_span
    ]
    phases = {identity.get("phase") for _, identity in innermost}
    if len(phases) != 1:
        return {
            "status": "AMBIGUOUS",
            "identity": None,
            "phase": None,
            "range_record_ids": sorted(str(record["record_id"]) for record, _ in candidates),
            "reasons": ["PHASE_OWNERSHIP_AMBIGUOUS"],
        }

    selected_identity = dict(innermost[0][1])
    return {
        "status": "VALID",
        "identity": selected_identity,
        "phase": selected_identity["phase"],
        "range_record_ids": sorted(str(record["record_id"]) for record, _ in candidates),
        "reasons": [],
    }


def _manifest_input_status(manifest: Mapping[str, Any]) -> tuple[str, list[str]]:
    observation = manifest.get("observation_validity", {})
    observation_status = str(observation.get("status", "invalid")).lower()
    if observation_status == "invalid":
        return "INVALID", ["TRACE_DROPPED_RECORDS"]
    identity = manifest.get("identity", {})
    if str(identity.get("status", "AMBIGUOUS")).upper() != "VALID":
        return "AMBIGUOUS", ["INVOCATION_OWNERSHIP_AMBIGUOUS"]
    if observation_status != "valid":
        return "AMBIGUOUS", ["INVOCATION_OWNERSHIP_AMBIGUOUS"]
    return "VALID", []


def _normalize_activity(
    activity: Mapping[str, Any],
    cuda_api_records: list[Mapping[str, Any]],
    nvtx_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    result = dict(activity)
    correlation_id = activity.get("correlation_id")
    enqueues = [api for api in cuda_api_records if api.get("correlation_id") == correlation_id]
    if correlation_id is None or len(enqueues) != 1:
        result.update(
            enqueue_record_id=None,
            enqueue_start_ns=None,
            enqueue_end_ns=None,
            enqueue_global_tid=None,
            request_id=None,
            repeat_id=None,
            origin_phase=None,
            invocation_identity=None,
            ownership_status="INVALID",
            ownership_reasons=["MISSING_ACTIVITY_CORRELATION"],
        )
        return result

    enqueue = enqueues[0]
    ownership = _phase_ownership(
        int(enqueue["start_ns"]),
        int(enqueue["end_ns"]),
        enqueue.get("global_tid"),
        nvtx_records,
    )
    identity = ownership["identity"]
    result.update(
        enqueue_record_id=enqueue["record_id"],
        enqueue_start_ns=enqueue["start_ns"],
        enqueue_end_ns=enqueue["end_ns"],
        enqueue_global_tid=enqueue.get("global_tid"),
        request_id=identity.get("request_id") if identity else None,
        repeat_id=identity.get("repeat_id") if identity else None,
        origin_phase=ownership["phase"],
        invocation_identity=identity,
        ownership_status=ownership["status"],
        ownership_reasons=ownership["reasons"],
        ownership_range_record_ids=ownership["range_record_ids"],
    )
    return result


def _normalize_sync(
    sync: Mapping[str, Any],
    nvtx_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    result = dict(sync)
    classification = classify_cuda_api(str(sync.get("runtime_api_name", "")))
    host_start = sync.get("runtime_start_ns")
    host_end = sync.get("runtime_end_ns")
    if host_start is None or host_end is None:
        ownership = {
            "status": "INVALID",
            "identity": None,
            "phase": None,
            "range_record_ids": [],
            "reasons": ["INVOCATION_BOUNDARY_INVALID"],
        }
    else:
        ownership = _phase_ownership(
            int(host_start),
            int(host_end),
            sync.get("runtime_global_tid"),
            nvtx_records,
        )
    identity = ownership["identity"]
    result.update(
        host_start_ns=host_start,
        host_end_ns=host_end,
        request_id=identity.get("request_id") if identity else None,
        repeat_id=identity.get("repeat_id") if identity else None,
        sync_owner_phase=ownership["phase"],
        invocation_identity=identity,
        ownership_status=ownership["status"],
        ownership_reasons=ownership["reasons"],
        ownership_range_record_ids=ownership["range_record_ids"],
        **classification,
    )
    return result


def build_semantic_inventory(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """把 Canonical Raw 事实标准化为 S 层待建图对象，不恢复依赖。"""

    records = bundle["records"]
    manifest = bundle["manifest"]
    input_status, input_reasons = _manifest_input_status(manifest)
    nvtx = list(records["nvtx"])
    cuda_api = list(records["cuda_api"])
    return {
        "input_status": input_status,
        "input_reasons": input_reasons,
        "execution_context": dict(manifest.get("execution_context", {})),
        "activities": [
            _normalize_activity(activity, cuda_api, nvtx)
            for activity in records["device_activity"]
        ],
        "syncs": [_normalize_sync(sync, nvtx) for sync in records["cuda_sync"]],
        "dependency_events": [
            _normalize_sync(event, nvtx)
            for event in records.get("cuda_sync", [])
            if classify_cuda_api(str(event.get("runtime_api_name", "")))["role"]
            == "DEPENDENCY_EDGE"
        ],
    }


def ownership_supported(
    activity: Mapping[str, Any],
    sync: Mapping[str, Any],
) -> dict[str, Any]:
    """判断 activity 是否属于 sync 的同一次 batched invocation。"""

    if activity.get("ownership_status") != "VALID" or sync.get("ownership_status") != "VALID":
        return {
            "supported": False,
            "cross_phase_dependency": False,
            "reason": "INVOCATION_OWNERSHIP_AMBIGUOUS",
        }
    activity_identity = activity.get("invocation_identity")
    sync_identity = sync.get("invocation_identity")
    if isinstance(activity_identity, Mapping) and isinstance(sync_identity, Mapping):
        same_invocation = _identity_key(activity_identity) == _identity_key(sync_identity)
    else:
        same_invocation = (
            activity.get("request_id"),
            activity.get("repeat_id"),
        ) == (
            sync.get("request_id"),
            sync.get("repeat_id"),
        )
    if not same_invocation:
        return {
            "supported": False,
            "cross_phase_dependency": False,
            "reason": "INVOCATION_BLEED",
        }
    return {
        "supported": True,
        "cross_phase_dependency": activity.get("origin_phase") != sync.get("sync_owner_phase"),
        "reason": None,
    }


def submission_evidence(
    activity: Mapping[str, Any],
    sync: Mapping[str, Any],
) -> dict[str, Any]:
    """只接受冻结合同中的两种提交证据。"""

    gpu_start = activity.get("start_ns")
    enqueue_end = activity.get("enqueue_end_ns")
    sync_start = sync.get("host_start_ns")
    if gpu_start is not None and sync_start is not None and gpu_start < sync_start:
        return {"status": "PROVEN", "proof": "GPU_STARTED_BEFORE_SYNC", "reason": None}
    if enqueue_end is not None and sync_start is not None and enqueue_end <= sync_start:
        return {"status": "PROVEN", "proof": "ENQUEUE_COMPLETED_BEFORE_SYNC", "reason": None}
    return {"status": "AMBIGUOUS", "proof": None, "reason": "SUBMISSION_ORDER_AMBIGUOUS"}
