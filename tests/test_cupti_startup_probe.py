"""Startup-only control tests. GPU/process providers are explicit CPU doubles."""
import hashlib,importlib.util,json,os,subprocess,sys
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT=Path(__file__).resolve().parents[1]
def load(name):
    path=ROOT/'scripts'/(name+'.py');assert path.is_file(),'bounded startup probe missing'
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def put(p,v):
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def contract():
    return dict(schema_version='cupti-startup-probe/0.1.0',role='Engineering',
        native_commit='ddc7abc8a1bf09b40fa868bf1a0c319f3977f80a',session_id='startup_test',
        model_process_budget=0,probe_process_budget=1,cupti_sessions=1,nsight_profiles=0,
        context_policy='PYTORCH_EMPTY64_ONE_STREAM_DRAIN_BEFORE_SESSION',allocation_bytes=64)

def test_default_probe_refuses_before_read_or_context_creation(tmp_path):
    m=load('cupti_startup_probe')
    with pytest.raises(ValueError,match='EXPLICIT'):m.run(tmp_path/'absent',tmp_path/'out')
    assert list(tmp_path.iterdir())==[]

@pytest.mark.parametrize('key,value',[('allocation_bytes',65),('model_process_budget',1),('probe_process_budget',2),
    ('cupti_sessions',2),('context_policy','MODEL'),('native_commit','a'*40),('session_id','../x')])
def test_probe_fixed_scope_cannot_become_model_or_multisession(key,value):
    c=contract();c[key]=value
    with pytest.raises(ValueError):load('cupti_startup_probe').validate_contract(c)


@pytest.mark.parametrize('damage',[None,'torch_version','origin','gpu','runtime'])
def test_context_setup_is_before_subscription_and_has_no_model(tmp_path,monkeypatch,damage):
    m=load('cupti_startup_probe');calls=[];site=tmp_path/'site';site.mkdir()
    runtime=tmp_path/'cudart64_12.dll';runtime.write_bytes(b'CPU_RUNTIME_DOUBLE_NOT_LOADED')
    gpu='GPU-0d8fafe6-a1e9-33cc-25fb-632316736455';pci='00000000:E1:00.0'
    cfg=dict(site_root=str(site),gpu_uuid=gpu,gpu_pci=pci,runtime=dict(path=str(runtime),sha256=sha(runtime)),context_policy='p')
    torch=SimpleNamespace(__version__='wrong' if damage=='torch_version' else '2.6.0+cu124',
        __file__=str((tmp_path if damage=='origin' else site)/'torch/__init__.py'),
        version=SimpleNamespace(cuda='12.4'),uint8='uint8',
        empty=lambda n,**kw:calls.append(('empty',n,kw)) or 'allocation',
        cuda=SimpleNamespace(set_device=lambda n:calls.append(('set_device',n)),
            Stream=lambda **kw:calls.append(('stream',kw)) or 'stream',synchronize=lambda n:calls.append(('drain',n))))
    monkeypatch.setitem(sys.modules,'torch',torch)
    import exposedpath.platform_adapter as platform
    monkeypatch.setattr(platform,'cuda_identity_native',lambda cuda:dict(
        gpu_uuid='GPU-00000000-0000-0000-0000-000000000000' if damage=='gpu' else gpu,pci_bus_id=pci))
    class F:
        def __init__(self,fn):self.fn=fn
        def __call__(self,*a):return self.fn(*a)
    def module_path(h,buf,n):buf.value=str(runtime);return len(buf.value)
    kernel=SimpleNamespace(GetModuleHandleW=F(lambda n:1),GetModuleFileNameW=F(module_path))
    monkeypatch.setattr(m.ctypes,'WinDLL',lambda *a,**kw:kernel)
    if damage=='runtime':cfg['runtime']['sha256']='f'*64
    if damage:
        with pytest.raises(ValueError):m.prepare_context(cfg)
        assert not any(c[0]=='empty' for c in calls)
    else:
        facts,keepalive=m.prepare_context(cfg)
        assert calls==[('set_device',0),('empty',64,dict(dtype='uint8',device='cuda:0')),('stream',dict(device=0)),('drain',0)]
        assert facts['model_loaded'] is False and facts['subscription_active_during_setup'] is False
        assert keepalive==('allocation','stream')

@pytest.mark.parametrize('failure',[None,'context','startup','close','missing_diagnostic'])
def test_probe_order_and_raw_startup_failure_survive_without_gpu(tmp_path,failure):
    m=load('cupti_startup_probe');calls=[];out=tmp_path/'p';out.mkdir()
    c=contract();c['session']={}
    step=dict(operation='cuptiActivityEnable',status_domain='CUPTI',status_code=37,success=False,
        activity_kind=36,activity_name='CUDA_EVENT',detail='')
    init=dict(schema_version='cupti-timeline-startup/0.1.0',succeeded=failure!='startup',overflow=0,
        steps=[step] if failure=='startup' else [],failure=step if failure=='startup' else None)
    def prepare(c):
        calls.append('context')
        if failure=='context':raise ValueError('CPU_CONTEXT_FAILURE')
        return dict(mode='CPU_CONTEXT_DOUBLE'),object()
    class Session:
        def __init__(self,c,p,**kw):
            self.output=p;self.startup=init;self.startup_report_error=None;calls.append('construct')
        def save(self):
            self.output.mkdir();put(self.output/'capture.json',dict(initialization=init));put(self.output/'receipt.json',{})
        def __enter__(self):
            calls.append('open')
            if failure=='startup':self.save();raise ValueError('CPU_OPEN_FAILED:3')
            return self
        def mark(self,*a):calls.append('mark')
        def __exit__(self,*a):
            calls.append('close');self.save()
            if failure=='missing_diagnostic':self.startup=None
            if failure=='close':raise ValueError('CPU_CLOSE_FAILED:4')
    result=m.exercise(c,out,prepare,Session)
    assert calls[0]=='context'
    assert result['status']==('STARTUP_OPEN_CLOSE_COMPLETE_PENDING_REVIEW' if failure is None else 'BLOCKED')
    assert result['original_model_failure_resolved'] is False and result['COE_admission']=='NOT_ASSESSED'
    assert result['startup_failure']==(step if failure=='startup' else None)
    assert bool(result['error'])==(failure is not None)
    if failure=='context':assert calls==['context'] and result['capture_sha256'] is None
    elif failure=='startup':assert calls==['context','construct','open'] and result['capture_sha256']
    else:assert calls==['context','construct','open','mark','close']

def test_unreviewed_controller_never_loads_package_or_components(tmp_path,monkeypatch):
    m=load('cupti_startup_b');seen=[]
    monkeypatch.setattr(m,'components',lambda *a:seen.append(True))
    with pytest.raises(ValueError,match='EXPLICIT'):m.run(tmp_path)
    assert not seen and list(tmp_path.iterdir())==[]

@pytest.mark.parametrize('failure',[None,'process','postcheck','result'])
def test_actual_startup_controller_file_chain_rechecks_and_seals_original_exit(tmp_path_factory,monkeypatch,failure):
    m=load('cupti_startup_b');base=tmp_path_factory.mktemp('s');package=base/'p';package.mkdir()
    a=base/'a';a.mkdir();put(a/'receipt.json',{});put(a/'source_bytes.json',{})
    cfg=dict(schema_version='cupti-startup-b/0.1.0',controller_commit='f'*40,
        native_commit=m.NATIVE_COMMIT,python=sys.executable,target_python=sys.executable,site_root='site',
        code_root=str(ROOT),server_root=str(base/'YLQ'),a_root=str(a),reviewed_a_receipt_sha256='a'*64,
        budget=m.fixed_budget(),gpu_uuid='uuid',gpu_pci='pci',runtime=dict(path='rt',sha256='b'*64),
        session_id='startup_test',client=dict(path='cl',sha256='c'*64),cupti=dict(path='cu',sha256='d'*64))
    put(package/'delivery.json',cfg)
    for n in ('cupti_startup_b.py','cupti_startup_probe.py','run_cupti_startup_b.ps1'):
        (package/n).write_bytes((ROOT/'scripts'/n).read_bytes())
    put(package/'package_manifest.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in package.iterdir()]))
    s=importlib.util.spec_from_file_location('cpu_support',ROOT/'scripts/memset_micro.py')
    support=importlib.util.module_from_spec(s);s.loader.exec_module(support)
    calls=[];checks=[]
    def checked(c,stage,helper):
        checks.append('A')
        if failure=='postcheck' and len(checks)==2:raise ValueError('CPU_CHANGED_A')
        return dict(acfg=cfg,a_root=a)
    def command(argv,cwd,log,**kw):
        calls.append((argv,kw));r=dict(pid=99,status='EXITED',exit_code=1 if failure=='process' else 0,timed_out=False)
        put(Path(log).with_suffix('.process.json'),r)
        if r['exit_code']:raise ValueError('CPU_PROCESS_EXIT')
        result=dict(schema_version='cupti-startup-probe-result/0.1.0',status='STARTUP_OPEN_CLOSE_COMPLETE_PENDING_REVIEW',
            pid=99,config_sha256=sha(Path(cwd)/'probe_config.json'),original_model_failure_resolved=False,
            COE_admission='NOT_ASSESSED',startup_failure=None,error=None,
            capture_sha256=sha(Path(cwd)/'probe_config.json'),session_receipt_sha256=sha(Path(cwd)/'probe_config.json'))
        if failure=='result':result['pid']=100
        put(Path(cwd)/'probe/result.json',result)
        # Explicit CPU file consumer double below: production consumer validates all raw/session hashes.
        return r
    support.command=command
    monkeypatch.setattr(m,'checked_a',checked)
    monkeypatch.setattr(m,'components',lambda *a:({'startup_resources':lambda *a:{}},support))
    monkeypatch.setattr(m,'read_probe_result',lambda out,process,cfg:m.require(
        json.loads((out/'probe/result.json').read_text())['pid']==process['pid'],'PROBE_PID'))
    monkeypatch.setattr(m,'sys',SimpleNamespace(executable=sys.executable,version_info=(3,11,16)))
    for n in m.FORBIDDEN:monkeypatch.delenv(n,raising=False)
    rc=m.run(package,enabled=True,reviewed='a'*64)
    assert rc==(0 if failure is None else 2) and checks==['A','A'] and len(calls)==1
    assert calls[0][1]['timeout']==120 and calls[0][1]['env']['CUDA_VISIBLE_DEVICES']=='3'
    assert '--run-reviewed-startup' in calls[0][0] and '-I' in calls[0][0] and '-S' in calls[0][0]
    with __import__('zipfile').ZipFile(next((base/'YLQ/transfer').glob('*.zip'))) as z:
        r=json.loads(z.read('receipt.json'));assert r['process']['pid']==99
        assert r['process']['exit_code']==(1 if failure=='process' else 0)
        assert r['post_execution_static_rechecked']==(failure!='postcheck')
        assert (r['status']=='BLOCKED')==(failure is not None)
        assert r['budget']['model_process_budget']==0 and r['COE_admission']=='NOT_ASSESSED'

def test_real_ps51_default_entry_refuses_without_configuration(tmp_path):
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    p=ROOT/'scripts/run_cupti_startup_b.ps1';assert p.is_file()
    r=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(p)],cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode!=0 and b'Explicit reviewed startup' in r.stderr and b'delivery.json' not in r.stderr


@pytest.mark.parametrize('damage',[None,'bootstrap','reviewed_hash'])
def test_real_ps51_explicit_entry_runs_only_hash_bound_cpu_driver(tmp_path,damage):
    launcher=ROOT/'scripts/run_cupti_startup_b.ps1';(tmp_path/launcher.name).write_bytes(launcher.read_bytes())
    driver=tmp_path/'cupti_startup_b.py';driver.write_text('from pathlib import Path\nPath(__file__).with_name("entered.txt").write_text("CPU_DOUBLE")\n')
    put(tmp_path/'delivery.json',dict(python=sys.executable,reviewed_a_receipt_sha256='a'*64,
        bootstrap_files=[dict(path=driver.name,sha256=sha(driver) if damage!='bootstrap' else 'b'*64)]))
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    p=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(tmp_path/launcher.name),
        '-RunReviewedStartup','-ReviewedAReceiptSha256','b'*64 if damage=='reviewed_hash' else 'a'*64],
        cwd=tmp_path,capture_output=True,timeout=20)
    assert (p.returncode==0)==(damage is None) and (tmp_path/'entered.txt').exists()==(damage is None)


@pytest.mark.parametrize('damage',[None,'code_root','library_path','receipt_version','source'])
def test_actual_a_hash_file_and_execution_binding(tmp_path,damage):
    m=load('cupti_startup_b');a=tmp_path/'a';a.mkdir();code=tmp_path/'code';code.mkdir()
    (code/'x.py').write_bytes(b'# fixed\n')
    for n in ('client','cupti','runtime'):(a/(n+'.dll')).write_bytes(n.encode())
    c=dict(a_root=str(a),code_root=str(code),server_root=str(tmp_path),python='python')
    cfg=dict(code_root=str(code),server_root=str(tmp_path),python='python',execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT)
    put(a/'delivery.json',cfg)
    put(a/'source_bytes.json',[dict(path='x.py',bytes=8,sha256=sha(code/'x.py'))])
    put(a/'build/build.json',dict(client=str(a/'client.dll'),vendor_gpu_executed=False,
        binaries=[dict(path='client.dll',bytes=6,sha256=sha(a/'client.dll'))]))
    for n in ('cupti','runtime'):put(a/(n+'_file.json'),dict(path=str(a/(n+'.dll')),sha256=sha(a/(n+'.dll'))))
    for n in ('client','cupti','runtime'):c[n]=dict(path=str(a/(n+'.dll')),sha256=sha(a/(n+'.dll')))
    r=dict(schema_version='cupti-timeline-stage-a-receipt/0.1.1',phase='A',status='STATIC_READY_FOR_REVIEW',error=None,
        B_authorized=False,execution_commit=m.NATIVE_COMMIT,analysis_commit=m.NATIVE_COMMIT,
        startup_diagnostic_version='cupti-timeline-startup/0.1.0',stage_a_cuda_programs_executed=0,
        model_process_budget=0,micro_process_budget=0,profile_budget=0)
    if damage=='receipt_version':r['schema_version']='cupti-timeline-stage-a-receipt/0.1.0'
    put(a/'receipt.json',r)
    put(a/'artifact_manifest.json',dict(files=[dict(path=p.relative_to(a).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in a.rglob('*') if p.is_file()]))
    for n,k in [('receipt.json','reviewed_a_receipt_sha256'),('artifact_manifest.json','a_manifest_sha256'),('delivery.json','a_delivery_sha256')]:c[k]=sha(a/n)
    support=load('memset_micro');support.tree=lambda cfg,commit:None
    stage=dict(bind_checkout_modules=lambda cfg:None)
    if damage=='code_root':c['code_root']=str(tmp_path/'other_code')
    if damage=='library_path':
        other=tmp_path/'other.dll';other.write_bytes(b'OTHER');c['client']=dict(path=str(other),sha256=sha(other))
    if damage=='source':(code/'x.py').write_bytes(b'# altered\n')
    if damage:
        with pytest.raises(ValueError):m.checked_a(c,stage,support)
    else:assert m.checked_a(c,stage,support)['acfg']==cfg


@pytest.mark.parametrize('damage',[None,'pid','kind','quality','marker','raw_hash'])
def test_real_isolated_cpu_consumer_validates_same_file_chain(tmp_path,damage):
    m=load('cupti_startup_b');out=tmp_path/'o';folder=out/'probe';(folder/'timeline').mkdir(parents=True)
    c=dict(code_root=str(ROOT),session_id='s',client=dict(sha256='a'*64),cupti=dict(sha256='b'*64),runtime=dict(sha256='c'*64))
    put(out/'probe_config.json',{})
    init=dict(schema_version='cupti-timeline-startup/0.1.0',succeeded=True,overflow=0,failure=None,
        steps=[dict(operation='cuptiActivityEnable',status_domain='CUPTI',status_code=0,success=True,
            activity_kind=k,activity_name='CPU_RECORD_FIXTURE',detail='') for k in [5,4,10,1,2,38,9,37,36]])
    if damage=='kind':init['steps'].pop()
    raw=dict(pid=7,session_id='s',source='TARGET_CUPTI',initialization=init,
        quality=dict(closed=True,errors=[],overflow=0,dropped=0,dropped_query_errors=0),
        markers=[dict(label='CUPTI_STARTUP_PROBE_CONTEXT_READY')])
    if damage=='quality':raw['quality']['dropped']=1
    if damage=='marker':raw['markers']=[]
    if damage=='pid':raw['pid']=8
    put(folder/'timeline/capture.json',raw)
    put(folder/'timeline/receipt.json',dict(pid=7,session_id='s',open_code=0,close_code=0,
        verification_mode='TARGET_CUPTI_UNQUALIFIED',model_error_type=None,
        capture_sha256=sha(folder/'timeline/capture.json'),client_sha256='a'*64,cupti_sha256='b'*64))
    put(folder/'context.json',dict(pid=7,setup_drained=True,subscription_active_during_setup=False,model_loaded=False,runtime_sha256='c'*64))
    r=dict(schema_version='cupti-startup-probe-result/0.1.0',status='STARTUP_OPEN_CLOSE_COMPLETE_PENDING_REVIEW',
        error=None,pid=7,session_id='s',native_commit=m.NATIVE_COMMIT,config_sha256=sha(out/'probe_config.json'),
        original_model_failure_resolved=False,COE_admission='NOT_ASSESSED',context_sha256=sha(folder/'context.json'),
        capture_sha256=sha(folder/'timeline/capture.json'),session_receipt_sha256=sha(folder/'timeline/receipt.json'))
    if damage=='raw_hash':r['capture_sha256']='d'*64
    put(folder/'result.json',r)
    boot='import json,runpy,sys;m=runpy.run_path(sys.argv[1]);m["read_probe_result"](sys.argv[2],{"pid":7},json.loads(sys.argv[3]))'
    p=subprocess.run([sys.executable,'-I','-S','-B','-c',boot,str(ROOT/'scripts/cupti_startup_b.py'),str(out),json.dumps(c)],
        cwd=tmp_path,capture_output=True,timeout=20)
    assert (p.returncode==0)==(damage is None),p.stderr.decode(errors='replace')
