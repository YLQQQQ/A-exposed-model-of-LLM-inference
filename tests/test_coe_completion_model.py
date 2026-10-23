"""Independent literal operation-time answers, not new CUDA qualification."""
from copy import deepcopy
import importlib
import importlib.util
import hashlib
import json
import zipfile

import pytest


def model():
    assert importlib.util.find_spec('analysis.coe_completion_model'), 'completion model connection missing'
    return importlib.import_module('analysis.coe_completion_model')


def members():
    # Same-stream predecessor K, a real nonzero Memset, and operation-internal D2H.
    return [dict(id='k', kind='KERNEL', start=30, end=55),
            dict(id='m', kind='MEMSET', start=56, end=60),
            dict(id='d', kind='MEMCPY', start=61, end=62)]


def test_gapped_operation_has_three_exact_parts_not_terminal_distance_as_wait():
    v = model().describe([40, 44], [45, 70], members(), 'd')
    # [40,55) + [56,60) + [61,62) = 20, not the 22-tick terminal span.
    assert (v['operation_wall_ns'], v['coe_ns'], v['uncovered_ns']) == (30, 20, 10)
    assert v['last_necessary_end_ns'] == 62
    assert v['terminal_relative_copy_ns'] == 22
    assert (v['uncovered_before_terminal_ns'], v['after_terminal_to_sync_return_ns']) == (2, 8)
    assert v['uncovered_intervals'] == [[55, 56], [60, 61], [62, 70]]
    assert v['coe_by_api_part_ns'] == dict(copy=4, between=1, sync=15)
    assert v['pure_host_blocking_ns'] is None and v['removable_latency_ns'] is None


def test_completed_members_are_retained_with_legal_zero_and_negative_terminal_offset():
    v = model().describe([10, 12], [12, 14], [dict(id='d', kind='MEMCPY', start=3, end=4)], 'd')
    assert v['member_count'] == 1 and v['coe_ns'] == 0
    assert v['terminal_relative_copy_ns'] == -6
    assert (v['uncovered_before_terminal_ns'], v['after_terminal_to_sync_return_ns']) == (0, 4)
    assert v['uncovered_intervals'] == [[10, 14]]


def test_union_deduplicates_kernel_memop_overlap_but_preserves_component_provenance():
    rows = [dict(id='k', kind='KERNEL', start=0, end=8), dict(id='d', kind='MEMCPY', start=4, end=10)]
    v = model().describe([2, 9], [9, 12], rows, 'd')
    assert v['coe_ns'] == 8 and v['kernel_ns'] == 6 and v['memop_ns'] == 6
    assert v['kernel_memop_overlap_ns'] == 4 and v['uncovered_ns'] == 2


@pytest.mark.parametrize('damage,reason', [
    ('duplicate', 'MEMBER_DUPLICATE'), ('missing', 'TERMINAL'),
    ('not_last', 'TERMINAL'), ('after_return', 'COMPLETION'),
    ('pair_order', 'OPERATION_ORDER'), ('unknown_kind', 'MEMBER_KIND'),
    ('float', 'TIME_RANGE'), ('empty', 'MEMBER_EMPTY'),
])
def test_model_does_not_turn_invalid_evidence_into_zero(damage, reason):
    rows = members(); terminal = 'd'; copy = [40, 44]; sync = [45, 70]
    if damage == 'duplicate': rows.append(deepcopy(rows[0]))
    if damage == 'missing': terminal = 'absent'
    if damage == 'not_last': terminal = 'k'
    if damage == 'after_return': rows[-1]['end'] = 71
    if damage == 'pair_order': copy[1] = 46
    if damage == 'unknown_kind': rows[0]['kind'] = 'UNSUPPORTED'
    if damage == 'float': copy[0] = 40.0
    if damage == 'empty': rows = []
    with pytest.raises(ValueError, match=reason): model().describe(copy, sync, rows, terminal)


def test_preview_uses_existing_budget_migration_with_original_wait_deduplicated():
    v = model().describe([4, 10], [10, 12], [dict(id='k', kind='KERNEL', start=3, end=9),
        dict(id='d', kind='MEMCPY', start=9, end=11)], 'd')
    atoms = [dict(start=0, end=4, category='submit', source_ids=['launch']),
             dict(start=4, end=10, category='submit', source_ids=['copy']),
             dict(start=10, end=11, category='device_wait', source_ids=['sync']),
             dict(start=11, end=12, category='residual', source_ids=['sync'])]
    original = deepcopy(atoms)
    p = model().preview([0, 12], atoms, [v, v])
    assert atoms == original
    assert p['candidate_budgets_ns'] == dict(host=0, submit=4, non_submit=0,
        completion_exposure=7, residual=1, unattributed=0)
    assert p['migrated_ns'] == 6 and p['original_device_wait_ns'] == 1
    assert p['migration'][0]['source_ids'] == ['copy']
    assert p['production_A_B_changed'] is False


def test_unknown_original_source_cannot_be_moved_into_candidate_exposure():
    v = model().describe([4, 10], [10, 12], [dict(id='d', kind='MEMCPY', start=6, end=8)], 'd')
    atoms = [dict(start=0, end=12, category='unattributed', source_ids=['unresolved'])]
    with pytest.raises(ValueError, match='UNATTRIBUTED'): model().preview([0, 12], atoms, [v])
    with pytest.raises(ValueError, match='SOURCE_PROVENANCE'):
        model().preview([0, 12], [dict(start=0, end=12, category='submit')], [v])


def test_saved_member_assurance_and_arithmetic_are_separate():
    # Input is explicitly a saved local S result; this routine must not claim
    # independent S recovery or full physical W just because arithmetic agrees.
    raw = dict(schema_version='cupti-timeline-capture/0.1.0', session_id='r', pid=7,
        clock='CUPTI_TIMESTAMP_NS', quality=dict(closed=True, errors=[], overflow=0,
            dropped=0, dropped_query_errors=0, dropped_scopes=[[3, 4]]),
        records=[dict(id='copy', kind='API', domain='RUNTIME', pid=7, tid=9,
                      start=40, end=44, return_code=0),
                 dict(id='sync', kind='API', domain='RUNTIME', pid=7, tid=9,
                      start=45, end=70, return_code=0),
                 *[dict(v, pid=7, device=0, context=3, stream=4) for v in members()]])
    scope = dict(session_id='r', pid=7, tid=9, device=0, context=3, stream=4,
        request_start=10, drain_end=5, completion_end=75, copy_api='copy', sync_api='sync',
        actual_token_ids=[17], completion_proof='HOST_TOKEN_READABLE', ownership='CLOSED_SINGLE_FIFO_NO_EVENTS_OR_GRAPHS')
    result = dict(schema_version='submit-effect-bridge/0.3.0', status='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS',
        session_id='r', clock='CUPTI_TIMESTAMP_NS', members=['k', 'm', 'd'], terminal='d',
        coe_ns=20, operation_wall_ns=30, sync_intersection_ns=15,
        activity_union=[[40, 55], [56, 60], [61, 62]], closed_prior_ids=[], logical_zero_call_ids=[])
    v = model().from_admitted(raw, scope, result)
    assert v['coe_ns'] == 20 and v['phase_wall_ns'] == 65
    assert v['necessary_current_phase_before_copy_ns'] == 10
    assert v['membership_assurance'] == 'REUSED_ACCEPTED_LOCAL_S_NOT_RECONSTRUCTED'
    assert v['full_physical_W_qualified'] is False
    assert v['original_A_extension'] == 'NOT_ASSESSED_NO_QUALIFIED_A_ATOMS'
    for field, value, reason in [('coe_ns', 19, 'SAVED_ARITHMETIC'),
                                ('status', 'BLOCKED', 'ADMISSION')]:
        bad = deepcopy(result); bad[field] = value
        with pytest.raises(ValueError, match=reason): model().from_admitted(raw, scope, bad)
    bad = deepcopy(raw); bad['records'][-1]['stream'] = 8
    with pytest.raises(ValueError, match='MEMBER_SCOPE'): model().from_admitted(bad, scope, result)


def archive_fixture(tmp_path, damage=None):
    """Complete tiny saved-file chain. Literal CPU source, never target evidence."""
    scope = dict(session_id='r', pid=7, tid=9, device=0, context=3, stream=4,
        request_start=10, drain_end=5, completion_end=75, copy_api='copy', sync_api='sync',
        actual_token_ids=[17], completion_proof='HOST_TOKEN_READABLE', ownership='CLOSED_SINGLE_FIFO_NO_EVENTS_OR_GRAPHS')
    raw = dict(schema_version='cupti-timeline-capture/0.1.0', session_id='r', pid=7,
        clock='CUPTI_TIMESTAMP_NS', quality=dict(closed=True, errors=[], overflow=0,
            dropped=0, dropped_query_errors=0, dropped_scopes=[[3, 4]]), records=[
            dict(id='copy', kind='API', domain='RUNTIME', pid=7, tid=9, start=40, end=44, return_code=0),
            dict(id='sync', kind='API', domain='RUNTIME', pid=7, tid=9, start=45, end=70, return_code=0),
            *[dict(v, pid=7, device=0, context=3, stream=4) for v in members()]])
    result = dict(schema_version='submit-effect-bridge/0.3.0', status='VALID_UNDER_DECLARED_SUPPORT_ASSUMPTIONS',
        session_id='r', clock='CUPTI_TIMESTAMP_NS', members=['k', 'm', 'd'], terminal='d',
        coe_ns=20, operation_wall_ns=30, sync_intersection_ns=15,
        activity_union=[[40, 55], [56, 60], [61, 62]], closed_prior_ids=[], logical_zero_call_ids=[])
    encode = lambda v: json.dumps(v, sort_keys=True).encode()
    raw_bytes, scope_bytes = encode(raw), encode(scope)
    saved = dict(schema_version='cupti-timeline-adapter/0.3.0', result=result, input=dict(
        capture_sha256=hashlib.sha256(raw_bytes).hexdigest(), scope_sha256=hashlib.sha256(scope_bytes).hexdigest()))
    tokens = dict(identity=dict(run_id='r', data_role='Pilot', run_role='PILOT'),
        actual_input_tokens=512, token_ids=[[17]], early_eos=False, actual_output_tokens=1, pid=7, tid=9)
    if damage == 'token': tokens['token_ids'] = [[18]]
    if damage == 'scope_hash': saved['input']['scope_sha256'] = '0'*64
    if damage == 'blocked': result['status'] = 'BLOCKED'
    files = {'runs/r/model/timeline/capture.json': raw_bytes, 'runs/r/model/tokens.json': encode(tokens),
             'runs/r/model/scope_token0.json': scope_bytes, 'runs/r/model/derived_token0/result.json': encode(saved)}
    manifest = encode(dict(schema_version='memset-micro-artifacts/0.1.0', files=[
        dict(path=n, bytes=len(b), sha256=hashlib.sha256(b).hexdigest()) for n, b in files.items()]))
    package = tmp_path/'sealed.zip'
    with zipfile.ZipFile(package, 'w') as z:
        for n, b in files.items(): z.writestr(n, b)
        z.writestr('artifact_manifest.json', manifest)
    index = dict(schema_version='cupti-input-pilot-closeout/0.1.0', archive_reference=dict(
        bytes=package.stat().st_size, sha256=hashlib.sha256(package.read_bytes()).hexdigest(),
        manifest_sha256=hashlib.sha256(manifest).hexdigest()), runs=[dict(run_id='r', role='Pilot',
        input_tokens=512, block=1, tokens=[[17]], capture_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        token_details=[dict(scope=scope)])])
    if damage == 'archive_hash': index['archive_reference']['sha256'] = '0'*64
    index_path = tmp_path/'sources.json'; index_path.write_bytes(encode(index))
    return package, index_path


def test_real_archive_reader_consumes_bound_files_and_refuses_overwrite(tmp_path):
    package, index = archive_fixture(tmp_path)
    original = package.read_bytes(); output = tmp_path/'derived'
    result = model().review_archive(package, index, output)
    assert result['operations'][0]['coe_ns'] == 20
    assert result['operations'][0]['after_terminal_to_sync_return_ns'] == 8
    assert len(result['consumed_member_hashes']) == 4
    assert json.loads((output/'completion_model.json').read_text()) == result
    assert package.read_bytes() == original
    with pytest.raises(ValueError, match='NO_OVERWRITE'): model().review_archive(package, index, output)


@pytest.mark.parametrize('damage,reason', [('archive_hash', 'ARCHIVE_IDENTITY'),
    ('scope_hash', 'SAVED_INPUT_BINDING'), ('token', 'TOKEN_IDENTITY'), ('blocked', 'ADMISSION')])
def test_actual_file_chain_rejects_conflicting_saved_inputs(tmp_path, damage, reason):
    package, index = archive_fixture(tmp_path, damage)
    output = tmp_path/'rejected'
    with pytest.raises(ValueError, match=reason): model().review_archive(package, index, output)
    assert not output.exists()
