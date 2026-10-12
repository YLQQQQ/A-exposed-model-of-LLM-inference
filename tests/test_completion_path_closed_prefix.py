"""Closed history is not request ownership or a qualified physical W/B."""
import json

import pytest


def source(tmp_path,monkeypatch,damage='closed_worker_prefix'):
    from test_n1_model_domain import source as producer
    from exposedpath import completion_path as c
    binding=c.schedule('closed-prefix-test')[1]
    return producer(tmp_path,monkeypatch,batch_binding=c.batch_binding(binding),
        completion_binding=binding,damage=damage)


def test_closed_other_thread_history_uses_real_file_chain_without_becoming_request_w(tmp_path,monkeypatch):
    from scripts.gate8_diagnostic_collect import analyze_receipt
    from exposedpath_v141.completion_path_scope import load
    receipt,execution,_=source(tmp_path,monkeypatch)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    path,result=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    assert result['status']=='PREFILL_LOCAL_ENGINEERING_ONLY'
    a=result['prefill']['a_records'][0]
    # Two 10ns launches and a 10ns copy; both 10ns syncs begin AFTER all
    # their necessary device work. Worker history ends before the drain.
    assert (a['A_cuda_api_ns'],a['A_device_wait_ns'],a['A_sync_residual_ns'],a['A_unattributed_ns'])==(30,0,20,0)
    proofs=result['full_pre_sync_dependencies']
    assert proofs[0]==proofs[1]
    assert len(proofs[0]['drained_raw_prefix_activity_ids'])==12
    assert len(proofs[0]['request_wait_set_activity_ids'])==2
    assert len(proofs[0]['terminal_activity_ids'])==1
    assert sorted(len(ids) for ids in proofs[0]['drained_raw_prefix_thread_activity_ids'].values())==[3,3,3,3]
    assert set(proofs[0]['drained_raw_prefix_activity_ids']).isdisjoint(proofs[0]['request_wait_set_activity_ids'])
    assert result['physical_b_qualified'] is False
    assert result['request_status']==result['decode_status']=='NOT_ACCEPTED_LOCAL_REVIEW_ONLY'
    assert result['dropped_records_status']=='UNKNOWN' and result['measurement_validity']=='NOT_ASSESSED'
    assert load(path,receipt,execution)==result


def test_legacy_result_retains_original_rejection_and_reader(tmp_path,monkeypatch):
    from exposedpath_v141 import completion_path_scope as m
    from scripts.gate8_diagnostic_collect import analyze_receipt
    from exposedpath_v141.gate8_files import _write
    receipt,execution,_=source(tmp_path,monkeypatch,damage=None)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    path,result=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    legacy=m._calculate(path.parent,receipt,execution,result_version='exposedpath-completion-path-prefill/0.1.0')
    legacy['files']=result['files']
    old=path.parent/'prefill.json'
    old.unlink();_write(old,legacy)
    assert m.load(old,receipt,execution)==legacy
    assert 'drained_raw_prefix_thread_activity_ids' not in legacy['full_pre_sync_dependencies'][0]


def test_legacy_calculation_does_not_rejudge_closed_worker_input(tmp_path,monkeypatch):
    from exposedpath_v141 import completion_path_scope as m
    from scripts.gate8_diagnostic_collect import analyze_receipt
    receipt,execution,_=source(tmp_path,monkeypatch)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    path,_=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    with pytest.raises(ValueError,match='COMPLETION_PATH_PRE_SYNC_PREFIX_SCOPE'):
        m._calculate(path.parent,receipt,execution,result_version='exposedpath-completion-path-prefill/0.1.0')


@pytest.mark.parametrize('damage',['version','history','source'])
def test_new_result_reader_still_refuses_tampering(tmp_path,monkeypatch,damage):
    from exposedpath_v141 import completion_path_scope as m
    from scripts.gate8_diagnostic_collect import analyze_receipt
    from test_gate8_identity import write_json
    receipt,execution,_=source(tmp_path,monkeypatch)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    path,value=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    if damage=='source':
        (path.parent/'diagnostics.json').write_text('{}',encoding='utf-8')
    else:
        if damage=='version':value['schema_version']='exposedpath-completion-path-prefill/99'
        else:value['full_pre_sync_dependencies'][0]['drained_raw_prefix_activity_ids'].pop()
        write_json(path,value)
    with pytest.raises(ValueError):m.load(path,receipt,execution)


def test_pending_other_thread_history_still_refuses_local_prefill(tmp_path,monkeypatch):
    from scripts.gate8_diagnostic_collect import analyze_receipt
    receipt,execution,_=source(tmp_path,monkeypatch,'pending_worker_prefix')
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    _,result=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    assert result['status']=='BLOCKED' and result['prefill']['a_records']==[]
    assert result['prefill']['reasons']==['ENGINEERING_SCOPE_PREFIX_PENDING']


def test_worker_history_does_not_hide_observed_prefix_order_conflict(tmp_path,monkeypatch):
    from scripts.gate8_diagnostic_collect import analyze_receipt
    receipt,execution,_=source(tmp_path,monkeypatch,'worker_prefix_overlap')
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    with pytest.raises(ValueError,match='COMPLETION_PATH_PRE_SYNC_PREFIX_ORDER'):
        analyze_receipt(manifest,receipt,execution,tmp_path/'derived')


@pytest.mark.parametrize('damage',['drain','drain_scope','correlation','pre_stream','mode_prefix','thread','dependency'])
def test_closed_history_does_not_waive_other_local_evidence_gates(tmp_path,monkeypatch,damage):
    from scripts.gate8_diagnostic_collect import analyze_receipt
    receipt,execution,_=source(tmp_path,monkeypatch,damage)
    manifest=json.loads((execution.parent/'manifest.json').read_text())
    try:
        _,result=analyze_receipt(manifest,receipt,execution,tmp_path/'derived')
    except ValueError:
        return
    assert result['status']=='BLOCKED' and result['prefill']['a_records']==[]
