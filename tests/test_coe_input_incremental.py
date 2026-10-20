"""Finite incremental inputs; OS/device/profile boundaries are CPU doubles."""
from copy import deepcopy
import json
import pytest
from exposedpath import coe_input_pilot as m
from tests.test_coe_input_low3 import row

VERSION='COE-INPUT-P-INCREMENTAL-PILOT/0.1'


def binding(length=768):
    return next(b for b in m.schedule('cpu-increment','a'*40,version=VERSION) if b['input_tokens']==length)


def test_new_slots_are_separate_from_old_low3_and_blocked_four_point():
    bs=m.schedule('cpu-increment','a'*40,version=VERSION)
    assert [b['input_tokens'] for b in bs]==[512,768,1536,768,1536,512,1536,512,768]
    assert len({b['run_id'] for b in bs})==9
    assert all(b['observation_variant']=='P' and b['variant'] is None and b['pass_id']=='pass1' for b in bs)
    for version in (m.VERSION,m.MIDPOINT_VERSION,m.EXTENDED_VERSION,m.LOW_SIDE_VERSION):
        with pytest.raises(ValueError,match='BINDING'):m.validate_binding({**binding(),'version':version})
    assert [b['input_tokens'] for b in m.schedule('old','a'*40,version=m.LOW_SIDE_VERSION)][:3]==[256,512,2048]


@pytest.mark.parametrize('n,ids_hash,mask_hash,batch_hash',[
    (768,'dea12a2fdeaa8e048c3f620b537a0f2b22defb1fad97ea69c2b19e87f7bc10f6',
     '1154fee84a23a98f245029319337f48da8c892f5ee1a496fb7d5bcab505962b5','e75f39e6440a536f48789ca0eeaddbe111c9a624ad515b0d06188208e266db9c'),
    (1536,'f07475de66a8b62d5bd51d44d372756e6c7728d9db31a41fd2f26352a2dd0e26',
     '355db3924c705f994f57825b280478434cbc7dfc46b4b57eb602bdadab55de9b','8da2e31db030756c61a4d425aafda42c14a72a0d676e897b717d067f3408b80f')])
def test_full_finite_input_and_mask_not_old_identity(tmp_path,n,ids_hash,mask_hash,batch_hash):
    from tests.test_gate8_identity import write_json,sha
    seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,samples=[dict(
        sample_index=0,input_ids=list(range(3,35))*16,attention_mask=[1]*512)]))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'inputs',version=VERSION)
    assert set(paths)=={512,768,1536}
    p=json.loads(paths[n].read_text());config=dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096)
    assert p['samples'][0]['input_ids']==list(range(3,35))*(n//32)
    assert m.validate_input(p,config,1,version=VERSION)==dict(schema_version='coe-input-incremental-identity/0.1.0',
        shape=[1,n],sample_indices=[0],input_ids_sha256=ids_hash,attention_mask_sha256=mask_hash,
        batch_sha256=batch_hash,algorithm='SHA256_COMPACT_UTF8_JSON_IN_ORDER')
    with pytest.raises(ValueError,match='INPUT_SHAPE'):m.input_identity(p,version=m.LOW_SIDE_VERSION)
    with pytest.raises(ValueError,match='MODEL_CONFIG'):m.validate_input(p,{**config,'max_position_embeddings':n+1},1,version=VERSION)
    p['samples'][0]['attention_mask'][-1]=0
    with pytest.raises(ValueError,match='MASK'):m.input_identity(p,version=VERSION)


def test_adjacent_primary_and_endpoint_descriptive_signed_R_no_old_2048():
    rows=[row(binding(n),q,g) for n,q,g in [(512,2,4),(768,10,20),(1536,12,30)]]
    r=m.block_contrasts(rows)['per_token'][0]
    # 512->768: 10-2*20/4=0. 768->1536: 12-10*30/20=-3.
    assert [(c['lower_input'],c['higher_input'],c['delta_coe_ns'],c['R_ns']) for c in r['primary_contrasts']]==[
        (512,768,8,0),(768,1536,2,-3)]
    assert r['descriptive_endpoint']['R_ns']==-3 and r['descriptive_endpoint']['delta_coe_ns']==10
    assert r['descriptive_endpoint']['primary'] is False
    assert r['primary_contrasts'][0]['primary'] is True
    assert set(r['raw_by_input'])=={512,768,1536}
    assert r['raw_by_input'][768]['candidate_completion_budget_over_phase']==.06
    rows[1]['result']['windows'][0]['baseline']['gpu_activity']['union_ns']=0
    r=m.block_contrasts(rows)['per_token'][0]
    assert r['primary_contrasts'][1]['R_ns'] is None
    assert r['primary_contrasts'][0]['R_ns']==10  # zero numerator GPU is valid, no epsilon
    assert r['descriptive_endpoint']['R_ns']==-3
    assert m.block_contrasts(rows)['per_token'][1]['primary_contrasts'][1]['R_ns']==-3.5
    with pytest.raises(ValueError,match='INCOMPLETE_BLOCK'):m.block_contrasts(rows[:2])
    wrong=deepcopy(rows);wrong[0]['binding']['batch_id']='historical'
    with pytest.raises(ValueError,match='BINDING'):m.block_contrasts(wrong)


@pytest.mark.parametrize('failure',[None,'dependency','token'])
def test_fixed_nine_or_first_hard_failure_keeps_unrun_slots(tmp_path,failure):
    seen=[]
    def collect(b,out):
        seen.append(b)
        if len(seen)==2 and failure=='dependency':raise ValueError('MISSING_DEPENDENCY')
        r=row(b,{512:10,768:0,1536:8}[b['input_tokens']],20)['result']
        if len(seen)==4 and failure=='token':r['token_ids']=[[99],[18]]
        return r
    r=m.run_batch('cpu-increment','a'*40,tmp_path/'out',collect,version=VERSION)
    if failure=='dependency':
        assert [s['status'] for s in r['runs']]==['COMPLETE','BLOCKED']+['NOT_RUN']*7 and r['blocks']==[]
    elif failure=='token':
        assert [s['status'] for s in r['runs']]==['COMPLETE']*3+['BLOCKED']+['NOT_RUN']*5
        assert r['incomplete_blocks']==[2,3] and len(r['blocks'])==1
    else:
        assert len(seen)==9 and len(r['blocks'])==3 and r['incomplete_blocks']==[]
        assert r['status']=='FIXED_NINE_INCREMENTAL_PILOT_COMPLETE_STOP_FOR_REVIEW'
        assert all(b['per_token'][0]['primary_contrasts'][0]['delta_coe_ns']==-10 for b in r['blocks'])


@pytest.mark.parametrize('length',[512,768,1536])
def test_actual_prepare_seal_profile_argv(tmp_path,monkeypatch,length):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_actual_prepare_seal_and_profile_argv(tmp_path,monkeypatch,length)


@pytest.mark.parametrize('damage',[None,'hash','identity','budget','version','exit'])
def test_actual_producer_canonical_two_token_preview_consumer(tmp_path,monkeypatch,damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_real_collection_consumer_checks_both_tokens_and_preview(tmp_path,monkeypatch,damage)


@pytest.mark.parametrize('damage',['drain','dependency','future_gap','token'])
def test_new_role_still_rejects_unclosed_two_token_evidence(tmp_path,monkeypatch,damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_real_producer_canonical_both_tokens_and_budget(tmp_path,monkeypatch,768,damage)


def test_nine_real_file_chains_form_only_new_complete_blocks(tmp_path,monkeypatch):
    from tests import test_coe_input_pilot as old
    from scripts.observation_preparation_batch import consume_collection
    def collect(b,folder):
        folder.mkdir()
        with monkeypatch.context() as slot:
            slot.setattr(old,'binding',lambda *a:b)
            old.test_real_collection_consumer_checks_both_tokens_and_preview(folder,slot,None)
            return consume_collection(folder,b,'a'*40)
    r=m.run_batch('cpu-increment','a'*40,tmp_path/'batch',collect,version=VERSION)
    assert r['status']=='FIXED_NINE_INCREMENTAL_PILOT_COMPLETE_STOP_FOR_REVIEW',[(s['status'],s.get('error')) for s in r['runs']]
    assert len(r['blocks'])==3 and all(len(b['per_token'])==2 for b in r['blocks'])
    assert all(set(b['per_token'][0]['raw_by_input'])=={512,768,1536} for b in r['blocks'])


def test_bad_new_input_bytes_rejected_before_device_prepare(tmp_path,monkeypatch):
    from scripts.observation_preparation_batch import run
    from exposedpath import platform_adapter,gate8_diagnostic
    from tests.test_gate8_identity import write_json,sha
    seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,samples=[dict(
        sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'prospective',version=VERSION)
    inputs={str(n):dict(file_sha256=sha(p),identity=m.input_identity(json.loads(p.read_text()),version=VERSION)) for n,p in paths.items()}
    inputs['768']['file_sha256']='0'*64
    nsys=tmp_path/'not-nsys';nsys.write_bytes(b'CPU')
    monkeypatch.setattr(platform_adapter,'git',lambda argv:'' if 'status' in argv else 'a'*40)
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',lambda **kw:pytest.fail('must reject before GPU prepare'))
    c=dict(schema_version='coe-input-incremental-pilot-delivery/0.1',input_contract_version=VERSION,
        commit='a'*40,analysis_commit='a'*40,model_process_budget=9,profile_budget=9,batch_id='cpu-increment',
        seed_input=str(seed),prompt_512_sha256=sha(seed),input_bindings=inputs,nsys=str(nsys),nsys_sha256=sha(nsys))
    with pytest.raises(ValueError,match='COE_INPUT_EXECUTION_INPUT_BINDING:768'):run(c,tmp_path/'out',execute=True,input_pilot=True)


def test_new_schema_cannot_relabel_old_binding(tmp_path):
    from scripts.observation_preparation_batch import run
    c=dict(schema_version='coe-input-incremental-pilot-delivery/0.1',input_contract_version=m.LOW_SIDE_VERSION,
        commit='a'*40,analysis_commit='a'*40,model_process_budget=9,profile_budget=9)
    with pytest.raises(ValueError,match='DELIVERY_CONTRACT_VERSION'):run(c,tmp_path/'out',execute=True,input_pilot=True)
    assert not (tmp_path/'out').exists()


def test_real_isolated_new_contract_import_rejects_foreign_module(tmp_path):
    import os,subprocess,sys
    from pathlib import Path
    root=Path(__file__).resolve().parents[1]
    (tmp_path/'exposedpath').mkdir()
    (tmp_path/'exposedpath/__init__.py').write_text("raise RuntimeError('FOREIGN_MODULE')")
    code="""import pathlib,sys
root=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(root))
from exposedpath import coe_input_pilot as m
assert pathlib.Path(m.__file__).resolve()==root/'exposedpath/coe_input_pilot.py'
assert len(m.schedule('isolated','a'*40,version='COE-INPUT-P-INCREMENTAL-PILOT/0.1'))==9
"""
    r=subprocess.run([sys.executable,'-I','-S','-B','-c',code,str(root)],cwd=tmp_path,
        env={**os.environ,'PYTHONPATH':str(tmp_path)},capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr
