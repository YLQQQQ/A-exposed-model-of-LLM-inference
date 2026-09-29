"""CPU sequence check: no CUDA and no import of torch in this test."""
import importlib
import pytest
import json
import sys
from pathlib import Path
from contextlib import nullcontext
from types import SimpleNamespace


def api():
    assert importlib.util.find_spec('scripts.gate9_bridge_target'), 'controlled explicit bridge entry missing'
    return importlib.import_module('scripts.gate9_bridge_target')


def test_controlled_sequence_and_host_read_before_completion():
    calls=[]
    class Backend:
        def submit(self,v): self.token=v; calls.append(('submit',v))
        def copy(self): calls.append(('copy',None))
        def wait(self,kind): calls.append((kind,None))
        def read(self): calls.append(('read',self.token)); return self.token
    observed=api().token_pair(Backend(),[11,12],lambda index:calls.append(('boundary',index)))
    assert observed==[11,12]
    assert calls==[('submit',11),('internal_wait',None),('copy',None),('wait',None),('read',11),('boundary',0),
                   ('submit',12),('copy',None),('wait',None),('read',12),('boundary',1)]


def test_bad_token_stops_before_ready_not_silent_success():
    calls=[]
    class Backend:
        def submit(self,v): pass
        def copy(self): pass
        def wait(self,kind): pass
        def read(self): return 99
    with pytest.raises(ValueError,match='TOKEN'):
        api().token_pair(Backend(),[11,12],calls.append)
    assert calls==[]


def test_import_does_not_initialize_cuda():
    # No target execution without explicit CLI authorization.
    with pytest.raises(SystemExit): api().main([])


@pytest.mark.parametrize('damage',[None,'missing_sources','wrong_profile'])
def test_actual_target_entry_writes_bound_producer_files_with_cpu_backend(tmp_path,monkeypatch,damage):
    from exposedpath_v141.gate8_files import _entry, _write, _json
    from exposedpath_v141.gate8_adapter import digest
    from exposedpath_v141.gate8_files import _identities
    module=api(); labels=[]
    device={'gpu_uuid':'12345678-1234-1234-1234-123456789abc','pci_bus_id':'0000:e1:00.0'}
    class Native:
        def __init__(self,lib):
            self.library=SimpleNamespace(**{n:SimpleNamespace() for n in ('ep_submit_on','ep_copy_on','ep_flags')})
        def _call(self,name,*args):
            if name=='ep_flags': args[1]._obj.value=1
            if name=='ep_submit_on': self.token=args[1]
        def read(self): return self.token
        def identity(self): return device
        def prepare(self): pass
        def close(self): pass
        def push(self,label): labels.append(label)
        def pop(self): pass
        def mark(self,label): labels.append(label)
    stream=SimpleNamespace(cuda_stream=123,device=SimpleNamespace(index=0),synchronize=lambda:None)
    cuda=SimpleNamespace(Stream=lambda **k:stream,stream=lambda s:nullcontext(),current_stream=lambda d:stream,
        nvtx=SimpleNamespace(range_push=labels.append,range_pop=lambda:None))
    monkeypatch.setitem(sys.modules,'torch',SimpleNamespace(__version__='2.6.0+cu124',version=SimpleNamespace(cuda='12.4'),
        __file__=str(tmp_path/'torch.py'),cuda=cuda))
    monkeypatch.setattr('exposedpath_v141.gate8_target_python.current',lambda _: {'pid':123})
    monkeypatch.setattr('exposedpath.platform_adapter.cuda_identity_native',lambda _:device)
    monkeypatch.setattr('exposedpath_v141.gate8_controlled_cli.NativeBackend',Native)
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID'); monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    library=tmp_path/'fake.dll'; library.write_bytes(b'CPU substitute')
    _write(tmp_path/'prompt.json',{'request_tokens':[[0,1],[11,12]],'warmup_count':0})
    manifest=dict(experiment_id='g9',wmpc_id='g9',run_id='test',run_role='ENGINEERING',data_role='Engineering',
        runner_git_commit='a'*40,runner_git_dirty=False,runner_source_sha256=digest(Path(module.__file__)),
        prompt_tokens_sha256=digest(tmp_path/'prompt.json'),
        domain_qualification={'contract':'G9-DOMAIN-QUALIFICATION/0.1.0','profile':'N1_EXPLICIT_STREAM_AB/0.1.0','declaration_role':'PRE_EXECUTION'})
    if damage=='wrong_profile': manifest['domain_qualification']['profile']='G1_NATURAL_PROJECTED_A/0.1.0'
    _write(tmp_path/'manifest.json',manifest)
    required=['scripts/gate9_bridge_target.py','scripts/gate9_bridge_token.cu','scripts/gate8_qualification_token.cu','exposedpath/gate9_stream_bridge.py']
    plan=dict(schema_version='gate9-bridge-plan/0.1.0',sources={n:digest(module.ROOT/n) for n in required},target_python={'site_root':str(tmp_path)},
        library={'path':str(library),'sha256':digest(library)},preflight=dict(device,gpu_index_physical=3),
        manifest=_entry(tmp_path/'manifest.json',tmp_path),prompt=_entry(tmp_path/'prompt.json',tmp_path))
    if damage=='missing_sources':
        plan['sources']={}
    _write(tmp_path/'plan.json',plan)
    if damage:
        assert module.execute(tmp_path/'plan.json',tmp_path/'out')==1
        assert _json(tmp_path/'out/execution.json')['error']
        assert labels==[]
        return
    assert module.execute(tmp_path/'plan.json',tmp_path/'out')==0
    assert _json(tmp_path/'out/execution.json')['observed_tokens']==[[0,1],[11,12]]
    from exposedpath.gate8_identity import validate_pass_identity
    validate_pass_identity(_json(tmp_path/'out/pass_identity.json'))  # Raw hash is finalized by Canonical, not producer.
    syncs=[json.loads(x.split(':',1)[1]) for x in labels if x.startswith('EXPOSEDPATH_JSON_V1:')]
    assert len(syncs)==6
    assert all(s['sync_origin']=='n1_intervention' and s.get('intervention_variant_id')=='bridge_qualification'
        and type(s.get('intervention_ordinal')) is int for s in syncs)
    assert len(_json(tmp_path/'out/host_boundaries.json'))==6
