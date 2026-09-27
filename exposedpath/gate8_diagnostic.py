"""Single-request Engineering diagnostic. Never grants scientific qualification."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from scripts.gate7_smoke_validation import validate_pre_model_identity


def _sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024*1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_model_inventory(model_path, inventory_path, expected_sha256, *, rehash=True):
    model = Path(model_path).resolve()
    if _sha(inventory_path) != expected_sha256.lower():
        raise ValueError('MODEL_INVENTORY_HASH')
    seen = set()
    with Path(inventory_path).open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            relative = Path(row['RelativePath'].replace('\\', '/'))
            lexical = model/relative
            target = lexical.resolve()
            if relative.is_absolute() or '..' in relative.parts or not target.is_relative_to(model) or target in seen:
                raise ValueError('MODEL_INVENTORY_PATH')
            if lexical != target:
                raise ValueError('MODEL_INVENTORY_REDIRECT')
            seen.add(target)
            if target.stat().st_size != int(row['Bytes']) or (rehash and _sha(target) != row['SHA256'].lower()):
                raise ValueError('MODEL_CONTENT_MISMATCH')
    actual = {p for p in model.rglob('*') if p.is_file() and '.cache' not in p.relative_to(model).parts}
    expected = {p for p in seen if '.cache' not in p.relative_to(model).parts}
    if not seen or actual != expected:
        raise ValueError('MODEL_INPUT_SET_MISMATCH')
    return dict(inventory_sha256=_sha(inventory_path), verified_files=len(seen),
                content_verification='CURRENT_CONTENT_HASHES' if rehash else 'HISTORICAL_HASH_REFERENCE_CURRENT_SIZE_SET_ONLY',
                model_input_files=len(expected), cache_auxiliary_files=len(seen)-len(expected), revision='UNKNOWN')


def prepare_diagnostic(*, output_dir, model_path, inventory_path, inventory_sha256,
                       prompt_path, prompt_sha256, expected_commit, physical_gpu,
                       engineering_attention_backend=None):
    """Explicit preflight: hashes and minimal CUDA identity, no model load."""
    from exposedpath import platform_adapter
    from exposedpath.manifest import create_manifest, finalize_manifest
    from exposedpath.workload import load_prompt_tokens
    from exposedpath_v141.gate8_source_probe import TorchBackend
    root = Path(__file__).resolve().parents[1]
    output = Path(output_dir).resolve()
    from exposedpath.gate8_engineering_contract import declaration
    declared = None if engineering_attention_backend is None else declaration(engineering_attention_backend)
    if output.exists():
        raise FileExistsError(output)
    if (platform_adapter.git(['-C',str(root),'rev-parse','HEAD']) != expected_commit
            or platform_adapter.git(['-C',str(root),'status','--porcelain'])):
        raise ValueError('DIAGNOSTIC_GIT_IDENTITY')
    if (os.environ.get('CUDA_DEVICE_ORDER') != 'PCI_BUS_ID'
            or os.environ.get('CUDA_VISIBLE_DEVICES') != str(physical_gpu)):
        raise ValueError('DIAGNOSTIC_MASK')
    content = verify_model_inventory(model_path, inventory_path, inventory_sha256, rehash=False)
    prompt = load_prompt_tokens(Path(prompt_path))
    if prompt['fixed_input_tokens'] != 32 or _sha(prompt_path) != prompt_sha256.lower():
        raise ValueError('DIAGNOSTIC_PROMPT_IDENTITY')
    observed = TorchBackend().identity()
    preflight = dict(physical_gpu_index=physical_gpu, logical_gpu_index=0,
                     gpu_uuid=observed['gpu_uuid'], gpu_pci_bus_id=observed['pci_bus_id'])
    output.mkdir(parents=True, exist_ok=False)
    for name, source in (('prompt.json',prompt_path),('model_inventory.csv',inventory_path)):
        with (output/name).open('xb') as handle:
            handle.write(Path(source).read_bytes())
    manifest = create_manifest(experiment_id='gate8-qwen-diagnostic',run_role='ENGINEERING',
        data_role='Engineering',model_path=str(Path(model_path).resolve()),
        prompt_tokens_file=str(output/'prompt.json'),batch_size=1,fixed_output_tokens=2,
        warmup_count=1,repeat_count=1,gpu=physical_gpu,gpu_index_physical=physical_gpu,
        gpu_index_logical=0,gpu_uuid=observed['gpu_uuid'],gpu_pci_bus_id=observed['pci_bus_id'],
        gpu_name='IDENTITY_BOUND_BY_UUID',require_git_identity=True,git_worktree=root)
    manifest.update(attention_backend='UNKNOWN_NOT_LOADED',
                    runner_source_sha256=_sha(root/'exposedpath/runner.py'),
                    model_content_snapshot=content)
    if declared is not None:
        manifest.update(engineering_scope=declared, attention_backend=engineering_attention_backend)
    manifest = finalize_manifest(manifest,prompt,prompt_tokens_path=output/'prompt.json')
    for name, value in (('manifest.json',manifest),('preflight.json',preflight)):
        with (output/name).open('x',encoding='utf-8') as handle:
            json.dump(value,handle,indent=2,sort_keys=True)
    return output


def run_diagnostic(*, manifest_path, prompt_path, preflight_path, project_root, output_dir):
    from exposedpath import runner

    if Path(project_root).resolve() != Path(__file__).resolve().parents[1]:
        raise ValueError('DIAGNOSTIC_CODE_ROOT_CONFLICT')
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)
    manifest_path, prompt_path = Path(manifest_path), Path(prompt_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    from exposedpath.gate8_engineering_contract import validate_declaration, EXECUTION_VERSION
    declared = validate_declaration(manifest) if 'engineering_scope' in manifest else None
    issues = validate_pre_model_identity(manifest_path, Path(preflight_path), Path(project_root))
    if issues:
        raise ValueError('; '.join(issues))
    expected = dict(fixed_input_tokens=32, fixed_output_tokens=2, batch_size=1,
                    warmup_count=1, repeat_count=1, execution_mode='eager',
                    run_role='ENGINEERING', data_role='Engineering',
                    dtype_and_quantization='fp16', sampling_config={'do_sample':False},
                    runner_git_dirty=False)
    if any(type(manifest.get(k)) is not type(v) or manifest[k] != v for k, v in expected.items()):
        raise ValueError('DIAGNOSTIC_FIXED_WORKLOAD_CONFLICT')
    if (manifest['prompt_tokens_sha256'] != _sha(prompt_path)
            or manifest['runner_source_sha256'] != _sha(runner.__file__)):
        raise ValueError('DIAGNOSTIC_INPUT_HASH_CONFLICT')
    fields = {k: manifest[k] for k in ('experiment_id', 'wmpc_id', 'run_id',
              'runner_git_commit', 'runner_git_dirty', 'runner_source_sha256')}
    fields.update(pid=os.getpid(), pass_id='pass1', attempt_id='diagnostic-1',
                  wmpc_manifest_sha256=_sha(manifest_path), prompt_sha256=_sha(prompt_path))
    output_dir.mkdir(parents=True, exist_ok=False)
    if declared is not None:
        # Probe in the target process, not the prepare process. These are device
        # identity observations, not model work or a completeness certificate.
        from exposedpath_v141.gate8_source_probe import TorchBackend
        from exposedpath_v141.gate8_adapter import normalized_uuid, normalized_pci
        observed_device=TorchBackend().identity()
        pre=json.loads(Path(preflight_path).read_text(encoding='utf-8'))
        if (normalized_uuid(observed_device['gpu_uuid'])!=normalized_uuid(pre['gpu_uuid'])
                or normalized_pci(observed_device['pci_bus_id'])!=normalized_pci(pre['gpu_pci_bus_id'])
                or os.environ.get('CUDA_DEVICE_ORDER')!='PCI_BUS_ID'
                or os.environ.get('CUDA_VISIBLE_DEVICES')!=str(manifest['gpu_index_physical'])):
            raise ValueError('ENGINEERING_PROBE_CONFLICT')
        adapter_pre=dict(gpu_index_physical=pre['physical_gpu_index'],gpu_uuid=pre['gpu_uuid'],
            pci_bus_id=pre['gpu_pci_bus_id'],cuda_device_order='PCI_BUS_ID',
            cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'])
        probe=dict(pid=os.getpid(),gpu_index_logical=manifest['gpu_index_logical'],
            **observed_device,cuda_device_order='PCI_BUS_ID',
            cuda_visible_devices=os.environ['CUDA_VISIBLE_DEVICES'])
        for name,value in (('adapter_preflight.json',adapter_pre),('cuda_probe.json',probe)):
            with (output_dir/name).open('x',encoding='utf-8') as handle:
                json.dump(value,handle,indent=2,sort_keys=True)
        with (output_dir/'runner_source.py').open('xb') as handle:
            handle.write(Path(runner.__file__).read_bytes())
    # Immutable input bytes; no mutation of any supplied manifest or prompt.
    for name, source in (('manifest.json', manifest_path), ('prompt.json', prompt_path),
                         ('preflight.json', Path(preflight_path))):
        with (output_dir/name).open('xb') as handle:
            handle.write(source.read_bytes())
    loaded_config = {}
    def observe_setup(model):
        config = getattr(model, 'config', None)
        loaded_config.update(
            configured_attention_backend=getattr(config, '_attn_implementation', None),
            model_type=getattr(config, 'model_type', None),
            configured_use_cache=getattr(config, 'use_cache', None),
            native_attention_backend='UNKNOWN', qualification='NOT_ASSESSED')
        with (output_dir/'loaded_config.json').open('x', encoding='utf-8') as handle:
            json.dump(loaded_config, handle, indent=2, sort_keys=True)
        if declared is not None and (loaded_config['configured_attention_backend']!=declared['attention_backend']
                or loaded_config['configured_use_cache'] is not True or not loaded_config['model_type']):
            raise ValueError('ENGINEERING_LOADED_CONFIGURATION_CONFLICT')
    path = runner.run_gate8_requests_to_files(
        output_dir=output_dir/'producer', output_len=2,
        device=f"cuda:{manifest['gpu_index_logical']}", pass_fields=fields,
        record_drains=True, record_stages=True, setup_observer=observe_setup,
        allow_load_fallback=False,
        model_setup=dict(model_path=manifest['model_id'], prompt_path=output_dir/'prompt.json',
                         physical_gpu_index=manifest['gpu_index_physical'], batch_size=1,
                         manifest_path=output_dir/'manifest.json'),
        request_plan=[dict(request_id='warmup-0', repeat_id='warmup-0', request_role='warmup'),
                      dict(request_id='request-0', repeat_id='0', request_role='measured')])
    producer = json.loads(path.read_text(encoding='utf-8'))
    if declared is not None:
        execution=dict(schema_version=EXECUTION_VERSION,manifest_sha256=_sha(manifest_path),
            producer_receipt_sha256=_sha(path),status=producer['status'],declaration=declared,
            identity={k:fields[k] for k in ('run_id','pass_id','attempt_id','pid')},
            observed_configuration={**{k:loaded_config.get(k) for k in (
                'configured_attention_backend','configured_use_cache','model_type')},'execution_mode':'eager'})
        with (output_dir/'engineering_execution.json').open('x',encoding='utf-8') as handle:
            json.dump(execution,handle,indent=2,sort_keys=True)
    result = dict(schema_version='gate8-qwen-diagnostic/0.1.0',
                  status='DIAGNOSTIC_COMPLETE' if producer['status'] == 'COMPLETE' else 'DIAGNOSTIC_INCOMPLETE',
                  qualification='NOT_QUALIFIED', gate8_verdict='NOT_RUN',
                  scientific_outputs_allowed=False, measurement_validity='NOT_ASSESSED',
                  dropped_records_status='UNKNOWN',
                  configured_attention_backend=loaded_config.get('configured_attention_backend'),
                  native_attention_backend='UNKNOWN',
                  producer_receipt_sha256=_sha(path), manifest_sha256=_sha(output_dir/'manifest.json'),
                  prompt_sha256=_sha(output_dir/'prompt.json'), run_id=manifest['run_id'])
    report = output_dir/'diagnostic_report.json'
    with report.open('x', encoding='utf-8') as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    for name in ('output-dir','model-path','inventory-path','inventory-sha256',
                 'prompt-path','prompt-sha256','expected-commit'):
        prep.add_argument('--'+name,required=True)
    prep.add_argument('--physical-gpu',required=True,type=int)
    prep.add_argument('--engineering-attention-backend',choices=('sdpa','eager'))
    run = commands.add_parser('run')
    for name in ('manifest-path', 'prompt-path', 'preflight-path', 'project-root', 'output-dir'):
        run.add_argument('--'+name, required=True, type=Path)
    arguments = vars(parser.parse_args())
    command = arguments.pop('command')
    if command == 'prepare':
        print(prepare_diagnostic(**arguments))
        return 0
    path = run_diagnostic(**arguments)
    value = json.loads(path.read_text(encoding='utf-8'))
    print(value['status'])
    return 0 if value['status'] == 'DIAGNOSTIC_COMPLETE' else 1


if __name__ == '__main__':
    raise SystemExit(main())
