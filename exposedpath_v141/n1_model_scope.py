"""N1 model multi-API admission. Reuses Canonical/S/A/B; no new accounting.

Version 0.1 supports a fresh, held, explicit nonblocking measured stream and
primary-thread FIFO work only. Additional streams/dependency edges are rejected,
not assumed to follow a framework context. Warmup stays outside the windows.
"""
import json
from pathlib import Path
import re
from collections import defaultdict

from exposedpath.n1_model import VERSION as CALL_VERSION, PREFIX, CALLSITE, validate_manifest
from exposedpath.gate9_stream_bridge import PREFIX as BRIDGE_PREFIX, VERSION as BRIDGE_VERSION
from exposedpath.gate8_engineering_contract import EXECUTION_VERSION, validate_declaration
from .gate8_adapter import digest
from .gate8_files import load_input_receipt, _json
from .gate9_domain import VERSION, require, analysis_stage
from .gate8_scope import load_projected_ownership, build_projected_ab_inputs
from .sync_semantics import load_canonical_bundle, build_semantic_inventory, classify_cuda_api
from .time_representation import SIGNED, time_representation

ADAPTER = 'exposedpath-n1-model-ownership/0.1.1'


def bindings(bundle, ownership, projections, calls, ledger, policy, drain_api, drain):
    rows=bundle['records']; inventory=build_semantic_inventory({**bundle,'ownership_records':ownership})
    require(inventory['input_status']=='VALID', 'MODEL_CANONICAL_QUALITY')
    full=[p for p in projections if p['phase']=='full_request']
    require(len(full)==1 and len(calls['requests'])==2, 'MODEL_REQUEST_SET')
    p=full[0]; identity=p['identity']; start,end=p['start_ns'],p['end_ns']
    selected=[r for r in calls['requests'] if r['identity']==identity]
    require(len(selected)==1, 'MODEL_REQUEST_IDENTITY')
    r=selected[0]; handle=r['native_handle']; generation=r['generation']
    require(type(handle) is int and handle>0 and r['logical_device']==0
        and r['request_role']=='measured' and r['status']=='COMPLETE_PENDING_TRACE_OWNERSHIP'
        and r['declaration']==policy and r['variant']==policy['variant'], 'MODEL_CALL_STATUS')
    require(r['actual_input_tokens']==32 and len(r['observed_tokens'])==2
        and all(isinstance(t,list) and len(t)==1 and type(t[0]) is int and t[0]>=0
                for t in r['observed_tokens']), 'MODEL_ACTUAL_WORKLOAD')
    warm=[x for x in calls['requests'] if x['request_role']=='warmup']
    require(len(warm)==1 and warm[0]['native_handle']!=handle
        and warm[0]['status']=='WARMUP_CALLS_COMPLETE_PENDING_TRACE_OWNERSHIP'
        and warm[0]['declaration']==policy, 'MODEL_WARMUP_STREAM')

    def marker(prefix,payload):
        matches=[x for x in rows['nvtx'] if (x.get('text') or '').startswith(prefix)
                 and json.loads(x['text'][len(prefix):])==payload]
        require(len(matches)==1,'MODEL_MARKER')
        x=matches[0]
        require(x['process_id']==ledger['pid'] and x['clock_domain_id']==p['clock_domain_id']
            and type(x['end_ns']) is int and x['end_ns']>=x['start_ns'],'MODEL_MARKER_SCOPE')
        return x
    life_payload=dict(schema_version=CALL_VERSION,operation='held_lifetime',identity=identity,
                      generation=generation,native_handle=handle,logical_device=0)
    require(r['lifetime_payload']==life_payload,'MODEL_LIFETIME_IDENTITY')
    life=marker(PREFIX,life_payload)
    require(life['start_ns']<=start<end<=life['end_ns'],'MODEL_LIFETIME')
    tid=life['global_tid']; global_pid=tid-tid%2**24

    def inside(x,outer): return outer['start_ns']<=x['start_ns']<=x['end_ns']<=outer['end_ns']
    from .a_api_classification import classify_a_api_name
    def companion(x):
        return (x['return_value']==0 and x['clock_domain_id']==p['clock_domain_id']
            and classify_a_api_name(x['api_name'])[0]=='non_submit'
            and not any(s['runtime_record_id']==x['record_id'] for s in rows['cuda_sync'])
            and not any(a.get('enqueue_record_id')==x['record_id'] for a in inventory['activities']))
    def actual_waits(marker_row):
        contained=[a for a in rows['cuda_api'] if a['global_tid']==tid and inside(a,marker_row)]
        waits=[]
        for a in contained:
            if re.fullmatch(r'cudaStreamSynchronize(?:_v[1-9][0-9]*)?',a['api_name']):
                require(a['return_value']==0,'MODEL_WAIT_RETURN'); waits.append(a)
            else:
                require(companion(a),'MODEL_CALL_COMPANION_UNSUPPORTED')
        return waits
    anchor=r['anchor']
    payload=dict(schema_version=BRIDGE_VERSION,identity=identity,generation=generation,logical_device=0,
                 native_handle=handle,operation='wait',ordinal=0)
    require(isinstance(anchor,dict) and anchor['payload']==payload and anchor['operation']=='wait'
        and anchor['before_native_handle']==anchor['after_native_handle']==handle
        and anchor['status']=='COMPLETE' and anchor['error'] is None,'MODEL_ANCHOR_CALL')
    am=marker(BRIDGE_PREFIX,payload)
    require(inside(am,life) and am['end_ns']<=start and am['global_tid']==tid,'MODEL_ANCHOR_POSITION')
    apis=actual_waits(am)
    require(len(apis)==1,'MODEL_ANCHOR_API')
    physical=[s for s in rows['cuda_sync'] if s['runtime_record_id']==apis[0]['record_id']]
    require(len(physical)==1 and physical[0]['runtime_mapping_count']==1,'MODEL_ANCHOR_CORRELATION')
    anchor_sync=physical[0]
    scope=tuple(anchor_sync[k] for k in ('device_id','context_id','stream_id'))
    require(anchor_sync['global_pid']==global_pid and inside(anchor_sync,apis[0]),'MODEL_ANCHOR_SCOPE')
    require(scope[:2]==(drain['device_id'],drain['context_id']) and drain['global_pid']==global_pid
        and drain_api['global_tid']==tid and am['end_ns']<=drain_api['start_ns']
        and all(a['end_ns']<=drain['end_ns'] for a in inventory['activities']
                if a['global_pid']==global_pid and a.get('enqueue_end_ns') is not None
                and a['enqueue_end_ns']<=drain_api['start_ns']), 'MODEL_DRAIN_BRIDGE_SCOPE')
    streams=[s for s in rows['stream'] if s['process_id']==ledger['pid'] and (s['context_id'],s['stream_id'])==scope[1:]]
    contexts=[c for c in rows['context'] if c['process_id']==ledger['pid'] and (c['device_id'],c['context_id'])==scope[:2]]
    require(len(streams)==len(contexts)==1 and streams[0]['flag']==2
        and contexts[0]['null_stream_id']!=scope[2],'MODEL_EXPLICIT_NONBLOCKING')
    # Do not truncate a physical W prefix. A reused trace stream with prior work
    # is outside this fresh-stream entry's support, even when warmup drained.
    activities=inventory['activities']
    by_api=defaultdict(list); sync_by_api=defaultdict(list)
    for a in activities: by_api[a.get('enqueue_record_id')].append(a)
    for s in rows['cuda_sync']: sync_by_api[s['runtime_record_id']].append(s)
    require(not any(tuple(a[k] for k in ('device_id','context_id','stream_id'))==scope
        and a['global_pid']==global_pid and a['start_ns']<start for a in activities),'MODEL_STREAM_PRIOR_WORK')
    require(not any(e.get('process_id')==ledger['pid'] and start<=e['start_ns']<end
        for e in rows.get('cuda_event',[])), 'MODEL_EVENT_DEPENDENCY_UNSUPPORTED')
    phase_rows=[x for x in projections if x['phase']!='full_request' and x['identity']==identity]
    def phase(x):
        matches=[q['phase'] for q in phase_rows if inside(x,q)]
        require(len(matches)==1,'MODEL_PHASE_AMBIGUOUS'); return matches[0]
    require(len(r['model_calls'])==2,'MODEL_FORWARD_COUNT')
    forwards=[]
    for i,c in enumerate(r['model_calls']):
        ph='prefill' if i==0 else 'decode'
        expected=dict(schema_version=CALL_VERSION,identity=identity,generation=generation,
            variant=policy['variant'],operation='model_forward',token_index=i,phase=ph)
        require(c['payload']==expected and c['phase']==ph and c['status']=='COMPLETE' and c['error'] is None
            and c['before_native_handle']==c['after_native_handle']==handle,'MODEL_FORWARD_CALL')
        m=marker(PREFIX,expected)
        require(m['global_tid']==tid and inside(m,p) and phase(m)==ph,'MODEL_FORWARD_POSITION')
        forwards.append(m)
    expected_count=0 if policy['variant']=='V0' else 1
    require(len(r['interventions'])==expected_count,'MODEL_INTERVENTION_COUNT')
    intervention=None
    if expected_count:
        c=r['interventions'][0]
        expected=dict(schema_version=CALL_VERSION,identity=identity,generation=generation,variant=policy['variant'],
            operation='intervention',token_index=1,layer_index=15,callsite_id=CALLSITE,marker_role='non_sync_marker')
        require(c['payload']==expected and c['token_index']==1 and c['layer_index']==15 and c['status']=='COMPLETE'
            and c['before_native_handle']==c['after_native_handle']==handle
            and c['synchronize_called'] is (policy['variant']=='Vsync'),'MODEL_INTERVENTION_CALL')
        intervention=marker(PREFIX,expected)
        require(intervention['global_tid']==tid and inside(intervention,forwards[1]),'MODEL_INTERVENTION_POSITION')
    observed_markers=[x for x in rows['nvtx'] if (x.get('text') or '').startswith(PREFIX)
        and json.loads(x['text'][len(PREFIX):]).get('identity')==identity]
    require(len(observed_markers)==3+expected_count,'MODEL_EXTRA_MARKER')
    # Every physical activity overlapping the request must have a unique
    # primary-thread enqueue. Unknown/cross-stream work cannot become Host.
    api_by_id={a['record_id']:a for a in rows['cuda_api']}
    for a in activities:
        if a['end_ns']<=start or a['start_ns']>=end: continue
        api=api_by_id.get(a.get('enqueue_record_id'))
        require(api is not None and inside(api,p) and api['global_tid']==tid
            and a['global_pid']==global_pid and a['clock_domain_id']==p['clock_domain_id']
            and tuple(a[k] for k in ('device_id','context_id','stream_id'))==scope
            and a['ownership_status']=='VALID'
            and all(a['invocation_identity'].get(k)==v for k,v in identity.items() if k!='data_role'),
            'MODEL_ACTIVITY_OWNERSHIP')
        require(a.get('graph_id') in (None,0) and a.get('graph_node_id') in (None,0), 'MODEL_GRAPH_UNSUPPORTED')
    output=[]; sync_ids=[]; unsupported=[]
    for a in rows['cuda_api']:
        if a['end_ns']<=start or a['start_ns']>=end: continue
        require(inside(a,p) and a['global_tid']==tid and a['clock_domain_id']==p['clock_domain_id']
            and a['return_value']==0,'MODEL_API_SCOPE')
        members=by_api[a['record_id']]
        syncs=sync_by_api[a['record_id']]
        category=classify_a_api_name(a['api_name'])[0]
        semantic=classify_cuda_api(a['api_name'])
        if syncs:
            require(len(syncs)==1 and syncs[0]['runtime_mapping_count']==1 and not members
                and tuple(syncs[0][k] for k in ('device_id','context_id','stream_id'))==scope
                and syncs[0]['global_pid']==global_pid and inside(syncs[0],a)
                and semantic['role']=='HOST_BLOCKING_SYNC','MODEL_SYNC_SCOPE')
            sync_ids.append(syncs[0]['record_id'])
            category='physical_sync'
        elif category=='submit':
            require(members and semantic['universe_class']!='DEVICE_DEPENDENCY_EDGE','MODEL_SUBMIT_MAPPING')
            require(all(inside(x,p) and x['ownership_status']=='VALID' and x.get('enqueue_global_tid')==tid
                and tuple(x[k] for k in ('device_id','context_id','stream_id'))==scope for x in members),'MODEL_SUBMIT_SCOPE')
        else:
            if category!='non_submit' or members:
                # Preserve every source record, not just the first exception.
                # Inspection is not admission: the caller still rejects before
                # writing domain.json, after diagnosing independent physical B.
                unsupported.append(dict(api_record_id=a['record_id'],api_name=a['api_name'],
                    source_table=a['source_table'],source_rowid=a['source_rowid'],
                    correlation_id=a['correlation_id'],category=category,
                    semantic_role=semantic['role'],registry_rule_id=semantic['registry_rule_id'],
                    phase=phase(a),start_ns=a['start_ns'],end_ns=a['end_ns'],
                    activity_record_ids=[x['record_id'] for x in members],
                    sync_record_ids=[x['record_id'] for x in syncs]))
        output.append(dict(identity=identity,phase=phase(a),api_record_id=a['record_id'],api_name=a['api_name'],
            category=category,correlation_id=a['correlation_id'],physical_record_ids=[x['record_id'] for x in members+syncs],
            native_handle=handle,generation=generation,device_id=scope[0],context_id=scope[1],trace_stream_id=scope[2],
            model_forward_refs=[m['record_id'] for m in forwards if inside(a,m)],
            anchor_api_record_id=apis[0]['record_id'],anchor_sync_record_id=anchor_sync['record_id']))
    require(all(any(b['category']=='submit' and m['record_id'] in b['model_forward_refs'] for b in output)
        for m in forwards),'MODEL_FORWARD_EMPTY')
    require({s['record_id'] for s in rows['cuda_sync'] if s['end_ns']>start and s['start_ns']<end}==set(sync_ids),
            'MODEL_UNBOUND_PHYSICAL_SYNC')
    in_intervention=actual_waits(intervention) if intervention is not None else []
    require(len(in_intervention)==(1 if policy['variant']=='Vsync' else 0)
        and all(re.fullmatch(r'cudaStreamSynchronize(?:_v[1-9][0-9]*)?',a['api_name']) for a in in_intervention),
        'MODEL_INTERVENTION_ACTUAL_COUNT')
    return output,set(sync_ids),unsupported,(global_pid,*scope)


def calculate_n1_model(root,receipt_path,execution_path,bridge_path):
    require(bridge_path is not None,'MODEL_CALLS_REQUIRED')
    receipt,paths=load_input_receipt(receipt_path)
    manifest=_json(paths['wmpc_manifest']); policy=validate_manifest(manifest)
    ledger=_json(paths['pass_identity']); execution=_json(execution_path); calls=_json(bridge_path)
    support=validate_declaration(manifest)
    require(set(execution)=={'schema_version','manifest_sha256','producer_receipt_sha256','identity',
        'declaration','observed_configuration','status','n1_model_calls_sha256'}
        and execution['schema_version']==EXECUTION_VERSION and execution['status']=='COMPLETE'
        and execution['declaration']==support and execution['manifest_sha256']==digest(paths['wmpc_manifest'])
        and execution['producer_receipt_sha256']==digest(paths['producer_receipt'])
        and execution['identity']=={k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')}
        and execution['n1_model_calls_sha256']==digest(Path(bridge_path)),'MODEL_EXECUTION_IDENTITY')
    from .gate8_engineering_scope import _model_configuration,_diagnostics
    _model_configuration(execution['observed_configuration'],support)
    require(calls['schema_version']==CALL_VERSION and calls['pid']==ledger['pid']
        and calls['manifest_sha256']==digest(paths['wmpc_manifest'])
        and calls['producer_receipt_sha256']==digest(paths['producer_receipt']),'MODEL_CALLS_IDENTITY')
    require(len(ledger['requests'])==2 and all(r['outcome']=='COMPLETE' and not r['early_eos'] and not r['reasons']
        and r['actual_output_tokens']==r['expected_output_tokens']==2 for r in ledger['requests']),'MODEL_REQUEST_COMPLETION')
    require([r['identity'] for r in calls['requests']]==[r['identity'] for r in ledger['requests']], 'MODEL_LEDGER_JOIN')
    canonical=root/'canonical/canonical_manifest.json'; scope=root/'projection/scope.json'
    bundle=load_canonical_bundle(canonical)
    ownership,projections=load_projected_ownership(canonical,bundle,scope)
    from .gate8_stage_scope import derive_stage_diagnostics
    stages=derive_stage_diagnostics(canonical,paths['stage_ledger'])
    from .gate8_diagnostic_scope import load_diagnostic_scope
    from .gate9_diagnostic_review import review
    diagnostic=load_diagnostic_scope(root/'diagnostics.json',paths['sqlite'],paths['pass_identity'])
    disposition=review(diagnostic,bundle)
    from .gate8_request_scope import _drain
    p=next(p for p in projections if p['phase']=='full_request')
    drain_api,drain=_drain(paths['drain_ledger'],{'drain_ledger':{'filename':paths['drain_ledger'].name,
        'sha256':digest(paths['drain_ledger'])}},bundle,p,scope,canonical.parent)
    bound,sync_ids,unsupported,physical_scope=bindings(bundle,ownership,projections,calls,ledger,policy,drain_api,drain)
    with time_representation(SIGNED):
        with analysis_stage('n1_physical_s_inputs'):
            inputs=build_projected_ab_inputs(canonical,scope,isolated_nonblocking_scope=physical_scope)
        from .a_accounting import calculate_a_windows
        from .b_provenance import calculate_b_syncs
        with analysis_stage('n1_a_and_physical_b'):
            a=list(calculate_a_windows(inputs)); physical_b=list(calculate_b_syncs(inputs))
    b=[x for x in physical_b if x['sync_id'] in sync_ids]
    invalid=[dict(sync_id=x['sync_id'],reason=x['primary_reason'],secondary_reasons=x['secondary_reasons'])
             for x in b if x['validity']!='B_VALID']
    require(not unsupported,'MODEL_UNSUPPORTED_API:'+json.dumps(dict(
        unsupported_apis=unsupported,
        physical_b_failures=invalid,
        global_quality_reasons=list(inputs.global_quality_reasons),
        a_failure_reasons=[dict(phase=x['phase'],primary_reason=x['primary_reason'],
            secondary_reasons=x['secondary_reasons']) for x in a
            if x['primary_reason'] is not None or x['secondary_reasons']]),sort_keys=True))
    require(not inputs.global_quality_reasons and len(b)==len(sync_ids)>0
        and not invalid,'MODEL_PHYSICAL_B:'+json.dumps(invalid,sort_keys=True))
    require(len(a)==3 and all(x['primary_reason'] is None and not x['secondary_reasons'] for x in a),'MODEL_A_VALIDITY')
    return dict(schema_version=VERSION,adapter_version=ADAPTER,declaration=manifest['domain_qualification'],
        identity=receipt['identity'],status='QUALITY_CHECK_PASSED_NOT_QUALIFICATION',
        model_api_bindings=bound,a_records=a,b_records=b,physical_s_records=list(inputs.s_records),
        physical_b_records=physical_b,stage_diagnostics=stages,
        requests=[dict(identity=p['identity'],status='QUALITY_CHECK_PASSED_NOT_QUALIFICATION',a_records=a)],
        input_receipt_sha256=digest(Path(receipt_path)),execution_receipt_sha256=digest(Path(execution_path)),
        bridge_sha256=digest(Path(bridge_path)),diagnostic_dispositions=_diagnostics(diagnostic),
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',formal_eligible=False,
        n1_model_feasibility='PENDING_TARGET_EVIDENCE_REVIEW',d_score_allowed=False,signature_allowed=False,
        **({'diagnostic_review':disposition} if disposition is not None else {}))
