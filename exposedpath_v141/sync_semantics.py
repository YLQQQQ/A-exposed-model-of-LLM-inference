"""ExposedPath S 层：Canonical Raw 加载与同步语义分类。"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from collections import defaultdict
from collections.abc import Mapping
from functools import lru_cache
from pathlib import Path
from typing import Any

from .canonical_raw import load_canonical_raw_schema


class SyncSemanticsError(ValueError):
    """S 层输入或语义证据不满足冻结合同。"""


_REGISTRY_PATH = Path("docs") / "v1_4_1" / "contracts" / "sync_semantics_registry_v0_2.json"
_SHA256_PATTERN = re.compile(r"^[0-9A-F]{64}$")
_ABI_SUFFIX = re.compile(r"_v[0-9]+$")
_STRUCTURED_NVTX_PREFIX = "EXPOSEDPATH_JSON_V1:"
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


def _trusted_activity_marker_identity(
    record: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    """返回可作为 activity ownership 证据的完整、未篡改 marker identity。"""

    return _trusted_structured_identity(record, _TRUSTED_ACTIVITY_MARKER_KINDS)


_TRUSTED_ACTIVITY_MARKER_KINDS = frozenset({"marker"})
_TRUSTED_SYNC_MARKER_KINDS = frozenset({"sync"})


def _trusted_structured_identity(
    record: Mapping[str, Any], kinds: frozenset[str]
) -> Mapping[str, Any] | None:
    """重新解析 structured payload；不可信、不完整或 kind 不符即返回 None。"""

    text = record.get("text")
    cached = record.get("structured_identity")
    if not isinstance(text, str) or not text.startswith(_STRUCTURED_NVTX_PREFIX):
        return None
    try:
        payload = json.loads(text[len(_STRUCTURED_NVTX_PREFIX) :])
    except json.JSONDecodeError:
        return None
    if (
        not isinstance(payload, Mapping)
        or not isinstance(cached, Mapping)
        or dict(payload) != dict(cached)
        or payload.get("kind") not in kinds
    ):
        return None
    required = (*_INVOCATION_FIELDS, "phase", "callsite_id")
    if any(
        not isinstance(payload.get(field), str) or not payload[field]
        for field in required
    ):
        return None
    return payload


def _record_interval(record: Mapping[str, Any]) -> tuple[int, int] | None:
    start = record.get("start_ns")
    end = record.get("end_ns")
    if (
        isinstance(start, int)
        and not isinstance(start, bool)
        and isinstance(end, int)
        and not isinstance(end, bool)
    ):
        return (start, end)
    return None


def _invalid_ownership(reason: str, range_record_ids: list[str]) -> dict[str, Any]:
    return {
        "status": "INVALID",
        "identity": None,
        "phase": None,
        "range_record_ids": sorted(set(range_record_ids)),
        "reasons": [reason],
    }


def _ambiguous_ownership(reason: str, range_record_ids: list[str]) -> dict[str, Any]:
    return {
        "status": "AMBIGUOUS",
        "identity": None,
        "phase": None,
        "range_record_ids": sorted(set(range_record_ids)),
        "reasons": [reason],
    }


def _matching_structured_ranges(
    nvtx_records: list[Mapping[str, Any]],
    identity: Mapping[str, Any],
    kind: str,
    phase: Any = None,
) -> list[Mapping[str, Any]]:
    """按 7-field identity（与可选 phase）查找匹配的 request/phase range。"""

    key = _identity_key(identity)
    matches: list[Mapping[str, Any]] = []
    for record in nvtx_records:
        candidate = record.get("structured_identity")
        if not isinstance(candidate, Mapping) or candidate.get("kind") != kind:
            continue
        if _identity_key(candidate) != key:
            continue
        if phase is not None and candidate.get("phase") != phase:
            continue
        if _record_interval(record) is None:
            continue
        matches.append(record)
    return matches


def _matching_request_ranges(
    nvtx_records: list[Mapping[str, Any]],
    identity: Mapping[str, Any],
) -> list[Mapping[str, Any]]:
    """按 identity 查找唯一 matching `full_request` range（kind request/phase）。"""

    key = _identity_key(identity)
    matches: list[Mapping[str, Any]] = []
    for record in nvtx_records:
        candidate = record.get("structured_identity")
        if (
            not isinstance(candidate, Mapping)
            or candidate.get("kind") not in {"request", "phase"}
            or candidate.get("phase") != "full_request"
        ):
            continue
        if _identity_key(candidate) != key:
            continue
        if _record_interval(record) is None:
            continue
        matches.append(record)
    return matches


def _marker_invocation_ownership(
    interval: tuple[int, int],
    identity: Mapping[str, Any],
    *,
    activity_interval: tuple[int, int] | None,
    nvtx_records: list[Mapping[str, Any]],
    range_record_ids: list[str],
    external_reason: str = "EXTERNAL_OWNERSHIP_IN_SCOPE",
) -> dict[str, Any]:
    """统一 marker authority：marker 只在其 matching request/phase 内授权 ownership。

    条件（Gate 6 Unified Marker Ownership amendment §2）：
    same-thread API containment 已由调用方保证；此处要求 identity 对应唯一 matching
    ``request`` range，并按 cross-thread temporal containment 判定。request 之前完全
    不相交的 launch marker 只能给出 ``EXTERNAL_OWNERSHIP_IN_SCOPE``；partial overlap、
    整体位于 request 之后、zero/multiple matching、phase 冲突一律 fail closed。
    """

    start_ns, end_ns = interval
    requests = _matching_request_ranges(nvtx_records, identity)
    if not requests:
        return _invalid_ownership("INVOCATION_BOUNDARY_INVALID", range_record_ids)
    if len(requests) > 1:
        return _ambiguous_ownership("INVOCATION_OWNERSHIP_AMBIGUOUS", range_record_ids)
    request_interval = _record_interval(requests[0])
    if request_interval is None:  # pragma: no cover - guarded by matcher
        return _invalid_ownership("INVOCATION_BOUNDARY_INVALID", range_record_ids)
    request_start, request_end = request_interval
    if end_ns <= request_start:
        # marker/API 完全位于 matching request 之前：只有 device activity 延伸进入
        # 该 request 时才是确定的外部 ownership。
        if activity_interval is not None:
            activity_start, activity_end = activity_interval
            if activity_start < request_end and request_start < activity_end:
                return _invalid_ownership(external_reason, range_record_ids)
        return _invalid_ownership("INVOCATION_BOUNDARY_INVALID", range_record_ids)
    if start_ns < request_start or request_end < end_ns:
        # partial overlap 或整体位于 request 之后：本 amendment 不分类为 external。
        return _invalid_ownership("INVOCATION_BOUNDARY_INVALID", range_record_ids)
    phase = identity.get("phase")
    phases = _matching_structured_ranges(nvtx_records, identity, "phase", phase)
    if not phases:
        return _invalid_ownership("INVOCATION_BOUNDARY_INVALID", range_record_ids)
    if len(phases) > 1:
        return _ambiguous_ownership("PHASE_OWNERSHIP_AMBIGUOUS", range_record_ids)
    phase_interval = _record_interval(phases[0])
    if phase_interval is None or not (
        phase_interval[0] <= start_ns and end_ns <= phase_interval[1]
    ):
        return _invalid_ownership("INVOCATION_BOUNDARY_INVALID", range_record_ids)
    return {
        "status": "VALID",
        "identity": dict(identity),
        "phase": phase,
        "range_record_ids": sorted(set(range_record_ids)),
        "reasons": [],
    }


def _trusted_marker_candidates(
    start_ns: int,
    end_ns: int,
    global_tid: Any,
    nvtx_records: list[Mapping[str, Any]],
    kinds: frozenset[str],
) -> list[tuple[str, Mapping[str, Any]]]:
    """同线程、完整覆盖 API interval 的可信 structured marker。"""

    found: list[tuple[str, Mapping[str, Any]]] = []
    for record in nvtx_records:
        if global_tid is None or record.get("global_tid") != global_tid:
            continue
        interval = _record_interval(record)
        if interval is None or interval[0] > start_ns or end_ns > interval[1]:
            continue
        payload = _trusted_structured_identity(record, kinds)
        if payload is not None:
            found.append((str(record.get("record_id")), payload))
    return found


def _activity_ownership(
    start_ns: int,
    end_ns: int,
    global_tid: int | None,
    nvtx_records: list[Mapping[str, Any]],
    activity_interval: tuple[int, int] | None = None,
) -> dict[str, Any]:
    """恢复 enqueue API 的 invocation/phase；marker 仅提供 activity ownership。"""

    candidates: list[tuple[Mapping[str, Any], Mapping[str, Any]]] = []
    invalid_marker_ids: list[str] = []
    for record in nvtx_records:
        if global_tid is None or record.get("global_tid") != global_tid:
            continue
        range_start = record.get("start_ns")
        range_end = record.get("end_ns")
        cached = record.get("structured_identity")
        kind = cached.get("kind") if isinstance(cached, Mapping) else None
        text = record.get("text")
        marker_claim = kind == "marker"
        if isinstance(text, str) and text.startswith(_STRUCTURED_NVTX_PREFIX):
            try:
                text_payload = json.loads(text[len(_STRUCTURED_NVTX_PREFIX) :])
            except json.JSONDecodeError:
                text_payload = None
            marker_claim = marker_claim or (
                isinstance(text_payload, Mapping) and text_payload.get("kind") == "marker"
            )

        valid_start = isinstance(range_start, int) and not isinstance(range_start, bool)
        valid_end = isinstance(range_end, int) and not isinstance(range_end, bool)
        fully_covers = (
            valid_start
            and valid_end
            and range_start <= start_ns
            and end_ns <= range_end
        )
        if kind in {"request", "phase"}:
            if fully_covers:
                candidates.append((record, cached))
            continue
        if not marker_claim or not valid_start:
            continue

        record_id = str(record.get("record_id"))
        if not valid_end:
            if range_start < end_ns:
                invalid_marker_ids.append(record_id)
            continue
        if not fully_covers:
            overlaps_api = range_start < end_ns and start_ns < range_end
            if overlaps_api:
                invalid_marker_ids.append(record_id)
            continue

        identity = _trusted_activity_marker_identity(record)
        if identity is None:
            invalid_marker_ids.append(record_id)
        else:
            candidates.append((record, identity))

    range_record_ids = sorted(
        {str(record.get("record_id")) for record, _ in candidates} | set(invalid_marker_ids)
    )
    if invalid_marker_ids:
        return {
            "status": "INVALID",
            "identity": None,
            "phase": None,
            "range_record_ids": range_record_ids,
            "reasons": ["INVOCATION_BOUNDARY_INVALID"],
        }
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
            "range_record_ids": range_record_ids,
            "reasons": ["INVOCATION_OWNERSHIP_AMBIGUOUS"],
        }

    specific = [item for item in candidates if item[1].get("phase") != "full_request"]
    selectable = specific or candidates
    phases = {identity.get("phase") for _, identity in selectable}
    if len(phases) != 1:
        return {
            "status": "AMBIGUOUS",
            "identity": None,
            "phase": None,
            "range_record_ids": range_record_ids,
            "reasons": ["PHASE_OWNERSHIP_AMBIGUOUS"],
        }

    if any(
        identity.get("kind") in {"request", "phase"} for _, identity in candidates
    ):
        # 原有同线程 request/phase ownership 路径保持不变。
        selected_identity = dict(selectable[0][1])
        return {
            "status": "VALID",
            "identity": selected_identity,
            "phase": selected_identity["phase"],
            "range_record_ids": range_record_ids,
            "reasons": [],
        }

    # 只有 trusted marker 时，authority 由 matching request/phase 的 cross-thread
    # temporal containment 决定（Gate 6 Unified Marker Ownership amendment）。
    marker_record_ids = [str(record.get("record_id")) for record, _ in candidates]
    resolved = [
        _marker_invocation_ownership(
            (start_ns, end_ns),
            identity,
            activity_interval=activity_interval,
            nvtx_records=nvtx_records,
            range_record_ids=marker_record_ids,
        )
        for _, identity in candidates
    ]
    statuses = {item["status"] for item in resolved}
    resolved_phases = {item["phase"] for item in resolved}
    if statuses == {"VALID"} and len(resolved_phases) == 1:
        return {
            "status": "VALID",
            "identity": resolved[0]["identity"],
            "phase": resolved[0]["phase"],
            "range_record_ids": range_record_ids,
            "reasons": [],
        }
    if len(resolved) == 1:
        return resolved[0]
    return _ambiguous_ownership("INVOCATION_OWNERSHIP_AMBIGUOUS", range_record_ids)


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
    cuda_apis_by_correlation: Mapping[Any, list[Mapping[str, Any]]],
    nvtx_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    result = dict(activity)
    correlation_id = activity.get("correlation_id")
    enqueues = list(cuda_apis_by_correlation.get(correlation_id, []))
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
    activity_start = activity.get("start_ns")
    activity_end = activity.get("end_ns")
    activity_interval = (
        (activity_start, activity_end)
        if isinstance(activity_start, int)
        and not isinstance(activity_start, bool)
        and isinstance(activity_end, int)
        and not isinstance(activity_end, bool)
        else None
    )
    ownership = _activity_ownership(
        int(enqueue["start_ns"]),
        int(enqueue["end_ns"]),
        enqueue.get("global_tid"),
        nvtx_records,
        activity_interval=activity_interval,
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
    marker_candidates: list[Mapping[str, Any]] = []
    if host_start is not None and host_end is not None:
        for record in nvtx_records:
            marker = record.get("structured_identity")
            if not isinstance(marker, Mapping) or marker.get("kind") != "sync":
                continue
            if record.get("global_tid") != sync.get("runtime_global_tid"):
                continue
            marker_end = record.get("end_ns")
            contains = (
                marker_end is not None
                and record.get("start_ns") <= host_start
                and host_end <= marker_end
            )
            exact_mark = marker_end is None and record.get("start_ns") == host_start
            if contains or exact_mark:
                marker_candidates.append(marker)
    marker_identity = marker_candidates[0] if len(marker_candidates) == 1 else None
    marker_status = "VALID" if marker_identity is not None else (
        "AMBIGUOUS" if marker_candidates else "INVALID"
    )
    if ownership["status"] != "VALID" and host_start is not None and host_end is not None:
        # Gate 6 Unified Marker Ownership amendment §4：worker thread 上的 trusted
        # `kind=sync` marker 可以跨 host thread 通过 matching request/phase 的
        # temporal containment 传播 request/repeat/owner phase。
        trusted_sync_markers = _trusted_marker_candidates(
            int(host_start),
            int(host_end),
            sync.get("runtime_global_tid"),
            nvtx_records,
            _TRUSTED_SYNC_MARKER_KINDS,
        )
        if len(trusted_sync_markers) > 1:
            ownership = _ambiguous_ownership(
                "INVOCATION_OWNERSHIP_AMBIGUOUS",
                [record_id for record_id, _ in trusted_sync_markers],
            )
        elif len(trusted_sync_markers) == 1:
            record_id, trusted_marker = trusted_sync_markers[0]
            ownership = _marker_invocation_ownership(
                (int(host_start), int(host_end)),
                trusted_marker,
                activity_interval=None,
                nvtx_records=nvtx_records,
                range_record_ids=[record_id],
                external_reason="INVOCATION_BOUNDARY_INVALID",
            )
        identity = ownership["identity"]
    if marker_identity is not None and identity is not None:
        if _identity_key(marker_identity) != _identity_key(identity):
            marker_status = "AMBIGUOUS"
            marker_identity = None
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
        sync_identity_status=marker_status,
        sync_origin=marker_identity.get("sync_origin") if marker_identity else None,
        callsite_id=marker_identity.get("callsite_id") if marker_identity else None,
        sync_ordinal=marker_identity.get("sync_ordinal") if marker_identity else None,
        token_index=marker_identity.get("token_index") if marker_identity else None,
        **classification,
    )
    return result


def _normalize_event_record(
    event: Mapping[str, Any],
    cuda_apis_by_correlation: Mapping[Any, list[Mapping[str, Any]]],
    nvtx_records: list[Mapping[str, Any]],
) -> dict[str, Any]:
    result = dict(event)
    correlation_id = event.get("correlation_id")
    candidates = [
        api
        for api in cuda_apis_by_correlation.get(correlation_id, [])
        if api.get("correlation_id") == correlation_id
        and classify_cuda_api(str(api.get("api_name", "")))["sync_kind"] == "EVENT_RECORD"
    ]
    if correlation_id is None or len(candidates) != 1:
        result.update(
            host_start_ns=None,
            host_end_ns=None,
            request_id=None,
            repeat_id=None,
            invocation_identity=None,
            ownership_status="INVALID",
            ownership_reasons=["MISSING_EVENT_RECORD"],
        )
        return result
    api = candidates[0]
    ownership = _phase_ownership(
        int(api["start_ns"]), int(api["end_ns"]), api.get("global_tid"), nvtx_records
    )
    if ownership["status"] != "VALID":
        # `cudaEventRecord` 的 ownership 与 activity 遵循同一 trusted marker authority：
        # marker 必须完整覆盖 API、同线程，并在 matching request/phase 内。
        trusted_event_markers = _trusted_marker_candidates(
            int(api["start_ns"]),
            int(api["end_ns"]),
            api.get("global_tid"),
            nvtx_records,
            _TRUSTED_ACTIVITY_MARKER_KINDS,
        )
        if len(trusted_event_markers) > 1:
            ownership = _ambiguous_ownership(
                "INVOCATION_OWNERSHIP_AMBIGUOUS",
                [record_id for record_id, _ in trusted_event_markers],
            )
        elif len(trusted_event_markers) == 1:
            record_id, trusted_marker = trusted_event_markers[0]
            ownership = _marker_invocation_ownership(
                (int(api["start_ns"]), int(api["end_ns"])),
                trusted_marker,
                activity_interval=None,
                nvtx_records=nvtx_records,
                range_record_ids=[record_id],
                external_reason="INVOCATION_BOUNDARY_INVALID",
            )
    identity = ownership["identity"]
    result.update(
        host_start_ns=api["start_ns"],
        host_end_ns=api["end_ns"],
        request_id=identity.get("request_id") if identity else None,
        repeat_id=identity.get("repeat_id") if identity else None,
        invocation_identity=identity,
        ownership_status=ownership["status"],
        ownership_reasons=ownership["reasons"],
        ownership_range_record_ids=ownership["range_record_ids"],
    )
    return result


def build_semantic_inventory(bundle: Mapping[str, Any]) -> dict[str, Any]:
    """把 Canonical Raw 事实标准化为 S 层待建图对象，不恢复依赖。"""

    records = bundle["records"]
    manifest = bundle["manifest"]
    input_status, input_reasons = _manifest_input_status(manifest)
    nvtx = list(records["nvtx"])
    cuda_api = list(records["cuda_api"])
    cuda_apis_by_correlation: dict[Any, list[Mapping[str, Any]]] = defaultdict(list)
    for api in cuda_api:
        cuda_apis_by_correlation[api.get("correlation_id")].append(api)
    normalized_syncs = [_normalize_sync(sync, nvtx) for sync in records["cuda_sync"]]
    normalized_activities = (
        [
            _normalize_activity(activity, cuda_apis_by_correlation, nvtx)
            for activity in records["device_activity"]
        ]
        if input_status == "VALID"
        else []
    )
    return {
        "input_status": input_status,
        "input_reasons": input_reasons,
        "execution_context": dict(manifest.get("execution_context", {})),
        "activity_count_observed": len(records["device_activity"]),
        "activities": normalized_activities,
        "syncs": [sync for sync in normalized_syncs if sync["role"] != "DEPENDENCY_EDGE"],
        "dependency_events": [
            sync for sync in normalized_syncs if sync["role"] == "DEPENDENCY_EDGE"
        ],
        "event_records": [
            _normalize_event_record(event, cuda_apis_by_correlation, nvtx)
            for event in records.get("cuda_event", [])
        ],
        "contexts": list(records.get("context", [])),
        "streams": list(records.get("stream", [])),
    }


def ownership_supported(
    activity: Mapping[str, Any],
    sync: Mapping[str, Any],
) -> dict[str, Any]:
    """判断 activity 是否属于 sync 的同一次 batched invocation。"""

    if activity.get("ownership_status") != "VALID":
        activity_reasons = list(activity.get("ownership_reasons", []))
        reason = activity_reasons[0] if activity_reasons else (
            "INVOCATION_OWNERSHIP_AMBIGUOUS"
            if activity.get("ownership_status") == "AMBIGUOUS"
            else "INVOCATION_BOUNDARY_INVALID"
        )
        return {
            "supported": False,
            "cross_phase_dependency": False,
            "reason": reason,
        }
    if sync.get("ownership_status") != "VALID":
        sync_reasons = list(sync.get("ownership_reasons", []))
        reason = sync_reasons[0] if sync_reasons else (
            "INVOCATION_OWNERSHIP_AMBIGUOUS"
            if sync.get("ownership_status") == "AMBIGUOUS"
            else "INVOCATION_BOUNDARY_INVALID"
        )
        return {
            "supported": False,
            "cross_phase_dependency": False,
            "reason": reason,
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
    enqueue_start = activity.get("enqueue_start_ns")
    enqueue_end = activity.get("enqueue_end_ns")
    sync_start = sync.get("host_start_ns")
    if gpu_start is not None and sync_start is not None and gpu_start < sync_start:
        return {"status": "PROVEN", "proof": "GPU_STARTED_BEFORE_SYNC", "reason": None}
    if enqueue_end is not None and sync_start is not None and enqueue_end <= sync_start:
        return {"status": "PROVEN", "proof": "ENQUEUE_COMPLETED_BEFORE_SYNC", "reason": None}
    if enqueue_start is not None and sync_start is not None and enqueue_start >= sync_start:
        return {"status": "NOT_PRECEDING", "proof": None, "reason": None}
    return {"status": "AMBIGUOUS", "proof": None, "reason": "SUBMISSION_ORDER_AMBIGUOUS"}


def _unresolved_candidate_reasons(
    candidate: Mapping[str, Any],
    boundary: Mapping[str, Any],
    proof: Mapping[str, Any],
) -> list[str]:
    """保留候选映射缺失等强 invalid，不让较弱的顺序歧义覆盖。"""

    reasons: list[str] = []
    relation = ownership_supported(candidate, boundary)
    if not relation["supported"]:
        reasons.extend(candidate.get("ownership_reasons", []))
        reasons.append(str(relation["reason"]))
    if proof.get("status") != "PROVEN" and proof.get("reason") is not None:
        reasons.append(str(proof["reason"]))
    return reasons


def _add_edge(
    predecessors: dict[str, set[str]],
    edges: list[dict[str, Any]],
    source: str,
    target: str,
    edge_type: str,
) -> None:
    if source == target or source in predecessors[target]:
        return
    predecessors[target].add(source)
    edges.append({"from": source, "to": target, "edge_type": edge_type})


def _stream_flags(inventory: Mapping[str, Any]) -> dict[tuple[Any, Any], Any]:
    return {
        (stream.get("context_id"), stream.get("stream_id")): stream.get("flag")
        for stream in inventory.get("streams", [])
    }


def _null_streams(inventory: Mapping[str, Any]) -> dict[Any, Any]:
    return {
        context.get("context_id"): context.get("null_stream_id")
        for context in inventory.get("contexts", [])
    }


def _same_invocation(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_identity = left.get("invocation_identity")
    right_identity = right.get("invocation_identity")
    if isinstance(left_identity, Mapping) and isinstance(right_identity, Mapping):
        return _identity_key(left_identity) == _identity_key(right_identity)
    return (left.get("request_id"), left.get("repeat_id")) == (
        right.get("request_id"), right.get("repeat_id")
    )


def _build_same_stream_edges(
    activities: list[Mapping[str, Any]],
    predecessors: dict[str, set[str]],
    edges: list[dict[str, Any]],
) -> list[str]:
    issues: list[str] = []
    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = defaultdict(list)
    for activity in activities:
        identity = activity.get("invocation_identity")
        invocation = _identity_key(identity) if isinstance(identity, Mapping) else (
            activity.get("request_id"), activity.get("repeat_id")
        )
        groups[(activity.get("context_id"), activity.get("stream_id"), *invocation)].append(activity)
    for group in groups.values():
        ordered = sorted(group, key=lambda item: (item["start_ns"], item["end_ns"], item["record_id"]))
        for previous, current in zip(ordered, ordered[1:]):
            if previous["end_ns"] <= current["start_ns"]:
                _add_edge(
                    predecessors,
                    edges,
                    str(previous["record_id"]),
                    str(current["record_id"]),
                    "SAME_STREAM_ORDER",
                )
            else:
                issues.append("DEPENDENCY_CLOSURE_AMBIGUOUS")
    return issues


def _capture_event_prefixes(
    inventory: Mapping[str, Any],
    predecessors: dict[str, set[str]],
    edges: list[dict[str, Any]],
) -> tuple[dict[Any, str], dict[Any, Mapping[str, Any]], list[str]]:
    event_nodes: dict[Any, str] = {}
    event_records: dict[Any, Mapping[str, Any]] = {}
    issues: list[str] = []
    activities_by_stream: dict[tuple[Any, Any], list[Mapping[str, Any]]] = defaultdict(list)
    for activity in inventory["activities"]:
        activities_by_stream[
            (activity.get("context_id"), activity.get("stream_id"))
        ].append(activity)
    records_by_sync_id: dict[Any, list[Mapping[str, Any]]] = defaultdict(list)
    for event in inventory.get("event_records", []):
        records_by_sync_id[event.get("event_sync_id")].append(event)
    for event_sync_id, candidates in records_by_sync_id.items():
        if event_sync_id is None or len(candidates) != 1:
            issues.append("MISSING_EVENT_RECORD")
            continue
        event = candidates[0]
        if event.get("ownership_status") != "VALID":
            issues.extend(event.get("ownership_reasons", ["MISSING_EVENT_RECORD"]))
            continue
        node_id = f"event::{event['record_id']}"
        event_nodes[event_sync_id] = node_id
        event_records[event_sync_id] = event
        for activity in activities_by_stream[
            (event.get("context_id"), event.get("stream_id"))
        ]:
            proof = submission_evidence(activity, event)
            if proof["status"] == "PROVEN":
                _add_edge(
                    predecessors, edges, str(activity["record_id"]), node_id,
                    "EVENT_RECORD_CAPTURE",
                )
            elif (
                activity.get("enqueue_start_ns") is not None
                and event.get("host_end_ns") is not None
                and activity["enqueue_start_ns"] >= event["host_end_ns"]
            ):
                continue
            else:
                issues.extend(_unresolved_candidate_reasons(activity, event, proof))
                issues.append("DEPENDENCY_CLOSURE_AMBIGUOUS")
    return event_nodes, event_records, issues


def _event_mapping_matches(
    reference: Mapping[str, Any], event: Mapping[str, Any]
) -> bool:
    """要求 eventSyncId 所指记录与同步或 wait 的 event/scope 完全一致。"""

    return all(
        reference.get(field) is not None
        and event.get(field) is not None
        and reference.get(field) == event.get(field)
        for field in ("event_id", "context_id", "device_id")
    )


def _add_stream_wait_edges(
    inventory: Mapping[str, Any],
    event_nodes: Mapping[Any, str],
    event_records: Mapping[Any, Mapping[str, Any]],
    predecessors: dict[str, set[str]],
    edges: list[dict[str, Any]],
) -> tuple[list[str], list[str]]:
    wait_nodes: list[str] = []
    issues: list[str] = []
    activities_by_stream: dict[tuple[Any, Any], list[Mapping[str, Any]]] = defaultdict(list)
    for activity in inventory["activities"]:
        activities_by_stream[
            (activity.get("context_id"), activity.get("stream_id"))
        ].append(activity)
    for wait in inventory.get("dependency_events", []):
        if wait.get("sync_kind") != "STREAM_WAIT_EVENT":
            continue
        event_node = event_nodes.get(wait.get("event_sync_id"))
        event = event_records.get(wait.get("event_sync_id"))
        if event_node is None or event is None or not _event_mapping_matches(wait, event):
            issues.append("MISSING_EVENT_RECORD")
            continue
        wait_node = f"wait::{wait['record_id']}"
        wait_nodes.append(wait_node)
        _add_edge(
            predecessors, edges, event_node, wait_node, "STREAM_WAIT_EVENT"
        )
        for activity in activities_by_stream[
            (wait.get("context_id"), wait.get("stream_id"))
        ]:
            enqueue_start = activity.get("enqueue_start_ns")
            if (
                enqueue_start is not None
                and wait.get("host_end_ns") is not None
                and enqueue_start >= wait["host_end_ns"]
            ):
                _add_edge(
                    predecessors, edges, wait_node, str(activity["record_id"]),
                    "SAME_STREAM_ORDER",
                )
            elif submission_evidence(activity, wait)["status"] != "PROVEN":
                issues.append("DEPENDENCY_CLOSURE_AMBIGUOUS")
    return wait_nodes, issues


def _add_default_stream_edges(
    inventory: Mapping[str, Any],
    sync: Mapping[str, Any],
    predecessors: dict[str, set[str]],
    edges: list[dict[str, Any]],
) -> list[str]:
    null_streams = _null_streams(inventory)
    activities = [
        activity
        for activity in inventory["activities"]
        if submission_evidence(activity, sync)["status"] != "NOT_PRECEDING"
    ]
    default_activities = [
        activity
        for activity in activities
        if null_streams.get(activity.get("context_id")) == activity.get("stream_id")
    ]
    if not default_activities:
        return []
    mode = inventory.get("execution_context", {}).get("default_stream_mode")
    if mode not in {"LEGACY", "PER_THREAD", "NO_DEFAULT_STREAM_OBSERVED"}:
        return ["DEFAULT_STREAM_MODE_UNKNOWN"]
    if mode == "NO_DEFAULT_STREAM_OBSERVED":
        return ["DEFAULT_STREAM_MODE_UNKNOWN"]
    if mode != "LEGACY":
        return []
    flags = _stream_flags(inventory)
    issues: list[str] = []
    for default in default_activities:
        for other in activities:
            if (
                other.get("context_id") != default.get("context_id")
                or other.get("stream_id") == default.get("stream_id")
                or flags.get((other.get("context_id"), other.get("stream_id"))) == 1
            ):
                continue
            ordering_values = (
                other.get("enqueue_start_ns"), other.get("enqueue_end_ns"),
                default.get("enqueue_start_ns"), default.get("enqueue_end_ns"),
            )
            if any(value is None for value in ordering_values):
                for candidate in (default, other):
                    proof = submission_evidence(candidate, sync)
                    issues.extend(
                        _unresolved_candidate_reasons(candidate, sync, proof)
                    )
                issues.append("DEPENDENCY_CLOSURE_AMBIGUOUS")
                continue
            if other["enqueue_end_ns"] <= default["enqueue_start_ns"]:
                _add_edge(
                    predecessors, edges, str(other["record_id"]), str(default["record_id"]),
                    "SUPPORTED_DEFAULT_STREAM_ORDER",
                )
            elif default["enqueue_end_ns"] <= other["enqueue_start_ns"]:
                _add_edge(
                    predecessors, edges, str(default["record_id"]), str(other["record_id"]),
                    "SUPPORTED_DEFAULT_STREAM_ORDER",
                )
            else:
                issues.append("DEPENDENCY_CLOSURE_AMBIGUOUS")
    return list(dict.fromkeys(issues))


def _scope_matches(activity: Mapping[str, Any], sync: Mapping[str, Any]) -> bool:
    kind = sync.get("sync_kind")
    if kind == "STREAM":
        return (
            activity.get("context_id") == sync.get("context_id")
            and activity.get("stream_id") == sync.get("stream_id")
        )
    if kind == "CONTEXT":
        return activity.get("context_id") == sync.get("context_id")
    if kind == "DEVICE":
        return activity.get("device_id") == sync.get("device_id")
    return False


def _transitive_predecessors(
    seeds: set[str], predecessors: Mapping[str, set[str]]
) -> set[str]:
    closure = set(seeds)
    pending = list(seeds)
    while pending:
        node = pending.pop()
        for predecessor in predecessors.get(node, set()):
            if predecessor not in closure:
                closure.add(predecessor)
                pending.append(predecessor)
    return closure


def recover_wait_set(
    inventory: Mapping[str, Any],
    sync: Mapping[str, Any],
) -> dict[str, Any]:
    """依 completion scope 恢复单个同步的 W(s)，不使用时间重叠建边。"""

    activities = list(inventory["activities"])
    by_id = {str(activity["record_id"]): activity for activity in activities}
    reasons: list[str] = list(inventory.get("input_reasons", []))
    graph_inventory = dict(inventory)
    if sync.get("sync_kind") == "EVENT":
        relevant_event_ids = {sync.get("event_sync_id")}
        relevant_waits: list[Mapping[str, Any]] = []
    elif sync.get("sync_kind") == "STREAM":
        relevant_waits = [
            wait
            for wait in inventory.get("dependency_events", [])
            if wait.get("context_id") == sync.get("context_id")
            and wait.get("stream_id") == sync.get("stream_id")
            and wait.get("host_end_ns") is not None
            and sync.get("host_start_ns") is not None
            and wait["host_end_ns"] <= sync["host_start_ns"]
        ]
        relevant_event_ids = {wait.get("event_sync_id") for wait in relevant_waits}
    else:
        relevant_waits = []
        relevant_event_ids = set()
    graph_inventory["dependency_events"] = relevant_waits
    graph_inventory["event_records"] = [
        event
        for event in inventory.get("event_records", [])
        if event.get("event_sync_id") in relevant_event_ids
    ]
    mode = inventory.get("execution_context", {}).get("default_stream_mode")
    cache_key = (
        sync.get("sync_kind"), sync.get("device_id"), sync.get("context_id"),
        sync.get("stream_id"), sync.get("event_sync_id"), mode,
        sync.get("host_start_ns") if mode != "PER_THREAD" else None,
        tuple(str(wait.get("record_id")) for wait in relevant_waits),
        tuple(str(event.get("record_id")) for event in graph_inventory["event_records"]),
    )
    cache = inventory.setdefault("_semantic_graph_cache", {}) if isinstance(inventory, dict) else {}
    cached = cache.get(cache_key)
    if cached is None:
        predecessors: dict[str, set[str]] = defaultdict(set)
        edges: list[dict[str, Any]] = []
        graph_reasons: list[str] = []
        relevant_streams = {
            (event.get("context_id"), event.get("stream_id"))
            for event in graph_inventory["event_records"]
        }
        if sync.get("sync_kind") == "STREAM":
            relevant_streams.add((sync.get("context_id"), sync.get("stream_id")))
        if sync.get("sync_kind") == "DEVICE":
            graph_activities = [
                activity for activity in activities
                if activity.get("device_id") == sync.get("device_id")
            ]
        elif sync.get("sync_kind") == "CONTEXT" or (
            mode != "PER_THREAD" and sync.get("context_id") is not None
        ):
            graph_activities = [
                activity for activity in activities
                if activity.get("context_id") == sync.get("context_id")
            ]
        else:
            graph_activities = [
                activity for activity in activities
                if (activity.get("context_id"), activity.get("stream_id")) in relevant_streams
            ]
        graph_inventory["activities"] = graph_activities
        graph_reasons.extend(
            _build_same_stream_edges(graph_activities, predecessors, edges)
        )
        event_nodes, event_records, event_issues = _capture_event_prefixes(
            graph_inventory, predecessors, edges
        )
        graph_reasons.extend(event_issues)
        wait_nodes, wait_issues = _add_stream_wait_edges(
            graph_inventory, event_nodes, event_records, predecessors, edges
        )
        graph_reasons.extend(wait_issues)
        graph_reasons.extend(
            _add_default_stream_edges(graph_inventory, sync, predecessors, edges)
        )
        cached = {
            "predecessors": predecessors,
            "edges": edges,
            "event_nodes": event_nodes,
            "event_records": event_records,
            "wait_nodes": wait_nodes,
            "reasons": list(dict.fromkeys(graph_reasons)),
            "semantic_owners": [
                *graph_inventory["event_records"],
                *graph_inventory["dependency_events"],
            ],
        }
        cache[cache_key] = cached
    predecessors = cached["predecessors"]
    edges = cached["edges"]
    event_nodes = cached["event_nodes"]
    event_records = cached["event_records"]
    wait_nodes = cached["wait_nodes"]
    reasons.extend(cached["reasons"])
    for semantic_owner in cached["semantic_owners"]:
        if semantic_owner.get("role") == "DEPENDENCY_EDGE":
            # Gate 6 Unified Marker Ownership amendment §5：`cudaStreamWaitEvent`
            # 等 dependency edge 不携带独立的 invocation ownership，因此不需要
            # marker；边的归属由它等待的 event node 承担，而 event node 同样在
            # semantic_owners 中并被单独校验（缺失或不匹配时 fail closed）。
            continue
        relation = ownership_supported(semantic_owner, sync)
        if not relation["supported"]:
            reasons.extend(semantic_owner.get("ownership_reasons", []))
            reasons.append(str(relation["reason"]))

    seeds: set[str] = set()
    submission: dict[str, dict[str, Any]] = {}
    event_record_id = None
    if sync.get("sync_kind") == "EVENT":
        event_node = event_nodes.get(sync.get("event_sync_id"))
        event = event_records.get(sync.get("event_sync_id"))
        if event_node is None or event is None or not _event_mapping_matches(sync, event):
            reasons.append("MISSING_EVENT_RECORD")
        else:
            seeds.add(event_node)
            event_record_id = event_node.removeprefix("event::")
    else:
        if sync.get("sync_kind") == "STREAM":
            seeds.update(wait_nodes)
        for activity in activities:
            if not _scope_matches(activity, sync):
                continue
            proof = submission_evidence(activity, sync)
            submission[str(activity["record_id"])] = proof
            if proof["status"] == "NOT_PRECEDING":
                continue
            relation = ownership_supported(activity, sync)
            if not relation["supported"]:
                reasons.extend(activity.get("ownership_reasons", []))
                reasons.append(relation["reason"])
                if proof["status"] != "PROVEN":
                    reasons.append(str(proof["reason"]))
                continue
            if proof["status"] != "PROVEN":
                reasons.append(str(proof["reason"]))
                continue
            seeds.add(str(activity["record_id"]))

    closure = _transitive_predecessors(seeds, predecessors)
    wait_ids: list[str] = []
    cross_phase = False
    for activity_id in closure:
        activity = by_id.get(activity_id)
        if activity is None:
            continue
        relation = ownership_supported(activity, sync)
        if not relation["supported"]:
            reasons.append(str(relation["reason"]))
            continue
        proof = submission_evidence(activity, sync)
        submission[activity_id] = proof
        if proof["status"] != "PROVEN":
            reasons.append(str(proof["reason"]))
            continue
        wait_ids.append(activity_id)
        cross_phase = cross_phase or relation["cross_phase_dependency"]

    wait_ids.sort(key=lambda item: (by_id[item]["start_ns"], by_id[item]["end_ns"], item))
    ordered_reasons = list(dict.fromkeys(reason for reason in reasons if reason and reason != "None"))
    return {
        "sync_id": sync.get("record_id"),
        "dependency_closure_status": "AMBIGUOUS" if ordered_reasons else "COMPLETE",
        "wait_set_activity_ids": wait_ids,
        "submission_evidence": submission,
        "dependency_edges": edges,
        "event_record_id": event_record_id,
        "reasons": ordered_reasons,
        "activity_origin_phases": {
            activity_id: by_id[activity_id].get("origin_phase") for activity_id in wait_ids
        },
        "cross_phase_dependency": cross_phase,
    }


@lru_cache(maxsize=1)
def _reason_rules() -> dict[str, tuple[int, str]]:
    from .contract import load_contract_bundle

    priorities = load_contract_bundle()["contract"]["s_layer"]["reason_priority"]
    return {
        reason: (int(group["rank"]), str(group["default_validity"]))
        for group in priorities
        for reason in group["reasons"]
    }


def _ordered_reasons(reasons: list[str]) -> tuple[str | None, list[str], str | None]:
    rules = _reason_rules()
    unique = list(dict.fromkeys(reason for reason in reasons if reason in rules))
    unique.sort(key=lambda reason: (rules[reason][0], reason))
    if not unique:
        return None, [], None
    primary = unique[0]
    validity = (
        "INVALID"
        if any(rules[reason][1] == "INVALID" for reason in unique)
        else rules[primary][1]
    )
    return primary, unique[1:], validity


def _semantic_frontier(
    wait_ids: list[str], edges: list[Mapping[str, Any]]
) -> list[str]:
    wait_set = set(wait_ids)
    outgoing: dict[str, set[str]] = defaultdict(set)
    for edge in edges:
        outgoing[str(edge["from"])].add(str(edge["to"]))

    frontier: list[str] = []
    for activity_id in wait_ids:
        seen = {activity_id}
        pending = list(outgoing.get(activity_id, set()))
        has_wait_successor = False
        while pending and not has_wait_successor:
            node = pending.pop()
            if node in seen:
                continue
            seen.add(node)
            if node in wait_set:
                has_wait_successor = True
                break
            pending.extend(outgoing.get(node, set()))
        if not has_wait_successor:
            frontier.append(activity_id)
    return frontier


def _invalid_terminal(status: str) -> dict[str, Any]:
    return {
        "status": "AMBIGUOUS" if status == "AMBIGUOUS" else "INVALID",
        "kind": "NONE",
        "activity_id": None,
        "end_ns": None,
        "clock_domain_id": None,
    }


def analyze_sync_semantics(
    inventory: Mapping[str, Any],
    sync: Mapping[str, Any],
) -> dict[str, Any]:
    """完成单个 physical sync 的 W(s)、terminal 与 validity 判定。"""

    if inventory.get("input_status") == "VALID":
        recovery = recover_wait_set(inventory, sync)
    else:
        recovery = {
            "dependency_closure_status": "AMBIGUOUS",
            "wait_set_activity_ids": [],
            "submission_evidence": {},
            "dependency_edges": [],
            "event_record_id": None,
            "reasons": list(inventory.get("input_reasons", [])),
            "activity_origin_phases": {},
            "cross_phase_dependency": False,
        }
    reasons = list(recovery["reasons"])
    role = sync.get("role")
    if role == "UNSUPPORTED":
        reasons.append("UNSUPPORTED_SYNC_API")
    elif role == "UNCLASSIFIED":
        reasons.append("UNCLASSIFIED_CUDA_API")
    elif role != "HOST_BLOCKING_SYNC":
        reasons.append("UNCLASSIFIED_CUDA_API")

    reasons.extend(sync.get("ownership_reasons", []))
    if sync.get("ownership_status") == "AMBIGUOUS":
        reasons.append("INVOCATION_OWNERSHIP_AMBIGUOUS")
    elif sync.get("ownership_status") != "VALID":
        reasons.append("INVOCATION_BOUNDARY_INVALID")
    if any(sync.get(field) is None for field in ("sync_origin", "callsite_id", "sync_ordinal")):
        reasons.append("INVOCATION_BOUNDARY_INVALID")

    kind = sync.get("sync_kind")
    if kind == "STREAM":
        if sync.get("context_id") is None:
            reasons.append("MISSING_CONTEXT_ID")
        if sync.get("stream_id") is None:
            reasons.append("MISSING_STREAM_ID")
    elif kind == "DEVICE" and sync.get("device_id") is None:
        reasons.append("MISSING_CONTEXT_ID")
    elif kind == "CONTEXT" and sync.get("context_id") is None:
        reasons.append("MISSING_CONTEXT_ID")
    elif kind == "EVENT":
        if sync.get("event_id") is None:
            reasons.append("MISSING_EVENT_ID")
        if sync.get("event_sync_id") is None:
            reasons.append("MISSING_EVENT_RECORD")

    activity_by_id = {
        str(activity["record_id"]): activity for activity in inventory["activities"]
    }
    wait_activities = [
        activity_by_id[activity_id]
        for activity_id in recovery["wait_set_activity_ids"]
        if activity_id in activity_by_id
    ]
    graph_mapping_unsupported = any(
        activity.get("graph_id") is not None and activity.get("graph_node_id") is None
        for activity in wait_activities
    )
    if graph_mapping_unsupported:
        reasons.append("GRAPH_MAPPING_UNSUPPORTED")
        recovery["wait_set_activity_ids"] = []
        recovery["activity_origin_phases"] = {}
        recovery["cross_phase_dependency"] = False

    frontier = _semantic_frontier(
        recovery["wait_set_activity_ids"], recovery["dependency_edges"]
    )
    terminal: dict[str, Any]
    if not recovery["wait_set_activity_ids"]:
        terminal = {
            "status": "NOT_APPLICABLE",
            "kind": "NONE",
            "activity_id": None,
            "end_ns": None,
            "clock_domain_id": None,
        }
    elif reasons:
        primary, _, reason_validity = _ordered_reasons(reasons)
        terminal = _invalid_terminal(reason_validity or "INVALID")
    elif not frontier:
        reasons.append("TERMINAL_NOT_FOUND")
        terminal = _invalid_terminal("INVALID")
    else:
        frontier_activities = [activity_by_id[activity_id] for activity_id in frontier]
        clock_domains = {activity.get("clock_domain_id") for activity in frontier_activities}
        if None in clock_domains or len(clock_domains) != 1:
            reasons.append("CLOCK_DOMAIN_UNRESOLVED")
            terminal = _invalid_terminal("INVALID")
        elif len(frontier_activities) == 1:
            selected = frontier_activities[0]
            terminal = {
                "status": "VALID",
                "kind": "ACTIVITY",
                "activity_id": selected["record_id"],
                "end_ns": selected["end_ns"],
                "clock_domain_id": selected["clock_domain_id"],
            }
        else:
            latest_end = max(int(activity["end_ns"]) for activity in frontier_activities)
            latest = [
                activity for activity in frontier_activities
                if int(activity["end_ns"]) == latest_end
            ]
            if len(latest) != 1:
                reasons.append("TERMINAL_TIE")
                terminal = _invalid_terminal("AMBIGUOUS")
            else:
                selected = latest[0]
                terminal = {
                    "status": "VALID",
                    "kind": "ACTIVITY",
                    "activity_id": selected["record_id"],
                    "end_ns": selected["end_ns"],
                    "clock_domain_id": selected["clock_domain_id"],
                }
        if (
            terminal["status"] == "VALID"
            and sync.get("host_end_ns") is not None
            and terminal["end_ns"] > sync["host_end_ns"]
        ):
            reasons.append("TERMINAL_AFTER_SYNC_END")
            terminal = _invalid_terminal("INVALID")

    primary_reason, secondary_reasons, reason_validity = _ordered_reasons(reasons)
    if reason_validity is not None:
        validity = reason_validity
        if terminal["status"] in {"VALID", "NOT_APPLICABLE"}:
            terminal = _invalid_terminal(validity)
    elif recovery["wait_set_activity_ids"]:
        validity = "VALID_NONEMPTY"
    else:
        validity = "VALID_EMPTY"

    terminal_activity = activity_by_id.get(str(terminal.get("activity_id")))
    result = {
        "sync_id": sync.get("record_id"),
        "registry_rule_id": sync.get("registry_rule_id"),
        "sync_universe_class": sync.get("universe_class"),
        "sync_kind": sync.get("sync_kind"),
        "request_id": sync.get("request_id"),
        "repeat_id": sync.get("repeat_id"),
        "sync_owner_phase": sync.get("sync_owner_phase"),
        "sync_origin": sync.get("sync_origin"),
        "callsite_id": sync.get("callsite_id"),
        "sync_ordinal": sync.get("sync_ordinal"),
        "host_start_ns": sync.get("host_start_ns"),
        "host_end_ns": sync.get("host_end_ns"),
        "device_id": sync.get("device_id"),
        "context_id": sync.get("context_id"),
        "stream_id": sync.get("stream_id"),
        "event_id": sync.get("event_id"),
        "completion_scope": sync.get("completion_scope"),
        "submission_evidence": recovery["submission_evidence"],
        "dependency_closure_status": recovery["dependency_closure_status"],
        "dependency_edges": recovery["dependency_edges"],
        "event_record_id": recovery["event_record_id"],
        "wait_set_status": validity,
        "wait_set_activity_ids": recovery["wait_set_activity_ids"],
        "semantic_frontier_activity_ids": frontier,
        "terminal": terminal,
        "validity": validity,
        "primary_reason": primary_reason,
        "secondary_reasons": secondary_reasons,
        "activity_origin_phases": recovery["activity_origin_phases"],
        "terminal_origin_phase": (
            terminal_activity.get("origin_phase") if terminal_activity else None
        ),
        "cross_phase_dependency": recovery["cross_phase_dependency"],
        "invocation_bleed": "INVOCATION_BLEED" in reasons,
    }
    return result


def analyze_semantic_inventory(inventory: Mapping[str, Any]) -> list[dict[str, Any]]:
    """按稳定 Host 时间和 sync identity 分析全部 physical sync。"""

    syncs = sorted(
        inventory["syncs"],
        key=lambda sync: (
            sync.get("host_start_ns") if sync.get("host_start_ns") is not None else -1,
            str(sync.get("record_id")),
        ),
    )
    return [analyze_sync_semantics(inventory, sync) for sync in syncs]
