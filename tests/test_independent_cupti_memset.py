"""Independent hand-specified evidence; no vendor DLL or GPU is invoked."""
import copy
import importlib
import json

import pytest


def module():
    assert importlib.util.find_spec('analysis.independent_cupti_memset'), 'independent consumer missing'
    return importlib.import_module('analysis.independent_cupti_memset')


def evidence():
    def call(i, domain, corr, parent, seq, count):
        return dict(call_id=i, parent_call_id=parent, domain=domain,
            cbid=51 if domain=='RUNTIME' else 216,
            name='cudaMemsetAsync' if domain=='RUNTIME' else 'cuMemsetD8Async',
            observed_name='cudaMemsetAsync' if domain=='RUNTIME' else 'cuMemsetD8Async',
            entry_kind='ORDINARY', pid=321, tid=654, context_uid=1,
            native_context='0x1230', native_stream='0x5670', pointer='0x9000',
            count=count, value=123, correlation_id=corr,
            enter_seq=seq, exit_seq=seq+3 if domain=='RUNTIME' else seq+1,
            entry_seen=True, exit_seen=True, params_copied=True, return_code=0)
    calls=[call(1,'RUNTIME',101,0,1,0),call(2,'RUNTIME',102,0,5,64),
           call(3,'DRIVER',901,2,6,64)]
    apis=[dict(domain=c['domain'],cbid=c['cbid'],correlation_id=c['correlation_id'],
        pid=321,tid=654,start={1:100,2:120,3:130}[c['call_id']],
        end={1:110,2:160,3:150}[c['call_id']],return_value=0)
        for c in calls]
    return dict(schema_version='independent-cupti-memset/0.1.0',source='HOST_CALLBACK_DOUBLE',
        role='ENGINEERING_PARAMETER_DIAGNOSTIC',run_id='cpu-run-1',pid=321,tid=654,
        callback_names={'ordinary':'cudaMemsetAsync','ptsz':'cudaMemsetAsync_ptsz'},
        callback_name_source='HOST_CALLBACK_DOUBLE',
        clock='CUPTI_TIMESTAMP_NS',runtime_version=12040,cupti_api_version=22,
        lifecycle=dict(subscribe=0,register_buffers=0,enable=0,flush=0,disable=0,
            unsubscribe=0,finalize=0,closed=True),
        loss=dict(callback_overflow=0,activity_overflow=0,buffer_exhaustion=0,
            callback_error=0,activity_error=0,dropped_records=0,dropped_queries=1,
            dropped_query_errors=0,outstanding_buffers=0),
        stream_binding=dict(context_uid=1,native_context='0x1230',native_stream='0x5670',
            stream_id=7,device_id=0,query_status=0),
        callbacks=calls,api_records=apis,
        effects=[dict(record_id='memset:1',correlation_domain='DRIVER',correlation_id=901,
            context_uid=1,stream_id=7,device_id=0,bytes=64,value=123,start=200,end=220,graph_id=0)],
        references=[dict(case_index=0,count=0,value=123,readback=[58]*64,success=True),
                    dict(case_index=1,count=64,value=123,readback=[123]*64,success=True)])


def test_hand_reference_separates_runtime_and_driver_ids_and_zero_dependency():
    r=module().review(evidence())
    assert r['status']=='MICRO_PARAMETER_EFFECT_PASS_LIMITED'
    assert r['source']=='HOST_CALLBACK_DOUBLE' and r['target_gpu_validated'] is False
    assert [(x['count'],x['effect_records']) for x in r['cases']]==[(0,[]),(64,['memset:1'])]
    assert r['cases'][1]['driver_correlations']==[901]
    assert r['zero_byte_dependency_qualification']=='NOT_ASSESSED'
    assert r['A_COE_admission']=='NOT_ASSESSED'


@pytest.mark.parametrize('mutation,reason',[
    ('params','PARAMETERS_MISSING'),('callback_missing','RUNTIME_COVERAGE'),
    ('callback_duplicate','CALL_ID_DUPLICATE'),('effect_missing','NONZERO_EFFECT_MISSING'),
    ('wrong_domain','EFFECT_CORRELATION_DOMAIN'),('same_numeric_id','NONZERO_EFFECT_MISSING'),
    ('wrong_stream','EFFECT_SCOPE'),('bad_parent','DRIVER_PARENTAGE'),
    ('ptsz','ENTRY_NOT_QUALIFIED'),('failed','CALL_FAILED'),
    ('overflow','LOSS_OR_OVERFLOW'),('dropped','LOSS_OR_OVERFLOW'),
    ('missing_loss_query','DROPPED_QUERY_UNKNOWN'),('subscribe','LIFECYCLE'),
    ('thread','CALL_SCOPE'),('context','CALL_SCOPE'),('count_float','PARAMETERS_MISSING'),
    ('readback','INDEPENDENT_READBACK'),('api_duplicate','API_ID_DUPLICATE'),
    ('api_domain','API_COVERAGE'),('effect_duplicate','EFFECT_ID_DUPLICATE')])
def test_rejects_concrete_missing_or_ambiguous_evidence(mutation,reason):
    m=module();v=evidence()
    if mutation=='params':v['callbacks'][1]['params_copied']=False
    elif mutation=='callback_missing':v['callbacks'].pop(0)
    elif mutation=='callback_duplicate':v['callbacks'].append(copy.deepcopy(v['callbacks'][0]))
    elif mutation=='effect_missing':v['effects']=[]
    elif mutation=='wrong_domain':v['effects'][0]['correlation_domain']='RUNTIME'
    elif mutation=='same_numeric_id':v['effects'][0]['correlation_id']=102
    elif mutation=='wrong_stream':v['effects'][0]['stream_id']=8
    elif mutation=='bad_parent':v['callbacks'][2]['parent_call_id']=1
    elif mutation=='ptsz':
        v['callbacks'][0].update(cbid=235,name='cudaMemsetAsync_ptsz',entry_kind='PTSZ')
        v['api_records'][0]['cbid']=235
    elif mutation=='failed':v['callbacks'][1]['return_code']=1
    elif mutation=='overflow':v['loss']['buffer_exhaustion']=1
    elif mutation=='dropped':v['loss']['dropped_records']=1
    elif mutation=='missing_loss_query':v['loss']['dropped_queries']=0
    elif mutation=='subscribe':v['lifecycle']['subscribe']=39
    elif mutation=='thread':v['callbacks'][1]['tid']=655
    elif mutation=='context':v['callbacks'][1]['context_uid']=2
    elif mutation=='count_float':v['callbacks'][1]['count']=64.0
    elif mutation=='readback':v['references'][0]['readback'][3]=123
    elif mutation=='api_duplicate':v['api_records'].append(copy.deepcopy(v['api_records'][0]))
    elif mutation=='api_domain':v['api_records'][2]['domain']='RUNTIME'
    elif mutation=='effect_duplicate':v['effects'].append(copy.deepcopy(v['effects'][0]))
    with pytest.raises(ValueError,match='^CUPTI_MICRO_'+reason+'$'):m.review(v)


def test_close_error_or_reused_callback_correlation_cannot_be_certified():
    m=module();v=evidence();v['error']='RUNTIME_CHANGED'
    with pytest.raises(ValueError,match='^CUPTI_MICRO_NATIVE_ERROR$'):m.review(v)
    v=evidence();v['callbacks'][1]['correlation_id']=101
    with pytest.raises(ValueError,match='^CUPTI_MICRO_CALLBACK_CORRELATION_DUPLICATE$'):m.review(v)


def test_target_label_needs_external_file_binding_not_just_role_change():
    m=module();v=evidence();v['source']='TARGET_GPU'
    with pytest.raises(ValueError,match='^CUPTI_MICRO_TARGET_BINDING$'):m.review(v)


@pytest.mark.parametrize('mutation,reason',[
    ('value','MICRO_PLAN'),('pointer','MICRO_PLAN'),('api_interval','API_PARENT_INTERVAL')])
def test_fixed_micro_buffer_value_and_parent_activity_consistency(mutation,reason):
    m=module();v=evidence()
    if mutation=='value':v['callbacks'][0]['value']=7
    elif mutation=='pointer':v['callbacks'][0]['pointer']='0xdead'
    else:v['api_records'][2]['start']=500;v['api_records'][2]['end']=510
    with pytest.raises(ValueError,match='^CUPTI_MICRO_'+reason+'$'):m.review(v)


def test_observed_name_must_match_fixed_entry_or_official_callback_name():
    m=module();v=evidence();v['callbacks'][0]['observed_name']='cudaLaunchKernel'
    with pytest.raises(ValueError,match='^CUPTI_MICRO_CALLBACK_NAME$'):m.review(v)


def test_file_chain_binds_exact_bytes_and_refuses_target_promotion(tmp_path):
    m=module();p=tmp_path/'raw.json';p.write_text(json.dumps(evidence()),encoding='utf8')
    out=tmp_path/'derived-v0.1';r=m.review_file(p,out)
    assert r['input']['sha256']==m.sha(p) and (out/'review.json').is_file()
    assert r['result']['target_gpu_validated'] is False
    with pytest.raises(FileExistsError):m.review_file(p,out)
    bad=evidence();bad['source']='FORMAL';p.write_text(json.dumps(bad),encoding='utf8')
    with pytest.raises(ValueError,match='^CUPTI_MICRO_SOURCE$'):m.review_file(p,tmp_path/'other')
