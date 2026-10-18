"""Package one source diagnostic from an actual commit and sealed references."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='4da800d2e8d270fdc2e25e07ab3511a73066df46'
DELIVERY_SHA='70b2083420dd9c3f6947353ddee466b3e14eb9396520f7bc801e02a260bdc483'
STATIC_SHA='6a94503a3dd3601608c32637d056bc7c3ad2e26ceb444519282ac3d34ba7e922'
CPU_TESTS=['tests/test_memset_callsite.py','tests/test_memset_callsite_delivery.py']


def build(output,reference_delivery,reference_static,cpu_count):
    from scripts.memset_micro import sha,write,require,verify_package
    from exposedpath import memset_callsite as c
    def git(*args):return subprocess.check_output(['git',*map(str,args)],cwd=ROOT)
    require(sha(reference_delivery)==DELIVERY_SHA and sha(reference_static)==STATIC_SHA,'REFERENCE_ARCHIVES')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(reference_delivery) as z:
        require(z.testzip() is None,'REFERENCE_CRC')
        old=json.loads(z.read('delivery.json'))
        for original,new in [('model_sha256.csv','model_inventory.csv'),('prospective_inputs/input_1024.json','input_1024.json')]:
            (out/new).write_bytes(z.read(original))
    with zipfile.ZipFile(reference_static) as z:
        require(z.testzip() is None,'STATIC_CRC');data=z.read('receipt.json');r=json.loads(data.decode('utf-8-sig'))
        require(r['execution_commit']==r['analysis_commit']==BASE and r['status']=='STATIC_READY_FOR_REVIEW'
            and r['error'] is None,'PREREQUISITE')
        require(z.read('delivery.json')==json.dumps(old,indent=2).encode() or json.loads(z.read('delivery.json'))==old,'REFERENCE_CONFIG')
        (out/'prerequisite_receipt.json').write_bytes(data)
    require(sha(out/'model_inventory.csv')==old['inventory_sha256']
        and sha(out/'input_1024.json')==old['input_bindings']['1024']['file_sha256'],'MODEL_INPUT_REFERENCE')
    target=git('rev-parse','HEAD').decode().strip();git('merge-base','--is-ancestor',BASE,target)
    sources={}
    paths=git('ls-tree','-r','--name-only',target).decode().splitlines()
    for name in paths:
        if not name.startswith(('exposedpath/','exposedpath_v141/','analysis/','scripts/','tests/')) or not name.endswith(('.py','.json','.ps1')):continue
        data=git('show',target+':'+name);variants=[dict(representation='EXACT_GIT_BLOB',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())]
        if b'\r' not in data and b'\n' in data:
            crlf=data.replace(b'\n',b'\r\n');variants.append(dict(representation='EXPLICIT_GIT_LF_TO_CRLF',bytes=len(crlf),sha256=hashlib.sha256(crlf).hexdigest()))
        actual=(ROOT/name).read_bytes();require(any(len(actual)==r['bytes'] and hashlib.sha256(actual).hexdigest()==r['sha256'] for r in variants),'UNCOMMITTED_SOURCE:'+name)
        sources[name]=variants
    for name in ('memset_callsite_stage.py','run_memset_callsite.ps1'):
        (out/name).write_bytes(git('show',target+':scripts/'+name))
    (out/'diagnostic_plan.md').write_bytes(git('show',target+':docs/v1_4_1/memset_parameter_feasibility_v0_1.md'))
    bundle=out/'execution.bundle';git('bundle','create',bundle,'HEAD','^'+BASE);git('bundle','verify',bundle)
    write(out/'prerequisite_reference.json',dict(archive=Path(reference_static).name,archive_sha256=STATIC_SHA,
        receipt_sha256=sha(out/'prerequisite_receipt.json'),execution_commit=BASE,
        use='CHECKOUT_IDENTITY_ONLY_NOT_NEW_DIAGNOSTIC_QUALIFICATION'))
    cfg={k:old[k] for k in ('server_root','code_root','target_python','site_root','model','nsys','nsys_sha256','gpu_uuid','gpu_pci_bus_id','inventory_sha256')}
    # Read-only discovery of Git occurs at the target; its path/hash is saved by
    # A. No VS, CUDA compiler, runtime injection or dependency install is needed.
    cfg.update(schema_version='memset-callsite-delivery/0.1.0',execution_commit=target,analysis_commit=target,
        prerequisite=BASE,python=str(Path(old['code_root'])/'.venv/Scripts/python.exe'),git='git',
        run_id='memset-source-'+target[:12],model_process_budget=1,profile_budget=1,role='Engineering',
        input_sha256=sha(out/'input_1024.json'),input_identity=old['input_bindings']['1024']['identity'],
        source_representations=sources,bootstrap_sha256=sha(out/'memset_callsite_stage.py'),
        cpu_tests=CPU_TESTS,cpu_test_count=cpu_count,profile_flags=list(c.PROFILE_FLAGS),
        automatic_retry=False,automatic_cleanup=False,temporary_required_bytes=12*2**30,
        estimated_minutes=[5,10],estimated_retained_gib=[0.5,2],profile_timeout_seconds=300,
        per_run_driver_timeout_seconds=900,historical_ylq_total_bytes=None,
        long_term_target_exclusive_bytes=50000000000,default_stage='A_CPU_ONLY',
        stage_b_requires=['NEW_STATIC_RECEIPT_HASH','EXPLICIT_COLLECTION_SWITCH','EXPLICIT_SAMPLING_RISK_ACCEPTANCE'])
    require(cfg['input_identity']==c.validate_input(json.loads((out/'input_1024.json').read_text()),
        dict(model_type='qwen2',vocab_size=151936,max_position_embeddings=32768)),'INPUT_MATRIX')
    write(out/'delivery.json',cfg)
    files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir())]
    write(out/'package_manifest.json',dict(schema_version='memset-callsite-package/0.1.0',files=files))
    verify_package(out);archive=out.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None and len(z.namelist())==len(files)+1,'ZIP_CRC_COVERAGE')
        for f in files:require(hashlib.sha256(z.read(f['path'])).hexdigest()==f['sha256'],'ZIP_CONTENT')
    return dict(commit=target,prerequisite=BASE,zip=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),
        launcher_sha256=sha(out/'run_memset_callsite.ps1'),manifest_sha256=sha(out/'package_manifest.json'),
        static_return=str(Path(cfg['server_root'])/'transfer'/('memset_callsite_'+target[:12]+'_static.zip')))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('output','reference-delivery','reference-static'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--cpu-count',type=int,required=True);a=p.parse_args()
    print(json.dumps(build(a.output,a.reference_delivery,a.reference_static,a.cpu_count),indent=2))
