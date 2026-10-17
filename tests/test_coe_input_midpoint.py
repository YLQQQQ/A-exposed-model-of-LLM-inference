"""Three-point file-chain checks; every CUDA/process boundary is a CPU double."""
from copy import deepcopy
import json
from pathlib import Path
import pytest

from tests.test_coe_input_pilot import row

VERSION='COE-INPUT-P-PILOT/0.2'


def api():
    from exposedpath import coe_input_pilot
    return coe_input_pilot


def binding(length=1024):
    return next(b for b in api().schedule('cpu-midpoint','a'*40,version=VERSION) if b['input_tokens']==length)


def test_three_point_schedule_preserves_old_finite_contract():
    m=api()
    assert [b['input_tokens'] for b in m.schedule('cpu-midpoint','a'*40,version=VERSION)]==[512,1024,2048,1024,2048,512,2048,512,1024]
    assert len(m.schedule('old','a'*40))==8
    old=deepcopy(binding());old['version']=m.VERSION
    with pytest.raises(ValueError,match='COE_INPUT_BINDING'):m.validate_binding(old)
    for k,v in [('pass_id','pass0'),('batch_size',2),('observation_variant','O'),('position',1),('warmup_count',1)]:
        b=binding();b[k]=v
        with pytest.raises(ValueError,match='COE_INPUT_BINDING'):m.validate_binding(b)


def test_1024_input_bytes_mask_and_identity_are_version_bound(tmp_path):
    from tests.test_gate8_identity import write_json,sha
    m=api();seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,
        samples=[dict(sample_index=0,input_ids=list(range(3,35))*16,attention_mask=[1]*512)]))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'inputs',version=VERSION)
    assert set(paths)=={512,1024,2048}
    p=json.loads(paths[1024].read_text());i=m.input_identity(p,version=VERSION)
    assert p['samples'][0]['input_ids']==list(range(3,35))*32 and i['shape']==[1,1024]
    assert i['schema_version']=='coe-input-axis-identity/0.2.0'
    with pytest.raises(ValueError,match='COE_INPUT_INPUT_SHAPE'):m.input_identity(p)
    from exposedpath import coe_pilot
    assert coe_pilot.validate_input(p,dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096),1,binding=binding())==i
    p['samples'][0]['attention_mask'][17]=0
    with pytest.raises(ValueError,match='COE_INPUT_MASK'):m.input_identity(p,version=VERSION)
    with pytest.raises(ValueError,match='COE_INPUT_SEED_HASH'):m.make_inputs(seed,'0'*64,tmp_path/'bad',version=VERSION)


def test_signed_endpoint_and_both_midpoint_references_have_hand_answers():
    m=api();bs=m.schedule('cpu-midpoint','a'*40,version=VERSION)[:3]
    rows=[row(b,q,g) for b,q,g in zip(bs,(10,9,12),(20,10,30))]
    r=m.block_contrasts(rows)['per_token'][0]
    assert r['delta_coe_ns']==2 and r['R_exact']==dict(numerator=-3,denominator=1)
    assert r['coe_over_phase_gpu']=={512:0.5,1024:0.9,2048:0.4}
    assert [(c['lower_input'],c['higher_input'],c['delta_coe_ns'],c['R_ns']) for c in r['midpoint_contrasts']]==[(512,1024,-1,4),(1024,2048,3,-15)]
    rows[1]['result']['windows'][0]['baseline']['gpu_activity']['union_ns']=0
    r=m.block_contrasts(rows)['per_token'][0]
    assert r['midpoint_contrasts'][1]['R_ns'] is None
    assert r['midpoint_contrasts'][1]['R_status']=='UNDEFINED_INVALID_PHASE_GPU_DENOMINATOR'
    assert m.block_contrasts(rows)['per_token'][1]['R_ns']==-3.5
    rows[1]['result']['windows'][0]['baseline']['gpu_activity']['status']='UNKNOWN'
    r=m.block_contrasts(rows)['per_token'][0]
    assert r['R_ns']==-3  # Endpoint reference must not silently depend on middle G.
    assert all(c['R_ns'] is None for c in r['midpoint_contrasts'])
    with pytest.raises(ValueError,match='INCOMPLETE_BLOCK'):m.block_contrasts(rows[:2])
    with pytest.raises(ValueError,match='BLOCK_CONDITIONS'):m.block_contrasts([rows[0],rows[0],rows[2]])


def test_nonmonotone_zero_values_complete_exactly_nine_slots(tmp_path):
    m=api();seen=[]
    def collect(b,out):
        seen.append((b['block'],b['input_tokens']))
        return row(b,{512:10,1024:0,2048:8}[b['input_tokens']],20)['result']
    r=m.run_batch('cpu-midpoint','a'*40,tmp_path/'runs',collect,version=VERSION)
    assert seen==[(1,512),(1,1024),(1,2048),(2,1024),(2,2048),(2,512),(3,2048),(3,512),(3,1024)]
    assert r['status']=='FIXED_NINE_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW' and r['incomplete_blocks']==[]
    assert r['model_process_budget']==r['profile_budget']==9 and len(r['blocks'])==3
    assert all(b['per_token'][0]['R_ns']==-2 for b in r['blocks'])


@pytest.mark.parametrize('failure',['dependency','token'])
def test_hard_failure_preserves_completed_block_and_all_unrun_slots(tmp_path,failure):
    m=api();seen=[]
    def collect(b,out):
        seen.append(b)
        if len(seen)==4 and failure=='dependency':raise ValueError('MISSING_DEPENDENCY')
        r=row(b,10,20)['result']
        if len(seen)==4:r['token_ids']=[[99],[18]]
        return r
    r=m.run_batch('cpu-midpoint','a'*40,tmp_path/'runs',collect,version=VERSION)
    assert len(seen)==4 and r['status']=='BLOCKED'
    assert [s['status'] for s in r['runs']]==['COMPLETE']*3+['BLOCKED']+['NOT_RUN']*5
    assert [b['block'] for b in r['blocks']]==[1] and r['incomplete_blocks']==[2,3]


@pytest.mark.parametrize('damage',[None,'drain','dependency','future_gap','token'])
def test_actual_producer_canonical_both_tokens_and_budget_for_1024(tmp_path,monkeypatch,damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_real_producer_canonical_both_tokens_and_budget(tmp_path,monkeypatch,1024,damage)


def test_actual_1024_prepare_seal_and_profile_boundary(tmp_path,monkeypatch):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_actual_prepare_seal_and_profile_argv(tmp_path,monkeypatch,1024)


@pytest.mark.parametrize('damage',[None,'hash','version','identity','exit','budget'])
def test_actual_1024_collection_report_consumption(tmp_path,monkeypatch,damage):
    from tests import test_coe_input_pilot as old
    monkeypatch.setattr(old,'binding',binding)
    old.test_real_collection_consumer_checks_both_tokens_and_preview(tmp_path,monkeypatch,damage)


def test_1024_identity_rejects_old_role_and_damaged_prepared_file(tmp_path):
    from tests.test_gate8_identity import write_json,sha
    from exposedpath import coe_pilot
    m=api();b=binding();p=dict(fixed_input_tokens=1024,samples=[dict(sample_index=0,input_ids=[7]*1024,attention_mask=[1]*1024)])
    model=tmp_path/'model';model.mkdir();write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    write_json(tmp_path/'prompt.json',p)
    root=Path(__file__).resolve().parents[1]
    mf={**m.minimal_fields(b),**dict(runner_git_commit='a'*40,runner_git_dirty=False,
        coe_input=m.input_identity(p,version=VERSION),target_python={},isolated_preflight_version='cpu',model_id=str(model),
        prompt_tokens_sha256=sha(tmp_path/'prompt.json'),runner_source_sha256=sha(root/'exposedpath/runner.py'),
        preparation_source_sha256=sha(root/'exposedpath/observation_preparation.py'),input_pilot_source_sha256=sha(root/'exposedpath/coe_input_pilot.py'))}
    assert m.validate(mf)==b;coe_pilot.validate_prepared(mf,tmp_path,root)
    bad=deepcopy(mf);bad['pilot']['version']=m.VERSION
    with pytest.raises(ValueError,match='COE_INPUT_BINDING'):m.validate(bad)
    p['samples'][0]['input_ids'][20]=8;write_json(tmp_path/'prompt.json',p)
    with pytest.raises(ValueError,match='COE_PILOT_INPUT_HASH'):coe_pilot.validate_prepared(mf,tmp_path,root)


def test_new_execution_rejects_bad_1024_bytes_before_device_prepare(tmp_path,monkeypatch):
    from scripts.observation_preparation_batch import run
    from exposedpath import platform_adapter,gate8_diagnostic
    from tests.test_gate8_identity import write_json,sha
    m=api();seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,
        samples=[dict(sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    nsys=tmp_path/'not-a-collector';nsys.write_bytes(b'CPU_ONLY')
    paths=m.make_inputs(seed,sha(seed),tmp_path/'planned',version=VERSION)
    bindings={str(n):dict(file_sha256=sha(p),identity=m.input_identity(json.loads(p.read_text()),version=VERSION)) for n,p in paths.items()}
    bindings['1024']['file_sha256']='0'*64
    monkeypatch.setattr(platform_adapter,'git',lambda argv:'' if 'status' in argv else 'a'*40)
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',lambda **kw:pytest.fail('Must reject before device prepare'))
    c=dict(schema_version='coe-input-pilot-delivery/0.2',input_contract_version=VERSION,commit='a'*40,analysis_commit='a'*40,
        batch_id='cpu-midpoint',model_process_budget=9,profile_budget=9,seed_input=str(seed),prompt_512_sha256=sha(seed),
        nsys=str(nsys),nsys_sha256=sha(nsys),input_bindings=bindings)
    with pytest.raises(ValueError,match='COE_INPUT_EXECUTION_INPUT_BINDING:1024'):run(c,tmp_path/'out',execute=True,input_pilot=True)


def test_nine_real_producer_files_consumed_as_three_complete_blocks(tmp_path,monkeypatch):
    from tests import test_coe_input_pilot as old
    from scripts.observation_preparation_batch import consume_collection
    m=api()
    def collect(b,folder):
        folder.mkdir()
        with monkeypatch.context() as slot:
            slot.setattr(old,'binding',lambda length=1024:b)
            old.test_real_collection_consumer_checks_both_tokens_and_preview(folder,slot,None)
            return consume_collection(folder,b,'a'*40)
    r=m.run_batch('cpu-midpoint','a'*40,tmp_path/'batch',collect,version=VERSION)
    assert r['status']=='FIXED_NINE_INPUT_PILOT_COMPLETE_STOP_FOR_REVIEW',[(s['status'],s.get('error')) for s in r['runs']]
    assert len(r['blocks'])==3 and len(r['runs'])==9
    assert all(b['per_token'][0]['delta_coe_ns']==b['per_token'][0]['R_ns']==0 for b in r['blocks'])
