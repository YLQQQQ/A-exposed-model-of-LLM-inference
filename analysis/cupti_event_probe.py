"""Narrow API22 event-record/link validation, not S/COE event qualification."""
import hashlib
import json
from pathlib import Path
from analysis.cupti_timeline import marker_ranges
from exposedpath.cupti_timeline import validate_startup_data,activity_policy
from exposedpath_v141.submit_effect_bridge import normal


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_EVENT_PROBE_'+reason)


def analyze(raw,side):
    require(raw.get('schema_version')=='cupti-timeline-capture/0.1.0' and
        side.get('schema_version')=='cupti-event-probe-side/0.1.0','SCHEMA')
    init=validate_startup_data(raw)
    require(init and init['succeeded'] and init.get('activity_policy')==activity_policy(),'POLICY')
    require(raw['clock']=='CUPTI_TIMESTAMP_NS' and raw['session_id']==side['session_id'] and
        raw['pid']==side['pid'] and type(side['tid']) is int and side['tid']>0,'IDENTITY')
    q=raw['quality']
    require(q['closed'] is True and q['errors']==[] and
        all(type(q[k]) is int and q[k]==0 for k in ('overflow','dropped','dropped_query_errors')),'QUALITY')
    require([s['operation'] for s in side['calls']]==['create','record','event_sync','stream_sync','destroy']
        and all(type(s['return_code']) is int and s['return_code']==0 for s in side['calls']),'FAILED_CALL')
    require(type(side['native_event']) is int and side['native_event']>0 and
        type(side['native_stream']) is int and side['native_stream']>0,'NATIVE_HANDLES')
    calls={c['id']:c for c in raw['callbacks']};require(len(calls)==len(raw['callbacks']),'CALL_DUPLICATE')
    require(all(c['closed'] is True and c['pid']==raw['pid'] for c in calls.values()),'CALL_UNCLOSED')
    records=raw['records'];require(len({r['id'] for r in records})==len(records),'RECORD_DUPLICATE')
    ranges=marker_ranges(raw['markers'])['ranges']
    def one(items,reason):
        items=list(items);require(len(items)==1,reason);return items[0]
    def root(c):
        seen=set()
        while c['domain']!='RUNTIME':
            require(c['id'] not in seen and c.get('parent_id') in calls,'PARENT')
            seen.add(c['id']);p=calls[c['parent_id']]
            require(p['tid']==c['tid'] and p['start']<=c['start']<=c['end']<=p['end'] and
                p['enter_seq']<c['enter_seq']<c['exit_seq']<p['exit_seq'],'PARENT')
            c=p
        return c
    rt={}
    for key,name in [('record','cudaEventRecord'),('event_sync','cudaEventSynchronize'),('stream_sync','cudaStreamSynchronize')]:
        label='EVENT-PROBE:'+side['session_id']+':'+key
        r=one((v for v in ranges if v['label']==label and v['tid']==side['tid']),'RANGE:'+key)
        c=one((v for v in calls.values() if v['domain']=='RUNTIME' and v['tid']==side['tid'] and
            normal(v['name'])==name and r['start']<=v['start']<=v['end']<=r['end']),'CALL:'+key)
        require(c['return_code']==0 and c['ptsz'] is False,'FAILED_CALL')
        api=one((a for a in records if a['kind']=='API' and a['domain']=='RUNTIME' and
            (a['pid'],a['tid'],a['correlation'],a['cbid'])==(c['pid'],c['tid'],c['correlation'],c['cbid'])),'API:'+key)
        require(api['return_code']==0 and r['start']<=api['start']<=api['end']<=r['end'],'API_SCOPE')
        rt[key]={**c,'activity_bounds':[api['start'],api['end']]}
    require(rt['record']['end']<=rt['event_sync']['start'] and rt['event_sync']['end']<=rt['stream_sync']['start'],'ORDER')
    event=one((r for r in records if r['kind']=='CUDA_EVENT'),'EVENT_COVERAGE')
    driver=one((c for c in calls.values() if c['domain']=='DRIVER' and c['correlation']==event['correlation']
        and normal(c['name']) in ('cuEventRecord','cuEventRecordWithFlags')),'EVENT_DRIVER')
    require(root(driver)['id']==rt['record']['id'] and driver['return_code']==0 and
        driver['ptsz'] is False and driver['context']==rt['record']['context']==event['context'],'PARENT')
    # If driver API rows were emitted, retain their exact domain/callback join.
    for a in records:
        if a['kind']=='API' and a['domain']=='DRIVER':
            c=one((c for c in calls.values() if c['domain']=='DRIVER' and
                (c['pid'],c['tid'],c['correlation'],c['cbid'])==(a['pid'],a['tid'],a['correlation'],a['cbid'])),'DRIVER_API')
            require(type(a['start']) is int and type(a['end']) is int and 0<=a['start']<=a['end']
                and c['return_code']==a['return_code'],'DRIVER_API_SCOPE')
    def physical(key,flag,names):
        candidates=[]
        for r in records:
            if r['kind']!='SYNC' or r['flags']!=flag:continue
            roots={root(c)['id'] for c in calls.values() if c['correlation']==r['correlation'] and normal(c['name']) in names}
            require(len(roots)<=1,'SYNC_AMBIGUOUS')
            if roots=={rt[key]['id']}:candidates.append(r)
        r=one(candidates,'EVENT_SYNC' if flag==1 else 'STREAM_SCOPE')
        require(r['context']==event['context'] and rt[key]['activity_bounds'][0]<=r['start']<=r['end']<=rt[key]['activity_bounds'][1],'SYNC_SCOPE')
        return r
    es=physical('event_sync',1,('cudaEventSynchronize','cuEventSynchronize'))
    ss=physical('stream_sync',3,('cudaStreamSynchronize','cuStreamSynchronize'))
    require(es['event']==event['event'],'EVENT_SYNC')
    c=rt['stream_sync']
    require(c['binding_status']==0 and c['context']==event['context'] and c['stream']==ss['stream']==event['stream']
        and c['params']['native_stream']==side['native_stream'],'STREAM_SCOPE')
    require(any(r['kind']=='CONTEXT' and r['context']==event['context'] and r['device']==c['device'] and r['flags']==0 for r in records)
        and any(r['kind']=='STREAM' and r['context']==event['context'] and r['stream']==event['stream'] for r in records),'RESOURCE_SCOPE')
    require([event['context'],event['stream']] in q['dropped_scopes'],'QUALITY_SCOPE')
    return dict(status='EVENT_LINK_COMPLETE_PENDING_REVIEW',event_record=event['id'],event_sync=es['id'],
        stream_sync=ss['id'],context=event['context'],stream=event['stream'],event_id=event['event'],
        event_driver_call=driver['id'],runtime_call_ids={k:c['id'] for k,c in rt.items()},
        event_completion_timestamp='NOT_AVAILABLE_IN_API22',
        driver_api_duration='NOT_COMPUTED',COE_admission='NOT_ASSESSED',pytorch_coverage='NOT_GRANTED',formal_eligible=False)


def analyze_files(capture,side,output):
    paths=[Path(capture).resolve(),Path(side).resolve()];out=Path(output).resolve()
    require(not out.exists() and not any(p.is_relative_to(out) for p in paths),'NEW_OUTPUT')
    originals=[p.read_bytes() for p in paths]
    result=analyze(*[json.loads(b) for b in originals])
    require([p.read_bytes() for p in paths]==originals,'INPUT_CHANGED')
    value=dict(schema_version='cupti-event-link-review/0.1.0',input_sha256=[hashlib.sha256(b).hexdigest() for b in originals],result=result)
    out.mkdir(parents=True)
    with (out/'review.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
    return value
