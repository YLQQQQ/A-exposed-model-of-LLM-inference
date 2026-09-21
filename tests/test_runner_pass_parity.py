"""EP-G7-09: Pass 0 / Pass 1 parity identity and machine-readable provenance.

These tests consume only existing artifacts (``cross_pass_parity.json``,
``inference_results.jsonl``, ``exclusion_log.jsonl``); no parallel manifest or
checker system is introduced.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from exposedpath import runner
from exposedpath.cross_pass_validator import (
    EXECUTION_PARITY_FAILURE,
    PARITY_ATTEMPT_PLAN_FIELDS,
    PARITY_ENVIRONMENT_FIELDS,
    PARITY_EXECUTION_FIELDS,
    PARITY_GPU_FIELDS,
    PARITY_PHASE_BOUNDARY_FIELDS,
    PARITY_STATUS_GROUPS,
    PARITY_WORKLOAD_FIELDS,
    PASS_ATTEMPT_ACCOUNTING_MISMATCH,
    PASS_EXECUTION_PARITY_MISMATCH,
    PASS_GPU_MISMATCH,
    PASS_PARITY_IDENTITY_MISSING,
    PASS_PARITY_OK,
    PASS_WORKLOAD_MISMATCH,
    load_attempt_accounting,
    summarize_attempt_records,
    validate_attempt_accounting,
    validate_pair,
)
from exposedpath.results import (
    EXCLUSION_REASON_EARLY_EOS,
    EXCLUSION_REASON_OOM,
    EXCLUSION_REASON_RUNTIME_ERROR,
    PHASE_BOUNDARY_POLICY,
    RETRY_POLICY,
    TOKEN_READY_MECHANISM,
    TOKEN_READY_ORIGIN_N1,
    TOKEN_READY_ORIGIN_NATURAL,
    record_exclusion,
    record_success,
)

RUN_ID = "run-20260921T000000Z-test0001"
PROVENANCE = {"data_role": "PILOT", "run_role": "PILOT", "study_mode": "G1_NATURAL"}


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _manifest(**overrides) -> dict:
    manifest = {
        "experiment_id": "gate7-parity",
        "wmpc_id": "wmpc-0123456789abcdef",
        "run_id": RUN_ID,
        "prompt_tokens_sha256": "a" * 64,
        "fixed_input_tokens": 128,
        "fixed_output_tokens": 8,
        "batch_size": 1,
        "sampling_config": {"do_sample": False},
        "warmup_count": 2,
        "repeat_count": 4,
        "gpu": 0,
        "gpu_index": 0,
        "gpu_uuid": "GPU-test-uuid",
        "gpu_pci_bus_id": "00000000:01:00.0",
        "gpu_name": "Test GPU",
        "attention_backend": "sdpa",
        "execution_mode": "eager",
        "study_mode": "G1_NATURAL",
        "n1_intervention": None,
        "data_role": "PILOT",
        "run_role": "PILOT",
        "model_id": "test-model",
    }
    manifest.update(overrides)
    return manifest


def _write_parity(tmp_path: Path, pass_label: str, manifest: dict) -> dict:
    """Run the real parity writer and return the file it produced."""
    manifest_path = tmp_path / "wmpc_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / pass_label
    runner._write_cross_pass_parity(
        manifest, pass_label, output_dir, manifest_path, manifest["model_id"], "cpu",
    )
    return json.loads((output_dir / "cross_pass_parity.json").read_text(encoding="utf-8"))


def _write_pass(tmp_path: Path, pass_label: str, plan: dict, *, provenance=None) -> Path:
    """Materialize one pass directory from a repeat-index plan."""
    provenance = provenance or PROVENANCE
    pass_dir = tmp_path / pass_label
    for index, outcome in plan.items():
        if outcome == "success":
            _write_success(pass_dir, index, provenance)
        else:
            _write_exclusion(pass_dir, index, outcome, provenance)
    return pass_dir


def _write_success(pass_dir: Path, index: int, provenance: dict, **overrides):
    kwargs = dict(provenance)
    kwargs.update(overrides)
    return record_success(
        pass_dir, RUN_ID, index,
        inference_start_ns=1_000_000, inference_end_ns=1_500_000,
        prefill_latency_ms=1.0, decode_latency_ms=2.0,
        actual_input_tokens=128, actual_output_tokens=8, batch_size=1,
        output_len_expected=8, **kwargs,
    )


def _write_exclusion(pass_dir: Path, index: int, reason_code: str, provenance: dict, **overrides):
    kwargs = dict(provenance)
    kwargs.update(overrides)
    return record_exclusion(
        pass_dir, RUN_ID, index, f"detail::{reason_code}",
        exclusion_reason=reason_code, output_len_expected=8, **kwargs,
    )


# ---------------------------------------------------------------------------
# frozen parity identity
# ---------------------------------------------------------------------------

def test_runner_parity_file_carries_the_frozen_identity(tmp_path):
    manifest = _manifest()
    parity = _write_parity(tmp_path, "pass0", manifest)

    assert parity["schema_version"] == "exposedpath-v3-cross-pass-2"
    for _status, fields in PARITY_STATUS_GROUPS:
        missing = [f for f in fields if f not in parity]
        assert missing == [], f"parity file is missing frozen identity fields: {missing}"


def test_frozen_tables_cover_workload_gpu_execution_phase_and_attempt_plan():
    assert "prompt_tokens_sha256" in PARITY_WORKLOAD_FIELDS
    assert "fixed_output_tokens" in PARITY_WORKLOAD_FIELDS
    assert "gpu_uuid" in PARITY_GPU_FIELDS
    assert "study_mode" in PARITY_EXECUTION_FIELDS
    assert "phase_boundary_policy" in PARITY_PHASE_BOUNDARY_FIELDS
    assert "token_ready_mechanism" in PARITY_PHASE_BOUNDARY_FIELDS
    assert "data_role" in PARITY_ENVIRONMENT_FIELDS
    assert "retry_policy" in PARITY_ATTEMPT_PLAN_FIELDS


def test_phase_boundary_and_retry_policy_are_the_frozen_values(tmp_path):
    manifest = _manifest()
    parity = _write_parity(tmp_path, "pass1", manifest)

    assert parity["phase_boundary_policy"] == PHASE_BOUNDARY_POLICY
    assert parity["token_ready_mechanism"] == TOKEN_READY_MECHANISM
    assert parity["token_ready_origin"] == TOKEN_READY_ORIGIN_NATURAL
    assert parity["retry_policy"] == RETRY_POLICY
    assert parity["planned_repeat_count"] == manifest["repeat_count"]
    assert parity["planned_warmup_count"] == manifest["warmup_count"]


def test_pass0_and_pass1_parity_identity_is_identical(tmp_path):
    manifest = _manifest()
    pass0 = _write_parity(tmp_path, "pass0", manifest)
    pass1 = _write_parity(tmp_path, "pass1", manifest)

    assert validate_pair(pass0, pass1) == [PASS_PARITY_OK]

    identity_fields = [f for _status, fields in PARITY_STATUS_GROUPS for f in fields]
    assert {f: pass0[f] for f in identity_fields} == {f: pass1[f] for f in identity_fields}
    assert pass0["pass_id"] != pass1["pass_id"]


def test_missing_phase_boundary_identity_fails_closed(tmp_path):
    manifest = _manifest()
    pass0 = _write_parity(tmp_path, "pass0", manifest)
    pass1 = dict(pass0)
    del pass1["phase_boundary_policy"]

    issues = validate_pair(pass0, pass1)
    assert PASS_PARITY_IDENTITY_MISSING in issues
    assert PASS_PARITY_OK not in issues


def test_missing_environment_identity_fails_closed(tmp_path):
    manifest = _manifest()
    pass0 = _write_parity(tmp_path, "pass0", manifest)
    pass1 = dict(pass0)
    del pass1["data_role"]

    issues = validate_pair(pass0, pass1)
    assert PASS_PARITY_IDENTITY_MISSING in issues
    assert PASS_EXECUTION_PARITY_MISMATCH in issues


def test_missing_attempt_plan_identity_fails_closed(tmp_path):
    manifest = _manifest()
    pass0 = _write_parity(tmp_path, "pass0", manifest)
    pass1 = dict(pass0)
    del pass1["retry_policy"]

    assert PASS_PARITY_IDENTITY_MISSING in validate_pair(pass0, pass1)


def test_legacy_parity_files_without_identity_fail_closed():
    legacy = {"runner_source_sha256": "same"}
    issues = validate_pair(dict(legacy), dict(legacy))

    assert PASS_PARITY_IDENTITY_MISSING in issues
    assert PASS_PARITY_OK not in issues


def test_empty_parity_identity_is_execution_failure():
    assert validate_pair({}, {}) == [EXECUTION_PARITY_FAILURE]


def test_intentional_token_ready_difference_fails(tmp_path):
    manifest = _manifest()
    pass0 = _write_parity(tmp_path, "pass0", manifest)
    pass1 = dict(pass0)
    pass1["token_ready_origin"] = TOKEN_READY_ORIGIN_N1

    issues = validate_pair(pass0, pass1)
    assert PASS_EXECUTION_PARITY_MISMATCH in issues
    assert PASS_PARITY_OK not in issues


def test_intentional_environment_difference_fails(tmp_path):
    manifest = _manifest()
    pass0 = _write_parity(tmp_path, "pass0", manifest)
    pass1 = dict(pass0)
    pass1["torch_num_threads"] = pass0["torch_num_threads"] + 1

    assert PASS_EXECUTION_PARITY_MISMATCH in validate_pair(pass0, pass1)


def test_intentional_workload_and_gpu_differences_still_detected(tmp_path):
    manifest = _manifest()
    pass0 = _write_parity(tmp_path, "pass0", manifest)

    workload_diff = dict(pass0)
    workload_diff["fixed_output_tokens"] = 16
    assert PASS_WORKLOAD_MISMATCH in validate_pair(pass0, workload_diff)

    gpu_diff = dict(pass0)
    gpu_diff["gpu_uuid"] = "GPU-other"
    assert PASS_GPU_MISMATCH in validate_pair(pass0, gpu_diff)


# ---------------------------------------------------------------------------
# attempt / exclusion / retry records
# ---------------------------------------------------------------------------

def test_success_record_carries_attempt_mode_and_phase_identity(tmp_path):
    record = _write_success(tmp_path, 0, PROVENANCE)

    assert record["attempt_status"] == "success"
    assert record["repeat_index"] == 0
    assert record["retry_index"] == 0
    assert record["is_retry"] is False
    assert record["retry_of_attempt_uid"] is None
    assert record["attempt_uid"] == f"{RUN_ID}-rep0000"
    assert record["attempt_plan_version"]
    assert record["data_role"] == "PILOT"
    assert record["run_role"] == "PILOT"
    assert record["study_mode"] == "G1_NATURAL"
    assert record["phase_boundary_policy_version"]
    assert record["early_eos"] is False
    assert record["oom"] is False
    assert record["exclusion_reason"] is None
    assert record["output_len_expected"] == 8


def test_exclusion_record_requires_a_frozen_reason_code(tmp_path):
    with pytest.raises(ValueError):
        record_exclusion(
            tmp_path, RUN_ID, 1, "free-form reason",
            exclusion_reason="NOT_A_FROZEN_CODE", **PROVENANCE,
        )

    record = _write_exclusion(tmp_path, 1, EXCLUSION_REASON_EARLY_EOS, PROVENANCE,
                              early_eos=True, output_len_actual=3)
    assert record["attempt_status"] == "excluded"
    assert record["exclusion_reason"] == EXCLUSION_REASON_EARLY_EOS
    assert record["invalid_reason"] == f"detail::{EXCLUSION_REASON_EARLY_EOS}"
    assert record["early_eos"] is True
    assert record["oom"] is False
    assert record["output_len_actual"] == 3


def test_missing_role_provenance_fails_closed(tmp_path):
    with pytest.raises(ValueError):
        _write_success(tmp_path, 0, {**PROVENANCE, "data_role": ""})
    with pytest.raises(ValueError):
        _write_exclusion(tmp_path, 1, EXCLUSION_REASON_OOM, {**PROVENANCE, "study_mode": ""})


def test_retry_record_needs_parent_and_has_distinct_uid(tmp_path):
    with pytest.raises(ValueError):
        _write_success(tmp_path, 0, PROVENANCE, retry_index=1)

    first = _write_success(tmp_path, 0, PROVENANCE)
    retry = _write_success(
        tmp_path, 0, PROVENANCE, retry_index=1, retry_of_attempt_uid=first["attempt_uid"],
    )
    assert retry["is_retry"] is True
    assert retry["attempt_uid"] != first["attempt_uid"]
    assert retry["retry_of_attempt_uid"] == first["attempt_uid"]


def test_pass0_and_pass1_records_share_one_key_shape(tmp_path):
    pass0_dir = tmp_path / "pass0"
    pass1_dir = tmp_path / "pass1"
    success0 = _write_success(pass0_dir, 0, PROVENANCE)
    success1 = _write_success(pass1_dir, 0, PROVENANCE)
    exclusion0 = _write_exclusion(pass0_dir, 1, EXCLUSION_REASON_OOM, PROVENANCE, oom=True)
    exclusion1 = _write_exclusion(pass1_dir, 1, EXCLUSION_REASON_OOM, PROVENANCE, oom=True)

    assert list(success0) == list(success1)
    assert list(exclusion0) == list(exclusion1)
    assert success0 == success1
    assert exclusion0 == exclusion1


# ---------------------------------------------------------------------------
# attempt accounting parity
# ---------------------------------------------------------------------------

def test_load_attempt_accounting_requires_the_results_artifact(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_attempt_accounting(
            tmp_path / "pass0", planned_warmup_count=2, planned_repeat_count=4,
        )


def test_load_attempt_accounting_reads_existing_artifacts(tmp_path):
    pass_dir = _write_pass(
        tmp_path, "pass0",
        {0: "success", 1: "success", 2: EXCLUSION_REASON_EARLY_EOS, 3: "success"},
    )
    accounting = load_attempt_accounting(
        pass_dir, planned_warmup_count=2, planned_repeat_count=4,
    )

    assert accounting["success_count"] == 3
    assert accounting["exclusion_count"] == 1
    assert accounting["success_repeat_indexes"] == [0, 1, 3]
    assert accounting["exclusion_repeat_indexes"] == [2]
    assert accounting["exclusion_reason_counts"] == {EXCLUSION_REASON_EARLY_EOS: 1}
    assert accounting["missing_repeat_indexes"] == []
    assert accounting["retry_count"] == 0
    assert accounting["exclusion_log_present"] is True


def test_equivalent_attempt_accounting_passes(tmp_path):
    plan = {0: "success", 1: "success", 2: EXCLUSION_REASON_EARLY_EOS, 3: "success"}
    pass0 = load_attempt_accounting(
        _write_pass(tmp_path, "pass0", plan), planned_warmup_count=2, planned_repeat_count=4,
    )
    pass1 = load_attempt_accounting(
        _write_pass(tmp_path, "pass1", plan), planned_warmup_count=2, planned_repeat_count=4,
    )

    assert validate_attempt_accounting(pass0, pass1) == [PASS_PARITY_OK]


def test_exclusion_reason_difference_fails(tmp_path):
    pass0 = load_attempt_accounting(
        _write_pass(tmp_path, "pass0", {0: "success", 1: EXCLUSION_REASON_EARLY_EOS}),
        planned_warmup_count=2, planned_repeat_count=2,
    )
    pass1 = load_attempt_accounting(
        _write_pass(tmp_path, "pass1", {0: "success", 1: EXCLUSION_REASON_OOM}),
        planned_warmup_count=2, planned_repeat_count=2,
    )

    issues = validate_attempt_accounting(pass0, pass1)
    assert PASS_ATTEMPT_ACCOUNTING_MISMATCH in issues
    assert PASS_PARITY_OK not in issues


def test_retry_difference_fails(tmp_path):
    pass0_dir = _write_pass(tmp_path, "pass0", {0: "success", 1: "success"})
    pass1_dir = _write_pass(tmp_path, "pass1", {0: "success", 1: "success"})
    first = _write_success(pass1_dir, 1, PROVENANCE)
    _write_success(pass1_dir, 1, PROVENANCE, retry_index=1,
                   retry_of_attempt_uid=first["attempt_uid"])

    pass0 = load_attempt_accounting(pass0_dir, planned_warmup_count=1, planned_repeat_count=2)
    pass1 = load_attempt_accounting(pass1_dir, planned_warmup_count=1, planned_repeat_count=2)

    assert pass1["retry_count"] == 1
    assert PASS_ATTEMPT_ACCOUNTING_MISMATCH in validate_attempt_accounting(pass0, pass1)


def test_missing_repeat_index_fails_closed(tmp_path):
    pass0 = load_attempt_accounting(
        _write_pass(tmp_path, "pass0", {0: "success", 1: "success", 3: "success"}),
        planned_warmup_count=2, planned_repeat_count=4,
    )
    pass1 = load_attempt_accounting(
        _write_pass(tmp_path, "pass1", {0: "success", 1: "success", 2: "success", 3: "success"}),
        planned_warmup_count=2, planned_repeat_count=4,
    )

    assert pass0["missing_repeat_indexes"] == [2]
    issues = validate_attempt_accounting(pass0, pass1)
    assert PASS_ATTEMPT_ACCOUNTING_MISMATCH in issues


def test_duplicate_attempt_fails_closed(tmp_path):
    pass0_dir = _write_pass(tmp_path, "pass0", {0: "success"})
    _write_success(pass0_dir, 0, PROVENANCE)

    pass0 = load_attempt_accounting(pass0_dir, planned_warmup_count=1, planned_repeat_count=1)
    pass1 = load_attempt_accounting(
        _write_pass(tmp_path, "pass1", {0: "success"}),
        planned_warmup_count=1, planned_repeat_count=1,
    )

    assert pass0["duplicate_repeat_indexes"] == [0]
    assert PASS_ATTEMPT_ACCOUNTING_MISMATCH in validate_attempt_accounting(pass0, pass1)


def test_legacy_records_without_attempt_identity_fail_closed():
    legacy_success = {"repeat_index": 0, "attempt_uid": "legacy-0", "attempt_status": "success"}
    legacy_exclusion = {"repeat_index": 1, "invalid_reason": "OOM", "attempt_status": "excluded"}

    accounting = summarize_attempt_records(
        [legacy_success], [legacy_exclusion], planned_warmup_count=1, planned_repeat_count=2,
    )
    fresh = summarize_attempt_records(
        [], [], planned_warmup_count=1, planned_repeat_count=2,
    )

    assert len(accounting["records_missing_attempt_identity"]) == 2
    issues = validate_attempt_accounting(accounting, fresh)
    assert PASS_PARITY_IDENTITY_MISSING in issues
    assert PASS_ATTEMPT_ACCOUNTING_MISMATCH in issues


def test_planned_count_mismatch_fails(tmp_path):
    pass0 = load_attempt_accounting(
        _write_pass(tmp_path, "pass0", {0: "success", 1: "success"}),
        planned_warmup_count=1, planned_repeat_count=2,
    )
    pass1 = load_attempt_accounting(
        _write_pass(tmp_path, "pass1", {0: "success", 1: "success"}),
        planned_warmup_count=1, planned_repeat_count=3,
    )

    assert PASS_EXECUTION_PARITY_MISMATCH in validate_attempt_accounting(pass0, pass1)


def test_attempt_accounting_missing_fields_fail_closed(tmp_path):
    pass0 = load_attempt_accounting(
        _write_pass(tmp_path, "pass0", {0: "success"}),
        planned_warmup_count=1, planned_repeat_count=1,
    )
    incomplete = {k: v for k, v in pass0.items() if k != "retry_count"}

    issues = validate_attempt_accounting(pass0, incomplete)
    assert PASS_PARITY_IDENTITY_MISSING in issues
    assert PASS_ATTEMPT_ACCOUNTING_MISMATCH in issues


def test_exclusion_log_absent_is_reported_not_assumed(tmp_path):
    pass_dir = _write_pass(tmp_path, "pass0", {0: "success", 1: "success"})
    accounting = load_attempt_accounting(
        pass_dir, planned_warmup_count=1, planned_repeat_count=2,
    )

    assert accounting["exclusion_log_present"] is False
    assert accounting["exclusion_count"] == 0


def test_runtime_exclusion_records_frozen_reason_code(tmp_path):
    record = _write_exclusion(tmp_path, 0, EXCLUSION_REASON_RUNTIME_ERROR, PROVENANCE)
    assert record["exclusion_reason"] == EXCLUSION_REASON_RUNTIME_ERROR
    assert record["oom"] is False
