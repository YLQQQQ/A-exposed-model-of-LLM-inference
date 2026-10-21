"""New B boundary only. CUDA/process providers below are explicit CPU doubles."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from tests.test_cupti_event_probe import chain

ROOT=Path(__file__).resolve().parents[1]


def load(name='cupti_event_b'):
    p=ROOT/'scripts'/(name+'.py')
    assert p.is_file(),'reviewed event B controller missing'
    s=importlib.util.spec_from_file_location('_test_'+name,p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def put(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v),encoding='utf8')


def test_default_refuses_before_any_package_or_cuda_boundary(tmp_path,monkeypatch):
    m=load()
    monkeypatch.setattr(m,'components',lambda *a:pytest.fail('unreviewed import'))
    with pytest.raises(ValueError,match='EXPLICIT'):m.run(tmp_path)
    assert list(tmp_path.iterdir())==[]


def a_fixture(tmp_path):
    m=load();a=tmp_path/'a';a.mkdir();code=tmp_path/'code';code.mkdir()
    (code/'x.py').write_bytes(b'# fixed\n')
    cfg=dict(code_root=str(code),server_root=str(tmp_path),python='python',git='git',
        execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,
        schema_version='cupti-timeline-stage-a/0.1.2',activity_policy_version='cupti-api22-activity-policy/0.2.0')
    put(a/'delivery.json',cfg)
    put(a/'source_bytes.json',[dict(path='x.py',bytes=8,sha256=sha(code/'x.py'))])
    for n in ('client','cupti','runtime'):(a/(n+'.dll')).write_bytes(('CPU_NOT_LOADED_'+n).encode())
    put(a/'build/build.json',dict(client=str(a/'client.dll'),vendor_gpu_executed=False,
        schema_version='cupti-timeline-build/0.1.0',activity_policy_version='cupti-api22-activity-policy/0.2.0',
        binaries=[dict(path='client.dll',bytes=(a/'client.dll').stat().st_size,sha256=sha(a/'client.dll'))]))
    c=dict(a_root=str(a),activity_policy_version='cupti-api22-activity-policy/0.2.0',**{k:cfg[k] for k in ('code_root','server_root','python')})
    for n in ('cupti','runtime'):put(a/(n+'_file.json'),dict(path=str(a/(n+'.dll')),bytes=(a/(n+'.dll')).stat().st_size,sha256=sha(a/(n+'.dll'))))
    for n in ('client','cupti','runtime'):c[n]=dict(path=str(a/(n+'.dll')),bytes=(a/(n+'.dll')).stat().st_size,sha256=sha(a/(n+'.dll')))
    put(a/'receipt.json',dict(schema_version='cupti-timeline-stage-a-receipt/0.1.2',phase='A',status='STATIC_READY_FOR_REVIEW',
        error=None,B_authorized=False,execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,
        startup_diagnostic_version='cupti-timeline-startup/0.2.0',activity_policy_version='cupti-api22-activity-policy/0.2.0',
        stage_a_cuda_programs_executed=0,model_process_budget=0,micro_process_budget=0,profile_budget=0))
    put(a/'artifact_manifest.json',dict(files=[dict(path=p.relative_to(a).as_posix(),bytes=p.stat().st_size,sha256=sha(p))
        for p in a.rglob('*') if p.is_file()]))
    for n,k in [('receipt.json','reviewed_a_receipt_sha256'),('artifact_manifest.json','a_manifest_sha256'),('delivery.json','a_delivery_sha256')]:c[k]=sha(a/n)
    return m,c,cfg


@pytest.mark.parametrize('damage,reason',[(None,None),('receipt','A_HASH'),('source','FILE_HASH'),
    ('code_root','A_EXECUTION_PATHS'),('client','LIBRARY'),('policy','BUILD_POLICY'),('legacy','A_RECEIPT')])
def test_new_a_exact_bytes_paths_and_policy_not_old_startup_contract(tmp_path,damage,reason):
    m,c,cfg=a_fixture(tmp_path);support=load('memset_micro');support.tree=lambda *a:None
    if damage=='receipt':put(Path(c['a_root'])/'receipt.json',{'status':'BLOCKED'})
    if damage=='source':(Path(c['code_root'])/'x.py').write_bytes(b'# changed\n')
    if damage=='code_root':c['code_root']=str(tmp_path/'other')
    if damage=='client':
        p=tmp_path/'other.dll';p.write_bytes(b'CPU_OTHER');c['client']=dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p))
    if damage=='policy':c['activity_policy_version']='cupti-api22-activity-policy/0.1.0'
    if damage=='legacy':
        a=Path(c['a_root']);r=json.loads((a/'receipt.json').read_text());r['schema_version']='cupti-timeline-stage-a-receipt/0.1.1'
        put(a/'receipt.json',r);c['reviewed_a_receipt_sha256']=sha(a/'receipt.json')
    stage=dict(bind_checkout_modules=lambda *a:None)
    if damage:
        with pytest.raises(ValueError,match=reason):m.checked_a(c,stage,support)
    else:assert m.checked_a(c,stage,support)['acfg']==cfg


def result_fixture(out,c,*,missing=False):
    raw,side=chain();raw['source']='TARGET_CUPTI'
    raw['shutdown']=dict(schema_version='cupti-timeline-shutdown/0.1.0',succeeded=True,overflow=0,failure=None,
        steps=[dict(operation=op,activity_kind=kind,status_domain='CUPTI',status_code=0,success=True) for op,kind in
            [('cuptiActivityFlushAll',None),*[('cuptiActivityDisable',k) for k in (37,9,38,2,1,10,4,5)],
             ('cuptiActivityFlushAll',None),('cuptiUnsubscribe',None),('cuptiFinalize',None)]])
    if missing:raw['records']=[r for r in raw['records'] if r['kind']!='CUDA_EVENT']
    folder=out/'probe';put(folder/'timeline/capture.json',raw);put(folder/'side.json',side)
    from exposedpath.cupti_timeline import activity_policy
    put(folder/'timeline/receipt.json',dict(schema_version='cupti-timeline-session-receipt/0.1.2',pid=7,session_id='s',
        open_code=0,close_code=0,model_error_type=None,verification_mode='TARGET_CUPTI_UNQUALIFIED',
        capture_sha256=sha(folder/'timeline/capture.json'),client_sha256=c['client']['sha256'],cupti_sha256=c['cupti']['sha256'],
        startup_report_version='cupti-timeline-startup/0.2.0',startup_failure=None,startup_report_error=None,activity_policy=activity_policy()))
    put(folder/'context.json',dict(pid=7,setup_drained=True,subscription_active_during_setup=False,model_loaded=False,
        runtime_path=c['runtime']['path'],runtime_sha256=c['runtime']['sha256'],logical_allocation_bytes=64,
        explicit_stream_count=1,torch_version='2.6.0+cu124',torch_origin=str(Path(c['site_root'])/'torch/__init__.py'),
        device=dict(gpu_uuid=c['gpu_uuid'],pci_bus_id=c['gpu_pci'])))
    if not missing:
        from analysis.cupti_event_probe import analyze_files
        analyze_files(folder/'timeline/capture.json',folder/'side.json',folder/'review')
    r=dict(schema_version='cupti-event-probe-result/0.1.0',status='EVENT_LINK_COMPLETE_PENDING_REVIEW' if not missing else 'BLOCKED',
        error=None if not missing else 'CUPTI_EVENT_PROBE_EVENT_COVERAGE',pid=7,config_sha256=sha(out/'probe_config.json'),
        COE_admission='NOT_ASSESSED',original_768_failure_resolved=False,original_1024_repaired=False,automatic_retry=False)
    put(folder/'result.json',r);return folder,r


def seal_result(folder,r):
    r['files']={p.relative_to(folder).as_posix():sha(p) for p in folder.rglob('*') if p.is_file() and p.name!='result.json'}
    put(folder/'result.json',r)


def context_cfg():
    return dict(session_id='s',client=dict(path='CPU_CLIENT_NOT_LOADED',sha256='a'*64),
        cupti=dict(path='CPU_CUPTI_NOT_LOADED',sha256='b'*64),code_root=str(ROOT),site_root=str(ROOT/'cpu_site'),
        runtime=dict(path='CPU_RUNTIME_NOT_LOADED',sha256='c'*64),gpu_uuid='GPU-0d8fafe6-a1e9-33cc-25fb-632316736455',gpu_pci='0000:e1:00.0')


@pytest.mark.parametrize('damage,reason',[(None,None),('pid','IDENTITY'),('config','PROBE_RESULT'),('hash','PROBE_FILE'),
    ('missing','PROBE_COVERAGE'),('shutdown','SHUTDOWN'),('event','REVIEW'),('context','CONTEXT'),('side','IDENTITY')])
def test_parent_consumer_reads_complete_same_capture_chain(tmp_path,damage,reason):
    m=load();c=context_cfg();put(tmp_path/'probe_config.json',{})
    folder,r=result_fixture(tmp_path,c)
    if damage=='pid':r['pid']=8
    if damage=='config':r['config_sha256']='d'*64
    if damage=='shutdown':
        v=json.loads((folder/'timeline/capture.json').read_text());v['shutdown']['succeeded']=False;put(folder/'timeline/capture.json',v)
        v=json.loads((folder/'timeline/receipt.json').read_text());v['capture_sha256']=sha(folder/'timeline/capture.json');put(folder/'timeline/receipt.json',v)
    if damage=='context':
        v=json.loads((folder/'context.json').read_text());v['setup_drained']=False;put(folder/'context.json',v)
    if damage=='event':
        v=json.loads((folder/'review/review.json').read_text());v['result']['status']='BLOCKED';put(folder/'review/review.json',v)
    if damage=='side':
        v=json.loads((folder/'side.json').read_text());v['pid']=8;put(folder/'side.json',v)
    seal_result(folder,r)
    if damage=='hash':r['files']['side.json']='e'*64;put(folder/'result.json',r)
    if damage=='missing':(folder/'side.json').unlink()
    if damage:
        with pytest.raises(ValueError,match=reason):m.read_probe_result(tmp_path,dict(pid=7),c)
    else:assert m.read_probe_result(tmp_path,dict(pid=7),c)['status']=='EVENT_LINK_COMPLETE_PENDING_REVIEW'


@pytest.mark.parametrize('failure',[None,'process','missing_event','postcheck','timeout','process_and_postcheck'])
def test_control_file_chain_one_child_postcheck_failure_and_unknown_writer(tmp_path,monkeypatch,failure):
    m=load();p=tmp_path/'p';p.mkdir();a=tmp_path/'a';a.mkdir()
    put(a/'receipt.json',{});put(a/'source_bytes.json',{})
    c=dict(context_cfg(),schema_version='cupti-event-b/0.1.0',controller_commit='f'*40,native_commit=m.NATIVE_COMMIT,
        analysis_commit=m.NATIVE_COMMIT,python=sys.executable,target_python=sys.executable,server_root=str(tmp_path/'YLQ'),
        a_root=str(a),reviewed_a_receipt_sha256='a'*64,activity_policy_version='cupti-api22-activity-policy/0.2.0',budget=m.fixed_budget())
    put(p/'delivery.json',c)
    for name in ('cupti_event_b.py','cupti_event_probe.py','run_cupti_event_b.ps1'):(p/name).write_bytes((ROOT/'scripts'/name).read_bytes())
    put(p/'package_manifest.json',dict(files=[dict(path=f.name,bytes=f.stat().st_size,sha256=sha(f)) for f in p.iterdir()]))
    support=load('memset_micro');checks=[];argvs=[]
    def checked(*args):
        checks.append('A')
        if failure in ('postcheck','process_and_postcheck') and len(checks)==2:raise ValueError('CPU_CHANGED_A')
        return dict(acfg=c,a_root=a,verification=dict(mode='CPU_STATIC_CHECK_DOUBLE'))
    def command(argv,cwd,log,**kw):
        argvs.append((argv,kw));process=dict(pid=7,status='EXITED',exit_code=2 if failure in ('process','missing_event','process_and_postcheck') else 0,timed_out=failure=='timeout')
        if failure=='timeout':process.update(status='BLOCKED',descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY')
        put(Path(log).with_suffix('.process.json'),process)
        if failure not in ('process','timeout','process_and_postcheck'):
            folder,r=result_fixture(Path(cwd),c,missing=failure=='missing_event');seal_result(folder,r)
        if failure in ('process','missing_event','timeout','process_and_postcheck'):raise ValueError('CPU_CHILD_STOP')
        return process
    support.command=command
    monkeypatch.setattr(m,'components',lambda *args:({'startup_resources':lambda *a:{}},support))
    monkeypatch.setattr(m,'checked_a',checked)
    monkeypatch.setattr(m,'sys',SimpleNamespace(executable=sys.executable,version_info=(3,11,16)))
    for n in m.FORBIDDEN:monkeypatch.delenv(n,raising=False)
    rc=m.run(p,enabled=True,reviewed='a'*64)
    assert rc==(0 if failure is None else 2) and checks==['A','A'] and len(argvs)==1
    argv,kw=argvs[0];assert kw['timeout']==120 and '--run-reviewed-event' in argv and '-I' in argv and '-S' in argv
    assert kw['env']['CUDA_VISIBLE_DEVICES']=='3'
    out=tmp_path/'YLQ/diagnostics'/('cupti_event_'+'f'*12+'_once');receipt=json.loads((out/'receipt.json').read_text())
    assert receipt['process']['pid']==7 and receipt['post_execution_static_rechecked']==(failure not in ('postcheck','process_and_postcheck'))
    assert receipt['formal_eligible'] is False and receipt['COE_admission']=='NOT_ASSESSED'
    assert json.loads((out/'static_precheck.json').read_text())['mode']=='CPU_STATIC_CHECK_DOUBLE'
    if failure=='process_and_postcheck':
        assert receipt['operation_error']=='ValueError:CPU_CHILD_STOP' and receipt['postcheck_error']=='ValueError:CPU_CHANGED_A'
    archives=list((tmp_path/'YLQ/transfer').glob('*.zip'))
    assert bool(archives)==(failure!='timeout')
    if archives:
        import zipfile
        with zipfile.ZipFile(archives[0]) as z:assert z.testzip() is None and 'receipt.json' in z.namelist()


@pytest.mark.parametrize('damage',[None,'default','hash','reviewed'])
def test_ps51_entry_explicit_switch_and_hash_gate(tmp_path,damage):
    launcher=ROOT/'scripts/run_cupti_event_b.ps1';assert launcher.is_file()
    (tmp_path/launcher.name).write_bytes(launcher.read_bytes())
    driver=tmp_path/'cupti_event_b.py';driver.write_text('from pathlib import Path\nPath(__file__).with_name("entered.txt").write_text("CPU_ONLY")\n')
    put(tmp_path/'delivery.json',dict(python=sys.executable,reviewed_a_receipt_sha256='a'*64,
        bootstrap_files=[dict(path=driver.name,sha256='b'*64 if damage=='hash' else sha(driver))]))
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    argv=[str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(tmp_path/launcher.name)]
    if damage!='default':argv+=['-RunReviewedEvent','-ReviewedAReceiptSha256','b'*64 if damage=='reviewed' else 'a'*64]
    r=subprocess.run(argv,cwd=tmp_path,capture_output=True,timeout=20)
    assert (r.returncode==0)==(damage is None) and (tmp_path/'entered.txt').exists()==(damage is None)


def test_real_isolated_parent_consumer_uses_verified_stdlib_reader_without_pythonpath(tmp_path):
    c=context_cfg();put(tmp_path/'probe_config.json',{});folder,r=result_fixture(tmp_path,c);seal_result(folder,r)
    boot='import runpy,json,sys;m=runpy.run_path(sys.argv[1]);m["read_probe_result"](sys.argv[2],{"pid":7},json.loads(sys.argv[3]))'
    env=os.environ.copy();env.pop('PYTHONPATH',None)
    p=subprocess.run([sys.executable,'-I','-S','-B','-c',boot,str(ROOT/'scripts/cupti_event_b.py'),str(tmp_path),json.dumps(c)],
        cwd=tmp_path,capture_output=True,timeout=20,env=env)
    assert p.returncode==0,p.stderr.decode(errors='replace')
