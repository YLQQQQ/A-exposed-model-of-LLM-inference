"""Q0 evaluator 的独立、严格覆盖和 fail-closed 测试。"""

from __future__ import annotations

from copy import deepcopy
import json

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
