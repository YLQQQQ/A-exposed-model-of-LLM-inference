"""CPU-only theory/prototype/input-gap probes, not CUDA or provider qualification.

Literal answers are independent of S/COE recovery. The test-only boundary
prototype is intentionally not connected to a runner or a GPU entry point.
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from exposedpath.gate8_boundary import BOUNDARY_PREFIX, Gate8BoundaryRecorder
from exposedpath.gate8_identity import validate_shape
from exposedpath_v141.a_accounting import calculate_a_windows

# Fixed local fixture builders, never an ambient third-party `tests` package.
_path = Path(__file__).with_name('test_v141_a_accounting.py').resolve()
_spec = importlib.util.spec_from_file_location('_coe_existing_a_cpu_fixture', _path)
_fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_fixture)
_activity, _api, _inputs, _sync = (_fixture._activity, _fixture._api, _fixture._inputs, _fixture._sync)


def independent_overlap(intervals, start, end):
    # Independent integer-cell oracle for small literal CPU examples only.
    assert all(type(t) is int for pair in intervals for t in pair)
    return len({t for lo, hi in intervals for t in range(lo, hi)
                if start <= t < end})


@pytest.mark.parametrize('intervals,copy,sync_return,host,expected', [
    ([(0, 10)], 8, 10, 11, 2),
    ([(0, 10)], 2, 10, 11, 8),  # earlier arrival, same completion
    ([(0, 10)], 9, 10, 11, 1),
    ([(0, 8)], 2, 8, 9, 6),    # COE rises, completion improves
    ([(0, 20)], 19, 20, 21, 1), # more work, less COE, later completion
    ([(0, 4), (8, 10)], 2, 10, 11, 4),  # terminal distance is not COE
    ([(0, 8), (4, 10)], 2, 10, 11, 8),  # overlapping members counted once
    ([(0, 4)], 5, 6, 7, 0),    # nonempty necessary set, legal zero
])
def test_literal_relations_do_not_identify_host_wait(intervals, copy, sync_return, host, expected):
    assert max(hi for _, hi in intervals) <= sync_return <= host
    coe = independent_overlap(intervals, copy, sync_return)
    before = independent_overlap(intervals, 0, copy)
    work = independent_overlap(intervals, 0, sync_return)
    assert coe == expected
    assert work == before + coe
    assert 0 <= coe <= min(work, sync_return - copy) <= host


def test_fixed_trajectory_arrival_identity_and_second_token_history_clipping():
    intervals = [(0, 4), (8, 10)]
    early = independent_overlap(intervals, 2, 10)
    late = independent_overlap(intervals, 9, 10)
    assert early - late == independent_overlap(intervals, 2, 9) == 3
    # Historical work stays necessary, but is not additional Decode work.
    assert independent_overlap(intervals, 0, 10) == 6
    assert independent_overlap(intervals, 8, 10) == 2
    assert independent_overlap(intervals, 8, 9) + independent_overlap(intervals, 9, 10) == 2


class PreparedBoundaryPrototype(Gate8BoundaryRecorder):
    """Test-only static payload/label hoist; no CUDA and no runtime installation."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sealed_identity = deepcopy(self.identity)
        self._sealed_ids = tuple(self.boundary_ids)
        self._prepared = []
        for ordinal, bid in enumerate(self.boundary_ids):
            index = None if ordinal == 0 else ordinal - 1
            payload = dict(schema_version='exposedpath-boundary-payload/0.1.0', kind='boundary',
                identity=deepcopy(self.identity), boundary_id=bid,
                boundary_kind='request_start' if ordinal == 0 else 'token_ready',
                token_index=index,
                completion_mechanism='predrained_inputs_resident' if ordinal == 0 else 'device_to_host_token_ids',
                marker_role='non_sync_marker')
            validate_shape('boundary_payload', payload)
            self._prepared.append((payload, BOUNDARY_PREFIX + json.dumps(payload, sort_keys=True, separators=(',', ':'))))

    def observe(self, host_observed_ns, token_index=None):
        if self.identity != self._sealed_identity or tuple(self.boundary_ids) != self._sealed_ids:
            raise ValueError('BOUNDARY_CACHE_IDENTITY_CONFLICT')
        ordinal = 0 if token_index is None else token_index + 1
        if ordinal != len(self.records) or ordinal >= len(self.boundary_ids):
            raise ValueError('BOUNDARY_ORDER_INVALID: producer sequence')
        payload, label = self._prepared[ordinal]
        before = self.clock_ns()
        if self.marker_sink is not None:
            self.marker_sink(label)
        after = self.clock_ns()
        if not host_observed_ns <= before <= after:
            raise ValueError('BOUNDARY_ORDER_INVALID: host marker diagnostics')
        self.records.append(dict(payload=payload, host_observed_ns=host_observed_ns,
            host_before_marker_ns=before, host_after_marker_ns=after, host_clock_id='PYTHON_PERF_COUNTER_NS'))


def identity(role='Engineering'):
    return dict(experiment_id='cpu-probe', wmpc_id='P-reference', run_id='run-a',
        run_role=role.upper(), data_role=role, pass_id='pass1', attempt_id='once',
        request_id='request-0', repeat_id='0')


def record(cls, pass_id='pass1', role='Engineering'):
    labels = []
    ticks = iter((20, 21, 40, 41, 60, 61))
    run_identity = identity(role)
    run_identity['pass_id'] = pass_id
    obj = cls(run_identity, ['request', 'token0', 'token1'], marker_sink=labels.append if pass_id == 'pass1' else None,
              clock_ns=lambda: next(ticks))
    for index, observed in ((None, 10), (0, 30), (1, 50)):
        obj.observe(observed, index)
    return obj, labels


@pytest.mark.parametrize('pass_id', ['pass0', 'pass1'])
@pytest.mark.parametrize('role', ['Engineering', 'Pilot'])
def test_real_recorder_and_cpu_prototype_have_identical_labels_payloads_and_dynamic_order(pass_id, role):
    original, old_labels = record(Gate8BoundaryRecorder, pass_id, role)
    proposed, labels = record(PreparedBoundaryPrototype, pass_id, role)
    assert old_labels == labels
    assert original.records == proposed.records


def test_prototype_removes_only_onsite_static_preparation(monkeypatch):
    import exposedpath.gate8_boundary as source
    old_validate = source.validate_shape
    calls = []
    def checked(kind, value):
        calls.append(kind)
        return old_validate(kind, value)
    monkeypatch.setattr(source, 'validate_shape', checked)
    obj = Gate8BoundaryRecorder(identity(), ['r', 't0', 't1'], marker_sink=lambda _: None,
                                clock_ns=lambda: 100)
    calls.clear()
    obj.observe(90)
    assert calls == ['boundary_payload']
    obj = PreparedBoundaryPrototype(identity(), ['r', 't0', 't1'], marker_sink=lambda _: None,
                                    clock_ns=lambda: 100)
    # If the proposal still calls the actual validation/serialization path
    # inside observe, this fails instead of timing a mocked fast function.
    monkeypatch.setattr(source, 'validate_shape', lambda *_: pytest.fail('onsite static validation'))
    monkeypatch.setattr(json, 'dumps', lambda *_a, **_kw: pytest.fail('onsite label encoding'))
    obj.observe(90)
    assert obj.records[0]['host_observed_ns'] == 90


@pytest.mark.parametrize('damage,reason', [
    ('identity', 'BOUNDARY_CACHE_IDENTITY_CONFLICT'),
    ('ids', 'BOUNDARY_CACHE_IDENTITY_CONFLICT'),
    ('order', 'BOUNDARY_ORDER_INVALID'),
    ('time', 'BOUNDARY_ORDER_INVALID'),
])
def test_prototype_does_not_move_or_bypass_dynamic_identity_and_sequence(damage, reason):
    obj = PreparedBoundaryPrototype(identity(), ['r', 't0', 't1'], marker_sink=lambda _: None,
                                    clock_ns=lambda: 100)
    if damage == 'identity':
        obj.identity['run_id'] = 'wrong'
    if damage == 'ids':
        obj.boundary_ids[0] = 'wrong'
    with pytest.raises(ValueError, match=reason):
        obj.observe(101 if damage == 'time' else 90, 0 if damage == 'order' else None)


def test_existing_a_requires_domain_owner_and_submit_proof_not_raw_api_union():
    effects = (_activity('k', 30, 50, 'KERNEL', 1),)
    syncs = (_sync('s', 40, 60, 'VALID_NONEMPTY', ['k']),)
    root = _api('runtime', 10, 30, 'cudaLaunchKernel', 1)
    result = calculate_a_windows(_inputs(apis=(root,), activities=effects, syncs=syncs))[0]
    assert [result[k] for k in ('A_host_path_ns', 'A_cuda_api_ns', 'A_device_wait_ns',
                                'A_sync_residual_ns', 'A_unattributed_ns')] == [60, 20, 10, 10, 0]
    child = _api('driver-query', 15, 20, 'cuCtxGetCurrent', 2)
    result = calculate_a_windows(_inputs(apis=(root, child), activities=effects, syncs=syncs))[0]
    # The old A input contract does not know this driver's budget owner.
    assert result['A_unattributed_ns'] == 5
    assert result['primary_reason'] == 'CUDA_API_SEMANTICS_UNRESOLVED'
    zero = _api('memset-zero', 0, 5, 'cudaMemsetAsync', 3)
    result = calculate_a_windows(_inputs(apis=(zero,), activities=(), syncs=()))[0]
    assert result['A_unattributed_ns'] == 5
    assert result['A_cuda_api_submit_ns'] == 0
    # No fabricated device effect is introduced to make the old proof pass.
