"""SDK22 identities, real record excerpts and independent CPU interval oracles."""
from copy import deepcopy
import importlib

import pytest

from analysis import cupti_timeline as adapter
from exposedpath_v141 import submit_effect_bridge as bridge
from test_cupti_timeline_adapter import capture

POLICY='cupti-api22-driver-queries/0.1.0'


def real_queries():
    # Original 768 capture 43ee54b8...0078, same immutable 358e6d17...edbf ZIP.
    rows=[('cuDevicePrimaryCtxGetState',392,23,27,14,2490881796208500,2490881796209000,2490881796209900,2490881796209900),
        ('cuCtxGetCurrent',304,163,248,144,2490881797834600,2490881797835000,2490881797835200,2490881797835200),
        ('cuKernelGetFunction',683,167,254,148,2490881797926100,2490881797926500,2490881797929100,2490881797929300),
        ('cuFuncGetAttribute',85,414,620,379,2490881799273600,2490881799273900,2490881799274600,2490881799274600),
        ('cuOccupancyMaxActiveBlocksPerMultiprocessorWithFlags',451,415,621,380,2490881799275700,2490881799276200,2490881799277000,2490881799277000)]
    return [dict(name=n,cbid=b,api_id=f'record:{a}',callback_id=c,correlation=k,
        callback_start=cs,api_start=astart,api_end=aend,callback_end=cend) for n,b,a,c,k,cs,astart,aend,cend in rows]


@pytest.mark.parametrize('row',real_queries(),ids=lambda r:r['name'])
def test_exact_real_query_is_supported_without_inventing_runtime_parent(row):
    spec=importlib.util.find_spec('exposedpath_v141.cupti_driver_queries')
    assert spec is not None, 'separate versioned driver query rules missing'
    m=importlib.import_module(spec.name)
    c=dict(id=row['callback_id'],parent_id=None,domain='DRIVER',pid=27080,tid=50908,
        name=row['name'],cbid=row['cbid'],correlation=row['correlation'],return_code=0,
        start=row['callback_start'],end=row['callback_end'])
    a={**c,'id':row['api_id'],'start':row['api_start'],'end':row['api_end']}
    before=deepcopy((a,c));r=m.query_rule(a,c)
    assert r['category']=='non_submit' and r['pure_cpu_cost'] is False
    assert r['scope']=='NO_DEVICE_WORK_SUBMISSION_OR_COMPLETION_GUARANTEE'
    assert (a,c)==before


def query_capture(name='cuDevicePrimaryCtxGetState',cbid=392):
    raw=capture();s=raw.pop('scope')
    cbids={1:211,2:307,3:51,4:51,5:216,6:41,7:279,8:131,9:126}
    for c in raw['callbacks']:
        c['cbid']=cbids[c['id']]
        if c['id'] in (1,2):c['params']=dict(native_stream=0)
        if c['id']==7:c['name']='cuMemcpyDtoHAsync_v2'
        for k in ('enter_seq','exit_seq'):
            if c[k]>=5:c[k]+=2
    for a in raw['records']:
        if a['kind']=='API':a['cbid']=cbids[int(a['id'][3:])]
    # This v0.3 profile has all API activity rows, like the real 768 capture;
    # the older hand fixture deliberately omitted nested DRIVER API activities.
    raw['records'] += [dict(c,id=f'api-driver-{c["id"]}',kind='API')
        for c in raw['callbacks'] if c['domain']=='DRIVER']
    q=dict(id=50,parent_id=None,domain='DRIVER',name=name,cbid=cbid,correlation=555,pid=7,tid=9,
        device=0,context=3,stream=0,start=16,end=17,enter_seq=5,exit_seq=6,
        return_code=0,closed=True,ptsz=False,binding_status=-1,params=None)
    raw['callbacks'].append(q)
    raw['records'].append({k:q[k] for k in ('domain','name','cbid','correlation','pid','tid','start','end','return_code')}|
        dict(id='query-api',kind='API'))
    return raw,s


def evidence(raw,s):
    return adapter.to_evidence(raw,s,timing_policy=bridge.SAMPLED_TIMING,driver_query_policy=POLICY)


def test_query_does_not_submit_or_change_hand_calculated_members_and_COE(tmp_path):
    import json
    raw,s=query_capture();before=deepcopy(raw)
    with pytest.raises(ValueError,match='PARENT'):
        bridge.analyze_scope(adapter.to_evidence(raw,s,timing_policy=bridge.SAMPLED_TIMING))
    r=bridge.analyze_scope(evidence(raw,s))
    assert r['schema_version']=='submit-effect-bridge/0.3.0'
    assert r['members']==['k','m','d'] and r['coe_ns']==20 and r['terminal']=='d'
    assert r['logical_zero_call_ids']==[3]
    assert r['driver_queries'][0]['api_id']=='query-api'
    assert r['driver_queries'][0]['api_interval_ns']==[16,17]
    assert r['driver_queries'][0]['budget_owner_api_id']=='query-api'
    assert 'query-api' not in r['submit_effects']
    assert sum(row['api_id']=='query-api' for row in r['accounting_api_sources'])==1
    assert r['accounting_api_union_ns']==44  # 6+2+6+4+25 + query1
    assert raw==before
    p=tmp_path/'capture.json';p.write_text(json.dumps(raw));sp=tmp_path/'scope.json';sp.write_text(json.dumps(s))
    out=adapter.analyze_files(p,sp,tmp_path/'derived',timing_policy=bridge.SAMPLED_TIMING,driver_query_policy=POLICY)
    assert out['schema_version']=='cupti-timeline-adapter/0.3.0'
    assert out['result']['coe_ns']==20


@pytest.mark.parametrize('damage,reason',[
    ('unknown','DRIVER_ROOT_API_UNSUPPORTED'),('get_prefix','DRIVER_ROOT_API_UNSUPPORTED'),
    ('cbid','DRIVER_QUERY_IDENTITY'),('domain','DRIVER_QUERY_IDENTITY'),
    ('query_effect','QUERY_DEVICE_EFFECT'),('query_sync','QUERY_SYNCHRONIZATION'),
    ('query_child_effect','QUERY_DEVICE_EFFECT'),('unknown_nested','DRIVER_NESTED_API_UNSUPPORTED'),
    ('submit_missing','POSITIVE_EFFECT_MISSING'),('failed_query','FAILED_API'),
    ('query_api_missing','DRIVER_API_COVERAGE'),('policy','DRIVER_QUERY_POLICY'),
    ('scope','SCOPE'),('duplicate','API_DUPLICATE'),('duplicate_record','RECORD_DUPLICATE'),
    ('runtime_policy','RUNTIME_QUERY_POLICY'),
])
def test_query_support_is_not_generic_no_activity_or_prefix_exemption(damage,reason):
    raw,s=query_capture();q=raw['callbacks'][-1];a=raw['records'][-1]
    if damage in ('unknown','get_prefix'):q['name']=a['name']='cuMystery' if damage=='unknown' else 'cuGetEverything'
    if damage=='cbid':q['cbid']=a['cbid']=391  # Both agree, but wrong SDK identity.
    if damage=='domain':q['domain']=a['domain']='RUNTIME'
    if damage=='failed_query':q['return_code']=a['return_code']=1
    if damage=='query_api_missing':raw['records'].remove(a)
    if damage=='scope':q['tid']=a['tid']=10
    if damage=='duplicate':raw['records'].append(dict(a,id='different-record-same-invocation'))
    if damage=='duplicate_record':raw['records'].append(deepcopy(a))
    if damage=='query_effect':raw['records'].append(dict(raw['records'][-5],id='bad-query-effect',kind='KERNEL',
        domain='DRIVER',pid=7,correlation=555,start=32,end=33,graph=0,graph_node=0,runtime_correlation=0))
    if damage=='query_sync':
        e=evidence(raw,s);e['synchronizations'].append(dict(id='bad-sync',domain='DRIVER',correlation=555,
            context=3,stream=4,start=16,end=17))
        with pytest.raises(ValueError,match=reason):bridge.analyze_scope(e)
        return
    if damage=='query_child_effect':
        q.update(start=10,end=16,enter_seq=1,exit_seq=4)
        raw['callbacks']=[c for c in raw['callbacks'] if c['id']!=1]
        raw['records']=[a for a in raw['records'] if a['id']!='api1']
        raw['callbacks'][0]['parent_id']=50;raw['records'][-1].update(start=10,end=16)
    if damage=='unknown_nested':raw['callbacks'][1]['name']='cuMysteryChild'
    if damage=='submit_missing':raw['records']=[a for a in raw['records'] if a['id']!='k']
    with pytest.raises(ValueError,match=reason):
        e=evidence(raw,s)
        if damage=='policy':e['driver_query_policy']='wrong'
        if damage=='runtime_policy':e['runtime_query_policy']='wrong'
        bridge.analyze_scope(e)


def test_direct_driver_launch_remains_real_submit_with_parameters_and_effect():
    raw,s=query_capture();raw['callbacks']=[c for c in raw['callbacks'] if c['id']!=1]
    c=raw['callbacks'][0];c['parent_id']=None
    raw['records']=[a for a in raw['records'] if a['id']!='api1']
    next(a for a in raw['records'] if a['id']=='api-driver-2')['id']='direct-launch'
    r=bridge.analyze_scope(evidence(raw,s))
    assert r['submit_effects']['direct-launch']==['k'] and r['coe_ns']==20
    assert sum(a['api_id']=='direct-launch' for a in r['accounting_api_sources'])==1
    saved=c['params'];c['params']=None
    with pytest.raises(ValueError,match='PARAMETERS'):bridge.analyze_scope(evidence(raw,s))
    c['params']=saved
    raw['records']=[a for a in raw['records'] if a['id']!='k']
    with pytest.raises(ValueError,match='POSITIVE_EFFECT_MISSING'):bridge.analyze_scope(evidence(raw,s))


def test_nested_driver_query_is_retained_but_not_double_accounted():
    raw,s=query_capture();q=raw['callbacks'][-1];q.update(parent_id=1,start=12,end=14,enter_seq=3,exit_seq=4)
    raw['callbacks'][0].update(exit_seq=6)
    raw['callbacks'][1].update(start=11,end=12,enter_seq=2,exit_seq=3)
    q.update(enter_seq=4,exit_seq=5)
    raw['records'][-1].update(start=12,end=14)
    r=bridge.analyze_scope(evidence(raw,s))
    assert r['driver_queries'][0]['budget_owner_api_id']=='api1'
    assert not any(a['api_id']=='query-api' for a in r['accounting_api_sources'])
    assert r['accounting_api_union_ns']==43


def test_nested_driver_activity_may_be_absent_without_inventing_its_time():
    raw,s=query_capture();q=raw['callbacks'][-1]
    for c in raw['callbacks'][:-1]:
        for k in ('enter_seq','exit_seq'):
            if c[k]>=13:c[k]+=4
    q.update(name='cuOccupancyMaxActiveBlocksPerMultiprocessorWithFlags',cbid=451,
        parent_id=51,start=31,end=33,enter_seq=14,exit_seq=15)
    outer=dict(q,id=51,parent_id=None,domain='RUNTIME',name='cudaOccupancyMaxActiveBlocksPerMultiprocessor',
        cbid=210,correlation=556,start=30,end=34,enter_seq=13,exit_seq=16)
    raw['callbacks'].append(outer)
    raw['records']=[a for a in raw['records'] if a['id'] not in ('query-api','api-driver-2','api-driver-5','api-driver-7','api-driver-9')]
    raw['records'].append(dict(outer,id='outer-query',kind='API'))
    r=bridge.analyze_scope(evidence(raw,s))
    assert r['coe_ns']==20 and r['driver_queries'][0]['api_id'] is None
    assert r['driver_queries'][0]['api_interval_ns'] is None
    assert r['driver_queries'][0]['budget_owner_api_id']=='outer-query'
    assert len(r['accounting_api_sources'])==6


@pytest.mark.parametrize('name,cbid',[
    ('cudaGetDevice',17),('cudaGetLastError',10),('cudaDeviceGetAttribute',200),
    ('cudaOccupancyMaxActiveBlocksPerMultiprocessor',210),
])
def test_exact_runtime_query_bridge_keeps_wall_and_does_not_admit_unknowns(name,cbid):
    raw,s=query_capture();q=raw['callbacks'][-1];a=raw['records'][-1]
    q.update(domain='RUNTIME',name=name,cbid=cbid);a.update(domain='RUNTIME',name=name,cbid=cbid)
    r=bridge.analyze_scope(evidence(raw,s))
    assert r['coe_ns']==20 and r['members']==['k','m','d']
    assert r['driver_queries']==[] and r['runtime_queries'][0]['api_interval_ns']==[16,17]
    assert r['accounting_api_union_ns']==44
    q['cbid']=a['cbid']=cbid+1
    with pytest.raises(ValueError,match='RUNTIME_QUERY_IDENTITY'):bridge.analyze_scope(evidence(raw,s))


@pytest.mark.parametrize('name,cbid,reason',[
    ('cuMemsetD8Async',216,'QUERY_DEVICE_SUBMISSION'),
    ('cuStreamSynchronize',126,'QUERY_SYNCHRONIZATION'),
])
def test_query_cannot_hide_a_zero_submit_or_sync_child_even_without_activity(name,cbid,reason):
    raw,s=query_capture();q=raw['callbacks'][-1]
    q.update(start=10,end=16,enter_seq=1,exit_seq=4)
    raw['callbacks']=[c for c in raw['callbacks'] if c['id']!=1]
    c=raw['callbacks'][0];c.update(parent_id=50,name=name,cbid=cbid,
        params=dict(native_stream=0,count=0,value=0))
    raw['records']=[a for a in raw['records'] if a['id'] not in ('api1','k')]
    next(a for a in raw['records'] if a['id']=='api-driver-2').update(name=name,cbid=cbid)
    next(a for a in raw['records'] if a['id']=='query-api').update(start=10,end=16)
    with pytest.raises(ValueError,match=reason):bridge.analyze_scope(evidence(raw,s))


@pytest.mark.parametrize('name,reason',[
    ('cuDevicePrimaryCtxGetState','CALLBACK_SCOPE'),('cuGetUnknown','DRIVER_ROOT_API_UNSUPPORTED'),
])
def test_api_in_window_is_not_omitted_when_callback_sample_starts_before_window(name,reason):
    raw,s=query_capture();raw['callbacks'][-1].update(name=name,start=9)
    raw['records'][-1]['name']=name
    # A callback beginning at 9 cannot be sequenced after other calls at 10.
    # Move only this CPU example's request to 16 and remove the earlier launch
    # tree/effect, so the interval is temporally consistent but straddles scope.
    raw['callbacks']=[c for c in raw['callbacks'] if c['id'] not in (1,2)]
    raw['records']=[a for a in raw['records'] if a['id'] not in ('api1','api-driver-2','k')]
    s['request_start']=16
    with pytest.raises(ValueError,match=reason):bridge.analyze_scope(evidence(raw,s))
