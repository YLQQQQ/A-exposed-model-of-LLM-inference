"""Fair activity-cost baseline, NOT exposure accounting or a second S layer."""
from collections import defaultdict
from pathlib import Path
from .a_api_classification import _classify,VERSION,OPAQUE_VERSION
from .sync_semantics import classify_cuda_api
import sqlite3

SCHEMA_VERSION='exposedpath-activity-baseline/0.1.0'


def require(ok,reason):
    if not ok: raise ValueError('BASELINE_'+reason)


def union(intervals):
    end=None; total=0
    for a,b in sorted(intervals):
        if end is None or a>=end:total+=b-a
        elif b>end:total+=b-end
        end=max(end,b) if end is not None else b
    return total


def calculate(api,activities,scope,owned_ids,*,registry_version):
    """Counts intersecting physical records, sums clipped duration, unions per layer.

    owned_ids must come from the already validated request adapter, not overlap.
    A missing owner leaves affected totals unknown and preserves observed records.
    """
    require(registry_version in (VERSION,OPAQUE_VERSION),'REGISTRY_VERSION')
    require(scope['identity'].get('pass_id')=='pass1' and scope['phase'] in ('full_request','prefill','decode'),'SCOPE')
    start,end=scope['start_ns'],scope['end_ns']
    require(type(start) is int and type(end) is int and -(2**63)<=start<end<2**63 and end-start<2**63,'TIME_RANGE')
    records=api+activities
    require(len({r['record_id'] for r in records})==len(records),'DUPLICATE_RECORD')
    for r in records:
        require(type(r['start_ns']) is int and type(r['end_ns']) is int and
            -(2**63)<=r['start_ns']<=r['end_ns']<2**63 and r['end_ns']-r['start_ns']<2**63,'TIME_RANGE')
        if r['process_id']==scope['process_id']:
            require(r['clock_domain_id']==scope['clock_domain_id'],'CLOCK_CONFLICT')
    def member(r,host=False):
        return (r['process_id']==scope['process_id'] and (not host or r['thread_id']==scope['thread_id'])
            and r['start_ns']<end and start<r['end_ns'])
    selected_api=[r for r in api if member(r,True)]
    selected_dev=[r for r in activities if member(r)]
    def metrics(rows):
        if any(r['record_id'] not in owned_ids for r in rows):
            return dict(count=None,sum_ns=None,union_ns=None,status='OWNERSHIP_UNKNOWN')
        intervals=[(max(start,r['start_ns']),min(end,r['end_ns'])) for r in rows]
        return dict(count=len(rows),sum_ns=sum(b-a for a,b in intervals),union_ns=union(intervals),status='KNOWN')
    sync=[r for r in selected_api if classify_cuda_api(r['api_name'])['role']=='HOST_BLOCKING_SYNC']
    unknown_api=[r['record_id'] for r in selected_api if _classify(r['api_name'],registry_version)[0] is None
                 and r not in sync]
    non_sync=[r for r in selected_api if r not in sync and r['record_id'] not in unknown_api]
    mapping=[]
    dev_by=defaultdict(list); api_by=defaultdict(list)
    for d in activities:
        if d.get('correlation_id') is not None:dev_by[d['process_id'],d['correlation_id']].append(d)
    for a in api:
        if a.get('correlation_id') is not None:api_by[a['process_id'],a['correlation_id']].append(a)
    # Membership is original launch start. Mapping delay is NOT window-clipped.
    for a in api:
        if a['process_id']!=scope['process_id'] or a['thread_id']!=scope['thread_id'] or not start<=a['start_ns']<end:continue
        if _classify(a['api_name'],registry_version)[0]!='submit':continue
        corr=a.get('correlation_id')
        candidates=dev_by[a['process_id'],corr] if corr is not None else []
        duplicates=api_by[a['process_id'],corr] if corr is not None else []
        status='MISSING_MAPPING' if not candidates else 'AMBIGUOUS_MAPPING' if len(duplicates)!=1 else 'MAPPED'
        if a['record_id'] not in owned_ids or any(d['record_id'] not in owned_ids for d in candidates):status='OWNERSHIP_UNKNOWN'
        if candidates and (len({(d.get('device_id'),d.get('context_id'),d.get('stream_id')) for d in candidates})!=1
            or any(any(d.get(k) is None for k in ('device_id','context_id','stream_id')) for d in candidates)):
            status='AMBIGUOUS_MAPPING'
        if candidates and a.get('context_id') is not None and any(d['context_id']!=a['context_id'] for d in candidates):status='AMBIGUOUS_MAPPING'
        delta=min(d['start_ns'] for d in candidates)-a['end_ns'] if status=='MAPPED' else None
        launch_delta=min(d['start_ns'] for d in candidates)-a['start_ns'] if status=='MAPPED' else None
        if delta is not None and delta<0:status='STARTED_BEFORE_API_RETURN'
        mapping.append(dict(api_record_id=a['record_id'],activity_record_ids=[d['record_id'] for d in candidates],
            correlation_id=corr,status=status,launch_to_start_ns=launch_delta,post_api_return_ns=delta))
    gpu=metrics(selected_dev)
    return dict(schema_version=SCHEMA_VERSION,scope=scope,registry_version=registry_version,
        api=metrics(selected_api),sync_api=metrics(sync),non_sync_api=metrics(non_sync),
        runtime_api=metrics([r for r in selected_api if r.get('source_table')!='CUPTI_ACTIVITY_KIND_DRIVER']),
        driver_api=metrics([r for r in selected_api if r.get('source_table')=='CUPTI_ACTIVITY_KIND_DRIVER']),
        unclassified_api_record_ids=unknown_api,
        kernel=metrics([r for r in selected_dev if r['activity_kind']=='KERNEL']),
        memop=metrics([r for r in selected_dev if r['activity_kind'] in ('MEMCPY','MEMSET')]),
        gpu_activity=gpu,gpu_active_ratio=None if gpu['union_ns'] is None else gpu['union_ns']/(end-start),
        launch_mapping=mapping,mapping_count=len(mapping),mapped_count=sum(m['post_api_return_ns'] is not None for m in mapping),
        timeline=[dict(r,ownership_status='KNOWN' if r['record_id'] in owned_ids else 'UNKNOWN') for r in selected_api+selected_dev],
        definitions=dict(api_sum='PHYSICAL_RECORDS_CLIPPED_INCLUDING_SYNC_AND_NESTING',
            api_union='WALL_CLOCK_UNION_NOT_A_API',gpu_active='OWNED_ACTIVITY_UNION_NOT_DEPENDENCY',
            launch_membership='ORIGINAL_API_START_HALF_OPEN',b_aggregation='FORBIDDEN'))


def _driver_records(path):
    """Read optional Raw driver layer without modifying Canonical or S/A/B.

    Same SQLite trace clock. No inferred activity correlation, dependency or API
    semantics: registry and mapping status are still explicit and shared.
    """
    from .canonical_raw import _global_parts,_base
    with sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        present=db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='CUPTI_ACTIVITY_KIND_DRIVER'").fetchone()
        if not present:return [],'NOT_COLLECTED_UNKNOWN'
        cols={r['name'] for r in db.execute('PRAGMA table_info(CUPTI_ACTIVITY_KIND_DRIVER)')}
        if not {'start','end','globalTid','correlationId','nameId','returnValue'}<=cols:
            return [],'REQUIRED_FIELDS_MISSING_UNKNOWN'
        strings={r['id']:r['value'] for r in db.execute('SELECT id,value FROM StringIds')}
        records=[]
        for r in db.execute('SELECT rowid AS source_rowid,* FROM CUPTI_ACTIVITY_KIND_DRIVER ORDER BY start,end,rowid'):
            pid,tid=_global_parts(r['globalTid'])
            item=_base('cuda_api','CUPTI_ACTIVITY_KIND_DRIVER',r['source_rowid'])
            item.update(start_ns=r['start'],end_ns=r['end'],process_id=pid,thread_id=tid,
                global_tid=r['globalTid'],correlation_id=r['correlationId'],api_name=strings.get(r['nameId'],''),
                return_value=r['returnValue'])
            records.append(item)
        return records,'OBSERVED_TABLE'


def _file_value(domain_path,receipt_path,execution_path,*,bridge_path=None,domain_review=None):
    """Use the same accepted domain, projected scope, clock, registry and Raw."""
    from .gate9_domain import load_domain
    from .sync_semantics import load_canonical_bundle,build_semantic_inventory,_phase_ownership
    from .gate8_scope import load_projected_ownership
    from .gate8_files import _write,_entry
    from .gate8_adapter import digest
    from .gate8_files import load_input_receipt
    from .time_representation import OPAQUE_ALLOCATION,time_representation
    domain_path=Path(domain_path)
    if domain_review is not None:
        from .gate9_domain import DomainReview
        require(isinstance(domain_review,DomainReview),'REVIEW_TYPE')
    loader=load_domain if domain_review is None else domain_review.admission
    result=loader(domain_path,receipt_path,execution_path,bridge_path=bridge_path)
    require(result['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION','DOMAIN_REJECTED')
    canonical=domain_path.parent/'canonical/canonical_manifest.json'
    scope=domain_path.parent/'projection/scope.json'
    bundle=load_canonical_bundle(canonical); owners,projections=load_projected_ownership(canonical,bundle,scope)
    _,paths=load_input_receipt(receipt_path)
    drivers,driver_status=_driver_records(paths['sqlite'])
    apis=[*bundle['records']['cuda_api'],*drivers]
    with time_representation(OPAQUE_ALLOCATION):
        inventory=build_semantic_inventory({**bundle,'ownership_records':owners})
    # Already validated owner facts, including G1 projection ownership. Never
    # infer dependency or ownership from temporal overlap alone here.
    windows=[]
    for p in projections:
        i=p['identity']; anchor=next(a for a in __import__('json').loads(scope.read_text())['anchors']
                                   if a['payload']['boundary_id']==p['start_boundary_id'])
        def matches(identity):
            return identity and all(identity.get(k)==v for k,v in i.items())
        owned={r['record_id'] for r in inventory['activities']
               if r['ownership_status']=='VALID' and matches(r.get('invocation_identity'))}
        for r in apis:
            owner=_phase_ownership(r['start_ns'],r['end_ns'],r['global_tid'],owners)
            if owner['status']=='VALID' and matches(owner['identity']):owned.add(r['record_id'])
        rawscope=dict(p,process_id=anchor['pid'],thread_id=anchor['tid'])
        w=calculate(apis,bundle['records']['device_activity'],rawscope,owned,registry_version=OPAQUE_VERSION)
        if driver_status!='OBSERVED_TABLE':
            w['driver_api']=dict(count=None,sum_ns=None,union_ns=None,status=driver_status)
        windows.append(w)
    value=dict(schema_version=SCHEMA_VERSION,domain_sha256=digest(domain_path),canonical_sha256=digest(canonical),
               projection_sha256=digest(scope),windows=windows,measurement_validity='NOT_ASSESSED')
    value['api_table_scope']=sorted({r['source_table'] for r in apis})
    value['driver_layer_status']=driver_status
    value['input_receipt_sha256']=digest(Path(receipt_path))
    if domain_review is not None:
        domain_review.check_unchanged()
    return value


def write_baseline(domain_path,receipt_path,execution_path,output_dir,*,bridge_path=None):
    from .gate8_files import _write
    output_dir=Path(output_dir)
    require(not output_dir.resolve().is_relative_to(Path(domain_path).parent.resolve()),'OUTPUT_OVER_INPUT')
    if output_dir.exists():raise FileExistsError(output_dir)
    value=_file_value(domain_path,receipt_path,execution_path,bridge_path=bridge_path)
    output_dir.mkdir(parents=True)
    _write(output_dir/'baseline.json',value)
    return output_dir/'baseline.json'


def load_baseline(path,domain_path,receipt_path,execution_path,*,bridge_path=None,domain_review=None):
    import json
    saved=json.loads(Path(path).read_text(encoding='utf-8'))
    require(saved==_file_value(domain_path,receipt_path,execution_path,bridge_path=bridge_path,
                              domain_review=domain_review),'FILE_SCOPE_OR_VALUES')
    return saved
