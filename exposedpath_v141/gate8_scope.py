"""D1: trace-native point -> independently versioned, source-bound projection.

No SQLite access, clock fitting, GPU dependency generation or Raw rewriting.
"""
from copy import deepcopy
import json
from pathlib import Path

from exposedpath.gate8_boundary import BOUNDARY_PREFIX
from exposedpath.gate8_identity import PROFILE, validate_pass_identity, validate_shape
from .gate8_adapter import digest


class ProjectedScope(dict):
    """Internal ownership view, never serialized as an observed NVTX record."""


def sidecar(root, ref):
    path = (root / ref["filename"]).resolve()
    if path.parent != root.resolve() or digest(path) != ref["sha256"]:
        raise ValueError("SOURCE_HASH_MISMATCH: Gate8 sidecar")
    return json.loads(path.read_text(encoding="utf-8"))


def derive_scopes(canonical_path, bundle, host_records, host_sha):
    manifest = bundle["manifest"]
    if manifest.get("observation_profile") != PROFILE:
        raise ValueError("PROFILE_VERSION_UNSUPPORTED")
    refs = manifest["gate8_sources"]
    ledger = sidecar(canonical_path.parent, refs["pass_identity"])
    validate_pass_identity(ledger, finalized=True)
    mapping = sidecar(canonical_path.parent, refs["device_mapping"])
    validate_shape("device_mapping", mapping)
    source_sha = manifest["source"]["sqlite"]["sha256"].lower()
    if (mapping["source_sqlite_sha256"] != source_sha
            or mapping["pid"] != ledger["pid"]
            or mapping["trace_device_id"] != manifest["execution_context"]["selected_device_id"]
            or ledger["device_mapping_sha256"] != refs["device_mapping"]["sha256"]
            or ledger["raw_artifact_sha256"] != manifest["source"]["raw"]["sha256"].lower()
            or ledger["requests"] != manifest["identity"]["requests"]):
        raise ValueError("SOURCE_HASH_MISMATCH: device/pass/Canonical lineage")
    host_by_id = {}
    for index, host in enumerate(host_records):
        validate_shape("boundary_payload", host["payload"])
        bid = host["payload"]["boundary_id"]
        if bid in host_by_id:
            raise ValueError("BOUNDARY_DUPLICATE: host ledger")
        host_by_id[bid] = (index, host)
    anchors = {}
    raw_by_id = {}
    for row in bundle["records"]["nvtx"]:
        if not row["text"].startswith(BOUNDARY_PREFIX):
            continue
        payload = json.loads(row["text"][len(BOUNDARY_PREFIX):])
        validate_shape("boundary_payload", payload)
        bid = payload["boundary_id"]
        if bid in anchors:
            raise ValueError("BOUNDARY_DUPLICATE: trace point")
        if bid not in host_by_id:
            raise ValueError("BOUNDARY_IDENTITY_CONFLICT: trace point absent from host ledger")
        index, host = host_by_id[bid]
        if payload != host["payload"] or row["process_id"] != ledger["pid"] or row["end_ns"] is not None:
            raise ValueError("BOUNDARY_IDENTITY_CONFLICT: payload/process/point")
        anchor = {
            "schema_version": "exposedpath-completion-anchor/0.1.0", "payload": payload,
            "raw_ref": {"source_sqlite_sha256": source_sha, **{k: row[k] for k in ("record_id", "source_table", "source_rowid")}},
            "trace_ns": row["start_ns"], "clock_domain_id": row["clock_domain_id"],
            "pid": row["process_id"], "tid": row["thread_id"],
            **{k: host[k] for k in ("host_observed_ns", "host_before_marker_ns", "host_after_marker_ns", "host_clock_id")},
            "producer_ledger_ref": {"sha256": host_sha, "selector": f"$[{index}]"},
        }
        validate_shape("anchor", anchor)
        if not anchor["host_observed_ns"] <= anchor["host_before_marker_ns"] <= anchor["host_after_marker_ns"]:
            raise ValueError("BOUNDARY_ORDER_INVALID: host diagnostics")
        anchors[bid] = anchor
        raw_by_id[bid] = row
    observed = [bid for r in ledger["requests"] for bid in r["observed_boundary_ids"]]
    if set(observed) != set(anchors) or set(observed) != set(host_by_id):
        raise ValueError("BOUNDARY_MISSING: ledger/trace bidirectional match")
    # The separate anchor artifact is content-addressed, not a circular scope hash.
    import hashlib
    anchor_list = [anchors[bid] for bid in sorted(anchors)]
    anchor_bytes = (json.dumps(anchor_list, sort_keys=True, separators=(",", ":")) + "\n").encode()
    anchor_sha = hashlib.sha256(anchor_bytes).hexdigest()
    projections = []
    intervals = []
    for request in ledger["requests"]:
        if request["request_role"] != "measured" or request["outcome"] != "COMPLETE":
            continue
        points = [anchors[bid] for bid in request["expected_boundary_ids"]]
        if any(p["payload"]["identity"] != request["identity"] for p in points):
            raise ValueError("BOUNDARY_IDENTITY_CONFLICT: request")
        if len({(p["pid"], p["tid"], p["clock_domain_id"]) for p in points}) != 1:
            raise ValueError("BOUNDARY_IDENTITY_CONFLICT: thread/clock")
        for ordinal, p in enumerate(points):
            expected_kind = "request_start" if ordinal == 0 else "token_ready"
            expected_token = None if ordinal == 0 else ordinal - 1
            if p["payload"]["boundary_kind"] != expected_kind or p["payload"]["token_index"] != expected_token:
                raise ValueError("BOUNDARY_ORDER_INVALID: point role/index")
        if any(a["trace_ns"] >= b["trace_ns"] for a, b in zip(points, points[1:])):
            raise ValueError("BOUNDARY_ORDER_INVALID: trace")
        intervals.append((points[0]["trace_ns"], points[-1]["trace_ns"]))
        for phase, a, b in (("full_request", points[0], points[-1]),
                            ("prefill", points[0], points[1]), ("decode", points[1], points[-1])):
            p = {
                "schema_version": "exposedpath-scope-projection/0.1.0",
                "identity": deepcopy(request["identity"]), "phase": phase,
                "start_boundary_id": a["payload"]["boundary_id"], "end_boundary_id": b["payload"]["boundary_id"],
                "start_ref": a["raw_ref"], "end_ref": b["raw_ref"],
                "start_ns": a["trace_ns"], "end_ns": b["trace_ns"], "clock_domain_id": a["clock_domain_id"],
                "canonical_manifest_sha256": digest(canonical_path), "anchor_artifact_sha256": anchor_sha,
                "pass_identity_sha256": refs["pass_identity"]["sha256"], "dependency_evidence": False,
            }
            validate_shape("projection", p)
            projections.append(p)
    intervals.sort()
    if any(a[1] > b[0] for a, b in zip(intervals, intervals[1:])):
        raise ValueError("BOUNDARY_IDENTITY_CONFLICT: overlapping requests")
    return {"schema_version": "exposedpath-gate8-scope-bundle/0.1.0", "observation_profile": PROFILE,
            "producer_ledger_sha256": host_sha, "producer_ledger": host_records,
            "anchors": anchor_list, "projections": projections}, anchor_bytes


def project_completion_scopes(canonical_path, host_ledger_path, output_path):
    from .sync_semantics import load_canonical_bundle
    canonical_path, host_ledger_path, output_path = map(Path, (canonical_path, host_ledger_path, output_path))
    if any(p.exists() for p in (output_path, output_path.with_suffix(".anchors.json"), output_path.with_suffix(".host.json"))):
        raise FileExistsError("refusing to overwrite scope/anchor evidence")
    bundle = load_canonical_bundle(canonical_path)
    result, anchor_bytes = derive_scopes(canonical_path, bundle,
                                       json.loads(host_ledger_path.read_text(encoding="utf-8")), digest(host_ledger_path))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.with_suffix(".anchors.json").open("xb") as handle:
        handle.write(anchor_bytes)
    with output_path.with_suffix(".host.json").open("xb") as handle:
        handle.write(host_ledger_path.read_bytes())
    with output_path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    return output_path


def load_projected_ownership(canonical_path, bundle, scope_path):
    """Re-derive and compare all scopes before lending them to S or A."""
    scope_path = Path(scope_path)
    saved = json.loads(scope_path.read_text(encoding="utf-8"))
    host_path = scope_path.with_suffix(".host.json")
    if digest(host_path) != saved["producer_ledger_sha256"] or json.loads(host_path.read_text(encoding="utf-8")) != saved["producer_ledger"]:
        raise ValueError("SOURCE_HASH_MISMATCH: host ledger")
    actual, anchor_bytes = derive_scopes(Path(canonical_path), bundle,
                                         saved["producer_ledger"], saved["producer_ledger_sha256"])
    if actual != saved or scope_path.with_suffix(".anchors.json").read_bytes() != anchor_bytes:
        raise ValueError("PROJECTION_REF_MISMATCH: scope/anchor derivation")
    original = bundle["records"]["nvtx"]
    projected = []
    by_id = {a["payload"]["boundary_id"]: a for a in actual["anchors"]}
    raw = {r["record_id"]: r for r in original}
    for index, p in enumerate(actual["projections"]):
        start = raw[by_id[p["start_boundary_id"]]["raw_ref"]["record_id"]]
        identity = {**p["identity"], "phase": p["phase"],
                    "kind": "request" if p["phase"] == "full_request" else "phase"}
        for r in original:
            i = r.get("structured_identity")
            if i and i.get("kind") in {"request", "phase"} and i.get("request_id") == identity["request_id"] and i.get("phase") == p["phase"]:
                if (r["start_ns"], r["end_ns"]) != (p["start_ns"], p["end_ns"]):
                    raise ValueError("PROJECTION_REF_MISMATCH: conflicting observed range")
        projected.append(ProjectedScope(
            record_id=f"projection:{digest(scope_path)}:{index}",
            source_kind="SCOPE_PROJECTION", projection=deepcopy(p),
            start_ns=p["start_ns"], end_ns=p["end_ns"], clock_domain_id=p["clock_domain_id"],
            global_tid=start["global_tid"], process_id=start["process_id"], thread_id=start["thread_id"],
            structured_identity=identity, text=None,
        ))
    # Keep all activity/sync markers, but never mix two range definitions.
    other = [r for r in original if (r.get("structured_identity") or {}).get("kind") not in {"request", "phase"}]
    return [*other, *projected], actual["projections"]


def build_projected_ab_inputs(canonical_path, scope_path):
    """Deterministic calculation inputs, NOT an integrity/qualification verdict.

    The Gate8 reporting entry point must gate these calculations on explicit
    integrity evidence. This low-level helper is also used by synthetic tests.
    """
    from .sync_semantics import load_canonical_bundle, build_semantic_inventory, analyze_sync_semantics, build_semantic_sync_candidates
    from .ab_inputs import CanonicalBundle, ABInputs, RequestPhaseWindow, _validate_s_join, _global_quality_reasons
    canonical_path, scope_path = Path(canonical_path), Path(scope_path)
    bundle = load_canonical_bundle(canonical_path)
    ownership, projections = load_projected_ownership(canonical_path, bundle, scope_path)
    # The default remains frozen A/B 0.2. Only an explicitly selected 0.3
    # time representation admits signed coordinates; never normalize clocks.
    from .time_representation import signed_time
    if not signed_time() and (any(p["start_ns"] < 0 or p["end_ns"] < 0 for p in projections)
            or any(isinstance(r.get(k), int) and r[k] < 0
                   for kind in ("device_activity", "cuda_sync")
                   for r in bundle["records"][kind] for k in ("start_ns", "end_ns"))):
        raise ValueError("GATE8_SIGNED_AB_ADAPTER_NOT_IMPLEMENTED: Raw/projection preserved; frozen A/B unchanged")
    inventory = build_semantic_inventory({**bundle, "ownership_records": ownership})
    s_records = tuple(analyze_sync_semantics(inventory, s) for s in inventory["syncs"])
    records = {k: tuple(v) for k, v in bundle["records"].items()}
    candidates = build_semantic_sync_candidates(records, ownership)
    canonical = CanonicalBundle(
        manifest=bundle["manifest"], records=records, schema=bundle["schema"],
        cuda_api_by_id={r["record_id"]: r for r in records["cuda_api"]},
        activity_by_id={r["record_id"]: r for r in records["device_activity"]},
        physical_sync_by_id={c.sync_id: c for c in candidates}, projected_ownership=tuple(ownership),
    )
    _validate_s_join(canonical, s_records)
    windows = tuple(RequestPhaseWindow(
        window_id=f"projection:{digest(scope_path)}:{i}",
        **{k: p["identity"][k] for k in ("experiment_id", "wmpc_id", "run_id", "run_role", "pass_id", "request_id", "repeat_id")},
        phase=p["phase"], start_ns=p["start_ns"], end_ns=p["end_ns"],
        nvtx_record_id=f"projection:{digest(scope_path)}:{i}",
    ) for i, p in enumerate(projections))
    return ABInputs(canonical=canonical, s_manifest={
        "observation_profile": PROFILE, "scope_sha256": digest(scope_path),
        "pass_identity_sha256": bundle["manifest"]["gate8_sources"]["pass_identity"]["sha256"],
        "qualification": "NOT_ASSESSED",
    }, s_records=s_records, windows=windows,
        global_quality_reasons=_global_quality_reasons(canonical), window_discovery_issues=())
