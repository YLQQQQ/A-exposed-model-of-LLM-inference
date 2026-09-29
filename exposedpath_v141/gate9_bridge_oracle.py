"""Narrow independent Raw oracle for the fixed explicit-stream construction.

No Canonical, S, A or B calculator imports. Submission sequence, tokens and
physical prefix membership are fixed BEFORE execution, not fitted to results.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3


def require(ok,reason):
    if not ok: raise ValueError('BRIDGE_ORACLE_'+reason)


def length(intervals):
    merged=[]
    for a,b in sorted(intervals):
        require(type(a) is int and type(b) is int and -(2**63)<=a<=b<2**63,'TIME')
        if merged and a<=merged[-1][1]: merged[-1]=(merged[-1][0],max(b,merged[-1][1]))
        else: merged.append((a,b))
    return sum(b-a for a,b in merged)


def intersection(left,right):
    return [(max(a,c),min(b,d)) for a,b in left for c,d in right if max(a,c)<min(b,d)]


def account(window,apis,syncs,activities):
    w=[window]; total=length(w)
    sync=length(intersection(w,syncs))
    wait=length(intersection(intersection(w,syncs),activities))
    api=length(intersection(w,apis))-length(intersection(intersection(w,apis),syncs))
    host=total-sync-api
    require(min(host,api,wait,sync-wait)>=0,'ACCOUNT')
    return [host,api,wait,sync-wait,0]


def per_sync(activities,sync):
    require(activities and all(b<=sync[1] for a,b in activities),'AFTER_RETURN')
    return [length(intersection(activities,[(-(2**63),sync[0])])),
            length(intersection(activities,[sync])),sync[1]-max(sync[0],activities[-1][1])]


def check(sqlite_path,producer,result):
    path=Path(sqlite_path).resolve(); producer=Path(producer)
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    require(not any(Path(str(path)+s).exists() and Path(str(path)+s).stat().st_size for s in ('-wal','-journal')),'UNSEALED')
    execution=json.loads((producer/'execution.json').read_text())
    ledger=json.loads((producer/'pass_identity.json').read_text())
    require(execution['status']=='COMPLETE' and execution['error'] is None
        and execution['observed_tokens']==[[0,1],[11,12]],'EXECUTION_TOKENS')
    require(len(ledger['requests'])==2 and [r['request_role'] for r in ledger['requests']]==['measured','measured'],'PLAN')
    connection=sqlite3.connect(path.as_uri()+'?mode=ro&immutable=1',uri=True); connection.row_factory=sqlite3.Row
    try:
        def rows(table):
            return [dict(r,table=table) for r in connection.execute('SELECT rowid AS rid,* FROM "'+table+'"')]
        strings={r['id']:r['value'] for r in rows('StringIds')}
        markers=rows('NVTX_EVENTS'); apis=rows('CUPTI_ACTIVITY_KIND_RUNTIME')
        tables={r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'CUPTI_ACTIVITY_KIND_DRIVER' in tables: apis+=rows('CUPTI_ACTIVITY_KIND_DRIVER')
        activities=rows('CUPTI_ACTIVITY_KIND_KERNEL')+rows('CUPTI_ACTIVITY_KIND_MEMCPY')
        syncs=rows('CUPTI_ACTIVITY_KIND_SYNCHRONIZATION')
        def cid(kind,r): return kind+':'+r['table']+':'+str(r['rid'])
        def interval(r): return (r['start'],r['end'])
        members=[]; checks=[]; selected_activities=set()
        for req in ledger['requests']:
            identity=req['identity']; rid=identity['request_id']; operations={}; points={}
            for row in markers:
                text=row.get('text') or strings.get(row.get('textId'),'')
                if not text.startswith(('EXPOSEDPATH_STREAM_BRIDGE_V1:','EXPOSEDPATH_BOUNDARY_V1:')): continue
                payload=json.loads(text.split(':',1)[1])
                if payload.get('identity')!=identity: continue
                if text.startswith('EXPOSEDPATH_BOUNDARY_V1:'):
                    require(payload['boundary_id'] not in points,'DUPLICATE_POINT'); points[payload['boundary_id']]=row
                elif payload['operation']!='lifetime':
                    require(payload['ordinal'] not in operations,'DUPLICATE_OP'); operations[payload['ordinal']]=(payload,row)
            require(len(operations)==7 and len(points)==3,'OPERATION_SET')
            boundaries=[points[k] for k in req['expected_boundary_ids']]
            a,mid,b=[r['start'] for r in boundaries]; tid=boundaries[0]['globalTid']; gpid=tid-tid%2**24
            require(all(r['globalTid']==tid and r['end'] is None for r in boundaries) and a<=mid<=b,'BOUNDARIES')
            waits=[]; selected_api=set(); previous=a
            for ordinal,kind in enumerate(('submit','internal_wait','copy','wait','submit','copy','wait')):
                payload,mark=operations[ordinal]
                require(payload['operation']==kind and mark['globalTid']==tid and previous<=mark['start']<=mark['end']<=b,'ORDER')
                previous=mark['end']
                name={'submit':'cudaLaunchKernel','copy':'cudaMemcpyAsync','wait':'cudaStreamSynchronize','internal_wait':'cudaStreamSynchronize'}[kind]
                calls=[r for r in apis if r['globalTid']==tid and mark['start']<=r['start']<=r['end']<=mark['end']
                    and re.fullmatch(name+r'(?:_v[0-9]+)?',strings.get(r['nameId'],''))]
                require(len(calls)==1 and calls[0]['returnValue']==0,'CALL')
                api=calls[0]; selected_api.add((api['table'],api['rid']))
                matches=[r for r in (activities if kind in ('submit','copy') else syncs)
                    if r['globalPid']==gpid and r['correlationId']==api['correlationId']]
                require(len(matches)==1,'CORRELATION'); raw=matches[0]
                if kind in ('submit','copy'):
                    require(raw['end']<=b,'COMPLETION')
                    if kind=='copy': require(raw['copyKind']==2 and raw['bytes']==4,'D2H')
                    else: require('g8q_token_kernel' in strings.get(raw['demangledName'],''),'KERNEL')
                    members.append(raw); selected_activities.add((raw['table'],raw['rid']))
                else:
                    waits.append(interval(api))
                    expected_ids=[cid('device_activity',r) for r in members]
                    got=[r for r in result['physical_b_records'] if r['sync_id']==cid('cuda_sync',raw)]
                    require(len(got)==1 and got[0]['wait_set_activity_ids']==expected_ids,'PHYSICAL_MEMBERS')
                    require(got[0]['terminal']['activity_id']==expected_ids[-1],'TERMINAL')
                    expected=per_sync([interval(r) for r in members],interval(api))
                    require([got[0][k] for k in ('wait_set_hidden_union_ns','wait_set_exposed_union_ns','sync_return_tail_ns')]==expected,'B_COMPONENTS')
                    checks.append(dict(sync_id=got[0]['sync_id'],expected_members=expected_ids,expected_b=expected))
                if ordinal==3: require(mark['end']<=mid,'FIRST_COMPLETION')
                if ordinal==4: require(mid<=mark['start'],'DECODE_START')
            non_sync=[interval(r) for r in apis if r['globalTid']==tid and a<=r['start']<=r['end']<=b
                and re.sub(r'_v[0-9]+$','',strings.get(r['nameId'],''))!='cudaStreamSynchronize']
            for phase,window in [('full_request',(a,b)),('prefill',(a,mid)),('decode',(mid,b))]:
                expected=account(window,non_sync,waits,[interval(r) for r in members])
                got=[r for r in result['a_records']+result['warmup_a_records'] if r['request_id']==rid and r['phase']==phase]
                require(len(got)==1 and [got[0][k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')]==expected,'A_COMPONENTS')
        require([len(c['expected_members']) for c in checks]==[1,2,4,5,6,8],'FIXED_PREFIX_SEQUENCE')
        require(selected_activities=={(r['table'],r['rid']) for r in activities},'EXTRA_ACTIVITY')
        require(hashlib.sha256(path.read_bytes()).hexdigest()==before,'RAW_CHANGED')
        return dict(schema_version='gate9-bridge-independent-oracle/0.1.0',status='MATCH_REVIEW_REQUIRED',
            source_sqlite_sha256=before,sync_checks=checks,dropped_records_status='UNKNOWN',gate9_verdict='NOT_RUN')
    finally: connection.close()
