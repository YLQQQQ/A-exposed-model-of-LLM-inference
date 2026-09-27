"""Diagnostic entry through real producer/files; CPU doubles, not CUDA qualification."""
import importlib
import importlib.util
import json
import inspect
import csv
from pathlib import Path

import pytest
from test_gate8_stage_producer import setup_case
from test_gate8_identity import sha, write_json


def api():
    assert importlib.util.find_spec('exposedpath.gate8_diagnostic'), 'Missing bounded diagnostic entry'
    return importlib.import_module('exposedpath.gate8_diagnostic')


def case(monkeypatch, tmp_path, failed=False):
    args, state, labels, _ = setup_case(monkeypatch, tmp_path, failed=failed)
    prompt = args['model_setup']['prompt_path']
    value = json.loads(prompt.read_text())
    value['fixed_input_tokens'] = 32
    value['samples'][0] = dict(input_ids=[1]*32, attention_mask=[1]*32)
    write_json(prompt, value)
    manifest = args['model_setup']['manifest_path']
    value = json.loads(manifest.read_text())
    value.update(fixed_input_tokens=32, prompt_tokens_sha256=sha(prompt),
                 sampling_config={'do_sample':False}, dtype_and_quantization='fp16')
    write_json(manifest, value)
    return dict(manifest_path=manifest, prompt_path=prompt,
                preflight_path=write_json(tmp_path/'preflight.json', {}),
                project_root=Path(__file__).resolve().parents[1], output_dir=tmp_path/'diagnostic'), state


def test_real_file_entry_produces_not_qualified_diagnostic(monkeypatch, tmp_path):
    module = api()
    args, state = case(monkeypatch, tmp_path)
    monkeypatch.setattr(module, 'validate_pre_model_identity', lambda *a: [])
    result = module.run_diagnostic(**args)
    report = json.loads(result.read_text())
    assert report['qualification'] == 'NOT_QUALIFIED'
    assert report['gate8_verdict'] == 'NOT_RUN'
    assert report['scientific_outputs_allowed'] is False
    assert report['status'] == 'DIAGNOSTIC_COMPLETE'
    ledger = json.loads((result.parent/'producer/pass_identity.json').read_text())
    assert [r['request_role'] for r in ledger['requests']] == ['warmup', 'measured']
    assert len(ledger['requests'][1]['observed_boundary_ids']) == 3
    assert (result.parent/'producer/drain_ledger.json').is_file()
    assert (result.parent/'producer/stage_ledger.json').is_file()
    assert state['loads'] == 1


def test_pre_model_failure_never_loads(monkeypatch, tmp_path):
    module = api()
    args, state = case(monkeypatch, tmp_path)
    monkeypatch.setattr(module, 'validate_pre_model_identity', lambda *a: ['identity conflict'])
    with pytest.raises(ValueError, match='identity conflict'):
        module.run_diagnostic(**args)
    assert state['loads'] == 0


def test_model_failure_preserves_incomplete_without_retry(monkeypatch, tmp_path):
    module = api()
    args, state = case(monkeypatch, tmp_path, failed=True)
    monkeypatch.setattr(module, 'validate_pre_model_identity', lambda *a: [])
    result = module.run_diagnostic(**args)
    assert json.loads(result.read_text())['status'] == 'DIAGNOSTIC_INCOMPLETE'
    assert state['loads'] == 1


@pytest.mark.parametrize('damage', ['output', 'hash', 'workload', 'sampling', 'dtype', 'root'])
def test_invalid_inputs_never_load(monkeypatch, tmp_path, damage):
    module = api()
    args, state = case(monkeypatch, tmp_path)
    monkeypatch.setattr(module, 'validate_pre_model_identity', lambda *a: [])
    if damage == 'output':
        args['output_dir'].mkdir()
    elif damage == 'root':
        args['project_root'] = tmp_path
    else:
        value = json.loads(args['manifest_path'].read_text())
        value['prompt_tokens_sha256' if damage == 'hash' else 'repeat_count'] = '0'*64 if damage == 'hash' else 2
        if damage in ('sampling','dtype'):
            value['repeat_count'] = 1
            value['sampling_config' if damage == 'sampling' else 'dtype_and_quantization'] = {'do_sample':True} if damage == 'sampling' else 'bf16'
        write_json(args['manifest_path'], value)
    with pytest.raises((ValueError, FileExistsError)):
        module.run_diagnostic(**args)
    assert state['loads'] == 0


def test_loaded_config_observation_is_not_native_backend_qualification(monkeypatch, tmp_path):
    module = api()
    args, state = case(monkeypatch, tmp_path)
    from exposedpath import runner
    from types import SimpleNamespace
    load = runner.load_model
    def configured_load(*a, **kw):
        result = load(*a, **kw)
        result[0].config = SimpleNamespace(_attn_implementation='sdpa', model_type='qwen2', use_cache=True)
        return result
    monkeypatch.setattr(runner, 'load_model', configured_load)
    monkeypatch.setattr(module, 'validate_pre_model_identity', lambda *a: [])
    report = json.loads(module.run_diagnostic(**args).read_text())
    assert report['configured_attention_backend'] == 'sdpa'
    assert report['native_attention_backend'] == 'UNKNOWN'
    observation = json.loads((args['output_dir']/'loaded_config.json').read_text())
    assert observation['model_type'] == 'qwen2'
    assert observation['qualification'] == 'NOT_ASSESSED'


def test_diagnostic_load_policy_disables_hidden_fallback(monkeypatch):
    from exposedpath import runner
    assert 'allow_fallback' in inspect.signature(runner.load_model).parameters
    calls = []
    def failure(*a, **kw):
        calls.append(kw)
        raise RuntimeError('deliberate load failure')
    monkeypatch.setattr(runner.AutoModelForCausalLM, 'from_pretrained', failure)
    monkeypatch.setattr(runner.torch.cuda, 'is_available', lambda:False)
    with pytest.raises(RuntimeError, match='deliberate'):
        runner.load_model('synthetic-model', allow_fallback=False)
    assert len(calls) == 1


@pytest.mark.parametrize('damage', [None, 'escape', 'changed', 'duplicate', 'redirect'])
def test_model_inventory_binds_content_without_path_escape(tmp_path, monkeypatch, damage):
    module = api()
    assert callable(getattr(module, 'verify_model_inventory', None))
    model = tmp_path/'model'; model.mkdir()
    (model/'config.json').write_text('{}')
    if damage == 'redirect':
        alias=model/'unlisted.json'; alias.write_text('{}')
        original=Path.resolve
        monkeypatch.setattr(Path,'resolve',lambda p,*a,**kw: original(model/'config.json') if p==alias else original(p,*a,**kw))
    row = dict(RelativePath='config.json', Bytes='2', SHA256=sha(model/'config.json'))
    if damage == 'escape': row['RelativePath'] = '../outside.json'
    if damage == 'changed': row['SHA256'] = '0'*64
    inventory = tmp_path/'model.csv'
    with inventory.open('w', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=row.keys()); writer.writeheader()
        writer.writerows([row,row] if damage == 'duplicate' else [row])
    if damage:
        with pytest.raises(ValueError): module.verify_model_inventory(model, inventory, sha(inventory))
    else:
        result = module.verify_model_inventory(model, inventory, sha(inventory))
        assert result['verified_files'] == 1
        assert result['revision'] == 'UNKNOWN'


def test_prepare_binds_fresh_manifest_to_real_inputs(monkeypatch, tmp_path):
    module = api()
    assert callable(getattr(module, 'prepare_diagnostic', None))
    from exposedpath import platform_adapter
    from exposedpath_v141 import gate8_source_probe
    from types import SimpleNamespace
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3'); monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(platform_adapter,'git',lambda args,**kw: '' if 'status' in args else 'd'*40)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'555.99')
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')))
    model=tmp_path/'model'; model.mkdir(); (model/'config.json').write_text('{"model_type":"qwen2"}')
    inventory=tmp_path/'model.csv'
    with inventory.open('w',newline='') as handle:
        writer=csv.DictWriter(handle,fieldnames=['RelativePath','Bytes','SHA256']); writer.writeheader()
        writer.writerow(dict(RelativePath='config.json',Bytes=(model/'config.json').stat().st_size,SHA256=sha(model/'config.json')))
    prompt=write_json(tmp_path/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',
        tokenizer_id='synthetic-tokenizer',fixed_input_tokens=32,
        samples=[dict(input_ids=[1]*32,attention_mask=[1]*32)]))
    output=module.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,
        inventory_path=inventory,inventory_sha256=sha(inventory),prompt_path=prompt,
        prompt_sha256=sha(prompt),expected_commit='d'*40,physical_gpu=3)
    manifest=json.loads((output/'manifest.json').read_text())
    assert manifest['repeat_count']==1 and manifest['warmup_count']==1
    assert manifest['attention_backend']=='UNKNOWN_NOT_LOADED'
    assert manifest['runner_git_commit']=='d'*40
    assert manifest['prompt_tokens_sha256']==sha(output/'prompt.json')
    assert manifest['runner_source_sha256']==sha(Path(module.__file__).parent/'runner.py')
    assert manifest['model_content_snapshot']['content_verification']=='HISTORICAL_HASH_REFERENCE_CURRENT_SIZE_SET_ONLY'
