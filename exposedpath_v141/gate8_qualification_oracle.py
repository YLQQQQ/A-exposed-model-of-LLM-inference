"""Independent narrow Raw oracle. No Canonical, S or A implementation imports.

Analytical intervals are valid only after exact construction matching. No
general workload dependency inference or zero-loss assertion is performed.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3


def require(ok,reason):
    if not ok: raise ValueError('QUALIFICATION_ORACLE_'+reason)


def account_window(window,apis,syncs,activities,gaps):
    """Disjoint construction intervals: closed-form clipped lengths, not A code."""
    start,end=window
    require(all(type(t) is int and -(2**63)<=t<2**63 for t in window) and start<=end,'WINDOW')
    def length(a,b): return max(0,min(end,b)-max(start,a))
    for group in (apis+syncs+gaps,activities):
        ordered=sorted(group)
        require(all(type(a) is int and type(b) is int and -(2**63)<=a<=b<2**63 for a,b in ordered),'TIME')
        require(all(a[1]<=b[0] for a,b in zip(ordered,ordered[1:])),'OVERLAP')
    api=sum(length(a,b) for a,b in apis)
    wait=sum(length(max(a,c),min(b,d)) for a,b in syncs for c,d in activities if max(a,c)<min(b,d))
    residual=sum(length(a,b) for a,b in syncs)-wait
    unknown=sum(length(a,b) for a,b in gaps)
    host=end-start-api-wait-residual-unknown
    require(min(host,api,wait,residual,unknown)>=0 and end-start<=2**64-1,'DURATION')
    return [host,api,wait,residual,unknown]


def compare_components(expected,actual):
    require(expected==actual,'A_CLASSIFICATION_MISMATCH')


def sync_kind(name):
    mapping={n:k for k in ('CONTEXT_SYNCHRONIZE','STREAM_SYNCHRONIZE')
        for n in (k,'CUPTI_ACTIVITY_SYNCHRONIZATION_TYPE_'+k)}
    require(name in mapping,'UNSUPPORTED_SYNC_ENUM')
    return mapping[name]


def check_raw(sqlite_path,producer):
    """Construction oracle independently binds original rows, not S/projection."""
    path=Path(sqlite_path).resolve(); root=Path(producer)
    require(not any(Path(str(path)+s).exists() and Path(str(path)+s).stat().st_size for s in ('-wal','-journal')),'UNSEALED_SQLITE')
    original=hashlib.sha256(path.read_bytes()).hexdigest()
    ledger=json.loads((root/'pass_identity.json').read_text(encoding='utf-8'))
    host=json.loads((root/'host_boundaries.json').read_text(encoding='utf-8'))
    drain_ledger=json.loads((root/'drain_ledger.json').read_text(encoding='utf-8'))['drains']
    execution=json.loads((root/'execution.json').read_text(encoding='utf-8'))
    require(execution['status']=='COMPLETE' and execution['error'] is None and len(ledger['requests'])==2,'EXECUTION')
    require([r['token'] for r in execution['observed_tokens']]==[11,12,21,22],'TOKENS')
    conn=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True); conn.row_factory=sqlite3.Row
    try:
        require(conn.execute('pragma integrity_check').fetchone()[0]=='ok','SQLITE')
        tables={r[0] for r in conn.execute("select name from sqlite_master where type='table'")}
        def rows(table):
            require(table in tables,'TABLE:'+table)
            return [dict(r,source_table=table) for r in conn.execute('SELECT rowid AS raw_id,* FROM "'+table+'"')]
        strings={r['id']:r['value'] for r in rows('StringIds')}
        nvtx=rows('NVTX_EVENTS'); apis=rows('CUPTI_ACTIVITY_KIND_RUNTIME')
        if 'CUPTI_ACTIVITY_KIND_DRIVER' in tables: apis+=rows('CUPTI_ACTIVITY_KIND_DRIVER')
        kernels=rows('CUPTI_ACTIVITY_KIND_KERNEL'); copies=rows('CUPTI_ACTIVITY_KIND_MEMCPY')
        syncs=rows('CUPTI_ACTIVITY_KIND_SYNCHRONIZATION'); contexts=rows('TARGET_INFO_CUDA_CONTEXT_INFO')
        sync_types={r['id']:r['name'] for r in rows('ENUM_CUPTI_SYNC_TYPE')}
        require(all(r['severity']==1 for r in rows('DIAGNOSTIC_EVENT')),'WARNING_IMPACT_UNKNOWN')
        def interval(r):
            a,b=r['start'],r['end']
            require(type(a) is int and type(b) is int and -(2**63)<=a<=b<2**63,'RAW_TIME')
            return a,b
        def ref(r): return dict(table=r['source_table'],rowid=r['raw_id'])
        op_rows={}; points={}; drain_rows={}
        for row in nvtx:
            text=row.get('text') or strings.get(row.get('textId'),'')
            if text.startswith('EXPOSEDPATH_QUALIFICATION_OP_V1:'):
                p=json.loads(text.split(':',1)[1]); key=(p['identity']['request_id'],p['ordinal'])
                require(key not in op_rows,'DUPLICATE_OPERATION'); op_rows[key]=(p,row)
            elif text.startswith('EXPOSEDPATH_DRAIN_V1:'):
                p=json.loads(text.split(':',1)[1]); key=p['identity']['request_id']
                require(key not in drain_rows,'DUPLICATE_DRAIN'); drain_rows[key]=(p,row)
            elif text.startswith('EXPOSEDPATH_BOUNDARY_V1:'):
                p=json.loads(text.split(':',1)[1]); key=p['boundary_id']
                require(key not in points and row['end'] is None and type(row['start']) is int,'POINT')
                points[key]=(p,row)
        require(len(op_rows)==18 and len(points)==len(host)==6 and len(drain_rows)==len(drain_ledger)==2,'MARKER_SET')
        results=[]
        for i,request in enumerate(ledger['requests']):
            ident=request['identity']; rid=ident['request_id']; token=11+10*i
            require(rid=='controlled-'+str(i) and ident['repeat_id']==str(i)
                and request['outcome']=='COMPLETE' and request['actual_output_tokens']==request['expected_output_tokens']==2
                and not request['early_eos'] and not request['reasons'],'REQUEST_IDENTITY')
            expected=[('submit',token),('internal_wait',None),('copy',None),('wait',None),('read',token),
                      ('submit',token+1),('copy',None),('wait',None),('read',token+1)]
            ordinals=[0,1,2,3,4,6,7,8,9]
            boundary_rows=[]
            for h in [h for h in host if h['payload']['identity']==ident]:
                require(h['payload']['boundary_id'] in points,'BOUNDARY_MISSING')
                payload,row=points[h['payload']['boundary_id']]
                require(payload==h['payload'],'BOUNDARY_PAYLOAD'); boundary_rows.append(row)
            require(len(boundary_rows)==3,'BOUNDARY_COUNT')
            a,split,b=[r['start'] for r in boundary_rows]; tid=boundary_rows[0]['globalTid']; gpid=tid-tid%2**24
            require(a<=split<=b and ((gpid>>24)&0xffffff)==ledger['pid']
                and all(r['globalTid']==tid for r in boundary_rows),'BOUNDARY_CLOCK_IDENTITY')
            require(execution['observed_tokens'][i*2:i*2+2]==[
                dict(identity=ident,ordinal=4,token=token),dict(identity=ident,ordinal=9,token=token+1)],'TOKEN_IDENTITY')
            payload,drain=drain_rows[rid]; record=drain_ledger[i]
            require(payload['identity']==ident and record['identity']==ident and record['status']=='COMPLETE'
                and record['error'] is None and all(record[k]==v for k,v in payload.items())
                and drain['globalTid']==tid and interval(drain)[1]<=a,'DRAIN_IDENTITY_BOUNDARY')
            matches=[r for r in apis if r['globalTid']==tid and drain['start']<=r['start']<=r['end']<=drain['end']
                and strings.get(r['nameId'])=='cudaDeviceSynchronize' and r['returnValue']==0]
            require(len(matches)==1,'DRAIN_API'); drain_api=matches[0]
            matches=[r for r in syncs if r['globalPid']==gpid and r['correlationId']==drain_api['correlationId']
                and sync_kind(sync_types.get(r['syncType']))=='CONTEXT_SYNCHRONIZE' and drain_api['start']<=r['start']<=r['end']<=drain_api['end']]
            require(len(matches)==1,'DRAIN_PHYSICAL_SYNC')
            require(all(r['end']<=drain_api['end'] for r in kernels+copies
                if r['globalPid']==gpid and r['start']<drain_api['start']),'DRAIN_PRIOR_COMPLETION')
            selected=[]; read_ranges=[]; previous=a
            for ordinal,(kind,value) in zip(ordinals,expected):
                payload,row=op_rows[(rid,ordinal)]
                require(payload==dict(construction='NULL-FIFO-D2H/0.1.0',identity=ident,ordinal=ordinal,operation=kind,value=value)
                    and row['globalTid']==tid,'OPERATION_IDENTITY')
                x,y=interval(row); require(previous<=x<=y<=b,'OPERATION_ORDER'); previous=y
                if kind=='read':
                    read_ranges.append((x,y)); continue
                name={'submit':'cudaLaunchKernel','internal_wait':'cudaStreamSynchronize','copy':'cudaMemcpyAsync','wait':'cudaStreamSynchronize'}[kind]
                matches=[r for r in apis if r['globalTid']==tid and x<=r['start']<=r['end']<=y
                         and re.sub(r'_v\d+$','',strings.get(r['nameId'],''))==name]
                require(len(matches)==1 and matches[0]['returnValue']==0,'OPERATION_API')
                selected.append((kind,matches[0]))
            require(read_ranges[0][1]<=split<=op_rows[(rid,6)][1]['start'] and read_ranges[1][1]<=b,'HOST_READ_COMPLETION')
            selected_refs={tuple(ref(r).values()) for _,r in selected}
            gaps=[]
            for api in apis:
                if api['start']>=b or api['end']<=a: continue
                require(api['globalTid']==tid and api['returnValue']==0 and a<=api['start']<=api['end']<=b,'API_SCOPE')
                if tuple(ref(api).values()) not in selected_refs:
                    require(re.sub(r'_v\d+$','',strings.get(api['nameId'],'')) in ('cuKernelGetFunction','cudaStreamIsCapturing'), 'EXTRA_API')
                    require(not any(r['correlationId']==api['correlationId'] and r['globalPid']==gpid for r in kernels+copies+syncs),'GAP_CONFLICT')
                    gaps.append(interval(api))
            activity=[]; waits=[]; members=[]; expected_members=[]
            scope=None
            for kind,api in selected:
                group=kernels if kind=='submit' else copies if kind=='copy' else syncs
                matches=[r for r in group if r['correlationId']==api['correlationId'] and r['globalPid']==gpid]
                require(len(matches)==1,'CORRELATION_OR_PHYSICAL_SYNC')
                raw=matches[0]; x,y=interval(raw)
                current=(raw['deviceId'],raw['contextId'],raw['streamId'])
                if scope is None: scope=current
                require(current==scope,'PHYSICAL_SCOPE')
                if kind in ('submit','copy'):
                    require(api['start']<=x<=y<=b,'ACTIVITY_TIME')
                    if kind=='copy': require(raw['copyKind']==2 and raw['bytes']==4,'D2H')
                    else: require('g8q_token_kernel' in strings.get(raw.get('demangledName'),'')
                        and raw.get('graphId') in (None,0) and raw.get('graphNodeId') in (None,0),'KERNEL')
                    activity.append(raw); members.append(ref(raw))
                else:
                    require(api['start']<=x<=y<=api['end'] and sync_kind(sync_types.get(raw['syncType']))=='STREAM_SYNCHRONIZE','SYNC_INTERVAL')
                    require(all(r['end']<=api['end'] for r in activity),'SYNC_COMPLETION')
                    waits.append(interval(api)); expected_members.append(dict(sync=ref(raw),members=list(members)))
            require([len(s['members']) for s in expected_members]==[1,2,4],'DEPENDENCY_CONSTRUCTION')
            require(any(c['processId']==ledger['pid'] and c['contextId']==scope[1]
                and c['nullStreamId']==scope[2] for c in contexts),'NULL_STREAM')
            relevant=[r for r in kernels+copies if a<=r['start']<b]
            require({tuple(ref(r).values()) for r in relevant}=={tuple(ref(r).values()) for r in activity},'EXTRA_ACTIVITY')
            relevant_sync=[r for r in syncs if a<r['end'] and r['start']<b]
            require({tuple(ref(r).values()) for r in relevant_sync}=={tuple(s['sync'].values()) for s in expected_members},'EXTRA_SYNC')
            windows={phase:account_window(w,[interval(r) for k,r in selected if k in ('submit','copy')],
                waits,[interval(r) for r in activity],gaps) for phase,w in
                [('full_request',(a,b)),('prefill',(a,split)),('decode',(split,b))]}
            results.append(dict(identity=ident,windows=windows,syncs=expected_members,local_gaps=gaps,
                drain_api=ref(drain_api),drain_marker=ref(drain)))
        require(hashlib.sha256(path.read_bytes()).hexdigest()==original,'SOURCE_CHANGED')
        return dict(schema_version='exposedpath-qualification-oracle/0.1.1',source_sqlite_sha256=original,
            requests=results,tokens=[[11,12],[21,22]],dropped_records_status='UNKNOWN')
    finally: conn.close()
