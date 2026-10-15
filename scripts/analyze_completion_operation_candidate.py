"""Bounded, read-only exploratory copy+sync analysis. NOT production S/A/B.

Only the twelve already reviewed G1 SQLite inputs are supported. No torch,
collector, Canonical/domain loader, or production accounting imports.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import csv
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import sqlite3


VERSION = "COMPLETION-OPERATION-CANDIDATE/0.1"
ROLE = "EXPLORATORY_POSTHOC_NOT_FORMAL_ACCOUNTING"
REFERENCE_SHA = "08523a5166b8b75c50ae71f2cdb287759e367f7d3624e80cb7c042301ae9792e"
PRIMARY_SQLITE_SHA = "84d3a0cfc8afab129f3c07b893d5155c1ee7101017b376359303f0cfec70d87e"


class CandidateError(ValueError):
    pass


def require(ok, reason):
    if not ok:
        raise CandidateError(reason)


@dataclass(frozen=True)
class Api:
    key: str
    start: int
    end: int
    correlation: int
    thread: int
    return_code: int = 0


@dataclass(frozen=True)
class Activity:
    key: str
    start: int
    end: int
    correlation: int
    process: int
    device: int
    context: int
    stream: int
    kind: str


def clipped_union(start, end, intervals):
    require(start <= end, "INTERVAL_ORDER")
    pieces = []
    for a, b in intervals:
        require(isinstance(a, int) and isinstance(b, int) and a <= b, "INTERVAL_ORDER")
        a, b = max(start, a), min(end, b)
        if a < b:
            pieces.append((a, b))
    result = []
    for a, b in sorted(pieces):
        if result and a <= result[-1][1]:
            result[-1] = (result[-1][0], max(b, result[-1][1]))
        else:
            result.append((a, b))
    return result


def completion_overlap(copy, sync, intervals):
    require(copy[0] <= copy[1] <= sync[0] <= sync[1], "OPERATION_ORDER")
    intervals = list(intervals)
    merged = clipped_union(copy[0], sync[1], intervals)
    length = lambda pieces: sum(b - a for a, b in pieces)
    covered = length(merged)
    complement = []
    cursor = copy[0]
    for a, b in merged:
        if cursor < a:
            complement.append((cursor, a))
        cursor = b
    if cursor < sync[1]:
        complement.append((cursor, sync[1]))
    return dict(candidate_ns=covered,
        original_sync_ns=length(clipped_union(*sync, intervals)),
        copy_api_activity_ns=length(clipped_union(*copy, intervals)),
        between_apis_activity_ns=length(clipped_union(copy[1], sync[0], intervals)),
        wall_ns=sync[1] - copy[0], uncovered_ns=sync[1] - copy[0] - covered,
        activity_union=merged, uncovered_intervals=complement)


def recover_suffix(activities, apis, *, request_start, drain_end, sync, scope, thread):
    """Qualified local FIFO suffix, NOT a claim to full physical W.

    Every input effect has an explicit submit reference. A complete historical
    inventory is retained separately even when its contribution projects to 0.
    """
    require(drain_end is not None and drain_end <= request_start <= sync[0] <= sync[1], "DRAIN_ORDER")
    require(len({a.key for a in activities}) == len(activities), "DUPLICATE_ACTIVITY")
    by_corr = defaultdict(list)
    for api in apis:
        by_corr[api.correlation].append(api)
    members, prior, future = [], [], []
    for activity in activities:
        matches = by_corr[activity.correlation]
        require(len(matches) == 1, "CORRELATION:" + activity.key)
        api = matches[0]
        require(api.start <= api.end and activity.start <= activity.end, "RECORD_ORDER")
        require(api.return_code == 0, "SUBMIT_FAILED:" + api.key)
        if api.end <= drain_end:
            require(activity.end <= drain_end, "PRIOR_NOT_CLOSED:" + activity.key)
            prior.append(activity)
        elif api.start >= sync[0]:
            future.append(activity)
        else:
            require(request_start <= api.start <= api.end <= sync[0], "SUBMISSION_BOUNDARY:" + api.key)
            require((activity.process, activity.device, activity.context, activity.stream) == scope,
                    "SUFFIX_SCOPE:" + activity.key)
            require(api.thread == thread, "SUFFIX_THREAD:" + activity.key)
            require(api.start <= activity.start and activity.end <= sync[1], "COMPLETION_CONFLICT:" + activity.key)
            members.append(activity)
    return members, prior, future


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one(values, reason):
    values = list(values)
    require(len(values) == 1, reason + ":" + str(len(values)))
    return values[0]


def normalized(name):
    return re.sub(r"_v[0-9]+$", "", name)


def enum_name(db, table, number):
    return one(db.execute(f'SELECT name FROM {table} WHERE id=?', (number,)), "ENUM")[0]


def validate_identity(receipt, token, formal_reference):
    receipt_keys = {'attempt_id', 'data_role', 'experiment_id', 'pass_id', 'run_id', 'run_role', 'wmpc_id'}
    require(set(receipt) == receipt_keys and set(token) == receipt_keys | {'formal_reference', 'request_id', 'repeat_id'}, 'IDENTITY_FIELDS')
    require(all(token[k] == receipt[k] for k in receipt_keys), 'IDENTITY_CONFLICT')
    require(token['formal_reference'] == formal_reference and token['request_id'] == 'request-0'
            and token['repeat_id'] == '0' and token['run_role'] == 'FORMAL'
            and token['data_role'] == 'Formal' and token['pass_id'] == 'pass1', 'IDENTITY_REFERENCE')


def write_summary(rows, path):
    fields = ['version', 'analysis_role', 'source_data_role', 'condition', 'block', 'token_index',
              'candidate_ns', 'original_sync_ns', 'wall_ns', 'uncovered_ns', 'copy_api_activity_ns',
              'between_apis_activity_ns', 'kernel_intersection_ns', 'memop_intersection_ns',
              'copy_only_correlation_intersection_ns', 'member_count', 'closed_prior_count',
              'completed_before_copy_count', 'sqlite_sha256']
    with path.open('x', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        for row in rows:
            values = dict(row, version=VERSION, analysis_role=ROLE, source_data_role='Formal')
            writer.writerow({key: values[key] for key in fields})


def verify_device_bridge(db, process_id, activity_device, context_id, probe, preflight):
    context = dict(one(db.execute('SELECT * FROM TARGET_INFO_CUDA_CONTEXT_INFO WHERE processId=? AND contextId=?',
                                 (process_id, context_id)), 'DEVICE_CONTEXT'))
    require(context['deviceId'] == activity_device, 'DEVICE_CONTEXT_ACTIVITY')
    target = dict(one(db.execute('SELECT * FROM TARGET_INFO_CUDA_DEVICE WHERE pid=? AND cudaId=?',
                                (process_id, context['deviceId'])), 'DEVICE_TARGET'))
    gpu = dict(one(db.execute('SELECT * FROM TARGET_INFO_GPU WHERE id=?', (target['gpuId'],)), 'DEVICE_GPU'))
    uid = lambda value: value.lower().removeprefix('gpu-')
    require(probe['pid'] == process_id and probe['gpu_index_logical'] == target['cudaId'], 'DEVICE_PROCESS_LOGICAL')
    require(len({uid(v) for v in (target['uuid'], gpu['uuid'], probe['gpu_uuid'], preflight['gpu_uuid'])}) == 1,
            'DEVICE_UUID')
    # Compare PCI components, not spelling of domain padding/case.
    pci = lambda value: tuple(int(part, 16) for part in re.split(r'[:.]', value))
    require(pci(probe['pci_bus_id']) == pci(preflight['pci_bus_id']) == pci(gpu['busLocation']), 'DEVICE_PCI')
    return dict(physical_index=preflight['gpu_index_physical'], logical_index=probe['gpu_index_logical'],
                activity_device=activity_device, context=context_id, inventory_gpu=target['gpuId'],
                uuid=uid(target['uuid']), pci=gpu['busLocation'])


def analyze_run(root, base, reference, run, sources):
    directory = base / "original/source/batch" / run / "collection"

    def read_bound(path, expected=None):
        data = path.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        rel = path.relative_to(root).as_posix()
        require(expected is None or digest == expected, "INPUT_HASH:" + rel)
        sources[rel] = digest
        return json.loads(data)

    old = read_bound(base / "derived_e19_v0_1" / (run + "_review.json"))
    require(old['status'] == 'QUALITY_CHECK_PASSED_NOT_QUALIFICATION', "OLD_REVIEW")
    receipt = read_bound(directory / "input_receipt.json", old['input_receipt_sha256'])
    require(receipt['identity']['run_id'] == run, "INPUT_RUN")
    for key in ('sqlite', 'formal_tokens', 'host_ledger', 'runner_source', 'drain_ledger', 'cuda_probe', 'preflight'):
        artifact = receipt['artifacts'][key]
        path = directory / artifact['filename']
        require(path.resolve().is_relative_to(directory.resolve()), "ARTIFACT_PATH")
        require(path.stat().st_size == artifact['size_bytes'] and sha(path) == artifact['sha256'], "ARTIFACT_HASH:" + key)
        rel = path.relative_to(root).as_posix()
        require(rel not in reference['sources'] or reference['sources'][rel] == artifact['sha256'], "REFERENCE_HASH")
        sources[rel] = artifact['sha256']
    tokens = read_bound(directory / receipt['artifacts']['formal_tokens']['filename'])
    token_request = one(tokens['requests'], "TOKEN_REQUEST")
    identity = token_request['identity']
    validate_identity(receipt['identity'], identity, old['formal_admission']['reference'])
    expected_values = [[463], [2529]] if '-G32-' in run else [[29184], [6556]]
    require(token_request['token_ids'] == expected_values, "TOKEN_VALUES")
    drains = read_bound(directory / receipt['artifacts']['drain_ledger']['filename'])['drains']
    probe = read_bound(directory / receipt['artifacts']['cuda_probe']['filename'])
    preflight = read_bound(directory / receipt['artifacts']['preflight']['filename'])
    drain_ledger = one(drains, "DRAIN_LEDGER")
    require(drain_ledger['identity'] == identity and drain_ledger['status'] == 'COMPLETE'
            and drain_ledger['error'] is None, "DRAIN_LEDGER_IDENTITY")
    path = directory / receipt['artifacts']['sqlite']['filename']
    if '-b1-G512-' in run:
        require(sha(path) == PRIMARY_SQLITE_SHA, "PRIMARY_SQLITE_HASH")
    connection = sqlite3.connect(path.resolve().as_uri() + '?mode=ro&immutable=1', uri=True)
    connection.row_factory = sqlite3.Row
    try:
        markers, scopes, drain_ranges = [], [], []
        for r in connection.execute('SELECT rowid AS rid,* FROM NVTX_EVENTS WHERE text IS NOT NULL'):
            text = r['text']
            if text.startswith('EXPOSEDPATH_BOUNDARY_V1:'):
                payload = json.loads(text.split(':', 1)[1])
                if payload['identity'] == identity:
                    markers.append((dict(r), payload))
            elif text.startswith('EXPOSEDPATH_JSON_V1:'):
                payload = json.loads(text.split(':', 1)[1])
                if payload.get('run_id') == run and payload.get('sync_origin') == 'natural_token_ready':
                    scopes.append((dict(r), payload))
            elif text.startswith('EXPOSEDPATH_DRAIN_V1:'):
                payload = json.loads(text.split(':', 1)[1])
                if payload['identity'] == identity:
                    drain_ranges.append((dict(r), payload))
        origin, _ = one(((r, p) for r, p in markers if p['boundary_kind'] == 'request_start'), 'REQUEST_START')
        drain, drain_payload = one(drain_ranges, 'DRAIN_RANGE')
        require(drain_payload['operation_id'] == drain_ledger['operation_id'] and drain['end'] <= origin['start'], 'DRAIN_BINDING')
        thread = origin['globalTid']
        # Serialized Nsight global IDs; cross-checked against this file's target
        # device PID below. Not device-number equality or a cross-run PID guess.
        global_pid = (thread >> 24) << 24
        process_id = (thread >> 24) & 0xFFFFFF
        runtime = [dict(r) for r in connection.execute(
            'SELECT a.rowid AS rid,a.*,s.value AS name FROM CUPTI_ACTIVITY_KIND_RUNTIME a JOIN StringIds s ON a.nameId=s.id')
            if ((r['globalTid'] >> 24) << 24) == global_pid]
        apis = [Api('RUNTIME:' + str(r['rid']), r['start'], r['end'], r['correlationId'], r['globalTid'], r['returnValue']) for r in runtime]
        api_by_correlation = defaultdict(list)
        for api in apis:
            api_by_correlation[api.correlation].append(api)
        drain_api = one((r for r in runtime if normalized(r['name']) == 'cudaDeviceSynchronize'
                        and drain['start'] <= r['start'] <= r['end'] <= drain['end']), 'DRAIN_API')
        require(drain_api['returnValue'] == 0 and drain_api['globalTid'] == thread, 'DRAIN_SUCCESS')
        physical_drain = dict(one(connection.execute('SELECT rowid AS rid,* FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE correlationId=? AND globalPid=?',
            (drain_api['correlationId'], global_pid)), 'DRAIN_PHYSICAL'))
        require(enum_name(connection, 'ENUM_CUPTI_SYNC_TYPE', physical_drain['syncType']).endswith('_CONTEXT_SYNCHRONIZE'), 'DRAIN_TYPE')
        activities, raw_effects = [], {}
        for kind in ('KERNEL', 'MEMCPY', 'MEMSET'):
            for r in connection.execute(f'SELECT rowid AS rid,* FROM CUPTI_ACTIVITY_KIND_{kind} WHERE globalPid=?', (global_pid,)):
                key = kind + ':' + str(r['rid'])
                raw_effects[key] = dict(r)
                activities.append(Activity(key, r['start'], r['end'], r['correlationId'], r['globalPid'],
                    r['deviceId'], r['contextId'], r['streamId'], kind))
        outputs, inventories = [], []
        for index in (0, 1):
            scope, scope_payload = one(((r, p) for r, p in scopes if p['token_index'] == index), 'TOKEN_SCOPE')
            anchor, _ = one(((r, p) for r, p in markers if p['token_index'] == index), 'TOKEN_POINT')
            require(scope_payload['request_id'] == identity['request_id'] and scope['globalTid'] == anchor['globalTid'] == thread,
                    'TOKEN_SCOPE_IDENTITY')
            local = [r for r in runtime if r['globalTid'] == thread and scope['start'] <= r['start'] <= r['end'] <= scope['end']]
            copy = one((r for r in local if normalized(r['name']) == 'cudaMemcpyAsync'), 'COPY')
            sync = one((r for r in local if normalized(r['name']) == 'cudaStreamSynchronize'), 'SYNC')
            require(len(local) == 2 and copy['returnValue'] == sync['returnValue'] == 0, 'PAIR_SUCCESS_AND_ADJACENCY')
            require(copy['end'] <= sync['start'] and sync['end'] < anchor['start'], 'PAIR_ORDER')
            mem_key = one((a.key for a in activities if a.kind == 'MEMCPY' and a.correlation == copy['correlationId']), 'COPY_EFFECT')
            mem = raw_effects[mem_key]
            physical = dict(one(connection.execute('SELECT rowid AS rid,* FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION WHERE correlationId=? AND globalPid=?',
                (sync['correlationId'], global_pid)), 'SYNC_EFFECT'))
            require(enum_name(connection, 'ENUM_CUPTI_SYNC_TYPE', physical['syncType']).endswith('_STREAM_SYNCHRONIZE'), 'SYNC_TYPE')
            necessary_scope = (global_pid, mem['deviceId'], mem['contextId'], mem['streamId'])
            require(tuple(physical[k] for k in ('globalPid', 'deviceId', 'contextId', 'streamId')) == necessary_scope, 'COPY_SYNC_SCOPE')
            require(enum_name(connection, 'ENUM_CUDA_MEMCPY_OPER', mem['copyKind']) == 'CUDA_MEMCPY_KIND_DTOH', 'COPY_DIRECTION')
            src, dst = (enum_name(connection, 'ENUM_CUDA_MEM_KIND', mem[k]) for k in ('srcKind', 'dstKind'))
            require(src == 'CUDA_MEMOPR_MEMORY_KIND_DEVICE' and dst == 'CUDA_MEMOPR_MEMORY_KIND_PAGEABLE' and mem['bytes'] == 8,
                    'COPY_MEMORY_AND_SIZE')
            target = verify_device_bridge(connection, process_id, mem['deviceId'], mem['contextId'], probe, preflight)
            require(physical_drain['deviceId'] == mem['deviceId'] and physical_drain['contextId'] == mem['contextId'], 'DRAIN_DEVICE_CONTEXT')
            require(drain['end'] <= origin['start'] <= copy['start'] <= mem['start'] <= mem['end'] <= sync['end'], 'CLOCK_ORDER')
            require(not any(r['start'] >= drain['end'] and r['start'] < sync['start'] and
                normalized(r['name']) in ('cudaStreamWaitEvent', 'cudaEventRecord', 'cudaEventSynchronize', 'cudaGraphLaunch') for r in runtime),
                'UNSUPPORTED_INCOMING_DEPENDENCY')
            members, prior, future = recover_suffix(activities, apis, request_start=origin['start'], drain_end=drain_api['end'],
                sync=(sync['start'], sync['end']), scope=necessary_scope, thread=thread)
            require(any(a.key == mem_key for a in members), 'COPY_NOT_IN_SUFFIX')
            # Do not silently treat a missing effect from a recorded submit as 0.
            counts = defaultdict(int)
            for a in members:
                counts[a.correlation] += 1
            for r in runtime:
                if origin['start'] <= r['start'] < sync['start'] and normalized(r['name']) in (
                        'cudaLaunchKernel', 'cudaMemcpyAsync', 'cudaMemsetAsync'):
                    require(counts[r['correlationId']] > 0, 'SUBMIT_EFFECT_MISSING:' + str(r['rid']))
            intervals = [(a.start, a.end) for a in members]
            result = completion_overlap((copy['start'], copy['end']), (sync['start'], sync['end']), intervals)
            terminal = one((a for a in members if a.end == max(m.end for m in members)), 'TERMINAL')
            old_row = one((r for r in reference['rows'] if r['run_id'] == run and r['token_index'] == index), 'REFERENCE_ROW')
            require((copy['rid'], sync['rid'], mem['rid'], anchor['rid']) ==
                    (old_row['copy_rowid'], old_row['sync_rowid'], old_row['d2h_rowid'], old_row['anchor_rowid']), 'REFERENCE_RECORDS')
            kernel_union = clipped_union(copy['start'], sync['end'], ((a.start, a.end) for a in members if a.kind == 'KERNEL'))
            memop_union = clipped_union(copy['start'], sync['end'], ((a.start, a.end) for a in members if a.kind != 'KERNEL'))
            # Row references plus the immutable SQLite hash preserve ALL members
            # without another copy of the Raw inventory or a giant domain file.
            inventories.append(dict(token_index=index,
                sqlite_sha256=receipt['artifacts']['sqlite']['sha256'],
                members=[dict(record=a.key, submit=one(api_by_correlation[a.correlation], 'MEMBER_API').key) for a in members],
                closed_raw_prior_ids=[a.key for a in prior], closed_prior_latest_end_ns=max(a.end for a in prior),
                future_excluded_ids=[a.key for a in future],
                full_physical_W_qualified=False, legacy_ptds_suffix_and_edges_equal=True,
                equality_basis='all post-drain prior submissions are same-thread same observed FIFO; other observed prefixes closed before drain; no incoming event/graph edges',
                support_assumption='qualified isolated main-thread G1; no unrecorded incoming dependency; UNKNOWN is not zero'))
            outputs.append(dict(run_id=run, condition=old['condition'], block=old['block'], token_index=index,
                role=ROLE, original_data_role='Formal', scope='QUALIFIED_LOCAL_REQUEST_SUFFIX_NOT_FULL_PHYSICAL_W',
                actual_token=expected_values[index], sqlite_sha256=receipt['artifacts']['sqlite']['sha256'],
                trace_clock='NSYS_TRACE_RELATIVE_NS', request_start_ns=origin['start'], thread=thread, scope_identity=necessary_scope,
                target_device=target, source_memory_kind=src, destination_memory_kind=dst,
                copy=copy, d2h=mem, physical_sync=physical, sync=sync, nvtx_scope=scope, anchor=anchor,
                drain_api=drain_api, physical_drain=physical_drain, member_count=len(members),
                completed_before_copy_count=sum(a.end <= copy['start'] for a in members),
                closed_prior_count=len(prior), terminal=asdict(terminal),
                kernel_intersection_ns=sum(b-a for a,b in kernel_union), memop_intersection_ns=sum(b-a for a,b in memop_union),
                copy_only_correlation_intersection_ns=sum(b-a for a,b in clipped_union(copy['start'],sync['end'],[(mem['start'],mem['end'])])),
                dropped_records_status=old['dropped_records_status'], measurement_validity=old['measurement_validity'],
                single_api_completion_guarantee='NOT_ESTABLISHED_BY_ASYNC_PAGEABLE_SEMANTICS',
                composite_completion_guarantee='SUCCESSFUL_SAME_STREAM_SYNC', pure_host_stall_ns=None,
                **result))
        return outputs, inventories
    finally:
        connection.close()
        require(sha(path) == receipt['artifacts']['sqlite']['sha256'], 'SQLITE_CHANGED')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    reference_path = root / '.local/diagnostics/completion_feasibility_v0_3/reference_audit.json'
    require(sha(reference_path) == REFERENCE_SHA, 'REFERENCE_BINDING')
    reference = json.loads(reference_path.read_text(encoding='utf-8'))
    require(not args.output.exists(), 'NO_OVERWRITE')
    args.output.mkdir(parents=True)
    sources = {reference_path.relative_to(root).as_posix(): REFERENCE_SHA}
    rows = []
    base = root / '.local/diagnostics/gate13_complete_v0_1'
    for block in range(1, 7):
        for condition in ('G32', 'G512'):
            run = f'formal-99f3bae966f2-20261010-sixblock-b{block}-{condition}-pass1'
            print('[read-only]', run, flush=True)
            new_rows, inventory = analyze_run(root, base, reference, run, sources)
            rows.extend(new_rows)
            with (args.output / (run + '_sources.json')).open('x', encoding='utf-8') as handle:
                json.dump(inventory, handle, ensure_ascii=False, separators=(',', ':'))
    result = dict(version=VERSION, role=ROLE, rows=rows, sources=sources,
        no_production_analysis_called=True, new_qualification=False,
        statement='candidate completion-operation necessary-activity overlap, NOT pure Host stall or new Formal A')
    with (args.output / 'candidate_results.json').open('x', encoding='utf-8') as handle:
        json.dump(result, handle, ensure_ascii=False, indent=2)
    write_summary(rows, args.output / 'candidate_rows.csv')
    print(json.dumps(dict(rows=len(rows), status='EXPLORATORY_CALCULATION_COMPLETE'), ensure_ascii=False))


if __name__ == '__main__':
    main()
