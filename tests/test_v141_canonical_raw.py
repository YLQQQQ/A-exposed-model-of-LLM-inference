"""Canonical Raw v0.2 数据合同与转换测试。"""

from __future__ import annotations

from copy import deepcopy

import pytest

from exposedpath_v141.canonical_raw import (
    CanonicalRawSchemaError,
    load_canonical_raw_schema,
    validate_canonical_raw_schema,
)


def test_committed_canonical_raw_schema_is_valid():
    validate_canonical_raw_schema(load_canonical_raw_schema())


def test_all_required_record_kinds_are_frozen():
    schema = load_canonical_raw_schema()

    assert set(schema["record_types"]) == {
        "nvtx",
        "cuda_api",
        "physical_sync",
        "device_activity",
        "cuda_event",
        "context",
        "stream",
        "diagnostic",
    }


def test_missing_record_kind_is_rejected():
    schema = deepcopy(load_canonical_raw_schema())
    del schema["record_types"]["physical_sync"]

    with pytest.raises(CanonicalRawSchemaError, match="record kind"):
        validate_canonical_raw_schema(schema)


def test_duplicate_or_overlapping_fields_are_rejected():
    schema = deepcopy(load_canonical_raw_schema())
    schema["record_types"]["nvtx"]["required_fields"].append("record_id")

    with pytest.raises(CanonicalRawSchemaError, match="字段重复"):
        validate_canonical_raw_schema(schema)

    schema = deepcopy(load_canonical_raw_schema())
    schema["record_types"]["nvtx"]["nullable_fields"].append("record_id")

    with pytest.raises(CanonicalRawSchemaError, match="同时属于"):
        validate_canonical_raw_schema(schema)


@pytest.mark.parametrize(
    "forbidden",
    ["wait_set_activity_ids", "terminal", "A_device_wait_ns", "B_status"],
)
def test_raw_schema_rejects_s_or_accounting_fields(forbidden):
    schema = deepcopy(load_canonical_raw_schema())
    schema["record_types"]["physical_sync"]["nullable_fields"].append(forbidden)

    with pytest.raises(CanonicalRawSchemaError, match="越层字段"):
        validate_canonical_raw_schema(schema)


def test_clock_and_source_identity_are_explicit():
    schema = load_canonical_raw_schema()

    assert schema["clock_model"] == {
        "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
        "unit": "ns",
        "comparison_scope": "SINGLE_SOURCE_TRACE_ONLY",
        "timestamp_normalization": "DISABLED",
    }
    assert schema["record_identity"]["tuple"] == [
        "source_sqlite_sha256",
        "source_table",
        "source_rowid",
    ]


def test_source_adapter_is_locked_to_reviewed_nsys_schema():
    schema = load_canonical_raw_schema()

    assert schema["source_adapters"] == [
        {
            "adapter_id": "NSYS-SQLITE-2026.1.1-3.24.14",
            "export_product_version": "2026.1.1.204",
            "export_schema_version": "3.24.14",
        }
    ]
