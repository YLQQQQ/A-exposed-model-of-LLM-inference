"""CPU doubles for the new controlled request producer, never CUDA evidence."""
import importlib
import json
import os
from itertools import count

import pytest

from test_gate8_identity import producer_pass


class Backend:
    def __init__(self, wrong=False, fail=False):
        self.events=[]
        self.wrong,self.fail=wrong,fail
    def mark(self,label): self.events.append(('mark',label))
    def push(self,label): self.events.append(('push',label))
    def pop(self): self.events.append(('pop',))
    def prepare(self): self.events.append(('prepare',))
    def submit(self,token): self.events.append(('submit',token)); self.token=token
    def copy(self): self.events.append(('copy',))
    def wait(self):
        self.events.append(('wait',))
        if self.fail: raise RuntimeError('controlled wait failure')
    def read(self): self.events.append(('read',)); return -1 if self.wrong else self.token


def fields():
    p=producer_pass()
    return {**{k:p[k] for k in ('experiment_id','wmpc_id','run_id','attempt_id','pass_id',
        'wmpc_manifest_sha256','prompt_sha256','runner_source_sha256','runner_git_commit','runner_git_dirty')},
        'pid':os.getpid()}


@pytest.mark.parametrize('failure',[None,'wrong','wait'])
def test_actual_controlled_producer_files_and_read_before_completion(tmp_path,failure):
    mod=importlib.import_module('exposedpath_v141.gate8_controlled')
    backend=Backend(wrong=failure=='wrong',fail=failure=='wait')
    clock=count(100)
    path=mod.run_controlled_to_files(tmp_path/'producer',pass_fields=fields(),backend=backend,
                                    clock_ns=lambda:next(clock))
    receipt=json.loads(path.read_text())
    ledger=json.loads((path.parent/'pass_identity.json').read_text())
    operations=json.loads((path.parent/'operation_ledger.json').read_text())
    assert receipt['gate8_verdict']=='NOT_RUN'
    if failure:
        assert receipt['status']=='INCOMPLETE'
        assert ledger['requests'][0]['outcome']=='FAILED'
        assert ledger['requests'][0]['actual_output_tokens']==0
        assert len([e for e in backend.events if e[0]=='submit'])==1
    else:
        assert receipt['status']=='COMPLETE'
        assert len(ledger['requests'])==2
        assert all(r['actual_output_tokens']==2 for r in ledger['requests'])
        assert [o['observed_token'] for o in operations['tokens']]==[11,12,21,22]
        events=[e[0] for e in backend.events]
        assert events.count('prepare')==2
        for i,e in enumerate(backend.events):
            if e[0]=='mark' and 'token_ready' in e[1]:
                assert backend.events[i-1][0]=='read'
        assert all(o['sync_origin']=='q0_controlled' for o in operations['tokens'])
    with pytest.raises(FileExistsError):
        mod.run_controlled_to_files(path.parent,pass_fields=fields(),backend=backend)


def test_controlled_native_has_real_d2h_read_and_explicit_stream():
    from pathlib import Path
    source=Path('scripts/gate8_controlled_token.cu').read_text()
    assert 'cudaMemcpyDeviceToHost' in source
    assert 'cudaStreamNonBlocking' in source
    assert 'cudaStreamSynchronize' in source
    assert 'g8_token_kernel' in source
