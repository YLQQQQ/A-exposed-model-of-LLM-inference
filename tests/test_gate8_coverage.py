"""D2 hand-calculated expectations, independent of production arithmetic."""
from copy import deepcopy
import importlib
import importlib.util

import pytest


def calculator():
    assert importlib.util.find_spec("exposedpath_v141.gate8_coverage"), "D2 reporter missing"
    return importlib.import_module("exposedpath_v141.gate8_coverage").calculate_window_coverage


def inputs():
    calls = [{"sync_id": key, "host_start_ns": a, "host_end_ns": b,
              "clock_domain_id": "NSYS_TRACE_RELATIVE_NS"}
             for key, a, b in (("a",120,200), ("b",160,220), ("c",250,250), ("d",240,290))]
    s = [{"sync_id": key, "request_id": "r", "repeat_id": "0", "validity": status}
         for key, status in (("a","VALID_NONEMPTY"), ("b","INVALID"), ("c","VALID_EMPTY"), ("d","VALID_NONEMPTY"))]
    b = [{"sync_id": key, "validity": status} for key, status in
         (("a","B_VALID"), ("b","B_INVALID"), ("c","B_NOT_APPLICABLE"), ("d","B_VALID"))]
    return calls, s, b


def report(window=(100,300), *, calls=None, s=None, b=None, status="COMPLETE"):
    defaults = inputs()
    return calculator()(
        window={"start_ns": window[0], "end_ns": window[1], "clock_domain_id": "NSYS_TRACE_RELATIVE_NS",
                "identity": {"request_id": "r", "repeat_id": "0"}},
        physical_calls=defaults[0] if calls is None else calls,
        s_records=defaults[1] if s is None else s, b_records=defaults[2] if b is None else b,
        denominator_status=status, source_sqlite_sha256="a"*64,
        lineage={"window_ref": {"sha256": "b"*64, "selector": "$.projections[0]"},
                 **{k:"c"*64 for k in ("canonical_manifest_sha256", "s_manifest_sha256", "ab_manifest_sha256", "integrity_artifact_sha256")}},
    )


@pytest.mark.parametrize("window,expected", [
    ((100,300), ((3,4),(130,190),(2,3),(130,130))),
    ((100,180), ((1,2),(60,80),(1,1),(60,60))),
    ((180,300), ((3,4),(70,110),(2,3),(70,70))),
])
def test_hand_computed_d2_cross_phase_call_weighting(window, expected):
    r = report(window)
    for field, pair in zip(("supported_count_coverage","supported_duration_coverage",
                            "b_valid_count_coverage","b_valid_duration_coverage"), expected):
        assert r[field] == {"status":"VALID", "numerator":pair[0], "denominator":pair[1]}


def test_duplicate_physical_reference_is_once_conflict_rejected():
    calls,s,b = inputs()
    calls.append(deepcopy(calls[0]))
    assert report(calls=calls) == report()
    calls[-1]["host_end_ns"] += 1
    with pytest.raises(ValueError, match="COVERAGE_INPUT_INVALID"):
        report(calls=calls)


@pytest.mark.parametrize("status", ["UNKNOWN", "INCOMPLETE"])
def test_unknown_never_becomes_zero_or_empty_members(status):
    r = report(status=status)
    assert r["members"] is None
    assert r["observed_unique_count"] == 4
    assert r["supported_count_coverage"] == {"status":"UNKNOWN", "numerator":None, "denominator":None}


def test_empty_and_zero_duration_have_different_count_denominators():
    empty = report((180,180))
    assert empty["members"] == []
    assert empty["supported_count_coverage"] == {"status":"NOT_APPLICABLE", "numerator":0, "denominator":0}
    calls,s,b = inputs()
    zero = report(calls=[calls[2]],s=[s[2]],b=[b[2]])
    assert zero["supported_count_coverage"]["denominator"] == 1
    assert zero["b_valid_count_coverage"]["numerator"] == 0
    assert zero["supported_duration_coverage"]["status"] == "NOT_APPLICABLE"


def test_b_valid_must_be_supported_and_missing_b_never_filled():
    calls,s,b = inputs()
    b[1]["validity"] = "B_VALID"
    with pytest.raises(ValueError, match="COVERAGE_INPUT_INVALID"):
        report(b=b)
    with pytest.raises(ValueError, match="COVERAGE_INPUT_INVALID"):
        report(b=b[:1])


def test_unknown_owner_poisoning_cannot_be_filtered_away():
    calls,s,b = inputs()
    s[1]["request_id"] = None
    r = report(s=s)
    assert r["denominator_status"] == "INCOMPLETE"
    assert r["supported_duration_coverage"]["numerator"] is None


def test_different_overlapping_calls_are_not_union_exposure():
    calls,s,b = inputs()
    calls = calls[:2]
    for c in calls:
        c.update(host_start_ns=100, host_end_ns=300)
    r = report(calls=calls,s=s[:2],b=b[:2])
    assert r["supported_duration_coverage"] == {"status":"VALID", "numerator":200, "denominator":400}


def test_boundary_zero_call_belongs_only_to_right_phase():
    calls,s,b = inputs()
    c = dict(calls[2],host_start_ns=180,host_end_ns=180)
    assert report((100,180),calls=[c],s=[s[2]],b=[b[2]])["members"] == []
    assert len(report((180,300),calls=[c],s=[s[2]],b=[b[2]])["members"]) == 1


def test_invalid_known_call_stays_in_denominator_and_negative_duration_rejects():
    calls,s,b = inputs()
    r = report(calls=[calls[1]],s=[s[1]],b=[b[1]])
    assert r["supported_count_coverage"] == {"status":"VALID","numerator":0,"denominator":1}
    assert r["b_valid_count_coverage"]["status"] == "NOT_APPLICABLE"
    calls[1]["host_end_ns"] = 100
    with pytest.raises(ValueError, match="COVERAGE_INPUT_INVALID"):
        report(calls=calls)
