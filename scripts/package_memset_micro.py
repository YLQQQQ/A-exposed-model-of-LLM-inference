"""Create one fixed, two-stage *micro-only* delivery from committed sources."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='d6957deeb588cc125bf386d8ae07620ea35e14e3'
DETOURS='e4bfd6b03e50de46b47abfbd1e46b384f0c5f833'
NVTX='bc282655dadb9288505f419c5b79d2ed3f1b4dfd'
DEP_HASH={'detours':'fef0b17c5c3c9356fb8ba7366a3b196149daadd131fb6a92abeda1cb4d3b9b85',
          'nvtx':'7a6b540fce926ec02a032d743397d472d071abcbe6c4a98b2ec247d8e332ffcf'}
SOURCES=['analysis/memset_same_capture.py','scripts/memset_micro.py','scripts/run_memset_micro.ps1',
    'scripts/package_memset_micro.py','scripts/coe_startup_storage.py',
    'tests/test_memset_same_capture.py','tests/test_memset_micro_delivery.py','tests/test_memset_micro_native.py',
    *['scripts/native_memset_probe/'+p for p in ('recorder.h','recorder.cpp','host_target.cpp','host_test.cpp','micro.cpp')]]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
def git(*a):return subprocess.check_output(['git',*map(str,a)],cwd=ROOT)


def make_sdk(output,sdk_parent):
    sdk_parent=Path(sdk_parent)
    components=[('cuda_cudart_12.4.127.zip','6a1c32e68ee1a95ca17334691ff9ad1ffe7f352c24a083d55e4c96b8063b2bcb',
        'cuda_cudart-windows-x86_64-12.4.127-archive/include/','include',sdk_parent/'cuda_cudart'),
        ('cuda_nvcc_12.4.131.zip','3b14cf8dd9dda4a3b1a9682270d46eef775f018e17650187a8a448a06111f2b8',
        'cuda_nvcc-windows-x86_64-12.4.131-archive/include/crt/','include/crt',sdk_parent/'cuda_nvcc')]
    seen=set();members=[]
    with zipfile.ZipFile(output,'x',zipfile.ZIP_DEFLATED) as z:
        for archive,expected,prefix,dest,local in components:
            assert sha(sdk_parent/archive)==expected
            with zipfile.ZipFile(sdk_parent/archive) as src:
                for r in src.infolist():
                    if r.is_dir() or not r.filename.startswith(prefix):continue
                    data=src.read(r);name=dest+'/'+r.filename[len(prefix):]
                    assert name.casefold() not in seen;seen.add(name.casefold())
                    assert (local/r.filename).read_bytes()==data # compiled local headers equal the pinned source archive
                    z.writestr(name,data);members.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    return members


def build(output,deps,sdk_parent,previous_delivery,toolchain_reference):
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    prior=Path(previous_delivery)
    assert sha(prior)=='3f4b6bd63b6ced66612f462b8344106a7d060418255ae8c936609238fd34a10f'
    with zipfile.ZipFile(prior) as z:
        receipt_bytes=z.read('receipt.json');delivery_bytes=z.read('delivery.json')
        previous=json.loads(receipt_bytes.decode('utf-8-sig'))
        assert previous['execution_commit']==previous['analysis_commit']==BASE
        assert hashlib.sha256(delivery_bytes).hexdigest()==previous['delivery_sha256']
        old=json.loads(delivery_bytes.decode('utf-8-sig'))
    write(out/'prerequisite_reference.json',dict(archive=prior.name,archive_sha256=sha(prior),
        execution_commit=BASE,receipt_sha256=hashlib.sha256(receipt_bytes).hexdigest(),
        delivery_sha256=hashlib.sha256(delivery_bytes).hexdigest(),status='BLOCKED_UNCHANGED',
        reuse_scope='EXECUTION_ENVIRONMENT_IDENTIFIERS_ONLY_NOT_FAILED_PILOT_QUALIFICATION'))
    (out/'prerequisite_receipt.json').write_bytes(receipt_bytes)
    (out/'prerequisite_delivery.json').write_bytes(delivery_bytes)
    assert old['commit']==BASE and old['nsys_sha256']=='b26707e479540314ebe4931b687b149c6a2d8a86eb6075a0c98169befc6e7417'
    target=git('rev-parse','HEAD').decode().strip();git('merge-base','--is-ancestor',BASE,target)
    assert not git('diff',BASE,target,'--','exposedpath','exposedpath_v141','analysis/coe_candidate.py','analysis/coe_pilot.py')
    rows=[]
    for relative in SOURCES:
        data=git('show',target+':'+relative)
        assert data==(ROOT/relative).read_bytes(),relative
        rows.append(dict(path=relative,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    for relative,name in [('scripts/memset_micro.py','memset_micro.py'),('scripts/run_memset_micro.ps1','run_memset_micro.ps1')]:
        (out/name).write_bytes(git('show',target+':'+relative))
    provenance={}
    for name,file,commit in [('detours','detours_e4bfd6b.zip',DETOURS),('nvtx','nvtx_bc282655.zip',NVTX)]:
        p=Path(deps)/file;assert sha(p)==DEP_HASH[name]
        shutil.copyfile(p,out/(name+'.zip'))
        provenance[name]=dict(commit=commit,sha256=sha(p),upstream='https://github.com/'+('microsoft/Detours' if name=='detours' else 'NVIDIA/NVTX'))
    provenance['sdk_headers']=dict(cuda_cudart='12.4.127',cuda_nvcc_crt='12.4.131',
        source_archives=['6a1c32e68ee1a95ca17334691ff9ad1ffe7f352c24a083d55e4c96b8063b2bcb',
                         '3b14cf8dd9dda4a3b1a9682270d46eef775f018e17650187a8a448a06111f2b8'],
        files=make_sdk(out/'sdk.zip',sdk_parent))
    write(out/'dependency_sources.json',provenance)
    write(out/'nsys_schema_reference.json',dict(source='TARGET_SAVED_NSIGHT_2026.2_ANALYSIS_GUIDE',
        sha256='bdcf574189e7eb687d4dc7c52bcebacae9c700c5a93a9e3aed8ff674960cbb11',
        upstream='https://archive.docs.nvidia.com/nsight-systems/2026.2/AnalysisGuide/index.html',
        correlation='MEMSET.correlationId REFERENCES CUPTI_ACTIVITY_KIND_RUNTIME(correlationId)',
        runtime_event_class=0,driver_event_class=1,nvtx_push_pop_event_type=59,
        not_native_cupti_driver_id_reinterpretation=True))
    with zipfile.ZipFile(toolchain_reference) as z:
        assert z.testzip() is None
        manifest=json.loads(z.read('artifact_manifest.json').decode('utf-8-sig'))
        for r in manifest['files']:
            data=z.read(r['path']);assert len(data)==r['size_bytes'] and hashlib.sha256(data).hexdigest()==r['sha256']
        t=json.loads(z.read('toolchain.json').decode('utf-8-sig'))
        tc=json.loads(z.read('config.json').decode('utf-8-sig'))
    facts={}
    for name in ('cl','link','lib','windows_h','kernel32_lib','msvcprt_lib'):
        v=t['files'][name];facts[name]=dict(path=v['path'],bytes=v['size_bytes'],sha256=v['sha256'])
    bundle=out/'execution.bundle';git('bundle','create',bundle,'HEAD','^'+BASE)
    (out/'bundle_verify.txt').write_bytes(git('bundle','verify',bundle))
    pci=old['gpu_pci_bus_id'].split(':');gpu_pci=f'{int(pci[0],16):04x}:{int(pci[1],16):02x}:'+pci[2].lower()
    config=dict(schema_version='memset-micro-delivery/0.1.0',execution_commit=target,analysis_commit=target,
        prerequisite=BASE,server_root=old['server_root'],code_root=old['code_root'],python=tc['test_python'],
        python_version=[3,11,16],git=tc['git'],toolchain_files=facts,
        build=dict(vc_root=str(Path(tc['vs_root'])/'VC/Tools/MSVC/14.38.33130'),
                   sdk_root=tc['sdk_root'],sdk_version='10.0.20348.0'),
        runtime_path=str(Path(old['site_root'])/'torch/lib/cudart64_12.dll'),
        runtime_identity_policy='OBSERVE_PE_VERSION_AND_BYTES_IN_A_BIND_EXACT_REVIEWED_A_IN_B_NOT_SELF_CERTIFIED',
        nsys=old['nsys'],nsys_sha256=old['nsys_sha256'],gpu_uuid=old['gpu_uuid'],gpu_pci=gpu_pci,
        run_id=uuid.uuid4().hex,detours_directory='Detours-'+DETOURS,nvtx_directory='NVTX-'+NVTX,
        micro_process_budget=1,profile_budget=1,model_process_budget=0,timeout_seconds=120,
        temporary_bytes=268435456,long_term_target_exclusive_bytes=50000000000,historical_ylq_total_bytes=None,
        automatic_retry=False,automatic_cleanup=False,sources=rows,bootstrap_sha256=sha(out/'memset_micro.py'),
        toolchain_reference=dict(file=Path(toolchain_reference).name,sha256=sha(toolchain_reference)),
        deployment_role='DEFAULT_A_BUILD_CPU_ONLY_B_REQUIRES_EXPLICIT_SWITCH_AND_REVIEWED_A_SHA')
    shutil.copyfile(toolchain_reference,out/'toolchain_reference.zip')
    write(out/'delivery.json',config)
    (out/'README.txt').write_text('A: run_memset_micro.ps1 (default): deploy, compile/link, CPU Host substitutes only.\n'
        'B: only after A receipt review: -CollectReviewedMicro -ReviewedStaticReceiptSHA256 <actual-reviewed-sha>.\n'
        'One native process / one profile / no model / no automatic retry. No old Pilot resumption.\n',encoding='utf8')
    files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir())]
    write(out/'package_manifest.json',dict(schema_version='memset-micro-package/0.1.0',files=files))
    from scripts.memset_micro import verify_package
    verify_package(out)
    archive=out.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        assert {v['path'] for v in files}|{'package_manifest.json'}==set(z.namelist())
        for r in files:assert hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256']
    return dict(commit=target,zip=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),
        launcher_sha256=sha(out/'run_memset_micro.ps1'),manifest_sha256=sha(out/'package_manifest.json'),
        stage_a_return=str(Path(old['server_root'])/'transfer'/('memset_micro_'+target[:12]+'_static.zip')),
        stage_b_return=str(Path(old['server_root'])/'transfer'/('memset_micro_'+target[:12]+'_once.zip')))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('output','deps','sdk-parent','previous-delivery','toolchain-reference'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();print(json.dumps(build(a.output,a.deps,a.sdk_parent,a.previous_delivery,a.toolchain_reference),indent=2))


if __name__=='__main__':main()
