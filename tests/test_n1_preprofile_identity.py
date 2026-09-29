"""Prepared-file -> real seal -> real collector argv. External tools are CPU doubles.

Identity declarations below reproduce the c6cdb36 prepared V0 (private paths,
GPU identity, runtime snapshot and hashes rebound to temporary CPU inputs).
No sealed validator, receipt or profile-argv function is mocked.
"""
import json
import subprocess
import sys
import sysconfig
from pathlib import Path

import pytest

from exposedpath import gate8_isolated_preflight as isolated, platform_adapter
from exposedpath_v141 import gate8_target_python as target
from scripts import gate8_diagnostic_collect as collector
from scripts.gate7_smoke_validation import validate_pre_model_identity


def prepared_case(tmp_path, monkeypatch, variant='V0'):
    root=tmp_path/'repo'; (root/'.git').mkdir(parents=True)
    (root/'.git/HEAD').write_text('a'*40)
    (root/'exposedpath').mkdir(); (root/'exposedpath/runner.py').write_text('# CPU source\n')
    prepared=tmp_path/'prepared'; prepared.mkdir()
    prompt=dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='cpu',fixed_input_tokens=32,
                samples=[dict(input_ids=[1]*32,attention_mask=[1]*32)])
    isolated.write_new(prepared/'prompt.json',prompt)
    (prepared/'model_inventory.csv').write_text('CPU inventory\n')
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID'); monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    probe=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    manifest=dict(run_id='cpu-prepared-run',runner_git_commit='a'*40,runner_git_dirty=False,
        gpu=3,gpu_index=3,gpu_index_physical=3,gpu_index_logical=0,
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='00000000:01:00.0',
        data_role='Engineering',run_role='ENGINEERING',study_mode='N1_INTERVENTION',
        isolated_preflight_version='exposedpath-isolated-preflight/0.1.0',target_python=probe,
        fixed_input_tokens=32,fixed_output_tokens=2,batch_size=1,warmup_count=1,repeat_count=1,
        execution_mode='eager',attention_backend='sdpa',dtype_and_quantization='fp16',sampling_config={'do_sample':False},
        prompt_tokens_sha256=isolated.sha(prepared/'prompt.json'),runner_source_sha256=isolated.sha(root/'exposedpath/runner.py'),
        engineering_scope=dict(profile='TARGET_SCOPE_ENGINEERING_SUFFICIENCY/0.1',attention_backend='sdpa',
            declaration_role='PRE_EXECUTION',assumptions=['NO_USER_CONCURRENCY','NO_EXPLICIT_IPC_OR_EVENT_DEPENDENCY','NO_UNRECORDED_INCOMING_DEPENDENCY']),
        domain_qualification=dict(contract='G9-DOMAIN-QUALIFICATION/0.1.0',declaration_role='PRE_EXECUTION',profile='N1_EXPLICIT_STREAM_AB/0.1.0'),
        n1_intervention=dict(callsite_id='qwen2.decode.layer_16.after_forward',intervention_variant_id=variant,sync_origin='n1_intervention'),
        n1_model=dict(schema_version='exposedpath-n1-model-calls/0.1.0',variant=variant,
            protocol_variant='V16' if variant=='Vsync' else variant,callsite_id='qwen2.decode.layer_16.after_forward',
            declaration_role='PRE_EXECUTION',frequency='ONCE_PER_DECODE_FORWARD',layer_index=15,phase='decode',
            qualification='NOT_ASSESSED',stream_policy='HELD_EXPLICIT_NONBLOCKING'),
        n1_model_execution=dict(version='N1-VERIFIED-MODEL/0.1',anchor='CURRENT_STREAM_SYNC_BEFORE_FINAL_DRAIN',
            batch_size=1,input_tokens=32,output_tokens=2,repeat_count=1,warmup_count=1,
            warmup_stream='SEPARATE_HELD_EXPLICIT',measured_stream='FRESH_HELD_EXPLICIT_AFTER_WARMUP'))
    isolated.write_new(prepared/'manifest.json',manifest)
    isolated.write_new(prepared/'preflight.json',dict(gpu_uuid=manifest['gpu_uuid'],gpu_pci_bus_id=manifest['gpu_pci_bus_id'],
        physical_gpu_index=3,logical_gpu_index=0))
    monkeypatch.setattr(platform_adapter,'git',lambda args,**kw:'a'*40 if 'rev-parse' in args else '')
    def binary_git(tool,args,**kw):
        assert tool==platform_adapter.TOOL_GIT and 'ls-files' in args and kw['text'] is False
        return subprocess.CompletedProcess(args,0,b'exposedpath/runner.py\0' if '--cached' in args else b'',b'')
    monkeypatch.setattr(platform_adapter,'run_tool',binary_git)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:
        '3, GPU-12345678-1234-1234-1234-123456789abc, 00000000:01:00.0')
    return root,prepared,manifest


@pytest.mark.parametrize('variant',['V0','Vmarker','Vsync'])
def test_real_seal_and_collector_reach_profile_boundary_with_n1(tmp_path,monkeypatch,variant):
    root,prepared,manifest=prepared_case(tmp_path,monkeypatch,variant)
    # The historical Gate7 caller must remain G1-only.
    assert 'Gate7 Engineering/G1 identity conflicts' in validate_pre_model_identity(
        prepared/'manifest.json',prepared/'preflight.json',root)
    nsys=tmp_path/'nsys.exe'; nsys.touch(); output=tmp_path/'collection'
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(output),'--execute-engineering-diagnostic','--engineering-domain'])
    def version(argv,**kw):
        assert argv==[str(nsys),'--version']
        return subprocess.CompletedProcess(argv,0,'NVIDIA Nsight Systems version 2026.2.1.210-262137639646v0','')
    monkeypatch.setattr(collector.subprocess,'run',version)
    def profile_boundary(argv,*args,**kw):
        assert argv[1]=='profile' and 'model-run' in argv
        assert str(Path(sys._base_executable).resolve()) in argv
        assert '--auxiliary-receipt' in argv and '--launch-nonce' in argv
        receipt=output/'auxiliary_preflight.json'; sealed=isolated.read(receipt)
        # Exercise the target's next receipt gate without loading any model.
        claim=isolated.consume(receipt=receipt,expected_sha=isolated.sha(receipt),nonce=sealed['nonce'],
            prepared=prepared,output=output,root=root)
        assert claim['run_id']==manifest['run_id']
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_REAL_PROFILE')
    monkeypatch.setattr(collector,'run_once',profile_boundary)
    assert collector.main()==1
    assert isolated.read(output/'auxiliary_preflight.claim.json')['run_id']=='cpu-prepared-run'
    assert isolated.read(output/'collection_report.json')['collection']['reason']=='CPU_STOP_BEFORE_REAL_PROFILE'


@pytest.mark.parametrize('damage',['domain','mode','variant','public-variant','callsite','missing-policy',
    'future-version','count','backend','input-length','output-length','prompt-hash','prompt-length','source-hash',
    'dirty','commit','gpu','mask'])
def test_invalid_n1_cannot_be_sealed(tmp_path,monkeypatch,damage):
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    if damage=='domain': m['domain_qualification']['profile']='G1_NATURAL_PROJECTED_A/0.1.0'
    elif damage=='mode': m['study_mode']='G1_NATURAL'
    elif damage=='variant': m['n1_intervention']['intervention_variant_id']='Vsync'
    elif damage=='public-variant': m['n1_model']['protocol_variant']='V16'
    elif damage=='callsite': m['n1_model']['layer_index']=14
    elif damage=='missing-policy': del m['n1_model']
    elif damage=='future-version': m['n1_model_execution']['version']='future'
    elif damage=='count': m['repeat_count']=2
    elif damage=='backend': m['attention_backend']='eager'
    elif damage=='input-length': m['fixed_input_tokens']=128
    elif damage=='output-length': m['fixed_output_tokens']=3
    elif damage=='prompt-hash': m['prompt_tokens_sha256']='0'*64
    elif damage=='prompt-length':
        p=isolated.read(prepared/'prompt.json'); p['fixed_input_tokens']=31
        (prepared/'prompt.json').write_text(json.dumps(p)); m['prompt_tokens_sha256']=isolated.sha(prepared/'prompt.json')
    elif damage=='source-hash': m['runner_source_sha256']='0'*64
    elif damage=='dirty': m['runner_git_dirty']=True
    elif damage=='commit': m['runner_git_commit']='b'*40
    elif damage=='gpu': m['gpu_uuid']='GPU-00000000-0000-0000-0000-000000000000'
    elif damage=='mask': monkeypatch.setenv('CUDA_VISIBLE_DEVICES','2')
    (prepared/'manifest.json').write_text(json.dumps(m))
    output=tmp_path/'collection'; output.mkdir()
    with pytest.raises(ValueError): isolated.seal(prepared,output,root)
    assert not (output/'auxiliary_preflight.json').exists()


def test_unknown_dispatch_contract_cannot_accept_valid_n1(tmp_path,monkeypatch):
    root,prepared,_=prepared_case(tmp_path,monkeypatch)
    issues=validate_pre_model_identity(prepared/'manifest.json',prepared/'preflight.json',root,
        execution_contract='N1-VERIFIED-MODEL/future')
    assert any('Unknown pre-model execution contract' in issue for issue in issues)
