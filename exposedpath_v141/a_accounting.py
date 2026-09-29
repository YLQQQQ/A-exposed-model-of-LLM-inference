"""Gate 5 的保守、互斥 request/phase A 墙钟记账。

本模块只投影 ``ABInputs`` 中已冻结的 Canonical 事实和 S 层结果。特别地，
它绝不由 activity 的时间重叠重建 ``W(s)`` 或依赖关系。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from .ab_inputs import ABInputs, RequestPhaseWindow
from .intervals import atomic_segments
from .a_api_classification import classify_a_api_name
from .time_representation import timestamp, duration, signed_time


_TOP_LEVEL = (
    "A_host_path_ns",
    "A_cuda_api_ns",
    "A_device_wait_ns",
    "A_sync_residual_ns",
    "A_unattributed_ns",
)
_CUDA_SUBCATEGORIES = ("A_cuda_api_submit_ns", "A_cuda_api_non_submit_ns")
_WAIT_SUBCATEGORIES = (
    "A_device_wait_kernel_only_ns",
    "A_device_wait_memop_only_ns",
    "A_device_wait_kernel_memop_mixed_ns",
)
_IDENTITY_FIELDS = (
    "window_id", "experiment_id", "wmpc_id", "run_id", "run_role", "pass_id",
    "request_id", "repeat_id", "phase", "window_start_ns", "window_end_ns",
)
_AUDIT_FIELDS = (
    "top_level_conservation_error_ns", "top_level_overlap_ns", "top_level_uncovered_ns",
    "out_of_window_ns", "cuda_api_subcategory_conservation_error_ns",
    "device_wait_subcategory_conservation_error_ns",
)
_REASON_FIELDS = ("primary_reason", "secondary_reasons")
_RECORD_FIELDS = frozenset((*_IDENTITY_FIELDS, "T_window_ns", *_TOP_LEVEL, *_CUDA_SUBCATEGORIES,
                            *_WAIT_SUBCATEGORIES, *_AUDIT_FIELDS, *_REASON_FIELDS))
_KNOWN_WAIT_KINDS = {"KERNEL", "MEMCPY", "MEMSET"}
_VALID_SYNC = {"VALID_NONEMPTY", "VALID_EMPTY"}
_INVALID_SYNC = {"AMBIGUOUS", "INVALID"}
_WINDOW_OWNER_IDENTITY_FIELDS = (
    "experiment_id", "wmpc_id", "run_id", "run_role", "pass_id", "request_id", "repeat_id",
)
_STRUCTURED_PREFIX = "EXPOSEDPATH_JSON_V1:"


def _integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{label} 必须是非负整数纳秒")
    return duration(value, label)


def _interval(record: Mapping[str, object], start_key: str, end_key: str, label: str) -> tuple[int, int]:
    start = timestamp(record.get(start_key), f"{label}.{start_key}")
    end = timestamp(record.get(end_key), f"{label}.{end_key}")
    if end < start:
        raise ValueError(f"{label} 的半开区间逆序")
    if signed_time():
        duration(end - start, label)
    return start, end


def _signed_interval(
    record: Mapping[str, object], start_key: str, end_key: str, label: str
) -> tuple[int, int]:
    start = record.get(start_key)
    end = record.get(end_key)
    if not isinstance(start, int) or isinstance(start, bool):
        raise ValueError(f"{label}.{start_key} 必须是整数纳秒")
    if not isinstance(end, int) or isinstance(end, bool):
        raise ValueError(f"{label}.{end_key} 必须是整数纳秒")
    if end < start:
        raise ValueError(f"{label} 的半开区间逆序")
    return start, end


def _covers(interval: tuple[int, int], segment: tuple[int, int]) -> bool:
    return interval[0] <= segment[0] and segment[1] <= interval[1]


def _reason_values(record: Mapping[str, object]) -> tuple[str, ...]:
    values: list[str] = []
    primary = record.get("primary_reason")
    if isinstance(primary, str) and primary:
        values.append(primary)
    secondary = record.get("secondary_reasons")
    if isinstance(secondary, list):
        values.extend(value for value in secondary if isinstance(value, str) and value)
    return tuple(dict.fromkeys(values))


def _api_category(api: Mapping[str, object], api_by_correlation: Mapping[object, tuple[Mapping[str, object], ...]], activity_correlations: set[object]) -> str | None:
    """返回冻结 API 子类；不支持或有歧义时返回 ``None``。"""

    name = api.get("api_name")
    if not isinstance(name, str) or not name:
        return None
    category, rule = classify_a_api_name(name)
    if category is None or (rule and rule.startswith('A-') and 'return_value' in api and api['return_value'] != 0):
        return None
    correlation = api.get("correlation_id")
    if category == 'non_submit':
        # An observed device submission contradicts a non-submit rule. Do not
        # reinterpret it as submit, or use missing activity as the rule itself.
        return None if correlation is not None and correlation in activity_correlations else 'non_submit'
    if rule and rule.startswith('EDGE-'):
        return 'submit'
    if correlation is None:
        return None
    matching_apis = api_by_correlation.get(correlation, ())
    if len(matching_apis) == 1 and correlation in activity_correlations:
        return "submit"
    return None


def _trusted_owner_identity(candidate: Mapping[str, object]) -> Mapping[str, object] | None:
    """仅返回与 Canonical 缓存完整一致的结构化 NVTX text identity。"""

    from .gate8_scope import ProjectedScope
    if isinstance(candidate, ProjectedScope):
        return candidate["structured_identity"]
    text = candidate.get("text")
    if not isinstance(text, str) or not text.startswith(_STRUCTURED_PREFIX):
        return None
    try:
        payload = json.loads(text[len(_STRUCTURED_PREFIX) :])
    except json.JSONDecodeError:
        return None
    cached_identity = candidate.get("structured_identity")
    if not isinstance(payload, Mapping) or not isinstance(cached_identity, Mapping):
        return None
    if dict(payload) != dict(cached_identity):
        return None
    return payload


def _api_ownership_reason(
    api: Mapping[str, object],
    api_interval: tuple[int, int],
    window: RequestPhaseWindow,
    nvtx_records: tuple[Mapping[str, object], ...],
) -> str | None:
    """确认 API 属于 window 的 invocation；range 证明 ownership，不定义 phase。"""

    api_thread = api.get("global_tid")
    if not isinstance(api_thread, int) or isinstance(api_thread, bool):
        return "CUDA_API_THREAD_OWNERSHIP_MISSING"

    expected = {field: getattr(window, field) for field in _WINDOW_OWNER_IDENTITY_FIELDS}
    same_thread_structured_seen = False
    matching_owner_seen = False
    incomplete_owner_seen = False
    conflicting_owner_seen = False
    invalid_owner_evidence_seen = False
    for candidate in nvtx_records:
        if candidate.get("global_tid") != api_thread:
            continue
        cached_identity = candidate.get("structured_identity")
        text = candidate.get("text")
        is_structured_claim = (
            isinstance(cached_identity, Mapping)
            and cached_identity.get("kind") in {"request", "phase", "marker"}
        ) or (isinstance(text, str) and text.startswith(_STRUCTURED_PREFIX))
        if not is_structured_claim:
            continue
        same_thread_structured_seen = True
        identity = _trusted_owner_identity(candidate)
        if identity is None or identity.get("kind") not in {"request", "phase", "marker"}:
            invalid_owner_evidence_seen = True
            continue
        try:
            candidate_interval = _interval(candidate, "start_ns", "end_ns", "structured NVTX")
        except ValueError:
            incomplete_owner_seen = True
            continue
        if not _covers(candidate_interval, api_interval):
            continue
        if any(field not in identity or not isinstance(identity.get(field), str) or not identity[field] for field in expected):
            incomplete_owner_seen = True
        elif any(identity.get(field) != value for field, value in expected.items()):
            conflicting_owner_seen = True
        else:
            matching_owner_seen = True

    if conflicting_owner_seen:
        return "CUDA_API_IDENTITY_CONFLICT"
    if incomplete_owner_seen:
        return "CUDA_API_IDENTITY_MISSING"
    if matching_owner_seen:
        return None
    if invalid_owner_evidence_seen:
        return "CUDA_API_OWNERSHIP_EVIDENCE_INVALID"
    if not same_thread_structured_seen:
        return "CUDA_API_EXTERNAL_THREAD"
    return "CUDA_API_WINDOW_OWNERSHIP_MISSING"


def _record_identity(window: RequestPhaseWindow) -> dict[str, object]:
    return {
        "window_id": window.window_id,
        "experiment_id": window.experiment_id,
        "wmpc_id": window.wmpc_id,
        "run_id": window.run_id,
        "run_role": window.run_role,
        "pass_id": window.pass_id,
        "request_id": window.request_id,
        "repeat_id": window.repeat_id,
        "phase": window.phase,
        "window_start_ns": window.start_ns,
        "window_end_ns": window.end_ns,
    }


def _empty_totals() -> dict[str, int]:
    return {field: 0 for field in (*_TOP_LEVEL, *_CUDA_SUBCATEGORIES, *_WAIT_SUBCATEGORIES)}


def _finalize(window: RequestPhaseWindow, totals: Mapping[str, int], reasons: tuple[str, ...]) -> dict[str, object]:
    record: dict[str, object] = _record_identity(window)
    record["T_window_ns"] = window.end_ns - window.start_ns
    record.update(totals)
    record.update(
        {
            "top_level_conservation_error_ns": 0,
            "top_level_overlap_ns": 0,
            "top_level_uncovered_ns": 0,
            "out_of_window_ns": 0,
            "cuda_api_subcategory_conservation_error_ns": 0,
            "device_wait_subcategory_conservation_error_ns": 0,
            "primary_reason": reasons[0] if reasons else None,
            "secondary_reasons": list(reasons[1:]),
        }
    )
    validate_a_record(record)
    return record


def _covering_by_segment(records, segments):
    """Sweep ordered atomic segments; retain input order and half-open coverage.

    Callers include every clipped interval endpoint in their atomic partition.
    Empty/outside intervals cannot cover a positive-length segment.
    """
    events = []
    for i, row in enumerate(records):
        start, end = row[1]
        if start < end:
            events.extend(((start, 1, i), (end, 0, i)))
    events.sort()
    active = set()
    cursor = 0
    for start, end in segments:
        while cursor < len(events) and events[cursor][0] <= start:
            _, added, i = events[cursor]
            if added:
                active.add(i)
            else:
                active.discard(i)
            cursor += 1
        yield [records[i] for i in sorted(active) if records[i][1][1] >= end]


def _window_record(inputs: ABInputs, window: RequestPhaseWindow) -> dict[str, object]:
    window_interval = (window.start_ns, window.end_ns)
    totals = _empty_totals()
    global_reasons = tuple(reason for reason in inputs.global_quality_reasons if isinstance(reason, str) and reason)
    if global_reasons:
        totals["A_unattributed_ns"] = window.end_ns - window.start_ns
        return _finalize(window, totals, global_reasons)

    activities: dict[str, tuple[Mapping[str, object], tuple[int, int]]] = {}
    for activity_id, activity in inputs.canonical.activity_by_id.items():
        activities[activity_id] = (activity, _interval(activity, "start_ns", "end_ns", f"activity {activity_id}"))

    syncs: list[tuple[Mapping[str, object], tuple[int, int], str]] = []
    reasons: list[str] = []
    for sync in inputs.s_records:
        if sync.get("host_start_ns") is None and sync.get("host_end_ns") is None:
            if sync.get("validity") != "INVALID" or sync.get("request_id") is not None:
                raise ValueError(
                    f"sync {sync.get('sync_id')} 缺少时间但不满足 request 外 invalid 条件"
                )
            continue
        interval = _interval(sync, "host_start_ns", "host_end_ns", f"sync {sync.get('sync_id')}")
        validity = sync.get("validity")
        status = validity if isinstance(validity, str) else "UNKNOWN"
        syncs.append((sync, interval, status))

    apis: list[tuple[Mapping[str, object], tuple[int, int]]] = []
    nvtx_records = tuple(
        record for record in (
            inputs.canonical.projected_ownership if inputs.canonical.projected_ownership is not None
            else inputs.canonical.records.get("nvtx", ())
        ) if isinstance(record, Mapping)
    )
    api_by_correlation: dict[object, list[Mapping[str, object]]] = {}
    for api in inputs.canonical.records.get("cuda_api", ()):
        interval = _signed_interval(
            api, "start_ns", "end_ns", f"cuda_api {api.get('record_id')}"
        )
        apis.append((api, interval))
        correlation = api.get("correlation_id")
        if correlation is not None:
            api_by_correlation.setdefault(correlation, []).append(api)
    api_by_correlation_frozen = {key: tuple(value) for key, value in api_by_correlation.items()}
    activity_correlations = {
        activity.get("correlation_id")
        for activity, _ in activities.values()
        if activity.get("correlation_id") is not None
    }

    boundaries = [window.start_ns, window.end_ns]
    def add_window_boundaries(interval: tuple[int, int]) -> None:
        start = max(window.start_ns, interval[0])
        end = min(window.end_ns, interval[1])
        if start < end:
            boundaries.extend((start, end))

    for _, interval, _ in syncs:
        add_window_boundaries(interval)
    for _, interval in apis:
        add_window_boundaries(interval)
    for _, interval in activities.values():
        add_window_boundaries(interval)

    segments = tuple(atomic_segments(window_interval, boundaries))
    for segment, active_syncs, active_apis in zip(
        segments, _covering_by_segment(syncs, segments), _covering_by_segment(apis, segments)
    ):
        duration = segment[1] - segment[0]
        covering_syncs = [(sync, status) for sync, interval, status in active_syncs]
        invalid_syncs = [(sync, status) for sync, status in covering_syncs if status in _INVALID_SYNC or status not in _VALID_SYNC]
        if invalid_syncs:
            totals["A_unattributed_ns"] += duration
            for sync, _ in invalid_syncs:
                reasons.extend(_reason_values(sync) or ("SYNC_VALIDITY_UNRESOLVED",))
            continue

        valid_syncs = [sync for sync, status in covering_syncs if status in _VALID_SYNC]
        if valid_syncs:
            active_waits: list[Mapping[str, object]] = []
            malformed_wait_set = False
            for sync in valid_syncs:
                wait_set = sync.get("wait_set_activity_ids")
                if not isinstance(wait_set, list):
                    malformed_wait_set = True
                    continue
                for activity_id in wait_set:
                    if not isinstance(activity_id, str) or activity_id not in activities:
                        malformed_wait_set = True
                        continue
                    activity, interval = activities[activity_id]
                    if _covers(interval, segment):
                        active_waits.append(activity)
            if malformed_wait_set:
                totals["A_unattributed_ns"] += duration
                reasons.append("WAIT_SET_ACTIVITY_UNRESOLVED")
                continue
            if active_waits:
                kinds = {activity.get("activity_kind") for activity in active_waits}
                if not kinds <= _KNOWN_WAIT_KINDS:
                    totals["A_unattributed_ns"] += duration
                    reasons.append("WAIT_ACTIVITY_KIND_UNSUPPORTED")
                    continue
                totals["A_device_wait_ns"] += duration
                if kinds == {"KERNEL"}:
                    totals["A_device_wait_kernel_only_ns"] += duration
                elif kinds <= {"MEMCPY", "MEMSET"}:
                    totals["A_device_wait_memop_only_ns"] += duration
                else:
                    totals["A_device_wait_kernel_memop_mixed_ns"] += duration
                continue
            totals["A_sync_residual_ns"] += duration
            continue

        covering_apis = [api for api, interval in active_apis]
        if covering_apis:
            ownership_reasons = [
                _api_ownership_reason(api, interval, window, nvtx_records)
                for api, interval in active_apis
            ]
            if any(reason is not None for reason in ownership_reasons):
                totals["A_unattributed_ns"] += duration
                reasons.extend(reason for reason in ownership_reasons if reason is not None)
                continue
            categories = {
                _api_category(api, api_by_correlation_frozen, activity_correlations)
                for api in covering_apis
            }
            if None in categories or len(categories) != 1:
                totals["A_unattributed_ns"] += duration
                reasons.append("CUDA_API_SEMANTICS_UNRESOLVED")
                continue
            category = categories.pop()
            totals["A_cuda_api_ns"] += duration
            if category == "submit":
                totals["A_cuda_api_submit_ns"] += duration
            else:
                totals["A_cuda_api_non_submit_ns"] += duration
            continue

        totals["A_host_path_ns"] += duration

    return _finalize(window, totals, tuple(dict.fromkeys(reasons)))


def calculate_a_windows(inputs: ABInputs) -> tuple[dict[str, object], ...]:
    """为每个唯一恢复的 request/phase window 返回一条守恒 A 记录。"""

    if not isinstance(inputs, ABInputs):
        raise TypeError("inputs 必须是 ABInputs")
    return tuple(_window_record(inputs, window) for window in inputs.windows)


def validate_a_record(record: Mapping[str, object]) -> None:
    """拒绝任一不满足冻结 A schema 的运行时记账记录。"""

    if not isinstance(record, Mapping):
        raise ValueError("A record 必须是对象")
    if set(record) != _RECORD_FIELDS:
        raise ValueError("A record 字段集合不匹配冻结 schema")
    for field in _IDENTITY_FIELDS[:8]:
        if not isinstance(record[field], str) or not record[field]:
            raise ValueError(f"{field} 必须是非空字符串")
    if record["phase"] not in {"full_request", "prefill", "decode"}:
        raise ValueError("phase 不属于冻结集合")
    start = timestamp(record.get("window_start_ns"), "window_start_ns")
    end = timestamp(record.get("window_end_ns"), "window_end_ns")
    if end < start:
        raise ValueError("A window 半开区间逆序")
    if _integer(record.get("T_window_ns"), "T_window_ns") != end - start:
        raise ValueError("A window 长度不一致")
    values = {field: _integer(record.get(field), field) for field in (*_TOP_LEVEL, *_CUDA_SUBCATEGORIES, *_WAIT_SUBCATEGORIES)}
    expected = end - start
    if sum(values[field] for field in _TOP_LEVEL) != expected:
        raise ValueError("A 顶层守恒失败")
    if values["A_cuda_api_submit_ns"] + values["A_cuda_api_non_submit_ns"] != values["A_cuda_api_ns"]:
        raise ValueError("A CUDA API 二级守恒失败")
    if sum(values[field] for field in _WAIT_SUBCATEGORIES) != values["A_device_wait_ns"]:
        raise ValueError("A device-wait 二级守恒失败")
    for field in _AUDIT_FIELDS:
        if _integer(record.get(field), field) != 0:
            raise ValueError(f"{field} 必须为 0")
    primary = record["primary_reason"]
    if primary is not None and (not isinstance(primary, str) or not primary):
        raise ValueError("primary_reason 必须是非空字符串或 null")
    secondary = record["secondary_reasons"]
    if not isinstance(secondary, list) or any(not isinstance(reason, str) or not reason for reason in secondary):
        raise ValueError("secondary_reasons 必须是非空字符串数组")
    if len(secondary) != len(set(secondary)) or primary in secondary:
        raise ValueError("reason codes 不得重复")
