"""Gate 5 A/B 与纯派生层 JSON Schema 合同测试。"""

from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError


ROOT = Path(__file__).resolve().parents[1]
AB_SCHEMA_PATH = ROOT / "docs" / "v1_4_1" / "contracts" / "ab_schema_v0_2.json"
DERIVED_SCHEMA_PATH = (
    ROOT / "docs" / "v1_4_1" / "contracts" / "derived_schema_v0_2.json"
)
CONTRACT_PATH = (
    ROOT / "docs" / "v1_4_1" / "contracts" / "measurement_contract_v0_2.json"
)


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(schema: dict, instance: dict) -> None:
    Draft202012Validator(schema).validate(instance)


def _file_record(filename: str, record_count: int) -> dict:
    return {
        "filename": filename,
        "record_count": record_count,
        "sha256": "A" * 64,
        "size_bytes": 128,
    }


def _ab_manifest() -> dict:
    return {
        "schema_version": "exposedpath-ab/0.2.0",
        "measurement_contract_version": "exposedpath-measurement-contract-0.2.0",
        "canonical_schema_version": "exposedpath-canonical-raw/0.2.0",
        "s_schema_version": "exposedpath-s-layer/0.2.0",
        "analyzer_version": "0.2.0-test",
        "generated_at_utc": "2026-09-12T00:00:00+00:00",
        "data_role": "Engineering",
        "source": {
            "canonical_manifest_name": "canonical_manifest.json",
            "canonical_manifest_sha256": "B" * 64,
            "s_manifest_name": "s_manifest.json",
            "s_manifest_sha256": "C" * 64,
            "source_sqlite_sha256": "D" * 64,
            "sync_registry": {
                "version": "exposedpath-sync-registry-0.2.0",
                "sha256": "E" * 64,
            },
        },
        "files": {
            "a_window_records": _file_record("a_window_records.jsonl.gz", 1),
            "b_sync_records": _file_record("b_sync_records.jsonl.gz", 1),
        },
        "quality": {"status": "VALID", "reasons": []},
        "summary": {
            "window_count": 1,
            "physical_sync_count": 1,
            "b_valid_count": 1,
            "b_not_applicable_count": 0,
            "b_ambiguous_count": 0,
            "b_invalid_count": 0,
        },
        "research_eligibility": {
            "formal_evidence": False,
            "q0_status": "NOT_RUN",
            "scope": "A_B_LAYER_ONLY",
        },
    }


def _a_window_record() -> dict:
    return {
        "window_id": "window:request-1:prefill",
        "experiment_id": "experiment-1",
        "wmpc_id": "wmpc-1",
        "run_id": "run-1",
        "run_role": "PASS1",
        "pass_id": "pass-1",
        "request_id": "request-1",
        "repeat_id": "repeat-1",
        "phase": "prefill",
        "window_start_ns": 0,
        "window_end_ns": 100,
        "T_window_ns": 100,
        "A_host_path_ns": 20,
        "A_cuda_api_ns": 10,
        "A_device_wait_ns": 40,
        "A_sync_residual_ns": 20,
        "A_unattributed_ns": 10,
        "A_cuda_api_submit_ns": 8,
        "A_cuda_api_non_submit_ns": 2,
        "A_device_wait_kernel_only_ns": 25,
        "A_device_wait_memop_only_ns": 5,
        "A_device_wait_kernel_memop_mixed_ns": 10,
        "top_level_conservation_error_ns": 0,
        "top_level_overlap_ns": 0,
        "top_level_uncovered_ns": 0,
        "out_of_window_ns": 0,
        "cuda_api_subcategory_conservation_error_ns": 0,
        "device_wait_subcategory_conservation_error_ns": 0,
        "primary_reason": None,
        "secondary_reasons": [],
    }


def _terminal() -> dict:
    return {
        "status": "VALID",
        "kind": "ACTIVITY",
        "activity_id": "device_activity:CUPTI_ACTIVITY_KIND_KERNEL:1",
        "end_ns": 90,
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
    }


def _b_sync_record(validity: str = "B_VALID") -> dict:
    timing = 0 if validity == "B_VALID" else None
    terminal = _terminal()
    if validity != "B_VALID":
        terminal = {
            "status": {
                "B_NOT_APPLICABLE": "NOT_APPLICABLE",
                "B_AMBIGUOUS": "AMBIGUOUS",
                "B_INVALID": "INVALID",
            }[validity],
            "kind": "NONE",
            "activity_id": None,
            "end_ns": None,
            "clock_domain_id": None,
        }
    return {
        "sync_id": "cuda_sync:CUPTI_ACTIVITY_KIND_SYNCHRONIZATION:1",
        "registry_rule_id": "SYNC-STREAM-RUNTIME-001",
        "sync_kind": "STREAM",
        "sync_origin": "natural_token_ready",
        "callsite_id": "token-ready",
        "request_id": "request-1",
        "repeat_id": "repeat-1",
        "sync_owner_phase": "prefill",
        "activity_origin_phases": ["prefill"],
        "terminal_origin_phase": "prefill" if validity == "B_VALID" else None,
        "cross_phase_dependency": False,
        "sync_start_ns": 50,
        "sync_end_ns": 100,
        "wait_set_activity_ids": (
            ["device_activity:CUPTI_ACTIVITY_KIND_KERNEL:1"]
            if validity == "B_VALID"
            else []
        ),
        "wait_set_hidden_union_ns": timing,
        "wait_set_exposed_union_ns": timing,
        "terminal": terminal,
        "terminal_pre_sync_ns": timing,
        "terminal_overlap_sync_ns": timing,
        "sync_return_tail_ns": timing,
        "validity": validity,
        "primary_reason": {
            "B_AMBIGUOUS": "TERMINAL_TIE",
            "B_INVALID": "MISSING_EVENT_RECORD",
        }.get(validity),
        "secondary_reasons": [],
    }


def _derived_manifest() -> dict:
    return {
        "schema_version": "exposedpath-derived/0.2.0",
        "measurement_contract_version": "exposedpath-measurement-contract-0.2.0",
        "input_schema_version": "exposedpath-ab/0.2.0",
        "analyzer_version": "0.2.0-test",
        "generated_at_utc": "2026-09-12T00:00:00+00:00",
        "data_role": "Engineering",
        "source": {
            "ab_manifest_name": "ab_manifest.json",
            "ab_manifest_sha256": "F" * 64,
            "a_window_records_sha256": "A" * 64,
            "b_sync_records_sha256": "B" * 64,
        },
        "files": {
            "d_window_records": _file_record("d_window_records.jsonl.gz", 1),
            "exposure_signature_records": _file_record(
                "exposure_signature_records.jsonl.gz", 1
            ),
        },
        "summary": {"d_window_count": 1, "exposure_signature_count": 1},
        "research_eligibility": {
            "formal_evidence": False,
            "q0_status": "NOT_RUN",
            "scope": "DERIVED_FROM_A_B_ONLY",
        },
    }


def _window_identity() -> dict:
    return {
        "window_id": "window:request-1:prefill",
        "experiment_id": "experiment-1",
        "wmpc_id": "wmpc-1",
        "run_id": "run-1",
        "run_role": "PASS1",
        "pass_id": "pass-1",
        "request_id": "request-1",
        "repeat_id": "repeat-1",
        "phase": "prefill",
    }


def _d_window_record() -> dict:
    return {
        **_window_identity(),
        "D_margin_ns": 10,
        "D_score": 10 / 70,
    }


def _timing_summary(median: float | None, p90: int | None) -> dict:
    return {"median": median, "p90": p90}


def _timing_distribution(value: int | None, count: int) -> list[dict]:
    return [{"value_ns": value, "count": count}]


def _exposure_signature_record() -> dict:
    a_fields = {
        "A_host_path_ns": 20,
        "A_cuda_api_ns": 10,
        "A_device_wait_ns": 40,
        "A_sync_residual_ns": 20,
        "A_unattributed_ns": 10,
        "A_cuda_api_submit_ns": 8,
        "A_cuda_api_non_submit_ns": 2,
        "A_device_wait_kernel_only_ns": 25,
        "A_device_wait_memop_only_ns": 5,
        "A_device_wait_kernel_memop_mixed_ns": 10,
    }
    ratio_fields = {
        key.removesuffix("_ns") + "_ratio": value / 100
        for key, value in a_fields.items()
    }
    metric_fields = [
        "wait_set_hidden_union_ns",
        "wait_set_exposed_union_ns",
        "terminal_pre_sync_ns",
        "terminal_overlap_sync_ns",
        "sync_return_tail_ns",
    ]
    return {
        **_window_identity(),
        "A_vector_ns": a_fields,
        "A_window_ratios": ratio_fields,
        "b_groups": [
            {
                "phase": "prefill",
                "sync_kind": "STREAM",
                "sync_origin": "natural_token_ready",
                "callsite_id": "token-ready",
                "status_counts": {
                    "B_VALID": 1,
                    "B_NOT_APPLICABLE": 0,
                    "B_AMBIGUOUS": 0,
                    "B_INVALID": 0,
                },
                "valid_timing_statistics_ns": {
                    field: _timing_summary(0, 0) for field in metric_fields
                },
                "valid_timing_distributions_ns": {
                    field: _timing_distribution(0, 1) for field in metric_fields
                },
                "terminal_kind_counts": [
                    {"terminal_kind": "ACTIVITY", "count": 1}
                ],
            }
        ],
    }


def test_committed_schemas_are_draft_2020_12_and_freeze_expected_defs():
    ab_schema = _load(AB_SCHEMA_PATH)
    derived_schema = _load(DERIVED_SCHEMA_PATH)

    Draft202012Validator.check_schema(ab_schema)
    Draft202012Validator.check_schema(derived_schema)
    assert ab_schema["$id"] == (
        "https://exposedpath.dev/schemas/ab_schema_v0_2.json"
    )
    assert ab_schema["schema_version"] == "exposedpath-ab/0.2.0"
    assert set(ab_schema["$defs"]) == {"manifest", "a_window_record", "b_sync_record"}
    assert derived_schema["$id"] == (
        "https://exposedpath.dev/schemas/derived_schema_v0_2.json"
    )
    assert derived_schema["schema_version"] == "exposedpath-derived/0.2.0"
    assert set(derived_schema["$defs"]) == {
        "manifest",
        "d_window_record",
        "exposure_signature_record",
    }
    for schema in (ab_schema, derived_schema):
        for definition in schema["$defs"].values():
            assert definition["required"]
            assert definition["additionalProperties"] is False


def test_ab_schema_accepts_manifest_a_window_and_each_b_state():
    schema = _load(AB_SCHEMA_PATH)

    _validate(schema, _ab_manifest())
    _validate(schema, _a_window_record())
    for validity in (
        "B_VALID",
        "B_NOT_APPLICABLE",
        "B_AMBIGUOUS",
        "B_INVALID",
    ):
        _validate(schema, _b_sync_record(validity))


def test_b_record_uses_exact_measurement_contract_fields():
    schema = _load(AB_SCHEMA_PATH)
    contract = _load(CONTRACT_PATH)

    assert set(schema["$defs"]["b_sync_record"]["properties"]) == set(
        contract["b_layer"]["output_fields"]
    )


def test_a_record_rejects_nonzero_conservation_error():
    schema = _load(AB_SCHEMA_PATH)
    record = _a_window_record()
    record["top_level_conservation_error_ns"] = 1

    with pytest.raises(ValidationError):
        _validate(schema, record)


@pytest.mark.parametrize(
    "validity", ["B_NOT_APPLICABLE", "B_AMBIGUOUS", "B_INVALID"]
)
@pytest.mark.parametrize(
    "timing_field",
    [
        "wait_set_hidden_union_ns",
        "wait_set_exposed_union_ns",
        "terminal_pre_sync_ns",
        "terminal_overlap_sync_ns",
        "sync_return_tail_ns",
    ],
)
def test_non_valid_b_record_rejects_zero_filled_timing(validity, timing_field):
    schema = _load(AB_SCHEMA_PATH)
    record = _b_sync_record(validity)
    record[timing_field] = 0

    with pytest.raises(ValidationError):
        _validate(schema, record)


def test_b_record_rejects_cross_sync_aggregate_field():
    schema = _load(AB_SCHEMA_PATH)
    record = _b_sync_record()
    record["wait_set_exposed_total_ns"] = 0

    with pytest.raises(ValidationError):
        _validate(schema, record)


def test_derived_schema_accepts_manifest_d_window_and_signature():
    schema = _load(DERIVED_SCHEMA_PATH)

    _validate(schema, _derived_manifest())
    _validate(schema, _d_window_record())
    _validate(schema, _exposure_signature_record())


def test_derived_manifest_rejects_missing_ab_input_lineage():
    schema = _load(DERIVED_SCHEMA_PATH)
    manifest = deepcopy(_derived_manifest())
    del manifest["source"]["ab_manifest_sha256"]

    with pytest.raises(ValidationError):
        _validate(schema, manifest)
