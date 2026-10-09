"""Hand intervals: nested API costs are not a wall-clock partition."""
from copy import deepcopy
import pytest


def source():
    # Scope [-10,20); API [-8,4) contains driver [-6,2), sync [4,10).
    # Two overlapping kernels: [0,8),[6,14). No timing oracle uses A/S.
    common=dict(process_id=7,thread_id=8,context_id=1,device_id=0,clock_domain_id='trace')
    api=[dict(common,record_id='r',api_name='cudaLaunchKernel_v7000',start_ns=-8,end_ns=4,correlation_id=1),
         dict(common,record_id='d',api_name='cuLaunchKernel',start_ns=-6,end_ns=2,correlation_id=2),
         dict(common,record_id='s',api_name='cudaStreamSynchronize_v3020',start_ns=4,end_ns=10,correlation_id=3)]
    activities=[dict(common,record_id='k1',activity_kind='KERNEL',start_ns=0,end_ns=8,correlation_id=1,stream_id=4),
                dict(common,record_id='k2',activity_kind='KERNEL',start_ns=6,end_ns=14,correlation_id=2,stream_id=4)]
    scope=dict(identity={'request_id':'r0','run_id':'run','pass_id':'pass1'},phase='full_request',
               start_ns=-10,end_ns=20,clock_domain_id='trace',process_id=7,thread_id=8)
    owned={'r','d','s','k1','k2'}
    return api,activities,scope,owned


def test_fair_nested_sum_union_and_signed_launch_mapping():
    from exposedpath_v141.activity_baseline import calculate
    api,dev,p,owned=source(); result=calculate(api,dev,p,owned,registry_version='exposedpath-a-api-registry/0.2.0')
    assert result['api']==dict(count=3,sum_ns=26,union_ns=18,status='KNOWN')
    assert result['sync_api']['union_ns']==6 and result['non_sync_api']['union_ns']==12
    assert result['kernel']['sum_ns']==16 and result['kernel']['union_ns']==14
    assert result['gpu_active_ratio']==14/30
    assert [m['post_api_return_ns'] for m in result['launch_mapping']]==[-4,4]
    assert result['launch_mapping'][0]['status']=='STARTED_BEFORE_API_RETURN'


def test_clipped_cost_full_mapping_and_halfopen_membership():
    from exposedpath_v141.activity_baseline import calculate
    api,dev,p,owned=source();p.update(phase='decode',start_ns=4,end_ns=20)
    r=calculate(api,dev,p,owned,registry_version='exposedpath-a-api-registry/0.2.0')
    assert r['api']['count']==1 and r['api']['sum_ns']==6
    assert r['kernel']['sum_ns']==12 and r['kernel']['union_ns']==10
    assert r['launch_mapping']==[]  # Launch starts before the phase; no invented member.


@pytest.mark.parametrize('damage',['mapping','ownership','scope','duplicate','registry'])
def test_baseline_never_invents_zero_or_wrong_scope(damage):
    from exposedpath_v141.activity_baseline import calculate
    api,dev,p,owned=source();version='exposedpath-a-api-registry/0.2.0'
    if damage=='mapping':dev[0]['correlation_id']=999
    if damage=='ownership':owned.remove('k1')
    if damage=='scope':dev[0]['clock_domain_id']='other'
    if damage=='duplicate':api.append(deepcopy(api[0]))
    if damage=='registry':version='unknown'
    if damage in ('scope','duplicate','registry'):
        with pytest.raises(ValueError): calculate(api,dev,p,owned,registry_version=version)
    else:
        r=calculate(api,dev,p,owned,registry_version=version)
        if damage=='mapping':assert r['launch_mapping'][0]['status']=='MISSING_MAPPING'
        else:assert r['gpu_active_ratio'] is None and r['kernel']['status']=='OWNERSHIP_UNKNOWN'


@pytest.mark.parametrize('driver',[False,True])
def test_baseline_actual_producer_canonical_domain_file_chain(tmp_path,monkeypatch,driver):
    import json
    from test_n1_model_domain import source as files
    from exposedpath_v141.gate9_domain import process_domain
    from exposedpath_v141.activity_baseline import write_baseline
    receipt,execution,calls=files(tmp_path,monkeypatch,'Vsync',driver_apis=driver)
    domain=process_domain(receipt,execution,tmp_path/'qualified',bridge_path=calls)
    out=write_baseline(domain,receipt,execution,tmp_path/'baseline',bridge_path=calls)
    result=json.loads(out.read_text())
    assert len(result['windows'])==3
    r=next(w for w in result['windows'] if w['scope']['phase']=='full_request')
    # Two forwards, each has two prescribed layer launches; two D2H.
    assert r['api']['status']=='KNOWN' and r['api']['count']>=5
    assert r['kernel']['count']==4 and r['memop']['count']==2
    assert r['sync_api']['count']==3
    assert r['definitions']['b_aggregation']=='FORBIDDEN'
    if driver:
        assert r['driver_api']['count']==4 and r['driver_api']['sum_ns']==32
        assert r['runtime_api']['union_ns']==r['api']['union_ns']
    else:assert r['driver_api']['count'] is None
    from exposedpath_v141.activity_baseline import load_baseline
    result['windows'][0]['scope']['start_ns']+=1
    out.write_text(json.dumps(result),encoding='utf-8')
    with pytest.raises(ValueError,match='FILE_SCOPE_OR_VALUES'):
        load_baseline(out,domain,receipt,execution,bridge_path=calls)
