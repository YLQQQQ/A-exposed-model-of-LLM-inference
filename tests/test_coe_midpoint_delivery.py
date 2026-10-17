"""Real PS5.1 dispatch with declared external process/device doubles only."""
import json
import pytest
from tests.test_observation_delivery import delivery,catalog,sha,ROOT
from tests.test_coe_input_delivery import input_delivery,launch_input


@pytest.fixture
def midpoint_delivery(input_delivery):
    root,code,pack,c=input_delivery
    c.update(schema_version='coe-input-pilot-delivery/0.2',input_contract_version='COE-INPUT-P-PILOT/0.2',
        batch_id='cpu-midpoint',model_process_budget=9,profile_budget=9,
        plan_sha256=sha(ROOT/'configs/coe_input_midpoint_pilot_v0_1.json'))
    (pack/'plan.json').write_bytes((ROOT/'configs/coe_input_midpoint_pilot_v0_1.json').read_bytes())
    (pack/'delivery.json').write_text(json.dumps(c));catalog(pack)
    return input_delivery


@pytest.mark.parametrize('scenario,reason',[('ok',None),('low','FREE_SPACE_INSUFFICIENT'),
    ('query','FREE_SPACE_UNKNOWN'),('write','PATH_NOT_WRITABLE'),('source','Source conflict')])
def test_midpoint_static_does_not_start_model(midpoint_delivery,scenario,reason):
    root,code,pack,c=midpoint_delivery
    if scenario=='source':(code/'scripts/coe_startup_storage.py').write_bytes(b'wrong')
    r=launch_input(midpoint_delivery,scenario)
    if reason:assert r.returncode!=0 and reason.encode() in r.stdout+r.stderr,(r.stdout+r.stderr).decode(errors='replace')
    else:
        assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
        receipt=json.loads((root/'logs/coe_input_aaaaaaaaaaaa_static/receipt.json').read_text(encoding='utf-8-sig'))
        assert receipt['model_process_budget']==receipt['profile_budget']==9
        assert receipt['stage_a_cuda_initializations']==receipt['stage_a_model_processes']==receipt['stage_a_profiles']==0
        assert receipt['historical_ylq_total_bytes'] is None
    assert not (root/'model_boundary_called').exists()


@pytest.mark.parametrize('mode',['actual','wrong','fresh_low','batch_fail','source_conflict'])
def test_midpoint_explicit_dispatch_requires_new_reviewed_static(midpoint_delivery,mode):
    root,code,pack,c=midpoint_delivery
    a=launch_input(midpoint_delivery);assert a.returncode==0,(a.stdout+a.stderr).decode(errors='replace')
    receipt=root/'logs/coe_input_aaaaaaaaaaaa_static/receipt.json'
    if mode=='source_conflict':(code/'scripts/coe_startup_storage.py').write_bytes(b'wrong')
    r=launch_input(midpoint_delivery,'low' if mode=='fresh_low' else 'batch_fail' if mode=='batch_fail' else 'ok',
        collect=True,reviewed='0'*64 if mode=='wrong' else sha(receipt))
    assert (r.returncode==0)==(mode=='actual'),(r.stdout+r.stderr).decode(errors='replace')
    assert (root/'model_boundary_called').exists()==(mode in ('actual','batch_fail'))
