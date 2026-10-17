"""Parameter evidence only. Never patches Canonical, production S/A/B or COE."""
import re
from .memset_same_capture import one,interval,within,name

VERSION='memset-prefill-parameters/0.1.0'
ZERO_RULE='MEMSET-ZERO-LOGICAL/0.1'


def require(ok,reason):
    if not ok:raise ValueError('MEMSET_PREFILL_'+reason)


def coverage(side,raw,expected):
    require(side.get('schema_version')=='memset-prefill-side/0.1.0'
        and side.get('role')=='ENGINEERING_MEMSET_PREFILL','ROLE_VERSION')
    scope=raw['scope'];require(scope==expected['scope'],'SCOPE')
    require(all(side.get(k)==scope[k] for k in ('run_id','pid','tid','creation_filetime')),'IDENTITY')
    require(side.get('entry')=='cudaMemsetAsync','ENTRY')
    require(all(side.get(k)==expected[k] for k in ('runtime_sha256','recorder_sha256')),'RUNTIME_IDENTITY')
    require(side.get('capacity')==4096 and all(type(side.get(k)) is int and side[k]==0 for k in
        ('attach_code','detach_code','recorder_error','begin_code','end_code')),'RECORDER')
    targets=[a for a in raw['apis'] if a['pid']==scope['pid'] and
        a['start']<scope['end'] and scope['start']<a['end'] and name(a['name']).startswith('cudaMemsetAsync')]
    require(all(name(a['name'])=='cudaMemsetAsync' and a['event_class']==0 for a in targets),'ENTRY')
    require(all(a['tid']==scope['tid'] for a in targets),'FOREIGN_THREAD')
    require(all(within(a,scope) for a in targets),'BOUNDARY')
    calls=side['calls'];require(bool(calls),'NO_TARGET_CALLS_NOT_DISCRIMINATING')
    require(len(calls)<=4096 and all(type(c['call_id']) is int for c in calls)
        and [c['call_id'] for c in calls]==list(range(1,len(calls)+1)),'CALLS')
    require(len(raw['ranges'])==len(calls),'RANGE_PAIR')
    used=set();out=[];last=scope['start']
    for c in calls:
        require(c['pid']==scope['pid'] and c['tid']==scope['tid'],'IDENTITY')
        require(type(c['count']) is int and 0<=c['count']<2**64 and type(c['value']) is int
            and -(2**31)<=c['value']<2**31 and type(c['pointer_alias']) is int and 0<=c['pointer_alias']<=4096
            and (c['count']==0 or c['pointer_alias']>0),'PARAMETERS')
        require(c['stream_hex']==scope['native_stream_hex'],'STREAM')
        require(type(c['forwards']) is int and c['forwards']==1 and c['completed'] is True,'FORWARDING')
        require(type(c['return_code']) is int and c['return_code']==0,'CALL_RETURN')
        push,pop=c['push_level'],c['pop_level']
        require(type(push) is int and type(pop) is int and ((push>=0 and push==pop) or (push,pop)==(-1,-1)),'NVTX_RETURN')
        nr=one((v for v in raw['ranges'] if v['call_id']==c['call_id']),'RANGE_PAIR')
        require(all(nr[k]==scope[k] for k in ('run_id','pid','tid')) and nr['event_type']==59
            and within(nr,scope) and nr['start']>=last,'RANGE_PAIR');last=nr['end']
        d=one((v for v in raw['domains'] if v['pid']==scope['pid'] and v['domain_id']==nr['domain_id']),'DOMAIN')
        require(d['event_type']==75 and d['name']=='EP_MEMSET_PREFILL' and d['start']<=nr['start'] and nr['domain_id']>0,'DOMAIN')
        a=one((a for a in targets if within(a,nr)),'RUNTIME_PAIR')
        require(a['record_id'] not in used and a['return_code']==c['return_code'],'RUNTIME_PAIR');used.add(a['record_id'])
        require(len([v for v in raw['apis'] if v['pid']==scope['pid'] and v['correlation_id']==a['correlation_id']])==1,'CORRELATION')
        effects=[v for v in raw['effects'] if v['pid']==scope['pid'] and v['correlation_id']==a['correlation_id']]
        if c['count']==0:
            require(not any(e['kind']=='MEMSET' and type(e.get('bytes')) is int and e['bytes']>0 for e in effects),'ZERO_EFFECT_CONFLICT')
            require(not effects,'ZERO_DEVICE_RECORD_UNSUPPORTED');state='ZERO_PAYLOAD_LOGICAL_ONLY'
        else:
            require(effects,'NONZERO_EFFECT_MISSING');effect=one(effects,'EFFECT')
            require(effect['kind']=='MEMSET' and effect['bytes']==c['count'] and effect['value']==(c['value']&255)
                and interval(effect) and a['start']<=effect['start'] and effect['end']<=scope['end']
                and all(effect[k]==scope[k] for k in ('device_id','context_id','stream_id')),'EFFECT')
            state='NONZERO_DEVICE_EFFECT_MAPPED'
        out.append(dict(call_id=c['call_id'],api_id=a['record_id'],range_id=nr['record_id'],count=c['count'],
            pointer_alias=c['pointer_alias'],value=c['value'],return_code=c['return_code'],
            state=state,api_wall_ns=a['end']-a['start'],effect_ids=[v['record_id'] for v in effects],
            start=a['start'],end=a['end'],native_stream_hex=c['stream_hex'],
            original_nvtx_returns=[push,pop],ordering='REQUIRES_SCOPE_PROOF' if not c['count'] else 'EXISTING_EFFECT_RULE'))
    require(len(targets)==len(used) and {a['record_id'] for a in targets}==used,'RUNTIME_COVERAGE')
    return dict(schema_version=VERSION,status='PARAMETERS_COVERED_SCOPE_NOT_YET_ADMITTED',calls=out,
        synthetic_activities=[],a_admission='NOT_ASSESSED',coe_admission='NOT_ASSESSED',dropped_records_status='UNKNOWN')


def zero_scope(p):
    """Closed FIFO proof over *real* members; zero nodes never become activities.

    This small rule consumes independently recovered real dependency graphs.
    It is not an alternative S algorithm or an acceptance flag for a model run.
    """
    require(type(p['drain_end']) is int and p['drain_end']<=p['request_start'],'DRAIN')
    require(all(r['end']<=p['drain_end'] for r in p['prefix']),'PREFIX_PENDING')
    require(p['scope_closed'] is True and not p['foreign_apis'],'SCOPE')
    require(not any(p[k] for k in ('unknown_dependencies','events','graphs')),'DEPENDENCY')
    require(type(p['sync_return']) is int and p['sync_return']==0
        and p['request_start']<=p['sync_start']<p['sync_end']<=p['completion_end'],'SYNC')
    a=p['activities'];require(a and len({r['id'] for r in a})==len(a),'MEMBERS')
    require(all(r['stream']==p['stream'] for r in a),'SCOPE')
    require(all(p['request_start']<=r['submit_start']<=r['submit_end']<=p['sync_start']
        and r['submit_start']<=r['start']<r['end']<=p['sync_end'] for r in a),'SUBMISSION')
    require(set(p['modes'])=={'LEGACY','PER_THREAD'} and p['modes']['LEGACY']==p['modes']['PER_THREAD'],'MODE')
    graph=p['modes']['LEGACY'];ids={r['id'] for r in a}
    require(len(graph['members'])==len(ids) and set(graph['members'])==ids,'MEMBERS')
    # The validated same-stream order supplies an independent finite invariant:
    # inserting a Host-only zero or an ordered empty node cannot change the
    # transitive order among real FIFO members. Verify that order, not A equality.
    ordered=sorted(a,key=lambda r:(r['submit_start'],r['submit_end']))
    require(all(x['submit_end']<=y['submit_start'] for x,y in zip(ordered,ordered[1:])),'SUBMISSION')
    # Strict one-FIFO domain: adjacent real submissions must have the original
    # FIFO edge; all edges must point forward. Linear verification avoids an
    # unnecessary quadratic transitive-closure materialization on model traces.
    positions={r['id']:i for i,r in enumerate(ordered)};edges={tuple(e) for e in graph['edges']}
    require(all(x in positions and y in positions and positions[x]<positions[y] for x,y in edges)
        and all((x['id'],y['id']) in edges for x,y in zip(ordered,ordered[1:])),'DEPENDENCY')
    terminal=ordered[-1]
    require(graph['terminal']==terminal['id']==p['copy_id'] and terminal['end']==max(r['end'] for r in a),'TERMINAL')
    for z in p['zero_calls']:
        require(p['request_start']<=z['start']<=z['end']<=terminal['submit_start']
            and z['native_stream_hex']=='0','ZERO_FRONTIER')
    return dict(schema_version=ZERO_RULE,admission='PARAMETER_SUPPORT_ONLY_NOT_COE_OR_A',
        logical_calls=[r['api_id'] for r in p['zero_calls']],real_members=graph['members'],
        real_dependency_edges=graph['edges'],terminal=graph['terminal'],synthetic_activities=[],
        zero_ordering='HOST_ONLY_OR_EMPTY_FIFO_NODE_REAL_GRAPH_INVARIANT',pure_wait_claim=False)


def read_raw(path,scope):
    """Same-capture 2026.2 provider. Explicit range identity, never nearest time."""
    import sqlite3
    from pathlib import Path
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        db.row_factory=sqlite3.Row
        strings=dict(db.execute('SELECT id,value FROM StringIds'))
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require({'CUPTI_ACTIVITY_KIND_RUNTIME','CUPTI_ACTIVITY_KIND_MEMSET','NVTX_EVENTS'}<=tables,'PROVIDER_TABLES')
        def rows(table):return [dict(r) for r in db.execute('SELECT rowid AS source_rowid,* FROM '+table)]
        apis=[];ranges=[];domains=[];effects=[]
        for r in rows('CUPTI_ACTIVITY_KIND_RUNTIME'):
            apis.append(dict(record_id='cuda_api:'+str(r['source_rowid']),name=strings[r['nameId']],
                start=r['start'],end=r['end'],pid=(r['globalTid']>>24)&0xffffff,tid=r['globalTid']&0xffffff,
                correlation_id=r['correlationId'],return_code=r['returnValue'],event_class=r['eventClass']))
        for r in rows('NVTX_EVENTS'):
            text=r.get('text') or strings.get(r.get('textId'),'')
            if r['eventType']==75:
                domains.append(dict(pid=(r['globalTid']>>24)&0xffffff,domain_id=r.get('domainId'),
                    name=text,event_type=75,start=r['start']))
            if not text.startswith('EP_MEMSET_PREFILL:'):continue
            m=re.fullmatch('EP_MEMSET_PREFILL:([0-9a-f]{32}):([1-9][0-9]*)',text)
            require(m is not None and m[1]==scope['run_id'],'RANGE_IDENTITY')
            require(r.get('endGlobalTid') in (None,r['globalTid']),'RANGE_THREAD')
            ranges.append(dict(record_id='nvtx:'+str(r['source_rowid']),run_id=m[1],call_id=int(m[2]),
                pid=(r['globalTid']>>24)&0xffffff,tid=r['globalTid']&0xffffff,start=r['start'],end=r['end'],
                event_type=r['eventType'],domain_id=r.get('domainId')))
        for table,kind in [('CUPTI_ACTIVITY_KIND_MEMSET','MEMSET'),('CUPTI_ACTIVITY_KIND_KERNEL','KERNEL'),('CUPTI_ACTIVITY_KIND_MEMCPY','MEMCPY')]:
            if table not in tables:continue
            for r in rows(table):
                effects.append(dict(record_id=kind+':'+str(r['source_rowid']),kind=kind,pid=(r['globalPid']>>24)&0xffffff,
                    correlation_id=r['correlationId'],bytes=r.get('bytes'),value=r.get('value'),device_id=r['deviceId'],
                    context_id=r['contextId'],stream_id=r['streamId'],start=r['start'],end=r['end']))
    return dict(scope=scope,apis=apis,ranges=ranges,domains=domains,effects=effects)


def process(receipt_path,execution_path,output):
    """New profile only; report parameter/scope evidence, not accepted A/COE.

    A temporary validation view discharges *only* independently covered zero
    submit rows. Original Canonical/API intervals are never altered. Existing
    scope gates still see every real activity and every other API. Their A is
    discarded; no production result is published or upgraded.
    """
    from copy import deepcopy
    from pathlib import Path
    import json
    from exposedpath import memset_prefill as contract
    from exposedpath.gate8_isolated_preflight import read,sha,write_new
    from exposedpath_v141 import gate8_engineering_scope as base
    from exposedpath_v141.canonical_raw import convert_sqlite_to_canonical
    from exposedpath_v141.sync_semantics import load_canonical_bundle,build_semantic_inventory
    from exposedpath_v141.gate8_scope import project_completion_scopes,load_projected_ownership,build_projected_ab_inputs
    from exposedpath_v141.gate8_stage_scope import derive_stage_diagnostics
    from exposedpath_v141.gate8_diagnostic_scope import write_diagnostic_scope
    from exposedpath_v141.gate9_diagnostic_review import review
    from exposedpath_v141.time_representation import SIGNED,time_representation
    receipt,paths,declared,execution=base._inputs(receipt_path,execution_path)
    mf=read(paths['wmpc_manifest']);b=contract.validate(mf)
    side_path=Path(execution_path).parent/'memset_parameters.json';side=read(side_path)
    started_path=Path(execution_path).parent.with_name('diagnostic-entry')/'started.json';started=read(started_path)
    ledger=read(paths['pass_identity']);measured=one((r for r in ledger['requests'] if r['request_role']=='measured'),'REQUEST')
    require(side.get('identity')==measured['identity'] and side.get('completion_observed') is True
        and started['pid']==ledger['pid']==side['pid'] and started['creation_filetime']==side['creation_filetime'],'PROCESS_INSTANCE')
    hashes={str(p):sha(p) for p in (Path(receipt_path),Path(execution_path),side_path,started_path,*paths.values())}
    out=Path(output).resolve();require(not any(Path(p).resolve().is_relative_to(out) for p in hashes),'OUTPUT_CONTAINS_INPUT')
    out.mkdir(parents=True,exist_ok=False)
    canonical=convert_sqlite_to_canonical(paths['sqlite'],out/'canonical','Engineering',raw_sha256=sha(paths['raw']),
        collector_version=receipt['collector_version'],gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
    scope_path=out/'projection/scope.json';project_completion_scopes(canonical,paths['host_ledger'],scope_path)
    bundle=load_canonical_bundle(canonical);ownership,projections=load_projected_ownership(canonical,bundle,scope_path)
    projection=one((p for p in projections if p['phase']=='prefill'),'PREFILL')
    diag=write_diagnostic_scope(paths['sqlite'],paths['pass_identity'],out/'diagnostics.json')
    disposition=review(diag,bundle);accepted=set(disposition['accepted_rowids']) if disposition else set()
    effective=[r for r in base._diagnostics(diag) if r['source_rowid'] not in accepted]
    stage=derive_stage_diagnostics(canonical,paths['stage_ledger'])
    drain_api,drain=base._drain(paths['drain_ledger'],{'drain_ledger':{'filename':paths['drain_ledger'].name,'sha256':sha(paths['drain_ledger'])}},
        bundle,projection,scope_path,canonical.parent)
    global_tid=drain_api['global_tid'];null=one((c for c in bundle['records']['context'] if c['context_id']==drain['context_id']),'CONTEXT')['null_stream_id']
    scope=dict(run_id=b['run_id'],pid=ledger['pid'],tid=global_tid&0xffffff,creation_filetime=started['creation_filetime'],
        start=projection['start_ns'],end=projection['end_ns'],device_id=drain['device_id'],context_id=drain['context_id'],
        stream_id=null,native_stream_hex='0',clock_id='NSYS_TRACE_NS')
    raw=read_raw(paths['sqlite'],scope)
    covered=coverage(side,raw,dict(scope=scope,runtime_sha256=b['runtime']['sha256'],recorder_sha256=b['recorder']['sha256']))
    # Provider row IDs must be joined explicitly to the unchanged Canonical IDs.
    by_row={a['source_rowid']:a for a in bundle['records']['cuda_api']}
    for c in covered['calls']:
        row=int(c['api_id'].split(':')[1]);require(row in by_row,'CANONICAL_API')
        c['api_id']=by_row[row]['record_id']
    zeros=[c for c in covered['calls'] if c['count']==0];ids={c['api_id'] for c in zeros}
    view=deepcopy(bundle);view['records']['cuda_api']=[a for a in view['records']['cuda_api'] if a['record_id'] not in ids]
    stage_view=deepcopy(stage)
    for s in stage_view['stages']:s['unresolved_submissions']=[u for u in s['unresolved_submissions'] if u['api_ref']['record_id'] not in ids]
    with time_representation(SIGNED):
        original=build_projected_ab_inputs(canonical,scope_path) # Contains ALL original API budgets.
        local=base._request(canonical,scope_path,paths,view,ownership,projection,original,stage_view,declared,effective,
            domain_proof=True,selected_phase='prefill')
    require(local['status']=='A_SCOPE_ENGINEERING_ONLY','LOCAL_SCOPE:'+json.dumps(local['reasons']))
    # Use the same explicit token-ready range and copy/sync selection, not the
    # longest copy or an assumed record number.
    from .coe_candidate import _canonical_records,select_pair,validate_operation_identity
    apis,effects=_canonical_records(bundle)
    nvtx=[];points=[]
    for n in bundle['records']['nvtx']:
        t=n.get('text') or ''
        if not t.startswith(('EXPOSEDPATH_JSON_V1:','EXPOSEDPATH_BOUNDARY_V1:')):continue
        p=json.loads(t.split(':',1)[1]);identity=p.get('identity',p)
        if not all(identity.get(k)==v for k,v in measured['identity'].items()):continue
        if p.get('sync_origin')=='natural_token_ready' and p.get('token_index')==0:nvtx.append((n,p))
        if p.get('boundary_kind')=='token_ready' and p.get('token_index')==0:points.append((n,p))
    token_range,payload=one(nvtx,'TOKEN_RANGE');point,payload_point=one(points,'TOKEN_POINT')
    validate_operation_identity(measured['identity'],payload,payload_point,0,'prefill')
    require(token_range['global_tid']==point['global_tid']==global_tid and token_range['start_ns']<=point['start_ns']<=token_range['end_ns'],'TOKEN_THREAD')
    copy,sync=select_pair(apis,thread=global_tid,start=token_range['start_ns'],end=token_range['end_ns'])
    inventory=build_semantic_inventory({**bundle,'ownership_records':ownership})
    aa={a['record_id']:a for a in inventory['activities']}
    final=one((s for s in inventory['syncs'] if s['runtime_record_id']==sync['id']),'SYNC')
    modes={}
    for mode_proof in local['facts']['conditional_suffix_proofs']:
        s=one((s for s in mode_proof['syncs'] if s['sync_id']==final['record_id']),'SYNC_PROOF')
        real=s['suffix_activity_ids'];edges=[[e['from'],e['to']] for e in s['dependency_edges']]
        terminals=set(real)-{e[0] for e in edges}
        modes[mode_proof['mode']]=dict(members=real,edges=edges,terminal=one(terminals,'TERMINAL'))
    real=[aa[k] for k in modes['LEGACY']['members']]
    d2h=one((a for a in real if a['enqueue_record_id']==copy['id'] and a['activity_kind']=='MEMCPY'),'COPY_EFFECT')
    from scripts.analyze_completion_operation_candidate import enum_name,verify_device_bridge
    import sqlite3
    attrs=d2h['attributes']
    with sqlite3.connect(paths['sqlite'].resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        db.row_factory=sqlite3.Row
        require(enum_name(db,'ENUM_CUDA_MEMCPY_OPER',attrs['copy_kind'])=='CUDA_MEMCPY_KIND_DTOH'
            and enum_name(db,'ENUM_CUDA_MEM_KIND',attrs['src_kind'])=='CUDA_MEMOPR_MEMORY_KIND_DEVICE'
            and enum_name(db,'ENUM_CUDA_MEM_KIND',attrs['dst_kind'])=='CUDA_MEMOPR_MEMORY_KIND_PAGEABLE'
            and attrs['bytes']==16,'TOKEN_COPY_PROFILE')
        bridge=verify_device_bridge(db,ledger['pid'],scope['device_id'],scope['context_id'],read(paths['cuda_probe']),read(paths['preflight']))
    p=dict(scope_closed=True,drain_end=drain['end_ns'],request_start=scope['start'],completion_end=scope['end'],
        zero_calls=zeros,activities=[dict(id=a['record_id'],submit_start=a['enqueue_start_ns'],submit_end=a['enqueue_end_ns'],
            start=a['start_ns'],end=a['end_ns'],stream=a['stream_id']) for a in real],
        prefix=[dict(id=k,end=aa[k]['end_ns']) for k in local['facts']['prefix_activity_ids']],stream=null,copy_id=d2h['record_id'],
        sync_start=sync['start'],sync_end=sync['end'],sync_return=sync['return_code'],
        unknown_dependencies=[],events=inventory['event_records'],graphs=[],foreign_apis=[],modes=modes)
    proof=zero_scope(p)
    require(all(sha(path)==h for path,h in hashes.items()),'INPUT_CHANGED')
    result=dict(schema_version=VERSION,status='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW',
        role='Engineering',binding=b,input_identity=mf['memset_input'],coverage=covered,scope_proof=proof,
        scope_evidence=p,source_hashes=hashes,diagnostic_disposition=disposition,device_bridge=bridge,
        scope_guard_facts=local['facts'],validation_view_excluded_api_ids=sorted(ids),
        canonical_manifest_sha256=sha(canonical),analysis_source_sha256=sha(__file__),zero_rule=ZERO_RULE,
        a_admission='NOT_ASSESSED',coe_admission='NOT_ASSESSED',request_status='NOT_ACCEPTED',decode_status='NOT_ACCEPTED',
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',formal_eligible=False)
    write_new(out/'parameters.json',result)
    return out/'parameters.json'


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--receipt',required=True);p.add_argument('--execution',required=True);p.add_argument('--output',required=True)
    args=p.parse_args();print(process(args.receipt,args.execution,args.output),flush=True)
