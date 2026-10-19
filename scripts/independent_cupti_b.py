"""One reviewed standalone CUPTI micro. No deploy, build, Nsight or model action."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import runpy
import shutil
import stat
import sys

NATIVE_COMMIT='cedd70610588d4d5691c5a86cbcb923ef8ea6433'
A_RECEIPT_SHA='67f02b575aa4ce37cdcdc9c861e1149a1e960d5d33b730d9983a541ae7877fb0'


def require(ok,reason):
    if not ok:raise ValueError('CUPTI_B_'+reason)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()


def package_index(package):
    # Verify before importing even the previously-reviewed Python helpers.
    for p in (package,*package.parents):
        s=p.lstat();require(not stat.S_ISLNK(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'PACKAGE_REPARSE')
    rows=json.loads((package/'package_manifest.json').read_text(encoding='utf8'))['files'];seen=set()
    for r in rows:
        name=r['path'];require(name and name not in ('.','..') and not any(c in name for c in '/\\:'),'PACKAGE_PATH')
        require(name.casefold() not in seen,'PACKAGE_DUPLICATE');seen.add(name.casefold())
        p=package/name;s=p.lstat()
        require(stat.S_ISREG(s.st_mode) and not getattr(s,'st_file_attributes',0)&0x400,'PACKAGE_REPARSE')
        require(s.st_size==r['bytes'] and sha(p)==r['sha256'],'FILE_HASH:'+name)
    require(rows and {p.name for p in package.iterdir()}=={r['path'] for r in rows}|{'package_manifest.json'},'PACKAGE_COVERAGE')
    return sha(package/'package_manifest.json')


def components(package):
    previous=sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode=True
        ns=runpy.run_path(str(Path(package)/'reviewed_stage.py'));return ns,ns['support']()
    finally:sys.dont_write_bytecode=previous


def checked_a(cfg,stage,m):
    root=Path(cfg['a_root'])
    require(sha(root/'receipt.json')==cfg['reviewed_a_receipt_sha256'],'A_RECEIPT_HASH')
    require(sha(root/'artifact_manifest.json')==cfg['a_manifest_sha256'],'A_MANIFEST_HASH')
    receipt=json.loads((root/'receipt.json').read_text(encoding='utf8'))
    require(receipt.get('schema_version')=='independent-cupti-stage-a-receipt/0.1.0' and
        receipt.get('phase')=='A' and receipt.get('status')=='STATIC_READY_FOR_REVIEW' and
        receipt.get('error') is None and receipt.get('stage_a_cuda_programs_executed')==0 and
        receipt.get('execution_commit')==receipt.get('analysis_commit')==NATIVE_COMMIT,'A_RECEIPT')
    rows=json.loads((root/'artifact_manifest.json').read_text(encoding='utf8'))['files']
    try:m.verify_rows(root,rows)
    except ValueError as exc:raise ValueError('CUPTI_B_A_FILE_HASH:'+str(exc)) from exc
    acfg=json.loads((root/'delivery.json').read_text(encoding='utf8'))
    require(acfg['execution_commit']==acfg['analysis_commit']==NATIVE_COMMIT,'A_VERSION')
    require(cfg['gpu_uuid']==acfg['gpu_uuid'] and re.fullmatch(r'GPU-[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}',cfg['gpu_uuid']),
        'GPU_IDENTITY')
    require(cfg['python']==acfg['python'] and cfg['python_version']==acfg['python_version'] and
        list(sys.version_info[:3])==cfg['python_version'] and Path(sys.executable)==Path(cfg['python']),'PYTHON_VERSION')
    m.tree(acfg,NATIVE_COMMIT)
    source_rows=json.loads((root/'source_bytes.json').read_text(encoding='utf8'))
    require({r['path'] for r in source_rows}==set(acfg['source_representations']),'A_SOURCE_COVERAGE')
    m.verify_rows(acfg['code_root'],source_rows)
    stage['bind_checkout_modules'](acfg)
    require(sha(root/'build/build.json')==cfg['build_sha256'],'BUILD_HASH')
    built=json.loads((root/'build/build.json').read_text(encoding='utf8'))
    require(built['micro_invoked'] is False and built['cuda_header_version']==12040 and built['cupti_header_version']==22,'BUILD_VERSION')
    micro=m.safe(root,'build/micro.exe');require(Path(built['micro'])==micro,'MICRO_PATH')
    require(cfg['micro_binary'] in built['binary_files'],'MICRO_BINDING')
    m.verify_rows(root/'build',built['binary_files'])
    runtime=json.loads((root/'runtime_file.json').read_text(encoding='utf8'))
    cupti=json.loads((root/'cupti_file.json').read_text(encoding='utf8'))
    require(runtime['path']==acfg['runtime_path'] and runtime['sha256']==cfg['runtime_sha256'] and
        runtime['file_version']=='6.14.11.12040' and sha(runtime['path'])==cfg['runtime_sha256'] and
        Path(runtime['path']).stat().st_size==runtime['bytes'],'RUNTIME_CHANGED')
    require(cupti['sha256']==cfg['cupti_sha256'] and sha(cupti['path'])==cfg['cupti_sha256'] and
        Path(cupti['path']).is_relative_to(root) and Path(cupti['path']).stat().st_size==cupti['bytes'],'CUPTI_CHANGED')
    return dict(a_root=root,acfg=acfg,micro=micro,runtime=runtime,cupti=cupti,source_rows=source_rows)


def execute_micro(m,argv,out,env):
    out=Path(out)
    return m.command(argv,out,out/'micro',env=env,timeout=120)


def reader(ctx):
    p=Path(ctx['acfg']['code_root'])/'analysis/independent_cupti_memset.py'
    spec=importlib.util.spec_from_file_location('_reviewed_independent_cupti_reader',p)
    result=importlib.util.module_from_spec(spec);previous=sys.dont_write_bytecode
    try:sys.dont_write_bytecode=True;spec.loader.exec_module(result)
    finally:sys.dont_write_bytecode=previous
    return result


def run(package,*,reviewed,enabled=False):
    package=Path(package).absolute();index=package_index(package)
    cfg=json.loads((package/'delivery.json').read_text(encoding='utf8'))
    require(enabled is True and reviewed==cfg['reviewed_a_receipt_sha256']==A_RECEIPT_SHA,'EXPLICIT_REVIEWED_B')
    require(cfg['schema_version']=='independent-cupti-stage-b/0.1.0' and
        cfg['native_commit']==cfg['analysis_commit']==NATIVE_COMMIT and
        re.fullmatch('[0-9a-f]{40}',cfg['controller_commit']) and cfg['timeout_seconds']==120 and
        cfg['micro_process_budget']==1 and cfg['profile_budget']==cfg['model_process_budget']==0 and
        cfg['temporary_required_bytes']==2**31,'B_CONTRACT')
    stage,m=components(package);m.verify_rows(package,cfg['helper_files'])
    root=Path(cfg['server_root']);tag=cfg['controller_commit'][:12]
    out=m.safe(root,'diagnostics/independent_cupti_'+tag+'_b_once')
    archive=m.safe(root,'transfer/independent_cupti_'+tag+'_b_once.zip')
    require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    out.mkdir(parents=True,exist_ok=False);archive.parent.mkdir(parents=True,exist_ok=True)
    for name in ('delivery.json','package_manifest.json'):
        shutil.copyfile(package/name,out/name)
    status='BLOCKED';error=None;process=None
    try:
        ctx=checked_a(cfg,stage,m)
        for src,dst in [('receipt.json','reviewed_a_receipt.json'),('artifact_manifest.json','reviewed_a_manifest.json'),
                        ('build/build.json','reviewed_build.json'),('runtime_file.json','reviewed_runtime.json'),
                        ('cupti_file.json','reviewed_cupti.json'),('source_bytes.json','reviewed_source_bytes.json')]:
            shutil.copyfile(ctx['a_root']/src,out/dst)
        m.write(out/'resources.json',stage['startup_resources'](out,archive,cfg))
        env=os.environ.copy()
        forbidden=('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH')
        require(not any(env.get(k) for k in forbidden),'EXTERNAL_PROFILER_ENVIRONMENT')
        env.update(CUDA_VISIBLE_DEVICES=cfg['gpu_uuid'],CUDA_DEVICE_ORDER='PCI_BUS_ID')
        m.write(out/'device_selection.json',dict(method='CUDA_VISIBLE_DEVICES_FULL_UUID',gpu_uuid=cfg['gpu_uuid'],
            visible_devices=env['CUDA_VISIBLE_DEVICES'],device_order=env['CUDA_DEVICE_ORDER'],native_local_ordinal=0,
            native_uuid_query_added=False,nsight_profiles=0,model_processes=0))
        run_id='cupti_'+tag+'_b_once';raw=out/'raw.json'
        argv=[str(ctx['micro']),'--run-reviewed-gpu-micro',ctx['runtime']['path'],ctx['cupti']['path'],
            run_id,str(raw),cfg['runtime_sha256'],cfg['cupti_sha256']]
        m.write(out/'execution_plan.json',dict(argv=argv,timeout_seconds=120,micro_process_budget=1,
            counts=[0,64],initial_byte=58,value=123,automatic_retry=False))
        process=execute_micro(m,argv,out,env)
        require(process.get('status')=='EXITED' and process.get('exit_code')==0 and
            process.get('timed_out') is False,'PROCESS_EXIT')
        v=json.loads(raw.read_text(encoding='utf8'))
        require(v.get('source')=='TARGET_GPU' and v.get('pid')==process.get('pid'),'PROCESS_IDENTITY')
        require(Path(v.get('runtime_loaded_path',''))==Path(ctx['runtime']['path']) and
            Path(v.get('cupti_loaded_path',''))==Path(ctx['cupti']['path']),'LOADED_LIBRARY_PATH')
        expected=dict(run_id=run_id,runtime_sha256=cfg['runtime_sha256'],cupti_sha256=cfg['cupti_sha256'])
        reader(ctx).review_file(raw,out/'derived',expected=expected)
        # No mutation of the reviewed A tree, checkout, binary or libraries.
        checked_a(cfg,stage,m)
        status='MICRO_EVIDENCE_COMPLETE_PENDING_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    m.write(out/'receipt.json',dict(schema_version='independent-cupti-stage-b-receipt/0.1.0',phase='B',status=status,error=error,
        controller_commit=cfg['controller_commit'],native_commit=NATIVE_COMMIT,analysis_commit=NATIVE_COMMIT,
        reviewed_a_receipt_sha256=reviewed,package_index_sha256=index,role='ENGINEERING_PARAMETER_DIAGNOSTIC',
        process=process,micro_process_budget=1,model_process_budget=0,profile_budget=0,timeout_seconds=120,
        automatic_retry=False,automatic_cleanup=False,pytorch_coverage='NOT_ASSESSED',A_COE_admission='NOT_ASSESSED',
        zero_byte_dependency_qualification='NOT_ASSESSED',old_instance_repair=False,
        historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000))
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:
        print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--package',required=True,type=Path)
    p.add_argument('--reviewed-a-receipt-sha256',required=True)
    p.add_argument('--run-reviewed-b',action='store_true');a=p.parse_args(argv)
    return run(a.package,reviewed=a.reviewed_a_receipt_sha256,enabled=a.run_reviewed_b)


if __name__=='__main__':raise SystemExit(main())
