"""Prospective candidate Pilot: strict receipt -> local Prefill -> COE, no domain dump."""
import json
from pathlib import Path

from exposedpath import coe_pilot as contract
from exposedpath.gate8_isolated_preflight import read,sha,write_new


def process(receipt_path,execution_path,output):
    from exposedpath_v141 import gate8_engineering_scope as base
    from exposedpath_v141.canonical_raw import convert_sqlite_to_canonical
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    from exposedpath_v141.gate8_scope import project_completion_scopes,load_projected_ownership,build_projected_ab_inputs
    from exposedpath_v141.gate8_stage_scope import derive_stage_diagnostics
    from exposedpath_v141.gate8_diagnostic_scope import write_diagnostic_scope
    from exposedpath_v141.gate9_diagnostic_review import review
    from exposedpath_v141.time_representation import SIGNED,time_representation
    from exposedpath_v141.gate9_domain import analysis_stage
    from .coe_candidate import analyze_files
    receipt,paths,declared,execution=base._inputs(receipt_path,execution_path)
    mf=read(paths['wmpc_manifest']);binding=contract.validate(mf)
    contract.validate_prepared(mf,paths['wmpc_manifest'].parent,Path(__file__).resolve().parents[1])
    hashes={Path(p):sha(p) for p in (receipt_path,execution_path,*paths.values())}
    out=Path(output).resolve()
    contract.require(not any(p.resolve().is_relative_to(out) for p in hashes),'OUTPUT_CONTAINS_INPUT')
    out.mkdir(parents=True,exist_ok=False)
    # A failed run retains partial files, but can never publish prefill.json.
    with analysis_stage('coe_canonical_projection'):
        canonical=convert_sqlite_to_canonical(paths['sqlite'],out/'canonical','Pilot',
            raw_sha256=sha(paths['raw']),collector_version=receipt['collector_version'],
            gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
        scope=out/'projection/scope.json'
        project_completion_scopes(canonical,paths['host_ledger'],scope)
        diagnostic=write_diagnostic_scope(paths['sqlite'],paths['pass_identity'],out/'diagnostics.json')
    with analysis_stage('coe_local_prefill'):
        bundle=load_canonical_bundle(canonical)
        ownership,projections=load_projected_ownership(canonical,bundle,scope)
        stage=derive_stage_diagnostics(canonical,paths['stage_ledger'])
        disposition=review(diagnostic,bundle)
        accepted=set(disposition['accepted_rowids']) if disposition else set()
        effective=[d for d in base._diagnostics(diagnostic) if d['source_rowid'] not in accepted]
        selected=[p for p in projections if p['phase']=='prefill']
        contract.require(len(selected)==1,'LOCAL_PREFILL_WINDOW')
        with time_representation(SIGNED):
            original=build_projected_ab_inputs(canonical,scope)
            local=base._request(canonical,scope,paths,bundle,ownership,selected[0],original,
                stage,declared,effective,domain_proof=True,selected_phase='prefill')
        contract.require(local['status']=='A_SCOPE_ENGINEERING_ONLY','LOCAL_ADMISSION:'+json.dumps(local['reasons']))
    with analysis_stage('coe_candidate'):
        candidate_path=analyze_files(receipt_path,canonical,out/'coe')
        candidate=read(candidate_path)
        ops=[o for o in candidate['operations'] if o['phase']=='prefill']
        contract.require(len(ops)==1 and ops[0]['operation_validity']=='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS','OPERATION:'+json.dumps(ops))
    # Explicit proof of isolation from observed unresolved future submissions:
    # _request already rejects crossing/earlier/foreign-thread unknown effects,
    # events, graph and non-FIFO suffixes. It never accepts a Decode label alone.
    unresolved=[r for s in stage['stages'] if s['payload']['request_identity']==local['identity']
        for r in s['unresolved_submissions']]
    later=[r['api_ref']['record_id'] for r in unresolved]
    api_by={r['record_id']:r for r in bundle['records']['cuda_api']}
    drain_tid=next(r['global_tid'] for r in bundle['records']['cuda_api'] if r['record_id']==local['facts']['drain_api_id'])
    future_unknown=[r for r in candidate['coverage'] if r['status']=='UNRESOLVED_OR_OUT_OF_SCOPE']
    for r in future_unknown:
        a=api_by[r['record']]
        contract.require(a['start_ns']>=selected[0]['end_ns'] and a['global_tid']==drain_tid
            and a['clock_domain_id']==selected[0]['clock_domain_id'],'DECODE_IMPACT_UNBOUNDED')
        later.append(r['record'])
    tokens=contract.validate_tokens(paths['pilot_tokens'],mf,read(paths['pass_identity']),execution,
                                    paths['wmpc_manifest'],paths['producer_receipt'])
    a=local['a_records'][0];p=selected[0]
    from exposedpath_v141.activity_baseline import calculate,_driver_records
    from exposedpath_v141.a_api_classification import VERSION as registry_version
    records=bundle['records'];drain=next(r for r in records['cuda_api'] if r['record_id']==local['facts']['drain_api_id'])
    owned=set(local['facts']['observed_api_ids'])|set(ops[0]['members'])
    drivers,driver_status=_driver_records(paths['sqlite'])
    baseline=calculate(records['cuda_api']+drivers,records['device_activity'],
        dict(p,process_id=drain['process_id'],thread_id=drain['thread_id']),owned,registry_version=registry_version)
    if driver_status!='OBSERVED_TABLE':baseline['driver_api']=dict(count=None,sum_ns=None,union_ns=None,status=driver_status)
    contract.require(all(sha(p)==h for p,h in hashes.items()),'SOURCE_CHANGED')
    result=dict(schema_version='coe-pilot-prefill-result/0.1.0',status='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW',
        binding=binding,source_identity=receipt['identity'],input_identity=mf['coe_input'],token_ids=tokens,
        input_receipt_sha256=sha(receipt_path),execution_receipt_sha256=sha(execution_path),
        candidate_sha256=sha(candidate_path),prefill=a,coe=ops[0],local_admission=local,
        baseline=baseline,driver_status=driver_status,
        decode_isolation=dict(basis='SUCCESSFUL_DRAIN_CLOSED_HISTORY_COMPLETE_MAIN_THREAD_FIFO_PREFILL_NO_INCOMING_EVENT_GRAPH',
            first_host_token_anchor_ns=p['end_ns'],post_completion_unresolved_api_ids=sorted(set(later)),
            post_completion_unresolved_records=future_unknown),
        request_status='NOT_ACCEPTED',decode_status='NOT_ACCEPTED',physical_b_qualified=False,
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',formal_eligible=False)
    write_new(out/'prefill.json',result)
    return out/'prefill.json'
