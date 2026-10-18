"""Default CPU A; one future source-only B needs reviewed A and risk acceptance."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import sys


def validate_b_opt_in(reviewed,risk):
    if not isinstance(reviewed,str) or re.fullmatch('[0-9a-fA-F]{64}',reviewed) is None:
        raise ValueError('MEMSET_CALLSITE_REVIEWED_STATIC_REQUIRED')
    if risk is not True:raise ValueError('MEMSET_CALLSITE_SAMPLING_RISK_ACCEPTANCE_REQUIRED')


def review_static(root,reviewed,cfg,index_sha):
    from scripts.memset_micro import sha,require
    validate_b_opt_in(reviewed,True)
    root=Path(root);p=root/'receipt.json'
    require(p.is_file() and sha(p)==reviewed.lower(),'REVIEWED_STATIC_HASH')
    r=json.loads(p.read_text(encoding='utf8'))
    require(r['schema_version']=='memset-callsite-receipt/0.1.0' and r['phase']=='A'
        and r['status']=='STATIC_READY_FOR_REVIEW' and r['error'] is None
        and r['execution_commit']==r['analysis_commit']==cfg['execution_commit']
        and r['package_index_sha256']==index_sha,'REVIEWED_STATIC_BINDING')
    for name,h in r['static_files'].items():require(sha(root/name)==h,'STATIC_FILE_CHANGED:'+name)
    return r


def verify_sources(code,representations):
    from scripts.memset_micro import safe,sha,require
    seen=[]
    for name,choices in representations.items():
        p=safe(code,name);actual=dict(bytes=p.stat().st_size,sha256=sha(p))
        require(any(actual=={k:r[k] for k in ('bytes','sha256')} for r in choices),'SOURCE_BYTES:'+name)
        seen.append(dict(path=name,**actual))
    require(seen,'EMPTY_SOURCE_INDEX');return seen


def capability(cfg,out):
    """Read help/version and actual token only. Never initialize CUDA."""
    import ctypes
    from scripts.memset_micro import command,sha,require,write
    require(sha(cfg['nsys'])==cfg['nsys_sha256'],'COLLECTOR_HASH')
    command([cfg['nsys'],'--version'],out,out/'nsys_version',timeout=30)
    require(b'2026.2.1.210' in (out/'nsys_version.stdout').read_bytes(),'COLLECTOR_VERSION')
    command([cfg['nsys'],'profile','--help'],out,out/'nsys_profile_help',timeout=30)
    help_text=(out/'nsys_profile_help.stdout').read_bytes().decode('utf8',errors='replace')
    required=('--cudabacktrace','--sampling-frequency','--sample','--duration','--kill')
    admin=bool(ctypes.windll.shell32.IsUserAnAdmin()) if os.name=='nt' else False
    result=dict(schema_version='memset-callsite-capability/0.1.0',windows=os.name=='nt',
        administrator=admin,required_options={n:n in help_text for n in required},
        actual_capture_coverage='NOT_RUN',historical_bugcheck_cause='UNKNOWN',cuda_initialized=False)
    write(out/'capability.json',result)
    require(result['windows'] and admin and all(result['required_options'].values()),'CAPABILITY_OR_ADMIN_REQUIRED_NO_AUTOMATIC_ELEVATION')
    return result


def collect(cfg,package,out):
    from exposedpath import gate8_diagnostic as entry,memset_callsite as c,gate8_isolated_preflight as isolated
    from exposedpath_v141.gate8_adapter import normalized_uuid,normalized_pci
    from scripts.gate8_diagnostic_collect import run_once
    from scripts.memset_micro import sha
    package=Path(package);prompt=package/'input_1024.json'
    c.require(sha(prompt)==cfg['input_sha256'],'INPUT_BYTES')
    identity=c.validate_input(isolated.read(prompt),isolated.read(Path(cfg['model'])/'config.json'))
    c.require(identity==cfg['input_identity'],'INPUT_MATRIX_BINDING')
    os.environ.update(CUDA_VISIBLE_DEVICES='3',CUDA_DEVICE_ORDER='PCI_BUS_ID')
    b=c.binding(cfg['run_id'],cfg['execution_commit'])
    prepared=entry.prepare_diagnostic(output_dir=out/'prepared',model_path=cfg['model'],
        inventory_path=package/'model_inventory.csv',inventory_sha256=cfg['inventory_sha256'],prompt_path=prompt,
        prompt_sha256=cfg['input_sha256'],expected_commit=cfg['execution_commit'],physical_gpu=3,
        engineering_attention_backend='sdpa',target_python=cfg['target_python'],site_root=cfg['site_root'],batch_binding=b)
    mf=isolated.read(prepared/'manifest.json')
    c.require(normalized_uuid(mf['gpu_uuid'])==normalized_uuid(cfg['gpu_uuid']) and
        normalized_pci(mf['gpu_pci_bus_id'])==normalized_pci(cfg['gpu_pci_bus_id']),'PREPARED_GPU')
    target=out/'collection'
    r=run_once([cfg['python'],'-X','utf8','-u',str(Path(cfg['code_root'])/'scripts/memset_callsite_collect.py'),
        '--nsys',cfg['nsys'],'--python',cfg['target_python'],'--prepared',str(prepared),'--output',str(target),
        '--execute-reviewed-source-diagnostic'],out/'one_source_driver',timeout_seconds=900,progress=True)
    c.require(r['status']=='COMPLETE' and r['exit_code']==0 and not r['timed_out'],'SOURCE_DRIVER_FAILED_SEE_PRESERVED_REPORT')
    result=isolated.read(target/'collection_report.json')
    c.require(result['schema_version']=='memset-callsite-collection/0.1.0'
        and result['status']=='CALLSITE_LOCATED_STOP_FOR_REVIEW'
        and result['result_sha256']==sha(target/'analyzed/sources.json'),'SOURCE_RESULT')
    return result


def stage(package,phase,reviewed=None,risk=False):
    package=Path(package).resolve();cfg=json.loads((package/'delivery.json').read_text(encoding='utf8'))
    sys.path.insert(0,cfg['code_root'])
    from scripts import memset_micro as common
    from scripts.memset_prefill_stage import verified_pack
    index=common.verify_package(package);require=common.require
    require(cfg['schema_version']=='memset-callsite-delivery/0.1.0' and phase in ('A','B')
        and cfg['execution_commit']==cfg['analysis_commit'] and cfg['model_process_budget']==cfg['profile_budget']==1,'DELIVERY')
    root=Path(cfg['server_root']);short=cfg['execution_commit'][:12];code=Path(cfg['code_root'])
    static=common.safe(root,'diagnostics/memset_callsite_'+short+'_static')
    out=static if phase=='A' else common.safe(root,'evidence/memset_callsite/'+short+'_once')
    archive=common.safe(root,'transfer/memset_callsite_'+short+('_static.zip' if phase=='A' else '_once.zip'))
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    if phase=='B':validate_b_opt_in(reviewed,risk);review_static(static,reviewed,cfg,index)
    out.mkdir(parents=True,exist_ok=False);status='BLOCKED';error=None;static_files={}
    for name in ('delivery.json','package_manifest.json','run_memset_callsite.ps1','memset_callsite_stage.py','prerequisite_reference.json'):
        shutil.copyfile(package/name,out/name)
    try:
        require(list(sys.version_info[:3])==[3,11,16],'CONTROLLER_PYTHON_VERSION')
        if phase=='A':common.deploy(cfg,package,out)
        common.tree(cfg,cfg['execution_commit'])
        common.write(out/'source_bytes.json',verify_sources(code,cfg['source_representations']))
        from scripts.coe_startup_storage import check
        temporary=[Path(os.environ['TEMP']),Path(os.environ['TMP'])]
        if os.environ.get('TMPDIR'):temporary.append(Path(os.environ['TMPDIR']))
        space=check(out,temporary,archive);common.write(out/'resources.json',space)
        require(space['status']=='STARTUP_RESOURCES_READY','STARTUP_RESOURCES_BLOCKED')
        capability(cfg,out)
        if phase=='A':
            env=os.environ.copy()
            for k in ('PYTEST_ADDOPTS','PYTEST_PLUGINS'):env.pop(k,None)
            env.update(CUDA_VISIBLE_DEVICES='-1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1')
            common.command([cfg['python'],'-X','utf8','-m','pytest','-q','-ra','-p','no:cacheprovider',*cfg['cpu_tests'],
                '--basetemp',str(root/'diagnostics'/('memset_callsite_'+short+'_cpu_tmp')),
                '--junitxml',str(out/'cpu.xml')],code,out/'cpu_changes',env=env,timeout=300)
            import xml.etree.ElementTree as ET
            suite=ET.parse(out/'cpu.xml').getroot().find('testsuite')
            require(int(suite.attrib['tests'])==cfg['cpu_test_count'] and all(suite.attrib[k]=='0' for k in ('failures','errors','skipped')),'CPU_RESULT')
            common.command([cfg['python'],'-X','utf8','-m','compileall','-q','exposedpath','analysis',
                'scripts/memset_callsite_stage.py','scripts/memset_callsite_collect.py'],code,out/'compile',env=env,timeout=120)
            static_files={n:common.sha(out/n) for n in ('source_bytes.json','resources.json','capability.json','cpu.xml','delivery.json')}
            status='STATIC_READY_FOR_REVIEW'
        else:
            shutil.copyfile(static/'receipt.json',out/'reviewed_static_receipt.json')
            collect(cfg,package,out);status='CALLSITE_LOCATED_STOP_FOR_REVIEW'
        verify_sources(code,cfg['source_representations']);common.tree(cfg,cfg['execution_commit'])
        require(common.sha(cfg['nsys'])==cfg['nsys_sha256'],'COLLECTOR_CHANGED_DURING_STAGE')
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    common.write(out/'receipt.json',dict(schema_version='memset-callsite-receipt/0.1.0',status=status,error=error,phase=phase,
        execution_commit=cfg['execution_commit'],analysis_commit=cfg['analysis_commit'],package_index_sha256=index,
        static_files=static_files,reviewed_static_receipt_sha256=reviewed,sampling_risk_accepted=risk,
        role='Engineering',model_process_budget=0 if phase=='A' else 1,profile_budget=0 if phase=='A' else 1,
        stage_a_cuda_initializations=0 if phase=='A' else None,automatic_retry=False,automatic_cleanup=False,
        historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000,
        parameter_evidence=False,a_admission='NOT_ASSESSED',coe_admission='NOT_ASSESSED',
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED'))
    try:print(json.dumps(verified_pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=('stage-a','stage-b'));p.add_argument('package',type=Path)
    p.add_argument('--reviewed-static-sha256');p.add_argument('--accept-reviewed-sampling-risk',action='store_true');a=p.parse_args(argv)
    return stage(a.package,'A' if a.action=='stage-a' else 'B',a.reviewed_static_sha256,a.accept_reviewed_sampling_risk)


if __name__=='__main__':raise SystemExit(main())
