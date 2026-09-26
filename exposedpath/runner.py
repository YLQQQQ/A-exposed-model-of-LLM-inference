"""
Runner: Pass 0 (no profiler) and Pass 1 (nsys-wrapped) inference execution.

Key constraints:
  - Every generated Token crosses the same Host-readable completion boundary
  - Natural Token-ready reads are distinct from N1 intervention identity
  - No tokenizer inside the timing path
  - Batch samples must be distinct (no cloning)
  - fixed_output_tokens must be generated exactly
  - Early EOS / wrong output count → exclusion
  - Attempts/exclusions carry machine-readable identity for Pass 0 / Pass 1 parity
"""

import sys
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from exposedpath.manifest import load_manifest
from exposedpath.nvtx import (
    make_invocation_label,
    make_natural_token_ready_identity,
    make_phase_label,
    make_structured_nvtx_label,
)
from exposedpath.cross_pass_validator import load_attempt_accounting
from exposedpath.results import (
    ATTEMPT_PLAN_VERSION,
    EXCLUSION_REASON_CUDA_ERROR,
    EXCLUSION_REASON_EARLY_EOS,
    EXCLUSION_REASON_OOM,
    EXCLUSION_REASON_OUTPUT_TOKEN_COUNT_MISMATCH,
    EXCLUSION_REASON_RUNTIME_ERROR,
    PHASE_BOUNDARY_POLICY,
    PHASE_BOUNDARY_POLICY_VERSION,
    RETRY_POLICY,
    TOKEN_READY_MECHANISM,
    TOKEN_READY_ORIGIN_NATURAL,
    record_exclusion,
    record_success,
)
from exposedpath.validation import validate_prompt_tokens_sha256_match
from exposedpath.workload import get_batch_inputs, load_prompt_tokens


SYNCHRONIZE_POLICY = (
    "request_start_drain_outside_window, natural_token_ready_host_read_per_token, "
    "no_final_cleanup_inside_window"
)


@dataclass(frozen=True)
class TokenReadyBoundary:
    token_index: int
    host_token_ids: tuple[int, ...]
    completed_ns: int
    sync_origin: str
    token_ready_mechanism: str


def token_ready_boundaries_to_records(
    boundaries: Sequence[TokenReadyBoundary],
) -> list[dict]:
    """Return JSON-ready Token-ready completion evidence."""
    return [
        {
            "token_index": boundary.token_index,
            "host_token_ids": list(boundary.host_token_ids),
            "completed_ns": boundary.completed_ns,
            "sync_origin": boundary.sync_origin,
            "token_ready_mechanism": boundary.token_ready_mechanism,
        }
        for boundary in boundaries
    ]


def observe_token_ready_boundary(
    token_tensor,
    *,
    token_index: int,
    identity_base: Mapping,
    phase: str,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
    emit_nvtx: bool,
    gate8_recorder=None,
) -> TokenReadyBoundary:
    """Block until token IDs are Host-readable, then timestamp completion."""
    identity = make_natural_token_ready_identity(
        identity_base,
        phase=phase,
        token_index=token_index,
        callsite_id=f"{phase}.token_ready",
        sync_ordinal=token_index,
        token_ready_mechanism=TOKEN_READY_MECHANISM,
    )
    if emit_nvtx:
        torch.cuda.nvtx.range_push(make_structured_nvtx_label(identity))
    try:
        values = token_tensor.detach().cpu().reshape(-1).tolist()
        host_token_ids = tuple(int(value) for value in values)
        if not host_token_ids:
            raise RuntimeError(f"Token-ready boundary {token_index} produced no Host-readable IDs")
        completed_ns = clock_ns()
        if gate8_recorder is not None:
            gate8_recorder.observe(completed_ns, token_index)
    finally:
        if emit_nvtx:
            torch.cuda.nvtx.range_pop()
    return TokenReadyBoundary(
        token_index=token_index,
        host_token_ids=host_token_ids,
        completed_ns=completed_ns,
        sync_origin="natural_token_ready",
        token_ready_mechanism=TOKEN_READY_MECHANISM,
    )


def validate_token_ready_boundaries(
    request_start_ns: int,
    boundaries: Sequence[TokenReadyBoundary],
    *,
    expected_count: int,
) -> None:
    """Validate complete, indexed, monotonic Token-ready evidence."""
    if len(boundaries) != expected_count:
        raise RuntimeError(
            f"expected {expected_count} token-ready boundaries, got {len(boundaries)}"
        )
    previous_ns = request_start_ns
    for expected_index, boundary in enumerate(boundaries):
        if boundary.token_index != expected_index:
            raise RuntimeError(
                f"missing token-ready boundary at index {expected_index}; "
                f"observed index {boundary.token_index}"
            )
        if boundary.completed_ns < previous_ns:
            raise RuntimeError(
                f"token-ready boundary {boundary.token_index} is not monotonic: "
                f"{boundary.completed_ns} < {previous_ns}"
            )
        if boundary.sync_origin != "natural_token_ready":
            raise RuntimeError(
                f"token-ready boundary {boundary.token_index} has invalid sync_origin "
                f"{boundary.sync_origin!r}"
            )
        previous_ns = boundary.completed_ns


def load_model(model_path: str, gpu: int = 0):
    """Load model (FP16) + tokenizer on specified GPU.

    Handles CUDA_VISIBLE_DEVICES remapping: if the user requested physical GPU *gpu*
    but CUDA_VISIBLE_DEVICES remaps it to a different logical index, we detect and
    log both. The *gpu* parameter always means the physical GPU index.
    """
    import os as _os
    physical_gpu_id = gpu
    visible = _os.environ.get("CUDA_VISIBLE_DEVICES", None)
    if visible is not None and visible.strip():
        ids = [x.strip() for x in visible.split(",")]
        if str(gpu) in ids:
            logical_gpu = ids.index(str(gpu))
            device = f"cuda:{logical_gpu}"
        else:
            # GPU not in visible list — fall back to cuda:0 with warning
            device = "cuda:0"
    else:
        device = f"cuda:{gpu}"

    logical_idx = int(device.split(":")[1]) if device.startswith("cuda:") else 0
    gpu_name = torch.cuda.get_device_name(logical_idx) if torch.cuda.is_available() else "unknown"

    print(f"[runner] Loading model from: {model_path}  -> {device}")
    print(f"[runner]   physical_gpu_id={physical_gpu_id}")
    print(f"[runner]   logical_device={device}")
    print(f"[runner]   gpu_name={gpu_name}")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.float16,
            device_map=device,
            trust_remote_code=True,
        )
    except Exception:
        print("[runner] trust_remote_code=True failed, retrying without...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.float16,
            device_map=device,
        )
    model.eval()
    vocab_size = model.config.vocab_size

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[runner] Model + tokenizer loaded. Vocab size: {vocab_size}")
    return model, tokenizer, vocab_size, device


def run_warmup(
    model,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    output_len: int,
    warmup_iters: int,
):
    """Warmup without NVTX, without results recording."""
    print(f"[runner] Running {warmup_iters} warmup iteration(s)...")
    batch_size, prompt_len = input_ids.shape
    for w in range(warmup_iters):
        print(f"[runner]   Warmup {w + 1}/{warmup_iters}")
        torch.cuda.synchronize()
        with torch.inference_mode():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=True)
        next_token = outputs.logits[:, -1, :].argmax(dim=-1)
        past_key_values = outputs.past_key_values
        for _ in range(1, output_len):
            current_input = next_token.unsqueeze(1)
            with torch.inference_mode():
                outputs = model(input_ids=current_input, past_key_values=past_key_values, use_cache=True)
            next_token = outputs.logits[:, -1, :].argmax(dim=-1)
            past_key_values = outputs.past_key_values
        torch.cuda.synchronize()
    print("[runner] Warmup complete.")


def run_one_invocation(
    model,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    output_len: int,
    device: str,
    nvtx_invocation_label: str,
    nvtx_full_request_label: str,
    nvtx_prefill_label: str,
    nvtx_decode_label: str,
    eos_token_id: Optional[int] = None,
    token_ready_identity_base: Optional[Mapping] = None,
    clock_ns: Callable[[], int] = time.perf_counter_ns,
    gate8_recorder=None,
    drain_recorder=None,
) -> Dict:
    """Execute a single inference invocation with NVTX annotation.

    Each generated token crosses the same Host-readable completion boundary.
    Returns result dict for record_success.
    """
    batch_size, prompt_len = input_ids.shape

    if gate8_recorder is not None:
        if gate8_recorder.identity != token_ready_identity_base or len(gate8_recorder.boundary_ids) != output_len + 1:
            raise ValueError("IDENTITY_CONFLICT: Gate8 recorder/request plan")
    gate8_pass0 = gate8_recorder is not None and gate8_recorder.identity["pass_id"] == "pass0"
    range_push = (lambda _label: None) if gate8_pass0 else torch.cuda.nvtx.range_push
    range_pop = (lambda: None) if gate8_pass0 else torch.cuda.nvtx.range_pop

    # ---- Final drain before timing ----
    if drain_recorder is None:
        torch.cuda.synchronize()
    else:
        if torch.cuda.current_device() != drain_recorder.payload['logical_device']:
            raise ValueError('DRAIN_CURRENT_DEVICE_CONFLICT')
        drain_recorder.observe(torch.cuda.synchronize)

    # ==================== NVTX: invocation ====================
    range_push(nvtx_invocation_label)

    if token_ready_identity_base is None:
        raise RuntimeError("token_ready_identity_base is required")

    t_start_ns = clock_ns()
    if gate8_recorder is not None:
        gate8_recorder.observe(t_start_ns)

    # ==================== NVTX: full_request ====================
    range_push(nvtx_full_request_label)

    # ==================== PREFILL ====================
    range_push(nvtx_prefill_label)

    with torch.inference_mode():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=True)

    next_token = outputs.logits[:, -1, :].argmax(dim=-1)
    past_key_values = outputs.past_key_values

    token_ready_boundaries = [
        observe_token_ready_boundary(
            next_token,
            token_index=0,
            identity_base=token_ready_identity_base,
            phase="prefill",
            clock_ns=clock_ns,
            emit_nvtx=bool(nvtx_invocation_label),
            gate8_recorder=gate8_recorder,
        )
    ]
    t_first_token_ns = token_ready_boundaries[0].completed_ns

    range_pop()  # prefill

    # ==================== DECODE ====================
    range_push(nvtx_decode_label)

    actual_output_tokens = 1  # first token from prefill
    early_eos = (
        eos_token_id is not None
        and eos_token_id in token_ready_boundaries[0].host_token_ids
    )

    for step_i in range(1, output_len):
        if early_eos:
            break
        current_input = next_token.unsqueeze(1)
        with torch.inference_mode():
            outputs = model(input_ids=current_input, past_key_values=past_key_values, use_cache=True)
        next_token = outputs.logits[:, -1, :].argmax(dim=-1)
        past_key_values = outputs.past_key_values
        actual_output_tokens += 1

        boundary = observe_token_ready_boundary(
            next_token,
            token_index=step_i,
            identity_base=token_ready_identity_base,
            phase="decode",
            clock_ns=clock_ns,
            emit_nvtx=bool(nvtx_invocation_label),
            gate8_recorder=gate8_recorder,
        )
        token_ready_boundaries.append(boundary)

        # Check for early EOS
        if eos_token_id is not None and eos_token_id in boundary.host_token_ids:
            early_eos = True
            break

    t_end_ns = token_ready_boundaries[-1].completed_ns

    # Close measured ranges immediately after the final Token-ready marker.
    # Boundary validation and all other Host cleanup stay outside the ranges.
    range_pop()  # decode
    range_pop()  # full_request
    range_pop()  # invocation

    validate_token_ready_boundaries(
        t_start_ns, token_ready_boundaries, expected_count=actual_output_tokens,
    )

    # ---- Time invariants ----
    if t_end_ns <= t_start_ns:
        raise RuntimeError(
            f"Time invariant violation: end_ns ({t_end_ns}) <= start_ns ({t_start_ns})"
        )
    if t_first_token_ns < t_start_ns or t_first_token_ns > t_end_ns:
        raise RuntimeError(
            f"Time invariant violation: first_token_ns ({t_first_token_ns}) "
            f"not in [{t_start_ns}, {t_end_ns}]"
        )

    # ---- Metrics (ns → ms) ----
    prefill_ms = (t_first_token_ns - t_start_ns) / 1_000_000.0
    decode_ms = (t_end_ns - t_first_token_ns) / 1_000_000.0

    if prefill_ms < 0 or decode_ms < 0:
        raise RuntimeError(
            f"Time invariant violation: prefill_ms={prefill_ms:.3f}, decode_ms={decode_ms:.3f}"
        )

    return {
        "inference_start_ns": t_start_ns,
        "inference_end_ns": t_end_ns,
        "prefill_latency_ms": round(prefill_ms, 3),
        "decode_latency_ms": round(decode_ms, 3),
        "actual_input_tokens": prompt_len,
        "actual_output_tokens": actual_output_tokens,
        "batch_size": batch_size,
        "early_eos": early_eos,
        "output_len_expected": output_len,
        "token_ready_boundaries": token_ready_boundaries,
    }


def run_gate8_requests(*, model=None, input_ids=None, attention_mask=None, output_len, device,
                       pass_fields, request_plan, eos_token_id=None,
                       clock_ns=time.perf_counter_ns, record_drains=False,
                       record_stages=False, model_setup=None):
    """Explicit local Gate8 producer API over already-resident inputs.

    Not enabled by the legacy CLI/launcher. The caller supplies preflight-bound
    artifact identities; this function records actual per-request outcomes and
    does not fabricate Raw/device hashes that only exist after collection.
    """
    import hashlib
    import json
    import os
    from exposedpath.gate8_identity import make_gate8_pass_identity, validate_pass_identity
    from exposedpath.gate8_boundary import Gate8BoundaryRecorder

    if pass_fields.get("pid") != os.getpid():
        raise ValueError("IDENTITY_CONFLICT: producer PID must be current process")
    if record_stages and not record_drains:
        raise ValueError('STAGE_DRAIN_RECORDING_REQUIRED')
    if model_setup is not None and (not record_stages or any(
            v is not None for v in (model,input_ids,attention_mask,eos_token_id))):
        raise ValueError('STAGE_SETUP_RESIDENT_INPUT_CONFLICT')
    if record_drains:
        device_text = str(device)
        if not device_text.startswith('cuda:') or not device_text[5:].isdigit():
            raise ValueError('DRAIN_EXPLICIT_LOGICAL_DEVICE_REQUIRED')
        logical_device = int(device_text[5:])
        if model_setup is None and torch.cuda.current_device() != logical_device:
            raise ValueError('DRAIN_CURRENT_DEVICE_CONFLICT')
    requests = []
    for plan in request_plan:
        identity_key = {**pass_fields, **plan}
        prefix = hashlib.sha256(json.dumps(identity_key, sort_keys=True).encode()).hexdigest()
        boundary_ids = [f"{prefix}:start", *[f"{prefix}:token:{i}" for i in range(output_len)]]
        if plan["request_role"] == "warmup":
            boundary_ids = []
        requests.append({**plan, "expected_output_tokens":output_len, "actual_output_tokens":0,
                         "expected_boundary_ids":boundary_ids, "observed_boundary_ids":[],
                         "outcome":"FAILED", "early_eos":False, "reasons":["NOT_EXECUTED"]})
    ledger = make_gate8_pass_identity(requests=requests, **pass_fields)
    host_records = []
    drain_records = []
    emit = ledger["pass_id"] == "pass1"
    stages = None
    def products():
        validate_pass_identity(ledger)
        result = [ledger,host_records]
        if record_drains:
            from exposedpath.gate8_drain import DRAIN_VERSION
            result.append(dict(schema_version=DRAIN_VERSION,drains=drain_records))
        if stages is not None:
            from exposedpath.gate8_stages import validate_stage_ledger
            validate_stage_ledger(stages.value,ledger)
            result.append(stages.value)
        return tuple(result)
    if record_stages:
        from exposedpath.gate8_stages import StageRecorder
        stages = StageRecorder(ledger,logical_device,torch.cuda,clock_ns,
                               setup_observed=model_setup is not None)
    if model_setup is not None:
        # This is an opt-in producer entry, not a replacement for launcher
        # preflight/target qualification. Check CPU-side input/mask before load.
        from exposedpath.manifest import resolve_logical_cuda_index
        if set(model_setup) != {'model_path','prompt_path','physical_gpu_index','batch_size','manifest_path'}:
            raise ValueError('STAGE_SETUP_SHAPE')
        physical = model_setup['physical_gpu_index']
        batch_size = model_setup['batch_size']
        if (type(physical) is not int or physical<0 or type(batch_size) is not int or batch_size<1
                or os.environ.get('CUDA_DEVICE_ORDER')!='PCI_BUS_ID'
                or os.environ.get('CUDA_VISIBLE_DEVICES')!=str(physical)):
            raise ValueError('STAGE_SETUP_DEVICE_OR_BATCH')
        resolve_logical_cuda_index(physical_gpu_index=physical,
            cuda_visible_devices=os.environ.get('CUDA_VISIBLE_DEVICES'),declared_logical_index=logical_device)
        prompt_path = Path(model_setup['prompt_path'])
        if hashlib.sha256(prompt_path.read_bytes()).hexdigest()!=ledger['prompt_sha256']:
            raise ValueError('STAGE_SETUP_PROMPT_HASH')
        manifest_bytes=Path(model_setup['manifest_path']).read_bytes()
        if (hashlib.sha256(manifest_bytes).hexdigest()!=ledger['wmpc_manifest_sha256']
                or hashlib.sha256(Path(__file__).read_bytes()).hexdigest()!=ledger['runner_source_sha256']):
            raise ValueError('STAGE_SETUP_MANIFEST_OR_SOURCE_HASH')
        manifest=json.loads(manifest_bytes)
        batch = get_batch_inputs(load_prompt_tokens(prompt_path),batch_size,run_role=ledger['run_role'])
        expected={k:ledger[k] for k in ('experiment_id','wmpc_id','run_id','run_role','data_role',
                                        'runner_git_commit','runner_git_dirty','runner_source_sha256')}
        expected.update(model_id=model_setup['model_path'],batch_size=batch_size,
            fixed_output_tokens=output_len,prompt_tokens_sha256=ledger['prompt_sha256'],
            gpu_index_physical=physical,gpu_index_logical=logical_device,
            execution_mode='eager',fixed_input_tokens=batch['fixed_input_tokens'],
            warmup_count=sum(r['request_role']=='warmup' for r in ledger['requests']),
            repeat_count=sum(r['request_role']=='measured' for r in ledger['requests']),
            study_mode='G1_NATURAL',n1_intervention=None)
        if (any(k not in manifest or type(manifest[k]) is not type(v) or manifest[k]!=v
                for k,v in expected.items())
                or ledger['runner_git_dirty'] is not False):
            raise ValueError('STAGE_SETUP_MANIFEST_IDENTITY')
        def initialize():
            loaded, tokenizer, _, actual_device = load_model(model_setup['model_path'],physical)
            if actual_device!=device or torch.cuda.current_device()!=logical_device:
                raise ValueError('STAGE_SETUP_DEVICE_CONFLICT')
            ids=torch.tensor(batch['input_ids'],dtype=torch.long,device=device)
            mask=torch.tensor(batch['attention_mask'],dtype=torch.long,device=device)
            return loaded,ids,mask,tokenizer.eos_token_id
        try:
            model,input_ids,attention_mask,eos_token_id = stages.observe('setup',None,initialize)
        except Exception as exc:
            for entry in ledger['requests']:
                entry['reasons']=[f'SETUP_FAILED:{type(exc).__name__}']
            return products()
    for entry in ledger["requests"]:
        if entry["request_role"] == "warmup":
            try:
                warmup=lambda:run_warmup(model, input_ids, attention_mask, output_len, 1)
                if stages is None:
                    warmup()
                else:
                    stages.observe('warmup',entry['identity'],warmup)
                entry.update(actual_output_tokens=output_len, outcome="COMPLETE", reasons=[])
            except Exception as exc:
                entry["reasons"] = [f"WARMUP_FAILED:{type(exc).__name__}"]
                break
            continue
        recorder = Gate8BoundaryRecorder(entry["identity"], entry["expected_boundary_ids"],
                                         marker_sink=torch.cuda.nvtx.mark if emit else None,
                                         clock_ns=clock_ns)
        drain_recorder = None
        if record_drains:
            from exposedpath.gate8_drain import DrainRecorder
            drain_recorder = DrainRecorder(entry['identity'], entry['expected_boundary_ids'][0]+':drain',
                logical_device, clock_ns=clock_ns,
                push=torch.cuda.nvtx.range_push if emit else None,
                pop=torch.cuda.nvtx.range_pop if emit else None)
        try:
            invocation = lambda:run_one_invocation(
                model, input_ids, attention_mask, output_len, device,
                "GATE8_REQUEST" if emit else "", "", "", "", eos_token_id,
                token_ready_identity_base=entry["identity"], clock_ns=clock_ns,
                gate8_recorder=recorder,
                drain_recorder=drain_recorder,
            )
            result = invocation() if stages is None else stages.observe('measured',entry['identity'],invocation)
            excluded = result["early_eos"] or result["actual_output_tokens"] != output_len
            entry.update(actual_output_tokens=result["actual_output_tokens"],
                         early_eos=result["early_eos"], outcome="EXCLUDED" if excluded else "COMPLETE",
                         reasons=["EARLY_EOS_OR_OUTPUT_COUNT_MISMATCH"] if excluded else [])
        except Exception as exc:
            entry.update(actual_output_tokens=max(0,len(recorder.records)-1),
                         outcome="FAILED", reasons=[f"RUNTIME_ERROR:{type(exc).__name__}"])
        entry["observed_boundary_ids"] = [r["payload"]["boundary_id"] for r in recorder.records]
        if drain_recorder is not None and drain_recorder.record is not None:
            drain_records.append(drain_recorder.record)
        host_records.extend(recorder.records)
        if entry["outcome"] == "FAILED":
            break  # Do not continue model work with a failed invocation's state.
    return products()


def run_gate8_requests_to_files(*, output_dir, **request_arguments):
    """Persist actual pass outcomes; no collection/export or hash back-patching.

    The caller either supplies resident inputs or explicit model_setup. Existing output is rejected
    before model work. A failed request remains FAILED, never a success receipt.
    """
    import json
    import hashlib
    import os
    import tempfile
    output_dir = Path(output_dir).resolve()
    if output_dir.exists():
        raise FileExistsError(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{output_dir.name}-partial-',dir=output_dir.parent))
    products = run_gate8_requests(**request_arguments)
    ledger, host_records = products[:2]
    files = {}
    outputs = [('pass_identity.json',ledger),('host_boundaries.json',host_records)]
    if len(products) >= 3:
        outputs.append(('drain_ledger.json', products[2]))
    if len(products) == 4:
        outputs.append(('stage_ledger.json', products[3]))
    for name, value in outputs:
        path = staging/name
        with path.open('x',encoding='utf-8',newline='\n') as handle:
            json.dump(value,handle,sort_keys=True,indent=2)
            handle.write('\n')
            handle.flush()
            os.fsync(handle.fileno())
        files[name] = {'filename':name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'size_bytes':path.stat().st_size}
    receipt = {'schema_version':'exposedpath-gate8-producer-receipt/0.1.0',
               'run_id':ledger['run_id'],'pass_id':ledger['pass_id'],'attempt_id':ledger['attempt_id'],
               'status':'COMPLETE' if all(r['outcome']=='COMPLETE' for r in ledger['requests']) else 'INCOMPLETE',
               'files':files, 'gate8_verdict':'NOT_RUN'}
    if len(products) >= 3:
        receipt['schema_version'] = 'exposedpath-gate8-producer-receipt/0.2.0'
    if len(products) == 4:
        receipt['schema_version'] = 'exposedpath-gate8-producer-receipt/0.3.0'
    with (staging/'producer_receipt.json').open('x',encoding='utf-8') as handle:
        json.dump(receipt,handle,sort_keys=True,indent=2)
        handle.write('\n')
        handle.flush()
        os.fsync(handle.fileno())
    staging.rename(output_dir)
    return output_dir/'producer_receipt.json'


def _write_cross_pass_parity(manifest, pass_label, output_dir, manifest_path, model_path, device):
    """Write cross_pass_parity.json for later cross-pass validation."""
    import hashlib, json as _json, os as _os, platform as _platform
    from pathlib import Path as _Path

    from exposedpath import platform_adapter as _adapter

    parity = {
        "schema_version": "exposedpath-v3-cross-pass-2",
        "experiment_id": manifest.get("experiment_id"),
        "wmpc_id": manifest.get("wmpc_id"),
        "run_id": manifest.get("run_id"),
        "pass_id": pass_label,
        "prompt_tokens_sha256": manifest.get("prompt_tokens_sha256"),
        "fixed_input_tokens": manifest.get("fixed_input_tokens"),
        "fixed_output_tokens": manifest.get("fixed_output_tokens"),
        "batch_size": manifest.get("batch_size"),
        "manifest_sha256": hashlib.sha256(_Path(manifest_path).read_bytes()).hexdigest(),
        "runner_source_sha256": hashlib.sha256(_Path(__file__).read_bytes()).hexdigest(),
        "python_executable": sys.executable,
        "python_version": _platform.python_version(),
        "pytorch_version": torch.__version__,
        "transformers_version": (lambda: __import__("transformers").__version__)(),
        "cuda_runtime_version": torch.version.cuda or "unknown",
        "nvidia_driver_version": "unknown",
        "requested_physical_gpu_index": manifest.get("gpu_index", manifest.get("gpu")),
        "cuda_visible_devices": _os.environ.get("CUDA_VISIBLE_DEVICES", ""),
        "cuda_device_order": _os.environ.get("CUDA_DEVICE_ORDER", ""),
        "process_local_cuda_device_index": int(device.split(":")[1]) if device.startswith("cuda:") else 0,
        "gpu_uuid": manifest.get("gpu_uuid"),
        "gpu_pci_bus_id": manifest.get("gpu_pci_bus_id"),
        "gpu_name": manifest.get("gpu_name"),
        "dtype": "fp16",
        "attention_backend": manifest.get("attention_backend", "sdpa"),
        "execution_mode": manifest.get("execution_mode", "eager"),
        # ---- Gate 7 frozen Pass0/Pass1 identity (EP-G7-09) ----
        "data_role": manifest.get("data_role"),
        "run_role": manifest.get("run_role"),
        "phase_boundary_policy_version": PHASE_BOUNDARY_POLICY_VERSION,
        "phase_boundary_policy": PHASE_BOUNDARY_POLICY,
        "token_ready_mechanism": TOKEN_READY_MECHANISM,
        "token_ready_origin": TOKEN_READY_ORIGIN_NATURAL,
        "attempt_plan_version": ATTEMPT_PLAN_VERSION,
        "retry_policy": RETRY_POLICY,
        "planned_warmup_count": manifest.get("warmup_count"),
        "planned_repeat_count": manifest.get("repeat_count"),
        "study_mode": manifest.get("study_mode"),
        "n1_intervention": manifest.get("n1_intervention"),
        "model_eval": True,
        "inference_mode": True,
        "use_cache": True,
        "sampling_config": manifest.get("sampling_config"),
        "warmup_count": manifest.get("warmup_count"),
        "repeat_count": manifest.get("repeat_count"),
        "synchronize_policy": SYNCHRONIZE_POLICY,
        "cpu_affinity": _os.environ.get("CPU_AFFINITY", ""),
        "torch_num_threads": torch.get_num_threads(),
        "torch_num_interop_threads": getattr(torch, "get_num_interop_threads", lambda: None)(),
        "process_pid": _os.getpid(),
        "process_priority": "",
        "omp_num_threads": _os.environ.get("OMP_NUM_THREADS", ""),
        "mkl_num_threads": _os.environ.get("MKL_NUM_THREADS", ""),
        "env_vars": {k: v for k, v in sorted(_os.environ.items()) if any(p in k.upper() for p in ["CUDA","TORCH","NVIDIA","OMP","MKL","NUMBA"])},
        "command_line": " ".join(sys.argv),
    }
    try:
        out = _adapter.nvidia_smi(["--query-gpu=driver_version", "--format=csv,noheader"], timeout=10)
        parity["nvidia_driver_version"] = out.strip().split("\n")[0].strip()
    except Exception:
        pass
    try:
        import psutil; p = psutil.Process(); parity["process_priority"] = str(p.nice())
    except: pass
    out_path = _Path(output_dir) / "cross_pass_parity.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(_json.dumps(parity, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"[runner] cross_pass_parity.json written: {out_path}")


def _sample_gpu_telemetry(
    manifest: dict, pass_label: str, output_dir: Path,
    stage: str, repeat_index=None, gpu_index=0,
):
    """Read-only GPU telemetry using nvidia-smi. Uses PHYSICAL GPU index."""
    import json as _json, datetime as _dt

    from exposedpath import platform_adapter as _adapter
    # Use physical GPU index for nvidia-smi (NOT logical cuda device)
    physical_idx = manifest.get("gpu_index_physical", gpu_index)
    expected_uuid = manifest.get("gpu_uuid")
    expected_pci = manifest.get("gpu_pci_bus_id")
    # Prefer UUID-based query over index for deterministic targeting
    selector = expected_uuid if expected_uuid else str(physical_idx)
    queried_selector = f"UUID={selector}" if expected_uuid else f"INDEX={physical_idx}"

    fields = "index,uuid,pci.bus_id,name,clocks.current.graphics,clocks.current.sm,clocks.current.memory,pstate,temperature.gpu,power.draw,power.limit,utilization.gpu,utilization.memory"
    try:
        out = _adapter.nvidia_smi(
            ["-i", selector, "--query-gpu=" + fields, "--format=csv,noheader,nounits"],
            timeout=10,
        ).strip()
        parts = [x.strip() for x in out.split(",")]
        q_ok = 0
    except Exception as e:
        parts = []; out = f"QUERY_FAILED: {e}"; q_ok = 1

    # Parse observed identity
    obs_index  = parts[0] if len(parts) > 0 else None
    obs_uuid   = parts[1] if len(parts) > 1 else None
    obs_pci    = parts[2] if len(parts) > 2 else None
    obs_name   = parts[3] if len(parts) > 3 else None

    # Identity verification
    uuid_ok = (expected_uuid is None) or (obs_uuid == expected_uuid)
    pci_ok  = (expected_pci is None) or (obs_pci == expected_pci)
    identity_match = uuid_ok and pci_ok
    mismatch_flag = ""
    if not identity_match and q_ok == 0:
        mismatch_flag = "TELEMETRY_GPU_IDENTITY_MISMATCH"
        print(f"[runner] TELEMETRY_GPU_IDENTITY_MISMATCH: expected UUID={expected_uuid} PCI={expected_pci}, observed UUID={obs_uuid} PCI={obs_pci}")

    record = {
        "experiment_id": manifest.get("experiment_id"),
        "wmpc_id": manifest.get("wmpc_id"),
        "run_id": manifest.get("run_id"),
        "pass_id": pass_label,
        "repeat_index": repeat_index,
        "sample_stage": stage,
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "requested_physical_gpu_index": physical_idx,
        "requested_gpu_uuid": expected_uuid,
        "requested_pci_bus_id": expected_pci,
        "queried_selector": queried_selector,
        "observed_gpu_index": obs_index,
        "observed_gpu_uuid": obs_uuid,
        "observed_pci_bus_id": obs_pci,
        "identity_match": identity_match,
        "identity_mismatch_flag": mismatch_flag or None,
        "query_exit_code": q_ok,
        "gpu_name": obs_name,
        "graphics_clock_mhz": parts[4] if len(parts) > 4 else None,
        "sm_clock_mhz": parts[5] if len(parts) > 5 else None,
        "memory_clock_mhz": parts[6] if len(parts) > 6 else None,
        "pstate": parts[7] if len(parts) > 7 else None,
        "temperature_c": parts[8] if len(parts) > 8 else None,
        "power_draw_w": parts[9] if len(parts) > 9 else None,
        "power_limit_w": parts[10] if len(parts) > 10 else None,
        "utilization_gpu_pct": parts[11] if len(parts) > 11 else None,
        "utilization_memory_pct": parts[12] if len(parts) > 12 else None,
        "raw_output": out,
    }
    tdir = output_dir / "telemetry"
    tdir.mkdir(parents=True, exist_ok=True)
    with open(tdir / f"{pass_label}_gpu_telemetry.jsonl", "a", encoding="utf-8") as f:
        f.write(_json.dumps(record, ensure_ascii=False) + "\n")


def _sample_host_state(
    manifest: dict, pass_label: str, output_dir: Path,
    stage: str, repeat_index=None,
):
    """Read-only host runtime state sample. Writes to JSONL."""
    import json as _json, datetime as _dt, os as _os, time as _time, platform as _plat
    try:
        import torch
        num_threads = torch.get_num_threads()
        num_interop = torch.get_num_interop_threads() if hasattr(torch, "get_num_interop_threads") else None
    except Exception:
        num_threads = None; num_interop = None
    try:
        import psutil
        proc = psutil.Process()
        cpu_time = proc.cpu_times()
        mem = proc.memory_info()
        affinity = proc.cpu_affinity() if hasattr(proc, "cpu_affinity") else None
        sys_mem = psutil.virtual_memory()
        cpu_pct = psutil.cpu_percent(interval=0.1)
        pid = proc.pid
    except Exception:
        cpu_time = None; mem = None; affinity = None; sys_mem = None; cpu_pct = None; pid = _os.getpid()
    record = {
        "experiment_id": manifest.get("experiment_id"),
        "wmpc_id": manifest.get("wmpc_id"),
        "run_id": manifest.get("run_id"),
        "pass_id": pass_label,
        "repeat_index": repeat_index,
        "sample_stage": stage,
        "timestamp_utc": _dt.datetime.now(_dt.timezone.utc).isoformat(),
        "pid": pid,
        "cpu_affinity": list(affinity) if affinity else None,
        "omp_num_threads": _os.environ.get("OMP_NUM_THREADS"),
        "mkl_num_threads": _os.environ.get("MKL_NUM_THREADS"),
        "torch_num_threads": num_threads,
        "torch_num_interop_threads": num_interop,
        "cpu_time_user": cpu_time.user if cpu_time else None,
        "cpu_time_system": cpu_time.system if cpu_time else None,
        "memory_rss_mb": round(mem.rss/1e6, 2) if mem else None,
        "memory_vms_mb": round(mem.vms/1e6, 2) if mem else None,
        "system_memory_available_gb": round(sys_mem.available/1e9, 2) if sys_mem else None,
        "system_cpu_percent": cpu_pct,
        "python_version": _plat.python_version(),
        "platform": _plat.platform(),
    }
    tdir = output_dir / "telemetry"
    tdir.mkdir(parents=True, exist_ok=True)
    with open(tdir / f"{pass_label}_host_state.jsonl", "a", encoding="utf-8") as f:
        f.write(_json.dumps(record, ensure_ascii=False) + "\n")


def execute_pass(
    manifest_path: Path,
    pass_label: str,
    output_dir: Path,
    use_nvtx: bool = True,
):
    """Execute a full Pass (0 or 1).

    Args:
        manifest_path: Path to wmpc_manifest.json.
        pass_label: 'pass0' or 'pass1'.
        output_dir: Directory for results (created if needed).
        use_nvtx: Whether to emit NVTX ranges (True for pass1, False for pass0).
    """
    manifest = load_manifest(manifest_path)
    run_id = manifest["run_id"]
    experiment_id = manifest["experiment_id"]
    wmpc_id = manifest["wmpc_id"]
    model_path = manifest["model_id"]
    batch_size = manifest["batch_size"]
    fixed_output_tokens = manifest["fixed_output_tokens"]
    warmup_count = manifest["warmup_count"]
    repeat_count = manifest["repeat_count"]
    # ---- Frozen Gate 7 run-mode identity: fail closed, never defaulted ----
    missing_identity = [
        key for key in ("run_role", "data_role", "study_mode") if not manifest.get(key)
    ]
    if missing_identity:
        raise RuntimeError(
            "manifest is missing required Gate 7 identity fields: "
            + ", ".join(missing_identity)
        )
    run_role = manifest["run_role"]
    data_role = manifest["data_role"]
    study_mode = manifest["study_mode"]
    if study_mode != "G1_NATURAL":
        raise RuntimeError(
            "N1_INTERVENTION execution is not enabled in EP-G7-08; "
            "only its identity contract is available"
        )
    attempt_provenance = {
        "data_role": data_role,
        "run_role": run_role,
        "study_mode": study_mode,
    }
    # Use physical GPU from manifest if present; fall back to 0.
    # The load_model function handles CUDA_VISIBLE_DEVICES remapping.
    gpu = manifest.get("gpu", 0) if isinstance(manifest.get("gpu"), int) else 0

    # ---- SHA-256 integrity check (before any GPU work) ----
    sha_err = validate_prompt_tokens_sha256_match(manifest)
    if sha_err:
        print(f"[runner] FATAL: prompt_tokens_sha256 verification failed:\n  {sha_err}")
        sys.exit(1)
    print(f"[runner] prompt_tokens_sha256 verified: {manifest['prompt_tokens_sha256'][:16]}...")

    # Load prompt_tokens
    pt_path = Path(manifest["prompt_tokens_file"])
    prompt_tokens = load_prompt_tokens(pt_path)
    batch_inputs = get_batch_inputs(prompt_tokens, batch_size, run_role=run_role)
    fixed_input_tokens = batch_inputs["fixed_input_tokens"]

    # Load model
    model, tokenizer, vocab_size, device = load_model(model_path, gpu)
    eos_token_id = tokenizer.eos_token_id

    # Prepare tensors
    input_ids = torch.tensor(batch_inputs["input_ids"], dtype=torch.long, device=device)
    attention_mask = torch.tensor(batch_inputs["attention_mask"], dtype=torch.long, device=device)

    # ---- Telemetry: before warmup ----
    _sample_gpu_telemetry(manifest, pass_label, output_dir, "before_warmup", gpu_index=gpu)

    # ---- Warmup (no NVTX, no results) ----
    run_warmup(model, input_ids, attention_mask, fixed_output_tokens, warmup_count)

    # ---- Telemetry: after warmup ----
    _sample_gpu_telemetry(manifest, pass_label, output_dir, "after_warmup", gpu_index=gpu)

    # ---- NVTX labels ----
    nvtx_invocation = ""  # placeholder template
    nvtx_full = make_phase_label("full_request") if use_nvtx else ""
    nvtx_prefill = make_phase_label("prefill") if use_nvtx else ""
    nvtx_decode = make_phase_label("decode") if use_nvtx else ""

    # ---- Formal repeats ----
    print(f"[runner] Starting {repeat_count} repeat(s) for {pass_label}...")
    for rep in range(repeat_count):
        print(f"\n[runner] === Repeat {rep + 1}/{repeat_count} ===")
        _sample_gpu_telemetry(manifest, pass_label, output_dir, "before_repeat", repeat_index=rep, gpu_index=gpu)
        _sample_host_state(manifest, pass_label, output_dir, "before_repeat", repeat_index=rep)
        label = make_invocation_label(experiment_id, wmpc_id, run_id, pass_label, rep) if use_nvtx else ""

        try:
            token_ready_identity_base = {
                "experiment_id": experiment_id,
                "wmpc_id": wmpc_id,
                "run_id": run_id,
                "run_role": run_role,
                "pass_id": pass_label,
                "request_id": f"{run_id}:repeat:{rep}",
                "repeat_id": str(rep),
            }
            result = run_one_invocation(
                model=model,
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_len=fixed_output_tokens,
                device=device,
                nvtx_invocation_label=label,
                nvtx_full_request_label=nvtx_full,
                nvtx_prefill_label=nvtx_prefill,
                nvtx_decode_label=nvtx_decode,
                eos_token_id=eos_token_id,
                token_ready_identity_base=token_ready_identity_base,
            )

            # Validate output
            if result["actual_output_tokens"] != fixed_output_tokens:
                reason = (
                    f"output token count mismatch: expected {fixed_output_tokens}, "
                    f"got {result['actual_output_tokens']}"
                    + (" (early EOS)" if result["early_eos"] else "")
                )
                record_exclusion(
                    output_dir, run_id, rep, reason,
                    exclusion_reason=EXCLUSION_REASON_OUTPUT_TOKEN_COUNT_MISMATCH,
                    early_eos=bool(result["early_eos"]),
                    output_len_expected=fixed_output_tokens,
                    output_len_actual=result["actual_output_tokens"],
                    **attempt_provenance,
                )
                print(f"  EXCLUDED: {reason}")
                continue

            if result["early_eos"]:
                record_exclusion(
                    output_dir, run_id, rep, "early EOS before fixed_output_tokens",
                    exclusion_reason=EXCLUSION_REASON_EARLY_EOS,
                    early_eos=True,
                    output_len_expected=fixed_output_tokens,
                    output_len_actual=result["actual_output_tokens"],
                    **attempt_provenance,
                )
                print(f"  EXCLUDED: early EOS")
                continue

            record_success(
                output_dir=output_dir,
                run_id=run_id,
                repeat_index=rep,
                inference_start_ns=result["inference_start_ns"],
                inference_end_ns=result["inference_end_ns"],
                prefill_latency_ms=result["prefill_latency_ms"],
                decode_latency_ms=result["decode_latency_ms"],
                actual_input_tokens=result["actual_input_tokens"],
                actual_output_tokens=result["actual_output_tokens"],
                batch_size=result["batch_size"],
                output_len_expected=fixed_output_tokens,
                **attempt_provenance,
                extra={
                    "token_ready_boundaries": token_ready_boundaries_to_records(
                        result["token_ready_boundaries"]
                    ),
                },
            )
            e2e_ms = (result['inference_end_ns'] - result['inference_start_ns']) / 1_000_000.0
            _sample_gpu_telemetry(manifest, pass_label, output_dir, "after_repeat", repeat_index=rep, gpu_index=gpu)
            _sample_host_state(manifest, pass_label, output_dir, "after_repeat", repeat_index=rep)
            print(
                f"  prefill={result['prefill_latency_ms']:.1f}ms  "
                f"decode={result['decode_latency_ms']:.1f}ms  "
                f"e2e={e2e_ms:.1f}ms"
            )

        except torch.cuda.OutOfMemoryError as e:
            record_exclusion(
                output_dir, run_id, rep, "OOM", exception=str(e),
                exclusion_reason=EXCLUSION_REASON_OOM,
                oom=True,
                output_len_expected=fixed_output_tokens,
                **attempt_provenance,
            )
            print(f"  EXCLUDED: OOM")
        except Exception as e:
            is_cuda_error = isinstance(e, getattr(torch.cuda, "CudaError", ()))
            record_exclusion(
                output_dir, run_id, rep,
                "CUDA error" if is_cuda_error else "runtime_error",
                exception=str(e),
                exclusion_reason=(
                    EXCLUSION_REASON_CUDA_ERROR if is_cuda_error
                    else EXCLUSION_REASON_RUNTIME_ERROR
                ),
                output_len_expected=fixed_output_tokens,
                **attempt_provenance,
            )
            traceback.print_exc()
            print(f"  EXCLUDED: {e}")

    # ---- Attempt ledger must account for every planned repeat index exactly once ----
    try:
        pass_accounting = load_attempt_accounting(
            output_dir,
            planned_warmup_count=warmup_count,
            planned_repeat_count=repeat_count,
        )
    except FileNotFoundError as e:
        print(f"[runner] FATAL: {e}")
        sys.exit(1)
    unless_accounted = (
        pass_accounting["missing_repeat_indexes"]
        or pass_accounting["duplicate_repeat_indexes"]
        or pass_accounting["unexpected_repeat_indexes"]
        or pass_accounting["records_missing_attempt_identity"]
    )
    if unless_accounted:
        print(
            f"[runner] FATAL: {pass_label} attempt accounting is incomplete or "
            f"ambiguous: missing={pass_accounting['missing_repeat_indexes']} "
            f"duplicate={pass_accounting['duplicate_repeat_indexes']} "
            f"unexpected={pass_accounting['unexpected_repeat_indexes']} "
            f"missing_identity={pass_accounting['records_missing_attempt_identity']}"
        )
        sys.exit(1)

    # ---- Telemetry: after pass ----
    _sample_gpu_telemetry(manifest, pass_label, output_dir, "after_pass", gpu_index=gpu)

    # ---- Write cross-pass parity metadata (after all repeats) ----
    _write_cross_pass_parity(manifest, pass_label, output_dir, manifest_path, model_path, device)

    print(f"\n[runner] {pass_label} complete.")
