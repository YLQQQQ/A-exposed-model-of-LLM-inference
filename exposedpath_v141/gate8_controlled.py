"""Narrow controlled token producer. Importing this module never loads CUDA.

Not a model benchmark, not the historical Q0-STREAM case, and not qualification.
The backend performs real kernel -> D2H -> stream wait -> host read in execution.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time

from exposedpath.gate8_boundary import Gate8BoundaryRecorder
from exposedpath.gate8_identity import make_gate8_pass_identity, validate_pass_identity
from exposedpath.nvtx import make_structured_nvtx_label
from .gate8_files import _write, _entry

CONSTRUCTION = 'CONTROLLED-D2H-REQUEST/0.1.0'
OP_PREFIX = 'EXPOSEDPATH_CONTROLLED_OP_V1:'
TOKEN_PLAN = ((11, 12), (21, 22))


def run_controlled_to_files(output_dir, *, pass_fields, backend, clock_ns=time.perf_counter_ns):
    destination = Path(output_dir).resolve()
    if destination.exists():
        raise FileExistsError(destination)
    if pass_fields.get('pid') != os.getpid() or pass_fields.get('pass_id') != 'pass1':
        raise ValueError('controlled producer requires actual PID / pass1')
    requests = []
    for i, tokens in enumerate(TOKEN_PLAN):
        prefix = hashlib.sha256(json.dumps([pass_fields, i], sort_keys=True).encode()).hexdigest()
        requests.append(dict(request_id=f'controlled-{i}',repeat_id=str(i),request_role='measured',
            expected_output_tokens=2,actual_output_tokens=0,early_eos=False,outcome='FAILED',
            expected_boundary_ids=[f'{prefix}:start',f'{prefix}:token:0',f'{prefix}:token:1'],
            observed_boundary_ids=[],reasons=['NOT_EXECUTED']))
    ledger = make_gate8_pass_identity(requests=requests, **pass_fields)
    destination.parent.mkdir(parents=True,exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f'.{destination.name}-partial-',dir=destination.parent))
    host, operations, drains = [], [], []
    failed = False
    for entry, tokens in zip(ledger['requests'],TOKEN_PLAN):
        identity = entry['identity']
        recorder = Gate8BoundaryRecorder(identity,entry['expected_boundary_ids'],
                                         marker_sink=backend.mark,clock_ns=clock_ns)
        try:
            before = clock_ns()
            drain_id=f"{identity['request_id']}:prepare"
            backend.push(OP_PREFIX+json.dumps(dict(construction=CONSTRUCTION,identity=identity,
                operation_id=drain_id,stage='prepare',token_index=None,phase=None),sort_keys=True,separators=(',',':')))
            try:
                backend.prepare()  # All inputs resident; drain outside request window.
            finally:
                backend.pop()
            drains.append(dict(request_id=identity['request_id'],operation_id=drain_id,
                               start_ns=before,end_ns=clock_ns(),status='COMPLETE'))
            recorder.observe(clock_ns())
            for ordinal, token in enumerate(tokens):
                phase = 'prefill' if ordinal == 0 else 'decode'
                operation = dict(identity=identity, token_index=ordinal, expected_token=token,
                    observed_token=None,sync_origin='q0_controlled',stages=[],status='INCOMPLETE')
                operations.append(operation)
                for stage, action in (('submit',lambda:backend.submit(token)),('copy',backend.copy),('wait',backend.wait)):
                    op_id=f"{identity['request_id']}:{ordinal}:{stage}"
                    payload=dict(construction=CONSTRUCTION,identity=identity,operation_id=op_id,
                                 stage=stage,token_index=ordinal,phase=phase)
                    backend.push(OP_PREFIX+json.dumps(payload,sort_keys=True,separators=(',',':')))
                    sync_label = make_structured_nvtx_label({**identity,'kind':'sync','phase':phase,
                        'sync_origin':'q0_controlled','sync_ordinal':ordinal,'callsite_id':f'controlled.{phase}.stream_wait'})
                    if stage=='wait': backend.push(sync_label)
                    try:
                        action()
                    finally:
                        if stage=='wait': backend.pop()
                        backend.pop()
                    operation['stages'].append(dict(operation_id=op_id,stage=stage,status='COMPLETE'))
                observed=backend.read()  # CPU dereference, after D2H completion.
                if type(observed) is not int or observed != token:
                    raise ValueError('TOKEN_READBACK_MISMATCH')
                operation['observed_token']=observed
                recorder.observe(clock_ns(),ordinal)
                operation['status']='COMPLETE'
                entry['actual_output_tokens']+=1
            entry.update(outcome='COMPLETE',reasons=[])
        except Exception as exc:
            entry['reasons']=[f'CONTROLLED_EXECUTION_FAILED:{type(exc).__name__}:{exc}']
            failed=True
        finally:
            entry['observed_boundary_ids']=[r['payload']['boundary_id'] for r in recorder.records]
            host.extend(recorder.records)
        if failed: break
    validate_pass_identity(ledger)
    _write(staging/'pass_identity.json',ledger)
    _write(staging/'host_boundaries.json',host)
    _write(staging/'operation_ledger.json',dict(schema_version='exposedpath-controlled-operations/0.1.0',
        construction=CONSTRUCTION,identity={k:ledger[k] for k in ('run_id','pass_id','attempt_id','pid')},
        request_stream_policy='DISJOINT_NONBLOCKING_STREAMS_WARMUP_SEPARATE',
        host_clock_id='PYTHON_PERF_COUNTER_NS',predrains=drains,tokens=operations,
        status='INCOMPLETE' if failed else 'COMPLETE',gate8_verdict='NOT_RUN',q0_status='NOT_RUN'))
    receipt = dict(schema_version='exposedpath-gate8-producer-receipt/0.1.0',
        run_id=ledger['run_id'],pass_id=ledger['pass_id'],attempt_id=ledger['attempt_id'],
        status='INCOMPLETE' if failed else 'COMPLETE',gate8_verdict='NOT_RUN',
        files={name:_entry(staging/name,staging) for name in ('pass_identity.json','host_boundaries.json')})
    _write(staging/'producer_receipt.json',receipt)
    _write(staging/'controlled_receipt.json',dict(schema_version='exposedpath-controlled-receipt/0.1.0',
        construction=CONSTRUCTION,files={name:_entry(staging/name,staging)
        for name in ('operation_ledger.json','producer_receipt.json')},
        status=receipt['status'],q0_status='NOT_RUN',gate8_verdict='NOT_RUN'))
    staging.rename(destination)
    return destination/'producer_receipt.json'
