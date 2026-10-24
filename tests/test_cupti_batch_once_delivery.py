"""Only the new delivery boundaries; GPU/site/remote observations are doubles."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest

ROOT=Path(__file__).resolve().parents[1]
C8='c8f3dad152659044691f9ff328498c7a127815ea'


def entry():
    import os
    reviewed=os.environ.get('BATCH_ONCE_REVIEWED_PACKAGE')
    p=Path(reviewed)/'cupti_batch_once_delivery.py' if reviewed else ROOT/'scripts/cupti_batch_once_delivery.py'
    spec=importlib.util.spec_from_file_location('batch_once_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def test_transfer_paths_and_single_instance_are_not_the_old_plan_locations(tmp_path):
    m=entry();c=dict(server_root=str(tmp_path),delivery_control_commit='a'*40)
    v=m.locations(c)
    assert v['root']==tmp_path/'transfer/coe_batch_L512B2_aaaaaaaaaaaa'
    assert v['static_zip'].parent==v['once_zip'].parent==tmp_path/'transfer'
    assert v['temporary'].is_relative_to(v['root'])


def test_unknown_asset_binding_cannot_select_a_compatibility_branch():
    m=entry()
    with pytest.raises(ValueError,match='BATCH_ONCE_COMPATIBILITY'):
        m.validate_compatibility(dict(schema_version='cupti-timeline-stage-b/0.5.0',
            asset_compatibility=dict(schema_version='unknown')))


def test_batch_capture_requires_new_authorization_not_the_micro_budget():
    m=entry()
    with pytest.raises(ValueError,match='BATCH_ONCE_MODEL_AUTHORIZATION'):
        m.authorize('execute',dict(approve_prepare=True,approve_model=False,shared_use_approved=True,
            reviewed_prepare_sha256=None,operator_reference='old-micro'))


def test_frozen_source_index_rejects_current_controlled_consumer_bytes():
    m=entry()
    with pytest.raises(ValueError,match='BATCH_ONCE_SCIENCE_BINDING'):
        m.validate_scientific_contract(dict(scientific_commit=C8,analysis_commit=C8,
            consumer_version='submit-effect-bridge/0.3.2'))


def builder():
    p=ROOT/'scripts/build_cupti_batch_once_delivery.py'
    spec=importlib.util.spec_from_file_location('batch_builder_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


@pytest.fixture(scope='module')
def package(tmp_path_factory):
    import os,shutil
    b=builder();out=tmp_path_factory.mktemp('pkg')/'delivery'
    reviewed=os.environ.get('BATCH_ONCE_REVIEWED_PACKAGE')
    if reviewed:
        entry().verify_package_files(Path(reviewed));shutil.copytree(reviewed,out);return out
    def source(commit,path):
        if commit=='a'*40:return (ROOT/path).read_bytes()
        return b.blob(commit,path)
    b.build_package(out,'a'*40,source=source)
    return out


def test_real_packaged_configuration_keeps_one_batch_and_exact_c8_payload(package):
    m=entry();c,one,b,stage,support=m.configuration(package)
    assert c['slots'][0]['condition']=='G512B2P' and len(c['slots'])==1
    assert one['model_contract']['schema_version']=='cupti-timeline-model/0.5.0'
    assert one['model_contract']['batch_size']==2 and one['consumer_version']=='submit-effect-bridge/0.3.0'
    lock=m.read(package/'science_lock.json')
    assert len(lock['package_science'])==16
    assert (package/'consumer/analysis/cupti_timeline.py').read_bytes()==builder().blob(C8,'analysis/cupti_timeline.py')
    assert (package/'consumer/exposedpath_v141/submit_effect_bridge.py').read_bytes()!= (ROOT/'exposedpath_v141/submit_effect_bridge.py').read_bytes()
    assert m.read(package/'input_512_B2.json')['batch_size']==2


def test_science_blob_check_rejects_resealed_current_HEAD_payload(package,tmp_path,monkeypatch):
    # Target filesystem/Git resources are not reached before this source check.
    m=entry();c,one,b,stage,support=m.configuration(package)
    lock=m.read(package/'science_lock.json');row=next(r for r in lock['package_science'] if r['path'].endswith('/submit_effect_bridge.py'))
    bad=deepcopy(lock);r=next(r for r in bad['package_science'] if r['path']==row['path']);r['sha256']='0'*64
    class Git:
        @staticmethod
        def git_bytes(git,code,*args):return builder().blob(C8,args[-1].split(':',1)[1])
    with pytest.raises(ValueError,match='BATCH_ONCE_SCIENCE_BLOB'):
        m.check_scientific_blobs(one,bad,Git)


def test_existing_legacy_reference_dispatch_remains_strict_without_new_profile(package):
    event=load_event(package)
    with pytest.raises(KeyError,match='a_root'):
        event.checked_a({},None,None)


def test_tampered_sibling_is_rejected_before_any_sibling_execution(package,tmp_path):
    import shutil
    copy=tmp_path/'bad';shutil.copytree(package,copy)
    target=copy/'cupti_timeline_b.py';target.write_text("raise RuntimeError('MUST_NOT_EXECUTE')",encoding='utf8')
    with pytest.raises(ValueError,match='BATCH_ONCE_PACKAGE_BYTES:cupti_timeline_b.py'):entry().configuration(copy)


def load_event(package):
    spec=importlib.util.spec_from_file_location('batch_event_test',package/'cupti_event_b.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def put(p,value):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value,indent=2)+'\n',encoding='utf8')


def reseal(package):
    p=package/'package_manifest.json';v=json.loads(p.read_bytes())
    v['delivery_control_commit']=json.loads((package/'delivery.json').read_bytes())['delivery_control_commit']
    for r in v['files']:
        b=(package/r['path']).read_bytes();r.update(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
    put(p,v)


@pytest.fixture(scope='module')
def scene(package,tmp_path_factory):
    import shutil
    root=tmp_path_factory.mktemp('s')
    repo=root/'repo';subprocess.run(['git','clone','--shared','--no-checkout','-q',str(ROOT),str(repo)],check=True)
    subprocess.run(['git','-C',str(repo),'-c','core.autocrlf=false','checkout','--detach',C8],check=True,capture_output=True)
    # New control object exists, while the actual source HEAD/index stay c8.
    env=dict(__import__('os').environ,GIT_INDEX_FILE=str(root/'control-index'),GIT_AUTHOR_NAME='CPU fixture',
        GIT_AUTHOR_EMAIL='cpu@example.invalid',GIT_COMMITTER_NAME='CPU fixture',GIT_COMMITTER_EMAIL='cpu@example.invalid')
    def git(*args,input=None):
        return subprocess.run(['git','-C',str(repo),*args],env=env,input=input,check=True,capture_output=True).stdout.strip()
    git('read-tree',C8)
    for name,path in builder().CONTROL_FILES.items():
        oid=git('hash-object','-w','--stdin',input=(package/name).read_bytes()).decode()
        git('update-index','--add','--cacheinfo','100644,'+oid+','+path)
    tree=git('write-tree').decode();control=git('commit-tree',tree,'-p',C8,input=b'CPU delivery fixture\n').decode()
    remote=root/'remote.git';subprocess.run(['git','clone','--bare','--shared','-q',str(repo),str(remote)],check=True)
    subprocess.run(['git','--git-dir',str(remote),'update-ref','refs/heads/main',control],check=True)
    a=root/'oldA';e=root/'oldEvent'
    m=entry();support=m.load(package/'micro_support.py','test_real_support')
    support.extract(ROOT/'.local/transfer/cupti_timeline_6c744bf52daf_static.zip',a)
    support.extract(ROOT/'.local/transfer/cupti_event_38baca449d2f_once.zip',e)
    # Only target absolute paths/interpreter/hardware facts are relocated or
    # doubled. Original A/event receipts, manifests and bytes remain real.
    c=json.loads((package/'delivery.json').read_bytes())
    c.update(code_root=str(repo),server_root=str(root/'YLQ'),git=shutil.which('git'),
        python=sys.executable,target_python=sys.executable,delivery_control_commit=control,a_root=str(a),event_root=str(e))
    model=root/'model';model.mkdir();(model/'config.json').write_bytes((package/'model_config_reference.json').read_bytes())
    c['model']=str(model)
    put(package/'delivery.json',c);reseal(package)
    return dict(package=package,root=root,repo=repo,remote=remote,a=a,event=e,control=control)


def configured_scene(scene,monkeypatch):
    m=entry()
    monkeypatch.setattr(m,'target_environment',lambda c:dict(source='HOST_INTERPRETER_DOUBLE_NOT_TARGET',
        actual_version=list(sys.version_info[:3]),target_version_not_executed=[3,11,16]))
    monkeypatch.setattr(m,'observe_asset',lambda fact:dict(fact)) # target DLL filesystem fact, NOT a DLL load
    original_config=m.configuration
    def configuration(p):
        c,one,b,stage,support=original_config(p)
        command=support.command
        def local_remote(argv,*args,**kw):
            argv=[str(x) for x in argv]
            argv=[str(scene['remote']) if x=='https://github.com/YLQQQQ/A-exposed-model-of-LLM-inference' else x for x in argv]
            return command(argv,*args,**kw)
        support.command=local_remote
        return c,one,b,stage,support
    monkeypatch.setattr(m,'configuration',configuration)
    return m


def test_real_A_event_and_current_c8_identity_close_without_relabeling_history(scene,monkeypatch):
    m=configured_scene(scene,monkeypatch);c,one,b,stage,support=m.configuration(scene['package'])
    one['compatibility_check_root']=str(scene['root']/'first-check')
    result=b.checked_a(one,stage,support) # actual c8 -> actual new event branch; no checked_a mock
    v=result['verification']
    assert v['historical_native_commit']=='6c744bf52daff3fc54571e264a0c34e3207aa1df'
    assert v['current_source']['execution_commit']==C8 and v['current_source']['index_matches_HEAD']
    assert v['event_reference']['status']=='EVENT_LINK_COMPLETE_PENDING_REVIEW'
    assert 'clean' not in v and v['old_receipts_modified'] is False


@pytest.mark.parametrize('damage,reason',[('a_hash','HISTORICAL_A_HASH'),('event_hash','EVENT_REFERENCE_HASH'),
    ('unknown_profile','COMPATIBILITY'),('wrong_current_head','CHECKOUT_COMMIT'),('wrong_batch','COMPATIBILITY_SCOPE')])
def test_real_reference_dispatch_rejects_specific_identity_conflicts(scene,monkeypatch,damage,reason):
    m=configured_scene(scene,monkeypatch);c,one,b,stage,support=m.configuration(scene['package'])
    one['compatibility_check_root']=str(scene['root']/('negative-'+damage))
    if damage=='a_hash':one['reviewed_a_receipt_sha256']='0'*64
    if damage=='event_hash':one['reviewed_event_receipt_sha256']='0'*64
    if damage=='unknown_profile':one['asset_compatibility']['schema_version']='unknown'
    if damage=='wrong_batch':one['model_contract']['batch_size']=4
    if damage=='wrong_current_head':
        subprocess.run(['git','-C',str(scene['repo']),'checkout','--detach',scene['control']],check=True,capture_output=True)
    try:
        with pytest.raises(ValueError,match=reason):b.checked_a(one,stage,support)
    finally:
        if damage=='wrong_current_head':
            subprocess.run(['git','-C',str(scene['repo']),'-c','core.autocrlf=false','checkout','--detach',C8],check=True,capture_output=True)


def test_prepare_real_entry_has_only_transfer_outputs_no_vendor_load_and_preserves_old_receipts(scene,monkeypatch):
    m=configured_scene(scene,monkeypatch);package=scene['package']
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in
        (scene['a']/'receipt.json',scene['event']/'receipt.json')}
    assert m.run(package,'prepare',dict(approve_prepare=True,operator_reference='CPU-NEW-BATCH-PREPARE'))==0
    c=m.read(package/'delivery.json');paths=m.locations(c);r=m.read(paths['root']/'prepare/receipt.json')
    assert r['status']=='PREPARED_NOT_EXECUTED' and r['actual_model_processes']==r['actual_cupti_sessions']==0
    assert r['publication']['control_is_published_ancestor'] is True
    assert not (scene['repo']/'.git/FETCH_HEAD').exists()
    assert Path(r['publication']['fetched_objects']).is_relative_to(paths['root'])
    assert paths['static_zip'].is_file() and not (paths['root']/'once').exists()
    assert not (Path(c['server_root'])/'diagnostics').exists() and not (Path(c['server_root'])/'evidence').exists()
    assert 'torch' not in sys.modules and 'exposedpath.cupti_timeline' not in sys.modules
    assert {p:hashlib.sha256(p.read_bytes()).hexdigest() for p in before}==before
    with pytest.raises(ValueError,match='NO_OVERWRITE_RESUME_RETRY'):
        m.run(package,'prepare',dict(approve_prepare=True,operator_reference='CPU-SECOND-PREPARE'))


def test_prepared_receipt_hash_and_manifest_are_checked_before_model_dispatch(tmp_path):
    m=entry();package=tmp_path/'package';package.mkdir();(package/'package_manifest.json').write_bytes(b'fixed index')
    paths=dict(root=tmp_path/'run');receipt=paths['root']/'prepare/receipt.json'
    value=dict(schema_version='cupti-batch-once-control-receipt/0.1.0',phase='prepare',
        status='PREPARED_NOT_EXECUTED',error=None,scientific_commit=C8,delivery_control_commit='a'*40,
        package_manifest_sha256=m.sha(package/'package_manifest.json'),actual_model_processes=0,actual_cupti_sessions=0)
    put(receipt,value);put(receipt.parent/'artifact_manifest.json',dict(files=[dict(path='receipt.json',
        bytes=receipt.stat().st_size,sha256=m.sha(receipt))]))
    support=m.load(ROOT/'scripts/memset_micro.py','prepare_fixture_support');c=dict(delivery_control_commit='a'*40)
    assert m.checked_preparation(package,paths,c,support,m.sha(receipt))['status']=='PREPARED_NOT_EXECUTED'
    with pytest.raises(ValueError,match='BATCH_ONCE_PREPARE_RECEIPT_HASH'):
        m.checked_preparation(package,paths,c,support,'0'*64)


@pytest.mark.parametrize('damage,reason',[('wrong_uuid','GPU_IDENTITY'),('low_space','GPU_FREE_RESERVE'),
    ('query_failed','QUERY_EXIT')])
def test_fresh_gpu_query_cannot_accept_unknown_or_wrong_resource_facts(tmp_path,monkeypatch,damage,reason):
    from types import SimpleNamespace
    m=entry();monkeypatch.setattr(m.shutil,'which',lambda name:'CPU-SMI-DOUBLE')
    def command(argv,cwd,log,**kw):
        if damage=='query_failed':raise ValueError('QUERY_EXIT')
        Path(log).with_suffix('.stdout').write_text('3, '+('wrong' if damage=='wrong_uuid' else 'GPU-expected')+
            ', 00000000:05:00.0, RTX 4090, 555.99, 24564, '+('8191' if damage=='low_space' else '8192')+'\n',encoding='utf8')
    with pytest.raises(ValueError,match=reason):
        m.gpu_resources(dict(gpu_uuid='GPU-expected',gpu_pci='00000000:05:00.0',gpu_reference=dict(
            name='RTX 4090',driver_version='555.99',total_mib=24564)),tmp_path,SimpleNamespace(command=command))


def test_exact_packaged_powershell_verify_and_default_no_authorization(scene):
    import os,shutil
    package=scene['package'];exe=shutil.which('powershell.exe');assert exe
    env=dict(os.environ,PSModulePath=os.path.join(os.environ['SystemRoot'],'System32/WindowsPowerShell/v1.0/Modules'))
    common=[exe,'-NoProfile','-ExecutionPolicy','Bypass','-File',str(package/'run_cupti_batch_once.ps1'),
        '-PackageManifestSha256',hashlib.sha256((package/'package_manifest.json').read_bytes()).hexdigest()]
    checked=subprocess.run(common+['-Action','verify'],capture_output=True,env=env,timeout=30)
    assert checked.returncode==0,checked.stdout.decode(errors='replace')+checked.stderr.decode(errors='replace')
    assert b'PACKAGE_VERIFIED_NO_TARGET_ACCESS' in checked.stdout
    denied=subprocess.run(common,capture_output=True,env=env,timeout=30)
    assert denied.returncode!=0 and b'PREPARE_AUTHORIZATION' in denied.stderr


def test_unpublished_control_cannot_be_deployed_through_offline_transfer(scene,monkeypatch,tmp_path):
    m=configured_scene(scene,monkeypatch);c,one,b,stage,support=m.configuration(scene['package'])
    subprocess.run(['git','--git-dir',str(scene['remote']),'update-ref','refs/heads/main',C8],check=True)
    try:
        with pytest.raises(ValueError,match='COMMAND_EXIT:published_ancestry:1'):
            m.check_publication(c,tmp_path,support)
    finally:
        subprocess.run(['git','--git-dir',str(scene['remote']),'update-ref','refs/heads/main',scene['control']],check=True)


def test_current_c8_content_change_is_not_accepted_by_the_new_compatibility(scene,monkeypatch):
    m=configured_scene(scene,monkeypatch);c,one,b,stage,support=m.configuration(scene['package'])
    one['compatibility_check_root']=str(scene['root']/'changed-source')
    p=scene['repo']/'exposedpath/runner.py';original=p.read_bytes();p.write_bytes(original+b'\n# CPU corruption\n')
    try:
        with pytest.raises(ValueError,match='CONTENT_IDENTITY:exposedpath/runner.py'):b.checked_a(one,stage,support)
    finally:p.write_bytes(original)


@pytest.mark.parametrize('tamper',[False,True])
def test_reuse_saved_batch_budget_files_without_rebuilding_S(tmp_path,tamper):
    import shutil
    m=entry();source=ROOT/'.local/b247/test_new_batch_real_file_chain1/model';assert source.is_dir()
    model=tmp_path/'model';shutil.copytree(source,model)
    index=m.read(model/'batch_accounting/index.json');mc=m.read(model/'model_config.json')
    c=dict(run_id=index['run_id'],input_identity=index['input_identity'],input_slot=index['input_slot'],
        analysis_commit=index['analysis_commit'],model_config=str(model/'model_config.json'),model_contract=mc)
    b=m.load(ROOT/'scripts/cupti_timeline_b.py','saved_budget_reader')
    if tamper:
        (model/'batch_accounting/coe.json').write_bytes(b'{}')
        with pytest.raises(ValueError,match='VIEW_HASH'):m.consume_instance(model,c,b)
    else:
        result=m.consume_instance(model,c,b)
        assert result['observed_completion_ns']['Request']==165
        assert result['actual_token_ids']==[[17,18],[27,28]]
        assert result['statistical_unit']=='WHOLE_BATCH_INVOCATION'
        assert result['independent_output_numerical_correctness']=='NOT_ASSESSED'


def test_explicit_B_model_failure_retains_exact_code_and_never_runs_analysis_or_retries(scene,monkeypatch):
    m=configured_scene(scene,monkeypatch);original=m.configuration;calls=[]
    monkeypatch.setattr(m.shutil,'which',lambda name:'CPU-SMI-DOUBLE' if name=='nvidia-smi.exe' else None)
    def configure(p):
        c,one,b,stage,support=original(p);command=support.command
        def run(argv,cwd,log,**kw):
            if str(argv[0])=='CPU-SMI-DOUBLE':
                r=c['gpu_reference']
                text=(f'3, {c["gpu_uuid"]}, {c["gpu_pci"]}, {r["name"]}, {r["driver_version"]}, {r["total_mib"]}, 8192\n'
                    if Path(log).name=='gpu' else 'N/A\n')
                return command([sys.executable,'-I','-S','-c','print('+repr(text)+',end="")'],cwd,log,**kw)
            if Path(log).name=='one_model':
                calls.append(list(argv));assert kw['timeout']==300
                return command([sys.executable,'-I','-S','-c','raise SystemExit(7)'],cwd,log,**kw)
            assert Path(log).name!='same_run_analysis'
            return command(argv,cwd,log,**kw)
        support.command=run;return c,one,b,stage,support
    monkeypatch.setattr(m,'configuration',configure)
    c=m.read(scene['package']/'delivery.json');paths=m.locations(c)
    flags=dict(approve_model=True,shared_use_approved=True,
        reviewed_prepare_sha256=m.sha(paths['root']/'prepare/receipt.json'),operator_reference='CPU-NEW-BATCH-MODEL')
    assert m.run(scene['package'],'execute',flags)==2
    assert len(calls)==1 and '--run-reviewed-model' in calls[0]
    r=m.read(paths['root']/'once/control_receipt.json')
    assert r['status']=='BLOCKED' and ':7' in r['error'] and r['actual_model_processes']==1
    assert r['actual_cupti_sessions'] is None and r['qualification']=='NOT_GRANTED'
    assert m.read(paths['root']/'once/one_model.process.json')['exit_code']==7
    assert paths['once_zip'].is_file() and not (paths['root']/'once/same_run_analysis.process.json').exists()
