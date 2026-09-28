"""Real file interfaces with synthetic traces and literal, independent A oracle.

No synthetic zero-loss receipt; these tests do not qualify a real collection.
"""
import importlib
import json
import sqlite3
import subprocess
import sys
from itertools import count
from types import SimpleNamespace

import pytest
from exposedpath.gate8_stages import StageRecorder
from test_gate8_closed_prior import closed_sources
from test_gate8_file_chain import input_files
from test_gate8_identity import write_json, sha

PROFILE = 'TARGET_SCOPE_ENGINEERING_SUFFICIENCY/0.1'


def entry():
    assert importlib.util.find_spec('exposedpath_v141.gate8_engineering_scope'), 'missing explicit real Engineering entry'
    return importlib.import_module('exposedpath_v141.gate8_engineering_scope')


def files(tmp_path, monkeypatch, mutation=None, shift=0):
    def factory(root, monkey, **kwargs):
        inputs, host, drain, _ = closed_sources(root, monkey, shift=shift, return_inputs=True)
        return inputs, host
    paths=input_files(tmp_path,monkeypatch,source_factory=factory)
    paths['drain_ledger']=tmp_path/'drain.json'
    manifest=json.loads(paths['wmpc_manifest'].read_text())
    manifest.update(execution_mode='eager', batch_size=1, attention_backend='sdpa',
        engineering_scope={'profile':PROFILE,'attention_backend':'sdpa',
            'assumptions':['NO_USER_CONCURRENCY','NO_EXPLICIT_IPC_OR_EVENT_DEPENDENCY',
                'NO_UNRECORDED_INCOMING_DEPENDENCY'], 'declaration_role':'PRE_EXECUTION'})
    write_json(paths['wmpc_manifest'],manifest)
    ledger=json.loads(paths['pass_identity'].read_text())
    ledger['wmpc_manifest_sha256']=sha(paths['wmpc_manifest'])
    write_json(paths['pass_identity'],ledger)
    labels=[]
    stream=SimpleNamespace(device=SimpleNamespace(index=0),cuda_stream=0)
    cuda=SimpleNamespace(is_initialized=lambda:True,current_device=lambda:0,
        current_stream=lambda _:stream,default_stream=lambda _:stream,
        nvtx=SimpleNamespace(range_push=labels.append,range_pop=lambda:None))
    monkeypatch.setattr('exposedpath.gate8_stages.threading.get_native_id',lambda:4)
    recorder=StageRecorder(ledger,0,cuda,lambda:next(ticks),setup_observed=True)
    ticks=count(0)
    recorder.observe('setup',None,lambda:None)
    for request in ledger['requests']:
        recorder.observe('measured',request['identity'],lambda:None)
    paths['stage_ledger']=write_json(tmp_path/'stage_ledger.json',recorder.value)
    with sqlite3.connect(paths['sqlite']) as db:
        tid=db.execute('SELECT globalTid FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1').fetchone()[0]
        db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET nullStreamId=2')
        # Add decode activity/sync; hand oracle request1 [400,600):
        # APIs 5+5, waits 20+20, residuals 10+10, Host130.
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT start+120,end+120,eventClass,globalTid,correlationId+20,nameId,returnValue,callchainId FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId IN (16,17)')
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL SELECT start+120,end+120,deviceId,contextId,greenContextId,streamId,correlationId+20,globalPid,demangledName,shortName,graphNodeId,graphId FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=16')
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SELECT start+120,end+120,deviceId,contextId,greenContextId,streamId,correlationId+20,globalPid,deprecatedSyncType,syncType,eventId,eventSyncId FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE correlationId=17')
        for (a,b),label in zip(((-100,0),(50,350),(350,650)),labels):
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',(a+shift,b+shift,label,tid))
        db.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN globalPid INTEGER')
        db.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN timestampType INTEGER')
        if mutation:
            mutation(db,tid)
    producer=json.loads(paths['producer_receipt'].read_text())
    producer['schema_version']='exposedpath-gate8-producer-receipt/0.3.0'
    for role,name in [('pass_identity','pass_identity.json'),('drain_ledger','drain_ledger.json'),('stage_ledger','stage_ledger.json')]:
        p=paths[role]
        producer['files'][name]={'filename':p.name,'sha256':sha(p),'size_bytes':p.stat().st_size}
    write_json(paths['producer_receipt'],producer)
    export=json.loads(paths['export_report'].read_text())
    export['canonical_sqlite_sha256']=sha(paths['sqlite'])
    export['attempts'][0].update(sqlite_sha256=sha(paths['sqlite']),sqlite_size=paths['sqlite'].stat().st_size)
    write_json(paths['export_report'],export)
    from exposedpath_v141.gate8_files import write_input_receipt
    receipt=write_input_receipt(tmp_path/'input.json',artifacts=paths,
        collector_version='2026.2.1.210',capture_session_id='synthetic-test-not-real-nsys')
    execution=write_json(tmp_path/'execution.json',{
        'schema_version':'exposedpath-engineering-execution/0.1.0',
        'manifest_sha256':sha(paths['wmpc_manifest']),
        'producer_receipt_sha256':sha(paths['producer_receipt']),
        'identity':{k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')},
        'declaration':manifest['engineering_scope'],
        'observed_configuration':{'configured_attention_backend':'sdpa','configured_use_cache':True,
            'model_type':'qwen2','execution_mode':'eager'},
        'status':'COMPLETE'})
    return receipt, execution, paths


def run(tmp_path, monkeypatch, mutation=None, shift=0):
    receipt, execution, paths=files(tmp_path,monkeypatch,mutation,shift)
    out=entry().process_engineering_scope(receipt,execution,tmp_path/'out')
    return json.loads(out.read_text()), out, paths


def components(row):
    return [row[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')]


@pytest.mark.parametrize('shift',[0,-550])
def test_default_equivalence_file_chain_preserves_physical_s_b(tmp_path,monkeypatch,shift):
    result,out,paths=run(tmp_path,monkeypatch,shift=shift)
    request=next(r for r in result['requests'] if r['identity']['request_id']=='request-1')
    assert request['status']=='A_SCOPE_ENGINEERING_ONLY'
    assert {r['phase']:components(r) for r in request['a_records']}=={
        'full_request':[130,10,40,20,0],'prefill':[45,5,20,10,0],'decode':[85,5,20,10,0]}
    assert request['facts']['default_equivalence_modes']==['LEGACY','PER_THREAD']
    assert request['assumptions']==json.loads(paths['wmpc_manifest'].read_text())['engineering_scope']['assumptions']
    assert result['dropped_records_status']=='UNKNOWN'
    assert result['gate8_verdict']==result['q0_status']=='NOT_RUN'
    assert result['d_score_allowed'] is result['signature_allowed'] is False
    assert any(r['validity'] not in ('VALID_NONEMPTY','VALID_EMPTY') for r in result['physical_s_records'])
    assert entry().load_engineering_scope(out,tmp_path/'input.json',tmp_path/'execution.json')==result
    assert not list(out.parent.rglob('derived_manifest.json'))


@pytest.mark.parametrize('name',['cudaStreamIsCapturing_v10000','cuKernelGetFunction'])
def test_supported_non_submit_is_not_a_classification_gap(tmp_path,monkeypatch,name):
    def gap(db,tid):
        db.execute('INSERT INTO StringIds VALUES (25,?)',(name,))
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (420,425,0,?,333,25,0,NULL)',(tid,))
    result,_,_=run(tmp_path,monkeypatch,gap)
    r=result['requests'][1]
    assert r['status']=='A_SCOPE_ENGINEERING_ONLY'
    assert components(r['a_records'][0])==[125,15,40,20,0]
    assert r['a_records'][0]['A_cuda_api_non_submit_ns']==5
    assert r['local_gaps']==[]


@pytest.mark.parametrize('damage',['other_stream','correlation','worker','missing_sync','unknown_api','warning','foreign_warning','boundary','drain'])
def test_visible_conflict_or_unbounded_gap_rejects_not_redistributes(tmp_path,monkeypatch,damage):
    def mutate(db,tid):
        if damage=='other_stream': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET streamId=9 WHERE correlationId=16')
        elif damage=='correlation': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=999 WHERE correlationId=16')
        elif damage=='worker': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=globalTid+1 WHERE correlationId=16')
        elif damage=='missing_sync': db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE correlationId=17')
        elif damage=='drain': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE correlationId=101')
        elif damage=='boundary': db.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE '%\"boundary_id\":\"t1-1\"%'")
        elif damage=='unknown_api':
            db.execute("INSERT INTO StringIds VALUES (25,'cuUnknownOperation')")
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (420,425,0,?,333,25,0,NULL)',(tid,))
        else:
            pid=tid-tid%2**24 if damage=='warning' else 99<<24
            db.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,2,'Not all NVTX events might have been collected.',?,2)",(pid,))
    try:
        result,_,_=run(tmp_path,monkeypatch,mutate)
    except ValueError:
        assert not (tmp_path/'out').exists()
    else:
        r=result['requests'][1]
        assert r['status']=='REJECTED' and r['a_records']==[]
        assert r['reasons']


def test_old_manifest_cannot_be_requalified_by_new_execution_receipt(tmp_path,monkeypatch):
    receipt,execution,paths=files(tmp_path,monkeypatch)
    value=json.loads(execution.read_text()); value['manifest_sha256']='0'*64
    write_json(execution,value)
    with pytest.raises(ValueError):
        entry().process_engineering_scope(receipt,execution,tmp_path/'out')
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('conflict',['activity','sync','error'])
def test_non_submit_rule_cannot_hide_file_backed_conflicting_evidence(tmp_path,monkeypatch,conflict):
    def mutate(db,tid):
        db.execute("INSERT INTO StringIds VALUES (25,'cudaStreamIsCapturing_v10000')")
        if conflict=='activity':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET nameId=25 WHERE correlationId=16')
        elif conflict=='sync':
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET nameId=25 WHERE correlationId=17')
        else:
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (420,425,0,?,333,25,900,NULL)',(tid,))
    result,_,_=run(tmp_path,monkeypatch,mutate)
    request=result['requests'][1]
    assert request['status']=='REJECTED' and request['a_records']==[]
    assert request['reasons']


def test_same_numeric_pid_in_another_namespace_cannot_borrow_enqueue(tmp_path,monkeypatch):
    def foreign(db,tid):
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET globalPid=globalPid+? WHERE correlationId=16',(1<<48,))
    result,_,_=run(tmp_path,monkeypatch,foreign)
    assert result['requests'][1]['status']=='REJECTED'
    assert result['requests'][1]['a_records']==[]


def test_blocked_request_does_not_reject_independent_earlier_window(tmp_path,monkeypatch):
    def failed(db,tid):
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE correlationId=17')
    result,_,_=run(tmp_path,monkeypatch,failed)
    assert result['status']=='BLOCKED'
    assert result['requests'][0]['status']=='A_SCOPE_ENGINEERING_ONLY'
    assert result['requests'][1]['status']=='REJECTED'


def test_rehashed_result_cannot_fabricate_accounting_or_drop_source(tmp_path,monkeypatch):
    result,out,_=run(tmp_path,monkeypatch)
    result['requests'][1]['a_records'][0]['A_host_path_ns']+=1
    write_json(out,result)
    with pytest.raises(ValueError,match='RESULT_MISMATCH'):
        entry().load_engineering_scope(out,tmp_path/'input.json',tmp_path/'execution.json')


def test_interrupted_pipeline_does_not_publish(tmp_path,monkeypatch):
    receipt,execution,_=files(tmp_path,monkeypatch)
    module=entry()
    def interrupted(*a,**kw): raise RuntimeError('interrupted')
    monkeypatch.setattr(module,'_calculate',interrupted)
    with pytest.raises(RuntimeError,match='interrupted'):
        module.process_engineering_scope(receipt,execution,tmp_path/'out')
    assert not (tmp_path/'out').exists()
    assert not list(tmp_path.glob('.out-partial-*/engineering_a.json'))


def test_zero_target_event_counter_conflicts_with_observed_boundaries(tmp_path,monkeypatch):
    def zero(db,tid):
        db.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,1,'Number of NVTX events collected: 0.',?,2)",(tid-tid%2**24,))
    result,_,_=run(tmp_path,monkeypatch,zero)
    assert all(r['status']=='REJECTED' and not r['a_records'] for r in result['requests'])


def test_unknown_collector_version_cannot_use_diagnostic_message_rules(tmp_path,monkeypatch):
    receipt,execution,_=files(tmp_path,monkeypatch)
    value=json.loads(receipt.read_text()); value['collector_version']='2099.unknown'
    write_json(receipt,value)
    with pytest.raises(ValueError,match='COLLECTOR_VERSION'):
        entry().process_engineering_scope(receipt,execution,tmp_path/'out')


def test_activity_completion_after_its_sync_return_blocks_even_inside_request(tmp_path,monkeypatch):
    def late(db,tid):
        db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET end=479 WHERE correlationId=16')
    result,_,_=run(tmp_path,monkeypatch,late)
    assert result['requests'][1]['status']=='REJECTED'
    assert result['requests'][1]['a_records']==[]


def test_offline_cli_publishes_separate_result_and_refuses_overwrite(tmp_path,monkeypatch):
    receipt,execution,_=files(tmp_path,monkeypatch)
    command=[sys.executable,'-m','exposedpath_v141.gate8_engineering_scope',
        '--input-receipt',str(receipt),'--execution-receipt',str(execution),'--output-dir',str(tmp_path/'cli')]
    completed=subprocess.run(command,capture_output=True,text=True,timeout=40)
    assert completed.returncode==0,completed.stderr
    assert json.loads((tmp_path/'cli/engineering_a.json').read_text())['status']=='A_SCOPE_ENGINEERING_ONLY'
    again=subprocess.run(command,capture_output=True,text=True,timeout=40)
    assert again.returncode!=0
