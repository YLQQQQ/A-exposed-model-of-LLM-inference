from copy import deepcopy
import importlib
import json
from pathlib import Path

import pytest

from test_submit_effect_bridge import sample
assert Path(sample.__code__.co_filename).resolve()==Path(__file__).with_name('test_submit_effect_bridge.py').resolve()


def module():
    spec=importlib.util.find_spec('analysis.cupti_timeline')
    assert spec is not None, 'new-source timeline adapter missing'
    return importlib.import_module('analysis.cupti_timeline')


def capture():
    v=sample();v['schema_version']='cupti-timeline-capture/0.1.0';v['source']='HOST_SDK_DOUBLE'
    for i,c in enumerate(v['callbacks']):c.update(cbid=100+i,closed=True,binding_status=0,ptsz=False,
        native_context=42,exit_context=c['context'],exit_native_context=42)
    cb={(c['domain'],c['pid'],c['correlation']):c for c in v['callbacks']}
    api=[dict(a,kind='API',cbid=cb[(a['domain'],a['pid'],a['correlation'])]['cbid']) for a in v.pop('apis')]
    sync=[dict(y,kind='SYNC',domain='UNSPECIFIED',flags=3,pid=7) for y in v.pop('synchronizations')]
    effects=v.pop('effects')
    for e in effects:e.update(graph_node=0,runtime_correlation=14 if e['kind']=='MEMCPY' else 0)
    v['records']=api+effects+sync+[dict(id='ctx',kind='CONTEXT',context=3,device=0,stream=4,flags=0)]
    return v


def test_new_source_full_file_chain_uses_real_parents_not_nsight_shaped_fake_fields(tmp_path):
    raw=capture();scope=raw.pop('scope')
    p=tmp_path/'capture.json';p.write_text(json.dumps(raw));s=tmp_path/'scope.json';s.write_text(json.dumps(scope))
    r=module().analyze_files(p,s,tmp_path/'derived')
    assert r['result']['coe_ns']==20 and r['result']['sync_intersection_ns']==15
    assert r['result']['logical_zero_call_ids']==[3]
    assert r['input']['clock']=='CUPTI_TIMESTAMP_NS' and r['input']['collector']=='INDEPENDENT_CUPTI'
    assert r['result']['provider_qualification']=='NOT_GRANTED_BY_THIS_CONSUMER'
    assert (tmp_path/'derived/result.json').is_file()
    with pytest.raises(FileExistsError):module().analyze_files(p,s,tmp_path/'derived')


@pytest.mark.parametrize('damage,reason',[
    ('version','VERSION'),('scope_session','SESSION'),('missing_binding','BINDING'),
    ('ptsz','ENTRY_NOT_QUALIFIED'),('duplicate_sync_domain','SYNC'),('event','EVENT'),
    ('graph','GRAPH'),('api_callback','CALLBACK'),('copy_runtime_conflict','COPY_RUNTIME'),
])
def test_codec_does_not_guess_missing_domain_scope_or_parameters(damage,reason):
    v=capture();s=v.pop('scope')
    if damage=='version':v['schema_version']='old-nsys'
    if damage=='scope_session':s['session_id']='different'
    if damage=='missing_binding':v['callbacks'][0]['binding_status']=-1
    if damage=='ptsz':v['callbacks'][0]['ptsz']=True
    if damage=='duplicate_sync_domain':
        # Same numeric corr in another runtime tree cannot identify the sync.
        c=deepcopy(v['callbacks'][-2]);c.update(id=20,correlation=104,enter_seq=30,exit_seq=31,parent_id=None)
        v['callbacks'].append(c)
    if damage=='event':v['records'].append(dict(id='event',kind='CUDA_EVENT'))
    if damage=='graph':v['records'][-3]['graph_node']=9
    if damage=='api_callback':v['records'][0]['cbid']+=1
    if damage=='copy_runtime_conflict':next(r for r in v['records'] if r['kind']=='MEMCPY')['runtime_correlation']=11
    with pytest.raises(ValueError,match=reason):module().to_evidence(v,s)


def test_marker_pairing_retains_original_labels_and_rejects_thread_migration():
    m=module()
    rows=[dict(action=1,time=1,tid=9,label='original helper label'),
          dict(action=0,time=2,tid=9,label='original point'),
          dict(action=2,time=3,tid=9,label='')]
    r=m.marker_ranges(rows)
    assert r['ranges']==[dict(label='original helper label',tid=9,start=1,end=3)]
    assert r['points']==[dict(label='original point',tid=9,time=2)]
    rows[-1]['tid']=10
    with pytest.raises(ValueError,match='MARKER'):m.marker_ranges(rows)


def marked_capture():
    v=capture();v.pop('scope')
    for c in v['callbacks']:c['enter_seq']+=2;c['exit_seq']+=2
    drain=dict(id=10,parent_id=None,domain='RUNTIME',correlation=16,name='cudaDeviceSynchronize',
        pid=7,tid=9,context=3,device=0,stream=4,start=1,end=5,enter_seq=1,exit_seq=2,
        return_code=0,params=None,cbid=165,closed=True,binding_status=-1,ptsz=False)
    v['callbacks'].insert(0,drain)
    v['records'].insert(0,dict(id='apiD',kind='API',domain='RUNTIME',correlation=16,
        cbid=165,pid=7,tid=9,name=drain['name'],start=1,end=5,return_code=0))
    v['records'].append(dict(id='physicalD',kind='SYNC',domain='UNSPECIFIED',correlation=16,
        flags=4,pid=7,context=3,stream=2**32-1,start=2,end=4))
    label=lambda prefix,kind:prefix+json.dumps(dict(identity=dict(run_id='run'),kind=kind))
    producer=dict(session_id=v['session_id'],pid=7,tid=9,run_id='run',actual_token_ids=[17],
        drain_label=label('EXPOSEDPATH_DRAIN_V1:','drain'),
        request_label=label('EXPOSEDPATH_BOUNDARY_V1:','request_start'),
        helper_label='EXPOSEDPATH_JSON_V1:'+json.dumps(dict(run_id='run',kind='sync')),
        token_label=label('EXPOSEDPATH_BOUNDARY_V1:','token_ready'))
    v['markers']=[dict(action=1,time=0,tid=9,label=producer['drain_label']),
        dict(action=2,time=6,tid=9,label=''),dict(action=0,time=10,tid=9,label=producer['request_label']),
        dict(action=1,time=39,tid=9,label=producer['helper_label']),
        dict(action=0,time=75,tid=9,label=producer['token_label']),dict(action=2,time=76,tid=9,label='')]
    return v,producer


def test_original_producer_labels_select_physical_drain_copy_sync_and_completion():
    m=module();assert hasattr(m,'select_scope'), 'same-clock producer bridge missing'
    v,p=marked_capture();s=m.select_scope(v,p)
    assert s['drain_end']==5 and s['request_start']==10 and s['completion_end']==75
    assert s['copy_api']=='api6' and s['sync_api']=='api8'
    assert m.analyze_scope(m.to_evidence(v,s))['coe_ns']==20


@pytest.mark.parametrize('damage',['missing_drain','foreign_label','wrong_token','missing_copy','future_completion'])
def test_producer_clock_bridge_rejects_missing_or_conflicting_physical_evidence(damage):
    v,p=marked_capture();m=module();assert hasattr(m,'select_scope'), 'same-clock producer bridge missing'
    if damage=='missing_drain':v['records']=[r for r in v['records'] if r['id']!='physicalD']
    if damage=='foreign_label':p['run_id']='other'
    if damage=='wrong_token':p['actual_token_ids']=[]
    if damage=='missing_copy':v['records']=[r for r in v['records'] if r['id']!='api6']
    if damage=='future_completion':v['markers'][-2]['time']=60
    with pytest.raises(ValueError):m.select_scope(v,p)


def test_closed_initialization_without_active_api_correlation_does_not_poison_request():
    v=capture();s=v.pop('scope')
    c=dict(v['callbacks'][0],id=100,parent_id=None,correlation=0,start=0,end=1,
        enter_seq=100,exit_seq=101,name='cudaSetup',params=None)
    v['callbacks'].append(c)
    v['records'].append(dict(id='early',kind='API',domain='RUNTIME',pid=7,tid=9,
        correlation=0,cbid=c['cbid'],start=0,end=1,return_code=0))
    e=module().to_evidence(v,s)
    assert module().analyze_scope(e)['coe_ns']==20 and e['closed_initialization_callback_ids']==[100]


def test_context_change_in_current_submission_is_not_treated_as_initialization():
    v=capture();s=v.pop('scope');v['callbacks'][0]['exit_context']=4
    with pytest.raises(ValueError,match='CONTEXT_CHANGED'):module().to_evidence(v,s)


def test_historical_event_is_closed_only_by_explicit_callback_and_later_drain():
    v=capture();s=v.pop('scope')
    c=dict(v['callbacks'][0],id=100,parent_id=None,name='cuEventRecord',domain='DRIVER',
        correlation=200,start=0,end=1,enter_seq=100,exit_seq=101)
    v['callbacks'].append(c)
    v['records'].append(dict(id='old-event',kind='CUDA_EVENT',context=3,stream=4,correlation=200))
    e=module().to_evidence(v,s)
    assert e['closed_prior_resource_ids']==['old-event']
    assert module().analyze_scope(e)['coe_ns']==20
    c['end']=30
    with pytest.raises(ValueError,match='EVENT_DEPENDENCY'):module().to_evidence(v,s)


def internal_capture():
    v=capture();s=v.pop('scope')
    for c in v['callbacks']:
        if c['id']==6:c.update(end=70,exit_seq=18)
        if c['id']==8:c.update(start=71,end=75,enter_seq=19,exit_seq=22)
        if c['id']==9:c.update(start=72,end=74,enter_seq=20,exit_seq=21)
    inner=dict(v['callbacks'][-1],id=10,parent_id=6,correlation=105,start=45,end=69,
        enter_seq=14,exit_seq=17,params=dict(native_stream=0),name='cuStreamSynchronize')
    v['callbacks'].append(inner)
    next(r for r in v['records'] if r['id']=='api6')['end']=70
    next(r for r in v['records'] if r['id']=='api8').update(start=71,end=75)
    next(r for r in v['records'] if r['kind']=='SYNC').update(start=72,end=74)
    v['records'].append(dict(id='internal-physical',kind='SYNC',domain='UNSPECIFIED',
        correlation=105,flags=3,context=3,stream=4,start=47,end=68))
    s['completion_end']=77
    return v,s


def test_observed_driver_sync_inside_copy_is_kept_as_internal_completion_not_invented_wait():
    v,s=internal_capture()
    e=module().to_evidence(v,s);r=module().analyze_scope(e)
    f=r['internal_synchronizations'][0]
    assert f['runtime_api_id']=='api6' and f['driver_call_id']==10
    assert f['necessary_member_ids']==['k','m','d'] and f['physical_activity_overlap_ns']==13
    assert f['driver_api_interval_ns'] is None and f['pure_host_blocking_ns'] is None


@pytest.mark.parametrize('damage',['no_parent','no_params','wrong_stream','failed','missing_submit_boundary','ambiguous_domain'])
def test_internal_completion_requires_actual_binding_and_submission_boundary(damage):
    v,s=internal_capture();d=v['callbacks'][-1]
    if damage=='no_parent':d['parent_id']=None
    if damage=='no_params':d['params']=None
    if damage=='wrong_stream':d['stream']=99
    if damage=='failed':d['return_code']=1
    if damage=='missing_submit_boundary':
        # Typed runtime correlation still proves the outer copy, but does not
        # prove when it was submitted relative to the inner synchronization.
        v['callbacks']=[c for c in v['callbacks'] if c['id']!=7]
    if damage=='ambiguous_domain':
        v['callbacks'].append(dict(d,id=111,domain='RUNTIME',parent_id=None,name='cudaStreamSynchronize',
            enter_seq=24,exit_seq=25,start=78,end=79))
    with pytest.raises(ValueError):module().analyze_scope(module().to_evidence(v,s))
