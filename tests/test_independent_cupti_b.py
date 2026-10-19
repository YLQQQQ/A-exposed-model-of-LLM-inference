"""New B boundary only. A/Git and native process are explicit CPU doubles."""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import zipfile

import pytest


ROOT=Path(__file__).resolve().parents[1]


def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def fixture(tmp_path,monkeypatch):
    m=importlib.import_module('scripts.independent_cupti_b')
    package=tmp_path/'package';package.mkdir();a=tmp_path/'A';(a/'build').mkdir(parents=True)
    # Exact existing Python components. No actual vendor DLL/EXE is run.
    for src,dst in [('independent_cupti_stage.py','reviewed_stage.py'),('memset_micro.py','micro_support.py')]:
        (package/dst).write_bytes((ROOT/'scripts'/src).read_bytes())
    stage,s=m.components(package)
    monkeypatch.setattr(m,'components',lambda p:(stage,s))
    monkeypatch.setattr(s,'tree',lambda cfg,target:None)  # External target checkout identity double.
    monkeypatch.setitem(stage['bind_checkout_modules'].__globals__,'support',lambda:s)
    parent=sys.modules['scripts']
    monkeypatch.setattr(parent,'__path__',[str(ROOT/'scripts')])
    monkeypatch.setattr(parent.__spec__,'submodule_search_locations',[str(ROOT/'scripts')])
    def write(p,v):p.write_text(json.dumps(v),encoding='utf8')
    sources=[dict(path=p,bytes=(ROOT/p).stat().st_size,sha256=digest(ROOT/p)) for p in
        ('scripts/coe_startup_storage.py','analysis/independent_cupti_memset.py')]
    runtime=tmp_path/'runtime.dll';runtime.write_bytes(b'CPU_LIBRARY_BYTES_NOT_LOADED')
    (a/'cupti').mkdir();cupti=a/'cupti/cupti.dll';cupti.write_bytes(b'CPU_CUPTI_BYTES_NOT_LOADED')
    micro=a/'build/micro.exe';micro.write_bytes(b'CPU_EXECUTION_BOUNDARY_ONLY')
    acfg=dict(execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,code_root=str(ROOT),git='git',
        python=sys.executable,python_version=list(sys.version_info[:3]),gpu_uuid='GPU-0d8fafe6-a1e9-33cc-25fb-632316736455',
        runtime_path=str(runtime),source_representations={r['path']:[r] for r in sources})
    write(a/'delivery.json',acfg);write(a/'source_bytes.json',sources)
    write(a/'runtime_file.json',dict(path=str(runtime),bytes=runtime.stat().st_size,sha256=digest(runtime),file_version='6.14.11.12040'))
    write(a/'cupti_file.json',dict(path=str(cupti),bytes=cupti.stat().st_size,sha256=digest(cupti)))
    write(a/'build/build.json',dict(micro=str(micro),micro_invoked=False,cuda_header_version=12040,
        cupti_header_version=22,binary_files=[dict(path='micro.exe',bytes=micro.stat().st_size,sha256=digest(micro))]))
    write(a/'receipt.json',dict(schema_version='independent-cupti-stage-a-receipt/0.1.0',phase='A',
        status='STATIC_READY_FOR_REVIEW',error=None,execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,
        stage_a_cuda_programs_executed=0,B_authorized=False,package_index_sha256='d'*64))
    rows=[dict(path=p.relative_to(a).as_posix(),bytes=p.stat().st_size,sha256=digest(p)) for p in a.rglob('*') if p.is_file()]
    write(a/'artifact_manifest.json',dict(files=rows))
    receipt=digest(a/'receipt.json');monkeypatch.setattr(m,'A_RECEIPT_SHA',receipt)
    cfg=dict(schema_version='independent-cupti-stage-b/0.1.0',controller_commit='a'*40,
        native_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,reviewed_a_receipt_sha256=receipt,
        a_manifest_sha256=digest(a/'artifact_manifest.json'),a_root=str(a),server_root=str(tmp_path/'YLQ'),
        build_sha256=digest(a/'build/build.json'),runtime_sha256=digest(runtime),cupti_sha256=digest(cupti),
        micro_binary=dict(path='micro.exe',bytes=micro.stat().st_size,sha256=digest(micro)),
        python=sys.executable,python_version=list(sys.version_info[:3]),gpu_uuid=acfg['gpu_uuid'],
        temporary_required_bytes=2**31,timeout_seconds=120,micro_process_budget=1,profile_budget=0,model_process_budget=0,
        helper_files=[dict(path=p.name,bytes=p.stat().st_size,sha256=digest(p)) for p in package.iterdir()])
    write(package/'delivery.json',cfg)
    manifest=[dict(path=p.name,bytes=p.stat().st_size,sha256=digest(p)) for p in package.iterdir()]
    write(package/'package_manifest.json',dict(files=manifest))
    base=runpy.run_path(str(ROOT/'tests/test_independent_cupti_memset.py'))['evidence']()
    invoked=[]
    def native(helper,argv,out,env):
        # Replacement for the GPU boundary only. The real child writes a
        # deterministic synthetic record and a real process receipt.
        assert argv[0]==str(micro) and argv[1]=='--run-reviewed-gpu-micro'
        assert argv[2:4]==[str(runtime),str(cupti)] and argv[6:]==[digest(runtime),digest(cupti)]
        assert env['CUDA_VISIBLE_DEVICES']==cfg['gpu_uuid'] and env['CUDA_DEVICE_ORDER']=='PCI_BUS_ID'
        invoked.append(argv)
        v=copy.deepcopy(base);v.update(source='TARGET_GPU',run_id=argv[4],runtime_sha256=digest(runtime),
            cupti_sha256=digest(cupti),runtime_loaded_path=str(runtime),cupti_loaded_path=str(cupti),
            callback_name_source='CUPTI_GET_CALLBACK_NAME')
        script="import json,os,sys;v=json.loads(sys.argv[1]);v['pid']=os.getpid();[c.update(pid=os.getpid()) for c in v['callbacks']];[a.update(pid=os.getpid()) for a in v['api_records']];open(sys.argv[2],'x').write(json.dumps(v))"
        return helper.command([sys.executable,'-I','-c',script,json.dumps(v),argv[5]],out,out/'micro',env=env,timeout=120)
    monkeypatch.setattr(m,'execute_micro',native)
    return m,s,cfg,package,a,invoked


def output(cfg):return Path(cfg['server_root'])/'diagnostics'/('independent_cupti_'+cfg['controller_commit'][:12]+'_b_once')


def test_real_receipt_raw_reader_and_pack_chain_cpu_double(tmp_path,monkeypatch):
    m,s,c,p,a,calls=fixture(tmp_path,monkeypatch)
    assert m.run(p,reviewed=c['reviewed_a_receipt_sha256'],enabled=True)==0
    out=output(c);r=json.loads((out/'receipt.json').read_text())
    assert r['status']=='MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW' and len(calls)==1
    assert r['native_commit']==r['analysis_commit']==m.NATIVE_COMMIT and r['controller_commit']=='a'*40
    assert r['micro_process_budget']==1 and r['profile_budget']==r['model_process_budget']==0
    assert r['A_COE_admission']=='NOT_ASSESSED' and r['pytorch_coverage']=='NOT_ASSESSED'
    assert json.loads((out/'derived/review.json').read_text())['result']['cases'][1]['count']==64
    with zipfile.ZipFile(out.parent.parent/'transfer'/('independent_cupti_'+('a'*12)+'_b_once.zip')) as z:
        assert z.testzip() is None and {'micro.process.json','raw.json','receipt.json','resources.json'}<=set(z.namelist())
    with pytest.raises(ValueError,match='NO_OVERWRITE'):m.run(p,reviewed=c['reviewed_a_receipt_sha256'],enabled=True)
    assert len(calls)==1


@pytest.mark.parametrize('mutation,reason',[
    ('receipt','A_RECEIPT_HASH'),('manifest','A_MANIFEST_HASH'),('build','A_FILE_HASH'),
    ('binary','A_FILE_HASH'),('library','RUNTIME_CHANGED'),('source','FILE_HASH'),
    ('gpu','GPU_IDENTITY'),('python','PYTHON_VERSION')])
def test_identity_conflicts_stop_before_native(tmp_path,monkeypatch,mutation,reason):
    m,s,c,p,a,calls=fixture(tmp_path,monkeypatch)
    if mutation=='receipt':(a/'receipt.json').write_bytes(b'{}')
    elif mutation=='manifest':(a/'artifact_manifest.json').write_bytes(b'{}')
    elif mutation=='build':(a/'build/build.json').write_bytes(b'{}')
    elif mutation=='binary':(a/'build/micro.exe').write_bytes(b'wrong executable')
    elif mutation=='library':Path(json.loads((a/'runtime_file.json').read_text())['path']).write_bytes(b'changed')
    elif mutation=='source':
        # Rebind the separately-indexed helper bytes, not a protected real source.
        (p/'micro_support.py').write_bytes(b'changed')
    else:
        c['gpu_uuid' if mutation=='gpu' else 'python_version']='wrong'
        (p/'delivery.json').write_text(json.dumps(c));(p/'package_manifest.json').unlink()
        s.write(p/'package_manifest.json',dict(files=[dict(path=x.name,bytes=x.stat().st_size,sha256=digest(x)) for x in p.iterdir()]))
    if mutation=='source':
        with pytest.raises(ValueError,match=reason):m.run(p,reviewed=c['reviewed_a_receipt_sha256'],enabled=True)
    else:
        assert m.run(p,reviewed=c['reviewed_a_receipt_sha256'],enabled=True)==2
        assert reason in json.loads((output(c)/'receipt.json').read_text())['error']
    assert not calls


def test_no_implicit_unlock_or_wrong_review_hash(tmp_path,monkeypatch):
    m,s,c,p,a,calls=fixture(tmp_path,monkeypatch)
    for enabled,reviewed in [(False,c['reviewed_a_receipt_sha256']),(True,'0'*64)]:
        with pytest.raises(ValueError,match='EXPLICIT_REVIEWED_B'):m.run(p,reviewed=reviewed,enabled=enabled)
    assert not calls and not output(c).exists()


@pytest.mark.parametrize('failure',['native_exit','unknown_writer','missing_effect','wrong_pid','space','space_low','profiler'])
def test_failure_propagation_and_unknown_writer_refuses_pack(tmp_path,monkeypatch,failure):
    m,s,c,p,a,calls=fixture(tmp_path,monkeypatch)
    original=m.execute_micro
    if failure=='space':monkeypatch.setattr(s,'resources',lambda *args:(_ for _ in ()).throw(OSError('SPACE_QUERY_UNKNOWN')))
    elif failure=='space_low':monkeypatch.setattr(s,'resources',lambda *args:dict(volumes={'cpu':dict(free_bytes=1)}))
    elif failure=='profiler':monkeypatch.setenv('CUDA_INJECTION64_PATH','CPU_EXTERNAL_PROFILER_CONFLICT')
    else:
        def execute(helper,argv,out,env):
            if failure in ('native_exit','unknown_writer'):
                helper.write(out/'micro.process.json',dict(status='EXITED' if failure=='native_exit' else 'BLOCKED',
                    exit_code=2,timed_out=failure=='unknown_writer',
                    descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY' if failure=='unknown_writer' else 'EXITED'))
                raise ValueError('NATIVE_PROCESS_FAILED')
            r=original(helper,argv,out,env);v=json.loads(Path(argv[5]).read_text())
            if failure=='missing_effect':v['effects']=[]
            if failure=='wrong_pid':v['pid']+=1
            Path(argv[5]).write_text(json.dumps(v));return r
        monkeypatch.setattr(m,'execute_micro',execute)
    assert m.run(p,reviewed=c['reviewed_a_receipt_sha256'],enabled=True)==2
    out=output(c);r=json.loads((out/'receipt.json').read_text())
    assert r['status']=='BLOCKED' and r['error']
    archives=list((out.parent.parent/'transfer').glob('*.zip'))
    assert bool(archives)==(failure!='unknown_writer')
    if failure in ('space','space_low','profiler'):assert not calls


def test_exact_120_second_single_process_gateway():
    m=importlib.import_module('scripts.independent_cupti_b');seen=[]
    class Helper:
        def command(self,argv,cwd,log,**kw):seen.append((argv,cwd,log,kw));return {'exit_code':0}
    m.execute_micro(Helper(),['fixed.exe'],'new-output',{'CUDA_VISIBLE_DEVICES':'GPU-fixed'})
    assert len(seen)==1 and seen[0][3]['timeout']==120
    assert seen[0][3]['env']=={'CUDA_VISIBLE_DEVICES':'GPU-fixed'}


@pytest.mark.parametrize('extra,success',[
    ([],False),(['-RunReviewedMicro','-ReviewedAReceiptSha256','0'*64],False),
    (['-RunReviewedMicro','-ReviewedAReceiptSha256','67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0'],True)])
def test_real_ps51_requires_explicit_review_and_uses_isolated_python(tmp_path,extra,success):
    if os.name!='nt':pytest.skip('Windows PS5.1 entry only; no Linux support claimed')
    launcher=tmp_path/'run_independent_cupti_b.ps1'
    launcher.write_bytes((ROOT/'scripts/run_independent_cupti_b.ps1').read_bytes())
    driver=tmp_path/'independent_cupti_b.py'
    driver.write_text("import sys,json,pathlib;pathlib.Path(__file__).with_name('dispatch.json').write_text(json.dumps({'argv':sys.argv[1:],'isolated':sys.flags.isolated}))")
    (tmp_path/'delivery.json').write_text(json.dumps(dict(python=sys.executable,controller_sha256=digest(driver))))
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    env=os.environ.copy();env['PSModulePath']=str(ps.parent/'Modules')
    p=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(launcher),*extra],
        capture_output=True,timeout=30,env=env)
    assert (p.returncode==0)==success,p.stderr.decode(errors='replace')
    if success:
        r=json.loads((tmp_path/'dispatch.json').read_text())
        assert r['isolated']==1 and r['argv']==['--package',str(tmp_path),'--run-reviewed-b',
            '--reviewed-a-receipt-sha256','67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0']
    else:assert not (tmp_path/'dispatch.json').exists()


def test_packaged_b_real_isolated_main_resources_to_native_boundary_only(tmp_path,monkeypatch):
    m,s,c,p,a,calls=fixture(tmp_path,monkeypatch)
    (p/'independent_cupti_b.py').write_bytes((ROOT/'scripts/independent_cupti_b.py').read_bytes())
    (p/'package_manifest.json').unlink()
    s.write(p/'package_manifest.json',dict(files=[dict(path=x.name,bytes=x.stat().st_size,sha256=digest(x)) for x in p.iterdir()]))
    # A identity and target Git are doubled, resources/imports and main/pack are
    # real. The native call is intercepted BEFORE any executable can launch.
    child="""
import json,runpy,sys
from pathlib import Path
package=Path(sys.argv[1]);ns=runpy.run_path(str(package/'independent_cupti_b.py'))
cfg=json.loads((package/'delivery.json').read_text());g=ns['run'].__globals__
g['A_RECEIPT_SHA']=cfg['reviewed_a_receipt_sha256']
stage,m=ns['components'](package);m.tree=lambda *args:None
stage['bind_checkout_modules'].__globals__['support']=lambda:m
g['components']=lambda package:(stage,m)
def stop(*args):raise RuntimeError('CPU_STOP_AT_NATIVE_BOUNDARY')
g['execute_micro']=stop
sys.exit(ns['main'](['--package',str(package),'--run-reviewed-b','--reviewed-a-receipt-sha256',cfg['reviewed_a_receipt_sha256']]))
"""
    before={x.name:digest(x) for x in p.iterdir()}
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    proc=subprocess.run([sys.executable,'-I','-c',child,str(p)],cwd=tmp_path,capture_output=True,env=env,timeout=30)
    assert proc.returncode==2,proc.stderr.decode(errors='replace')
    out=output(c);r=json.loads((out/'receipt.json').read_text())
    assert 'CPU_STOP_AT_NATIVE_BOUNDARY' in r['error'] and not (out/'micro.process.json').exists()
    assert (out/'resources.json').is_file() and (out/'execution_plan.json').is_file()
    assert {x.name:digest(x) for x in p.iterdir()}==before
