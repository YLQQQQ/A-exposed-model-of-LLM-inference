"""CPU file-chain evidence, not new CUDA qualification or a missing-work waiver."""
import json
import sqlite3

import pytest

from test_gate8_identity import sha, write_json
from test_gate9_domain import source


def memset_source(tmp_path, monkeypatch, mode):
    receipt, execution, paths = source(tmp_path, monkeypatch)
    with sqlite3.connect(paths['sqlite']) as db:
        db.execute("INSERT INTO StringIds VALUES (26,'cudaMemsetAsync_v3020')")
        if mode == 'mapped':
            # Independent 5 ns submit owns an explicitly recorded 35 ns memset
            # (450..485), not a kernel borrowed merely because it is nearby.
            db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET nameId=26 WHERE correlationId=36')
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_MEMSET SELECT start,end,deviceId,contextId,greenContextId,'
                'streamId,correlationId,globalPid,0,64,NULL,2 FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=36')
            db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=36')
        else:
            tid = db.execute('SELECT globalTid FROM CUPTI_ACTIVITY_KIND_RUNTIME LIMIT 1').fetchone()[0]
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (441,444,0,?,35,26,0,NULL)', (tid,))
            if mode == 'adjacent_driver':
                # corr35 ends at444, driver corr36 starts at445. Neither
                # adjacency nor consecutive correlations supplies a bridge.
                db.execute("INSERT INTO StringIds VALUES (27,'cuLaunchKernel')")
                db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET nameId=27,eventClass=1 WHERE correlationId=36')
    export = json.loads(paths['export_report'].read_text())
    export['canonical_sqlite_sha256'] = sha(paths['sqlite'])
    export['attempts'][0].update(sqlite_sha256=sha(paths['sqlite']), sqlite_size=paths['sqlite'].stat().st_size)
    write_json(paths['export_report'], export)
    from exposedpath_v141.gate8_files import write_input_receipt
    receipt = write_input_receipt(tmp_path/'mutated-input.json', artifacts=paths,
        collector_version='2026.2.1.210', capture_session_id='synthetic')
    return receipt, execution


@pytest.mark.parametrize('mode', ['mapped', 'missing', 'adjacent_driver'])
def test_real_file_chain_missing_memset_cannot_borrow_driver_work(tmp_path, monkeypatch, mode):
    from exposedpath_v141.gate9_domain import process_domain, load_domain
    from scripts.gate8_diagnostic_collect import check_model_admission, ModelScopeBlocked
    receipt, execution = memset_source(tmp_path, monkeypatch, mode)
    result = process_domain(receipt, execution, tmp_path/'derived')
    value = load_domain(result, receipt, execution)
    request = value['requests'][1]
    if mode == 'mapped':
        assert request['status'] == 'QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
        a = request['a_records'][0]
        # Independent oracle unchanged: Host45/API15/wait15/residual25/unknown0.
        assert [a[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns',
            'A_sync_residual_ns','A_unattributed_ns')] == [45,15,15,25,0]
    else:
        assert request['a_records'] == []
        assert request['reasons'] == ['ENGINEERING_SCOPE_SUBMIT_MAPPING']
        with pytest.raises(ModelScopeBlocked, match='^MODEL_A_SCOPE_BLOCKED$') as error:
            check_model_admission(result, value, domain=True)
        details = error.value.details
        assert details['result_sha256'] == sha(result)
        assert details['requests'][1]['reasons'] == request['reasons']
        assert details['requests'][1]['identity'] == request['identity']
        assert value['dropped_records_status'] == 'UNKNOWN'


def test_collection_keeps_leaf_rejection_separate_from_process_exit(tmp_path, monkeypatch):
    from scripts import gate8_diagnostic_collect as m
    result = write_json(tmp_path/'result.json', dict(status='BLOCKED', requests=[dict(
        identity={'request_id':'request-0'}, status='REJECTED',
        reasons=['ENGINEERING_SCOPE_SUBMIT_MAPPING'], a_records=[])]))
    with pytest.raises(m.ModelScopeBlocked) as error:
        m.check_model_admission(result, json.loads(result.read_text()), domain=True)
    report = dict(status='DIAGNOSTIC_COLLECTED_NOT_QUALIFIED', collection={'status':'COMPLETE'})
    m.record_analysis_error(report, error.value)
    assert report['error'] == 'MODEL_A_SCOPE_BLOCKED'
    assert report['status'] == 'DIAGNOSTIC_COLLECTED_NOT_QUALIFIED'
    assert report['analysis_rejection']['requests'][0]['reasons'] == ['ENGINEERING_SCOPE_SUBMIT_MAPPING']
    generic = dict(status='BLOCKED')
    m.record_analysis_error(generic, ValueError('MODEL_PREPARED_IDENTITY'))
    assert generic == dict(status='BLOCKED', error='MODEL_PREPARED_IDENTITY')


def test_wrong_request_count_cannot_mask_rejection_when_source_has_no_reasons(tmp_path):
    from scripts.gate8_diagnostic_collect import check_model_admission, ModelScopeBlocked
    r=dict(identity={'request_id':'request-0'},status='QUALITY_CHECK_PASSED_NOT_QUALIFICATION',a_records=[])
    value=dict(status='QUALITY_CHECK_PASSED_NOT_QUALIFICATION',requests=[r,r])
    path=write_json(tmp_path/'domain.json',value)
    with pytest.raises(ModelScopeBlocked,match='^MODEL_A_SCOPE_BLOCKED$') as error:
        check_model_admission(path,value,domain=True)
    assert all('reasons' not in r for r in error.value.details['requests'])


def test_batch_rejection_keeps_leaf_context_and_never_admits_it():
    from scripts.batch_load_diagnostic import check_profile_admission
    value = dict(status='DIAGNOSTIC_COLLECTED_NOT_QUALIFIED', error='MODEL_A_SCOPE_BLOCKED',
        analysis_rejection=dict(version='model-scope-rejection/0.1.0',
            requests=[dict(reasons=['ENGINEERING_SCOPE_SUBMIT_MAPPING'])]))
    with pytest.raises(ValueError, match='BATCH_LOAD_PROFILE_ADMISSION:') as error:
        check_profile_admission(value)
    details = json.loads(str(error.value).split(':',1)[1])
    assert details == value
    check_profile_admission(dict(status='A_SCOPE_ENGINEERING_ONLY',error=None))
    with pytest.raises(ValueError):
        check_profile_admission(dict(status='A_SCOPE_ENGINEERING_ONLY',error=None,
            analysis_rejection=value['analysis_rejection']))


def test_actual_collection_report_persists_rejection_without_changing_admission(tmp_path, monkeypatch):
    import sys
    import sysconfig
    import subprocess
    from scripts import gate8_diagnostic_collect as m
    from scripts import gate7_nsys_postprocess as export
    from exposedpath.batch_load import minimal_fields
    from test_batch_load_diagnostic import binding
    from exposedpath_v141.gate8_target_python import probe
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    manifest = minimal_fields(binding())
    manifest['target_python'] = probe(sys._base_executable,sysconfig.get_path('purelib'))
    prepared = tmp_path/'prepared'; prepared.mkdir()
    write_json(prepared/'manifest.json',manifest)
    nsys=tmp_path/'nsys.exe'; nsys.touch()
    output=tmp_path/'collection'
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(output),
        '--execute-engineering-diagnostic','--engineering-a-only'])
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**kw:
        subprocess.CompletedProcess(a[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    def captured(*a,**kw):
        (output/'diagnostic').mkdir()
        write_json(output/'diagnostic/diagnostic_report.json',dict(status='DIAGNOSTIC_COMPLETE',
            qualification='NOT_QUALIFIED',scientific_outputs_allowed=False))
        return dict(status='COMPLETE',exit_code=0,timed_out=False)
    monkeypatch.setattr(m,'run_once',captured)
    monkeypatch.setattr(export,'run_postprocess',lambda **kw:dict(status='PASS'))
    result = write_json(tmp_path/'blocked.json',dict(status='BLOCKED',requests=[dict(
        identity={'request_id':'request-0'},status='REJECTED',
        reasons=['ENGINEERING_SCOPE_SUBMIT_MAPPING'],a_records=[])]))
    def blocked(*a,**kw):
        m.check_model_admission(result,json.loads(result.read_text()),domain=True)
    monkeypatch.setattr(m,'analyze_model',blocked)
    # Collector exit0 still means captured diagnostics, not request admission.
    # No real process, model, exporter or CUDA is used by these CPU doubles.
    assert m.main()==0
    report=json.loads((output/'collection_report.json').read_text())
    assert report['collection']['status']=='COMPLETE' and report['export_status']=='PASS'
    assert report['error']=='MODEL_A_SCOPE_BLOCKED'
    assert report['analysis_rejection']['result_sha256']==sha(result)
    from scripts.batch_load_diagnostic import check_profile_admission
    with pytest.raises(ValueError,match='ENGINEERING_SCOPE_SUBMIT_MAPPING'):
        check_profile_admission(report)
