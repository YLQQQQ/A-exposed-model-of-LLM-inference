"""Versioned integrity evidence inlet. No affirmative Nsight provider exists yet."""
from exposedpath.gate8_identity import validate_shape


def nsys_unknown_receipts(**scope):
    """Preserve the unresolved provider, even when export exits zero."""
    result = [{
        "schema_version":"exposedpath-observation-integrity/0.1.0", **scope,
        "clock_domain_id":"NSYS_TRACE_RELATIVE_NS", "channel":channel,
        "status":"UNKNOWN", "dropped_count":None, "basis":"UNAVAILABLE",
        "finalized":False, "coverage_complete":False, "evidence_refs":[],
        "reasons":["NSYS_FULL_SESSION_AFFIRMATIVE_PROVIDER_NOT_ESTABLISHED"],
    } for channel in ("CUDA_ACTIVITY","NVTX")]
    for receipt in result:
        validate_shape("integrity", receipt)
    return result


def assess_integrity(receipts, *, expected):
    """Validate source/scope and state consistency, NOT collector authenticity.

    EVIDENCE_SHAPE_CONFIRMED is intentionally not PASS. A future version-bound
    collector provider must authenticate counters/attestations before real use.
    """
    seen = set()
    reasons = []
    for r in receipts:
        validate_shape("integrity", r)
        if r["channel"] in seen:
            raise ValueError("OBSERVATION_INTEGRITY_CONFLICT: duplicate channel")
        seen.add(r["channel"])
        for k in ("capture_session_id","source_raw_sha256","pass_identity_sha256","scope_pid","collector_version"):
            if r[k] != expected[k]:
                raise ValueError(f"SOURCE_HASH_MISMATCH: integrity {k}")
        if (r["scope_start_ns"] > expected["scope_start_ns"]
                or r["scope_end_ns"] < expected["scope_end_ns"]
                or r["scope_start_ns"] > r["scope_end_ns"]):
            raise ValueError("OBSERVATION_INTEGRITY_CONFLICT: incomplete scope")
        if r["status"] == "UNKNOWN":
            reasons.append("OBSERVATION_INTEGRITY_UNKNOWN")
        elif r["status"] == "NONZERO":
            reasons.append("OBSERVATION_LOSS_CONFIRMED")
        elif r["status"] == "CONFLICT":
            if r["basis"] != "CONFLICTING_EVIDENCE" or not r["reasons"]:
                raise ValueError("OBSERVATION_INTEGRITY_CONFLICT: missing conflict basis")
            reasons.append("OBSERVATION_INTEGRITY_CONFLICT")
    if seen != {"CUDA_ACTIVITY","NVTX"}:
        reasons.append("OBSERVATION_INTEGRITY_UNKNOWN")
    return {"status":"BLOCKED" if reasons else "EVIDENCE_SHAPE_CONFIRMED",
            "reasons":sorted(set(reasons)), "provider_authenticated":False}
