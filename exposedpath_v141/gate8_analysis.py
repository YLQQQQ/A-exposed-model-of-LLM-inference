"""Local Gate8 entry: verified identity/scopes, integrity gate, no collection.

Real Nsight scientific analysis is deliberately BLOCKED until an affirmative
provider is established. Synthetic mode is marked and never qualifies a run.
"""
import json
import tempfile
from pathlib import Path

from exposedpath.gate8_identity import PROFILE, ADAPTER_VERSION
from .gate8_adapter import digest
from .gate8_integrity import nsys_unknown_receipts, assess_integrity
from .gate8_scope import sidecar, load_projected_ownership, build_projected_ab_inputs
from .sync_semantics import load_canonical_bundle


def analyze_gate8_local(canonical_path, scope_path, output_dir, *, capture_session_id,
                       integrity_receipts=None, synthetic_fixture=False, scope_assessment=None,
                       controlled_evidence=None):
    canonical_path, scope_path, output_dir = map(Path, (canonical_path, scope_path, output_dir))
    if output_dir.exists():
        raise FileExistsError("refusing to overwrite Gate8 derived output")
    bundle = load_canonical_bundle(canonical_path)
    _, projections = load_projected_ownership(canonical_path, bundle, scope_path)
    if not projections:
        raise ValueError("BOUNDARY_MISSING: no complete measured request")
    manifest = bundle["manifest"]
    pass_ref = manifest["gate8_sources"]["pass_identity"]
    ledger = sidecar(canonical_path.parent, pass_ref)
    expected = dict(capture_session_id=capture_session_id,
                    source_raw_sha256=ledger["raw_artifact_sha256"],
                    pass_identity_sha256=pass_ref["sha256"], scope_pid=ledger["pid"],
                    scope_start_ns=min(p["start_ns"] for p in projections),
                    scope_end_ns=max(p["end_ns"] for p in projections),
                    collector_version=manifest["source"]["raw"]["collector_version"])
    receipts = nsys_unknown_receipts(**expected) if integrity_receipts is None else integrity_receipts
    integrity = assess_integrity(receipts, expected=expected)
    requests_complete = all(r['outcome']=='COMPLETE' for r in ledger['requests'])
    can_calculate = synthetic_fixture and requests_complete and integrity["status"] == "EVIDENCE_SHAPE_CONFIRMED"
    reasons = list(integrity["reasons"])
    if not requests_complete:
        reasons.append('REQUEST_ATTEMPT_NOT_COMPLETE')
    if not synthetic_fixture:
        reasons.append("NSYS_AFFIRMATIVE_PROVIDER_NOT_IMPLEMENTED")
    if scope_assessment is not None:
        from .gate8_target_quality import validate_projection, validate_assessment
        from .time_representation import time_representation, SIGNED
        if not synthetic_fixture or integrity_receipts is not None:
            raise ValueError('SYNTHETIC scoped evidence only; no mixed quality modes')
        validate_assessment(scope_assessment, synthetic_fixture)
        with time_representation(SIGNED):
            scoped_inputs = build_projected_ab_inputs(canonical_path, scope_path)
        can_calculate = validate_projection(scope_assessment, projections, scoped_inputs) and requests_complete
        reasons = [*scope_assessment['reasons'], 'COLLECTOR_INTEGRITY_UNKNOWN_NOT_ZERO']
        if not requests_complete:
            reasons.append('REQUEST_ATTEMPT_NOT_COMPLETE')
    controlled_report=None
    if controlled_evidence is not None:
        from .gate8_controlled_evidence import ControlledEvidence
        from .time_representation import time_representation,SIGNED
        if type(controlled_evidence) is not ControlledEvidence or scope_assessment is not None or integrity_receipts is not None:
            raise ValueError('CONTROLLED_FILE_PROOF_REQUIRED')
        with time_representation(SIGNED):
            controlled_inputs=build_projected_ab_inputs(canonical_path,scope_path)
        controlled_report=controlled_evidence.validate_projection_and_s(manifest,projections,controlled_inputs.s_records)
        reasons=[*controlled_inputs.global_quality_reasons,*controlled_report['s_comparison_issues'],
                 'COLLECTOR_INTEGRITY_UNKNOWN_NOT_ZERO']
        can_calculate=requests_complete and not controlled_inputs.global_quality_reasons and not controlled_report['s_comparison_issues']
    result = {
        "schema_version":"exposedpath-gate8-local-analysis/0.2.0",
        "observation_profile":PROFILE, "adapter_version":ADAPTER_VERSION,
        "data_role":"Engineering", "validation_role":"SYNTHETIC_REGRESSION_ONLY" if synthetic_fixture else "LOCAL_DIAGNOSTIC_ONLY",
        "status":"SYNTHETIC_CALCULATION_ONLY" if can_calculate else "BLOCKED",
        "gate8_verdict":"NOT_RUN", "q0_status":"NOT_RUN", "formal_evidence":False,
        "reasons":sorted(set(reasons)), "measurement_validity":"NOT_ASSESSED",
        "source":{"canonical_manifest_sha256":digest(canonical_path), "scope_sha256":digest(scope_path),
                  "pass_identity_sha256":pass_ref["sha256"]}, "files":{},
    }
    destination = output_dir
    if scope_assessment is not None:
        result['schema_version'] = 'exposedpath-gate8-local-analysis/0.3.0'
        result['target_scope'] = scope_assessment
    if controlled_report is not None:
        result['schema_version']='exposedpath-gate8-local-analysis/0.4.0'
        result['controlled_scope']=controlled_report
        if not synthetic_fixture:
            result['validation_role']='CONTROLLED_ENGINEERING_DIAGNOSTIC_ONLY'
            result['status']='CONTROLLED_CALCULATION_ONLY' if can_calculate else 'BLOCKED'
    destination.parent.mkdir(parents=True, exist_ok=True)
    output_dir = Path(tempfile.mkdtemp(prefix=f'.{destination.name}-partial-', dir=destination.parent))

    def write(key, name, data):
        path = output_dir / name
        with path.open("x", encoding="utf-8", newline="\n") as handle:
            json.dump(data, handle, sort_keys=True, indent=2)
            handle.write("\n")
        result["files"][key] = {"filename":name, "sha256":digest(path)}
        return digest(path)

    integrity_sha = write("integrity", "integrity.json", receipts)
    if can_calculate:
        from .s_bundle import analyze_canonical_to_s
        from .ab_bundle import analyze_ab, load_ab_bundle
        from .derived import derive_exposure
        from .time_representation import time_representation, SIGNED
        from .gate8_coverage import coverage_from_inputs
        s_path = analyze_canonical_to_s(canonical_path, output_dir/'s', scope_manifest=scope_path)
        ab_path = analyze_ab(canonical_path, s_path, output_dir/'ab', scope_manifest=scope_path)
        loaded = load_ab_bundle(ab_path, canonical_manifest=canonical_path, s_manifest=s_path)
        a, b = loaded['a_window_records'], loaded['b_sync_records']
        s_sha, ab_sha = digest(s_path), digest(ab_path)
        result['files']['s'] = {'filename':'s/s_manifest.json','sha256':s_sha}
        result['files']['ab'] = {'filename':'ab/ab_manifest.json','sha256':ab_sha}
        with time_representation(SIGNED):
            inputs = build_projected_ab_inputs(canonical_path, scope_path)
        coverage = [coverage_from_inputs(inputs, window, b, lineage={
            "window_ref":{"sha256":digest(scope_path),"selector":f"$.projections[{i}]"},
            "canonical_manifest_sha256":digest(canonical_path), "s_manifest_sha256":s_sha,
            "ab_manifest_sha256":ab_sha, "integrity_artifact_sha256":integrity_sha,
        }, denominator_status="COMPLETE" if not inputs.global_quality_reasons else "INCOMPLETE")
                    for i,window in enumerate(inputs.windows)]
        write("coverage", "coverage.json", coverage)
        if scope_assessment is not None or controlled_report is not None:
            from .gate8_target_quality import publication
            write('publication', 'publication.json', publication(a,result['validation_role']))
        b_oracle_ok=True
        if controlled_report is not None:
            by_id={row['sync_id']:row for row in b}
            for expected_sync in controlled_report['sync_expectations']:
                ref=expected_sync['sync_ref']
                row=by_id.get(f"cuda_sync:{ref['source_table']}:{ref['source_rowid']}",{})
                if row.get('validity')!='B_VALID' or any(row.get(k)!=v for k,v in expected_sync['timing'].items()):
                    b_oracle_ok=False
            controlled_report['b_oracle_match']=b_oracle_ok
            if not b_oracle_ok:
                result['status']='BLOCKED'
                result['reasons'].append('CONTROLLED_INDEPENDENT_ORACLE_B_MISMATCH')
        eligible = (loaded['manifest']['quality']['status'] == 'VALID'
                    and b_oracle_ok
                    and all(r['primary_reason'] is None and r['A_unattributed_ns'] == 0 for r in a)
                    and all(r['validity'] in ('B_VALID','B_NOT_APPLICABLE') for r in b)
                    and all(r['denominator_status'] == 'COMPLETE' for r in coverage))
        if eligible:
            derived = derive_exposure(ab_path, output_dir/'derived')
            result['files']['derived'] = {'filename':'derived/derived_manifest.json','sha256':digest(derived)}
        else:
            result['reasons'].append('DERIVED_BLOCKED_UPSTREAM_NOT_QUALIFIED')
    path = output_dir / "gate8_local_analysis.json"
    with path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, sort_keys=True, indent=2)
        handle.write("\n")
    output_dir.rename(destination)
    return destination / path.name
