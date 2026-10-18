"""Narrow API22 micro diagnostic. Not a Canonical provider or S/A/COE adapter."""
import hashlib
import json
from pathlib import Path

VERSION='independent-cupti-memset/0.1.0'


def require(ok, reason):
    if not ok:raise ValueError('CUPTI_MICRO_'+reason)


def integer(v, low=0, high=2**64-1):
    return type(v) is int and low<=v<=high


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def review(v, *, expected=None):
    require(v.get('schema_version')==VERSION,'VERSION')
    require(v.get('source') in ('HOST_CALLBACK_DOUBLE','TARGET_GPU'),'SOURCE')
    require(v.get('error','')=='','NATIVE_ERROR')
    require(v.get('role')=='ENGINEERING_PARAMETER_DIAGNOSTIC','ROLE')
    require(v.get('runtime_version')==12040 and v.get('cupti_api_version')==22,'VERSION')
    require(v.get('clock')=='CUPTI_TIMESTAMP_NS' and isinstance(v.get('run_id'),str)
        and v['run_id'] and integer(v.get('pid'),1) and integer(v.get('tid'),1),'IDENTITY')
    if v['source']=='TARGET_GPU':
        require(type(expected) is dict and all(expected.get(k)==v.get(k) for k in
            ('run_id','runtime_sha256','cupti_sha256')) and
            all(isinstance(expected.get(k),str) and len(expected[k])==64 for k in
                ('runtime_sha256','cupti_sha256')),'TARGET_BINDING')
    names=v.get('callback_names',{})
    require(all(isinstance(names.get(k),str) and names[k] for k in ('ordinary','ptsz')) and
        v.get('callback_name_source')==('CUPTI_GET_CALLBACK_NAME' if v['source']=='TARGET_GPU' else 'HOST_CALLBACK_DOUBLE'),
        'CALLBACK_NAME_REGISTRY')
    life=v.get('lifecycle',{})
    require(all(type(life.get(k)) is int and life[k]==0 for k in
        ('subscribe','register_buffers','enable','flush','disable','unsubscribe','finalize'))
        and life.get('closed') is True,'LIFECYCLE')
    loss=v.get('loss',{})
    require(all(type(loss.get(k)) is int and loss[k]==0 for k in
        ('callback_overflow','activity_overflow','buffer_exhaustion','callback_error','activity_error',
         'dropped_records','dropped_query_errors','outstanding_buffers')),'LOSS_OR_OVERFLOW')
    require(integer(loss.get('dropped_queries'),1),'DROPPED_QUERY_UNKNOWN')
    b=v.get('stream_binding',{})
    require(b.get('query_status')==0 and integer(b.get('context_uid'),1) and
        integer(b.get('stream_id'),1) and integer(b.get('device_id')) and
        all(isinstance(b.get(k),str) and b[k].startswith('0x') and int(b[k],16)>0
            for k in ('native_context','native_stream')),'STREAM_BINDING')
    calls={};callback_keys=set()
    for c in v['callbacks']:
        require(integer(c.get('call_id'),1) and c['call_id'] not in calls,'CALL_ID_DUPLICATE')
        calls[c['call_id']]=c
        require(c.get('domain') in ('RUNTIME','DRIVER'),'DOMAIN')
        require(c.get('pid')==v['pid'] and c.get('tid')==v['tid'] and
            c.get('context_uid')==b['context_uid'] and c.get('native_context')==b['native_context'],'CALL_SCOPE')
        require(c.get('entry_seen') is True and c.get('exit_seen') is True and
            integer(c.get('enter_seq'),1) and integer(c.get('exit_seq'),c['enter_seq']+1),'ENTRY_EXIT')
        require(integer(c.get('correlation_id'),1,2**32-1) and integer(c.get('cbid'),1),'CALL_IDENTITY')
        key=(c['domain'],c['correlation_id'])
        require(key not in callback_keys,'CALLBACK_CORRELATION_DUPLICATE');callback_keys.add(key)
        require(type(c.get('return_code')) is int and c['return_code']==0,'CALL_FAILED')
        if c['domain']=='RUNTIME':
            require(c.get('params_copied') is True and integer(c.get('count')) and
                type(c.get('value')) is int and c.get('native_stream')==b['native_stream'] and
                isinstance(c.get('pointer'),str) and int(c['pointer'],16)>0,'PARAMETERS_MISSING')
            require((c['cbid'],c.get('name'),c.get('entry_kind'))==
                (51,'cudaMemsetAsync','ORDINARY'),'ENTRY_NOT_QUALIFIED')
            require(c.get('observed_name') in ('cudaMemsetAsync',names['ordinary']),'CALLBACK_NAME')
    runtime=[c for c in calls.values() if c['domain']=='RUNTIME']
    require(len(runtime)==2,'RUNTIME_COVERAGE')
    runtime.sort(key=lambda c:c['enter_seq'])
    require([c['count'] for c in runtime]==[0,64] and
        all(c['value']==123 for c in runtime) and runtime[0]['pointer']==runtime[1]['pointer'] and
        runtime[0]['exit_seq']<runtime[1]['enter_seq'],'MICRO_PLAN')
    api={}
    for a in v['api_records']:
        key=(a.get('domain'),a.get('correlation_id'))
        require(key not in api,'API_ID_DUPLICATE');api[key]=a
    for c in calls.values():
        a=api.get((c['domain'],c['correlation_id']))
        require(a is not None and a.get('cbid')==c['cbid'] and a.get('pid')==c['pid']
            and a.get('tid')==c['tid'] and a.get('return_value')==c['return_code']
            and integer(a.get('start'),1) and integer(a.get('end'),a['start']),'API_COVERAGE')
        if c['domain']=='DRIVER':
            p=calls.get(c['parent_call_id'])
            require(p is not None and p['domain']=='RUNTIME' and
                p['enter_seq']<c['enter_seq']<c['exit_seq']<p['exit_seq'],'DRIVER_PARENTAGE')
            parent_api=api.get(('RUNTIME',p['correlation_id']))
            require(parent_api is not None and parent_api['start']<=a['start']<=a['end']<=parent_api['end'],
                'API_PARENT_INTERVAL')
    wanted={(c['domain'],c['correlation_id']) for c in runtime}
    observed={(a['domain'],a['correlation_id']) for a in v['api_records']
              if a['domain']=='RUNTIME' and a['cbid'] in (51,235)}
    require(wanted==observed,'RUNTIME_COVERAGE')
    effects={}
    for e in v['effects']:
        require(e.get('record_id') and e['record_id'] not in effects,'EFFECT_ID_DUPLICATE')
        effects[e['record_id']]=e
        require(e.get('correlation_domain')=='DRIVER','EFFECT_CORRELATION_DOMAIN')
        require(all(e.get(k)==b[k] for k in ('context_uid','stream_id','device_id'))
            and e.get('graph_id')==0 and integer(e.get('start'),1) and
            integer(e.get('end'),e['start']),'EFFECT_SCOPE')
    refs=v.get('references',[])
    require(len(refs)==2 and all(r.get('case_index')==i and r.get('success') is True and
        r.get('count')==[0,64][i] and r.get('value')==123 and
        r.get('readback')==([58]*64 if i==0 else [123]*64) for i,r in enumerate(refs)),
        'INDEPENDENT_READBACK')
    results=[];used=set()
    for c in runtime:
        ds=[x for x in calls.values() if x['domain']=='DRIVER' and x['parent_call_id']==c['call_id']]
        ids={x['correlation_id'] for x in ds}
        es=[e for e in effects.values() if e['correlation_id'] in ids]
        if c['count']:
            require(len(es)==1,'NONZERO_EFFECT_MISSING')
            require(es[0]['bytes']==64 and es[0]['value']==(c['value']&255),'EFFECT_PAYLOAD')
        else:require(all(e['bytes']==0 for e in es),'ZERO_EFFECT_CONFLICT')
        used.update(e['record_id'] for e in es)
        results.append(dict(runtime_correlation=c['correlation_id'],driver_correlations=sorted(ids),
            count=c['count'],native_stream=c['native_stream'],return_code=c['return_code'],
            effect_records=[e['record_id'] for e in es]))
    require(used==set(effects),'UNASSIGNED_EFFECT')
    return dict(schema_version='independent-cupti-memset-review/0.1.0',
        status='MICRO_PARAMETER_EFFECT_PASS_LIMITED',source=v['source'],cases=results,
        target_gpu_validated=v['source']=='TARGET_GPU',pytorch_coverage='NOT_ASSESSED',
        zero_byte_dependency_qualification='NOT_ASSESSED',A_COE_admission='NOT_ASSESSED',
        old_instance_repair=False)


def review_file(path, output, *, expected=None):
    p=Path(path);out=Path(output)
    if out.exists():raise FileExistsError(out)
    raw=p.read_bytes();v=json.loads(raw)
    result=review(v,expected=expected)
    r=dict(input=dict(file=p.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest()),result=result)
    out.mkdir(parents=True,exist_ok=False)
    with (out/'review.json').open('x',encoding='utf8') as f:json.dump(r,f,indent=2)
    return r
