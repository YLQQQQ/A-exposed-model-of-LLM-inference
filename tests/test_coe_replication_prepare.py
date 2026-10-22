"""Only new statement/configuration/summary boundaries; no CUDA or old suites."""
from copy import deepcopy
import importlib.util,json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]
STATEMENT=ROOT/'configs/coe_endpoint_replication_v0_1.json'


def entry():
    p=ROOT/'scripts/coe_replication_prepare.py'
    assert p.is_file(),'new candidate statement is not connected to the existing configured plan'
    spec=importlib.util.spec_from_file_location('_replication_prepare',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def fixture(tmp):
    m=entry();s=json.loads(STATEMENT.read_text());inputs=tmp/'inputs';inputs.mkdir()
    # Explicit CPU file doubles, not the archived prompt/content qualification.
    for n in (512,2048):
        p=inputs/f'input_{n}.json';v=dict(fixed_input_tokens=n,samples=[dict(sample_index=0,
            input_ids=list(range(100,132))*(n//32),attention_mask=[1]*n)])
        p.write_text(json.dumps(v));r=s['input_reference']['inputs'][str(n)]
        r.update(bytes=p.stat().st_size,sha256=m.sha(p),identity=m.contract().input_identity(v,n))
    path=tmp/'statement.json';path.write_text(json.dumps(s))
    prepared=m.prepare(path,inputs,'cpu-replication','a'*40,tmp/'prepared')
    return m,s,path,prepared,inputs


def rows(prepared):
    r=[]
    for slot in prepared['slots']:
        low,high={1:(20,30),2:(20,40),3:(10,50),4:(10,30)}[slot['block']]
        q=low if slot['input_tokens']==512 else high;g=100 if slot['input_tokens']==512 else 200
        r.append(dict(slot=slot,report_sha256='1'*64,capture_sha256='2'*64,
            metrics=[dict(token_index=i,coe_ns=q,phase_gpu_union_ns=g,phase_ns=1000,coe_phase_ratio=q/1000) for i in (0,1)]))
    return r


def test_statement_reuses_configured_schedule_budget_and_real_model_contract(tmp_path):
    m,s,path,p,inputs=fixture(tmp_path)
    assert [(v['block'],v['input_tokens']) for v in p['slots']]==[
        (1,512),(1,2048),(2,2048),(2,512),(3,2048),(3,512),(4,512),(4,2048)]
    assert len({v['run_id'] for v in p['slots']})==8 and p['gpu_authorized'] is False
    assert p['budget']['model_process_budget']==8 and p['budget']['blocks']==4
    assert json.loads((tmp_path/'prepared/execution_plan.json').read_text())==s['execution_plan']
    cfg=dict(schema_version=m.contract().PLAN_VERSION,plan=s['execution_plan'],native_commit=m.contract().NATIVE,
        controller_commit='a'*40,analysis_commit='a'*40,inputs=p['inputs'],producer_policy_sha256='3'*64,code_root=str(ROOT),
        activity_policy_version=s['components']['activity_policy'],model_config_sha256='4'*64,
        model_limits=dict(vocab_size=151936,max_position_embeddings=32768,eos_token_ids=[151645]))
    for slot in p['slots']:
        c=m.pilot().one_configuration(cfg,slot)['model_contract']
        c['session']=dict(activity_policy_version=cfg['activity_policy_version'])
        assert m.contract().validate_model(c)==m.contract().NATIVE
        assert c['batch_size']==1 and c['input_slot']==slot


def test_whole_block_summary_preserves_signed_R_and_order_sensitivity(tmp_path):
    m,s,path,p,_=fixture(tmp_path);r=rows(p)
    result=m.summarize(path,p,r)
    assert [v['R_ns'] for v in result['comparisons'] if v['token_index']==0]==[-10,0,30,10]
    d=result['descriptive'][0]
    assert d['R_mean_ns']==7.5 and d['R_median_ns']==5 and d['R_range_ns']==[-10,30]
    assert d['by_order_R_mean_ns']=={'512_2048':0.0,'2048_512':15.0}
    assert d['leave_one_out_R_mean_ns'][2]['R_mean_ns']==0
    assert result['scientific_verdict']=='REVIEW_REQUIRED_NOT_DATA_QUALITY_PASS' and not result['formal_eligible']
    z=deepcopy(r);z[0]['metrics'][0]['phase_gpu_union_ns']=0
    u=m.summarize(path,p,z)
    assert u['descriptive'][0]['R_mean_ns'] is None and u['descriptive'][0]['R_undefined_blocks']==[1]


@pytest.mark.parametrize('damage,reason',[
    ('incomplete','INCOMPLETE'),('spliced','SLOT'),('missing_token','TOKEN_COVERAGE'),
    ('statement_changed','STATEMENT_CHANGED'),('missing_source_hash','SOURCE_HASH'),
    ('source_changed','SOURCE_COMPONENT_CHANGED')])
def test_invalid_or_misaligned_files_never_form_complete_repeats(tmp_path,damage,reason):
    m,s,path,p,_=fixture(tmp_path);r=rows(p)
    if damage=='incomplete':r.pop()
    if damage=='spliced':r[-1]['slot']=p['slots'][0]
    if damage=='missing_token':r[-1]['metrics'].pop()
    if damage=='statement_changed':path.write_text(path.read_text()+' ')
    if damage=='missing_source_hash':r[0]['capture_sha256']=None
    if damage=='source_changed':p['source_sha256']['scripts/cupti_input_contract.py']='0'*64
    with pytest.raises(ValueError,match=reason):m.summarize(path,p,r)


@pytest.mark.parametrize('damage,reason',[('input_bytes','INPUT_HASH'),('mask_identity','INPUT_IDENTITY'),
    ('role','PLAN_ROLE'),('budget','BUDGET'),('unbalanced','BALANCE'),('R_policy','ANALYSIS_POLICY')])
def test_preparation_checks_content_role_budget_and_order(tmp_path,damage,reason):
    m,s,path,p,inputs=fixture(tmp_path)
    if damage=='input_bytes':(inputs/'input_512.json').write_text('{}')
    if damage=='mask_identity':s['input_reference']['inputs']['512']['identity']['attention_mask_sha256']='0'*64
    if damage=='role':s['execution_plan']['role']='Formal'
    if damage=='budget':s['budget']['model_processes']=9
    if damage=='unbalanced':s['execution_plan']['orders'][1]=[512,2048]
    if damage=='R_policy':s['analysis']['R']='COE2048-COE512'
    path.write_text(json.dumps(s))
    with pytest.raises(ValueError,match=reason):m.prepare(path,inputs,'cpu-other','b'*40,tmp_path/'other')


@pytest.mark.parametrize('slot_index',[0,1])
def test_new_slot_through_existing_two_token_isolated_file_consumer(tmp_path,slot_index):
    import subprocess,sys,jsonschema
    from tests.test_cupti_configured_plan import planned_files
    m,s,path,p,inputs=fixture(tmp_path)
    folder=tmp_path/'model'
    _,cfg=planned_files(folder,p['slots'][slot_index])
    cfg_path=tmp_path/'control.json';cfg_path.write_text(json.dumps(cfg))
    boot="""import sys,json,runpy
from pathlib import Path
sys.path.insert(0,sys.argv[1])
sys.path.append(sys.argv[4]) # explicitly reuse installed CPU schema dependency under -S
import jsonschema
assert Path(jsonschema.__file__).resolve().parent.parent==Path(sys.argv[4]).resolve()
m=runpy.run_path(sys.argv[1]+'/scripts/cupti_timeline_b.py')
r=m['analyze_model'](Path(sys.argv[2]),dict(pid=7),json.loads(Path(sys.argv[3]).read_text()))
assert not any(n=='torch' or n.startswith('torch.') for n in sys.modules)
print(json.dumps({'status':r['status'],'token_values':[v['result']['coe_ns'] for v in r['token_results']]}))
"""
    result=subprocess.run([sys.executable,'-I','-S','-B','-c',boot,str(ROOT),str(folder),str(cfg_path),
        str(Path(jsonschema.__file__).resolve().parent.parent)],
        cwd=tmp_path,capture_output=True,text=True,timeout=20)
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)==dict(status='BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW',token_values=[20,1])
