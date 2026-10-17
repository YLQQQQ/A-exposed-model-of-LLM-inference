"""Actual PowerShell entry, external commands doubled; never a CUDA run."""
import json
from pathlib import Path
import subprocess
import os
import pytest

from tests.test_observation_delivery import delivery,launch,catalog,sha,ROOT


@pytest.fixture
def input_delivery(delivery):
    root,code,pack,c=delivery
    c.update(schema_version='coe-input-pilot-delivery/0.1',batch_id='cpu-input-eight',
        plan_sha256=sha(ROOT/'configs/coe_input_axis_proposal_v0_1.json'))
    (pack/'plan.json').write_bytes((ROOT/'configs/coe_input_axis_proposal_v0_1.json').read_bytes())
    (pack/'delivery.json').write_text(json.dumps(c));catalog(pack)
    return delivery


def launch_input(f,scenario='ok',collect=False,reviewed=''):
    root,code,pack,cfg=f
    env={**os.environ,'OBS_TEST_LAUNCHER':str(pack/'run_observation_preparation.ps1'),
        'OBS_TEST_PYTHON':__import__('sys')._base_executable,'OBS_TEST_COLLECT':'1' if collect else '0',
        'OBS_TEST_REVIEWED':reviewed,'OBS_TEST_SCENARIO':scenario,'OBS_TEST_STORAGE':str(ROOT/'tests/coe_storage_boundary.py'),
        'COE_TEST_SCENARIO':scenario,'OBS_TEST_INPUT_PILOT':'1'}
    return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(ROOT/'tests/observation_launcher_boundary.ps1')],env=env,capture_output=True,timeout=60)


@pytest.mark.parametrize('scenario,reason',[('ok',None),('low','FREE_SPACE_INSUFFICIENT'),
    ('query','FREE_SPACE_UNKNOWN'),('write','PATH_NOT_WRITABLE'),('source','Source conflict')])
def test_new_static_entry_never_crosses_collection_boundary(input_delivery,scenario,reason):
    root,code,pack,c=input_delivery
    if scenario=='source':(code/'scripts/coe_startup_storage.py').write_bytes(b'wrong')
    r=launch_input(input_delivery,scenario)
    if reason:assert r.returncode!=0 and reason.encode() in r.stdout+r.stderr,(r.stdout+r.stderr).decode(errors='replace')
    else:
        assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
        v=json.loads((root/'logs/coe_input_aaaaaaaaaaaa_static/receipt.json').read_text(encoding='utf-8-sig'))
        assert v['status']=='STATIC_READY_FOR_REVIEW' and v['role']=='Pilot'
        assert v['historical_ylq_total_bytes'] is None and v['stage_a_cuda_initializations']==0
    assert not (root/'model_boundary_called').exists()


@pytest.mark.parametrize('mode',['actual','wrong','fresh_low','batch_fail','source_conflict'])
def test_explicit_pilot_needs_new_reviewed_receipt_and_fresh_resources(input_delivery,mode):
    root,code,pack,c=input_delivery
    r=launch_input(input_delivery);assert r.returncode==0,(r.stdout+r.stderr).decode(errors='replace')
    receipt=root/'logs/coe_input_aaaaaaaaaaaa_static/receipt.json'
    if mode=='source_conflict':(code/'scripts/coe_startup_storage.py').write_bytes(b'wrong')
    r=launch_input(input_delivery,'low' if mode=='fresh_low' else 'batch_fail' if mode=='batch_fail' else 'ok',
        collect=True,reviewed='0'*64 if mode=='wrong' else sha(receipt))
    assert (r.returncode==0)==(mode=='actual'),(r.stdout+r.stderr).decode(errors='replace')
    assert (root/'model_boundary_called').exists()==(mode in ('actual','batch_fail'))
