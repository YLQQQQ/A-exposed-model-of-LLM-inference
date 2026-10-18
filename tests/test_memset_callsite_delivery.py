"""Real file/entry checks with explicit CPU boundaries, no target CUDA claims."""
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import os

import pytest


def stage_api():
    assert importlib.util.find_spec('scripts.memset_callsite_stage'), 'missing stage entry'
    from scripts import memset_callsite_stage
    return memset_callsite_stage


def test_unreviewed_b_and_unaccepted_sampling_risk_stop_before_target(tmp_path):
    m=stage_api()
    with pytest.raises(ValueError,match='REVIEWED_STATIC'):
        m.review_static(tmp_path,None,{'execution_commit':'a'*40},'b'*64)
    with pytest.raises(ValueError,match='SAMPLING_RISK'):
        m.validate_b_opt_in('a'*64,False)


@pytest.mark.parametrize('collect',[False,True])
def test_real_ps51_default_a_or_explicit_b(tmp_path,collect):
    m=stage_api();root=Path(__file__).resolve().parents[1]
    launcher=tmp_path/'run_memset_callsite.ps1';launcher.write_bytes((root/'scripts/run_memset_callsite.ps1').read_bytes())
    driver=tmp_path/'memset_callsite_stage.py'
    driver.write_text('import sys,json\nfrom pathlib import Path\nPath(sys.argv[2]).joinpath("argv.json").write_text(json.dumps(sys.argv[1:]))\n')
    from scripts.memset_micro import write,sha
    write(tmp_path/'delivery.json',dict(python=sys.executable,bootstrap_sha256=sha(driver)))
    args=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(launcher)]
    if collect:args+=['-CollectReviewed1024Sources','-ReviewedStaticReceiptSHA256','a'*64,'-AcceptReviewedSamplingRisk']
    env=os.environ.copy();env['PSModulePath']=str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/Modules')
    r=subprocess.run(args,capture_output=True,timeout=30,env=env)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    actual=json.loads((tmp_path/'argv.json').read_text())
    assert actual[0]==('stage-b' if collect else 'stage-a')
    assert ('--accept-reviewed-sampling-risk' in actual)==collect


def test_profile_flags_added_only_to_diagnostic_collector_not_legacy():
    m=stage_api()
    from exposedpath import memset_callsite as c
    from scripts.gate8_diagnostic_collect import profile_argv
    assert '--cudabacktrace=all:0' in c.PROFILE_FLAGS
    # Independent legacy behavior is covered by its existing argv tests; the
    # new collector must not monkeypatch a global profile_argv implementation.
    assert profile_argv.__module__=='scripts.gate8_diagnostic_collect'


def test_legacy_collector_refuses_source_only_manifest(tmp_path,monkeypatch):
    from scripts import gate8_diagnostic_collect as legacy
    from exposedpath import memset_callsite as c,gate8_isolated_preflight as i
    p=tmp_path/'prepared';p.mkdir();i.write_new(p/'manifest.json',c.minimal_fields(c.binding('cpu','a'*40)))
    monkeypatch.setattr(legacy,'target_argv',lambda *a:['CPU_NO_MODEL'])
    with pytest.raises(ValueError,match='SOURCE_ONLY'):legacy.profile_argv('CPU_NSYS','CPU_PYTHON',p,tmp_path/'out')


@pytest.mark.parametrize('failure',[None,'profile','analysis'])
def test_collection_actual_controller_retains_failure_without_retry(tmp_path,monkeypatch,failure):
    assert importlib.util.find_spec('scripts.memset_callsite_collect'), 'missing bounded collector'
    from scripts import memset_callsite_collect as m,gate8_diagnostic_collect as legacy
    from exposedpath import memset_callsite as c,gate8_isolated_preflight as isolated,observation_preparation as p
    from exposedpath_v141 import gate8_target_python as target
    from scripts import gate7_nsys_postprocess as post
    from analysis import memset_callsite as reader
    calls=[];prepared=tmp_path/'prepared';prepared.mkdir();out=tmp_path/'capture'
    b=c.binding('cpu-diagnostic','a'*40)
    isolated.write_new(prepared/'manifest.json',{**c.minimal_fields(b),'target_python':{},'isolated_preflight_version':isolated.VERSION})
    monkeypatch.setattr(p,'validate_prepared',lambda *a:calls.append('CPU_PREPARED_VALIDATION'))
    monkeypatch.setattr(target,'validate_probe',lambda _:dict(requested_executable=str(Path(sys.executable).resolve()),environment=target.environment()))
    def seal(*a):
        path=out/'auxiliary_preflight.json';isolated.write_new(path,{});calls.append('CPU_SEAL_BOUNDARY');return path
    monkeypatch.setattr(isolated,'seal',seal);monkeypatch.setattr(isolated,'finalize',lambda *a:calls.append('CPU_FINALIZE_BOUNDARY'))
    monkeypatch.setattr(m,'bind_capture',lambda *a:calls.append('CPU_TARGET_TRACE_BINDING_BOUNDARY'))
    monkeypatch.setattr(c,'profile_argv',lambda *a:['CPU_NOT_NSYS','profile','--cudabacktrace=all:0'])
    def run(argv,path,**kw):
        calls.append('ONE_PROFILE_CPU_BOUNDARY');assert kw['timeout_seconds']==300
        if failure=='profile':return dict(status='BLOCKED',exit_code=1,timed_out=False)
        (out/'diagnostic-entry').mkdir();(out/'diagnostic').mkdir()
        isolated.write_new(out/'diagnostic-entry/started.json',dict(status='STARTED',pid=123))
        isolated.write_new(out/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=0,pid=123))
        isolated.write_new(out/'diagnostic/diagnostic_report.json',dict(status='DIAGNOSTIC_COMPLETE',qualification='NOT_QUALIFIED',scientific_outputs_allowed=False))
        (out/'capture.nsys-rep').write_bytes(b'CPU_REP_BOUNDARY')
        return dict(status='COMPLETE',exit_code=0,timed_out=False)
    monkeypatch.setattr(legacy,'run_once',run)
    def export(**kw):
        calls.append('ONE_EXPORT_CPU_BOUNDARY');assert kw['max_attempts']==1
        Path(kw['canonical_path']).write_bytes(b'CPU_SQLITE_BOUNDARY');return dict(status='PASS')
    monkeypatch.setattr(post,'run_postprocess',export)
    def analyze(*args):
        calls.append('CPU_SOURCE_QUERY_BOUNDARY');p=out/'analyzed';p.mkdir()
        isolated.write_new(p/'sources.json',dict(status='INCONCLUSIVE' if failure=='analysis' else 'CALLSITE_LOCATED',
            token_ids=[[29184],[6556]],parameter_evidence=False));return p/'sources.json'
    monkeypatch.setattr(reader,'process',analyze)
    r=m.collect('CPU_NOT_NSYS',sys.executable,prepared,out,Path(__file__).resolve().parents[1])
    assert calls.count('ONE_PROFILE_CPU_BOUNDARY')==1
    assert r['status']==('CALLSITE_LOCATED_STOP_FOR_REVIEW' if failure is None else 'BLOCKED')
    assert (out/'collection_report.json').is_file() and r['scientific_outputs_allowed'] is False
    assert r['parameter_evidence'] is False
    closure=isolated.read(out/'target_closure.process.json')
    assert closure['descendant_exit_status']==('UNKNOWN_STOP_AND_INSPECT_NO_RETRY' if failure=='profile' else 'TARGET_EXIT_OBSERVED')


def test_target_manifest_must_equal_prepared_bytes_before_source_query(tmp_path):
    from scripts import memset_callsite_collect as m
    prepared=tmp_path/'prepared';prepared.mkdir();out=tmp_path/'capture';(out/'diagnostic').mkdir(parents=True)
    (prepared/'manifest.json').write_bytes(b'{"role":"EXPECTED"}')
    (out/'diagnostic/manifest.json').write_bytes(b'{"role":"WRONG"}')
    with pytest.raises(ValueError,match='PREPARED_TARGET_BYTES'):m.bind_capture(prepared,out)


@pytest.mark.parametrize('failure',[None,'cpu','capability'])
def test_real_stage_a_files_receipt_and_zip_with_explicit_os_command_doubles(tmp_path,monkeypatch,failure):
    """Real controller, manifest and ZIP. Git/NSys/OS/pytest are CPU doubles."""
    import hashlib
    from scripts import memset_micro as common,coe_startup_storage as storage
    m=stage_api();server=tmp_path/'YLQ';(server/'transfer').mkdir(parents=True)
    code=tmp_path/'code';code.mkdir();(code/'cpu.py').write_bytes(b'CPU identity')
    tool=tmp_path/'CPU_NOT_NSYS.exe';tool.write_bytes(b'CPU file identity, never executed')
    package=tmp_path/'package';package.mkdir()
    for n in ('memset_callsite_stage.py','run_memset_callsite.ps1','prerequisite_reference.json'):
        (package/n).write_bytes(b'CPU_PACKAGE_BOUNDARY')
    cfg=dict(schema_version='memset-callsite-delivery/0.1.0',server_root=str(server),code_root=str(code),
        execution_commit='a'*40,analysis_commit='a'*40,prerequisite='b'*40,model_process_budget=1,profile_budget=1,
        source_representations={'cpu.py':[dict(bytes=12,sha256=common.sha(code/'cpu.py'))]},
        python=sys.executable,cpu_tests=['CPU_TEST_BOUNDARY'],cpu_test_count=1,
        nsys=str(tool),nsys_sha256=common.sha(tool))
    common.write(package/'delivery.json',cfg)
    rows=[dict(path=p.name,bytes=p.stat().st_size,sha256=common.sha(p)) for p in package.iterdir()]
    common.write(package/'package_manifest.json',dict(files=rows))
    calls=[]
    monkeypatch.setattr(m.sys,'version_info',(3,11,16))
    monkeypatch.setattr(common,'deploy',lambda *a:calls.append('CPU_GIT_DEPLOY_BOUNDARY'))
    monkeypatch.setattr(common,'tree',lambda *a:None)
    monkeypatch.setattr(storage,'check',lambda *a:dict(status='STARTUP_RESOURCES_READY',historical_ylq_total_bytes=None))
    def cap(cfg,out):
        common.write(out/'capability.json',dict(administrator=failure!='capability',actual_capture_coverage='NOT_RUN'))
        if failure=='capability':raise ValueError('CPU_CAPABILITY_BOUNDARY_FAILURE')
    monkeypatch.setattr(m,'capability',cap)
    def cmd(argv,cwd,log,**kw):
        assert kw['env']['CUDA_VISIBLE_DEVICES']=='-1'
        calls.append('CPU_COMMAND_BOUNDARY')
        if 'pytest' in argv:
            out=Path(argv[argv.index('--junitxml')+1])
            out.write_text('<testsuites><testsuite tests="1" failures="'+('1' if failure=='cpu' else '0')+'" errors="0" skipped="0"/></testsuites>')
    monkeypatch.setattr(common,'command',cmd)
    assert m.stage(package,'A')==(0 if failure is None else 2)
    root=server/'diagnostics'/('memset_callsite_'+('a'*12)+'_static')
    assert (server/'transfer'/('memset_callsite_'+('a'*12)+'_static.zip')).is_file()
    receipt=json.loads((root/'receipt.json').read_text())
    assert receipt['stage_a_cuda_initializations']==0 and receipt['parameter_evidence'] is False
    if failure is None:
        reviewed=common.sha(root/'receipt.json');index=common.sha(package/'package_manifest.json')
        assert m.review_static(root,reviewed,cfg,index)['status']=='STATIC_READY_FOR_REVIEW'
        (root/'source_bytes.json').write_bytes(b'changed')
        with pytest.raises(ValueError,match='STATIC_FILE_CHANGED'):m.review_static(root,reviewed,cfg,index)
    else:assert receipt['status']=='BLOCKED' and receipt['error']


def test_actual_1024_prepare_seal_consume_and_source_profile_boundary(tmp_path,monkeypatch):
    import csv,sysconfig
    from types import SimpleNamespace
    from exposedpath import gate8_diagnostic as entry,platform_adapter,gate8_isolated_preflight as isolated,memset_callsite as c
    from exposedpath_v141 import gate8_source_probe
    from scripts import memset_callsite_collect as collector,gate8_diagnostic_collect as legacy
    from test_gate8_identity import write_json,sha
    b=c.binding('cpu-callsite','a'*40)
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3');monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(platform_adapter,'git',lambda args,**kw:'' if 'status' in args else 'a'*40)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'3, GPU-12345678-1234-1234-1234-123456789abc, 00000000:01:00.0')
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')))
    model=tmp_path/'model';model.mkdir();write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    inventory=tmp_path/'inventory.csv'
    with inventory.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['RelativePath','Bytes','SHA256']);w.writeheader()
        w.writerow(dict(RelativePath='config.json',Bytes=(model/'config.json').stat().st_size,SHA256=sha(model/'config.json')))
    prompt=write_json(tmp_path/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='CPU',fixed_input_tokens=1024,
        samples=[dict(sample_index=0,input_ids=[7]*1024,attention_mask=[1]*1024)]))
    prepared=entry.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,inventory_path=inventory,
        inventory_sha256=sha(inventory),prompt_path=prompt,prompt_sha256=sha(prompt),expected_commit='a'*40,
        physical_gpu=3,engineering_attention_backend='sdpa',target_python=sys._base_executable,
        site_root=sysconfig.get_path('purelib'),batch_binding=b)
    assert isolated.read(prepared/'manifest.json')['run_role']=='ENGINEERING'
    root=tmp_path/'repo';(root/'.git').mkdir(parents=True);(root/'.git/HEAD').write_text('a'*40)
    files=('exposedpath/runner.py','exposedpath/observation_preparation.py')
    real=Path(__file__).resolve().parents[1]
    for p in files:
        dest=root/p;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((real/p).read_bytes())
    monkeypatch.setattr(platform_adapter,'run_tool',lambda tool,args,**kw:subprocess.CompletedProcess(args,0,
        ('\0'.join(files)+'\0').encode() if '--cached' in args else b'',b''))
    out=tmp_path/'collection';calls=[]
    def stop_at_profile(argv,*args,**kw):
        calls.append(argv)
        assert '--cudabacktrace=all:0' in argv and '--sample=process-tree' in argv and 'model-run' in argv
        assert '--sample=none' not in argv and kw['timeout_seconds']==300
        sealed=isolated.read(out/'auxiliary_preflight.json')
        claim=isolated.consume(receipt=out/'auxiliary_preflight.json',expected_sha=sha(out/'auxiliary_preflight.json'),
            nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==b['run_id']
        return dict(status='BLOCKED',exit_code=1,timed_out=False,reason='CPU_STOP_BEFORE_REAL_MODEL_OR_CUDA')
    monkeypatch.setattr(legacy,'run_once',stop_at_profile)
    assert collector.collect('CPU_NOT_NSYS',sys._base_executable,prepared,out,root)['status']=='BLOCKED'
    assert len(calls)==1
