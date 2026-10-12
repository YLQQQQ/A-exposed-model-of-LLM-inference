"""Independent CPU expectations. No target CUDA qualification."""
import importlib.util
import json
from copy import deepcopy
from types import SimpleNamespace

import pytest
from test_gate8_identity import write_json


def api():
    assert importlib.util.find_spec('exposedpath.completion_path'), 'missing prospective completion contract'
    from exposedpath import completion_path
    return completion_path


def test_closed_two_p1_slots_and_distinct_engineering_role():
    m=api(); rows=m.schedule('completion-check')
    assert [b['variant'] for b in rows]==['C0','Cpre']
    for b in rows:
        manifest=m.minimal_fields(b)
        assert manifest['batch_size']==4 and manifest['fixed_input_tokens']==512
        assert manifest['fixed_output_tokens']==2 and manifest['warmup_count']==3
        assert manifest['study_mode']=='COMPLETION_PATH_ENGINEERING'
        assert manifest['domain_qualification'] is None
        assert m.validate(manifest)==b
    for key,value in [('variant','Vsync'),('pass_id','pass0'),('batch_size',1),('warmup_count',1),('run_id','old')]:
        bad=deepcopy(rows[0]);bad[key]=value
        with pytest.raises(ValueError):m.validate_binding(bad)


@pytest.mark.parametrize('variant,expected', [('C0',['host_read','host_read']),('Cpre',['pre_sync','host_read','host_read'])])
def test_real_verified_entry_hook_only_first_measured_token(tmp_path,monkeypatch,variant,expected):
    from test_batch_load_diagnostic import source
    from exposedpath import gate8_diagnostic as entry,runner
    args,_,events=source(tmp_path,monkeypatch)
    m=api();b=next(b for b in m.schedule('completion-check') if b['variant']==variant)
    manifest=json.loads(args['manifest_path'].read_text());manifest.update(m.minimal_fields(b))
    write_json(args['manifest_path'],manifest)
    stream=SimpleNamespace(cuda_stream=0,device=SimpleNamespace(index=0),synchronize=lambda:events.append('pre_sync'))
    monkeypatch.setattr(runner.torch.cuda,'current_stream',lambda _:stream)
    root=entry.run_diagnostic(**args).parent
    assert events==expected
    execution=json.loads((root/'engineering_execution.json').read_text())
    assert execution['completion_path']==b and len(execution['completion_calls'])==1
    call=execution['completion_calls'][0]
    assert call['phase']=='prefill' and call['token_index']==0
    assert call['sync_count']==(variant=='Cpre') and call['status']=='COMPLETE'
    assert call['native_stream']==0 and call['thread_id']>0
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    assert ledger['completion_path']==b
    assert json.loads((root/'batch_tokens.json').read_text())['requests'][0]['token_ids']==[[13]*4,[14]*4]


@pytest.mark.parametrize('damage',['stream','failed_sync'])
def test_failed_actual_stream_or_sync_cannot_complete(tmp_path,monkeypatch,damage):
    from test_batch_load_diagnostic import source
    from exposedpath import gate8_diagnostic as entry,runner
    args,_,_=source(tmp_path,monkeypatch)
    m=api();b=m.schedule('completion-check')[1]
    value=json.loads(args['manifest_path'].read_text());value.update(m.minimal_fields(b));write_json(args['manifest_path'],value)
    def fail():raise RuntimeError('actual sync failure')
    monkeypatch.setattr(runner.torch.cuda,'current_stream',lambda _:SimpleNamespace(cuda_stream=0,
        device=SimpleNamespace(index=1 if damage=='stream' else 0),synchronize=fail))
    report=json.loads(entry.run_diagnostic(**args).read_text())
    assert report['status']=='DIAGNOSTIC_INCOMPLETE'


@pytest.mark.parametrize('variant',['C0','Cpre'])
def test_actual_producer_raw_file_chain_and_independent_member_expectations(tmp_path,monkeypatch,variant):
    m=api()
    from test_n1_model_domain import source
    from scripts.gate8_diagnostic_collect import analyze_receipt
    b=next(b for b in m.schedule('completion-check') if b['variant']==variant)
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=m.batch_binding(b),completion_binding=b)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    path,result=analyze_receipt(manifest,receipt,execution,tmp_path/'local-prefill')
    assert result['status']=='PREFILL_LOCAL_ENGINEERING_ONLY'
    assert result['request_status']=='NOT_ACCEPTED_LOCAL_REVIEW_ONLY'
    assert result['decode_status']=='NOT_ACCEPTED_LOCAL_REVIEW_ONLY'
    a=result['prefill']['a_records'][0]
    # Two 10ns launches plus one 10ns copy; sync APIs have priority.
    assert a['phase']=='prefill' and a['A_cuda_api_ns']==30
    assert a['A_device_wait_ns']==0 and a['A_unattributed_ns']==0
    assert a['A_sync_residual_ns']==(20 if variant=='Cpre' else 10)
    proofs=result['prefill']['facts']['conditional_suffix_proofs']
    assert proofs[0]['syncs']==proofs[1]['syncs']
    # Already completed two kernels are in the pre-sync W; later D2H is not.
    assert [len(s['suffix_activity_ids']) for s in proofs[0]['syncs']]==([2,3] if variant=='Cpre' else [3])
    if variant=='Cpre':
        full=result['full_pre_sync_dependencies'][0]
        assert len(full['drained_raw_prefix_activity_ids'])==12  # two kernels x two tokens x three warmups
        assert len(full['all_observed_preceding_activity_ids'])==14
        assert len(full['request_wait_set_activity_ids'])==2
    assert result['dropped_records_status']=='UNKNOWN' and result['measurement_validity']=='NOT_ASSESSED'
    assert result['timeline']['copy_apis'] and result['timeline']['host_completion']


@pytest.mark.parametrize('damage',['correlation','stream','warning','boundary','drain','duplicate_map','graph','dependency'])
def test_local_prefill_cannot_hide_hard_failure(tmp_path,monkeypatch,damage):
    m=api()
    from test_n1_model_domain import source
    from scripts.gate8_diagnostic_collect import analyze_receipt
    b=m.schedule('completion-check')[1]
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=m.batch_binding(b),completion_binding=b,damage=damage)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    try:
        _,result=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    except ValueError:return
    assert result['status']=='BLOCKED' and not result['prefill']['a_records']


@pytest.mark.parametrize('damage',['variant','count','identity','bool_device','bool_token'])
def test_execution_call_conflicts_refuse_even_with_updated_hash(tmp_path,monkeypatch,damage):
    m=api()
    from test_n1_model_domain import source
    from scripts.gate8_diagnostic_collect import analyze_receipt
    b=m.schedule('completion-check')[1]
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=m.batch_binding(b),completion_binding=b)
    value=json.loads(execution.read_text())
    if damage=='variant':value['completion_calls'][0]['variant']='C0'
    elif damage=='count':value['completion_calls'][0]['sync_count']=0
    elif damage=='bool_device':value['completion_calls'][0]['logical_device']=False
    elif damage=='bool_token':value['completion_calls'][0]['token_index']=False
    else:value['completion_calls'][0]['identity']['request_id']='foreign'
    write_json(execution,value)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    with pytest.raises(ValueError):analyze_receipt(manifest,receipt,execution,tmp_path/'derived')


def test_two_slot_budget_stops_without_retry(tmp_path):
    m=api();seen=[]
    def collect(b,p):
        seen.append(b['variant']);raise ValueError('unknown warning impact')
    result=m.run_batch('completion-check',tmp_path/'batch',collect)
    assert seen==['C0'] and result['runs'][1]['status']=='NOT_RUN'
    assert result['status']=='BLOCKED' and result['automatic_retry'] is False


@pytest.mark.parametrize('variant,expected',[('C0',[31,27,0,2,0]),('Cpre',[32,4,20,4,0])])
def test_independent_hand_timeline_full_predecessors_and_later_copy(variant,expected):
    from test_v141_sync_semantics import _owned_activity,_owned_sync,_semantic_inventory
    from test_v141_a_accounting import _inputs,_api,_activity,_window,_sync
    from exposedpath_v141.sync_semantics import recover_wait_set
    from exposedpath_v141.a_accounting import calculate_a_windows
    acts=[_owned_activity('completed',2,1,5,enqueue_start=-2,enqueue_end=-1),
        _owned_activity('K1',2,10,30,enqueue_start=0,enqueue_end=1),
        _owned_activity('K2',2,30,40,enqueue_start=2,enqueue_end=3),
        _owned_activity('D2H',2,43,44,enqueue_start=43,enqueue_end=45)]
    inv=_semantic_inventory(acts)
    pre=recover_wait_set(inv,_owned_sync('STREAM',20,42))
    assert pre['wait_set_activity_ids']==['completed','K1','K2']
    assert pre['dependency_closure_status']=='COMPLETE' and not pre['reasons']
    post=recover_wait_set(inv,_owned_sync('STREAM',46,48))
    assert post['wait_set_activity_ids']==['completed','K1','K2','D2H']
    apis=(_api('l1',0,1,'cudaLaunchKernel',1),_api('l2',2,3,'cudaLaunchKernel',2),
        _api('copy',20 if variant=='C0' else 43,45,'cudaMemcpyAsync',3),
        _api('post',46,48,'cudaStreamSynchronize',4))
    syncs=(_sync('post',46,48,'VALID_NONEMPTY',post['wait_set_activity_ids']),)
    if variant=='Cpre':
        apis+=(_api('pre',20,42,'cudaStreamSynchronize',5),)
        syncs+=(_sync('pre',20,42,'VALID_NONEMPTY',pre['wait_set_activity_ids']),)
    a=calculate_a_windows(_inputs(windows=(_window('prefill',0,60),),apis=apis,syncs=syncs,
        activities=tuple(_activity(x['record_id'],x['start_ns'],x['end_ns'],
            'MEMCPY' if x['record_id']=='D2H' else 'KERNEL',
            {'K1':1,'K2':2,'D2H':3}.get(x['record_id'])) for x in acts)))[0]
    assert [a[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')]==expected


def test_mode_ambiguity_is_not_resolved_by_same_a_value():
    from test_v141_sync_semantics import _owned_activity,_owned_sync,_semantic_inventory
    from exposedpath_v141.sync_semantics import recover_wait_set
    rows=[_owned_activity('other-blocking',2,1,5,enqueue_start=-2,enqueue_end=-1),
        _owned_activity('target',0,10,15,enqueue_start=2,enqueue_end=3)]
    sync=_owned_sync('STREAM',20,30,stream_id=0)
    legacy=recover_wait_set(_semantic_inventory(rows,mode='LEGACY'),sync)
    ptds=recover_wait_set(_semantic_inventory(rows,mode='PER_THREAD'),sync)
    assert legacy['wait_set_activity_ids']!=ptds['wait_set_activity_ids']
    # Both sets finished before entry and thus would give A wait=0. Membership
    # conflict remains a rejection, never permission to fill a global mode.
    assert all(r['end_ns']<20 for r in rows)


@pytest.mark.parametrize('variant,damage',[('C0',None),('Cpre',None),('Cpre','input'),('Cpre','variant'),('Cpre','role')])
def test_real_seal_and_verified_profile_boundary(tmp_path,monkeypatch,variant,damage):
    import sys,subprocess
    from test_n1_preprofile_identity import prepared_case
    from exposedpath import gate8_isolated_preflight as isolated
    from scripts import gate8_diagnostic_collect as collector
    from test_gate8_identity import sha
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    m.pop('n1_model');m.pop('n1_model_execution')
    b=next(b for b in api().schedule('completion-check') if b['variant']==variant)
    m.update(api().minimal_fields(b))
    model=tmp_path/'model';model.mkdir()
    write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096));m['model_id']=str(model)
    write_json(prepared/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='synthetic',
        fixed_input_tokens=512,samples=[dict(sample_index=i,input_ids=[7]*512,attention_mask=[1]*512) for i in range(4)]))
    m['prompt_tokens_sha256']=sha(prepared/'prompt.json')
    if damage=='input':m['prompt_tokens_sha256']='0'*64
    if damage=='variant':m['completion_path']['variant']='Vsync'
    if damage=='role':m['data_role']='Pilot'
    write_json(prepared/'manifest.json',m)
    nsys=tmp_path/'nsys';nsys.touch();out=tmp_path/'collection'
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(out),'--execute-engineering-diagnostic','--engineering-a-only'])
    monkeypatch.setattr(collector.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    called=[]
    def stop(argv,*a,**kw):
        assert argv[1]=='profile' and 'model-run' in argv
        sealed=isolated.read(out/'auxiliary_preflight.json')
        claim=isolated.consume(receipt=out/'auxiliary_preflight.json',expected_sha=sha(out/'auxiliary_preflight.json'),
            nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==api().batch_binding(b)['run_id'];called.append(argv)
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_REAL_PROFILE')
    monkeypatch.setattr(collector,'run_once',stop)
    if damage:
        with pytest.raises(ValueError):collector.main()
        assert not called
    else:assert collector.main()==1 and len(called)==1


@pytest.mark.parametrize('damage',['future_gap','prefill_gap','pre_stream','pre_failure','mode_prefix'])
def test_phase_bounded_failure_and_actual_sync_rejections(tmp_path,monkeypatch,damage):
    from test_n1_model_domain import source
    from scripts.gate8_diagnostic_collect import analyze_receipt
    b=api().schedule('completion-check')[1]
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=api().batch_binding(b),completion_binding=b,damage=damage)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    if damage in ('pre_failure','mode_prefix'):
        with pytest.raises(ValueError):analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
        return
    _,result=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    if damage=='pre_stream':
        assert result['status']=='BLOCKED' and not result['prefill']['a_records']
        assert 'ENGINEERING_SCOPE_SYNC_SCOPE' in result['prefill']['reasons']
    elif damage=='prefill_gap':
        assert result['status']=='BLOCKED' and result['prefill']['reasons']==['ENGINEERING_SCOPE_SUBMIT_MAPPING']
    else:
        assert result['status']=='PREFILL_LOCAL_ENGINEERING_ONLY'
        assert len(result['decode_unresolved_effects'])==1 and result['decode_status']=='NOT_ACCEPTED_LOCAL_REVIEW_ONLY'
        assert result['prefill']['a_records'][0]['A_unattributed_ns']==0


def test_old_domain_reader_cannot_accept_new_local_role(tmp_path,monkeypatch):
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain
    from exposedpath_v141.gate8_engineering_scope import process_engineering_scope
    b=api().schedule('completion-check')[0]
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=api().batch_binding(b),completion_binding=b)
    with pytest.raises(ValueError,match='DECLARATION'):process_domain(receipt,execution,tmp_path/'old-domain')
    with pytest.raises(ValueError,match='LOCAL_COMPLETION_ENTRY_REQUIRED'):
        process_engineering_scope(receipt,execution,tmp_path/'old-engineering')
