"""Resident producer file lifecycle with CPU-only devices/model doubles."""
import hashlib
import itertools
import json
from contextlib import nullcontext

import pytest

from test_n1_model_calls import fixture, module
from test_runner_token_ready import _FakeInput, _patch_cpu_torch


def setup(tmp_path, monkeypatch, variant='Vsync'):
    from exposedpath import runner
    _patch_cpu_torch(monkeypatch)
    model, cuda, stream, identity, events = fixture()
    cuda.Stream = lambda **kw: stream
    cuda.stream = lambda s: nullcontext()
    cuda.current_device = lambda: 0
    cuda.synchronize = lambda: events.append('drain')
    cuda.nvtx.mark = lambda label: events.append(('mark', label))
    monkeypatch.setattr(runner.torch, 'cuda', cuda)
    monkeypatch.setattr(runner.torch, 'tensor', lambda data, **kw: _FakeInput())
    prompt = tmp_path/'prompt.json'
    prompt.write_text(json.dumps({'input_ids': [[3, 4, 5, 6]], 'attention_mask': [[1, 1, 1, 1]]}))
    manifest = dict(schema_version='exposedpath-n1-resident-plan/0.1.0', identity=identity,
        n1=module().declaration(variant), prompt_sha256=hashlib.sha256(prompt.read_bytes()).hexdigest(),
        output_tokens=2, batch_size=1, warmup_count=1, repeat_count=1,
        eos_token_id=99,
        execution_mode='eager', backend='sdpa', logical_device=0,
        precondition='CALLER_VERIFIED_RESIDENT_MODEL_INPUT_AND_PLATFORM')
    plan = tmp_path/'manifest.json'
    plan.write_text(json.dumps(manifest))
    return model, cuda, stream, events, plan, prompt


def test_resident_file_entry_records_actual_calls_drain_and_boundaries(tmp_path, monkeypatch):
    model, cuda, stream, events, plan, prompt = setup(tmp_path, monkeypatch)
    assert hasattr(module(), 'run_resident_to_files')
    receipt = module().run_resident_to_files(model=model, manifest_path=plan, prompt_path=prompt,
        output_dir=tmp_path/'out', eos_token_id=99, clock_ns=itertools.count(100).__next__)
    data = json.loads(receipt.read_text())
    assert data['status'] == 'COMPLETE_PENDING_TRACE_OWNERSHIP'
    assert data['n1_model_feasibility'] == 'NOT_RUN'
    paths = data['files']
    assert (receipt.parent/'manifest.json').read_bytes() == plan.read_bytes()
    assert (receipt.parent/'prompt.json').read_bytes() == prompt.read_bytes()
    assert data['identity']['request_id'] == 'request-0'
    assert data['observed_model']['backend'] == 'sdpa'
    assert data['source_sha256']['exposedpath/n1_model.py'] == hashlib.sha256(
        __import__('pathlib').Path(module().__file__).read_bytes()).hexdigest()
    for ref in paths.values():
        assert hashlib.sha256((receipt.parent/ref['path']).read_bytes()).hexdigest() == ref['sha256']
    calls = json.loads((receipt.parent/'model_calls.json').read_text())
    host = json.loads((receipt.parent/'host_boundaries.json').read_text())
    drain = json.loads((receipt.parent/'drain_ledger.json').read_text())['drains'][0]
    assert drain['status'] == 'COMPLETE'
    assert drain['host_end_ns'] <= host[0]['host_observed_ns']
    assert len(host) == 3 and calls['measured']['observed_tokens'] == [[13], [14]]
    assert calls['warmup']['identity']['request_id'] != calls['measured']['identity']['request_id']
    assert len(calls['warmup']['interventions']) == len(calls['measured']['interventions']) == 1
    assert calls['warmup']['generation'] == calls['measured']['generation']
    assert events.count('sync') == 2  # One warmup decode + one measured decode, never prefill.
    assert events.count('drain') == 3  # Existing warmup entry/exit + final request drain.
    with pytest.raises(FileExistsError):
        module().run_resident_to_files(model=model, manifest_path=plan, prompt_path=prompt,
            output_dir=tmp_path/'out', eos_token_id=99)


@pytest.mark.parametrize('damage', ['prompt', 'mode', 'declaration', 'device', 'eos'])
def test_plan_conflict_rejected_before_model_calls(tmp_path, monkeypatch, damage):
    model, cuda, stream, events, plan, prompt = setup(tmp_path, monkeypatch)
    assert hasattr(module(), 'run_resident_to_files')
    value = json.loads(plan.read_text())
    if damage == 'prompt': prompt.write_text('{}')
    if damage == 'mode': value['execution_mode'] = 'compile'
    if damage == 'declaration': value['n1']['layer_index'] = 7
    if damage == 'device': value['logical_device'] = 3
    if damage == 'eos': value['eos_token_id'] = 77
    plan.write_text(json.dumps(value))
    with pytest.raises(ValueError, match='N1_MODEL'):
        module().run_resident_to_files(model=model, manifest_path=plan, prompt_path=prompt, output_dir=tmp_path/'out', eos_token_id=99)
    assert model.calls == 0


def test_failed_warmup_persisted_not_relabelled_complete(tmp_path, monkeypatch):
    model, cuda, stream, events, plan, prompt = setup(tmp_path, monkeypatch)
    assert hasattr(module(), 'run_resident_to_files')
    def broken(value): raise RuntimeError('original warmup error')
    model.model.layers[15].forward = broken
    with pytest.raises(RuntimeError, match='original warmup error'):
        module().run_resident_to_files(model=model, manifest_path=plan, prompt_path=prompt, output_dir=tmp_path/'out', eos_token_id=99)
    receipt = json.loads((tmp_path/'out/producer_receipt.json').read_text())
    assert receipt['status'] == 'FAILED'
    assert receipt['error'] == 'RuntimeError:original warmup error'
    assert receipt['n1_model_feasibility'] == 'NOT_RUN'
