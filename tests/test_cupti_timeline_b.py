import hashlib
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT=Path(__file__).resolve().parents[1]


def module():
    path=ROOT/'scripts/cupti_timeline_b.py'
    assert path.is_file(), 'bound Stage B controller missing'
    spec=importlib.util.spec_from_file_location('timeline_b_test',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def put(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v),encoding='utf8')


def hashfile(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def test_unreviewed_or_default_entry_never_loads_components(tmp_path,monkeypatch):
    m=module();called=[]
    monkeypatch.setattr(m,'components',lambda *a:called.append(True))
    with pytest.raises(ValueError,match='EXPLICIT'):m.run(tmp_path,enabled=False,reviewed='x')
    assert not called and list(tmp_path.iterdir())==[]


def test_checked_a_verifies_exact_original_receipt_and_all_sealed_files(tmp_path):
    m=module();root=tmp_path/'a';code=tmp_path/'code';code.mkdir();root.mkdir()
    (code/'x.py').write_bytes(b'# bound\n')
    (root/'client.dll').write_bytes(b'native-client')
    (root/'cupti.dll').write_bytes(b'vendor-cupti')
    (tmp_path/'runtime.dll').write_bytes(b'runtime')
    row=lambda p,name:dict(path=name,bytes=p.stat().st_size,sha256=hashfile(p))
    acfg=dict(execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,code_root=str(code))
    receipt=dict(schema_version='cupti-timeline-stage-a-receipt/0.1.0',phase='A',status='STATIC_READY_FOR_REVIEW',
        error=None,execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,
        stage_a_cuda_programs_executed=0,model_process_budget=0,micro_process_budget=0,profile_budget=0,B_authorized=False)
    put(root/'receipt.json',receipt);put(root/'delivery.json',acfg)
    put(root/'source_bytes.json',[row(code/'x.py','x.py')])
    put(root/'build/build.json',dict(vendor_gpu_executed=False,binaries=[row(root/'client.dll','../client.dll')]))
    put(root/'runtime_file.json',dict(path=str(tmp_path/'runtime.dll'),bytes=7,sha256=hashfile(tmp_path/'runtime.dll')))
    put(root/'cupti_file.json',dict(path=str(root/'cupti.dll'),bytes=12,sha256=hashfile(root/'cupti.dll')))
    rows=[row(p,p.relative_to(root).as_posix()) for p in root.rglob('*') if p.is_file()]
    put(root/'artifact_manifest.json',dict(files=rows))
    c=dict(a_root=str(root),reviewed_a_receipt_sha256=hashfile(root/'receipt.json'),
        a_manifest_sha256=hashfile(root/'artifact_manifest.json'),a_delivery_sha256=hashfile(root/'delivery.json'),
        client=dict(path=str(root/'client.dll'),sha256=hashfile(root/'client.dll')),
        cupti=dict(path=str(root/'cupti.dll'),sha256=hashfile(root/'cupti.dll')),
        runtime=dict(path=str(tmp_path/'runtime.dll'),sha256=hashfile(tmp_path/'runtime.dll')))
    def verify(base,rs):
        for r in rs:
            p=Path(base)/r['path'];assert p.stat().st_size==r['bytes'] and hashfile(p)==r['sha256']
    support=SimpleNamespace(verify_rows=verify,tree=lambda *a:None)
    stage=dict(bind_checkout_modules=lambda *a:None)
    ctx=m.checked_a(c,stage,support)
    assert ctx['acfg']==acfg
    (code/'x.py').write_bytes(b'# corrupt\n')
    with pytest.raises((AssertionError,ValueError)):m.checked_a(c,stage,support)


def test_postcheck_runs_even_when_same_run_reader_rejects(tmp_path):
    m=module();events=[]
    def analyse():events.append('analysis');raise ValueError('missing-effect')
    with pytest.raises(ValueError,match='missing-effect'):
        m.with_postcheck(analyse,lambda:events.append('postcheck'))
    assert events==['analysis','postcheck']


def test_postcheck_failure_never_becomes_success():
    m=module()
    def broken():raise ValueError('changed-static')
    with pytest.raises(ValueError,match='changed-static'):m.with_postcheck(lambda:1,broken)


def test_new_capture_is_only_analyzed_after_process_and_token_binding(tmp_path):
    m=module()
    with pytest.raises(ValueError,match='MODEL_RESULT'):m.analyze_model(tmp_path,dict(pid=1),{})


def test_b_budget_is_one_model_without_nsight_or_retry():
    m=module();c=m.fixed_budget()
    assert c==dict(model_process_budget=1,cupti_sessions=1,nsight_profiles=0,micro_process_budget=0,
        timeout_seconds=300,analysis_timeout_seconds=180,temporary_required_bytes=12*2**30,
        automatic_retry=False,automatic_cleanup=False)


def test_real_ps51_default_refuses_before_config_read(tmp_path):
    import os,subprocess
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    r=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(ROOT/'scripts/run_cupti_timeline_b.ps1')],
        cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode!=0 and b'Explicit reviewed model' in r.stderr and b'delivery.json' not in r.stderr


def test_real_ps51_explicit_entry_hashes_then_runs_only_cpu_double(tmp_path):
    import os,subprocess,sys
    script=ROOT/'scripts/run_cupti_timeline_b.ps1'
    (tmp_path/script.name).write_bytes(script.read_bytes())
    body='from pathlib import Path\nPath(__file__).with_name("entered.txt").write_text("CPU_ONLY")\n'
    target=tmp_path/'cupti_timeline_b.py';target.write_text(body,encoding='utf8')
    put(tmp_path/'delivery.json',dict(python=sys.executable,reviewed_a_receipt_sha256='a'*64,
        bootstrap_files=[dict(path=target.name,sha256=hashfile(target))]))
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    r=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(tmp_path/script.name),
        '-RunReviewedModel','-ReviewedAReceiptSha256','a'*64],cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    assert (tmp_path/'entered.txt').read_text()=='CPU_ONLY'


@pytest.mark.parametrize('failure',[None,'analysis','model'])
def test_actual_controller_file_flow_seals_success_or_failure_and_rechecks_a(tmp_path,monkeypatch,failure):
    """Real controller/packaging; process, A and storage are explicit CPU doubles."""
    import runpy,sys,zipfile
    m=module();package=tmp_path/'package';package.mkdir();server=tmp_path/'YLQ';server.mkdir()
    a=tmp_path/'a';(a/'build').mkdir(parents=True)
    for name in ('receipt.json','artifact_manifest.json','source_bytes.json','build/build.json'):put(a/name,{})
    calls=[];checks=[]
    helper=runpy.run_path(str(ROOT/'scripts/memset_micro.py'))
    support=SimpleNamespace(**{k:v for k,v in helper.items() if not k.startswith('__')})
    def command(argv,cwd,log,**kw):
        calls.append((list(argv),Path(log).name,kw))
        r=dict(pid=7,status='EXITED',exit_code=1 if Path(log).name==('one_model' if failure=='model' else 'same_run_analysis' if failure else '') else 0,timed_out=False)
        support.write(Path(log).with_suffix('.process.json'),r)
        if r['exit_code']:raise ValueError('CPU_PROCESS_DOUBLE_FAILURE')
        return r
    support.command=command
    cfg=dict(schema_version='cupti-timeline-stage-b/0.1.0',native_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,
        controller_commit='f'*40,server_root=str(server),code_root=str(ROOT),python=sys.executable,target_python=sys.executable,
        site_root=str(tmp_path),reviewed_a_receipt_sha256='a'*64,budget=m.fixed_budget(),
        model_contract={},model='model',inventory_sha256='b'*64,prompt_sha256='c'*64,gpu_uuid='uuid',gpu_pci='pci',
        session_id='session',client=dict(path='client',sha256='d'*64),cupti=dict(path='cupti',sha256='e'*64))
    for name in ('cupti_timeline_b.py','cupti_timeline_model.py','run_cupti_timeline_b.ps1'):
        (package/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    put(package/'delivery.json',cfg)
    rows=[dict(path=p.name,bytes=p.stat().st_size,sha256=hashfile(p)) for p in package.iterdir()]
    put(package/'package_manifest.json',dict(files=rows))
    def checked(*args):checks.append('A');return dict(a_root=a,acfg=dict())
    monkeypatch.setattr(m,'checked_a',checked)
    monkeypatch.setattr(m,'components',lambda *a:({'startup_resources':lambda *a:dict(status='CPU_STORAGE_DOUBLE')},support))
    monkeypatch.setattr(m,'sys',SimpleNamespace(executable=sys.executable,version_info=(3,11,16)))
    for name in ('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH'):
        monkeypatch.delenv(name,raising=False)
    result=m.run(package,enabled=True,reviewed='a'*64)
    assert result==(0 if failure is None else 2)
    assert checks==['A','A']
    assert [c[1] for c in calls]==(['one_model'] if failure=='model' else ['one_model','same_run_analysis'])
    assert calls[0][2]['timeout']==300 and calls[0][2]['env']['CUDA_VISIBLE_DEVICES']=='3'
    assert '-I' in calls[0][0] and '-S' in calls[0][0] and '--run-reviewed-model' in calls[0][0]
    archives=list((server/'transfer').glob('*.zip'));assert len(archives)==1
    with zipfile.ZipFile(archives[0]) as z:
        assert z.testzip() is None
        r=json.loads(z.read('receipt.json'))
        assert r['post_execution_static_rechecked'] is True
        assert (r['status']=='BLOCKED') is (failure is not None)
        assert r['COE_admission']=='NOT_ASSESSED'
