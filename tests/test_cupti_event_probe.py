"""Independent hand-built event chain; not CUDA event collection evidence."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[1]


def modules():
    from analysis.cupti_event_probe import analyze
    p=ROOT/'scripts/cupti_event_probe.py'
    spec=importlib.util.spec_from_file_location('_event_probe_test',p)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    return analyze,m


def chain():
    # Runtime 10 -> actual nested driver 11 -> event record correlation 111;
    # event-sync runtime 20 -> driver21 -> physical event7, NOT native handle99.
    calls=[];records=[];markers=[]
    for idx,name,corr,driver,dcorr,lo,hi in [(10,'cudaEventRecord',100,'cuEventRecord',111,10,20),
        (20,'cudaEventSynchronize',200,'cuEventSynchronize',211,30,40),
        (30,'cudaStreamSynchronize',300,'cuStreamSynchronize',311,50,60)]:
        base=dict(pid=7,tid=8,context=3,closed=True,return_code=0,ptsz=False)
        calls += [dict(base,id=idx,parent_id=None,domain='RUNTIME',name=name,correlation=corr,start=lo,end=hi,
            enter_seq=idx,exit_seq=idx+3,cbid=idx,params=dict(native_stream=55),binding_status=0,stream=4,device=0),
            dict(base,id=idx+1,parent_id=idx,domain='DRIVER',name=driver,correlation=dcorr,start=lo+1,end=hi-1,
                enter_seq=idx+1,exit_seq=idx+2,cbid=idx+1)]
        records += [dict(id=str(idx),kind='API',domain='RUNTIME',pid=7,tid=8,correlation=corr,cbid=idx,
            return_code=0,start=lo,end=hi)]
        label={10:'record',20:'event_sync',30:'stream_sync'}[idx]
        markers += [dict(action=1,label='EVENT-PROBE:s:'+label,tid=8,time=lo-1),dict(action=2,label='',tid=8,time=hi+1)]
    records += [dict(id='ctx',kind='CONTEXT',context=3,device=0,flags=0),dict(id='stream',kind='STREAM',context=3,stream=4),
        dict(id='event',kind='CUDA_EVENT',correlation=111,context=3,stream=4,event=7),
        dict(id='event_sync',kind='SYNC',correlation=211,context=3,stream=4294967295,event=7,flags=1,start=32,end=38),
        dict(id='stream_sync',kind='SYNC',correlation=311,context=3,stream=4,event=0,flags=3,start=52,end=58)]
    from exposedpath.cupti_timeline import activity_policy
    steps=[dict(operation='cuptiActivityEnableAndDump' if k in (9,37) else 'cuptiActivityEnable',
        activity_kind=k,activity_name=str(k),status_domain='CUPTI',status_code=0,success=True,detail='') for k in [5,4,10,1,2,38,9,37]]
    raw=dict(schema_version='cupti-timeline-capture/0.1.0',session_id='s',pid=7,clock='CUPTI_TIMESTAMP_NS',
        quality=dict(closed=True,errors=[],overflow=0,dropped=0,dropped_query_errors=0,dropped_scopes=[[3,4]]),
        callbacks=calls,records=records,markers=markers,
        initialization=dict(schema_version='cupti-timeline-startup/0.2.0',activity_policy=activity_policy(),
            succeeded=True,overflow=0,steps=steps,failure=None))
    side=dict(schema_version='cupti-event-probe-side/0.1.0',session_id='s',pid=7,tid=8,native_event=99,
        native_stream=55,calls=[dict(operation=x,return_code=0) for x in ('create','record','event_sync','stream_sync','destroy')])
    return raw,side


def test_independent_event_chain_is_association_not_open_success():
    analyze,_=modules();raw,side=chain();r=analyze(raw,side)
    assert r['event_record']=='event' and r['event_sync']=='event_sync' and r['stream']==4
    assert r['event_id']==7 and r['event_completion_timestamp']=='NOT_AVAILABLE_IN_API22'
    assert r['COE_admission']=='NOT_ASSESSED' and r['pytorch_coverage']=='NOT_GRANTED'


@pytest.mark.parametrize('damage,reason',[('missing_event','EVENT_COVERAGE'),('duplicate','EVENT_COVERAGE'),
    ('wrong_event','EVENT_SYNC'),('wrong_stream','STREAM_SCOPE'),('wrong_parent','PARENT'),
    ('failed','FAILED_CALL'),('loss','QUALITY'),('missing_range','RANGE'),('missing_api','API'),('policy','POLICY')])
def test_event_missing_or_wrong_link_stays_rejected(damage,reason):
    analyze,_=modules();raw,side=chain()
    if damage=='missing_event':raw['records']=[r for r in raw['records'] if r['kind']!='CUDA_EVENT']
    if damage=='duplicate':raw['records'].append({**raw['records'][-3],'id':'duplicate'})
    if damage=='wrong_event':raw['records'][-2]['event']=77
    if damage=='wrong_stream':raw['records'][-1]['stream']=9
    if damage=='wrong_parent':raw['callbacks'][1]['parent_id']=20
    if damage=='failed':side['calls'][1]['return_code']=21
    if damage=='loss':raw['quality']['dropped']=1
    if damage=='missing_range':raw['markers']=raw['markers'][2:]
    if damage=='missing_api':raw['records']=raw['records'][1:]
    if damage=='policy':raw['initialization']['activity_policy']['dependent_records']=[]
    with pytest.raises(ValueError,match=reason):analyze(raw,side)


def test_probe_default_never_reads_config_or_loads_cuda(tmp_path):
    _,m=modules()
    with pytest.raises(ValueError,match='EXPLICIT'):m.run(tmp_path/'missing',tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_probe_real_operation_order_and_file_chain_with_external_runtime_double(tmp_path):
    analyze,m=modules();raw,side=chain();seen=[]
    class F:
        def __init__(self,fn):self.fn=fn
        def __call__(self,*args):return self.fn(*args)
    from types import SimpleNamespace
    def create(ptr,flags):seen.append('create');ptr._obj.value=99;return 0
    rt=SimpleNamespace(cudaEventCreateWithFlags=F(create),
        cudaEventRecord=F(lambda *a:seen.append('record') or 0),
        cudaEventSynchronize=F(lambda *a:seen.append('event_sync') or 0),
        cudaStreamSynchronize=F(lambda *a:seen.append('stream_sync') or 0),
        cudaEventDestroy=F(lambda *a:seen.append('destroy') or 0))
    class Session:
        def mark(self,action,label):seen.append(('marker',action,label))
    facts=m.event_operations(rt,55,Session(),'s')
    assert [x for x in seen if isinstance(x,str)]==['create','record','event_sync','stream_sync','destroy']
    assert facts['native_event']==99 and facts['native_stream']==55
    # Full analyzer file wrapper preserves immutable sources and rejects absent
    # event despite otherwise successful open/close receipt.
    a=tmp_path/'capture.json';b=tmp_path/'side.json'
    a.write_text(json.dumps(raw));b.write_text(json.dumps(side));before=(a.read_bytes(),b.read_bytes())
    from analysis.cupti_event_probe import analyze_files
    out=tmp_path/'derived';assert analyze_files(a,b,out)['result']['event_id']==7
    assert (a.read_bytes(),b.read_bytes())==before


def test_api_activity_and_callback_timestamps_need_not_be_identical():
    analyze,_=modules();raw,side=chain()
    for r in raw['records']:
        if r['kind']=='API':r['start']-=1;r['end']+=1
    assert analyze(raw,side)['event_id']==7


def test_failed_event_call_saves_actual_code_and_stops_without_destroy_or_retry(tmp_path):
    _,m=modules();seen=[]
    class F:
        def __init__(self,fn):self.fn=fn
        def __call__(self,*a):return self.fn(*a)
    from types import SimpleNamespace
    def create(ptr,flags):ptr._obj.value=99;return 0
    rt=SimpleNamespace(cudaEventCreateWithFlags=F(create),cudaEventRecord=F(lambda *a:21),
        cudaEventSynchronize=F(lambda *a:seen.append('unexpected')),cudaStreamSynchronize=F(lambda *a:seen.append('unexpected')),
        cudaEventDestroy=F(lambda *a:seen.append('unexpected')))
    p=tmp_path/'side.json'
    with pytest.raises(ValueError,match='record:21'):m.event_operations(rt,55,SimpleNamespace(mark=lambda *a:None),'s',evidence_path=p)
    assert not seen and json.loads(p.read_text())['calls']==[dict(operation='create',return_code=0),dict(operation='record',return_code=21)]


@pytest.mark.parametrize('missing',[False,True])
def test_real_probe_entry_capture_side_review_receipt_chain_with_cpu_providers(tmp_path,monkeypatch,missing):
    import os,sys
    from types import SimpleNamespace
    from exposedpath import cupti_timeline as session_module
    from scripts import cupti_startup_probe as setup_module
    _,m=modules();raw,side=chain()
    if missing:raw['records']=[r for r in raw['records'] if r['kind']!='CUDA_EVENT']
    monkeypatch.setattr(m,'sys',SimpleNamespace(flags=SimpleNamespace(isolated=1,no_site=1),version_info=(3,11,16),executable=sys.executable))
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3');monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(setup_module,'prepare_context',lambda c:(dict(role='CPU_CONTEXT_DOUBLE_NOT_GPU'),(object(),SimpleNamespace(cuda_stream=55))))
    monkeypatch.setattr(m,'ctypes',SimpleNamespace(WinDLL=lambda *a,**k:object()))
    class Session:
        def __init__(self,c,out,**kw):self.out=out
        def __enter__(self):self.out.mkdir();return self
        def __exit__(self,*a):
            (self.out/'capture.json').write_text(json.dumps(raw));(self.out/'receipt.json').write_text('{"role":"CPU_SESSION_DOUBLE"}')
    monkeypatch.setattr(session_module,'CaptureSession',Session)
    def operations(*args,evidence_path):Path(evidence_path).write_text(json.dumps(side))
    monkeypatch.setattr(m,'event_operations',operations)
    cfg=dict(schema_version='cupti-event-probe/0.1.0',role='Engineering',session_id='s',
        budget=dict(processes=1,sessions=1,models=0,nsight_profiles=0,hard_seconds=120),target_python=sys.executable,
        context_policy='PYTORCH_EMPTY64_ONE_STREAM_DRAIN_BEFORE_SESSION',runtime=dict(path='CPU_NOT_LOADED'),
        session=dict(session_id='s',activity_policy_version='cupti-api22-activity-policy/0.2.0'))
    p=tmp_path/'config.json';p.write_text(json.dumps(cfg));out=tmp_path/'out'
    assert m.run(p,out,enabled=True)==(2 if missing else 0)
    receipt=json.loads((out/'result.json').read_text())
    assert bool(receipt['error'])==missing and receipt['COE_admission']=='NOT_ASSESSED'
    assert 'timeline/capture.json' in receipt['files'] and 'side.json' in receipt['files']
    assert (out/'review/review.json').exists()==(not missing)
