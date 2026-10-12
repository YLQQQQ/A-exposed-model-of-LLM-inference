"""Bounded delivery orchestration, CPU substitutes only."""
import json
from pathlib import Path
import os
import subprocess
import pytest


@pytest.mark.parametrize('fail',[False,True,'token'])
@pytest.mark.parametrize('remaining',[False,True])
def test_real_two_slot_driver_stops_without_retry(tmp_path,monkeypatch,fail,remaining):
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
    from scripts import completion_path_reference
    common={k:'cpu' for k in completion_path_reference.COMMON_FIELDS}
    def fake_manifest(b):
        return dict(common,**c.minimal_fields(b),gpu_uuid=config['gpu_uuid'],gpu_pci_bus_id=config['gpu_pci_bus_id'],
            runner_git_commit='d'*40,runner_git_dirty=False)
    if remaining:
        config.update(schema_version='completion-path-remaining-delivery/0.1',model_process_budget=1,profile_budget=1,
            reference_output=str(tmp_path/'historical_reference'))
        old=c.schedule('cpu-original')[0]
        def reference(config,output,code_root):
            assert code_root==m.ROOT
            # Historical process.json must not enter the new live writer tree.
            assert output==tmp_path/'historical_reference'
            target=tmp_path/'old';(target/'analyzed').mkdir(parents=True);write_new(target/'analyzed/prefill.json',{'cpu':'old'})
            return dict(binding=old,prefill={'a_records':[a]},timeline={},full_pre_sync_dependencies=[],decode_unresolved_effects=[]),[[13]*4,[14]*4],fake_manifest(old),target
        monkeypatch.setattr(completion_path_reference,'review_reference',reference)
    seen=[]
    def prepare(**kw):
        b=kw['completion_binding'];seen.append(b['variant'])
        assert kw['batch_binding']==c.batch_binding(b)
        p=kw['output_dir'];p.mkdir();write_new(p/'manifest.json',fake_manifest(b))
        return p
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',prepare)
    def collect(argv,p,**kw):
        assert '--engineering-a-only' in argv and 'direct-python' in argv and kw['timeout_seconds']==900
        out=Path(argv[argv.index('--output')+1]);(out/'analyzed').mkdir(parents=True);(out/'diagnostic').mkdir()
        write_new(out/'analyzed/prefill.json',{})
        prepared=Path(argv[argv.index('--prepared')+1]);write_new(out/'diagnostic/manifest.json',json.loads((prepared/'manifest.json').read_text()))
        write_new(out/'diagnostic/target_runtime.json',{'cpu':'stand-in'});write_new(out/'target_launch.json',{'cpu':'stand-in'})
        write_new(out/'diagnostic/batch_tokens.json',dict(requests=[dict(token_ids=[[13]*4,[14 if not(fail=='token' and (remaining or len(seen)==2)) else 15]*4])]))
        # The real 0.1.0 collector omits error on success (sealed C0 regression).
        report=dict(status='BLOCKED' if fail is True else 'PREFILL_LOCAL_ENGINEERING_ONLY',
            schema_version='gate8-qwen-engineering-collection/0.1.0',qualification='NOT_QUALIFIED',gate8_verdict='NOT_RUN',
            scientific_outputs_allowed=False,collection=dict(status='COMPLETE',exit_code=0,timed_out=False),export_status='PASS',
            q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
            result_filename='prefill.json',result_sha256=sha(out/'analyzed/prefill.json'),
            manifest_sha256=sha(out/'diagnostic/manifest.json'),target_runtime_sha256=sha(out/'diagnostic/target_runtime.json'),
            target_launch_sha256=sha(out/'target_launch.json'))
        if fail is True:report['error']='unbounded diagnostic'
        write_new(out/'collection_report.json',report)
        return dict(status='COMPLETE',exit_code=0,timed_out=False)
    monkeypatch.setattr(collector,'run_once',collect)
    a=dict(T_window_ns=50,A_cuda_api_ns=30,A_device_wait_ns=0,A_sync_residual_ns=10,A_unattributed_ns=0,A_host_path_ns=10)
    monkeypatch.setattr(completion_path_scope,'load',lambda path,*args:dict(status='PREFILL_LOCAL_ENGINEERING_ONLY',
        binding=json.loads((path.parent.parent/'diagnostic/manifest.json').read_text())['completion_path'],
        prefill={'a_records':[a]},timeline={},full_pre_sync_dependencies=[],decode_unresolved_effects=[],
        request_status='NOT_ACCEPTED_LOCAL_REVIEW_ONLY',decode_status='NOT_ACCEPTED_LOCAL_REVIEW_ONLY'))
    result=m.run(config,tmp_path/'experiment',execute=True)
    assert seen==(['Cpre'] if remaining else ['C0'] if fail is True else ['C0','Cpre'])
    assert result['status']==('BATCH_COMPLETE_STOP_FOR_REVIEW' if fail is False else 'BLOCKED')
    assert result['automatic_retry'] is False
    assert (tmp_path/'experiment/comparison.json').exists()==(fail is False)
    if remaining:
        assert len(result['runs'])==1 and result['runs'][0]['binding']['variant']=='Cpre'
        assert result['model_process_budget']==result['profile_budget']==1


def test_collection_requires_opt_in():
    from scripts.completion_path_diagnostic import run
    with pytest.raises(ValueError,match='OPT_IN'):run({},'unused')


def test_bad_c0_reference_stops_before_any_prepare_or_profile(tmp_path,monkeypatch):
    from scripts import completion_path_diagnostic as m,completion_path_reference as reference
    from exposedpath import platform_adapter,gate8_diagnostic
    from exposedpath.gate8_isolated_preflight import write_new,sha
    seed=tmp_path/'seed.json';write_new(seed,dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='cpu',
        fixed_input_tokens=512,samples=[dict(sample_index=0,input_ids=[7]*512,attention_mask=[1]*512)]))
    nsys=tmp_path/'collector';nsys.write_bytes(b'CPU STAND-IN')
    config=dict(schema_version='completion-path-remaining-delivery/0.1',model_process_budget=1,profile_budget=1,
        commit='d'*40,seed_input=str(seed),prompt_512_sha256=sha(seed),nsys=str(nsys),nsys_sha256=sha(nsys),
        reference_output=str(tmp_path/'historical_reference'))
    monkeypatch.setattr(platform_adapter,'git',lambda args:'d'*40 if 'rev-parse' in args else '')
    def rejected(*args):raise ValueError('REFERENCE_SOURCE_BINDING')
    def forbidden(**kw):pytest.fail('Reference rejection must precede model prepare')
    monkeypatch.setattr(reference,'review_reference',rejected)
    monkeypatch.setattr(gate8_diagnostic,'prepare_diagnostic',forbidden)
    with pytest.raises(ValueError,match='REFERENCE_SOURCE_BINDING'):m.run(config,tmp_path/'new',execute=True)
    assert not (tmp_path/'new/batch').exists()


def test_ps51_parse_and_default_cpu_boundary():
    script=Path(__file__).resolve().parents[1]/'scripts/run_completion_path_engineering.ps1'
    text=script.read_text(encoding='utf-8')
    assert text.startswith('param([switch]$CollectReviewedEngineering)')
    assert "CUDA_VISIBLE_DEVICES='-1'" in text and '--execute-reviewed-completion-path' in text
    assert '$BR.runs.Count -ne 2' in text and '$BR.runs.Count -ne 1' in text
    if os.name=='nt':
        code='$T=$null;$E=$null;[System.Management.Automation.Language.Parser]::ParseFile($env:COMPLETION_PARSE_FILE,[ref]$T,[ref]$E)|Out-Null;if($E.Count){exit 1}'
        p=subprocess.run(['powershell.exe','-NoProfile','-Command',code],capture_output=True,timeout=20,
            env=dict(os.environ,COMPLETION_PARSE_FILE=str(script)))
        assert p.returncode==0,p.stdout+p.stderr


@pytest.mark.parametrize('schema,budget',[('completion-path-remaining-delivery/0.1',2),('completion-path-delivery/0.1',1),('future',1)])
def test_real_ps_entry_rejects_wrong_closed_budget_before_tools(tmp_path,schema,budget):
    if os.name!='nt':pytest.skip('PowerShell5.1 entry is Windows-specific')
    import shutil
    src=Path(__file__).resolve().parents[1]/'scripts/run_completion_path_engineering.ps1'
    script=tmp_path/'entry.ps1';shutil.copyfile(src,script)
    (tmp_path/'delivery.json').write_text(json.dumps(dict(schema_version=schema,model_process_budget=budget,profile_budget=budget)))
    p=subprocess.run(['powershell.exe','-NoProfile','-File',str(script)],capture_output=True,timeout=20)
    assert p.returncode!=0 and b'Closed Engineering delivery conflict' in p.stdout+p.stderr
    assert set(p.name for p in tmp_path.iterdir())=={'entry.ps1','delivery.json'}
