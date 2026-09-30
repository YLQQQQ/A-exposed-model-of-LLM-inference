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


def test_current_domain_file_is_consumed_without_legacy_adapter_constant(tmp_path,monkeypatch):
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain
    from exposedpath.gate8_isolated_preflight import sha
    receipt,execution,calls=source(tmp_path,monkeypatch,variant='V0',allocations=True,internal=True)
    path=process_domain(receipt,execution,tmp_path/'domain',bridge_path=calls)
    report=dict(result_filename='domain.json',result_sha256=sha(path))
    assert api().validate_domain(report,path)['allocation_records']
    report['result_sha256']='f'*64
    with pytest.raises(ValueError,match='DOMAIN_RESULT'): api().validate_domain(report,path)


@pytest.mark.parametrize('damage',[None,'token','input','commit','runner','snapshot','marker','failed'])
def test_remaining_groups_preserve_reviewed_v0_parity_and_stop(tmp_path,damage):
    from copy import deepcopy
    common=dict(runner_git_commit='a'*40,runner_source_sha256='b'*64,prompt='c'*64,target_snapshot={'version':'fixed'})
    baseline=dict(common_identity=common,observed_tokens=[[463],[2529]])
    seen=[]
    def execute(v,path):
        seen.append(v); record=deepcopy(baseline); record['status']='FEASIBLE_ONCE_PENDING_REVIEW'
        record['common_identity']['runner_git_commit']='d'*40
        if v=='Vmarker':
            if damage=='token': record['observed_tokens']=[[463],[0]]
            if damage=='input': record['common_identity']['prompt']='foreign'
            if damage=='commit': record['common_identity']['runner_git_commit']='e'*40
            if damage=='runner': record['common_identity']['runner_source_sha256']='f'*64
            if damage=='snapshot': record['common_identity']['target_snapshot']={}
            if damage=='marker': record['status']='NOT_RUN'
            if damage=='failed': raise ValueError('deliberate missing dependency')
        return record
    result=api().run_remaining_groups(tmp_path/'batch',execute,baseline,'d'*40)
    assert seen==(['Vmarker','V16'] if damage is None else ['Vmarker'])
    assert result['status']==('BATCH_COMPLETE_PENDING_REVIEW' if damage is None else 'BLOCKED')
    assert [r['variant'] for r in result['groups']]==['Vmarker','V16']
    assert result['baseline']['observed_tokens']==[[463],[2529]]
    assert result['n1_model_feasibility']=='NOT_RUN'


@pytest.mark.parametrize('damage',[None,'source','baseline','review','copied_expected','token'])
def test_baseline_source_and_review_must_match_not_just_expected_values(tmp_path,monkeypatch,damage):
    from exposedpath.gate8_isolated_preflight import sha
    from test_n1_reference_bytes import fixture
    _,_,code,old,review,reference=fixture(tmp_path,monkeypatch)
    (old/'raw.nsys-rep').write_bytes(b'sealed raw')
    reference['baseline_files']['raw.nsys-rep']=sha(old/'raw.nsys-rep')
    reference['baseline_sizes']['raw.nsys-rep']=(old/'raw.nsys-rep').stat().st_size
    if damage=='source': (code/'producer.py').write_bytes(b'changed')
    if damage=='baseline': (old/'raw.nsys-rep').write_bytes(b'changed')
    if damage=='review': reference['review_sha256']='f'*64
    if damage=='copied_expected': reference['common_identity']['fixed_input_tokens']=128
    if damage=='token': reference['observed_tokens']=[[463],[0]]
    if damage is None: assert api().validate_reference(reference,review,code)==reference
    else:
        with pytest.raises(ValueError): api().validate_reference(reference,review,code)


@pytest.mark.parametrize('damage',['input','variant'])
def test_remaining_manifest_parity_is_checked_before_profile(tmp_path,monkeypatch,damage):
    from test_n1_verified_entry import source
    from test_gate8_identity import UUID
    from exposedpath.gate8_isolated_preflight import sha,write_new
    from exposedpath import gate8_diagnostic
    from scripts import gate8_diagnostic_collect
    _,args,_,_=source(tmp_path,monkeypatch,variant='Vmarker')
    monkeypatch.setattr(api(),'read',lambda p:json.loads(p.read_text(encoding='utf-8-sig')))
    manifest=json.loads(args['manifest_path'].read_text()); manifest['target_python']={'actual':{'snapshot':{'version':'cpu'}}}
    manifest.update(gpu_uuid=UUID,gpu_pci_bus_id='00000000:E1:00.0')
    prepared=tmp_path/'prepared'; prepared.mkdir(); write_new(prepared/'manifest.json',manifest)
    baseline=dict(common_identity=api().common_identity(manifest))
    if damage=='input': baseline['common_identity']['prompt_tokens_sha256']='f'*64
    else:
        from exposedpath.n1_model import declaration
        manifest['n1_model']=declaration('V0'); (prepared/'manifest.json').write_text(json.dumps(manifest))
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',lambda **kw:prepared)
    def forbidden(*a,**kw): pytest.fail('profile started before common-input conflict rejected')
    monkeypatch.setattr(gate8_diagnostic_collect,'run_once',forbidden)
    prompt=tmp_path/'prompt'; prompt.write_bytes(b'cpu-only')
    c=dict(prompt=str(prompt),prompt_sha256=sha(prompt),model='cpu',inventory='cpu',inventory_sha256='a'*64,
        commit=manifest['runner_git_commit'],target_python='cpu',site_root='cpu',gpu_uuid=UUID,gpu_pci_bus_id=manifest['gpu_pci_bus_id'],
        reviewed_baseline=baseline,nsys='cpu')
    with pytest.raises(ValueError,match='REMAINING_PREMODEL_PARITY|VARIANT'):
        api().collect_group('Vmarker',tmp_path/'new_group',c)
