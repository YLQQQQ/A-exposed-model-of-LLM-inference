"""Versioned, offline completion-operation description over accepted local S.

Not an admission gate, full physical W, new A, or an estimator of Host blocking.
Keeps the original API intervals, COE, terminal and uncovered time separate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import zipfile

from .coe_candidate import interval, clipped_union, preview_budget
from scripts.analyze_completion_operation_candidate import completion_overlap

VERSION = 'coe-completion-model/0.1.0'
ROLE = 'EXPLORATORY_COMPLETION_MODEL_NOT_FORMAL_A'


def require(ok, reason):
    if not ok:
        raise ValueError('COE_MODEL_' + reason)


def length(parts):
    return sum(b-a for a, b in parts)


def describe(copy, sync, members, terminal_id):
    """Interval arithmetic only. Semantic membership must be supplied, not guessed."""
    interval(*copy); interval(*sync)
    require(copy[0] <= copy[1] <= sync[0] <= sync[1], 'OPERATION_ORDER')
    require(members, 'MEMBER_EMPTY')
    require(len({r['id'] for r in members}) == len(members), 'MEMBER_DUPLICATE')
    for r in members:
        interval(r['start'], r['end'])
        require(r['kind'] in ('KERNEL', 'MEMCPY', 'MEMSET'), 'MEMBER_KIND')
    require(all(r['end'] <= sync[1] for r in members), 'COMPLETION')
    last = max(r['end'] for r in members)
    terminal = [r for r in members if r['id'] == terminal_id]
    require(len(terminal) == 1 and terminal[0]['end'] == last, 'TERMINAL')
    spans = [(r['start'], r['end']) for r in members]
    old = completion_overlap(copy, sync, spans)
    c, end = copy[0], sync[1]
    cut = max(c, last)
    before_gaps = length(clipped_union(c, cut, old['uncovered_intervals']))
    after = end-cut
    require(old['candidate_ns'] + before_gaps + after == old['wall_ns'], 'DECOMPOSITION')
    kernel = length(clipped_union(c, end, [(r['start'], r['end']) for r in members if r['kind'] == 'KERNEL']))
    memop = length(clipped_union(c, end, [(r['start'], r['end']) for r in members if r['kind'] != 'KERNEL']))
    return dict(schema_version=VERSION, role=ROLE, arithmetic_only=True,
        copy_interval_ns=list(copy), sync_interval_ns=list(sync), member_count=len(members),
        terminal_id=terminal_id, last_necessary_end_ns=last,
        terminal_relative_copy_ns=last-c, terminal_span_inside_operation_ns=cut-c,
        operation_wall_ns=old['wall_ns'], coe_ns=old['candidate_ns'], uncovered_ns=old['uncovered_ns'],
        activity_union=[list(p) for p in old['activity_union']],
        uncovered_intervals=[list(p) for p in old['uncovered_intervals']],
        uncovered_before_terminal_ns=before_gaps, after_terminal_to_sync_return_ns=after,
        coe_by_api_part_ns=dict(copy=old['copy_api_activity_ns'], between=old['between_apis_activity_ns'],
            sync=old['original_sync_ns']), kernel_ns=kernel, memop_ns=memop,
        kernel_memop_overlap_ns=kernel+memop-old['candidate_ns'],
        interpretation='NECESSARY_ACTIVITY_INSIDE_COMPLETION_OPERATION',
        pure_host_blocking_ns=None, removable_latency_ns=None, production_A_B_changed=False,
        new_admission_granted=False)


def from_admitted(raw, scope, result, *, phase_start=None):
    """Consume a source-bound saved S result; do not re-run or replace its gate."""
    require(raw.get('schema_version') == 'cupti-timeline-capture/0.1.0' and
        result.get('schema_version') == 'submit-effect-bridge/0.3.0', 'VERSION')
    require(result.get('status') == 'VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS', 'ADMISSION')
    require(raw['clock'] == result['clock'] == 'CUPTI_TIMESTAMP_NS' and
        raw['session_id'] == result['session_id'] == scope['session_id'] and raw['pid'] == scope['pid'], 'IDENTITY_CLOCK')
    q = raw['quality']
    require(q.get('closed') is True and q.get('errors') == [] and
        all(type(q.get(k)) is int and q[k] == 0 for k in ('overflow', 'dropped', 'dropped_query_errors')) and
        [scope['context'], scope['stream']] in q.get('dropped_scopes', []), 'QUALITY')
    require(scope.get('completion_proof') == 'HOST_TOKEN_READABLE' and scope.get('actual_token_ids') and
        all(type(t) is int and t >= 0 for t in scope['actual_token_ids']) and
        scope.get('ownership') == 'CLOSED_SINGLE_FIFO_NO_EVENTS_OR_GRAPHS', 'COMPLETION_PROOF')
    rows = {r['id']: r for r in raw['records']}
    require(len(rows) == len(raw['records']), 'RECORD_DUPLICATE')
    ids = result['members']
    require(len(set(ids)) == len(ids), 'MEMBER_DUPLICATE')
    require(all(k in rows for k in ids), 'MEMBER_MISSING')
    members = [rows[k] for k in ids]
    require(all(all(r.get(k) == scope[k] for k in ('pid', 'device', 'context', 'stream')) for r in members), 'MEMBER_SCOPE')
    require(scope['copy_api'] in rows and scope['sync_api'] in rows, 'PAIR_MISSING')
    copy, sync = (rows[scope[k]] for k in ('copy_api', 'sync_api'))
    require(all(r.get('kind') == 'API' and r.get('domain') == 'RUNTIME' and r.get('return_code') == 0 and
        (r.get('pid'), r.get('tid')) == (scope['pid'], scope['tid']) for r in (copy, sync)), 'PAIR_IDENTITY_OR_SUCCESS')
    a = scope['request_start'] if phase_start is None else phase_start
    interval(scope['drain_end'], scope['request_start']); interval(a, copy['start'])
    require(scope['request_start'] <= a and sync['end'] <= scope['completion_end'], 'PHASE_ORDER')
    value = describe([copy['start'], copy['end']], [sync['start'], sync['end']], members, result['terminal'])
    require(value['coe_ns'] == result['coe_ns'] and value['operation_wall_ns'] == result['operation_wall_ns'] and
        value['coe_by_api_part_ns']['sync'] == result['sync_intersection_ns'] and
        value['activity_union'] == [list(p) for p in result['activity_union']], 'SAVED_ARITHMETIC')
    spans = [(r['start'], r['end']) for r in members]
    gpu = [(r['start'], r['end']) for r in raw['records'] if r['kind'] in ('KERNEL', 'MEMCPY', 'MEMSET') and
           all(r.get(k) == scope[k] for k in ('pid', 'device', 'context'))]
    g = length(clipped_union(a, scope['completion_end'], gpu))
    value.update(arithmetic_only=False, clock=raw['clock'], session_id=raw['session_id'],
        copy_api_id=scope['copy_api'], sync_api_id=scope['sync_api'],
        scope={k: scope[k] for k in ('pid', 'tid', 'device', 'context', 'stream')},
        membership_assurance='REUSED_ACCEPTED_LOCAL_S_NOT_RECONSTRUCTED', full_physical_W_qualified=False,
        completion_point_ns=scope['completion_end'], phase_start_ns=a, phase_wall_ns=scope['completion_end']-a,
        phase_gpu_union_ns=g, coe_phase_ratio=value['coe_ns']/(scope['completion_end']-a),
        coe_phase_gpu_ratio=value['coe_ns']/g if g else None,
        necessary_history_before_phase_ns=length(clipped_union(scope['request_start'], a, spans)),
        necessary_current_phase_before_copy_ns=length(clipped_union(a, copy['start'], spans)),
        closed_prior_ids=list(result['closed_prior_ids']), logical_zero_call_ids=list(result['logical_zero_call_ids']),
        original_A_extension='NOT_ASSESSED_NO_QUALIFIED_A_ATOMS', formal_eligible=False)
    return value


def preview(window, atoms, models):
    """Reuse the existing migration formula, never invent an original A partition."""
    require(models and all(v.get('schema_version') == VERSION for v in models), 'MODEL_VERSION')
    require(all(isinstance(a.get('source_ids'), list) and a['source_ids'] for a in atoms), 'SOURCE_PROVENANCE')
    value = preview_budget(window, atoms, [v['activity_union'] for v in models])
    for piece in value['migration']:
        source = [a for a in atoms if a['start'] <= piece['start'] < piece['end'] <= a['end']]
        require(len(source) == 1, 'SOURCE_PROVENANCE')
        piece['source_ids'] = list(source[0]['source_ids'])
    budgets = dict(value['budgets_ns']); budgets['completion_exposure'] = budgets.pop('device_wait')
    return dict(schema_version=VERSION, role=ROLE, candidate_budgets_ns=budgets,
        migrated_ns=value['migrated_ns'], migration=value['migration'],
        original_device_wait_ns=sum(a['end']-a['start'] for a in atoms if a['category'] == 'device_wait'),
        original_atom_semantic_proofs='REQUIRED_FROM_CALLER_NOT_CREATED_BY_THIS_ARITHMETIC',
        production_A_B_changed=False, formal_eligible=False)


def review_archive(archive_path, source_index, output):
    """Finite saved-result reader: once per run, no S recovery or giant domain."""
    archive_path, source_index, output = map(Path, (archive_path, source_index, output))
    require(not output.exists(), 'NO_OVERWRITE')
    root = Path(__file__).resolve().parents[1]
    modules = ('analysis/coe_completion_model.py', 'analysis/coe_candidate.py',
               'scripts/analyze_completion_operation_candidate.py')
    code_hashes = {p: hashlib.sha256((root/p).read_bytes()).hexdigest() for p in modules}
    index_bytes = source_index.read_bytes(); index = json.loads(index_bytes)
    require(index['schema_version'] == 'cupti-input-pilot-closeout/0.1.0', 'SOURCE_INDEX_VERSION')
    ref = index['archive_reference']
    with archive_path.open('rb') as f:
        actual_hash = hashlib.file_digest(f, 'sha256').hexdigest()
    require(archive_path.stat().st_size == ref['bytes'] and actual_hash == ref['sha256'], 'ARCHIVE_IDENTITY')
    hashes = {}; reports = []
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        require(len(set(names)) == len(names) and all('\\' not in n and not PurePosixPath(n).is_absolute()
            and '..' not in PurePosixPath(n).parts and ':' not in n for n in names), 'ARCHIVE_PATH')
        manifest = archive.read('artifact_manifest.json')
        require(hashlib.sha256(manifest).hexdigest() == ref['manifest_sha256'], 'MANIFEST_HASH')
        entries = json.loads(manifest)['files']; files = {v['path']: v for v in entries}
        require(len(files) == len(entries), 'MANIFEST_DUPLICATE')

        def read(name):
            require(name in files and name in names, 'MEMBER_MISSING:' + name)
            b = archive.read(name); h = hashlib.sha256(b).hexdigest(); expected = files[name]
            require(len(b) == expected['bytes'] and h == expected['sha256'], 'MEMBER_HASH:' + name)
            hashes[name] = h
            return json.loads(b)

        run_ids = [r['run_id'] for r in index['runs']]
        require(run_ids and len(set(run_ids)) == len(run_ids), 'RUN_DUPLICATE')
        for run in index['runs']:
            base = 'runs/' + run['run_id'] + '/model/'
            require(run['role'] == 'Pilot', 'SOURCE_ROLE')
            raw = read(base + 'timeline/capture.json')
            require(hashes[base + 'timeline/capture.json'] == run['capture_sha256'], 'CAPTURE_HASH')
            tokens = read(base + 'tokens.json')
            require(tokens['identity']['run_id'] == raw['session_id'] == run['run_id'] and
                tokens['identity']['data_role'] == 'Pilot' and tokens['identity']['run_role'] == 'PILOT' and
                tokens['actual_input_tokens'] == run['input_tokens'] and tokens['token_ids'] == run['tokens'] and
                tokens['early_eos'] is False and tokens['actual_output_tokens'] == len(run['token_details']), 'TOKEN_IDENTITY')
            previous = None
            for i, detail in enumerate(run['token_details']):
                scope_name = base + f'scope_token{i}.json'; result_name = base + f'derived_token{i}/result.json'
                scope = read(scope_name); saved = read(result_name)
                require(saved['schema_version'] == 'cupti-timeline-adapter/0.3.0' and
                    saved['input']['capture_sha256'] == run['capture_sha256'] and
                    saved['input']['scope_sha256'] == hashes[scope_name], 'SAVED_INPUT_BINDING')
                require(scope == detail['scope'] and scope['actual_token_ids'] == tokens['token_ids'][i] and
                    scope['pid'] == tokens['pid'] and scope['tid'] == tokens['tid'], 'TOKEN_SCOPE')
                value = from_admitted(raw, scope, saved['result'], phase_start=previous)
                value.update(run_id=run['run_id'], block=run['block'], input_tokens=run['input_tokens'],
                    token_index=i, source_role='Pilot', raw_reference=base + 'timeline/capture.json',
                    saved_membership_reference=result_name, scope_reference=scope_name)
                reports.append(value); previous = scope['completion_end']
                del saved
            del raw
    require(source_index.read_bytes() == index_bytes, 'SOURCE_INDEX_CHANGED')
    with archive_path.open('rb') as f:
        require(hashlib.file_digest(f, 'sha256').hexdigest() == actual_hash, 'ARCHIVE_CHANGED')
    require(all(hashlib.sha256((root/p).read_bytes()).hexdigest() == h for p, h in code_hashes.items()), 'ANALYSIS_SOURCE_CHANGED')
    value = dict(schema_version=VERSION, role=ROLE, archive_sha256=actual_hash,
        source_index_sha256=hashlib.sha256(index_bytes).hexdigest(), consumed_member_hashes=hashes,
        operations=reports, analysis_sources=code_hashes,
        production_A_B_changed=False, new_S_recovery=False, new_GPU_qualification=False)
    output.mkdir(parents=True, exist_ok=False)
    with (output/'completion_model.json').open('x', encoding='utf-8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
    return value


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'source-index', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    value = review_archive(args.archive, args.source_index, args.output)
    print(json.dumps(dict(version=VERSION, operations=len(value['operations']), output=str(args.output))))


if __name__ == '__main__':
    main()
