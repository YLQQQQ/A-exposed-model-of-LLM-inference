"""Real producer/Raw adapter/file consumers; OS, CUDA and model are CPU doubles."""
import json
import os
import sys
import sysconfig
from pathlib import Path
import pytest
from test_gate8_identity import write_json,sha
from exposedpath import gate11_pilot as pilot


def pair_files(tmp_path,monkeypatch,condition='N16',bindings=None,shared_model=None):
    import test_n1_model_domain as fixture
    from exposedpath_v141 import gate8_target_python as target
    from exposedpath_v141.gate9_domain import process_domain
    contract=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    rows=bindings if bindings is not None else [r for r in pilot.schedule('file-batch') if r['condition']==condition and r['block']==1]
    output=[]
    for binding in rows:
        folder=tmp_path/binding['pass_id']; folder.mkdir()
        with monkeypatch.context() as m:
            original=fixture.entry_source
            def entry_source(*args,**kwargs):
                entry,opts,state,events=original(*args,**kwargs)
                value=json.loads(opts['manifest_path'].read_text()); value['target_python']=contract
                if shared_model is not None:value['model_id']=str(shared_model)
                if condition=='G512':
                    model=shared_model if shared_model is not None else tmp_path/'cpu_model';model.mkdir(exist_ok=True)
                    write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=1024))
                    prompt=json.loads(opts['prompt_path'].read_text());prompt['fixed_input_tokens']=512
                    prompt['samples']=[dict(input_ids=[1]*512,attention_mask=[1]*512)]
                    write_json(opts['prompt_path'],prompt)
                    value.update(model_id=str(model),prompt_tokens_sha256=sha(opts['prompt_path']))
                write_json(opts['manifest_path'],value)
                m.setattr(target,'current',lambda _:dict(pid=os.getpid(),parent_pid=os.getppid(),snapshot=contract['actual']['snapshot']))
                return entry,opts,state,events
            m.setattr(fixture,'entry_source',entry_source)
            formal=binding['version']=='G12-FORMAL-ENVELOPE/0.1'
            options={'formal_binding' if formal else 'pilot_binding':binding}
            receipt,execution,calls=fixture.source(folder,m,binding['variant'] or 'V0',**options)
            if receipt is not None:
                path=process_domain(receipt,execution,folder/'analyzed',**(dict(bridge_path=calls) if binding['variant'] else {}))
                # The common collection adapter uses this fixed receipt name.
                (folder/'input_receipt.json').write_bytes(receipt.read_bytes())
                actual=json.loads((folder/'diagnostic/manifest.json').read_text()).get('formal',binding)
                report=dict(status='FORMAL_RUN_COMPLETE_PENDING_REVIEW' if formal else 'PILOT_RUN_COMPLETE_PENDING_REVIEW',
                    **{('formal' if formal else 'pilot'):actual},
                    collection={'status':'COMPLETE'},export_status='PASS',error=None,result_sha256=sha(path))
                write_json(folder/'collection_report.json',report)
            else:
                actual=json.loads((folder/'diagnostic/manifest.json').read_text()).get('formal',binding)
                write_json(folder/'baseline_report.json',dict(status='BASELINE_COMPLETE_NOT_ACCEPTANCE',
                    **{('formal' if formal else 'pilot'):actual},role='UNPROFILED_LIMITED_FORMAL' if formal else 'UNPROFILED_LIMITED_PILOT'))
        root=folder/'diagnostic'; manifest=json.loads((root/'manifest.json').read_text())
        (folder/'diagnostic-entry').mkdir()
        write_json(folder/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=0,pid=os.getpid()))
        sealed=dict(run_id=manifest['run_id'],nonce=binding['run_id'],input_hashes={
            'manifest.json':sha(root/'manifest.json'),'prompt.json':sha(root/'prompt.json')})
        write_json(folder/'auxiliary_preflight.json',sealed)
        claim=dict(target_pid=os.getpid(),nonce=sealed['nonce'],preflight_sha256=sha(folder/'auxiliary_preflight.json'))
        write_json(folder/'auxiliary_preflight.claim.json',claim); write_json(root/'isolated_preflight_target.json',claim)
        write_json(folder/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=sha(folder/'auxiliary_preflight.json'),target_claim_sha256=sha(folder/'auxiliary_preflight.claim.json')))
        output.append(dict(binding=binding,output=str(folder)))
    return output


@pytest.mark.parametrize('condition',['G32','G512','N0','Nm','N16'])
def test_real_pilot_pair_file_consumer(tmp_path,monkeypatch,condition):
    from scripts.gate11_pilot_batch import summarize_pair
    rows=pair_files(tmp_path,monkeypatch,condition)
    result=summarize_pair(*rows,tmp_path)
    assert result['status']=='PAIR_COMPLETE_PENDING_REVIEW'
    assert result['token_ids']==[[13],[14]] and result['data_role']=='Pilot'
    assert result['gate11_verdict']=='NOT_RUN' and not result['formal_eligible']
    for v in result['overhead'].values(): assert v['delta_ns']==v['pass1_ns']-v['pass0_ns']


@pytest.mark.parametrize('damage',['token','role','variant','pass','input','entry','partial','budget_order'])
def test_pilot_pair_rejects_wrong_evidence_even_if_count_matches(tmp_path,monkeypatch,damage):
    from scripts.gate11_pilot_batch import summarize_pair
    rows=pair_files(tmp_path,monkeypatch,'N16'); root=Path(rows[0]['output'])/'diagnostic'
    if damage=='budget_order': rows.reverse()
    elif damage=='partial': (root/'producer/drain_ledger.json').unlink()
    elif damage=='entry': write_json(root.parent/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=1,pid=os.getpid()))
    elif damage=='token':
        tokens=json.loads((root/'pilot_tokens.json').read_text()); tokens['requests'][0]['token_ids'][1]=[99]
        write_json(root/'pilot_tokens.json',tokens)
        # Rehash local token claims; N1 actual observed values must still match.
        for name in ('engineering_execution.json','diagnostic_report.json'):
            x=json.loads((root/name).read_text()); x['pilot_tokens_sha256']=sha(root/'pilot_tokens.json'); write_json(root/name,x)
    else:
        m=json.loads((root/'manifest.json').read_text())
        if damage=='role': m['data_role']='Engineering'
        if damage=='variant': m['n1_model']['variant']='V0'
        if damage=='pass': m['pilot']['pass_id']='pass1' if m['pilot']['pass_id']=='pass0' else 'pass0'
        if damage=='input': m['prompt_tokens_sha256']='0'*64
        write_json(root/'manifest.json',m)
    with pytest.raises((ValueError,FileNotFoundError)):
        summarize_pair(*rows,tmp_path)


def test_pilot_receipt_token_artifact_must_be_execution_bound_file(tmp_path,monkeypatch):
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain
    b=next(r for r in pilot.schedule('token-source') if r['condition']=='N0' and r['pass_id']=='pass1')
    receipt,execution,calls=source(tmp_path,monkeypatch,'V0',pilot_binding=b)
    value=json.loads(receipt.read_text()); entry=value['artifacts']['pilot_tokens']
    foreign=tmp_path/'unbound_tokens.json'
    foreign.write_bytes((execution.parent/'pilot_tokens.json').read_bytes())
    altered=json.loads(foreign.read_text());altered['requests'][0]['token_ids'][1]=[98]
    write_json(foreign,altered)
    entry.update(filename=foreign.name,sha256=sha(foreign),size_bytes=foreign.stat().st_size)
    write_json(receipt,value)
    with pytest.raises(ValueError,match='TOKEN'):
        process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)


@pytest.mark.parametrize('condition',['G32','N0','Nm','N16'])
def test_actual_pilot_seal_and_target_claim_before_profile_cpu_stop(tmp_path,monkeypatch,condition):
    import subprocess
    from test_n1_preprofile_identity import prepared_case
    from scripts import gate8_diagnostic_collect as collector
    from exposedpath import gate8_isolated_preflight as isolated
    from scripts.gate7_smoke_validation import validate_pre_model_identity
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    b=next(r for r in pilot.schedule('seal') if r['condition']==condition and r['pass_id']=='pass1')
    if not b['variant']: m.pop('n1_model');m.pop('n1_model_execution')
    m.update(pilot.minimal_fields(b));write_json(prepared/'manifest.json',m)
    assert validate_pre_model_identity(prepared/'manifest.json',prepared/'preflight.json',root)
    nsys=tmp_path/'nsys.exe'; nsys.touch(); out=tmp_path/'collection'
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(out),'--execute-engineering-diagnostic','--engineering-domain','--pilot'])
    monkeypatch.setattr(collector.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    def stop(argv,*a,**kw):
        assert argv[1]=='profile' and 'model-run' in argv
        receipt=out/'auxiliary_preflight.json'; sealed=isolated.read(receipt)
        claim=isolated.consume(receipt=receipt,expected_sha=sha(receipt),nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==b['run_id']
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_PROFILE')
    monkeypatch.setattr(collector,'run_once',stop)
    assert collector.main()==1
    assert isolated.read(out/'collection_report.json')['pilot']==b


@pytest.mark.parametrize('damage',['role','variant','mask','dirty','pass'])
def test_pilot_preprofile_dispatch_is_closed(tmp_path,monkeypatch,damage):
    from test_n1_preprofile_identity import prepared_case
    from exposedpath import gate8_isolated_preflight as isolated
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    b=next(r for r in pilot.schedule('seal') if r['condition']=='N16' and r['pass_id']=='pass1')
    m.update(pilot.minimal_fields(b))
    if damage=='role': m['data_role']='Engineering'
    if damage=='variant': m['n1_model']['variant']='V0'
    if damage=='mask': monkeypatch.setenv('CUDA_VISIBLE_DEVICES','0')
    if damage=='dirty': m['runner_git_dirty']=True
    if damage=='pass': m['pilot']['pass_id']='future'
    write_json(prepared/'manifest.json',m); out=tmp_path/'out';out.mkdir()
    with pytest.raises(ValueError): isolated.seal(prepared,out,root)
