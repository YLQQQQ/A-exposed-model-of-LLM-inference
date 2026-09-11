"""Q0 独立标准答案的结构与区间算术测试。"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys

import pytest

from exposedpath_v141.q0_oracle import (
    OracleValidationError,
    calculate_expected_timing,
    load_oracle_bundle,
    validate_oracle_bundle,
)
from scripts.verify_q0_oracle_independence import check_source


def literal_bundle():
    return {
        "oracle_version": "exposedpath-q0-oracle-0.2.0",
        "contract_version": "exposedpath-measurement-contract-0.2.0",
        "cases": [
            {
                "case_id": "LITERAL-STREAM-001",
                "case_class": "POSITIVE",
                "required_for_q0": True,
                "features": ["STREAM", "UNRELATED_OVERLAP"],
                "required_contract_rules": ["MC-S-003", "MC-S-009"],
                "construction": {
                    "activities": [
                        {
                            "activity_label": "K1",
                            "activity_type": "KERNEL",
                            "start_ns": 10,
                            "end_ns": 30,
                        },
                        {
                            "activity_label": "K2",
                            "activity_type": "KERNEL",
                            "start_ns": 30,
                            "end_ns": 90,
                        },
                    ],
                    "syncs": [
                        {
                            "sync_label": "S1",
                            "sync_kind": "STREAM",
                            "start_ns": 50,
                            "end_ns": 100,
                        }
                    ],
                    "dependency_edges": [
                        {"from": "K1", "to": "K2", "edge_type": "SAME_STREAM_ORDER"}
                    ],
                },
                "expected": {
                    "syncs": [
                        {
                            "sync_label": "S1",
                            "wait_set_status": "VALID_NONEMPTY",
                            "wait_set_activity_labels": ["K1", "K2"],
                            "terminal": {
                                "status": "VALID",
                                "kind": "ACTIVITY",
                                "activity_label": "K2",
                            },
                            "validity": "VALID_NONEMPTY",
                            "primary_reason": None,
                            "secondary_reasons": [],
                            "b_status": "B_VALID",
                            "a_relations": ["A_device_wait_ns=40", "A_sync_residual_ns=10"],
                            "b_relations": ["wait_set_exposed_union_ns=40"],
                        }
                    ]
                },
            }
        ],
    }


def test_minimal_oracle_bundle_is_accepted():
    validate_oracle_bundle(literal_bundle())


def test_duplicate_case_id_is_rejected():
    bundle = literal_bundle()
    bundle["cases"].append(deepcopy(bundle["cases"][0]))

    with pytest.raises(OracleValidationError, match="重复 case_id"):
        validate_oracle_bundle(bundle)


def test_oracle_does_not_infer_wait_set():
    bundle = literal_bundle()
    del bundle["cases"][0]["expected"]["syncs"][0]["wait_set_activity_labels"]

    with pytest.raises(OracleValidationError, match="wait-set 标准答案"):
        validate_oracle_bundle(bundle)


def test_wait_set_cannot_reference_unknown_activity():
    bundle = literal_bundle()
    bundle["cases"][0]["expected"]["syncs"][0]["wait_set_activity_labels"].append("K9")

    with pytest.raises(OracleValidationError, match="未知 activity"):
        validate_oracle_bundle(bundle)


def test_valid_terminal_must_be_in_written_wait_set():
    bundle = literal_bundle()
    bundle["cases"][0]["expected"]["syncs"][0]["terminal"]["activity_label"] = "K1"
    bundle["cases"][0]["expected"]["syncs"][0]["wait_set_activity_labels"] = ["K2"]

    with pytest.raises(OracleValidationError, match="terminal 不属于"):
        validate_oracle_bundle(bundle)


def test_expected_timing_uses_written_wait_set_and_interval_union():
    case = literal_bundle()["cases"][0]

    timing = calculate_expected_timing(case, "S1")

    assert timing == {
        "wait_set_hidden_union_ns": 40,
        "wait_set_exposed_union_ns": 40,
        "terminal_pre_sync_ns": 20,
        "terminal_overlap_sync_ns": 40,
        "sync_return_tail_ns": 10,
    }


def test_completed_before_terminal_tail_does_not_include_pre_sync_gap():
    case = literal_bundle()["cases"][0]
    case["construction"]["activities"] = [
        {"activity_label": "K1", "activity_type": "KERNEL", "start_ns": 10, "end_ns": 30}
    ]
    expected_sync = case["expected"]["syncs"][0]
    expected_sync["wait_set_activity_labels"] = ["K1"]
    expected_sync["terminal"]["activity_label"] = "K1"

    timing = calculate_expected_timing(case, "S1")

    assert timing["wait_set_hidden_union_ns"] == 20
    assert timing["wait_set_exposed_union_ns"] == 0
    assert timing["sync_return_tail_ns"] == 50


def test_core_positive_cases_exist():
    cases = {case["case_id"]: case for case in load_oracle_bundle()["cases"]}

    assert {
        "Q0-STREAM-001",
        "Q0-DEVICE-001",
        "Q0-CONTEXT-001",
        "Q0-EVENT-001",
        "Q0-EVENT-XSTREAM-001",
        "Q0-COMPLETED-001",
        "Q0-EMPTY-001",
        "Q0-KERNEL-MEMOP-001",
    } <= set(cases)


def test_core_cases_cover_required_positive_features():
    features = {
        feature
        for case in load_oracle_bundle()["cases"]
        for feature in case["features"]
    }

    assert {
        "STREAM",
        "DEVICE",
        "CONTEXT",
        "EVENT_PREFIX",
        "CROSS_STREAM_EVENT",
        "COMPLETED_BEFORE",
        "VALID_EMPTY",
        "UNRELATED_OVERLAP",
        "KERNEL_MEMOP_MIXED",
    } <= features


@pytest.mark.parametrize(
    ("case_id", "sync_label", "expected"),
    [
        (
            "Q0-STREAM-001",
            "S_STREAM",
            {
                "wait_set_hidden_union_ns": 40,
                "wait_set_exposed_union_ns": 40,
                    "terminal_pre_sync_ns": 20,
                "terminal_overlap_sync_ns": 40,
                "sync_return_tail_ns": 10,
            },
        ),
        (
            "Q0-COMPLETED-001",
            "S_STREAM",
            {
                "wait_set_hidden_union_ns": 20,
                "wait_set_exposed_union_ns": 0,
                "terminal_pre_sync_ns": 20,
                "terminal_overlap_sync_ns": 0,
                "sync_return_tail_ns": 50,
            },
        ),
    ],
)
def test_committed_oracle_has_hand_checkable_timing(case_id, sync_label, expected):
    cases = {case["case_id"]: case for case in load_oracle_bundle()["cases"]}

    assert calculate_expected_timing(cases[case_id], sync_label) == expected


def test_negative_ambiguous_and_boundary_cases_exist():
    cases = {case["case_id"]: case for case in load_oracle_bundle()["cases"]}

    assert {
        "Q0-TERMINAL-TIE-001",
        "Q0-MISSING-EVENT-001",
        "Q0-MISSING-CORR-001",
        "Q0-DROPPED-001",
        "Q0-EXTERNAL-001",
        "Q0-SUBMISSION-RACE-001",
        "Q0-DEFAULT-LEGACY-001",
        "Q0-DEFAULT-PTDS-001",
        "Q0-MULTITHREAD-ORDERED-001",
        "Q0-OVERLAPPING-HOST-SYNC-001",
        "Q0-PHASE-SPILL-001",
        "Q0-INVOCATION-BLEED-001",
        "Q0-GRAPH-UNSUPPORTED-001",
        "Q0-SYNC-D2H-UNSUPPORTED-001",
        "Q0-QUERY-001",
    } <= set(cases)


def test_required_failure_modes_have_explicit_non_valid_answers():
    cases = load_oracle_bundle()["cases"]
    targeted = [
        case
        for case in cases
        if case["case_class"] in {"NEGATIVE", "AMBIGUOUS"}
    ]

    assert targeted
    for case in targeted:
        for expected_sync in case["expected"]["syncs"]:
            assert expected_sync["validity"] in {"INVALID", "AMBIGUOUS"}
            assert expected_sync["primary_reason"]
            assert expected_sync["terminal"]["status"] != "VALID"


def test_oracle_feature_matrix_is_complete():
    features = {
        feature
        for case in load_oracle_bundle()["cases"]
        for feature in case["features"]
    }

    assert {
        "TERMINAL_TIE",
        "MISSING_EVENT_MAPPING",
        "MISSING_CORRELATION",
        "DROPPED_RECORDS",
        "EXTERNAL_OWNERSHIP",
        "SUBMISSION_RACE",
        "DEFAULT_STREAM_LEGACY",
        "DEFAULT_STREAM_PTDS",
        "MULTITHREAD_ORDERED",
        "OVERLAPPING_HOST_SYNC",
        "PHASE_SPILL",
        "INVOCATION_BLEED",
        "GRAPH_UNSUPPORTED",
        "SYNC_D2H_UNSUPPORTED",
        "QUERY_NON_SYNC",
    } <= features


def test_oracle_references_only_frozen_rules_and_reason_codes():
    root = Path(__file__).resolve().parents[1]
    contract = json.loads(
        (root / "docs" / "v1_4_1" / "contracts" / "measurement_contract_v0_2.json")
        .read_text(encoding="utf-8")
    )
    known_rules = {rule["rule_id"] for rule in contract["rules"]}
    reason_validity = {
        reason: group["default_validity"]
        for group in contract["s_layer"]["reason_priority"]
        for reason in group["reasons"]
    }

    for case in load_oracle_bundle()["cases"]:
        assert set(case["required_contract_rules"]) <= known_rules
        for expected_sync in case["expected"]["syncs"]:
            reason = expected_sync["primary_reason"]
            if reason is not None:
                assert reason in reason_validity
                assert expected_sync["validity"] == reason_validity[reason]


def test_oracle_independence_checker_passes():
    root = Path(__file__).resolve().parents[1]
    completed = subprocess.run(
        [sys.executable, str(root / "scripts" / "verify_q0_oracle_independence.py")],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "oracle_independence: PASS" in completed.stdout


def test_oracle_independence_checker_rejects_analyzer_import_and_inference():
    source = """
import analysis

def calculate_expected_timing(case, sync_label):
    edges = case[\"construction\"][\"dependency_edges\"]
    return recover_wait_set(edges)
"""

    problems = check_source(source)

    assert "禁止导入: analysis" in problems
    assert "区间函数禁止读取 dependency_edges" in problems
    assert "区间函数禁止调用被测逻辑: recover_wait_set" in problems
