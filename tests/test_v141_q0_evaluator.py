"""Q0 evaluator 的独立、严格覆盖和 fail-closed 测试。"""

from __future__ import annotations

from copy import deepcopy
import json

import pytest

from exposedpath_v141.q0_evaluator import evaluate_q0_observed
from exposedpath_v141.q0_oracle import load_oracle_bundle
from exposedpath_v141.q0_synthetic import build_synthetic_observed


def test_evaluator_accepts_production_generated_synthetic_observed():
    oracle = load_oracle_bundle()
    observed = build_synthetic_observed()

    report = evaluate_q0_observed(oracle, observed)

    assert report["summary"]["passed_case_count"] == 23
    assert report["summary"]["failed_case_count"] == 0
    assert report["verdict"] == "SYNTHETIC_PASS"
    assert report["q0_status"] == "NOT_RUN"


def test_wrong_wait_set_is_reported_by_case_and_sync():
    oracle = load_oracle_bundle()
    observed = build_synthetic_observed()
    broken = deepcopy(observed)
    target = next(case for case in broken["cases"] if case["syncs"])
    target["syncs"][0]["wait_set_activity_labels"] = []

    report = evaluate_q0_observed(oracle, broken)

    assert report["verdict"] == "FAIL"
    failure = next(case for case in report["cases"] if case["case_id"] == target["case_id"])
    assert failure["status"] == "FAIL"
    assert any(target["syncs"][0]["sync_label"] in item for item in failure["mismatches"])


def _device_wait_set_observed():
    observed = build_synthetic_observed()
    case = next(
        case for case in observed["cases"] if case["case_id"] == "Q0-DEVICE-001"
    )
    return observed, case["syncs"][0]


def test_wait_set_labels_accept_same_unique_members_in_different_order():
    oracle = load_oracle_bundle()
    observed, sync = _device_wait_set_observed()
    sync["wait_set_activity_labels"] = ["K_B", "K_A"]

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "SYNTHETIC_PASS"


@pytest.mark.parametrize(
    "labels",
    [
        ["K_A"],
        ["K_A", "K_B", "K_EXTRA"],
        ["K_A", "K_B", "K_B"],
    ],
    ids=["missing", "extra", "duplicate"],
)
def test_wait_set_labels_reject_non_exact_or_duplicate_members(labels):
    oracle = load_oracle_bundle()
    observed, sync = _device_wait_set_observed()
    sync["wait_set_activity_labels"] = labels

    report = evaluate_q0_observed(oracle, observed)
    failure = next(
        case for case in report["cases"] if case["case_id"] == "Q0-DEVICE-001"
    )

    assert report["verdict"] == "FAIL"
    assert any("wait_set_activity_labels" in item for item in failure["mismatches"])


def test_missing_and_extra_case_fail_closed():
    oracle = load_oracle_bundle()
    observed = build_synthetic_observed()
    missing = deepcopy(observed)
    missing["cases"].pop()
    extra = deepcopy(observed)
    duplicate = deepcopy(extra["cases"][0])
    duplicate["case_id"] = "Q0-UNKNOWN-001"
    extra["cases"].append(duplicate)

    assert evaluate_q0_observed(oracle, missing)["verdict"] == "FAIL"
    assert evaluate_q0_observed(oracle, extra)["verdict"] == "FAIL"


def test_observed_cannot_claim_real_q0_or_formal_evidence():
    oracle = load_oracle_bundle()
    observed = build_synthetic_observed()
    observed["research_eligibility"]["q0_status"] = "PASS"
    observed["research_eligibility"]["formal_evidence"] = True

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "FAIL"
    assert "资格" in "；".join(report["global_mismatches"])


def test_observed_schema_rejects_unknown_fields_and_duplicate_sync():
    oracle = load_oracle_bundle()
    observed = build_synthetic_observed()
    observed["unexpected"] = "must fail closed"

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "FAIL"
    assert any("schema" in item for item in report["global_mismatches"])

    duplicate = build_synthetic_observed()
    target = next(case for case in duplicate["cases"] if case["syncs"])
    target["syncs"].append(deepcopy(target["syncs"][0]))
    duplicate_report = evaluate_q0_observed(oracle, duplicate)
    assert duplicate_report["verdict"] == "FAIL"
    assert any("重复" in item for item in duplicate_report["cases"][0]["mismatches"] + duplicate_report["global_mismatches"]) or any(
        "重复" in item
        for case in duplicate_report["cases"]
        for item in case["mismatches"]
    )


def test_synthetic_builder_does_not_read_oracle_expected():
    oracle = load_oracle_bundle()
    for case in oracle["cases"]:
        case["expected"] = {"forbidden": "the builder must ignore this"}

    observed = build_synthetic_observed(oracle_cases=oracle["cases"])

    assert len(observed["cases"]) == 23
    assert all("syncs" in case for case in observed["cases"])


def _real_stream_case():
    oracle = load_oracle_bundle()
    observed = build_synthetic_observed()
    oracle["cases"] = [case for case in oracle["cases"] if case["case_id"] == "Q0-STREAM-001"]
    observed["cases"] = [case for case in observed["cases"] if case["case_id"] == "Q0-STREAM-001"]
    observed["source_kind"] = "REAL_CONTROLLED_TRACE"
    observed["research_eligibility"]["scope"] = "Q0_REAL_CANDIDATE_ONLY"
    case = observed["cases"][0]
    case["activity_intervals"] = [
        {"activity_label": "K_S1_A", "activity_kind": "KERNEL", "start_ns": 100, "end_ns": 300},
        {"activity_label": "K_S1_B", "activity_kind": "KERNEL", "start_ns": 300, "end_ns": 900},
        {"activity_label": "K_OTHER", "activity_kind": "KERNEL", "start_ns": 550, "end_ns": 950},
    ]
    sync = case["syncs"][0]
    sync["sync_start_ns"] = 500
    sync["sync_end_ns"] = 1000
    sync["b_timing"] = {
        "wait_set_hidden_union_ns": 400,
        "wait_set_exposed_union_ns": 400,
        "terminal_pre_sync_ns": 200,
        "terminal_overlap_sync_ns": 400,
        "sync_return_tail_ns": 100,
    }
    sync["a_window"]["A_device_wait_ns"] = 400
    sync["a_window"]["A_sync_residual_ns"] = 100
    return oracle, observed


def test_real_observed_uses_actual_intervals_not_synthetic_literals():
    oracle, observed = _real_stream_case()

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "REAL_CASE_PASS"
    assert report["evidence_scope"] == "REAL_CASE_ONLY"
    assert report["q0_status"] == "NOT_RUN"


def test_real_observed_wrong_timing_fails_closed():
    oracle, observed = _real_stream_case()
    observed["cases"][0]["syncs"][0]["b_timing"]["wait_set_exposed_union_ns"] += 1

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "FAIL"
    assert any(
        "wait_set_exposed_union_ns" in mismatch
        for mismatch in report["cases"][0]["mismatches"]
    )


def test_real_observed_requires_activity_intervals():
    oracle, observed = _real_stream_case()
    del observed["cases"][0]["activity_intervals"]

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "FAIL"
    assert any("schema" in mismatch for mismatch in report["global_mismatches"])


def _real_empty_case():
    oracle = load_oracle_bundle()
    observed = build_synthetic_observed()
    oracle["cases"] = [
        case for case in oracle["cases"] if case["case_id"] == "Q0-EMPTY-001"
    ]
    observed["cases"] = [
        case for case in observed["cases"] if case["case_id"] == "Q0-EMPTY-001"
    ]
    observed["source_kind"] = "REAL_CONTROLLED_TRACE"
    observed["research_eligibility"]["scope"] = "Q0_REAL_CANDIDATE_ONLY"
    observed["cases"][0]["activity_intervals"] = []
    sync = observed["cases"][0]["syncs"][0]
    sync["sync_start_ns"] = 1000
    sync["sync_end_ns"] = 21271
    sync["a_window"]["A_device_wait_ns"] = 0
    sync["a_window"]["A_sync_residual_ns"] = 20271
    return oracle, observed


def test_real_empty_uses_actual_sync_duration_for_a_residual():
    """捕获：真实 VALID_EMPTY 仍拿合成 trace 的 30 ns 常量验收。"""
    oracle, observed = _real_empty_case()

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "REAL_CASE_PASS"


def test_real_empty_wrong_a_residual_fails_closed():
    oracle, observed = _real_empty_case()
    observed["cases"][0]["syncs"][0]["a_window"]["A_sync_residual_ns"] -= 1

    report = evaluate_q0_observed(oracle, observed)

    assert report["verdict"] == "FAIL"
    assert any(
        "A_sync_residual_ns" in mismatch
        for mismatch in report["cases"][0]["mismatches"]
    )
