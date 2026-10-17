"""Fixed incremental one-B2 diagnostic delivery; no collection occurs here."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import uuid
import zipfile

ROOT=Path(__file__).resolve().parents[1]
BASE='002f3ae9fcc22f04356dbd22092dcddd8c63a460'
MICRO_DELIVERY_SHA='bee9778d3d2759d0f748f640e5f3cbde8994030d943f389d159b812a6008c4f6'
MICRO_ONCE_SHA='29e4413ad7c2895d261718c54fd301266c01a94e647fe2d265475865f22ab3b8'
OLD_BATCH_SHA='3f4b6bd63b6ced66612f462b8344106a7d060418255ae8c936609238fd34a10f'
CPU_TESTS=['tests/test_memset_prefill.py','tests/test_memset_prefill_native.py',
    'tests/test_memset_prefill_entry.py','tests/test_memset_prefill_files.py','tests/test_memset_prefill_delivery.py']
SOURCES=['analysis/memset_prefill.py','exposedpath/memset_prefill.py','exposedpath/batch_load.py',
    'exposedpath/gate8_diagnostic.py','exposedpath/runner.py','exposedpath_v141/gate8_target_python.py',
    'scripts/gate7_smoke_validation.py','scripts/gate8_diagnostic_collect.py','scripts/memset_micro.py',
    'analysis/memset_same_capture.py','scripts/coe_startup_storage.py','scripts/native_memset_probe/recorder.h',
    'scripts/native_memset_probe/recorder.cpp','scripts/native_memset_probe/micro.cpp',
    'scripts/native_memset_probe/host_target.cpp','scripts/native_memset_probe/host_test.cpp',
    'scripts/native_memset_probe/prefill_recorder.cpp','scripts/native_memset_probe/prefill_host_test.cpp',
    'scripts/memset_prefill_stage.py','scripts/memset_prefill_native.py','scripts/run_memset_prefill.ps1',
    'scripts/package_memset_prefill.py','tests/test_n1_model_domain.py',*CPU_TESTS]


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
def git(*args):return subprocess.check_output(['git',*map(str,args)],cwd=ROOT)


def build(output,micro_delivery,micro_once,old_batch,cpu_count):
    from scripts.memset_micro import verify_package
    out=Path(output);out.mkdir(parents=True,exist_ok=False)
    for p,h in ((micro_delivery,MICRO_DELIVERY_SHA),(micro_once,MICRO_ONCE_SHA),(old_batch,OLD_BATCH_SHA)):
        if sha(p)!=h:raise ValueError('REFERENCE_ARCHIVE_IDENTITY:'+str(p))
    with zipfile.ZipFile(micro_delivery) as z:
        old=json.loads(z.read('delivery.json'));previous=json.loads(z.read('prerequisite_delivery.json'))
        for n in ('detours.zip','nvtx.zip','sdk.zip','dependency_sources.json','toolchain_reference.zip'):
            (out/n).write_bytes(z.read(n))
        old_index=json.loads(z.read('package_manifest.json'))
        for r in old_index['files']:
            data=z.read(r['path'])
            if len(data)!=r['bytes'] or hashlib.sha256(data).hexdigest()!=r['sha256']:raise ValueError('OLD_PACKAGE_INDEX')
    with zipfile.ZipFile(micro_once) as z:
        r=z.read('receipt.json');receipt=json.loads(r.decode('utf-8-sig'))
        if receipt['execution_commit']!=BASE or receipt['analysis_commit']!=BASE:raise ValueError('PREREQUISITE')
        (out/'prerequisite_receipt.json').write_bytes(r)
    # This original BLOCKED receipt establishes checkout identity, not a new
    # experiment PASS. The offline NVTX adjudication remains separate/history.
    write(out/'prerequisite_reference.json',dict(archive=Path(micro_once).name,archive_sha256=MICRO_ONCE_SHA,
        receipt_sha256=hashlib.sha256(r).hexdigest(),execution_commit=BASE,original_status=receipt['status'],
        reuse='CHECKOUT_AND_ENVIRONMENT_ONLY_MICRO_PASS_NOT_MODEL_COVERAGE'))
    with zipfile.ZipFile(old_batch) as z:
        names=[n for n in z.namelist() if '-B1-pass1/prepared/model_inventory.csv' in n]
        if len(names)!=1:raise ValueError('REFERENCE_INVENTORY')
        (out/'model_inventory.csv').write_bytes(z.read(names[0]))
        (out/'input_b1.json').write_bytes(z.read('experiment/inputs/input_b1.json'))
        manifest_member=names[0].rsplit('/',1)[0]+'/manifest.json';mf=json.loads(z.read(manifest_member))
        declared_input=json.loads((out/'input_b1.json').read_text())
        if sha(out/'input_b1.json')!=mf['prompt_tokens_sha256'] or declared_input['construction']['source_sha256']!=previous['prompt_512_sha256']:
            raise ValueError('BATCH_INPUT_LINEAGE')
        write(out/'input_reference.json',dict(archive_sha256=OLD_BATCH_SHA,input_member='experiment/inputs/input_b1.json',
            input_member_sha256=sha(out/'input_b1.json'),manifest_member=manifest_member,
            manifest_member_sha256=hashlib.sha256(z.read(manifest_member)).hexdigest(),
            source_seed_sha256=previous['prompt_512_sha256'],role='SEALED_INPUT_CONTENT_ONLY_NOT_NEW_QUALIFICATION'))
        token_members=[n for n in z.namelist() if '-B2-pass1/collection/diagnostic/pilot_tokens.json' in n]
        if len(token_members)!=1:raise ValueError('TOKEN_REFERENCE_MEMBER')
        token_member=token_members[0]
        token_data=json.loads(z.read(token_member));prefix=token_member.rsplit('/',1)[0]
        prior_mf=z.read(prefix+'/manifest.json');prior_prod=z.read(prefix+'/producer/producer_receipt.json')
        if hashlib.sha256(prior_mf).hexdigest()!=token_data['manifest_sha256'] or hashlib.sha256(prior_prod).hexdigest()!=token_data['producer_receipt_sha256']:
            raise ValueError('TOKEN_REFERENCE_LINEAGE')
        tr=token_data['requests'][0];require_tokens=tr['token_ids']
        if tr['actual_input_shape']!=[2,512] or tr['actual_output_tokens_per_sample']!=[2,2] or tr['early_eos'] is not False:
            raise ValueError('TOKEN_REFERENCE_SHAPE')
        write(out/'token_reference.json',dict(archive_sha256=OLD_BATCH_SHA,member=token_member,
            member_sha256=hashlib.sha256(z.read(token_member)).hexdigest(),token_ids=require_tokens,
            role='FUNCTIONAL_VALUE_REFERENCE_ONLY_OLD_B2_REMAINS_BLOCKED'))
    if sha(out/'model_inventory.csv')!=previous['inventory_sha256']:
        raise ValueError('MODEL_OR_INPUT_REFERENCE')
    target=git('rev-parse','HEAD').decode().strip();git('merge-base','--is-ancestor',BASE,target)
    rows=[]
    for name in SOURCES:
        data=git('show',target+':'+name)
        if data!=(ROOT/name).read_bytes():raise ValueError('UNCOMMITTED_SOURCE:'+name)
        rows.append(dict(path=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest()))
    for n in ('memset_prefill_stage.py','run_memset_prefill.ps1'):(out/n).write_bytes(git('show',target+':scripts/'+n))
    bundle=out/'execution.bundle';git('bundle','create',bundle,'HEAD','^'+BASE);git('bundle','verify',bundle)
    cfg=dict(**{k:old[k] for k in ('server_root','code_root','python','python_version','git','toolchain_files','build',
        'runtime_path','detours_directory','nvtx_directory','nsys','nsys_sha256')},
        **{k:previous[k] for k in ('target_python','site_root','model','inventory_sha256','gpu_uuid','gpu_pci_bus_id')},
        schema_version='memset-prefill-delivery/0.1.0',execution_commit=target,analysis_commit=target,prerequisite=BASE,
        run_id=uuid.uuid4().hex,model_process_budget=1,profile_budget=1,automatic_retry=False,automatic_cleanup=False,
        runtime_expected_sha256='f95273031fc5ea44cdb37e0a696a1b15b9d84a4ee977299a6f6e652ef4d790cf',
        input_seed_sha256=sha(out/'input_b1.json'),sources=rows,cpu_tests=CPU_TESTS,cpu_test_count=cpu_count,
        expected_token_ids=require_tokens,
        bootstrap_sha256=sha(out/'memset_prefill_stage.py'),temporary_required_bytes=2**31,
        historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000,
        role='Engineering',scope='ONE_NEW_B2_PREFILL_PARAMETERS_ONLY_NOT_PILOT_OR_COE_QUALIFICATION')
    write(out/'delivery.json',cfg)
    files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(out.iterdir())]
    write(out/'package_manifest.json',dict(schema_version='memset-prefill-package/0.1.0',files=files))
    verify_package(out);archive=out.with_suffix('.zip')
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for p in sorted(out.iterdir()):z.write(p,p.name)
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None or len(z.namelist())!=len(files)+1:raise ValueError('ZIP_CRC_OR_COVERAGE')
        for r in files:
            if hashlib.sha256(z.read(r['path'])).hexdigest()!=r['sha256']:raise ValueError('ZIP_CONTENT')
    return dict(commit=target,prerequisite=BASE,zip=str(archive),bytes=archive.stat().st_size,sha256=sha(archive),
        launcher_sha256=sha(out/'run_memset_prefill.ps1'),manifest_sha256=sha(out/'package_manifest.json'),
        static_return=str(Path(cfg['server_root'])/'transfer'/('memset_prefill_'+target[:12]+'_static.zip')))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('output','micro-delivery','micro-once','old-batch'):p.add_argument('--'+n,required=True,type=Path)
    p.add_argument('--cpu-count',required=True,type=int);a=p.parse_args()
    print(json.dumps(build(a.output,a.micro_delivery,a.micro_once,a.old_batch,a.cpu_count),indent=2))
