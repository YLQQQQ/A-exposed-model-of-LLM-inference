"""Stage A real files/receipts; deployment, compiler and target OS are CPU doubles."""
import importlib
import json
import os
from pathlib import Path
import sys
import subprocess
import zipfile

import pytest


def setup_package(tmp_path,monkeypatch,*,fail=None):
    m=importlib.import_module('scripts.independent_cupti_stage');s=m.support()
    package=tmp_path/'package';package.mkdir();code=Path(__file__).resolve().parents[1]
    source='scripts/coe_startup_storage.py'
    cfg=dict(schema_version='independent-cupti-stage-a/0.1.0',execution_commit='a'*40,
        analysis_commit='a'*40,prerequisite='9c78e355bb43a8696f7eccb44c48d8448f366d09',
        server_root=str(tmp_path/'YLQ'),code_root=str(code),python=sys.executable,python_version=list(sys.version_info[:3]),
        git='git',source_representations={source:[dict(bytes=(code/source).stat().st_size,sha256=s.sha(code/source))]},
        toolchain_files={},build={},runtime_path=str(tmp_path/'runtime.dll'),
        cupti_dll_sha256='b'*64,cpu_test_count=3,temporary_required_bytes=2**31,
        micro_process_budget=0,model_process_budget=0,profile_budget=0,default_stage='A_ONLY_NO_B_ENTRY',
        sdk_files=[],cupti_files=[])
    (tmp_path/'runtime.dll').write_bytes(b'PE-double')
    for name in ('sdk.zip','cupti.zip'):
        rows=[]
        with zipfile.ZipFile(package/name,'x') as z:
            payloads={'include/placeholder.h':b'cpu test headers'}
            if name=='cupti.zip':payloads['lib/cupti64_2024.1.1.dll']=b'CPU_CUPTI_DLL_DOUBLE'
            for relative,data in payloads.items():
                import hashlib
                z.writestr(relative,data);rows.append(dict(path=relative,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
        cfg['sdk_files' if name=='sdk.zip' else 'cupti_files']=rows
    cfg['cupti_dll_sha256']=cfg['cupti_files'][1]['sha256']
    s.write(package/'delivery.json',cfg)
    s.write(package/'prerequisite_reference.json',dict(execution_commit=cfg['prerequisite']))
    s.write(package/'package_manifest.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=s.sha(p))
        for p in package.iterdir()]))
    monkeypatch.setattr(m,'deploy',lambda *a:None)
    monkeypatch.setattr(s,'tree',lambda *a:None)
    # This in-process deployment double shares pytest's interpreter. Model the
    # explicit namespace of an isolated checkout; ambient/merged packages are
    # exercised and rejected in the real -I children below.
    parent=sys.modules['scripts']
    monkeypatch.setattr(parent,'__path__',[str(code/'scripts')])
    monkeypatch.setattr(parent.__spec__,'submodule_search_locations',[str(code/'scripts')])
    monkeypatch.setattr(s,'runtime_fact',lambda p:s.file_fact(p))
    def build(config,out):
        out=Path(out);out.mkdir();(out/'micro.exe').write_bytes(b'NOT EXECUTED')
        v=dict(micro=str(out/'micro.exe'),micro_invoked=False,binary_files=[dict(path='micro.exe',bytes=12,
            sha256=s.sha(out/'micro.exe'))]);s.write(out/'build.json',v);return v
    monkeypatch.setattr(m,'build_native',build)
    monkeypatch.setattr(m,'inspect_exports',lambda *a:dict(source='EXTERNAL_PE_INSPECTION_DOUBLE'))
    seen=[]
    def command(argv,cwd,log,**kw):
        assert '-m' in argv and 'pytest' in argv
        assert kw['env']['CUDA_VISIBLE_DEVICES']=='-1'
        seen.append(argv)
        if fail=='cpu':raise ValueError('CPU_HARD_FAILURE')
        out=Path(argv[argv.index('--junitxml')+1]);out.write_text(
            '<testsuites><testsuite tests="3" failures="0" errors="0" skipped="0"/></testsuites>')
        return dict(exit_code=0)
    monkeypatch.setattr(s,'command',command)
    # support() must return the same controlled external-boundary object.
    monkeypatch.setattr(m,'support',lambda:s)
    return m,s,cfg,package,seen


def test_stage_a_actual_receipt_pack_chain_does_not_run_gpu(tmp_path,monkeypatch):
    m,s,cfg,p,seen=setup_package(tmp_path,monkeypatch)
    assert hasattr(m,'stage_a'), 'stage A not wired'
    assert m.main(['--package',str(p)])==0
    out=Path(cfg['server_root'])/'diagnostics'/('independent_cupti_'+('a'*12)+'_static')
    r=json.loads((out/'receipt.json').read_text())
    assert r['status']=='STATIC_READY_FOR_REVIEW' and r['phase']=='A'
    assert r['stage_a_cuda_programs_executed']==0 and r['B_authorized'] is False
    assert r['historical_ylq_total_bytes'] is None and len(seen)==1
    imports=json.loads((out/'checkout_imports.json').read_text())
    assert imports['modules'][0]['origin']==str(Path(cfg['code_root'])/'scripts/coe_startup_storage.py')
    assert imports['sys_path_modified'] is False and imports['pythonpath_used'] is False
    resources=json.loads((out/'resources.json').read_text())
    assert resources['volumes'] and all(v['required_bytes']==2**31 for v in resources['volumes'].values())
    archive=Path(cfg['server_root'])/'transfer'/('independent_cupti_'+('a'*12)+'_static.zip')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and 'receipt.json' in z.namelist()
    with pytest.raises(ValueError,match='NO_OVERWRITE'):m.stage_a(p)


def test_cpu_failure_preserves_blocked_new_receipt_and_returns_failure(tmp_path,monkeypatch):
    m,s,cfg,p,seen=setup_package(tmp_path,monkeypatch,fail='cpu')
    assert hasattr(m,'stage_a'), 'stage A not wired'
    assert m.stage_a(p)==2
    out=Path(cfg['server_root'])/'diagnostics'/('independent_cupti_'+('a'*12)+'_static')
    r=json.loads((out/'receipt.json').read_text())
    assert r['status']=='BLOCKED' and 'CPU_HARD_FAILURE' in r['error'] and not r['B_authorized']


def test_changed_package_or_source_is_not_accepted(tmp_path,monkeypatch):
    m,s,cfg,p,seen=setup_package(tmp_path,monkeypatch)
    assert hasattr(m,'stage_a'), 'stage A not wired'
    (p/'sdk.zip').write_bytes(b'tampered')
    with pytest.raises(ValueError,match='FILE_HASH'):m.stage_a(p)
    assert not seen


def test_stage_a_has_no_collection_dispatch_or_receipt_unlock(monkeypatch):
    m=importlib.import_module('scripts.independent_cupti_stage')
    with pytest.raises(SystemExit) as e:m.main(['--package','none','--collect'])
    assert e.value.code==2


@pytest.mark.parametrize('mutation',['source','version','commit'])
def test_source_or_delivery_identity_conflict_stops_before_cpu(tmp_path,monkeypatch,mutation):
    m,s,cfg,p,seen=setup_package(tmp_path,monkeypatch)
    if mutation=='source':cfg['source_representations']['scripts/coe_startup_storage.py'][0]['sha256']='0'*64
    else:
        cfg['schema_version' if mutation=='version' else 'analysis_commit']='wrong'
    (p/'delivery.json').write_text(json.dumps(cfg),encoding='utf8')
    (p/'package_manifest.json').unlink()
    s.write(p/'package_manifest.json',dict(files=[dict(path=f.name,bytes=f.stat().st_size,sha256=s.sha(f)) for f in p.iterdir()]))
    if mutation=='source':
        assert m.stage_a(p)==2
        out=Path(cfg['server_root'])/'diagnostics'/('independent_cupti_'+('a'*12)+'_static')
        assert 'SOURCE_BYTES' in json.loads((out/'receipt.json').read_text())['error']
    else:
        with pytest.raises(ValueError,match='A_ONLY_DELIVERY'):m.stage_a(p)
    assert not seen


@pytest.mark.parametrize('extra,success',[([],True),(['-CollectReviewedMicro'],False)])
def test_actual_powershell51_launcher_has_only_static_dispatch(tmp_path,extra,success):
    if os.name!='nt':pytest.skip('Windows-only launcher; no Linux support claimed')
    from scripts.memset_micro import sha
    root=Path(__file__).resolve().parents[1]
    launcher=tmp_path/'run.ps1';launcher.write_bytes((root/'scripts/run_independent_cupti_a.ps1').read_bytes())
    driver=tmp_path/'independent_cupti_stage.py'
    driver.write_text("import json,sys,pathlib\npathlib.Path(__file__).with_name('argv.json').write_text(json.dumps(sys.argv[1:]))\n",encoding='utf8')
    helper=tmp_path/'micro_support.py';helper.write_bytes(b'# external-boundary double\n')
    (tmp_path/'delivery.json').write_text(json.dumps(dict(python=sys.executable,
        bootstrap_sha256=sha(driver),support_sha256=sha(helper))),encoding='utf8')
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    # A Python spawned from PowerShell 7 can inherit its incompatible module path.
    # Use the actual PS5.1 built-in module directory, as existing launcher tests do.
    env=os.environ.copy();env['PSModulePath']=str(ps.parent/'Modules')
    p=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(launcher),*extra],
        capture_output=True,timeout=30,env=env)
    assert (p.returncode==0)==success,p.stderr.decode(errors='replace')
    if success:assert json.loads((tmp_path/'argv.json').read_text())==['--package',str(tmp_path)]
    else:assert not (tmp_path/'argv.json').exists()


def test_packaged_support_import_does_not_change_strict_package_file_set(tmp_path):
    root=Path(__file__).resolve().parents[1]
    driver=tmp_path/'independent_cupti_stage.py'
    driver.write_bytes((root/'scripts/independent_cupti_stage.py').read_bytes())
    (tmp_path/'micro_support.py').write_bytes((root/'scripts/memset_micro.py').read_bytes())
    before={p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*') if p.is_file()}
    p=subprocess.run([sys.executable,'-I','-c',
        "import runpy,sys; ns=runpy.run_path(sys.argv[1]); ns['support']()",str(driver)],
        capture_output=True,timeout=20)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    after={p.relative_to(tmp_path).as_posix() for p in tmp_path.rglob('*') if p.is_file()}
    assert after==before, 'bootstrap import polluted strict package coverage'


def isolated_resources_fixture(tmp_path):
    """Real packaged files + real minimal Git checkout; no storage/import doubles."""
    import hashlib
    root=Path(__file__).resolve().parents[1]
    package=tmp_path/'package';package.mkdir()
    for src,dst in [('independent_cupti_stage.py','independent_cupti_stage.py'),
                    ('memset_micro.py','micro_support.py')]:
        (package/dst).write_bytes((root/'scripts'/src).read_bytes())
    code=tmp_path/'verified checkout';(code/'scripts').mkdir(parents=True)
    source=root/'scripts/coe_startup_storage.py'
    data=source.read_bytes();(code/'scripts'/source.name).write_bytes(data)
    def git(*args):
        return subprocess.check_output(['git','-C',str(code),*args],stderr=subprocess.PIPE).decode().strip()
    git('init','-q');git('add','scripts/coe_startup_storage.py')
    git('-c','user.name=CPU Fixture','-c','user.email=fixture@example.invalid',
        '-c','core.autocrlf=false','commit','-qm','isolated storage fixture')
    cfg=dict(code_root=str(code),git='git',execution_commit=git('rev-parse','HEAD'),
        temporary_required_bytes=1,source_representations={'scripts/coe_startup_storage.py':[
            dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())]})
    config=tmp_path/'config.json';config.write_text(json.dumps(cfg),encoding='utf8')
    (tmp_path/'output').mkdir();(tmp_path/'transfer').mkdir()
    # No CUDA imports, library loading, compiler or target deployment in this child.
    child="""
import json,runpy,sys
from pathlib import Path
ns=runpy.run_path(sys.argv[1]);cfg=json.loads(Path(sys.argv[2]).read_text())
mode=sys.argv[3];base=Path(sys.argv[2]).parent
if mode in ('wrong_parent','old_checkout','wrong_leaf','merged_namespace'):
    import importlib.util
    wrong=base/'untrusted';(wrong/'scripts').mkdir(parents=True)
    if mode=='wrong_parent':
        (wrong/'scripts/__init__.py').write_text('ORIGIN="third-party"')
        sys.path.insert(0,str(wrong));__import__('scripts')
    else:
        import types
        parent=types.ModuleType('scripts');parent.__path__=[str(wrong/'scripts') if mode=='old_checkout' else str(Path(cfg['code_root'])/'scripts')]
        if mode=='merged_namespace':parent.__path__.append(str(wrong/'scripts'))
        parent.__spec__=importlib.util.spec_from_loader('scripts',loader=None,is_package=True)
        parent.__spec__.submodule_search_locations=parent.__path__;sys.modules['scripts']=parent
        if mode=='wrong_leaf':
            leaf=wrong/'scripts/coe_startup_storage.py';leaf.write_text('raise RuntimeError("must not execute")')
            spec=importlib.util.spec_from_file_location('scripts.coe_startup_storage',leaf)
            sys.modules[spec.name]=importlib.util.module_from_spec(spec)
if mode=='untrusted_available':
    wrong=base/'untrusted';(wrong/'scripts').mkdir(parents=True)
    (wrong/'scripts/__init__.py').write_text('raise RuntimeError("third-party must not execute")')
    sys.path.insert(0,str(wrong))
if mode=='old_commit':cfg['execution_commit']='0'*40
if mode=='wrong_bytes':cfg['source_representations']['scripts/coe_startup_storage.py'][0]['sha256']='0'*64
if mode=='stage_a':
    import hashlib
    package=Path(sys.argv[1]).parent
    cfg.update(schema_version='independent-cupti-stage-a/0.1.0',analysis_commit=cfg['execution_commit'],
        prerequisite='9c78e355bb43a8696f7eccb44c48d8448f366d09',server_root=str(base/'YLQ'),
        python_version=list(sys.version_info[:3]),default_stage='A_ONLY_NO_B_ENTRY',
        micro_process_budget=0,model_process_budget=0,profile_budget=0,sdk_files=[{}],cupti_files=[{}],
        toolchain_files={},runtime_path=str(base/'intentionally-absent-runtime.dll'))
    (package/'delivery.json').write_text(json.dumps(cfg))
    rows=[dict(path=p.name,bytes=p.stat().st_size,sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in package.iterdir()]
    (package/'package_manifest.json').write_text(json.dumps(dict(files=rows)))
    # External deployment only is doubled: preserve the real tree/source gate,
    # packaged imports, resources, failure receipt and pack. No build or GPU.
    ns['stage_a'].__globals__['deploy']=lambda *args:None
    rc=ns['stage_a'](package)
    out=base/'YLQ/diagnostics'/('independent_cupti_'+cfg['execution_commit'][:12]+'_static')
    receipt=json.loads((out/'receipt.json').read_text())
    print(json.dumps(dict(return_code=rc,receipt=receipt,
        imports=json.loads((out/'checkout_imports.json').read_text()),
        resources=json.loads((out/'resources.json').read_text()),isolated=sys.flags.isolated)))
    raise SystemExit(0)
binding=ns['bind_checkout_modules'](cfg)
r=ns['startup_resources'](base/'output',base/'transfer/new.zip',cfg)
print(json.dumps(dict(binding=binding,resources=r,isolated=sys.flags.isolated,
    origin=sys.modules['scripts.coe_startup_storage'].__file__,
    forbidden_loaded=any(k=='torch' or k.startswith('torch.') for k in sys.modules))))
"""
    return package,config,child


@pytest.mark.parametrize('mode',['clean','untrusted_available'])
def test_packaged_isolated_bootstrap_uses_real_verified_storage_dependency(tmp_path,mode):
    package,config,child=isolated_resources_fixture(tmp_path)
    before={p.name:p.read_bytes() for p in package.iterdir()}
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    p=subprocess.run([sys.executable,'-I','-c',child,str(package/'independent_cupti_stage.py'),str(config),mode],
        cwd=tmp_path,capture_output=True,timeout=30,env=env)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    result=json.loads(p.stdout)
    assert result['isolated']==1 and result['forbidden_loaded'] is False
    assert Path(result['origin'])==tmp_path/'verified checkout/scripts/coe_startup_storage.py'
    assert result['resources']['volumes'] and result['resources']['historical_ylq_total_bytes'] is None
    assert all(type(v['free_bytes']) is int and v['free_bytes']>0 for v in result['resources']['volumes'].values())
    assert {p.name:p.read_bytes() for p in package.iterdir()}==before
    assert not any(tmp_path.rglob('.coe-write-probe-*'))


@pytest.mark.parametrize('mode,reason',[
    ('wrong_parent','CHECKOUT_PACKAGE_ORIGIN'),('old_checkout','CHECKOUT_PACKAGE_ORIGIN'),
    ('merged_namespace','CHECKOUT_PACKAGE_ORIGIN'),
    ('wrong_leaf','CHECKOUT_MODULE_ORIGIN'),('old_commit','COMMIT'),('wrong_bytes','SOURCE_BYTES')])
def test_isolated_bootstrap_rejects_wrong_module_or_checkout_identity(tmp_path,mode,reason):
    package,config,child=isolated_resources_fixture(tmp_path)
    p=subprocess.run([sys.executable,'-I','-c',child,str(package/'independent_cupti_stage.py'),str(config),mode],
        cwd=tmp_path,capture_output=True,timeout=30)
    assert p.returncode!=0 and reason in p.stderr.decode(errors='replace'),p.stderr.decode(errors='replace')


def test_isolated_stage_a_real_resources_reaches_next_gate_and_preserves_failure(tmp_path):
    package,config,child=isolated_resources_fixture(tmp_path)
    p=subprocess.run([sys.executable,'-I','-c',child,str(package/'independent_cupti_stage.py'),str(config),'stage_a'],
        cwd=tmp_path,capture_output=True,timeout=30)
    assert p.returncode==0,p.stderr.decode(errors='replace')
    result=json.loads(p.stdout.decode().splitlines()[-1]);receipt=result['receipt']
    assert result['isolated']==1 and result['return_code']==2
    assert receipt['status']=='BLOCKED' and 'FILE_MISSING' in receipt['error']
    assert 'intentionally-absent-runtime.dll' in receipt['error']
    assert not receipt['B_authorized'] and receipt['stage_a_cuda_programs_executed']==0
    assert {'source_bytes.json','checkout_imports.json','resources.json'}<=receipt['static_files'].keys()
    assert result['imports']['execution_commit']==receipt['execution_commit']
    assert result['resources']['volumes']
    archive=next((tmp_path/'YLQ/transfer').glob('*.zip'))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and 'checkout_imports.json' in z.namelist()
