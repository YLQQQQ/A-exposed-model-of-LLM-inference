"""独立 Q0 observed evaluator；不恢复 W(s)，不调用 S/A/B。"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .q0_oracle import calculate_expected_timing


_ELIGIBILITY_BASE = {"formal_evidence": False, "q0_status": "NOT_RUN"}
_B_TIMING = (
    "wait_set_hidden_union_ns",
    "wait_set_exposed_union_ns",
    "terminal_pre_sync_ns",
    "terminal_overlap_sync_ns",
    "sync_return_tail_ns",
)
_OBSERVED_SCHEMA = (
    Path(__file__).resolve().parents[1]
    / "docs"
    / "v1_4_1"
    / "contracts"
    / "q0_observed_schema_v0_2.json"
)


def _by_unique_id(items: Any, key: str, label: str) -> tuple[dict[str, Mapping[str, Any]], list[str]]:
    problems: list[str] = []
    if not isinstance(items, list):
        return {}, [f"{label} 必须是数组"]
    result: dict[str, Mapping[str, Any]] = {}
    for item in items:
        if not isinstance(item, Mapping):
            problems.append(f"{label} 成员必须是对象")
            continue
        value = item.get(key)
        if not isinstance(value, str) or not value:
            problems.append(f"{label}.{key} 必须是非空字符串")
            continue
        if value in result:
            problems.append(f"{label} 重复 {key}: {value}")
            continue
        result[value] = item
    return result, problems


def _compare_field(
    mismatches: list[str], sync_label: str, field: str, expected: Any, observed: Any
) -> None:
    if observed != expected:
        mismatches.append(
            f"{sync_label}.{field}: expected={expected!r}, observed={observed!r}"
        )


def _compare_unique_string_set_field(
    mismatches: list[str], sync_label: str, field: str, expected: Any, observed: Any
) -> None:
    def is_unique_string_list(value: Any) -> bool:
        return (
            isinstance(value, list)
            and all(isinstance(item, str) for item in value)
            and len(value) == len(set(value))
        )

    if (
        not is_unique_string_list(expected)
        or not is_unique_string_list(observed)
        or set(observed) != set(expected)
    ):
        mismatches.append(
            f"{sync_label}.{field}: expected={expected!r}, observed={observed!r}"
        )


def _intersection(interval: tuple[int, int], window: tuple[int, int]) -> tuple[int, int] | None:
    start, end = max(interval[0], window[0]), min(interval[1], window[1])
    return (start, end) if end > start else None


def _union_length(intervals: Sequence[tuple[int, int]]) -> int:
    if not intervals:
        return 0
    ordered = sorted(intervals)
    start, end = ordered[0]
    total = 0
    for next_start, next_end in ordered[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            total += end - start
            start, end = next_start, next_end
    return total + end - start


def _real_expected_timing(
    expected_sync: Mapping[str, Any], observed_case: Mapping[str, Any], observed_sync: Mapping[str, Any]
) -> dict[str, int]:
    """用人工 wait-set/terminal 标签和真实区间独立计算，不读取 analyzer 数值。"""

    intervals, problems = _by_unique_id(
        observed_case.get("activity_intervals"), "activity_label", "activity_intervals"
    )
    if problems:
        raise ValueError("；".join(problems))
    wait_labels = expected_sync.get("wait_set_activity_labels", [])
    missing = sorted(set(wait_labels) - set(intervals))
    if missing:
        raise ValueError(f"真实活动区间缺少 oracle wait-set 标签: {missing}")
    sync_start = int(observed_sync["sync_start_ns"])
    sync_end = int(observed_sync["sync_end_ns"])
    if sync_end < sync_start:
        raise ValueError("真实 sync 区间非法")
    hidden: list[tuple[int, int]] = []
    exposed: list[tuple[int, int]] = []
    for label in wait_labels:
        activity = intervals[label]
        interval = (int(activity["start_ns"]), int(activity["end_ns"]))
        if interval[1] < interval[0]:
            raise ValueError(f"真实活动区间非法: {label}")
        before = _intersection(interval, (0, sync_start))
        during = _intersection(interval, (sync_start, sync_end))
        if before:
            hidden.append(before)
        if during:
            exposed.append(during)
    terminal = expected_sync.get("terminal", {})
    terminal_pre = terminal_overlap = 0
    terminal_end = sync_start
    if terminal.get("status") == "VALID":
        label = terminal.get("activity_label")
        if label not in intervals:
            raise ValueError(f"真实活动区间缺少 oracle terminal 标签: {label}")
        activity = intervals[label]
        activity_start, terminal_end = int(activity["start_ns"]), int(activity["end_ns"])
        terminal_pre = max(0, min(terminal_end, sync_start) - activity_start)
        terminal_overlap = max(
            0, min(terminal_end, sync_end) - max(activity_start, sync_start)
        )
    exposed_union = _union_length(exposed)
    return {
        "wait_set_hidden_union_ns": _union_length(hidden),
        "wait_set_exposed_union_ns": exposed_union,
        "terminal_pre_sync_ns": terminal_pre,
        "terminal_overlap_sync_ns": terminal_overlap,
        "sync_return_tail_ns": max(0, sync_end - max(sync_start, terminal_end)),
        "A_device_wait_ns": exposed_union,
        "A_sync_residual_ns": max(0, sync_end - sync_start - exposed_union),
    }


def _check_relation(
    relation: str,
    observed_sync: Mapping[str, Any],
    mismatches: list[str],
    real_expected: Mapping[str, int] | None = None,
) -> None:
    sync_label = str(observed_sync.get("sync_label"))
    a_window = observed_sync.get("a_window")
    if not isinstance(a_window, Mapping):
        a_window = {}
    b_timing = observed_sync.get("b_timing")
    if not isinstance(b_timing, Mapping):
        b_timing = {}

    if relation.startswith("A_") and "_ns=" in relation:
        field, literal = relation.split("=", 1)
        expected = real_expected.get(field) if real_expected is not None else int(literal)
        _compare_field(mismatches, sync_label, field, expected, a_window.get(field))
    elif relation.startswith(("wait_set_", "sync_return_tail_ns=")) and "=" in relation:
        field, literal = relation.split("=", 1)
        expected = real_expected.get(field) if real_expected is not None else int(literal)
        _compare_field(mismatches, sync_label, field, expected, b_timing.get(field))
    elif relation.startswith("terminal="):
        expected = relation.split("=", 1)[1]
        terminal = observed_sync.get("terminal")
        actual = terminal.get("activity_label") if isinstance(terminal, Mapping) else None
        _compare_field(mismatches, sync_label, "terminal", expected, actual)
    elif relation == "terminal_kind=MEMOP":
        if observed_sync.get("terminal_activity_kind") not in {"MEMCPY", "MEMSET"}:
            mismatches.append(f"{sync_label}.terminal_kind 不是 MEMOP")
    elif relation in {"whole_sync=A_unattributed", "affected_window=A_unattributed"}:
        duration = int(observed_sync["sync_end_ns"]) - int(observed_sync["sync_start_ns"])
        if int(a_window.get("A_unattributed_ns", -1)) < duration:
            mismatches.append(f"{sync_label}.A_unattributed 未覆盖同步区间")
    elif relation == "device_wait_composition=MIXED":
        if int(a_window.get("A_device_wait_kernel_memop_mixed_ns", 0)) <= 0:
            mismatches.append(f"{sync_label}.device_wait_composition 不是 MIXED")
    elif relation.endswith("_not_dependency"):
        activity = relation.removesuffix("_not_dependency")
        if activity in observed_sync.get("wait_set_activity_labels", []):
            mismatches.append(f"{sync_label}.{activity} 被错误纳入依赖")
    elif relation == "accounting_owner_phase=DECODE":
        if str(observed_sync.get("sync_owner_phase", "")).upper() != "DECODE":
            mismatches.append(f"{sync_label}.accounting_owner_phase 不是 DECODE")
    elif relation == "activity_origin_phase=PREFILL":
        origins = {str(value).upper() for value in observed_sync.get("activity_origin_phases", [])}
        if "PREFILL" not in origins:
            mismatches.append(f"{sync_label}.activity_origin_phase 缺少 PREFILL")
    elif relation == "cross_phase=true":
        if observed_sync.get("cross_phase_dependency") is not True:
            mismatches.append(f"{sync_label}.cross_phase 不是 true")
    elif relation in {"A_uses_interval_union", "A_overlap_not_double_counted"}:
        if a_window.get("top_level_conservation_error_ns") != 0 or a_window.get("top_level_overlap_ns") != 0:
            mismatches.append(f"{sync_label}.A 区间并集/互斥审计失败")
    elif relation in {
        "B_is_per_sync",
        "B_records_not_summed",
        "legacy_cross_stream_predecessor_in_W",
        "ptds_scope_is_thread_local",
        "cross_thread_order_requires_event_evidence",
    }:
        # 精确 sync 集合和 wait-set 比较已经覆盖这些关系，不额外接受总量字段。
        return
    else:
        mismatches.append(f"{sync_label}.未支持的 oracle relation: {relation}")


def evaluate_q0_observed(
    oracle: Mapping[str, Any], observed: Mapping[str, Any]
) -> dict[str, Any]:
    """逐 case 比较人工 expected 与已标准化 observed，任何缺口均 fail closed。"""

    global_mismatches: list[str] = []
    if not isinstance(observed, Mapping):
        observed = {}
        global_mismatches.append("observed 必须是对象")
    schema = json.loads(_OBSERVED_SCHEMA.read_text(encoding="utf-8"))
    schema_errors = sorted(
        Draft202012Validator(schema).iter_errors(observed),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if schema_errors:
        first = schema_errors[0]
        location = ".".join(str(part) for part in first.absolute_path) or "root"
        global_mismatches.append(f"observed schema 失败 {location}: {first.message}")
    if observed.get("schema_version") != "exposedpath-q0-observed/0.2.0":
        global_mismatches.append("observed schema_version 不匹配")
    source_kind = observed.get("source_kind")
    if source_kind not in {"SYNTHETIC_CANONICAL", "REAL_CONTROLLED_TRACE"}:
        global_mismatches.append("observed source_kind 非法")
    if observed.get("data_role") != "Engineering":
        global_mismatches.append("observed data_role 必须是 Engineering")
    expected_scope = (
        "Q0_REAL_CANDIDATE_ONLY"
        if source_kind == "REAL_CONTROLLED_TRACE"
        else "Q0_SYNTHETIC_ONLY"
    )
    expected_eligibility = {**_ELIGIBILITY_BASE, "scope": expected_scope}
    if observed.get("research_eligibility") != expected_eligibility:
        global_mismatches.append("observed 资格不得升级")

    oracle_cases, oracle_problems = _by_unique_id(oracle.get("cases"), "case_id", "oracle.cases")
    observed_cases, observed_problems = _by_unique_id(
        observed.get("cases"), "case_id", "observed.cases"
    )
    global_mismatches.extend(oracle_problems)
    global_mismatches.extend(observed_problems)
    if set(oracle_cases) != set(observed_cases):
        missing = sorted(set(oracle_cases) - set(observed_cases))
        extra = sorted(set(observed_cases) - set(oracle_cases))
        global_mismatches.append(f"case 集合不一致: missing={missing}, extra={extra}")

    case_reports: list[dict[str, Any]] = []
    for case_id in sorted(oracle_cases):
        mismatches: list[str] = []
        oracle_case = oracle_cases[case_id]
        observed_case = observed_cases.get(case_id)
        if observed_case is None:
            case_reports.append(
                {"case_id": case_id, "required_for_q0": bool(oracle_case["required_for_q0"]), "status": "FAIL", "mismatches": ["case 缺失"]}
            )
            continue
        expected_syncs, expected_problems = _by_unique_id(
            oracle_case["expected"].get("syncs"), "sync_label", f"{case_id}.expected.syncs"
        )
        actual_syncs, actual_problems = _by_unique_id(
            observed_case.get("syncs"), "sync_label", f"{case_id}.observed.syncs"
        )
        mismatches.extend(expected_problems)
        mismatches.extend(actual_problems)
        if set(expected_syncs) != set(actual_syncs):
            mismatches.append(
                f"sync 集合不一致: expected={sorted(expected_syncs)}, observed={sorted(actual_syncs)}"
            )
        expected_non_sync = oracle_case["expected"].get("non_sync_api_labels", [])
        _compare_field(
            mismatches,
            case_id,
            "non_sync_api_labels",
            expected_non_sync,
            observed_case.get("non_sync_api_labels"),
        )
        for sync_label, expected_sync in expected_syncs.items():
            actual = actual_syncs.get(sync_label)
            if actual is None:
                continue
            _compare_unique_string_set_field(
                mismatches,
                sync_label,
                "wait_set_activity_labels",
                expected_sync.get("wait_set_activity_labels"),
                actual.get("wait_set_activity_labels"),
            )
            for field in (
                "wait_set_status",
                "validity",
                "primary_reason",
                "secondary_reasons",
                "b_status",
            ):
                _compare_field(mismatches, sync_label, field, expected_sync.get(field), actual.get(field))
            _compare_field(
                mismatches, sync_label, "terminal", expected_sync.get("terminal"), actual.get("terminal")
            )
            timing = actual.get("b_timing")
            real_expected: Mapping[str, int] | None = None
            if (
                source_kind == "REAL_CONTROLLED_TRACE"
                and expected_sync.get("b_status") in {"B_VALID", "B_NOT_APPLICABLE"}
            ):
                try:
                    real_expected = _real_expected_timing(
                        expected_sync, observed_case, actual
                    )
                except (KeyError, TypeError, ValueError) as exc:
                    mismatches.append(f"{sync_label}.真实区间预期无法计算: {exc}")
            if expected_sync.get("b_status") == "B_VALID":
                try:
                    if source_kind == "REAL_CONTROLLED_TRACE":
                        expected_timing = real_expected or {}
                    else:
                        expected_timing = calculate_expected_timing(
                            oracle_case, sync_label
                        )
                except (KeyError, TypeError, ValueError) as exc:
                    mismatches.append(f"{sync_label}.真实区间预期无法计算: {exc}")
                    expected_timing = {}
                for field in _B_TIMING:
                    _compare_field(
                        mismatches,
                        sync_label,
                        field,
                        expected_timing.get(field),
                        timing.get(field) if isinstance(timing, Mapping) else None,
                    )
            elif not isinstance(timing, Mapping) or any(timing.get(field) is not None for field in _B_TIMING):
                mismatches.append(f"{sync_label}.非 B_VALID timing 必须全为 null")
            for relation in [*expected_sync.get("a_relations", []), *expected_sync.get("b_relations", [])]:
                _check_relation(str(relation), actual, mismatches, real_expected)
        case_reports.append(
            {
                "case_id": case_id,
                "required_for_q0": bool(oracle_case["required_for_q0"]),
                "status": "PASS" if not mismatches else "FAIL",
                "mismatches": mismatches,
            }
        )

    required = [case for case in case_reports if case["required_for_q0"]]
    passed = sum(case["status"] == "PASS" for case in required)
    failed = len(required) - passed
    pass_verdict = "REAL_CASE_PASS" if source_kind == "REAL_CONTROLLED_TRACE" else "SYNTHETIC_PASS"
    verdict = pass_verdict if not global_mismatches and failed == 0 else "FAIL"
    evidence_scope = "REAL_CASE_ONLY" if source_kind == "REAL_CONTROLLED_TRACE" else "SYNTHETIC_ONLY"
    return {
        "schema_version": "exposedpath-q0-comparison/0.2.0",
        "evidence_scope": evidence_scope,
        "q0_status": "NOT_RUN",
        "research_eligibility": expected_eligibility,
        "verdict": verdict,
        "global_mismatches": global_mismatches,
        "summary": {
            "required_case_count": len(required),
            "passed_case_count": passed,
            "failed_case_count": failed,
        },
        "cases": case_reports,
    }
