"""New publication-control boundaries only; sealed receipts are real bytes."""
import base64
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import zipfile

import pytest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
NEW='f'*40


def load(path,name):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def reviewed_source(name):
    import os
    packet=os.environ.get('BATCH_REPAIR_REVIEWED_PACKAGE')
    return Path(packet)/name if packet else ROOT/'scripts'/name


def repair():return load(reviewed_source('cupti_batch_publication_repair.py'),'repair_test')
def api():return load(reviewed_source('cupti_batch_once_delivery.py'),'once_api_test')


def extract(zpath,out):
    out.mkdir()
    with zipfile.ZipFile(zpath) as z:
        assert z.testzip() is None
        for n in z.namelist():
            p=PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts and '\\' not in n
            target=out/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(n))


@pytest.fixture(scope='module')
def sealed(tmp_path_factory):
    root=tmp_path_factory.mktemp('sealed')
    transfer=ROOT/'.local/transfer'
    package=root/'parent_delivery';extract(transfer/'coe_batch_e358d37f0bcd_delivery.zip',package)
    old=root/'old';extract(transfer/'coe_batch_L512B2_e358d37f0bcd_once.zip',old)
    return dict(root=old,parent_package=package,
        static_zip=transfer/'coe_batch_L512B2_e358d37f0bcd_static.zip',
        once_zip=transfer/'coe_batch_L512B2_e358d37f0bcd_once.zip',
        package_zip=transfer/'coe_batch_e358d37f0bcd_delivery.zip')


def config(paths):
    c=json.loads((paths['parent_package']/'delivery.json').read_bytes())
    c.update(delivery_control_commit=NEW,repair_profile=repair().profile())
    return c


def support():return load(ROOT/'scripts/memset_micro.py','repair_support')


def test_real_A_publication_and_failed_B_are_accepted_without_any_network(sealed,monkeypatch):
    m=repair()
    def forbidden(*args,**kw):raise AssertionError('NETWORK_OR_SUBPROCESS_MUST_NOT_RUN')
    monkeypatch.setattr(subprocess,'run',forbidden)
    monkeypatch.setattr(subprocess,'Popen',forbidden)
    s=support();monkeypatch.setattr(s,'command',forbidden)
    v=m.checked_parent(config(sealed),s,api(),paths=sealed)
    assert v['historical_publication']['remote_main']=='4f2ffc769ac3a42bf08886c3cda09bccde067206'
    assert v['parent_A_receipt_sha256']=='d17423afd2422c7843564777f7603d034ff8ed4f03403682a1222592f73d7e16'
    assert v['prior_actual_model_processes']==0 and v['prior_actual_cupti_sessions_original'] is None
    assert v['prior_model_dispatch_reached'] is False
    assert v['old_network_failure_preserved'] is True
    assert v['historical_A_is_not_new_control_publication'] is True


@pytest.mark.parametrize('damage,reason',[('a_receipt','A_RECEIPT_HASH'),('a_missing','A_ARTIFACT_MISSING'),
    ('a_source_tamper','A_ARTIFACT_HASH'),('delivery','PARENT_PACKAGE_BYTES'),('old_attempt','FAILED_ARTIFACT_HASH')])
def test_real_evidence_damage_is_rejected_for_the_expected_reason(sealed,tmp_path,damage,reason):
    paths=dict(sealed)
    for key in ('root','parent_package'):
        target=tmp_path/key;shutil.copytree(paths[key],target);paths[key]=target
    if damage=='a_receipt':(paths['root']/'prepare/receipt.json').write_bytes(b'{}')
    if damage=='a_missing':(paths['root']/'prepare/published_source_1.stdout').unlink()
    if damage=='a_source_tamper':(paths['root']/'prepare/published_source_1.stdout').write_bytes(b'changed')
    if damage=='delivery':(paths['parent_package']/'input_512_B2.json').write_bytes(b'[]')
    if damage=='old_attempt':(paths['root']/'once/control_receipt.json').write_bytes(b'{}')
    with pytest.raises(ValueError,match='BATCH_REPAIR_'+reason):
        repair().checked_parent(config(sealed),support(),api(),paths=paths)


def test_changed_science_or_input_is_not_hidden_by_old_A(sealed):
    c=config(sealed);c['consumer_version']='submit-effect-bridge/0.3.2'
    with pytest.raises(ValueError,match='BATCH_REPAIR_PARENT_CONFIG_CHANGED'):
        repair().checked_parent(c,support(),api(),paths=sealed)


def test_legacy_network_failure_stays_failure_for_sealed_and_current_control(sealed,tmp_path,monkeypatch):
    from types import SimpleNamespace
    c=json.loads((sealed['parent_package']/'delivery.json').read_bytes())
    c.update(git=shutil.which('git'),code_root=str(ROOT))
    for i,m in enumerate((load(sealed['parent_package']/'cupti_batch_once_delivery.py','sealed_legacy'),api())):
        temp=tmp_path/str(i);temp.mkdir();monkeypatch.setenv('TEMP',str(temp))
        calls=[]
        def offline(argv,*args,**kwargs):
            calls.append(argv);assert argv[1]=='ls-remote'
            raise ValueError('MEMSET_MICRO_COMMAND_EXIT:published_main:128')
        with pytest.raises(ValueError,match='COMMAND_EXIT:published_main:128'):
            m.check_publication(c,temp,SimpleNamespace(command=offline))
        assert len(calls)==1


def release_flags(commit=NEW):
    # Explicit CPU receipt fixture, NOT a claim of actual remote publication.
    r=dict(schema_version='exposedpath-publication-receipt/0.1.0',status='PUBLISHED_REMOTE_REF_VERIFIED',
        repository='YLQQQQ/A-exposed-model-of-LLM-inference',ref='refs/heads/main',
        base='4f2ffc769ac3a42bf08886c3cda09bccde067206',target=commit,remote_after=commit,
        force_used=False,commits=[commit],
        validation_scope='CPU_SYNTHETIC_PUBLICATION_RECEIPT_NOT_REMOTE_FACT')
    raw=json.dumps(r,separators=(',',':')).encode()
    return dict(reviewed_control_publication=base64.b64encode(raw).decode(),
        reviewed_control_publication_sha256=hashlib.sha256(raw).hexdigest())


def test_new_control_has_separate_exact_reviewed_publication_identity(sealed):
    v=repair().check_release_evidence(config(sealed),release_flags())
    assert v['new_control_commit']==NEW
    assert v['basis']=='EXTERNALLY_REVIEWED_PUBLICATION_RECEIPT'
    assert v['server_network_used'] is False


@pytest.mark.parametrize('damage,reason',[('missing','NEW_CONTROL_PUBLICATION_REQUIRED'),
    ('bad_hash','NEW_CONTROL_PUBLICATION_HASH'),('old_control','NEW_CONTROL_PUBLICATION_TARGET')])
def test_old_A_or_unknown_release_cannot_authorize_new_control(sealed,damage,reason):
    flags=release_flags()
    if damage=='missing':flags={}
    if damage=='bad_hash':flags['reviewed_control_publication_sha256']='0'*64
    if damage=='old_control':flags=release_flags('e358d37f0bcd1b07c4de7a882fabc4d7788f905c')
    with pytest.raises(ValueError,match='BATCH_REPAIR_'+reason):
        repair().check_release_evidence(config(sealed),flags)


def builder():return load(ROOT/'scripts/build_cupti_batch_once_delivery.py','repair_builder')


@pytest.fixture(scope='module')
def control_bundle(tmp_path_factory):
    root=tmp_path_factory.mktemp('cb');repo=root/'repo'
    subprocess.run(['git','clone','--shared','--no-checkout','-q',str(ROOT),str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'-c','core.autocrlf=false','checkout','--detach',api().SCIENCE],check=True,capture_output=True)
    import os
    reviewed=os.environ.get('BATCH_REPAIR_REVIEWED_PACKAGE')
    if reviewed:
        p=Path(reviewed);c=json.loads((p/'delivery.json').read_bytes())
        return dict(repo=repo,commit=c['delivery_control_commit'],bundle=p/'repair.bundle')
    env=dict(__import__('os').environ,GIT_INDEX_FILE=str(root/'separate-index'),GIT_AUTHOR_NAME='CPU fixture',
        GIT_AUTHOR_EMAIL='cpu@example.invalid',GIT_COMMITTER_NAME='CPU fixture',GIT_COMMITTER_EMAIL='cpu@example.invalid')
    def git(*args,input=None):
        return subprocess.run(['git','-C',str(repo),*args],env=env,input=input,check=True,capture_output=True).stdout.strip()
    git('read-tree',repair().PUBLISHED)
    files=dict(builder().CONTROL_FILES);files['cupti_batch_publication_repair.py']='scripts/cupti_batch_publication_repair.py'
    for path in files.values():
        oid=git('hash-object','-w','--stdin',input=(ROOT/path).read_bytes()).decode()
        git('update-index','--add','--cacheinfo','100644,'+oid+','+path)
    tree=git('write-tree').decode();commit=git('commit-tree',tree,'-p',repair().PUBLISHED,input=b'CPU repair identity\n').decode()
    git('update-ref','refs/heads/main',commit)
    bundle=root/'control.bundle';git('bundle','create',str(bundle),'refs/heads/main','^'+api().SCIENCE)
    return dict(repo=repo,commit=commit,bundle=bundle)


@pytest.fixture
def packet(control_bundle,tmp_path):
    import os
    reviewed=os.environ.get('BATCH_REPAIR_REVIEWED_PACKAGE')
    if reviewed:
        out=tmp_path/'packet';shutil.copytree(reviewed,out);return out
    def source(commit,path):
        return subprocess.run(['git','-C',str(control_bundle['repo']),'cat-file','blob',commit+':'+path],check=True,capture_output=True).stdout
    out=tmp_path/'packet'
    builder().build_repair_package(out,control_bundle['commit'],source=source,bundle_bytes=control_bundle['bundle'].read_bytes())
    return out


def test_real_repair_packet_preserves_all_science_and_rejects_prepare(packet):
    m=api();c,one,b,stage,s=m.configuration(packet)
    assert c['consumer_version']=='submit-effect-bridge/0.3.0' and c['analysis_commit']==m.SCIENCE
    assert len(c['slots'])==1 and one['model_contract']['batch_size']==2
    assert m.locations(c)['root'].name.endswith('_repair1')
    with zipfile.ZipFile(ROOT/'.local/transfer/coe_batch_e358d37f0bcd_delivery.zip') as z:
        old=json.loads(z.read('science_lock.json'))
        for row in old['package_science']:
            assert (packet/row['path']).read_bytes()==z.read(row['path'])
    with pytest.raises(ValueError,match='BATCH_ONCE_REPAIR_NO_A_REPLAY'):
        m.run(packet,'prepare',dict(approve_prepare=True,operator_reference='CPU'))


def test_real_bundle_checks_control_bytes_without_remote_access(packet,control_bundle,tmp_path,monkeypatch):
    m=api();c,one,b,stage,s=m.configuration(packet)
    c.update(git=shutil.which('git'),code_root=str(control_bundle['repo']))
    temp=tmp_path/'temp';temp.mkdir();monkeypatch.setenv('TEMP',str(temp))
    out=tmp_path/'logs';out.mkdir();original=s.command
    def command(argv,*args,**kwargs):
        assert 'ls-remote' not in argv and not any(str(x).startswith('https://') for x in argv)
        return original(argv,*args,**kwargs)
    s.command=command
    v=repair().verify_control_bundle(c,out,s)
    assert v['control_commit']==control_bundle['commit'] and v['source_count']==5 and v['network_used'] is False
    assert not (control_bundle['repo']/'.git/FETCH_HEAD').exists()


def test_bundle_identity_conflict_is_not_self_certified(packet,control_bundle,tmp_path):
    m=api();c,one,b,stage,s=m.configuration(packet);c['repair_bundle']['sha256']='0'*64
    with pytest.raises(ValueError,match='BATCH_REPAIR_CONTROL_BUNDLE_IDENTITY'):
        repair().verify_control_bundle(c,tmp_path,s)


def test_new_delivery_cannot_change_input_under_the_old_A(sealed,packet):
    m=api();c=m.configuration(packet)[0]
    (packet/'input_512_B2.json').write_bytes(b'[]')
    with pytest.raises(ValueError,match='BATCH_REPAIR_UNCHANGED_COMPONENT:input_512_B2.json'):
        repair().checked_parent(c,support(),m,paths=sealed)


def test_valid_bundle_does_not_authenticate_a_different_control_file(packet,control_bundle,tmp_path,monkeypatch):
    m=api();c,one,b,stage,s=m.configuration(packet)
    c.update(git=shutil.which('git'),code_root=str(control_bundle['repo']))
    p=packet/'cupti_batch_once_delivery.py';p.write_bytes(p.read_bytes()+b'\n# altered control\n')
    temp=tmp_path/'temp';temp.mkdir();monkeypatch.setenv('TEMP',str(temp))
    out=tmp_path/'logs';out.mkdir()
    with pytest.raises(ValueError,match='BATCH_REPAIR_CONTROL_SOURCE_BYTES'):
        repair().verify_control_bundle(c,out,s)


def test_unlisted_model_artifact_prevents_reusing_prior_zero_budget(sealed,tmp_path):
    paths=dict(sealed);paths['root']=tmp_path/'old';shutil.copytree(sealed['root'],paths['root'])
    (paths['root']/'once/one_model.process.json').write_bytes(b'{"pid":123}')
    with pytest.raises(ValueError,match='BATCH_REPAIR_FAILED_COVERAGE'):
        repair().checked_parent(config(sealed),support(),api(),paths=paths)


def target_scene(packet,control_bundle,sealed,tmp_path,monkeypatch,mode):
    """Only filesystem/interpreter/GPU/model execution is externally doubled."""
    m=api();server=tmp_path/'YLQ';transfer=server/'transfer';transfer.mkdir(parents=True)
    old=transfer/'coe_batch_L512B2_e358d37f0bcd';shutil.copytree(sealed['root'],old)
    shutil.copytree(sealed['parent_package'],transfer/'coe_batch_e358d37f0bcd_delivery')
    for key,name in [('static_zip','coe_batch_L512B2_e358d37f0bcd_static.zip'),
        ('once_zip','coe_batch_L512B2_e358d37f0bcd_once.zip'),('package_zip','coe_batch_e358d37f0bcd_delivery.zip')]:
        shutil.copyfile(sealed[key],transfer/name)
    a=tmp_path/'native_a';e=tmp_path/'event'
    extract(ROOT/'.local/transfer/cupti_timeline_6c744bf52daf_static.zip',a)
    extract(ROOT/'.local/transfer/cupti_event_38baca449d2f_once.zip',e)
    model=tmp_path/'weights';model.mkdir();(model/'config.json').write_bytes((packet/'model_config_reference.json').read_bytes())
    monkeypatch.setattr(m,'target_environment',lambda c:dict(source='HOST_INTERPRETER_DOUBLE_NOT_TARGET'))
    monkeypatch.setattr(m,'observe_asset',lambda fact:dict(fact))
    resource_calls=[]
    def resources(*args):
        resource_calls.append(args);return dict(status='STARTUP_RESOURCES_READY',scope='CPU_VOLUME_DOUBLE_NOT_TARGET')
    monkeypatch.setattr(m,'startup_resources',resources)
    native_which=shutil.which
    monkeypatch.setattr(m.shutil,'which',lambda n:'CPU-SMI' if n=='nvidia-smi.exe' else native_which(n))
    original_config=m.configuration;calls=[]
    def configuration(p):
        c,one,b,stage,s=original_config(p)
        relocation=dict(code_root=str(control_bundle['repo']),server_root=str(server),git=native_which('git'),
            python=sys.executable,target_python=sys.executable,model=str(model),a_root=str(a),event_root=str(e))
        c.update(relocation);one.update(relocation)
        real=s.command
        def command(argv,cwd,log,**kw):
            assert 'ls-remote' not in argv and not any(str(x).startswith('https://') for x in argv)
            if argv[0]=='CPU-SMI':
                r=c['gpu_reference'];free=8191 if mode=='low_gpu' else 8192
                text=(f'3, {c["gpu_uuid"]}, {c["gpu_pci"]}, {r["name"]}, {r["driver_version"]}, {r["total_mib"]}, {free}\n'
                    if Path(log).name=='gpu' else 'N/A\n')
                return real([sys.executable,'-I','-S','-c','print('+repr(text)+',end="")'],cwd,log,**kw)
            if Path(log).name=='one_model':
                assert mode=='exit7' and kw['timeout']==300;calls.append(argv)
                return real([sys.executable,'-I','-S','-c','raise SystemExit(7)'],cwd,log,**kw)
            assert Path(log).name!='same_run_analysis'
            return real(argv,cwd,log,**kw)
        s.command=command;return c,one,b,stage,s
    monkeypatch.setattr(m,'configuration',configuration)
    flags=dict(approve_model=True,shared_use_approved=True,reviewed_prepare_sha256=repair().PREPARE,
        operator_reference='CPU_REPAIR_EXECUTION',**release_flags(control_bundle['commit']))
    if mode=='missing_release':flags.pop('reviewed_control_publication')
    return m,flags,calls,resource_calls,old


@pytest.mark.parametrize('mode,reason,model_starts',[('exit7','COMMAND_EXIT:one_model:7',1),
    ('low_gpu','GPU_FREE_RESERVE',0),('missing_release','NEW_CONTROL_PUBLICATION_REQUIRED',0)])
def test_actual_repair_entry_keeps_fresh_gates_exact_failures_and_old_evidence(packet,control_bundle,sealed,tmp_path,monkeypatch,mode,reason,model_starts):
    m,flags,calls,resources,old=target_scene(packet,control_bundle,sealed,tmp_path,monkeypatch,mode)
    original_hash=hashlib.sha256((old/'once/control_receipt.json').read_bytes()).hexdigest()
    assert m.run(packet,'execute',flags)==2
    c=m.configuration(packet)[0];paths=m.locations(c)
    r=json.loads((paths['root']/'once/control_receipt.json').read_bytes())
    assert r['schema_version']=='cupti-batch-once-control-receipt/0.1.1' and r['status']=='BLOCKED' and reason in r['error']
    assert len(calls)==model_starts and resources and paths['once_zip'].is_file()
    assert hashlib.sha256((old/'once/control_receipt.json').read_bytes()).hexdigest()==original_hash
    assert paths['root']!=old and paths['root'].is_relative_to(old.parent)
    if mode=='exit7':
        proc=json.loads((paths['root']/'once/one_model.process.json').read_bytes());assert proc['exit_code']==7
        assert r['model_receipt']['post_execution_static_rechecked'] is True
    with pytest.raises(ValueError,match='NO_OVERWRITE_RESUME_RETRY'):m.run(packet,'execute',flags)


def test_new_packaged_PS_default_only_verifies_and_prepare_is_refused(packet):
    import os
    c=json.loads((packet/'delivery.json').read_bytes());c['python']=sys.executable
    (packet/'delivery.json').write_text(json.dumps(c),encoding='utf8')
    index=json.loads((packet/'package_manifest.json').read_bytes())
    for row in index['files']:
        data=(packet/row['path']).read_bytes();row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
    (packet/'package_manifest.json').write_text(json.dumps(index),encoding='utf8')
    env=dict(os.environ,PSModulePath=str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/Modules'))
    args=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(packet/'run_cupti_batch_once.ps1'),
        '-PackageManifestSha256',hashlib.sha256((packet/'package_manifest.json').read_bytes()).hexdigest()]
    p=subprocess.run(args,capture_output=True,env=env,timeout=30)
    assert p.returncode==0 and b'PACKAGE_VERIFIED_NO_TARGET_ACCESS' in p.stdout
    p=subprocess.run(args+['-Action','prepare','-ApprovePrepare','-OperatorReference','CPU'],capture_output=True,env=env,timeout=30)
    assert p.returncode!=0 and b'REPAIR_NO_A_REPLAY' in p.stderr
