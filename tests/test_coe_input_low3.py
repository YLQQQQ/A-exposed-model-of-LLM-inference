"""Independent low-side Pilot; device/OS/collector boundaries are CPU doubles."""
from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import os
import pytest
from exposedpath import coe_input_pilot as m
from tests.test_coe_input_pilot import row as old_row

VERSION='COE-INPUT-P-LOW3-PILOT/0.1'

def row(b,q,g):
    r=old_row(b,q,g)
    for i,p in enumerate(('prefill','decode')):
        r['result']['operations'][i].update(copy_wall_ns=50,wall_ns=60,original_sync_ns=0,
            kernel_ns=q+i,memop_ns=0,same_operation_all_gpu_union_ns=q+i,uncovered_ns=60-q-i,
            members=['kernel-prefix','copy'],member_submits=[{'record':'kernel-prefix','submit':'api-1'},{'record':'copy','submit':'api-2'}])
        r['result']['windows'][i].update(projection=dict(start_ns=0,end_ns=100),a=dict(T_window_ns=100))
    # Independent synthetic preview: completion budget=6, not necessarily Q.
    r['result']['candidate_budget_windows']=[dict(phase=p,original_a=dict(T_window_ns=100),
        candidate_budgets_ns=dict(completion_exposure=6,host_path=50,submit=44)) for p in ('prefill','decode')]
    r['result']['candidate_member_positions']=[dict(token_index=i,position_union_ns=dict(before_copy=3,inside_operation=q+i)) for i in (0,1)]
    return r

def binding(length=256):
    return next(b for b in m.schedule('cpu-low3','a'*40,version=VERSION) if b['input_tokens']==length)

def test_independent_nine_slot_plan_does_not_unlock_four_point_contract():
    bs=m.schedule('cpu-low3','a'*40,version=VERSION)
    assert [b['input_tokens'] for b in bs]==[256,512,2048,512,2048,256,2048,256,512]
    assert len({b['run_id'] for b in bs})==9
    assert all(b['observation_variant']=='P' and b['variant'] is None and b['pass_id']=='pass1' for b in bs)
    assert len(m.schedule('old','a'*40,version=m.EXTENDED_VERSION))==16
    for version in (m.VERSION,m.MIDPOINT_VERSION,m.EXTENDED_VERSION):
        with pytest.raises(ValueError,match='BINDING'):m.validate_binding({**binding(),'version':version})

def test_256_full_input_identity_and_old_versions_stay_closed(tmp_path):
    from tests.test_gate8_identity import write_json,sha
    seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,samples=[dict(
        sample_index=0,input_ids=list(range(3,35))*16,attention_mask=[1]*512)]))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'inputs',version=VERSION)
    assert set(paths)=={256,512,2048}
    p=json.loads(paths[256].read_text());config=dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096)
    i=m.validate_input(p,config,1,version=VERSION)
    assert i==dict(schema_version='coe-input-low3-identity/0.1.0',shape=[1,256],sample_indices=[0],
        input_ids_sha256='fd4064e87c5bf79f04475d4294cb4d76a76d004654689565e6c64392604e01e0',
        attention_mask_sha256='84f8088ae6128f1785dfb442ea8c1e65cfa6a1bf8ee48751c7b02d4f79e3c4c3',
        batch_sha256='aa7c39c661b5fdec094860e503db8cd3b7b0700c7dbe5bfa8be62c187b5dac88',
        algorithm='SHA256_COMPACT_UTF8_JSON_IN_ORDER')
    assert p['samples'][0]['input_ids']==list(range(3,35))*8
    with pytest.raises(ValueError,match='INPUT_SHAPE'):m.input_identity(p)
    with pytest.raises(ValueError,match='MODEL_CONFIG'):m.validate_input(p,{**config,'max_position_embeddings':257},1,version=VERSION)
    p['samples'][0]['attention_mask'][255]=0
    with pytest.raises(ValueError,match='MASK'):m.input_identity(p,version=VERSION)

def test_signed_low_and_endpoint_R_are_independent_with_zero_denominator():
    rows=[row(binding(n),q,g) for n,q,g in [(256,2,4),(512,10,20),(2048,12,30)]]
    r=m.block_contrasts(rows)['per_token'][0]
    # Low: 10-2*20/4=0; endpoint: 12-10*30/20=-3.
    assert r['delta_coe_ns']==2 and r['R_exact']==dict(numerator=-3,denominator=1)
    assert r['low_side_comparison']['delta_coe_ns']==8 and r['low_side_comparison']['R_ns']==0
    assert r['coe_over_phase_gpu']=={256:.5,512:.5,2048:.4}
    assert r['raw_by_input'][256]['coe_over_phase']==.02
    assert r['raw_by_input'][256]['candidate_completion_budget_over_phase']==.06
    assert r['raw_by_input'][256]['positions']==dict(H_ns=3,D_ns=7)
    rows[0]['result']['windows'][0]['baseline']['gpu_activity']['union_ns']=0
    r=m.block_contrasts(rows)['per_token'][0]
    assert r['low_side_comparison']['R_ns'] is None and r['R_ns']==-3
    assert m.block_contrasts(rows)['per_token'][1]['R_ns']==-3.5
    with pytest.raises(ValueError,match='INCOMPLETE_BLOCK'):m.block_contrasts(rows[:2])

@pytest.mark.parametrize('failure',[None,'dependency','token'])
def test_fixed_budget_or_hard_failure_never_fills_missing_slots(tmp_path,failure):
    seen=[]
    def collect(b,out):
        seen.append(b)
        if len(seen)==4 and failure=='dependency':raise ValueError('MISSING_DEPENDENCY')
        r=row(b,{256:10,512:0,2048:8}[b['input_tokens']],20)['result']
        if len(seen)==4 and failure=='token':r['token_ids']=[[99],[18]]
        return r
    r=m.run_batch('cpu-low3','a'*40,tmp_path/'out',collect,version=VERSION)
    if failure:
        assert [s['status'] for s in r['runs']]==['COMPLETE']*3+['BLOCKED']+['NOT_RUN']*5
        assert r['incomplete_blocks']==[2,3] and len(r['blocks'])==1
    else:
        assert len(seen)==9 and len(r['blocks'])==3 and r['incomplete_blocks']==[]
        assert r['status']=='FIXED_NINE_LOW3_PILOT_COMPLETE_STOP_FOR_REVIEW'
        assert all(b['per_token'][0]['low_side_comparison']['delta_coe_ns']==-10 for b in r['blocks'])

@pytest.mark.parametrize('length',[256,512,2048])
def test_real_prepare_seal_and_profile_boundary(tmp_path,monkeypatch,length):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_actual_prepare_seal_and_profile_argv(tmp_path,monkeypatch,length)

@pytest.mark.parametrize('damage',[None,'hash','identity','budget','version','exit'])
def test_real_producer_canonical_two_token_consumer(tmp_path,monkeypatch,damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_real_collection_consumer_checks_both_tokens_and_preview(tmp_path,monkeypatch,damage)

@pytest.mark.parametrize('damage',['drain','dependency','future_gap','token'])
def test_new_role_keeps_actual_admission_rejections(tmp_path,monkeypatch,damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_real_producer_canonical_both_tokens_and_budget(tmp_path,monkeypatch,256,damage)

def test_isolated_import_origin_and_helper_identities(tmp_path):
    root=Path(__file__).resolve().parents[1]
    (tmp_path/'exposedpath').mkdir()
    (tmp_path/'exposedpath/__init__.py').write_text("raise RuntimeError('FOREIGN_MODULE_MUST_NOT_LOAD')")
    # -I is retained. Bind this already checked source root explicitly, not
    # PYTHONPATH or a third-party scripts package; no torch/CUDA import needed.
    code="""import sys,pathlib,json
root=pathlib.Path(sys.argv[1]).resolve();sys.path.insert(0,str(root))
from exposedpath import coe_input_pilot as m
from analysis.coe_helper_identity import validate_source
assert pathlib.Path(m.__file__).resolve()==root/'exposedpath/coe_input_pilot.py'
assert len(m.schedule('isolated','a'*40,version='COE-INPUT-P-LOW3-PILOT/0.1'))==9
print(json.dumps(validate_source((root/'exposedpath/runner.py').read_text(encoding='utf8'),'COE_PILOT_NATURAL')))
"""
    r=subprocess.run([sys.executable,'-I','-c',code,str(root)],cwd=tmp_path,
        env={**os.environ,'PYTHONPATH':str(tmp_path)},capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr

def test_old_four_point_delivery_is_still_proposal_only(tmp_path):
    from scripts.observation_preparation_batch import run
    with pytest.raises(ValueError,match='DELIVERY_CONTRACT'):
        run(dict(schema_version='coe-input-pilot-delivery/0.3',input_contract_version=m.EXTENDED_VERSION,
            model_process_budget=16,profile_budget=16,commit='a'*40,analysis_commit='a'*40),tmp_path/'out',execute=True,input_pilot=True)

def test_nine_actual_producer_results_form_three_new_whole_blocks(tmp_path,monkeypatch):
    from tests import test_coe_input_pilot as old
    from scripts.observation_preparation_batch import consume_collection
    def collect(b,folder):
        folder.mkdir()
        with monkeypatch.context() as slot:
            slot.setattr(old,'binding',lambda *a:b)
            old.test_real_collection_consumer_checks_both_tokens_and_preview(folder,slot,None)
            return consume_collection(folder,b,'a'*40)
    r=m.run_batch('cpu-low3','a'*40,tmp_path/'batch',collect,version=VERSION)
    assert r['status']=='FIXED_NINE_LOW3_PILOT_COMPLETE_STOP_FOR_REVIEW',[(s['status'],s.get('error')) for s in r['runs']]
    assert len(r['blocks'])==3 and all(len(b['per_token'])==2 for b in r['blocks'])
    assert all(set(b['per_token'][0]['raw_by_input'])=={256,512,2048} for b in r['blocks'])

def test_new_run_entry_rejects_bad_256_bytes_before_device_prepare(tmp_path,monkeypatch):
    from scripts.observation_preparation_batch import run
    from exposedpath import platform_adapter,gate8_diagnostic
    from tests.test_gate8_identity import write_json,sha
    seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,samples=[dict(
        sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'prospective',version=VERSION)
    bindings={str(n):dict(file_sha256=sha(p),identity=m.input_identity(json.loads(p.read_text()),version=VERSION)) for n,p in paths.items()}
    bindings['256']['file_sha256']='0'*64
    nsys=tmp_path/'not-nsys';nsys.write_bytes(b'CPU')
    monkeypatch.setattr(platform_adapter,'git',lambda argv:'' if 'status' in argv else 'a'*40)
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',lambda **kw:pytest.fail('must reject before GPU prepare'))
    c=dict(schema_version='coe-input-low3-pilot-delivery/0.1',input_contract_version=VERSION,
        commit='a'*40,analysis_commit='a'*40,model_process_budget=9,profile_budget=9,batch_id='cpu-low3',
        seed_input=str(seed),prompt_512_sha256=sha(seed),input_bindings=bindings,nsys=str(nsys),nsys_sha256=sha(nsys))
    with pytest.raises(ValueError,match='COE_INPUT_EXECUTION_INPUT_BINDING:256'):run(c,tmp_path/'out',execute=True,input_pilot=True)

def test_new_run_entry_cannot_relabel_old_delivery_schema(tmp_path):
    from scripts.observation_preparation_batch import run
    c=dict(schema_version='coe-input-low3-pilot-delivery/0.1',input_contract_version=m.EXTENDED_VERSION,
        commit='a'*40,analysis_commit='a'*40,model_process_budget=9,profile_budget=9)
    with pytest.raises(ValueError,match='DELIVERY_CONTRACT_VERSION'):run(c,tmp_path/'out',execute=True,input_pilot=True)
    assert not (tmp_path/'out').exists()
