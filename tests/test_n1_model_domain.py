"""Verified entry -> real producer files -> synthetic Raw -> existing S/A/B.

CPU trace recorder only. Expected members below are from the prescribed two
launches + D2H sequence, not the analyzer. No target CUDA qualification.
"""
import json
import os
from types import SimpleNamespace
import pytest
from qualification_fixture import capture
from test_n1_verified_entry import source as entry_source
from test_gate8_identity import UUID, sha, write_json


def source(tmp_path, monkeypatch, variant='Vsync', damage=None, internal=False, queries=False,
           default_prefix=False, allocations=False, vm_bits=False, pilot_binding=None):
    queries=queries or damage=='unknown_query'
    from exposedpath import runner
    def execute(Backend, clock, db, plan):
        entry,args,state,events=entry_source(tmp_path,monkeypatch,variant)
        manifest=json.loads(args['manifest_path'].read_text())
        if pilot_binding is not None:
            from exposedpath.gate11_pilot import minimal_fields
            if pilot_binding['variant'] is None:
                manifest.pop('n1_model'); manifest.pop('n1_model_execution')
            manifest.update(minimal_fields(pilot_binding))
        manifest.update(gpu_uuid=UUID,gpu_pci_bus_id='0000:E1:00.0')
        write_json(args['manifest_path'],manifest)
        write_json(args['preflight_path'],dict(physical_gpu_index=3,logical_gpu_index=0,
            gpu_uuid=UUID,gpu_pci_bus_id='0000:E1:00.0'))
        from exposedpath import platform_adapter
        monkeypatch.setattr(platform_adapter,'cuda_identity_native',lambda _:dict(gpu_uuid=UUID,pci_bus_id='0000:E1:00.0'))
        backend=Backend(None); cuda=runner.torch.cuda
        db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET nullStreamId=1')
        db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=2')
        db.execute('INSERT INTO TARGET_INFO_CUDA_STREAM SELECT 3,hwId,vmId,processId,contextId,priority,2 FROM TARGET_INFO_CUDA_STREAM')
        if pilot_binding is not None and pilot_binding['variant'] is None:
            db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET nullStreamId=3')
            db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=3 WHERE streamId=3')
        native_streams={123:2,456:3,0:3}
        def stream_id():
            handle=cuda.current_stream(0).cuda_stream
            if handle not in native_streams:
                sid=max(native_streams.values())+1
                db.execute('INSERT INTO TARGET_INFO_CUDA_STREAM SELECT ?,hwId,vmId,processId,contextId,priority,2 FROM TARGET_INFO_CUDA_STREAM WHERE streamId=3',(sid,))
                native_streams[handle]=sid
            return native_streams[handle]
        def launch():
            a,b,c=backend.api('cudaLaunchKernel_v7000')
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,0,1,NULL,?,?,?,?,?,NULL,NULL)',
                (b,b+2,stream_id(),c,os.getpid()<<24,1,1))
        def sync():
            query='cudaGetDevice' if damage=='unknown_query' else 'cudaStreamIsCapturing'
            if queries: backend.api(query)
            a,b,c=backend.api('cudaStreamSynchronize_v3020')
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,?,0,1,NULL,?,?,?,NULL,3,4294967295,NULL)',
                (a+1,b-1,stream_id(),c,os.getpid()<<24))
            if queries: backend.api(query)
        create=cuda.Stream
        def stream(**kw):
            value=create(**kw); value.synchronize=sync; return value
        monkeypatch.setattr(cuda,'Stream',stream)
        monkeypatch.setattr(cuda,'synchronize',backend.prepare)
        def push(label):
            backend.push(label)
            if damage=='unexpected_sync' and label.startswith('EXPOSEDPATH_N1_MODEL_V1:'):
                payload=json.loads(label.split(':',1)[1])
                if payload.get('operation')=='intervention': sync()
        monkeypatch.setattr(cuda.nvtx,'range_push',push)
        monkeypatch.setattr(cuda.nvtx,'range_pop',backend.pop)
        monkeypatch.setattr(cuda.nvtx,'mark',backend.mark)
        run=runner.run_gate8_requests
        monkeypatch.setattr(runner,'run_gate8_requests',lambda **kw:run(**kw,clock_ns=clock))
        load=runner.load_model
        from test_runner_token_ready import _FakeToken
        cpu=_FakeToken.cpu
        def read(token):
            a,b,c=backend.api('cudaMemcpyAsync_v3020')
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMCPY VALUES (?,?,0,1,NULL,?,?,?,4,2,2,1,NULL)',
                (b,b+2,stream_id(),c,os.getpid()<<24))
            sync(); return cpu(token)
        monkeypatch.setattr(_FakeToken,'cpu',read)
        def model(*a,**kw):
            result=load(*a,**kw)
            for i in (0,15): result[0].model.layers[i].forward=lambda x:launch()
            if internal:
                def first(x):
                    launch(); sync()  # Framework internal call, no intervention marker.
                result[0].model.layers[0].forward=first
            if allocations:
                def allocate_then_launch(x):
                    backend.api('cudaMalloc_v3020'); launch()
                    if internal: sync()
                result[0].model.layers[0].forward=allocate_then_launch
            return result
        monkeypatch.setattr(runner,'load_model',model)
        if default_prefix:
            # Setup work in NULL stream, finished before warmup/request drain.
            # It is NOT in the explicit nonblocking stream's physical W.
            db.execute('INSERT INTO TARGET_INFO_CUDA_STREAM SELECT 1,hwId,vmId,processId,contextId,priority,3 FROM TARGET_INFO_CUDA_STREAM LIMIT 1')
            a,b,c=backend.api('cudaLaunchKernel_v7000')
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,0,1,NULL,?,?,?,?,?,NULL,NULL)',
                (b,b+2,1,c,os.getpid()<<24,1,1))
        entry.run_diagnostic(**args)
        if damage=='correlation': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=999999')
        if damage=='stream': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET streamId=2 WHERE streamId=3')
        if damage=='unknown_api': db.execute("UPDATE StringIds SET value='unknownCudaOperation' WHERE value='cudaLaunchKernel_v7000'")
        if damage=='duplicate_map': db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT * FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId=(SELECT MAX(correlationId) FROM CUPTI_ACTIVITY_KIND_KERNEL)')
        if damage=='warning': db.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (1,3,2,'Unknown CUDA failure',?,2)",(os.getpid()<<24,))
        if damage=='boundary': db.execute("DELETE FROM NVTX_EVENTS WHERE eventType=34")
        if damage=='drain': db.execute("DELETE FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE syncType=2")
        if damage=='marker_sync': db.execute("DELETE FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId=(SELECT MAX(correlationId) FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE syncType=3)")
        if damage=='thread': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET globalTid=globalTid+1 WHERE correlationId=(SELECT MAX(correlationId) FROM CUPTI_ACTIVITY_KIND_KERNEL)')
        if damage=='dependency': db.execute("UPDATE StringIds SET value='cudaStreamWaitEvent' WHERE value='cudaLaunchKernel_v7000'")
        if damage=='drain_scope': db.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET contextId=22 WHERE syncType=2')
        if damage=='graph': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET graphId=7')
        if damage=='blocking_flag': db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=1 WHERE streamId=3')
        if damage=='null_measured': db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET nullStreamId=3')
        if damage=='unmarked_token':
            db.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE '%natural_token_ready%'")
        if damage=='unmarked_intervention':
            db.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE 'EXPOSEDPATH_JSON_V1:%n1_intervention%'")
        if damage=='raw_marker_conflict':
            # Put a structured sync marker with foreign identity around the
            # first internal wait; a Raw alternative must never override it.
            marker=db.execute("SELECT text FROM NVTX_EVENTS WHERE text LIKE '%natural_token_ready%' LIMIT 1").fetchone()[0]
            payload=json.loads(marker.split(':',1)[1]); payload['request_id']='foreign'
            first=db.execute('SELECT start,end FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE correlationId=(SELECT MIN(correlationId) FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE streamId=3)').fetchone()
            tid=db.execute('SELECT globalTid FROM CUPTI_ACTIVITY_KIND_RUNTIME WHERE start=?',(first[0],)).fetchone()[0]
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',
                (first[0],first[1],'EXPOSEDPATH_JSON_V1:'+json.dumps(payload),tid))
        if vm_bits:
            # Nsight global process/thread IDs include a VM field above the
            # 24-bit OS PID. Raw IDs must retain it; PID joins must decode it.
            for table in ('NVTX_EVENTS','CUPTI_ACTIVITY_KIND_RUNTIME'):
                db.execute('UPDATE '+table+' SET globalTid=globalTid+?',(1<<48,))
            for table in ('CUPTI_ACTIVITY_KIND_KERNEL','CUPTI_ACTIVITY_KIND_MEMCPY',
                          'CUPTI_ACTIVITY_KIND_SYNCHRONIZATION','DIAGNOSTIC_EVENT'):
                db.execute('UPDATE '+table+' SET globalPid=globalPid+?',(1<<48,))
        return args['output_dir']/'producer/producer_receipt.json'
    _,_,sqlite,rep,export=capture(tmp_path,monkeypatch,executor=execute)
    root=tmp_path/'diagnostic'
    if pilot_binding is not None and pilot_binding['pass_id']=='pass0':
        return None,root/'engineering_execution.json',root/'n1_model_calls.json'
    from exposedpath_v141.gate8_files import write_input_receipt
    names=dict(preflight='adapter_preflight.json',cuda_probe='cuda_probe.json',wmpc_manifest='manifest.json',
        prompt='prompt.json',runner_source='runner_source.py',producer_receipt='producer/producer_receipt.json',
        pass_identity='producer/pass_identity.json',host_ledger='producer/host_boundaries.json',
        drain_ledger='producer/drain_ledger.json',stage_ledger='producer/stage_ledger.json')
    if pilot_binding is not None: names['pilot_tokens']='pilot_tokens.json'
    receipt=write_input_receipt(tmp_path/'input.json',collector_version='2026.2.1.210',capture_session_id='CPU',
        artifacts=dict(raw=rep,sqlite=sqlite,export_report=export,**{k:root/v for k,v in names.items()}))
    return receipt,root/'engineering_execution.json',root/'n1_model_calls.json'


@pytest.mark.parametrize('variant,sync_count', [('V0',2),('Vmarker',2),('Vsync',3)])
def test_verified_model_multi_api_file_chain(tmp_path,monkeypatch,variant,sync_count):
    receipt,execution,calls=source(tmp_path,monkeypatch,variant)
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    path=process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    result=load_domain(path,receipt,execution,bridge_path=calls)
    assert result['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
    assert len(result['a_records'])==3 and len(result['b_records'])==sync_count
    # 2 kernels + D2H per token. The decode intervention waits for prefix
    # (3 prior activities) plus its 2 model kernels, before final D2H.
    assert sorted(len(b['wait_set_activity_ids']) for b in result['b_records']) == ([3,6] if sync_count==2 else [3,5,6])
    assert all(a['A_unattributed_ns']==0 for a in result['a_records'])
    for a in result['a_records']:
        n=2 if a['phase']=='full_request' else 1
        extra=1 if variant=='Vsync' and a['phase']!='prefill' else 0
        # Recorder API ranges are 10 ns; kernels end before their sync call.
        assert a['A_cuda_api_ns']==30*n and a['A_device_wait_ns']==0
        assert a['A_sync_residual_ns']==10*(n+extra)
        assert a['A_host_path_ns']==a['T_window_ns']-30*n-10*(n+extra)
    assert result['dropped_records_status']=='UNKNOWN'
    assert len(result['model_api_bindings'])==6+sync_count


@pytest.mark.parametrize('damage',['correlation','stream','unknown_api','sidecar_identity','count',
                                  'duplicate_map','warning','boundary','drain','marker_sync','thread','dependency','unknown_query',
                                  'drain_scope','graph'])
def test_model_consumer_rejects_missing_ownership_or_intervention(tmp_path,monkeypatch,damage):
    receipt,execution,calls=source(tmp_path,monkeypatch,damage=damage)
    if damage in ('sidecar_identity','count'):
        value=json.loads(calls.read_text())
        if damage=='count': value['requests'][1]['interventions']=[]
        else: value['requests'][1]['identity']['request_id']='foreign'
        write_json(calls,value)
        value=json.loads(execution.read_text()); value['n1_model_calls_sha256']=sha(calls); write_json(execution,value)
    from exposedpath_v141.gate9_domain import process_domain
    with pytest.raises(ValueError): process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    assert not (tmp_path/'derived/domain.json').exists()


def test_shared_collector_dispatches_model_sidecar_without_controlled_api_assumption(tmp_path,monkeypatch):
    receipt,execution,calls=source(tmp_path,monkeypatch)
    from scripts.gate8_diagnostic_collect import analyze_receipt
    value=json.loads((calls.parent/'manifest.json').read_text())
    path,result=analyze_receipt(value,receipt,execution,tmp_path/'derived')
    assert result['adapter_version']=='exposedpath-n1-model-ownership/0.3.0'
    assert len(result['model_api_bindings'])==9


def test_internal_unmarked_blocking_calls_require_physical_s_identity(tmp_path,monkeypatch):
    receipt,execution,calls=source(tmp_path,monkeypatch,internal=True)
    from exposedpath_v141.gate9_domain import process_domain
    from exposedpath_v141.n1_model_scope import calculate_n1_model,LEGACY_ADAPTER
    # The amended path is explicit; the old adapter continues to reject.
    result=process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    with pytest.raises(ValueError,match='MODEL_PHYSICAL_B:.*INVOCATION_BOUNDARY_INVALID'):
        calculate_n1_model(result.parent,receipt,execution,calls,adapter_version=LEGACY_ADAPTER)


def test_anchor_and_intervention_allow_only_registered_non_submit_companions(tmp_path,monkeypatch):
    receipt,execution,calls=source(tmp_path,monkeypatch,queries=True)
    from exposedpath_v141.gate9_domain import process_domain
    result=json.loads(process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls).read_text())
    full=next(a for a in result['a_records'] if a['phase']=='full_request')
    assert full['A_cuda_api_non_submit_ns']==60
    assert sorted(len(b['wait_set_activity_ids']) for b in result['b_records'])==[3,5,6]


def test_vmarker_actual_sync_cannot_pass_by_declaring_false(tmp_path,monkeypatch):
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='Vmarker',damage='unexpected_sync')
    from exposedpath_v141.gate9_domain import process_domain
    with pytest.raises(ValueError,match='MODEL_INTERVENTION_ACTUAL_COUNT'):
        process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)


def test_nonblocking_model_waits_do_not_require_mode_for_unrelated_default_setup(tmp_path,monkeypatch):
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0',default_prefix=True)
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    result=process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    value=load_domain(result,receipt,execution,bridge_path=calls)
    # Independent submission sequence: 2 kernels + D2H per token, not setup.
    assert [len(b['wait_set_activity_ids']) for b in value['b_records']]==[3,6]
    assert all(b['validity']=='B_VALID' for b in value['b_records'])
    assert all(a['A_unattributed_ns']==0 for a in value['a_records'])


def test_allocation_rejection_keeps_all_source_records_and_other_b_failures(tmp_path,monkeypatch):
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0',allocations=True,internal=True,default_prefix=True)
    from exposedpath_v141.gate9_domain import process_domain
    path=process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    from exposedpath_v141.n1_model_scope import calculate_n1_model,RAW_ADAPTER
    with pytest.raises(ValueError,match='MODEL_UNSUPPORTED_API:') as error:
        calculate_n1_model(path.parent,receipt,execution,calls,adapter_version=RAW_ADAPTER)
    details=json.loads(str(error.value).split('MODEL_UNSUPPORTED_API:',1)[1])
    assert len(details['unsupported_apis'])==2
    assert {r['phase'] for r in details['unsupported_apis']}=={'prefill','decode'}
    assert all(r['api_name']=='cudaMalloc_v3020' and r['category'] is None
        and r['activity_record_ids']==[] and r['sync_record_ids']==[]
        and r['api_record_id'] and type(r['correlation_id']) is int for r in details['unsupported_apis'])
    assert details['physical_b_failures']==[]
    assert all(a['semantic_role']=='KNOWN_ALLOCATION' and a['completion_support']=='UNSUPPORTED'
               for a in details['unsupported_apis'])
    assert not any('DEFAULT_STREAM_MODE_UNKNOWN' in b['secondary_reasons'] for b in details['physical_b_failures'])
    assert json.loads(path.read_text())['allocation_records']


@pytest.mark.parametrize('damage',['blocking_flag','null_measured','dependency','correlation','stream'])
def test_nonblocking_scope_opt_in_never_bypasses_actual_evidence(tmp_path,monkeypatch,damage):
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0',default_prefix=True,damage=damage)
    from exposedpath_v141.gate9_domain import process_domain
    with pytest.raises(ValueError): process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    assert not (tmp_path/'derived/domain.json').exists()


def test_nonblocking_raw_scope_preserves_vm_bits_but_joins_decoded_os_pid(tmp_path,monkeypatch):
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0',default_prefix=True,vm_bits=True)
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    result=process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    value=load_domain(result,receipt,execution,bridge_path=calls)
    assert [len(b['wait_set_activity_ids']) for b in value['b_records']]==[3,6]
    from exposedpath_v141.sync_semantics import load_canonical_bundle
    rows=load_canonical_bundle(result.parent/'canonical/canonical_manifest.json')['records']
    assert all(a['global_pid']>1<<48 for a in rows['device_activity'])
    assert {a['process_id'] for a in rows['device_activity']}=={os.getpid()}
