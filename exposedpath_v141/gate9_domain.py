"""Versioned domain admission over immutable file evidence; not a Gate verdict."""
from pathlib import Path
import json
import tempfile

from .gate8_adapter import digest
from .gate8_files import load_input_receipt, _json, _write, _entry, _resolve

VERSION = 'exposedpath-domain-qualification/0.1.0'
CONTRACT = 'G9-DOMAIN-QUALIFICATION/0.1.0'
G1 = 'G1_NATURAL_PROJECTED_A/0.1.0'
N1 = 'N1_EXPLICIT_STREAM_AB/0.1.0'


def require(ok, reason):
    if not ok: raise ValueError('DOMAIN_' + reason)


def declaration(profile):
    require(profile in (G1, N1), 'PROFILE')
    return dict(contract=CONTRACT, profile=profile, declaration_role='PRE_EXECUTION')


def _calculate(root, receipt_path, execution_path, bridge_path=None):
    receipt, paths = load_input_receipt(receipt_path)
    declared = _json(paths['wmpc_manifest']).get('domain_qualification')
    require(isinstance(declared, dict) and declared == declaration(declared.get('profile')), 'DECLARATION')
    require(receipt['identity']['run_role']=='ENGINEERING', 'ROLE_NOT_QUALIFIED')
    if declared['profile']==N1:
        from .gate9_n1 import calculate_n1
        return calculate_n1(root, receipt_path, execution_path, bridge_path)
    require(bridge_path is None, 'G1_BRIDGE_FORBIDDEN')
    from . import gate8_engineering_scope as old
    from .gate8_scope import load_projected_ownership, build_projected_ab_inputs
    from .gate8_stage_scope import derive_stage_diagnostics
    from .gate8_diagnostic_scope import load_diagnostic_scope
    from .sync_semantics import load_canonical_bundle
    from .time_representation import SIGNED, time_representation
    from .b_provenance import calculate_b_syncs
    _, paths, support, execution = old._inputs(receipt_path, execution_path)
    canonical, scope = root/'canonical/canonical_manifest.json', root/'projection/scope.json'
    bundle=load_canonical_bundle(canonical)
    for marker in bundle['records']['nvtx']:
        text=marker.get('text') or ''
        if text.startswith('EXPOSEDPATH_JSON_V1:'):
            payload=json.loads(text.split(':',1)[1])
            if payload.get('kind')=='sync':
                require(payload.get('sync_origin')=='natural_token_ready'
                    and not any(k in payload for k in ('intervention_variant_id','intervention_ordinal')),
                    'G1_INTERVENTION_CONFLICT')
    require(bundle['manifest']['source']['sqlite']['sha256'].lower()==digest(paths['sqlite']), 'SOURCE')
    ownership, projections=load_projected_ownership(canonical,bundle,scope)
    stage=derive_stage_diagnostics(canonical,paths['stage_ledger'])
    diagnostic=load_diagnostic_scope(root/'diagnostics.json',paths['sqlite'],paths['pass_identity'])
    diagnostics=old._diagnostics(diagnostic)
    from .gate9_diagnostic_review import review
    diagnostic_review=review(diagnostic,bundle)
    accepted=set(diagnostic_review['accepted_rowids']) if diagnostic_review else set()
    effective=[d for d in diagnostics if d['source_rowid'] not in accepted]
    with time_representation(SIGNED):
        original=build_projected_ab_inputs(canonical,scope)
        requests=[old._request(canonical,scope,paths,bundle,ownership,p,original,stage,support,effective,
                              domain_proof=True) for p in projections if p['phase']=='full_request']
        physical_b=list(calculate_b_syncs(original))
    require(requests, 'NO_REQUESTS')
    for r in requests:
        if r['status']=='A_SCOPE_ENGINEERING_ONLY':
            r['status']='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
        r['qualification_action']='REUSE_PROFILE_CHECK_EACH_REQUEST'
        r['explanation_status']=('REJECTED' if not r['a_records'] else
            'LOCALLY_INCOMPLETE' if any(a['A_unattributed_ns'] for a in r['a_records']) else
            'SUPPORTED_ACCOUNTING_NOT_SCIENTIFIC_VALIDITY')
    return dict(schema_version=VERSION, declaration=declared, identity=receipt['identity'],
        status='QUALITY_CHECK_PASSED_NOT_QUALIFICATION' if all(r['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION' for r in requests) else 'BLOCKED',
        input_receipt_sha256=digest(Path(receipt_path)), execution_receipt_sha256=digest(Path(execution_path)),
        requests=requests, physical_s_records=list(original.s_records), physical_b_records=physical_b,
        diagnostic_dispositions=diagnostics, dropped_records_status='UNKNOWN', measurement_validity='NOT_ASSESSED',
        formal_eligible=False, gate9_verdict='NOT_RUN', d_score_allowed=False, signature_allowed=False,
        **({'diagnostic_review':diagnostic_review} if diagnostic_review is not None else {}))


def process_domain(receipt_path, execution_path, output_dir, *, bridge_path=None):
    output=Path(output_dir).resolve()
    if output.exists(): raise FileExistsError(output)
    receipt,paths=load_input_receipt(receipt_path)
    decl=_json(paths['wmpc_manifest']).get('domain_qualification')
    require(isinstance(decl,dict) and decl==declaration(decl.get('profile')), 'DECLARATION')
    inputs=[Path(receipt_path),Path(execution_path),*paths.values()]
    if bridge_path is not None: inputs.append(Path(bridge_path))
    require(not any(p.resolve().is_relative_to(output) for p in inputs), 'OUTPUT_CONTAINS_INPUT')
    hashes={p:digest(p) for p in inputs}
    output.parent.mkdir(parents=True,exist_ok=True)
    root=Path(tempfile.mkdtemp(prefix='.'+output.name+'-partial-',dir=output.parent))
    from .canonical_raw import convert_sqlite_to_canonical
    from .gate8_scope import project_completion_scopes
    from .gate8_diagnostic_scope import write_diagnostic_scope
    canonical=convert_sqlite_to_canonical(paths['sqlite'],root/'canonical','Engineering',
        raw_sha256=digest(paths['raw']),collector_version=receipt['collector_version'],
        gate8_sources={k:paths[k] for k in ('pass_identity','preflight','cuda_probe')})
    project_completion_scopes(canonical,paths['host_ledger'],root/'projection/scope.json')
    write_diagnostic_scope(paths['sqlite'],paths['pass_identity'],root/'diagnostics.json')
    result=_calculate(root,receipt_path,execution_path,bridge_path)
    require(all(digest(p)==h for p,h in hashes.items()), 'SOURCE_CHANGED')
    result['files']=[_entry(p,root) for p in sorted(root.rglob('*')) if p.is_file()]
    _write(root/'domain.json',result)
    root.rename(output)
    return output/'domain.json'


def load_domain(result_path, receipt_path, execution_path, *, bridge_path=None):
    path=Path(result_path); saved=_json(path)
    require(saved.get('schema_version')==VERSION, 'RESULT_VERSION')
    files=[_resolve(path.parent,r) for r in saved['files']]
    require(len(set(files))==len(files) and set(files)=={p.resolve() for p in path.parent.rglob('*') if p.is_file() and p!=path}, 'FILE_SET')
    actual=_calculate(path.parent,receipt_path,execution_path,bridge_path)
    require({k:v for k,v in saved.items() if k!='files'}==actual, 'RESULT_MISMATCH')
    return saved
