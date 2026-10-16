"""Prospective COE Pilot wiring. CPU evidence, never target CUDA qualification."""
import json
from copy import deepcopy
from pathlib import Path

import pytest

from test_gate8_identity import sha, write_json


def api():
    from exposedpath import coe_pilot
    return coe_pilot


def binding(batch=2):
    return next(b for b in api().schedule('cpu-coe','a'*40) if b['batch_size']==batch)


def prompt(batch=2):
    return dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='synthetic',
        fixed_input_tokens=512,samples=[dict(sample_index=i,input_ids=[7]*512,
        attention_mask=[1]*512) for i in range(batch)])


def test_schedule_is_nine_closed_slots_and_whole_batch_identity():
    m=api();rows=m.schedule('cpu-coe','a'*40)
    assert [r['batch_size'] for r in rows]==[1,2,4,2,4,1,4,1,2]
    assert len({r['run_id'] for r in rows})==9
    assert all(r['pass_id']=='pass1' and r['variant'] is None for r in rows)
    one=m.input_identity(prompt(1));two=m.input_identity(prompt(2))
    assert two['shape']==[2,512] and two['sample_indices']==[0,1]
    assert one['input_ids_sha256']!=two['input_ids_sha256']
    assert one['attention_mask_sha256']!=two['attention_mask_sha256']
    assert one['batch_sha256']!=two['batch_sha256']


@pytest.mark.parametrize('damage',['version','batch','pass','commit','role','warmup','order'])
def test_binding_is_not_a_generic_pilot_permission(damage):
    m=api();b=binding()
    k,v={'version':('version','future'),'batch':('batch_size',8),'pass':('pass_id','pass0'),
        'commit':('execution_commit','not-a-commit'),'role':('formal_eligible',True),
        'warmup':('warmup_count',1),'order':('position',9)}[damage]
    b[k]=v
    with pytest.raises(ValueError):m.validate_binding(b)


@pytest.mark.parametrize('batch',[1,2,4])
@pytest.mark.parametrize('constructed_mask_conflict',[False,True])
def test_real_producer_and_new_token_contract(tmp_path,monkeypatch,batch,constructed_mask_conflict):
    from test_batch_load_diagnostic import source
    from exposedpath import gate8_diagnostic as entry
    args,state,_=source(tmp_path,monkeypatch,batch=batch if batch!=2 else 4)
    mf=json.loads(args['manifest_path'].read_text())
    mf.pop('batch_load');mf.pop('engineering_pair');mf.pop('domain_qualification')
    mf.update(api().minimal_fields(binding(batch)))
    write_json(args['prompt_path'],prompt(batch))
    mf.update(prompt_tokens_sha256=sha(args['prompt_path']),coe_input=api().input_identity(prompt(batch)),
              runner_git_commit='a'*40,**api().SOFTWARE)
    monkeypatch.setattr(api(),'software_identity',lambda _:dict(api().SOFTWARE)) # runtime boundary only
    from exposedpath import gate8_isolated_preflight as isolated
    from exposedpath_v141 import gate8_target_python as target
    import os
    mf.update(target_python={},isolated_preflight_version=isolated.VERSION,
        model_content_snapshot={'inventory_sha256':'a'*64})
    monkeypatch.setattr(isolated,'consume',lambda **kw:dict(target_pid=os.getpid()))
    monkeypatch.setattr(isolated,'read',lambda _: {})
    monkeypatch.setattr(isolated,'verify_snapshot',lambda *a:None)
    monkeypatch.setattr(target,'current',lambda _:dict(pid=os.getpid()))
    monkeypatch.setattr(entry,'verify_model_inventory',lambda *a,**kw:{})
    from exposedpath import platform_adapter,runner
    monkeypatch.setattr(platform_adapter,'cuda_identity_native',lambda _:dict(gpu_uuid=mf['gpu_uuid'],pci_bus_id=mf['gpu_pci_bus_id']))
    from exposedpath_v141 import gate8_source_probe
    from types import SimpleNamespace
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(cuda=runner.torch.cuda))
    args.update(auxiliary_receipt=tmp_path/'aux.json',auxiliary_sha256='a'*64,launch_nonce='cpu')
    write_json(args['manifest_path'],mf)
    if batch==2:
        # Actual tensor and output dimensions, not just manifest assertions.
        from test_runner_token_ready import _FakeModel,_FakeToken
        from exposedpath import runner
        from types import SimpleNamespace
        def load(*a,**kw):
            state['loads']+=1;state['initialized']=True
            model=_FakeModel(iter([_FakeToken(x,[]) for x in [[13,13],[14,14]]*4]))
            model.dtype='torch.float16';model.training=False
            model.config=SimpleNamespace(_attn_implementation='sdpa',model_type='qwen2',use_cache=True)
            return model,SimpleNamespace(eos_token_id=2),100,'cuda:0'
        monkeypatch.setattr(runner,'load_model',load)
    if constructed_mask_conflict:
        original=runner.get_batch_inputs
        def changed(*a,**kw):
            value=deepcopy(original(*a,**kw));value['attention_mask'][-1][0]=0;return value
        monkeypatch.setattr(runner,'get_batch_inputs',changed)
        with pytest.raises(ValueError,match='MASK|INPUT'):entry.run_diagnostic(**args)
        assert state['loads']==0
        return
    path=entry.run_diagnostic(**args);root=path.parent
    manifest=json.loads((root/'manifest.json').read_text());ledger=json.loads((root/'producer/pass_identity.json').read_text())
    execution=json.loads((root/'engineering_execution.json').read_text())
    tokens=api().validate_tokens(root/'pilot_tokens.json',manifest,ledger,execution,
                                root/'manifest.json',root/'producer/producer_receipt.json')
    assert tokens==[[13]*batch,[14]*batch]
    assert len(ledger['requests'])==4 and all(r['actual_output_tokens'] is None for r in ledger['requests'][:3])
    assert ledger['schema_version']==api().PASS_VERSION
    assert json.loads((root/'producer/producer_receipt.json').read_text())['schema_version']==api().PRODUCER_VERSION
    assert json.loads((root/'pilot_tokens.json').read_text())['requests'][0]['actual_input_shape']==[batch,512]


@pytest.mark.parametrize('damage',[None,'identity','mask','token','drain','pair','dependency','future_gap','prefill_gap'])
def test_real_files_to_canonical_local_prefill_and_coe(tmp_path,monkeypatch,damage):
    from test_n1_model_domain import source
    from exposedpath_v141.gate8_files import load_input_receipt
    from analysis.coe_pilot import process
    # Preload real JSON helpers before explicit external OS doubles.
    api()
    receipt,execution,_=source(tmp_path,monkeypatch,pilot_binding=binding(),damage=damage)
    _,paths=load_input_receipt(receipt)
    if damage=='identity':
        v=json.loads(paths['wmpc_manifest'].read_text());v['pilot']['execution_commit']='b'*40
        write_json(paths['wmpc_manifest'],v)
    if damage=='mask':
        v=json.loads(paths['prompt'].read_text());v['samples'][1]['attention_mask'][0]=0
        write_json(paths['prompt'],v)
    if damage=='token':
        v=json.loads(paths['pilot_tokens'].read_text());v['requests'][0]['token_ids'][0][1]=None
        write_json(paths['pilot_tokens'],v)
    if damage in ('identity','mask','token','drain','pair','dependency','prefill_gap'):
        with pytest.raises(ValueError):process(receipt,execution,tmp_path/'result')
        assert not (tmp_path/'result/prefill.json').exists()
    else:
        path=process(receipt,execution,tmp_path/'result');r=json.loads(path.read_text())
        assert r['status']=='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW'
        # Independent fixture: model returns 10+forward-count. Three 2-step
        # warmups give measured tokens 17,18. D2H [copy.end,copy.end+2)
        # is inside I but before sync; both kernels precede copy entry.
        assert r['binding']==binding() and r['token_ids']==[[17,17],[18,18]]
        assert (r['coe']['candidate_ns'],r['coe']['original_sync_ns'])==(2,0)
        assert r['prefill']['A_unattributed_ns']==0
        assert r['request_status']=='NOT_ACCEPTED' and r['decode_status']=='NOT_ACCEPTED'
        assert not list((tmp_path/'result').rglob('domain.json'))
        if damage=='future_gap':assert r['decode_isolation']['post_completion_unresolved_api_ids']


def test_failure_stops_and_whole_blocks_keep_signed_differences(tmp_path):
    m=api();seen=[]
    def collect(b,out):
        seen.append(b)
        if len(seen)==5:raise ValueError('explicit local quality failure')
        q={1:10,2:5,4:3}[b['batch_size']]
        return dict(status='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW',binding=b,token_ids=[[13]*b['batch_size'],[14]*b['batch_size']],
            coe={'candidate_ns':q},result_sha256='f'*64)
    r=m.run_batch('cpu-coe','a'*40,tmp_path/'out',collect)
    assert r['status']=='BLOCKED' and len(seen)==5
    assert [s['status'] for s in r['runs']]==['COMPLETE']*4+['BLOCKED']+['NOT_RUN']*4
    assert r['blocks']==[dict(block=1,b4_minus_b1_candidate_ns=-7)]
    assert r['incomplete_blocks']==[2,3]


def test_wrong_tokens_never_complete_block(tmp_path):
    m=api()
    def collect(b,out):
        return dict(status='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW',binding=b,
            token_ids=[[13]*b['batch_size'],[14+b['position']]*b['batch_size']],coe={'candidate_ns':0},result_sha256='f'*64)
    r=m.run_batch('cpu-coe','a'*40,tmp_path/'out',collect)
    assert r['status']=='BLOCKED' and not r['blocks'] and r['runs'][2]['status']=='NOT_RUN'


def test_clones_are_only_accepted_in_the_new_closed_candidate_domain():
    from exposedpath.workload import get_batch_inputs
    for role in ('PILOT','FORMAL'):
        with pytest.raises(ValueError):get_batch_inputs(prompt(),2,run_role=role)
    assert get_batch_inputs(prompt(),2,run_role='PILOT',coe_binding=binding())['input_ids']==[[7]*512]*2
    with pytest.raises(ValueError):get_batch_inputs(prompt(),2,run_role='FORMAL',coe_binding=binding())


@pytest.mark.parametrize('damage',[None,'input','mask','role','commit','batch'])
def test_real_seal_and_explicit_collector_argv(tmp_path,monkeypatch,damage):
    import sys,subprocess
    from test_n1_preprofile_identity import prepared_case
    from exposedpath import gate8_isolated_preflight as isolated
    from scripts import gate8_diagnostic_collect as collector
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    for k in ('n1_model','n1_model_execution','domain_qualification'):m.pop(k)
    m.update(api().minimal_fields(binding()),coe_input=api().input_identity(prompt()))
    model=tmp_path/'model';model.mkdir();write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    m['model_id']=str(model);write_json(prepared/'prompt.json',prompt());m['prompt_tokens_sha256']=sha(prepared/'prompt.json')
    if damage=='input':m['prompt_tokens_sha256']='0'*64
    elif damage=='mask':m['coe_input']['attention_mask_sha256']='0'*64
    elif damage=='role':m['run_role']='ENGINEERING'
    elif damage=='commit':m['pilot']['execution_commit']='b'*40
    elif damage=='batch':m['batch_size']=1
    write_json(prepared/'manifest.json',m)
    nsys=tmp_path/'nsys.exe';nsys.touch();out=tmp_path/'collection';calls=[]
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(out),'--execute-engineering-diagnostic','--engineering-a-only','--pilot'])
    monkeypatch.setattr(collector.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    def before_profile(argv,*a,**kw):
        calls.append(argv)
        assert argv[1]=='profile' and 'model-run' in argv and '--auxiliary-receipt' in argv
        sealed=isolated.read(out/'auxiliary_preflight.json')
        claim=isolated.consume(receipt=out/'auxiliary_preflight.json',expected_sha=sha(out/'auxiliary_preflight.json'),
            nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==binding()['run_id']
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_CUDA')
    monkeypatch.setattr(collector,'run_once',before_profile)
    if damage:
        with pytest.raises(ValueError):collector.main()
        assert not calls
    else:assert collector.main()==1 and len(calls)==1


def test_default_batch_entry_never_prepares_or_profiles(tmp_path,monkeypatch):
    from scripts.coe_pilot_batch import run
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    with pytest.raises(ValueError,match='OPT_IN'):run({},tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_target_software_is_observed_not_filled_from_expected():
    from types import SimpleNamespace
    m=api()
    actual=m.software_identity(SimpleNamespace(__version__='wrong-torch',version=SimpleNamespace(cuda='12.4')))
    assert actual['inference_framework_version']=='torchwrong-torch'
    with pytest.raises(ValueError,match='SOFTWARE'):m.validate_software(actual,{})
