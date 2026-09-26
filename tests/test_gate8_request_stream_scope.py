"""Two real file invocations with GPU records; documents an unfixed scope limit.

Synthetic SQLite, not a GPU run. No drain-based erasure of historical records.
"""
import sqlite3
import pytest
from test_gate8_signed_time import signed_inputs
from test_gate8_boundaries import project


@pytest.mark.parametrize('shared',[True,False])
def test_prior_request_completed_work_is_not_silently_removed(tmp_path,monkeypatch,shared):
    inputs,host=signed_inputs(tmp_path,monkeypatch,return_sources=True)
    with sqlite3.connect(inputs[0]) as db:
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_RUNTIME SELECT start+300,end+300,eventClass,globalTid,correlationId+10,nameId,returnValue,callchainId FROM CUPTI_ACTIVITY_KIND_RUNTIME')
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_KERNEL SELECT start+300,end+300,deviceId,contextId,greenContextId,?,correlationId+10,globalPid,demangledName,shortName,graphNodeId,graphId FROM CUPTI_ACTIVITY_KIND_KERNEL',(2 if shared else 3,))
        db.execute('INSERT INTO CUPTI_ACTIVITY_KIND_SYNCHRONIZATION SELECT start+300,end+300,deviceId,contextId,greenContextId,?,correlationId+10,globalPid,deprecatedSyncType,syncType,eventId,eventSyncId FROM CUPTI_ACTIVITY_KIND_SYNCHRONIZATION',(2 if shared else 3,))
        if not shared:
            db.execute('INSERT INTO TARGET_INFO_CUDA_STREAM SELECT 3,hwId,vmId,processId,contextId,priority,1 FROM TARGET_INFO_CUDA_STREAM LIMIT 1')
    canonical,scope=project(tmp_path,inputs,host)
    from exposedpath_v141.gate8_scope import build_projected_ab_inputs
    from exposedpath_v141.time_representation import time_representation,SIGNED
    with time_representation(SIGNED): result=build_projected_ab_inputs(canonical,scope)
    rows={r['request_id']:r for r in result.s_records}
    assert rows['request-0']['validity']=='VALID_NONEMPTY'
    if shared:
        assert rows['request-1']['primary_reason']=='INVOCATION_BLEED'
        assert rows['request-1']['validity'] not in ('VALID_EMPTY','VALID_NONEMPTY')
    else:
        assert rows['request-1']['validity']=='VALID_NONEMPTY'
    assert len(result.canonical.records['device_activity'])==2
