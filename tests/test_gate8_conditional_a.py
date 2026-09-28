"""Independent literal outcomes; no real collector and no zero-loss assertion."""
import json
import pytest
from test_gate8_engineering_scope import files, components, entry
from test_gate8_identity import sha

MESSAGES = (
    'Not all NVTX events might have been collected.',
    'No NVTX events collected. Does the process use NVTX?',
    'CUDA profiling might have not been started correctly.',
    'No CUDA events collected. Does the process use CUDA?',
)


def build(tmp_path, monkeypatch, damage=None):
    def mutate(db, tid):
        foreign = 99 << 24
        for i, message in enumerate(MESSAGES):
            pid = tid-tid%2**24 if damage=='target' and i==0 else foreign
            if damage=='unknown_pid' and i==0: pid = None
            if damage=='different_pid' and i==0: pid = 98 << 24
            if damage=='new_warning' and i==0: message = 'New shared buffer loss'
            db.execute('INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,2,?,?,2)',(message,pid))
        if damage=='extra_warning':
            db.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,2,'Lost CUDA buffer',?,2)",(foreign,))
        if damage=='zero_target':
            db.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (0,3,1,'Number of CUDA events collected: 0.',?,2)",(tid-tid%2**24,))
        if damage=='drain': db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE correlationId=101')
        if damage=='correlation': db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=999 WHERE correlationId=16')
        if damage=='boundary': db.execute("DELETE FROM NVTX_EVENTS WHERE text LIKE '%\"boundary_id\":\"t1-1\"%'")
        if damage=='gap':
            db.execute("INSERT INTO StringIds VALUES (25,'cudaStreamIsCapturing_v10000')")
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (420,425,0,?,333,25,0,NULL)',(tid,))
    receipt, execution, paths = files(tmp_path,monkeypatch,mutate)
    formal = entry().process_engineering_scope(receipt,execution,tmp_path/'formal')
    return receipt,execution,paths,formal


@pytest.mark.parametrize('damage',[None,'gap'])
def test_conditional_reuses_accounting_but_never_changes_formal(tmp_path,monkeypatch,damage):
    receipt,execution,paths,formal=build(tmp_path,monkeypatch,damage)
    before={p:sha(p) for p in [formal,*paths.values()]}
    assert json.loads(formal.read_text())['status']=='BLOCKED'
    module=entry()
    assert callable(getattr(module,'process_conditional_scope',None)), 'missing narrow assumption entry'
    output=module.process_conditional_scope(formal,receipt,execution,tmp_path/'conditional',
        assumption='FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1')
    result=json.loads(output.read_text())
    assert result['status']=='CONDITIONAL_A_ONLY_NOT_ACCEPTED'
    assert result['trusted_a'] is False and result['gate8_verdict']=='NOT_RUN'
    assert result['dropped_records_status']=='UNKNOWN'
    assert len(result['warning_assumption']['records'])==4
    assert result['warning_assumption']['scope_proven'] is False
    assert components(result['requests'][1]['a_records'][0])==([125,15,40,20,0] if damage else [130,10,40,20,0])
    assert {p:sha(p) for p in before}==before


@pytest.mark.parametrize('damage',['target','unknown_pid','different_pid','new_warning','extra_warning','zero_target','drain','correlation','boundary'])
def test_assumption_never_hides_other_conflicts(tmp_path,monkeypatch,damage):
    if damage=='boundary':
        with pytest.raises(ValueError,match='BOUNDARY_MISSING'):
            build(tmp_path,monkeypatch,damage)
        return
    receipt,execution,paths,formal=build(tmp_path,monkeypatch,damage)
    module=entry()
    assert callable(getattr(module,'process_conditional_scope',None)), 'missing narrow assumption entry'
    try:
        output=module.process_conditional_scope(formal,receipt,execution,tmp_path/'conditional',
            assumption='FOUR_OTHER_PROCESS_WARNINGS_NO_TARGET_IMPACT/0.1')
    except ValueError:
        assert not (tmp_path/'conditional').exists()
    else:
        result=json.loads(output.read_text())
        assert result['status']=='BLOCKED'
        assert any(r['status']=='REJECTED' and not r['a_records'] for r in result['requests'])
