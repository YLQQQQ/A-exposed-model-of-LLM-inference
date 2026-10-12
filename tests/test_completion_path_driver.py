"""Bounded delivery orchestration, CPU substitutes only."""
import json
from pathlib import Path
import os
import subprocess
import pytest


@pytest.mark.parametrize('fail',[False,True,'token'])
def test_real_two_slot_driver_stops_without_retry(tmp_path,monkeypatch,fail):
    from scripts import completion_path_diagnostic as m,gate8_diagnostic_collect as collector
    from exposedpath import completion_path as c,gate8_diagnostic,platform_adapter
    from exposedpath.gate8_isolated_preflight import write_new,sha
    from exposedpath_v141 import completion_path_scope
    seed=tmp_path/'seed.json';write_new(seed,dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='cpu',
        fixed_input_tokens=512,samples=[dict(sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    nsys=tmp_path/'nsys';nsys.write_bytes(b'CPU STAND-IN')
    config=dict(schema_version='completion-path-delivery/0.1',model_process_budget=2,profile_budget=2,
        commit='d'*40,batch_id='cpu-completion',seed_input=str(seed),prompt_512_sha256=sha(seed),
        nsys=str(nsys),nsys_sha256=sha(nsys),model='unused',inventory='unused',inventory_sha256='0'*64,
        target_python='direct-python',site_root='explicit-site',code_root=str(m.ROOT),
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='0000:01:00.0')
    monkeypatch.setattr(platform_adapter,'git',lambda argv:'d'*40 if 'rev-parse' in argv else '')
    seen=[]
    def prepare(**kw):
        b=kw['completion_binding'];seen.append(b['variant'])
        assert kw['batch_binding']==c.batch_binding(b)
        p=kw['output_dir'];p.mkdir();write_new(p/'manifest.json',dict(c.minimal_fields(b),
            gpu_uuid=config['gpu_uuid'],gpu_pci_bus_id=config['gpu_pci_bus_id']))
        return p
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',prepare)
    def collect(argv,p,**kw):
        assert '--engineering-a-only' in argv and 'direct-python' in argv and kw['timeout_seconds']==900
        out=Path(argv[argv.index('--output')+1]);(out/'analyzed').mkdir(parents=True);(out/'diagnostic').mkdir()
        write_new(out/'analyzed/prefill.json',{})
        write_new(out/'diagnostic/batch_tokens.json',dict(requests=[dict(token_ids=[[13]*4,[14 if not(fail=='token' and len(seen)==2) else 15]*4])]))
        write_new(out/'collection_report.json',dict(status='BLOCKED' if fail is True else 'PREFILL_LOCAL_ENGINEERING_ONLY',
            error='unbounded diagnostic' if fail is True else None,result_filename='prefill.json',result_sha256=sha(out/'analyzed/prefill.json')))
        return dict(status='COMPLETE',exit_code=0,timed_out=False)
    monkeypatch.setattr(collector,'run_once',collect)
    a=dict(T_window_ns=50,A_cuda_api_ns=30,A_device_wait_ns=0,A_sync_residual_ns=10,A_unattributed_ns=0,A_host_path_ns=10)
    monkeypatch.setattr(completion_path_scope,'load',lambda *args:dict(status='PREFILL_LOCAL_ENGINEERING_ONLY',
        prefill={'a_records':[a]},timeline={},full_pre_sync_dependencies=[],decode_unresolved_effects=[],
        request_status='NOT_ACCEPTED',decode_status='NOT_ACCEPTED'))
    result=m.run(config,tmp_path/'experiment',execute=True)
    assert seen==(['C0'] if fail is True else ['C0','Cpre'])
    assert result['status']==('BATCH_COMPLETE_STOP_FOR_REVIEW' if fail is False else 'BLOCKED')
    assert result['automatic_retry'] is False
    assert (tmp_path/'experiment/comparison.json').exists()==(fail is False)


def test_collection_requires_opt_in():
    from scripts.completion_path_diagnostic import run
    with pytest.raises(ValueError,match='OPT_IN'):run({},'unused')


def test_ps51_parse_and_default_cpu_boundary():
    script=Path(__file__).resolve().parents[1]/'scripts/run_completion_path_engineering.ps1'
    text=script.read_text(encoding='utf-8')
    assert text.startswith('param([switch]$CollectReviewedEngineering)')
    assert "CUDA_VISIBLE_DEVICES='-1'" in text and '--execute-reviewed-completion-path' in text
    assert '$BR.runs.Count -ne 2' in text and 'model_process_budget=2' in text
    if os.name=='nt':
        code='$T=$null;$E=$null;[System.Management.Automation.Language.Parser]::ParseFile($env:COMPLETION_PARSE_FILE,[ref]$T,[ref]$E)|Out-Null;if($E.Count){exit 1}'
        p=subprocess.run(['powershell.exe','-NoProfile','-Command',code],capture_output=True,timeout=20,
            env=dict(os.environ,COMPLETION_PARSE_FILE=str(script)))
        assert p.returncode==0,p.stdout+p.stderr
