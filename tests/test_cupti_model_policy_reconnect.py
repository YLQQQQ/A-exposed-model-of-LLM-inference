"""Reconnect the existing model chain; external GPU/process boundaries are CPU doubles."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest
from tests.test_cupti_timeline_model import config as legacy_model_config
from tests.test_cupti_timeline_file_chain import fixture as legacy_files
from tests.test_cupti_event_probe import chain as event_chain

ROOT=Path(__file__).resolve().parents[1]
NATIVE='6c744bf52daff3fc54571e264a0c34e3207aa1df'


def load(name):
    s=importlib.util.spec_from_file_location('_reconnect_'+name,ROOT/'scripts'/(name+'.py'))
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def put(p,v):p.write_text(json.dumps(v),encoding='utf8')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def model_config():
    c=legacy_model_config();c.update(schema_version='cupti-timeline-model/0.1.1',native_commit=NATIVE,
        control_commit='a'*40,activity_policy_version='cupti-api22-activity-policy/0.2.0',
        session=dict(activity_policy_version='cupti-api22-activity-policy/0.2.0'))
    return c


def test_explicit_model_version_reuses_p_and_rejects_mixed_native_or_policy():
    m=load('cupti_timeline_model');c=model_config();m.validate_contract(c)
    from exposedpath.observation_preparation import Execution
    p=m.preparer(c)
    assert type(p).prepare is Execution.prepare and type(p).finish is Execution.finish
    assert p.binding['version']=='CUPTI-TIMELINE-MODEL/0.2'
    m.validate_contract(legacy_model_config())
    for k,v in [('native_commit','7fa36efb340fe59a3138eb6132e162d6b0cbfc41'),('activity_policy_version','old'),
        ('control_commit','bad'),('input_tokens',1024),('role','Pilot')]:
        bad=deepcopy(c);bad[k]=v
        with pytest.raises(ValueError,match='CONTRACT'):m.validate_contract(bad)
    bad=deepcopy(c);bad['session']['activity_policy_version']='old'
    with pytest.raises(ValueError,match='CONTRACT'):m.validate_contract(bad)


def new_files(root):
    b,c=legacy_files(root);cfg=model_config();cfg['run_id']='r'
    put(root/'model_config.json',cfg)
    c.update(schema_version='cupti-timeline-stage-b/0.1.1',native_commit=NATIVE,analysis_commit=NATIVE,
        controller_commit='a'*40,activity_policy_version='cupti-api22-activity-policy/0.2.0')
    ledger=json.loads((root/'producer/pass_identity.json').read_text());ledger['runner_git_commit']=NATIVE
    ledger['wmpc_manifest_sha256']=sha(root/'model_config.json')
    put(root/'producer/pass_identity.json',ledger)
    receipt=json.loads((root/'producer/producer_receipt.json').read_text())
    item=receipt['files']['pass_identity.json'];item.update(sha256=sha(root/'producer/pass_identity.json'),size_bytes=(root/'producer/pass_identity.json').stat().st_size)
    put(root/'producer/producer_receipt.json',receipt)
    raw=json.loads((root/'timeline/capture.json').read_text())
    raw['initialization']=event_chain()[0]['initialization']
    raw['shutdown']=dict(schema_version='cupti-timeline-shutdown/0.1.0',succeeded=True,overflow=0,failure=None,
        steps=[dict(operation=op,activity_kind=k,status_domain='CUPTI',status_code=0,success=True) for op,k in
            [('cuptiActivityFlushAll',None),*[('cuptiActivityDisable',k) for k in (37,9,38,2,1,10,4,5)],
             ('cuptiActivityFlushAll',None),('cuptiUnsubscribe',None),('cuptiFinalize',None)]])
    put(root/'timeline/capture.json',raw)
    session=json.loads((root/'timeline/receipt.json').read_text());session.update(
        schema_version='cupti-timeline-session-receipt/0.1.2',session_id='test',activity_policy=raw['initialization']['activity_policy'],
        capture_sha256=sha(root/'timeline/capture.json'),startup_report_error=None,startup_failure=None)
    put(root/'timeline/receipt.json',session)
    result=json.loads((root/'model_result.json').read_text());result.update(schema_version='cupti-timeline-model-result/0.1.1',
        native_commit=NATIVE,control_commit='a'*40,activity_policy_version='cupti-api22-activity-policy/0.2.0',
        model_entry_sha256=sha(ROOT/'scripts/cupti_timeline_model.py'),config_sha256=sha(root/'model_config.json'))
    for key,name in [('capture_sha256','timeline/capture.json'),('session_receipt_sha256','timeline/receipt.json'),
        ('producer_receipt_sha256','producer/producer_receipt.json')]:result[key]=sha(root/name)
    put(root/'model_result.json',result)
    return b,c


def reseal(root):
    r=json.loads((root/'model_result.json').read_text())
    for key,name in [('capture_sha256','timeline/capture.json'),('session_receipt_sha256','timeline/receipt.json'),('token_sha256','tokens.json')]:r[key]=sha(root/name)
    put(root/'model_result.json',r)


@pytest.mark.parametrize('damage,reason',[(None,None),('policy','POLICY'),('close','SHUTDOWN'),
    ('token','TOKEN_REFERENCE'),('native','MODEL_VERSION'),('positive_effect','SAME_RUN_ANALYSIS')])
def test_two_tokens_new_policy_real_consumer_and_memset_explanation(tmp_path,damage,reason):
    folder=tmp_path/'m';b,c=new_files(folder)
    if damage in ('policy','close','positive_effect'):
        raw=json.loads((folder/'timeline/capture.json').read_text())
        if damage=='policy':raw['initialization']['activity_policy']['dependent_records']=[]
        if damage=='close':raw['shutdown']['succeeded']=False
        if damage=='positive_effect':raw['records']=[r for r in raw['records'] if r['kind']!='MEMSET']
        put(folder/'timeline/capture.json',raw)
        s=json.loads((folder/'timeline/receipt.json').read_text());s['capture_sha256']=sha(folder/'timeline/capture.json');put(folder/'timeline/receipt.json',s)
    if damage=='token':
        t=json.loads((folder/'tokens.json').read_text());t['token_ids'][0]=[999];put(folder/'tokens.json',t)
    if damage=='native':
        r=json.loads((folder/'model_result.json').read_text());r['native_commit']='b'*40;put(folder/'model_result.json',r)
    reseal(folder)
    if damage:
        with pytest.raises(ValueError,match=reason):b.analyze_model(folder,dict(pid=7),c)
        if damage=='positive_effect':
            rows=json.loads((folder/'memset_coverage.json').read_text())['tokens'][0]['calls']
            assert any(r['status']=='UNRESOLVED_NOT_ADMITTED' and r['count']==64 for r in rows)
    else:
        report=b.analyze_model(folder,dict(pid=7),c)
        assert [r['result']['coe_ns'] for r in report['token_results']]==[20,1]
        coverage=json.loads((folder/'memset_coverage.json').read_text())
        assert coverage['scope_authority']=='EXISTING_STRICT_S_COE_ONLY'
        first=coverage['tokens'][0]['calls']
        assert next(r for r in first if r['count']==0)['status']=='LOGICAL_ZERO_QUALIFIED'
        assert next(r for r in first if r['count']==64)['status']=='POSITIVE_EFFECT_QUALIFIED'
        assert all(r['native_stream']==0 for r in first)


def test_new_consumption_isolated_file_chain_without_gpu(tmp_path):
    import jsonschema
    folder=tmp_path/'m';b,c=new_files(folder)
    boot='import sys,runpy,json;sys.dont_write_bytecode=True;p=sys.argv.pop(1);sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];runpy.run_path(p)["analyze_model"](sys.argv[1],{"pid":7},json.loads(sys.argv[2]))'
    r=subprocess.run([sys.executable,'-I','-S','-B','-c',boot,str(ROOT/'scripts/cupti_timeline_b.py'),str(ROOT),str(Path(jsonschema.__file__).parents[1]),str(folder),json.dumps(c)],
        cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    assert json.loads((folder/'analysis_report.json').read_text())['status']=='BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW'


def test_event_reference_real_original_and_tampering(tmp_path):
    p=ROOT/'.local/transfer/cupti_event_38baca449d2f_once.zip'
    assert sha(p)=='1b30ac79fa3e4dd0ee6776ab3e95d380f273fff97a13ed2a07052612dc66e5ed'
    m=load('cupti_timeline_b');support=load('memset_micro');out=tmp_path/'event'
    support.extract(p,out)
    c=json.loads((out/'delivery.json').read_text());c.update(event_root=str(out),
        reviewed_event_receipt_sha256='824183fcea1e4ca5d0f3423cfedf6fb791379bc80a4f3dd47318854a0fac0ed9',
        event_manifest_sha256=sha(out/'artifact_manifest.json'))
    assert m.checked_event(c,support)['event_id']==1
    (out/'probe/side.json').write_text('{}')
    with pytest.raises(ValueError,match='FILE_HASH'):m.checked_event(c,support)


def test_zero_parameter_without_admitted_scope_never_becomes_qualification(tmp_path):
    folder=tmp_path/'m';b,c=new_files(folder)
    raw=json.loads((folder/'timeline/capture.json').read_text());scopes=json.loads((folder/'scope_producers.json').read_text())
    r=b.memset_coverage(raw,scopes,{})
    zero=next(v for v in r['tokens'][0]['calls'] if v['count']==0)
    assert zero['status']=='UNRESOLVED_NOT_ADMITTED' and zero['parameter_class']=='OBSERVED_ZERO' and zero['effect_ids'] is None


@pytest.mark.parametrize('failure',[False,True])
def test_new_control_actual_isolated_consumer_failure_propagation_and_postcheck(tmp_path_factory,monkeypatch,failure):
    import jsonschema
    b=load('cupti_timeline_b');base=tmp_path_factory.mktemp('mc');package=base/'p';package.mkdir()
    a=base/'a';(a/'build').mkdir(parents=True)
    for name in ('receipt.json','artifact_manifest.json','source_bytes.json','build/build.json'):put(a/name,{})
    event=base/'event';(event/'probe/review').mkdir(parents=True)
    for name in ('receipt.json','artifact_manifest.json','probe/review/review.json'):put(event/name,dict(role='CPU_REFERENCE_DOUBLE'))
    c=dict(schema_version='cupti-timeline-stage-b/0.1.1',controller_commit='a'*40,native_commit=NATIVE,analysis_commit=NATIVE,
        activity_policy_version='cupti-api22-activity-policy/0.2.0',server_root=str(base/'YLQ'),code_root=str(ROOT),
        python=sys.executable,target_python=sys.executable,site_root=str(Path(jsonschema.__file__).parents[1]),
        reviewed_a_receipt_sha256='a'*64,reviewed_event_receipt_sha256='b'*64,a_root=str(a),event_root=str(event),budget=b.fixed_budget(),
        model_contract=model_config(),model='CPU_MODEL_NOT_LOADED',inventory_sha256='i'*64,prompt_sha256='b'*64,
        gpu_uuid='CPU_GPU_NOT_QUERIED',gpu_pci='CPU_NOT_QUERIED',run_id='r',session_id='test',expected_token_ids=[[17],[18]],
        client=dict(path='CPU_DLL_NOT_LOADED',sha256='d'*64),cupti=dict(path='CPU_DLL_NOT_LOADED',sha256='e'*64))
    c['model_contract']['run_id']='r'
    for n in ('cupti_timeline_b.py','cupti_timeline_model.py','run_cupti_timeline_b.ps1'):(package/n).write_bytes((ROOT/'scripts'/n).read_bytes())
    put(package/'delivery.json',c)
    put(package/'package_manifest.json',dict(files=[dict(path=p.name,bytes=p.stat().st_size,sha256=sha(p)) for p in package.iterdir()]))
    support=load('memset_micro');calls=[];checks=[]
    def checked(*args):
        checks.append('A_EVENT');return dict(a_root=a,acfg={},verification=dict(mode='CPU_A_EVENT_DOUBLE'))
    def command(argv,cwd,log,**kw):
        calls.append((Path(log).name,kw))
        if Path(log).name=='one_model':
            folder=Path(cwd)/'model';unused,analysiscfg=new_files(folder)
            ledger=json.loads((folder/'producer/pass_identity.json').read_text());ledger['wmpc_manifest_sha256']=sha(Path(cwd)/'model_config.json')
            put(folder/'producer/pass_identity.json',ledger)
            r=json.loads((folder/'producer/producer_receipt.json').read_text())
            r['files']['pass_identity.json'].update(sha256=sha(folder/'producer/pass_identity.json'),size_bytes=(folder/'producer/pass_identity.json').stat().st_size)
            put(folder/'producer/producer_receipt.json',r)
            r=json.loads((folder/'model_result.json').read_text());r['config_sha256']=sha(Path(cwd)/'model_config.json');r['producer_receipt_sha256']=sha(folder/'producer/producer_receipt.json')
            put(folder/'model_result.json',r)
            if failure:
                raw=json.loads((folder/'timeline/capture.json').read_text());raw['records']=[r for r in raw['records'] if r['kind']!='MEMSET'];put(folder/'timeline/capture.json',raw)
                s=json.loads((folder/'timeline/receipt.json').read_text());s['capture_sha256']=sha(folder/'timeline/capture.json');put(folder/'timeline/receipt.json',s);reseal(folder)
            proc=dict(pid=7,status='EXITED',exit_code=0,timed_out=False)
        else:
            # Execute the actual isolated CPU consumer; never substitute its answer.
            r=subprocess.run(argv,cwd=cwd,env=kw['env'],capture_output=True,timeout=20)
            Path(log).with_suffix('.stdout').write_bytes(r.stdout);Path(log).with_suffix('.stderr').write_bytes(r.stderr)
            proc=dict(pid=99,status='EXITED',exit_code=r.returncode,timed_out=False)
        put(Path(log).with_suffix('.process.json'),proc)
        if proc['exit_code']:raise ValueError('CPU_REAL_READER_EXIT:'+str(proc['exit_code']))
        return proc
    support.command=command
    monkeypatch.setattr(b,'components',lambda *a:({'startup_resources':lambda out,archive,cfg:dict(required=cfg['temporary_required_bytes'])},support))
    monkeypatch.setattr(b,'checked_a',checked)
    monkeypatch.setattr(b,'sys',SimpleNamespace(executable=sys.executable,version_info=(3,11,16)))
    for key in ('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH'):monkeypatch.delenv(key,raising=False)
    assert b.run(package,enabled=True,reviewed='a'*64,reviewed_event='b'*64)==(2 if failure else 0)
    assert checks==['A_EVENT','A_EVENT'] and [r[0] for r in calls]==['one_model','same_run_analysis']
    assert [r[1]['timeout'] for r in calls]==[300,180]
    archive=next((base/'YLQ/transfer').glob('*.zip'))
    with zipfile.ZipFile(archive) as z:
        r=json.loads(z.read('receipt.json'));assert r['native_commit']==NATIVE and r['post_execution_static_rechecked'] is True
        assert r['analysis_process']['exit_code']==(1 if failure else 0) and (r['error'] is not None)==failure
        assert r['reviewed_event_receipt_sha256']=='b'*64 and r['COE_admission']=='NOT_ASSESSED'
        assert 'model/memset_coverage.json' in z.namelist()


@pytest.mark.parametrize('event_hash',[None,'b'*64,'c'*64])
@pytest.mark.parametrize('version',['cupti-timeline-stage-b/0.1.1','cupti-timeline-stage-b/0.2.0'])
def test_ps51_new_model_gate_requires_both_reviewed_receipts(tmp_path,event_hash,version):
    script=ROOT/'scripts/run_cupti_timeline_b.ps1';(tmp_path/script.name).write_bytes(script.read_bytes())
    driver=tmp_path/'cupti_timeline_b.py';driver.write_text('from pathlib import Path\nPath(__file__).with_name("entered.txt").write_text("CPU_ONLY")\n')
    put(tmp_path/'delivery.json',dict(schema_version=version,python=sys.executable,
        reviewed_a_receipt_sha256='a'*64,reviewed_event_receipt_sha256='b'*64,
        bootstrap_files=[dict(path=driver.name,sha256=sha(driver))]))
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    argv=[str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(tmp_path/script.name),'-RunReviewedModel','-ReviewedAReceiptSha256','a'*64]
    if event_hash:argv+=['-ReviewedEventReceiptSha256',event_hash]
    r=subprocess.run(argv,cwd=tmp_path,capture_output=True,timeout=20)
    assert (r.returncode==0)==(event_hash=='b'*64) and (tmp_path/'entered.txt').exists()==(event_hash=='b'*64)
