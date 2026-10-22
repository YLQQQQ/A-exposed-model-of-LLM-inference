"""Finite 1024 file chain. GPU/model boundaries below are CPU doubles only."""
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
import zipfile

import pytest

from tests.test_cupti_model_policy_reconnect import new_files, model_config, put, sha

ROOT=Path(__file__).resolve().parents[1]


def load(name):
    spec=importlib.util.spec_from_file_location('_finite_'+name,ROOT/'scripts'/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def contract():
    c=model_config();c.update(schema_version='cupti-timeline-model/0.2.0',input_tokens=1024,
        consumer_version='submit-effect-bridge/0.3.0',
        timing_policy='cupti-api22-distinct-api-callback-boundaries/0.2.0',
        driver_query_policy='cupti-api22-driver-queries/0.1.0',
        runtime_query_policy='cupti-api22-runtime-queries/0.1.0')
    return c


def test_1024_explicit_contract_keeps_old_finite_domains():
    m=load('cupti_timeline_model');c=contract()
    assert m.validate_contract(c)=='6c744bf52daff3fc54571e264a0c34e3207aa1df'
    p=m.preparer(c)
    from exposedpath.observation_preparation import Execution
    assert type(p).prepare is Execution.prepare and type(p).finish is Execution.finish
    assert p.binding['input_tokens']==1024 and p.binding['version']=='CUPTI-TIMELINE-MODEL/0.3'
    for key,value in [('input_tokens',768),('consumer_version','submit-effect-bridge/0.2.0'),
        ('runtime_query_policy','unknown'),('role','Formal'),('completion_policy','CPRE')]:
        bad=deepcopy(c);bad[key]=value
        with pytest.raises(ValueError,match='CONTRACT'):m.validate_contract(bad)
    bad=model_config();bad['input_tokens']=1024
    with pytest.raises(ValueError,match='CONTRACT'):m.validate_contract(bad)


def finite_files(root):
    b,c=new_files(root);mc=contract();mc['run_id']='r'
    # Hand-shaped input and mask; no model or device is imported.
    prompt=dict(fixed_input_tokens=1024,samples=[dict(sample_index=0,
        input_ids=list(range(100,132))*32,attention_mask=[1]*1024)])
    from exposedpath.coe_input_pilot import input_identity,MIDPOINT_VERSION
    ident=input_identity(prompt,version=MIDPOINT_VERSION)
    put(root/'input_1024.json',prompt)
    mc.update(prompt=str(root/'input_1024.json'),prompt_sha256=sha(root/'input_1024.json'),input_identity=ident)
    put(root/'model_config.json',mc)
    c.update(schema_version='cupti-timeline-stage-b/0.2.0',analysis_commit='a'*40,
        prompt_sha256=mc['prompt_sha256'],input_identity=ident,model_contract=mc,
        consumer_version=mc['consumer_version'],timing_policy=mc['timing_policy'],
        driver_query_policy=mc['driver_query_policy'],runtime_query_policy=mc['runtime_query_policy'])
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    ledger.update(wmpc_manifest_sha256=sha(root/'model_config.json'),prompt_sha256=mc['prompt_sha256'])
    put(root/'producer/pass_identity.json',ledger)
    receipt=json.loads((root/'producer/producer_receipt.json').read_text())
    receipt['files']['pass_identity.json'].update(sha256=sha(root/'producer/pass_identity.json'),size_bytes=(root/'producer/pass_identity.json').stat().st_size)
    put(root/'producer/producer_receipt.json',receipt)
    t=json.loads((root/'tokens.json').read_text());t.update(actual_input_tokens=1024,input_identity=ident)
    put(root/'tokens.json',t)
    s=json.loads((root/'setup.json').read_text());s.update(input_shape=[1,1024],input_sha256=mc['prompt_sha256'],input_identity=ident)
    put(root/'setup.json',s)
    raw=json.loads((root/'timeline/capture.json').read_text())
    # Exact API22 startup identity and matching callback IDs for new consumer.
    cbids={1:211,2:307,3:51,4:51,5:216,6:41,7:279,8:131,9:126,10:165}
    for call in raw['callbacks']:
        call['cbid']=cbids[call['id']%100]
        if call['id']%100==7:call['name']='cuMemcpyDtoHAsync_v2'
        if call['id']%100 in (1,2):call['params']=dict(native_stream=0)
        if isinstance(call.get('params'),dict):call['params'].setdefault('native_stream',0)
    indexed={(v['domain'],v['correlation']):v for v in raw['callbacks']}
    for api in raw['records']:
        if api['kind']=='API':api['cbid']=indexed[(api['domain'],api['correlation'])]['cbid']
    put(root/'timeline/capture.json',raw)
    sr=json.loads((root/'timeline/receipt.json').read_text());sr['capture_sha256']=sha(root/'timeline/capture.json');put(root/'timeline/receipt.json',sr)
    r=json.loads((root/'model_result.json').read_text());r.update(schema_version='cupti-timeline-model-result/0.2.0',
        config_sha256=sha(root/'model_config.json'))
    for key,name in dict(capture_sha256='timeline/capture.json',session_receipt_sha256='timeline/receipt.json',
        producer_receipt_sha256='producer/producer_receipt.json',token_sha256='tokens.json',setup_sha256='setup.json').items():r[key]=sha(root/name)
    put(root/'model_result.json',r)
    return b,c


def test_1024_real_producer_files_reach_explicit_03_two_token_consumer(tmp_path):
    b,c=finite_files(tmp_path/'m')
    report=b.analyze_model(tmp_path/'m',dict(pid=7),c)
    assert [r['result']['coe_ns'] for r in report['token_results']]==[20,1]
    assert report['analysis_commit']=='a'*40 and report['native_commit']!=report['analysis_commit']
    assert all(r['result']['schema_version']=='submit-effect-bridge/0.3.0' for r in report['token_results'])


@pytest.mark.parametrize('damage,reason',[
    ('input_bytes','INPUT_HASH'),('mask_identity','INPUT_IDENTITY'),('token','TOKEN_REFERENCE'),
    ('consumer','CONSUMER_POLICY'),('scope','SCOPE_PRODUCER_BINDING'),('positive_effect','SAME_RUN_ANALYSIS')])
def test_1024_rejects_real_file_chain_damage(tmp_path,damage,reason):
    root=tmp_path/'m';b,c=finite_files(root)
    r=json.loads((root/'model_result.json').read_text())
    if damage=='input_bytes':(root/'input_1024.json').write_text('{}')
    elif damage=='consumer':c['consumer_version']='submit-effect-bridge/0.2.0'
    else:
        name={'mask_identity':'tokens.json','token':'tokens.json','scope':'scope_producers.json','positive_effect':'timeline/capture.json'}[damage]
        v=json.loads((root/name).read_text())
        if damage=='mask_identity':v['input_identity']['attention_mask_sha256']='0'*64
        if damage=='token':v['token_ids'][0]=[999]
        if damage=='scope':v[0]['run_id']='other'
        if damage=='positive_effect':v['records']=[a for a in v['records'] if a['kind']!='MEMSET']
        put(root/name,v)
        key={'tokens.json':'token_sha256','scope_producers.json':'scope_producers_sha256','timeline/capture.json':'capture_sha256'}[name]
        r[key]=sha(root/name)
        if damage=='positive_effect':
            sr=json.loads((root/'timeline/receipt.json').read_text());sr['capture_sha256']=r[key];put(root/'timeline/receipt.json',sr);r['session_receipt_sha256']=sha(root/'timeline/receipt.json')
        put(root/'model_result.json',r)
    with pytest.raises(ValueError,match=reason):b.analyze_model(root,dict(pid=7),c)


def test_packaged_consumer_isolated_origin_and_tamper(tmp_path):
    """A stale checkout consumer must not silently replace the 0.3 overlay."""
    import jsonschema
    from shutil import copyfile
    files=['analysis/cupti_timeline.py','exposedpath_v141/cupti_driver_queries.py',
        'exposedpath_v141/submit_effect_bridge.py','scripts/analyze_completion_operation_candidate.py']
    for name in files:
        p=tmp_path/'consumer'/name;p.parent.mkdir(parents=True,exist_ok=True);copyfile(ROOT/name,p)
    cfg=dict(code_root=str(ROOT),consumer_root=str(tmp_path/'consumer'),
        consumer_files=[dict(path=n,bytes=(ROOT/n).stat().st_size,sha256=sha(ROOT/n)) for n in files])
    put(tmp_path/'config.json',cfg)
    script=ROOT/'scripts/cupti_model_consumer.py'
    boot='import sys,runpy,json;sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];m=runpy.run_path(sys.argv[1]);c=json.load(open(sys.argv[2]));print(json.dumps(m["bind_consumer"](c)));assert "torch" not in sys.modules'
    args=[sys.executable,'-I','-S','-B','-c',boot,str(ROOT),str(Path(jsonschema.__file__).parents[1]),str(script),str(tmp_path/'config.json')]
    r=subprocess.run(args,cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    fact=json.loads(r.stdout);assert fact['consumer_version']=='submit-effect-bridge/0.3.0'
    assert all(Path(v['origin']).is_relative_to(tmp_path/'consumer') for v in fact['modules'])
    (tmp_path/'consumer/analysis/cupti_timeline.py').write_text('raise RuntimeError("must not import tampered code")')
    r=subprocess.run(args,cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode!=0 and b'CONSUMER_FILE' in r.stderr and b'must not import tampered code' not in r.stderr
    (tmp_path/'consumer/analysis/cupti_timeline.py').write_bytes((ROOT/'analysis/cupti_timeline.py').read_bytes())
    # An already loaded old reader must not be silently replaced or accepted.
    blocked=boot.replace('m=runpy.run_path',
        'import exposedpath_v141.submit_effect_bridge;m=runpy.run_path')
    args[args.index(boot)]=blocked
    r=subprocess.run(args,cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode!=0 and b'MODULE_ALREADY_LOADED' in r.stderr


@pytest.mark.parametrize('failure',[False,True])
def test_1024_control_to_actual_isolated_consumer_and_final_archive(tmp_path,monkeypatch,failure):
    """Only the external model and static hardware boundary are doubles."""
    import jsonschema
    from shutil import copyfile
    b=load('cupti_timeline_b');package=tmp_path/'p';package.mkdir()
    ar=tmp_path/'a';(ar/'build').mkdir(parents=True);er=tmp_path/'event';(er/'probe/review').mkdir(parents=True)
    for n in ('receipt.json','artifact_manifest.json','source_bytes.json','build/build.json'):put(ar/n,dict(CPU_REFERENCE_DOUBLE=True))
    for n in ('receipt.json','artifact_manifest.json','probe/review/review.json'):put(er/n,dict(CPU_REFERENCE_DOUBLE=True))
    support=load('memset_micro');mc=contract();mc['run_id']='r'
    c=dict(schema_version='cupti-timeline-stage-b/0.2.0',controller_commit='a'*40,analysis_commit='a'*40,
        native_commit=mc['native_commit'],activity_policy_version=mc['activity_policy_version'],
        server_root=str(tmp_path/'YLQ'),code_root=str(ROOT),python=sys.executable,target_python=sys.executable,
        site_root=str(Path(jsonschema.__file__).parents[1]),a_root=str(ar),event_root=str(er),
        reviewed_a_receipt_sha256='a'*64,reviewed_event_receipt_sha256='b'*64,budget=b.fixed_budget(),
        run_id='r',session_id='test',model='CPU_MODEL_NOT_LOADED',inventory_sha256='i'*64,
        gpu_uuid='CPU_GPU_NOT_QUERIED',gpu_pci='CPU_GPU_NOT_QUERIED',expected_token_ids=[[17],[18]],
        client=dict(path='CPU_DLL_NOT_LOADED',sha256='d'*64),cupti=dict(path='CPU_DLL_NOT_LOADED',sha256='e'*64),
        model_contract=mc,**{k:mc[k] for k in ('consumer_version','timing_policy','driver_query_policy','runtime_query_policy')})
    reference=tmp_path/'reference';_,ref=finite_files(reference)
    c.update(input_identity=ref['input_identity'],prompt_sha256=ref['prompt_sha256'])
    copyfile(reference/'input_1024.json',package/'input_1024.json')
    for n in ('cupti_timeline_b.py','cupti_timeline_model.py','cupti_model_consumer.py','run_cupti_timeline_b.ps1'):copyfile(ROOT/'scripts'/n,package/n)
    files=['exposedpath_v141/cupti_driver_queries.py','scripts/analyze_completion_operation_candidate.py',
        'exposedpath_v141/submit_effect_bridge.py','analysis/cupti_timeline.py']
    for n in files:
        p=package/'consumer'/n;p.parent.mkdir(parents=True,exist_ok=True);copyfile(ROOT/n,p)
    c['consumer_files']=[dict(path=n,bytes=(ROOT/n).stat().st_size,sha256=sha(ROOT/n)) for n in files]
    put(package/'delivery.json',c)
    put(package/'package_manifest.json',dict(files=[dict(path=p.relative_to(package).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in package.rglob('*') if p.is_file()]))
    calls=[];checks=[]
    def checked(*args):
        checks.append('A_EVENT');return dict(a_root=ar,acfg={},verification=dict(mode='CPU_A_EVENT_DOUBLE'))
    def command(argv,cwd,log,**kw):
        calls.append(dict(name=Path(log).name,timeout=kw['timeout'],argv=argv))
        if Path(log).name=='one_model':
            folder=Path(cwd)/'model';_,fc=finite_files(folder)
            # Bind the same generated configuration that the real producer receives.
            ledger=json.loads((folder/'producer/pass_identity.json').read_text());ledger['wmpc_manifest_sha256']=sha(Path(cwd)/'model_config.json');put(folder/'producer/pass_identity.json',ledger)
            pr=json.loads((folder/'producer/producer_receipt.json').read_text());pr['files']['pass_identity.json'].update(sha256=sha(folder/'producer/pass_identity.json'),size_bytes=(folder/'producer/pass_identity.json').stat().st_size);put(folder/'producer/producer_receipt.json',pr)
            r=json.loads((folder/'model_result.json').read_text());r['config_sha256']=sha(Path(cwd)/'model_config.json');r['producer_receipt_sha256']=sha(folder/'producer/producer_receipt.json');put(folder/'model_result.json',r)
            if failure:
                raw=json.loads((folder/'timeline/capture.json').read_text());raw['records']=[v for v in raw['records'] if v['kind']!='MEMSET'];put(folder/'timeline/capture.json',raw)
                sr=json.loads((folder/'timeline/receipt.json').read_text());sr['capture_sha256']=sha(folder/'timeline/capture.json');put(folder/'timeline/receipt.json',sr)
                r.update(capture_sha256=sha(folder/'timeline/capture.json'),session_receipt_sha256=sha(folder/'timeline/receipt.json'));put(folder/'model_result.json',r)
            proc=dict(pid=7,status='EXITED',exit_code=0,timed_out=False)
        else:
            run=subprocess.run(argv,cwd=cwd,env=kw['env'],capture_output=True,timeout=20)
            Path(log).with_suffix('.stdout').write_bytes(run.stdout);Path(log).with_suffix('.stderr').write_bytes(run.stderr)
            proc=dict(pid=99,status='EXITED',exit_code=run.returncode,timed_out=False)
        put(Path(log).with_suffix('.process.json'),proc)
        if proc['exit_code']:raise ValueError('CPU_REAL_CONSUMER_EXIT:'+str(proc['exit_code']))
        return proc
    support.command=command
    monkeypatch.setattr(b,'components',lambda *a:({'startup_resources':lambda out,archive,cfg:dict(required=cfg['temporary_required_bytes'],CPU_RESOURCE_DOUBLE=True)},support))
    monkeypatch.setattr(b,'checked_a',checked)
    monkeypatch.setattr(b,'sys',SimpleNamespace(executable=sys.executable,version_info=(3,11,16)))
    for k in ('CUDA_INJECTION64_PATH','NVTX_INJECTION64_PATH','NV_COMPUTE_PROFILER_INJECTION_PATH'):monkeypatch.delenv(k,raising=False)
    assert b.run(package,enabled=True,reviewed='a'*64,reviewed_event='b'*64)==(2 if failure else 0)
    assert checks==['A_EVENT','A_EVENT']
    assert [(r['name'],r['timeout']) for r in calls]==[('one_model',300),('same_run_analysis',180)]
    assert '-I' in calls[0]['argv'] and '-S' in calls[1]['argv']
    with zipfile.ZipFile(next((tmp_path/'YLQ/transfer').glob('*.zip'))) as z:
        r=json.loads(z.read('receipt.json'));report=json.loads(z.read('model/analysis_report.json'))
        assert r['analysis_commit']=='a'*40 and r['native_commit']==mc['native_commit']
        assert r['post_execution_static_rechecked'] is True and r['analysis_process']['exit_code']==int(failure)
        assert report['status']==('BLOCKED' if failure else 'BOTH_TOKENS_EVIDENCE_COMPLETE_PENDING_REVIEW')
        assert 'model/consumer_binding.json' in z.namelist() and 'delivery/consumer/analysis/cupti_timeline.py' in z.namelist()
        if not failure:assert [v['result']['coe_ns'] for v in report['token_results']]==[20,1]
