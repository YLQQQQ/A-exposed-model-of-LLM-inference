"""Fixed Stage-A-only package. Uses official cached SDK bytes, no network or GPU."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='9c78e355bb43a8696f7eccb44c48d8448f366d09'
STATIC_SHA='d4ceeae555ec0f5b146821aba40133e2d7df6e6cc61aaeff1cbed3dcd5d96b4b'
OLD_MICRO_PACKAGE_SHA='bee9778d3d2759d0f748f640e5f3cbde8994030d943f389d159b812a6008c4f6'
CUPTI_ARCHIVE_SHA='6ad8df634d60e4bc96cf6914af71a5708f6460a25a39d0183780c6bdebfa60c7'
CUPTI_DLL_SHA='560a36596b6c6db6ecb44bbdc1b9d3bbf34965e919d13e7285f4d1c3542916ce'
SOURCES=['scripts/independent_cupti_stage.py','scripts/package_independent_cupti.py',
    'scripts/run_independent_cupti_a.ps1','scripts/memset_micro.py','scripts/coe_startup_storage.py',
    'analysis/independent_cupti_memset.py','tests/__init__.py',
    'tests/test_independent_cupti_memset.py','tests/test_independent_cupti_native.py',
    'tests/test_independent_cupti_delivery.py',
    *['scripts/native_cupti_memset/'+x for x in ('core.h','micro.cpp','host_test.cpp','host_client_test.cpp')]]


def build(output, sdk_parent, reference_static, old_micro_package, cpu_count):
    from scripts.memset_micro import sha,write,require,verify_package
    from scripts.package_memset_micro import make_sdk
    def git(*args):return subprocess.check_output(['git',*map(str,args)],cwd=ROOT)
    require(sha(reference_static)==STATIC_SHA and sha(old_micro_package)==OLD_MICRO_PACKAGE_SHA,'REFERENCE_ARCHIVES')
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(reference_static) as z:
        require(z.testzip() is None,'REFERENCE_CRC')
        rows=json.loads(z.read('artifact_manifest.json'))['files']
        require(len(z.namelist())==len(rows)+1,'REFERENCE_COVERAGE')
        for r in rows:
            data=z.read(r['path']);require(len(data)==r['bytes'] and hashlib.sha256(data).hexdigest()==r['sha256'],'REFERENCE_HASH')
        receipt=z.read('receipt.json');r=json.loads(receipt.decode('utf-8-sig'))
        require(r['execution_commit']==r['analysis_commit']==BASE and r['status']=='BLOCKED','PREREQUISITE')
        old_source=json.loads(z.read('delivery.json'));(out/'prerequisite_receipt.json').write_bytes(receipt)
    write(out/'prerequisite_reference.json',dict(archive=Path(reference_static).name,sha256=STATIC_SHA,
        receipt_sha256=sha(out/'prerequisite_receipt.json'),execution_commit=BASE,
        use='CHECKOUT_ONLY_OLD_BLOCKED_NOT_REWRITTEN'))
    with zipfile.ZipFile(old_micro_package) as z:
        require(z.testzip() is None,'TOOLCHAIN_REFERENCE_CRC')
        old=json.loads(z.read('delivery.json'))
        t=z.read('toolchain_reference.zip');require(hashlib.sha256(t).hexdigest()==old['toolchain_reference']['sha256'],'TOOLCHAIN_REFERENCE_HASH')
        (out/'toolchain_reference.zip').write_bytes(t)
    require(old['code_root']==old_source['code_root'] and old['python']==old_source['python'],'REFERENCE_ENVIRONMENT')
    target=git('rev-parse','HEAD').decode().strip();git('merge-base','--is-ancestor',BASE,target)
    sources={}
    for name in SOURCES:
        data=git('show',target+':'+name)
        choices=[dict(representation='EXACT_GIT_BLOB',bytes=len(data),sha256=hashlib.sha256(data).hexdigest())]
        if b'\r' not in data and b'\n' in data:
            alt=data.replace(b'\n',b'\r\n');choices.append(dict(representation='EXPLICIT_GIT_LF_TO_CRLF',bytes=len(alt),sha256=hashlib.sha256(alt).hexdigest()))
        actual=(ROOT/name).read_bytes();require(any(len(actual)==x['bytes'] and hashlib.sha256(actual).hexdigest()==x['sha256'] for x in choices),'UNCOMMITTED_SOURCE:'+name)
        sources[name]=choices
    for original,name in [('scripts/independent_cupti_stage.py','independent_cupti_stage.py'),
        ('scripts/memset_micro.py','micro_support.py'),('scripts/run_independent_cupti_a.ps1','run_independent_cupti_a.ps1')]:
        (out/name).write_bytes(git('show',target+':'+original))
    sdk_rows=make_sdk(out/'sdk.zip',sdk_parent)
    archive=Path(sdk_parent)/'cuda_cupti_12.4.127.zip';require(sha(archive)==CUPTI_ARCHIVE_SHA,'CUPTI_ARCHIVE_IDENTITY')
    cupti_rows=[];prefix='cuda_cupti-windows-x86_64-12.4.127-archive/'
    with zipfile.ZipFile(archive) as src,zipfile.ZipFile(out/'cupti.zip','x',zipfile.ZIP_DEFLATED) as dst:
        require(src.testzip() is None,'CUPTI_ARCHIVE_CRC')
        for entry in src.infolist():
            if entry.is_dir():continue
            require(entry.filename.startswith(prefix),'CUPTI_ARCHIVE_PREFIX')
            name=entry.filename[len(prefix):];data=src.read(entry)
            dst.writestr(name,data);cupti_rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    require(next(r['sha256'] for r in cupti_rows if r['path']=='lib/cupti64_2024.1.1.dll')==CUPTI_DLL_SHA,'CUPTI_DLL')
    write(out/'dependency_sources.json',dict(schema_version='independent-cupti-sdk/0.1.0',
        cupti_archive=dict(version='12.4.127',api=22,sha256=CUPTI_ARCHIVE_SHA,
            upstream='https://developer.download.nvidia.com/compute/cuda/redist/cuda_cupti/windows-x86_64/cuda_cupti-windows-x86_64-12.4.127-archive.zip'),
        cuda_headers='12.4.127',crt_headers='12.4.131',sdk_files=sdk_rows,cupti_files=cupti_rows,
        toolchain_reference=dict(archive=Path(old_micro_package).name,sha256=OLD_MICRO_PACKAGE_SHA,
            scope='EXISTING_MSVC_AND_SDK_IDENTITY_ONLY_NOT_CUPTI_QUALIFICATION')))
    bundle=out/'execution.bundle';git('bundle','create',bundle,'HEAD','^'+BASE);git('bundle','verify',bundle)
    cfg={k:old[k] for k in ('server_root','code_root','python','python_version','git','toolchain_files','build','runtime_path','gpu_uuid','gpu_pci')}
    cfg.update(schema_version='independent-cupti-stage-a/0.1.0',execution_commit=target,analysis_commit=target,
        prerequisite=BASE,source_representations=sources,default_stage='A_ONLY_NO_B_ENTRY',
        micro_process_budget=0,model_process_budget=0,profile_budget=0,
        future_micro_plan=dict(counts=[0,64],initial_byte=58,value=123,micro_processes=1,
            timeout_seconds=120,nsight_profiles=0,run_role='ENGINEERING_PARAMETER_DIAGNOSTIC',
            B_authorized=False,model_coverage='NOT_ASSESSED',A_COE_admission='NOT_ASSESSED'),
        cpu_test_count=cpu_count,sdk_files=sdk_rows,cupti_files=cupti_rows,cupti_dll_sha256=CUPTI_DLL_SHA,
        bootstrap_sha256=sha(out/'independent_cupti_stage.py'),support_sha256=sha(out/'micro_support.py'),
        automatic_retry=False,automatic_cleanup=False,temporary_required_bytes=2**31,
        historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000)
    write(out/'delivery.json',cfg)
    (out/'README.txt').write_text('Stage A only: deploy, build/link real CUDA12.4/CUPTI API22 headers, Host-only doubles.\n'
        'No Nsight, Torch, CUDA initialization or GPU binary execution. No B switch is shipped.\n'
        'Return the static ZIP. New A evidence review is mandatory before any GPU command.\n',encoding='utf8')
    rows=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir())]
    write(out/'package_manifest.json',dict(schema_version='independent-cupti-package/0.1.0',files=rows))
    verify_package(out);result=out.with_suffix('.zip')
    with zipfile.ZipFile(result,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(result) as z:
        require(z.testzip() is None and set(z.namelist())=={r['path'] for r in rows}|{'package_manifest.json'},'FINAL_ZIP')
        for r in rows:require(hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256'],'FINAL_HASH')
    return dict(commit=target,zip=str(result),bytes=result.stat().st_size,sha256=sha(result),
        launcher_sha256=sha(out/'run_independent_cupti_a.ps1'),manifest_sha256=sha(out/'package_manifest.json'),
        stage_a_return=str(Path(cfg['server_root'])/'transfer'/('independent_cupti_'+target[:12]+'_static.zip')))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('output','sdk-parent','reference-static','old-micro-package'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--cpu-count',type=int,required=True);a=p.parse_args()
    print(json.dumps(build(a.output,a.sdk_parent,a.reference_static,a.old_micro_package,a.cpu_count),indent=2))


if __name__=='__main__':main()
