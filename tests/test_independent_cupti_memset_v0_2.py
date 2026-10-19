"""Independent literal call graph. No CUDA/vendor code or analyzer-derived answer."""
import copy
import importlib
import json
from pathlib import Path
import runpy

import pytest


def evidence(*,driver_api=False):
    # Reuse the hand-specified 0/64 fixture; do not call either analyzer for truth.
    root=Path(__file__).resolve().parents[1]
    v=runpy.run_path(str(root/'tests/test_independent_cupti_memset.py'))['evidence']()
    driver=v['callbacks'][2]
    driver.update(params_copied=False,count=0,value=0,native_stream='0x0',pointer='0x0')
    if not driver_api:v['api_records']=[a for a in v['api_records'] if a['domain']!='DRIVER']
    return v


def module():return importlib.import_module('analysis.independent_cupti_memset_v0_2')


@pytest.mark.parametrize('driver_api',[False,True])
def test_actual_parent_graph_and_same_driver_domain_effect_do_not_need_driver_duration(driver_api):
    v=evidence(driver_api=driver_api);before=copy.deepcopy(v)
    result=module().review(v)
    assert result['schema_version']=='independent-cupti-memset-review/0.2.0'
    assert result['status']=='MICRO_PARAMETER_EFFECT_PASS_LIMITED'
    assert [(x['count'],x['effect_records']) for x in result['cases']]==[(0,[]),(64,['memset:1'])]
    # Runtime102 is NOT driver901. Changing to an equality-only bridge breaks this.
    d=result['cases'][1]['driver_evidence'][0]
    assert d['call_id']==3 and d['parent_call_id']==2 and d['driver_correlation']==901
    assert d['api_record_present'] is driver_api and d['api_interval_checked'] is driver_api
    assert d['api_duration_ns'] is None and d['parameters_observed'] is False
    assert result['missing_driver_api_call_ids']==([] if driver_api else [3])
    assert result['pytorch_coverage']==result['A_COE_admission']=='NOT_ASSESSED'
    assert result['full_B_admission']=='NOT_ASSESSED_BY_RAW_CONSUMER'
    assert v==before, 'consumer modified or synthesized input evidence'


def test_legacy_keeps_refusal_for_exact_same_missing_driver_evidence():
    from analysis.independent_cupti_memset import review as old_review
    v=evidence()
    with pytest.raises(ValueError,match='^CUPTI_MICRO_API_COVERAGE$'):old_review(v)
    assert module().review(v)['status']=='MICRO_PARAMETER_EFFECT_PASS_LIMITED'


@pytest.mark.parametrize('mutation,reason',[
    ('runtime_api_missing','RUNTIME_API_COVERAGE'),('runtime_failed_api','RUNTIME_API_COVERAGE'),
    ('driver_callback_missing','NONZERO_EFFECT_MISSING'),('driver_parent_missing','DRIVER_PARENTAGE'),
    ('driver_parent_zero_case','DRIVER_PARENTAGE'),('driver_bad_order','DRIVER_PARENTAGE'),
    ('duplicate_sequence','SEQUENCE_DUPLICATE'),('failed_driver_return','CALL_FAILED'),
    ('wrong_thread','CALL_SCOPE'),('wrong_context','CALL_SCOPE'),
    ('wrong_runtime_stream','PARAMETERS_MISSING'),('wrong_effect_stream','EFFECT_SCOPE'),
    ('unknown_driver','DRIVER_ENTRY_OUT_OF_SCOPE'),('driver_ptsz','DRIVER_ENTRY_OUT_OF_SCOPE'),
    ('missing_effect','NONZERO_EFFECT_MISSING'),('effect_domain_runtime','EFFECT_CORRELATION_DOMAIN'),
    ('use_runtime_numeric_id','NONZERO_EFFECT_MISSING'),('effect_duplicate','EFFECT_ID_DUPLICATE'),
    ('callback_duplicate','CALL_ID_DUPLICATE'),('effect_wrong_bytes','EFFECT_PAYLOAD'),
    ('effect_wrong_value','EFFECT_PAYLOAD'),('params_missing','PARAMETERS_MISSING'),
    ('readback_conflict','INDEPENDENT_READBACK'),('dropped','LOSS_OR_OVERFLOW'),
    ('flush_failed','LIFECYCLE'),('query_unknown','DROPPED_QUERY_UNKNOWN')])
def test_missing_or_conflicting_evidence_is_not_rescued_by_optional_driver_api(mutation,reason):
    v=evidence();d=v['callbacks'][2]
    if mutation=='runtime_api_missing':v['api_records'].pop(1)
    elif mutation=='runtime_failed_api':v['api_records'][1]['return_value']=1
    elif mutation=='driver_callback_missing':v['callbacks'].pop(2)
    elif mutation=='driver_parent_missing':d['parent_call_id']=99
    elif mutation=='driver_parent_zero_case':d['parent_call_id']=1
    elif mutation=='driver_bad_order':d['enter_seq'],d['exit_seq']=10,11
    elif mutation=='duplicate_sequence':d['enter_seq']=5
    elif mutation=='failed_driver_return':d['return_code']=1
    elif mutation=='wrong_thread':d['tid']+=1
    elif mutation=='wrong_context':d['context_uid']+=1
    elif mutation=='wrong_runtime_stream':v['callbacks'][1]['native_stream']='0xbad'
    elif mutation=='wrong_effect_stream':v['effects'][0]['stream_id']+=1
    elif mutation=='unknown_driver':d['cbid'],d['name'],d['observed_name']=999,'unknown','unknown'
    elif mutation=='driver_ptsz':d['cbid'],d['name'],d['observed_name']=428,'cuMemsetD8Async_ptsz','cuMemsetD8Async_ptsz'
    elif mutation=='missing_effect':v['effects']=[]
    elif mutation=='effect_domain_runtime':v['effects'][0]['correlation_domain']='RUNTIME'
    elif mutation=='use_runtime_numeric_id':v['effects'][0]['correlation_id']=102
    elif mutation=='effect_duplicate':v['effects'].append(copy.deepcopy(v['effects'][0]))
    elif mutation=='callback_duplicate':v['callbacks'].append(copy.deepcopy(d))
    elif mutation=='effect_wrong_bytes':v['effects'][0]['bytes']=32
    elif mutation=='effect_wrong_value':v['effects'][0]['value']=1
    elif mutation=='params_missing':v['callbacks'][1]['params_copied']=False
    elif mutation=='readback_conflict':v['references'][1]['readback'][0]=0
    elif mutation=='dropped':v['loss']['dropped_records']=1
    elif mutation=='flush_failed':v['lifecycle']['flush']=1
    elif mutation=='query_unknown':v['loss']['dropped_queries']=0
    with pytest.raises(ValueError) as exc:module().review(v)
    assert str(exc.value)=='CUPTI_MICRO_V02_'+reason


@pytest.mark.parametrize('field,value,reason',[
    ('cbid',1,'DRIVER_API_COVERAGE'),('pid',9,'DRIVER_API_COVERAGE'),
    ('tid',9,'DRIVER_API_COVERAGE'),('return_value',1,'DRIVER_API_COVERAGE'),
    ('start',1,'API_PARENT_INTERVAL'),('end',999,'API_PARENT_INTERVAL')])
def test_present_driver_api_must_be_checked_and_never_discarded(field,value,reason):
    v=evidence(driver_api=True);v['api_records'][2][field]=value
    with pytest.raises(ValueError) as exc:module().review(v)
    assert str(exc.value)=='CUPTI_MICRO_V02_'+reason


def test_same_cross_domain_numbers_still_require_real_parent_and_complete_runtime():
    v=evidence();v['callbacks'][2]['correlation_id']=102;v['effects'][0]['correlation_id']=102
    assert module().review(v)['cases'][1]['effect_records']==['memset:1']
    v['callbacks'][2]['parent_call_id']=0
    with pytest.raises(ValueError,match='DRIVER_PARENTAGE'):module().review(v)


def test_real_file_chain_preserves_input_and_refuses_overwrite(tmp_path):
    p=tmp_path/'raw.json';p.write_text(json.dumps(evidence()),encoding='utf8');before=p.read_bytes()
    r=module().review_file(p,tmp_path/'v0_2')
    assert r==json.loads((tmp_path/'v0_2/review.json').read_text())
    assert r['result']['missing_driver_api_call_ids']==[3] and p.read_bytes()==before
    with pytest.raises(FileExistsError):module().review_file(p,tmp_path/'v0_2')


@pytest.mark.parametrize('parent',[1,2])
def test_missing_api_exception_needs_each_driver_own_nonzero_effect(parent):
    v=evidence();extra=copy.deepcopy(v['callbacks'][2]);extra.update(call_id=4,parent_call_id=parent,correlation_id=902)
    if parent==1:
        v['callbacks'][0]['exit_seq']=4;extra.update(enter_seq=2,exit_seq=3)
    else:
        v['callbacks'][1]['exit_seq']=10;extra.update(enter_seq=8,exit_seq=9)
    v['callbacks'].append(extra)
    with pytest.raises(ValueError,match='MISSING_DRIVER_API_BRIDGE_INCOMPLETE'):module().review(v)


def test_present_target_driver_api_with_unmatched_id_cannot_be_silently_ignored():
    v=evidence(driver_api=True);v['api_records'][2]['correlation_id']=999
    with pytest.raises(ValueError,match='DRIVER_API_UNASSIGNED'):module().review(v)


def test_claimed_direct_driver_siblings_cannot_actually_be_nested():
    v=evidence();v['callbacks'][1]['exit_seq']=12;v['callbacks'][2]['exit_seq']=11
    extra=copy.deepcopy(v['callbacks'][2]);extra.update(call_id=4,correlation_id=902,enter_seq=7,exit_seq=10)
    v['callbacks'].append(extra)
    with pytest.raises(ValueError,match='DRIVER_PARENTAGE'):module().review(v)
