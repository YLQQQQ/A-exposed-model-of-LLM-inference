"""Opt-in resident Qwen decode intervention; not a model/trace qualification.

The unmodified runner owns drain, token reads, EOS and completion windows.
This adapter only brackets calls and installs the approved layer-16 callsite
for decode. It does not infer physical CUDA ownership from a Python context.
"""
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import time

from .gate8_identity import validate_shape
from .gate9_stream_bridge import StreamBridge
from .nvtx import make_n1_intervention_identity, make_structured_nvtx_label

VERSION = 'exposedpath-n1-model-calls/0.1.0'
PREFIX = 'EXPOSEDPATH_N1_MODEL_V1:'
CALLSITE = 'qwen2.decode.layer_16.after_forward'
VARIANTS = ('V0', 'Vmarker', 'Vsync')


def execution_declaration():
    return dict(version='N1-VERIFIED-MODEL/0.1', warmup_stream='SEPARATE_HELD_EXPLICIT',
                measured_stream='FRESH_HELD_EXPLICIT_AFTER_WARMUP',
                anchor='CURRENT_STREAM_SYNC_BEFORE_FINAL_DRAIN', input_tokens=32, output_tokens=2,
                batch_size=1, warmup_count=1, repeat_count=1)


def require(ok, reason):
    if not ok:
        raise ValueError('N1_MODEL_' + reason)


def declaration(variant):
    require(variant in VARIANTS, 'VARIANT')
    return dict(schema_version=VERSION, variant=variant, protocol_variant='V16' if variant == 'Vsync' else variant,
                callsite_id=CALLSITE, phase='decode', layer_index=15,
                frequency='ONCE_PER_DECODE_FORWARD', stream_policy='HELD_EXPLICIT_NONBLOCKING',
                declaration_role='PRE_EXECUTION', qualification='NOT_ASSESSED')


def validate_manifest(manifest):
    """Explicit N1 opt-in; the shared verified entry still checks all identities."""
    from exposedpath_v141.gate9_domain import declaration as domain, N1
    policy = manifest.get('n1_model')
    require(isinstance(policy, dict) and policy == declaration(policy.get('variant')), 'DECLARATION')
    expected = dict(sync_origin='n1_intervention', callsite_id=CALLSITE,
                    intervention_variant_id=policy['variant'])
    require(manifest.get('study_mode') == 'N1_INTERVENTION' and manifest.get('n1_intervention') == expected
            and manifest.get('domain_qualification') == domain(N1), 'DOMAIN_IDENTITY')
    require('engineering_pair' not in manifest and 'gate10_workload' not in manifest
            and manifest.get('attention_backend') == 'sdpa'
            and 'target_python' in manifest and 'isolated_preflight_version' in manifest, 'VERIFIED_ENTRY_REQUIRED')
    require(manifest.get('n1_model_execution')==execution_declaration(), 'EXECUTION_DECLARATION')
    return policy


def validate_prepared(manifest, prepared, root):
    """Before profile: reuse N1 declarations and the verified entry's fixed inputs.

    This does not claim the model has loaded or performed an intervention.
    Target runtime/device/model-content observations are still checked in entry.
    """
    from .gate8_engineering_contract import validate_declaration
    from .workload import load_prompt_tokens
    validate_manifest(manifest)
    validate_declaration(manifest)
    expected=dict(fixed_input_tokens=32,fixed_output_tokens=2,batch_size=1,
        warmup_count=1,repeat_count=1,execution_mode='eager',run_role='ENGINEERING',
        data_role='Engineering',dtype_and_quantization='fp16',sampling_config={'do_sample':False})
    require(all(type(manifest.get(k)) is type(v) and manifest[k]==v for k,v in expected.items()),
            'FIXED_WORKLOAD_CONFLICT')
    prompt=Path(prepared)/'prompt.json'
    for path,key in ((prompt,'prompt_tokens_sha256'),(Path(root)/'exposedpath/runner.py','runner_source_sha256')):
        require(hashlib.sha256(path.read_bytes()).hexdigest()==manifest.get(key),'INPUT_HASH_CONFLICT')
    require(load_prompt_tokens(prompt)['fixed_input_tokens']==32,'INPUT_LENGTH')


class Execution:
    """Attach to the existing loader/runner, never a replacement entry.

    Hold the warmup stream alive; a different dedicated measured stream is
    created after warmup's successful drain. All groups share this policy.
    The out-of-window anchor binds actual native handle to trace stream IDs.
    """
    def __init__(self, policy, cuda):
        self.policy, self.cuda = deepcopy(policy), cuda
        self.streams, self.requests = [], []

    def run(self, model, identity, operation, *, warmup=False):
        stream = self.cuda.Stream(device=0)
        require(int(stream.cuda_stream) > 0 and all(s.cuda_stream != stream.cuda_stream for s in self.streams),
                'STREAM_GENERATION_REUSE')
        self.streams.append(stream)
        generation = identity['run_id'] + ':' + identity['request_id'] + ':held'
        with self.cuda.stream(stream):
            proxy = ModelCalls(model, self.cuda, stream, identity, self.policy['variant'], generation=generation)
            self.requests.append(proxy.record)
            proxy.record.update(request_role='warmup' if warmup else 'measured', anchor=None)
            life = dict(schema_version=VERSION, operation='held_lifetime', identity=identity,
                        generation=generation, native_handle=int(stream.cuda_stream), logical_device=0)
            proxy.record['lifetime_payload'] = life
            proxy._push(life)
            try:
                if not warmup:
                    anchor = StreamBridge(self.cuda, stream, identity, generation)
                    with anchor:
                        anchor.synchronize('wait')
                    proxy.record['anchor'] = deepcopy(anchor.records[0])
                result = operation(proxy)
                if warmup:
                    require(len(proxy.record['model_calls']) == 2
                            and all(r['status'] == 'COMPLETE' for r in proxy.record['model_calls'])
                            and len(proxy.record['interventions']) == (0 if self.policy['variant']=='V0' else 1), 'WARMUP')
                    proxy.record['status'] = 'WARMUP_CALLS_COMPLETE_PENDING_TRACE_OWNERSHIP'
                else:
                    require(result['actual_input_tokens']==32 and result['actual_output_tokens']==2,
                            'ACTUAL_WORKLOAD')
                    proxy.finish(result)
                return result
            except BaseException:
                proxy.record['status'] = 'FAILED'
                raise
            finally:
                self.cuda.nvtx.range_pop()


class ModelCalls:
    """One invocation, one thread, sequential prefill then decode calls.

    Vmarker/Vsync use the same scoped layer-forward wrapper, not a persistent
    framework hook. V0 never wraps a layer. The original return object, args,
    kwargs, cache and exception are preserved. No extra token read is added.
    """
    def __init__(self, model, cuda, stream, identity, variant, *, generation):
        validate_shape('identity', identity)
        policy = declaration(variant)
        require(identity['run_role'] == 'ENGINEERING' and identity['data_role'] == 'Engineering', 'ROLE')
        require(identity['pass_id'] == 'pass1', 'PROFILE_ONLY_ENTRY')
        config = model.config
        require(type(model).__name__ == 'Qwen2ForCausalLM' and config.model_type == 'qwen2'
                and config.num_hidden_layers == 28 and config._attn_implementation == 'sdpa'
                and model.training is False, 'MODEL_CONFIGURATION')
        layers = model.model.layers
        require(len(layers) == 28 and all(type(layer).__name__ == 'Qwen2DecoderLayer' for layer in layers),
                'LAYER_CONFIGURATION')
        require(isinstance(generation, str) and bool(generation), 'GENERATION')
        self.model, self.cuda, self.identity, self.variant = model, cuda, deepcopy(identity), variant
        self.layer, self.generation = layers[15], generation
        self.bridge = StreamBridge(cuda, stream, identity, generation)
        self.bridge._current()  # Same actual-current/thread/device guard as the qualified bridge.
        self.record = dict(schema_version=VERSION, identity=deepcopy(identity), variant=variant,
            declaration=policy, generation=generation, native_handle=self.bridge.handle,
            logical_device=self.bridge.device, model_calls=[], interventions=[],
            status='OPEN', observed_tokens=[], physical_ownership='NOT_ASSESSED')

    def _push(self, payload):
        self.cuda.nvtx.range_push(PREFIX + json.dumps(payload, sort_keys=True, separators=(',', ':')))

    def _intervene(self, index, count):
        count[0] += 1
        require(count[0] == 1, 'DUPLICATE_LAYER_CALL')
        self.bridge._current()
        payload = dict(schema_version=VERSION, identity=self.identity, generation=self.generation,
                       variant=self.variant, operation='intervention', token_index=index,
                       layer_index=15, callsite_id=CALLSITE, marker_role='non_sync_marker')
        record = dict(payload=payload, token_index=index, layer_index=15, before_native_handle=self.bridge.handle,
                      after_native_handle=None, synchronize_called=False, status='FAILED', bridge=None)
        self.record['interventions'].append(record)
        self._push(payload)
        try:
            # Both controls have identical ranges/callsite branches. A marker is
            # not a CUDA operation: only actual APIs can produce S/B records.
            label = make_n1_intervention_identity(self.identity, phase='decode', callsite_id=CALLSITE,
                sync_ordinal=index-1, intervention_variant_id=self.variant, intervention_ordinal=index-1)
            self.cuda.nvtx.range_push(make_structured_nvtx_label(label))
            try:
                with self.bridge:
                    def controlled_call(_handle):
                        if self.variant == 'Vsync':
                            record['synchronize_called'] = True
                            return self.bridge._current().synchronize()
                        return None
                    self.bridge.observe('internal_wait', controlled_call)
            finally:
                record['bridge'] = deepcopy(self.bridge.records)
                self.cuda.nvtx.range_pop()
            # Each intervention gets a distinct bridge lifetime, same held resource.
            self.bridge = StreamBridge(self.cuda, self.bridge.stream, self.identity, self.generation)
            record['after_native_handle'] = int(self.bridge._current().cuda_stream)
            record['status'] = 'COMPLETE'
        finally:
            self.cuda.nvtx.range_pop()

    def __call__(self, **kwargs):
        require(self.record['status'] == 'OPEN', 'INVOCATION_CLOSED')
        calls = self.record['model_calls']
        require(not calls or calls[-1]['status'] == 'COMPLETE', 'PREVIOUS_CALL_FAILED')
        index = len(calls)
        require(index < 2, 'OUTPUT_SCOPE')
        expected = {'input_ids', 'use_cache', 'attention_mask' if index == 0 else 'past_key_values'}
        require(set(kwargs) == expected and kwargs['use_cache'] is True, 'FORWARD_ORDER_OR_ARGUMENTS')
        self.bridge._current()
        payload = dict(schema_version=VERSION, identity=self.identity, generation=self.generation,
                       variant=self.variant, operation='model_forward', token_index=index,
                       phase='prefill' if index == 0 else 'decode')
        record = dict(payload=payload, phase=payload['phase'], status='FAILED',
                      before_native_handle=self.bridge.handle, after_native_handle=None, error=None)
        calls.append(record)
        self._push(payload)
        original = self.layer.forward
        had_override = 'forward' in vars(self.layer)
        count = [0]
        wrapped = index > 0 and self.variant != 'V0'
        def after_layer(*args, **kw):
            value = original(*args, **kw)
            self._intervene(index, count)
            return value
        try:
            if wrapped:
                self.layer.forward = after_layer
            value = self.model(**kwargs)
            require(not wrapped or count[0] == 1, 'MISSING_LAYER_CALL')
            record['after_native_handle'] = int(self.bridge._current().cuda_stream)
            record['status'] = 'COMPLETE'
            return value
        except BaseException as exc:
            record['error'] = type(exc).__name__ + ':' + str(exc)
            raise
        finally:
            if wrapped:
                if had_override:
                    self.layer.forward = original
                else:
                    del self.layer.forward
            self.cuda.nvtx.range_pop()

    def finish(self, result):
        require(self.record['status'] == 'OPEN', 'INVOCATION_CLOSED')
        boundaries = result['token_ready_boundaries']
        require(not result['early_eos'] and result['actual_output_tokens'] == result['output_len_expected']
                and len(boundaries) == len(self.record['model_calls']) == result['actual_output_tokens']
                and result['batch_size'] == 1 and len(boundaries) >= 2
                and all(r['status'] == 'COMPLETE' for r in self.record['model_calls']), 'INCOMPLETE_OUTPUT')
        expected = 0 if self.variant == 'V0' else len(boundaries)-1
        require(len(self.record['interventions']) == expected
                and all(r['status'] == 'COMPLETE' for r in self.record['interventions']), 'INTERVENTION_COUNT')
        self.bridge._current()
        self.record.update(status='COMPLETE_PENDING_TRACE_OWNERSHIP',
                           actual_input_tokens=result['actual_input_tokens'],
                           observed_tokens=[list(b.host_token_ids) for b in boundaries])
        return deepcopy(self.record)


def run_resident_to_files(*, model, manifest_path, prompt_path, output_dir, eos_token_id, clock_ns=time.perf_counter_ns):
    """Local opt-in building block, deliberately not a deployment/model loader.

    Caller must bind model weights/platform/code via the existing preflight.
    This sub-receipt proves neither that prerequisite nor physical ownership.
    A single held stream covers variant-identical warmup and measured work;
    its entire prefix is retained for later physical S/B (never truncated).
    """
    from . import runner
    from .gate8_boundary import Gate8BoundaryRecorder
    from .gate8_drain import DrainRecorder, DRAIN_VERSION
    cuda = runner.torch.cuda
    manifest_bytes = Path(manifest_path).read_bytes()
    prompt_bytes = Path(prompt_path).read_bytes()
    plan, prompt = json.loads(manifest_bytes), json.loads(prompt_bytes)
    fields = {'schema_version', 'identity', 'n1', 'prompt_sha256', 'output_tokens', 'batch_size',
              'warmup_count', 'repeat_count', 'execution_mode', 'backend', 'logical_device', 'precondition', 'eos_token_id'}
    require(set(plan) == fields and plan['schema_version'] == 'exposedpath-n1-resident-plan/0.1.0'
            and plan['precondition'] == 'CALLER_VERIFIED_RESIDENT_MODEL_INPUT_AND_PLATFORM', 'PLAN')
    require(plan['n1'] == declaration(plan['n1'].get('variant')), 'DECLARATION')
    # Actual tokenizer value is supplied by the verified model loader. Do not
    # substitute config lists or silently suppress EOS detection.
    require(type(eos_token_id) is int and eos_token_id >= 0
            and type(plan['eos_token_id']) is int and plan['eos_token_id'] == eos_token_id, 'EOS_IDENTITY')
    require(plan['execution_mode'] == 'eager' and plan['backend'] == 'sdpa'
            and all(type(plan[k]) is int and plan[k] == v for k, v in
                    dict(output_tokens=2, batch_size=1, warmup_count=1, repeat_count=1, logical_device=0).items()),
            'CONFIGURATION')
    validate_shape('identity', plan['identity'])
    require(plan['identity']['pass_id'] == 'pass1', 'PROFILE_ONLY_ENTRY')
    require(hashlib.sha256(prompt_bytes).hexdigest() == plan['prompt_sha256'], 'PROMPT_HASH')
    require(set(prompt) == {'input_ids', 'attention_mask'} and len(prompt['input_ids']) == 1
            and len(prompt['attention_mask']) == 1 and len(prompt['input_ids'][0]) > 0
            and all(type(x) is int and 0 <= x < model.config.vocab_size for x in prompt['input_ids'][0])
            and prompt['attention_mask'][0] == [1] * len(prompt['input_ids'][0])
            and all(type(x) is int for x in prompt['attention_mask'][0]), 'PROMPT')
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=False)
    files = {}
    def write_bytes(name, data):
        # New directory, exclusive files: partial output never overwrites evidence.
        with (output/name).open('xb') as f:
            f.write(data)
        files[name] = dict(path=name, sha256=hashlib.sha256(data).hexdigest(), size_bytes=len(data))
    def write(name, value):
        write_bytes(name, json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2).encode('utf-8'))
    write_bytes('manifest.json', manifest_bytes)
    write_bytes('prompt.json', prompt_bytes)
    sources = ('exposedpath/n1_model.py', 'exposedpath/runner.py', 'exposedpath/gate9_stream_bridge.py')
    root = Path(__file__).resolve().parents[1]
    receipt = dict(schema_version='exposedpath-n1-resident-receipt/0.1.0', status='FAILED', error=None,
                   manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(), prompt_sha256=plan['prompt_sha256'],
                   identity=deepcopy(plan['identity']),
                   source_sha256={name: hashlib.sha256((root/name).read_bytes()).hexdigest() for name in sources},
                   observed_model=dict(class_name=type(model).__name__, backend=model.config._attn_implementation,
                       model_type=model.config.model_type, num_hidden_layers=model.config.num_hidden_layers,
                       training=model.training),
                   n1_model_feasibility='NOT_RUN', physical_ownership='NOT_ASSESSED', files=files)
    warmup = measured = boundary = drain = None
    original_error = None
    try:
        require(cuda.current_device() == 0, 'ACTUAL_DEVICE')
        device = 'cuda:0'
        ids = runner.torch.tensor(prompt['input_ids'], dtype=runner.torch.long, device=device)
        mask = runner.torch.tensor(prompt['attention_mask'], dtype=runner.torch.long, device=device)
        stream = cuda.Stream(device=0)
        generation = plan['identity']['run_id'] + ':n1-held-stream'
        with cuda.stream(stream):
            # Resource kept alive through warmup, final drain, request and cleanup.
            warm_identity = {**plan['identity'], 'request_id': plan['identity']['request_id'] + ':warmup'}
            warmup = ModelCalls(model, cuda, stream, warm_identity, plan['n1']['variant'], generation=generation)
            lifetime = dict(schema_version=VERSION, operation='held_lifetime', identity=plan['identity'],
                            generation=generation, native_handle=int(stream.cuda_stream), logical_device=0)
            warmup._push(lifetime)
            try:
                runner.run_warmup(warmup, ids, mask, 2, 1)
                require(len(warmup.record['model_calls']) == 2
                        and all(r['status'] == 'COMPLETE' for r in warmup.record['model_calls']), 'WARMUP')
                warmup.record['status'] = 'WARMUP_CALLS_COMPLETE_PENDING_TRACE_OWNERSHIP'
                measured = ModelCalls(model, cuda, stream, plan['identity'], plan['n1']['variant'], generation=generation)
                prefix = hashlib.sha256(manifest_bytes).hexdigest()
                boundary = Gate8BoundaryRecorder(plan['identity'], [prefix + ':' + str(i) for i in range(3)],
                    marker_sink=cuda.nvtx.mark, clock_ns=clock_ns)
                drain = DrainRecorder(plan['identity'], prefix + ':drain', 0, clock_ns=clock_ns,
                    push=cuda.nvtx.range_push, pop=cuda.nvtx.range_pop)
                result = runner.run_one_invocation(measured, ids, mask, 2, device, 'N1_MODEL_REQUEST', '', '', '',
                    token_ready_identity_base=plan['identity'], clock_ns=clock_ns,
                    gate8_recorder=boundary, drain_recorder=drain,
                    eos_token_id=eos_token_id)
                measured.finish(result)
                require(result['actual_input_tokens'] == len(prompt['input_ids'][0]), 'ACTUAL_INPUT_LENGTH')
                receipt['status'] = 'COMPLETE_PENDING_TRACE_OWNERSHIP'
            finally:
                cuda.nvtx.range_pop()
    except BaseException as exc:
        original_error = exc
        receipt['error'] = type(exc).__name__ + ':' + str(exc)
        raise
    finally:
        try:
            write('model_calls.json', dict(schema_version=VERSION,
                warmup=warmup.record if warmup else None, measured=measured.record if measured else None))
            write('host_boundaries.json', boundary.records if boundary else [])
            write('drain_ledger.json', dict(schema_version=DRAIN_VERSION,
                drains=[drain.record] if drain and drain.record else []))
            write('producer_receipt.json', receipt)
        except BaseException as io_error:
            if original_error is None:
                raise
            original_error.add_note('N1 receipt persistence also failed: ' + type(io_error).__name__)
    return output/'producer_receipt.json'
