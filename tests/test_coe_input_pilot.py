"""Finite input-axis Pilot; all device/process execution below is a CPU double."""
from copy import deepcopy
import importlib
import importlib.util
import json
from pathlib import Path

import pytest


def api():
    assert importlib.util.find_spec('exposedpath.coe_input_pilot'), 'missing finite input Pilot'
    from exposedpath import coe_pilot  # real file helpers, before OS/device doubles
    return importlib.import_module('exposedpath.coe_input_pilot')


def binding(length=2048):
    return next(b for b in api().schedule('cpu-input', 'a'*40) if b['input_tokens']==length)


def test_schedule_and_input_identity_do_not_expand_legacy_domains(tmp_path):
    m=api()
    assert [b['input_tokens'] for b in m.schedule('cpu-input','a'*40)]==[512,2048,2048,512,2048,512,512,2048]
    seed=dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='cpu',fixed_input_tokens=512,
        samples=[dict(sample_index=0,input_ids=list(range(3,35))*16,attention_mask=[1]*512)])
    from test_gate8_identity import write_json,sha
    p=write_json(tmp_path/'seed.json',seed)
    paths=m.make_inputs(p,sha(p),tmp_path/'inputs')
    v=json.loads(paths[2048].read_text())
    i=m.validate_input(v,dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096),1)
    assert i['shape']==[1,2048] and v['samples'][0]['input_ids']==list(range(3,35))*64
    from exposedpath import coe_pilot,observation_preparation as old
    with pytest.raises(ValueError):old.validate_input(v,{},2048)
    with pytest.raises(ValueError):coe_pilot.validate_binding({**binding(),'version':coe_pilot.VERSION})


@pytest.mark.parametrize('change',[('version','future'),('variant','O'),('batch_size',2),('input_tokens',1024),
    ('pass_id','pass0'),('warmup_count',1),('position',3),('formal_eligible',True)])
def test_finite_binding_cannot_be_relabelled(change):
    m=api();b=binding();b[change[0]]=change[1]
    with pytest.raises(ValueError,match='COE_INPUT_'):m.validate_binding(b)


def row(b,q,g):
    return dict(binding=b,status='COMPLETE',result=dict(status=api().STATUS,binding=b,token_ids=[[17],[18]],
        operations=[dict(token_index=i,phase=p,candidate_ns=q+i,positions=dict(H_ns=3,D_ns=7))
            for i,p in enumerate(('prefill','decode'))],
        windows=[dict(phase=p,baseline=dict(gpu_activity=dict(status='KNOWN',union_ns=g))) for p in ('prefill','decode')]))


def test_signed_residual_uses_phase_not_cumulative_members_and_zero_is_undefined():
    m=api();b=m.schedule('cpu-input','a'*40)[:2]
    # Hand calculation: 12 - 10*(30/20) = -3; negative is retained.
    rows=[row(b[0],10,20),row(b[1],12,30)]
    r=m.block_contrasts(rows)['per_token'][0]
    assert r['delta_coe_ns']==2 and r['R_ns']==-3 and r['R_exact']==dict(numerator=-3,denominator=1)
    rows[0]['result']['windows'][0]['baseline']['gpu_activity']['union_ns']=0
    r=m.block_contrasts(rows)['per_token'][0]
    assert r['R_ns'] is None and r['R_status']=='UNDEFINED_INVALID_PHASE_GPU_DENOMINATOR'
    assert m.block_contrasts(rows)['per_token'][1]['R_ns']==-3.5


def test_whole_block_failure_stops_without_replacement(tmp_path):
    m=api();seen=[]
    def collect(b,out):
        seen.append(b)
        if len(seen)==4:raise ValueError('MISSING_DEPENDENCY')
        return row(b,10,20)['result']
    r=m.run_batch('cpu-input','a'*40,tmp_path/'batch',collect)
    assert len(seen)==4 and r['status']=='BLOCKED'
    assert [s['status'] for s in r['runs']]==['COMPLETE']*3+['BLOCKED']+['NOT_RUN']*4
    assert [s['block'] for s in r['blocks']]==[1] and r['incomplete_blocks']==[2,3,4]


def test_fixed_budget_complete_preserves_zero_and_negative_values(tmp_path):
    m=api();seen=[]
    def collect(b,out):
        seen.append((b['block'],b['input_tokens']))
        return row(b,0 if b['input_tokens']==2048 else 10,20)['result']
    r=m.run_batch('cpu-input','a'*40,tmp_path/'batch',collect)
    assert seen==[(1,512),(1,2048),(2,2048),(2,512),(3,2048),(3,512),(4,512),(4,2048)]
    assert r['status']=='FIXED_EIGHT_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW' and r['incomplete_blocks']==[]
    assert len(r['runs'])==8 and len(r['blocks'])==4
    assert all(b['per_token'][0]['delta_coe_ns']==-10 and b['per_token'][0]['R_ns']==-10 for b in r['blocks'])


@pytest.mark.parametrize('role,data',[('ENGINEERING','Engineering'),('FORMAL','Formal')])
def test_role_relabel_is_not_new_pilot_evidence(role,data):
    m=api();b=binding();mf=m.minimal_fields(b)
    prompt=dict(fixed_input_tokens=2048,samples=[dict(sample_index=0,input_ids=[7]*2048,attention_mask=[1]*2048)])
    mf.update(runner_git_commit='a'*40,runner_git_dirty=False,coe_input=m.input_identity(prompt))
    assert m.validate(mf)==b
    mf.update(run_role=role,data_role=data)
    with pytest.raises(ValueError,match='COE_INPUT_DECLARATION'):m.validate(mf)


def test_execution_rejects_changed_input_before_device_prepare(tmp_path,monkeypatch):
    from scripts.observation_preparation_batch import run
    from exposedpath import platform_adapter,gate8_diagnostic
    from test_gate8_identity import write_json,sha
    m=api();seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,schema_version='exposedpath-prompt-tokens/1',
        tokenizer_id='cpu',samples=[dict(sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    nsys=tmp_path/'not-a-collector';nsys.write_bytes(b'CPU_ONLY')
    monkeypatch.setattr(platform_adapter,'git',lambda argv:'' if 'status' in argv else 'a'*40)
    def forbidden(*a,**kw):pytest.fail('must reject input before any device prepare')
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',forbidden)
    c=dict(schema_version='coe-input-pilot-delivery/0.1',commit='a'*40,analysis_commit='a'*40,
        batch_id='cpu-input',
        model=str(tmp_path/'model'),inventory=str(tmp_path/'inventory'),inventory_sha256='a'*64,
        target_python='cpu-python',site_root='cpu-site',
        model_process_budget=8,profile_budget=8,seed_input=str(seed),prompt_512_sha256=sha(seed),nsys=str(nsys),nsys_sha256=sha(nsys),
        input_bindings={'512':dict(file_sha256='0'*64,identity={}),'2048':dict(file_sha256='0'*64,identity={})})
    with pytest.raises(ValueError,match='COE_INPUT_EXECUTION_INPUT_BINDING'):run(c,tmp_path/'out',execute=True,input_pilot=True)


@pytest.mark.parametrize('length',[512,2048])
@pytest.mark.parametrize('damage',[None,'drain','dependency','future_gap','token'])
def test_real_producer_canonical_both_tokens_and_budget(tmp_path,monkeypatch,length,damage):
    m=api()
    from test_n1_model_domain import source
    from exposedpath_v141.gate8_files import load_input_receipt
    from analysis.observation_preparation import process
    from test_gate8_identity import write_json
    receipt,execution,_=source(tmp_path,monkeypatch,pilot_binding=binding(length),damage=damage)
    _,paths=load_input_receipt(receipt)
    if damage=='token':
        t=json.loads(paths['pilot_tokens'].read_text());t['requests'][0]['token_ids'][0][0]=-1
        write_json(paths['pilot_tokens'],t)
    if damage:
        reason={'drain':'DRAIN','dependency':'API_SEMANTICS_UNBOUNDED:cudaStreamWaitEvent',
            'future_gap':'STAGE|SUBMIT|SEMANTICS','token':'ARTIFACT_HASH_MISMATCH'}[damage]
        with pytest.raises(ValueError,match=reason):process(receipt,execution,tmp_path/'analyzed')
        assert not (tmp_path/'analyzed/sensitivity.json').exists()
    else:
        r=json.loads(process(receipt,execution,tmp_path/'analyzed').read_text())
        assert r['binding']==binding(length) and r['status']==m.STATUS
        assert r['token_ids']==[[17],[18]] and [o['candidate_ns'] for o in r['operations']]==[2,2]
        assert [o['original_sync_ns'] for o in r['operations']]==[0,0]
        assert json.loads(execution.read_text())['observation_preparation']['consumed_token_indices']==[0,1]
        budget=json.loads((tmp_path/'analyzed/candidate_budget_preview.json').read_text())
        assert len(budget['windows'])==3
        assert not list((tmp_path/'analyzed').rglob('domain.json'))


@pytest.mark.parametrize('length',[512,2048])
def test_actual_prepare_seal_and_profile_argv(tmp_path,monkeypatch,length):
    import csv,subprocess,sys,sysconfig
    from types import SimpleNamespace
    from exposedpath import gate8_diagnostic as entry,platform_adapter,gate8_isolated_preflight as isolated
    from exposedpath_v141 import gate8_source_probe
    from scripts import gate8_diagnostic_collect as collector
    from test_gate8_identity import write_json,sha
    b=binding(length);m=api()
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3');monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(platform_adapter,'git',lambda args,**kw:'' if 'status' in args else 'a'*40)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'3, GPU-12345678-1234-1234-1234-123456789abc, 00000000:01:00.0')
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')))
    model=tmp_path/'model';model.mkdir();write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    inventory=tmp_path/'inventory.csv'
    with inventory.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['RelativePath','Bytes','SHA256']);w.writeheader()
        w.writerow(dict(RelativePath='config.json',Bytes=(model/'config.json').stat().st_size,SHA256=sha(model/'config.json')))
    prompt=write_json(tmp_path/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='cpu',fixed_input_tokens=length,
        samples=[dict(sample_index=0,input_ids=[7]*length,attention_mask=[1]*length)]))
    prepared=entry.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,inventory_path=inventory,
        inventory_sha256=sha(inventory),prompt_path=prompt,prompt_sha256=sha(prompt),expected_commit='a'*40,
        physical_gpu=3,engineering_attention_backend='sdpa',target_python=sys._base_executable,
        site_root=sysconfig.get_path('purelib'),pilot_binding=b)
    mf=isolated.read(prepared/'manifest.json');assert m.validate(mf)==b
    assert mf['coe_input']['shape']==[1,length] and mf['run_role']=='PILOT'
    root=tmp_path/'repo';(root/'.git').mkdir(parents=True);(root/'.git/HEAD').write_text('a'*40)
    files=('exposedpath/runner.py','exposedpath/observation_preparation.py','exposedpath/coe_input_pilot.py')
    real=Path(__file__).resolve().parents[1]
    for p in files:
        target=root/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((real/p).read_bytes())
    monkeypatch.setattr(platform_adapter,'run_tool',lambda tool,args,**kw:subprocess.CompletedProcess(args,0,
        ('\0'.join(files)+'\0').encode() if '--cached' in args else b'',b''))
    out=tmp_path/'collection';nsys=tmp_path/'nsys.exe';nsys.touch();calls=[]
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(out),'--execute-engineering-diagnostic','--engineering-a-only','--pilot'])
    monkeypatch.setattr(collector.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    def boundary(argv,*a,**kw):
        calls.append(argv);assert argv[1]=='profile' and 'model-run' in argv
        sealed=isolated.read(out/'auxiliary_preflight.json')
        claim=isolated.consume(receipt=out/'auxiliary_preflight.json',expected_sha=sha(out/'auxiliary_preflight.json'),
            nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==b['run_id']
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_CUDA')
    monkeypatch.setattr(collector,'run_once',boundary)
    assert collector.main()==1 and len(calls)==1


def test_input_batch_default_cannot_collect(tmp_path):
    from scripts.observation_preparation_batch import run
    with pytest.raises(ValueError,match='OPT_IN_REQUIRED'):run({},tmp_path/'out')


@pytest.mark.parametrize('damage',[None,'hash','version','identity','exit','budget'])
def test_real_collection_consumer_checks_both_tokens_and_preview(tmp_path,monkeypatch,damage):
    from analysis.observation_preparation import process  # real JSON helpers before OS doubles
    from test_n1_model_domain import source
    from scripts.observation_preparation_batch import consume_collection
    from scripts.gate8_diagnostic_collect import analyze_receipt
    from exposedpath_v141.gate8_files import load_input_receipt
    from test_gate8_identity import write_json,sha
    m=api();b=binding();receipt,execution,_=source(tmp_path,monkeypatch,pilot_binding=b)
    target_receipt=tmp_path/'input_receipt.json';target_receipt.write_bytes(receipt.read_bytes())
    _,paths=load_input_receipt(target_receipt);mf=json.loads(paths['wmpc_manifest'].read_text());ledger=json.loads(paths['pass_identity'].read_text())
    result,value=analyze_receipt(mf,target_receipt,execution,tmp_path/'analyzed')
    write_json(tmp_path/'target_launch.json',dict(role='CPU_EXTERNAL_LAUNCH_DOUBLE'))
    d=tmp_path/'diagnostic-entry';d.mkdir(exist_ok=True);write_json(d/'exit.json',dict(status='EXITED',exit_code=0,pid=ledger['pid']))
    report=dict(schema_version='coe-input-pilot-collection/0.1.0',status=m.STATUS,qualification='NOT_QUALIFIED',scientific_outputs_allowed=False,
        export_status='PASS',result_filename='sensitivity.json',pilot=b,run_role='PILOT',data_role='Pilot',q0_status='NOT_RUN',
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',collection=dict(status='COMPLETE',exit_code=0,timed_out=False),
        result_sha256=sha(result),manifest_sha256=sha(paths['wmpc_manifest']),target_runtime_sha256=sha(tmp_path/'diagnostic/target_runtime.json'),
        target_launch_sha256=sha(tmp_path/'target_launch.json'))
    if damage=='hash':report['result_sha256']='0'*64
    if damage=='version':report['schema_version']='future'
    if damage=='identity':report['pilot']={**b,'run_id':'wrong'}
    if damage=='exit':write_json(d/'exit.json',dict(status='EXITED',exit_code=3,pid=ledger['pid']))
    if damage=='budget':(tmp_path/'analyzed/candidate_budget_preview.json').write_text('{}')
    write_json(tmp_path/'collection_report.json',report)
    if damage:
        reason={'hash':'COLLECTION_HASH','version':'COLLECTION_CONTRACT','identity':'COLLECTION_CONTRACT',
            'exit':'TARGET_EXIT','budget':'BUDGET_PREVIEW_BINDING'}[damage]
        with pytest.raises(ValueError,match=reason):consume_collection(tmp_path,b,'a'*40)
    else:
        r=consume_collection(tmp_path,b,'a'*40)
        assert r['token_ids']==[[17],[18]] and r['candidate_budget_preview_sha256']==sha(tmp_path/'analyzed/candidate_budget_preview.json')
