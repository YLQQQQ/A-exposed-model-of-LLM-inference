"""Affirmative evidence checks are distinct from successful export/schema."""
from copy import deepcopy
import importlib
import importlib.util

import pytest


def module():
    assert importlib.util.find_spec("exposedpath_v141.gate8_integrity"), "integrity gate missing"
    return importlib.import_module("exposedpath_v141.gate8_integrity")


def facts():
    return dict(capture_session_id="capture", source_raw_sha256="a"*64,
                pass_identity_sha256="b"*64, scope_pid=3, scope_start_ns=100,
                scope_end_ns=600, collector_version="2026.2.1.210")


def receipts(status="ZERO_CONFIRMED"):
    return [{"schema_version":"exposedpath-observation-integrity/0.1.0", **facts(),
             "clock_domain_id":"NSYS_TRACE_RELATIVE_NS", "channel":channel,
             "status":status, "dropped_count":0, "basis":"COLLECTOR_COUNTER",
             "finalized":True, "coverage_complete":True,
             "evidence_refs":[{"sha256":"c"*64,"selector":"full_session_counter"}], "reasons":[]}
            for channel in ("CUDA_ACTIVITY","NVTX")]


def test_nsys_no_warning_or_exit_zero_cannot_create_zero_receipt():
    r = module().nsys_unknown_receipts(**facts())
    assert {x["status"] for x in r} == {"UNKNOWN"}
    assert all(x["dropped_count"] is None for x in r)
    assert module().assess_integrity(r, expected=facts())["status"] == "BLOCKED"


def test_both_channels_need_affirmative_complete_scope():
    gate = module().assess_integrity
    assert gate(receipts(), expected=facts())["status"] == "EVIDENCE_SHAPE_CONFIRMED"
    assert gate(receipts()[:1], expected=facts())["status"] == "BLOCKED"
    r = receipts()
    r[0].update(status="UNKNOWN", dropped_count=None, basis="UNAVAILABLE", reasons=["counter unavailable"])
    assert gate(r, expected=facts())["status"] == "BLOCKED"


@pytest.mark.parametrize("field,value", [("finalized",False), ("coverage_complete",False),
    ("evidence_refs",[]), ("scope_pid",4), ("source_raw_sha256","d"*64),
    ("scope_start_ns",101), ("capture_session_id","other")])
def test_false_zero_and_wrong_source_rejected(field,value):
    r = receipts()
    r[0][field] = value
    with pytest.raises(ValueError):
        module().assess_integrity(r, expected=facts())


def test_nonzero_and_conflict_preserved_not_unknown_zero():
    r = receipts()
    r[0].update(status="NONZERO", dropped_count=2)
    assert "OBSERVATION_LOSS_CONFIRMED" in module().assess_integrity(r, expected=facts())["reasons"]
    r[0].update(status="CONFLICT", dropped_count=None, basis="CONFLICTING_EVIDENCE", reasons=["counter conflict"])
    assert "OBSERVATION_INTEGRITY_CONFLICT" in module().assess_integrity(r, expected=facts())["reasons"]


def test_attestation_does_not_fabricate_numeric_zero():
    r = receipts()
    r[0].update(basis="COLLECTOR_ATTESTATION", dropped_count=None)
    assert module().assess_integrity(r, expected=facts())["status"] == "EVIDENCE_SHAPE_CONFIRMED"
