"""Bounded 0/64-byte micro evidence, NOT an A/S/COE admission implementation.

Provider namespace: the *saved target 2026.2 AnalysisGuide* explicitly defines
MEMSET.correlationId REFERENCES CUPTI_ACTIVITY_KIND_RUNTIME(correlationId).
This is not a reinterpretation of native CUpti_ActivityMemset4's driver ID.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3

VERSION='memset-same-capture-review/0.1.0'
PROVIDER='nsys-2026.2-memset-micro/0.1.0'


def require(ok,reason):
    if not ok:raise ValueError('MEMSET_MICRO_'+reason)


def one(rows,reason):
    rows=list(rows);require(len(rows)==1,reason);return rows[0]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def name(value):
    return re.sub(r'_v[0-9]+$','',value)


def interval(row):
    return (type(row.get('start')) is int and type(row.get('end')) is int
            and 0<=row['start']<row['end'])


def within(a,b):
    return interval(a) and interval(b) and b['start']<=a['start']<a['end']<=b['end']


def diagnostics(raw):
    if not raw['diagnostics']:return None
    require('diagnostic_scope' in raw and 'diagnostic_bundle' in raw,'DIAGNOSTIC')
    from exposedpath_v141.gate9_diagnostic_review import review as established_review
    try:return established_review(raw['diagnostic_scope'],raw['diagnostic_bundle'])
    except ValueError as error:raise ValueError('MEMSET_MICRO_DIAGNOSTIC:'+str(error)) from error


def review(side,raw,expected):
    require(side.get('schema_version')=='memset-same-capture-side/0.1.0'
        and side.get('role')=='ENGINEERING_MEMSET_MICRO','ROLE_VERSION')
    require(raw.get('schema_version')==PROVIDER and raw.get('clock_id')=='NSYS_TRACE_NS','PROVIDER')
    require(side.get('run_id')==expected['run_id'] and re.fullmatch('[0-9a-f]{32}',side['run_id'])
        and type(side.get('pid')) is int and side['pid']>0
        and type(side.get('creation_filetime')) is int and side['creation_filetime']>0,'IDENTITY')
    require(side.get('entry')=='cudaMemsetAsync' and side.get('recorder_kind')=='CUDA_RUNTIME_EXPORT','ENTRY')
    require(os.path.normcase(side.get('runtime_path',''))==os.path.normcase(expected['runtime_path'])
        and side.get('runtime_version')==12040,'RUNTIME')
    require(side.get('gpu_uuid')==expected['gpu_uuid']
        and isinstance(side.get('pci_bus_id'),str) and side['pci_bus_id'].casefold()==expected['pci_bus_id'].casefold(),'DEVICE')
    require(side.get('attach_code')==side.get('detach_code')==side.get('recorder_error')==0,'RECORDER')
    require(type(side.get('setup_drain_return')) is int and side['setup_drain_return']==0,'DRAIN')
    disposition=diagnostics(raw)
    calls=side['calls'];require(len(calls)==2 and [c['call_id'] for c in calls]==[1,2],'CALLS')
    used=set();result=[]
    for c,expected_count in zip(calls,[0,64]):
        require(c.get('pid')==side['pid'] and type(c.get('tid')) is int and c['tid']>0,'IDENTITY')
        require(type(c.get('count')) is int and 0<=c['count']<2**64 and c['count']==expected_count,'COUNT')
        require(c.get('value')==123 and c.get('stream_hex')=='0' and c.get('pointer_alias')==1,'PARAMETERS')
        require(c.get('forwards')==1 and c.get('completed') is True,'FORWARDING')
        require(type(c.get('return_code')) is int and c['return_code']==0,'CALL_RETURN')
        require(type(c.get('push_level')) is int and c['push_level']>=0
            and c.get('pop_level')==c['push_level'],'NVTX_RECORDING')
        nr=one((v for v in raw['ranges'] if v['call_id']==c['call_id']),'RANGE_PAIR')
        require(nr.get('run_id')==side['run_id'] and nr.get('pid')==c['pid']
            and nr.get('tid')==c['tid'] and nr.get('event_type')==59 and interval(nr),'RANGE_PAIR')
        runtime=one((v for v in raw['apis'] if v['pid']==c['pid'] and v['tid']==c['tid']
            and v['event_class']==0 and name(v['name'])=='cudaMemsetAsync' and within(v,nr)),'RUNTIME_PAIR')
        require(runtime['record_id'] not in used and runtime['return_code']==c['return_code'],'RUNTIME_PAIR')
        used.add(runtime['record_id'])
        vr=one((v for v in raw['verification_ranges'] if v['call_id']==c['call_id']),'STREAM_SCOPE')
        require(vr['pid']==c['pid'] and vr['tid']==c['tid'] and interval(vr)
            and vr['start']>=nr['end'],'STREAM_SCOPE')
        sync=one((v for v in raw['sync_apis'] if v['pid']==c['pid'] and v['tid']==c['tid']
            and name(v['name'])=='cudaStreamSynchronize' and within(v,vr) and v['return_code']==0),'STREAM_SCOPE')
        physical=one((v for v in raw['synchronizations'] if v['pid']==c['pid']
            and v['correlation_id']==sync['correlation_id']),'STREAM_SCOPE')
        require(physical.get('sync_type')=='STREAM_SYNCHRONIZE' and physical['device_id']==0
            and physical['context_id'] is not None and physical['stream_id'] is not None,'STREAM_SCOPE')
        # UNIQUE API correlation in this process; never borrow a driver ID or a
        # different API just because numbers/times are close.
        require(len([v for v in raw['apis']+raw['sync_apis'] if v['pid']==c['pid']
            and v['correlation_id']==runtime['correlation_id']])==1,'CORRELATION_AMBIGUOUS')
        effects=[v for v in raw['effects'] if v['pid']==c['pid'] and v['correlation_id']==runtime['correlation_id']]
        if c['count']==0:
            require(not any(v.get('bytes')!=0 for v in effects),'ZERO_EFFECT_CONFLICT')
            state='ZERO_LENGTH_ARGUMENT_OBSERVED'
        else:
            require(effects,'NONZERO_EFFECT_MISSING');effect=one(effects,'EFFECT_CONFLICT')
            require(effect['kind']=='MEMSET' and effect['bytes']==64 and effect['value']==123
                and interval(effect) and runtime['start']<=effect['start']<effect['end']<=sync['end'],'EFFECT_CONFLICT')
            require(all(effect[k]==physical[k] for k in ('device_id','context_id','stream_id')),'STREAM_SCOPE')
            state='NONZERO_DEVICE_EFFECT_MAPPED'
        oracle=one((v for v in side['cases'] if v['call_id']==c['call_id']),'FUNCTIONAL_ORACLE')
        require(oracle['sync_return']==oracle['copy_return']==0 and
            oracle['readback_hex']==('3c' if c['count']==0 else '7b')*64,'FUNCTIONAL_ORACLE')
        result.append(dict(call_id=c['call_id'],count=c['count'],state=state,
            runtime_id=runtime['record_id'],range_id=nr['record_id'],effect_ids=[v['record_id'] for v in effects],
            scope=physical,zero_length_ordering='NOT_PROVEN' if c['count']==0 else 'NOT_APPLICABLE'))
    target=[v for v in raw['apis'] if v['pid']==side['pid'] and name(v['name'])=='cudaMemsetAsync']
    require({v['record_id'] for v in target}==used and len(target)==len(used),'RUNTIME_COVERAGE')
    require(len(raw['ranges'])==len(calls),'RANGE_PAIR')
    return dict(schema_version=VERSION,status='MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW',
        role='Engineering',calls=result,coe_admission='NOT_ASSESSED',a_admission='NOT_ASSESSED',
        pytorch_internal_coverage='NOT_PROVEN',dropped_records_status='UNKNOWN',
        diagnostic_disposition=disposition,
        namespace='NSYS_EXPORTED_API_TABLE_NOT_NATIVE_CUPTI_MEMSET4')


def read_sqlite(path,run_id):
    """Strict miniature adapter; only future micro schema, never upgrades Raw."""
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro&immutable=1',uri=True) as db:
        db.row_factory=sqlite3.Row
        require(db.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLITE_INTEGRITY')
        tables={v[0] for v in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require({'StringIds','NVTX_EVENTS','CUPTI_ACTIVITY_KIND_RUNTIME','CUPTI_ACTIVITY_KIND_MEMSET',
                 'CUPTI_ACTIVITY_KIND_SYNCHRONIZATION','ENUM_CUPTI_SYNC_TYPE','DIAGNOSTIC_EVENT'}<=tables,'SQLITE_SCHEMA')
        require({'source','severity','text','globalPid','timestampType'}<=
                {r[1] for r in db.execute('PRAGMA table_info(DIAGNOSTIC_EVENT)')},'DIAGNOSTIC_SCHEMA')
        strings=dict(db.execute('SELECT id,value FROM StringIds'))
        def rows(table):return [dict(v) for v in db.execute('SELECT rowid AS source_rowid,* FROM '+table)]
        ranges=[];verification=[];scopes=[];nvtx_all=[]
        for r in rows('NVTX_EVENTS'):
            text=r.get('text') or strings.get(r.get('textId'),'')
            nvtx_all.append(dict(record_id='NVTX:'+str(r['source_rowid']),source_table='NVTX_EVENTS',
                source_rowid=r['source_rowid'],global_tid=r['globalTid']))
            if text=='EP_MICRO:'+run_id:scopes.append(r)
            match=re.fullmatch(r'EP_(MEMSET|VERIFY):([0-9a-f]{32}):([12])',text)
            if not match:continue
            require(match[2]==run_id,'IDENTITY')
            require(r.get('endGlobalTid') in (None,r['globalTid']),'RANGE_PAIR')
            v=dict(record_id='NVTX:'+str(r['source_rowid']),run_id=match[2],call_id=int(match[3]),
                pid=(r['globalTid']>>24)&0xffffff,tid=r['globalTid']&0xffffff,
                start=r['start'],end=r['end'],event_type=r['eventType'])
            (ranges if match[1]=='MEMSET' else verification).append(v)
        scope=one(scopes,'MICRO_SCOPE');require(interval(scope),'MICRO_SCOPE')
        target_global_pid=scope['globalTid']-scope['globalTid']%2**24
        apis=[];sync=[]
        for r in rows('CUPTI_ACTIVITY_KIND_RUNTIME'):
            n=strings[r['nameId']]
            v=dict(record_id='API:'+str(r['source_rowid']),name=n,event_class=r['eventClass'],
                pid=(r['globalTid']>>24)&0xffffff,tid=r['globalTid']&0xffffff,start=r['start'],end=r['end'],
                correlation_id=r['correlationId'],return_code=r['returnValue'])
            if r['globalTid']==scope['globalTid'] and within(v,scope):
                require(not (name(n).startswith('cudaMemsetAsync') and name(n)!='cudaMemsetAsync'),'ENTRY')
                (sync if name(n)=='cudaStreamSynchronize' else apis).append(v)
            elif name(n)=='cudaMemsetAsync' and within(v,scope):
                # Other-thread calls cannot be silently dropped from coverage.
                apis.append(v)
        effects=[]
        for table,kind in [('CUPTI_ACTIVITY_KIND_MEMSET','MEMSET'),('CUPTI_ACTIVITY_KIND_KERNEL','KERNEL'),
                           ('CUPTI_ACTIVITY_KIND_MEMCPY','MEMCPY')]:
            if table not in tables:continue
            for r in rows(table):
                effects.append(dict(record_id=kind+':'+str(r['source_rowid']),kind=kind,
                    pid=(r['globalPid']>>24)&0xffffff,correlation_id=r['correlationId'],bytes=r.get('bytes'),
                    value=r.get('value'),device_id=r['deviceId'],context_id=r['contextId'],stream_id=r['streamId'],
                    start=r['start'],end=r['end']))
        types=dict(db.execute('SELECT id,name FROM ENUM_CUPTI_SYNC_TYPE'))
        physical=[dict(pid=(r['globalPid']>>24)&0xffffff,correlation_id=r['correlationId'],
            device_id=r['deviceId'],context_id=r['contextId'],stream_id=r['streamId'],
            sync_type=types.get(r['syncType'],'').removeprefix('CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_'))
            for r in rows('CUPTI_ACTIVITY_KIND_SYNCHRONIZATION')]
        diagnostics=rows('DIAGNOSTIC_EVENT') if 'DIAGNOSTIC_EVENT' in tables else []
        result=dict(schema_version=PROVIDER,clock_id='NSYS_TRACE_NS',ranges=ranges,
            verification_ranges=verification,apis=apis,sync_apis=sync,effects=effects,
            synchronizations=physical,diagnostics=diagnostics)
        if diagnostics:
            diagnostic_records=[]
            for r in diagnostics:
                require({'source','severity','text','globalPid','timestampType'}<=r.keys(),'DIAGNOSTIC_SCHEMA')
                gp=r['globalPid'];pid=((gp>>24)&0xffffff) if type(gp) is int and gp>0 and gp%2**24==0 else None
                diagnostic_records.append(dict(source_rowid=r['source_rowid'],global_pid=gp,process_id=pid,
                    process_relation='UNKNOWN' if pid is None else 'TARGET_PROCESS' if gp==target_global_pid else 'OTHER_PROCESS',
                    severity_id=r['severity'],source_id=r['source'],timestamp_type=r['timestampType'],text=r['text']))
            cuda_all=[]
            for table in ('CUPTI_ACTIVITY_KIND_MEMSET','CUPTI_ACTIVITY_KIND_KERNEL','CUPTI_ACTIVITY_KIND_MEMCPY'):
                if table in tables:
                    cuda_all += [dict(record_id=table+':'+str(r['source_rowid']),global_pid=r['globalPid']) for r in rows(table)]
            refs=[v for v in nvtx_all if v['global_tid']-v['global_tid']%2**24==target_global_pid]
            h=sha(path)
            result['diagnostic_scope']=dict(records=diagnostic_records,target_global_pid=target_global_pid,
                target_pid=(target_global_pid>>24)&0xffffff,source_sqlite_sha256=h,target_nvtx_refs=refs)
            result['diagnostic_bundle']=dict(manifest=dict(source=dict(export=dict(platform='windows-desktop',
                product_version='2026.2.1.210'),sqlite=dict(sha256=h))),
                records=dict(nvtx=nvtx_all,device_activity=cuda_all,cuda_api=[dict(global_tid=r['globalTid']) for r in rows('CUPTI_ACTIVITY_KIND_RUNTIME')]))
        return result


def review_files(sqlite,side_path,expected,output):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    before={str(p):sha(p) for p in (Path(sqlite),Path(side_path))}
    side=json.loads(Path(side_path).read_text(encoding='utf8'))
    raw=read_sqlite(sqlite,expected['run_id'])
    try:
        result=review(side,raw,expected)
    except BaseException as error:
        result=dict(schema_version=VERSION,status='BLOCKED',error=str(error),
            coe_admission='NOT_ASSESSED',dropped_records_status='UNKNOWN')
        raise
    finally:
        require(all(sha(p)==h for p,h in before.items()),'INPUT_CHANGED')
        for n,v in [('review.json',result),('source_hashes.json',before),('raw_excerpt.json',raw)]:
            with (output/n).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
    return result
