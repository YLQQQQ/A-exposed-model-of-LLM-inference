"""Q0 独立标准答案的结构与区间算术测试。"""

from __future__ import annotations

from copy import deepcopy

import pytest

from exposedpath_v141.q0_oracle import (
    OracleValidationError,
    calculate_expected_timing,
    validate_oracle_bundle,
)


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
                            "end_ns": 70,
                        },
                        {
                            "activity_label": "K2",
                            "activity_type": "KERNEL",
                            "start_ns": 20,
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
        "terminal_pre_sync_ns": 30,
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
