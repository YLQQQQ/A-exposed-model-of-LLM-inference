"""Gate9 reuse of the accepted, user-relayed Gate8 vendor interpretation.

This is a separate evidence disposition, not a rewrite of Raw diagnostics, an
all-capture completeness certificate, or permission to omit later scope checks.
"""
from .gate8_engineering_scope import _diagnostics
from .gate8_warning_assumption import MESSAGES

VERSION = 'exposedpath-gate9-diagnostic-review/0.1.0'


def review(diagnostic, bundle):
    dispositions = _diagnostics(diagnostic)
    blocked = {r['source_rowid'] for r in dispositions if r['disposition'] != 'INFORMATION_ONLY'}
    if not blocked:
        return None  # Preserve existing no-warning result and loader behavior.

    def require(ok):
        if not ok:
            raise ValueError('DOMAIN_DIAGNOSTIC_IMPACT_UNBOUNDED')

    rows = [r for r in diagnostic['records'] if r['source_rowid'] in blocked]
    target = diagnostic['target_global_pid']
    source = bundle['manifest']['source']
    export = source.get('export', {})
    require(export.get('platform') == 'windows-desktop'
            and export.get('product_version') == '2026.2.1.210'
            and source['sqlite']['sha256'].lower() == diagnostic['source_sqlite_sha256'].lower())
    require(len(rows) == 4 and len(blocked) == 4 and {r['text'] for r in rows} == MESSAGES
            and len({r['global_pid'] for r in rows}) == 1)
    require(all(r['process_relation'] == 'OTHER_PROCESS'
                and type(r['global_pid']) is int and 0 < r['global_pid'] < 2**63
                and r['global_pid'] % 2**24 == 0 and r['global_pid'] != target
                and r['global_pid'] >> 48 == target >> 48
                and r['process_id'] == ((r['global_pid'] >> 24) & 0xffffff)
                and r['process_id'] not in (None, 0, diagnostic['target_pid'])
                and r['severity_id'] == 2 and r['source_id'] == 3 and r['timestamp_type'] == 2
                for r in rows))
    records = bundle['records']
    refs = diagnostic['target_nvtx_refs']
    nvtx = [r for r in records['nvtx'] if any(
        r['source_table'] == ref['source_table'] and r['source_rowid'] == ref['source_rowid']
        and r['global_tid'] == ref['global_tid']
        and r['global_tid'] - r['global_tid'] % 2**24 == target for ref in refs)]
    cuda = [r for r in records['device_activity'] if r['global_pid'] == target]
    require(nvtx and cuda)
    other = rows[0]['global_pid']
    # An observed contradiction to the no-events message is NOT covered.
    require(not any(r['global_pid'] == other for r in records['device_activity'])
            and not any(r['global_tid'] - r['global_tid'] % 2**24 == other
                        for r in records['nvtx'] + records.get('cuda_api', [])))
    return dict(schema_version=VERSION, basis='G8-WARNING-EVIDENCE/0.1',
        source_status='USER_RELAYED_OFFICIAL_RESPONSE',
        decision='PROCESS_TREE_NO_EVENTS_TARGET_CAPTURE_SUPPORTED',
        accepted_rowids=sorted(blocked), original_records=rows,
        target_global_pid=target, target_nvtx_record_ids=[r['record_id'] for r in nvtx],
        target_activity_record_ids=[r['record_id'] for r in cuda],
        source_sqlite_sha256=diagnostic['source_sqlite_sha256'],
        dropped_records_status='UNKNOWN', full_capture_completeness_proven=False,
        subsequent_scope_checks_required=True)
