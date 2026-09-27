"""Local source probe preparation and CPU execution doubles, never CUDA/Nsight."""
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


def module():
    assert importlib.util.find_spec('exposedpath_v141.gate8_source_probe'), 'source probe missing'
    from exposedpath_v141 import gate8_source_probe
    return gate8_source_probe


def test_profile_argv_is_explicit_and_not_the_minimal_profile(tmp_path):
    probe=module()
    args=probe.profile_argv('nsys.exe','python.exe',tmp_path/'plan.json',tmp_path/'new')
    assert args[:2]==['nsys.exe','profile']
    for flag in ('--trace=cuda,nvtx','--sample=process-tree','--cpuctxsw=process-tree',
                 '--sampling-frequency=200','--cudabacktrace=memory:0,sync:0',
                 '--cuda-memory-usage=false','--isr=false','--cuda-trace-scope=process-tree'):
        assert flag in args
    assert '--sample=none' not in args and not any('force-overwrite' in x for x in args)
    assert args[-9:]==['python.exe','-m','exposedpath_v141.gate8_source_probe','run',
                      '--plan',str(tmp_path/'plan.json'),'--output',str(tmp_path/'new'/'producer'),
                      '--execute-source-probe']
    assert not (tmp_path/'new').exists()  # builder never executes or creates evidence


def test_plan_prepare_is_static_and_pins_existing_sources(monkeypatch,tmp_path):
    probe=module()
    monkeypatch.setattr(probe,'check_git',lambda _:None)
    pre=tmp_path/'pre.json'
    pre.write_text(json.dumps(dict(gpu_index_physical=3,gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',
        pci_bus_id='00000000:E1:00.0',cuda_device_order='PCI_BUS_ID',cuda_visible_devices='3')))
    plan=probe.prepare(tmp_path/'plan',preflight_path=pre,expected_commit='a'*40,run_id='source-probe')
    value=json.loads(plan.read_text())
    assert value['profile']==probe.PROFILE and value['purpose']=='SOURCE_DIAGNOSTIC_ONLY'
    assert value['expected_tokens']==[[15,15],[15,15]]
    assert value['gate8_verdict']=='NOT_RUN' and value['measurement_validity']=='NOT_ASSESSED'
    assert value['inputs']['preflight']['sha256']==probe.digest(pre)
    with pytest.raises(FileExistsError):
        probe.prepare(tmp_path/'plan',preflight_path=pre,expected_commit='a'*40,run_id='source-probe')


def test_run_requires_explicit_execution_switch():
    probe=module()
    with pytest.raises(SystemExit):
        probe.main(['run','--plan','not-used.json','--output','not-used'])


def test_probe_task_branch_is_not_a_model_loading_attempt():
    from exposedpath.gate8_load_tasks import LoadTaskObserver
    from test_gate8_load_tasks import source, original_spawn
    from test_gate8_identity import producer_pass
    from exposedpath.gate8_identity import PASS_FIELDS
    from concurrent.futures import ThreadPoolExecutor
    ledger=producer_pass()
    descriptor=source(); descriptor['profile']='hf-source-probe/0.1.0'
    observer=LoadTaskObserver(identity={k:ledger[k] for k in PASS_FIELDS},pid=os.getpid(),
        parent_stage_id='a'*64,source=descriptor,push=lambda _:None,pop=lambda:None)
    core=SimpleNamespace(spawn_materialize=original_spawn)
    def work():
        with ThreadPoolExecutor(max_workers=1) as pool:
            return core.spawn_materialize(pool,lambda:15).result()
    assert observer.run_attempt(core,work,branch='source_probe')==15
    value=observer.seal()
    assert value['schema_version']=='exposedpath-load-task-ledger/0.2.0'
    assert value['tasks'][0]['marker_payload']['schema_version']=='exposedpath-load-task-marker/0.2.0'
    assert value['default_stream_mode']=='UNKNOWN'


def cpu_case(monkeypatch,tmp_path):
    probe=module()
    monkeypatch.setattr(probe,'check_git',lambda _:None)
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID'); monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    pre=tmp_path/'pre.json'
    pre.write_text(json.dumps(dict(gpu_index_physical=3,gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',
        pci_bus_id='00000000:E1:00.0',cuda_device_order='PCI_BUS_ID',cuda_visible_devices='3')))
    plan=probe.prepare(tmp_path/'plan',preflight_path=pre,expected_commit='a'*40,run_id='source-probe')
    from exposedpath import runner
    from test_gate8_load_tasks import source
    torch=runner.torch
    labels=[]; syncs=[]
    monkeypatch.setattr(torch.cuda,'is_initialized',lambda:False)
    monkeypatch.setattr(torch.cuda,'current_device',lambda:0)
    monkeypatch.setattr(torch.cuda,'synchronize',lambda:syncs.append('drain'))
    monkeypatch.setattr(torch.cuda.nvtx,'range_push',labels.append)
    monkeypatch.setattr(torch.cuda.nvtx,'range_pop',lambda:None)
    monkeypatch.setattr(torch.cuda.nvtx,'mark',labels.append)
    def spawn(pool,tensor,**kwargs):
        return pool.submit(lambda:tensor.clone())
    core=SimpleNamespace(spawn_materialize=spawn)
    class CPU:
        cuda=torch.cuda
        def identity(self): return json.loads(pre.read_text())
        def source(self): return core,source(),spawn
        def inputs(self): return torch.tensor([[0]]),torch.tensor([[1]])
        def vectors(self): return [torch.arange(16,dtype=torch.float16) for _ in range(2)]
        def model(self,values): return probe.VectorModel(*values)
    return probe,plan,CPU,labels,syncs


def test_cpu_actual_file_entry_records_tasks_requests_and_unknown(monkeypatch,tmp_path):
    probe,plan,CPU,labels,syncs=cpu_case(monkeypatch,tmp_path)
    receipt=probe.execute(plan,tmp_path/'result',backend_factory=CPU)
    value=probe.read_result(receipt)
    assert value['tokens']==[[15,15],[15,15]]
    assert value['status']=='COMPLETE' and value['measurement_validity']=='NOT_ASSESSED'
    assert value['source_binding']=='UNKNOWN'
    from exposedpath.gate8_load_tasks import load_producer_observations
    tasks=load_producer_observations(receipt.parent/'producer_receipt.json')
    assert len(tasks['tasks'])==2 and tasks['attempts'][0]['branch']=='source_probe'
    assert len(syncs)==2  # only existing request-start drains
    assert sum(x.startswith('EXPOSEDPATH_BOUNDARY_V1:') for x in labels)==6
    assert sum(x.startswith('EXPOSEDPATH_LOAD_TASK_V1:') for x in labels)==2
    with pytest.raises(FileExistsError): probe.execute(plan,tmp_path/'result',backend_factory=CPU)


@pytest.mark.parametrize('damage',['mask','source','plan','input'])
def test_prework_identity_rejects_conflict(monkeypatch,tmp_path,damage):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    data=json.loads(plan.read_text())
    if damage=='mask': monkeypatch.setenv('CUDA_VISIBLE_DEVICES','0')
    elif damage=='source': data['source_sha256']['exposedpath/runner.py']='f'*64
    elif damage=='plan': data['expected_tokens']=[[0,0],[0,0]]
    else: (plan.parent/'preflight.json').write_text('{}')
    plan.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        probe.execute(plan,tmp_path/'result',backend_factory=lambda:pytest.fail('backend before validation'))
    assert not (tmp_path/'result').exists()


def test_failed_job_leaves_only_partial_files_and_no_retry(monkeypatch,tmp_path):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    class Broken(CPU):
        def vectors(self): raise RuntimeError('synthetic failure')
    with pytest.raises(RuntimeError): probe.execute(plan,tmp_path/'result',backend_factory=Broken)
    assert not (tmp_path/'result').exists()
    partial=list(tmp_path.glob('.result-partial-*'))
    assert len(partial)==1
    assert json.loads((partial[0]/'failure.json').read_text())['status']=='FAILED'


@pytest.mark.parametrize('damage',['missing','hash','run','qualification'])
def test_result_reader_rejects_artifact_and_claim_tampering(monkeypatch,tmp_path,damage):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    receipt=probe.execute(plan,tmp_path/'result',backend_factory=CPU)
    data=json.loads(receipt.read_text())
    if damage=='missing': (receipt.parent/'load_tasks.json').unlink()
    elif damage=='hash': (receipt.parent/'host_boundaries.json').write_text('[]')
    elif damage=='run': data['run_id']='other'
    else: data['measurement_validity']='VALID'
    receipt.write_text(json.dumps(data))
    with pytest.raises((ValueError,FileNotFoundError)): probe.read_result(receipt)


@pytest.mark.parametrize('name,field,replacement',[
    ('wmpc_manifest.json','gpu_uuid','GPU-aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'),
    ('prompt.json','construction','other'),
    ('cuda_probe.json','pci_bus_id','00000000:A1:00.0'),
])
def test_rehashed_provenance_conflict_is_not_accepted(monkeypatch,tmp_path,name,field,replacement):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    receipt=probe.execute(plan,tmp_path/'result',backend_factory=CPU)
    path=receipt.parent/name
    assert path.exists(), 'actual device probe must be persisted'
    data=json.loads(path.read_text()); data[field]=replacement; path.write_text(json.dumps(data))
    value=json.loads(receipt.read_text()); value['files'][name]=probe._entry(path,path.parent)
    # Update the ledger/producer hashes too: semantic checks, not stale hashes, must reject.
    if name in ('wmpc_manifest.json','prompt.json'):
        ledger_path=path.parent/'pass_identity.json'
        ledger=json.loads(ledger_path.read_text())
        ledger['wmpc_manifest_sha256' if name.startswith('wmpc') else 'prompt_sha256']=probe.digest(path)
        ledger_path.write_text(json.dumps(ledger))
        prod_path=path.parent/'producer_receipt.json'
        prod=json.loads(prod_path.read_text()); prod['files']['pass_identity.json']=probe._entry(ledger_path,path.parent)
        prod_path.write_text(json.dumps(prod))
        for item in (ledger_path,prod_path): value['files'][item.name]=probe._entry(item,path.parent)
    receipt.write_text(json.dumps(value))
    with pytest.raises(ValueError): probe.read_result(receipt)


def test_token_claim_has_request_boundary_backing(monkeypatch,tmp_path):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    receipt=probe.execute(plan,tmp_path/'result',backend_factory=CPU)
    path=receipt.parent/'request_results.json'
    assert path.exists(), 'tokens need per-request host-read records'
    rows=json.loads(path.read_text())
    assert [r['identity']['request_id'] for r in rows]==['r0','r1']
    rows[0]['token_ready_boundaries'][0]['completed_ns']+=1
    path.write_text(json.dumps(rows))
    value=json.loads(receipt.read_text()); value['files'][path.name]=probe._entry(path,path.parent)
    receipt.write_text(json.dumps(value))
    with pytest.raises(ValueError): probe.read_result(receipt)


def test_failed_publication_never_has_an_accepted_partial_receipt(monkeypatch,tmp_path):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    rename=Path.rename
    def fail_publication(path,target):
        if path.name.startswith('.result-partial-'): raise PermissionError('synthetic publish failure')
        return rename(path,target)
    monkeypatch.setattr(Path,'rename',fail_publication)
    with pytest.raises(PermissionError): probe.execute(plan,tmp_path/'result',backend_factory=CPU)
    partial=next(tmp_path.glob('.result-partial-*'))
    with pytest.raises(ValueError): probe.read_result(partial/'source_receipt.json')


@pytest.mark.parametrize('field',['profile','schema_version'])
def test_source_task_family_cannot_be_relabelled_as_loader(monkeypatch,tmp_path,field):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    receipt=probe.execute(plan,tmp_path/'result',backend_factory=CPU)
    from exposedpath.gate8_load_tasks import validate_load_tasks, _digest
    tasks=json.loads((receipt.parent/'load_tasks.json').read_text())
    if field=='profile':
        tasks['source_descriptor']['profile']='hf-load-tasks/0.1.0'
        tasks['source_descriptor_sha256']=_digest(tasks['source_descriptor'])
    else: tasks['schema_version']='exposedpath-load-task-ledger/0.1.0'
    with pytest.raises(ValueError): validate_load_tasks(tasks,
        json.loads((receipt.parent/'pass_identity.json').read_text()),
        json.loads((receipt.parent/'stage_ledger.json').read_text()))


def test_second_request_failure_preserves_first_and_partial_boundaries(monkeypatch,tmp_path):
    probe,plan,CPU,_,_=cpu_case(monkeypatch,tmp_path)
    class Broken(CPU):
        def model(self,values):
            original=super().model(values); calls=[]
            def model(**kwargs):
                calls.append(1)
                if len(calls)==3: raise RuntimeError('second request')
                return original(**kwargs)
            return model
    with pytest.raises(RuntimeError): probe.execute(plan,tmp_path/'result',backend_factory=Broken)
    partial=next(tmp_path.glob('.result-partial-*'))
    host_path=partial/'host_boundaries.json'
    assert host_path.exists(), 'observed boundaries lost on failure'
    assert len(json.loads(host_path.read_text()))==4
    assert len(json.loads((partial/'drain_ledger.json').read_text())['drains'])==2
    ledger=json.loads((partial/'pass_identity.json').read_text())
    assert [x['outcome'] for x in ledger['requests']]==['COMPLETE','FAILED']
    assert len(ledger['requests'][1]['observed_boundary_ids'])==1
