"""Real runner/file entry, CPU tensor/model/device doubles; not CUDA evidence."""
import inspect
import json
import os
from pathlib import Path
from itertools import count
from types import SimpleNamespace

import pytest
from exposedpath import runner
from test_gate8_identity import producer_pass, sha, write_json
from test_runner_token_ready import _FakeModel, _FakeInput, _FakeToken, _patch_cpu_torch


def setup_case(monkeypatch, tmp_path, pass_id='pass1', failed=False):
    _patch_cpu_torch(monkeypatch)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '3')
    monkeypatch.setenv('CUDA_DEVICE_ORDER', 'PCI_BUS_ID')
    state = {'initialized':False, 'syncs':0, 'loads':0}
    labels, reads = [], []
    monkeypatch.setattr(runner.torch.cuda, 'is_initialized', lambda:state['initialized'])
    monkeypatch.setattr(runner.torch.cuda, 'current_device', lambda:0)
    stream = SimpleNamespace(cuda_stream=0, device=SimpleNamespace(index=0))
    def read_stream(device):
        assert state['initialized'], 'observer must not initialize CUDA before setup'
        assert device == 0
        reads.append('stream')
        return stream
    monkeypatch.setattr(runner.torch.cuda, 'current_stream', read_stream)
    monkeypatch.setattr(runner.torch.cuda, 'default_stream', read_stream)
    monkeypatch.setattr(runner.torch.cuda, 'set_stream', lambda *a:pytest.fail('stream changed'))
    monkeypatch.setattr(runner.torch.cuda.nvtx, 'range_push', labels.append)
    monkeypatch.setattr(runner.torch.cuda.nvtx, 'mark', labels.append)
    def sync():
        state['syncs'] += 1
    monkeypatch.setattr(runner.torch.cuda, 'synchronize', sync)
    def load(path, gpu):
        assert path == 'synthetic-model' and gpu == 3
        state['loads'] += 1
        if failed:
            raise RuntimeError('synthetic load failure')
        state['initialized'] = True
        return (_FakeModel(iter([_FakeToken([10], []) for _ in range(4)])),
                SimpleNamespace(eos_token_id=None), 100, 'cuda:0')
    monkeypatch.setattr(runner, 'load_model', load)
    monkeypatch.setattr(runner.torch, 'tensor', lambda data,**kw:_FakeInput())
    prompt = write_json(tmp_path/'prompt.json', {'schema_version':'exposedpath-prompt-tokens/1',
        'tokenizer_id':'synthetic-tokenizer', 'fixed_input_tokens':4,
        'samples':[{'input_ids':[1,2,3,4], 'attention_mask':[1,1,1,1]}]})
    ledger=producer_pass()
    fields={k:ledger[k] for k in ('experiment_id','wmpc_id','run_id','attempt_id',
        'wmpc_manifest_sha256','prompt_sha256','runner_source_sha256','runner_git_commit','runner_git_dirty')}
    fields.update(pid=os.getpid(),pass_id=pass_id,prompt_sha256=sha(prompt),
                  runner_source_sha256=sha(Path(runner.__file__)))
    manifest=write_json(tmp_path/'manifest.json',dict(
        **{k:fields[k] for k in ('experiment_id','wmpc_id','run_id','runner_git_commit','runner_git_dirty','runner_source_sha256')},
        run_role='ENGINEERING',data_role='Engineering',study_mode='G1_NATURAL',n1_intervention=None,
        model_id='synthetic-model',batch_size=1,fixed_output_tokens=2,prompt_tokens_sha256=sha(prompt),
        execution_mode='eager',fixed_input_tokens=4,warmup_count=1,repeat_count=1,
        gpu_index_physical=3,gpu_index_logical=0))
    fields['wmpc_manifest_sha256']=sha(manifest)
    args=dict(output_dir=tmp_path/'producer', record_stages=True, record_drains=True,
        model_setup=dict(model_path='synthetic-model',prompt_path=prompt,physical_gpu_index=3,
                         batch_size=1,manifest_path=manifest),
        output_len=2,device='cuda:0',pass_fields=fields,
        request_plan=[dict(request_id='w0',repeat_id='warmup-0',request_role='warmup'),
                      dict(request_id='r0',repeat_id='0',request_role='measured')],
        clock_ns=lambda:next(ticks))
    ticks=count(100)
    return args,state,labels,reads


@pytest.mark.parametrize('pass_id', ['pass0','pass1'])
def test_actual_setup_warmup_and_request_have_sealed_non_completion_stages(monkeypatch,tmp_path,pass_id):
    assert 'model_setup' in inspect.signature(runner.run_gate8_requests).parameters
    args,state,labels,_=setup_case(monkeypatch,tmp_path,pass_id)
    path=runner.run_gate8_requests_to_files(**args)
    receipt=json.loads(path.read_text())
    assert receipt['schema_version']=='exposedpath-gate8-producer-receipt/0.3.0'
    assert receipt['status']=='COMPLETE'
    ref=receipt['files']['stage_ledger.json']
    assert ref['sha256']==sha(path.parent/ref['filename'])
    stage=json.loads((path.parent/ref['filename']).read_text())
    assert [s['payload']['stage_role'] for s in stage['stages']]==['setup','warmup','measured']
    assert stage['stages'][0]['payload']['request_identity'] is None
    assert stage['stages'][1]['payload']['request_identity']['request_id']=='w0'
    assert stage['stages'][0]['before']['status']=='UNKNOWN'
    assert stage['stages'][0]['before']['reason']=='CUDA_NOT_INITIALIZED'
    after=stage['stages'][0]['after']
    assert after['current_native_handle']==after['default_native_handle']==0
    assert after['default_stream_mode']=='UNKNOWN'
    assert after['lifetime_status']=='UNKNOWN'
    assert all(s['payload']['scope_semantics']=='HOST_CALL_ONLY' for s in stage['stages'])
    assert state['syncs']==3  # existing warmup before/after + measured predrain
    assert state['loads']==1
    markers=[s for s in labels if s.startswith('EXPOSEDPATH_STAGE_V1:')]
    assert len(markers)==(3 if pass_id=='pass1' else 0)
    ledger=json.loads((path.parent/'pass_identity.json').read_text())
    assert ledger['requests'][0]['observed_boundary_ids']==[]
    assert len(ledger['requests'][1]['observed_boundary_ids'])==3


def test_failed_setup_is_preserved_and_never_runs_warmup(monkeypatch,tmp_path):
    assert 'model_setup' in inspect.signature(runner.run_gate8_requests).parameters
    args,state,_,_=setup_case(monkeypatch,tmp_path,failed=True)
    path=runner.run_gate8_requests_to_files(**args)
    assert json.loads(path.read_text())['status']=='INCOMPLETE'
    stage=json.loads((path.parent/'stage_ledger.json').read_text())['stages']
    assert len(stage)==1 and stage[0]['status']=='FAILED'
    assert stage[0]['error']=='RuntimeError'
    assert state['syncs']==0
    ledger=json.loads((path.parent/'pass_identity.json').read_text())
    assert all(r['outcome']=='FAILED' and not r['observed_boundary_ids'] for r in ledger['requests'])


@pytest.mark.parametrize('damage',['prompt','mask','role','output_exists','model','source','manifest_hash'])
def test_bad_pre_setup_identity_never_loads_model(monkeypatch,tmp_path,damage):
    assert 'model_setup' in inspect.signature(runner.run_gate8_requests).parameters
    args,state,_,_=setup_case(monkeypatch,tmp_path)
    if damage=='prompt': args['pass_fields']['prompt_sha256']='f'*64
    elif damage=='mask': monkeypatch.setenv('CUDA_VISIBLE_DEVICES','2')
    elif damage=='role': args['pass_fields']['data_role']='Formal'
    elif damage=='model': args['model_setup']['model_path']='different-model'
    elif damage=='source': args['pass_fields']['runner_source_sha256']='e'*64
    elif damage=='manifest_hash': args['pass_fields']['wmpc_manifest_sha256']='e'*64
    else: args['output_dir'].mkdir()
    with pytest.raises((ValueError,FileExistsError)):
        runner.run_gate8_requests_to_files(**args)
    assert state['loads']==state['syncs']==0


def test_stream_probe_failure_preserves_unknown_without_fallback(monkeypatch,tmp_path):
    assert 'record_stages' in inspect.signature(runner.run_gate8_requests).parameters
    args,_,_,_=setup_case(monkeypatch,tmp_path)
    monkeypatch.setattr(runner.torch.cuda,'current_stream',lambda _:(_ for _ in ()).throw(RuntimeError('probe')))
    path=runner.run_gate8_requests_to_files(**args)
    stage=json.loads((path.parent/'stage_ledger.json').read_text())['stages']
    assert stage[0]['after']['status']=='UNKNOWN'
    assert stage[0]['after']['reason']=='PROBE_FAILED:RuntimeError'
    assert stage[0]['after']['current_native_handle'] is None


@pytest.mark.parametrize('damage',['truncated','failed_stage_complete_request'])
def test_failed_request_cannot_hide_missing_or_contradictory_stages(monkeypatch,tmp_path,damage):
    from exposedpath.gate8_stages import validate_stage_ledger
    args,_,_,_=setup_case(monkeypatch,tmp_path)
    path=runner.run_gate8_requests_to_files(**args)
    stages=json.loads((path.parent/'stage_ledger.json').read_text())
    ledger=json.loads((path.parent/'pass_identity.json').read_text())
    if damage=='truncated':
        ledger['requests'][1].update(outcome='FAILED',reasons=['RUNTIME_ERROR:ValueError'])
        stages['stages']=stages['stages'][:1]
    else:
        stages['stages'][-1].update(status='FAILED',error='ValueError')
        ledger['requests'][0].update(outcome='EXCLUDED',reasons=['SYNTHETIC'])
    with pytest.raises(ValueError,match='STAGE_'):
        validate_stage_ledger(stages,ledger)


@pytest.mark.parametrize('field,value', [('execution_mode','compile'),('fixed_input_tokens',999),
                                       ('warmup_count',99),('repeat_count',99),('batch_size',True)])
def test_setup_rejects_hashed_but_different_execution_contract(monkeypatch,tmp_path,field,value):
    args,state,_,_=setup_case(monkeypatch,tmp_path)
    path=args['model_setup']['manifest_path']
    manifest=json.loads(path.read_text()); manifest[field]=value
    write_json(path,manifest)
    args['pass_fields']['wmpc_manifest_sha256']=sha(path)
    with pytest.raises(ValueError,match='STAGE_SETUP_MANIFEST_IDENTITY'):
        runner.run_gate8_requests_to_files(**args)
    assert state['loads']==0
