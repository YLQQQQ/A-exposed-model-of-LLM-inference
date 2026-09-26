"""Stage producer -> synthetic SQLite -> real file entry. No real Nsight."""
import json
import sqlite3
from itertools import count
from types import SimpleNamespace

import pytest
from exposedpath.gate8_stages import StageRecorder
from test_gate8_file_chain import input_files, api
from test_gate8_identity import write_json, sha


def stage_files(tmp_path, monkeypatch, damage=None):
    files=input_files(tmp_path,monkeypatch)
    ledger=json.loads(files['pass_identity'].read_text())
    labels=[]
    cuda=SimpleNamespace(is_initialized=lambda:False,
        nvtx=SimpleNamespace(range_push=labels.append,range_pop=lambda:None))
    monkeypatch.setattr('exposedpath.gate8_stages.threading.get_native_id',lambda:4)
    ticks=count(100)
    recorder=StageRecorder(ledger,0,cuda,lambda:next(ticks),setup_observed=False)
    for r in ledger['requests']:
        recorder.observe('measured',r['identity'],lambda:None)
    with sqlite3.connect(files['sqlite']) as db:
        tid=db.execute('SELECT globalTid FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1').fetchone()[0]
        for (start,end),label in zip(((-70,150),(230,450)),labels):
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',
                       (start,end,label,tid))
        if damage=='worker':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=? WHERE correlationId=6',(tid+1,))
        elif damage=='marker':
            db.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_STAGE_V1:%'")
        elif damage=='clock_order':
            db.execute("UPDATE NVTX_EVENTS SET end=start-1 WHERE text LIKE 'EXPOSEDPATH_STAGE_V1:%'")
        elif damage=='logical':
            for entry in recorder.value['stages']:
                entry['payload']['logical_device']=1
                for probe in (entry['before'],entry['after']): probe['logical_device']=1
                import hashlib
                payload=entry['payload']
                payload['stage_id']=hashlib.sha256(json.dumps({k:v for k,v in payload.items() if k!='stage_id'},sort_keys=True).encode()).hexdigest()
            rows=db.execute("SELECT rowid FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_STAGE_V1:%'").fetchall()
            for (rowid,),entry in zip(rows,recorder.value['stages']):
                db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',
                    ('EXPOSEDPATH_STAGE_V1:'+json.dumps(entry['payload']),rowid))
    files['stage_ledger']=write_json(tmp_path/'stage_ledger.json',recorder.value)
    files['drain_ledger']=write_json(tmp_path/'drain_ledger.json',{
        'schema_version':'exposedpath-drain-ledger/0.1.0','drains':[]})
    p=json.loads(files['producer_receipt'].read_text())
    p['schema_version']='exposedpath-gate8-producer-receipt/0.3.0'
    for key in ('stage_ledger','drain_ledger'):
        path=files[key]
        p['files'][path.name]=dict(filename=path.name,sha256=sha(path),size_bytes=path.stat().st_size)
    write_json(files['producer_receipt'],p)
    report=json.loads(files['export_report'].read_text())
    report['canonical_sqlite_sha256']=sha(files['sqlite'])
    report['attempts'][0].update(sqlite_sha256=sha(files['sqlite']),sqlite_size=files['sqlite'].stat().st_size)
    write_json(files['export_report'],report)
    return files


@pytest.mark.parametrize('worker',[False,True])
def test_stage_file_chain_association_does_not_invent_worker_ownership(monkeypatch,tmp_path,worker):
    files=stage_files(tmp_path,monkeypatch,'worker' if worker else None)
    before={k:sha(p) for k,p in files.items()}
    receipt=api().write_input_receipt(tmp_path/'input.json',artifacts=files,
        collector_version='synthetic',capture_session_id='synthetic')
    output=api().process_gate8_receipt(receipt,tmp_path/'derived')
    result=api().load_chain_result(output)
    assert result['schema_version']=='exposedpath-gate8-file-chain/0.5.0'
    assert result['status']=='BLOCKED' and result['gate8_verdict']=='NOT_RUN'
    diagnostics=json.loads((output.parent/'projection/stages.json').read_text())
    stage=diagnostics['stages'][0]
    if worker:
        assert any(r['reason']=='OTHER_THREAD_OWNERSHIP_UNKNOWN' for r in stage['unresolved_submissions'])
        assert len(stage['same_thread_api_refs'])==1
    else:
        assert stage['unresolved_submissions']==[]
        assert len(stage['same_thread_api_refs'])==2
    assert stage['scope_semantics']=='HOST_CALL_ONLY'
    assert diagnostics['measurement_validity']=='NOT_ASSESSED'
    assert diagnostics['stream_lifetime_status']=='UNKNOWN'
    assert not list(output.parent.rglob('ab_manifest.json'))
    assert not list(output.parent.rglob('derived_manifest.json'))
    assert {k:sha(p) for k,p in files.items()}==before


@pytest.mark.parametrize('damage',['marker','clock_order','logical'])
def test_stage_trace_mismatch_does_not_publish(monkeypatch,tmp_path,damage):
    files=stage_files(tmp_path,monkeypatch,damage)
    receipt=api().write_input_receipt(tmp_path/'input.json',artifacts=files,
        collector_version='synthetic',capture_session_id='synthetic')
    with pytest.raises(ValueError):
        api().process_gate8_receipt(receipt,tmp_path/'derived')
    assert not (tmp_path/'derived').exists()


@pytest.mark.parametrize('damage',['version','identity','missing','partial'])
def test_bad_stage_ledger_rejected_even_with_refreshed_receipt_hash(monkeypatch,tmp_path,damage):
    files=stage_files(tmp_path,monkeypatch)
    value=json.loads(files['stage_ledger'].read_text())
    if damage=='version': value['schema_version']='future'
    elif damage=='identity': value['stages'][0]['payload']['identity']['pass_id']='pass0'
    elif damage=='missing': value['stages'].pop()
    write_json(files['stage_ledger'],value)
    if damage=='partial': files['stage_ledger'].write_text('{')
    p=json.loads(files['producer_receipt'].read_text())
    p['files']['stage_ledger.json'].update(sha256=sha(files['stage_ledger']),size_bytes=files['stage_ledger'].stat().st_size)
    write_json(files['producer_receipt'],p)
    with pytest.raises(ValueError):
        api().write_input_receipt(tmp_path/'input.json',artifacts=files,
            collector_version='synthetic',capture_session_id='synthetic')
    assert not (tmp_path/'input.json').exists()


def test_stage_diagnostics_cannot_be_promoted_by_synthetic_quality_override(monkeypatch,tmp_path):
    files=stage_files(tmp_path,monkeypatch)
    receipt=api().write_input_receipt(tmp_path/'input.json',artifacts=files,
        collector_version='synthetic',capture_session_id='synthetic')
    with pytest.raises(ValueError,match='STAGE_SOURCE_NOT_QUALIFIED'):
        api().process_gate8_receipt(receipt,tmp_path/'derived',synthetic_fixture=True,
                                    integrity_receipts_path=tmp_path/'not_even_read.json')
    assert not (tmp_path/'derived').exists()


def refresh_result_file(result, path, root):
    entry=next(e for e in result['files'] if e['filename']==path.relative_to(root).as_posix())
    entry.update(sha256=sha(path),size_bytes=path.stat().st_size)


@pytest.mark.parametrize('damage',['downgrade','downgrade_and_rehash_stage',
                                 'input_artifact_removed','input_version_downgraded'])
def test_stage_result_version_is_bound_to_input_not_self_declaration(monkeypatch,tmp_path,damage):
    files=stage_files(tmp_path,monkeypatch)
    receipt=api().write_input_receipt(tmp_path/'input.json',artifacts=files,
        collector_version='synthetic',capture_session_id='synthetic')
    output=api().process_gate8_receipt(receipt,tmp_path/'derived')
    result=json.loads(output.read_text())
    if damage.startswith('downgrade'):
        result['schema_version']='exposedpath-gate8-file-chain/0.1.0'
        result.pop('stage_diagnostics_sha256')
        if damage.endswith('rehash_stage'):
            stage_path=output.parent/'projection/stages.json'
            stages=json.loads(stage_path.read_text()); stages['default_stream_mode']='LEGACY'
            write_json(stage_path,stages)
            refresh_result_file(result,stage_path,output.parent)
    else:
        input_path=output.parent/'provenance/input_receipt.json'
        value=json.loads(input_path.read_text())
        if damage=='input_artifact_removed': value['artifacts'].pop('stage_ledger')
        else: value['schema_version']='exposedpath-gate8-input-receipt/0.1.0'
        write_json(input_path,value)
        result['input_receipt_sha256']=sha(input_path)
        refresh_result_file(result,input_path,output.parent)
    write_json(output,result)
    with pytest.raises(ValueError,match='VERSION|ARTIFACT'):
        api().load_chain_result(output)


def test_old_input_cannot_accept_unclaimed_extra_stage_files(monkeypatch,tmp_path):
    from test_gate8_file_chain import receipt
    path,_=receipt(tmp_path,monkeypatch)
    output=api().process_gate8_receipt(path,tmp_path/'derived')
    result=json.loads(output.read_text())
    extra=write_json(output.parent/'projection/stages.json',{'unclaimed':'extra'})
    result['files'].append(dict(filename='projection/stages.json',sha256=sha(extra),size_bytes=extra.stat().st_size))
    write_json(output,result)
    with pytest.raises(ValueError,match='VERSION|ARTIFACT'):
        api().load_chain_result(output)
