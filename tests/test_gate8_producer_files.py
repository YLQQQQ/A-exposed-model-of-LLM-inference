"""Real runner file wrapper with CPU token/model doubles only."""
import json
import os
from itertools import count
import pytest
from exposedpath import runner
from test_gate8_identity import producer_pass
from test_runner_token_ready import _FakeToken, _FakeModel, _FakeInput, _patch_cpu_torch


@pytest.mark.parametrize('pass_id', ['pass0','pass1'])
def test_runner_publishes_real_outcomes_with_non_circular_hashes(monkeypatch,tmp_path,pass_id):
    execute = getattr(runner,'run_gate8_requests_to_files',None)
    assert callable(execute), 'actual runner products still memory-only'
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setattr(runner.torch.cuda.nvtx,'mark',lambda label:None)
    original=producer_pass()
    fields={k:original[k] for k in ('experiment_id','wmpc_id','run_id','attempt_id',
        'wmpc_manifest_sha256','prompt_sha256','runner_source_sha256','runner_git_commit','runner_git_dirty')}
    fields.update(pid=os.getpid(),pass_id=pass_id)
    clock=count(100)
    path=execute(output_dir=tmp_path/'producer',model=_FakeModel(iter([_FakeToken([1],[]),_FakeToken([2],[])])),
        input_ids=_FakeInput(),attention_mask=object(),output_len=2,device='cpu',pass_fields=fields,
        request_plan=[{'request_id':'r0','repeat_id':'0','request_role':'measured'}],clock_ns=lambda:next(clock))
    receipt=json.loads(path.read_text())
    from test_gate8_identity import sha
    for ref in receipt['files'].values():
        assert sha(path.parent/ref['filename'])==ref['sha256']
    ledger=json.loads((path.parent/'pass_identity.json').read_text())
    assert ledger['requests'][0]['outcome']=='COMPLETE'
    host=json.loads((path.parent/'host_boundaries.json').read_text())
    assert [r['payload']['boundary_id'] for r in host]==ledger['requests'][0]['observed_boundary_ids']
    assert ledger['raw_artifact_sha256'] is None
    with pytest.raises(FileExistsError):
        execute(output_dir=path.parent)
