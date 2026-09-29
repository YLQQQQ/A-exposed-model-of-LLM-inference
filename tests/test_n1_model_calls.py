"""Independent CPU expectations for decode layer 16, never CUDA qualification."""
from contextlib import nullcontext
import importlib
import json
from types import SimpleNamespace

import pytest

from test_runner_token_ready import (_FakeInput, _FakeOutputs, _FakeToken,
                                    _patch_cpu_torch, _clock)


def module():
    # Assertion, rather than an import error, records the missing production entry.
    assert importlib.util.find_spec('exposedpath.n1_model') is not None
    return importlib.import_module('exposedpath.n1_model')


def fixture(variant='Vsync'):
    events = []
    identity = dict(experiment_id='exp', wmpc_id='w', run_id='r', run_role='ENGINEERING',
                    data_role='Engineering', pass_id='pass1', attempt_id='a',
                    request_id='request-0', repeat_id='0')
    class Stream:
        cuda_stream = 123
        device = SimpleNamespace(index=0)
        def synchronize(self): events.append('sync')
    stream = Stream()
    cuda = SimpleNamespace(current_stream=lambda _: stream, nvtx=SimpleNamespace(
        range_push=lambda label: events.append(('push', label)),
        range_pop=lambda: events.append('pop')))
    class Qwen2DecoderLayer:
        def __init__(self, index): self.index = index
        def forward(self, value):
            events.append(('layer', self.index))
            return value
    class Qwen2ForCausalLM:
        config = SimpleNamespace(model_type='qwen2', num_hidden_layers=28,
                                 _attn_implementation='sdpa', vocab_size=100)
        training = False
        def __init__(self):
            self.model = SimpleNamespace(layers=[Qwen2DecoderLayer(i) for i in range(28)])
            self.calls = 0
        def __call__(self, **kwargs):
            for layer in self.model.layers: layer.forward(None)
            self.calls += 1
            return _FakeOutputs(_FakeToken([10 + self.calls], events))
    model = Qwen2ForCausalLM()
    return model, cuda, stream, identity, events


@pytest.mark.parametrize('variant, interventions, syncs', [('V0', 0, 0), ('Vmarker', 1, 0), ('Vsync', 1, 1)])
def test_real_runner_decode_only_same_tokens_and_completion(monkeypatch, variant, interventions, syncs):
    from exposedpath import runner
    _patch_cpu_torch(monkeypatch)
    model, cuda, stream, identity, events = fixture()
    proxy = module().ModelCalls(model, cuda, stream, identity, variant, generation='stream-0')
    result = runner.run_one_invocation(proxy, _FakeInput(), object(), 2, 'cpu', '', '', '', '',
        token_ready_identity_base=identity, clock_ns=_clock(100, 120, 150))
    record = proxy.finish(result)
    assert record['status'] == 'COMPLETE_PENDING_TRACE_OWNERSHIP'
    assert record['observed_tokens'] == [[11], [12]]
    assert record['variant'] == variant
    assert len(record['interventions']) == interventions
    assert events.count('sync') == syncs
    assert [c['phase'] for c in record['model_calls']] == ['prefill', 'decode']
    assert result['inference_start_ns'] == 100 and result['inference_end_ns'] == 150
    assert [b.completed_ns for b in result['token_ready_boundaries']] == [120, 150]
    assert 'forward' not in model.model.layers[15].__dict__  # Restore the original descriptor.
    if interventions:
        op = record['interventions'][0]
        assert op['layer_index'] == 15 and op['token_index'] == 1
        assert op['synchronize_called'] is (variant == 'Vsync')
        assert op['before_native_handle'] == op['after_native_handle'] == 123
        if syncs:
            i = events.index('sync')
            assert max(j for j, e in enumerate(events[:i]) if e == ('layer', 15)) > events.index(('layer', 27))
            assert events[i:].index(('layer', 16)) > 0


@pytest.mark.parametrize('damage', ['skip', 'twice', 'stream', 'backend', 'variant'])
def test_no_success_for_missing_call_duplicate_stream_or_support_conflict(monkeypatch, damage):
    from exposedpath import runner
    _patch_cpu_torch(monkeypatch)
    model, cuda, stream, identity, events = fixture()
    if damage == 'backend': model.config = SimpleNamespace(model_type='qwen2', num_hidden_layers=28, _attn_implementation='eager')
    if damage == 'skip': model.model.layers[15] = SimpleNamespace(forward=lambda x: x)
    if damage == 'twice':
        # Another layer invokes the intervention layer a second time.
        model.model.layers[16].forward = lambda x: model.model.layers[15].forward(x)
    if damage == 'stream': cuda.current_stream = lambda _: SimpleNamespace(cuda_stream=456, device=stream.device)
    with pytest.raises(ValueError, match='N1_MODEL|STREAM_BRIDGE'):
        proxy = module().ModelCalls(model, cuda, stream, identity,
                                   'V8' if damage == 'variant' else 'Vsync', generation='s0')
        runner.run_one_invocation(proxy, _FakeInput(), object(), 2, 'cpu', '', '', '', '',
            token_ready_identity_base=identity, clock_ns=_clock(100, 120, 150))
    assert 'forward' not in model.model.layers[15].__dict__ or damage == 'skip'


def test_model_exception_restores_layer_and_retains_original_failure():
    model, cuda, stream, identity, events = fixture()
    layer = model.model.layers[15]
    def broken(value): raise RuntimeError('original layer failure')
    layer.forward = broken
    proxy = module().ModelCalls(model, cuda, stream, identity, 'Vsync', generation='s0')
    # Prefill fails before any intervention; no fake success or sync.
    with pytest.raises(RuntimeError, match='original layer failure'):
        proxy(input_ids=_FakeInput(), attention_mask=object(), use_cache=True)
    assert layer.forward is broken and events.count('sync') == 0
    assert proxy.record['model_calls'][0]['status'] == 'FAILED'


def test_decode_exception_restores_instance_forward_and_no_success():
    model, cuda, stream, identity, events = fixture()
    proxy = module().ModelCalls(model, cuda, stream, identity, 'Vsync', generation='s0')
    proxy(input_ids=_FakeInput(), attention_mask=object(), use_cache=True)
    layer = model.model.layers[15]
    def broken(value): raise RuntimeError('decode original')
    layer.forward = broken
    with pytest.raises(RuntimeError, match='decode original'):
        proxy(input_ids=_FakeInput(), past_key_values=object(), use_cache=True)
    assert layer.forward is broken
    assert proxy.record['model_calls'][-1]['status'] == 'FAILED'


def test_new_request_requires_fresh_adapter_and_valid_identity():
    model, cuda, stream, identity, events = fixture()
    identity['pass_id'] = 'not-a-pass'
    with pytest.raises(ValueError, match='IDENTITY_CONFLICT'):
        module().ModelCalls(model, cuda, stream, identity, 'Vsync', generation='s0')


def test_marker_and_sync_emit_same_range_structure_only_sync_call_differs(monkeypatch):
    from exposedpath import runner
    _patch_cpu_torch(monkeypatch)
    structures = []
    for variant in ('Vmarker', 'Vsync'):
        model, cuda, stream, identity, events = fixture()
        proxy = module().ModelCalls(model, cuda, stream, identity, variant, generation='s0')
        result = runner.run_one_invocation(proxy, _FakeInput(), object(), 2, 'cpu', '', '', '', '',
            token_ready_identity_base=identity, clock_ns=_clock(100, 120, 150))
        proxy.finish(result)
        structures.append([e[1].split(':', 1)[0] if isinstance(e, tuple) and e[0] == 'push'
                           else e for e in events if e != 'sync'])
    assert structures[0] == structures[1]


def test_more_than_first_two_token_entry_rejected():
    model, cuda, stream, identity, events = fixture()
    proxy = module().ModelCalls(model, cuda, stream, identity, 'Vsync', generation='s0')
    proxy(input_ids=_FakeInput(), attention_mask=object(), use_cache=True)
    proxy(input_ids=_FakeInput(), past_key_values=object(), use_cache=True)
    with pytest.raises(ValueError, match='N1_MODEL_OUTPUT_SCOPE'):
        proxy(input_ids=_FakeInput(), past_key_values=object(), use_cache=True)


def test_real_missing_layer_execution_rejected_and_restored():
    model, cuda, stream, identity, events = fixture()
    proxy = module().ModelCalls(model, cuda, stream, identity, 'Vsync', generation='s0')
    proxy(input_ids=_FakeInput(), attention_mask=object(), use_cache=True)
    original = model.model.layers
    # Preserve validated objects, but the forward path stops visiting layer 16.
    model.model.layers = original[:15] + original[16:]
    with pytest.raises(ValueError, match='N1_MODEL_MISSING_LAYER_CALL'):
        proxy(input_ids=_FakeInput(), past_key_values=object(), use_cache=True)
    assert 'forward' not in original[15].__dict__


def test_eos_cannot_be_presented_as_completed_intervention(monkeypatch):
    from exposedpath import runner
    _patch_cpu_torch(monkeypatch)
    model, cuda, stream, identity, events = fixture()
    proxy = module().ModelCalls(model, cuda, stream, identity, 'Vsync', generation='s0')
    result = runner.run_one_invocation(proxy, _FakeInput(), object(), 2, 'cpu', '', '', '', '',
        eos_token_id=11, token_ready_identity_base=identity, clock_ns=_clock(100, 120))
    with pytest.raises(ValueError, match='N1_MODEL_INCOMPLETE_OUTPUT'): proxy.finish(result)
    assert events.count('sync') == 0
