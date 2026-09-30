"""Per-physical-sync B provenance projected from already recovered S semantics.

This module intentionally does not recover a wait set, choose a terminal, or
change validity.  Those are S-layer decisions.  B only combines the supplied
S membership with Canonical activity intervals to describe one sync's visible
lifecycle.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .ab_inputs import ABInputs
from .intervals import intersect_interval, interval_length
from .time_representation import timestamp, duration, hidden_lower_bound


class BProvenanceError(ValueError):
    """A B record or the trusted S-to-Canonical projection is malformed."""


_B_FIELDS = frozenset({
    "sync_id", "registry_rule_id", "sync_kind", "sync_origin", "callsite_id",
    "request_id", "repeat_id", "sync_owner_phase", "activity_origin_phases",
    "terminal_origin_phase", "cross_phase_dependency", "sync_start_ns", "sync_end_ns",
    "wait_set_activity_ids", "wait_set_hidden_union_ns", "wait_set_exposed_union_ns",
    "terminal", "terminal_pre_sync_ns", "terminal_overlap_sync_ns",
    "sync_return_tail_ns", "validity", "primary_reason", "secondary_reasons",
})
_TIMING_FIELDS = (
    "wait_set_hidden_union_ns", "wait_set_exposed_union_ns", "terminal_pre_sync_ns",
    "terminal_overlap_sync_ns", "sync_return_tail_ns",
)
_VALIDITY = {
    "VALID_NONEMPTY": "B_VALID",
    "VALID_EMPTY": "B_NOT_APPLICABLE",
    "AMBIGUOUS": "B_AMBIGUOUS",
    "INVALID": "B_INVALID",
}
_TERMINAL_FIELDS = frozenset({"status", "kind", "activity_id", "end_ns", "clock_domain_id"})


def _nonnegative_integer(value: object, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise BProvenanceError(f"{label} 必须是非负整数")
    return duration(value, label)


def _optional_text(value: object, label: str) -> str | None:
    if value is not None and (not isinstance(value, str) or not value):
        raise BProvenanceError(f"{label} 必须是非空字符串或 null")
    return value


def _terminal_from_s(s_record: Mapping[str, object]) -> dict[str, object]:
    raw = s_record.get("terminal")
    if not isinstance(raw, Mapping):
        raise BProvenanceError("S terminal 必须是对象")
    if set(raw) != _TERMINAL_FIELDS:
        raise BProvenanceError("S terminal 字段集合不匹配")
    return {field: raw[field] for field in _TERMINAL_FIELDS}


def _activity_interval(inputs: ABInputs, activity_id: str) -> tuple[int, int]:
    activity = inputs.canonical.activity_by_id.get(activity_id)
    if activity is None:
        raise BProvenanceError(f"S wait-set activity 不在 Canonical 中: {activity_id}")
    return (
        timestamp(activity.get("start_ns"), f"activity {activity_id}.start_ns"),
        timestamp(activity.get("end_ns"), f"activity {activity_id}.end_ns"),
    )


def _calculate_valid_timing(
    inputs: ABInputs, s_record: Mapping[str, object], terminal: Mapping[str, object],
) -> dict[str, int | None]:
    sync_start = timestamp(s_record.get("host_start_ns"), "S host_start_ns")
    sync_end = timestamp(s_record.get("host_end_ns"), "S host_end_ns")
    if sync_start > sync_end:
        raise BProvenanceError("S sync 时间区间逆序")
    raw_wait_set = s_record.get("wait_set_activity_ids")
    if not isinstance(raw_wait_set, list):
        raise BProvenanceError("S wait_set_activity_ids 必须是数组")

    activity_intervals = [_activity_interval(inputs, str(activity_id)) for activity_id in raw_wait_set]
    hidden = [
        overlap for interval in activity_intervals
        if (overlap := intersect_interval(interval, (hidden_lower_bound(), sync_start))) is not None
    ]
    exposed = [
        overlap for interval in activity_intervals
        if (overlap := intersect_interval(interval, (sync_start, sync_end))) is not None
    ]

    terminal_kind = terminal.get("kind")
    terminal_end = timestamp(terminal.get("end_ns"), "terminal.end_ns")
    if terminal_kind == "ACTIVITY":
        terminal_id = terminal.get("activity_id")
        if not isinstance(terminal_id, str) or not terminal_id:
            raise BProvenanceError("ACTIVITY terminal 缺少 activity_id")
        terminal_interval = _activity_interval(inputs, terminal_id)
        terminal_pre = intersect_interval(terminal_interval, (hidden_lower_bound(), sync_start))
        terminal_overlap = intersect_interval(terminal_interval, (sync_start, sync_end))
        terminal_pre_ns: int | None = 0 if terminal_pre is None else terminal_pre[1] - terminal_pre[0]
        terminal_overlap_ns: int | None = (
            0 if terminal_overlap is None else terminal_overlap[1] - terminal_overlap[0]
        )
    elif terminal_kind == "COMPLETION_BOUNDARY":
        terminal_pre_ns = None
        terminal_overlap_ns = None
    else:
        raise BProvenanceError("B_VALID 的 S terminal kind 非法")

    return {
        "wait_set_hidden_union_ns": interval_length(hidden),
        "wait_set_exposed_union_ns": interval_length(exposed),
        "terminal_pre_sync_ns": terminal_pre_ns,
        "terminal_overlap_sync_ns": terminal_overlap_ns,
        "sync_return_tail_ns": max(0, sync_end - max(sync_start, terminal_end)),
    }


def _project_b_record(inputs: ABInputs, s_record: Mapping[str, object]) -> dict[str, object]:
    s_validity = s_record.get("validity")
    b_validity = _VALIDITY.get(s_validity)
    if b_validity is None:
        raise BProvenanceError("S validity 非法")
    terminal = _terminal_from_s(s_record)
    wait_set = s_record.get("wait_set_activity_ids")
    if not isinstance(wait_set, list):
        raise BProvenanceError("S wait_set_activity_ids 必须是数组")
    origins = s_record.get("activity_origin_phases")
    if not isinstance(origins, Mapping):
        raise BProvenanceError("S activity_origin_phases 必须是 activity -> phase 对象")
    if set(origins) != set(wait_set):
        raise BProvenanceError("S activity_origin_phases 必须覆盖且仅覆盖 wait set")
    phases = {_optional_text(value, "S activity_origin_phases 成员") for value in origins.values()}
    record: dict[str, object] = {
        "sync_id": s_record.get("sync_id"),
        "registry_rule_id": s_record.get("registry_rule_id"),
        "sync_kind": s_record.get("sync_kind"),
        "sync_origin": s_record.get("sync_origin"),
        "callsite_id": s_record.get("callsite_id"),
        "request_id": s_record.get("request_id"),
        "repeat_id": s_record.get("repeat_id"),
        "sync_owner_phase": s_record.get("sync_owner_phase"),
        # S retains activity -> phase; B's existing schema is unique phases.
        # Explicit null remains unknown. Stable order is serialization only.
        "activity_origin_phases": sorted(phases, key=lambda value: (value is None, value or "")),
        "terminal_origin_phase": s_record.get("terminal_origin_phase"),
        "cross_phase_dependency": s_record.get("cross_phase_dependency"),
        "sync_start_ns": s_record.get("host_start_ns"),
        "sync_end_ns": s_record.get("host_end_ns"),
        "wait_set_activity_ids": list(wait_set),
        "terminal": terminal,
        "validity": b_validity,
        "primary_reason": s_record.get("primary_reason"),
        "secondary_reasons": list(s_record.get("secondary_reasons", [])),
    }
    if b_validity == "B_VALID":
        record.update(_calculate_valid_timing(inputs, s_record, terminal))
    else:
        record.update({field: None for field in _TIMING_FIELDS})
    if 'ownership_profile' in s_record:
        from copy import deepcopy
        from .gate8_closed_prior import EXTRA_FIELDS
        record.update({k:deepcopy(s_record[k]) for k in EXTRA_FIELDS})
    if 'sync_provenance' in s_record:
        from copy import deepcopy
        from .time_representation import raw_physical_provenance
        if not raw_physical_provenance() or inputs.s_manifest.get('schema_version')!='exposedpath-s-layer/0.4.0':
            raise BProvenanceError('RAW_PROVENANCE_VERSION_MISMATCH')
        record['sync_provenance'] = deepcopy(s_record['sync_provenance'])
    validate_b_record(record)
    return record


def calculate_b_syncs(inputs: ABInputs) -> tuple[dict[str, object], ...]:
    """Return exactly one deterministic B record for every trusted S physical sync."""

    sync_ids = [record.get("sync_id") for record in inputs.s_records]
    if any(not isinstance(sync_id, str) or not sync_id for sync_id in sync_ids):
        raise BProvenanceError("S sync_id 必须是非空字符串")
    if len(set(sync_ids)) != len(sync_ids):
        raise BProvenanceError("S sync_id 重复，无法保持 per-physical-sync 一一对应")
    return tuple(
        _project_b_record(inputs, record)
        for record in sorted(inputs.s_records, key=lambda item: str(item["sync_id"]))
    )


def validate_b_record(record: Mapping[str, object]) -> None:
    """Validate the frozen per-sync B record shape and null-only validity rules."""

    from .gate8_closed_prior import EXTRA_FIELDS, PROFILE
    extra = EXTRA_FIELDS if 'ownership_profile' in record else set()
    raw_extra = {'sync_provenance'} if 'sync_provenance' in record else set()
    from .time_representation import raw_physical_provenance
    if bool(raw_extra) != raw_physical_provenance() or (raw_extra and extra):
        raise BProvenanceError('RAW_PROVENANCE_VERSION_MISMATCH')
    if set(record) != _B_FIELDS | extra | raw_extra:
        raise BProvenanceError("B record 字段集合不匹配")
    if raw_extra:
        from .raw_sync_provenance import validate_provenance
        validate_provenance(record)
    if extra:
        from .gate8_closed_prior import validate_provenance
        validate_provenance(record)
        if record['ownership_profile'] != PROFILE:
            raise BProvenanceError('CLOSED_PRIOR_VERSION_UNSUPPORTED')
        provenance = record['activity_provenance']
        if not isinstance(provenance,list) or [p['activity_id'] for p in provenance] != record['wait_set_activity_ids']:
            raise BProvenanceError('CLOSED_PRIOR_PROVENANCE_WAIT_SET_MISMATCH')
        cross = any(p['relation_to_sync']=='closed_prior_request' for p in provenance)
        if type(record['cross_request_dependency']) is not bool or record['cross_request_dependency'] != cross:
            raise BProvenanceError('CLOSED_PRIOR_CROSS_REQUEST_MISMATCH')
    sync_id = record["sync_id"]
    if not isinstance(sync_id, str) or not sync_id:
        raise BProvenanceError("sync_id 必须是非空字符串")
    for field in (
        "registry_rule_id", "sync_kind", "sync_origin", "callsite_id", "request_id",
        "repeat_id", "sync_owner_phase", "terminal_origin_phase", "primary_reason",
    ):
        _optional_text(record[field], field)
    if record["validity"] in {"B_VALID", "B_NOT_APPLICABLE"}:
        start = timestamp(record["sync_start_ns"], "sync_start_ns")
        end = timestamp(record["sync_end_ns"], "sync_end_ns")
        if start > end:
            raise BProvenanceError("B sync 时间区间逆序")
    else:
        start, end = record["sync_start_ns"], record["sync_end_ns"]
        if (start is None) != (end is None):
            raise BProvenanceError("B invalid/ambiguous sync 时间必须同时存在或同时为空")
        if start is not None:
            start = timestamp(start, "sync_start_ns")
            end = timestamp(end, "sync_end_ns")
            if start > end:
                raise BProvenanceError("B sync 时间区间逆序")
    if not isinstance(record["cross_phase_dependency"], bool):
        raise BProvenanceError("cross_phase_dependency 必须是布尔值")
    origins = record["activity_origin_phases"]
    if not isinstance(origins, list) or len(set(origins)) != len(origins):
        raise BProvenanceError("activity_origin_phases 必须是唯一数组")
    for origin in origins:
        _optional_text(origin, "activity_origin_phases 成员")
    wait_set = record["wait_set_activity_ids"]
    if not isinstance(wait_set, list) or len(set(wait_set)) != len(wait_set):
        raise BProvenanceError("wait_set_activity_ids 必须是唯一数组")
    for activity_id in wait_set:
        if not isinstance(activity_id, str) or not activity_id:
            raise BProvenanceError("wait_set_activity_ids 成员必须是非空字符串")
    reasons = record["secondary_reasons"]
    if not isinstance(reasons, list) or len(set(reasons)) != len(reasons):
        raise BProvenanceError("secondary_reasons 必须是唯一数组")
    for reason in reasons:
        if not isinstance(reason, str) or not reason:
            raise BProvenanceError("secondary_reasons 成员必须是非空字符串")

    terminal = record["terminal"]
    if not isinstance(terminal, Mapping) or set(terminal) != _TERMINAL_FIELDS:
        raise BProvenanceError("terminal 字段集合不匹配")
    status, kind = terminal.get("status"), terminal.get("kind")
    if status not in {"VALID", "NOT_APPLICABLE", "AMBIGUOUS", "INVALID"}:
        raise BProvenanceError("terminal.status 非法")
    if kind not in {"ACTIVITY", "COMPLETION_BOUNDARY", "NONE"}:
        raise BProvenanceError("terminal.kind 非法")
    activity_id, terminal_end, clock = terminal.get("activity_id"), terminal.get("end_ns"), terminal.get("clock_domain_id")
    if kind == "ACTIVITY":
        if status != "VALID" or not isinstance(activity_id, str) or not activity_id:
            raise BProvenanceError("ACTIVITY terminal 必须是有效且具 identity")
        timestamp(terminal_end, "terminal.end_ns")
        if not isinstance(clock, str) or not clock:
            raise BProvenanceError("ACTIVITY terminal 缺少 clock")
    elif kind == "COMPLETION_BOUNDARY":
        if status != "VALID" or activity_id is not None:
            raise BProvenanceError("COMPLETION_BOUNDARY terminal 非法")
        timestamp(terminal_end, "terminal.end_ns")
        if not isinstance(clock, str) or not clock:
            raise BProvenanceError("COMPLETION_BOUNDARY terminal 缺少 clock")
    elif any(value is not None for value in (activity_id, terminal_end, clock)):
        raise BProvenanceError("NONE terminal 不得带 identity 或时钟")

    validity = record["validity"]
    if validity not in set(_VALIDITY.values()):
        raise BProvenanceError("B validity 非法")
    if validity == "B_VALID":
        if status != "VALID" or kind not in {"ACTIVITY", "COMPLETION_BOUNDARY"}:
            raise BProvenanceError("B_VALID 必须保留有效 terminal")
        if record["primary_reason"] is not None:
            raise BProvenanceError("B_VALID primary_reason 必须为 null")
        for field in ("wait_set_hidden_union_ns", "wait_set_exposed_union_ns", "sync_return_tail_ns"):
            _nonnegative_integer(record[field], field)
        for field in ("terminal_pre_sync_ns", "terminal_overlap_sync_ns"):
            if kind == "ACTIVITY":
                _nonnegative_integer(record[field], field)
            elif record[field] is not None:
                raise BProvenanceError("COMPLETION_BOUNDARY terminal timing 必须为 null")
        return

    if any(record[field] is not None for field in _TIMING_FIELDS):
        raise BProvenanceError("非 B_VALID 的 timing 必须为 null")
    expected_status = {
        "B_NOT_APPLICABLE": "NOT_APPLICABLE",
        "B_AMBIGUOUS": "AMBIGUOUS",
        "B_INVALID": "INVALID",
    }[validity]
    if status != expected_status or kind != "NONE":
        raise BProvenanceError("非 B_VALID terminal 状态与 validity 不一致")
    if validity == "B_NOT_APPLICABLE":
        if record["primary_reason"] is not None:
            raise BProvenanceError("B_NOT_APPLICABLE primary_reason 必须为 null")
    elif record["primary_reason"] is None:
        raise BProvenanceError("B_AMBIGUOUS/B_INVALID 必须保留 primary_reason")
