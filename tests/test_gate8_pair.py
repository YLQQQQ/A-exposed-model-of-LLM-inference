"""CPU producer wiring and hand-derived overhead; not a profiled workload."""
import importlib
import json
import pytest
from test_gate8_diagnostic_entry import case, api
from test_gate8_identity import write_json


def module():
    assert importlib.util.find_spec('scripts.gate8_pair'), 'missing paired orchestration'
    return importlib.import_module('scripts.gate8_pair')


def test_pass0_declaration_reaches_actual_producer(tmp_path,monkeypatch):
    args,state=case(monkeypatch,tmp_path)
    value=json.loads(args['manifest_path'].read_text())
    value['engineering_pair']={'schema_version':'gate8-engineering-pair/0.1','pair_id':'pair-test','pass_id':'pass0'}
    write_json(args['manifest_path'],value)
    monkeypatch.setattr(api(),'validate_pre_model_identity',lambda *a:[])
    result=api().run_diagnostic(**args)
    ledger=json.loads((result.parent/'producer/pass_identity.json').read_text())
    assert ledger['pass_id']=='pass0'
    assert ledger['requests'][1]['outcome']=='COMPLETE'


@pytest.mark.parametrize('damage',['version','pass','empty'])
def test_invalid_pair_never_loads_model(tmp_path,monkeypatch,damage):
    args,state=case(monkeypatch,tmp_path)
    value=json.loads(args['manifest_path'].read_text())
    pair={'schema_version':'gate8-engineering-pair/0.1','pair_id':'pair-test','pass_id':'pass0'}
    pair[{'version':'schema_version','pass':'pass_id','empty':'pair_id'}[damage]]='invalid' if damage!='empty' else ''
    value['engineering_pair']=pair
    write_json(args['manifest_path'],value)
    monkeypatch.setattr(api(),'validate_pre_model_identity',lambda *a:[])
    with pytest.raises(ValueError,match='PAIR'): api().run_diagnostic(**args)
    assert state['loads']==0


def test_host_timing_uses_observed_completion_not_marker_or_process_time():
    m=module()
    records=[dict(host_clock_id='PYTHON_PERF_COUNTER_NS',host_observed_ns=t,
        host_before_marker_ns=t+2,host_after_marker_ns=t+5,
        payload=dict(boundary_kind=k,token_index=i,completion_mechanism=c))
        for t,k,i,c in [(100,'request_start',None,'predrained_inputs_resident'),
            (160,'token_ready',0,'device_to_host_token_ids'),(200,'token_ready',1,'device_to_host_token_ids')]]
    assert m.host_durations(records)==dict(full_request=100,prefill=60,decode=40)
    assert m.overhead(dict(full_request=100,prefill=60,decode=40),
        dict(full_request=120,prefill=66,decode=54))['full_request']==dict(
            pass0_ns=100,pass1_ns=120,delta_ns=20,relative_delta=0.2)


def test_equal_boundary_is_not_missing_and_zero_denominator_is_unknown():
    m=module()
    r=[dict(host_clock_id='PYTHON_PERF_COUNTER_NS',host_observed_ns=t,
        host_before_marker_ns=t,host_after_marker_ns=t,
        payload=dict(boundary_kind='request_start' if i==0 else 'token_ready',
            token_index=None if i==0 else i-1,
            completion_mechanism='predrained_inputs_resident' if i==0 else 'device_to_host_token_ids'))
        for i,t in enumerate([-10,0,0])]
    assert m.host_durations(r)==dict(full_request=10,prefill=10,decode=0)
    assert m.overhead(dict(full_request=10,prefill=10,decode=0),dict(full_request=12,prefill=11,decode=1))['decode']==dict(
        pass0_ns=0,pass1_ns=1,delta_ns=1,relative_delta=None)


@pytest.mark.parametrize('damage',['missing','reverse','clock','marker','mechanism'])
def test_host_timing_rejects_missing_or_incompatible_evidence(damage):
    m=module()
    r=[dict(host_clock_id='PYTHON_PERF_COUNTER_NS',host_observed_ns=t,
        host_before_marker_ns=t+1,host_after_marker_ns=t+2,
        payload=dict(boundary_kind='request_start' if i==0 else 'token_ready',
            token_index=None if i==0 else i-1,
            completion_mechanism='predrained_inputs_resident' if i==0 else 'device_to_host_token_ids'))
        for i,t in enumerate([100,160,200])]
    if damage=='missing': r.pop()
    elif damage=='reverse': r[1]['host_observed_ns']=300
    elif damage=='clock': r[1]['host_clock_id']='UNKNOWN'
    elif damage=='marker': r[1]['host_before_marker_ns']=0
    else: r[1]['payload']['completion_mechanism']='submitted_only'
    with pytest.raises(ValueError): m.host_durations(r)


def test_unprofiled_argv_is_exact_same_target_entry_without_nsys(tmp_path):
    import sys,sysconfig
    from exposedpath_v141.gate8_target_python import probe
    from scripts.gate8_diagnostic_collect import profile_argv
    m=module(); p=tmp_path/'prepared';p.mkdir()
    write_json(p/'manifest.json',{'target_python':probe(sys._base_executable,sysconfig.get_path('purelib'))})
    full=profile_argv('nsys',sys._base_executable,p,tmp_path/'out')
    actual=m.unprofiled_argv(sys._base_executable,p,tmp_path/'out')
    assert full[-len(actual):]==actual
    assert 'model-run' in actual and 'nsys' not in actual


def pair_files(tmp_path,monkeypatch):
    """Real CPU producer; model/device/OS execution observations are explicit doubles."""
    import os,sys,sysconfig
    from types import SimpleNamespace
    from exposedpath import runner
    from exposedpath.gate8_engineering_contract import declaration
    from exposedpath_v141 import gate8_source_probe,gate8_target_python as target
    from test_gate8_identity import sha
    contract=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    runtime=dict(pid=os.getpid(),parent_pid=os.getppid(),snapshot=contract['actual']['snapshot'])
    monkeypatch.setattr(target,'current',lambda _:runtime)
    monkeypatch.setattr(api(),'verify_model_inventory',lambda *a,**kw:{})
    roots=[]
    for pass_id in ('pass0','pass1'):
        folder=tmp_path/pass_id; folder.mkdir()
        args,state=case(monkeypatch,folder)
        value=json.loads(args['manifest_path'].read_text())
        value.update(run_id='run-'+pass_id,attention_backend='sdpa',engineering_scope=declaration('sdpa'),
            gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='0000:01:00.0',
            target_python=contract,model_content_snapshot={'inventory_sha256':'0'*64},
            engineering_pair=dict(schema_version='gate8-engineering-pair/0.1',pair_id='pair-test',pass_id=pass_id))
        write_json(args['manifest_path'],value)
        write_json(args['preflight_path'],dict(physical_gpu_index=3,logical_gpu_index=0,
            gpu_uuid=value['gpu_uuid'],gpu_pci_bus_id=value['gpu_pci_bus_id']))
        monkeypatch.setattr(api(),'validate_pre_model_identity',lambda *a:[])
        monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
            gpu_uuid=value['gpu_uuid'],pci_bus_id=value['gpu_pci_bus_id'])))
        load=runner.load_model
        def configured(*a,_load=load,**kw):
            result=_load(*a,**kw); result[0].config=SimpleNamespace(_attn_implementation='sdpa',model_type='qwen2',use_cache=True)
            return result
        monkeypatch.setattr(runner,'load_model',configured)
        output=api().run_diagnostic(**args).parent.parent
        root=output/'diagnostic'
        (output/'diagnostic-entry').mkdir()
        write_json(output/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=0,pid=os.getpid()))
        # The producer is real; these OS/preflight receipts are synthetic evidence.
        write_json(output/'auxiliary_preflight.json',dict(run_id=value['run_id'],nonce=pass_id))
        claim=dict(target_pid=os.getpid(),nonce=pass_id,preflight_sha256=sha(output/'auxiliary_preflight.json'))
        write_json(output/'auxiliary_preflight.claim.json',claim)
        write_json(root/'isolated_preflight_target.json',claim)
        write_json(output/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=sha(output/'auxiliary_preflight.json'),
            target_claim_sha256=sha(output/'auxiliary_preflight.claim.json')))
        # Mark profile selection after this old-path CPU producer double, rebinding its manifest identity.
        m=json.loads((root/'manifest.json').read_text()); m['isolated_preflight_version']='exposedpath-isolated-preflight/0.1.0'
        write_json(root/'manifest.json',m)
        ledger=json.loads((root/'producer/pass_identity.json').read_text()); ledger['wmpc_manifest_sha256']=sha(root/'manifest.json')
        write_json(root/'producer/pass_identity.json',ledger)
        producer=json.loads((root/'producer/producer_receipt.json').read_text())
        producer['files']['pass_identity.json'].update(sha256=sha(root/'producer/pass_identity.json'),size_bytes=(root/'producer/pass_identity.json').stat().st_size)
        write_json(root/'producer/producer_receipt.json',producer)
        for name in ('engineering_execution.json','diagnostic_report.json'):
            r=json.loads((root/name).read_text()); r.update(manifest_sha256=sha(root/'manifest.json'),producer_receipt_sha256=sha(root/'producer/producer_receipt.json'))
            write_json(root/name,r)
        sealed=json.loads((output/'auxiliary_preflight.json').read_text())
        sealed['input_hashes']={'manifest.json':sha(root/'manifest.json'),'prompt.json':sha(root/'prompt.json')}
        write_json(output/'auxiliary_preflight.json',sealed)
        claim['preflight_sha256']=sha(output/'auxiliary_preflight.json')
        write_json(output/'auxiliary_preflight.claim.json',claim)
        write_json(root/'isolated_preflight_target.json',claim)
        write_json(output/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=sha(output/'auxiliary_preflight.json'),
            target_claim_sha256=sha(output/'auxiliary_preflight.claim.json')))
        write_json(output/('baseline_report.json' if pass_id=='pass0' else 'collection_report.json'),
            dict(status='BASELINE_COMPLETE_NOT_ACCEPTANCE') if pass_id=='pass0' else
            dict(collection={'status':'COMPLETE'},export_status='PASS',error='MODEL_A_SCOPE_BLOCKED'))
        roots.append(output)
    return roots


@pytest.mark.parametrize('damage',[None,'input','pair','host_identity','receipt','exit','cuda','missing'])
def test_real_producer_pair_summary_rejects_mixed_or_partial_inputs(tmp_path,monkeypatch,damage):
    roots=pair_files(tmp_path,monkeypatch); m=module()
    from test_gate8_identity import sha
    if damage:
        name={'input':'diagnostic/prompt.json','pair':'diagnostic/manifest.json',
            'host_identity':'diagnostic/producer/host_boundaries.json','receipt':'auxiliary_preflight.final.json',
            'exit':'diagnostic-entry/exit.json','cuda':'diagnostic/cuda_probe.json','missing':'diagnostic/producer/drain_ledger.json'}[damage]
        path=roots[1]/name
        if damage=='missing': path.unlink()
        else:
            v=json.loads(path.read_text())
            if damage=='host_identity': v[0]['payload']['identity']['run_id']='wrong'
            elif damage=='pair': v['engineering_pair']['pair_id']='wrong'
            elif damage=='exit': v['exit_code']=1
            elif damage=='cuda': v['gpu_uuid']='GPU-conflict'
            else: v['changed']=True
            write_json(path,v)
        with pytest.raises((ValueError,FileNotFoundError)): m.summarize(*roots)
    else:
        result=m.summarize(*roots)
        assert result['status']=='PAIR_OBSERVED_NOT_ACCEPTANCE' and result['gate8_verdict']=='NOT_RUN'
        assert all(r['pass0_ns']>0 and r['pass1_ns']>0 and r['delta_ns']==r['pass1_ns']-r['pass0_ns']
                   for r in result['overhead'].values())


def test_baseline_actual_probe_must_match_its_manifest_not_just_other_pass(tmp_path,monkeypatch):
    roots=pair_files(tmp_path,monkeypatch); m=module()
    for root in roots:
        p=root/'diagnostic/cuda_probe.json'; v=json.loads(p.read_text())
        v['gpu_uuid']='GPU-99999999-1234-1234-1234-123456789abc'; write_json(p,v)
    with pytest.raises(ValueError,match='DEVICE'): m.summarize(*roots)


def test_warmup_cannot_overlap_baseline_request_even_with_consistent_hashes(tmp_path,monkeypatch):
    from test_gate8_identity import sha
    roots=pair_files(tmp_path,monkeypatch); root=roots[0]/'diagnostic'
    p=root/'producer/stage_ledger.json'; stages=json.loads(p.read_text())
    host=json.loads((root/'producer/host_boundaries.json').read_text())
    stages['stages'][1]['host_end_ns']=host[0]['host_observed_ns']+1; write_json(p,stages)
    producer=json.loads((root/'producer/producer_receipt.json').read_text())
    producer['files']['stage_ledger.json'].update(sha256=sha(p),size_bytes=p.stat().st_size)
    write_json(root/'producer/producer_receipt.json',producer)
    for name in ('engineering_execution.json','diagnostic_report.json'):
        v=json.loads((root/name).read_text());v['producer_receipt_sha256']=sha(root/'producer/producer_receipt.json')
        write_json(root/name,v)
    with pytest.raises(ValueError,match='STAGE'): module().summarize(*roots)
