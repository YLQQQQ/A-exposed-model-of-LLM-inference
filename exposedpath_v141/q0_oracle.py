"""Q0 独立标准答案的加载、校验与简单区间算术。

本模块只读取人工写定的 wait-set 与 terminal，不实现 S 层依赖恢复。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


class OracleValidationError(ValueError):
    """Q0 oracle 文件结构或内部关系不合法。"""


_ORACLE_RELATIVE_PATH = Path("q0") / "oracle_cases_v0_2.json"
_CASE_CLASSES = {"POSITIVE", "NEGATIVE", "AMBIGUOUS", "BOUNDARY"}
_VALIDITY_STATES = {"VALID_NONEMPTY", "VALID_EMPTY", "AMBIGUOUS", "INVALID"}
_PLACEHOLDERS = ("todo", "tbd", "待定")


def _mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise OracleValidationError(f"{label} 必须是对象")
    return value


def _list(value: Any, label: str) -> list[Any]:
    if not isinstance(value, list):
        raise OracleValidationError(f"{label} 必须是数组")
    return value


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise OracleValidationError(f"{label} 必须是非空字符串")
    return value


def _unique(values: list[str], label: str) -> None:
    duplicates = {value for value in values if values.count(value) > 1}
    if duplicates:
        raise OracleValidationError(f"重复 {label}: {', '.join(sorted(duplicates))}")


def _scan_placeholders(value: Any, path: str = "root") -> None:
    if isinstance(value, str):
        if any(token in value.casefold() for token in _PLACEHOLDERS):
            raise OracleValidationError(f"发现占位文本: {path}")
    elif isinstance(value, Mapping):
        for key, child in value.items():
            _scan_placeholders(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _scan_placeholders(child, f"{path}[{index}]")


def _validate_interval(item: Mapping[str, Any], label: str) -> None:
    start = item.get("start_ns")
    end = item.get("end_ns")
    if not isinstance(start, int) or not isinstance(end, int) or start < 0 or end < start:
        raise OracleValidationError(f"{label} 的时间区间非法")


def validate_oracle_bundle(bundle: Mapping[str, Any]) -> None:
    """验证 oracle 自身，不从 construction 推导任何标准答案。"""

    bundle = _mapping(bundle, "oracle")
    _text(bundle.get("oracle_version"), "oracle.oracle_version")
    _text(bundle.get("contract_version"), "oracle.contract_version")
    cases = _list(bundle.get("cases"), "oracle.cases")
    if not cases:
        raise OracleValidationError("oracle.cases 不能为空")

    case_ids: list[str] = []
    for case_index, raw_case in enumerate(cases):
        case = _mapping(raw_case, f"cases[{case_index}]")
        case_id = _text(case.get("case_id"), f"cases[{case_index}].case_id")
        case_ids.append(case_id)
        if case.get("case_class") not in _CASE_CLASSES:
            raise OracleValidationError(f"{case_id} 的 case_class 非法")
        if not isinstance(case.get("required_for_q0"), bool):
            raise OracleValidationError(f"{case_id}.required_for_q0 必须是布尔值")
        _list(case.get("features"), f"{case_id}.features")
        _list(case.get("required_contract_rules"), f"{case_id}.required_contract_rules")

        construction = _mapping(case.get("construction"), f"{case_id}.construction")
        activities = _list(construction.get("activities", []), f"{case_id}.activities")
        syncs = _list(construction.get("syncs", []), f"{case_id}.syncs")
        activity_by_label: dict[str, Mapping[str, Any]] = {}
        for raw_activity in activities:
            activity = _mapping(raw_activity, f"{case_id}.activity")
            label = _text(activity.get("activity_label"), f"{case_id}.activity_label")
            _validate_interval(activity, f"{case_id}.{label}")
            activity_by_label[label] = activity
        _unique(list(activity_by_label), f"{case_id} activity_label")

        sync_by_label: dict[str, Mapping[str, Any]] = {}
        for raw_sync in syncs:
            sync = _mapping(raw_sync, f"{case_id}.sync")
            label = _text(sync.get("sync_label"), f"{case_id}.sync_label")
            _validate_interval(sync, f"{case_id}.{label}")
            sync_by_label[label] = sync
        _unique(list(sync_by_label), f"{case_id} sync_label")

        expected = _mapping(case.get("expected"), f"{case_id}.expected")
        expected_syncs = _list(expected.get("syncs"), f"{case_id}.expected.syncs")
        expected_labels: list[str] = []
        for raw_expected_sync in expected_syncs:
            expected_sync = _mapping(raw_expected_sync, f"{case_id}.expected.sync")
            sync_label = _text(expected_sync.get("sync_label"), f"{case_id}.sync_label")
            expected_labels.append(sync_label)
            if sync_label not in sync_by_label:
                raise OracleValidationError(f"{case_id} 引用未知 sync: {sync_label}")
            if "wait_set_activity_labels" not in expected_sync:
                raise OracleValidationError(f"{case_id}/{sync_label} 缺少 wait-set 标准答案")
            wait_set = _list(
                expected_sync["wait_set_activity_labels"],
                f"{case_id}/{sync_label}.wait_set_activity_labels",
            )
            _unique(wait_set, f"{case_id}/{sync_label} wait-set activity")
            unknown = sorted(set(wait_set) - set(activity_by_label))
            if unknown:
                raise OracleValidationError(
                    f"{case_id}/{sync_label} wait-set 引用未知 activity: {', '.join(unknown)}"
                )

            validity = expected_sync.get("validity")
            if validity not in _VALIDITY_STATES:
                raise OracleValidationError(f"{case_id}/{sync_label} validity 非法")
            if expected_sync.get("wait_set_status") != validity:
                raise OracleValidationError(f"{case_id}/{sync_label} wait_set_status 与 validity 不一致")
            terminal = _mapping(expected_sync.get("terminal"), f"{case_id}/{sync_label}.terminal")
            terminal_status = terminal.get("status")
            if validity == "VALID_NONEMPTY":
                if not wait_set:
                    raise OracleValidationError(f"{case_id}/{sync_label} 非空 wait-set 实际为空")
                if terminal_status != "VALID":
                    raise OracleValidationError(f"{case_id}/{sync_label} 缺少有效 terminal")
                terminal_label = _text(
                    terminal.get("activity_label"), f"{case_id}/{sync_label}.terminal.activity_label"
                )
                if terminal_label not in wait_set:
                    raise OracleValidationError(f"{case_id}/{sync_label} terminal 不属于 wait-set")
                if expected_sync.get("b_status") != "B_VALID":
                    raise OracleValidationError(f"{case_id}/{sync_label} B 状态应为 B_VALID")
            elif validity == "VALID_EMPTY":
                if wait_set:
                    raise OracleValidationError(f"{case_id}/{sync_label} 空 wait-set 包含 activity")
                if terminal_status != "NOT_APPLICABLE":
                    raise OracleValidationError(f"{case_id}/{sync_label} terminal 应为不适用")
                if expected_sync.get("b_status") != "B_NOT_APPLICABLE":
                    raise OracleValidationError(f"{case_id}/{sync_label} B 状态应为不适用")
            else:
                _text(expected_sync.get("primary_reason"), f"{case_id}/{sync_label}.primary_reason")
                if terminal_status == "VALID":
                    raise OracleValidationError(f"{case_id}/{sync_label} 非有效记录不能有有效 terminal")
            _list(expected_sync.get("secondary_reasons", []), f"{case_id}/{sync_label}.secondary_reasons")
            _list(expected_sync.get("a_relations", []), f"{case_id}/{sync_label}.a_relations")
            _list(expected_sync.get("b_relations", []), f"{case_id}/{sync_label}.b_relations")

        _unique(expected_labels, f"{case_id} expected sync_label")
        if set(expected_labels) != set(sync_by_label):
            raise OracleValidationError(f"{case_id} 的 construction 与 expected sync 集合不一致")

    _unique(case_ids, "case_id")
    _scan_placeholders(bundle)


def load_oracle_bundle(root: Path | None = None) -> dict[str, Any]:
    """从仓库根目录加载 Q0 oracle。"""

    if root is None:
        root = Path(__file__).resolve().parents[1]
    path = root / _ORACLE_RELATIVE_PATH
    with path.open("r", encoding="utf-8") as handle:
        bundle = json.load(handle)
    validate_oracle_bundle(bundle)
    return bundle


def _intersection(interval: tuple[int, int], window: tuple[int, int]) -> tuple[int, int] | None:
    start = max(interval[0], window[0])
    end = min(interval[1], window[1])
    return (start, end) if end > start else None


def _union_length(intervals: list[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    ordered = sorted(intervals)
    total = 0
    current_start, current_end = ordered[0]
    for start, end in ordered[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end
    return total + current_end - current_start


def calculate_expected_timing(case: Mapping[str, Any], sync_label: str) -> dict[str, int]:
    """仅基于人工写定的 W(s)/terminal 计算可手算的区间标准答案。"""

    construction = _mapping(case.get("construction"), "case.construction")
    activities = {
        activity["activity_label"]: activity
        for activity in _list(construction.get("activities", []), "case.activities")
    }
    syncs = {
        sync["sync_label"]: sync
        for sync in _list(construction.get("syncs", []), "case.syncs")
    }
    expected_syncs = {
        sync["sync_label"]: sync
        for sync in _list(_mapping(case.get("expected"), "case.expected").get("syncs"), "expected.syncs")
    }
    if sync_label not in syncs or sync_label not in expected_syncs:
        raise OracleValidationError(f"未知 sync: {sync_label}")

    sync = syncs[sync_label]
    expected = expected_syncs[sync_label]
    sync_start = sync["start_ns"]
    sync_end = sync["end_ns"]
    wait_activities = [activities[label] for label in expected["wait_set_activity_labels"]]

    hidden_intervals: list[tuple[int, int]] = []
    exposed_intervals: list[tuple[int, int]] = []
    for activity in wait_activities:
        hidden = _intersection((activity["start_ns"], activity["end_ns"]), (0, sync_start))
        exposed = _intersection(
            (activity["start_ns"], activity["end_ns"]), (sync_start, sync_end)
        )
        if hidden:
            hidden_intervals.append(hidden)
        if exposed:
            exposed_intervals.append(exposed)

    terminal = expected["terminal"]
    terminal_pre_sync = 0
    terminal_overlap_sync = 0
    terminal_end = sync_start
    if terminal.get("status") == "VALID":
        terminal_activity = activities[terminal["activity_label"]]
        terminal_end = terminal_activity["end_ns"]
        terminal_pre_sync = max(0, min(terminal_end, sync_start) - terminal_activity["start_ns"])
        terminal_overlap_sync = max(
            0,
            min(terminal_end, sync_end) - max(terminal_activity["start_ns"], sync_start),
        )

    return {
        "wait_set_hidden_union_ns": _union_length(hidden_intervals),
        "wait_set_exposed_union_ns": _union_length(exposed_intervals),
        "terminal_pre_sync_ns": terminal_pre_sync,
        "terminal_overlap_sync_ns": terminal_overlap_sync,
        "sync_return_tail_ns": max(0, sync_end - max(sync_start, terminal_end)),
    }
