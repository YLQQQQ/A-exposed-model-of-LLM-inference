"""Bounded controller/report CPU tests, never target collection evidence."""
import importlib.util
import pytest


def api():
    assert importlib.util.find_spec('scripts.batch_load_diagnostic'), 'missing actual bounded entry'
    from scripts import batch_load_diagnostic
    return batch_load_diagnostic


def test_controller_requires_explicit_collection_and_fixed_budget():
    with pytest.raises(ValueError,match='OPT_IN'):
        api().run({},'unused',execute=False)


@pytest.mark.parametrize('damage',['sync','copy','source'])
def test_report_never_infers_necessary_activity_from_overlap(damage):
    # Report data comes from the admitted dependency membership, not API overlap.
    a=dict(record_id='s',runtime_record_id='api-s',start_ns=22,end_ns=29)
    rows={'cuda_sync':[a], 'cuda_api':[dict(record_id='api-s',api_name='cudaStreamSynchronize_v3020',
        start_ns=20,end_ns=30,correlation_id=5,thread_id=7)],
        'device_activity':[dict(record_id='copy',start_ns=11,end_ns=18,activity_kind='MEMCPY')],
        'nvtx':[]}
    proof=dict(sync_id='s',suffix_activity_ids=['copy'],scope='A_INTERSECTION_ONLY_NOT_PHYSICAL_W')
    if damage=='sync': rows['cuda_sync']=[]
    if damage=='copy': proof['suffix_activity_ids']=['not-observed']
    if damage=='source': rows['cuda_api']=[]
    with pytest.raises(ValueError): api().sync_evidence(rows,proof)


def test_sync_report_separates_host_api_activity_and_supported_wait():
    rows={'cuda_sync':[dict(record_id='s',runtime_record_id='api',start_ns=22,end_ns=29)],
        'cuda_api':[dict(record_id='api',api_name='cudaStreamSynchronize_v3020',start_ns=20,end_ns=30,
            correlation_id=5,thread_id=7)],
        'device_activity':[dict(record_id='copy',start_ns=11,end_ns=18,activity_kind='MEMCPY')], 'nvtx':[]}
    value=api().sync_evidence(rows,dict(sync_id='s',suffix_activity_ids=['copy'],scope='A_INTERSECTION_ONLY_NOT_PHYSICAL_W'))
    assert value['host_api_duration_ns']==10 and value['last_necessary_activity_end_ns']==18
    assert value['supported_device_wait_union_ns']==0
    assert value['internal_api_wait']=='NOT_IDENTIFIABLE_NOT_SPLIT'


def test_report_consumes_real_producer_canonical_dependency_proofs(tmp_path,monkeypatch):
    from test_batch_load_diagnostic import binding,api as contract
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain
    from exposedpath.gate8_isolated_preflight import write_new,sha
    contract()
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=binding())
    result=process_domain(receipt,execution,tmp_path/'analyzed')
    # Inputs from the CPU Raw fixture reside at root, matching real collector names.
    __import__('shutil').copyfile(receipt,tmp_path/'input_receipt.json')
    __import__('shutil').copyfile(tmp_path/'trace.sqlite',tmp_path/'capture.sqlite')
    write_new(tmp_path/'collection_report.json',dict(error=None,result_sha256=sha(result)))
    value=api().report_profile(tmp_path)
    assert len(value['windows'])==3 and len(value['synchronization'])==2
    for w in value['windows']:
        n=2 if w['phase']=='full_request' else 1
        assert w['a']['A_cuda_api_ns']==30*n and w['activity_cost']['gpu_activity']['union_ns']==6*n
        assert len(w['d2h_activities'])==n and w['activity_cost']['driver_api']['count'] is None
        assert w['activity_cost']['driver_api']['status']=='NOT_COLLECTED_UNKNOWN'
    assert all(s['supported_device_wait_union_ns']==0 and s['host_api_duration_ns']==10 for s in value['synchronization'])
    assert value['measurement_validity']=='NOT_ASSESSED'


def test_delivery_default_does_not_collect_and_ps51_parses():
    import subprocess
    from pathlib import Path
    root=Path(__file__).resolve().parents[1];script=root/'scripts/run_batch_load_engineering.ps1'
    text=script.read_text(encoding='utf-8')
    assert text.startswith('param([switch]$CollectReviewedEngineering)')
    assert 'if (!$CollectReviewedEngineering)' in text and "CUDA_VISIBLE_DEVICES='-1'" in text
    assert "CUDA_VISIBLE_DEVICES='3'" in text and '--execute-reviewed-engineering-batch' in text
    # CPU negative fixtures must not be confused with real recorded writers by packing.
    assert "('diagnostics\\batch_load_'" in text and "'--basetemp',$CpuTemp" in text
    if __import__('os').name=='nt':
        code="$T=$null;$E=$null;[System.Management.Automation.Language.Parser]::ParseFile($env:BATCH_LOAD_PARSE_FILE,[ref]$T,[ref]$E)|Out-Null;if($E.Count){$E|ForEach-Object{Write-Output $_.Message};exit 1}"
        # Windows PowerShell 5.1 parsing only; do not execute the server script.
        env=dict(__import__('os').environ,BATCH_LOAD_PARSE_FILE=str(script))
        result=subprocess.run(['powershell.exe','-NoProfile','-Command',code],capture_output=True,timeout=20,env=env)
        assert result.returncode==0,result.stdout+result.stderr


@pytest.mark.parametrize('fail_pair',[False,True,'profile_rejected'])
def test_actual_controller_wiring_has_four_slots_and_stops_on_pair_failure(tmp_path,monkeypatch,fail_pair):
    from exposedpath import batch_load,platform_adapter,gate8_diagnostic
    from exposedpath.gate8_isolated_preflight import write_new,sha
    from scripts import gate8_pair,gate8_diagnostic_collect
    m=api();nsys=tmp_path/'nsys';nsys.write_bytes(b'CPU tool stand-in')
    seed=tmp_path/'seed.json';write_new(seed,dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='synthetic',
        fixed_input_tokens=512,samples=[dict(sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    uuid='GPU-12345678-1234-1234-1234-123456789abc'
    config=dict(schema_version='batch-load-delivery/0.1',model_process_budget=4,profile_budget=2,commit='d'*40,
        batch_id='cpu-batch',seed_input=str(seed),prompt_512_sha256=sha(seed),nsys=str(nsys),nsys_sha256=sha(nsys),
        model='unused',inventory='unused',inventory_sha256='0'*64,target_python='direct-python',
        site_root='explicit-site',code_root=str(m.ROOT),gpu_uuid=uuid,gpu_pci_bus_id='0000:01:00.0')
    monkeypatch.setattr(platform_adapter,'git',lambda a:'d'*40 if a[-1]=='HEAD' else '')
    observed=[]
    def prepare(**kw):
        b=kw['batch_binding'];observed.append((b['condition'],b['pass_id']))
        path=kw['output_dir'];path.mkdir()
        write_new(path/'manifest.json',dict(batch_load=b,gpu_uuid=uuid,gpu_pci_bus_id='0000:01:00.0'))
        return path
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',prepare)
    monkeypatch.setattr(gate8_pair,'baseline',lambda *a:dict(status='BASELINE_COMPLETE_NOT_ACCEPTANCE'))
    def profile(argv,path,**kw):
        assert '--execute-engineering-diagnostic' in argv and '--engineering-a-only' in argv
        assert 'direct-python' in argv and kw['timeout_seconds']==900
        out=__import__('pathlib').Path(argv[argv.index('--output')+1]);out.mkdir()
        rejected=fail_pair=='profile_rejected'
        write_new(out/'collection_report.json',dict(status='DIAGNOSTIC_COLLECTED_NOT_QUALIFIED' if rejected else 'A_SCOPE_ENGINEERING_ONLY',
            error='MODEL_A_SCOPE_BLOCKED' if rejected else None,
            **({'analysis_rejection':dict(version='model-scope-rejection/0.1.0',requests=[dict(
                reasons=['ENGINEERING_SCOPE_SUBMIT_MAPPING'])])} if rejected else {})))
        return dict(status='COMPLETE')
    monkeypatch.setattr(gate8_diagnostic_collect,'run_once',profile)
    def pair(*a):
        if fail_pair:raise ValueError('per-sample token mismatch')
        return {p:dict(timing_ns=dict(full_request=100,prefill=60,decode=40)) for p in ('pass0','pass1')}
    monkeypatch.setattr(gate8_pair,'summarize',pair)
    monkeypatch.setattr(m,'report_profile',lambda p:dict(role='Engineering'))
    result=m.run(config,tmp_path/'out',execute=True)
    if fail_pair:
        assert observed==[('B1','pass0'),('B1','pass1')]
        assert result['status']=='BLOCKED' and result['runs'][2]['status']=='NOT_RUN'
        assert not (tmp_path/'out/comparison.json').exists()
        if fail_pair=='profile_rejected':
            assert 'ENGINEERING_SCOPE_SUBMIT_MAPPING' in result['runs'][1]['error']
            assert 'MODEL_A_SCOPE_BLOCKED' in result['runs'][1]['error']
    else:
        assert observed==[('B1','pass0'),('B1','pass1'),('B4','pass0'),('B4','pass1')]
        assert result['status']=='BATCH_COMPLETE_STOP_FOR_REVIEW'
