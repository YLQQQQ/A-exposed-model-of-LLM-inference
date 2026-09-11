"""Measurement Contract v0.2 的机器可检查不变量。"""

from __future__ import annotations

from copy import deepcopy

import pytest

from exposedpath_v141.contract import (
    ContractValidationError,
    load_contract_bundle,
    validate_contract_bundle,
)


def valid_literal_bundle():
    """返回与磁盘文件无关的最小合法合同，用于验证拒绝路径。"""

    contract = {
        "contract_version": "exposedpath-measurement-contract-0.2.0",
        "registry_version": "exposedpath-sync-registry-0.2.0",
        "test_map_version": "exposedpath-contract-test-map-0.2.0",
        "rules": [
            {"rule_id": "MC-S-001", "decision": "completion_scope_first"},
            {"rule_id": "MC-A-001", "decision": "partition_wall_clock"},
        ],
        "a_layer": {
            "top_level_categories": [
                "A_host_path",
                "A_cuda_api",
                "A_device_wait",
                "A_sync_residual",
                "A_unattributed",
            ],
            "priority": [
                "A_unattributed",
                "A_device_wait",
                "A_sync_residual",
                "A_cuda_api",
                "A_host_path",
            ],
            "output_fields": [
                "A_host_path_ns",
                "A_cuda_api_ns",
                "A_device_wait_ns",
                "A_sync_residual_ns",
                "A_unattributed_ns",
            ],
        },
        "b_layer": {
            "output_fields": [
                "sync_id",
                "wait_set_activity_ids",
                "wait_set_hidden_union_ns",
                "wait_set_exposed_union_ns",
                "terminal",
                "validity",
            ],
            "aggregation_policy": "NO_CROSS_SYNC_SUM",
            "enters_a_wall_clock_budget": False,
        },
        "derived": {
            "D_score": {
                "inputs": ["A_host_path_ns", "A_device_wait_ns"],
                "formula": "A_device_wait_ns / (A_device_wait_ns + A_host_path_ns)",
            },
            "Exposure_Signature": {
                "inputs": ["A_host_path_ns", "b.validity"],
                "formula": "versioned_projection",
            },
        },
    }
    registry = {
        "registry_version": "exposedpath-sync-registry-0.2.0",
        "contract_version": "exposedpath-measurement-contract-0.2.0",
        "rules": [
            {
                "registry_rule_id": "SYNC-STREAM-RUNTIME-001",
                "aliases": ["cudaStreamSynchronize"],
                "universe_class": "SUPPORTED_PHYSICAL_BLOCKING_SYNC",
                "completion_scope": "target_stream_dependency_closure",
                "required_evidence": ["context_id", "stream_id"],
            }
        ],
    }
    test_map = {
        "test_map_version": "exposedpath-contract-test-map-0.2.0",
        "contract_version": "exposedpath-measurement-contract-0.2.0",
        "cases": [
            {
                "case_id": "CONTRACT-COVERAGE-001",
                "kind": "contract",
                "rule_ids": ["MC-S-001", "MC-A-001"],
            }
        ],
    }
    return contract, registry, test_map


def test_minimal_valid_bundle_is_accepted():
    contract, registry, test_map = valid_literal_bundle()
    validate_contract_bundle(contract, registry, test_map)


def test_duplicate_rule_id_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    contract["rules"].append(deepcopy(contract["rules"][0]))

    with pytest.raises(ContractValidationError, match="重复规则"):
        validate_contract_bundle(contract, registry, test_map)


def test_unmapped_rule_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    test_map["cases"][0]["rule_ids"] = ["MC-S-001"]

    with pytest.raises(ContractValidationError, match="没有验证案例"):
        validate_contract_bundle(contract, registry, test_map)


def test_unknown_rule_reference_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    test_map["cases"][0]["rule_ids"].append("MC-S-999")

    with pytest.raises(ContractValidationError, match="不存在的合同规则"):
        validate_contract_bundle(contract, registry, test_map)


def test_supported_sync_without_evidence_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    registry["rules"][0]["required_evidence"] = []

    with pytest.raises(ContractValidationError, match="必需证据"):
        validate_contract_bundle(contract, registry, test_map)


def test_duplicate_api_alias_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    duplicate = deepcopy(registry["rules"][0])
    duplicate["registry_rule_id"] = "SYNC-STREAM-DRIVER-001"
    registry["rules"].append(duplicate)

    with pytest.raises(ContractValidationError, match="API alias"):
        validate_contract_bundle(contract, registry, test_map)


def test_a_priority_must_cover_each_category_once():
    contract, registry, test_map = valid_literal_bundle()
    contract["a_layer"]["priority"][-1] = "A_cuda_api"

    with pytest.raises(ContractValidationError, match="A 层优先级"):
        validate_contract_bundle(contract, registry, test_map)


def test_derived_metric_cannot_read_raw_fields():
    contract, registry, test_map = valid_literal_bundle()
    contract["derived"]["D_score"]["inputs"].append("raw.kernel_duration_ns")

    with pytest.raises(ContractValidationError, match="只能读取 A/B"):
        validate_contract_bundle(contract, registry, test_map)


def test_placeholder_text_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    contract["rules"][0]["decision"] = "TBD"

    with pytest.raises(ContractValidationError, match="占位文本"):
        validate_contract_bundle(contract, registry, test_map)


def test_default_bundle_freezes_observable_token_boundaries():
    bundle = load_contract_bundle()
    phases = bundle["contract"]["phase_boundaries"]

    assert phases["prefill"]["start"] == "request.start"
    assert phases["prefill"]["end"] == "token[0].host_readable"
    assert phases["decode"]["start"] == "token[0].host_readable"
    assert phases["decode"]["empty_when_fixed_output_tokens"] == 1
    assert phases["full_request"]["end"] == "token[N-1].host_readable"


def test_natural_and_intervention_sync_have_disjoint_origins():
    bundle = load_contract_bundle()
    identities = bundle["contract"]["sync_identity"]["origins"]

    assert identities["natural_token_ready"]["study_role"] == "G1_NATURAL"
    assert identities["n1_intervention"]["study_role"] == "N1_INTERVENTION"
    assert identities["non_sync_marker"]["is_physical_sync"] is False


def test_pass0_and_pass1_share_completion_behavior():
    parity = load_contract_bundle()["contract"]["pass_parity"]

    assert parity["same_token_ready_operations"] is True
    assert parity["same_sync_operations"] is True
    assert parity["pass1_only_adds"] == ["NVTX_MARKERS", "NSIGHT_PROFILER"]


def test_registry_separates_blocking_syncs_from_dependency_edges():
    registry = load_contract_bundle()["registry"]
    classes = {rule["registry_rule_id"]: rule["universe_class"] for rule in registry["rules"]}

    assert classes["SYNC-STREAM-RUNTIME-001"] == "SUPPORTED_PHYSICAL_BLOCKING_SYNC"
    assert classes["EDGE-STREAM-WAIT-EVENT-001"] == "DEVICE_DEPENDENCY_EDGE"
    assert classes["EDGE-EVENT-RECORD-001"] == "DEVICE_DEPENDENCY_EDGE"
    assert classes["NON-SYNC-QUERY-001"] == "NON_BLOCKING_QUERY"


def test_default_bundle_keeps_completed_predecessors_and_rejects_overlap_dependency():
    rules = {
        rule["rule_id"]: rule for rule in load_contract_bundle()["contract"]["rules"]
    }

    assert rules["MC-S-008"]["decision"] == "completed_before_sync_remains_in_W"
    assert rules["MC-S-009"]["decision"] == "temporal_overlap_never_creates_dependency"


def test_submission_rule_uses_only_frozen_observable_ordering_evidence():
    submission = load_contract_bundle()["contract"]["s_layer"]["submission_proven"]

    assert submission["any_of"] == [
        "activity.gpu_start_ns < sync.host_start_ns",
        "enqueue.host_end_ns <= sync.host_start_ns",
    ]
    assert submission["overlapping_enqueue_without_started_activity"] == "AMBIGUOUS"


def test_terminal_selection_uses_frontier_before_timestamps():
    terminal = load_contract_bundle()["contract"]["s_layer"]["terminal"]

    assert terminal["candidate_source"] == "maximal_nodes_of_semantic_dependency_frontier"
    assert terminal["unique_frontier_policy"] == "SELECT_UNIQUE_FRONTIER_EVIDENCE"
    assert terminal["equal_latest_completion_policy"] == "AMBIGUOUS"
    assert terminal["tie_tolerance_ns"] == 0


def test_validity_states_keep_empty_ambiguous_and_invalid_distinct():
    validity = load_contract_bundle()["contract"]["s_layer"]["validity"]

    assert set(validity["states"]) == {
        "VALID_NONEMPTY",
        "VALID_EMPTY",
        "AMBIGUOUS",
        "INVALID",
    }
    assert validity["completed_before_sync_can_be_valid_empty"] is False
    assert validity["unknown_becomes_zero"] is False


def test_a_priority_is_conservative_and_complete_in_default_bundle():
    a = load_contract_bundle()["contract"]["a_layer"]

    assert a["priority"] == [
        "A_unattributed",
        "A_device_wait",
        "A_sync_residual",
        "A_cuda_api",
        "A_host_path",
    ]
    assert set(a["priority"]) == set(a["top_level_categories"])
    assert a["valid_empty_sync_category"] == "A_sync_residual"
    assert a["ambiguous_invalid_sync_category"] == "A_unattributed"


def test_b_is_per_sync_and_return_tail_stays_inside_sync_window():
    b = load_contract_bundle()["contract"]["b_layer"]

    assert b["aggregation_policy"] == "NO_CROSS_SYNC_SUM"
    assert b["enters_a_wall_clock_budget"] is False
    assert b["metrics"]["sync_return_tail_ns"]["formula"] == (
        "max(0, sync.end_ns - max(sync.start_ns, terminal.end_ns))"
    )


def test_d_and_signature_are_only_derived_views():
    derived = load_contract_bundle()["contract"]["derived"]

    assert derived["D_margin"]["formula"] == (
        "A_device_wait_ns-A_host_path_ns-A_cuda_api_ns"
    )
    assert derived["D_score"]["zero_denominator_result"] is None
    assert derived["Exposure_Signature"]["creates_new_wall_clock_budget"] is False


def test_nonzero_semantic_tolerance_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    contract["time_model"] = {
        "semantic_ordering_tolerance_ns": 1,
        "terminal_tie_tolerance_ns": 0,
    }

    with pytest.raises(ContractValidationError, match="语义时间容差"):
        validate_contract_bundle(contract, registry, test_map)


def test_invalid_validity_state_set_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    contract["s_layer"] = {
        "validity": {"states": ["VALID_NONEMPTY", "INVALID"]},
        "reason_priority": [],
    }

    with pytest.raises(ContractValidationError, match="validity 状态"):
        validate_contract_bundle(contract, registry, test_map)


def test_cross_sync_b_aggregation_is_rejected():
    contract, registry, test_map = valid_literal_bundle()
    contract["b_layer"]["aggregation_policy"] = "SUM_ALL_SYNCS"

    with pytest.raises(ContractValidationError, match="B 层"):
        validate_contract_bundle(contract, registry, test_map)
