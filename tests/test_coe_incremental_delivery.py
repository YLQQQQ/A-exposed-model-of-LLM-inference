"""Actual PS5.1 branches; external deployment and GPU commands doubled only."""
import json
import pytest
from tests.test_observation_delivery import delivery,catalog,sha,ROOT
from tests.test_coe_input_delivery import input_delivery,launch_input


@pytest.fixture
def incremental_delivery(input_delivery):
    root,code,pack,c=input_delivery
    c.update(schema_version='coe-input-incremental-pilot-delivery/0.1',
        input_contract_version='COE-INPUT-P-INCREMENTAL-PILOT/0.1',batch_id='cpu-increment',
        model_process_budget=9,profile_budget=9,plan_sha256=sha(ROOT/'configs/coe_input_incremental_pilot_v0_1.json'))
    (pack/'plan.json').write_bytes((ROOT/'configs/coe_input_incremental_pilot_v0_1.json').read_bytes())
    (pack/'delivery.json').write_text(json.dumps(c));catalog(pack)
    return input_delivery


@pytest.mark.parametrize('scenario,reason',[('ok',None),('low','FREE_SPACE_INSUFFICIENT'),
    ('query','FREE_SPACE_UNKNOWN'),('write','PATH_NOT_WRITABLE'),('source','Source conflict')])
def test_incremental_A_is_static_and_unknown_space_cannot_pass(incremental_delivery,scenario,reason):
    root,code,pack,c=incremental_delivery
    if scenario=='source':(code/'scripts/coe_startup_storage.py').write_bytes(b'wrong')
    r=launch_input(incremental_delivery,scenario)
    if reason:assert r.returncode!=0 and reason.encode() in r.stdout+r.stderr,(r.stdout+r.stderr).decode(errors='replace')
    else:
        assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
        receipt=json.loads((root/'logs/coe_input_aaaaaaaaaaaa_static/receipt.json').read_text(encoding='utf-8-sig'))
        assert receipt['model_process_budget']==receipt['profile_budget']==9
        assert receipt['stage_a_model_processes']==receipt['stage_a_cuda_initializations']==receipt['stage_a_profiles']==0
        assert receipt['historical_ylq_total_bytes'] is None
    assert not (root/'model_boundary_called').exists()


@pytest.mark.parametrize('mode',['actual','wrong','fresh_low','batch_fail','source_conflict','existing'])
def test_incremental_B_needs_new_actual_A_and_never_resumes(incremental_delivery,mode):
    root,code,pack,c=incremental_delivery
    r=launch_input(incremental_delivery);assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    receipt=root/'logs/coe_input_aaaaaaaaaaaa_static/receipt.json'
    if mode=='source_conflict':(code/'scripts/coe_startup_storage.py').write_bytes(b'wrong')
    if mode=='existing':(root/'evidence/coe_input_pilot/cpu-increment').mkdir(parents=True)
    r=launch_input(incremental_delivery,'low' if mode=='fresh_low' else 'batch_fail' if mode=='batch_fail' else 'ok',
        collect=True,reviewed='0'*64 if mode=='wrong' else sha(receipt))
    assert (r.returncode==0)==(mode=='actual'),(r.stdout+r.stderr).decode(errors='replace')
    assert (root/'model_boundary_called').exists()==(mode in ('actual','batch_fail'))
