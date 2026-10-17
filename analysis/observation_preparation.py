"""Both-token Engineering admission and COE; reuses existing S/A unchanged."""
from pathlib import Path
from exposedpath import observation_preparation as contract
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
    from exposedpath_v141.activity_baseline import calculate,_driver_records
    from exposedpath_v141.a_api_classification import VERSION as registry_version
    from .coe_candidate import analyze_files
    receipt,paths,declared,execution=base._inputs(receipt_path,execution_path)
    from exposedpath import coe_input_pilot as axis,coe_pilot
    mf=read(paths['wmpc_manifest']);input_axis=axis.active(mf.get('pilot'))
    binding=axis.validate(mf) if input_axis else contract.validate(mf)
    validator=coe_pilot if input_axis else contract
    validator.validate_prepared(mf,paths['wmpc_manifest'].parent,Path(__file__).resolve().parents[1])
    hashes={Path(p):sha(p) for p in (receipt_path,execution_path,*paths.values())}
    out=Path(output).resolve()
    contract.require(not any(p.resolve().is_relative_to(out) for p in hashes),'OUTPUT_CONTAINS_INPUT')
    out.mkdir(parents=True,exist_ok=False)
    with analysis_stage('preparation_canonical_projection'):
        canonical=convert_sqlite_to_canonical(paths['sqlite'],out/'canonical',mf['data_role'],raw_sha256=sha(paths['raw']),
            collector_version=receipt['collector_version'],gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
        scope=out/'projection/scope.json';project_completion_scopes(canonical,paths['host_ledger'],scope)
        diagnostic=write_diagnostic_scope(paths['sqlite'],paths['pass_identity'],out/'diagnostics.json')
    with analysis_stage('preparation_both_token_admission'):
        bundle=load_canonical_bundle(canonical)
        ownership,projections=load_projected_ownership(canonical,bundle,scope)
        stage=derive_stage_diagnostics(canonical,paths['stage_ledger']);disposition=review(diagnostic,bundle)
        accepted=set(disposition['accepted_rowids']) if disposition else set()
        effective=[d for d in base._diagnostics(diagnostic) if d['source_rowid'] not in accepted]
        full=[p for p in projections if p['phase']=='full_request']
        contract.require(len(full)==1,'REQUEST_WINDOW')
        # No new Decode projection exception: require the existing full request
        # closed FIFO admission, then take its already calculated phase A rows.
        with time_representation(SIGNED):
            original=build_projected_ab_inputs(canonical,scope)
            local=base._request(canonical,scope,paths,bundle,ownership,full[0],original,stage,declared,effective,domain_proof=True)
        contract.require(local['status']=='A_SCOPE_ENGINEERING_ONLY','BOTH_TOKEN_ADMISSION:'+str(local['reasons']))
    with analysis_stage('preparation_coe_both_tokens'):
        candidate_path=analyze_files(receipt_path,canonical,out/'coe');candidate=read(candidate_path)
        ops=candidate['operations']
        contract.require(len(ops)==2 and [o['token_index'] for o in ops]==[0,1]
            and all(o['operation_validity']=='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS' for o in ops),
            'OPERATIONS:'+str([dict(token=o.get('token_index'),reasons=o.get('reasons')) for o in ops]))
        contract.require(not any(c['status']=='UNRESOLVED_OR_OUT_OF_SCOPE' for c in candidate['coverage']),'COVERAGE')
    tokens=validator.validate_tokens(paths['pilot_tokens' if input_axis else 'batch_tokens'],mf,read(paths['pass_identity']),execution,paths['wmpc_manifest'],paths['producer_receipt'])
    records=bundle['records'];activities={r['record_id']:r for r in records['device_activity']}
    apis={r['record_id']:r for r in records['cuda_api']};drivers,driver_status=_driver_records(paths['sqlite'])
    drain=apis[local['facts']['drain_api_id']];windows=[]
    contract.require(drain['thread_id']==execution['observation_preparation']['tid'],'PREPARATION_TRACE_THREAD')
    for op in ops:
        members=[activities[k] for k in op['members']]
        submits=[apis[s['submit']] for s in op['member_submits']]
        pre=[s for s in submits if s['end_ns']<=op['copy_interval'][0]]
        kernels=[m for m in members if m['activity_kind']=='KERNEL']
        contract.require(pre and kernels,'POSITION_EVIDENCE')
        L=max(s['end_ns'] for s in pre);K=max(k['end_ns'] for k in kernels);C=op['copy_interval'][0]
        op['positions']=dict(clock='NSYS_TRACE_RELATIVE_NS',L_ns=L,C_ns=C,K_ns=K,H_ns=C-L,D_ns=K-L,
            terminal_ns=op['terminal_end_ns'],sync_return_ns=op['sync_interval'][1],token_point_ns=op['token_point_ns'],
            last_precopy_submit_ids=sorted({s['record_id'] for s in pre if s['end_ns']==L}))
        op['member_records']=members;op['submission_records']=[apis[s['submit']] for s in op['member_submits']]
        p=next(p for p in projections if p['phase']==op['phase'])
        a=next(a for a in local['a_records'] if a['phase']==op['phase'])
        baseline=calculate(records['cuda_api']+drivers,records['device_activity'],
            dict(p,process_id=drain['process_id'],thread_id=drain['thread_id']),
            set(local['facts']['observed_api_ids'])|set(op['members']),registry_version=registry_version)
        if driver_status!='OBSERVED_TABLE':baseline['driver_api']=dict(count=None,sum_ns=None,union_ns=None,status=driver_status)
        windows.append(dict(phase=op['phase'],projection=p,a=a,baseline=baseline))
    contract.require(all(sha(p)==h for p,h in hashes.items()),'SOURCE_CHANGED')
    with analysis_stage('preparation_independent_candidate_budget'):
        from . import coe_budget_preview as preview_module
        preview=preview_module.calculate_preview(candidate,local,records)
        preview.update(candidate_sha256=sha(candidate_path),input_receipt_sha256=sha(receipt_path),
            canonical_manifest_sha256=sha(canonical),analysis_sources={
                'analysis/observation_preparation.py':sha(Path(__file__)),
                'analysis/coe_budget_preview.py':sha(Path(preview_module.__file__)),
                'analysis/coe_candidate.py':sha(Path(__file__).with_name('coe_candidate.py'))})
        # Separate versioned artifact; never replace the saved original a_records.
        write_new(out/'candidate_budget_preview.json',preview)
    result=dict(schema_version=axis.RESULT_VERSION if input_axis else contract.RESULT_VERSION,
        status=axis.STATUS if input_axis else contract.STATUS,binding=binding,token_ids=tokens,
        analysis_code_sha256=sha(Path(__file__)),
        input_receipt_sha256=sha(receipt_path),execution_receipt_sha256=sha(execution_path),candidate_sha256=sha(candidate_path),
        candidate_budget_preview_sha256=sha(out/'candidate_budget_preview.json'),
        operations=ops,windows=windows,local_admission=local,coverage=candidate['coverage'],
        preparation=execution['observation_preparation'],formal_eligible=False,physical_b_qualified=False,
        H_is_exact_preparation_cost=False,pure_host_stall_ns=None,dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    write_new(out/'sensitivity.json',result);return out/'sensitivity.json'
