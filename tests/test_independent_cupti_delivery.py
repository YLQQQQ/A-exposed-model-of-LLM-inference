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
    package=tmp_path/'package';package.mkdir();code=tmp_path/'code';code.mkdir()
    (code/'payload.py').write_bytes(b'x=1\n')
    cfg=dict(schema_version='independent-cupti-stage-a/0.1.0',execution_commit='a'*40,
        analysis_commit='a'*40,prerequisite='9c78e355bb43a8696f7eccb44c48d8448f366d09',
        server_root=str(tmp_path/'YLQ'),code_root=str(code),python=sys.executable,python_version=list(sys.version_info[:3]),
        git='git',source_representations={'payload.py':[dict(bytes=4,sha256=s.sha(code/'payload.py'))]},
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
    monkeypatch.setattr(m,'startup_resources',lambda *a:dict(historical_ylq_total_bytes=None,
        long_term_status='UNKNOWN_NOT_PROVEN',volumes={'test':dict(free_bytes=2**35,required_bytes=2**31)}))
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
    if mutation=='source':(Path(cfg['code_root'])/'payload.py').write_bytes(b'x=2\n')
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
