"""Actual runner load entry and sealed producer files; CPU model/tensor doubles."""
import inspect
import json
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest
from exposedpath import runner
from exposedpath import gate8_load_tasks as tasks
from test_gate8_stage_producer import setup_case
from test_gate8_load_tasks import source, original_spawn
from test_runner_token_ready import _FakeModel, _FakeToken
from test_gate8_identity import sha


REAL_LOAD_MODEL=runner.load_model


def case(monkeypatch,tmp_path,pass_id='pass1',retry=False):
    args,state,labels,reads=setup_case(monkeypatch,tmp_path,pass_id)
    args['record_load_tasks']=True
    monkeypatch.setattr(runner,'load_model',REAL_LOAD_MODEL)
    monkeypatch.setattr(runner.torch.cuda,'is_available',lambda:True)
    monkeypatch.setattr(runner.torch.cuda,'get_device_name',lambda _: 'SYNTHETIC_DEVICE')
    module=SimpleNamespace(spawn_materialize=original_spawn)
    monkeypatch.setattr(tasks,'resolve_target_source',lambda:(module,source(),original_spawn))
    calls=[]
    def load(path,**kwargs):
        assert path=='synthetic-model'
        assert kwargs['device_map']=='cuda:0' and kwargs['dtype']==runner.torch.float16
        calls.append(dict(kwargs))
        with ThreadPoolExecutor(max_workers=1) as pool:
            value=module.spawn_materialize(pool,lambda:17).result()
        assert value==17
        if retry and len(calls)==1:
            raise RuntimeError('first attempt fails')
        model=_FakeModel(iter([_FakeToken([10],[]) for _ in range(4)]))
        model.config=SimpleNamespace(vocab_size=100)
        model.eval=lambda:model
        state['initialized']=True
        return model
    tokenizer=SimpleNamespace(eos_token_id=None,pad_token='p',eos_token='e')
    monkeypatch.setattr(runner,'AutoModelForCausalLM',SimpleNamespace(from_pretrained=load))
    monkeypatch.setattr(runner,'AutoTokenizer',SimpleNamespace(from_pretrained=lambda *a,**kw:tokenizer))
    return args,state,labels,module,calls


@pytest.mark.parametrize('pass_id',['pass0','pass1'])
def test_real_loader_producer_seals_task_identity_and_source(monkeypatch,tmp_path,pass_id):
    assert 'record_load_tasks' in inspect.signature(runner.run_gate8_requests).parameters
    args,state,labels,module,calls=case(monkeypatch,tmp_path,pass_id)
    receipt_path=runner.run_gate8_requests_to_files(**args)
    receipt=json.loads(receipt_path.read_text())
    assert receipt['schema_version']=='exposedpath-gate8-producer-receipt/0.4.0'
    assert receipt['files']['load_tasks.json']['sha256']==sha(receipt_path.parent/'load_tasks.json')
    assert hasattr(tasks,'load_producer_observations'),'sealed observation reader missing'
    value=tasks.load_producer_observations(receipt_path)
    stages=json.loads((receipt_path.parent/'stage_ledger.json').read_text())
    assert value['parent_stage_id']==stages['stages'][0]['payload']['stage_id']
    assert value['tasks'][0]['native_tid']!=threading.get_native_id()
    assert value['tasks'][0]['marker_payload']['identity']['pass_id']==pass_id
    assert value['tasks'][0]['marker_payload']['request_identity'] is None
    assert value['ownership_status']=='NOT_ASSESSED'
    assert state['syncs']==3 and len(calls)==1
    assert module.spawn_materialize is original_spawn
    task_labels=[label for label in labels if label.startswith(tasks.PREFIX)]
    assert len(task_labels)==(1 if pass_id=='pass1' else 0)
    with pytest.raises(FileExistsError):
        runner.run_gate8_requests_to_files(**args)
    assert len(calls)==1  # existing output rejected before loading


def test_loader_fallback_attempts_remain_separate(monkeypatch,tmp_path):
    assert 'record_load_tasks' in inspect.signature(runner.run_gate8_requests).parameters
    args,_,_,_,calls=case(monkeypatch,tmp_path,retry=True)
    receipt=runner.run_gate8_requests_to_files(**args)
    value=tasks.load_producer_observations(receipt)
    assert [a['branch'] for a in value['attempts']]==['trust_remote_code','fallback']
    assert [a['status'] for a in value['attempts']]==['FAILED','COMPLETE']
    assert len({t['attempt_id'] for t in value['tasks']})==2
    assert value['observation_status']=='INCOMPLETE'
    assert calls[0]['trust_remote_code'] is True and 'trust_remote_code' not in calls[1]


@pytest.mark.parametrize('damage',['hash','missing','run','parent','task_id','version','source'])
def test_file_reader_rejects_mixed_missing_or_forged_observations(monkeypatch,tmp_path,damage):
    assert 'record_load_tasks' in inspect.signature(runner.run_gate8_requests).parameters
    args,_,_,_,_=case(monkeypatch,tmp_path)
    receipt_path=runner.run_gate8_requests_to_files(**args)
    path=receipt_path.parent/'load_tasks.json'
    value=json.loads(path.read_text())
    if damage=='missing':
        path.unlink()
    else:
        if damage=='run': value['identity']['run_id']='other'
        elif damage=='parent': value['parent_stage_id']='c'*64
        elif damage=='task_id': value['tasks'][0]['task_id']='d'*64
        elif damage=='version': value['schema_version']='unknown/99'
        elif damage=='source':
            value['source_descriptor']['source_files'].pop()
            value['source_descriptor_sha256']=tasks._digest(value['source_descriptor'])
            for task in value['tasks']:
                task['marker_payload']['source_descriptor_sha256']=value['source_descriptor_sha256']
        else: value['issues'].append('changed')
        path.write_text(json.dumps(value),encoding='utf-8')
        if damage!='hash':
            receipt=json.loads(receipt_path.read_text())
            receipt['files']['load_tasks.json'].update(sha256=sha(path),size_bytes=path.stat().st_size)
            receipt_path.write_text(json.dumps(receipt),encoding='utf-8')
    with pytest.raises((ValueError,FileNotFoundError)):
        tasks.load_producer_observations(receipt_path)


@pytest.mark.parametrize('name',['host_boundaries.json','drain_ledger.json'])
def test_reader_rejects_rehashed_cross_run_sidecar(monkeypatch,tmp_path,name):
    args,_,_,_,_=case(monkeypatch,tmp_path)
    receipt_path=runner.run_gate8_requests_to_files(**args)
    path=receipt_path.parent/name
    value=json.loads(path.read_text())
    identity=value[0]['payload']['identity'] if name.startswith('host') else value['drains'][0]['identity']
    identity['run_id']='unrelated-run'
    path.write_text(json.dumps(value),encoding='utf-8')
    receipt=json.loads(receipt_path.read_text())
    receipt['files'][name].update(sha256=sha(path),size_bytes=path.stat().st_size)
    receipt_path.write_text(json.dumps(receipt),encoding='utf-8')
    with pytest.raises(ValueError):
        tasks.load_producer_observations(receipt_path)


def test_source_conflict_stops_before_model_and_no_success_receipt(monkeypatch,tmp_path):
    args,_,_,_,calls=case(monkeypatch,tmp_path)
    def conflict():
        raise ValueError('LOAD_SOURCE_HASH')
    monkeypatch.setattr(tasks,'resolve_target_source',conflict)
    with pytest.raises(ValueError,match='LOAD_TASK_SOURCE_NOT_OBSERVED'):
        runner.run_gate8_requests_to_files(**args)
    assert calls==[] and not args['output_dir'].exists()
