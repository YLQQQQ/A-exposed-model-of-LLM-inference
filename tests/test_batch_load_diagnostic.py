"""Prospective batch diagnostic: CPU doubles, never CUDA qualification."""
import importlib.util
import json
import os
from types import SimpleNamespace

import pytest
from test_gate8_identity import write_json, sha


def api():
    assert importlib.util.find_spec('exposedpath.batch_load'), 'missing closed batch diagnostic'
    from exposedpath import batch_load
    return batch_load


def binding(batch=4, pass_id='pass1'):
    return dict(version='BATCH-LOAD-ENGINEERING/0.1', batch_id='batch-check',
        condition=f'B{batch}', batch_size=batch, pair_id=f'batch-check-B{batch}',
        run_id=f'batch-check-B{batch}-{pass_id}', pass_id=pass_id,
        input_tokens=512, output_tokens=2, warmup_count=3, repeat_count=1,
        purpose='SAME_COMPLETION_BATCH_DIAGNOSTIC_ONLY', declaration_role='PRE_EXECUTION',
        formal_eligible=False)


def test_schedule_is_four_fresh_processes_without_extra_points():
    rows=api().schedule('batch-check')
    assert rows==[binding(1,'pass0'),binding(1,'pass1'),binding(4,'pass0'),binding(4,'pass1')]


@pytest.mark.parametrize('damage',['batch','warmup','pass','run','version','role'])
def test_closed_binding_rejects_scope_changes(damage):
    b=binding()
    key,value={'batch':('batch_size',8),'warmup':('warmup_count',1),
        'pass':('pass_id','pass2'),'run':('run_id','another-run'),
        'version':('version','future'),'role':('formal_eligible',True)}[damage]
    b[key]=value
    with pytest.raises(ValueError): api().validate_binding(b)


def test_input_clones_have_explicit_sample_identity_and_digest(tmp_path):
    m=api(); seed=write_json(tmp_path/'seed.json',dict(schema_version='exposedpath-prompt-tokens/1',
        tokenizer_id='synthetic',fixed_input_tokens=512,
        samples=[dict(sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'inputs')
    prompts=[json.loads(p.read_text()) for p in paths]
    assert [len(p['samples']) for p in prompts]==[1,4]
    assert [s['sample_index'] for s in prompts[1]['samples']]==[0,1,2,3]
    assert all(s['input_ids']==[7]*512 for s in prompts[1]['samples'])
    assert prompts[1]['construction']['source_sha256']==sha(seed)
    with pytest.raises(ValueError): m.make_inputs(seed,'0'*64,tmp_path/'bad')


def source(tmp_path,monkeypatch,batch=4,pass_id='pass1',eos=False,short=False):
    from test_gate8_diagnostic_entry import case
    from test_runner_token_ready import _FakeModel,_FakeToken
    from exposedpath import runner,gate8_diagnostic as entry
    from exposedpath_v141 import gate8_source_probe
    args,state=case(monkeypatch,tmp_path)
    model=tmp_path/'model';model.mkdir()
    write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    prompt=dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='synthetic',fixed_input_tokens=512,
        samples=[dict(sample_index=i,input_ids=[7]*512,attention_mask=[1]*512) for i in range(batch)])
    write_json(args['prompt_path'],prompt)
    v=json.loads(args['manifest_path'].read_text());v.update(api().minimal_fields(binding(batch,pass_id)),
        model_id=str(model),prompt_tokens_sha256=sha(args['prompt_path']),
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='00000000:01:00.0')
    write_json(args['manifest_path'],v)
    write_json(args['preflight_path'],dict(physical_gpu_index=3,logical_gpu_index=0,
        gpu_uuid=v['gpu_uuid'],gpu_pci_bus_id=v['gpu_pci_bus_id']))
    events=[]
    def load(*a,**kw):
        state['loads']+=1;state['initialized']=True
        values=[[13]*batch,[14]*batch]*4
        if eos: values[-1][-1]=2
        if short: values[-1]=values[-1][:-1]
        m=_FakeModel(iter([_FakeToken(x,events) for x in values]))
        m.dtype='torch.float16';m.training=False
        m.config=SimpleNamespace(_attn_implementation='sdpa',model_type='qwen2',use_cache=True)
        return m,SimpleNamespace(eos_token_id=2),100,'cuda:0'
    monkeypatch.setattr(runner,'load_model',load)
    monkeypatch.setattr(runner.torch,'tensor',lambda data,**kw:SimpleNamespace(shape=(len(data),len(data[0]))))
    monkeypatch.setattr(entry,'validate_pre_model_identity',lambda *a,**kw:[])
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid=v['gpu_uuid'],pci_bus_id=v['gpu_pci_bus_id']),cuda=runner.torch.cuda))
    from exposedpath import platform_adapter
    monkeypatch.setattr(platform_adapter,'cuda_identity_native',lambda _:dict(gpu_uuid=v['gpu_uuid'],pci_bus_id=v['gpu_pci_bus_id']))
    return args,state,events


@pytest.mark.parametrize('batch,pass_id',[(1,'pass0'),(1,'pass1'),(4,'pass0'),(4,'pass1')])
def test_actual_producer_reads_all_samples_once_per_token_and_executes_three_warmups(tmp_path,monkeypatch,batch,pass_id):
    from exposedpath import gate8_diagnostic as entry
    args,state,events=source(tmp_path,monkeypatch,batch,pass_id)
    report=entry.run_diagnostic(**args)
    assert json.loads(report.read_text())['status']=='DIAGNOSTIC_COMPLETE'
    root=report.parent; ledger=json.loads((root/'producer/pass_identity.json').read_text())
    assert len(ledger['requests'])==4 and ledger['pass_id']==pass_id
    assert [r['identity']['request_id'] for r in ledger['requests']]==['warmup-0','warmup-1','warmup-2','request-0']
    assert all(r['actual_output_tokens'] is None and r['early_eos'] is None for r in ledger['requests'][:-1])
    assert state['syncs']==7 and state['loads']==1  # warmup before/after x3 + one predrain
    assert events==['host_read','host_read']  # persistence must not add tensor reads
    tokens=json.loads((root/'batch_tokens.json').read_text())
    assert tokens['requests'][0]['token_ids']==[[13]*batch,[14]*batch]
    assert tokens['requests'][0]['actual_input_shape']==[batch,512]
    assert tokens['requests'][0]['sample_indices']==list(range(batch))


@pytest.mark.parametrize('damage',['eos','short'])
def test_one_sample_eos_or_missing_value_cannot_be_a_complete_batch(tmp_path,monkeypatch,damage):
    from exposedpath import gate8_diagnostic as entry
    args,_,_=source(tmp_path,monkeypatch,eos=damage=='eos',short=damage=='short')
    report=entry.run_diagnostic(**args)
    assert json.loads(report.read_text())['status']=='DIAGNOSTIC_INCOMPLETE'


def test_old_engineering_and_formal_roles_do_not_inherit_batch_permission():
    from exposedpath.gate8_engineering_contract import validate_declaration,declaration
    v=api().minimal_fields(binding());v['data_role']='Formal'
    with pytest.raises(ValueError): validate_declaration(v)
    v=dict(run_role='ENGINEERING',data_role='Engineering',batch_size=4,execution_mode='eager',
        engineering_scope=declaration('sdpa'),attention_backend='sdpa')
    with pytest.raises(ValueError): validate_declaration(v)


@pytest.mark.parametrize('damage',[None,'token','role','warmup','report_version'])
def test_real_batch_producer_to_pair_consumer(tmp_path,monkeypatch,damage):
    import sys,sysconfig
    from exposedpath import gate8_diagnostic as entry,gate8_isolated_preflight as isolated
    from exposedpath_v141 import gate8_target_python as target
    from scripts.gate8_pair import summarize
    api()  # Capture real JSON helpers before explicit OS receipt doubles.
    contract=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    runtime=dict(pid=os.getpid(),parent_pid=os.getppid(),snapshot=contract['actual']['snapshot'])
    monkeypatch.setattr(target,'current',lambda _:runtime)
    monkeypatch.setattr(isolated,'consume',lambda **kw:dict(target_pid=os.getpid()))
    monkeypatch.setattr(isolated,'read',lambda _: {})
    monkeypatch.setattr(isolated,'verify_snapshot',lambda *a:None)
    monkeypatch.setattr(entry,'verify_model_inventory',lambda *a,**kw:{})
    shared_model=tmp_path/'shared-model';shared_model.mkdir()
    write_json(shared_model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    roots=[]
    for p in ('pass0','pass1'):
        directory=tmp_path/p;directory.mkdir()
        args,_,_=source(directory,monkeypatch,pass_id=p)
        m=json.loads(args['manifest_path'].read_text());m.update(target_python=contract,model_id=str(shared_model),
            model_content_snapshot={'inventory_sha256':'0'*64},isolated_preflight_version=isolated.VERSION)
        write_json(args['manifest_path'],m)
        args.update(auxiliary_receipt=directory/'aux.json',auxiliary_sha256='0'*64,launch_nonce=p)
        root=entry.run_diagnostic(**args).parent;output=root.parent
        (output/'diagnostic-entry').mkdir()
        write_json(output/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=0,pid=os.getpid()))
        # Explicit synthetic OS receipts; actual runner files remain unmodified.
        write_json(output/'auxiliary_preflight.json',dict(run_id=m['run_id'],nonce=p,
            input_hashes={'manifest.json':sha(root/'manifest.json'),'prompt.json':sha(root/'prompt.json')}))
        claim=dict(target_pid=os.getpid(),nonce=p,preflight_sha256=sha(output/'auxiliary_preflight.json'))
        write_json(output/'auxiliary_preflight.claim.json',claim);write_json(root/'isolated_preflight_target.json',claim)
        write_json(output/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=sha(output/'auxiliary_preflight.json'),
            target_claim_sha256=sha(output/'auxiliary_preflight.claim.json')))
        write_json(output/('baseline_report.json' if p=='pass0' else 'collection_report.json'),
            dict(status='BASELINE_COMPLETE_NOT_ACCEPTANCE') if p=='pass0' else
            dict(collection={'status':'COMPLETE'},export_status='PASS',error=None))
        roots.append(output)
    root=roots[1]/'diagnostic'
    if damage=='token':
        path=root/'batch_tokens.json';value=json.loads(path.read_text());value['requests'][0]['token_ids'][1][-1]=15
        write_json(path,value);e=json.loads((root/'engineering_execution.json').read_text());e['batch_tokens_sha256']=sha(path)
        write_json(root/'engineering_execution.json',e);r=json.loads((root/'diagnostic_report.json').read_text());r['batch_tokens_sha256']=sha(path)
        write_json(root/'diagnostic_report.json',r)
    if damage=='report_version':
        path=root/'diagnostic_report.json';value=json.loads(path.read_text())
        value['schema_version']='batch-load-diagnostic/999.0.0';write_json(path,value)
    if damage in ('role','warmup'):
        path=root/'manifest.json';m=json.loads(path.read_text());m['data_role' if damage=='role' else 'warmup_count']='Formal' if damage=='role' else 1
        write_json(path,m)
    if damage:
        with pytest.raises(ValueError):summarize(*roots)
    else:
        result=summarize(*roots)
        assert result['batch_token_parity']==dict(status='PER_SAMPLE_VALUES_EQUAL',batch_size=4,token_ids=[[13]*4,[14]*4])
        assert result['statistical_stability']=='NOT_ASSESSED'


def test_failed_batch_stops_before_next_condition(tmp_path):
    m=api();calls=[]
    def collect(b,path):
        calls.append(b['run_id'])
        raise ValueError('observed hard failure')
    result=m.run_batch('batch-check',tmp_path/'batch',collect)
    assert calls==['batch-check-B1-pass0']
    assert result['status']=='BLOCKED' and [r['status'] for r in result['runs']]==['BLOCKED','NOT_RUN','NOT_RUN','NOT_RUN']


@pytest.mark.parametrize('damage',[None,'correlation','warning','drain','thread','unknown_api','dependency','stream'])
def test_batch_real_file_chain_uses_existing_s_a_and_rejects_conflicting_evidence(tmp_path,monkeypatch,damage):
    from test_n1_model_domain import source as raw_source
    from exposedpath_v141.gate8_files import load_input_receipt
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    receipt,execution,_=raw_source(tmp_path,monkeypatch,batch_binding=binding(),damage=damage)
    value,paths=load_input_receipt(receipt)
    assert value['schema_version']=='exposedpath-batch-load-input-receipt/0.1.0'
    assert paths['batch_tokens'].name=='batch_tokens.json'
    if damage=='warning':
        with pytest.raises(ValueError,match='DIAGNOSTIC_IMPACT_UNBOUNDED'):
            process_domain(receipt,execution,tmp_path/'derived')
        assert not (tmp_path/'derived/domain.json').exists()
        return
    result=process_domain(receipt,execution,tmp_path/'derived')
    output=load_domain(result,receipt,execution)
    if damage:
        assert output['status']=='BLOCKED' and not output['requests'][0]['a_records']
        return
    assert output['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
    records=output['requests'][0]['a_records']
    assert len(records)==3
    for a in records:
        n=2 if a['phase']=='full_request' else 1
        # Two 10ns launches plus one 10ns D2H API and one 10ns sync per token.
        assert a['A_cuda_api_ns']==30*n and a['A_sync_residual_ns']==10*n
        assert a['A_device_wait_ns']==0 and a['A_unattributed_ns']==0
        assert a['A_host_path_ns']==a['T_window_ns']-40*n
    assert output['dropped_records_status']=='UNKNOWN' and not output['formal_eligible']


@pytest.mark.parametrize('batch,pass_id',[(1,'pass0'),(1,'pass1'),(4,'pass0'),(4,'pass1')])
def test_prepare_finalizes_real_prompt_hash_and_closed_batch_manifest(tmp_path,monkeypatch,batch,pass_id):
    import csv,sys,sysconfig
    from exposedpath import platform_adapter,gate8_diagnostic as entry
    from exposedpath_v141 import gate8_source_probe
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3');monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(platform_adapter,'git',lambda argv,**kw:'' if 'status' in argv else 'd'*40)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'555.99')
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')))
    model=tmp_path/'model';model.mkdir()
    config=write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    inventory=tmp_path/'model.csv'
    with inventory.open('w',newline='') as h:
        w=csv.DictWriter(h,fieldnames=['RelativePath','Bytes','SHA256']);w.writeheader()
        w.writerow(dict(RelativePath='config.json',Bytes=config.stat().st_size,SHA256=sha(config)))
    prompt=write_json(tmp_path/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',
        tokenizer_id='synthetic',fixed_input_tokens=512,samples=[dict(sample_index=i,
            input_ids=[7]*512,attention_mask=[1]*512) for i in range(batch)]))
    out=entry.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,
        inventory_path=inventory,inventory_sha256=sha(inventory),prompt_path=prompt,prompt_sha256=sha(prompt),
        expected_commit='d'*40,physical_gpu=3,engineering_attention_backend='sdpa',
        target_python=sys._base_executable,site_root=sysconfig.get_path('purelib'),batch_binding=binding(batch,pass_id))
    manifest=json.loads((out/'manifest.json').read_text())
    assert manifest['run_id']==f'batch-check-B{batch}-{pass_id}'
    assert manifest['prompt_tokens_sha256']==sha(out/'prompt.json')
    assert manifest['batch_size']==batch and manifest['warmup_count']==3
    assert manifest['run_role']=='ENGINEERING' and manifest['study_mode']=='G1_NATURAL'
    assert entry.measurement_pass(manifest)==pass_id


@pytest.mark.parametrize('damage',[None,'values','samples','source','missing','warmup'])
def test_real_producer_token_file_consumer_rejects_rebound_or_incomplete_batch(tmp_path,monkeypatch,damage):
    from exposedpath import gate8_diagnostic as entry
    args,_,_=source(tmp_path,monkeypatch)
    root=entry.run_diagnostic(**args).parent
    read=lambda p:json.loads(p.read_text())
    manifest=read(root/'manifest.json');ledger=read(root/'producer/pass_identity.json')
    execution=read(root/'engineering_execution.json');path=root/'batch_tokens.json'
    if damage=='missing':path.unlink()
    elif damage=='warmup':ledger['requests'][0]['actual_output_tokens']=2
    elif damage:
        v=read(path)
        if damage=='values':v['requests'][0]['token_ids'][1][-1]=None
        if damage=='samples':v['requests'][0]['sample_indices']=[0,1,1,3]
        if damage=='source':v['manifest_sha256']='0'*64
        write_json(path,v);execution['batch_tokens_sha256']=sha(path)
    if damage:
        with pytest.raises((ValueError,FileNotFoundError)):
            api().validate_tokens(path,manifest,ledger,execution,root/'manifest.json',root/'producer/producer_receipt.json')
    else:
        assert api().validate_tokens(path,manifest,ledger,execution,root/'manifest.json',root/'producer/producer_receipt.json')==[[13]*4,[14]*4]


@pytest.mark.parametrize('damage',[None,'input','role','batch'])
def test_real_seal_to_profile_boundary_is_cpu_only_and_closed(tmp_path,monkeypatch,damage):
    import sys,subprocess
    from test_n1_preprofile_identity import prepared_case
    from exposedpath import gate8_isolated_preflight as isolated
    from scripts import gate8_diagnostic_collect as collector
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    m.pop('n1_model');m.pop('n1_model_execution');m.update(api().minimal_fields(binding()))
    model=tmp_path/'model';model.mkdir()
    write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    m['model_id']=str(model)
    write_json(prepared/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',
        tokenizer_id='synthetic',fixed_input_tokens=512,samples=[dict(sample_index=i,
            input_ids=[7]*512,attention_mask=[1]*512) for i in range(4)]))
    m['prompt_tokens_sha256']=sha(prepared/'prompt.json')
    if damage=='input':m['prompt_tokens_sha256']='0'*64
    if damage=='role':m['data_role']='Pilot'
    if damage=='batch':m['batch_size']=1
    write_json(prepared/'manifest.json',m)
    nsys=tmp_path/'nsys.exe';nsys.touch();out=tmp_path/'collection'
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(out),'--execute-engineering-diagnostic','--engineering-a-only'])
    monkeypatch.setattr(collector.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    calls=[]
    def stop(argv,*a,**kw):
        calls.append(argv)
        assert 'model-run' in argv and argv[1]=='profile'
        sealed=isolated.read(out/'auxiliary_preflight.json')
        claim=isolated.consume(receipt=out/'auxiliary_preflight.json',expected_sha=sha(out/'auxiliary_preflight.json'),
            nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']=='batch-check-B4-pass1'
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_PROFILE')
    monkeypatch.setattr(collector,'run_once',stop)
    if damage:
        with pytest.raises(ValueError):collector.main()
        assert not calls
    else:
        assert collector.main()==1 and len(calls)==1
