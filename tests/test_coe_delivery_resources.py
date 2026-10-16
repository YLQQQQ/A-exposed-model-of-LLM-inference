"""Real sealed reference and real PS5.1 entry; explicit CPU process/OS doubles.

No Git deployment, pytest110, CUDA, nsys or model is executed by the harness.
"""
import csv
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import pytest

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'.local/transfer/coe_4f1c3b55caf3_static.zip'
COMMIT='a'*40


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2),encoding='utf8');return p


def sealed():
    path=Path(os.environ.get('COE_REUSE_STATIC_ARCHIVE',str(STATIC)))
    if not path.is_file():pytest.skip('sealed static ZIP needed for this local artifact regression')
    assert path.stat().st_size==85783 and sha(path)=='b062b9502e2796cdbd91b47a1d0de17c549062036cc361948a9d6d131e8e13bc'
    return path


@pytest.fixture
def prepared(tmp_path):
    archive=sealed()
    with zipfile.ZipFile(archive) as z:
        old=json.loads(z.read('delivery.json').decode('utf-8-sig'))
        source=json.loads(z.read('source_bytes.json').decode('utf-8-sig'))
        receipt=z.read('receipt.json')
    code=tmp_path/'checkout';code.mkdir()
    locked={};old_paths=[]
    for row in source:
        path=row['path'];old_paths.append(path)
        file=code/path;file.parent.mkdir(parents=True,exist_ok=True)
        file.write_bytes((ROOT/path).read_bytes())
        locked[path]=row['expected']
    changes=['scripts/coe_startup_storage.py','scripts/coe_delivery_reuse.py','scripts/coe_storage_binding.py',
             'scripts/run_coe_candidate_pilot.ps1']
    for path in changes:
        data=(ROOT/path).read_bytes();file=code/path;file.parent.mkdir(parents=True,exist_ok=True);file.write_bytes(data)
        locked[path]=[dict(representation='EXACT_COMMITTED_OPERATIONAL_BYTES',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())]
    root=tmp_path/'YLQ'
    (root/'logs/coe_4f1c3b55caf3_static').mkdir(parents=True)
    (root/'logs/coe_4f1c3b55caf3_static/receipt.json').write_bytes(receipt)
    for name in ('transfer','logs','evidence/coe_pilot'): (root/name).mkdir(parents=True,exist_ok=True)
    pack=tmp_path/'delivery';pack.mkdir()
    shutil.copyfile(archive,pack/archive.name)
    compatibility=dict(schema_version='coe-component-reuse/0.1.0',baseline_commit=old['commit'],
        execution_commit=COMMIT,analysis_commit=COMMIT,
        unchanged_sources={r['path']:r['expected'] for r in source},
        allowed_operational_changes=changes,scope='ALL_311_PREVIOUSLY_CHECKED_SOURCE_PATHS_UNCHANGED')
    write(pack/'component_compatibility.json',compatibility)
    (pack/'execution.bundle').write_bytes(b'CPU_GIT_PROCESS_BOUNDARY_NOT_A_BUNDLE')
    cfg=dict(old,commit=COMMIT,analysis_commit=COMMIT,prerequisite=old['commit'],
        server_root=str(root),code_root=str(code),stage_a_only=False,
        operational_revision='coe-startup-resources/0.1.0',batch_id='cpu-resources-nine',
        source_representations=locked,bundle='execution.bundle',bundle_bytes=34,
        bundle_sha256=sha(pack/'execution.bundle'),
        reuse_static_archive=archive.name,component_compatibility='component_compatibility.json',
        component_compatibility_sha256=sha(pack/'component_compatibility.json'))
    cfg['launcher_sha256']=sha(code/'scripts/run_coe_candidate_pilot.ps1')
    (pack/'cpu-not-collector.bin').write_bytes(b'NOT_A_COLLECTOR')
    cfg.update(nsys=str(pack/'cpu-not-collector.bin'),nsys_sha256=sha(pack/'cpu-not-collector.bin'))
    for name in ('prompt_512.json','model_sha256.csv'):(pack/name).write_bytes(b'CPU_BOUNDARY_NOT_MODEL_INPUT')
    cfg['bundle_bytes']=(pack/'execution.bundle').stat().st_size
    write(pack/'delivery.json',cfg)
    # New catalog is observed bytes, checked against PRE-EXISTING expected forms.
    catalog=[dict(path=p,actual_bytes=(code/p).stat().st_size,actual_sha256=sha(code/p),
                  expected=forms,matched=any(sha(code/p)==f['sha256'] for f in forms)) for p,forms in locked.items()]
    return dict(root=root,code=code,pack=pack,cfg=cfg,catalog=catalog,old_paths=old_paths)


@pytest.mark.parametrize('damage,reason',[(None,None),('receipt','OLD_RECEIPT_CHANGED'),
    ('source','REUSED_COMPONENT_CONFLICT'),('plan','COMPATIBILITY_SCOPE'),('target','COMPATIBILITY_TARGET'),
    ('contract','REUSED_EXECUTION_CONTRACT_CONFLICT')])
def test_actual_reference_reuse_cannot_certify_new_launcher_as_old(prepared,damage,reason):
    from scripts import coe_delivery_reuse as m
    f=prepared;cfg=f['cfg'];table=f['catalog']
    if damage=='receipt':(f['root']/'logs/coe_4f1c3b55caf3_static/receipt.json').write_bytes(b'changed')
    elif damage=='contract':cfg['plan_sha256']='0'*64
    elif damage=='source':next(r for r in table if r['path']=='analysis/coe_candidate.py')['actual_sha256']='0'*64
    elif damage in ('plan','target'):
        p=f['pack']/'component_compatibility.json';v=json.loads(p.read_text())
        if damage=='plan':v['unchanged_sources'].pop('analysis/coe_candidate.py')
        else:v['execution_commit']='b'*40
        write(p,v);cfg['component_compatibility_sha256']=sha(p)
    if reason:
        with pytest.raises(ValueError) as error:m.verify(cfg,f['pack'],table)
        assert str(error.value)==reason
    else:
        r=m.verify(cfg,f['pack'],table)
        assert r['status']=='COMPONENT_REUSE_VERIFIED' and r['unchanged_source_count']==311
        assert r['historical_static_status']=='BLOCKED_UNCHANGED'
        assert 'scripts/run_coe_candidate_pilot.ps1' in r['new_operational_paths']
        assert r['new_launcher_equals_old_executed_required'] is False


def manifest(folder):
    files=sorted(p for p in folder.iterdir() if p.is_file() and p.name!='artifact_sha256.csv')
    with (folder/'artifact_sha256.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=['path','bytes','sha256']);w.writeheader()
        for p in files:w.writerow(dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)))


def launch(f,scenario='ok',collect=False,reviewed=None):
    launcher=f['pack']/'run_coe_candidate_pilot.ps1'
    shutil.copyfile(ROOT/'scripts/run_coe_candidate_pilot.ps1',launcher)
    manifest(f['pack'])
    env=dict(os.environ,COE_TEST_LOCAL_PYTHON=sys.executable,COE_TEST_SCENARIO=scenario,
             COE_TEST_REVIEWED=reviewed or '',COE_TEST_COLLECT='1' if collect else '0',
             COE_TEST_LAUNCHER=str(launcher),PYTHONPATH=str(ROOT))
    return subprocess.run(['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',
                           str(ROOT/'tests/coe_launcher_boundary.ps1')],env=env,capture_output=True,timeout=90)


@pytest.mark.parametrize('scenario,reason',[('ok',None),('low','FREE_SPACE_INSUFFICIENT'),
    ('query','FREE_SPACE_UNKNOWN'),('write','PATH_NOT_WRITABLE'),('existing','No overwrite'),
    ('receipt','OLD_RECEIPT_CHANGED'),('source','Source conflict')])
def test_real_default_launcher_only_deploys_and_checks_changed_wiring(prepared,scenario,reason):
    if os.name!='nt':pytest.skip('real Windows PowerShell 5.1 launcher only')
    f=prepared
    if scenario=='receipt':(f['root']/'logs/coe_4f1c3b55caf3_static/receipt.json').write_bytes(b'changed')
    elif scenario=='source':(f['code']/'analysis/coe_candidate.py').write_bytes(b'changed')
    elif scenario=='existing':(f['root']/('logs/coe_'+COMMIT[:12]+'_static')).mkdir()
    p=launch(f,scenario)
    output=p.stdout+p.stderr
    if reason:assert p.returncode!=0 and reason.encode() in output,output.decode(errors='replace')
    else:
        assert p.returncode==0,output.decode(errors='replace')
        path=f['root']/('logs/coe_'+COMMIT[:12]+'_static/receipt.json')
        r=json.loads(path.read_text(encoding='utf-8-sig'))
        assert r['status']=='STATIC_READY_FOR_REVIEW' and r['execution_commit']==COMMIT
        assert r['reused_cpu_count']==110 and r['historical_ylq_total_bytes'] is None
        assert not (f['root']/'collector_was_called').exists()


@pytest.mark.parametrize('review', ['actual','wrong','missing','historical','fresh_space_low'])
def test_real_explicit_collect_dispatch_requires_actual_new_a_receipt(prepared,review):
    if os.name!='nt':pytest.skip('real Windows PowerShell 5.1 launcher only')
    f=prepared;p=launch(f)
    assert p.returncode==0,(p.stdout+p.stderr).decode(errors='replace')
    static=f['root']/('logs/coe_'+COMMIT[:12]+'_static/receipt.json')
    value=sha(static) if review in ('actual','fresh_space_low') else '0'*64 if review=='wrong' else '988de2ec87d9c427e2a5c76a6d33b3f2ea798f2adc88f6e752977570c12bc0b5' if review=='historical' else None
    p=launch(f,scenario='low' if review=='fresh_space_low' else 'ok',collect=True,reviewed=value)
    if review=='actual':
        assert p.returncode==0,(p.stdout+p.stderr).decode(errors='replace')
        assert (f['root']/'collector_was_called').read_text()=='CPU_BOUNDARY_ONLY'
        r=json.loads((f['root']/'evidence/coe_pilot/cpu-resources-nine/receipt.json').read_text(encoding='utf-8-sig'))
        assert r['status']=='FIXED_NINE_COMPLETE_STOP_FOR_REVIEW'
    elif review=='fresh_space_low':
        assert p.returncode!=0 and b'FREE_SPACE_INSUFFICIENT' in p.stdout
        assert not (f['root']/'collector_was_called').exists()
    else:
        assert p.returncode!=0 and b'Explicit reviewed Stage A receipt hash required' in p.stderr
        assert not (f['root']/'collector_was_called').exists()
