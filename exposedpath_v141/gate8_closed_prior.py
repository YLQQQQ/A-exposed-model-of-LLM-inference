"""Source-bound ownership admission, never truncation of physical wait sets.

Continuous source-owned, non-default streams only. Lifetime markers are producer
claims requiring target qualification; matching them is NOT measurement validity.
No SQLite, CUDA, clock fitting, inferred missing activity, or loss certification.
"""
from copy import deepcopy
import json
from pathlib import Path

from exposedpath.gate8_drain import DRAIN_PREFIX, DRAIN_VERSION
from exposedpath.gate8_identity import IDENTITY_FIELDS
from .gate8_adapter import digest

PROFILE = 'G8-CLOSED-PRIOR/0.1.0'
VERSION = 'exposedpath-closed-prior-evidence/0.1.0'
S_VERSION = 'exposedpath-s-layer/0.3.0'
AB_VERSION = 'exposedpath-ab/0.4.0'
EXTRA_FIELDS = {'ownership_profile', 'cross_request_dependency', 'activity_provenance'}
LIFETIME_PREFIX = 'EXPOSEDPATH_STREAM_LIFETIME_V1:'


def validate_provenance(record):
    from jsonschema import Draft202012Validator, ValidationError
    schema_path = Path(__file__).resolve().parents[1]/'docs/v1_4_1/contracts/s_layer_schema_v0_3.json'
    fields = json.loads(schema_path.read_text(encoding='utf-8'))['closed_prior_fields']
    try:
        for key, schema in fields.items():
            Draft202012Validator(schema).validate(record[key])
    except (KeyError, ValidationError) as exc:
        raise ValueError('CLOSED_PRIOR_PROVENANCE_SHAPE') from exc
    origins = record['activity_provenance']
    _require([p['activity_id'] for p in origins]==record['wait_set_activity_ids'], 'PROVENANCE_WAIT_SET')
    _require(len({p['activity_id'] for p in origins})==len(origins), 'PROVENANCE_DUPLICATE')
    _require(record['cross_request_dependency']==any(p['relation_to_sync']=='closed_prior_request' for p in origins), 'CROSS_REQUEST')
    for p in origins:
        same = (p['origin_identity']['request_id'],p['origin_identity']['repeat_id']) == (record['request_id'],record['repeat_id'])
        _require(same == (p['relation_to_sync']=='same_request'), 'PROVENANCE_OWNER')
        _require((p['drain_ref'] is None)==same, 'PROVENANCE_DRAIN')
        _require(p['activity_ref']['record_id']==p['activity_id'], 'PROVENANCE_ACTIVITY_REF')


def _require(condition, reason):
    if not condition:
        raise ValueError('CLOSED_PRIOR_' + reason)


def _key(identity):
    return tuple(identity.get(k) for k in IDENTITY_FIELDS) if identity else None


def _ref(row, source):
    return dict(source_sqlite_sha256=source,
                **{k: row[k] for k in ('record_id','source_table','source_rowid','clock_domain_id')})


class ClosedPriorAdmissions:
    def __init__(self, origins, pairs, source_sha):
        self.origins, self.pairs, self.source_sha = origins, pairs, source_sha

    def relation(self, activity, sync):
        return self.pairs.get((activity['record_id'], _key(sync.get('invocation_identity'))))

    def annotate(self, result, sync):
        provenance = []
        for aid in result['wait_set_activity_ids']:
            origin = deepcopy(self.origins[aid])
            drain = self.pairs.get((aid, _key(sync.get('invocation_identity'))))
            origin.update(relation_to_sync='closed_prior_request' if drain else 'same_request',
                          drain_ref=deepcopy(drain))
            provenance.append(origin)
        result.update(ownership_profile=PROFILE, activity_provenance=provenance,
                      cross_request_dependency=any(p['relation_to_sync']=='closed_prior_request' for p in provenance))
        return result


def load_admissions(path, canonical_path, scope_path, bundle, projections, inventory):
    from .gate8_scope import sidecar
    path = Path(path)
    value = json.loads(path.read_text(encoding='utf-8'))
    _require(set(value) == {'schema_version','canonical_manifest_sha256','scope_sha256','drain_ledger','lifetimes'}
             and value['schema_version'] == VERSION, 'VERSION_OR_SHAPE')
    _require(value['canonical_manifest_sha256'] == digest(canonical_path)
             and value['scope_sha256'] == digest(scope_path), 'SOURCE_HASH')
    ledger = sidecar(Path(canonical_path).parent, bundle['manifest']['gate8_sources']['pass_identity'])
    mapping = sidecar(Path(canonical_path).parent, bundle['manifest']['gate8_sources']['device_mapping'])
    drains = sidecar(path.parent, value['drain_ledger'])
    _require(set(drains)=={'schema_version','drains'} and drains['schema_version']==DRAIN_VERSION, 'DRAIN_VERSION')
    records = bundle['records']
    raw = {r['record_id']:r for rows in records.values() for r in rows}
    full = {_key(p['identity']):p for p in projections if p['phase']=='full_request'}
    anchors = {a['payload']['boundary_id']:a
               for a in json.loads(Path(scope_path).read_text(encoding='utf-8'))['anchors']}
    request_roles = {_key(r['identity']):r['request_role'] for r in ledger['requests']}
    source_sha = bundle['manifest']['source']['sqlite']['sha256']
    clock = bundle['manifest']['clock']['clock_domain_id']
    _require(len(value['lifetimes']) > 0, 'LIFETIME_MISSING')
    origins, stream_lives = {}, {}
    for item in value['lifetimes']:
        _require(set(item)=={'marker_record_id','binding_activity_id'}, 'LIFETIME_SHAPE')
        marker, binding = raw.get(item['marker_record_id']), raw.get(item['binding_activity_id'])
        _require(marker is not None and binding is not None and marker in records['nvtx']
                 and binding in records['device_activity'], 'LIFETIME_REF')
        _require(marker['text'].startswith(LIFETIME_PREFIX), 'LIFETIME_MARKER')
        payload = json.loads(marker['text'][len(LIFETIME_PREFIX):])
        _require(set(payload)=={'schema_version','generation','mode','logical_device','producer_source_sha256','identity'}
                 and payload['schema_version']=='exposedpath-stream-lifetime-marker/0.1.0'
                 and payload['mode']=='CONTINUOUS_OWNED'
                 and isinstance(payload['generation'],str) and bool(payload['generation']), 'LIFETIME_UNSUPPORTED')
        _require(payload['identity']=={k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')}
                 and payload['producer_source_sha256']==ledger['runner_source_sha256']
                 and type(payload['logical_device']) is int
                 and payload['logical_device']==mapping['gpu_index_logical'], 'LIFETIME_IDENTITY')
        scope = (binding['device_id'], binding['context_id'], binding['stream_id'])
        _require(scope not in stream_lives and binding['device_id']==mapping['trace_device_id'], 'LIFETIME_ALIAS')
        contexts = [r for r in records['context'] if r['context_id']==scope[1] and r['device_id']==scope[0]]
        streams = [r for r in records['stream'] if r['context_id']==scope[1] and r['stream_id']==scope[2]]
        _require(len(contexts)==1 and len(streams)==1 and contexts[0]['null_stream_id']!=scope[2], 'LIFETIME_CONTEXT_OR_DEFAULT')
        _require(contexts[0]['process_id']==streams[0]['process_id']==ledger['pid']
                 and contexts[0]['clock_domain_id']==streams[0]['clock_domain_id']==clock, 'LIFETIME_INVENTORY_SCOPE')
        _require(marker['process_id']==ledger['pid'] and marker['clock_domain_id']==clock
                 and type(marker['end_ns']) is int and marker['start_ns']<marker['end_ns'], 'LIFETIME_CLOCK')
        lifecycle_apis = ('cudaStreamCreate','cudaStreamDestroy','cudaDeviceReset',
                          'cuStreamCreate','cuStreamDestroy','cuCtxCreate','cuCtxDestroy',
                          'cuDevicePrimaryCtxReset','cuDevicePrimaryCtxRelease')
        # Raw Runtime rows do not expose resource handles. In this narrow
        # continuous-owned profile a lifecycle counterexample is not dismissible
        # as unrelated merely because its stream/context cannot be recovered.
        _require(not any(a['process_id']==ledger['pid']
            and a['start_ns']<marker['end_ns'] and marker['start_ns']<a['end_ns']
            and a['api_name'].startswith(lifecycle_apis) for a in records['cuda_api']), 'LIFETIME_COUNTEREVIDENCE')
        stream_lives[scope] = payload['generation']
        for activity in inventory['activities']:
            if (activity['device_id'],activity['context_id'],activity['stream_id']) != scope:
                continue
            identity = activity.get('invocation_identity')
            _require(activity['ownership_status']=='VALID' and _key(identity) in full, 'UNOWNED_HISTORY')
            _require(activity['clock_domain_id']==clock and activity['process_id']==ledger['pid']
                     and marker['start_ns']<=activity['enqueue_start_ns']<=activity['end_ns']<=marker['end_ns'], 'LIFETIME_RANGE')
            origins[activity['record_id']] = dict(activity_id=activity['record_id'],
                origin_identity={k:identity[k] for k in IDENTITY_FIELDS},
                origin_role=request_roles[_key(identity)], origin_phase=activity.get('origin_phase'),
                stream_generation=payload['generation'], lifetime_ref=_ref(marker,source_sha),
                activity_ref=_ref(activity,source_sha))
    # A narrow initial support domain, not an assertion that missing events do not exist.
    for event in [*inventory['event_records'], *inventory['dependency_events']]:
        _require(not any(event.get('context_id')==s[1] for s in stream_lives), 'EVENT_PATH_NOT_SUPPORTED')
    _require(set(origins)=={a['record_id'] for a in inventory['activities']}, 'UNBOUND_ACTIVITY_SCOPE')
    resolved_drains, operation_ids = {}, set()
    for entry in drains['drains']:
        _require(set(entry)=={'schema_version','operation_id','identity','logical_device','marker_role',
                             'thread_id','host_start_ns','host_end_ns','host_clock_id','status','error'}
                 and entry['schema_version']=='exposedpath-drain-marker/0.1.0'
                 and entry['marker_role']=='non_sync_marker'
                 and isinstance(entry['operation_id'],str) and bool(entry['operation_id'])
                 and type(entry['logical_device']) is int and type(entry['thread_id']) is int,
                 'DRAIN_SHAPE_OR_VERSION')
        from exposedpath.gate8_identity import validate_shape
        validate_shape('identity',entry['identity'])
        identity = entry['identity']
        key = _key(identity)
        _require(key in full and key not in resolved_drains and entry['operation_id'] not in operation_ids, 'DRAIN_IDENTITY')
        operation_ids.add(entry['operation_id'])
        _require(entry['status']=='COMPLETE' and entry['error'] is None
                 and type(entry['host_start_ns']) is int and type(entry['host_end_ns']) is int
                 and entry['host_start_ns']<=entry['host_end_ns']
                 and entry['logical_device']==mapping['gpu_index_logical'], 'DRAIN_FAILED')
        start_anchor = anchors[full[key]['start_boundary_id']]
        _require(entry.get('host_clock_id')==start_anchor['host_clock_id']=='PYTHON_PERF_COUNTER_NS'
                 and entry['host_end_ns']<=start_anchor['host_observed_ns'], 'DRAIN_HOST_CLOCK_OR_ORDER')
        payload = {k:entry[k] for k in ('schema_version','operation_id','identity','logical_device','marker_role')}
        markers = [r for r in records['nvtx'] if r['text'].startswith(DRAIN_PREFIX)
                   and json.loads(r['text'][len(DRAIN_PREFIX):])==payload]
        _require(len(markers)==1, 'DRAIN_MARKER_MISSING_OR_DUPLICATE')
        marker = markers[0]
        _require(marker['clock_domain_id']==clock and marker['process_id']==ledger['pid']
                 and marker['thread_id']==entry['thread_id'] and type(marker['end_ns']) is int, 'DRAIN_CLOCK_OR_THREAD')
        apis = [a for a in records['cuda_api'] if a['global_tid']==marker['global_tid']
                and marker['start_ns']<=a['start_ns']<=a['end_ns']<=marker['end_ns']]
        _require(len(apis)==1 and apis[0]['api_name']=='cudaDeviceSynchronize', 'DRAIN_API_MISSING_OR_AMBIGUOUS')
        api = apis[0]
        _require(api['return_value']==0 and api['clock_domain_id']==clock
                 and marker['end_ns']<=full[key]['start_ns'], 'DRAIN_RETURN_OR_CLOCK')
        physical = [s for s in records['cuda_sync'] if s['runtime_record_id']==api['record_id']]
        _require(len(physical)==1, 'DRAIN_PHYSICAL_SCOPE_MISSING_OR_AMBIGUOUS')
        scoped = physical[0]
        _require(scoped['runtime_mapping_count']==1 and scoped['process_id']==ledger['pid']
                 and scoped['clock_domain_id']==clock and scoped['device_id']==mapping['trace_device_id']
                 and all((s[0],s[1])==(scoped['device_id'],scoped['context_id']) for s in stream_lives)
                 and api['start_ns']<=scoped['start_ns']<=scoped['end_ns']<=api['end_ns'], 'DRAIN_PHYSICAL_SCOPE_CONFLICT')
        resolved_drains[key] = (api, scoped)
    _require(set(resolved_drains)==set(full), 'DRAIN_MISSING')
    pairs = {}
    for activity in inventory['activities']:
        origin = origins[activity['record_id']]
        own = full[_key(activity['invocation_identity'])]
        for key, target in full.items():
            if _key(activity['invocation_identity'])==key or own['start_ns']>=target['start_ns']:
                continue
            drain, scoped = resolved_drains[key]
            _require(own['end_ns']<=drain['start_ns'] and activity['end_ns']<=drain['end_ns']
                     and activity['enqueue_end_ns']<=drain['start_ns'], 'PRIOR_NOT_CLOSED')
            # The physical record links back to the matched Runtime API and
            # preserves device/context scope. The marker alone cannot do this.
            pairs[(activity['record_id'],key)] = _ref(scoped,source_sha)
        activity['_closed_prior_generation'] = origin['stream_generation']
    return ClosedPriorAdmissions(origins,pairs,digest(path))
