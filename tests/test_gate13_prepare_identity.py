"""Real prepare/verified-entry CPU file chain, never CUDA or protocol authority.

Regression: Formal validation must not consume an unfinalized manifest. External
device, interpreter, Git and model operations are doubled; hash/copy/declaration,
manifest construction, role gates and producer files remain production code.
"""
import csv
import hashlib
import json
from types import SimpleNamespace

import pytest

from test_gate8_identity import write_json


def prepared_case(tmp_path, monkeypatch, condition, pass_id, damage=None, protocol_version='G12-ROUTEA/0.1'):
    from test_gate12_formal import release
    from test_n1_verified_entry import source
    from exposedpath import formal_protocol as f, manifest as manifests, platform_adapter
    from exposedpath import gate8_diagnostic as entry, gate8_isolated_preflight as isolated, runner
    from exposedpath_v141 import gate8_source_probe, gate8_target_python as target
    from pathlib import Path
    verify_inventory = entry.verify_model_inventory
    variant = {'N0':'V0', 'Nm':'Vmarker', 'N16':'Vsync'}.get(condition)
    entry, args, state, events = source(tmp_path, monkeypatch, variant or 'V0')
    # The older Engineering fixture has only warmup1 + measured handles.
    # Formal's actual three warmups retain three different streams, then fresh
    # measured stream; do not change the production stream policy for a fixture.
    handles = iter([123,124,125,456])
    def create_stream(**kw):
        assert kw == {'device':0}
        handle = next(handles)
        return SimpleNamespace(cuda_stream=handle, device=SimpleNamespace(index=0),
                               synchronize=lambda: events.append(('sync',handle)))
    monkeypatch.setattr(runner.torch.cuda, 'Stream', create_stream)
    monkeypatch.setattr(entry, 'verify_model_inventory', verify_inventory)
    model = tmp_path/'model'; model.mkdir()
    write_json(model/'config.json', dict(model_type='qwen2', vocab_size=100, max_position_embeddings=1024))
    inventory = tmp_path/'model.csv'
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    with inventory.open('w', newline='', encoding='utf-8') as handle:
        w = csv.DictWriter(handle, fieldnames=['RelativePath','Bytes','SHA256']); w.writeheader()
        w.writerow(dict(RelativePath='config.json', Bytes=(model/'config.json').stat().st_size,
                        SHA256=sha(model/'config.json')))
    length = 512 if condition == 'G512' else 32
    prompt = tmp_path/'declared_input.json'
    write_json(prompt, dict(schema_version='exposedpath-prompt-tokens/1',
        tokenizer_id='synthetic-tokenizer', fixed_input_tokens=length,
        samples=[dict(input_ids=[1]*length, attention_mask=[1]*length)]))
    p, a = release()
    p['version'] = protocol_version
    if protocol_version == 'G12-ROUTEA/0.1.1':
        name = 'docs/v1_4_1/contracts/formal_envelope_schema_v0_1_1.json'
        p['artifact_hashes'][name] = sha(Path(name))
    p['execution_commit'] = p['analysis_commit'] = 'c'*40
    p['input_hashes']['G512' if condition == 'G512' else 'G32'] = sha(prompt)
    p['execution_constraints']['model_inventory_sha256'] = sha(inventory)
    p['execution_constraints']['software']['nvidia_driver_version'] = 'CPU_DOUBLE'
    c = p['execution_constraints']['gpu']; c['pci'] = '0000:01:00.0'
    a['protocol_sha256'] = f.content_hash(p)
    b = f.make_binding(p, a, batch_id='prepare-cpu', block=1, condition=condition,
                      pass_id=pass_id, declared_at='2026-10-03T00:00:00Z')
    monkeypatch.setattr(platform_adapter, 'git', lambda argv, **kw: 'c'*40 if 'rev-parse' in argv else '')
    monkeypatch.setattr(manifests, '_get_nvidia_driver', lambda: 'CPU_DOUBLE')
    monkeypatch.setattr(target, 'probe', lambda *args: {'cpu_fixture':True})
    monkeypatch.setattr(gate8_source_probe, 'TorchBackend', lambda: SimpleNamespace(cuda=runner.torch.cuda,
        identity=lambda: dict(gpu_uuid=c['uuid'], pci_bus_id=c['pci'])))
    monkeypatch.setattr(isolated, 'consume', lambda **kw: dict(formal_reference=f.reference(b), run_id=b['run_id']))
    monkeypatch.setenv('CUDA_DEVICE_ORDER', 'PCI_BUS_ID'); monkeypatch.setenv('CUDA_VISIBLE_DEVICES', '3')
    if damage == 'frozen_input':
        # Valid JSON and same shape, but different bytes than the signed input.
        prompt.write_bytes(prompt.read_bytes()+b' ')
    if damage == 'unsigned': b['approval']['status'] = 'PENDING_USER_SIGNATURE'
    if damage == 'version': b['protocol']['version'] = 'G12-ROUTEA/999'
    if damage == 'copied_input':
        create = manifests.create_manifest
        def corrupt_copy(**kw):
            copied = Path(kw['prompt_tokens_file'])
            copied.write_bytes(copied.read_bytes()+b' ')
            return create(**kw)
        monkeypatch.setattr(manifests, 'create_manifest', corrupt_copy)
    expected = p['input_hashes']['G512' if condition == 'G512' else 'G32']
    prepared = entry.prepare_diagnostic(output_dir=tmp_path/'prepared', model_path=model,
        inventory_path=inventory, inventory_sha256=sha(inventory), prompt_path=prompt,
        prompt_sha256=expected, expected_commit='c'*40, physical_gpu=3,
        engineering_attention_backend='sdpa', target_python='cpu-double', site_root='cpu-site', formal_binding=b)
    args.update(manifest_path=prepared/'manifest.json', prompt_path=prepared/'prompt.json',
                preflight_path=prepared/'preflight.json')
    return entry, args, state, b, prompt, events


@pytest.mark.parametrize('condition', ['G32','G512','N0','Nm','N16'])
@pytest.mark.parametrize('pass_id', ['pass0','pass1'])
@pytest.mark.parametrize('protocol_version', ['G12-ROUTEA/0.1','G12-ROUTEA/0.1.1'])
def test_actual_prepare_finalizes_input_before_formal_gate_and_verified_entry(tmp_path, monkeypatch, condition, pass_id, protocol_version):
    from exposedpath import formal_protocol as f
    entry, args, state, b, prompt, events = prepared_case(tmp_path, monkeypatch, condition, pass_id, protocol_version=protocol_version)
    manifest = json.loads(args['manifest_path'].read_text())
    assert manifest['prompt_tokens_sha256'] == hashlib.sha256(prompt.read_bytes()).hexdigest()
    assert args['prompt_path'].read_bytes() == prompt.read_bytes()
    assert manifest['wmpc_id'] and f.validate(manifest) == b
    f.validate_prepared(manifest, args['manifest_path'].parent, args['project_root'])
    report = entry.run_diagnostic(**args)
    assert json.loads(report.read_text())['status'] == 'DIAGNOSTIC_COMPLETE'
    ledger = json.loads((report.parent/'producer/pass_identity.json').read_text())
    assert ledger['formal'] == b and ledger['pass_id'] == pass_id
    f.validate_actual_requests(manifest, ledger)
    if b['variant']:
        calls=json.loads((report.parent/'n1_model_calls.json').read_text())['requests']
        assert [r['native_handle'] for r in calls] == [123,124,125,456]
        assert len(calls[-1]['interventions']) == (0 if b['variant']=='V0' else 1)
    assert state['loads'] == 1


def test_patch_release_requires_new_content_approval_and_explicit_schema_lock():
    from test_gate12_formal import release
    from exposedpath import formal_protocol as f
    p, a = release(); p['version'] = 'G12-ROUTEA/0.1.1'
    name = 'docs/v1_4_1/contracts/formal_envelope_schema_v0_1_1.json'
    p['artifact_hashes'][name] = '1'*64
    a['protocol_sha256'] = f.content_hash(p)
    f.validate_release(p,a)
    del p['artifact_hashes'][name]; a['protocol_sha256'] = f.content_hash(p)
    with pytest.raises(ValueError,match='SOURCE_LOCK_INCOMPLETE'): f.validate_release(p,a)
    p['artifact_hashes'][name] = '1'*64; a['protocol_sha256'] = '0'*64
    with pytest.raises(ValueError,match='PROTOCOL_HASH'): f.validate_release(p,a)


@pytest.mark.parametrize('damage', ['frozen_input','copied_input','unsigned','version'])
def test_prepare_rejects_original_input_or_release_conflicts_before_model(tmp_path, monkeypatch, damage):
    with pytest.raises(ValueError):
        prepared_case(tmp_path, monkeypatch, 'G32', 'pass0', damage)
    assert not (tmp_path/'diagnostic').exists()


@pytest.mark.parametrize('damage', ['role','hash','input','input_file','variant','config','commit'])
def test_prepared_formal_conflicts_never_load_cpu_model(tmp_path, monkeypatch, damage):
    entry, args, state, b, prompt, events = prepared_case(tmp_path, monkeypatch, 'N16', 'pass1')
    m = json.loads(args['manifest_path'].read_text())
    if damage == 'role': m['data_role'] = 'Pilot'
    if damage == 'hash': m['formal']['approval']['protocol_sha256'] = '0'*64
    if damage == 'input': m['prompt_tokens_sha256'] = '0'*64
    if damage == 'input_file': args['prompt_path'].write_bytes(args['prompt_path'].read_bytes()+b' ')
    if damage == 'variant': m['n1_model']['variant'] = 'V0'
    if damage == 'config': m['repeat_count'] = 2
    if damage == 'commit': m['runner_git_commit'] = 'e'*40
    write_json(args['manifest_path'], m)
    with pytest.raises(ValueError): entry.run_diagnostic(**args)
    assert state['loads'] == 0


@pytest.mark.parametrize('version', ['G12-ROUTEA/999','G12-ROUTEA/0.1'])
def test_patch_ledger_cannot_mix_or_guess_protocol_reference(tmp_path, monkeypatch, version):
    from exposedpath.gate8_identity import validate_pass_identity
    entry,args,_,_,_,_=prepared_case(tmp_path,monkeypatch,'G32','pass0',protocol_version='G12-ROUTEA/0.1.1')
    report=entry.run_diagnostic(**args)
    ledger=json.loads((report.parent/'producer/pass_identity.json').read_text())
    ledger['requests'][0]['identity']['formal_reference']['protocol_version']=version
    with pytest.raises(ValueError): validate_pass_identity(ledger)
