"""Compiled CPU producer -> synthetic Raw -> existing S/A; not CUDA qualification."""
import importlib
import json
import sqlite3
import subprocess

import pytest

from test_native_llama import prepared, cpu_native_binary, GPU
from test_gate8_identity import write_json, sha, UUID
from test_v141_canonical_raw import _make_source_sqlite


def api():
    assert importlib.util.find_spec('exposedpath_v141.native_llama_scope'), 'native source-bound scope adapter missing'
    return importlib.import_module('exposedpath_v141.native_llama_scope')


def sources(tmp_path,binary,damage=None):
    spec=prepared(tmp_path); p=tmp_path/'producer.json'
    run=subprocess.run([str(binary),str(spec),str(p),'ok'],capture_output=True,timeout=20)
    assert run.returncode==0
    observed=json.loads(p.read_text());sqlite=tmp_path/'trace.sqlite'
    tid=_make_source_sqlite(sqlite);global_pid=tid-tid%2**24
    with sqlite3.connect(sqlite) as db:
        db.execute('ALTER TABLE TARGET_INFO_GPU ADD COLUMN uuid TEXT')
        db.execute('ALTER TABLE TARGET_INFO_GPU ADD COLUMN busLocation TEXT')
        db.execute('UPDATE TARGET_INFO_GPU SET id=9,uuid=?,busLocation=?',(UUID,GPU['pci_bus_id']))
        db.execute('CREATE TABLE TARGET_INFO_CUDA_DEVICE(pid INTEGER,cudaId INTEGER,uuid TEXT,gpuId INTEGER)')
        db.execute('INSERT INTO TARGET_INFO_CUDA_DEVICE VALUES (3,0,?,9)',(UUID,))
        for table in ('NVTX_EVENTS','CUPTI_ACTIVITY_KIND_RUNTIME','CUPTI_ACTIVITY_KIND_SYNCHRONIZATION',
            'CUPTI_ACTIVITY_KIND_KERNEL','CUPTI_ACTIVITY_KIND_MEMCPY','CUPTI_ACTIVITY_KIND_MEMSET','CUPTI_ACTIVITY_KIND_CUDA_EVENT'):
            db.execute('DELETE FROM '+table)
        db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=2')
        db.execute("INSERT INTO StringIds VALUES (20,'cudaLaunchKernel')")
        for timestamp,b in zip((100,180,300),observed['boundaries']):
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,NULL,34,?,?)',
                (timestamp,'EXPOSEDPATH_NATIVE_BOUNDARY_V1:'+json.dumps(b['payload']),tid))
        for (start,end),call in zip(((140,170),(240,270)),observed['sync_calls']):
            db.execute('INSERT INTO NVTX_EVENTS(start,end,eventType,text,globalTid) VALUES (?,?,59,?,?)',
                (start-1,end+1,'EXPOSEDPATH_JSON_V1:'+json.dumps(call['payload']),tid))
        # Literal independent order: already-complete prefill work + pending
        # prefill work, then decode submission. A future submission cannot join W.
        for corr,start,end in ((5,101,103),(6,110,115),(16,190,195)):
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,?,20,0,NULL)',(start,end,tid,corr))
        for corr,start,end in ((5,110,120),(6,130,160),(16,210,260)):
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (?,?,0,1,NULL,2,?,?,2,2,NULL,NULL)',(start,end,corr,global_pid))
        for corr,start,end in ((7,140,170),(17,240,270)):
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (?,?,0,?,?,1,0,NULL)',(start,end,tid,corr))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION VALUES (?,?,0,1,NULL,2,?,?,NULL,3,4294967295,NULL)',(start+1,end-1,corr,global_pid))
        if damage=='boundary':db.execute('DELETE FROM NVTX_EVENTS WHERE start=180')
        if damage=='stream':db.execute('UPDATE CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SET streamId=9 WHERE correlationId=7')
        if damage=='correlation':db.execute('UPDATE CUPTI_ACTIVITY_KIND_KERNEL SET correlationId=99 WHERE correlationId=6')
        if damage=='effect':db.execute('DELETE FROM CUPTI_ACTIVITY_KIND_KERNEL WHERE correlationId=6')
        if damage=='failed':db.execute('UPDATE CUPTI_ACTIVITY_KIND_RUNTIME SET returnValue=1 WHERE correlationId=7')
        if damage=='unknown':
            db.execute("INSERT INTO DIAGNOSTIC_EVENT VALUES (1,0,2,'unbounded new diagnostic')")
        if damage=='mode':
            db.execute('UPDATE TARGET_INFO_CUDA_STREAM SET flag=0')
            db.execute('INSERT INTO TARGET_INFO_CUDA_STREAM VALUES (0,1,2,3,1,0,0)')
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME VALUES (125,126,0,?,25,20,0,NULL)',(tid,))
            db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL VALUES (130,135,0,1,NULL,0,25,?,2,2,NULL,NULL)',(global_pid,))
        if damage=='request':
            row=db.execute('SELECT rowid,text FROM NVTX_EVENTS WHERE start=139').fetchone()
            payload=json.loads(row[1].split(':',1)[1]);payload['request_id']='other'
            db.execute('UPDATE NVTX_EVENTS SET text=? WHERE rowid=?',('EXPOSEDPATH_JSON_V1:'+json.dumps(payload),row[0]))
        db.execute("UPDATE META_DATA_EXPORT SET value='2026.2.1.210' WHERE name='EXPORT_PRODUCT_VERSION'")
        db.execute("UPDATE META_DATA_EXPORT SET value='3.25.0' WHERE name='EXPORT_SCHEMA_VERSION'")
    raw=tmp_path/'synthetic.rep';raw.write_bytes(b'CPU fixture, not an Nsight REP')
    source=write_json(tmp_path/'canonical_source.json',dict(json.loads(spec.read_text())['identity'],
        default_stream_mode='UNKNOWN',selected_device_id=None))
    from exposedpath_v141.canonical_raw import convert_sqlite_to_canonical
    canonical=convert_sqlite_to_canonical(sqlite,tmp_path/'canonical','Engineering',raw_sha256=sha(raw),
        collector_version='2026.2.1.210',source_manifest=source)
    preflight=write_json(tmp_path/'preflight.json',GPU)
    return canonical,spec,p,sqlite,preflight,raw


def test_compiled_points_bridge_recover_complete_prefix_and_exclude_future(tmp_path,cpu_native_binary):
    paths=sources(tmp_path,cpu_native_binary)
    path=api().write_review(*paths,tmp_path/'review')
    result=api().load_review(path,*paths)
    assert result['qualification']=='NOT_RUN' and not result['formal_eligible']
    assert [(w['phase'],w['start_ns'],w['end_ns']) for w in result['projections']]==[
        ('full_request',100,300),('prefill',100,180),('decode',180,300)]
    s=result['s_records'][0]
    assert s['validity']=='VALID_NONEMPTY'
    assert len(s['wait_set_activity_ids'])==2
    assert s['terminal']['end_ns']==160
    assert all('CUPTI_ACTIVITY_KIND_KERNEL' in i for i in s['wait_set_activity_ids'])
    a=result['a_records'][0]
    # Two 30ns API waits each expose 20ns, hence 20ns total residual.
    # Launch APIs occupy 2+5+5=12ns; Host=200-60-12=128ns.
    assert [a[k] for k in ('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')]==[128,12,40,20,0]
    assert [r['T_window_ns'] for r in result['a_records']]==[200,80,120]
    assert result['device_mapping']['gpu_index_physical']==3
    assert result['device_mapping']['gpu_index_logical']==0
    assert result['device_mapping']['nsys_inventory_gpu_id']==9
    assert result['device_mapping']['trace_device_id']==0
    result['projections'][0]['end_ns']=301;write_json(path,result)
    with pytest.raises(ValueError,match='RESULT_CHANGED'):api().load_review(path,*paths)


def test_derived_sidecar_missing_is_not_accepted(tmp_path,cpu_native_binary):
    paths=sources(tmp_path,cpu_native_binary)
    path=api().write_review(*paths,tmp_path/'review')
    (path.parent/'diagnostics.json').unlink()
    with pytest.raises((ValueError,OSError)):api().load_review(path,*paths)


@pytest.mark.parametrize('damage',['boundary','stream','correlation','effect','failed','request','unknown','mode'])
def test_native_missing_evidence_cannot_be_host_or_zero(tmp_path,cpu_native_binary,damage):
    paths=sources(tmp_path,cpu_native_binary,damage)
    with pytest.raises(ValueError):api().write_review(*paths,tmp_path/'blocked')
    assert not (tmp_path/'blocked').exists()
