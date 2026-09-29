"""Explicit stream bridge -> Canonical -> physical S/A/B, synthetic evidence only."""
import importlib
import json
import sqlite3
from types import SimpleNamespace
import pytest
from test_gate9_domain import source, N1
from test_gate8_identity import write_json, sha


def source_n1(tmp_path,monkeypatch,damage=None,warmup=False):
    receipt,execution,paths=source(tmp_path,monkeypatch)
    manifest=json.loads(paths['wmpc_manifest'].read_text()); manifest['domain_qualification']['profile']=N1
    write_json(paths['wmpc_manifest'],manifest)
    ledger=json.loads(paths['pass_identity'].read_text()); ledger['wmpc_manifest_sha256']=sha(paths['wmpc_manifest'])
    if warmup: ledger['requests'][0]['request_role']='warmup'
    write_json(paths['pass_identity'],ledger)
    records=[]
    from exposedpath.gate9_stream_bridge import StreamBridge
    with sqlite3.connect(paths['sqlite']) as db:
        db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET nullStreamId=1')
        db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=2')
        for rowid,text in db.execute("SELECT rowid,text FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_STREAM_LIFETIME_V1:%'").fetchall():
            payload=json.loads(text.split(':',1)[1]); payload['producer_source_sha256']=ledger['runner_source_sha256']
            payload['generation']='live-0'
            db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',('EXPOSEDPATH_STREAM_LIFETIME_V1:'+json.dumps(payload),rowid))
        tid=db.execute('SELECT globalTid FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1').fetchone()[0]
        for i,req in enumerate(ledger['requests']):
            labels=[]
            stream=SimpleNamespace(cuda_stream=123,device=SimpleNamespace(index=0),synchronize=lambda:None)
            cuda=SimpleNamespace(current_stream=lambda _:stream,nvtx=SimpleNamespace(range_push=labels.append,range_pop=lambda:None))
            bridge=StreamBridge(cuda,stream,req['identity'],'live-0')
            correlations=[6,7] if i==0 else [16,17,36,37]
            with bridge:
                for corr in correlations:
                    if corr in (7,17,37): bridge.synchronize()
                    else: bridge.observe('submit',lambda h:None)
            ranges=[(99,301)] if i==0 else [(399,501)]
            ranges += [(a-1,min(b+1,300 if i==0 else 500)) for corr in correlations for a,b in db.execute('SELECT start,end FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId=?',(corr,))]
            for (a,b),label in zip(ranges,labels):
                db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',(a,b,label,tid))
            records.append(dict(identity=req['identity'],generation='live-0',status=bridge.status,records=bridge.records))
        if damage=='stream': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET streamId=9 WHERE correlationId=16')
        if damage=='correlation': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=999 WHERE correlationId=16')
        if damage=='marker': db.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_STREAM_BRIDGE_V1:%'")
        if damage=='flags': db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=0')
        if damage=='first_drain': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE correlationId=100')
        if damage=='generation':
            records[1]['generation']='other-generation'
            for r in records[1]['records']: r['payload']['generation']='other-generation'
            for rowid,text in db.execute("SELECT rowid,text FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_STREAM_BRIDGE_V1:%'").fetchall():
                p=json.loads(text.split(':',1)[1])
                if p['identity']==ledger['requests'][1]['identity']:
                    p['generation']='other-generation'
                    db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',('EXPOSEDPATH_STREAM_BRIDGE_V1:'+json.dumps(p),rowid))
        if damage=='namespace': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET globalPid=globalPid+? WHERE correlationId=16',(1<<48,))
        if damage=='logical':
            for rowid,text in db.execute("SELECT rowid,text FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_STREAM_BRIDGE_V1:%'").fetchall():
                p=json.loads(text.split(':',1)[1]); p['logical_device']=3
                db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',('EXPOSEDPATH_STREAM_BRIDGE_V1:'+json.dumps(p),rowid))
            for request in records:
                for r in request['records']: r['payload']['logical_device']=3
    if damage=='handle': records[1]['records'][0]['after_native_handle']=456
    if damage=='identity': records[1]['identity']['run_id']='other'
    bridge_path=write_json(tmp_path/'bridge.json',dict(schema_version='exposedpath-stream-bridge/0.1.0',
        source_sha256=ledger['runner_source_sha256'],pid=ledger['pid'],requests=records))
    producer=json.loads(paths['producer_receipt'].read_text())
    paths.pop('stage_ledger')
    producer['schema_version']='exposedpath-gate8-producer-receipt/0.2.0'
    producer['files'].pop('stage_ledger.json')
    producer['files']['pass_identity.json'].update(sha256=sha(paths['pass_identity']),size_bytes=paths['pass_identity'].stat().st_size)
    write_json(paths['producer_receipt'],producer)
    export=json.loads(paths['export_report'].read_text()); export['canonical_sqlite_sha256']=sha(paths['sqlite'])
    export['attempts'][0].update(sqlite_sha256=sha(paths['sqlite']),sqlite_size=paths['sqlite'].stat().st_size)
    write_json(paths['export_report'],export)
    from exposedpath_v141.gate8_files import write_input_receipt
    receipt=write_input_receipt(tmp_path/'n1-input.json',artifacts=paths,collector_version='2026.2.1.210',capture_session_id='synthetic')
    execution=write_json(tmp_path/'n1-execution.json',dict(schema_version='exposedpath-n1-bridge-execution/0.1.0',
        input_receipt_sha256=sha(receipt),bridge_sha256=sha(bridge_path),status='COMPLETE'))
    return receipt,execution,bridge_path


def test_unmapped_warmup_cannot_be_relabelled_as_measured(tmp_path,monkeypatch):
    paths=source_n1(tmp_path,monkeypatch,warmup=True)
    import exposedpath_v141.gate9_domain as domain
    with pytest.raises(ValueError,match='BRIDGE_REQUEST_SET'):
        domain.process_domain(paths[0],paths[1],tmp_path/'out',bridge_path=paths[2])


@pytest.mark.parametrize('cupti_flag,accepted',[(2,True),(1,False),(0,False),(3,False),(99,False)])
def test_cupti_stream_type_is_not_runtime_creation_flags(tmp_path,monkeypatch,cupti_flag,accepted):
    receipt,execution,bridge=source_n1(tmp_path,monkeypatch)
    from exposedpath_v141.gate8_files import load_input_receipt,write_input_receipt
    from exposedpath_v141.gate9_domain import process_domain
    _,paths=load_input_receipt(receipt)
    with sqlite3.connect(paths['sqlite']) as db:
        db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=?',(cupti_flag,))
    export=json.loads(paths['export_report'].read_text(encoding='utf-8'))
    export['canonical_sqlite_sha256']=sha(paths['sqlite'])
    export['attempts'][0].update(sqlite_sha256=sha(paths['sqlite']),sqlite_size=paths['sqlite'].stat().st_size)
    write_json(paths['export_report'],export)
    receipt=write_input_receipt(tmp_path/'flag-input.json',artifacts=paths,collector_version='2026.2.1.210',capture_session_id='synthetic')
    value=json.loads(execution.read_text(encoding='utf-8'));value['input_receipt_sha256']=sha(receipt)
    execution=write_json(tmp_path/'flag-execution.json',value)
    if accepted:
        assert process_domain(receipt,execution,tmp_path/'out',bridge_path=bridge).is_file()
    else:
        with pytest.raises(ValueError,match='BRIDGE_EXPLICIT_NONBLOCKING'):
            process_domain(receipt,execution,tmp_path/'out',bridge_path=bridge)


def test_physical_members_include_completed_prior_not_only_overlap(tmp_path,monkeypatch):
    paths=source_n1(tmp_path,monkeypatch)
    import exposedpath_v141.gate9_domain as domain
    out=domain.process_domain(paths[0],paths[1],tmp_path/'out',bridge_path=paths[2])
    result=json.loads(out.read_text())
    assert result['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
    b=[r for r in result['b_records'] if r['request_id']=='request-1']
    assert [len(r['wait_set_activity_ids']) for r in b]==[2,3]
    assert [r['validity'] for r in b]==['B_VALID','B_VALID']
    assert [(r['wait_set_hidden_union_ns'],r['wait_set_exposed_union_ns'],r['sync_return_tail_ns']) for r in b]==[(45,5,10),(75,10,15)]
    assert all(r['actual_trace_stream_id']==2 and r['native_handle']==123 for r in result['bridge_bindings'])
    assert domain.load_domain(out,paths[0],paths[1],bridge_path=paths[2])==result


@pytest.mark.parametrize('damage',['stream','correlation','marker','flags','handle','identity','namespace','logical','first_drain','generation'])
def test_bridge_cannot_borrow_context_or_ownership(tmp_path,monkeypatch,damage):
    paths=source_n1(tmp_path,monkeypatch,damage)
    import exposedpath_v141.gate9_domain as domain
    with pytest.raises(ValueError): domain.process_domain(paths[0],paths[1],tmp_path/'out',bridge_path=paths[2])
    assert not (tmp_path/'out').exists()
