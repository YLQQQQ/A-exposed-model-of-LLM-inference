"""Fixed clock expectations; payloads come from the real runner boundary helper."""
import json
import sqlite3

import pytest

from exposedpath import runner
from test_runner_token_ready import _FakeToken, _FakeModel, _FakeInput, _patch_cpu_torch
from test_gate8_identity import sources, write_json, convert


def record_request(monkeypatch, identity, boundary_ids, output_len=2):
    import exposedpath.nvtx as nvtx
    factory = getattr(nvtx, "Gate8BoundaryRecorder", None)
    assert callable(factory), "common completion point producer is not implemented"
    events, labels, ranges = [], [], []
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda.nvtx, "range_push", ranges.append)
    clock = iter([900000, 900001, 900002, 900080, 900081, 900082, 900200, 900201, 900202])
    recorder = factory(identity, boundary_ids, marker_sink=labels.append, clock_ns=lambda: next(clock))
    result = runner.run_one_invocation(
        model=_FakeModel(iter([_FakeToken([10], events), _FakeToken([11], events)])),
        input_ids=_FakeInput(), attention_mask=object(), output_len=output_len, device="cpu",
        nvtx_invocation_label="test", nvtx_full_request_label="full",
        nvtx_prefill_label="prefill", nvtx_decode_label="decode",
        token_ready_identity_base=identity, clock_ns=lambda: next(clock), gate8_recorder=recorder,
    )
    assert events == ["host_read"] * output_len
    assert result["inference_end_ns"] == (900080 if output_len == 1 else 900200)
    assert len(labels) == output_len + 1
    return recorder.records, labels, [r for r in ranges if r.startswith("EXPOSEDPATH_JSON_V1:")]


def boundary_sources(tmp_path, monkeypatch, output_len=2):
    inputs = sources(tmp_path)
    ledger = json.loads(inputs[3].read_text())
    if output_len == 1:
        for request in ledger["requests"]:
            request.update(expected_output_tokens=1, actual_output_tokens=1,
                           expected_boundary_ids=request["expected_boundary_ids"][:2],
                           observed_boundary_ids=request["observed_boundary_ids"][:2])
        write_json(inputs[3], ledger)
    host_records = []
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute("DELETE FROM NVTX_EVENTS")
        for index, request in enumerate(ledger["requests"]):
            records, labels, ranges = record_request(monkeypatch, request["identity"], request["expected_boundary_ids"], output_len)
            host_records.extend(records)
            for timestamp, label in zip((100, 180, 300), labels):
                conn.execute("INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,NULL,34,?,?)",
                             (timestamp + index * 300, label, (1 << 56) | (2 << 48) | (3 << 24) | 4))
            for (start, end), label in zip(((130, 180), (250, 300)), ranges):
                conn.execute("INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)",
                             (start + index * 300, end + index * 300, label, (1 << 56) | (2 << 48) | (3 << 24) | 4))
    host = write_json(tmp_path / "host_boundaries.json", host_records)
    return inputs, host


def project(tmp_path, inputs, host):
    from exposedpath_v141.gate8_scope import project_completion_scopes
    canonical = convert(tmp_path, inputs)
    return canonical, project_completion_scopes(canonical, host, tmp_path / "scope.json")


def test_real_producer_points_to_same_clock_scopes(monkeypatch, tmp_path):
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    canonical, path = project(tmp_path, inputs, host)
    scope = json.loads(path.read_text())
    assert [(p["phase"], p["start_ns"], p["end_ns"]) for p in scope["projections"][:3]] == [
        ("full_request", 100, 300), ("prefill", 100, 180), ("decode", 180, 300)]
    assert all(p["dependency_evidence"] is False for p in scope["projections"])
    assert scope["projections"][1]["end_ref"] == scope["projections"][2]["start_ref"]
    assert len(scope["anchors"]) == 6
    assert scope["anchors"][0]["host_observed_ns"] == 900000
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    assert all(r["end_ns"] is None for r in load_canonical_bundle(canonical)["records"]["nvtx"] if r["text"].startswith("EXPOSEDPATH_BOUNDARY_V1:"))


def test_one_output_token_has_exact_same_ref_empty_decode(monkeypatch, tmp_path):
    inputs, host = boundary_sources(tmp_path, monkeypatch, output_len=1)
    _, path = project(tmp_path, inputs, host)
    decode = json.loads(path.read_text())["projections"][2]
    assert (decode["start_ns"], decode["end_ns"]) == (180,180)
    assert decode["start_ref"] == decode["end_ref"]


def test_signed_raw_clock_is_preserved_and_old_ab_limit_is_explicit(monkeypatch, tmp_path):
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute("UPDATE NVTX_EVENTS SET start=start-1000,end=end-1000")
    canonical, path = project(tmp_path, inputs, host)
    assert json.loads(path.read_text())["projections"][0]["start_ns"] == -900
    from exposedpath_v141.gate8_scope import build_projected_ab_inputs
    with pytest.raises(ValueError, match="GATE8_SIGNED_AB_ADAPTER_NOT_IMPLEMENTED"):
        build_projected_ab_inputs(canonical, path)


@pytest.mark.parametrize("sql,reason", [
    ("DELETE FROM NVTX_EVENTS WHERE start=300", "BOUNDARY_MISSING"),
    ("INSERT INTO NVTX_EVENTS SELECT * FROM NVTX_EVENTS WHERE start=180", "BOUNDARY_DUPLICATE"),
    ("UPDATE NVTX_EVENTS SET start=170 WHERE start=300", "BOUNDARY_ORDER_INVALID"),
    ("UPDATE NVTX_EVENTS SET globalTid=globalTid+1 WHERE start=180", "BOUNDARY_IDENTITY_CONFLICT"),
])
def test_raw_boundary_fail_closed(monkeypatch, tmp_path, sql, reason):
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute(sql)
    with pytest.raises(ValueError, match=reason):
        project(tmp_path, inputs, host)
    assert not (tmp_path / "scope.json").exists()


def test_host_diagnostic_reversal_rejects(monkeypatch, tmp_path):
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    records = json.loads(host.read_text())
    records[0]["host_after_marker_ns"] = 1
    write_json(host, records)
    with pytest.raises(ValueError, match="BOUNDARY_ORDER_INVALID"):
        project(tmp_path, inputs, host)


def test_projection_drives_existing_s_ownership_without_raw_range_fabrication(monkeypatch, tmp_path):
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    with sqlite3.connect(inputs[0]) as conn:
        conn.execute("UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=140,end=170")
        conn.execute("INSERT INTO StringIds VALUES (20,'cudaLaunchKernel')")
        conn.execute("INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME(start,end,eventClass,globalTid,correlationId,nameId,returnValue) SELECT 110,115,0,globalTid,6,20,0 FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1")
        conn.execute("UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET start=145,end=165")
        conn.execute("UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=150,end=160")
        conn.execute("DELETE FROM CUPTI_ACTIVITY_KIND_MEMCPY")
        conn.execute("DELETE FROM CUPTI_ACTIVITY_KIND_MEMSET")
        conn.execute("DELETE FROM CUPTI_ACTIVITY_KIND_CUDA_EVENT")
    canonical, scope_path = project(tmp_path, inputs, host)
    from exposedpath_v141 import gate8_scope
    loader = getattr(gate8_scope, "load_projected_ownership", None)
    assert callable(loader), "S and A need the same verified scope source"
    from exposedpath_v141.sync_semantics import load_canonical_bundle, build_semantic_inventory, analyze_sync_semantics
    bundle = load_canonical_bundle(canonical)
    ownership, projections = loader(canonical, bundle, scope_path)
    inventory = build_semantic_inventory({**bundle, "ownership_records": ownership})
    result = analyze_sync_semantics(inventory, inventory["syncs"][0])
    assert result["request_id"] == "request-0"
    assert result["validity"] == "VALID_NONEMPTY", result
    assert result["terminal"]["end_ns"] == 160
    assert len(projections) == 6
    assert all(r["end_ns"] is None for r in bundle["records"]["nvtx"] if r["text"].startswith("EXPOSEDPATH_BOUNDARY_V1:"))
    builder = getattr(gate8_scope, "build_projected_ab_inputs", None)
    assert callable(builder), "A must consume the same projections as S"
    from exposedpath_v141.a_accounting import calculate_a_windows
    from exposedpath_v141.b_provenance import calculate_b_syncs
    ab_inputs = builder(canonical, scope_path)
    a = calculate_a_windows(ab_inputs)
    full = next(r for r in a if r["request_id"] == "request-0" and r["phase"] == "full_request")
    # W activity only spans [150,160): 10 wait ns, not the entire
    # [140,160) prefix. Residual is [140,150) U [160,170) = 20 ns.
    assert [full[k] for k in ("T_window_ns", "A_host_path_ns", "A_cuda_api_ns", "A_device_wait_ns", "A_sync_residual_ns", "A_unattributed_ns")] == [200, 165, 5, 10, 20, 0]
    assert calculate_b_syncs(ab_inputs)[0]["validity"] == "B_VALID"
    # New coverage consumes the real registry universe and real S/B outputs.
    from exposedpath_v141.gate8_coverage import coverage_from_inputs
    window = next(w for w in ab_inputs.windows if w.request_id == "request-0" and w.phase == "full_request")
    lineage = {"window_ref":{"sha256":"a"*64,"selector":"$.projections[0]"},
               **{k:"b"*64 for k in ("canonical_manifest_sha256","s_manifest_sha256","ab_manifest_sha256","integrity_artifact_sha256")}}
    coverage = coverage_from_inputs(ab_inputs, window, calculate_b_syncs(ab_inputs),
                                    lineage=lineage, denominator_status="COMPLETE")
    assert coverage["supported_duration_coverage"] == {"status":"VALID","numerator":30,"denominator":30}
    assert calculate_a_windows(ab_inputs) == a
    # An unknown API cannot be silently excluded from a COMPLETE denominator.
    from dataclasses import replace
    unknown = dict(ab_inputs.canonical.records["cuda_api"][0], api_name="unknownFutureApi", start_ns=150, end_ns=151)
    changed_records = dict(ab_inputs.canonical.records)
    changed_records["cuda_api"] = (*changed_records["cuda_api"], unknown)
    changed = replace(ab_inputs, canonical=replace(ab_inputs.canonical, records=changed_records))
    assert coverage_from_inputs(changed, window, calculate_b_syncs(ab_inputs), lineage=lineage,
                                denominator_status="COMPLETE")["denominator_status"] == "INCOMPLETE"
    from exposedpath_v141.gate8_analysis import analyze_gate8_local
    blocked_path = analyze_gate8_local(canonical, scope_path, tmp_path / "blocked", capture_session_id="fixture")
    receipts = json.loads((blocked_path.parent / "integrity.json").read_text())
    for r in receipts:
        r.update(status="ZERO_CONFIRMED", dropped_count=0, basis="COLLECTOR_COUNTER",
                 finalized=True, coverage_complete=True, evidence_refs=[{"sha256":"f"*64,"selector":"synthetic_counter"}], reasons=[])
    path = analyze_gate8_local(canonical, scope_path, tmp_path / "synthetic", capture_session_id="fixture",
                               integrity_receipts=receipts, synthetic_fixture=True)
    result = json.loads(path.read_text())
    assert result["status"] == "SYNTHETIC_CALCULATION_ONLY"
    assert result["q0_status"] == result["gate8_verdict"] == "NOT_RUN"
    assert result["validation_role"] == "SYNTHETIC_REGRESSION_ONLY"
    assert json.loads((path.parent / "coverage.json").read_text())[0]["supported_count_coverage"]["denominator"] == 1
    document = json.loads(scope_path.read_text())
    document["projections"][0]["end_ns"] = 301
    write_json(scope_path, document)
    with pytest.raises(ValueError, match="PROJECTION_REF_MISMATCH"):
        loader(canonical, bundle, scope_path)


def test_real_gate8_analysis_entry_blocks_without_verified_integrity_provider(monkeypatch, tmp_path):
    import importlib.util
    assert importlib.util.find_spec("exposedpath_v141.gate8_analysis"), "new-profile analysis gate missing"
    from exposedpath_v141.gate8_analysis import analyze_gate8_local
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    canonical, scope_path = project(tmp_path, inputs, host)
    out = analyze_gate8_local(canonical, scope_path, tmp_path / "analysis", capture_session_id="synthetic-capture")
    result = json.loads(out.read_text())
    assert result["status"] == "BLOCKED"
    assert "OBSERVATION_INTEGRITY_UNKNOWN" in result["reasons"]
    assert result["gate8_verdict"] == "NOT_RUN"
    assert result["files"].keys() == {"integrity"}
    assert not (tmp_path / "analysis" / "ab_records.json").exists()


def test_scope_loader_binds_host_ledger_bytes_and_mapping_sidecar(monkeypatch, tmp_path):
    inputs, host = boundary_sources(tmp_path, monkeypatch)
    canonical, scope_path = project(tmp_path, inputs, host)
    from exposedpath_v141.gate8_scope import load_projected_ownership
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    mapping_path = canonical.parent / "gate8_device_mapping.json"
    mapping = json.loads(mapping_path.read_text())
    mapping["trace_device_id"] = 3
    write_json(mapping_path, mapping)
    with pytest.raises(ValueError, match="SOURCE_HASH_MISMATCH"):
        load_projected_ownership(canonical, load_canonical_bundle(canonical), scope_path)


@pytest.mark.parametrize("pass_id", ["pass0", "pass1"])
def test_pass_producer_records_actual_completion_and_exclusion(monkeypatch, pass_id):
    from itertools import count
    from test_gate8_identity import producer_pass
    execute = getattr(runner, "run_gate8_requests", None)
    assert callable(execute), "runner must produce the ledger from actual outcomes"
    _patch_cpu_torch(monkeypatch)
    points = []
    ranges = []
    monkeypatch.setattr(runner.torch.cuda.nvtx, "range_push", ranges.append)
    monkeypatch.setattr(runner.torch.cuda.nvtx, "mark", points.append)
    initial = producer_pass()
    fields = {k:initial[k] for k in ("experiment_id","wmpc_id","run_id","attempt_id","pid",
              "wmpc_manifest_sha256","prompt_sha256","runner_source_sha256","runner_git_commit","runner_git_dirty")}
    import os
    fields["pid"] = os.getpid()
    clock = count(100)
    events = []
    ledger, host = execute(model=_FakeModel(iter([_FakeToken([10],events),_FakeToken([11],events),_FakeToken([2],events)])),
        input_ids=_FakeInput(), attention_mask=object(), output_len=2, device="cpu", eos_token_id=2,
        pass_fields={**fields,"pass_id":pass_id}, request_plan=[
            {"request_id":"r0","repeat_id":"0","request_role":"measured"},
            {"request_id":"r1","repeat_id":"1","request_role":"measured"}], clock_ns=lambda:next(clock))
    assert [r["outcome"] for r in ledger["requests"]] == ["COMPLETE","EXCLUDED"]
    assert [r["actual_output_tokens"] for r in ledger["requests"]] == [2,1]
    assert ledger["requests"][1]["early_eos"] is True
    assert len(host) == 5
    assert len(points) == (5 if pass_id == "pass1" else 0)
    assert events == ["host_read"]*3
    if pass_id == "pass0":
        assert ranges == [], "Gate8 Pass0 must not emit even empty NVTX ranges"
