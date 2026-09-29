"""Finite Engineering candidates, real file entry; no CUDA/model execution."""
import importlib
import json
from pathlib import Path

import pytest
from test_gate8_identity import write_json, sha


def api():
    assert importlib.util.find_spec('exposedpath.gate10_workload'), 'Gate10 workload adapter missing'
    return importlib.import_module('exposedpath.gate10_workload')


def prompt(n=128):
    return dict(schema_version='exposedpath-v3', tokenizer_id='Qwen2.5-1.5B-Instruct',
        fixed_input_tokens=n,special_tokens={'eos_token_id':999},
        samples=[dict(input_ids=list(range(1,33))*(n//32),attention_mask=[1]*n)])


def test_reproducible_prefix_axis_and_no_overwrite(tmp_path):
    m=api(); seed=write_json(tmp_path/'seed.json',prompt(32))
    paths=m.make_inputs(seed,sha(seed),tmp_path/'inputs')
    assert [json.loads(p.read_text())['fixed_input_tokens'] for p in paths]==[128,512]
    for p in paths:
        v=json.loads(p.read_text()); ids=v['samples'][0]['input_ids']
        assert ids[:33]==list(range(1,33))+[1]
        assert v['construction']['source_sha256']==sha(seed)
    with pytest.raises(FileExistsError): m.make_inputs(seed,sha(seed),tmp_path/'inputs')
    with pytest.raises(ValueError): m.make_inputs(seed,'0'*64,tmp_path/'bad')


@pytest.mark.parametrize('damage',['length','mask','float','range','special','max_position','empty'])
def test_invalid_input_is_not_silently_padded_or_clipped(damage):
    m=api(); p=prompt(); config=dict(model_type='qwen2',vocab_size=1000,max_position_embeddings=32768)
    if damage=='length': p['samples'][0]['input_ids'].pop()
    if damage=='mask': p['samples'][0]['attention_mask'][0]=0
    if damage=='float': p['samples'][0]['input_ids'][0]=1.0
    if damage=='range': p['samples'][0]['input_ids'][0]=1000
    if damage=='special': p['samples'][0]['input_ids'][0]=999
    if damage=='max_position': config['max_position_embeddings']=128
    if damage=='empty': p['samples']=[]
    with pytest.raises(ValueError): m.validate_input(p,config,128)


def test_target_file_entry_accepts_declared_length_and_rejects_mismatch(tmp_path,monkeypatch):
    from test_gate8_diagnostic_entry import case
    from exposedpath import gate8_diagnostic as entry
    m=api(); args,state=case(monkeypatch,tmp_path)
    monkeypatch.chdir(tmp_path)
    p=prompt(); write_json(args['prompt_path'],p)
    manifest=json.loads(args['manifest_path'].read_text())
    model=Path(manifest['model_id']); model.mkdir(exist_ok=True)
    write_json(model/'config.json',dict(model_type='qwen2',vocab_size=1000,max_position_embeddings=32768))
    manifest.update(fixed_input_tokens=128,prompt_tokens_sha256=sha(args['prompt_path']),
        gate10_workload=m.declaration(128))
    from exposedpath_v141.gate9_domain import G1,declaration
    manifest['domain_qualification']=declaration(G1)
    write_json(args['manifest_path'],manifest)
    monkeypatch.setattr(entry,'validate_pre_model_identity',lambda *a:[])
    from exposedpath import runner
    from test_runner_token_ready import _FakeInput
    def tensor(data,**kw):
        value=_FakeInput(); value.shape=(1,len(data[0])); return value
    monkeypatch.setattr(runner.torch,'tensor',tensor)
    result=entry.run_diagnostic(**args)
    assert json.loads(result.read_text())['status']=='DIAGNOSTIC_COMPLETE'
    assert state['loads']==1
    ledger=json.loads((result.parent/'producer/pass_identity.json').read_text())
    assert ledger['requests'][1]['actual_output_tokens']==2
    observed=json.loads((result.parent/'workload_observed.json').read_text())
    assert observed['observations'][0]['actual_input_tokens']==128
    assert observed['observations'][0]['identity']==ledger['requests'][1]['identity']
    manifest['fixed_input_tokens']=512
    write_json(args['manifest_path'],manifest)
    args['output_dir']=tmp_path/'bad'
    with pytest.raises(ValueError): entry.run_diagnostic(**args)
    assert state['loads']==1


def test_unknown_workload_version_rejected():
    m=api(); d=m.declaration(128); d['version']='future'
    with pytest.raises(ValueError): m.input_length({'gate10_workload':d,'fixed_input_tokens':128})


def test_collector_declared_domain_dispatch_uses_actual_file_chain(tmp_path,monkeypatch):
    from test_gate9_domain import source
    from scripts import gate8_diagnostic_collect as collector
    receipt,execution,paths=source(tmp_path,monkeypatch)
    assert hasattr(collector,'analyze_receipt'), 'collector domain dispatch missing'
    out,value=collector.analyze_receipt(json.loads(paths['wmpc_manifest'].read_text()),receipt,execution,tmp_path/'domain')
    assert value['declaration']['profile']=='G1_NATURAL_PROJECTED_A/0.1.0'
    assert value['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
    assert out.name=='domain.json'
    assert all(r['facts']['conditional_suffix_proofs'] for r in value['requests'])


@pytest.mark.parametrize('failed',[False,True])
def test_finite_batch_stops_no_retry_and_preserves_unrun_point(tmp_path,failed):
    assert importlib.util.find_spec('scripts.gate10_feasibility'), 'bounded batch missing'
    from scripts.gate10_feasibility import run_candidates
    calls=[]
    def point(n,path):
        calls.append(n)
        if failed: raise RuntimeError('deliberate failure, not evidence of OOM')
        return dict(status='FEASIBLE_ONCE_NOT_STABILITY',actual_input_tokens=n,actual_output_tokens=2)
    out=run_candidates(tmp_path/'batch',point)
    assert calls==([128] if failed else [128,512])
    assert out['gate10_verdict']=='NOT_RUN'
    assert out['points'][1]['status']==('NOT_RUN' if failed else 'FEASIBLE_ONCE_NOT_STABILITY')
    if failed: assert out['points'][0]['failure_kind']=='UNCLASSIFIED_FAILURE'
    assert json.loads((tmp_path/'batch/batch_report.json').read_text())==out
    with pytest.raises(FileExistsError): run_candidates(tmp_path/'batch',point)


@pytest.mark.parametrize('kind,expected',[
    ('oom','RESOURCE_INFEASIBLE'),('eos','TOKEN_COUNT_EXCLUSION'),
    ('timeout','TIMEOUT_UNRESOLVED'),('analysis','EVIDENCE_OR_ANALYSIS_FAILURE'),
    ('missing','EXECUTION_FAILURE_UNRESOLVED')])
def test_failure_categories_do_not_guess_oom(tmp_path,kind,expected):
    from scripts.gate10_feasibility import failure_kind
    process={'timed_out':kind=='timeout'}
    (tmp_path/'diagnostic-entry').mkdir()
    (tmp_path/'diagnostic/producer').mkdir(parents=True)
    if kind=='oom': write_json(tmp_path/'diagnostic-entry/exit.json',{'error':'OutOfMemoryError: allocation failed'})
    if kind=='eos': write_json(tmp_path/'diagnostic/producer/pass_identity.json',{'reasons':['EARLY_EOS_OR_OUTPUT_COUNT_MISMATCH']})
    if kind=='analysis': write_json(tmp_path/'collection_report.json',{'collection':{'status':'COMPLETE'},'error':'mapping missing'})
    assert failure_kind(tmp_path,process)==expected


def test_zero_exit_cannot_hide_analysis_failure(tmp_path,monkeypatch):
    from exposedpath import gate8_diagnostic
    from scripts import gate8_diagnostic_collect as collect,gate10_feasibility as batch
    p=write_json(tmp_path/'input_128.json',prompt())
    def prepare(**kw):
        out=kw['output_dir']; out.mkdir(parents=True)
        write_json(out/'manifest.json',{'gpu_uuid':'gpu-test','gpu_pci_bus_id':'pci-test'})
        return out
    def process(argv,logs,**kw):
        out=Path(argv[argv.index('--output')+1]); out.mkdir()
        write_json(out/'collection_report.json',{'status':'DIAGNOSTIC_COLLECTED_NOT_QUALIFIED',
            'collection':{'status':'COMPLETE'},'error':'MODEL_A_SCOPE_BLOCKED'})
        return {'status':'COMPLETE','exit_code':0}
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',prepare)
    monkeypatch.setattr(collect,'run_once',process)
    c=dict(input_root=str(tmp_path),input_hashes={'128':sha(p)},model='unused',inventory='unused',
        inventory_sha256='0'*64,commit='a'*40,target_python='unused',site_root='unused',nsys='unused',
        gpu_uuid='gpu-test',gpu_pci_bus_id='pci-test')
    result=batch.collect_point(128,tmp_path/'point',c)
    assert result['status']=='BLOCKED'
    assert result['failure_kind']=='EVIDENCE_OR_ANALYSIS_FAILURE'
