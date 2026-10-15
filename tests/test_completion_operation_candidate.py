"""Hand-derived model examples; not CUDA or new Formal qualification."""
from dataclasses import replace
import sqlite3

import pytest

from scripts.analyze_completion_operation_candidate import (
    Activity, Api, CandidateError, completion_overlap, recover_suffix, validate_identity,
    verify_device_bridge,
)


def effect(key, start, end, correlation=1, stream=7):
    return Activity(key, start, end, correlation, 100, 0, 1, stream, "KERNEL")


@pytest.mark.parametrize("copy,sync,members,want", [
    # Host useful work [2,8) overlaps the GPU for 6ns. Result is not Host stall.
    ((0, 2), (8, 10), [(1, 9)], (8, 1, 2, 6)),
    # Tiny D2H [9,10), long required kernel [2,9): copy correlation alone loses 5.
    ((4, 10), (10, 12), [(2, 9), (9, 10)], (6, 0, 2, 0)),
    # Completed members stay in W, but contribute zero here.
    ((10, 12), (12, 14), [(0, 4), (4, 5)], (0, 0, 4, 0)),
    # GPU gaps are not activity and must not be counted as a continuous wait.
    ((0, 8), (8, 10), [(1, 3), (7, 8)], (3, 0, 7, 0)),
    # Overlap and duplicate record references are unioned, not double counted.
    ((0, 8), (8, 10), [(1, 6), (3, 9), (1, 6)], (8, 1, 2, 0)),
    # Signed timestamps, crossing zero, and half-open equal boundaries.
    ((-5, 0), (0, 2), [(-8, -2), (0, 0)], (3, 0, 4, 0)),
])
def test_overlap_does_not_turn_envelope_or_gaps_into_wait(copy, sync, members, want):
    result = completion_overlap(copy, sync, members)
    assert (result["candidate_ns"], result["original_sync_ns"],
            result["uncovered_ns"], result["between_apis_activity_ns"]) == want


def test_unrelated_stream_overlap_and_future_submission_are_not_dependencies():
    apis = [Api("a", 0, 1, 1, 12), Api("b", 1, 2, 2, 12),
            Api("future", 12, 13, 3, 12)]
    activities = [effect("K", 1, 3), effect("D", 3, 4, 2), effect("F", 13, 20, 3)]
    members, prior, future = recover_suffix(activities, apis, request_start=0,
        drain_end=-2, sync=(4, 5), scope=(100, 0, 1, 7), thread=12)
    assert [a.key for a in members] == ["K", "D"]
    assert [a.key for a in future] == ["F"]
    # An unrelated U is NOT offered as a member merely because it overlaps.
    assert completion_overlap((0, 2), (2, 5), [(a.start, a.end) for a in members])["candidate_ns"] == 3
    assert prior == []
    # The bounded single-FIFO reader must reject an observed extra stream; it
    # cannot silently include U or silently call it irrelevant without proof.
    with pytest.raises(CandidateError, match='SUFFIX_SCOPE'):
        recover_suffix(activities + [effect('U', 0, 20, 4, stream=9)],
            apis + [Api('unrelated', 0, 0, 4, 12)], request_start=0,
            drain_end=-2, sync=(4, 5), scope=(100, 0, 1, 7), thread=12)


def test_closed_prior_retains_raw_identity_and_completed_required_suffix():
    apis = [Api("old", -10, -9, 0, 99), Api("a", 0, 1, 1, 12)]
    activities = [effect("old", -8, -3, 0, 8), effect("K", 1, 3)]
    members, prior, _ = recover_suffix(activities, apis, request_start=0,
        drain_end=-2, sync=(10, 12), scope=(100, 0, 1, 7), thread=12)
    assert [a.key for a in prior] == ["old"]
    assert [a.key for a in members] == ["K"]
    assert completion_overlap((7, 9), (10, 12), [(a.start, a.end) for a in members])["candidate_ns"] == 0


@pytest.mark.parametrize("mutation,reason", [
    ("pending_prior", "PRIOR_NOT_CLOSED"),
    ("wrong_stream", "SUFFIX_SCOPE"),
    ("wrong_thread", "SUFFIX_THREAD"),
    ("missing_mapping", "CORRELATION"),
    ("ambiguous_mapping", "CORRELATION"),
    ("failed_submit", "SUBMIT_FAILED"),
    ("unfinished_member", "COMPLETION_CONFLICT"),
    ("missing_drain", "DRAIN_ORDER"),
])
def test_scope_and_evidence_conflicts_reject_not_zero(mutation, reason):
    apis = [Api("a", 0, 1, 1, 12)]
    activities = [effect("K", 1, 3)]
    drain = -2
    if mutation == "pending_prior":
        apis.append(Api("old", -10, -9, 0, 99))
        activities.append(effect("old", -8, 1, 0))
    elif mutation == "wrong_stream":
        activities[0] = replace(activities[0], stream=8)
    elif mutation == "wrong_thread":
        apis[0] = replace(apis[0], thread=99)
    elif mutation == "missing_mapping":
        apis.clear()
    elif mutation == "ambiguous_mapping":
        apis.append(replace(apis[0], key="other"))
    elif mutation == "failed_submit":
        apis[0] = replace(apis[0], return_code=1)
    elif mutation == "unfinished_member":
        activities[0] = replace(activities[0], end=13)
    elif mutation == "missing_drain":
        drain = None
    with pytest.raises(CandidateError, match=reason):
        recover_suffix(activities, apis, request_start=0, drain_end=drain,
                       sync=(10, 12), scope=(100, 0, 1, 7), thread=12)


@pytest.mark.parametrize("copy,sync", [((2, 1), (3, 4)), ((0, 4), (3, 5))])
def test_illegal_order_is_not_silently_clipped(copy, sync):
    with pytest.raises(CandidateError, match="ORDER"):
        completion_overlap(copy, sync, [])


def test_changing_start_changes_the_object_not_the_underlying_host_stall():
    # The same physical effects, two different declared operations. This is NOT
    # permission to move the start to obtain the larger answer.
    assert completion_overlap((4, 10), (10, 12), [(2, 9), (9, 10)])["candidate_ns"] == 6
    assert completion_overlap((0, 10), (10, 12), [(2, 9), (9, 10)])["candidate_ns"] == 8


def test_primary_raw_intervals_match_independent_six_piece_sum():
    # Raw record references: K12039/12040/12041, memset343, K12042, memcpy347.
    # Hand sum = 6688 + 4288 + 1434101 + 320 + 79424 + 544 = 1525365.
    result = completion_overlap((86897104, 88771602), (88772503, 88808056), [
        (87084265, 87090953), (87091689, 87095977), (87097353, 88531454),
        (88533182, 88533502), (88608445, 88687869), (88689277, 88689821),
    ])
    assert result['candidate_ns'] == 1525365
    assert result['original_sync_ns'] == 0
    assert result['wall_ns'] == 1910952
    assert result['uncovered_ns'] == 385587


@pytest.mark.parametrize('mutation', [None, 'run_id', 'run_role', 'request_id', 'reference', 'missing'])
def test_receipt_scope_identity_is_bound_to_full_token_identity(mutation):
    receipt = dict(attempt_id='a', data_role='Formal', experiment_id='e', pass_id='pass1',
                   run_id='r', run_role='FORMAL', wmpc_id='w')
    reference = dict(protocol_version='signed', protocol_sha256='p', approval_sha256='s')
    token = dict(**receipt, request_id='request-0', repeat_id='0', formal_reference=reference)
    if mutation in ('run_id', 'run_role', 'request_id'):
        token[mutation] = 'wrong'
    elif mutation == 'reference':
        token['formal_reference'] = dict(reference, protocol_sha256='wrong')
    elif mutation == 'missing':
        token.pop('pass_id')
    if mutation is None:
        validate_identity(receipt, token, reference)
    else:
        with pytest.raises(CandidateError, match='IDENTITY'):
            validate_identity(receipt, token, reference)


@pytest.mark.parametrize('mutation', [None, 'probe_uuid', 'gpu_uuid', 'pci', 'activity_device'])
def test_device_bridge_uses_context_uuid_pci_not_equal_gpu_numbers(mutation):
    db = sqlite3.connect(':memory:')
    db.row_factory = sqlite3.Row
    db.executescript('''
        CREATE TABLE TARGET_INFO_CUDA_CONTEXT_INFO(processId,contextId,deviceId);
        INSERT INTO TARGET_INFO_CUDA_CONTEXT_INFO VALUES(77,1,0);
        CREATE TABLE TARGET_INFO_CUDA_DEVICE(pid,cudaId,gpuId,uuid);
        INSERT INTO TARGET_INFO_CUDA_DEVICE VALUES(77,0,2,'abc');
        CREATE TABLE TARGET_INFO_GPU(id,uuid,busLocation);
        INSERT INTO TARGET_INFO_GPU VALUES(2,'abc','0000:e1:00.0');
    ''')
    probe = dict(pid=77, gpu_index_logical=0, gpu_uuid='GPU-abc', pci_bus_id='0000:E1:00.0')
    preflight = dict(gpu_index_physical=3, gpu_uuid='GPU-abc', pci_bus_id='00000000:E1:00.0')
    device = 0
    if mutation == 'probe_uuid':
        probe['gpu_uuid'] = 'GPU-wrong'
    elif mutation == 'gpu_uuid':
        db.execute("UPDATE TARGET_INFO_GPU SET uuid='wrong'")
    elif mutation == 'pci':
        preflight['pci_bus_id'] = '0000:61:00.0'
    elif mutation == 'activity_device':
        device = 3
    try:
        if mutation is None:
            bridge = verify_device_bridge(db, 77, device, 1, probe, preflight)
            assert bridge['physical_index'] == 3
            assert bridge['inventory_gpu'] == 2
            assert bridge['logical_index'] == 0
        else:
            with pytest.raises(CandidateError, match='DEVICE'):
                verify_device_bridge(db, 77, device, 1, probe, preflight)
    finally:
        db.close()
