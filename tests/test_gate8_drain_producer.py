"""CPU doubles around the real producer; no CUDA or collector execution."""
import inspect
import json
import os
from itertools import count

import pytest
from exposedpath import runner
from test_gate8_identity import producer_pass, sha
from test_runner_token_ready import _FakeToken, _FakeModel, _FakeInput, _patch_cpu_torch


@pytest.mark.parametrize('pass_id', ['pass0', 'pass1'])
@pytest.mark.parametrize('failed', [False, True])
def test_existing_drain_is_recorded_without_extra_sync(monkeypatch, tmp_path, pass_id, failed):
    assert 'record_drains' in inspect.signature(runner.run_gate8_requests).parameters
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda, 'current_device', lambda:0)
    calls, labels = [], []
    def drain():
        calls.append('drain')
        if failed:
            raise RuntimeError('synthetic drain error')
    monkeypatch.setattr(runner.torch.cuda, 'synchronize', drain)
    monkeypatch.setattr(runner.torch.cuda.nvtx, 'mark', labels.append)
    monkeypatch.setattr(runner.torch.cuda.nvtx, 'range_push', labels.append)
    ledger = producer_pass()
    fields = {k: ledger[k] for k in ('experiment_id', 'wmpc_id', 'run_id', 'attempt_id',
        'wmpc_manifest_sha256', 'prompt_sha256', 'runner_source_sha256', 'runner_git_commit', 'runner_git_dirty')}
    fields.update(pid=os.getpid(), pass_id=pass_id)
    ticks = count(100)
    path = runner.run_gate8_requests_to_files(output_dir=tmp_path/'producer',
        record_drains=True, model=_FakeModel(iter([_FakeToken([1], []), _FakeToken([2], [])])),
        input_ids=_FakeInput(), attention_mask=object(), output_len=2, device='cuda:0',
        pass_fields=fields, request_plan=[dict(request_id='r0', repeat_id='0', request_role='measured')],
        clock_ns=lambda: next(ticks))
    receipt = json.loads(path.read_text())
    assert receipt['schema_version'] == 'exposedpath-gate8-producer-receipt/0.2.0'
    ref = receipt['files']['drain_ledger.json']
    assert ref['sha256'] == sha(path.parent/ref['filename'])
    records = json.loads((path.parent/ref['filename']).read_text())
    assert calls == ['drain']
    assert len(records['drains']) == 1
    record = records['drains'][0]
    assert record['status'] == ('FAILED' if failed else 'COMPLETE')
    assert record['identity']['request_id'] == 'r0'
    assert record['logical_device'] == 0
    assert record['host_start_ns'] <= record['host_end_ns']
    assert receipt['status'] == ('INCOMPLETE' if failed else 'COMPLETE')
    assert bool([s for s in labels if s.startswith('EXPOSEDPATH_DRAIN_V1:')]) == (pass_id == 'pass1')
    if not failed:
        host = json.loads((path.parent/'host_boundaries.json').read_text())
        assert record['host_end_ns'] <= host[0]['host_observed_ns']


@pytest.mark.parametrize('device', ['cuda:1','cuda'])
def test_declared_drain_device_is_checked_before_any_warmup(monkeypatch,device):
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda, 'current_device', lambda:0)
    calls=[]
    monkeypatch.setattr(runner, 'run_warmup', lambda *a,**k:calls.append('warmup'))
    ledger=producer_pass()
    fields={k:ledger[k] for k in ('experiment_id','wmpc_id','run_id','attempt_id',
        'wmpc_manifest_sha256','prompt_sha256','runner_source_sha256','runner_git_commit','runner_git_dirty')}
    fields.update(pid=os.getpid(),pass_id='pass0')
    with pytest.raises(ValueError,match='DRAIN_'):
        runner.run_gate8_requests(record_drains=True,model=None,input_ids=None,attention_mask=None,
            output_len=2,device=device,pass_fields=fields,request_plan=[
                dict(request_id='w0',repeat_id='warmup-0',request_role='warmup'),
                dict(request_id='r0',repeat_id='0',request_role='measured')])
    assert calls==[]


def test_drain_recorder_rejects_half_configured_pass0_marker():
    from exposedpath.gate8_drain import DrainRecorder
    identity=producer_pass()['requests'][0]['identity']; identity['pass_id']='pass0'
    with pytest.raises(ValueError,match='DRAIN_'):
        DrainRecorder(identity,'drain',0,clock_ns=lambda:1,push=lambda label:None)
