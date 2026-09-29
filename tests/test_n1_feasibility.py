"""Finite group orchestration only; no CUDA, Nsight or model."""
import importlib.util
import json
import pytest


def api():
    assert importlib.util.find_spec('scripts.n1_model_feasibility'), 'N1 bounded delivery adapter missing'
    from scripts import n1_model_feasibility
    return n1_model_feasibility


@pytest.mark.parametrize('failure',[None,'V0','Vmarker','V16','parity'])
def test_fixed_three_groups_no_retry_and_actual_token_parity(tmp_path,failure):
    calls=[]
    def run(variant,path):
        calls.append(variant)
        if variant==failure: raise ValueError('deliberate identity/ownership failure')
        return dict(status='FEASIBLE_ONCE_PENDING_REVIEW',observed_tokens=[[1],[3 if failure=='parity' and variant=='Vmarker' else 2]],
            common_identity={'input_sha256':'a'*64,'backend':'sdpa'})
    result=api().run_groups(tmp_path/'batch',run)
    assert calls==(['V0'] if failure=='V0' else ['V0','Vmarker'] if failure in ('Vmarker','parity') else ['V0','Vmarker','V16'])
    assert result['status']==('BATCH_COMPLETE_PENDING_REVIEW' if failure is None else 'BLOCKED')
    assert result['n1_model_feasibility']=='NOT_RUN'
    assert json.loads((tmp_path/'batch/batch_report.json').read_text())==result
    with pytest.raises(FileExistsError): api().run_groups(tmp_path/'batch',run)


def test_changed_common_execution_contract_rejects(tmp_path):
    def run(variant,path):
        return dict(status='FEASIBLE_ONCE_PENDING_REVIEW',observed_tokens=[[1],[2]],
            common_identity={'input_sha256':variant})
    assert api().run_groups(tmp_path/'batch',run)['status']=='BLOCKED'
