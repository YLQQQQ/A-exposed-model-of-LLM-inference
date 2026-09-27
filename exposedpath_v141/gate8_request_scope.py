"""Versioned A-only prefix-bound proof. Never a physical W/B replacement.

The only admitted source qualification is a synthetic controlled oracle. Real
producer coverage is deliberately unimplemented, rather than inferred from the
absence of Raw records. Frozen readers and S/A/B calculations are unchanged.
"""
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path

from exposedpath.gate8_drain import DRAIN_PREFIX, DRAIN_VERSION
from .gate8_adapter import digest
from .gate8_scope import build_projected_ab_inputs, load_projected_ownership, sidecar
from .sync_semantics import (load_canonical_bundle, build_semantic_inventory,
                             analyze_sync_semantics, classify_cuda_api)
from .time_representation import SIGNED, time_representation

PROFILE = 'G8-REQUEST-DRAIN-SCOPE/0.1.0'
CERTIFICATE_VERSION = 'exposedpath-request-prefix-certificate/0.1.0'
RESULT_VERSION = 'exposedpath-request-a-scope/0.1.0'
PROOF_FIELDS = {'prefix_producers_closed', 'no_late_relevant_submission',
                'request_dependency_records_complete', 'resource_lifetime_continuous'}


def require(ok, reason):
    if not ok:
        raise ValueError('REQUEST_SCOPE_' + reason)


def _same_request(observed, expected):
    return isinstance(observed, dict) and all(observed.get(k)==v for k,v in expected.items())


def _drain(certificate_path, cert, bundle, projection, scope, canonical_root):
    """Join producer observation -> trace marker -> API -> physical scope."""
    drains = sidecar(certificate_path.parent, cert['drain_ledger'])
    require(set(drains)=={'schema_version', 'drains'} and drains['schema_version']==DRAIN_VERSION,
            'DRAIN_VERSION')
    entries = [d for d in drains['drains'] if d.get('identity')==projection['identity']]
    require(len(entries)==1, 'DRAIN_IDENTITY')
    entry = entries[0]
    require(set(entry)=={'schema_version','operation_id','identity','logical_device','marker_role',
                        'thread_id','host_start_ns','host_end_ns','host_clock_id','status','error'}
            and entry['schema_version']=='exposedpath-drain-marker/0.1.0'
            and entry['marker_role']=='non_sync_marker', 'DRAIN_SHAPE')
    records = bundle['records']
    ledger = sidecar(canonical_root, bundle['manifest']['gate8_sources']['pass_identity'])
    mapping = sidecar(canonical_root, bundle['manifest']['gate8_sources']['device_mapping'])
    anchor = next(a for a in json.loads(Path(scope).read_text(encoding='utf-8'))['anchors']
                  if a['payload']['boundary_id']==projection['start_boundary_id'])
    require(entry['status']=='COMPLETE' and entry['error'] is None
            and type(entry['host_start_ns']) is int and type(entry['host_end_ns']) is int
            and entry['host_start_ns']<=entry['host_end_ns']<=anchor['host_observed_ns']
            and entry['host_clock_id']==anchor['host_clock_id']=='PYTHON_PERF_COUNTER_NS'
            and type(entry['logical_device']) is int
            and entry['logical_device']==mapping['gpu_index_logical'], 'DRAIN_HOST_OR_STATUS')
    payload = {k:entry[k] for k in ('schema_version','operation_id','identity','logical_device','marker_role')}
    markers = [r for r in records['nvtx'] if (r.get('text') or '').startswith(DRAIN_PREFIX)
               and json.loads(r['text'][len(DRAIN_PREFIX):])==payload]
    require(len(markers)==1, 'DRAIN_MARKER')
    marker = markers[0]
    clock = projection['clock_domain_id']
    require(marker['clock_domain_id']==clock and marker['process_id']==ledger['pid']
            and marker['thread_id']==entry['thread_id']
            and type(marker['end_ns']) is int and marker['end_ns']<=projection['start_ns'], 'DRAIN_CLOCK_THREAD')
    apis = [a for a in records['cuda_api'] if a['global_tid']==marker['global_tid']
            and marker['start_ns']<=a['start_ns']<=a['end_ns']<=marker['end_ns']]
    require(len(apis)==1 and classify_cuda_api(apis[0]['api_name'])['registry_rule_id']=='SYNC-DEVICE-RUNTIME-001',
            'DRAIN_API')
    api = apis[0]
    require(api['return_value']==0 and api['clock_domain_id']==clock, 'DRAIN_RETURN')
    physical = [s for s in records['cuda_sync'] if s['runtime_record_id']==api['record_id']]
    require(len(physical)==1, 'DRAIN_PHYSICAL')
    physical = physical[0]
    require(physical['runtime_mapping_count']==1 and physical['process_id']==ledger['pid']
            and physical['device_id']==mapping['trace_device_id']
            and physical['context_id'] is not None and physical['clock_domain_id']==clock
            and api['start_ns']<=physical['start_ns']<=physical['end_ns']<=api['end_ns'], 'DRAIN_SCOPE')
    return api, physical


def _calculate(canonical_path, scope_path, certificate_path, synthetic_fixture):
    require(synthetic_fixture is True, 'SOURCE_NOT_QUALIFIED')
    cert = json.loads(certificate_path.read_text(encoding='utf-8'))
    require(set(cert)=={'schema_version','canonical_manifest_sha256','scope_sha256',
                       'request_id','drain_ledger','source_proof'}
            and cert['schema_version']==CERTIFICATE_VERSION, 'CERTIFICATE_VERSION_OR_SHAPE')
    require(cert['canonical_manifest_sha256']==digest(canonical_path)
            and cert['scope_sha256']==digest(scope_path), 'SOURCE_HASH')
    proof = cert['source_proof']
    require(isinstance(proof,dict) and set(proof)==PROOF_FIELDS|{'basis'}
            and proof['basis']=='SYNTHETIC_CONTROLLED_ORACLE'
            and all(proof[k] is True for k in PROOF_FIELDS), 'SOURCE_PROOF')
    bundle = load_canonical_bundle(canonical_path)
    ownership, projections = load_projected_ownership(canonical_path, bundle, scope_path)
    selected = [p for p in projections if p['phase']=='full_request'
                and p['identity']['request_id']==cert['request_id']]
    require(len(selected)==1, 'REQUEST_IDENTITY')
    projection = selected[0]
    # Sidecars belong to Canonical, not necessarily to the projection directory.
    drain_api, drain = _drain(certificate_path, cert, bundle, projection, scope_path, canonical_path.parent)
    inventory = build_semantic_inventory({**bundle, 'ownership_records': ownership})
    require(inventory['input_status']=='VALID', 'INPUT_QUALITY')
    require(not inventory['event_records'] and not inventory['dependency_events'], 'EVENT_PATH_NOT_SUPPORTED')
    start, end = projection['start_ns'], projection['end_ns']
    clock = projection['clock_domain_id']
    prefix, suffix = [], []
    for activity in inventory['activities']:
        require(activity['process_id']==drain['process_id']
                and activity['device_id']==drain['device_id'] and activity['context_id']==drain['context_id']
                and activity['clock_domain_id']==clock, 'ACTIVITY_SCOPE')
        enqueue_start, enqueue_end = activity.get('enqueue_start_ns'), activity.get('enqueue_end_ns')
        require(type(enqueue_start) is int and type(enqueue_end) is int, 'SUBMISSION_MISSING')
        require(enqueue_start<=activity['start_ns']<=activity['end_ns'], 'ACTIVITY_TIME_ORDER')
        if enqueue_end<=drain_api['start_ns']:
            require(activity['end_ns']<=drain['end_ns'], 'PREFIX_NOT_COMPLETE')
            prefix.append(activity)
        else:
            require(start<=enqueue_start<=enqueue_end<=end
                    and _same_request(activity.get('invocation_identity'),projection['identity']), 'LATE_OR_EXTERNAL_SUBMISSION')
            suffix.append(activity)
    contexts = [c for c in inventory['contexts'] if c['context_id']==drain['context_id']]
    require(len(contexts)==1, 'CONTEXT_AMBIGUOUS')
    # Initial support domain is explicit, continuous non-default streams. No
    # inference that a NULL stream's unknown TU mode is equivalent to this case.
    # Complete synthetic source proof + no NULL-stream activities is required;
    # mode remains untouched and is checked by S whenever it affects a closure.
    require(all(a['stream_id']!=contexts[0]['null_stream_id'] for a in prefix+suffix), 'DEFAULT_STREAM_NOT_SUPPORTED')
    history_start = min([drain_api['start_ns'], *[a['enqueue_start_ns'] for a in prefix]])
    for api in bundle['records']['cuda_api']:
        if history_start <= api['start_ns'] < end:
            require(not any(word in api['api_name'] for word in ('Create','Destroy','Reset','SetDevice')),
                    'RESOURCE_LIFETIME_CONFLICT')
        if drain_api['end_ns'] < api['end_ns'] and api['start_ns'] < end:
            require(start<=api['start_ns']<=api['end_ns']<=end
                    and api['global_tid']==drain_api['global_tid'] and api['return_value']==0
                    and api['clock_domain_id']==clock, 'LATE_OR_EXTERNAL_API')
    # Keep the physical inventory/results untouched. The reduced inventory is
    # only a proof of the A intersection after the certified completion bound.
    restricted = deepcopy(inventory)
    restricted['activities'] = deepcopy(suffix)
    selected_syncs = [s for s in inventory['syncs']
                      if _same_request(s.get('invocation_identity'),projection['identity'])]
    require(selected_syncs, 'SYNC_MISSING')
    for sync in selected_syncs:
        require(all(sync.get(k)==drain[k] for k in ('process_id','device_id','context_id','clock_domain_id'))
                and sync.get('runtime_global_tid')==drain_api['global_tid']
                and sync.get('runtime_mapping_count')==1
                and type(sync.get('host_start_ns')) is int and type(sync.get('host_end_ns')) is int
                and start<=sync['host_start_ns']<=sync['host_end_ns']<=end, 'SYNC_SCOPE')
    suffix_s = tuple(analyze_sync_semantics(restricted,s) for s in selected_syncs)
    require(all(s['validity'] in {'VALID_NONEMPTY','VALID_EMPTY'} for s in suffix_s), 'SUFFIX_NOT_QUALIFIED')
    original = build_projected_ab_inputs(canonical_path, scope_path)
    require(not original.global_quality_reasons, 'GLOBAL_QUALITY')
    a_inputs = replace(original, s_records=suffix_s,
                       windows=tuple(w for w in original.windows if w.request_id==cert['request_id']))
    from .a_accounting import calculate_a_windows
    from .b_provenance import calculate_b_syncs
    a = calculate_a_windows(a_inputs)
    require(len(a)==3 and all(r['A_unattributed_ns']==0 and r['primary_reason'] is None for r in a),
            'A_NOT_QUALIFIED')
    source = bundle['manifest']['source']['sqlite']['sha256']
    def ref(row):
        return {'source_sqlite_sha256':source, **{k:row[k] for k in
                ('record_id','source_table','source_rowid','clock_domain_id')}}
    return dict(schema_version=RESULT_VERSION, observation_profile=PROFILE,
        canonical_manifest_sha256=digest(canonical_path), scope_sha256=digest(scope_path),
        certificate_sha256=digest(certificate_path), identity=projection['identity'],
        validation_role='SYNTHETIC_REGRESSION_ONLY', measurement_validity='NOT_ASSESSED',
        dropped_records_status='UNKNOWN', a_qualification='A_SCOPE_CERTIFIED',
        d_score_allowed=False, signature_allowed=False, drain_ref=ref(drain),
        prefix_activity_refs=[ref(a) for a in prefix],
        a_suffix_proof=[{'sync_id':s['sync_id'], 'suffix_activity_ids':s['wait_set_activity_ids'],
                         'scope':'A_INTERSECTION_ONLY_NOT_PHYSICAL_W'} for s in suffix_s],
        a_records=list(a), physical_s_records=list(original.s_records),
        physical_b_records=list(calculate_b_syncs(original)))


def analyze_request_scope(canonical_path, scope_path, certificate_path, output_path, *, synthetic_fixture=False):
    """New output only, all checks before writing; real source admission closed."""
    paths = tuple(Path(p) for p in (canonical_path,scope_path,certificate_path))
    output = Path(output_path)
    require(not output.exists(), 'OUTPUT_EXISTS')
    with time_representation(SIGNED):
        result = _calculate(*paths, synthetic_fixture)
    # Exclusive create cannot replace inputs or another writer's result.
    with output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2, ensure_ascii=False)
        stream.write('\n')
    return result


def load_request_scope(result_path, canonical_path, scope_path, certificate_path, *, synthetic_fixture=False):
    """Explicit new reader rederives evidence; never accepted by AB/Derived."""
    saved = json.loads(Path(result_path).read_text(encoding='utf-8'))
    require(saved.get('schema_version')==RESULT_VERSION, 'RESULT_VERSION')
    with time_representation(SIGNED):
        actual = _calculate(*(Path(p) for p in (canonical_path,scope_path,certificate_path)), synthetic_fixture)
    require(saved==actual, 'RESULT_MISMATCH')
    return saved
