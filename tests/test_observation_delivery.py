"""Real PS5.1 launcher parse/file checks; external command boundaries doubled."""
from pathlib import Path
import os
import subprocess
import csv
import hashlib
import json
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]


def test_launcher_exists_and_parses_with_actual_windows_powershell():
    p=ROOT/'scripts/run_observation_preparation.ps1'
    assert p.is_file(), 'missing two-stage preparation launcher'
    r=subprocess.run(['powershell.exe','-NoProfile','-Command',
        "$t=$null;$e=$null;[System.Management.Automation.Language.Parser]::ParseFile($env:OBS_SCRIPT,[ref]$t,[ref]$e)|Out-Null;if($e.Count){$e|Out-String|Write-Output;exit 1}"],
        env={**os.environ,'OBS_SCRIPT':str(p)},capture_output=True,text=True)
    assert r.returncode==0,r.stdout+r.stderr


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def catalog(folder):
    with (folder/'artifact_sha256.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader()
        for p in sorted(folder.iterdir()):
            if p.is_file() and p.name!='artifact_sha256.csv':w.writerow(dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)))


@pytest.fixture
def delivery(tmp_path):
    root=tmp_path/'YLQ';code=root/'checkout';pack=tmp_path/'delivery';pack.mkdir()
    for p in ('transfer','logs','diagnostics','evidence/observation_preparation'): (root/p).mkdir(parents=True,exist_ok=True)
    sources={}
    for p in ('scripts/coe_startup_storage.py','scripts/gate13_retention.py','scripts/run_observation_preparation.ps1'):
        dst=code/p;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((ROOT/p).read_bytes())
        sources[p]=[dict(bytes=dst.stat().st_size,sha256=sha(dst))]
    (pack/'run_observation_preparation.ps1').write_bytes((ROOT/'scripts/run_observation_preparation.ps1').read_bytes())
    for p in ('execution.bundle','prompt_512.json','model_sha256.csv'):(pack/p).write_bytes(b'CPU_PROCESS_BOUNDARY_ONLY')
    (pack/'not-a-collector').write_bytes(b'CPU_ONLY')
    cfg=dict(schema_version='observation-preparation-delivery/0.1',commit='a'*40,analysis_commit='a'*40,
        prerequisite='b'*40,model_process_budget=8,profile_budget=8,code_root=str(code),server_root=str(root),batch_id='cpu-eight',
        source_representations=sources,launcher_sha256=sha(pack/'run_observation_preparation.ps1'),
        bundle='execution.bundle',bundle_ref='refs/heads/main',bundle_sha256=sha(pack/'execution.bundle'),
        bundle_bytes=(pack/'execution.bundle').stat().st_size,nsys=str(pack/'not-a-collector'),nsys_sha256=sha(pack/'not-a-collector'))
    (pack/'delivery.json').write_text(json.dumps(cfg),encoding='utf8');catalog(pack)
    return root,code,pack,cfg


def launch(f,scenario='ok',collect=False,reviewed=''):
    root,code,pack,cfg=f
    env={**os.environ,'OBS_TEST_LAUNCHER':str(pack/'run_observation_preparation.ps1'),
         'OBS_TEST_PYTHON':sys._base_executable,'OBS_TEST_COLLECT':'1' if collect else '0',
         'OBS_TEST_REVIEWED':reviewed,'OBS_TEST_SCENARIO':scenario,
         'OBS_TEST_STORAGE':str(ROOT/'tests/coe_storage_boundary.py'),'COE_TEST_SCENARIO':scenario}
    return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
        str(ROOT/'tests/observation_launcher_boundary.ps1')],env=env,capture_output=True,timeout=60)


@pytest.mark.parametrize('scenario,reason',[('ok',None),('low','FREE_SPACE_INSUFFICIENT'),
    ('query','FREE_SPACE_UNKNOWN'),('write','PATH_NOT_WRITABLE'),('source','Source conflict')])
def test_real_a_does_not_cross_model_boundary(delivery,scenario,reason):
    root,code,pack,cfg=delivery
    if scenario=='source':(code/'scripts/coe_startup_storage.py').write_bytes(b'changed')
    p=launch(delivery,scenario);output=p.stdout+p.stderr
    if reason:assert p.returncode!=0 and reason.encode() in output,output.decode(errors='replace')
    else:
        assert p.returncode==0,output.decode(errors='replace')
        r=json.loads((root/'logs/observation_aaaaaaaaaaaa_static/receipt.json').read_text(encoding='utf-8-sig'))
        assert r['status']=='STATIC_READY_FOR_REVIEW' and r['historical_ylq_total_bytes'] is None
        assert r['stage_a_cuda_initializations']==r['stage_a_model_processes']==r['stage_a_profiles']==0
    assert not (root/'model_boundary_called').exists()


@pytest.mark.parametrize('review',['actual','wrong','fresh_low','batch_fail'])
def test_b_requires_reviewed_new_a_and_fresh_resources(delivery,review):
    root,code,pack,cfg=delivery
    p=launch(delivery);assert p.returncode==0,(p.stdout+p.stderr).decode(errors='replace')
    receipt=root/'logs/observation_aaaaaaaaaaaa_static/receipt.json'
    p=launch(delivery,scenario='low' if review=='fresh_low' else 'batch_fail' if review=='batch_fail' else 'ok',
        collect=True,reviewed='0'*64 if review=='wrong' else sha(receipt))
    if review=='actual':assert p.returncode==0,(p.stdout+p.stderr).decode(errors='replace')
    else:assert p.returncode!=0
    assert (root/'model_boundary_called').exists()==(review in ('actual','batch_fail'))
