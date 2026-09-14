"""Gate 6 GPU 前 Q0 执行合同、dry-run 与资格边界测试。"""

from __future__ import annotations

from copy import deepcopy

import pytest

from exposedpath_v141.q0_execution import (
    Q0ExecutionError,
    load_q0_execution_manifest,
    validate_q0_execution_manifest,
)
from exposedpath_v141.q0_oracle import load_oracle_bundle


def test_committed_execution_manifest_covers_oracle_exactly_once():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()

    assert {case["case_id"] for case in manifest["cases"]} == {
        case["case_id"] for case in oracle["cases"]
    }
    assert len(manifest["cases"]) == 23
    assert manifest["research_eligibility"] == {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "Q0_PRE_GPU_ONLY",
    }


@pytest.mark.parametrize("mutation", ["missing", "extra", "duplicate"])
def test_case_coverage_mismatch_fails_closed(mutation):
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    if mutation == "missing":
        manifest["cases"].pop()
    elif mutation == "extra":
        extra = deepcopy(manifest["cases"][0])
        extra["case_id"] = "Q0-UNKNOWN-001"
        manifest["cases"].append(extra)
    else:
        manifest["cases"].append(deepcopy(manifest["cases"][0]))

    with pytest.raises(Q0ExecutionError, match="case"):
        validate_q0_execution_manifest(manifest, oracle)


def test_execution_manifest_cannot_claim_q0_or_formal_eligibility():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    manifest["research_eligibility"]["q0_status"] = "PASS"
    manifest["research_eligibility"]["formal_evidence"] = True

    with pytest.raises(Q0ExecutionError, match="资格"):
        validate_q0_execution_manifest(manifest, oracle)


def test_stable_labels_must_equal_oracle_construction():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    target = next(case for case in manifest["cases"] if case["activity_labels"])
    target["activity_labels"].append("UNKNOWN_ACTIVITY")

    with pytest.raises(Q0ExecutionError, match="activity_labels"):
        validate_q0_execution_manifest(manifest, oracle)


@pytest.mark.parametrize(
    ("strategy", "seed", "fault"),
    [
        ("NATIVE_CUDA", None, None),
        ("NATIVE_WITH_CANONICAL_FAULT", "Q0-MISSING-CORR-001", None),
        ("SYNTHETIC_CANONICAL", "Q0-TERMINAL-TIE-001", None),
    ],
)
def test_strategy_specific_fields_are_not_silently_guessed(strategy, seed, fault):
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    target = manifest["cases"][0]
    target.update(
        execution_strategy=strategy,
        native_seed_case_id=seed,
        fault_injection=fault,
    )

    with pytest.raises(Q0ExecutionError, match="策略"):
        validate_q0_execution_manifest(manifest, oracle)


def test_each_case_has_explicit_synthetic_profile():
    oracle = load_oracle_bundle()
    manifest = load_q0_execution_manifest()
    manifest["cases"][0]["synthetic_profile"] = None

    with pytest.raises(Q0ExecutionError, match="synthetic_profile"):
        validate_q0_execution_manifest(manifest, oracle)

