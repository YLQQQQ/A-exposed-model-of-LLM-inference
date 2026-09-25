"""Real filesystem entry over synthetic producer/SQLite; never Nsight evidence."""
import importlib
import json
from pathlib import Path
import pytest
from test_gate8_identity import write_json, sha
from test_gate8_signed_time import signed_inputs


def api():
    assert importlib.util.find_spec('exposedpath_v141.gate8_files'), 'sealed file entry missing'
    return importlib.import_module('exposedpath_v141.gate8_files')


def input_files(tmp_path, monkeypatch):
    inputs, host = signed_inputs(tmp_path, monkeypatch, return_sources=True)
    db, pre, probe, ledger_path = inputs
    raw = tmp_path/'synthetic.rep'
    raw.write_bytes(b'SYNTHETIC fixture, not a real REP')
    prompt = write_json(tmp_path/'prompt.json', {'token_ids':[10,11]})
    runner = tmp_path/'producer.py'
    runner.write_text('# synthetic producer source identity\n')
    ledger = json.loads(ledger_path.read_text())
    manifest = {k:ledger[k] for k in ('experiment_id','wmpc_id','run_id','run_role','data_role','runner_git_commit','runner_git_dirty')}
    manifest.update(prompt_tokens_sha256=sha(prompt), runner_source_sha256=sha(runner),
                    gpu_index_physical=3, gpu_index_logical=0,
                    gpu_uuid=json.loads(pre.read_text())['gpu_uuid'],
                    gpu_pci_bus_id=json.loads(pre.read_text())['pci_bus_id'])
    wmpc = write_json(tmp_path/'wmpc.json', manifest)
    ledger.update(wmpc_manifest_sha256=sha(wmpc), prompt_sha256=sha(prompt), runner_source_sha256=sha(runner))
    ledger_path = write_json(tmp_path/'pass_identity.json', ledger)
    producer = write_json(tmp_path/'producer_receipt.json', {
        'schema_version':'exposedpath-gate8-producer-receipt/0.1.0',
        'run_id':ledger['run_id'],'pass_id':ledger['pass_id'],'attempt_id':ledger['attempt_id'],
        'status':'COMPLETE','gate8_verdict':'NOT_RUN',
        'files':{name:{'filename':name,'sha256':sha(p),'size_bytes':p.stat().st_size}
                 for name,p in [('pass_identity.json',ledger_path),('host_boundaries.json',host)]}})
    export = write_json(tmp_path/'export_report.json', {
        'status':'PASS','error':None,'attempt_count':1,'successful_attempt':1,'analyzer_allowed':True,
        'rep_sha256':sha(raw),'canonical_sqlite_sha256':sha(db),
        'attempts':[{'number':1,'status':'PASS','rep_sha256':sha(raw),'sqlite_sha256':sha(db),
                     'exit_code':0,'process_exited':True,'timed_out':False,'terminated_pid':None,
                     'validation_issues':[],'sqlite_size':db.stat().st_size}]})
    return dict(raw=raw, sqlite=db, pass_identity=ledger_path, host_ledger=host,
                preflight=pre, cuda_probe=probe, wmpc_manifest=wmpc, prompt=prompt,
                runner_source=runner, producer_receipt=producer, export_report=export)


def receipt(tmp_path, monkeypatch):
    files = input_files(tmp_path, monkeypatch)
    path = api().write_input_receipt(tmp_path/'input_receipt.json', artifacts=files,
              collector_version='2026.1.1.204', capture_session_id='synthetic-session')
    return path, files


def test_actual_file_entry_unknown_blocks_numbers(monkeypatch, tmp_path):
    path, files = receipt(tmp_path, monkeypatch)
    before = {k:sha(p) for k,p in files.items()}
    result_path = api().process_gate8_receipt(path, tmp_path/'output')
    result = api().load_chain_result(result_path)
    assert result['status'] == 'BLOCKED'
    assert result['gate8_verdict'] == 'NOT_RUN'
    assert (result_path.parent/'provenance/wmpc_manifest.json').read_bytes() == files['wmpc_manifest'].read_bytes()
    assert (result_path.parent/'provenance/input_receipt.json').read_bytes() == path.read_bytes()
    assert not list(result_path.parent.rglob('ab_manifest.json'))
    assert not list(result_path.parent.rglob('derived_manifest.json'))
    assert {k:sha(p) for k,p in files.items()} == before


def test_signed_full_file_chain_synthetic_only(monkeypatch, tmp_path):
    path, _ = receipt(tmp_path, monkeypatch)
    blocked = api().process_gate8_receipt(path, tmp_path/'blocked')
    counters = json.loads((blocked.parent/'analysis/integrity.json').read_text())
    for r in counters:
        r.update(status='ZERO_CONFIRMED', dropped_count=0, basis='COLLECTOR_COUNTER', finalized=True,
                 coverage_complete=True, evidence_refs=[{'sha256':'f'*64,'selector':'SYNTHETIC_COUNTER'}], reasons=[])
    evidence = write_json(tmp_path/'synthetic_integrity.json', counters)
    out = api().process_gate8_receipt(path, tmp_path/'full', integrity_receipts_path=evidence, synthetic_fixture=True)
    result = api().load_chain_result(out)
    assert result['status'] == 'SYNTHETIC_CALCULATION_ONLY'
    assert result['validation_role'] == 'SYNTHETIC_REGRESSION_ONLY'
    from exposedpath_v141.derived import load_derived_bundle
    d = load_derived_bundle(out.parent/'analysis/derived/derived_manifest.json', ab_manifest=out.parent/'analysis/ab/ab_manifest.json')
    assert len(d['d_window_records']) == 6
    assert next(r for r in d['d_window_records'] if r['phase']=='full_request' and r['request_id']=='request-0')['D_margin_ns'] == -150
    with pytest.raises(FileExistsError):
        api().process_gate8_receipt(path, out.parent)
    (out.parent/'analysis/coverage.json').write_text('{}')
    with pytest.raises(ValueError, match='HASH'):
        api().load_chain_result(out)


@pytest.mark.parametrize('damage', ['missing','partial','identity','pass'])
def test_input_damage_is_fail_closed_before_publication(monkeypatch, tmp_path, damage):
    path, files = receipt(tmp_path, monkeypatch)
    if damage == 'missing':
        files['host_ledger'].unlink()
    elif damage == 'partial':
        files['pass_identity'].write_text('{')
    else:
        value = json.loads(files['pass_identity'].read_text())
        value['run_id' if damage=='identity' else 'pass_id'] = 'other' if damage=='identity' else 'pass0'
        write_json(files['pass_identity'],value)
    with pytest.raises((ValueError,OSError)):
        api().process_gate8_receipt(path, tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_result_cannot_relabel_run_identity(monkeypatch, tmp_path):
    path, _ = receipt(tmp_path, monkeypatch)
    out = api().process_gate8_receipt(path,tmp_path/'out')
    result = json.loads(out.read_text())
    result['identity']['run_id'] = 'another-run'
    write_json(out,result)
    with pytest.raises(ValueError, match='IDENTITY'):
        api().load_chain_result(out)


def test_interrupted_analysis_never_publishes_final_directory(monkeypatch, tmp_path):
    path, _ = receipt(tmp_path, monkeypatch)
    from exposedpath_v141 import gate8_analysis
    def interrupt(*args,**kwargs):
        raise RuntimeError('simulated process interruption')
    monkeypatch.setattr(gate8_analysis,'analyze_gate8_local',interrupt)
    with pytest.raises(RuntimeError,match='interruption'):
        api().process_gate8_receipt(path,tmp_path/'out')
    assert not (tmp_path/'out').exists()
    assert not list(tmp_path.glob('.out-partial-*/chain_result.json'))


def test_producer_receipt_cannot_pair_other_host_ledger(monkeypatch,tmp_path):
    files=input_files(tmp_path,monkeypatch)
    p=files['producer_receipt']
    value=json.loads(p.read_text())
    value['files']['host_boundaries.json']['sha256']='0'*64
    write_json(p,value)
    with pytest.raises(ValueError,match='HASH'):
        api().write_input_receipt(tmp_path/'receipt.json',artifacts=files,
            collector_version='fixture',capture_session_id='fixture')


def test_export_report_must_bind_exact_raw_and_sqlite(monkeypatch,tmp_path):
    files=input_files(tmp_path,monkeypatch)
    p=files['export_report']
    report=json.loads(p.read_text())
    report['rep_sha256']='a'*64
    write_json(p,report)
    with pytest.raises(ValueError,match='EXPORT'):
        api().write_input_receipt(tmp_path/'receipt.json',artifacts=files,
            collector_version='fixture',capture_session_id='fixture')


def test_incomplete_planned_request_blocks_even_synthetic_counter(monkeypatch,tmp_path):
    files=input_files(tmp_path,monkeypatch)
    ledger=json.loads(files['pass_identity'].read_text())
    ledger['requests'][1].update(outcome='FAILED',reasons=['SYNTHETIC_FAILURE'])
    write_json(files['pass_identity'],ledger)
    producer=json.loads(files['producer_receipt'].read_text())
    producer['status']='INCOMPLETE'
    producer['files']['pass_identity.json'].update(sha256=sha(files['pass_identity']),size_bytes=files['pass_identity'].stat().st_size)
    write_json(files['producer_receipt'],producer)
    path=api().write_input_receipt(tmp_path/'receipt.json',artifacts=files,collector_version='fixture',capture_session_id='fixture')
    blocked=api().process_gate8_receipt(path,tmp_path/'blocked')
    counters=json.loads((blocked.parent/'analysis/integrity.json').read_text())
    for r in counters:
        r.update(status='ZERO_CONFIRMED',dropped_count=0,basis='COLLECTOR_COUNTER',finalized=True,
                 coverage_complete=True,evidence_refs=[{'sha256':'f'*64,'selector':'SYNTHETIC_COUNTER'}],reasons=[])
    evidence=write_json(tmp_path/'synthetic_integrity.json',counters)
    out=api().process_gate8_receipt(path,tmp_path/'second',integrity_receipts_path=evidence,synthetic_fixture=True)
    assert api().load_chain_result(out)['status']=='BLOCKED'
    assert not list(out.parent.rglob('ab_manifest.json'))
