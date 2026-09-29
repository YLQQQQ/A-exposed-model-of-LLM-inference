"""Existing verified model entry -> real runner/files with CPU-only devices."""
import json
from contextlib import contextmanager
from types import SimpleNamespace

import pytest
from test_gate8_diagnostic_entry import case
from test_gate8_identity import sha, write_json
from test_n1_model_calls import fixture


def source(tmp_path, monkeypatch, variant='Vsync'):
    from exposedpath import gate8_diagnostic as entry, runner, n1_model
    from exposedpath.gate8_engineering_contract import declaration
    from exposedpath_v141.gate9_domain import declaration as domain, N1
    args, state = case(monkeypatch, tmp_path)
    model, _, _, _, events = fixture()
    model.config.use_cache = True
    model.dtype = runner.torch.float16
    def load(*a, **kw):
        state['loads'] += 1; state['initialized'] = True
        assert kw == {'allow_fallback': False}
        return model, SimpleNamespace(eos_token_id=99), 100, 'cuda:0'
    monkeypatch.setattr(runner, 'load_model', load)
    cuda = runner.torch.cuda
    monkeypatch.setattr(runner.torch,'tensor',lambda data,**kw:SimpleNamespace(shape=(len(data),len(data[0]))))
    active = [SimpleNamespace(cuda_stream=0, device=SimpleNamespace(index=0))]
    serial = iter([123, 456])
    def create(**kw):
        handle = next(serial)
        return SimpleNamespace(cuda_stream=handle, device=SimpleNamespace(index=0),
            synchronize=lambda: events.append(('sync', handle)))
    @contextmanager
    def context(s):
        previous = active[0]; active[0] = s
        try: yield
        finally: active[0] = previous
    monkeypatch.setattr(cuda, 'Stream', create)
    monkeypatch.setattr(cuda, 'stream', context)
    monkeypatch.setattr(cuda, 'current_stream', lambda _: active[0])
    monkeypatch.setattr(entry, 'validate_pre_model_identity', lambda *a: [])
    # External target/runtime/content probes are already independently tested;
    # only their boundaries are doubled here, not the runner or file producer.
    from exposedpath import gate8_isolated_preflight as isolated
    from exposedpath_v141 import gate8_target_python as target, gate8_source_probe
    from exposedpath import platform_adapter
    import os
    monkeypatch.setattr(isolated, 'consume', lambda **kw: {'target_pid': os.getpid()})
    monkeypatch.setattr(isolated, 'read', lambda _: {})
    monkeypatch.setattr(isolated, 'verify_snapshot', lambda *a: None)
    monkeypatch.setattr(target, 'current', lambda _: {'pid': os.getpid()})
    monkeypatch.setattr(entry, 'verify_model_inventory', lambda *a, **kw: {})
    monkeypatch.setattr(gate8_source_probe, 'TorchBackend', lambda: SimpleNamespace(cuda=cuda))
    monkeypatch.setattr(platform_adapter, 'cuda_identity_native', lambda _: dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc', pci_bus_id='0000:01:00.0'))
    value = json.loads(args['manifest_path'].read_text())
    value.update(engineering_scope=declaration('sdpa'), attention_backend='sdpa',
        target_python={}, isolated_preflight_version=isolated.VERSION,
        model_content_snapshot={'inventory_sha256': 'a'*64}, domain_qualification=domain(N1),
        n1_model=n1_model.declaration(variant),n1_model_execution=n1_model.execution_declaration(), study_mode='N1_INTERVENTION',
        n1_intervention=dict(sync_origin='n1_intervention', callsite_id=n1_model.CALLSITE,
                             intervention_variant_id=variant))
    write_json(args['manifest_path'], value)
    write_json(args['preflight_path'], dict(physical_gpu_index=3, logical_gpu_index=0,
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc', gpu_pci_bus_id='0000:01:00.0'))
    args.update(auxiliary_receipt=tmp_path/'aux.json', auxiliary_sha256='a'*64, launch_nonce='nonce')
    return entry, args, state, events


@pytest.mark.parametrize('variant,count', [('V0',0), ('Vmarker',1), ('Vsync',1)])
def test_verified_entry_real_producer_records_variant_and_actual_streams(tmp_path,monkeypatch,variant,count):
    entry,args,state,events = source(tmp_path,monkeypatch,variant)
    report = entry.run_diagnostic(**args)
    assert json.loads(report.read_text())['status'] == 'DIAGNOSTIC_COMPLETE'
    record = json.loads((report.parent/'n1_model_calls.json').read_text())
    measured = record['requests'][1]
    assert record['requests'][0]['native_handle'] == 123
    assert measured['native_handle'] == 456
    assert len(measured['interventions']) == count
    assert measured['observed_tokens'] == [[13],[14]]
    assert len(measured['model_calls']) == 2
    execution = json.loads((report.parent/'engineering_execution.json').read_text())
    assert execution['n1_model_calls_sha256'] == sha(report.parent/'n1_model_calls.json')
    assert state['loads'] == 1


@pytest.mark.parametrize('damage', ['mode','variant','target','source'])
def test_new_n1_branch_never_bypasses_existing_or_domain_identity(tmp_path,monkeypatch,damage):
    entry,args,state,events = source(tmp_path,monkeypatch)
    from exposedpath_v141 import gate8_target_python
    value = json.loads(args['manifest_path'].read_text())
    if damage == 'mode': value['study_mode']='G1_NATURAL'
    if damage == 'variant': value['n1_model']['layer_index']=7
    if damage == 'source': value['runner_source_sha256']='f'*64
    if damage == 'target':
        def reject(_): raise ValueError('TARGET_IDENTITY_CONFLICT')
        monkeypatch.setattr(gate8_target_python, 'current', reject)
    write_json(args['manifest_path'], value)
    with pytest.raises(ValueError): entry.run_diagnostic(**args)
    assert state['loads'] == 0


def test_verified_model_failure_restores_wrapper_and_persists_incomplete(tmp_path,monkeypatch):
    entry,args,state,events=source(tmp_path,monkeypatch)
    from exposedpath import runner
    load=runner.load_model; kept=[]
    def changed(*a,**kw):
        result=load(*a,**kw); model=result[0]; layer=model.model.layers[15]
        original=layer.forward
        def fail(value):
            if model.calls==3: raise RuntimeError('original measured decode exception')
            return original(value)
        layer.forward=fail; kept.append((layer,fail)); return result
    monkeypatch.setattr(runner,'load_model',changed)
    report=entry.run_diagnostic(**args)
    assert json.loads(report.read_text())['status']=='DIAGNOSTIC_INCOMPLETE'
    calls=json.loads((report.parent/'n1_model_calls.json').read_text())
    measured=calls['requests'][1]
    assert measured['status']=='FAILED' and not measured['interventions']
    assert measured['model_calls'][1]['error']=='RuntimeError:original measured decode exception'
    assert kept[0][0].forward is kept[0][1]
