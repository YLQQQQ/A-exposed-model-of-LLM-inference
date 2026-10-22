"""New controlled-program wiring only; existing 72-case suite is not rerun."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).resolve().parents[1]


def entry():
    path=ROOT/'scripts/coe_cupti_controlled.py'
    assert path.is_file(), 'controlled CUPTI completion entry is missing'
    spec=importlib.util.spec_from_file_location('controlled_entry',path)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


class Fn:
    def __init__(self,fn):self.fn=fn
    def __call__(self,*args):return self.fn(*args)


def host_program(fail=None):
    """Only CUDA execution is replaced, not exercise order/markers/side files."""
    class Lib:pass
    lib=Lib();seen=[];state={'value':0}
    def call(name,args):
        seen.append((name,args))
        if name==fail:return 9
        if name=='ep_submit':state['value']=args[0]
        if name=='ep_read':return state['value']
        return 0
    for name in ('ep_prepare','ep_submit','ep_memset','ep_copy','ep_wait','ep_read'):
        setattr(lib,name,Fn(lambda *args,n=name:call(n,args)))
    return lib,seen


class Markers:
    def __init__(self):self.rows=[]
    def mark(self,action,label):self.rows.append((action,label))


def test_actual_exercise_fixed_members_and_completion_order(tmp_path):
    m=entry();lib,seen=host_program();marks=Markers()
    side=m.exercise(lib,marks,'controlled-1',7,9,tmp_path/'side.json',cpu_double=True)
    assert seen==[('ep_prepare',()),('ep_submit',(17,)),('ep_wait',()),
        ('ep_memset',(4,0)),('ep_submit',(23,)),('ep_memset',(0,123)),
        ('ep_copy',()),('ep_wait',()),('ep_read',()),('ep_submit',(29,)),('ep_wait',())]
    assert side['actual_token_ids']==[23] and side['mode']=='CPU_EXECUTION_DOUBLE'
    assert [r['step'] for r in side['calls']]==['drain','early_kernel','early_wait','positive_memset',
        'late_kernel','zero_memset','copy','paired_sync','host_read','future_kernel','future_wait']
    assert json.loads((tmp_path/'side.json').read_text())==side
    pushes=[label for action,label in marks.rows if action==1]
    assert len(pushes)==12 # eleven construction steps plus outer helper
    assert sum(a==1 for a,_ in marks.rows)==sum(a==2 for a,_ in marks.rows)


@pytest.mark.parametrize('failure',['ep_prepare','ep_submit','ep_memset','ep_copy','ep_wait'])
def test_failure_preserves_partial_and_does_not_continue(tmp_path,failure):
    m=entry();lib,seen=host_program(failure);marks=Markers()
    with pytest.raises(ValueError,match='CUDA_CALL'):
        m.exercise(lib,marks,'controlled-1',7,9,tmp_path/'side.json',cpu_double=True)
    side=json.loads((tmp_path/'side.json').read_text())
    assert side['status']=='BLOCKED' and side['calls'][-1]['return_code']==9
    assert not any(n=='ep_read' for n,_ in seen)


def test_default_import_and_run_require_explicit_authorization_before_library_load(tmp_path):
    m=entry()
    with pytest.raises(ValueError,match='EXPLICIT'):
        m.run(tmp_path/'missing.json',tmp_path/'out')
    assert not (tmp_path/'out').exists()
    with pytest.raises(ValueError,match='EXPLICIT'):
        m.bounded_run(tmp_path/'missing.json',tmp_path/'out')


def test_independent_reference_uses_raw_intervals_and_literal_members(tmp_path):
    module=entry()
    assert hasattr(module,'independent_intersection'),'independent endpoint calculation missing'
    assert module.independent_intersection([40,70],[[30,55],[56,60],[61,62]])==20
    assert module.independent_intersection([45,70],[[30,55],[56,60],[61,62]])==15
    assert module.independent_intersection([40,70],[[1,2]])==0


def controlled_files(folder):
    """Literal SDK-shaped CPU input; never an actual CUPTI/GPU reference."""
    m=entry();lib,_=host_program();marks=Markers()
    side=m.exercise(lib,marks,'controlled-1',7,9,folder/'side.json',cpu_double=True)
    # Endpoints are only for exercising the file/identity chain. Target answers
    # are to be obtained from future captured intervals, not these numbers.
    slots=[('drain',1,5,165,'cudaDeviceSynchronize'),
        ('early_kernel',10,11,211,'cudaLaunchKernel'),
        ('early_wait',15,18,131,'cudaStreamSynchronize'),
        ('positive_memset',20,22,51,'cudaMemsetAsync'),
        ('late_kernel',26,28,211,'cudaLaunchKernel'),
        ('zero_memset',29,30,51,'cudaMemsetAsync'),
        ('copy',40,44,41,'cudaMemcpyAsync'),
        ('paired_sync',45,70,131,'cudaStreamSynchronize'),
        ('future_kernel',80,84,211,'cudaLaunchKernel'),
        ('future_wait',96,100,131,'cudaStreamSynchronize')]
    raw=dict(schema_version='cupti-timeline-capture/0.1.0',source='HOST_SDK_DOUBLE',
        session_id='controlled-1',pid=7,clock='CUPTI_TIMESTAMP_NS',callbacks=[],records=[],markers=[],
        quality=dict(closed=True,errors=[],overflow=0,dropped=0,dropped_query_errors=0,dropped_scopes=[[3,4]]))
    for i,(step,a,b,cbid,name) in enumerate(slots,1):
        params=dict(native_stream=0)
        if step in ('positive_memset','zero_memset'):
            params.update(count=4 if step=='positive_memset' else 0,value=0 if step=='positive_memset' else 123)
        if step=='copy':params.update(count=4,copy_kind=2)
        cb=dict(id=i,parent_id=None,domain='RUNTIME',correlation=100+i,name=name,cbid=cbid,
            pid=7,tid=9,device=0,context=3,stream=4,start=a,end=b,enter_seq=i*4,exit_seq=i*4+3,
            return_code=0,params=params,closed=True,ptsz=False,binding_status=0,
            native_context=42,exit_native_context=42,exit_context=3)
        raw['callbacks'].append(cb);raw['records'].append(dict(cb,id='api-'+step,kind='API'))
        label=next(v['label'] for v in side['calls'] if v['step']==step)
        raw['markers'] += [dict(action=1,time=a,tid=9,label=label),dict(action=2,time=b,tid=9,label='')]
        if step in ('drain','early_wait','paired_sync','future_wait'):
            raw['records'].append(dict(id='sync-'+step,kind='SYNC',domain='UNSPECIFIED',pid=7,
                context=3,stream=2**32-1 if step=='drain' else 4,correlation=100+i,
                flags=4 if step=='drain' else 3,start=a+1,end=b-1))
    for step,kind,a,b,extra in [('early_kernel','KERNEL',12,14,{}),
        ('positive_memset','MEMSET',24,25,dict(bytes=4,value=0)),
        ('late_kernel','KERNEL',30,55,{}),('copy','MEMCPY',61,62,dict(bytes=4,copy_kind=2)),
        ('future_kernel','KERNEL',90,95,{})]:
        parent=next(c for c in raw['callbacks'] if c['name'] in ('cudaLaunchKernel','cudaMemsetAsync','cudaMemcpyAsync')
            and c['correlation']==101+next(i for i,s in enumerate(slots) if s[0]==step))
        did=parent['id']+1000;cid=parent['correlation']+1000
        dn,db={'KERNEL':('cuLaunchKernel',307),'MEMSET':('cuMemsetD8Async',216),
            'MEMCPY':('cuMemcpyDtoHAsync_v2',279)}[kind]
        child=dict(parent,id=did,parent_id=parent['id'],domain='DRIVER',correlation=cid,name=dn,cbid=db,
            enter_seq=parent['enter_seq']+1,exit_seq=parent['exit_seq']-1)
        raw['callbacks'].append(child);raw['records'].append(dict(child,id='driver-'+step,kind='API'))
        raw['records'].append(dict(id='effect-'+step,kind=kind,domain='DRIVER',pid=7,device=0,context=3,
            stream=4,correlation=cid,runtime_correlation=parent['correlation'] if kind=='MEMCPY' else 0,
            start=a,end=b,graph=0,graph_node=0,**extra))
    raw['records'].append(dict(id='context',kind='CONTEXT',context=3,device=0,stream=4,flags=0))
    raw['markers'] += [dict(action=0,time=8,tid=9,label=side['labels']['request_label']),
        dict(action=1,time=39,tid=9,label=side['labels']['helper_label']),
        dict(action=1,time=72,tid=9,label=side['calls'][8]['label']),dict(action=2,time=74,tid=9,label=''),
        dict(action=0,time=75,tid=9,label=side['labels']['token_label']),dict(action=2,time=76,tid=9,label='')]
    raw['markers'].sort(key=lambda r:r['time'])
    (folder/'capture.json').write_text(json.dumps(raw),encoding='utf8')
    return raw,side


def test_real_file_entry_agrees_with_construction_before_consumer(tmp_path):
    import subprocess,sys
    raw,side=controlled_files(tmp_path)
    before=[(tmp_path/n).read_bytes() for n in ('capture.json','side.json')]
    boot="import sys,runpy,json;sys.path.insert(0,sys.argv[1]);m=runpy.run_path(sys.argv[1]+'/scripts/coe_cupti_controlled.py');print(json.dumps(m['review'](sys.argv[2]+'/capture.json',sys.argv[2]+'/side.json',sys.argv[2]+'/derived')))"
    p=subprocess.run([sys.executable,'-I','-S','-B','-c',boot,str(ROOT),str(tmp_path)],capture_output=True,text=True,timeout=15)
    assert p.returncode==0,p.stderr
    r=json.loads(p.stdout)
    assert r['mode']=='CPU_EXECUTION_DOUBLE' and r['formal_eligible'] is False
    assert r['reference']['members']==['effect-early_kernel','effect-positive_memset','effect-late_kernel','effect-copy']
    assert r['reference']['terminal']=='effect-copy'
    assert r['reference']['excluded_ids']==['effect-future_kernel']
    assert r['reference']['expected_coe_ns']==16 and r['reference']['expected_sync_ns']==11
    assert [(tmp_path/n).read_bytes() for n in ('capture.json','side.json')]==before


@pytest.mark.parametrize('damage,reason',[
    ('side_args','SIDE_ARGUMENTS'),('wrong_run','SIDE_LABEL_IDENTITY'),('missing_effect','EFFECT:positive_memset'),
    ('wrong_stream','EFFECT_SCOPE'),('failed_sync','CALL_IDENTITY:paired_sync'),
    ('wrong_cbid','CALL_IDENTITY:copy'),
    ('duplicate_callback','CALL_DUPLICATE'),('late_early','EARLY_COMPLETION'),
    ('wrong_zero','PAYLOAD'),('future_before_read','FUTURE_ORDER')])
def test_new_reference_rejects_corrupt_evidence_without_qualification(tmp_path,damage,reason):
    raw,side=controlled_files(tmp_path)
    if damage=='side_args':side['calls'][3]['args']=[0,0]
    if damage=='wrong_run':side['run_id']='different'
    if damage=='missing_effect':raw['records']=[r for r in raw['records'] if r['id']!='effect-positive_memset']
    if damage=='wrong_stream':next(r for r in raw['records'] if r['id']=='effect-late_kernel')['stream']=5
    if damage=='failed_sync':next(c for c in raw['callbacks'] if c['id']==8)['return_code']=1
    if damage=='wrong_cbid':next(c for c in raw['callbacks'] if c['id']==7)['cbid']=999
    if damage=='duplicate_callback':raw['callbacks'].append(dict(raw['callbacks'][0]))
    if damage=='late_early':next(r for r in raw['records'] if r['id']=='effect-early_kernel')['end']=41
    if damage=='wrong_zero':next(c for c in raw['callbacks'] if c['id']==6)['params']['count']=1
    if damage=='future_before_read':
        # A late completion point must not legalize a post-completion slot.
        next(r for r in raw['markers'] if r['action']==0 and r['label']==side['labels']['token_label'])['time']=85
        next(r for r in raw['markers'] if r['time']==76)['time']=86
        raw['markers'].sort(key=lambda r:r['time'])
    with pytest.raises(ValueError,match=reason):entry().independent_reference(raw,side)


def test_isolated_source_binding_and_wrong_preloaded_origin(tmp_path):
    import subprocess,sys,hashlib
    m=entry();index={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in m.SOURCE_FILES}
    binding=tmp_path/'binding.json';binding.write_text(json.dumps(index))
    boot="""import sys,runpy,json,types
from pathlib import Path
m=runpy.run_path(sys.argv[1]+'/scripts/coe_cupti_controlled.py')
v=json.loads(Path(sys.argv[2]).read_text())
if sys.argv[3]=='conflict':
 fake=types.ModuleType('analysis');fake.__file__='/untrusted/analysis/__init__.py';sys.modules['analysis']=fake
if sys.argv[3]=='hash':v['analysis/cupti_timeline.py']='0'*64
m['bind_sources'](v)
assert not any(n=='torch' or n.startswith('torch.') for n in sys.modules)
print('CPU_BOUND_NO_VENDOR_LOAD')
"""
    for mode,reason in [('ok',None),('conflict','MODULE_ORIGIN:analysis'),('hash','SOURCE_HASH:analysis')]:
        p=subprocess.run([sys.executable,'-I','-S','-B','-c',boot,str(ROOT),str(binding),mode],
            cwd=tmp_path,capture_output=True,text=True,timeout=15)
        if reason:assert p.returncode!=0 and reason in p.stderr,p.stderr
        else:assert p.returncode==0 and p.stdout.strip()=='CPU_BOUND_NO_VENDOR_LOAD',p.stderr


def test_existing_session_opens_before_context_init_and_keeps_actual_read_order(tmp_path):
    m=entry();lib,seen=host_program();events=[]
    lib.ep_init=Fn(lambda device:events.append('init') or 0)
    lib.ep_stream_handle=Fn(lambda:0)
    def identity(uid,pci,cap):pci.value=b'0000:01:00.0';events.append('identity');return 0
    lib.ep_identity=Fn(identity)
    class Session(Markers):
        def __init__(self,*a,**k):super().__init__()
        def __enter__(self):events.append('open');return self
        def __exit__(self,*a):events.append('close')
    c=dict(session={},run_id='controlled-1',gpu_uuid='GPU-00000000-0000-0000-0000-000000000000',gpu_pci='0000:01:00.0')
    side=m.capture_program(lib,Session,c,tmp_path,7,9,cpu_double=True)
    assert events==['open','init','identity','close']
    assert side['actual_token_ids']==[23] and seen[0]==('ep_prepare',())


def test_closed_initialization_zero_correlations_do_not_poison_literal_local_reference(tmp_path):
    raw,side=controlled_files(tmp_path)
    template=dict(raw['callbacks'][0])
    raw['callbacks'] += [dict(template,id=901,correlation=0,start=0,end=0),
        dict(template,id=902,correlation=0,start=0,end=0)]
    # They remain Raw facts, but have no invented unique correlation or member.
    r=entry().independent_reference(raw,side)
    assert r['members']==['effect-early_kernel','effect-positive_memset','effect-late_kernel','effect-copy']
    assert r['closed_initialization_callback_ids']==[901,902]


@pytest.mark.parametrize('code',[0,7])
def test_bounded_process_wiring_preserves_code_and_timeout_with_cpu_process_double(tmp_path,monkeypatch,code):
    import subprocess
    seen=[]
    class Process:
        pid=123
        def __init__(self,argv,**kwargs):seen.append((argv,kwargs))
        def wait(self,timeout):seen.append(timeout);return code
    monkeypatch.setattr(subprocess,'Popen',Process)
    m=entry();out=tmp_path/'bounded'
    if code:
        with pytest.raises(ValueError,match='COMMAND_EXIT:process:7'):m.bounded_run(tmp_path/'cfg.json',out,enabled=True)
    else:m.bounded_run(tmp_path/'cfg.json',out,enabled=True)
    r=json.loads((out/'process.process.json').read_text())
    assert r['exit_code']==code and r['timed_out'] is False
    assert len(seen)==2 and seen[1]==120
    assert seen[0][0][1:4]==['-I','-S','-B']
    assert '--controlled-worker' in seen[0][0] and not (out/'run').exists()
