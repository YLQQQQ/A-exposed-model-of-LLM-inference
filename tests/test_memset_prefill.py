"""Hand-authored scope/parameter expectations, never CUDA qualification."""
from copy import deepcopy
import importlib.util
import pytest


def api():
    assert importlib.util.find_spec('analysis.memset_prefill'), 'missing versioned Prefill consumer'
    from analysis import memset_prefill
    return memset_prefill


def evidence():
    scope=dict(run_id='a'*32,pid=12,tid=13,creation_filetime=123,start=100,end=200,
        device_id=0,context_id=1,stream_id=7,native_stream_hex='0',clock_id='NSYS_TRACE_NS')
    apis=[dict(record_id='A1',name='cudaMemsetAsync_v3020',start=110,end=112,pid=12,tid=13,
        return_code=0,correlation_id=51,event_class=0)]
    side=dict(schema_version='memset-prefill-side/0.1.0',role='ENGINEERING_MEMSET_PREFILL',
        run_id='a'*32,pid=12,tid=13,creation_filetime=123,entry='cudaMemsetAsync',
        runtime_sha256='b'*64,recorder_sha256='c'*64,capacity=4096,attach_code=0,detach_code=0,
        recorder_error=0,begin_code=0,end_code=0,calls=[dict(call_id=1,pid=12,tid=13,count=0,
            value=123,stream_hex='0',pointer_alias=1,return_code=0,forwards=1,completed=True,
            push_level=-1,pop_level=-1)])
    raw=dict(scope=scope,apis=apis,ranges=[dict(record_id='N1',run_id='a'*32,call_id=1,
        pid=12,tid=13,start=109,end=113,event_type=59,domain_id=2)],
        domains=[dict(pid=12,domain_id=2,name='EP_MEMSET_PREFILL',event_type=75,start=90)],effects=[])
    return side,raw,dict(scope=scope,runtime_sha256='b'*64,recorder_sha256='c'*64)


def proof():
    # K completed before the operation; L follows the logical zero; D2H is
    # submitted inside copy before final sync. All are required, not pending-only.
    return dict(scope_closed=True,drain_end=95,request_start=100,completion_end=200,
        zero_calls=[dict(api_id='A1',start=110,end=112,native_stream_hex='0')],
        activities=[dict(id='K',submit_start=101,submit_end=102,start=103,end=108,stream=7),
            dict(id='L',submit_start=120,submit_end=121,start=122,end=150,stream=7),
            dict(id='D',submit_start=160,submit_end=161,start=165,end=170,stream=7)],
        prefix=[dict(id='P',end=94)],stream=7,copy_id='D',sync_start=180,sync_end=190,
        sync_return=0,unknown_dependencies=[],events=[],graphs=[],foreign_apis=[],
        modes={'LEGACY':dict(members=['K','L','D'],edges=[['K','L'],['L','D']],terminal='D'),
               'PER_THREAD':dict(members=['K','L','D'],edges=[['K','L'],['L','D']],terminal='D')})


def test_zero_payload_keeps_logical_call_and_original_api_budget():
    m=api();s,r,e=evidence();v=m.coverage(s,r,e)
    assert v['calls'][0]['state']=='ZERO_PAYLOAD_LOGICAL_ONLY'
    assert v['calls'][0]['api_wall_ns']==2 and v['calls'][0]['effect_ids']==[]
    p=m.zero_scope(proof())
    assert p['real_members']==['K','L','D'] and p['terminal']=='D'
    assert p['logical_calls']==['A1'] and p['synthetic_activities']==[]
    assert p['admission']=='PARAMETER_SUPPORT_ONLY_NOT_COE_OR_A'


def test_observed_null_pointer_zero_payload_is_not_made_into_an_allocation():
    s,r,e=evidence();s['calls'][0]['pointer_alias']=0
    assert api().coverage(s,r,e)['calls'][0]['state']=='ZERO_PAYLOAD_LOGICAL_ONLY'
    s['calls'][0]['count']=64
    with pytest.raises(ValueError,match='PARAMETERS'):api().coverage(s,r,e)


@pytest.mark.parametrize('damage,reason',[
    ('missing','RUNTIME_COVERAGE'),('duplicate','RANGE_PAIR'),('foreign','FOREIGN_THREAD'),
    ('ptsz','ENTRY'),('failed','CALL_RETURN'),('stream','STREAM'),('capacity','RECORDER'),
    ('domain','DOMAIN'),('runtime','RUNTIME_IDENTITY'),('unclosed','RANGE_PAIR')])
def test_bidirectional_coverage_rejects_actual_gap(damage,reason):
    m=api();s,r,e=evidence()
    if damage=='missing':r['apis'].append(dict(r['apis'][0],record_id='A2',correlation_id=52,start=114,end=115))
    if damage=='duplicate':r['ranges']*=2
    if damage=='foreign':r['apis'][0]['tid']=99
    if damage=='ptsz':r['apis'][0]['name']='cudaMemsetAsync_ptsz'
    if damage=='failed':s['calls'][0]['return_code']=1
    if damage=='stream':s['calls'][0]['stream_hex']='9'
    if damage=='capacity':s['recorder_error']=4
    if damage=='domain':r['domains'][0]['name']='EP_MEMSET_MICRO'
    if damage=='runtime':s['runtime_sha256']='0'*64
    if damage=='unclosed':r['ranges'][0]['end']=None
    with pytest.raises(ValueError,match=reason):m.coverage(s,r,e)


@pytest.mark.parametrize('count,effect,want',[(64,True,'NONZERO_DEVICE_EFFECT_MAPPED'),
    (64,False,'NONZERO_EFFECT_MISSING'),(0,True,'ZERO_EFFECT_CONFLICT')])
def test_zero_and_nonzero_have_distinct_effect_obligations(count,effect,want):
    m=api();s,r,e=evidence();s['calls'][0]['count']=count
    if effect:r['effects']=[dict(record_id='M1',kind='MEMSET',pid=12,correlation_id=51,
        bytes=64,value=123,device_id=0,context_id=1,stream_id=7,start=114,end=120)]
    if count==64 and effect:assert m.coverage(s,r,e)['calls'][0]['state']==want
    else:
        with pytest.raises(ValueError,match=want):m.coverage(s,r,e)


@pytest.mark.parametrize('damage,reason',[
    ('pending','PREFIX_PENDING'),('otherstream','SCOPE'),('dependency','DEPENDENCY'),
    ('mode','MODE'),('terminal','TERMINAL'),('late','SUBMISSION'),('no_drain','DRAIN'),
    ('unbounded_zero','ZERO_FRONTIER')])
def test_zero_never_erases_real_order_or_unresolved_scope(damage,reason):
    m=api();p=proof()
    if damage=='pending':p['prefix'][0]['end']=96
    if damage=='otherstream':p['activities'][0]['stream']=8
    if damage=='dependency':p['unknown_dependencies']=['incoming']
    if damage=='mode':p['modes']['PER_THREAD']['members']=['L','D']
    if damage=='terminal':p['modes']['LEGACY']['terminal']='K';p['modes']['PER_THREAD']['terminal']='K'
    if damage=='late':p['activities'][1]['submit_end']=191
    if damage=='no_drain':p['drain_end']=None
    if damage=='unbounded_zero':p['zero_calls'][0].update(start=175,end=176)
    with pytest.raises(ValueError,match=reason):m.zero_scope(p)


def test_old_batch_domain_does_not_gain_batch2_permission():
    from exposedpath import batch_load
    b=deepcopy(batch_load.schedule('fixed')[0]);b.update(batch_size=2,condition='B2')
    with pytest.raises(ValueError):batch_load.validate_binding(b)


@pytest.mark.parametrize('edges',[[['K','D']],[['K','L'],['L','D'],['D','K']]])
def test_missing_order_edge_or_cycle_is_not_numeric_equivalence(edges):
    p=proof();p['modes']['LEGACY']['edges']=edges;p['modes']['PER_THREAD']['edges']=edges
    with pytest.raises(ValueError,match='DEPENDENCY'):api().zero_scope(p)


def test_new_engineering_binding_is_closed_not_pilot():
    assert importlib.util.find_spec('exposedpath.memset_prefill'), 'missing model profile'
    from exposedpath import memset_prefill as c,batch_load
    b=c.binding('a'*32,'d'*40,dict(path='recorder.dll',sha256='c'*64),dict(path='runtime.dll',sha256='b'*64))
    assert batch_load.validate_binding(b)==b
    mf=batch_load.minimal_fields(b)
    assert mf['run_role']=='ENGINEERING' and mf['data_role']=='Engineering' and mf['batch_size']==2
    assert 'pilot' not in mf and 'domain_qualification' not in mf
    for key,value in [('pass_id','pass0'),('batch_size',4),('warmup_count',1),('version','future')]:
        bad=dict(b,**{key:value})
        with pytest.raises(ValueError):c.validate_binding(bad)
