"""Measurement Contract v0.2 的机器可检查不变量。"""

from __future__ import annotations

from copy import deepcopy

import pytest

from exposedpath_v141.contract import ContractValidationError, validate_contract_bundle


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
