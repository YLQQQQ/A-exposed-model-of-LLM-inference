"""Conditional oracle checks, NOT a real source/default-stream admission.

The fixtures explicitly posit complete source evidence. They do not infer it
from an observed single stream, or qualify the returned Qwen diagnostic.
"""
from copy import deepcopy

import pytest

from exposedpath_v141.a_accounting import calculate_a_windows
from exposedpath_v141.sync_semantics import analyze_sync_semantics
from test_v141_a_accounting import _activity, _api, _inputs, _window
from test_v141_sync_semantics import _owned_activity, _owned_sync, _semantic_inventory


def evaluate(activities, syncs, mode, *, windows=None, global_reasons=()):
    inventory = _semantic_inventory(deepcopy(activities), mode=mode)
    semantic = tuple(analyze_sync_semantics(inventory, s) for s in syncs)
    apis = tuple(_api(a['enqueue_record_id'], a['enqueue_start_ns'],
                      a['enqueue_end_ns'], 'cudaLaunchKernel', i)
                 for i, a in enumerate(activities))
    gpu = tuple(_activity(a['record_id'], a['start_ns'], a['end_ns'], 'KERNEL', i)
                for i, a in enumerate(activities))
    inputs = _inputs(apis=apis, activities=gpu, syncs=semantic, windows=windows,
                     global_reasons=global_reasons)
    return semantic, calculate_a_windows(inputs)


def components(row):
    return [row[k] for k in ('A_host_path_ns', 'A_cuda_api_ns',
                            'A_device_wait_ns', 'A_sync_residual_ns', 'A_unattributed_ns')]


def three_sync_case():
    activities = [
        _owned_activity('internal', 0, 20, 40, enqueue_start=10, enqueue_end=12),
        _owned_activity('token0', 0, 80, 100, enqueue_start=70, enqueue_end=72),
        _owned_activity('token1', 0, 150, 170, enqueue_start=140, enqueue_end=142),
    ]
    syncs = []
    for name, start, end in [('internal', 30, 50), ('token0', 90, 110), ('token1', 160, 180)]:
        sync = _owned_sync('STREAM', start, end, stream_id=0)
        sync['record_id'] = 'sync:' + name
        syncs.append(sync)
    return activities, syncs


@pytest.mark.parametrize('mode', ['LEGACY', 'PER_THREAD'])
def test_complete_single_fifo_three_sync_oracle_has_identical_a(mode):
    # Catches dropping the internal sync or treating only the final token as wait.
    activities, syncs = three_sync_case()
    windows = (_window(start=0, end=200), _window('prefill', 0, 120),
               _window('decode', 120, 200))
    semantic, rows = evaluate(activities, syncs, mode, windows=windows)
    assert [s['validity'] for s in semantic] == ['VALID_NONEMPTY'] * 3
    assert [s['wait_set_activity_ids'] for s in semantic] == [
        ['internal'], ['internal', 'token0'], ['internal', 'token0', 'token1']]
    assert [s['terminal']['activity_id'] for s in semantic] == ['internal', 'token0', 'token1']
    # Hand arithmetic: 3 disjoint waits of 10, 3 tails of 10, 3 APIs of 2.
    assert {r['phase']: components(r) for r in rows} == {
        'full_request': [134, 6, 30, 30, 0],
        'prefill': [76, 4, 20, 20, 0], 'decode': [58, 2, 10, 10, 0]}


@pytest.mark.parametrize('mode,wait_ids,expected', [
    ('LEGACY', ['other', 'target'], [53, 2, 40, 5, 0]),
    ('PER_THREAD', ['target'], [53, 2, 10, 35, 0]),
])
def test_one_relevant_blocking_stream_breaks_equivalence_despite_same_terminal(mode, wait_ids, expected):
    # Catches admitting default-stream equivalence from terminal identity alone.
    other = _owned_activity('other', 2, 0, 60, enqueue_start=0, enqueue_end=1)
    target = _owned_activity('target', 0, 60, 70, enqueue_start=10, enqueue_end=11)
    semantic, rows = evaluate([other, target], [_owned_sync('STREAM', 30, 75, stream_id=0)], mode)
    assert semantic[0]['validity'] == 'VALID_NONEMPTY'
    assert semantic[0]['wait_set_activity_ids'] == wait_ids
    assert semantic[0]['terminal']['activity_id'] == 'target'
    assert components(rows[0]) == expected


def test_missing_other_stream_can_look_like_valid_single_stream_but_change_a():
    # Independent identifiability counterexample: S cannot detect an omitted
    # activity if a caller falsely supplies a complete/VALID inventory.
    target = _owned_activity('target', 0, 60, 70, enqueue_start=10, enqueue_end=11)
    semantic, rows = evaluate([target], [_owned_sync('STREAM', 30, 75, stream_id=0)], 'LEGACY')
    assert semantic[0]['validity'] == 'VALID_NONEMPTY'
    assert components(rows[0]) == [54, 1, 10, 35, 0]
    # This apparent closure is NOT evidence for real-source completeness.


def test_unknown_mode_preserves_all_three_sync_gaps_not_host_or_residual():
    activities, syncs = three_sync_case()
    semantic, rows = evaluate(activities, syncs, None, windows=(_window(start=0, end=200),))
    assert all(s['primary_reason'] == 'DEFAULT_STREAM_MODE_UNKNOWN' for s in semantic)
    assert components(rows[0]) == [134, 6, 0, 0, 60]


def test_unbounded_input_risk_is_not_only_the_observed_sync_duration():
    activities, syncs = three_sync_case()
    _, rows = evaluate(activities, syncs, 'LEGACY', windows=(_window(start=0, end=200),),
                       global_reasons=('DROPPED_RECORDS',))
    assert components(rows[0]) == [0, 0, 0, 0, 200]
