"""Report an admitted window suffix without asserting physical B qualification."""
import json


def sync_evidence(records, proof):
    from .activity_baseline import union
    from exposedpath.batch_load import require
    syncs=[s for s in records['cuda_sync'] if s['record_id']==proof['sync_id']]
    require(len(syncs)==1,'REPORT_SYNC_REFERENCE');s=syncs[0]
    apis=[a for a in records['cuda_api'] if a['record_id']==s['runtime_record_id']]
    require(len(apis)==1,'REPORT_API_REFERENCE');a=apis[0]
    members=[r for r in records['device_activity'] if r['record_id'] in proof['suffix_activity_ids']]
    require(len(members)==len(set(proof['suffix_activity_ids'])),'REPORT_MEMBER_REFERENCE')
    intervals=[(max(a['start_ns'],r['start_ns']),min(a['end_ns'],r['end_ns'])) for r in members
               if r['start_ns']<a['end_ns'] and a['start_ns']<r['end_ns']]
    markers=[r for r in records['nvtx'] if (r.get('text') or '').startswith('EXPOSEDPATH_JSON_V1:')
             and json.loads(r['text'].split(':',1)[1]).get('kind')=='sync'
             and r['start_ns']<=a['start_ns'] and r.get('end_ns') is not None and a['end_ns']<=r['end_ns']]
    return dict(sync_record_id=s['record_id'],runtime_api=a,physical_sync=s,
        host_api_duration_ns=a['end_ns']-a['start_ns'],necessary_activity_ids=proof['suffix_activity_ids'],
        dependency_scope=proof['scope'],last_necessary_activity_end_ns=max((r['end_ns'] for r in members),default=None),
        supported_device_wait_union_ns=union(intervals),sync_markers=markers,
        internal_api_wait='NOT_IDENTIFIABLE_NOT_SPLIT',physical_b_qualified=False)
