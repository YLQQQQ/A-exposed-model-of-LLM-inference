"""Separate, prospective Prefill-only Engineering review. No Request acceptance."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile

from exposedpath import completion_path as contract
from . import gate8_engineering_scope as base
from .gate8_files import _json,_write,_entry,_resolve
from .gate8_adapter import digest
from .sync_semantics import load_canonical_bundle,build_semantic_inventory,recover_wait_set,_semantic_frontier
from .time_representation import SIGNED,time_representation
from .gate8_scope import load_projected_ownership,build_projected_ab_inputs

VERSION='exposedpath-completion-path-prefill/0.1.0'


def _calculate(root,receipt_path,execution_path):
    receipt,paths,declared,execution=base._inputs(receipt_path,execution_path)
    manifest=_json(paths['wmpc_manifest']);binding=contract.validate(manifest)
    ledger=_json(paths['pass_identity']);call=contract.validate_calls(manifest,ledger,execution)
    canonical=root/'canonical/canonical_manifest.json';scope=root/'projection/scope.json'
    bundle=load_canonical_bundle(canonical);records=bundle['records']
    contract.require(bundle['manifest']['source']['sqlite']['sha256'].lower()==digest(paths['sqlite'])
        and bundle['manifest']['source']['raw']['sha256'].lower()==digest(paths['raw']),'RAW_LINEAGE')
    ownership,projections=load_projected_ownership(canonical,bundle,scope)
    from .gate8_stage_scope import derive_stage_diagnostics
    from .gate8_diagnostic_scope import load_diagnostic_scope
    from .gate9_diagnostic_review import review
    stage=derive_stage_diagnostics(canonical,paths['stage_ledger'])
    diagnostic=load_diagnostic_scope(root/'diagnostics.json',paths['sqlite'],paths['pass_identity'])
    dispositions=base._diagnostics(diagnostic);reviewed=review(diagnostic,bundle)
    accepted=set(reviewed['accepted_rowids']) if reviewed else set()
    effective=[d for d in dispositions if d['source_rowid'] not in accepted]
    selected=[p for p in projections if p['phase']=='prefill' and p['identity']==call['identity']]
    contract.require(len(selected)==1,'PREFILL_PROJECTION')
    p=selected[0]
    markers=[];interventions=[]
    for row in records['nvtx']:
        text=row.get('text') or ''
        if text.startswith(contract.MARKER):
            payload=json.loads(text[len(contract.MARKER):]);expected={**call,'status':'STARTED','sync_count':0}
            contract.require(payload==expected and row['process_id']==call['pid']
                and row['thread_id']==call['thread_id'] and row['clock_domain_id']==p['clock_domain_id']
                and type(row['end_ns']) is int and p['start_ns']<=row['start_ns']<=row['end_ns']<=p['end_ns'],'HOOK_RAW_IDENTITY')
            markers.append(row)
        if text.startswith('EXPOSEDPATH_JSON_V1:'):
            value=json.loads(text.split(':',1)[1])
            if value.get('kind')=='sync' and value.get('sync_origin')!= 'natural_token_ready':
                contract.require(value==dict(call['identity'],kind='sync',phase='prefill',sync_origin=contract.ORIGIN,
                    callsite_id='engineering.prefill.precopy',sync_ordinal=0,
                    intervention_variant_id='Cpre',intervention_ordinal=0),'FOREIGN_INTERVENTION')
                interventions.append(row)
    contract.require(len(markers)==1 and len(interventions)==call['sync_count'],'HOOK_RAW_COUNT')
    marker=markers[0]
    marker_apis=[a for a in records['cuda_api'] if a['start_ns']<marker['end_ns'] and marker['start_ns']<a['end_ns']]
    pre=[a for a in marker_apis if base.re.sub(r'_v\d+$','',a['api_name'])=='cudaStreamSynchronize']
    contract.require(len(pre)==call['sync_count'] and all(a['return_value']==0 and a['process_id']==call['pid']
        and a['thread_id']==call['thread_id'] and marker['start_ns']<=a['start_ns']<=a['end_ns']<=marker['end_ns'] for a in pre),'PRE_SYNC_COUNT_OR_STATUS')
    contract.require(all(base.re.sub(r'_v\d+$','',a['api_name']) in ('cudaStreamSynchronize','cudaGetDevice',
        'cudaGetDeviceProperties','cudaStreamIsCapturing') for a in marker_apis),'HOOK_UNEXPECTED_API')
    # Query observations cannot be used to prove an unobserved native-handle map.
    with time_representation(SIGNED):
        original=build_projected_ab_inputs(canonical,scope)
        result=base._request(canonical,scope,paths,bundle,ownership,p,original,stage,declared,effective,
            domain_proof=True,selected_phase='prefill')
    report=dict(schema_version=VERSION,status='BLOCKED',binding=binding,identity=receipt['identity'],
        input_receipt_sha256=digest(Path(receipt_path)),execution_receipt_sha256=digest(Path(execution_path)),
        prefill=result,requests=[result],request_status='NOT_ACCEPTED_LOCAL_REVIEW_ONLY',
        decode_status='NOT_ACCEPTED_LOCAL_REVIEW_ONLY',diagnostic_dispositions=dispositions,
        diagnostic_review=reviewed,dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        physical_b_qualified=False,formal_eligible=False,d_score_allowed=False,signature_allowed=False)
    if result['status']!='A_SCOPE_ENGINEERING_ONLY':return report
    facts=result['facts'];proofs=facts['conditional_suffix_proofs'][0]['syncs']
    from .sync_observation import sync_evidence
    from .activity_baseline import union
    timeline_syncs=[]
    for proof in proofs:
        evidence=sync_evidence(records,proof)
        evidence['supported_sync_residual_ns']=evidence['host_api_duration_ns']-evidence['supported_device_wait_union_ns']
        timeline_syncs.append(evidence)
    owned=set(facts['observed_api_ids']);members=set(i for s in proofs for i in s['suffix_activity_ids'])
    ready=[]
    for r in records['nvtx']:
        text=r.get('text') or ''
        if text.startswith('EXPOSEDPATH_JSON_V1:'):
            v=json.loads(text.split(':',1)[1])
            if v.get('sync_origin')=='natural_token_ready' and v.get('phase')=='prefill' and v.get('token_index')==0:
                contract.require(all(v.get(k)==value for k,value in call['identity'].items())
                    and r['process_id']==call['pid'] and r['thread_id']==call['thread_id'],'TOKEN_HELPER_IDENTITY')
                ready.append(r)
    contract.require(len(ready)==1,'TOKEN_HELPER_MISSING_OR_DUPLICATE')
    helper=ready[0]
    copy_apis=[a for a in records['cuda_api'] if a['record_id'] in owned and 'Memcpy' in a['api_name']
        and helper['start_ns']<=a['start_ns']<=a['end_ns']<=helper['end_ns']]
    inv=build_semantic_inventory({**bundle,'ownership_records':ownership})
    copy_ids={a['record_id'] for a in copy_apis}
    d2h_ids={a['record_id'] for a in inv['activities'] if a['enqueue_record_id'] in copy_ids}
    d2h=[a for a in records['device_activity'] if a['record_id'] in d2h_ids and a['activity_kind']=='MEMCPY'
        and a.get('attributes',{}).get('copy_kind')==2]
    contract.require(len(copy_apis)==1 and len(d2h)==1 and d2h_ids=={a['record_id'] for a in d2h},'COPY_EFFECT_MISSING')
    contract.require(all(marker['end_ns']<=a['start_ns'] for a in copy_apis),'PRE_COPY_ORDER')
    # Device effects, syncs and successful call mappings must identify one actual
    # trace stream/context. Native 0 and trace IDs are never equated numerically.
    targets=[a for a in records['device_activity'] if a['record_id'] in members]
    contexts={(a['device_id'],a['context_id'],a['stream_id']) for a in targets}
    contract.require(len(contexts)==1 and call['native_stream']==0,'ACTUAL_STREAM_SUPPORT')
    trace_scope=next(iter(contexts))
    full=[]
    if pre:
        inventory=build_semantic_inventory({**bundle,'ownership_records':ownership})
        sync=[s for s in inventory['syncs'] if s['runtime_record_id']==pre[0]['record_id']]
        contract.require(len(sync)==1,'PRE_SYNC_PHYSICAL_MAPPING');s=sync[0]
        contract.require((s['device_id'],s['context_id'],s['stream_id'])==trace_scope,'PRE_SYNC_WRONG_STREAM')
        # The window projection is NOT physical B. Keep the complete drained
        # Raw FIFO prefix separately, without fabricating request ownership for
        # setup/warmup records which the physical S reader may reject.
        prefix=[a for a in inventory['activities'] if a['record_id'] in facts['prefix_activity_ids']]
        contract.require(all((a['device_id'],a['context_id'],a['stream_id'])==trace_scope
            and a['enqueue_global_tid']==s['runtime_global_tid'] for a in prefix),'PRE_SYNC_PREFIX_SCOPE')
        full_prefix=sorted(prefix,key=lambda a:(a['start_ns'],a['end_ns'],a['record_id']))
        contract.require(all(a['end_ns']<=b['start_ns'] for a,b in zip(full_prefix,full_prefix[1:])),
            'PRE_SYNC_PREFIX_ORDER')
        for mode in ('LEGACY','PER_THREAD'):
            restricted=deepcopy(inventory)
            restricted['activities']=[a for a in inventory['activities'] if a['record_id'] in members]
            restricted['execution_context']['default_stream_mode']=mode
            r=recover_wait_set(restricted,s)
            contract.require(r['dependency_closure_status']=='COMPLETE' and not r['reasons'],'PRE_SYNC_CLOSURE')
            ids=r['wait_set_activity_ids'];edges=r['dependency_edges']
            selected=[a for a in restricted['activities'] if a['record_id'] in ids]
            contract.require(len(selected)==len(ids) and all(a['end_ns']<=s['host_end_ns'] for a in selected)
                and (not ids or len(_semantic_frontier(ids,edges))==1),'PRE_SYNC_TERMINAL')
            contract.require(not {a['record_id'] for a in d2h}&set(ids),'LATER_COPY_IN_PRE_SYNC')
            full.append(dict(request_wait_set_activity_ids=ids,dependency_edges=edges,
                terminal_activity_ids=sorted(_semantic_frontier(ids,edges)),
                drained_raw_prefix_activity_ids=[a['record_id'] for a in full_prefix],
                all_observed_preceding_activity_ids=[a['record_id'] for a in full_prefix]+ids,
                scope='DRAIN_CLOSED_RAW_FIFO_PREFIX_PLUS_COMPLETE_REQUEST_SUFFIX_NOT_PHYSICAL_B'))
        contract.require(full[0]==full[1],'PRE_SYNC_DEFAULT_AMBIGUOUS')
    submit=[a for a in records['cuda_api'] if a['record_id'] in owned and base.re.sub(r'_v\d+$','',a['api_name']) in base.SUBMIT_APIS
        and a['end_ns']<=marker['start_ns']]
    contract.require(submit,'LAST_SUBMISSION_MISSING')
    # Every unknown submit-effect after completion is explicitly retained. This
    # is not an accepted Request/Decode domain or a zero-effects assertion.
    # Canonical uses correlation mapping in the semantic inventory, not proximity.
    mapped={a['enqueue_record_id'] for a in inv['activities']}
    future_gaps=[a for a in records['cuda_api'] if a['start_ns']>=p['end_ns']
        and base.re.sub(r'_v\d+$','',a['api_name']) in base.SUBMIT_APIS and a['record_id'] not in mapped]
    contract.require(all(a['global_tid']==next(a for a in records['cuda_api'] if a['record_id']==facts['drain_api_id'])['global_tid']
        and a['clock_domain_id']==p['clock_domain_id'] for a in future_gaps),'DECODE_IMPACT_UNBOUNDED')
    report.update(status='PREFILL_LOCAL_ENGINEERING_ONLY',full_pre_sync_dependencies=full,
        decode_unresolved_effects=[dict(record_id=a['record_id'],api_name=a['api_name'],start_ns=a['start_ns'],
            reason='POST_COMPLETION_SUBMIT_EFFECT_UNPROVEN') for a in future_gaps],
        timeline=dict(clock_domain_id=p['clock_domain_id'],trace_device_context_stream=list(trace_scope),
            last_submit=max(submit,key=lambda a:a['end_ns']),common_hook=marker,copy_apis=copy_apis,
            d2h_activities=d2h,synchronization=timeline_syncs,pre_sync_runtime_ids=[a['record_id'] for a in pre],
            host_completion=p,device_activity_union_ns=union([(max(a['start_ns'],p['start_ns']),min(a['end_ns'],p['end_ns']))
                for a in targets if a['start_ns']<p['end_ns'] and p['start_ns']<a['end_ns']]),
            api_internal_wait='NOT_IDENTIFIABLE_NOT_SPLIT'))
    return report


def process(receipt_path,execution_path,output_dir):
    output=Path(output_dir).resolve()
    if output.exists():raise FileExistsError(output)
    _,paths,_,_=base._inputs(receipt_path,execution_path)
    hashes={Path(p):digest(Path(p)) for p in [receipt_path,execution_path,*paths.values()]}
    contract.require(not any(p.resolve().is_relative_to(output) for p in hashes),'OUTPUT_CONTAINS_INPUT')
    output.parent.mkdir(parents=True,exist_ok=True)
    root=Path(tempfile.mkdtemp(prefix='.'+output.name+'-partial-',dir=output.parent))
    from .canonical_raw import convert_sqlite_to_canonical
    from .gate8_scope import project_completion_scopes
    from .gate8_diagnostic_scope import write_diagnostic_scope
    from .gate9_domain import analysis_stage
    with analysis_stage('completion_path_canonical'):
        canonical=convert_sqlite_to_canonical(paths['sqlite'],root/'canonical','Engineering',
            raw_sha256=digest(paths['raw']),collector_version='2026.2.1.210',
            gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
        project_completion_scopes(canonical,paths['host_ledger'],root/'projection/scope.json')
        write_diagnostic_scope(paths['sqlite'],paths['pass_identity'],root/'diagnostics.json')
    with analysis_stage('completion_path_prefill_review'):result=_calculate(root,receipt_path,execution_path)
    contract.require(all(digest(p)==h for p,h in hashes.items()),'SOURCE_CHANGED')
    result['files']=[_entry(p,root) for p in sorted(root.rglob('*')) if p.is_file()]
    _write(root/'prefill.json',result);root.rename(output)
    return output/'prefill.json'


def load(path,receipt_path,execution_path):
    path=Path(path);value=_json(path)
    contract.require(value.get('schema_version')==VERSION,'RESULT_VERSION')
    files=[_resolve(path.parent,f) for f in value['files']]
    contract.require(len(files)==len(set(files)) and set(files)=={p.resolve() for p in path.parent.rglob('*') if p.is_file() and p!=path},'RESULT_FILES')
    contract.require({k:v for k,v in value.items() if k!='files'}==_calculate(path.parent,receipt_path,execution_path),'RESULT_CHANGED')
    return value
