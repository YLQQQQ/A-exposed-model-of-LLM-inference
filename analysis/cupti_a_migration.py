"""Same-CUPTI, original-formula A partition and exploratory COE migration.

Consumes saved, source-bound local S/0.3 proofs. It does not grant physical W/B,
Formal or provider qualification, and never writes a production A result.
"""
from __future__ import annotations

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path, PurePosixPath
import time
import zipfile

from .coe_candidate import clipped_union, preview_budget
from .coe_completion_model import from_admitted, length
from exposedpath_v141.a_accounting import _covering_by_segment
from exposedpath_v141.a_api_classification import _classify, VERSION as REGISTRY
from exposedpath_v141.cupti_driver_queries import (
    query_rule, runtime_query_rule, VERSION as DRIVER_POLICY,
    RUNTIME_VERSION as RUNTIME_POLICY,
)
from exposedpath_v141.intervals import atomic_segments
from exposedpath_v141.submit_effect_bridge import validate_api_callback, SAMPLED_TIMING

VERSION = 'cupti-a-coe-migration-preview/0.1.0'
ROLE = 'EXPLORATORY_SAME_CUPTI_SOURCE_PREVIEW_NOT_FORMAL_A'
CATEGORIES = ('host', 'submit', 'non_submit', 'device_wait', 'residual', 'unattributed')
SYNC_NAMES = {('RUNTIME', 'cudaStreamSynchronize', 131), ('DRIVER', 'cuStreamSynchronize', 126)}


def require(ok, reason):
    if not ok:
        raise ValueError('CUPTI_A_PREVIEW_' + reason)


def key(row):
    return row['domain'], row['pid'], row['correlation']


def overlaps(a, b):
    return a[0] < b[1] and b[0] < a[1]


def migrate_atoms(window, atoms, q):
    """Apply existing preview only to affected atoms; identical interval rule.

    Avoid clipping a thousands-piece Q against every unrelated Host/query atom.
    The old routine still validates the full original partition and performs
    every actual subtraction, including old-wait and unattributed handling.
    """
    value = preview_budget(window, atoms, [])
    q = clipped_union(*window, q); ends = [b for _, b in q]
    for atom in atoms:
        i = bisect_right(ends, atom['start']); local = []
        while i < len(q) and q[i][0] < atom['end']:
            local.append(q[i]); i += 1
        if not local:
            continue
        part = preview_budget([atom['start'],atom['end']], [atom], [local])
        value['budgets_ns'][atom['category']] -= atom['end']-atom['start']
        for category, ns in part['budgets_ns'].items():
            value['budgets_ns'][category] += ns
        value['migration'].extend(part['migration']); value['migrated_ns'] += part['migrated_ns']
    value['cuda_api_ns'] = value['budgets_ns']['submit']+value['budgets_ns']['non_submit']
    require(sum(value['budgets_ns'].values()) == window[1]-window[0], 'CONSERVATION')
    return value


def _partition(window, owners, syncs, rows):
    """Reuse old A's atomic sweep and precedence, with explicit source proofs."""
    apis = [(a, (a['start'], a['end'])) for a in owners]
    ss = [(s, tuple(s['host_interval_ns'])) for s in syncs]
    # Clip each W to its own sync before union: no cross-sync B summation.
    waits = [(s, p) for s, host in ss for p in clipped_union(*host,
        [(rows[i]['start'], rows[i]['end']) for i in s['member_ids']])]
    boundaries = [p for _, span in [*apis, *ss, *waits] for p in span]
    boundaries.extend(p for r in rows.values() if r['kind'] in ('KERNEL','MEMCPY','MEMSET') for p in (r['start'],r['end']))
    segments = atomic_segments(tuple(window), boundaries)
    atoms = []
    for (a, b), aa, sy, ww in zip(segments, _covering_by_segment(apis, segments),
            _covering_by_segment(ss, segments), _covering_by_segment(waits, segments)):
        if sy:
            category = 'device_wait' if ww else 'residual'
            source = sorted({s['record_id'] for s, _ in sy})
        elif aa:
            cats = {r['category'] for r, _ in aa}
            require(len(cats) == 1, 'API_OWNER_CATEGORY_OVERLAP')
            category = cats.pop(); source = sorted(r['id'] for r, _ in aa)
        else:
            category = 'host'; source = ['scope:closed-request-thread']
        atoms.append(dict(start=a, end=b, category=category, source_ids=source))
    return atoms


def _window(name, span, owners, syncs, rows, models):
    atoms = _partition(span, owners, syncs, rows)
    original = dict.fromkeys(CATEGORIES, 0)
    for a in atoms:
        original[a['category']] += a['end']-a['start']
    q = clipped_union(*span, [p for m in models for p in m['activity_union']])
    value = migrate_atoms(span, atoms, q)
    old = [(a['start'], a['end']) for a in atoms if a['category'] == 'device_wait']
    overlap = sum(length(clipped_union(a, b, old)) for a, b in q)
    starts = [a['start'] for a in atoms]; source_totals = Counter()
    for piece in value['migration']:
        atom = atoms[bisect_right(starts, piece['start'])-1]
        require(atom['start'] <= piece['start'] < piece['end'] <= atom['end'], 'MIGRATION_SOURCE')
        piece['source_ids'] = atom['source_ids']
        source_totals[piece['from_category']] += piece['duration_ns']
    member_ids = {i for m in models for i in m['member_ids']}
    activity_rows = [(rows[i], (rows[i]['start'],rows[i]['end'])) for i in sorted(member_ids)]
    spans = [(p['start'],p['end']) for p in value['migration']]
    for piece, activities in zip(value['migration'], _covering_by_segment(activity_rows, spans)):
        piece['necessary_activity_ids'] = [r['id'] for r,_ in activities]
        piece['operation_sync_ids'] = [m['sync_api_id'] for m in models if
            m['copy_interval_ns'][0] <= piece['start'] < piece['end'] <= m['sync_interval_ns'][1] and
            any(r['id'] in m['member_ids'] for r,_ in activities)]
        require(piece['necessary_activity_ids'] and piece['operation_sync_ids'], 'MIGRATION_ACTIVITY_PROVENANCE')
    extended = dict(value['budgets_ns'])
    extended['completion_exposure'] = extended.pop('device_wait')
    require(value['migrated_ns'] == length(q)-overlap, 'COE_COVERAGE')
    require(extended['completion_exposure'] == original['device_wait']+length(q)-overlap, 'EXTENDED_UNION')
    require(sum(original.values()) == sum(extended.values()) == span[1]-span[0], 'CONSERVATION')
    return dict(name=name, window_ns=list(span), wall_ns=span[1]-span[0],
        original_budgets_ns=original, coe_union_ns=length(q), old_wait_overlap_ns=overlap,
        new_migration_ns=value['migrated_ns'], migration_source_ns=dict(source_totals),
        extended_budgets_ns=extended, migration=value['migration'],
        coe_union=[list(p) for p in q], old_wait_union=[list(p) for p in clipped_union(*span, old)],
        original_atom_count=len(atoms), original_atom_sha256=hashlib.sha256(
            json.dumps(atoms, separators=(',', ':'), sort_keys=True).encode()).hexdigest(),
        original_partition='ORIGINAL_FORMULA_SAME_CUPTI_CANDIDATE_SOURCE_PARTITION',
        cuda_api_original_ns=original['submit']+original['non_submit'],
        cuda_api_extended_ns=extended['submit']+extended['non_submit'],
        coe_fully_in_extended_union=True, conservation_error_ns=0)


def audit_run(raw, scopes, saved_results):
    """Fail closed on whole-window sources; preserve precise local gap extent."""
    require(len(scopes) == len(saved_results) == 2, 'TWO_TOKEN_PROFILE')
    require(scopes[0]['request_start'] == scopes[1]['request_start'] and
        scopes[0]['completion_end'] < scopes[1]['completion_end'] and
        all(scopes[0][k] == scopes[1][k] for k in ('pid','tid','device','context','stream','session_id','drain_end')), 'SCOPE_PAIR')
    models = [from_admitted(raw, s, r, phase_start=None if i == 0 else scopes[0]['completion_end'])
        for i, (s, r) in enumerate(zip(scopes, saved_results))]
    for m, r in zip(models, saved_results):
        m['member_ids'] = list(r['members'])
    proof = saved_results[-1]; scope = scopes[-1]
    require(proof.get('driver_query_policy') == DRIVER_POLICY and
        proof.get('runtime_query_policy') == RUNTIME_POLICY and
        proof.get('api_callback_timing_policy') == SAMPLED_TIMING, 'POLICIES')
    request = (scope['request_start'], scope['completion_end'])
    records = {r['id']: r for r in raw['records']}
    calls = {c['id']: c for c in raw['callbacks']}
    require(len(calls) == len(raw['callbacks']), 'CALL_DUPLICATE')
    callkeys = {key(c): c for c in calls.values()}
    require(len(callkeys) == len(calls), 'CALL_KEY_DUPLICATE')
    apis = {k: r for k, r in records.items() if r['kind'] == 'API'}
    apikeys = {key(a): a for a in apis.values()}
    require(len(apikeys) == len(apis), 'API_KEY_DUPLICATE')
    gaps = []; owners = {}; projections = []

    def gap(reason, row=None, **extra):
        value = dict(reason=reason, record_id=row['id'] if row else None)
        if row:
            value['unsafe_interval_ns'] = [row['start'], row['end']]
        value.update(extra); gaps.append(value)

    def root(c):
        seen = set()
        while c.get('parent_id') is not None:
            require(c['id'] not in seen and c['parent_id'] in calls, 'CALL_PARENT')
            seen.add(c['id']); p = calls[c['parent_id']]
            require(p['pid'] == c['pid'] and p['tid'] == c['tid'] and
                p['start'] <= c['start'] <= c['end'] <= p['end'], 'CALL_PARENT_SCOPE')
            c = p
        return c

    owner_proofs = {r['api_id']: r for r in proof['accounting_api_sources']}
    require(len(owner_proofs) == len(proof['accounting_api_sources']), 'OWNER_DUPLICATE')
    query_proofs = {r['callback_id']: r for label in ('driver_queries','runtime_queries') for r in proof[label]}
    for a in apis.values():
        if not overlaps((a['start'], a['end']), request):
            continue
        c = callkeys.get(key(a))
        if c is None:
            gap('API_CALLBACK_MISSING', a); continue
        named = dict(a, name=c['name'])
        validate_api_callback(named, c, policy=SAMPLED_TIMING)
        r = root(c); owner = apikeys.get(key(r))
        if owner is None:
            gap('API_OWNER_MISSING', a); continue
        if not (owner['start'] <= a['start'] <= a['end'] <= owner['end']):
            gap('NESTED_API_OUTSIDE_OWNER', a, owner_api_id=owner['id'],
                owner_interval_ns=[owner['start'],owner['end']],
                unsafe_interval_ns=[min(a['start'],owner['start']),max(a['end'],owner['end'])])
        if owner['id'] in owners:
            continue
        owner = dict(owner, name=r['name'], callback_id=r['id'])
        owners[owner['id']] = owner
        if not (owner['tid'] == scope['tid'] and owner['pid'] == scope['pid'] and
                request[0] <= owner['start'] <= owner['end'] <= request[1]):
            gap('API_OWNER_SCOPE', owner)
        p = owner_proofs.get(owner['id'])
        if p is None or any(p[k] != owner[k] for k in ('domain','name','start','end','return_code')) or p['callback_id'] != r['id']:
            gap('SAVED_OWNER_COVERAGE', owner)
        if owner['return_code'] != 0:
            gap('API_FAILED', owner)
        category, rule = _classify(owner['name'], REGISTRY)
        qr = query_rule(owner, r) if r['domain'] == 'DRIVER' else runtime_query_rule(owner, r)
        if qr is not None:
            q = query_proofs.get(r['id'])
            if q is None or q['budget_owner_api_id'] != owner['id'] or q['name'] != r['name'] or q['cbid'] != r['cbid']:
                gap('QUERY_PROOF_MISSING', owner)
            category = qr['category']; rule = qr['policy_version']+'/'+r['name']
            if proof['submit_effects'].get(owner['id']):
                gap('QUERY_UNEXPECTED_EFFECT', owner)
        if (r['domain'], r['name'], r['cbid']) in SYNC_NAMES:
            owner['category'] = 'physical_sync'; owner['rule'] = 'EXACT_SUCCESSFUL_STREAM_SYNC'; continue
        if category is None:
            gap('API_CLASSIFICATION_MISSING', owner)
        elif category == 'submit':
            effects = proof['submit_effects'].get(owner['id'])
            zero = r['id'] in proof['logical_zero_call_ids']
            if effects is None or (not effects and not (zero and r['params'].get('count') == 0 and owner['name'] == 'cudaMemsetAsync')):
                gap('SUBMIT_PROOF_MISSING', owner)
            elif any(i not in records or records[i]['kind'] not in ('KERNEL','MEMCPY','MEMSET') for i in effects):
                gap('SUBMIT_EFFECT_MISSING', owner)
        owner['category'] = category; owner['rule'] = rule
    for aid in owner_proofs.keys()-owners.keys():
        gap('SAVED_OWNER_COVERAGE', apis.get(aid), owner_api_id=aid)

    # Prefix projection of *accepted* request-local FIFO membership. Completed
    # predecessors remain members; future submit calls are excluded, not hidden.
    member_ids = proof['members']; member_set = set(member_ids)
    submit_sources = {r['api_id']: r for r in proof['submission_api_sources']}
    require(len(submit_sources) == len(proof['submission_api_sources']), 'SUBMIT_SOURCE_DUPLICATE')
    for aid, source in submit_sources.items():
        actual = apis.get(aid)
        if actual is None or any(source[k] != actual[k] for k in ('domain','start','end')):
            gap('SUBMIT_SOURCE_IDENTITY', actual, owner_api_id=aid)
    effect_owner = {}
    for aid, ids in proof['submit_effects'].items():
        for eid in ids:
            require(eid not in effect_owner, 'EFFECT_OWNER_DUPLICATE')
            effect_owner[eid] = aid
    for eid in member_ids:
        if eid not in effect_owner or effect_owner[eid] not in submit_sources:
            gap('SUBMIT_PROOF_MISSING', records[eid])
    internal = {f['source_record_id']: f for f in proof['internal_synchronizations']}
    mapped_sync_apis = Counter(); mapped_sync_calls = Counter()
    physical = [r for r in records.values() if r['kind'] == 'SYNC' and overlaps((r['start'], r['end']), request)]
    for y in sorted(physical, key=lambda r: (r['start'], r['id'])):
        fact = internal.get(y['id'])
        if fact is not None:
            owner = owners.get(fact['runtime_api_id']); d = calls.get(fact['driver_call_id'])
            require(owner is not None and d is not None and root(d)['id'] == owner['callback_id'] and
                (d['domain'], d['name'], d['cbid']) in SYNC_NAMES and d['return_code'] == 0, 'INTERNAL_SYNC_IDENTITY')
            mapped_sync_calls[d['id']] += 1
            actual = apikeys.get(key(d))
            if actual is None or fact['driver_api_interval_ns'] is None:
                gap('INTERNAL_SYNC_HOST_API_INTERVAL_MISSING', y, owner_api_id=owner['id'],
                    driver_call_id=d['id'], callback_sample_interval_ns=[d['start'], d['end']],
                    physical_interval_ns=[y['start'], y['end']], unsafe_interval_ns=[owner['start'], owner['end']])
                continue
            require(fact['driver_api_interval_ns'] == [actual['start'], actual['end']], 'INTERNAL_SYNC_TIME')
            ids = fact['necessary_member_ids']; host = [actual['start'], actual['end']]
            require(set(ids) <= member_set, 'INTERNAL_SYNC_MEMBER')
            api_id = actual['id']
        else:
            candidates = [c for c in calls.values() if c['pid'] == y['pid'] and c['correlation'] == y['correlation'] and
                (c['domain'], c['name'], c['cbid']) in SYNC_NAMES and
                (y['domain'] == 'UNSPECIFIED' or y['domain'] == c['domain'])]
            roots = {root(c)['id'] for c in candidates}
            if len(roots) != 1:
                gap('PHYSICAL_SYNC_MAPPING', y); continue
            c = calls[next(iter(roots))]; actual = apikeys.get(key(c))
            if actual is None or (c['domain'], c['name'], c['cbid']) not in SYNC_NAMES:
                gap('PHYSICAL_SYNC_HOST_API_MISSING', y); continue
            require(c['return_code'] == 0 and all(c[k] == scope[k] for k in ('pid','tid','device','context','stream')),
                'SYNC_SCOPE')
            for match in candidates:
                mapped_sync_calls[match['id']] += 1
            api_id = actual['id']; host = [actual['start'], actual['end']]
            ids = [eid for eid in member_ids if eid in effect_owner and effect_owner[eid] in submit_sources and
                submit_sources[effect_owner[eid]]['end'] <= host[0]]
            mapped_sync_apis[api_id] += 1
        require(y['flags'] == 3 and all(y[k] == scope[k] for k in ('pid','context','stream')) and
            host[0] <= y['start'] <= y['end'] <= host[1], 'SYNC_PHYSICAL_SCOPE')
        if not ids or any(records[i]['end'] > y['end'] for i in ids):
            gap('SYNC_PREFIX_COMPLETION', y); continue
        terminal = max(records[i]['end'] for i in ids)
        terminals = [i for i in ids if records[i]['end'] == terminal]
        if len(terminals) != 1:
            gap('SYNC_PREFIX_TERMINAL', y); continue
        projections.append(dict(record_id=y['id'], api_id=api_id, host_interval_ns=host,
            physical_interval_ns=[y['start'], y['end']], member_ids=ids, terminal_ids=terminals,
            old_wait_ns=length(clipped_union(*host, [(records[i]['start'], records[i]['end']) for i in ids])),
            assurance='PREFIX_PROJECTION_OF_ACCEPTED_LOCAL_FIFO_NOT_FULL_PHYSICAL_W'))
    for a in owners.values():
        if a['category'] == 'physical_sync' and mapped_sync_apis[a['id']] != 1:
            gap('PHYSICAL_SYNC_MISSING' if not mapped_sync_apis[a['id']] else 'PHYSICAL_SYNC_DUPLICATE', a)
    for c in calls.values():
        if (c['domain'],c['name'],c['cbid']) in SYNC_NAMES and overlaps((c['start'],c['end']),request) and mapped_sync_calls[c['id']] != 1:
            owner = apikeys.get(key(root(c)))
            gap('SYNC_CALLBACK_PHYSICAL_COVERAGE', owner, callback_id=c['id'],
                physical_mapping_count=mapped_sync_calls[c['id']])
    base = dict(schema_version=VERSION, role=ROLE, session_id=raw['session_id'], clock=raw['clock'],
        request_window_ns=list(request), gaps=gaps, sync_projections=projections, operations=models,
        registry=REGISTRY, driver_query_policy=DRIVER_POLICY, runtime_query_policy=RUNTIME_POLICY,
        membership_assurance='REUSED_ACCEPTED_LOCAL_S_WITH_FIFO_PREFIX_PROJECTIONS',
        full_physical_W_qualified=False, production_A_B_changed=False, formal_eligible=False,
        new_S_recovery=False, pure_host_blocking_ns=None)
    if gaps:
        local = []
        for m in models:
            span = [m['copy_interval_ns'][0], m['sync_interval_ns'][1]]
            relevant = [g for g in gaps if g.get('unsafe_interval_ns') is None or overlaps(span, g['unsafe_interval_ns'])]
            local.append(dict(window_ns=span, status='BLOCKED_LOCAL_SOURCE_GAP' if relevant else 'LOCAL_SOURCES_ONLY_NOT_FULL_A',
                gap_reasons=sorted({g['reason'] for g in relevant}), coe_ns=m['coe_ns']))
        return dict(base, status='BLOCKED_WHOLE_WINDOW_SOURCE_GAP', windows=None, local_previews=local,
            request_equals_phase_sum=None)
    values = [_window(name, span, list(owners.values()), projections, records, models) for name, span in (
        ('Request', request), ('Prefill', (request[0], scopes[0]['completion_end'])),
        ('Decode', (scopes[0]['completion_end'], request[1])))]
    for field in ('original_budgets_ns', 'extended_budgets_ns'):
        require(all(values[0][field][k] == values[1][field][k]+values[2][field][k] for k in values[0][field]), 'PHASE_SUM')
    for field in ('coe_union_ns','old_wait_overlap_ns','new_migration_ns'):
        require(values[0][field] == values[1][field]+values[2][field], 'PHASE_SUM')
    for model in models:
        model['original_A_extension'] = 'SAME_SOURCE_CANDIDATE_PREVIEW_ONLY'
    return dict(base, status='COMPLETE_WINDOW_SOURCE_PREVIEW_NOT_FORMAL', windows=values,
        local_previews=[], request_equals_phase_sum=True,
        owner_API_count=len(owners), classified_owner_counts=dict(Counter(a['name'] for a in owners.values())))


def review_archive(archive_path, source_index, output, *, run_id=None, all_runs=False):
    """Hash every consumed file; release each Raw before the next run. No S rerun."""
    require((run_id is not None) != all_runs, 'EXPLICIT_RUN_SELECTION')
    archive_path, source_index, output = map(Path, (archive_path, source_index, output))
    require(not output.exists(), 'NO_OVERWRITE')
    source_bytes = source_index.read_bytes(); index = json.loads(source_bytes)
    require(index['schema_version'] == 'cupti-input-pilot-closeout/0.1.0', 'INDEX_VERSION')
    ref = index['archive_reference']
    def filehash(path):
        with path.open('rb') as f:
            return hashlib.file_digest(f, 'sha256').hexdigest()
    require(archive_path.stat().st_size == ref['bytes'] and filehash(archive_path) == ref['sha256'], 'ARCHIVE_HASH')
    root = Path(__file__).resolve().parents[1]
    code_paths = ['analysis/cupti_a_migration.py','analysis/coe_completion_model.py','analysis/coe_candidate.py',
        'scripts/analyze_completion_operation_candidate.py',
        'exposedpath_v141/a_accounting.py','exposedpath_v141/a_api_classification.py','exposedpath_v141/cupti_driver_queries.py',
        'exposedpath_v141/submit_effect_bridge.py','exposedpath_v141/intervals.py',
        'docs/v1_4_1/contracts/a_api_registry_v0_1.json']
    code_hashes = {p: filehash(root/p) for p in code_paths}
    hashes = {}; reports = []; selected = [r for r in index['runs'] if all_runs or r['run_id'] == run_id]
    require(selected and len({r['run_id'] for r in selected}) == len(selected), 'RUN_SELECTION')
    started = time.perf_counter()
    with zipfile.ZipFile(archive_path) as z:
        names = z.namelist()
        require(len(names) == len(set(names)) and all('\\' not in n and not PurePosixPath(n).is_absolute()
            and '..' not in PurePosixPath(n).parts and ':' not in n for n in names), 'ARCHIVE_PATH')
        manifest = z.read('artifact_manifest.json')
        require(hashlib.sha256(manifest).hexdigest() == ref['manifest_sha256'], 'MANIFEST_HASH')
        entries = json.loads(manifest)['files']; files = {r['path']: r for r in entries}
        require(len(files) == len(entries), 'MANIFEST_DUPLICATE')
        def read(name):
            require(name in files and name in names, 'MEMBER_MISSING:'+name)
            b = z.read(name); h = hashlib.sha256(b).hexdigest()
            require(len(b) == files[name]['bytes'] and h == files[name]['sha256'], 'MEMBER_HASH:'+name)
            hashes[name] = h
            return json.loads(b)
        for run in selected:
            print('[same-source] '+run['run_id']+' START', flush=True)
            require(run['role'] == 'Pilot', 'ROLE')
            base = 'runs/'+run['run_id']+'/model/'
            raw = read(base+'timeline/capture.json'); tokens = read(base+'tokens.json')
            require(hashes[base+'timeline/capture.json'] == run['capture_sha256'] and
                raw['session_id'] == tokens['identity']['run_id'] == run['run_id'] and
                tokens['token_ids'] == run['tokens'] and tokens['actual_input_tokens'] == run['input_tokens'] and
                tokens['identity']['data_role'] == 'Pilot' and tokens['identity']['run_role'] == 'PILOT' and
                tokens['early_eos'] is False and tokens['actual_output_tokens'] == 2, 'RUN_TOKEN_IDENTITY')
            scopes = []; proofs = []
            for i, detail in enumerate(run['token_details']):
                sn = base+f'scope_token{i}.json'; rn = base+f'derived_token{i}/result.json'
                scope = read(sn); saved = read(rn)
                require(scope == detail['scope'] and scope['actual_token_ids'] == tokens['token_ids'][i] and
                    (scope['pid'],scope['tid']) == (tokens['pid'],tokens['tid']), 'TOKEN_SCOPE')
                require(saved['schema_version'] == 'cupti-timeline-adapter/0.3.0' and
                    saved['input']['capture_sha256'] == run['capture_sha256'] and
                    saved['input']['scope_sha256'] == hashes[sn], 'SAVED_INPUT_BINDING')
                scopes.append(scope); proofs.append(saved['result'])
            result = audit_run(raw, scopes, proofs)
            result.update(run_id=run['run_id'],block=run['block'],input_tokens=run['input_tokens'],
                raw_sha256=run['capture_sha256'],source_role='Pilot')
            reports.append(result)
            print('[same-source] '+run['run_id']+' '+result['status'], flush=True)
            del raw, scopes, proofs
    require(source_index.read_bytes() == source_bytes and filehash(archive_path) == ref['sha256'], 'INPUT_CHANGED')
    require(all(filehash(root/p) == h for p,h in code_hashes.items()), 'CODE_CHANGED')
    value = dict(schema_version=VERSION, role=ROLE, archive_sha256=ref['sha256'],
        manifest_sha256=ref['manifest_sha256'], source_index_sha256=hashlib.sha256(source_bytes).hexdigest(),
        consumed_member_hashes=hashes, analysis_sources=code_hashes, runs=reports,
        counts=dict(runs=len(reports),complete_window_previews=sum(r['windows'] is not None for r in reports),
            blocked=sum(r['windows'] is None for r in reports)), elapsed_seconds=time.perf_counter()-started,
        production_A_B_changed=False, new_GPU_qualification=False)
    output.mkdir(parents=True, exist_ok=False)
    with (output/'same_source_migration.json').open('x', encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2)
    return value


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for k in ('archive','source-index','output'):
        p.add_argument('--'+k, type=Path, required=True)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument('--run-id'); group.add_argument('--all-runs', action='store_true')
    a = p.parse_args(); v = review_archive(a.archive,a.source_index,a.output,run_id=a.run_id,all_runs=a.all_runs)
    print(json.dumps(dict(version=VERSION,counts=v['counts'],output=str(a.output))))


if __name__ == '__main__':
    main()
