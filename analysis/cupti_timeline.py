"""Explicit new CUPTI source -> evidence bridge -> local S/COE.

No Nsight SQLite, rowid, clock name or validity flag is fabricated. This does
not qualify a provider/model by itself; its scope must come from a separately
bound producer, and its single-FIFO assumptions remain visible in the result.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from exposedpath_v141.submit_effect_bridge import analyze_scope,normal,require,DRIVER_SUBMITS

VERSION='cupti-timeline-adapter/0.1.0'


def marker_ranges(rows):
    stacks={};ranges=[];points=[];last={}
    for m in rows:
        tid=m['tid'];t=m['time'];action=m['action'];stack=stacks.setdefault(tid,[])
        require(type(t) is int and t>=last.get(tid,0) and isinstance(m['label'],str),'MARKER_ORDER')
        last[tid]=t
        if action==0:points.append(dict(label=m['label'],tid=tid,time=t))
        elif action==1:stack.append(m)
        elif action==2:
            require(stack and m['label']=='','MARKER_STACK')
            p=stack.pop();ranges.append(dict(label=p['label'],tid=tid,start=p['time'],end=t))
        else:require(False,'MARKER_KIND')
    require(all(not s for s in stacks.values()),'MARKER_UNCLOSED')
    return dict(ranges=ranges,points=points)


def select_scope(raw,producer):
    """Join original producer labels to this capture's own CUPTI clock.

    Producer/token files must be bound by the caller's input manifest. This
    verifies their marker and physical completion joins, not file authenticity.
    """
    require(raw['session_id']==producer['session_id'] and raw['pid']==producer['pid'],'SESSION')
    require(producer.get('actual_token_ids') and all(type(t) is int and t>=0 for t in producer['actual_token_ids']),'TOKEN')
    tid=producer['tid'];parsed=marker_ranges(raw['markers'])
    def one(rows,reason):
        rows=list(rows);require(len(rows)==1,reason);return rows[0]
    labels={'drain_label':'EXPOSEDPATH_DRAIN_V1:','request_label':'EXPOSEDPATH_BOUNDARY_V1:',
        'helper_label':'EXPOSEDPATH_JSON_V1:','token_label':'EXPOSEDPATH_BOUNDARY_V1:'}
    for name,prefix in labels.items():
        label=producer[name];require(isinstance(label,str) and label.startswith(prefix),'PRODUCER_LABEL')
        payload=json.loads(label[len(prefix):])
        # The real structured helper label is flat; drain/boundary identities
        # are nested. These are explicit source schemas, not a guessed fallback.
        identity=payload if name=='helper_label' else payload['identity']
        require(identity['run_id']==producer['run_id'],'PRODUCER_IDENTITY')
    dr=one((r for r in parsed['ranges'] if r['tid']==tid and r['label']==producer['drain_label']),'DRAIN_RANGE')
    helper=one((r for r in parsed['ranges'] if r['tid']==tid and r['label']==producer['helper_label']),'HELPER_RANGE')
    start=one((r for r in parsed['points'] if r['tid']==tid and r['label']==producer['request_label']),'REQUEST_POINT')['time']
    end=one((r for r in parsed['points'] if r['tid']==tid and r['label']==producer['token_label']),'TOKEN_POINT')['time']
    calls={(c['domain'],c['pid'],c['correlation']):c for c in raw['callbacks']}
    apis=[]
    for r in raw['records']:
        if r['kind']=='API' and r['domain']=='RUNTIME':
            c=calls.get((r['domain'],r['pid'],r['correlation']));require(c is not None,'API_CALLBACK')
            apis.append({**r,'name':normal(c['name'])})
    drain=one((a for a in apis if a['name']=='cudaDeviceSynchronize' and a['tid']==tid and
        dr['start']<=a['start']<=a['end']<=dr['end']),'DRAIN_API')
    copy=one((a for a in apis if a['name']=='cudaMemcpyAsync' and a['tid']==tid and
        helper['start']<=a['start']<=a['end']<=helper['end']),'COPY_API')
    sync=one((a for a in apis if a['name']=='cudaStreamSynchronize' and a['tid']==tid and
        helper['start']<=a['start']<=a['end']<=helper['end']),'SYNC_API')
    require(all(a['return_code']==0 for a in (drain,copy,sync)),'FAILED_COMPLETION')
    c=calls[(copy['domain'],copy['pid'],copy['correlation'])]
    require(drain['end']<=start<=helper['start']<=copy['start']<=copy['end']<=sync['start']<=sync['end']<=end<=helper['end'],'COMPLETION_ORDER')
    scope=dict(session_id=producer['session_id'],pid=producer['pid'],tid=tid,device=c['device'],
        context=c['context'],stream=c['stream'],drain_end=drain['end'],request_start=start,completion_end=end,
        copy_api=copy['id'],sync_api=sync['id'],completion_proof='HOST_TOKEN_READABLE',
        actual_token_ids=deepcopy(producer['actual_token_ids']),ownership='CLOSED_SINGLE_FIFO_NO_EVENTS_OR_GRAPHS')
    evidence=to_evidence(raw,scope)
    physical=one((s for s in evidence['synchronizations'] if s['domain']=='RUNTIME' and
        s['correlation']==drain['correlation'] and s['flags']==4),'DRAIN_PHYSICAL_SYNC')
    require(physical['context']==scope['context'] and drain['start']<=physical['start']<=physical['end']<=drain['end'],'DRAIN_SCOPE')
    return scope


def to_evidence(raw,scope):
    require(raw.get('schema_version')=='cupti-timeline-capture/0.1.0','CAPTURE_VERSION')
    if 'initialization' in raw:
        from exposedpath.cupti_timeline import validate_startup_data
        require(validate_startup_data(raw)['succeeded'],'STARTUP_FAILED')
    require(raw['session_id']==scope['session_id'] and raw['pid']==scope['pid'],'SESSION')
    all_calls={c['id']:c for c in raw['callbacks']}
    require(len(all_calls)==len(raw['callbacks']),'CALLBACK_DUPLICATE')
    # CUPTI startup can precede active API correlation. Only a closed historical
    # node before the physical drain may be omitted from this local view. Keep
    # the original capture immutable and list every such source ID explicitly.
    removed={c['id'] for c in all_calls.values() if c['correlation']==0 and c['end']<=scope['drain_end'] and c.get('closed') is True}
    while True:
        more={c['id'] for c in all_calls.values() if c.get('parent_id') in removed and c['end']<=scope['drain_end'] and c.get('closed') is True}
        if more<=removed:break
        removed.update(more)
    calls={k:c for k,c in all_calls.items() if k not in removed}
    keys={(c['domain'],c['pid'],c['correlation']):c for c in calls.values()}
    require(len(keys)==len(calls),'CALLBACK_CORRELATION_DUPLICATE')
    for c in calls.values():
        require(c.get('closed') is True,'CALLBACK_UNCLOSED')
        if scope['request_start']<=c['start']<scope['completion_end']:
            require(c.get('ptsz') is False,'ENTRY_NOT_QUALIFIED')
            if normal(c['name']) in ('cudaLaunchKernel','cudaMemsetAsync','cudaMemcpyAsync','cudaStreamSynchronize') or (
                c['domain']=='DRIVER' and c.get('parent_id') is None and normal(c['name']) in DRIVER_SUBMITS):
                require(c.get('binding_status')==0,'NATIVE_STREAM_BINDING')
                require(c.get('exit_context')==c['context'] and c.get('exit_native_context')==c.get('native_context'),'CONTEXT_CHANGED')
    def root(c):
        seen=set()
        while c['domain']!='RUNTIME':
            require(c['id'] not in seen and c.get('parent_id') in calls,'PARENT')
            seen.add(c['id']);c=calls[c['parent_id']]
        return c

    apis=[];effects=[];syncs=[];internal=[];contexts=[];streams=[];ids=set();prior_resources=[]
    for r in raw['records']:
        require(r['id'] not in ids,'RECORD_DUPLICATE');ids.add(r['id'])
        kind=r['kind'];k=(r.get('domain'),r.get('pid'),r.get('correlation'))
        if kind=='API':
            c=keys.get(k)
            if c is None and r['end']<=scope['drain_end']:continue
            require(c is not None and c['cbid']==r['cbid'],'API_CALLBACK')
            apis.append({**r,'name':c['name']})
        elif kind in ('KERNEL','MEMCPY','MEMSET'):
            require(r.get('graph')==0 and r.get('graph_node',0)==0,'GRAPH_UNSUPPORTED')
            if kind=='MEMCPY' and r.get('runtime_correlation',0):
                c=keys.get(k);rt=keys.get(('RUNTIME',raw['pid'],r['runtime_correlation']))
                require(rt is not None and normal(rt['name'])=='cudaMemcpyAsync' and
                    (c is None or root(c)['id']==rt['id']),'COPY_RUNTIME_CORRELATION')
            effects.append(r)
        elif kind=='SYNC':
            candidates=[c for c in calls.values() if c['correlation']==r['correlation'] and
                normal(c['name']) in ('cudaStreamSynchronize','cudaDeviceSynchronize','cuStreamSynchronize')]
            roots={root(c)['id'] for c in candidates}
            require(len(roots)==1,'SYNC_DOMAIN_AMBIGUOUS_OR_MISSING')
            c=calls[next(iter(roots))]
            if normal(c['name']) not in ('cudaStreamSynchronize','cudaDeviceSynchronize'):
                # A real nested driver synchronization is a separate observed
                # completion fact. The enclosing API is not renamed a sync.
                require(len(candidates)==1,'INTERNAL_SYNC_AMBIGUOUS')
                d=candidates[0]
                require(d['domain']=='DRIVER' and normal(d['name'])=='cuStreamSynchronize' and
                    d.get('ptsz') is False and d.get('binding_status')==0 and
                    isinstance(d.get('params'),dict) and type(d['params'].get('native_stream')) is int and
                    d['params']['native_stream']>=0 and d['return_code']==0 and r['flags']==3 and
                    (d['context'],d['stream'])==(r['context'],r['stream']) and
                    d['start']<=r['start']<=r['end']<=d['end'],'INTERNAL_SYNC_SCOPE')
                internal.append({**r,'driver_call_id':d['id'],'runtime_call_id':c['id']})
                continue
            # Keep the physical correlation intact as provenance; the derived
            # edge points explicitly to its verified runtime ancestor.
            syncs.append({**r,'domain':'RUNTIME','correlation':c['correlation'],
                'raw_domain':r['domain'],'raw_correlation':r['correlation'],
                'callback_bridge_ids':[c['id'] for c in candidates]})
            require((normal(c['name']),r.get('flags')) in
                (('cudaStreamSynchronize',3),('cudaDeviceSynchronize',4)),'SYNC_KIND')
        elif kind=='CONTEXT':contexts.append(r)
        elif kind=='STREAM':streams.append(r)
        elif kind=='CUDA_EVENT':
            # An event recorded before a later context-wide physical drain is
            # historical; no request event/wait edge is silently supported.
            event=keys.get(('DRIVER',raw['pid'],r.get('correlation')))
            require(event is not None and normal(event['name'])=='cuEventRecord' and
                event['context']==r['context']==scope['context'] and
                event['end']<=scope['drain_end'],'EVENT_DEPENDENCY_NOT_SUPPORTED')
            prior_resources.append(r['id'])
        else:require(False,'UNKNOWN_RECORD_KIND:'+str(kind))
    context=[r for r in contexts if r['context']==scope['context']]
    require(context and all(r['device']==scope['device'] and r['flags']==0 for r in context),'CONTEXT_RESOURCE')
    require(any(r['stream']==scope['stream'] for r in context) or
        any(r['context']==scope['context'] and r['stream']==scope['stream'] for r in streams),'STREAM_RESOURCE')
    if 'markers' in raw:marker_ranges(raw['markers'])
    return dict(schema_version='submit-effect-evidence/0.1.0',source=raw['source'],
        clock=raw['clock'],session_id=raw['session_id'],pid=raw['pid'],quality=deepcopy(raw['quality']),
        callbacks=deepcopy(list(calls.values())),apis=apis,effects=deepcopy(effects),synchronizations=syncs,
        internal_completions=internal,
        closed_prior_resource_ids=prior_resources,
        closed_initialization_callback_ids=sorted(removed),scope=deepcopy(scope))


def analyze_files(capture_path,scope_path,output):
    a,b=Path(capture_path).resolve(),Path(scope_path).resolve();out=Path(output).resolve()
    require(not any(p.is_relative_to(out) for p in (a,b)),'OUTPUT_CONTAINS_INPUT')
    if out.exists():raise FileExistsError(out)
    ab=a.read_bytes();bb=b.read_bytes()
    raw=json.loads(ab);scope=json.loads(bb)
    result=analyze_scope(to_evidence(raw,scope))
    require(a.read_bytes()==ab and b.read_bytes()==bb,'SOURCE_CHANGED')
    value=dict(schema_version=VERSION,input=dict(capture_sha256=hashlib.sha256(ab).hexdigest(),
        scope_sha256=hashlib.sha256(bb).hexdigest(),clock=raw['clock'],collector='INDEPENDENT_CUPTI'),result=result)
    out.mkdir(parents=True,exist_ok=False)
    with (out/'result.json').open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
    return value
