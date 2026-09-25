"""D2 exact call-weighted diagnostics; never an exposure or B sum.

The arithmetic function expects a verified candidate universe and a separately
established denominator status. It cannot establish collector completeness.
"""
import json
from pathlib import Path
import re

from jsonschema import Draft202012Validator

_SCHEMA = json.loads((Path(__file__).resolve().parents[1] / "docs/v1_4_1/contracts/gate8/coverage_reporting_schema_v0_1.json").read_text(encoding="utf-8"))
_S = {"VALID_NONEMPTY", "VALID_EMPTY", "INVALID", "AMBIGUOUS"}
_B = {"B_VALID", "B_NOT_APPLICABLE", "B_INVALID", "B_AMBIGUOUS"}


def _unique(rows):
    result = {}
    for row in rows:
        key = row.get("sync_id")
        if not isinstance(key, str) or not key or (key in result and result[key] != row):
            raise ValueError("COVERAGE_INPUT_INVALID: duplicate/conflicting physical reference")
        result[key] = row
    return result


def calculate_window_coverage(*, window, physical_calls, s_records, b_records,
                              source_sqlite_sha256, lineage, denominator_status):
    if denominator_status not in {"COMPLETE", "INCOMPLETE", "UNKNOWN"} or not re.fullmatch("[0-9a-f]{64}", source_sqlite_sha256):
        raise ValueError("COVERAGE_INPUT_INVALID: status/source identity")
    calls, ss, bs = map(_unique, (physical_calls, s_records, b_records))
    if set(calls) != set(ss) or set(calls) != set(bs):
        raise ValueError("COVERAGE_INPUT_INVALID: physical/S/B join must be complete")
    a,b = window["start_ns"], window["end_ns"]
    if type(a) is not int or type(b) is not int or a > b or window["clock_domain_id"] != "NSYS_TRACE_RELATIVE_NS":
        raise ValueError("COVERAGE_INPUT_INVALID: window/clock")
    members = []
    reasons = []
    observed = 0
    for key,c in sorted(calls.items()):
        s, provenance = ss[key], bs[key]
        if s.get("validity") not in _S or provenance.get("validity") not in _B:
            raise ValueError("COVERAGE_INPUT_INVALID: unknown validity")
        supported = s["validity"] in {"VALID_NONEMPTY", "VALID_EMPTY"}
        valid = provenance["validity"] == "B_VALID"
        if valid and (not supported or s["validity"] == "VALID_EMPTY"):
            raise ValueError("COVERAGE_INPUT_INVALID: B-valid is not supported nonempty")
        x,y = c.get("host_start_ns"), c.get("host_end_ns")
        if x is None or y is None or c.get("clock_domain_id") is None:
            denominator_status = "INCOMPLETE"
            reasons.append("PHYSICAL_CALL_TIME_UNKNOWN")
            observed += 1
            continue
        if type(x) is not int or type(y) is not int or x > y or c["clock_domain_id"] != window["clock_domain_id"]:
            raise ValueError("COVERAGE_INPUT_INVALID: call time/clock")
        intersects = a < b and (max(a,x) < min(b,y) if x < y else a <= x < b)
        if not intersects:
            continue
        observed += 1
        if s.get("request_id") is None or s.get("repeat_id") is None:
            denominator_status = "INCOMPLETE"
            reasons.append("PHYSICAL_CALL_OWNERSHIP_UNKNOWN")
            continue
        if any(s[k] != window["identity"][k] for k in ("request_id", "repeat_id")):
            # Another proven owner does not become this request merely by overlap.
            continue
        members.append({
            "physical_sync_uid": f"{source_sqlite_sha256}:{key}",
            "s_record_ref": {"sha256":lineage["s_manifest_sha256"], "selector": f"sync_id={key}"},
            "b_record_ref": {"sha256":lineage["ab_manifest_sha256"], "selector": f"sync_id={key}"},
            "clipped_duration_ns": max(0,min(b,y)-max(a,x)), "supported": supported, "b_valid": valid,
        })
    unknown = denominator_status != "COMPLETE"
    p = [m for m in members if m["supported"]]
    v = [m for m in members if m["b_valid"]]
    duration = lambda rows: sum(m["clipped_duration_ns"] for m in rows)

    def ratio(n,d):
        return {"status": "UNKNOWN" if unknown else ("VALID" if d else "NOT_APPLICABLE"),
                "numerator": None if unknown else n, "denominator": None if unknown else d}

    result = {
        "schema_version":"exposedpath-sync-call-coverage/0.1.0", "data_role":"Engineering",
        **lineage, "denominator_status":denominator_status,
        "members":None if unknown else members, "observed_unique_count":observed,
        "supported_count_coverage":ratio(len(p),len(members)),
        "supported_duration_coverage":ratio(duration(p),duration(members)),
        "b_valid_count_coverage":ratio(len(v),len(p)),
        "b_valid_duration_coverage":ratio(duration(v),duration(p)),
        "reasons":sorted(set(reasons or (["COMPLETENESS_NOT_ESTABLISHED"] if unknown else []))),
        "duration_interpretation":"PHYSICAL_CALL_CLIPPED_DURATION_NOT_REQUEST_EXPOSURE",
    }
    Draft202012Validator(_SCHEMA).validate(result)
    return result


def coverage_from_inputs(inputs, window, b_records, *, lineage, denominator_status):
    """Use the same registry candidate universe already verified by S/A/B."""
    from .a_accounting import _api_category
    from .sync_semantics import classify_cuda_api
    by_correlation = {}
    for api in inputs.canonical.records["cuda_api"]:
        by_correlation.setdefault(api.get("correlation_id"), []).append(api)
    activity_correlations = {r.get("correlation_id") for r in inputs.canonical.records["device_activity"]}
    for api in inputs.canonical.records["cuda_api"]:
        if (classify_cuda_api(api.get("api_name", ""))["role"] == "UNCLASSIFIED"
                and _api_category(api, by_correlation, activity_correlations) is None):
            start, end = api.get("start_ns"), api.get("end_ns")
            if start is None or end is None or max(start,window.start_ns) < min(end,window.end_ns):
                denominator_status = "INCOMPLETE"
    calls = [{"sync_id": c.sync_id, "host_start_ns":c.host_start_ns,
              "host_end_ns":c.host_end_ns, "clock_domain_id":c.clock_domain_id}
             for c in inputs.canonical.semantic_sync_by_id.values()]
    return calculate_window_coverage(
        window={"start_ns":window.start_ns, "end_ns":window.end_ns,
                "clock_domain_id":"NSYS_TRACE_RELATIVE_NS",
                "identity":{"request_id":window.request_id, "repeat_id":window.repeat_id}},
        physical_calls=calls, s_records=inputs.s_records, b_records=b_records,
        source_sqlite_sha256=inputs.canonical.manifest["source"]["sqlite"]["sha256"].lower(),
        lineage=lineage, denominator_status=denominator_status,
    )
