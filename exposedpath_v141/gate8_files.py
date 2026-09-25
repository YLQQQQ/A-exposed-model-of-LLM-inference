"""Sealed local file lifecycle. No collection, exporter, model or device access.

Inputs are referenced read-only. A complete result is published by directory
rename; interrupted staging is retained for diagnosis, never an accepted result.
"""
import json
import os
from pathlib import Path
import tempfile
import shutil

from exposedpath.gate8_identity import validate_pass_identity, PASS_FIELDS
from .gate8_adapter import digest, normalized_uuid, normalized_pci

RECEIPT_VERSION = 'exposedpath-gate8-input-receipt/0.1.0'
RESULT_VERSION = 'exposedpath-gate8-file-chain/0.1.0'
ARTIFACTS = {'raw','sqlite','pass_identity','host_ledger','preflight','cuda_probe',
             'wmpc_manifest','prompt','runner_source','producer_receipt','export_report'}


def _json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def _write(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as handle:
        json.dump(value, handle, sort_keys=True, indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())


def _entry(path, root):
    path = Path(path).resolve()
    if not path.is_file() or path.stat().st_size == 0:
        raise ValueError('ARTIFACT_MISSING_OR_EMPTY')
    return {'filename':path.relative_to(root.resolve()).as_posix(),
            'sha256':digest(path), 'size_bytes':path.stat().st_size}


def _resolve(root, item):
    if set(item) != {'filename','sha256','size_bytes'}:
        raise ValueError('ARTIFACT_ENTRY_INVALID')
    path = (root/item['filename']).resolve()
    if not path.is_relative_to(root.resolve()) or path == root.resolve():
        raise ValueError('ARTIFACT_PATH_ESCAPE')
    if _entry(path, root) != item:
        raise ValueError('ARTIFACT_HASH_MISMATCH')
    return path


def _identities(paths):
    ledger, manifest = _json(paths['pass_identity']), _json(paths['wmpc_manifest'])
    validate_pass_identity(ledger)
    producer = _json(paths['producer_receipt'])
    if (producer.get('schema_version') != 'exposedpath-gate8-producer-receipt/0.1.0'
            or any(producer.get(k) != ledger[k] for k in ('run_id','pass_id','attempt_id'))
            or producer.get('gate8_verdict') != 'NOT_RUN'
            or producer.get('status') != ('COMPLETE' if all(r['outcome']=='COMPLETE' for r in ledger['requests']) else 'INCOMPLETE')
            or set(producer.get('files',{})) != {'pass_identity.json','host_boundaries.json'}):
        raise ValueError('IDENTITY_CONFLICT: producer receipt')
    for key,name in [('pass_identity','pass_identity.json'),('host_ledger','host_boundaries.json')]:
        if _resolve(Path(paths['producer_receipt']).resolve().parent,producer['files'][name]) != Path(paths[key]).resolve():
            raise ValueError('SOURCE_HASH_MISMATCH: producer receipt')
    if ledger['pass_id'] != 'pass1' or ledger['runner_git_dirty'] is not False:
        raise ValueError('IDENTITY_CONFLICT: pass1 clean required')
    for k in ('experiment_id','wmpc_id','run_id','run_role','data_role','runner_git_commit','runner_git_dirty'):
        if manifest.get(k) != ledger[k]:
            raise ValueError(f'IDENTITY_CONFLICT: WMPC {k}')
    for key, field in [('wmpc_manifest','wmpc_manifest_sha256'),('prompt','prompt_sha256'),('runner_source','runner_source_sha256')]:
        if digest(paths[key]) != ledger[field]:
            raise ValueError(f'SOURCE_HASH_MISMATCH: {key}')
    if manifest.get('prompt_tokens_sha256') != digest(paths['prompt']) or manifest.get('runner_source_sha256') != digest(paths['runner_source']):
        raise ValueError('SOURCE_HASH_MISMATCH: WMPC prompt/source')
    pre, probe = _json(paths['preflight']), _json(paths['cuda_probe'])
    if (manifest.get('gpu_index_physical') != pre['gpu_index_physical']
            or manifest.get('gpu_index_logical') != probe['gpu_index_logical']
            or normalized_uuid(manifest.get('gpu_uuid')) != normalized_uuid(pre['gpu_uuid'])
            or normalized_pci(manifest.get('gpu_pci_bus_id')) != normalized_pci(pre['pci_bus_id'])):
        raise ValueError('IDENTITY_CONFLICT: WMPC GPU')
    if ledger['raw_artifact_sha256'] not in (None,digest(paths['raw'])):
        raise ValueError('SOURCE_HASH_MISMATCH: Raw')
    export = _json(paths['export_report'])
    attempts = export.get('attempts',[])
    successful = [a for a in attempts if a.get('number') == export.get('successful_attempt')]
    if (export.get('status') != 'PASS' or export.get('error') is not None
            or export.get('analyzer_allowed') is not True or export.get('attempt_count') != len(attempts)
            or len(successful) != 1 or not 1 <= len(attempts) <= 2
            or export.get('rep_sha256','').lower() != digest(paths['raw'])
            or export.get('canonical_sqlite_sha256','').lower() != digest(paths['sqlite'])):
        raise ValueError('EXPORT_LINEAGE_UNPROVEN')
    attempt = successful[0]
    if (attempt.get('status') != 'PASS' or type(attempt.get('exit_code')) is not int or attempt['exit_code'] != 0
            or attempt.get('process_exited') is not True or attempt.get('timed_out') is not False
            or attempt.get('terminated_pid') is not None or attempt.get('validation_issues') != []
            or attempt.get('sqlite_size') != Path(paths['sqlite']).stat().st_size
            or attempt.get('rep_sha256','').lower() != digest(paths['raw'])
            or attempt.get('sqlite_sha256','').lower() != digest(paths['sqlite'])):
        raise ValueError('EXPORT_ATTEMPT_UNPROVEN')
    return {k:ledger[k] for k in PASS_FIELDS}


def write_input_receipt(output_path, *, artifacts, collector_version, capture_session_id):
    output_path = Path(output_path).resolve()
    if output_path.exists():
        raise FileExistsError(output_path)
    if set(artifacts) != ARTIFACTS:
        raise ValueError('INPUT_ARTIFACT_SET_INVALID')
    if not isinstance(collector_version,str) or not collector_version or not isinstance(capture_session_id,str) or not capture_session_id:
        raise ValueError('COLLECTOR_SESSION_IDENTITY_MISSING')
    identity = _identities(artifacts)
    entries = {k:_entry(Path(p),output_path.parent) for k,p in artifacts.items()}
    if len({e['filename'] for e in entries.values()}) != len(entries):
        raise ValueError('INPUT_ARTIFACT_ALIAS')
    _write(output_path, dict(schema_version=RECEIPT_VERSION, identity=identity, artifacts=entries,
                            collector_version=collector_version, capture_session_id=capture_session_id))
    return output_path


def load_input_receipt(path):
    path = Path(path).resolve()
    value = _json(path)
    if (set(value) != {'schema_version','identity','artifacts','collector_version','capture_session_id'}
            or value['schema_version'] != RECEIPT_VERSION or set(value['artifacts']) != ARTIFACTS):
        raise ValueError('INPUT_RECEIPT_VERSION_OR_SHAPE_INVALID')
    paths = {k:_resolve(path.parent,e) for k,e in value['artifacts'].items()}
    if value['identity'] != _identities(paths):
        raise ValueError('IDENTITY_CONFLICT: receipt')
    return value, paths


def process_gate8_receipt(receipt_path, output_dir, *, integrity_receipts_path=None, synthetic_fixture=False):
    from .canonical_raw import convert_sqlite_to_canonical
    from .gate8_scope import project_completion_scopes
    from .gate8_analysis import analyze_gate8_local
    receipt_path, output_dir = Path(receipt_path).resolve(), Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)
    receipt, paths = load_input_receipt(receipt_path)
    if any(p.is_relative_to(output_dir) for p in [receipt_path,*paths.values()]):
        raise ValueError('OUTPUT_CONTAINS_INPUT')
    receipt_hash = digest(receipt_path)
    integrity = None if integrity_receipts_path is None else _json(integrity_receipts_path)
    integrity_hash = None if integrity_receipts_path is None else digest(integrity_receipts_path)
    output_dir.parent.mkdir(parents=True,exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{output_dir.name}-partial-',dir=output_dir.parent))
    provenance = staging/'provenance'
    provenance.mkdir()
    shutil.copyfile(receipt_path,provenance/'input_receipt.json')
    for role, path in paths.items():
        if role not in ('raw','sqlite'):
            shutil.copyfile(path,provenance/f'{role}.json')
    # No catch-and-pass: failures leave only an uncommitted diagnostic staging tree.
    canonical = convert_sqlite_to_canonical(paths['sqlite'], staging/'canonical', 'Engineering',
        raw_sha256=digest(paths['raw']), collector_version=receipt['collector_version'],
        gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
    scope = project_completion_scopes(canonical, paths['host_ledger'], staging/'projection/scope.json')
    analysis = analyze_gate8_local(canonical,scope,staging/'analysis',capture_session_id=receipt['capture_session_id'],
                                  integrity_receipts=integrity,synthetic_fixture=synthetic_fixture)
    load_input_receipt(receipt_path)
    if digest(receipt_path) != receipt_hash or (integrity_hash is not None and digest(integrity_receipts_path) != integrity_hash):
        raise ValueError('SOURCE_HASH_CHANGED_DURING_PROCESSING')
    report = _json(analysis)
    files = [_entry(p,staging) for p in sorted(staging.rglob('*')) if p.is_file()]
    final = dict(schema_version=RESULT_VERSION, identity=receipt['identity'],
                 input_receipt_sha256=receipt_hash, integrity_input_sha256=integrity_hash,
                 status=report['status'], validation_role=report['validation_role'],
                 gate8_verdict='NOT_RUN', q0_status='NOT_RUN', files=files)
    _write(staging/'chain_result.json',final)
    staging.rename(output_dir)
    return output_dir/'chain_result.json'


def load_chain_result(path):
    path = Path(path).resolve()
    value = _json(path)
    if value.get('schema_version') != RESULT_VERSION or value.get('gate8_verdict') != 'NOT_RUN' or value.get('q0_status') != 'NOT_RUN':
        raise ValueError('CHAIN_VERSION_OR_QUALIFICATION_INVALID')
    resolved = [_resolve(path.parent,e) for e in value['files']]
    actual = {p.resolve() for p in path.parent.rglob('*') if p.is_file() and p != path}
    if len(resolved) != len(set(resolved)) or set(resolved) != actual:
        raise ValueError('CHAIN_FILE_SET_MISMATCH')
    report = _json(path.parent/'analysis/gate8_local_analysis.json')
    canonical = _json(path.parent/'canonical/canonical_manifest.json')
    if value['identity'] != canonical['identity']['values']:
        raise ValueError('CHAIN_IDENTITY_MISMATCH')
    provenance = path.parent/'provenance'
    if digest(provenance/'input_receipt.json') != value['input_receipt_sha256']:
        raise ValueError('CHAIN_INPUT_RECEIPT_HASH_MISMATCH')
    receipt = _json(provenance/'input_receipt.json')
    if receipt['identity'] != value['identity']:
        raise ValueError('CHAIN_INPUT_IDENTITY_MISMATCH')
    for role,item in receipt['artifacts'].items():
        if role not in ('raw','sqlite') and digest(provenance/f'{role}.json') != item['sha256']:
            raise ValueError('CHAIN_PROVENANCE_HASH_MISMATCH')
    if (canonical['source']['raw']['sha256'].lower() != receipt['artifacts']['raw']['sha256']
            or canonical['source']['sqlite']['sha256'].lower() != receipt['artifacts']['sqlite']['sha256']):
        raise ValueError('CHAIN_RAW_LINEAGE_MISMATCH')
    if any(value[k] != report[k] for k in ('status','validation_role','gate8_verdict','q0_status')):
        raise ValueError('CHAIN_REPORT_IDENTITY_MISMATCH')
    return value
