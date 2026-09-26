"""Independent, narrow construction-to-Raw checker; no Canonical/S/A/B imports.

Matching is not a session loss certificate, new Q0 qualification, or support for
an arbitrary model. Unknown API variants and unexplained Driver calls stop it.
"""
import hashlib
import json
from pathlib import Path
import re
import sqlite3

from .q0_oracle import calculate_expected_timing

CONSTRUCTION='CONTROLLED-D2H-REQUEST/0.2.0'
OP_PREFIX='EXPOSEDPATH_CONTROLLED_OP_V1:'
BOUNDARY_PREFIX='EXPOSEDPATH_BOUNDARY_V1:'
API_NAMES={
    'prepare':({'cudaDeviceSynchronize','cudaDeviceSynchronize_v3020'},),
    'submit':({'cudaLaunchKernel','cudaLaunchKernel_v7000'},),
    'copy':({'cudaMemcpyAsync','cudaMemcpyAsync_v3020'},),
    'wait':({'cudaStreamSynchronize','cudaStreamSynchronize_v3020'},),
}


def _sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def _json(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def _require(condition,reason):
    if not condition: raise ValueError(reason)
def _pid(value):
    _require(type(value) is int,'PROCESS_ID_MISSING')
    return (value>>24)&0xFFFFFF
def _time(row):
    _require(all(type(row[k]) is int and -(2**63)<=row[k]<2**63 for k in ('start','end'))
             and row['start']<=row['end'],'RAW_TIME_INVALID')
    return row['start'],row['end']
def _ref(table,row,sha):
    return dict(source_sqlite_sha256=sha,source_table=table,source_rowid=row['source_rowid'])
def _verify_files(root,receipt):
    for item in receipt['files'].values():
        p=(root/item['filename']).resolve()
        _require(p.is_relative_to(root) and p.is_file() and p.stat().st_size==item['size_bytes']
                 and _sha(p)==item['sha256'],'CONTROLLED_RECEIPT_HASH_MISMATCH')


def check_controlled_raw(sqlite_path,producer_dir):
    sqlite_path,root=Path(sqlite_path).resolve(),Path(producer_dir).resolve()
    sealed=_json(root/'controlled_receipt.json'); _verify_files(root,sealed)
    producer=_json(root/'producer_receipt.json'); _verify_files(root,producer)
    ledger=_json(root/'pass_identity.json'); host=_json(root/'host_boundaries.json')
    operations=_json(root/'operation_ledger.json')
    _require(sealed['construction']==CONSTRUCTION and sealed['status']==producer['status']=='COMPLETE'
             and operations['schema_version']=='exposedpath-controlled-operations/0.1.0'
             and operations['construction']==CONSTRUCTION and operations['status']=='COMPLETE'
             and operations['request_stream_policy']=='DISJOINT_NONBLOCKING_STREAMS_WARMUP_SEPARATE',
             'CONTROLLED_EXECUTION_INCOMPLETE_OR_VERSION')
    _require(ledger['pass_id']=='pass1' and ledger['runner_git_dirty'] is False
             and ledger['run_role']=='ENGINEERING' and ledger['data_role']=='Engineering', 'CONTROLLED_IDENTITY_INVALID')
    requests=ledger['requests']; pid=ledger['pid']
    _require(len(requests)==2 and len(operations['tokens'])==4 and len(operations['predrains'])==2,
             'CONTROLLED_CONSTRUCTION_COUNT')
    _require(operations['identity']=={k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')},'CONTROLLED_LEDGER_IDENTITY')
    wanted_ops={}; wanted_boundaries={}
    for index,entry in enumerate(requests):
        ident=entry['identity']; rid=ident['request_id']
        _require(rid==f'controlled-{index}' and ident['repeat_id']==str(index)
                 and entry['outcome']=='COMPLETE' and entry['actual_output_tokens']==entry['expected_output_tokens']==2
                 and entry['observed_boundary_ids']==entry['expected_boundary_ids'] and len(entry['expected_boundary_ids'])==3,
                 'CONTROLLED_REQUEST_INCOMPLETE')
        drain=operations['predrains'][index]
        _require(drain['request_id']==rid and drain['operation_id']==f'{rid}:prepare' and drain['status']=='COMPLETE','PREDRAIN_UNPROVEN')
        wanted_ops[f'{rid}:prepare']=(ident,'prepare',None,None)
        for n,token in enumerate((11+index*10,12+index*10)):
            op=operations['tokens'][index*2+n]
            _require(op['identity']==ident and op['expected_token']==op['observed_token']==token
                     and op['token_index']==n and op['status']=='COMPLETE' and op['sync_origin']=='q0_controlled',
                     'CONTROLLED_READBACK_OR_IDENTITY')
            phase='prefill' if n==0 else 'decode'
            _require(op['stages']==[dict(operation_id=f'{rid}:{n}:{s}',stage=s,status='COMPLETE')
                                    for s in ('submit','copy','wait')],'CONTROLLED_STAGE_PLAN')
            for stage in ('submit','copy','wait'):
                wanted_ops[f'{rid}:{n}:{stage}']=(ident,stage,n,phase)
        for h in host:
            p=h['payload']
            if p['identity']==ident:
                _require(p['boundary_id'] not in wanted_boundaries,'DUPLICATE_HOST_BOUNDARY')
                wanted_boundaries[p['boundary_id']]=p
    _require(len(wanted_boundaries)==6,'HOST_BOUNDARY_SET_INVALID')
    sha=_sha(sqlite_path)
    conn=sqlite3.connect(sqlite_path.as_uri()+'?mode=ro&immutable=1',uri=True)
    conn.row_factory=sqlite3.Row
    try:
        _require(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLITE_CORRUPT')
        def rows(table):
            try: return [dict(r) for r in conn.execute(f'SELECT rowid AS source_rowid,* FROM "{table}"')]
            except sqlite3.Error as exc: raise ValueError('RAW_TABLE_MISSING:'+table) from exc
        strings={r['id']:r['value'] for r in rows('StringIds')}
        tables={r[0] for r in conn.execute('SELECT name FROM sqlite_master')}
        _require('CUPTI_ACTIVITY_KIND_DRIVER' not in tables or not rows('CUPTI_ACTIVITY_KIND_DRIVER'),
                 'SEPARATE_DRIVER_TABLE_REQUIRES_ADAPTER')
        enums={r['id']:r['name'] for r in rows('ENUM_NSYS_EVENT_CLASS')}
        copy_enums={r['id']:r['name'] for r in rows('ENUM_CUDA_MEMCPY_OPER')}
        observed_ops={}; observed_points={}
        for row in rows('NVTX_EVENTS'):
            text=row.get('text') or strings.get(row.get('textId'),'')
            if not (text.startswith(OP_PREFIX) or text.startswith(BOUNDARY_PREFIX)): continue
            _require(_pid(row.get('globalTid'))==pid,'NVTX_PROCESS_CONFLICT')
            prefix=OP_PREFIX if text.startswith(OP_PREFIX) else BOUNDARY_PREFIX
            payload=json.loads(text[len(prefix):])
            if prefix==OP_PREFIX:
                key=payload['operation_id']; _require(key in wanted_ops and key not in observed_ops,'OPERATION_SET_CONFLICT')
                identity,stage,token_index,phase=wanted_ops[key]
                _require(payload==dict(construction=CONSTRUCTION,identity=identity,operation_id=key,
                         stage=stage,token_index=token_index,phase=phase),'OPERATION_PAYLOAD_CONFLICT')
                _time(row); observed_ops[key]=row
            else:
                key=payload['boundary_id']
                _require(key in wanted_boundaries and key not in observed_points and payload==wanted_boundaries[key]
                         and row['end'] is None and type(row['start']) is int,'BOUNDARY_SET_CONFLICT')
                observed_points[key]=row
        _require(set(observed_ops)==set(wanted_ops) and set(observed_points)==set(wanted_boundaries),'RAW_MARKERS_MISSING')
        apis=rows('CUPTI_ACTIVITY_KIND_RUNTIME')
        selected={}; used_api=set()
        for key,operation in observed_ops.items():
            found=[a for a in apis if a['globalTid']==operation['globalTid']
                   and operation['start']<=a['start']<=a['end']<=operation['end']]
            found.sort(key=lambda a:(a['start'],a['end'],a['source_rowid']))
            groups=API_NAMES[wanted_ops[key][1]]
            _require(len(found)==len(groups),'EXPECTED_API_SET_MISSING_OR_EXTRA:'+key)
            for a,allowed in zip(found,groups):
                _time(a)
                _require(strings.get(a['nameId']) in allowed
                         and enums.get(a['eventClass'])=='TRACE_PROCESS_EVENT_CUDA_RUNTIME'
                         and a['returnValue']==0 and a['source_rowid'] not in used_api,'API_NAME_LAYER_RETURN_OR_ALIAS')
                used_api.add(a['source_rowid'])
            selected[key]=found
        kernels=rows('CUPTI_ACTIVITY_KIND_KERNEL'); copies=rows('CUPTI_ACTIVITY_KIND_MEMCPY')
        syncs=rows('CUPTI_ACTIVITY_KIND_SYNCHRONIZATION'); memsets=rows('CUPTI_ACTIVITY_KIND_MEMSET')
        activities=[('CUPTI_ACTIVITY_KIND_KERNEL',r) for r in kernels]+[('CUPTI_ACTIVITY_KIND_MEMCPY',r) for r in copies]
        expectations=[]; windows=[]; all_activity_refs=set(); request_streams=[]
        previous_end=None
        for entry in requests:
            identity=entry['identity']; rid=identity['request_id']
            points=[observed_points[k] for k in entry['expected_boundary_ids']]
            start,first,end=[p['start'] for p in points]
            tid=points[0]['globalTid']; drain=observed_ops[f'{rid}:prepare']
            _require(start<=first<=end and drain['end']<=start and all(p['globalTid']==tid for p in points)
                     and (previous_end is None or previous_end<=drain['start']),'REQUEST_TRACE_ORDER_CONFLICT')
            previous_end=end
            _require(all(_pid(a['globalTid'])!=pid or a['end']<=drain['start'] or a['start']>=end
                         or a['source_rowid'] in used_api for a in apis),'UNEXPLAINED_TARGET_API')
            _require(not any(_pid(a['globalPid'])==pid and a['start']<end and start<a['end'] for a in memsets),'UNEXPLAINED_MEMSET')
            chain=[]; stream_identity=None; used_local=set()
            for ordinal in range(2):
                prefix=f'{rid}:{ordinal}:'
                launch=selected[prefix+'submit'][0]; copy=selected[prefix+'copy'][0]; wait=selected[prefix+'wait'][0]
                phase_start=start if ordinal==0 else first; phase_end=first if ordinal==0 else end
                ranges=[observed_ops[prefix+s] for s in ('submit','copy','wait')]
                _require(phase_start<=ranges[0]['start']<=ranges[0]['end']<=ranges[1]['start']<=ranges[1]['end']
                         <=ranges[2]['start']<=ranges[2]['end']<=phase_end and all(r['globalTid']==tid for r in ranges),'OPERATION_TRACE_ORDER')
                matched=[]
                for table,api in (('CUPTI_ACTIVITY_KIND_KERNEL',launch),('CUPTI_ACTIVITY_KIND_MEMCPY',copy)):
                    _require(api['correlationId'] is not None and sum(1 for a in apis if _pid(a['globalTid'])==pid
                             and a['correlationId']==api['correlationId'])==1,'CORRELATION_LAYER_AMBIGUOUS')
                    candidates=[r for t,r in activities if t==table and _pid(r['globalPid'])==pid and r['correlationId']==api['correlationId']]
                    _require(len(candidates)==1,'ACTIVITY_MAPPING_NOT_UNIQUE')
                    r=candidates[0]; _time(r)
                    stream=(r['deviceId'],r['contextId'],r['streamId'])
                    if stream_identity is None: stream_identity=stream
                    _require(stream==stream_identity,'STREAM_CONTEXT_DEVICE_CONFLICT')
                    _require(start<=r['start']<=r['end']<=wait['end'],'ACTIVITY_OUTSIDE_COMPLETION')
                    if table.endswith('KERNEL'):
                        name=strings.get(r['demangledName'],'')
                        _require(re.search(r'\bg8_token_kernel(?:\s*\(|$)',name) is not None,'KERNEL_IDENTITY_CONFLICT')
                    else:
                        _require(r['bytes']==4 and copy_enums.get(r['copyKind'])=='CUDA_MEMCPY_KIND_DTOH','D2H_IDENTITY_CONFLICT')
                    ref=_ref(table,r,sha); matched.append((r,ref))
                    key=(table,r['source_rowid']); used_local.add(key); all_activity_refs.add(key)
                _require(matched[0][0]['end']<=matched[1][0]['start'],'STREAM_OPERATION_ORDER_CONFLICT')
                physical=[s for s in syncs if _pid(s['globalPid'])==pid and s['correlationId']==wait['correlationId']]
                _require(len(physical)==1 and (physical[0]['deviceId'],physical[0]['contextId'],physical[0]['streamId'])==stream_identity,
                         'PHYSICAL_SYNC_MAPPING_CONFLICT')
                chain.extend(matched)
                # Independent construction prefix, not an analyzer-recovered W(s).
                oracle={'construction':{'activities':[dict(activity_label=str(i),start_ns=r['start']-start,end_ns=r['end']-start)
                            for i,(r,_) in enumerate(chain)],'syncs':[dict(sync_label='s',start_ns=wait['start']-start,end_ns=wait['end']-start)]},
                        'expected':{'syncs':[dict(sync_label='s',wait_set_activity_labels=[str(i) for i in range(len(chain))],
                                                 terminal=dict(status='VALID',activity_label=str(len(chain)-1)))]}}
                expectations.append(dict(request_id=rid,repeat_id=identity['repeat_id'],token_index=ordinal,
                    sync_ref=_ref('CUPTI_ACTIVITY_KIND_SYNCHRONIZATION',physical[0],sha),
                    runtime_ref=_ref('CUPTI_ACTIVITY_KIND_RUNTIME',wait,sha),wait_set_refs=[ref for _,ref in chain],
                    terminal_ref=chain[-1][1],timing=calculate_expected_timing(oracle,'s')))
            _require(stream_identity not in request_streams,'REQUEST_STREAM_REUSED')
            request_streams.append(stream_identity)
            _require(not any(_pid(r['globalPid'])==pid and
                         (r['deviceId'],r['contextId'],r['streamId'])==stream_identity for r in memsets),
                     'UNEXPLAINED_DEPENDENCY_MEMSET')
            actual_syncs={s['source_rowid'] for s in syncs if _pid(s['globalPid'])==pid
                          and s['start']<end and start<s['end']}
            expected_syncs={e['sync_ref']['source_rowid'] for e in expectations if e['request_id']==rid}
            _require(actual_syncs==expected_syncs,'TARGET_PHYSICAL_SYNC_SET_CONFLICT')
            for table,r in activities:
                if _pid(r['globalPid'])!=pid: continue
                same_stream=(r['deviceId'],r['contextId'],r['streamId'])==stream_identity
                if same_stream or (r['start']<end and start<r['end']):
                    _require((table,r['source_rowid']) in used_local,'UNEXPLAINED_ACTIVITY_IN_TARGET_OR_DEPENDENCY_SCOPE')
            windows.append(dict(request_id=rid,repeat_id=identity['repeat_id'],start_ns=start,end_ns=end,
                                dependency_start_ns=drain['start'],first_token_ns=first))
        tables={r[0] for r in conn.execute('SELECT name FROM sqlite_master')}
        diagnostics=rows('DIAGNOSTIC_EVENT') if 'DIAGNOSTIC_EVENT' in tables else None
        _require(not diagnostics,'UNBOUNDED_DIAGNOSTIC_REQUIRES_REVIEW')
        return dict(schema_version='exposedpath-controlled-raw-check/0.1.0',construction=CONSTRUCTION,
            status='CONTROLLED_RAW_MATCH',source_sqlite_sha256=sha,
            producer_receipt_sha256=_sha(root/'producer_receipt.json'),
            controlled_receipt_sha256=_sha(root/'controlled_receipt.json'),
            collector_integrity_status='UNKNOWN',dropped_count=None,
            diagnostics_status='NO_EXPORTED_RECORDS' if diagnostics is not None else 'NOT_EXPORTED',
            windows=windows,sync_expectations=expectations,request_streams=request_streams,
            scope_limit='THIS_CLOSED_CONSTRUCTION_ONLY_NOT_ARBITRARY_MODEL',
            gate8_verdict='NOT_RUN',q0_status='NOT_RUN',formal_evidence=False)
    finally:
        conn.close()
