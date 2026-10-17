"""CPU collection/report boundary, no model, CUDA, Nsight or export execution."""
import json
import subprocess
import sys
import sysconfig

import pytest
from test_gate8_identity import write_json


@pytest.mark.parametrize('mode',['analysis_rejected','missing_result','success','legacy_diagnostic'])
def test_parameter_analysis_failure_is_nonzero_without_changing_legacy_capture(tmp_path,monkeypatch,mode):
    """Catches the observed export-PASS + analyzer-fail -> exit0 fallthrough.

    Real main/exception/report/hash code; model/collector/export and analyzer
    execution boundaries are CPU doubles. The literals reproduce the sealed
    63ca051 collection status/error, not an assertion on a mock's call count.
    """
    from scripts import gate8_diagnostic_collect as m,gate7_nsys_postprocess as exporter
    from exposedpath import memset_prefill as c
    from exposedpath_v141.gate8_target_python import probe
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    b=c.binding('a'*32,'d'*40,dict(path='cpu-recorder.dll',sha256='c'*64),dict(path='cpu-runtime.dll',sha256='e'*64))
    mf=c.minimal_fields(b)
    if mode=='legacy_diagnostic':
        from exposedpath.batch_load import minimal_fields,schedule
        mf=minimal_fields(schedule('cpu-legacy')[1])
    mf.update(runner_git_commit='d'*40,runner_git_dirty=False)
    mf['target_python']=probe(sys._base_executable,sysconfig.get_path('purelib'))
    prepared=tmp_path/'prepared';prepared.mkdir();write_json(prepared/'manifest.json',mf)
    output=tmp_path/'collection';nsys=tmp_path/'cpu-not-nsys.exe';nsys.touch()
    argv=['collect','--nsys',str(nsys),'--python',sys._base_executable,'--prepared',str(prepared),
        '--output',str(output),'--execute-engineering-diagnostic','--engineering-a-only']
    if mode!='legacy_diagnostic':argv.append('--memset-prefill-parameters')
    monkeypatch.setattr(sys,'argv',argv)
    monkeypatch.setattr(m.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],0,
        'NVIDIA Nsight Systems version 2026.2.1.210',''))
    def captured(*a,**kw):
        (output/'diagnostic').mkdir()
        write_json(output/'diagnostic/diagnostic_report.json',dict(status='DIAGNOSTIC_COMPLETE',
            qualification='NOT_QUALIFIED',scientific_outputs_allowed=False))
        write_json(output/'diagnostic/manifest.json',mf)
        write_json(output/'diagnostic/target_runtime.json',{'role':'CPU_TARGET_BOUNDARY'})
        write_json(output/'target_launch.json',{'role':'CPU_LAUNCH_BOUNDARY'})
        return dict(status='COMPLETE',exit_code=0,timed_out=False,attempt_count=1)
    monkeypatch.setattr(m,'run_once',captured)
    monkeypatch.setattr(exporter,'run_postprocess',lambda **kw:dict(status='PASS'))
    def analyze(*a,**kw):
        if mode in ('analysis_rejected','legacy_diagnostic'):
            # Exact observed adapter-level exception; the original leaf reason
            # remains in its separate analyzer stderr/process record.
            raise ValueError('PARAMETER_OFFLINE_DRIVER_FAILED_SEE_ORIGINAL_LOG')
        p=output/'analyzed/parameters.json'
        if mode=='success':
            p.parent.mkdir();write_json(p,dict(status='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW'))
        return p
    monkeypatch.setattr(m,'analyze_model',analyze)
    code=m.main();report=json.loads((output/'collection_report.json').read_text())
    assert report['collection']['exit_code']==0 and report['export_status']=='PASS'
    assert report['scientific_outputs_allowed'] is False and report['qualification']=='NOT_QUALIFIED'
    if mode=='legacy_diagnostic':
        # Scope: do not redefine the historical diagnostic-only exit contract.
        assert code==0 and report['status']=='DIAGNOSTIC_COLLECTED_NOT_QUALIFIED'
    elif mode=='success':
        assert code==0 and report['status']=='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW'
        assert report['a_admission']==report['coe_admission']=='NOT_ASSESSED'
        assert 'error' not in report
    else:
        assert code==1 and report['status']=='BLOCKED'
        if mode=='analysis_rejected':assert report['error']=='PARAMETER_OFFLINE_DRIVER_FAILED_SEE_ORIGINAL_LOG'
        else:assert 'parameters.json' in report['error']


def test_zero_capture_is_not_relabelled_as_zero_payload():
    from analysis.memset_prefill import coverage
    from test_memset_prefill import evidence
    side,raw,expected=evidence();side['calls']=[];raw['ranges']=[]
    with pytest.raises(ValueError,match='^MEMSET_PREFILL_NO_TARGET_CALLS_NOT_DISCRIMINATING$'):
        coverage(side,raw,expected)
