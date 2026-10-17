"""Stage A/B guards. CPU boundaries only, never Nsight/model execution."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
import pytest


def api():
    assert importlib.util.find_spec('scripts.memset_prefill_stage'),'missing real stage entry'
    from scripts import memset_prefill_stage
    return memset_prefill_stage


def test_unreviewed_b_is_refused_before_any_target_action(tmp_path):
    m=api()
    with pytest.raises(ValueError,match='REVIEWED_STATIC'):
        m.review_static(tmp_path,None,dict(execution_commit='a'*40),'b'*64)


def test_nested_plain_process_json_unknown_writer_cannot_be_packed(tmp_path):
    m=api();out=tmp_path/'evidence';leaf=out/'collection/analyzed_parameters_driver';leaf.mkdir(parents=True)
    (leaf/'process.json').write_text(json.dumps(dict(status='BLOCKED',descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY')))
    assert hasattr(m,'verified_pack'),'missing nested process quiescence guard'
    with pytest.raises(ValueError,match='UNKNOWN_WRITER'):m.verified_pack(out,tmp_path/'return.zip')
    assert not (tmp_path/'return.zip').exists() and (leaf/'process.json').is_file()


@pytest.mark.parametrize('collect',[False,True])
def test_ps51_actual_switch_dispatch_is_cpu_only(tmp_path,collect):
    m=api();root=Path(__file__).resolve().parents[1]
    ps=tmp_path/'run.ps1';ps.write_bytes((root/'scripts/run_memset_prefill.ps1').read_bytes())
    driver=tmp_path/'memset_prefill_stage.py'
    driver.write_text('import sys,json\nfrom pathlib import Path\nPath(sys.argv[2]).joinpath("argv.json").write_text(json.dumps(sys.argv[1:]))\n')
    from scripts.memset_micro import sha,write
    write(tmp_path/'delivery.json',dict(python=sys.executable,bootstrap_sha256=sha(driver)))
    argv=['powershell.exe','-NoProfile','-ExecutionPolicy','Bypass','-File',str(ps)]
    if collect:argv+=['-CollectReviewedB2','-ReviewedStaticReceiptSHA256','a'*64]
    env=os.environ.copy();env['PSModulePath']=str(Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/Modules')
    run=subprocess.run(argv,capture_output=True,timeout=30,env=env)
    assert run.returncode==0,run.stderr.decode(errors='replace')
    a=json.loads((tmp_path/'argv.json').read_text())
    assert a[0]==('stage-b' if collect else 'stage-a')
    if collect:assert a[-2:]==['--reviewed-static-sha256','a'*64]


def test_wrong_software_and_unknown_zero_device_record_stay_blocked():
    from exposedpath import memset_prefill as c
    from analysis.memset_prefill import coverage
    from tests.test_memset_prefill import evidence
    with pytest.raises(ValueError,match='TARGET_SOFTWARE'):c.validate_target_software({},dict(required_software={}))
    side,raw,expected=evidence();raw['effects']=[dict(kind='MEMSET',pid=12,correlation_id=51,bytes=0)]
    with pytest.raises(ValueError,match='ZERO_DEVICE_RECORD_UNSUPPORTED'):coverage(side,raw,expected)


def test_process_creation_instance_is_actual_cpu_os_query():
    import os
    if os.name!='nt':pytest.skip('Windows only; no Linux adapter claim')
    from exposedpath.memset_prefill import creation_filetime
    a=creation_filetime();b=creation_filetime()
    assert type(a) is int and a>0 and a==b


@pytest.mark.parametrize('failure',[False,True])
def test_actual_model_entry_records_instance_or_stops_before_model(tmp_path,monkeypatch,failure):
    from exposedpath import memset_prefill as c,gate8_diagnostic
    from exposedpath_v141 import gate8_target_python as target
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps(dict(batch_load=dict(version=c.VERSION))))
    monkeypatch.setattr(sys,'argv',['entry','model-run','--output-dir',str(tmp_path/'diagnostic'),'--manifest-path',str(manifest)])
    calls=[];monkeypatch.setattr(gate8_diagnostic,'main',lambda:calls.append('CPU_MODEL_BOUNDARY') or 0)
    if failure:
        def bad():raise OSError('CPU_INSTANCE_UNAVAILABLE')
        monkeypatch.setattr(c,'creation_filetime',bad)
        with pytest.raises(OSError,match='CPU_INSTANCE_UNAVAILABLE'):target.main()
        assert not calls
    else:assert target.main()==0 and calls==['CPU_MODEL_BOUNDARY']
    started=json.loads((tmp_path/'diagnostic-entry/started.json').read_text())
    exited=json.loads((tmp_path/'diagnostic-entry/exit.json').read_text())
    assert exited['exit_code']==(1 if failure else 0)
    if not failure:assert started['creation_filetime']==exited['creation_filetime']==c.creation_filetime()


@pytest.mark.parametrize('state',['ready','low','unknown'])
def test_fresh_space_is_distinct_from_unknown_historical_total(tmp_path,monkeypatch,state):
    from types import SimpleNamespace
    from scripts import coe_startup_storage as storage
    m=api();out=tmp_path/'out';out.mkdir()
    monkeypatch.setenv('TEMP',str(out));monkeypatch.setenv('TMP',str(out));monkeypatch.delenv('TMPDIR',raising=False)
    seen=[];monkeypatch.setattr(storage,'volume_identity',lambda _: 'ONE_VOLUME')
    def usage(path):
        seen.append(path)
        if state=='unknown':raise OSError('CPU_SPACE_QUERY_FAILURE')
        return SimpleNamespace(free=3*2**30 if state=='ready' else 1)
    monkeypatch.setattr(m.shutil,'disk_usage',usage)
    v=m.resources(out,tmp_path/'new.zip')
    assert len(seen)==1 and v['historical_ylq_total_bytes'] is None
    assert v['status']==('STARTUP_RESOURCES_READY' if state=='ready' else 'STARTUP_RESOURCES_BLOCKED')
    if state!='ready':assert v['errors']


@pytest.mark.parametrize('failure',[None,'token','driver'])
def test_one_new_b2_uses_verified_entry_and_never_retries(tmp_path,monkeypatch,failure):
    from scripts import memset_micro as common,gate8_diagnostic_collect as collector
    from exposedpath import gate8_diagnostic as entry
    m=api();package=tmp_path/'pkg';package.mkdir();static=tmp_path/'static';(static/'build').mkdir(parents=True)
    runtime=tmp_path/'cpu_runtime.dll';runtime.write_bytes(b'CPU runtime file only')
    rec=static/'build/recorder.dll';rec.write_bytes(b'CPU BUILD BOUNDARY')
    common.write(static/'build/build.json',dict(recorder=str(rec),binary_files=[dict(path=rec.name,bytes=rec.stat().st_size,sha256=common.sha(rec))]))
    common.write(static/'runtime_file.json',common.file_fact(runtime))
    prompt=dict(fixed_input_tokens=512,samples=[dict(sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)])
    common.write(package/'input_b1.json',prompt);(package/'model_inventory.csv').write_bytes(b'CPU inventory')
    nsys=tmp_path/'CPU_NOT_NSYS.exe';nsys.write_bytes(b'NEVER EXECUTED')
    cfg=dict(code_root=str(tmp_path),python=sys.executable,run_id='a'*32,execution_commit='d'*40,
        runtime_path=str(runtime),runtime_expected_sha256=common.sha(runtime),nsys=str(nsys),nsys_sha256=common.sha(nsys),
        input_seed_sha256=common.sha(package/'input_b1.json'),model='CPU_MODEL',inventory_sha256='e'*64,
        target_python='CPU_TARGET_PYTHON',site_root='CPU_SITE',expected_token_ids=[[13,13],[14,14]],
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='00000000:01:00.0')
    monkeypatch.setattr(common,'runtime_fact',lambda p:common.file_fact(p))
    calls=[]
    def prepare(**kw):
        p=json.loads(Path(kw['prompt_path']).read_text());assert len(p['samples'])==2
        assert [s['sample_index'] for s in p['samples']]==[0,1] and p['samples'][0]['input_ids']==p['samples'][1]['input_ids']
        assert kw['batch_binding']['purpose']=='PREFILL_PARAMETERS_ONLY_NOT_PILOT'
        out=Path(kw['output_dir']);out.mkdir();common.write(out/'manifest.json',dict(gpu_uuid=cfg['gpu_uuid'],gpu_pci_bus_id=cfg['gpu_pci_bus_id']))
        calls.append('VERIFIED_PREPARE_CPU_BOUNDARY');return out
    monkeypatch.setattr(entry,'prepare_diagnostic',prepare)
    def run(argv,output,**kw):
        calls.append('SINGLE_COLLECTOR_CPU_BOUNDARY')
        assert '--memset-prefill-parameters' in argv and '--pilot' not in argv and kw['timeout_seconds']==900
        if failure=='driver':return dict(status='BLOCKED',exit_code=1,timed_out=False)
        out=Path(argv[argv.index('--output')+1]);(out/'analyzed').mkdir(parents=True);(out/'diagnostic').mkdir()
        common.write(out/'analyzed/parameters.json',dict(role='CPU_CONSUMER_BOUNDARY_NOT_EVIDENCE'))
        common.write(out/'collection_report.json',dict(schema_version='memset-prefill-collection/0.1.0',
            status='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW',export_status='PASS',result_sha256=common.sha(out/'analyzed/parameters.json')))
        common.write(out/'diagnostic/batch_tokens.json',dict(requests=[dict(token_ids=[[13,13],[14,15]] if failure=='token' else cfg['expected_token_ids'])]))
        return dict(status='COMPLETE',exit_code=0,timed_out=False)
    monkeypatch.setattr(collector,'run_once',run)
    out=tmp_path/'new_once';out.mkdir()
    if failure:
        with pytest.raises(ValueError,match='TOKEN_REFERENCE_CONFLICT' if failure=='token' else 'ONE_B2_DRIVER_FAILED'):
            m.collect(cfg,package,static,out)
    else:assert m.collect(cfg,package,static,out)['status']=='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW'
    assert calls==['VERIFIED_PREPARE_CPU_BOUNDARY','SINGLE_COLLECTOR_CPU_BOUNDARY']


@pytest.mark.parametrize('failure',[None,'cpu','source','version','runtime'])
def test_actual_stage_a_to_archive_with_explicit_build_git_cpu_boundaries(tmp_path,monkeypatch,failure):
    """Real controller/files/pack; Git, PE and build/pytest execution are doubles.

    Native compile/Detours and real pytest results have separate tests. This
    fixture cannot be used as a target static receipt or a CUDA qualification.
    """
    import zipfile
    import hashlib
    from scripts import memset_micro as common,memset_prefill_native as native
    m=api();server=tmp_path/'YLQ';(server/'transfer').mkdir(parents=True)
    code=tmp_path/'code';code.mkdir();(code/'cpu.py').write_bytes(b'unchanged CPU source')
    (code/'exposedpath').mkdir()
    (code/'exposedpath/runner.py').write_bytes((Path(__file__).resolve().parents[1]/'exposedpath/runner.py').read_bytes())
    rt=tmp_path/'cpu_runtime.dll';rt.write_bytes(b'PE BOUNDARY DOUBLE')
    tool=tmp_path/'cpu_cl.exe';tool.write_bytes(b'NEVER EXECUTED')
    package=tmp_path/'package';package.mkdir()
    def put(n,data):
        (package/n).write_bytes(data)
    for n in ('memset_prefill_stage.py','run_memset_prefill.ps1','prerequisite_reference.json'):put(n,b'CPU PACKAGE DOUBLE')
    for n,member in [('detours.zip','Detours-c/src/a.h'),('nvtx.zip','NVTX-c/c/include/a.h'),('sdk.zip','include/a.h')]:
        with zipfile.ZipFile(package/n,'w') as z:z.writestr(member,b'CPU HEADER DOUBLE')
    cfg=dict(schema_version='memset-prefill-delivery/0.1.0',execution_commit='a'*40,analysis_commit='a'*40,
        prerequisite='b'*40,server_root=str(server),code_root=str(code),model_process_budget=1,profile_budget=1,
        python_version=list(sys.version_info[:3]),python=sys.executable,toolchain_files={'cl':common.file_fact(tool)},
        sources=[dict(path='cpu.py',bytes=20,sha256=common.sha(code/'cpu.py'))],
        runtime_path=str(rt),runtime_expected_sha256=common.sha(rt),build={},detours_directory='Detours-c',nvtx_directory='NVTX-c',
        cpu_tests=['tests/test_memset_prefill.py'],cpu_test_count=1)
    if failure=='source':cfg['sources'][0]['sha256']='0'*64
    if failure=='version':cfg['python_version']=[1,2,3]
    if failure=='runtime':cfg['runtime_expected_sha256']='0'*64
    common.write(package/'delivery.json',cfg)
    files=[dict(path=p.name,bytes=p.stat().st_size,sha256=common.sha(p)) for p in package.iterdir()]
    common.write(package/'package_manifest.json',dict(files=files))
    actions=[]
    monkeypatch.setattr(common,'deploy',lambda cfg,p,o:actions.append('GIT_DEPLOY_DOUBLE'))
    monkeypatch.setattr(common,'tree',lambda cfg,target:actions.append('GIT_TREE_DOUBLE'))
    monkeypatch.setattr(common,'runtime_fact',lambda p:common.file_fact(p))
    monkeypatch.setattr(m,'resources',lambda o,a:dict(status='STARTUP_RESOURCES_READY',role='CPU_VOLUME_DOUBLE'))
    def build(config,out):
        out.mkdir();(out/'recorder.dll').write_bytes(b'HOST BUILD DOUBLE')
        value=dict(binary_files=[dict(path='recorder.dll',bytes=17,sha256=common.sha(out/'recorder.dll'))],recorder=str(out/'recorder.dll'))
        common.write(out/'build.json',value);actions.append('NATIVE_BUILD_DOUBLE');return value
    monkeypatch.setattr(native,'build',build)
    def command(argv,cwd,log,**kw):
        assert argv[1:4]==['-X','utf8','-m'] and argv[4]=='pytest'
        actions.append('PYTEST_BOUNDARY_DOUBLE')
        if failure=='cpu':raise ValueError('EXACT_CPU_FAILURE_STOP')
        xml=Path(argv[argv.index('--junitxml')+1]);xml.write_text('<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>')
    monkeypatch.setattr(common,'command',command)
    monkeypatch.setattr(m,'collect',lambda *a:pytest.fail('A must never call collection'))
    code_value=m.stage(package,'A');out=server/'diagnostics'/('memset_prefill_'+'a'*12+'_static')
    receipt=json.loads((out/'receipt.json').read_text())
    assert code_value==(2 if failure else 0)
    assert receipt['status']==('BLOCKED' if failure else 'STATIC_READY_FOR_REVIEW')
    assert receipt['model_process_budget']==receipt['profile_budget']==receipt['stage_a_cuda_programs_executed']==0
    archive=server/'transfer'/('memset_prefill_'+'a'*12+'_static.zip')
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        index=json.loads(z.read('artifact_manifest.json'))
        assert {r['path'] for r in index['files']}|{'artifact_manifest.json'}==set(z.namelist())
        assert all(hashlib.sha256(z.read(r['path'])).hexdigest()==r['sha256'] for r in index['files'])
    if failure=='cpu':assert receipt['error']=='ValueError:EXACT_CPU_FAILURE_STOP'
