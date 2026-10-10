"""Single-request Engineering diagnostic. Never grants scientific qualification."""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path

from scripts.gate7_smoke_validation import validate_pre_model_identity


def measurement_pass(manifest):
    if 'formal' in manifest or manifest.get('run_role')=='FORMAL' or manifest.get('data_role')=='Formal':
        from .formal_protocol import validate
        return validate(manifest)['pass_id']
    if 'pilot' in manifest or manifest.get('data_role')=='Pilot' or manifest.get('run_role')=='PILOT':
        from .gate11_pilot import validate
        return validate(manifest)['pass_id']
    if 'engineering_pair' not in manifest:
        return 'pass1'
    pair=manifest['engineering_pair']
    if (not isinstance(pair,dict) or set(pair)!={'schema_version','pair_id','pass_id'}
            or pair['schema_version']!='gate8-engineering-pair/0.1'
            or not isinstance(pair['pair_id'],str) or not pair['pair_id'].strip()
            or pair['pass_id'] not in ('pass0','pass1')):
        raise ValueError('ENGINEERING_PAIR_DECLARATION')
    return pair['pass_id']


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
                       engineering_attention_backend=None, target_python=None, site_root=None,
                       pair_id=None, pair_pass=None, gate10_input_tokens=None, n1_variant=None,
                       pilot_binding=None, formal_binding=None):
    """Explicit preflight: hashes and minimal CUDA identity, no model load."""
    from exposedpath import platform_adapter
    from exposedpath.manifest import create_manifest, finalize_manifest
    from exposedpath.workload import load_prompt_tokens
    from exposedpath_v141.gate8_source_probe import TorchBackend
    root = Path(__file__).resolve().parents[1]
    output = Path(output_dir).resolve()
    if formal_binding is not None:
        from . import formal_protocol as formal
        formal.validate_binding(formal_binding)  # BEFORE probes, filesystem creation or CUDA.
        if pilot_binding is not None or any(x is not None for x in (pair_id,pair_pass,n1_variant,gate10_input_tokens)):
            raise ValueError('FORMAL_LEGACY_ARGUMENT_CONFLICT')
        if (engineering_attention_backend!='sdpa' or not target_python or not site_root
                or expected_commit!=formal_binding['protocol']['execution_commit']):
            raise ValueError('FORMAL_VERIFIED_ENTRY_REQUIRED')
        formal.validate_artifacts(root,formal_binding['protocol'])
        n1_variant=formal_binding['variant']
        if formal_binding['condition']=='G512': gate10_input_tokens=512
    if pilot_binding is not None:
        from .gate11_pilot import minimal_fields
        pilot_fields=minimal_fields(pilot_binding)
        if any(x is not None for x in (pair_id,pair_pass,n1_variant,gate10_input_tokens)):
            raise ValueError('PILOT_LEGACY_ARGUMENT_CONFLICT')
        if engineering_attention_backend!='sdpa' or not target_python or not site_root:
            raise ValueError('PILOT_VERIFIED_ENTRY_REQUIRED')
        n1_variant=pilot_binding['variant']
        if pilot_binding['condition']=='G512': gate10_input_tokens=512
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
    if bool(target_python) != bool(site_root) or (target_python and declared is None):
        raise ValueError('DIAGNOSTIC_TARGET_ARGUMENTS')
    from exposedpath_v141.gate8_target_python import probe
    target = probe(target_python,site_root) if target_python else None
    if n1_variant is not None and (target is None or engineering_attention_backend!='sdpa'
            or pair_id is not None or pair_pass is not None or gate10_input_tokens is not None):
        raise ValueError('N1_PREPARE_PROFILE')
    content = verify_model_inventory(model_path, inventory_path, inventory_sha256, rehash=True)
    prompt = load_prompt_tokens(Path(prompt_path))
    length=32 if gate10_input_tokens is None else gate10_input_tokens
    if prompt['fixed_input_tokens'] != length or _sha(prompt_path) != prompt_sha256.lower():
        raise ValueError('DIAGNOSTIC_PROMPT_IDENTITY')
    if gate10_input_tokens is not None:
        from exposedpath.gate10_workload import validate_input
        if engineering_attention_backend!='sdpa' or target is None or pair_id is not None or pair_pass is not None:
            raise ValueError('GATE10_EXECUTION_PROFILE')
        validate_input(prompt,json.loads((Path(model_path)/'config.json').read_text(encoding='utf-8')),length)
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
    if pair_id is not None or pair_pass is not None:
        if target is None or declared is None:
            raise ValueError('ENGINEERING_PAIR_TARGET_REQUIRED')
        manifest['engineering_pair']=dict(schema_version='gate8-engineering-pair/0.1',pair_id=pair_id,pass_id=pair_pass)
        measurement_pass(manifest)
    if declared is not None:
        manifest.update(engineering_scope=declared, attention_backend=engineering_attention_backend)
    if target is not None:
        manifest['target_python']=target
        from exposedpath.gate8_isolated_preflight import VERSION
        manifest['isolated_preflight_version']=VERSION
    if gate10_input_tokens is not None:
        from exposedpath.gate10_workload import declaration as workload
        from exposedpath_v141.gate9_domain import declaration as domain, G1
        manifest.update(gate10_workload=workload(length),domain_qualification=domain(G1))
    if n1_variant is not None:
        from exposedpath.n1_model import declaration as policy, CALLSITE, validate_manifest, execution_declaration
        from exposedpath_v141.gate9_domain import declaration as domain, N1
        variant='Vsync' if n1_variant=='V16' else n1_variant
        manifest.update(n1_model=policy(variant),n1_model_execution=execution_declaration(),domain_qualification=domain(N1),study_mode='N1_INTERVENTION',
            n1_intervention=dict(sync_origin='n1_intervention',callsite_id=CALLSITE,intervention_variant_id=variant))
        validate_manifest(manifest)
    if pilot_binding is not None:
        manifest.pop('gate10_workload',None)
        manifest.update(pilot_fields)
        from .gate11_pilot import validate
        validate(manifest)
    if formal_binding is not None:
        manifest.pop('gate10_workload',None)
        manifest.update(formal.minimal_fields(formal_binding))
    manifest = finalize_manifest(manifest,prompt,prompt_tokens_path=output/'prompt.json')
    if formal_binding is not None:
        # Validate the final producer object: create_manifest deliberately leaves
        # input hash / WMPC unfinished. Never substitute the declared expectation
        # for the SHA256 recomputed from the actual copied input bytes.
        formal.validate(manifest)
    for name, value in (('manifest.json',manifest),('preflight.json',preflight)):
        with (output/name).open('x',encoding='utf-8') as handle:
            json.dump(value,handle,indent=2,sort_keys=True)
    return output


def run_diagnostic(*, manifest_path, prompt_path, preflight_path, project_root, output_dir,
                   auxiliary_receipt=None,auxiliary_sha256=None,launch_nonce=None):
    from exposedpath import runner

    if Path(project_root).resolve() != Path(__file__).resolve().parents[1]:
        raise ValueError('DIAGNOSTIC_CODE_ROOT_CONFLICT')
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)
    manifest_path, prompt_path = Path(manifest_path), Path(prompt_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8-sig'))
    pass_id=measurement_pass(manifest)
    from .gate11_pilot import roles
    role=roles(manifest)
    from .formal_protocol import control
    pilot=control(manifest)
    formal='formal' in manifest
    if formal:
        import platform
        # Already imported framework / interpreter facts, no auxiliary commands
        # and no CUDA call added to the target or measured window.
        actual=dict(runtime_version='python'+platform.python_version(),
            inference_framework_version='torch'+runner.torch.__version__,
            cuda_version_used=runner.torch.version.cuda or 'unknown')
        expected=pilot['protocol']['execution_constraints']['software']
        if any(actual[k]!=expected[k] for k in actual):raise ValueError('FORMAL_TARGET_SOFTWARE')
    from .gate11_warmup import active as warmup_control,request_plan as warmup_plan
    from exposedpath.gate8_engineering_contract import validate_declaration, EXECUTION_VERSION
    declared = validate_declaration(manifest) if 'engineering_scope' in manifest else None
    n1 = None
    if 'n1_model' in manifest:
        from exposedpath.n1_model import Execution, validate_manifest
        n1 = Execution(validate_manifest(manifest), runner.torch.cuda,warmup_tokens_unknown=warmup_control(pilot))
    elif manifest.get('study_mode') != 'G1_NATURAL' or manifest.get('n1_intervention') is not None:
        raise ValueError('DIAGNOSTIC_MODE_CONFLICT')
    isolated='isolated_preflight_version' in manifest
    claim=None
    if isolated:
        from exposedpath import gate8_isolated_preflight as isolated_gate
        if (manifest['isolated_preflight_version']!=isolated_gate.VERSION or declared is None
                or 'target_python' not in manifest or not all((auxiliary_receipt,auxiliary_sha256,launch_nonce))):
            raise ValueError('ISOLATED_PREFLIGHT_REQUIRED')
        if Path(prompt_path).resolve()!=manifest_path.resolve().parent/'prompt.json' or Path(preflight_path).resolve()!=manifest_path.resolve().parent/'preflight.json':
            raise ValueError('ISOLATED_PREFLIGHT_INPUT_PATH')
        claim=isolated_gate.consume(receipt=auxiliary_receipt,expected_sha=auxiliary_sha256,
            nonce=launch_nonce,prepared=manifest_path.parent,output=output_dir.parent,root=project_root)
        if formal:
            from .formal_protocol import reference
            if claim.get('formal_reference')!=reference(pilot):raise ValueError('FORMAL_TARGET_PREFLIGHT_REFERENCE')
    elif any(x is not None for x in (auxiliary_receipt,auxiliary_sha256,launch_nonce)):
        raise ValueError('ISOLATED_PREFLIGHT_UNDECLARED')
    runtime=None
    if 'target_python' in manifest:
        from exposedpath_v141.gate8_target_python import current
        runtime=current(manifest['target_python'])
        if declared is None:
            raise ValueError('DIAGNOSTIC_TARGET_PROFILE_MISSING')
        verify_model_inventory(manifest['model_id'],manifest_path.parent/'model_inventory.csv',
            manifest['model_content_snapshot']['inventory_sha256'],rehash=True)
    issues = [] if isolated else validate_pre_model_identity(manifest_path, Path(preflight_path), Path(project_root))
    if issues:
        raise ValueError('; '.join(issues))
    from exposedpath.gate10_workload import input_length,validate_input
    length=input_length(manifest)
    if 'gate10_workload' in manifest or (pilot is not None and length==512):
        validate_input(json.loads(prompt_path.read_text(encoding='utf-8')),
            json.loads((Path(manifest['model_id'])/'config.json').read_text(encoding='utf-8')),length)
    expected = dict(fixed_input_tokens=length, fixed_output_tokens=2, batch_size=1,
                    warmup_count=pilot.get('warmup_count',1) if pilot is not None else 1,
                    repeat_count=1, execution_mode='eager',
                    **role,
                    dtype_and_quantization='fp16', sampling_config={'do_sample':False},
                    runner_git_dirty=False)
    if any(type(manifest.get(k)) is not type(v) or manifest[k] != v for k, v in expected.items()):
        raise ValueError('DIAGNOSTIC_FIXED_WORKLOAD_CONFLICT')
    if (manifest['prompt_tokens_sha256'] != _sha(prompt_path)
            or manifest['runner_source_sha256'] != _sha(runner.__file__)):
        raise ValueError('DIAGNOSTIC_INPUT_HASH_CONFLICT')
    fields = {k: manifest[k] for k in ('experiment_id', 'wmpc_id', 'run_id',
              'runner_git_commit', 'runner_git_dirty', 'runner_source_sha256')}
    fields.update(pid=os.getpid(), pass_id=pass_id, attempt_id='diagnostic-1',
                  wmpc_manifest_sha256=_sha(manifest_path), prompt_sha256=_sha(prompt_path))
    if pilot is not None:
        fields.update(**role,**{('formal' if formal else 'pilot'):pilot})
    output_dir.mkdir(parents=True, exist_ok=False)
    if claim is not None:
        isolated_gate.write_new(output_dir/'isolated_preflight_target.json',claim)
    if runtime is not None:
        with (output_dir/'target_runtime.json').open('x',encoding='utf-8') as handle:
            json.dump(runtime,handle,indent=2,sort_keys=True)
    if declared is not None:
        # Probe in the target process, not the prepare process. These are device
        # identity observations, not model work or a completeness certificate.
        from exposedpath_v141.gate8_source_probe import TorchBackend
        from exposedpath_v141.gate8_adapter import normalized_uuid, normalized_pci
        backend=TorchBackend()
        if isolated:
            from exposedpath.platform_adapter import cuda_identity_native
            observed_device=cuda_identity_native(backend.cuda)
        else:
            observed_device=backend.identity()
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
        if n1 is not None and (str(model.dtype)!='torch.float16' or model.training is not False):
            raise ValueError('N1_ACTUAL_DTYPE_OR_TRAINING')
        config = getattr(model, 'config', None)
        loaded_config.update(
            configured_attention_backend=getattr(config, '_attn_implementation', None),
            model_type=getattr(config, 'model_type', None),
            configured_use_cache=getattr(config, 'use_cache', None),
            native_attention_backend='UNKNOWN', qualification='NOT_ASSESSED')
        with (output_dir/'loaded_config.json').open('x', encoding='utf-8') as handle:
            json.dump(loaded_config, handle, indent=2, sort_keys=True)
        if declared is not None and (loaded_config['configured_attention_backend']!=declared['attention_backend']
                or loaded_config['configured_use_cache'] is not True or loaded_config['model_type']!='qwen2'):
            raise ValueError('ENGINEERING_LOADED_CONFIGURATION_CONFLICT')
    observed_workload=[]
    observed_tokens=[]
    def observe_invocation(identity,result):
        observed_workload.append(dict(identity=identity,**{k:result[k] for k in (
            'actual_input_tokens','actual_output_tokens','early_eos')}))
        if pilot is not None:
            # Already host-readable values, after final completion and measured
            # ranges. No Tensor operation, D2H or synchronization here.
            observed_tokens.append(dict(identity=identity,
                token_ids=[list(b.host_token_ids) for b in result['token_ready_boundaries']]))
    plan=warmup_plan(pilot) if warmup_control(pilot) else [
        dict(request_id='warmup-0',repeat_id='warmup-0',request_role='warmup'),
        dict(request_id='request-0',repeat_id='0',request_role='measured')]
    path = runner.run_gate8_requests_to_files(
        output_dir=output_dir/'producer', output_len=2,
        device=f"cuda:{manifest['gpu_index_logical']}", pass_fields=fields,
        record_drains=True, record_stages=True, setup_observer=observe_setup,
        allow_load_fallback=False,
        n1_controller=n1,
        invocation_observer=observe_invocation if 'gate10_workload' in manifest or pilot is not None else None,
        model_setup=dict(model_path=manifest['model_id'], prompt_path=output_dir/'prompt.json',
                         physical_gpu_index=manifest['gpu_index_physical'], batch_size=1,
                         manifest_path=output_dir/'manifest.json'),
        request_plan=plan)
    producer = json.loads(path.read_text(encoding='utf-8'))
    if pilot is not None:
        with (output_dir/('formal_tokens.json' if formal else 'pilot_tokens.json')).open('x',encoding='utf-8') as handle:
            from .formal_protocol import TOKEN_VERSION
            json.dump(dict(schema_version=TOKEN_VERSION if formal else 'exposedpath-pilot-tokens/0.1.0',**{('formal' if formal else 'pilot'):pilot},
                manifest_sha256=_sha(manifest_path),producer_receipt_sha256=_sha(path),
                requests=observed_tokens),handle,indent=2,sort_keys=True)
    if n1 is not None:
        from exposedpath.n1_model import VERSION
        with (output_dir/'n1_model_calls.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(schema_version='exposedpath-n1-model-calls/0.2.0' if warmup_control(pilot) else VERSION, manifest_sha256=_sha(manifest_path),
                producer_receipt_sha256=_sha(path),pid=os.getpid(),requests=n1.requests),handle,indent=2,sort_keys=True)
    if 'gate10_workload' in manifest or pilot is not None:
        with (output_dir/'workload_observed.json').open('x',encoding='utf-8') as handle:
            json.dump(dict(schema_version='gate10-workload-observed/0.1',
                manifest_sha256=_sha(manifest_path),producer_receipt_sha256=_sha(path),
                observations=observed_workload),handle,indent=2,sort_keys=True)
    if isolated:
        isolated_gate.verify_snapshot(isolated_gate.read(auxiliary_receipt),manifest_path.parent,project_root)
    if declared is not None:
        execution=dict(schema_version=EXECUTION_VERSION,manifest_sha256=_sha(manifest_path),
            producer_receipt_sha256=_sha(path),status=producer['status'],declaration=declared,
            identity={k:fields[k] for k in ('run_id','pass_id','attempt_id','pid')},
            observed_configuration={**{k:loaded_config.get(k) for k in (
                'configured_attention_backend','configured_use_cache','model_type')},'execution_mode':'eager'})
        if n1 is not None:
            execution['n1_model_calls_sha256']=_sha(output_dir/'n1_model_calls.json')
        if pilot is not None:
            if formal:
                from .formal_protocol import EXECUTION_VERSION as formal_version
                execution.update(schema_version=formal_version,**role,formal=pilot,
                    formal_tokens_sha256=_sha(output_dir/'formal_tokens.json'))
            else:
                from .gate11_pilot import versions
                execution.update(schema_version=versions(pilot)[1],**role,pilot=pilot,
                    pilot_tokens_sha256=_sha(output_dir/'pilot_tokens.json'))
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
    if pilot is not None and not formal:
        result.update(schema_version='gate11-pilot-diagnostic/0.2.0' if warmup_control(pilot) else 'gate11-pilot-diagnostic/0.1.0',**role,pilot=pilot,
            pilot_tokens_sha256=_sha(output_dir/'pilot_tokens.json'),gate11_verdict='BLOCKED' if warmup_control(pilot) else 'NOT_RUN')
    if formal:
        from .formal_protocol import reference
        result.update(schema_version='exposedpath-formal-execution-report/0.1.0',**role,formal=pilot,
            formal_reference=reference(pilot),formal_tokens_sha256=_sha(output_dir/'formal_tokens.json'))
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
    prep.add_argument('--target-python')
    prep.add_argument('--site-root')
    prep.add_argument('--pair-id')
    prep.add_argument('--pair-pass',choices=('pass0','pass1'))
    prep.add_argument('--gate10-input-tokens',choices=(128,512),type=int)
    prep.add_argument('--n1-variant',choices=('V0','Vmarker','V16'))
    run = commands.add_parser('run')
    for name in ('manifest-path', 'prompt-path', 'preflight-path', 'project-root', 'output-dir'):
        run.add_argument('--'+name, required=True, type=Path)
    run.add_argument('--auxiliary-receipt',type=Path)
    run.add_argument('--auxiliary-sha256')
    run.add_argument('--launch-nonce')
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
