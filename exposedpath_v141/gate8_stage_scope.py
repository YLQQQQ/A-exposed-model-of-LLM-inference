"""Trace-clock host stage associations. Never an input to S ownership or A windows."""
import json
from pathlib import Path
from exposedpath.gate8_stages import STAGE_PREFIX, validate_stage_ledger
from .gate8_adapter import digest
from .gate8_scope import sidecar


def derive_stage_diagnostics(canonical_path, stage_path):
    from .sync_semantics import load_canonical_bundle
    canonical_path, stage_path = Path(canonical_path), Path(stage_path)
    bundle=load_canonical_bundle(canonical_path)
    manifest,records=bundle['manifest'],bundle['records']
    ledger=sidecar(canonical_path.parent,manifest['gate8_sources']['pass_identity'])
    mapping=sidecar(canonical_path.parent,manifest['gate8_sources']['device_mapping'])
    stages=json.loads(stage_path.read_text(encoding='utf-8'))
    validate_stage_ledger(stages,ledger)
    if ledger['pass_id']!='pass1':
        raise ValueError('STAGE_TRACE_REQUIRES_PASS1')
    source=manifest['source']['sqlite']['sha256']
    clock=manifest['clock']['clock_domain_id']
    def ref(row):
        return dict(source_sqlite_sha256=source,
            **{k:row[k] for k in ('record_id','source_table','source_rowid','clock_domain_id')})
    markers=[r for r in records['nvtx'] if r['text'].startswith(STAGE_PREFIX)]
    if len(markers)!=len(stages['stages']):
        raise ValueError('STAGE_TRACE_MARKER_SET')
    output=[]
    used=set()
    previous=None
    for entry in stages['stages']:
        if entry['payload']['logical_device']!=mapping['gpu_index_logical']:
            raise ValueError('STAGE_DEVICE_MAPPING_CONFLICT')
        matches=[r for r in markers if json.loads(r['text'][len(STAGE_PREFIX):])==entry['payload']]
        if len(matches)!=1:
            raise ValueError('STAGE_TRACE_MARKER_IDENTITY')
        row=matches[0]
        if (row['record_id'] in used or row['process_id']!=ledger['pid']
                or row['thread_id']!=entry['thread_id'] or row['clock_domain_id']!=clock
                or type(row['end_ns']) is not int or row['end_ns']<row['start_ns']
                or (previous is not None and previous>row['start_ns'])):
            raise ValueError('STAGE_TRACE_SCOPE_CONFLICT')
        previous=row['end_ns']
        used.add(row['record_id'])
        same,unresolved=[],[]
        for api in records['cuda_api']:
            if api['process_id']!=ledger['pid']:
                continue
            if api['clock_domain_id']!=clock:
                raise ValueError('STAGE_TRACE_CLOCK_CONFLICT')
            if not api['start_ns']<row['end_ns'] or not row['start_ns']<api['end_ns']:
                continue
            if (api['thread_id']==row['thread_id']
                    and row['start_ns']<=api['start_ns']<=api['end_ns']<=row['end_ns']):
                same.append(ref(api))
            else:
                unresolved.append(dict(api_ref=ref(api),reason='OTHER_THREAD_OWNERSHIP_UNKNOWN'
                    if api['thread_id']!=row['thread_id'] else 'CROSSES_STAGE_BOUNDARY'))
        output.append(dict(payload=entry['payload'],raw_ref=ref(row),
            trace_start_ns=row['start_ns'],trace_end_ns=row['end_ns'],
            scope_semantics='HOST_CALL_ONLY',same_thread_api_refs=same,
            unresolved_submissions=unresolved,ownership_status='NOT_ASSESSED'))
    return dict(schema_version='exposedpath-stage-diagnostics/0.1.0',
        canonical_manifest_sha256=digest(canonical_path),stage_ledger_sha256=digest(stage_path),
        stages=output,measurement_validity='NOT_ASSESSED',stream_lifetime_status='UNKNOWN',
        default_stream_mode='UNKNOWN',qualification_reason='STAGE_SOURCE_NOT_QUALIFIED')
