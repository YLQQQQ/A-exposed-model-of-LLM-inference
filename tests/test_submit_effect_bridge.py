"""Independent small trace oracles; no CUDA, model, or profiler is loaded."""
from copy import deepcopy
import importlib

import pytest


def bridge():
    spec=importlib.util.find_spec('exposedpath_v141.submit_effect_bridge')
    assert spec is not None, 'versioned API-to-effect bridge missing'
    return importlib.import_module('exposedpath_v141.submit_effect_bridge')


def sample():
    def cb(i,parent,domain,corr,name,begin,end,seq,params=None):
        return dict(id=i,parent_id=parent,domain=domain,correlation=corr,name=name,
            pid=7,tid=9,context=3,device=0,stream=4,start=begin,end=end,
            enter_seq=seq,exit_seq=seq+1,return_code=0,params=params)
    callbacks=[
        cb(1,None,'RUNTIME',11,'cudaLaunchKernel',10,16,1),
        cb(2,1,'DRIVER',101,'cuLaunchKernel',11,15,2),
        cb(3,None,'RUNTIME',12,'cudaMemsetAsync',17,19,5,dict(count=0,value=0,native_stream=0)),
        cb(4,None,'RUNTIME',13,'cudaMemsetAsync',20,26,7,dict(count=64,value=123,native_stream=0)),
        cb(5,4,'DRIVER',102,'cuMemsetD8Async',21,25,8),
        cb(6,None,'RUNTIME',14,'cudaMemcpyAsync',40,44,11,dict(count=8,copy_kind=2,native_stream=0)),
        cb(7,6,'DRIVER',103,'cuMemcpyDtoHAsync',41,43,12),
        cb(8,None,'RUNTIME',15,'cudaStreamSynchronize',45,70,15,dict(native_stream=0)),
        cb(9,8,'DRIVER',104,'cuStreamSynchronize',46,69,16),
    ]
    # ENTRY/EXIT are nested, not merely time-near. Set true global sequence order.
    for i,enter,exit in [(1,1,4),(2,2,3),(3,5,6),(4,7,10),(5,8,9),
                         (6,11,14),(7,12,13),(8,15,18),(9,16,17)]:
        callbacks[i-1].update(enter_seq=enter,exit_seq=exit)
    def effect(i,kind,corr,start,end,**kw):
        return dict(id=i,kind=kind,domain='DRIVER',correlation=corr,pid=7,
                    device=0,context=3,stream=4,start=start,end=end,graph=0,**kw)
    apis=[dict(id='api'+str(c['id']),domain=c['domain'],correlation=c['correlation'],
        pid=c['pid'],tid=c['tid'],name=c['name'],start=c['start'],end=c['end'],return_code=0)
        for c in callbacks if c['domain']=='RUNTIME']
    return dict(schema_version='submit-effect-evidence/0.1.0',session_id='same-session',
        clock='CUPTI_TIMESTAMP_NS',source='HOST_ORACLE',pid=7,
        quality=dict(closed=True,errors=[],overflow=0,dropped=0,dropped_query_errors=0,
                     dropped_scopes=[[3,4]]),
        callbacks=callbacks,apis=apis,effects=[effect('k','KERNEL',101,30,55),
            effect('m','MEMSET',102,56,60,bytes=64,value=123),
            effect('d','MEMCPY',103,61,62,bytes=8,copy_kind=2)],
        synchronizations=[dict(id='sync',domain='DRIVER',correlation=104,
                               context=3,stream=4,start=47,end=68)],
        scope=dict(session_id='same-session',pid=7,tid=9,device=0,context=3,stream=4,
            drain_end=5,request_start=10,completion_end=75,copy_api='api6',sync_api='api8',
            completion_proof='HOST_TOKEN_READABLE',actual_token_ids=[17],
            ownership='CLOSED_SINGLE_FIFO_NO_EVENTS_OR_GRAPHS'))


def test_real_parent_domains_and_logical_zero_produce_known_hand_calculated_result():
    m=bridge();r=m.analyze_scope(sample())
    assert r['status']=='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS'
    assert r['members']==['k','m','d'] and r['terminal']=='d'
    assert r['coe_ns']==20 and r['sync_intersection_ns']==15
    assert r['operation_wall_ns']==30
    assert r['logical_zero_call_ids']==[3] and r['synthetic_activities']==[]
    assert r['submit_effects']=={'api1':['k'],'api3':[],'api4':['m'],'api6':['d']}
    assert r['production_A_B_changed'] is False and r['pure_host_blocking'] is None
    # Runtime API wall budget is preserved, including the zero-payload call.
    assert r['runtime_api_intervals']==[(10,16),(17,19),(20,26),(40,44),(45,70)]


def test_real_top_level_driver_launch_with_its_own_api_is_not_forced_into_fake_runtime_parent():
    v=sample();v['callbacks']=[c for c in v['callbacks'] if c['id']!=1]
    c=v['callbacks'][0];c['parent_id']=None;c['params']=dict(native_stream=0)
    v['apis']=[a for a in v['apis'] if a['id']!='api1']
    v['apis'].append(dict(id='driver-launch',domain='DRIVER',correlation=101,pid=7,tid=9,
        name='cuLaunchKernel',start=11,end=15,return_code=0))
    r=bridge().analyze_scope(v)
    assert r['coe_ns']==20 and r['submit_effects']['driver-launch']==['k']
    edge=next(e for e in r['effect_edges'] if e['effect_id']=='k')
    assert edge['submit_domain']=='DRIVER' and edge['runtime_api_id'] is None


@pytest.mark.parametrize('damage,reason',[
    ('missing_parent','PARENT'),('wrong_parent','PARENT'),('wrong_domain','EFFECT_BRIDGE'),
    ('same_id_wrong_domain','EFFECT_BRIDGE'),('wrong_stream','SCOPE'),
    ('wrong_pid','SCOPE'),('nonzero_missing','POSITIVE_EFFECT_MISSING'),
    ('unknown_count','PARAMETERS'),('zero_conflict','ZERO_EFFECT_CONFLICT'),
    ('effect_bytes','PAYLOAD'),('effect_value','PAYLOAD'),('future','COMPLETION'),
    ('unrelated','UNASSIGNED_EFFECT'),('drop','QUALITY'),('missing_drop_scope','QUALITY'),
    ('unclosed','QUALITY'),('cross_session','SESSION'),('events','OWNERSHIP'),
    ('missing_sync','SYNC'),('failed_sync','FAILED_API'),('duplicate_api','API_DUPLICATE'),
])
def test_ambiguous_missing_or_conflicting_evidence_is_not_filled_with_zero(damage,reason):
    v=sample()
    if damage=='missing_parent':v['callbacks'][1]['parent_id']=None
    if damage=='wrong_parent':v['callbacks'][1]['parent_id']=4
    if damage=='wrong_domain':v['effects'][0]['domain']='RUNTIME'
    if damage=='same_id_wrong_domain':v['effects'][0].update(domain='RUNTIME',correlation=101)
    if damage=='wrong_stream':v['effects'][0]['stream']=5
    if damage=='wrong_pid':v['effects'][0]['pid']=8
    if damage=='nonzero_missing':v['effects'].pop(1)
    if damage=='unknown_count':v['callbacks'][2]['params']=None
    if damage=='zero_conflict':v['callbacks'][2]['params']['count']=0;v['callbacks'][3]['params']['count']=0
    if damage=='effect_bytes':v['effects'][1]['bytes']=63
    if damage=='effect_value':v['effects'][1]['value']=0
    if damage=='future':v['effects'][0]['end']=80
    if damage=='unrelated':v['effects'].append({**v['effects'][0],'id':'x','correlation':999})
    if damage=='drop':v['quality']['dropped']=1
    if damage=='missing_drop_scope':v['quality']['dropped_scopes']=[]
    if damage=='unclosed':v['quality']['closed']=False
    if damage=='cross_session':v['scope']['session_id']='old-session'
    if damage=='events':v['scope']['ownership']='UNKNOWN_EVENT_RELATION'
    if damage=='missing_sync':v['synchronizations']=[]
    if damage=='failed_sync':v['apis'][-1]['return_code']=v['callbacks'][7]['return_code']=2
    if damage=='duplicate_api':v['apis'].append(deepcopy(v['apis'][0]))
    with pytest.raises(ValueError,match=reason):bridge().analyze_scope(v)


def test_two_driver_effects_are_allowed_only_with_exact_payload_and_real_parent():
    v=sample();v['effects'][1]['bytes']=32
    v['effects'].insert(2,{**v['effects'][1],'id':'m2','start':60,'end':61})
    r=bridge().analyze_scope(v)
    assert r['submit_effects']['api4']==['m','m2'] and r['coe_ns']==21


def test_equal_cross_domain_numbers_are_not_merged():
    v=sample();v['callbacks'][1]['correlation']=11;v['effects'][0]['correlation']=11
    r=bridge().analyze_scope(v)
    assert r['members']==['k','m','d'] and r['coe_ns']==20


def test_orphan_driver_and_effect_cannot_be_bound_by_nearest_time_or_same_stream():
    v=sample();v['callbacks'][1]['parent_id']=None
    with pytest.raises(ValueError,match='PARENT'):bridge().analyze_scope(v)


def test_memcpy_runtime_correlation_is_an_explicit_typed_bridge_not_id_guessing():
    v=sample();v['callbacks']=[c for c in v['callbacks'] if c['id']!=7]
    v['effects'][-1]['runtime_correlation']=14
    r=bridge().analyze_scope(v)
    assert r['coe_ns']==20
    assert next(e for e in r['effect_edges'] if e['effect_id']=='d')['bridge']=='MEMCPY_RUNTIME_CORRELATION'


def test_real_isolated_import_does_not_use_an_external_scripts_package(tmp_path):
    import json,subprocess,sys
    from pathlib import Path
    other=tmp_path/'foreign';(other/'scripts').mkdir(parents=True)
    (other/'scripts/__init__.py').write_text("raise RuntimeError('FOREIGN_SCRIPTS_PACKAGE')")
    inp=tmp_path/'input.json';inp.write_text(json.dumps(sample()))
    root=Path(__file__).resolve().parents[1]
    code="""import sys,json,importlib.util,pathlib
sys.path[:0]=[sys.argv[1],sys.argv[2]]
from exposedpath_v141.submit_effect_bridge import analyze_scope
assert analyze_scope(json.loads(pathlib.Path(sys.argv[3]).read_text()))['coe_ns']==20
p=pathlib.Path(sys.argv[1])/'scripts/build_cupti_timeline.py'
s=importlib.util.spec_from_file_location('reviewed_builder',p)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
assert pathlib.Path(m.tools.__file__).resolve()==p.with_name('memset_micro.py')
"""
    p=subprocess.run([sys.executable,'-I','-S','-B','-c',code,str(root),str(other),str(inp)],
        cwd=tmp_path,capture_output=True,text=True,timeout=20)
    assert p.returncode==0,p.stdout+p.stderr
