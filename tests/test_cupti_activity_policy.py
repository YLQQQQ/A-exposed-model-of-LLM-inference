"""Real SDK/client with CPU ABI double: controls are not record coverage."""
from copy import deepcopy
import json
import pytest
from tests.test_cupti_timeline_startup import startup,invoke
from exposedpath.cupti_timeline import startup_diagnostic


def test_invalid_direct_event_enable_is_not_attempted_but_event_decoder_retained(startup,tmp_path):
    # Model the actual INVALID_KIND only at direct kind=36. New fixed policy
    # must never invoke that operation, rather than accept its failing code.
    r,raw=invoke(startup,tmp_path,'event_failure',21)
    assert r['open_code']==r['close_code']==0
    controls=r['controls']
    assert [(s['operation'],s['kind']) for s in controls if s['operation'] in ('enable','dump')]==[
        ('enable',5),('enable',4),('enable',10),('enable',1),('enable',2),('enable',38),('dump',9),('dump',37)]
    assert [s['kind'] for s in controls if s['operation']=='disable']==[37,9,38,2,1,10,4,5]
    assert all(s['code']==0 for s in controls)
    init=startup_diagnostic(tmp_path/'capture.json')
    assert init['schema_version']=='cupti-timeline-startup/0.2.0'
    assert init['activity_policy']['retained_record_kinds']==[5,4,10,1,2,38,9,37,36]
    assert init['activity_policy']['dependent_records']==[dict(kind=36,controlled_by=38)]


@pytest.mark.parametrize('mode,code,operation,kind',[
    ('sync_failure',21,'cuptiActivityEnable',38),('stream_failure',37,'cuptiActivityEnableAndDump',37)])
def test_remaining_control_failures_stop_and_close_only_successful_prefix(startup,tmp_path,mode,code,operation,kind):
    r,raw=invoke(startup,tmp_path,mode,code)
    assert r['open_code']==3 and r['close_code']!=0
    f=raw['initialization']['failure']
    assert (f['operation'],f['activity_kind'],f['status_code'])==(operation,kind,code)
    controls=r['controls'];enabled=[x['kind'] for x in controls if x['operation'] in ('enable','dump') and x['code']==0]
    assert [x['kind'] for x in controls if x['operation']=='disable']==enabled[::-1]
    assert len([x for x in controls if x['kind']==kind and x['operation'] in ('enable','dump')])==1


@pytest.mark.parametrize('mode',['disable_failure','flush_failure'])
def test_close_failure_is_not_accepted_when_open_succeeded(startup,tmp_path,mode):
    r,raw=invoke(startup,tmp_path,mode,21)
    assert r['open_code']==0 and r['close_code']==4 and raw['quality']['errors']
    assert raw['shutdown']['failure']['status_code']==21 and raw['shutdown']['succeeded'] is False
    if mode=='disable_failure':assert next(s for s in r['controls'] if s['operation']=='disable' and s['kind']==38)['code']==21


def test_legacy_original_error_stays_error_not_reinterpreted_as_new_policy(tmp_path):
    f=dict(operation='cuptiActivityEnable',status_domain='CUPTI',status_code=21,success=False,
        activity_kind=36,activity_name='CUDA_EVENT',detail='')
    old=dict(schema_version='cupti-timeline-startup/0.1.0',succeeded=False,overflow=0,steps=[f],failure=f)
    p=tmp_path/'capture.json';p.write_text(json.dumps(dict(initialization=old)))
    assert startup_diagnostic(p)==old
    old['activity_policy']={}
    p.write_text(json.dumps(dict(initialization=old)))
    with pytest.raises(ValueError,match='POLICY_VERSION'):startup_diagnostic(p)


@pytest.mark.parametrize('damage',['version','controls','dependent','records','step_order'])
def test_new_policy_cannot_drop_record_obligations_or_guess_controls(startup,tmp_path,damage):
    _,raw=invoke(startup,tmp_path,'success');v=deepcopy(raw['initialization'])
    if damage=='version':v['activity_policy']['schema_version']='future'
    if damage=='controls':v['activity_policy']['explicit_enable_kinds'].append(36)
    if damage=='dependent':v['activity_policy']['dependent_records']=[]
    if damage=='records':v['activity_policy']['retained_record_kinds'].remove(36)
    if damage=='step_order':v['steps'][-1],v['steps'][-2]=v['steps'][-2],v['steps'][-1]
    p=tmp_path/'modified.json';p.write_text(json.dumps(dict(initialization=v)))
    with pytest.raises(ValueError,match='POLICY'):startup_diagnostic(p)


def test_expected_new_session_cannot_accept_old_missing_policy_or_unknown_version(tmp_path):
    from tests.test_cupti_timeline_session import Function
    from types import SimpleNamespace
    from exposedpath.cupti_timeline import CaptureSession,sha
    a=tmp_path/'cl';b=tmp_path/'cu';a.write_bytes(b'CPU');b.write_bytes(b'CPU')
    cfg=dict(client=str(a),cupti=str(b),client_sha256=sha(a),cupti_sha256=sha(b),session_id='s',activity_policy_version='future')
    with pytest.raises(ValueError,match='POLICY_VERSION'):CaptureSession(cfg,tmp_path/'never')
    cfg['activity_policy_version']='cupti-api22-activity-policy/0.2.0'
    def close(path):
        Path=__import__('pathlib').Path
        Path(path).write_text(json.dumps(dict(initialization=dict(schema_version='cupti-timeline-startup/0.1.0',
            succeeded=True,overflow=0,steps=[],failure=None))));return 0
    lib=SimpleNamespace(ep_timeline_abi_version=Function(lambda:1),ep_timeline_open=Function(lambda *a:0),
        ep_timeline_mark=Function(lambda *a:0),ep_timeline_close=Function(close))
    with pytest.raises(ValueError,match='STARTUP_REPORT_INVALID'):
        with CaptureSession(cfg,tmp_path/'out',allow_target_capture=True,_library_factory=lambda *a:lib):pass
    receipt=json.loads((tmp_path/'out/receipt.json').read_text())
    assert 'POLICY_EXPECTED_NEW_CAPTURE' in receipt['startup_report_error']


def test_new_startup_policy_reaches_actual_source_bridge_without_granting_event_dependency():
    from tests.test_cupti_timeline_adapter import capture
    from tests.test_cupti_event_probe import chain
    from analysis.cupti_timeline import to_evidence,analyze_scope
    raw=capture();scope=raw.pop('scope');raw['initialization']=chain()[0]['initialization']
    assert analyze_scope(to_evidence(raw,scope))['coe_ns']==20
    raw['initialization']['activity_policy']['schema_version']='unknown'
    with pytest.raises(ValueError,match='POLICY_VERSION'):to_evidence(raw,scope)
