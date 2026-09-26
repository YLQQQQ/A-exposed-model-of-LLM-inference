"""Controlled producer -> Raw checker -> actual file chain; all Raw synthetic."""
import importlib
import json
import os
import sqlite3

import pytest

from test_gate8_controlled_cli import prepare
from test_gate8_controlled_raw import controlled_raw
from test_gate8_identity import UUID,sha,write_json


def chain_inputs(tmp_path,monkeypatch,diagnostics=False):
    _,plan,_=prepare(tmp_path,monkeypatch)
    manifest=plan.parent/'wmpc_manifest.json'; prompt=plan.parent/'prompt.json'; source=plan.parent/'runner_source.py'
    identity=json.loads(plan.read_text())['identity']
    fields={k:identity[k] for k in ('experiment_id','wmpc_id','run_id','runner_git_commit','runner_git_dirty')}
    fields.update(pid=os.getpid(),pass_id='pass1',attempt_id='controlled-attempt-1',
        wmpc_manifest_sha256=sha(manifest),prompt_sha256=sha(prompt),runner_source_sha256=sha(source))
    db,producer=controlled_raw(tmp_path,fields)
    pid=os.getpid()
    with sqlite3.connect(db) as conn:
        conn.execute('ALTER TABLE TARGET_INFO_GPU ADD COLUMN uuid TEXT')
        conn.execute('ALTER TABLE TARGET_INFO_GPU ADD COLUMN busLocation TEXT')
        conn.execute('UPDATE TARGET_INFO_GPU SET uuid=?,busLocation=?',(UUID,'00000000:E1:00.0'))
        conn.execute('CREATE TABLE TARGET_INFO_CUDA_DEVICE(pid INTEGER,cudaId INTEGER,uuid TEXT,gpuId INTEGER)')
        conn.execute('INSERT INTO TARGET_INFO_CUDA_DEVICE VALUES (?,0,?,0)',(pid,UUID))
        conn.execute('UPDATE TARGET_INFO_CUDA_CONTEXT_INFO SET processId=?',(pid,))
        conn.execute('UPDATE TARGET_INFO_CUDA_STREAM SET processId=?,flag=1',(pid,))
        conn.execute('INSERT INTO TARGET_INFO_CUDA_STREAM SELECT 3,hwId,vmId,processId,contextId,priority,1 FROM TARGET_INFO_CUDA_STREAM WHERE streamId=2')
    if diagnostics:
        from test_gate8_controlled_diagnostics import add_diagnostics
        add_diagnostics(db)
    raw=tmp_path/'synthetic.rep'; raw.write_bytes(b'SYNTHETIC_ONLY_NOT_A_REP')
    probe=write_json(tmp_path/'cuda_probe.json',dict(pid=pid,gpu_index_logical=0,gpu_uuid=UUID,
        pci_bus_id='0000:E1:00.0',cuda_device_order='PCI_BUS_ID',cuda_visible_devices='3'))
    execution=write_json(tmp_path/'execution.json',dict(schema_version='exposedpath-controlled-execution/0.1.0',
        plan_path=str(plan),output_dir=str(producer.parent),python_executable='python',
        plan_sha256=sha(plan),commit='d'*40,process_id=pid,init_status='COMPLETE',warmup_status='COMPLETE',
        cleanup_status='COMPLETE',status='COMPLETE',errors=[],process_exit_code=0,
        producer_receipt_sha256=sha(producer/'producer_receipt.json'),gate8_verdict='NOT_RUN',q0_status='NOT_RUN'))
    collection=write_json(tmp_path/'collection.json',dict(schema_version='exposedpath-controlled-collection/0.1.0',
        process_exit_code=0,execution_receipt_sha256=sha(execution),rep_sha256=sha(raw),
        plan_sha256=sha(plan),observation_profile='G8-CONTROLLED-CUDA-NVTX/0.1.0',
        rep_path=str(raw.with_suffix(''))+'.nsys-rep',
        argv=['nsys','profile','--trace=cuda,nvtx','--sample=none','--cpuctxsw=none',
              '--cuda-memory-usage=false','--cuda-trace-scope=process-tree','--isr=false',
              '--output',str(raw.with_suffix('')),'python','-m','exposedpath_v141.gate8_controlled_cli',
              'run','--plan',str(plan),'--output-dir',str(producer.parent),'--execute-controlled']))
    export=write_json(tmp_path/'export.json',dict(status='PASS',error=None,attempt_count=1,successful_attempt=1,
        analyzer_allowed=True,rep_sha256=sha(raw),canonical_sqlite_sha256=sha(db),attempts=[dict(number=1,status='PASS',
        rep_sha256=sha(raw),sqlite_sha256=sha(db),sqlite_size=db.stat().st_size,exit_code=0,
        process_exited=True,timed_out=False,terminated_pid=None,validation_issues=[])]))
    from exposedpath_v141.gate8_files import write_input_receipt
    receipt=write_input_receipt(tmp_path/'input_receipt.json',collector_version='2026.2.1.210',
        capture_session_id='synthetic-controlled',artifacts=dict(raw=raw,sqlite=db,
        pass_identity=producer/'pass_identity.json',host_ledger=producer/'host_boundaries.json',
        producer_receipt=producer/'producer_receipt.json',preflight=plan.parent/'preflight.json',
        cuda_probe=probe,wmpc_manifest=manifest,prompt=prompt,runner_source=source,export_report=export))
    return receipt,dict(plan=plan,execution=execution,collection=collection,
        controlled_receipt=producer/'controlled_receipt.json',operation_ledger=producer/'operation_ledger.json')


def test_controlled_raw_proof_enters_file_chain_without_synthetic_zero_counter(tmp_path,monkeypatch):
    receipt,sources=chain_inputs(tmp_path,monkeypatch)
    mod=importlib.import_module('exposedpath_v141.gate8_files')
    out=mod.process_gate8_receipt(receipt,tmp_path/'result',controlled_sources=sources,synthetic_fixture=True)
    report=json.loads((out.parent/'analysis/gate8_local_analysis.json').read_text())
    assert report['status']=='SYNTHETIC_CALCULATION_ONLY'
    assert report['measurement_validity']=='NOT_ASSESSED'
    assert report['controlled_scope']['collector_integrity_status']=='UNKNOWN'
    assert len(report['controlled_scope']['sync_expectations'])==4
    from exposedpath_v141.ab_bundle import load_ab_bundle
    ab=load_ab_bundle(out.parent/'analysis/ab/ab_manifest.json')
    # New controlled source performs only a checked launch, copy and wait.
    # This does not grant support to an unobserved API in arbitrary models.
    assert [r['A_unattributed_ns'] for r in ab['a_window_records']]==[0,0,0,0,0,0]
    assert all(r['validity']=='B_VALID' for r in ab['b_sync_records'])
    assert list(out.parent.rglob('derived_manifest.json'))
    mod.load_chain_result(out)


def test_controlled_collection_failure_cannot_be_overridden_by_complete_producer(tmp_path,monkeypatch):
    receipt,sources=chain_inputs(tmp_path,monkeypatch)
    value=json.loads(sources['collection'].read_text()); value['process_exit_code']=1; write_json(sources['collection'],value)
    from exposedpath_v141.gate8_files import process_gate8_receipt
    with pytest.raises(ValueError):
        process_gate8_receipt(receipt,tmp_path/'out',controlled_sources=sources,synthetic_fixture=True)
    assert not (tmp_path/'out').exists()


def test_scoped_diagnostics_are_preserved_through_actual_file_chain(tmp_path,monkeypatch):
    receipt,sources=chain_inputs(tmp_path,monkeypatch,diagnostics=True)
    from exposedpath_v141.gate8_files import process_gate8_receipt
    out=process_gate8_receipt(receipt,tmp_path/'out',controlled_sources=sources,synthetic_fixture=True)
    report=json.loads((out.parent/'analysis/gate8_local_analysis.json').read_text())
    assert report['status']=='SYNTHETIC_CALCULATION_ONLY'
    assert report['measurement_validity']=='NOT_ASSESSED'
    assessment=report['controlled_scope']['diagnostic_assessment']
    assert len(assessment['records'])==3
    assert assessment['records'][1]['disposition']=='OUTSIDE_DECLARED_DEPENDENCY_SCOPE'
    assert assessment['collector_integrity_status']=='UNKNOWN'


@pytest.mark.parametrize('damage',['conflicting_trace','wrong_plan'])
def test_collection_command_conflicts_fail_closed(tmp_path,monkeypatch,damage):
    receipt,sources=chain_inputs(tmp_path,monkeypatch)
    value=json.loads(sources['collection'].read_text())
    if damage=='conflicting_trace': value['argv'].append('--trace=none')
    else: value['argv'].extend(['--plan','other_plan.json'])
    write_json(sources['collection'],value)
    from exposedpath_v141.gate8_files import process_gate8_receipt
    with pytest.raises(ValueError): process_gate8_receipt(receipt,tmp_path/'out',controlled_sources=sources,synthetic_fixture=True)
