"""Actual diagnostic runner/files with CPU doubles; not server qualification."""
import json
import sqlite3
from types import SimpleNamespace
import pytest
from test_gate8_diagnostic_entry import case
from test_gate8_identity import sha, write_json


@pytest.mark.parametrize('backend',['sdpa','wrong','wrong_model'])
def test_predeclared_profile_is_bound_to_actual_setup_before_requests(tmp_path,monkeypatch,backend):
    from exposedpath import gate8_diagnostic as module, runner
    from exposedpath.gate8_engineering_contract import declaration
    from exposedpath_v141 import gate8_source_probe
    args,state=case(monkeypatch,tmp_path)
    manifest=json.loads(args['manifest_path'].read_text())
    manifest.update(attention_backend='sdpa',engineering_scope=declaration('sdpa'))
    write_json(args['manifest_path'],manifest)
    write_json(args['preflight_path'],dict(physical_gpu_index=3,logical_gpu_index=0,
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='0000:01:00.0'))
    monkeypatch.setattr(module,'validate_pre_model_identity',lambda *a:[])
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='0000:01:00.0')))
    load=runner.load_model
    def configured(*a,**kw):
        result=load(*a,**kw)
        result[0].config=SimpleNamespace(_attn_implementation='sdpa' if backend=='wrong_model' else backend,
            model_type='other' if backend=='wrong_model' else 'qwen2',use_cache=True)
        return result
    monkeypatch.setattr(runner,'load_model',configured)
    result=module.run_diagnostic(**args)
    receipt=json.loads((result.parent/'engineering_execution.json').read_text())
    assert receipt['manifest_sha256']==sha(args['manifest_path'])
    assert receipt['producer_receipt_sha256']==sha(result.parent/'producer/producer_receipt.json')
    assert receipt['observed_configuration']['configured_attention_backend']==('sdpa' if backend=='wrong_model' else backend)
    assert receipt['status']==('COMPLETE' if backend=='sdpa' else 'INCOMPLETE')
    probe=json.loads((result.parent/'cuda_probe.json').read_text())
    ledger=json.loads((result.parent/'producer/pass_identity.json').read_text())
    assert probe['pid']==ledger['pid'] and probe['gpu_index_logical']==0
    assert sha(result.parent/'runner_source.py')==ledger['runner_source_sha256']
    if backend!='sdpa':
        assert not any(r['observed_boundary_ids'] for r in ledger['requests'])
        assert state['syncs']==0


def test_unknown_profile_cannot_enter_model_setup(tmp_path,monkeypatch):
    from exposedpath import gate8_diagnostic as module
    args,state=case(monkeypatch,tmp_path)
    manifest=json.loads(args['manifest_path'].read_text())
    manifest['engineering_scope']={'profile':'future'}
    write_json(args['manifest_path'],manifest)
    monkeypatch.setattr(module,'validate_pre_model_identity',lambda *a:[])
    with pytest.raises(ValueError): module.run_diagnostic(**args)
    assert state['loads']==0


def test_actual_producer_receipts_flow_into_canonical_and_a(tmp_path,monkeypatch):
    from exposedpath import gate8_diagnostic as module, runner
    from exposedpath.gate8_engineering_contract import declaration
    from exposedpath_v141 import gate8_source_probe
    from exposedpath_v141.gate8_files import write_input_receipt
    from exposedpath_v141.gate8_engineering_scope import process_engineering_scope
    from test_gate8_identity import sources
    from exposedpath_v141 import gate8_target_python as target
    import sys,sysconfig,os,shutil
    contract=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    runtime=dict(pid=os.getpid(),parent_pid=os.getppid(),snapshot=contract['actual']['snapshot'])
    monkeypatch.setattr(target,'current',lambda _:runtime)  # CPU runner double; real adapter covered separately.
    monkeypatch.setattr(module,'verify_model_inventory',lambda *a,**kw:{})
    args,_=case(monkeypatch,tmp_path)
    value=json.loads(args['manifest_path'].read_text())
    value.update(attention_backend='sdpa',engineering_scope=declaration('sdpa'),
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='0000:01:00.0',
        target_python=contract,model_content_snapshot={'inventory_sha256':'0'*64})
    write_json(args['manifest_path'],value)
    write_json(args['preflight_path'],dict(physical_gpu_index=3,logical_gpu_index=0,
        gpu_uuid=value['gpu_uuid'],gpu_pci_bus_id=value['gpu_pci_bus_id']))
    monkeypatch.setattr(module,'validate_pre_model_identity',lambda *a:[])
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid=value['gpu_uuid'],pci_bus_id=value['gpu_pci_bus_id'])))
    load=runner.load_model
    def configured(*a,**kw):
        result=load(*a,**kw)
        result[0].config=SimpleNamespace(_attn_implementation='sdpa',model_type='qwen2',use_cache=True)
        return result
    monkeypatch.setattr(runner,'load_model',configured)
    labels=[]
    monkeypatch.setattr(runner.torch.cuda.nvtx,'range_push',labels.append)
    monkeypatch.setattr(runner.torch.cuda.nvtx,'mark',labels.append)
    result=module.run_diagnostic(**args)
    root=result.parent
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    stages=json.loads((root/'producer/stage_ledger.json').read_text())
    tid=(ledger['pid']<<24)|stages['stages'][-1]['thread_id']
    pid=tid-tid%2**24
    rawdir=tmp_path/'raw'; rawdir.mkdir()
    db,*_=sources(rawdir)
    with sqlite3.connect(db) as c:
        c.execute('DELETE FROM NVTX_EVENTS')
        stage_index=point_index=0
        for label in labels:
            if label.startswith('EXPOSEDPATH_STAGE_V1:'):
                a,b=((0,40),(50,80),(85,310))[stage_index]; stage_index+=1
            elif label.startswith('EXPOSEDPATH_DRAIN_V1:'): a,b=90,99
            elif label.startswith('EXPOSEDPATH_BOUNDARY_V1:'):
                a=(100,180,300)[point_index]; b=None; point_index+=1
            else: continue
            c.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,?,?,?)',
                (a,b,34 if b is None else 59,label,tid))
        for table in ('CUPTI_ACTIVITY_KIND_MEMCPY','CUPTI_ACTIVITY_KIND_MEMSET','CUPTI_ACTIVITY_KIND_CUDA_EVENT'):
            c.execute('DELETE FROM '+table)
        c.execute('UPDATE TARGET_INFO_CUDA_DEVICE SET pid=?',(ledger['pid'],))
        c.execute("UPDATE TARGET_INFO_GPU SET busLocation='0000:01:00.0'")
        c.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET processId=?,nullStreamId=2',(ledger['pid'],))
        c.execute('UPDATE TARGET_INFO_CUDA_STREAM SET processId=?',(ledger['pid'],))
        c.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET start=140,end=170,globalTid=?',(tid,))
        c.execute("INSERT INTO StringIds VALUES (20,'cudaLaunchKernel'),(21,'cudaDeviceSynchronize')")
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (110,115,0,?,6,20,0,NULL)',(tid,))
        c.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET start=130,end=160,globalPid=?',(pid,))
        c.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET start=145,end=165,globalPid=?',(pid,))
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT start+120,end+120,eventClass,globalTid,correlationId+20,nameId,returnValue,callchainId FROM CUPTI_ACTIVITY_KIND_RUNTIME')
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL SELECT start+120,end+120,deviceId,contextId,greenContextId,streamId,correlationId+20,globalPid,demangledName,shortName,graphNodeId,graphId FROM CUPTI_ACTIVITY_KIND_KERNEL')
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SELECT start+120,end+120,deviceId,contextId,greenContextId,streamId,correlationId+20,globalPid,deprecatedSyncType,syncType,eventId,eventSyncId FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION')
        c.execute("INSERT INTO ENUM_CUPTI_SYNC_TYPE VALUES (2,'CONTEXT','Context synchronize')")
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (92,98,0,?,100,21,0,NULL)',(tid,))
        c.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (93,97,0,1,NULL,4294967295,100,?,NULL,2,4294967295,NULL)',(pid,))
        c.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN globalPid INTEGER')
        c.execute('ALTER TABLE DIAGNOSTIC_EVENT ADD COLUMN timestampType INTEGER')
        c.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (0,2,1,?,?,2)',
            ('Process '+str(ledger['pid'])+' was launched by the profiler',pid))
    rep=tmp_path/'synthetic.rep'; rep.write_bytes(b'Synthetic trace, not Nsight')
    export=write_json(tmp_path/'export.json',dict(status='PASS',error=None,analyzer_allowed=True,
        attempt_count=1,successful_attempt=1,rep_sha256=sha(rep),canonical_sqlite_sha256=sha(db),
        attempts=[dict(number=1,status='PASS',exit_code=0,process_exited=True,timed_out=False,
            terminated_pid=None,validation_issues=[],rep_sha256=sha(rep),sqlite_sha256=sha(db),sqlite_size=db.stat().st_size)]))
    paths=dict(raw=rep,sqlite=db,export_report=export,
        **{k:root/v for k,v in {'preflight':'adapter_preflight.json','cuda_probe':'cuda_probe.json',
        'wmpc_manifest':'manifest.json','prompt':'prompt.json','runner_source':'runner_source.py',
        'producer_receipt':'producer/producer_receipt.json','pass_identity':'producer/pass_identity.json',
        'host_ledger':'producer/host_boundaries.json','drain_ledger':'producer/drain_ledger.json',
        'stage_ledger':'producer/stage_ledger.json'}.items()})
    receipt=write_input_receipt(tmp_path/'input.json',artifacts=paths,
        collector_version='2026.2.1.210',capture_session_id='CPU-synthetic')
    out=process_engineering_scope(receipt,root/'engineering_execution.json',tmp_path/'baseline-analyzed')
    answer=json.loads(out.read_text())
    assert answer['status']=='A_SCOPE_ENGINEERING_ONLY'
    full=answer['requests'][0]['a_records'][0]
    assert [full[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')]==[130,10,40,20,0]
    assert answer['requests'][0]['identity']==ledger['requests'][1]['identity']
    from scripts.gate8_diagnostic_collect import analyze_model
    shutil.copyfile(db,tmp_path/'capture.sqlite'); shutil.copyfile(rep,tmp_path/'capture.nsys-rep')
    shutil.copyfile(export,tmp_path/'postprocess_report.json')
    result=analyze_model(tmp_path,args['manifest_path'].parent,'2026.2.1.210')
    assert json.loads(result.read_text())['status']=='A_SCOPE_ENGINEERING_ONLY'
    launch=json.loads((tmp_path/'target_launch.json').read_text())
    assert launch['pid']==ledger['pid']
    # A modified runtime cannot borrow the successful producer's identity.
    runtime['pid']+=1; write_json(root/'target_runtime.json',runtime)
    with pytest.raises(ValueError,match='PRODUCER_IDENTITY'):
        analyze_model(tmp_path,args['manifest_path'].parent,'2026.2.1.210')
