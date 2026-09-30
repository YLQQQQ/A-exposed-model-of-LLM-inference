"""Explicit P1 extension. Raw provenance never manufactures source callsites.

Only a uniquely mapped successful physical stream wait, wholly inside a
verified N1 model_forward and outside intervention markers, is eligible.
This evidence is independent of (and cannot replace) W/terminal recovery.
"""
import json
from functools import lru_cache
from pathlib import Path

from jsonschema import Draft202012Validator, ValidationError

VERSION = 'exposedpath-sync-provenance/0.1.0'
S_VERSION = 'exposedpath-s-layer/0.4.0'
EXTRA_FIELDS = {'sync_provenance'}
PREFIX = 'EXPOSEDPATH_N1_MODEL_V1:'


def _require(condition, reason):
    if not condition:
        raise ValueError('RAW_PROVENANCE_' + reason)


@lru_cache(maxsize=1)
def schema():
    path = Path(__file__).resolve().parents[1]/'docs/v1_4_1/contracts/sync_provenance_schema_v0_1.json'
    return json.loads(path.read_text(encoding='utf-8'))


def validate_provenance(record):
    value = record.get('sync_provenance')
    try:
        Draft202012Validator(schema()).validate(value)
    except ValidationError as error:
        raise ValueError('RAW_PROVENANCE_SCHEMA: ' + error.message) from error
    if value['basis']=='RAW_PHYSICAL':
        p = value['physical_source']
        _require(record.get('sync_origin') is None and record.get('callsite_id') is None
                 and record.get('sync_ordinal') is None, 'SOURCE_LABEL_CONFLICT')
        _require(record.get('sync_id')==p['sync_record_id'] and record.get('sync_kind')=='STREAM'
                 and record.get('request_id')==p['request_id']
                 and record.get('repeat_id')==p['repeat_id']
                 and record.get('sync_owner_phase')==p['phase'], 'IDENTITY_CONFLICT')
        start = record.get('host_start_ns', record.get('sync_start_ns'))
        end = record.get('host_end_ns', record.get('sync_end_ns'))
        _require(start==p['host_start_ns'] and end==p['host_end_ns']
                 and start<=p['physical_start_ns']<=p['physical_end_ns']<=end
                 and p['return_value']==0, 'CALL_CONFLICT')
        from .canonical_raw import _global_parts
        _require(_global_parts(p['global_pid'])[0]==p['process_id']
                 and p['global_tid']-p['global_tid']%2**24==p['global_pid'], 'PROCESS_CONFLICT')
        for key in ('device_id', 'context_id', 'stream_id'):
            if key in record:
                _require(record[key]==p[key], 'SCOPE_CONFLICT')


def _proof(bundle, inventory, sync):
    rows = bundle['records']
    api = next((a for a in rows['cuda_api'] if a['record_id']==sync.get('runtime_record_id')), None)
    _require(api is not None and sync.get('runtime_mapping_count')==1
             and api['correlation_id'] is not None and sync['correlation_id']==api['correlation_id']
             and api['return_value']==0, 'MAPPING_OR_SUCCESS')
    _require(sync['source_table']=='CUPTI_ACTIVITY_KIND_SYNCHRONIZATION'
             and api['source_table']=='CUPTI_ACTIVITY_KIND_RUNTIME'
             and sync['role']=='HOST_BLOCKING_SYNC' and sync['sync_kind']=='STREAM'
             and sync['sync_identity_status']=='INVALID'
             and sync['ownership_status']=='VALID'
             and not sync['ownership_reasons']
             and all(sync.get(k) is None for k in ('sync_origin','callsite_id','sync_ordinal')), 'SOURCE_CONFLICT')
    clock = api['clock_domain_id']
    from .canonical_raw import _global_parts
    _require(_global_parts(sync['global_pid'])[0]==api['process_id']
             and api['global_tid']-api['global_tid']%2**24==sync['global_pid'], 'PROCESS_CONFLICT')
    _require(sync['clock_domain_id']==clock and api['global_tid']==sync['runtime_global_tid']
             and api['start_ns']<=sync['start_ns']<=sync['end_ns']<=api['end_ns']
             and (sync['global_pid'],sync['device_id'],sync['context_id'],sync['stream_id'])
                 == inventory.get('isolated_nonblocking_scope'), 'SCOPE_OR_CLOCK')
    forwards=[]; interventions=[]
    for marker in rows['nvtx']:
        text = marker.get('text') or ''
        mstart, mend = marker['start_ns'], marker.get('end_ns')
        overlap = (mend is not None and mstart<api['end_ns'] and api['start_ns']<mend)
        identity = marker.get('structured_identity')
        if overlap and text.startswith('EXPOSEDPATH_JSON_V1:'):
            _require(isinstance(identity, dict) and identity.get('kind')!='sync', 'MARKER_CONFLICT')
        if not text.startswith(PREFIX):
            continue
        payload = json.loads(text[len(PREFIX):])
        if payload.get('operation')=='intervention' and overlap:
            interventions.append(marker)
        if (payload.get('operation')=='model_forward' and payload.get('schema_version')=='exposedpath-n1-model-calls/0.1.0'
                and payload.get('identity')=={k:v for k,v in sync['invocation_identity'].items()
                                              if k not in ('phase','kind')}
                and marker['global_tid']==api['global_tid'] and marker['clock_domain_id']==clock
                and mend is not None and mstart<=api['start_ns']<=api['end_ns']<=mend
                and payload.get('phase')==sync['sync_owner_phase']):
            forwards.append(marker)
    _require(len(forwards)==1 and not interventions, 'NOT_INTERNAL_FORWARD')
    refs = sync['ownership_range_record_ids']
    _require(refs and all(str(r).startswith('projection:') for r in refs), 'PROJECTED_OWNERSHIP')
    source = bundle['manifest']
    return dict(raw_sqlite_sha256=source['source']['sqlite']['sha256'],
        pass_identity_sha256=source['gate8_sources']['pass_identity']['sha256'],
        sync_record_id=sync['record_id'],sync_source_table=sync['source_table'],sync_source_rowid=sync['source_rowid'],
        api_record_id=api['record_id'],api_source_table=api['source_table'],api_source_rowid=api['source_rowid'],
        correlation_id=api['correlation_id'],process_id=api['process_id'],global_pid=sync['global_pid'],
        global_tid=api['global_tid'],clock_domain_id=clock,device_id=sync['device_id'],
        context_id=sync['context_id'],stream_id=sync['stream_id'],request_id=sync['request_id'],
        repeat_id=sync['repeat_id'],phase=sync['sync_owner_phase'],projection_record_ids=refs,
        model_forward_record_id=forwards[0]['record_id'],host_start_ns=api['start_ns'],host_end_ns=api['end_ns'],
        physical_start_ns=sync['start_ns'],physical_end_ns=sync['end_ns'],return_value=api['return_value'])


def attach_inventory_provenance(bundle, inventory, raw_sync_ids):
    _require(isinstance(raw_sync_ids, (set, frozenset)) and all(isinstance(s,str) for s in raw_sync_ids), 'IDS')
    _require(not raw_sync_ids or inventory.get('input_status')=='VALID', 'INPUT_QUALITY')
    by_id={s['record_id']:s for s in inventory['syncs']}
    _require(raw_sync_ids <= by_id.keys(), 'MISSING_SYNC')
    proofs={}
    for sync_id, s in by_id.items():
        basis = 'STRUCTURED' if (s['sync_identity_status']=='VALID' and
            all(s.get(k) is not None for k in ('sync_origin','callsite_id','sync_ordinal'))) else 'UNRESOLVED'
        physical_source=None
        if sync_id in raw_sync_ids and basis!='STRUCTURED':
            physical_source=_proof(bundle,inventory,s)
            basis='RAW_PHYSICAL'
        proofs[sync_id]=dict(schema_version=VERSION,basis=basis,physical_source=physical_source)
    inventory['sync_provenance']=proofs


def validate_source_join(canonical, record):
    """Recheck physical facts when serialized S records are consumed."""
    validate_provenance(record)
    p=record['sync_provenance']['physical_source']
    if p is None:
        return
    rows=canonical.records
    physical=[s for s in rows['cuda_sync'] if s['record_id']==p['sync_record_id']]
    api=canonical.cuda_api_by_id.get(p['api_record_id'])
    _require(len(physical)==1 and api is not None, 'SOURCE_RECORD_MISSING')
    s=physical[0]
    expected={
        'raw_sqlite_sha256':canonical.manifest['source']['sqlite']['sha256'],
        'pass_identity_sha256':canonical.manifest['gate8_sources']['pass_identity']['sha256'],
        'sync_source_table':s['source_table'],'sync_source_rowid':s['source_rowid'],
        'api_source_table':api['source_table'],'api_source_rowid':api['source_rowid'],
        'correlation_id':api['correlation_id'],'process_id':api['process_id'],
        'global_pid':s['global_pid'],'global_tid':api['global_tid'],'clock_domain_id':api['clock_domain_id'],
        'device_id':s['device_id'],'context_id':s['context_id'],'stream_id':s['stream_id'],
        'host_start_ns':api['start_ns'],'host_end_ns':api['end_ns'],
        'physical_start_ns':s['start_ns'],'physical_end_ns':s['end_ns'],'return_value':api['return_value'],
    }
    _require(all(p[k]==v for k,v in expected.items()) and s['runtime_record_id']==api['record_id']
             and s['runtime_mapping_count']==1, 'SOURCE_MISMATCH')
    # Replay source/ownership/forward evidence rather than trusting serialized
    # refs. This is local provenance validation, not a second W computation.
    from .sync_semantics import _normalize_sync
    ownership=list(canonical.projected_ownership or rows['nvtx'])
    actual=_normalize_sync(s,ownership)
    scope=(s['global_pid'],s['device_id'],s['context_id'],s['stream_id'])
    streams=[x for x in rows['stream'] if x['process_id']==api['process_id']
             and (x['context_id'],x['stream_id'])==scope[2:]]
    contexts=[x for x in rows['context'] if x['process_id']==api['process_id']
              and (x['device_id'],x['context_id'])==scope[1:3]]
    _require(len(streams)==len(contexts)==1 and streams[0]['flag']==2
             and type(contexts[0]['null_stream_id']) is int
             and contexts[0]['null_stream_id']!=s['stream_id'], 'NONBLOCKING_SCOPE')
    source_bundle={'manifest':canonical.manifest,'records':rows}
    _require(_proof(source_bundle,{'isolated_nonblocking_scope':scope},actual)==p, 'SOURCE_MISMATCH')
