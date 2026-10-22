"""Real sealed receipts/dispatch; target paths, Git and free-space are CPU doubles.

No checked_a/checked_event/receipt validator is replaced. No DLL is loaded.
The missing local CUDART binary alone uses its sealed file-fact reference.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import stat
import subprocess
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[1]
TRANSFER=ROOT/'.local/transfer'
NATIVE='6c744bf52daff3fc54571e264a0c34e3207aa1df'
SOURCES=(
    ('cupti_input_4ea08bb33684_static.zip','726aaca8707be4bc8421ca79bb054d8f1d0693badc2fbac4066f7008fcf1e775'),
    ('cupti_input_4ea08bb33684_delivery.zip','337f539b85801583495997fac87a2af173bd5a822186cfade05dbf6cd5a5f7a9'),
    ('cupti_timeline_6c744bf52daf_static.zip','894d3636653d4ef30603bd0e279110ef6e18727db7e0fa8343f6989827c5ebdb'),
    ('cupti_event_38baca449d2f_once.zip','1b30ac79fa3e4dd0ee6776ab3e95d380f273fff97a13ed2a07052612dc66e5ed'))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def put(path,value):Path(path).write_text(json.dumps(value),encoding='utf8')
def read(path):return json.loads(Path(path).read_bytes())


def load(path):
    spec=importlib.util.spec_from_file_location('_real_ref_'+Path(path).stem,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


@pytest.fixture(scope='module')
def sealed(tmp_path_factory):
    root=tmp_path_factory.mktemp('real_receipts')
    for (name,digest),folder in zip(SOURCES,('failure','package','a','event')):
        source=TRANSFER/name
        if not source.is_file():pytest.skip('Optional sealed-original CPU audit: local archive unavailable: '+name)
        assert sha(source)==digest
        target=root/folder;target.mkdir()
        with zipfile.ZipFile(source) as z:
            names=z.namelist();assert z.testzip() is None and len(names)==len({n.casefold() for n in names})
            for info in z.infolist():
                p=PurePosixPath(info.filename)
                assert not p.is_absolute() and '..' not in p.parts and ':' not in info.filename
                assert '\\' not in info.filename and not stat.S_ISLNK(info.external_attr>>16)
            index='package_manifest.json' if folder=='package' else 'artifact_manifest.json'
            rows=json.loads(z.read(index))['files']
            assert len(rows)==len({r['path'].casefold() for r in rows})
            assert set(names)=={r['path'] for r in rows}|{index}
            for r in rows:
                blob=z.read(r['path']);assert len(blob)==r['bytes'] and hashlib.sha256(blob).hexdigest()==r['sha256']
            z.extractall(target)
    failed=read(root/'failure/receipt.json')
    assert failed['error']=='ValueError:CUPTI_TIMELINE_B_A_RECEIPT'
    assert failed['actual_model_processes']==failed['actual_cupti_sessions']==0
    assert read(root/'failure/delivery.json')==read(root/'package/delivery.json')
    assert sha(root/'a/receipt.json')=='9d6d4000d07ea7d752c78f4d337f88fe35085e99995ee88242eae5a824ad971e'
    assert sha(root/'event/receipt.json')=='824183fcea1e4ca5d0f3423cfedf6fb791379bc80a4f3dd47318854a0fac0ed9'
    # Recover the *byte-identical* source snapshot from native Git content and
    # the original byte index, not from this worktree or an arbitrary hash.
    rows=read(root/'a/source_bytes.json')
    queries=''.join(NATIVE+':'+r['path']+'\n' for r in rows).encode()
    result=subprocess.check_output(['git','cat-file','--batch'],input=queries,cwd=ROOT)
    offset=0
    for r in rows:
        end=result.index(b'\n',offset);header=result[offset:end].split();assert header[1]==b'blob'
        size=int(header[2]);blob=result[end+1:end+1+size];offset=end+size+2
        choices=(blob,blob.replace(b'\r\n',b'\n').replace(b'\n',b'\r\n'))
        matches=[v for v in choices if len(v)==r['bytes'] and hashlib.sha256(v).hexdigest()==r['sha256']]
        assert matches,r['path']
        p=root/'code'/r['path'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(matches[0])
    assert offset==len(result)
    return root


@pytest.fixture
def scene(sealed,tmp_path,monkeypatch):
    for name in ('package','a','event','code'):shutil.copytree(sealed/name,tmp_path/name)
    package=tmp_path/'package';cfg=read(package/'delivery.json')
    pilot=load(ROOT/'scripts/cupti_input_pilot.py');b=load(ROOT/'scripts/cupti_timeline_b.py')
    stage,m=b.components(package);event=b.event_control();original_safe=m.safe
    # File-system relocation ONLY. Original receipt/config/manifest bytes stay
    # unchanged, including their server paths and expected hashes.
    pairs=[(Path(cfg['a_root']),tmp_path/'a'),(Path(cfg['event_root']),tmp_path/'event'),
        (Path(cfg['code_root']),tmp_path/'code'),(Path(cfg['server_root']),tmp_path/'YLQ')]
    def local(path):
        p=Path(path)
        for old,new in pairs:
            if p==old or p.is_relative_to(old):return new/p.relative_to(old)
        return p
    for module in (pilot,b,event):monkeypatch.setattr(module,'Path',local)
    monkeypatch.setattr(m,'safe',lambda root,relative:original_safe(local(root),relative))
    checks=[]
    def tree(acfg,head):
        assert head==acfg['execution_commit']==NATIVE
        checks.append('CPU_TARGET_HEAD_CLEAN_DOUBLE')
    monkeypatch.setattr(m,'tree',tree)
    stage['bind_checkout_modules']=lambda c:checks.append('CPU_TARGET_IMPORT_BOUNDARY_DOUBLE')
    stage['startup_resources']=lambda *a:dict(mode='CPU_FRESH_SPACE_DOUBLE',historical_ylq_total_bytes=None)
    monkeypatch.setattr(pilot,'check_runtime',lambda c:dict(mode='CPU_TARGET_PYTHON_DOUBLE'))
    # CUDART bytes are not included in the old A archive. Do not claim a real
    # local vendor-file check; its expected fact is independently fixed below.
    runtime=local(cfg['runtime']['path']);runtime.parent.mkdir(parents=True,exist_ok=True)
    runtime.write_bytes(b'\0'*553984)
    original_event_sha=event.sha
    def event_sha(p):
        if local(p)==runtime:return 'f95273031fc5ea44cdb37e0a696a1b15b9d84a4ee977299a6f6e652ef4d790cf'
        return original_event_sha(p)
    monkeypatch.setattr(event,'sha',event_sha)
    monkeypatch.setattr(b,'event_control',lambda:event)
    monkeypatch.setattr(b,'components',lambda p:(stage,m))
    monkeypatch.setattr(pilot,'control',lambda:b)
    for key in ('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH'):
        monkeypatch.delenv(key,raising=False)
    return pilot,b,stage,m,cfg,package,tmp_path,checks


def reseal_package(package):
    put(package/'package_manifest.json',dict(files=[dict(path=p.relative_to(package).as_posix(),
        bytes=p.stat().st_size,sha256=sha(p)) for p in package.rglob('*') if p.is_file() and p.name!='package_manifest.json']))


def test_full_static_entry_dispatches_batch_to_real_native_A_and_event(scene):
    pilot,b,stage,m,c,package,root,checks=scene
    assert pilot.main(['--package',str(package)])==0
    out,archive=pilot.locations(c,m,'A');r=read(out/'receipt.json')
    assert r['status']=='STATIC_READY_FOR_REVIEW' and r['error'] is None
    assert r['verification']['native_commit']==NATIVE
    assert r['verification']['a_receipt_sha256']=='9d6d4000d07ea7d752c78f4d337f88fe35085e99995ee88242eae5a824ad971e'
    assert r['verification']['event_reference']['status']=='EVENT_LINK_COMPLETE_PENDING_REVIEW'
    assert r['actual_model_processes']==r['actual_cupti_sessions']==0 and r['B_authorized'] is False
    assert checks==['CPU_TARGET_HEAD_CLEAN_DOUBLE','CPU_TARGET_IMPORT_BOUNDARY_DOUBLE']
    assert archive.is_file() and len(list((out/'compile').glob('*.pyc')))==len(c['cpu_sources'])


@pytest.mark.parametrize('damage,reason',[
    ('batch_version','CUPTI_INPUT_CONFIGURATION'),('a_hash','CUPTI_EVENT_B_A_HASH:receipt.json'),
    ('a_version','CUPTI_EVENT_B_A_RECEIPT'),('event_hash','CUPTI_TIMELINE_B_EVENT_REFERENCE_HASH'),
    ('event_version','CUPTI_TIMELINE_B_EVENT_REFERENCE'),('source','MEMSET_MICRO_FILE_HASH')])
def test_real_static_receipts_keep_specific_version_hash_and_source_rejections(scene,damage,reason):
    pilot,b,stage,m,c,package,root,checks=scene
    if damage=='batch_version':c['schema_version']='CUPTI-INPUT-PILOT/unknown'
    if damage=='a_hash':(root/'a/receipt.json').write_bytes((root/'a/receipt.json').read_bytes()+b' ')
    if damage=='a_version':
        r=read(root/'a/receipt.json');r['schema_version']='cupti-timeline-stage-a-receipt/0.1.0'
        put(root/'a/receipt.json',r);c['reviewed_a_receipt_sha256']=sha(root/'a/receipt.json')
    if damage=='event_hash':(root/'event/receipt.json').write_bytes((root/'event/receipt.json').read_bytes()+b' ')
    if damage=='event_version':
        r=read(root/'event/receipt.json');r['schema_version']='cupti-event-b-receipt/unknown'
        put(root/'event/receipt.json',r);c['reviewed_event_receipt_sha256']=sha(root/'event/receipt.json')
        index=read(root/'event/artifact_manifest.json')
        for row in index['files']:
            if row['path']=='receipt.json':row.update(bytes=(root/'event/receipt.json').stat().st_size,sha256=c['reviewed_event_receipt_sha256'])
        put(root/'event/artifact_manifest.json',index);c['event_manifest_sha256']=sha(root/'event/artifact_manifest.json')
    if damage=='source':(root/'code/analysis/accounting_utils.py').write_bytes(b'# altered\n')
    put(package/'delivery.json',c);reseal_package(package)
    if damage=='batch_version':
        with pytest.raises(ValueError,match=reason):pilot.main(['--package',str(package)])
    else:
        assert pilot.main(['--package',str(package)])==2
        out,_=pilot.locations(c,m,'A');receipt=read(out/'receipt.json')
        assert reason in receipt['error']
        assert receipt['actual_model_processes']==receipt['actual_cupti_sessions']==0


@pytest.mark.parametrize('version',['CUPTI-INPUT-PILOT/0.1.0','cupti-timeline-stage-b/unknown'])
def test_single_run_reference_verifier_rejects_batch_and_unknown_contracts(scene,version):
    pilot,b,stage,m,c,package,root,checks=scene
    one=pilot.one_configuration(c,c['slots'][0]);one['schema_version']=version
    with pytest.raises(ValueError,match='REFERENCE_CONTRACT_VERSION'):b.checked_a(one,stage,m)
    assert checks==[]


@pytest.mark.parametrize('change_after_child',[False,True])
def test_B_per_run_and_finally_recheck_use_real_receipts_not_batch(scene,monkeypatch,change_after_child):
    pilot,b,stage,m,c,package,root,checks=scene
    assert pilot.static(package)==0
    static,_=pilot.locations(c,m,'A');commands=[]
    def command(argv,cwd,log,**kw):
        # No target program executes; fail at the sole external child boundary.
        commands.append(Path(log).name)
        assert Path(log).name=='one_model'
        m.write(Path(log).with_suffix('.process.json'),dict(pid=7,status='EXITED',exit_code=2,timed_out=False))
        if change_after_child:(root/'a/receipt.json').write_bytes((root/'a/receipt.json').read_bytes()+b' ')
        raise ValueError('CPU_MODEL_BOUNDARY_STOP_NO_CUDA')
    monkeypatch.setattr(m,'command',command)
    assert pilot.run(package,enabled=True,reviewed=c['reviewed_a_receipt_sha256'],
        reviewed_event=c['reviewed_event_receipt_sha256'],reviewed_static=sha(static/'receipt.json'))==2
    out,_=pilot.locations(c,m,'B');r=read(out/'receipt.json')
    assert commands==['one_model'] and [s['status'] for s in r['slots']]==['BLOCKED']+['NOT_RUN']*8
    single=read(out/'runs'/c['slots'][0]['run_id']/'receipt.json')
    assert single['operation_error']=='ValueError:CPU_MODEL_BOUNDARY_STOP_NO_CUDA'
    assert single['post_execution_static_rechecked'] is (not change_after_child)
    if change_after_child:assert 'CUPTI_EVENT_B_A_HASH:receipt.json' in single['postcheck_error']
    else:
        assert single['postcheck_error'] is None
        assert len(checks)==6  # real native reference checks: A, run pre, run finally
