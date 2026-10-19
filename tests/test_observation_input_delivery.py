"""Real PowerShell branches; explicit OS/process/device doubles, no GPU."""
import json
import pytest
from tests.test_observation_delivery import delivery,launch,catalog,sha,ROOT

@pytest.fixture
def input_sensitivity_delivery(delivery):
    root,code,pack,c=delivery
    c.update(schema_version='observation-preparation-delivery/0.2',
        observation_contract_version='OBSERVATION-PREPARATION-ENGINEERING/0.2',
        plan_sha256=sha(ROOT/'configs/observation_input_sensitivity_v0_1.json'))
    (pack/'plan.json').write_bytes((ROOT/'configs/observation_input_sensitivity_v0_1.json').read_bytes())
    (pack/'delivery.json').write_text(json.dumps(c));catalog(pack)
    return delivery

@pytest.mark.parametrize('mode',['ok','low','query','write','source'])
def test_new_a_resources_and_identity_without_model(input_sensitivity_delivery,mode):
    root,code,pack,c=input_sensitivity_delivery
    if mode=='source':(code/'scripts/coe_startup_storage.py').write_bytes(b'wrong')
    r=launch(input_sensitivity_delivery,mode)
    assert (r.returncode==0)==(mode=='ok'),(r.stdout+r.stderr).decode(errors='replace')
    assert not (root/'model_boundary_called').exists()
    if mode=='ok':
        a=json.loads((root/'logs/observation_aaaaaaaaaaaa_static/receipt.json').read_text(encoding='utf-8-sig'))
        assert a['status']=='STATIC_READY_FOR_REVIEW' and a['stage_a_model_processes']==0

@pytest.mark.parametrize('mode',['actual','wrong','fresh_low','batch_fail'])
def test_b_needs_real_new_a_and_fails_closed(input_sensitivity_delivery,mode):
    root,code,pack,c=input_sensitivity_delivery
    r=launch(input_sensitivity_delivery);assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    receipt=root/'logs/observation_aaaaaaaaaaaa_static/receipt.json'
    r=launch(input_sensitivity_delivery,'low' if mode=='fresh_low' else 'batch_fail' if mode=='batch_fail' else 'ok',
        collect=True,reviewed='0'*64 if mode=='wrong' else sha(receipt))
    assert (r.returncode==0)==(mode=='actual'),(r.stdout+r.stderr).decode(errors='replace')
    assert (root/'model_boundary_called').exists()==(mode in ('actual','batch_fail'))
