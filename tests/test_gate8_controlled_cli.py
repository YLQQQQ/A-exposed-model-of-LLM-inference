"""No device calls: CLI identity gates are checked before loading the backend."""
import importlib
import json
from pathlib import Path

import pytest

from test_gate8_identity import UUID,write_json


def prepare(tmp_path,monkeypatch):
    mod=importlib.import_module('exposedpath_v141.gate8_controlled_cli')
    monkeypatch.setattr(mod.platform_adapter,'git',lambda args: 'd'*40 if args[-1]=='HEAD' else '')
    pre=write_json(tmp_path/'physical.json',dict(gpu_index_physical=3,gpu_uuid='GPU-'+UUID,
        pci_bus_id='00000000:E1:00.0',cuda_device_order='PCI_BUS_ID',cuda_visible_devices='3'))
    library=tmp_path/'controlled.dll'
    library.write_bytes(b'CPU_TEST_ONLY_NOT_A_REAL_LIBRARY')
    plan=mod.prepare_controlled(tmp_path/'inputs',preflight_path=pre,library_path=library,
                                expected_commit='d'*40,run_id='controlled-test')
    return mod,plan,library


@pytest.mark.parametrize('fault',['mask','git','library','source','identity'])
def test_refuse_before_backend_load(tmp_path,monkeypatch,fault):
    mod,plan,library=prepare(tmp_path,monkeypatch)
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    if fault=='mask': monkeypatch.setenv('CUDA_VISIBLE_DEVICES','0')
    elif fault=='git': monkeypatch.setattr(mod.platform_adapter,'git',lambda args:'e'*40)
    elif fault=='library': library.write_bytes(b'changed')
    elif fault=='source': (plan.parent/'runner_source.py').write_text('changed')
    else:
        doc=json.loads(plan.read_text()); doc['identity']['runner_git_commit']='e'*40; write_json(plan,doc)
    def forbidden(*args,**kwargs): raise AssertionError('backend must not load')
    with pytest.raises(ValueError):
        mod.execute_controlled(plan,tmp_path/'run',backend_factory=forbidden)
    assert not (tmp_path/'run'/'producer').exists()


def test_prepare_has_explicit_versions_hashes_and_no_qualification(tmp_path,monkeypatch):
    mod,plan,_=prepare(tmp_path,monkeypatch)
    doc=json.loads(plan.read_text())
    assert doc['construction']=='CONTROLLED-D2H-REQUEST/0.1.0'
    assert doc['expected_commit']=='d'*40
    assert doc['gate8_verdict']=='NOT_RUN'
    assert {'wmpc_manifest','prompt','preflight','runner_source'} <= set(doc['inputs'])
    with pytest.raises(FileExistsError):
        mod.prepare_controlled(plan.parent,preflight_path=plan,library_path=plan,
                                expected_commit='d'*40,run_id='x')


@pytest.mark.parametrize('cleanup_fails',[False,True])
def test_wrapper_records_cleanup_not_just_producer_success(tmp_path,monkeypatch,cleanup_fails):
    mod,plan,_=prepare(tmp_path,monkeypatch)
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID'); monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    from test_gate8_controlled_producer import Backend
    class FakeNative(Backend):
        def identity(self): return dict(gpu_uuid=UUID,pci_bus_id='0000:E1:00.0')
        def close(self):
            if cleanup_fails: raise RuntimeError('close failure')
    path=mod.execute_controlled(plan,tmp_path/'run',backend_factory=lambda _:FakeNative())
    report=json.loads(path.read_text())
    assert report['status']==('BLOCKED' if cleanup_fails else 'COMPLETE')
    assert report['process_exit_code']==(1 if cleanup_fails else 0)
    assert report['gate8_verdict']=='NOT_RUN'
