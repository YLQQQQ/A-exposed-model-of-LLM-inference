"""Versioned real collector shape; no private trace or server paths."""
from copy import deepcopy
import json
import pytest
from exposedpath.gate8_isolated_preflight import sha,write_new
from scripts import completion_path_diagnostic as m


@pytest.fixture
def target(tmp_path):
    (tmp_path/'analyzed').mkdir();(tmp_path/'diagnostic').mkdir()
    for name in ('analyzed/prefill.json','diagnostic/manifest.json','diagnostic/target_runtime.json','target_launch.json'):
        write_new(tmp_path/name,{'fixture':'CPU ONLY'})
    # Fields copied from actual C0 report; argv/PID/elapsed anonymized.
    report=dict(schema_version='gate8-qwen-engineering-collection/0.1.0',
        status='PREFILL_LOCAL_ENGINEERING_ONLY',qualification='NOT_QUALIFIED',gate8_verdict='NOT_RUN',
        scientific_outputs_allowed=False,collection=dict(argv=['cpu'],attempt_count=1,status='COMPLETE',
            timed_out=False,pid=123,exit_code=0,descendant_exit_status='NOT_OBSERVED',elapsed_seconds=1.0),
        export_status='PASS',result_filename='prefill.json',result_sha256=sha(tmp_path/'analyzed/prefill.json'),
        manifest_sha256=sha(tmp_path/'diagnostic/manifest.json'),target_runtime_sha256=sha(tmp_path/'diagnostic/target_runtime.json'),
        target_launch_sha256=sha(tmp_path/'target_launch.json'),q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    return tmp_path,report


@pytest.mark.parametrize('optional_error',[False,True])
def test_actual_success_shape_allows_only_absent_or_null_error(target,optional_error):
    root,report=target
    if optional_error:report['error']=None
    assert m.validate_collection_report(report,root)==root/'analyzed/prefill.json'


@pytest.mark.parametrize('field,value',[
    ('schema_version','gate8-qwen-engineering-collection/99'),('status','BLOCKED'),('error','actual failure'),
    ('error',False),('result_filename','../prefill.json'),('result_sha256','0'*64),
    ('manifest_sha256','0'*64),('target_runtime_sha256','0'*64),('target_launch_sha256','0'*64),
    ('scientific_outputs_allowed',True),('measurement_validity','VALID'),('dropped_records_status','ZERO_CONFIRMED'),
    ('qualification','QUALIFIED'),('export_status','BLOCKED')])
def test_report_conflicts_are_not_covered_by_optional_error(target,field,value):
    root,report=target;report[field]=value
    with pytest.raises(ValueError):m.validate_collection_report(report,root)


@pytest.mark.parametrize('field',['schema_version','status','result_filename','result_sha256','manifest_sha256','collection'])
def test_missing_required_report_fields_fail_closed(target,field):
    root,report=target;del report[field]
    with pytest.raises(ValueError):m.validate_collection_report(report,root)


@pytest.mark.parametrize('field,value',[('status','BLOCKED'),('exit_code',1),('exit_code',False),('timed_out',True)])
def test_report_rejects_collection_process_failure(target,field,value):
    root,report=target;report['collection'][field]=value
    with pytest.raises(ValueError):m.validate_collection_report(report,root)


def test_result_missing_before_loader_is_rejected(target):
    root,report=target;(root/'analyzed/prefill.json').unlink()
    with pytest.raises(ValueError):m.validate_collection_report(report,root)


@pytest.mark.parametrize('damage',[None,'binding','commit','token_file','result_file'])
def test_actual_producer_canonical_report_consumer_file_chain(tmp_path,monkeypatch,damage):
    from test_n1_model_domain import source
    from scripts.gate8_diagnostic_collect import analyze_receipt
    from exposedpath import completion_path as c
    b=c.schedule('report-chain')[0]
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=c.batch_binding(b),completion_binding=b)
    # This fixture names the receipt input.json; the real collector names it
    # input_receipt.json. Preserve identical bytes/hash when aligning the entry.
    import shutil
    shutil.copyfile(receipt,tmp_path/'input_receipt.json')
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    path,value=analyze_receipt(manifest,receipt,execution,tmp_path/'analyzed')
    # These two artifacts are collector-level bindings, not synthetic timing evidence.
    for name in ('diagnostic/target_runtime.json','target_launch.json'):
        if not (tmp_path/name).exists():write_new(tmp_path/name,{'fixture':'CPU ONLY'})
    report=dict(schema_version='gate8-qwen-engineering-collection/0.1.0',status='PREFILL_LOCAL_ENGINEERING_ONLY',
        qualification='NOT_QUALIFIED',gate8_verdict='NOT_RUN',scientific_outputs_allowed=False,
        collection=dict(status='COMPLETE',exit_code=0,timed_out=False),export_status='PASS',result_filename='prefill.json',
        result_sha256=sha(path),manifest_sha256=sha(execution.parent/'manifest.json'),
        target_runtime_sha256=sha(tmp_path/'diagnostic/target_runtime.json'),target_launch_sha256=sha(tmp_path/'target_launch.json'),
        q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED')
    write_new(tmp_path/'collection_report.json',report)
    expected=deepcopy(b);commit=manifest['runner_git_commit']
    if damage=='binding':expected=c.schedule('foreign-request')[0]
    if damage=='commit':commit='0'*40
    if damage=='token_file':(execution.parent/'batch_tokens.json').write_text('{}')
    if damage=='result_file':path.write_text('{}')
    if damage:
        with pytest.raises((ValueError,KeyError)):m.consume_collection(tmp_path,expected,commit)
    else:
        observed,tokens=m.consume_collection(tmp_path,expected,commit)
        assert observed['prefill']['a_records'][0]['A_cuda_api_ns']==30
        # fixture's stream is 11,12,...; three two-token warmups consume
        # 11..16, leaving measured values 17,18 (not the other fixture's 13,14).
        assert tokens==[[17]*4,[18]*4]
