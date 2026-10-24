"""Local deterministic packaging only; reads fixed blobs and sealed references."""
import argparse
import csv
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile

sys.dont_write_bytecode=True

ROOT=Path(__file__).resolve().parents[1]
SCIENCE='c8f3dad152659044691f9ff328498c7a127815ea'
NATIVE='6c744bf52daff3fc54571e264a0c34e3207aa1df'
CONTROL_FILES={'cupti_batch_once_delivery.py':'scripts/cupti_batch_once_delivery.py',
    'cupti_event_b.py':'scripts/cupti_event_b.py','run_cupti_batch_once.ps1':'scripts/run_cupti_batch_once.ps1',
    'git_materialization.py':'scripts/coe_controlled_deployment.py'}
FLAT=('cupti_input_contract','cupti_input_pilot','cupti_model_consumer','cupti_batch_accounting',
      'cupti_timeline_b','cupti_timeline_model')
CONSUMER=('exposedpath_v141/cupti_driver_queries.py','scripts/analyze_completion_operation_candidate.py',
    'exposedpath_v141/submit_effect_bridge.py','analysis/cupti_timeline.py','analysis/coe_helper_identity.py',
    'analysis/coe_candidate.py','analysis/coe_completion_model.py','analysis/cupti_a_migration.py')


def blob(commit,path):
    return subprocess.run(['git','show',commit+':'+path],cwd=ROOT,check=True,capture_output=True).stdout
def digest(b):return hashlib.sha256(b).hexdigest()
def encoded(v):return (json.dumps(v,indent=2)+'\n').encode('utf8')
def fact(path,b,**extra):return dict(path=path,bytes=len(b),sha256=digest(b),**extra)


def build_package(output,control_commit,*,source=blob,validation_xml=None):
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    with zipfile.ZipFile(ROOT/'.local/transfer/cupti_input_62b5a5a1d2e4_delivery.zip') as z:
        c=json.loads(z.read('delivery.json'))
        payload={n:z.read(n) for n in ('reviewed_stage.py','micro_support.py','model_sha256.csv','model_config_reference.json')}
    with zipfile.ZipFile(ROOT/'.local/transfer/cupti_input_bd377c860faf_delivery.zip') as z:
        single=json.loads(z.read('input_512.json'))
    with zipfile.ZipFile(ROOT/'.local/transfer/cupti_timeline_6c744bf52daf_static.zip') as z:
        source_index_sha=digest(z.read('source_bytes.json'))
        native_a_config=json.loads(z.read('delivery.json'))
        payload['history/native_a_receipt.json']=z.read('receipt.json')
    with zipfile.ZipFile(ROOT/'.local/transfer/cupti_event_38baca449d2f_once.zip') as z:
        payload['history/event_receipt.json']=z.read('receipt.json')
    science=[]
    for n in FLAT:
        name=n+'.py';payload[name]=source(SCIENCE,'scripts/'+name)
        science.append(fact(name,payload[name],git_path='scripts/'+name))
    for p in CONSUMER:
        name='consumer/'+p;payload[name]=source(SCIENCE,p)
        science.append(fact(name,payload[name],git_path=p))
    payload['producer_policy.py']=source(SCIENCE,'exposedpath/gate11_pilot.py')
    science.append(fact('producer_policy.py',payload['producer_policy.py'],git_path='exposedpath/gate11_pilot.py'))
    payload['startup_storage.py']=source(SCIENCE,'scripts/coe_startup_storage.py')
    science.append(fact('startup_storage.py',payload['startup_storage.py'],git_path='scripts/coe_startup_storage.py'))
    for name,path in CONTROL_FILES.items():payload[name]=source(control_commit,path)
    # Use the fixed contract itself to serialize input; no torch/GPU imports.
    contract_path=output/'cupti_input_contract.py';contract_path.write_bytes(payload['cupti_input_contract.py'])
    spec=importlib.util.spec_from_file_location('_batch_pack_contract',contract_path)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    prompt=helper.batch_prompt(single,2)
    model=json.loads(payload['model_config_reference.json'])
    identity=helper.input_identity(prompt,512,model,batch_size=2,version=helper.BATCH_IDENTITY)
    payload['input_512_B2.json']=encoded(prompt)
    plan=dict(schema_version=helper.BATCH_PLAN_VERSION,role='Engineering',conditions=[dict(input_tokens=512,batch_size=2)],
        blocks=1,orders=[['G512B2P']],comparisons=[])
    # schedule's package-local producer lookup is byte-verified below.
    (output/'producer_policy.py').write_bytes(payload['producer_policy.py'])
    batch_id='coe-batch-b2-'+control_commit[:12]
    c.update(schema_version=helper.BATCH_PLAN_VERSION,scientific_commit=SCIENCE,controller_commit=SCIENCE,
        analysis_commit=SCIENCE,delivery_control_commit=control_commit,batch_id=batch_id,plan=plan,
        producer_policy_sha256=digest(payload['producer_policy.py']),
        git=native_a_config['git'],
        slots=helper.schedule(batch_id,SCIENCE,plan=plan),model_config_sha256=digest(payload['model_config_reference.json']),
        model_limits=helper.model_limits(model),inputs={'G512B2P':dict(path='input_512_B2.json',
            sha256=digest(payload['input_512_B2.json']),identity=identity,output_validation=dict(
                version='cupti-output-validation/0.3.0',batch_size=2,output_tokens=2,
                eos_policy='ANY_SAMPLE_EOS_REJECT_WHOLE_INVOCATION',mode='OBSERVED_ENGINEERING',expected_token_ids=None))},
        scientific_files=[r['path'] for r in science],control_sources=[fact(name,payload[name],git_path=p)
            for name,p in CONTROL_FILES.items()],asset_compatibility=dict(
            schema_version='cupti-batch-historical-assets-current-source/0.1.0',historical_native_commit=NATIVE,
            current_scientific_commit=SCIENCE,reviewed_a_receipt_sha256='9d6d4000d07ea7d752c78f4d337f88fe35085e99995ee88242eae5a824ad971e',
            reviewed_event_receipt_sha256='824183fcea1e4ca5d0f3423cfedf6fb791379bc80a4f3dd47318854a0fac0ed9',
            history_is_not_current_checkout=True),a_source_bytes_sha256=source_index_sha,
        budget=dict(model_process_budget=1,cupti_sessions=1,nsight_profiles=0,blocks=1,per_model_seconds=300,
            per_analysis_seconds=180,temporary_required_bytes=12*2**30,automatic_retry=False,
            automatic_replacement=False,automatic_cleanup=False),cpu_sources=[])
    for k,v in helper.POLICIES.items():c[k]=v
    # Full conservative import closure, plus the already materialized controlled
    # source paths: never grant unknown dirty files or a partial 13-file proof.
    paths=subprocess.run(['git','ls-tree','-r','--name-only',SCIENCE,'exposedpath','exposedpath_v141','analysis'],
        cwd=ROOT,check=True,capture_output=True).stdout.decode().splitlines()
    paths=({p for p in paths if p.endswith('.py')}|{'scripts/'+n+'.py' for n in FLAT}|
        {'scripts/coe_startup_storage.py','scripts/analyze_completion_operation_candidate.py'})
    with zipfile.ZipFile(ROOT/'.local/transfer/coe_controlled_c8f3dad_repair2_once.zip') as z:
        paths.update(r['path'] for r in json.loads(z.read('prepare/source_binding.json'))['sources'])
        gpu=z.read('once/gpu.stdout');values=[s.strip() for s in next(csv.reader(gpu.decode().splitlines()))]
        assert values[0]==c['gpu_uuid'] and values[1].lower()==c['gpu_pci'].lower()
        c['gpu_reference']=dict(name=values[2],driver_version=values[3],total_mib=int(values[4]),
            source='SEALED_CONTROLLED_RUN_NOT_PERFORMANCE_REFERENCE',source_sha256=digest(gpu))
    rows=[fact(p,source(SCIENCE,p)) for p in sorted(paths)]
    native=[]
    for p in ['scripts/native_cupti_timeline/'+n for n in ('client.cpp','core.h','writer.h','activity_policy.h')]+[
        'exposedpath/cupti_timeline.py','exposedpath/runner.py','exposedpath/observation_preparation.py']:
        b=source(SCIENCE,p);assert b==source(NATIVE,p);native.append(fact(p,b))
    payload['science_lock.json']=encoded(dict(schema_version='cupti-batch-science-lock/0.1.0',scientific_commit=SCIENCE,
        native_commit=NATIVE,package_science=science,current_sources=rows,native_source_equivalence=native))
    payload['delivery.json']=encoded(c)
    payload['local_authorization_scope.json']=encoded(dict(schema_version='cupti-batch-delivery-scope/0.1.0',
        local_implementation_testing_packaging_approved=True,server_execution_approved=False,
        remote_publication_approved=False,old_micro_authorization_applicable=False,
        source='DIRECT_USER_REQUEST_LOCAL_PREPARATION_2026-10-24',required_future='NEW_EXPLICIT_OPERATOR_AUTHORITY_AND_PUBLICATION'))
    payload['README.txt']=('''L512/B2/P bounded Engineering delivery - pending review

Science/analysis: c8f3dad152659044691f9ff328498c7a127815ea.
Native assets: 6c744bf52daff3fc54571e264a0c34e3207aa1df, activity policy 0.2.0.
Submit-effect bridge: 0.3.0. No controlled-only 0.3.2 science payload.
Delivery control commit: '''+control_commit+'''.

Default prepare is CPU/identity/storage only: no DLL load, rebuild, model or CUDA.
It verifies publication of this control commit to the fixed repository main,
then verifies the actual c8 checkout/index/content. Only proven CRLF-to-blob
differences in the source lock may be materialized in binary mode. Other changes
stop. No checkout/reset, global Git change or replacement of old receipts.
Historical A/event receipts prove native assets, not today's checkout HEAD.
Legacy model runner_git fields denote unchanged native-version source content;
the separate binding.json records the actual c8 checkout. No fake 6c HEAD.

All NEW evidence/logs/cache/temp/archives are under server_root/transfer.
Old assets and weights stay in place. No automatic deletion or ACL/history scan.
Prepare archive: transfer/coe_batch_L512B2_<control12>_static.zip.
Model archive, if separately authorized later: same prefix with _once.zip.

This package is NOT a server/publication/model authorization. Normal publication
of the listed control commit and explicit deployment/prepare authorization remain
required. The old micro authorization does not authorize this batch invocation.
After the real prepare archive is reviewed, execution additionally requires its
exact receipt SHA256, a new model approval and current shared-use permission.
Do not add a switch to any old entry or reuse an old preparation receipt.

One Engineering invocation only: L512, B2, output2 per sample, P natural
Host-readable policy, warmup3/repeat1, FP16/eager/SDPA, one process/session.
Model hard timeout 300s; CPU analysis 180s. Reserve about ten minutes including
checks/packing, not a guarantee. Fresh 12GiB on participating volumes; same-volume
requests are not summed. Historical YLQ total remains UNKNOWN, long-term target
is <50,000,000,000 bytes and is not claimed met by this check.
Shared GPU free reserve 8GiB is NOT a measured B2 peak or a noninterference
guarantee. Actual UUID/PCI/driver, explicit sharing permission and successful
session subscription are required. Unreadable process data remains UNKNOWN.

No retries, replacement, smaller configuration, B4 or automatic comparisons.
Any identity/effect/dependency/terminal/capacity/quality failure stops. Unknown
writers refuse packaging. Preserve the scene and report the exact error.
Actual [2,2] tokens and whole-batch completion are checked; independent numerical
output correctness is NOT_ASSESSED. Never treat batch samples as repeats.
Original A, COE and candidate E stay separate; no Formal/performance qualification.

Local validation uses real sealed A/event bytes and real local Git/PS5.1, with
explicit target-interpreter/library/GPU observations and exit7 process doubles.
It is NOT target Python3.11.16, DLL-load, CUDA, model or B2 applicability evidence.
Historical 26 CPU and limited controlled-GPU evidence are reused, not rerun or
upgraded. No target execution is claimed by the local XML in this package.
''').encode('utf8')
    if validation_xml is not None:
        raw=Path(validation_xml).read_bytes();tree=ET.fromstring(raw)
        cases=tree.findall('.//testcase')
        assert cases and not tree.findall('.//failure') and not tree.findall('.//error') and not tree.findall('.//skipped')
        payload['validation/local_cpu.xml']=raw
        payload['validation/local_validation.json']=encoded(dict(
            schema_version='cupti-batch-local-control-validation/0.1.0',passed=len(cases),failed=0,skipped=0,
            xml_sha256=digest(raw),host_python=list(sys.version_info[:3]),
            target_python=[3,11,16],target_python_executed=False,
            target_gpu_executed=False,model_executed=False,server_accessed=False,
            real_components=['sealed A/event receipts','local Git/content/index','PS5.1 entry'],
            explicit_doubles=['target interpreter','target library observations','nvidia-smi','exit7 model substitute'],
            previous_26_tests='REUSED_NOT_RERUN'))
    for name,b in payload.items():
        p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
    index=dict(schema_version='cupti-batch-once-package/0.1.0',delivery_control_commit=control_commit,
        scientific_commit=SCIENCE,files=[fact(p,b) for p,b in sorted(payload.items())])
    (output/'package_manifest.json').write_bytes(encoded(index))
    return c


def archive_package(output,archive):
    output,archive=Path(output),Path(archive)
    index=json.loads((output/'package_manifest.json').read_bytes())
    names=[r['path'] for r in index['files']]+['package_manifest.json']
    assert len(names)==len(set(n.casefold() for n in names))
    with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(names):
            item=zipfile.ZipInfo(name,(1980,1,1,0,0,0));item.compress_type=zipfile.ZIP_DEFLATED
            item.external_attr=0o100644<<16;z.writestr(item,(output/name).read_bytes())
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None and set(z.namelist())==set(names)
        for row in index['files']:
            b=z.read(row['path']);assert len(b)==row['bytes'] and digest(b)==row['sha256']
    return dict(path=str(archive),bytes=archive.stat().st_size,sha256=digest(archive.read_bytes()),
        manifest_sha256=digest((output/'package_manifest.json').read_bytes()),
        launcher_sha256=digest((output/'run_cupti_batch_once.ps1').read_bytes()),files=len(names))


def build_repair_package(output,control_commit,*,source=blob,bundle_bytes=None,validation_xml=None):
    """Copy the sealed e358 packet; replace only explicit control/metadata files."""
    output=Path(output);output.mkdir(parents=True,exist_ok=False)
    old=ROOT/'.local/transfer/coe_batch_e358d37f0bcd_delivery.zip'
    assert digest(old.read_bytes())=='b5e9190080bb6ac3d9e7be4b357f1f457a6f2698ec0250d91c0b5a8f2b434626'
    with zipfile.ZipFile(old) as z:payload={n:z.read(n) for n in z.namelist() if n!='package_manifest.json'}
    controls=dict(CONTROL_FILES)
    controls['cupti_batch_publication_repair.py']='scripts/cupti_batch_publication_repair.py'
    for name,path in controls.items():payload[name]=source(control_commit,path)
    helper_path=output/'cupti_batch_publication_repair.py';helper_path.write_bytes(payload[helper_path.name])
    spec=importlib.util.spec_from_file_location('_pack_publication_repair',helper_path)
    helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    if bundle_bytes is None:
        assert subprocess.run(['git','rev-parse','refs/heads/main'],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()==control_commit
        subprocess.run(['git','bundle','create',str((output/'repair.bundle').resolve()),'refs/heads/main','^'+SCIENCE],cwd=ROOT,check=True,capture_output=True)
        bundle_bytes=(output/'repair.bundle').read_bytes()
    payload['repair.bundle']=bundle_bytes
    c=json.loads(payload['delivery.json'])
    c.update(delivery_control_commit=control_commit,repair_profile=helper.profile(),
        repair_bundle=dict(path='repair.bundle',bytes=len(bundle_bytes),sha256=digest(bundle_bytes),
            prerequisite=SCIENCE,control_commit=control_commit),
        control_sources=[fact(name,payload[name],git_path=path) for name,path in controls.items()])
    payload['delivery.json']=encoded(c)
    payload['README.txt']=('''Single B2 publication-control repair, pending review
New control commit: '''+control_commit+'''
Science/analysis remain c8f3dad; bridge0.3.0, native collector6c, no rebuild.
The 16 scientific payloads, input/mask, plan and budget are unchanged e358 bytes.
Default launcher action is package verification only. prepare is refused for this
repair profile: the reviewed A is reused, never rerun or overwritten.

Old B failed at published_main exit128, GitHub443, BEFORE model/session dispatch.
Its BLOCKED, null session count and all logs remain unchanged. Before any model,
the exact old A receipt/129-file seal, parent delivery, fixed publication records,
failed-attempt 140-file seal and original ZIP hashes must all match.
No online publication query runs on the target. The old A proves ONLY e358.
NEW control publication must be separately authorized/pushed and remotely checked
on the publishing machine. Supply the exact externally reviewed publication JSON
as base64 plus its reviewed SHA256 via ReviewedControlPublication and
ReviewedControlPublicationSha256. Missing, changed or wrong-target proof refuses.
The supplied proof is operator authenticated, not a cryptographic signature.
The repair.bundle independently binds all five new control payloads to the exact
new Git commit. It is verified offline in transfer-only temporary objects; it
proves Git content, never by itself proves remote publication.

This packet does NOT grant deployment or a new model run. Review its new identity
and publication proof first, then reconfirm the unused single-instance budget and
fresh lab shared-use permission. Never reuse the original failed output directory.
New output: transfer/coe_batch_L512B2_<new-control12>_repair1/;
return ZIP: same prefix with _once.zip. No old tree, marker or library is modified.
Fresh disk>=12GiB and GPU>=8GiB, UUID/PCI/driver/source/library checks still apply;
8GiB is not a peak measurement or noninterference guarantee. Unknown process data
stays UNKNOWN; real session open/quality/effect/dependency checks remain strict.
One L512/B2/output2/P Engineering invocation, warmup3/repeat1, one model/session,
zero Nsight; model300s, analysis180s, approx10min. No retries, smaller input,
replacement or added experiments. Unknown writers refuse packing.
Same-source original A, COE and E remain separate. No Formal qualification,
comparison/matrix authorization or performance/numerical correctness claim.
Old local_cpu.xml is reused history, not rerun. New repair validation, if present,
is CPU-only with explicit device/interpreter observations and exit7 doubles.
''').encode('utf8')
    payload['local_authorization_scope.json']=encoded(dict(schema_version='cupti-batch-repair-local-scope/0.1.0',
        local_repair_validation_packaging_approved=True,new_control_publication_approved=False,
        new_deployment_execution_approved=False,prior_model_starts=0,remaining_model_process_budget=1,
        prior_failure_status_unchanged=True,server_accessed=False))
    if validation_xml is not None:
        raw=Path(validation_xml).read_bytes();tree=ET.fromstring(raw)
        assert tree.findall('.//testcase') and not any(tree.findall('.//'+n) for n in ('failure','error','skipped'))
        payload['validation/repair_cpu.xml']=raw
    for name,b in payload.items():
        path=output/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(b)
    index=dict(schema_version='cupti-batch-once-package/0.1.1',delivery_control_commit=control_commit,
        scientific_commit=SCIENCE,files=[fact(n,b) for n,b in sorted(payload.items())])
    (output/'package_manifest.json').write_bytes(encoded(index))
    return c


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--control-commit',required=True)
    p.add_argument('--validation-xml',type=Path)
    p.add_argument('--zip',type=Path)
    p.add_argument('--publication-repair',action='store_true')
    a=p.parse_args();build=build_repair_package if a.publication_repair else build_package
    c=build(a.output,a.control_commit,validation_xml=a.validation_xml)
    result=dict(path=str(a.output),control_commit=c['delivery_control_commit'],scientific_commit=SCIENCE)
    if a.zip is not None:result.update(archive_package(a.output,a.zip))
    print(json.dumps(result))


if __name__=='__main__':main()
