"""Actual new producer -> synthetic Raw -> domain -> independent Raw oracle.

CPU doubles create observations, not expected A/B. No real CUDA/collector claim.
"""
from contextlib import nullcontext
import copy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
from qualification_fixture import capture
from test_gate8_identity import UUID, sha, write_json


def source(tmp_path,monkeypatch):
    from scripts import gate9_bridge_target as target
    from exposedpath_v141.gate8_files import _entry, _json, write_input_receipt
    from exposedpath_v141.gate9_domain import declaration,N1
    def execute(Backend,clock,db,old_plan):
        db.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET nullStreamId=1')
        db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=1')
        class Native(Backend):
            def __init__(self,lib):
                super().__init__(lib)
                self.library=SimpleNamespace(**{n:SimpleNamespace() for n in ('ep_submit_on','ep_copy_on','ep_flags')})
                active.append(self)
            def _call(self,name,*args):
                if name=='ep_flags': args[1]._obj.value=1
                elif name=='ep_submit_on': self.submit(args[1])
                elif name=='ep_copy_on': self.copy()
                else: raise AssertionError(name)
        active=[]
        stream=SimpleNamespace(cuda_stream=123,device=SimpleNamespace(index=0),synchronize=lambda:active[0].wait())
        cuda=SimpleNamespace(Stream=lambda **_:stream,stream=lambda _:nullcontext(),current_stream=lambda _:stream,
            nvtx=SimpleNamespace(range_push=lambda label:active[0].push(label),range_pop=lambda:active[0].pop()))
        monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(__version__='2.6.0+cu124',version=SimpleNamespace(cuda='12.4'),
            __file__=str(tmp_path/'torch.py'),cuda=cuda))
        monkeypatch.setattr('exposedpath.platform_adapter.cuda_identity_native',lambda _:dict(gpu_uuid=UUID,pci_bus_id='0000:E1:00.0'))
        monkeypatch.setattr('exposedpath_v141.gate8_controlled_cli.NativeBackend',Native)
        monkeypatch.setattr(target.time,'perf_counter_ns',clock)
        old=_json(old_plan)
        write_json(tmp_path/'prompt.json',dict(request_tokens=[[0,1],[11,12]],warmup_count=0))
        manifest=dict(experiment_id='g9',wmpc_id='g9',run_id='bridge-test',run_role='ENGINEERING',data_role='Engineering',
            runner_git_commit='a'*40,runner_git_dirty=False,runner_source_sha256=sha(Path(target.__file__)),
            prompt_tokens_sha256=sha(tmp_path/'prompt.json'),domain_qualification=declaration(N1),
            gpu_index_physical=3,gpu_index_logical=0,gpu_uuid=UUID,gpu_pci_bus_id='0000:E1:00.0')
        write_json(tmp_path/'manifest.json',manifest)
        required=['scripts/gate9_bridge_target.py','scripts/gate9_bridge_token.cu','scripts/gate8_qualification_token.cu','exposedpath/gate9_stream_bridge.py']
        plan=dict(schema_version='gate9-bridge-plan/0.1.0',sources={n:sha(target.ROOT/n) for n in required},target_python=old['target_python'],
            library=dict(path=str(tmp_path/'synthetic.dll'),sha256=sha(tmp_path/'synthetic.dll')),
            preflight=dict(gpu_index_physical=3,gpu_uuid=UUID,pci_bus_id='0000:E1:00.0',cuda_device_order='PCI_BUS_ID',cuda_visible_devices='3'),
            manifest=_entry(tmp_path/'manifest.json',tmp_path),prompt=_entry(tmp_path/'prompt.json',tmp_path))
        plan['target_python']['site_root']=str(tmp_path)
        plan_path=write_json(tmp_path/'plan.json',plan)
        assert target.execute(plan_path,tmp_path/'producer')==0,_json(tmp_path/'producer/execution.json')
        return tmp_path/'producer/producer_receipt.json'
    _,_,sqlite,rep,export=capture(tmp_path,monkeypatch,executor=execute)
    producer=tmp_path/'producer'
    artifacts={k:producer/v for k,v in dict(pass_identity='pass_identity.json',host_ledger='host_boundaries.json',
        drain_ledger='drain_ledger.json',producer_receipt='producer_receipt.json',preflight='preflight.json',
        cuda_probe='cuda_probe.json',wmpc_manifest='manifest.json',prompt='prompt.json',runner_source='runner_source.py').items()}
    artifacts.update(raw=rep,sqlite=sqlite,export_report=export)
    receipt=write_input_receipt(tmp_path/'input.json',artifacts=artifacts,collector_version='2026.2.1.210',capture_session_id='CPU-SYNTHETIC')
    execution=write_json(tmp_path/'execution.json',dict(schema_version='exposedpath-n1-bridge-execution/0.1.0',
        input_receipt_sha256=sha(receipt),bridge_sha256=sha(producer/'bridge.json'),status='COMPLETE'))
    return receipt,execution,producer,sqlite


def test_actual_new_producer_and_independent_oracle_file_chain(tmp_path,monkeypatch):
    receipt,execution,producer,sqlite=source(tmp_path,monkeypatch)
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    from exposedpath_v141.gate9_bridge_oracle import check
    result=process_domain(receipt,execution,tmp_path/'result',bridge_path=producer/'bridge.json')
    value=load_domain(result,receipt,execution,bridge_path=producer/'bridge.json')
    before=sha(sqlite)
    oracle=check(sqlite,producer,value)
    assert oracle['status']=='MATCH_REVIEW_REQUIRED'
    assert [len(s['expected_members']) for s in oracle['sync_checks']]==[1,2,4,5,6,8]
    assert len(value['a_records'])==6 and len(value['b_records'])==6
    assert sha(sqlite)==before
    damaged=copy.deepcopy(value)
    damaged['physical_b_records'][-1]['wait_set_activity_ids'].pop()
    with pytest.raises(ValueError,match='PHYSICAL_MEMBERS'): check(sqlite,producer,damaged)
    damaged=copy.deepcopy(value)
    damaged['a_records'][0]['A_device_wait_ns']+=5
    damaged['a_records'][0]['A_sync_residual_ns']-=5
    with pytest.raises(ValueError,match='A_COMPONENTS'): check(sqlite,producer,damaged)
