"""B provenance must be a per-physical-sync projection of S semantics."""

from __future__ import annotations

import importlib
from typing import Any

import pytest

from exposedpath_v141.ab_inputs import ABInputs, CanonicalBundle
from exposedpath_v141.q0_oracle import calculate_expected_timing, load_oracle_bundle


def _b_module():
    try:
        return importlib.import_module("exposedpath_v141.b_provenance")
    except ModuleNotFoundError as exc:
        pytest.fail(f"B provenance 尚未实现: {exc}")


def _case(case_id: str) -> dict[str, Any]:
    return next(case for case in load_oracle_bundle()["cases"] if case["case_id"] == case_id)


def _inputs(case_id: str, *, reverse_syncs: bool = False) -> tuple[ABInputs, dict[str, Any]]:
    case = _case(case_id)
    construction = case["construction"]
    activities = {
        activity["activity_label"]: {
            "record_id": f"{case_id}:{activity['activity_label']}",
            "start_ns": activity["start_ns"],
            "end_ns": activity["end_ns"],
            "activity_kind": activity["activity_type"],
        }
        for activity in construction.get("activities", [])
    }
    expected_by_label = {
        expected["sync_label"]: expected for expected in case["expected"]["syncs"]
    }
    s_records: list[dict[str, object]] = []
    for ordinal, sync in enumerate(construction["syncs"]):
        expected = expected_by_label[sync["sync_label"]]
        terminal_expected = expected["terminal"]
        terminal_label = terminal_expected.get("activity_label")
        terminal = {
            "status": terminal_expected["status"],
            "kind": terminal_expected["kind"],
            "activity_id": None if terminal_label is None else activities[terminal_label]["record_id"],
            "end_ns": None if terminal_label is None else activities[terminal_label]["end_ns"],
            "clock_domain_id": None if terminal_label is None else "NSYS_TRACE_RELATIVE_NS",
        }
        s_records.append({
            "sync_id": f"{case_id}:{sync['sync_label']}",
            "registry_rule_id": f"rule:{sync['sync_kind']}",
            "sync_kind": sync["sync_kind"],
            "sync_origin": "natural_token_ready",
            "callsite_id": f"callsite:{sync['sync_label']}",
            "request_id": "request-1",
            "repeat_id": "repeat-1",
            "sync_owner_phase": construction.get("sync_owner_phase", "DECODE"),
            "host_start_ns": sync["start_ns"],
            "host_end_ns": sync["end_ns"],
            "wait_set_activity_ids": [activities[label]["record_id"] for label in expected["wait_set_activity_labels"]],
            "terminal": terminal,
            "validity": expected["validity"],
            "primary_reason": expected.get("primary_reason"),
            "secondary_reasons": expected["secondary_reasons"],
            "activity_origin_phases": {
                activities[label]["record_id"]: construction.get("activity_origin_phase", "PREFILL")
                for label in expected["wait_set_activity_labels"]
            },
            "terminal_origin_phase": construction.get("activity_origin_phase", "PREFILL") if terminal_label else None,
            "cross_phase_dependency": case_id == "Q0-PHASE-SPILL-001",
        })
    if reverse_syncs:
        s_records.reverse()
    canonical = CanonicalBundle(
        manifest={}, records={"device_activity": tuple(activities.values())}, schema={},
        cuda_api_by_id={}, activity_by_id={row["record_id"]: row for row in activities.values()},
        physical_sync_by_id={},
    )
    return ABInputs(canonical, {}, tuple(s_records), (), (), ()), case


@pytest.mark.parametrize("case_id", ["Q0-STREAM-001", "Q0-COMPLETED-001", "Q0-EVENT-001"])
def test_valid_sync_timing_matches_independent_q0_oracle(case_id: str):
    """Drops union/pre-sync/return-tail arithmetic or includes unrelated overlap."""
    inputs, case = _inputs(case_id)
    record = _b_module().calculate_b_syncs(inputs)[0]
    expected = calculate_expected_timing(case, case["construction"]["syncs"][0]["sync_label"])

    assert record["validity"] == "B_VALID"
    assert {field: record[field] for field in expected} == expected
    _b_module().validate_b_record(record)


def test_b_rows_are_one_to_one_with_s_syncs_and_deterministically_ordered():
    """Would fail if B merged physical syncs or leaked input iteration order."""
    inputs, _ = _inputs("Q0-OVERLAPPING-HOST-SYNC-001", reverse_syncs=True)
    records = _b_module().calculate_b_syncs(inputs)

    assert [record["sync_id"] for record in records] == sorted(
        record["sync_id"] for record in inputs.s_records
    )
    assert {record["sync_id"] for record in records} == {
        record["sync_id"] for record in inputs.s_records
    }
    assert len(records) == len(inputs.s_records)
    assert not any("total" in field.casefold() or "sum" in field.casefold() for field in records[0])


@pytest.mark.parametrize(
    ("case_id", "expected_status"),
    [
        ("Q0-EMPTY-001", "B_NOT_APPLICABLE"),
        ("Q0-TERMINAL-TIE-001", "B_AMBIGUOUS"),
        ("Q0-MISSING-EVENT-001", "B_INVALID"),
    ],
)
def test_non_calculable_s_states_project_to_null_timing(case_id: str, expected_status: str):
    """Would fail if unknown/empty evidence became a zero-valued timing claim."""
    inputs, _ = _inputs(case_id)
    record = _b_module().calculate_b_syncs(inputs)[0]

    assert record["validity"] == expected_status
    assert all(record[field] is None for field in (
        "wait_set_hidden_union_ns", "wait_set_exposed_union_ns", "terminal_pre_sync_ns",
        "terminal_overlap_sync_ns", "sync_return_tail_ns",
    ))
    _b_module().validate_b_record(record)


def test_cross_phase_provenance_is_preserved_without_clipping_b_lifecycle():
    """Would fail if B adopted A's phase-window clipping or discarded S provenance."""
    inputs, case = _inputs("Q0-PHASE-SPILL-001")
    record = _b_module().calculate_b_syncs(inputs)[0]
    expected = calculate_expected_timing(case, "S_DECODE_OWNER")

    assert record["sync_owner_phase"] == "DECODE"
    assert record["activity_origin_phases"] == ["PREFILL"]
    assert record["terminal_origin_phase"] == "PREFILL"
    assert record["cross_phase_dependency"] is True
    assert {field: record[field] for field in expected} == expected


def test_overlapping_wait_set_activities_use_union_not_duration_sum():
    """Would fail if overlapping hidden/exposed activity time were double counted."""
    inputs, _ = _inputs("Q0-STREAM-001")
    first_id, second_id = inputs.s_records[0]["wait_set_activity_ids"]
    inputs.canonical.activity_by_id[str(first_id)]["end_ns"] = 70
    inputs.canonical.activity_by_id[str(second_id)]["start_ns"] = 30

    record = _b_module().calculate_b_syncs(inputs)[0]

    assert record["wait_set_hidden_union_ns"] == 40  # [10, 50), not 40 + 20.
    assert record["wait_set_exposed_union_ns"] == 40  # [50, 90), not 20 + 40.


def test_completion_boundary_terminal_nulls_activity_timing_but_keeps_return_tail():
    """Would fail if a boundary terminal gained activity duration or lost its observable tail."""
    inputs, _ = _inputs("Q0-STREAM-001")
    inputs.s_records[0]["terminal"] = {
        "status": "VALID",
        "kind": "COMPLETION_BOUNDARY",
        "activity_id": None,
        "end_ns": 70,
        "clock_domain_id": "OBSERVED_BOUNDARY",
    }

    record = _b_module().calculate_b_syncs(inputs)[0]

    assert record["terminal_pre_sync_ns"] is None
    assert record["terminal_overlap_sync_ns"] is None
    assert record["sync_return_tail_ns"] == 30
    _b_module().validate_b_record(record)


def test_validation_rejects_extra_aggregate_field_and_zero_for_nonvalid_state():
    """Would fail if the public record admitted an aggregate or fabricated unknown timing."""
    inputs, _ = _inputs("Q0-EMPTY-001")
    record = _b_module().calculate_b_syncs(inputs)[0]

    aggregate = dict(record)
    aggregate["b_total_ns"] = 1
    with pytest.raises(ValueError, match="字段集合"):
        _b_module().validate_b_record(aggregate)

    fabricated = dict(record)
    fabricated["wait_set_hidden_union_ns"] = 0
    with pytest.raises(ValueError, match="null"):
        _b_module().validate_b_record(fabricated)


@pytest.mark.parametrize(("values", "want"), [
    (("prefill", "prefill"), ["prefill"]),
    (("prefill", "decode"), ["decode", "prefill"]),
    ((None, "prefill"), ["prefill", None]),
    ((None, None), [None]),
])
def test_b_projects_real_s_mapping_values_not_activity_keys(values, want):
    """The real S shape is a mapping, unlike the old list-only B fixture."""
    inputs, _ = _inputs("Q0-STREAM-001")
    sr = inputs.s_records[0]
    first, second = sr["wait_set_activity_ids"]
    sr["activity_origin_phases"] = {second: values[1], first: values[0]}
    record = _b_module().calculate_b_syncs(inputs)[0]
    assert record["activity_origin_phases"] == want
    sr["activity_origin_phases"] = {first: values[0], second: values[1]}
    assert _b_module().calculate_b_syncs(inputs)[0] == record


@pytest.mark.parametrize("damage", ["missing", "null", "list", "missing_member", "extra_member", "empty_phase", "nontext_phase"])
def test_b_rejects_malformed_s_phase_mapping_without_guessing(damage):
    inputs, _ = _inputs("Q0-STREAM-001")
    sr = inputs.s_records[0]
    first = sr["wait_set_activity_ids"][0]
    if damage == "missing": del sr["activity_origin_phases"]
    elif damage == "null": sr["activity_origin_phases"] = None
    elif damage == "list": sr["activity_origin_phases"] = ["prefill"]
    elif damage == "missing_member": del sr["activity_origin_phases"][first]
    elif damage == "extra_member": sr["activity_origin_phases"]["outside"] = "prefill"
    elif damage == "empty_phase": sr["activity_origin_phases"][first] = ""
    else: sr["activity_origin_phases"][first] = 1
    with pytest.raises(ValueError, match="activity_origin_phases"):
        _b_module().calculate_b_syncs(inputs)
