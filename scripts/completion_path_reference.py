"""CPU-only, immutable archive reference for one new Cpre, never batch resume."""
import csv
import hashlib
import io
from pathlib import Path,PurePosixPath
import stat
import zipfile

from exposedpath import completion_path as contract
from exposedpath.gate8_isolated_preflight import read,sha,write_new

VERSION='completion-path-c0-reference/0.1'
COMMON_FIELDS=('model_id','model_content_snapshot','revision','gpu_uuid','gpu_pci_bus_id',
    'gpu_index_physical','gpu_index_logical','nvidia_driver_version','cuda_version_used',
    'inference_framework_version','dtype_and_quantization','execution_mode','attention_backend',
    'batch_size','fixed_input_tokens','fixed_output_tokens','warmup_count','repeat_count',
    'sampling_config','prompt_tokens_sha256','runner_source_sha256')


def extract_reference(archive,metadata,output):
    archive=Path(archive);output=Path(output)
    contract.require(archive.is_file() and archive.stat().st_size==metadata['archive_bytes']
        and sha(archive)==metadata['archive_sha256'],'REFERENCE_ARCHIVE')
    contract.require(not output.exists(),'REFERENCE_EXISTS')
    with zipfile.ZipFile(archive) as z:
        names=z.namelist()
        contract.require(len(names)==len(set(n.casefold() for n in names)),'REFERENCE_DUPLICATE')
        for info in z.infolist():
            p=PurePosixPath(info.filename)
            contract.require(not p.is_absolute() and '..' not in p.parts and '\\' not in info.filename
                and ':' not in info.filename and not stat.S_ISLNK(info.external_attr>>16)
                and not info.is_dir(),'REFERENCE_PATH')
        contract.require(z.testzip() is None,'REFERENCE_CRC')
        index=z.read('artifact_sha256.csv')
        contract.require(hashlib.sha256(index).hexdigest()==metadata['archive_manifest_sha256'],'REFERENCE_MANIFEST')
        rows=list(csv.DictReader(io.StringIO(index.decode('utf-8-sig'))))
        contract.require(bool(rows) and len(rows)==len({r['path'].casefold() for r in rows})
            and {r['path'] for r in rows}|{'artifact_sha256.csv'}==set(names),'REFERENCE_COVERAGE')
        for row in rows:
            b=z.read(row['path'])
            contract.require(len(b)==int(row['bytes']) and hashlib.sha256(b).hexdigest()==row['sha256'].lower(),'REFERENCE_MEMBER')
        output.mkdir(parents=True,exist_ok=False);z.extractall(output)
    return output


def check_sources(root,sources,preflight):
    root=Path(root).resolve();actual={}
    contract.require(bool(sources),'REFERENCE_EMPTY_SOURCES')
    for name,item in sources.items():
        p=(root/name).resolve()
        contract.require(not Path(name).is_absolute() and p.is_relative_to(root) and p!=root
            and not p.is_symlink() and p.is_file(),'REFERENCE_SOURCE_PATH')
        contract.require(preflight['tree_hashes'].get(name)==item['old_runtime_sha256']
            and any(r['sha256']==item['old_runtime_sha256'] for r in item['representations'])
            and item['representations'][0]['sha256']==item['git_sha256'],'REFERENCE_SOURCE_BINDING')
        entry=dict(sha256=sha(p),bytes=p.stat().st_size)
        entry['matched']=any(entry['sha256']==r['sha256'] and entry['bytes']==r['bytes'] for r in item['representations'])
        actual[name]=entry
        contract.require(entry['matched'],'REFERENCE_CURRENT_SOURCE_'+name)
    return actual


def review_reference(config,output,code_root):
    from scripts.completion_path_diagnostic import consume_collection
    reference=Path(config['c0_reference'])
    contract.require(sha(reference)==config['c0_reference_sha256'],'REFERENCE_METADATA_HASH')
    metadata=read(reference)
    contract.require(metadata['schema_version']==VERSION and metadata['compatible_commit']==config['commit'],'REFERENCE_VERSION')
    archive=reference.parent/metadata['archive_filename']
    contract.require(metadata['archive_filename']=='c0_sealed_original.zip'
        and archive.resolve().parent==reference.parent.resolve(),'REFERENCE_ARCHIVE_PATH')
    root=extract_reference(archive,metadata,output)
    target=root/'experiment/batch/C0/collection'
    preflight=read(target/'auxiliary_preflight.json');final=read(target/'auxiliary_preflight.final.json')
    claim=read(target/'auxiliary_preflight.claim.json');execution=read(target/'diagnostic/engineering_execution.json')
    contract.require(preflight['git_commit']==metadata['execution_commit'] and preflight['git_dirty'] is False
        and final['status']=='PASS' and final['preflight_sha256']==sha(target/'auxiliary_preflight.json')
        and final['target_claim_sha256']==sha(target/'auxiliary_preflight.claim.json')
        and claim['preflight_sha256']==sha(target/'auxiliary_preflight.json')
        and claim['nonce']==preflight['nonce'] and claim['run_id']==preflight['run_id']
        and claim['target_pid']==execution['identity']['pid'],'REFERENCE_PREFLIGHT')
    source_actual=check_sources(code_root,metadata['unchanged_measurement_sources'],preflight)
    binding=metadata['binding'];contract.validate_binding(binding)
    contract.require(binding['variant']=='C0' and preflight['run_id']==contract.batch_binding(binding)['run_id'],'REFERENCE_VARIANT_OR_RUN')
    value,tokens=consume_collection(target,binding,metadata['execution_commit'])
    manifest=read(target/'diagnostic/manifest.json')
    contract.require(sha(root/'model_sha256.csv')==config['inventory_sha256']
        and sha(root/'prompt_512.json')==config['prompt_512_sha256'],'REFERENCE_COMMON_INPUTS')
    write_new(root.parent/(root.name+'.review.json'),dict(schema_version=VERSION,status='C0_PREFILL_REFERENCE_REVIEWED',
        execution_commit=metadata['execution_commit'],analysis_commit=config['commit'],
        archive_sha256=metadata['archive_sha256'],result_sha256=sha(target/'analyzed/prefill.json'),
        source_actual=source_actual,request_accepted=False,decode_accepted=False,
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED'))
    return value,tokens,manifest,target
