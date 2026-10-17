"""Default A: CPU/build only. One future B2 requires reviewed new A, never resumes Pilot."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys


def review_static(root,reviewed,cfg,index_sha):
    # No CUDA/model/collector import or action before this verified binding.
    import re
    p=Path(root)/'receipt.json'
    if not isinstance(reviewed,str) or re.fullmatch('[0-9a-fA-F]{64}',reviewed) is None or not p.is_file():
        raise ValueError('MEMSET_PREFILL_REVIEWED_STATIC_REQUIRED')
    from scripts.memset_micro import check_reviewed_static
    return check_reviewed_static(root,reviewed,cfg['execution_commit'],index_sha)


def resources(out,archive):
    from scripts.coe_startup_storage import volume_identity,safe_directory,write_probe
    values={};errors=[];locations=[];temporary=[Path(os.environ['TEMP']),Path(os.environ['TMP'])]
    if os.environ.get('TMPDIR'):temporary.append(Path(os.environ['TMPDIR']))
    for path in (Path(out),Path(archive).parent,*temporary):
        locations.append(str(path))
        try:path=safe_directory(path);write_probe(path);key=volume_identity(path)
        except OSError as exc:
            errors.append(dict(path=str(path),reason='PATH_WRITE_OR_VOLUME_UNAVAILABLE',error=str(exc)));continue
        if key in values:continue
        values[key]=dict(path=str(path),free_bytes=None,status='UNKNOWN',required_bytes=2**31)
        try:
            usage=shutil.disk_usage(path)
            if type(usage.free) is not int or usage.free<0:raise OSError('Invalid free-byte value')
            values[key].update(free_bytes=usage.free,status='OBSERVED')
            if usage.free<2**31:errors.append(dict(path=str(path),reason='FREE_SPACE_INSUFFICIENT',free_bytes=usage.free))
        except OSError as exc:errors.append(dict(path=str(path),reason='FREE_SPACE_UNKNOWN',error=str(exc)))
    return dict(status='STARTUP_RESOURCES_BLOCKED' if errors else 'STARTUP_RESOURCES_READY',locations=locations,
        errors=errors,volumes=values,historical_ylq_total_bytes=None,
        long_term_target_exclusive_bytes=50000000000,long_term_status='UNKNOWN_NOT_PROVEN',automatic_cleanup=False)


def verified_pack(out,archive):
    from scripts import memset_micro as common
    for p in Path(out).rglob('process.json'):
        v=json.loads(p.read_text(encoding='utf8'))
        common.require(not str(v.get('descendant_exit_status','')).startswith('UNKNOWN'),'UNKNOWN_WRITER:'+str(p))
        common.require(v.get('status') not in ('STARTING','RUNNING'),'ACTIVE_WRITER:'+str(p))
    return common.pack(out,archive) # Also checks *.process.json, reparse, bytes and ZIP.


def collect(cfg,package,static,out):
    """Exactly one NEW B2, no loops, retries, P0, Cpre or Pilot slots."""
    from scripts import memset_micro as common
    from exposedpath import gate8_diagnostic as entry,memset_prefill as contract
    from exposedpath.gate8_isolated_preflight import read,sha,write_new
    old=Path(static);built=read(old/'build/build.json')
    common.verify_rows(old/'build',built['binary_files'])
    require=contract.require
    require(common.runtime_fact(cfg['runtime_path'])==read(old/'runtime_file.json'),'RUNTIME_CHANGED_SINCE_A')
    require(sha(cfg['nsys'])==cfg['nsys_sha256'],'COLLECTOR_HASH')
    # Module bytes come from the independently reviewed static receipt + build,
    # not a target's just-observed runtime hash promoted to its own expectation.
    b=contract.binding(cfg['run_id'],cfg['execution_commit'],dict(path=built['recorder'],sha256=sha(built['recorder'])),
        dict(path=cfg['runtime_path'],sha256=cfg['runtime_expected_sha256']))
    prompt=read(Path(package)/'input_b1.json');require(sha(Path(package)/'input_b1.json')==cfg['input_seed_sha256'],'INPUT_SEED')
    from copy import deepcopy
    prompt['samples']=[dict(deepcopy(prompt['samples'][0]),sample_index=i) for i in range(2)]
    write_new(out/'input_b2.json',prompt)
    # Only B prepares/probes CUDA. Stage A never calls this function.
    os.environ.update(CUDA_VISIBLE_DEVICES='3',CUDA_DEVICE_ORDER='PCI_BUS_ID')
    prepared=entry.prepare_diagnostic(output_dir=out/'prepared',model_path=cfg['model'],
        inventory_path=Path(package)/'model_inventory.csv',inventory_sha256=cfg['inventory_sha256'],
        prompt_path=out/'input_b2.json',prompt_sha256=sha(out/'input_b2.json'),expected_commit=cfg['execution_commit'],
        physical_gpu=3,engineering_attention_backend='sdpa',target_python=cfg['target_python'],site_root=cfg['site_root'],batch_binding=b)
    mf=read(prepared/'manifest.json')
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    require(normalized_uuid(mf['gpu_uuid'])==normalized_uuid(cfg['gpu_uuid']) and
        normalized_pci(mf['gpu_pci_bus_id'])==normalized_pci(cfg['gpu_pci_bus_id']),'PREPARED_DEVICE')
    code=Path(cfg['code_root']);target=out/'collection'
    from scripts.gate8_diagnostic_collect import run_once
    process=run_once([cfg['python'],'-X','utf8','-u',str(code/'scripts/gate8_diagnostic_collect.py'),
        '--nsys',cfg['nsys'],'--python',cfg['target_python'],'--prepared',str(prepared),'--output',str(target),
        '--execute-engineering-diagnostic','--engineering-a-only','--memset-prefill-parameters'],out/'one_b2_driver',timeout_seconds=900,progress=True)
    require(process['status']=='COMPLETE' and process['exit_code']==0 and process['timed_out'] is False,'ONE_B2_DRIVER_FAILED_STOP_SEE_RAW_LOG')
    result=read(target/'collection_report.json')
    require(result.get('schema_version')=='memset-prefill-collection/0.1.0' and result.get('error') is None
        and result['status']=='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW'
        and result['export_status']=='PASS' and result['result_sha256']==sha(target/'analyzed/parameters.json'),'COLLECTION_RESULT')
    tokens=read(target/'diagnostic/batch_tokens.json')['requests'][0]['token_ids']
    require(tokens==cfg['expected_token_ids'] and all(len(row)==2 and row[0]==row[1] for row in tokens),'TOKEN_REFERENCE_CONFLICT')
    return result


def stage(package,phase,reviewed=None):
    package=Path(package).resolve()
    cfg=json.loads((package/'delivery.json').read_text(encoding='utf8'))
    code=Path(cfg['code_root']);sys.path.insert(0,str(code))
    from scripts import memset_micro as common
    from exposedpath.gate8_isolated_preflight import read
    index=common.verify_package(package)
    require=common.require
    require(cfg['schema_version']=='memset-prefill-delivery/0.1.0' and phase in ('A','B')
        and cfg['execution_commit']==cfg['analysis_commit'] and cfg['model_process_budget']==cfg['profile_budget']==1,'DELIVERY')
    root=Path(cfg['server_root']);short=cfg['execution_commit'][:12]
    static=root/'diagnostics'/('memset_prefill_'+short+'_static')
    out=static if phase=='A' else root/'evidence/memset_prefill'/('b2_'+short+'_once')
    archive=root/'transfer'/('memset_prefill_'+short+('_static.zip' if phase=='A' else '_b2_once.zip'))
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    if phase=='B':review_static(static,reviewed,cfg,index)
    out.mkdir(parents=True,exist_ok=False);status='BLOCKED';error=None;build_sha=None
    try:
        require(list(sys.version_info[:3])==cfg['python_version'],'PYTHON_VERSION')
        if phase=='A':common.deploy(cfg,package,out)
        common.tree(cfg,cfg['execution_commit']);common.verify_rows(code,cfg['sources'])
        common.write(out/'source_bytes.json',[dict(expected=r,actual=common.file_fact(common.safe(code,r['path']))) for r in cfg['sources']])
        observed_space=resources(out,archive);common.write(out/'resources.json',observed_space)
        require(observed_space['status']=='STARTUP_RESOURCES_READY','STARTUP_RESOURCES_BLOCKED_SEE_RECEIPT')
        for n,r in cfg['toolchain_files'].items():require(common.file_fact(r['path'])==r,'TOOLCHAIN:'+n)
        runtime=common.runtime_fact(cfg['runtime_path']);require(runtime['sha256']==cfg['runtime_expected_sha256'],'RUNTIME_BYTES')
        common.write(out/'runtime_file.json',runtime)
        if phase=='A':
            from analysis.coe_helper_identity import validate_source
            common.write(out/'helper_identity.json',validate_source((code/'exposedpath/runner.py').read_text(encoding='utf8'),'COE_PILOT_NATURAL'))
            from scripts.memset_prefill_native import build
            common.extract(package/'detours.zip',out/'detours',prefix=cfg['detours_directory']+'/')
            common.extract(package/'nvtx.zip',out/'nvtx',prefix=cfg['nvtx_directory']+'/c/include/')
            common.extract(package/'sdk.zip',out/'sdk')
            bc=dict(cfg['build'],detours=str(out/'detours'),nvtx_include=str(out/'nvtx'),
                cuda_include=str(out/'sdk/include'),crt_include=str(out/'sdk/include'))
            built=build(bc,out/'build');build_sha=common.sha(out/'build/build.json')
            common.write(out/'build_configuration.json',bc)
            env=os.environ.copy()
            for k in ('PYTEST_ADDOPTS','PYTEST_PLUGINS'):env.pop(k,None)
            env.update(CUDA_VISIBLE_DEVICES='-1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',MEMSET_MICRO_CPU_CONFIG=str(out/'build_configuration.json'),
                MEMSET_PREFILL_BUILT_JSON=str(out/'build/build.json'))
            common.command([cfg['python'],'-X','utf8','-m','pytest','-q','-ra','-p','no:cacheprovider',*cfg['cpu_tests'],
                '--basetemp',str(root/'diagnostics'/('memset_prefill_'+short+'_cpu_tmp')),
                '--junitxml',str(out/'cpu.xml')],code,out/'cpu_changes',env=env,timeout=300)
            import xml.etree.ElementTree as ET
            suite=ET.parse(out/'cpu.xml').getroot().find('testsuite')
            require(int(suite.attrib['tests'])==cfg['cpu_test_count'] and all(suite.attrib[k]=='0' for k in ('failures','errors','skipped')),'CPU_RESULT')
            require(common.runtime_fact(cfg['runtime_path'])==runtime,'RUNTIME_CHANGED')
            status='STATIC_READY_FOR_REVIEW'
        else:
            collect(cfg,package,static,out);status='ONE_B2_EVIDENCE_COMPLETE_STOP_FOR_REVIEW'
        common.verify_rows(code,cfg['sources']);common.tree(cfg,cfg['execution_commit'])
        require(common.runtime_fact(cfg['runtime_path'])==runtime,'RUNTIME_CHANGED_DURING_STAGE')
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    common.write(out/'receipt.json',dict(schema_version='memset-prefill-receipt/0.1.0',status=status,error=error,phase=phase,
        execution_commit=cfg['execution_commit'],analysis_commit=cfg['analysis_commit'],package_index_sha256=index,
        build_sha256=build_sha,runtime_file_sha256=common.sha(out/'runtime_file.json') if (out/'runtime_file.json').is_file() else None,
        reviewed_static_receipt_sha256=reviewed,automatic_retry=False,role='Engineering',
        model_process_budget=0 if phase=='A' else 1,profile_budget=0 if phase=='A' else 1,
        stage_a_cuda_programs_executed=0 if phase=='A' else None,a_admission='NOT_ASSESSED',coe_admission='NOT_ASSESSED',
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',historical_ylq_total_bytes=None,
        long_term_target_exclusive_bytes=50000000000))
    # Copy the exact executed bootstrap/launcher/config for review, outside code.
    for name in ('delivery.json','package_manifest.json','run_memset_prefill.ps1','memset_prefill_stage.py','prerequisite_reference.json'):
        shutil.copyfile(package/name,out/name)
    try:print(json.dumps(verified_pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('stage-a','stage-b'));p.add_argument('package',type=Path)
    p.add_argument('--reviewed-static-sha256');a=p.parse_args(argv)
    return stage(a.package,'A' if a.action=='stage-a' else 'B',a.reviewed_static_sha256)


if __name__=='__main__':raise SystemExit(main())
