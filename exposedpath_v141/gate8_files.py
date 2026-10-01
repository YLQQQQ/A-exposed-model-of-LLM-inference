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
DRAIN_RECEIPT_VERSION = 'exposedpath-gate8-input-receipt/0.2.0'
STAGE_RECEIPT_VERSION = 'exposedpath-gate8-input-receipt/0.3.0'
PILOT_RECEIPT_VERSION = 'exposedpath-pilot-input-receipt/0.1.0'
STAGE_RESULT_VERSION = 'exposedpath-gate8-file-chain/0.5.0'
CLOSED_RESULT_VERSION = 'exposedpath-gate8-file-chain/0.4.0'
RESULT_VERSION = 'exposedpath-gate8-file-chain/0.1.0'
SCOPED_RESULT_VERSION = 'exposedpath-gate8-file-chain/0.2.0'
CONTROLLED_RESULT_VERSION = 'exposedpath-gate8-file-chain/0.3.0'
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
    with_drains = 'drain_ledger' in paths
    with_stages = 'stage_ledger' in paths
    producer_version = 'exposedpath-gate8-producer-receipt/0.2.0' if with_drains else 'exposedpath-gate8-producer-receipt/0.1.0'
    producer_files = {'pass_identity.json','host_boundaries.json'} | ({'drain_ledger.json'} if with_drains else set())
    if with_stages:
        producer_version='exposedpath-gate8-producer-receipt/0.3.0'
        producer_files.add('stage_ledger.json')
        from exposedpath.gate8_stages import validate_stage_ledger
        validate_stage_ledger(_json(paths['stage_ledger']),ledger)
    if ledger['run_role']=='PILOT':
        from exposedpath.gate11_pilot import validate
        binding=validate(manifest)
        from exposedpath.gate11_warmup import active
        observed_warmups=active(binding)
        if (not with_stages or 'pilot_tokens' not in paths or ledger['pilot']!=binding
                or producer.get('pilot')!=binding or producer.get('run_role')!='PILOT'
                or producer.get('data_role')!='Pilot'
                or producer.get('gate11_verdict')!=('BLOCKED' if observed_warmups else 'NOT_RUN')):
            raise ValueError('PILOT_PRODUCER_BINDING')
        producer_version=('exposedpath-pilot-producer-receipt/0.2.0' if observed_warmups
                          else 'exposedpath-pilot-producer-receipt/0.1.0')
    if (producer.get('schema_version') != producer_version
            or any(producer.get(k) != ledger[k] for k in ('run_id','pass_id','attempt_id'))
            or producer.get('gate8_verdict') != 'NOT_RUN'
            or producer.get('status') != ('COMPLETE' if all(r['outcome']=='COMPLETE' for r in ledger['requests']) else 'INCOMPLETE')
            or set(producer.get('files',{})) != producer_files):
        raise ValueError('IDENTITY_CONFLICT: producer receipt')
    source_pairs = [('pass_identity','pass_identity.json'),('host_ledger','host_boundaries.json')]
    if with_drains:
        source_pairs.append(('drain_ledger','drain_ledger.json'))
    if with_stages:
        source_pairs.append(('stage_ledger','stage_ledger.json'))
    for key,name in source_pairs:
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
    if set(artifacts) not in (ARTIFACTS, ARTIFACTS | {'drain_ledger'}, ARTIFACTS | {'drain_ledger','stage_ledger'}, ARTIFACTS | {'drain_ledger','stage_ledger','pilot_tokens'}):
        raise ValueError('INPUT_ARTIFACT_SET_INVALID')
    if not isinstance(collector_version,str) or not collector_version or not isinstance(capture_session_id,str) or not capture_session_id:
        raise ValueError('COLLECTOR_SESSION_IDENTITY_MISSING')
    identity = _identities(artifacts)
    entries = {k:_entry(Path(p),output_path.parent) for k,p in artifacts.items()}
    if len({e['filename'] for e in entries.values()}) != len(entries):
        raise ValueError('INPUT_ARTIFACT_ALIAS')
    version = DRAIN_RECEIPT_VERSION if 'drain_ledger' in artifacts else RECEIPT_VERSION
    if 'stage_ledger' in artifacts:
        version=STAGE_RECEIPT_VERSION
    if identity['run_role']=='PILOT':
        version=PILOT_RECEIPT_VERSION
    elif 'pilot_tokens' in artifacts:
        raise ValueError('PILOT_ARTIFACT_ROLE_CONFLICT')
    _write(output_path, dict(schema_version=version, identity=identity, artifacts=entries,
                            collector_version=collector_version, capture_session_id=capture_session_id))
    return output_path


def load_input_receipt(path):
    path = Path(path).resolve()
    value = _json(path)
    expected_artifacts = ARTIFACTS | ({'drain_ledger'} if value.get('schema_version') in (DRAIN_RECEIPT_VERSION,STAGE_RECEIPT_VERSION) else set())
    if value.get('schema_version')==STAGE_RECEIPT_VERSION:
        expected_artifacts=expected_artifacts | {'stage_ledger'}
    if value.get('schema_version')==PILOT_RECEIPT_VERSION:
        expected_artifacts=ARTIFACTS | {'drain_ledger','stage_ledger','pilot_tokens'}
    if (set(value) != {'schema_version','identity','artifacts','collector_version','capture_session_id'}
            or value['schema_version'] not in (RECEIPT_VERSION,DRAIN_RECEIPT_VERSION,STAGE_RECEIPT_VERSION,PILOT_RECEIPT_VERSION) or set(value['artifacts']) != expected_artifacts):
        raise ValueError('INPUT_RECEIPT_VERSION_OR_SHAPE_INVALID')
    paths = {k:_resolve(path.parent,e) for k,e in value['artifacts'].items()}
    if value['identity'] != _identities(paths):
        raise ValueError('IDENTITY_CONFLICT: receipt')
    if (value['identity']['run_role']=='PILOT') != (value['schema_version']==PILOT_RECEIPT_VERSION):
        raise ValueError('PILOT_RECEIPT_VERSION')
    return value, paths


def process_gate8_receipt(receipt_path, output_dir, *, integrity_receipts_path=None, synthetic_fixture=False,
                          scope_assessment_path=None, controlled_sources=None, closed_prior_bindings_path=None):
    from .canonical_raw import convert_sqlite_to_canonical
    from .gate8_scope import project_completion_scopes
    from .gate8_analysis import analyze_gate8_local
    receipt_path, output_dir = Path(receipt_path).resolve(), Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)
    receipt, paths = load_input_receipt(receipt_path)
    with_stages='stage_ledger' in paths
    if with_stages and any(v is not None for v in (integrity_receipts_path,scope_assessment_path,
                                                  controlled_sources,closed_prior_bindings_path)):
        raise ValueError('STAGE_SOURCE_NOT_QUALIFIED: diagnostic-only entry cannot admit S/A/B')
    if not with_stages and ('drain_ledger' in paths) != (closed_prior_bindings_path is not None):
        raise ValueError('CLOSED_PRIOR_DRAIN_BINDINGS_REQUIRED')
    if closed_prior_bindings_path is not None and controlled_sources is not None:
        raise ValueError('CLOSED_PRIOR_CONTROLLED_PROFILE_CONFLICT')
    bindings_hash = None if closed_prior_bindings_path is None else digest(closed_prior_bindings_path)
    if any(p.is_relative_to(output_dir) for p in [receipt_path,*paths.values()]):
        raise ValueError('OUTPUT_CONTAINS_INPUT')
    receipt_hash = digest(receipt_path)
    controlled=None
    if controlled_sources is not None:
        from .gate8_controlled_evidence import ControlledEvidence
        if scope_assessment_path is not None or integrity_receipts_path is not None:
            raise ValueError('CONFLICTING_QUALITY_INPUTS')
        controlled=ControlledEvidence(receipt_path,controlled_sources)
    assessment, assessment_sources, assessment_hash = None, [], None
    if scope_assessment_path is not None:
        from .gate8_target_quality import load_assessment
        if integrity_receipts_path is not None:
            raise ValueError('CONFLICTING_QUALITY_INPUTS')
        assessment, assessment_sources = load_assessment(scope_assessment_path, receipt_hash, synthetic_fixture)
        assessment_hash = digest(scope_assessment_path)
    integrity = None if integrity_receipts_path is None else _json(integrity_receipts_path)
    integrity_hash = None if integrity_receipts_path is None else digest(integrity_receipts_path)
    output_dir.parent.mkdir(parents=True,exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{output_dir.name}-partial-',dir=output_dir.parent))
    provenance = staging/'provenance'
    provenance.mkdir()
    shutil.copyfile(receipt_path,provenance/'input_receipt.json')
    if controlled is not None:
        for key,path in controlled.sources.items():
            shutil.copyfile(path,provenance/f'controlled_{key}.json')
    if assessment is not None:
        shutil.copyfile(scope_assessment_path, provenance/'target_scope_assessment.json')
        for i, source in enumerate(assessment_sources):
            shutil.copyfile(source, provenance/f'target_evidence_{i}.json')
    for role, path in paths.items():
        if role not in ('raw','sqlite'):
            shutil.copyfile(path,provenance/f'{role}.json')
    # No catch-and-pass: failures leave only an uncommitted diagnostic staging tree.
    canonical = convert_sqlite_to_canonical(paths['sqlite'], staging/'canonical', 'Engineering',
        raw_sha256=digest(paths['raw']), collector_version=receipt['collector_version'],
        gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
    scope = project_completion_scopes(canonical, paths['host_ledger'], staging/'projection/scope.json')
    if with_stages:
        from .gate8_stage_scope import derive_stage_diagnostics
        _write(staging/'projection/stages.json',derive_stage_diagnostics(canonical,paths['stage_ledger']))
    closed_path = None
    if closed_prior_bindings_path is not None:
        from .gate8_closed_prior import VERSION
        bindings = _json(closed_prior_bindings_path)
        if (set(bindings) != {'schema_version','source_sqlite_sha256','lifetimes'}
                or bindings['schema_version'] != 'exposedpath-lifetime-bindings/0.1.0'
                or bindings['source_sqlite_sha256'] != digest(paths['sqlite'])):
            raise ValueError('CLOSED_PRIOR_BINDINGS_VERSION_OR_SOURCE')
        closed_dir = staging/'closed_prior'
        closed_dir.mkdir()
        shutil.copyfile(paths['drain_ledger'],closed_dir/'drain.json')
        shutil.copyfile(closed_prior_bindings_path,provenance/'lifetime_bindings.json')
        closed_path=closed_dir/'evidence.json'
        _write(closed_path,dict(schema_version=VERSION,canonical_manifest_sha256=digest(canonical),
            scope_sha256=digest(scope),drain_ledger={'filename':'drain.json','sha256':digest(paths['drain_ledger'])},
            lifetimes=bindings['lifetimes']))
    analysis = analyze_gate8_local(canonical,scope,staging/'analysis',capture_session_id=receipt['capture_session_id'],
                                  integrity_receipts=integrity,synthetic_fixture=synthetic_fixture,
                                  scope_assessment=assessment,controlled_evidence=controlled,
                                  closed_prior_manifest=closed_path)
    if controlled is not None:
        controlled.review()
        if any(digest(provenance/f'controlled_{k}.json')!=v for k,v in controlled.hashes.items()):
            raise ValueError('CONTROLLED_PROVENANCE_COPY_CONFLICT')
    if assessment is not None:
        load_assessment(scope_assessment_path, receipt_hash, synthetic_fixture)
        if digest(scope_assessment_path) != assessment_hash:
            raise ValueError('TARGET_SCOPE_CHANGED_DURING_PROCESSING')
        if digest(provenance/'target_scope_assessment.json') != assessment_hash:
            raise ValueError('TARGET_SCOPE_COPY_MISMATCH')
        for i, item in enumerate(assessment['evidence']):
            if digest(provenance/f'target_evidence_{i}.json') != item['sha256']:
                raise ValueError('TARGET_EVIDENCE_COPY_MISMATCH')
    load_input_receipt(receipt_path)
    if digest(receipt_path) != receipt_hash or (integrity_hash is not None and digest(integrity_receipts_path) != integrity_hash):
        raise ValueError('SOURCE_HASH_CHANGED_DURING_PROCESSING')
    report = _json(analysis)
    if with_stages and report['status']!='BLOCKED':
        raise ValueError('STAGE_SOURCE_NOT_QUALIFIED')
    if closed_path is not None:
        if (digest(closed_prior_bindings_path)!=bindings_hash or digest(provenance/'lifetime_bindings.json')!=bindings_hash
                or digest(closed_path.parent/'drain.json')!=digest(paths['drain_ledger'])):
            raise ValueError('CLOSED_PRIOR_SOURCE_CHANGED')
    files = [_entry(p,staging) for p in sorted(staging.rglob('*')) if p.is_file()]
    final = dict(schema_version=RESULT_VERSION, identity=receipt['identity'],
                 input_receipt_sha256=receipt_hash, integrity_input_sha256=integrity_hash,
                 status=report['status'], validation_role=report['validation_role'],
                 gate8_verdict='NOT_RUN', q0_status='NOT_RUN', files=files)
    if assessment is not None:
        final['schema_version'] = SCOPED_RESULT_VERSION
        final['target_scope_assessment_sha256'] = assessment_hash
    if controlled is not None:
        final['schema_version']=CONTROLLED_RESULT_VERSION
        final['controlled_source_hashes']=controlled.hashes
    if closed_path is not None:
        final['schema_version']=CLOSED_RESULT_VERSION
        final['closed_prior_bindings_sha256']=bindings_hash
        final['closed_prior_manifest_sha256']=digest(closed_path)
    if with_stages:
        final['schema_version']=STAGE_RESULT_VERSION
        final['stage_diagnostics_sha256']=digest(staging/'projection/stages.json')
    _write(staging/'chain_result.json',final)
    staging.rename(output_dir)
    return output_dir/'chain_result.json'


def load_chain_result(path):
    path = Path(path).resolve()
    value = _json(path)
    if value.get('schema_version') not in (RESULT_VERSION, SCOPED_RESULT_VERSION, CONTROLLED_RESULT_VERSION, CLOSED_RESULT_VERSION,STAGE_RESULT_VERSION) or value.get('gate8_verdict') != 'NOT_RUN' or value.get('q0_status') != 'NOT_RUN':
        raise ValueError('CHAIN_VERSION_OR_QUALIFICATION_INVALID')
    if value['schema_version'] != CLOSED_RESULT_VERSION and (value['schema_version'] == SCOPED_RESULT_VERSION) != ('target_scope_assessment_sha256' in value):
        raise ValueError('CHAIN_SCOPE_VERSION_CONFLICT')
    if (value['schema_version']==CONTROLLED_RESULT_VERSION)!=('controlled_source_hashes' in value):
        raise ValueError('CHAIN_CONTROLLED_VERSION_CONFLICT')
    resolved = [_resolve(path.parent,e) for e in value['files']]
    actual = {p.resolve() for p in path.parent.rglob('*') if p.is_file() and p != path}
    if len(resolved) != len(set(resolved)) or set(resolved) != actual:
        raise ValueError('CHAIN_FILE_SET_MISMATCH')
    report = _json(path.parent/'analysis/gate8_local_analysis.json')
    canonical = _json(path.parent/'canonical/canonical_manifest.json')
    if value['identity'] != canonical['identity']['values']:
        raise ValueError('CHAIN_IDENTITY_MISMATCH')
    provenance = path.parent/'provenance'
    # Choose the interpretation from the sealed input AND producer, never from
    # the result's self-declared version alone (including downgrade attacks).
    receipt = _json(provenance/'input_receipt.json')
    contracts = {
        RECEIPT_VERSION: (ARTIFACTS, {RESULT_VERSION,SCOPED_RESULT_VERSION,CONTROLLED_RESULT_VERSION},
                          'exposedpath-gate8-producer-receipt/0.1.0'),
        DRAIN_RECEIPT_VERSION: (ARTIFACTS | {'drain_ledger'}, {CLOSED_RESULT_VERSION},
                                'exposedpath-gate8-producer-receipt/0.2.0'),
        STAGE_RECEIPT_VERSION: (ARTIFACTS | {'drain_ledger','stage_ledger'}, {STAGE_RESULT_VERSION},
                                'exposedpath-gate8-producer-receipt/0.3.0'),
    }
    if receipt.get('schema_version') not in contracts:
        raise ValueError('CHAIN_INPUT_VERSION_INVALID')
    expected_artifacts, result_versions, producer_version = contracts[receipt['schema_version']]
    if set(receipt.get('artifacts',{})) != expected_artifacts or value['schema_version'] not in result_versions:
        raise ValueError('CHAIN_INPUT_RESULT_VERSION_OR_ARTIFACT_CONFLICT')
    producer = _json(provenance/'producer_receipt.json')
    producer_names={'pass_identity.json','host_boundaries.json'} | {
        name+'.json' for name in ('drain_ledger','stage_ledger') if name in expected_artifacts}
    if producer.get('schema_version')!=producer_version or set(producer.get('files',{}))!=producer_names:
        raise ValueError('CHAIN_PRODUCER_VERSION_OR_ARTIFACT_CONFLICT')
    for name, present in (('provenance/stage_ledger.json','stage_ledger' in expected_artifacts),
                          ('projection/stages.json','stage_ledger' in expected_artifacts),
                          ('provenance/drain_ledger.json','drain_ledger' in expected_artifacts),
                          ('closed_prior/evidence.json',receipt['schema_version']==DRAIN_RECEIPT_VERSION)):
        if (path.parent/name).is_file()!=present:
            raise ValueError('CHAIN_VERSION_ARTIFACT_PRESENCE_CONFLICT')
    if (value['schema_version']==STAGE_RESULT_VERSION)!=('stage_diagnostics_sha256' in value):
        raise ValueError('CHAIN_STAGE_VERSION_CONFLICT')
    if value['schema_version']==STAGE_RESULT_VERSION:
        from .gate8_stage_scope import derive_stage_diagnostics
        stage_path=path.parent/'projection/stages.json'
        if (digest(stage_path)!=value['stage_diagnostics_sha256'] or value['status']!='BLOCKED'
                or _json(stage_path)!=derive_stage_diagnostics(path.parent/'canonical/canonical_manifest.json',
                    provenance/'stage_ledger.json')):
            raise ValueError('CHAIN_STAGE_SOURCE_MISMATCH')
    if (value['schema_version']==CLOSED_RESULT_VERSION) != ('closed_prior_manifest_sha256' in value):
        raise ValueError('CHAIN_CLOSED_PRIOR_VERSION_CONFLICT')
    if value['schema_version']==CLOSED_RESULT_VERSION:
        proof_path=path.parent/'closed_prior/evidence.json'
        if (digest(proof_path)!=value['closed_prior_manifest_sha256']
                or digest(provenance/'lifetime_bindings.json')!=value['closed_prior_bindings_sha256']
                or report.get('closed_prior_manifest_sha256')!=value['closed_prior_manifest_sha256']
                or digest(path.parent/'closed_prior/drain.json')!=digest(provenance/'drain_ledger.json')):
            raise ValueError('CHAIN_CLOSED_PRIOR_HASH_MISMATCH')
        proof=_json(proof_path)
        if (proof['canonical_manifest_sha256']!=digest(path.parent/'canonical/canonical_manifest.json')
                or proof['scope_sha256']!=digest(path.parent/'projection/scope.json')):
            raise ValueError('CHAIN_CLOSED_PRIOR_SOURCE_MISMATCH')
    if 'controlled_source_hashes' in value:
        for key,sha in value['controlled_source_hashes'].items():
            if digest(provenance/f'controlled_{key}.json')!=sha:
                raise ValueError('CHAIN_CONTROLLED_HASH_CONFLICT')
        if (report.get('controlled_scope',{}).get('source_hashes')!=value['controlled_source_hashes']
                or report['controlled_scope'].get('input_receipt_sha256')!=value['input_receipt_sha256']):
            raise ValueError('CHAIN_CONTROLLED_REPORT_CONFLICT')
    if 'target_scope_assessment_sha256' in value:
        assessment = provenance/'target_scope_assessment.json'
        if digest(assessment) != value['target_scope_assessment_sha256']:
            raise ValueError('CHAIN_TARGET_SCOPE_HASH_MISMATCH')
        target = _json(assessment)
        expected_report = 'exposedpath-gate8-local-analysis/0.5.0' if value['schema_version']==CLOSED_RESULT_VERSION else 'exposedpath-gate8-local-analysis/0.3.0'
        if report.get('target_scope') != target or report.get('schema_version') != expected_report:
            raise ValueError('CHAIN_TARGET_SCOPE_REPORT_CONFLICT')
        if target['input_receipt_sha256'] != value['input_receipt_sha256']:
            raise ValueError('CHAIN_TARGET_SCOPE_INPUT_MISMATCH')
        for i, entry in enumerate(target['evidence']):
            if digest(provenance/f'target_evidence_{i}.json') != entry['sha256']:
                raise ValueError('CHAIN_TARGET_EVIDENCE_HASH_MISMATCH')
    if digest(provenance/'input_receipt.json') != value['input_receipt_sha256']:
        raise ValueError('CHAIN_INPUT_RECEIPT_HASH_MISMATCH')
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
