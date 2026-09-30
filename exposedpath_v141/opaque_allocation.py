"""Opt-in opaque occupancy proof; never a barrier, W builder or B producer."""
from collections import defaultdict
import re

from .allocation_semantics import describe_allocation
from .time_representation import timestamp,duration,opaque_allocation

CONTRACT='N1_OPAQUE_ALLOCATION_BUDGET/0.1.0'
REGISTRY='exposedpath-a-api-registry/0.2.0'


def require(ok,reason):
    if not ok: raise ValueError('OPAQUE_ALLOCATION_'+reason)


def interval(row):
    a=timestamp(row.get('start_ns'),'allocation start'); b=timestamp(row.get('end_ns'),'allocation end')
    require(b>=a,'BOUNDARY'); duration(b-a,'allocation duration')
    return a,b


def overlaps(left,right):
    return left[0]<right[1] and right[0]<left[1]


def admit_allocations(inputs,scope,drain_api_id):
    """Check observed single-stream closure, not the absence of invisible work.

    The verified model entrance supplies actual scope/drain references. All
    successful source records are rejoined here; missing facts never default.
    """
    require(opaque_allocation() and not inputs.global_quality_reasons,'VERSION_OR_QUALITY')
    require(isinstance(scope,tuple) and len(scope)==4,'SCOPE')
    rows=inputs.canonical.records; apis=rows['cuda_api']; acts=rows['device_activity']
    full=[w for w in inputs.windows if w.phase=='full_request']
    require(len(full)==1,'REQUEST_SET'); w=full[0]; win=(w.start_ns,w.end_ns)
    candidates=[a for a in apis if describe_allocation(a.get('api_name')) is not None
                and overlaps(interval(a),win)]
    if not candidates: return ()
    from .a_accounting import _api_ownership_reason
    ownership=inputs.canonical.projected_ownership or rows['nvtx']
    drains=[a for a in apis if a['record_id']==drain_api_id]
    require(len(drains)==1,'DRAIN'); d=drains[0]; ds=interval(d)
    require(d['return_value']==0 and ds[1]<=win[0]
        and re.fullmatch(r'cudaDeviceSynchronize(?:_v[1-9][0-9]*)?',d['api_name']),'DRAIN')
    tid=d['global_tid']; clock=d['clock_domain_id']; pid=d['process_id']
    require(tid-tid%2**24==scope[0],'PROCESS')
    physical=[s for s in rows['cuda_sync'] if s['runtime_record_id']==drain_api_id]
    require(len(physical)==1 and physical[0]['runtime_mapping_count']==1
        and physical[0]['clock_domain_id']==clock and physical[0]['correlation_id']==d['correlation_id']
        and tuple(physical[0][k] for k in ('global_pid','device_id','context_id'))==scope[:3]
        and ds[0]<=physical[0]['start_ns']<=physical[0]['end_ns']<=ds[1],'DRAIN_MAPPING')
    streams=[s for s in rows['stream'] if (s['process_id'],s['context_id'],s['stream_id'])==(pid,scope[2],scope[3])]
    contexts=[s for s in rows['context'] if (s['process_id'],s['device_id'],s['context_id'])==(pid,scope[1],scope[2])]
    require(len(streams)==len(contexts)==1 and streams[0]['flag']==2
            and contexts[0]['null_stream_id']!=scope[3],'NONBLOCKING_SCOPE')
    require(not any(e.get('process_id')==pid and (e.get('start_ns') is None or ds[0]<=e['start_ns']<win[1])
                    for e in rows.get('cuda_event',())), 'DEPENDENCY_UNBOUNDED')
    by_corr=defaultdict(list)
    for a in apis:
        if a.get('process_id')==pid: by_corr[a.get('correlation_id')].append(a)
    current=[a for a in apis if overlaps(interval(a),win)]
    from .a_api_classification import classify_a_api_name
    for a in current:
        span=interval(a)
        require(a['return_value']==0 and a['global_tid']==tid and a['clock_domain_id']==clock
                and win[0]<=span[0]<=span[1]<=win[1]
                and _api_ownership_reason(a,span,w,tuple(ownership)) is None,'API_OWNERSHIP')
        if classify_a_api_name(a['api_name'])[0] is None:
            matches=[s for s in rows['cuda_sync'] if s['runtime_record_id']==a['record_id']]
            require(len(matches)==1,'UNRESOLVED_DOWNSTREAM_API')
    for activity in acts:
        span=interval(activity)
        if activity.get('global_pid')==scope[0] and activity['end_ns']<=ds[0]: continue
        if not overlaps(span,(ds[0],win[1])): continue
        matching=by_corr.get(activity.get('correlation_id'),())
        require(len(matching)==1,'SUBMISSION_MAPPING'); a=matching[0]
        if a['end_ns']<=ds[0]:
            require(activity['end_ns']<=physical[0]['end_ns'],'DRAIN_PREFIX')
            continue
        require(tuple(activity[k] for k in ('global_pid','device_id','context_id','stream_id'))==scope
            and activity['clock_domain_id']==clock and a['global_tid']==tid and a['return_value']==0
            and win[0]<=a['start_ns']<=a['end_ns']<=win[1]
            and classify_a_api_name(a['api_name'])[0]=='submit','DEPENDENCY_UNBOUNDED')
    selected=[s for s in inputs.s_records if s.get('host_start_ns') is not None
              and overlaps((s['host_start_ns'],s['host_end_ns']),win)]
    require(selected and all(s['validity'] in ('VALID_NONEMPTY','VALID_EMPTY')
        and s['dependency_closure_status']=='COMPLETE'
        and s['terminal']['status']==('VALID' if s['validity']=='VALID_NONEMPTY' else 'NOT_APPLICABLE')
        and tuple(s[k] for k in ('device_id','context_id','stream_id'))==scope[1:]
        for s in selected),'DOWNSTREAM_SYNC_UNRESOLVED')
    require({s['record_id'] for s in rows['cuda_sync'] if overlaps(interval(s),win)}=={s['sync_id'] for s in selected},'SYNC_UNCONSUMED')
    result=[]
    for a in candidates:
        span=interval(a); corr=a['correlation_id']
        require(corr is not None and len(by_corr[corr])==1,'CORRELATION')
        require(not any(x['record_id']!=a['record_id'] and overlaps(interval(x),span) for x in apis),'NESTED_OR_OVERLAP')
        require(not any(x.get('correlation_id')==corr for x in acts)
                and not any(x['runtime_record_id']==a['record_id'] for x in rows['cuda_sync']),'MAPPING_CONFLICT')
        result.append(dict(contract_version=CONTRACT,registry_version=REGISTRY,
            classification='non_submit',subtype='OPAQUE_RESOURCE_MANAGEMENT',
            rule_id='A-OPAQUE-RESOURCE-CUDAMALLOC',api_record_id=a['record_id'],api_name=a['api_name'],
            source_table=a['source_table'],source_rowid=a['source_rowid'],correlation_id=corr,
            start_ns=span[0],end_ns=span[1],global_tid=tid,process_id=pid,clock_domain_id=clock,
            scope=list(scope),drain_api_record_id=drain_api_id,request_id=w.request_id,repeat_id=w.repeat_id,
            source_sqlite_sha256=inputs.canonical.manifest['source']['sqlite']['sha256'],
            pass_identity_sha256=inputs.canonical.manifest['gate8_sources']['pass_identity']['sha256'],
            downstream_sync_ids=[s['sync_id'] for s in selected],allocation_size_bytes=None,
            internal_wait_status='NOT_DECOMPOSED',completion_support='UNSUPPORTED'))
    return tuple(result)


def validate_admissions(inputs):
    proofs=inputs.opaque_allocation_admissions
    require(not proofs or opaque_allocation(),'VERSION')
    if not proofs: return
    expected=admit_allocations(inputs,tuple(proofs[0]['scope']),proofs[0]['drain_api_record_id'])
    require(proofs==expected,'SOURCE_MISMATCH')


def window_report(window,proofs,occupied):
    calls=[]
    for p in proofs:
        a=max(window.start_ns,p['start_ns']); b=min(window.end_ns,p['end_ns'])
        if a<b: calls.append(dict(api_record_id=p['api_record_id'],clip_start_ns=a,clip_end_ns=b,
                                 occupied_ns=b-a,allocation_size_bytes=None))
    return dict(contract_version=CONTRACT,registry_version=REGISTRY,subtype='OPAQUE_RESOURCE_MANAGEMENT',
                internal_wait_status='NOT_DECOMPOSED',occupied_non_submit_ns=occupied,calls=calls)
