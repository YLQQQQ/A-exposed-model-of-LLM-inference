"""512/2048 O/P Engineering: real file chain, explicitly doubled device/OS only."""
from copy import deepcopy
import json
import pytest
from exposedpath import observation_preparation as m

VERSION='OBSERVATION-PREPARATION-ENGINEERING/0.2'

def binding(variant='P',length=2048):
    return next(b for b in m.schedule('cpu-prep','a'*40,version=VERSION)
                if b['block']==1 and b['variant']==variant and b['input_tokens']==length)

def test_new_schedule_and_strict_legacy_input(tmp_path):
    from test_gate8_identity import write_json,sha
    rows=m.schedule('cpu-prep','a'*40,version=VERSION)
    assert [(b['input_tokens'],b['variant']) for b in rows]==[
        (512,'O'),(512,'P'),(2048,'P'),(2048,'O'),(2048,'O'),(2048,'P'),(512,'P'),(512,'O')]
    seed=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,samples=[dict(
        sample_index=0,input_ids=list(range(3,35))*16,attention_mask=[1]*512)]))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'inputs',version=VERSION)
    p=json.loads(paths[2048].read_text())
    config=dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096)
    identity=m.validate_input(p,config,2048,binding=binding('O'))
    assert identity['shape']==[1,2048] and len(identity['batch_sha256'])==64
    with pytest.raises(ValueError,match='INPUT_LENGTH'):m.validate_input(p,config,2048)
    with pytest.raises(ValueError,match='BINDING'):m.validate_binding({**binding(),'version':m.VERSION})
    p['samples'][0]['attention_mask'][-1]=0
    with pytest.raises(ValueError,match='MASK'):m.validate_input(p,config,2048,binding=binding())

@pytest.mark.parametrize('variant',['O','P'])
@pytest.mark.parametrize('length',[512,2048])
def test_prepare_seal_profile_and_real_producer_consumer(tmp_path,monkeypatch,variant,length):
    # Existing tests exercise real prepare/seal/collector argv and actual
    # producer->Canonical->S/A->COE->receipt consumer. External GPU is a double.
    import test_observation_preparation as old
    monkeypatch.setattr(old,'binding',binding)
    (tmp_path/'prepare').mkdir();(tmp_path/'chain').mkdir()
    old.test_actual_prepare_seal_collector_boundary(tmp_path/'prepare',monkeypatch,variant,length)
    monkeypatch.setattr(old,'binding',lambda *a:binding(variant,length))
    old.test_real_result_consumer_file_chain(tmp_path/'chain',monkeypatch,None)
    # Real saved result through whole-block summary; clones remain CPU doubles.
    result=json.loads((tmp_path/'chain/analyzed/sensitivity.json').read_text())
    def collect(b,out):
        r=deepcopy(result);r['binding']=b;return r
    summary=m.run_batch('cpu-prep','a'*40,tmp_path/'batch',collect,version=VERSION)
    assert summary['status']=='FIXED_EIGHT_COMPLETE_STOP_FOR_REVIEW' and len(summary['blocks'])==2
    assert all(len(b['per_token'])==2 for b in summary['blocks'])

def test_helpers_keep_actual_read_and_encoding_order(monkeypatch):
    import test_observation_preparation as old
    monkeypatch.setattr(old,'binding',lambda v='P',length=32:binding(v,2048))
    old.test_labels_equivalent_and_only_p_eliminates_onsite_preparation(monkeypatch)

def rows():
    answer=[]
    for b in m.schedule('cpu-prep','a'*40,version=VERSION)[:4]:
        n,v=b['input_tokens'],b['variant']
        q={(512,'O'):10,(2048,'O'):12,(512,'P'):8,(2048,'P'):20}[n,v]
        answer.append(dict(binding=b,status='COMPLETE',result=dict(status=m.STATUS,binding=b,token_ids=[[17],[18]],
            operations=[dict(token_index=i,phase=p,candidate_ns=q,positions=dict(H_ns=3,D_ns=7),
                kernel_ns=q,memop_ns=0,wall_ns=50,uncovered_ns=50-q,copy_wall_ns=40,
                sync_wall_ns=10,original_sync_ns=0,same_operation_all_gpu_union_ns=q)
                for i,p in enumerate(('prefill','decode'))],
            windows=[dict(phase=p,projection=dict(start_ns=0,end_ns=100),
                baseline=dict(gpu_activity=dict(status='KNOWN',union_ns=20 if n==512 else 30)))
                for p in ('prefill','decode')])))
    return answer

def test_signed_proportional_residual_and_invalid_denominator():
    r=rows();s=m.block_contrasts(r)['per_token'][0]
    # Hand values: O=12-10*30/20=-3; P=20-8*30/20=8; P-O=11.
    assert s['R_by_variant']['O']['R_ns']==-3
    assert s['R_by_variant']['P']['R_ns']==8 and s['R_P_minus_R_O_ns']==11
    assert s['raw_by_condition']['G2048P']['coe_over_phase']==.2
    assert s['raw_by_condition']['G2048P']['phase_gpu_union_ns']==30
    r[0]['result']['windows'][0]['baseline']['gpu_activity']['union_ns']=0
    s=m.block_contrasts(r)['per_token'][0]
    assert s['R_by_variant']['O']['R_ns'] is None and s['R_P_minus_R_O_ns'] is None
    # A wrong-block sample must never complete a block.
    r[0]['binding']=next(b for b in m.schedule('cpu-prep','a'*40,version=VERSION)
        if b['block']==2 and b['condition']==r[0]['binding']['condition'])
    with pytest.raises(ValueError,match='BLOCK_IDENTITY'):m.block_contrasts(r)

def test_fixed_eight_failure_preserves_unrun_slots(tmp_path):
    seen=[];examples=rows()
    def collect(b,out):
        seen.append(b)
        if len(seen)==6:raise ValueError('MISSING_DEPENDENCY')
        r=deepcopy(next(x['result'] for x in examples if x['binding']['condition']==b['condition']))
        r['binding']=b
        return r
    r=m.run_batch('cpu-prep','a'*40,tmp_path/'batch',collect,version=VERSION)
    assert [s['status'] for s in r['runs']]==['COMPLETE']*5+['BLOCKED']+['NOT_RUN']*2
    assert len(r['blocks'])==1 and r['incomplete_blocks']==[2]

@pytest.mark.parametrize('damage',['drain','dependency','unmarked_token','stream'])
def test_new_scope_keeps_existing_quality_rejections(tmp_path,monkeypatch,damage):
    import test_observation_preparation as old
    monkeypatch.setattr(old,'binding',lambda *a:binding())
    reason={'drain':'DRAIN','dependency':'API_SEMANTICS_UNBOUNDED:cudaStreamWaitEvent',
        'unmarked_token':'TOKEN','stream':'STREAM|OTHER_STREAM'}[damage]
    old.test_existing_quality_rejections_still_stop_both_token_chain(tmp_path,monkeypatch,damage,reason)

@pytest.mark.parametrize('damage',['result_hash','token','exit','version'])
def test_new_consumer_rejects_actual_file_chain_damage(tmp_path,monkeypatch,damage):
    import test_observation_preparation as old
    monkeypatch.setattr(old,'binding',lambda *a:binding('O'))
    old.test_real_result_consumer_file_chain(tmp_path,monkeypatch,damage)

@pytest.mark.parametrize('damage',['token','role','variant','source','cache'])
def test_new_producer_identity_cannot_be_relabelled(tmp_path,monkeypatch,damage):
    import test_observation_preparation as old
    monkeypatch.setattr(old,'binding',lambda *a:binding('P'))
    old.test_real_producer_evidence_tampering_rejected(tmp_path,monkeypatch,damage)

def test_new_execution_input_hash_checked_before_model_prepare(tmp_path,monkeypatch):
    from scripts.observation_preparation_batch import run
    from exposedpath import platform_adapter,gate8_diagnostic
    from test_gate8_identity import write_json,sha
    p=write_json(tmp_path/'seed.json',dict(fixed_input_tokens=512,samples=[dict(
        sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    nsys=tmp_path/'not-collector';nsys.write_bytes(b'CPU')
    monkeypatch.setattr(platform_adapter,'git',lambda argv:'' if 'status' in argv else 'a'*40)
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',lambda **kw:pytest.fail('must not reach device prepare'))
    c=dict(schema_version='observation-preparation-delivery/0.2',observation_contract_version=VERSION,
        commit='a'*40,analysis_commit='a'*40,model_process_budget=8,profile_budget=8,
        nsys=str(nsys),nsys_sha256=sha(nsys),seed_input=str(p),prompt_512_sha256=sha(p),
        input_bindings={'512':{},'2048':{}})
    with pytest.raises(ValueError,match='EXECUTION_INPUT_BINDING'):run(c,tmp_path/'out',execute=True)

def test_new_budget_artifact_cannot_be_tampered(tmp_path,monkeypatch):
    import test_observation_preparation as old
    from scripts.observation_preparation_batch import consume_collection
    monkeypatch.setattr(old,'binding',lambda *a:binding('O'))
    old.test_real_result_consumer_file_chain(tmp_path,monkeypatch,None)
    (tmp_path/'analyzed/candidate_budget_preview.json').write_text('{}')
    with pytest.raises(ValueError,match='BUDGET_PREVIEW_BINDING'):consume_collection(tmp_path,binding('O'),'a'*40)
