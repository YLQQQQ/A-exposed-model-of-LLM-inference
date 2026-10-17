"""Real verified producer file chain; model/device/OS are explicit CPU doubles."""
import json
from types import SimpleNamespace
import pytest
from test_gate8_identity import write_json,sha


def test_parameter_controller_cannot_enter_old_domain_before_model_load(tmp_path,monkeypatch):
    from test_gate8_stage_producer import setup_case
    from exposedpath import runner
    args,state,_,_=setup_case(monkeypatch,tmp_path)
    with pytest.raises(ValueError,match='MEMSET_PREFILL_PROFILE_REQUIRED'):
        runner.run_gate8_requests_to_files(**args,parameter_recorder=object())
    assert state['loads']==0


@pytest.mark.parametrize('fail_begin',[False,True])
def test_real_verified_model_entry_keeps_three_warmups_and_natural_tokens(tmp_path,monkeypatch,fail_begin):
    from test_batch_load_diagnostic import source
    from test_runner_token_ready import _FakeModel,_FakeToken
    from exposedpath import runner,gate8_diagnostic as entry,memset_prefill as c
    args,state,events=source(tmp_path,monkeypatch)
    rec=tmp_path/'recorder.dll';rec.write_bytes(b'CPU-only recorder file')
    runtime=tmp_path/'runtime.dll';runtime.write_bytes(b'CPU-only runtime file')
    b=c.binding('a'*32,'d'*40,dict(path=str(rec),sha256=sha(rec)),dict(path=str(runtime),sha256=sha(runtime)))
    m=json.loads(args['manifest_path'].read_text());m.pop('domain_qualification');m.pop('engineering_pair')
    m.update(c.minimal_fields(b),runner_git_commit='d'*40)
    p=json.loads(args['prompt_path'].read_text());p['samples']=p['samples'][:2];write_json(args['prompt_path'],p)
    m.update(memset_input=c.validate_input(p,json.loads((tmp_path/'model/config.json').read_text())),prompt_tokens_sha256=sha(args['prompt_path']))
    # Only the OS interpreter/preflight boundary is doubled; real manifest,
    # module/input hashes, runner, completion and all producer files remain real.
    from exposedpath import gate8_isolated_preflight as isolated
    from exposedpath_v141 import gate8_target_python as target
    m.update(target_python={'CPU_OS_BOUNDARY':True},isolated_preflight_version=isolated.VERSION,
        model_content_snapshot={'inventory_sha256':'0'*64})
    monkeypatch.setattr(target,'current',lambda _:dict(pid=123))
    monkeypatch.setattr(isolated,'consume',lambda **kw:dict(target_pid=123))
    monkeypatch.setattr(isolated,'read',lambda _: {})
    monkeypatch.setattr(isolated,'verify_snapshot',lambda *a:None)
    monkeypatch.setattr(entry,'verify_model_inventory',lambda *a,**kw:{})
    from exposedpath import coe_pilot
    monkeypatch.setattr(coe_pilot,'software_identity',lambda _:dict(coe_pilot.SOFTWARE)) # target runtime identity double
    args.update(auxiliary_receipt=tmp_path/'cpu_aux.json',auxiliary_sha256='0'*64,launch_nonce='cpu')
    write_json(args['manifest_path'],m)
    def load(*a,**kw):
        state['loads']+=1;state['initialized']=True
        model=_FakeModel(iter([_FakeToken([13,13],events),_FakeToken([14,14],events)]*4))
        model.dtype='torch.float16';model.training=False
        model.config=SimpleNamespace(_attn_implementation='sdpa',model_type='qwen2',use_cache=True)
        return model,SimpleNamespace(eos_token_id=2),100,'cuda:0'
    monkeypatch.setattr(runner,'load_model',load)
    calls=[]
    class CPURecorder:
        def __init__(self,binding):assert binding==b
        def install(self,identity):calls.append(('install',state['syncs'],len(events)))
        def begin(self,identity):
            calls.append(('begin',state['syncs'],len(events)));self.identity=identity
            if fail_begin:raise RuntimeError('CPU_BEGIN_FAIL')
        def end(self,completed_ns):calls.append(('end',state['syncs'],len(events)))
        def close(self,path):
            calls.append(('close',state['syncs'],len(events)));write_json(path,dict(role='CPU_SUBSTITUTE',identity=self.identity))
    monkeypatch.setattr(c,'Recorder',CPURecorder)
    root=entry.run_diagnostic(**args).parent
    if fail_begin:
        assert json.loads((root/'diagnostic_report.json').read_text())['status']=='DIAGNOSTIC_INCOMPLETE'
        ledger=json.loads((root/'producer/pass_identity.json').read_text())
        assert ledger['requests'][-1]['reasons']==['RUNTIME_ERROR:RuntimeError']
        assert calls==[('install',6,0),('begin',7,0),('close',7,0)]
        return
    assert json.loads((root/'diagnostic_report.json').read_text())['status']=='DIAGNOSTIC_COMPLETE'
    assert calls==[('install',6,0),('begin',7,0),('end',7,1),('close',7,2)]
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    tokens=json.loads((root/'batch_tokens.json').read_text())
    assert ledger['batch_load']==b and len(ledger['requests'])==4
    assert ledger['run_role']=='ENGINEERING' and tokens['requests'][0]['token_ids']==[[13,13],[14,14]]
    assert json.loads((root/'memset_parameters.json').read_text())['identity']==ledger['requests'][-1]['identity']
    c.validate(m)


def test_prepare_new_domain_binds_batch_content_and_rejects_missing_modules(tmp_path,monkeypatch):
    import csv,sys,sysconfig
    from exposedpath import gate8_diagnostic as entry,platform_adapter,memset_prefill as c
    from exposedpath_v141 import gate8_source_probe
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3');monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(platform_adapter,'git',lambda argv,**kw:'' if 'status' in argv else 'd'*40)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'555.99')
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')))
    model=tmp_path/'model';model.mkdir();p=write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    inv=tmp_path/'inventory.csv'
    with inv.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['RelativePath','Bytes','SHA256']);w.writeheader();w.writerow(dict(RelativePath='config.json',Bytes=p.stat().st_size,SHA256=sha(p)))
    prompt=write_json(tmp_path/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='CPU',fixed_input_tokens=512,
        samples=[dict(sample_index=i,input_ids=[7]*512,attention_mask=[1]*512) for i in range(2)]))
    rec=tmp_path/'rec.dll';rec.write_bytes(b'CPU');rt=tmp_path/'rt.dll';rt.write_bytes(b'CPU runtime')
    b=c.binding('a'*32,'d'*40,dict(path=str(rec),sha256=sha(rec)),dict(path=str(rt),sha256=sha(rt)))
    prepared=entry.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,inventory_path=inv,inventory_sha256=sha(inv),
        prompt_path=prompt,prompt_sha256=sha(prompt),expected_commit='d'*40,physical_gpu=3,engineering_attention_backend='sdpa',
        target_python=sys._base_executable,site_root=sysconfig.get_path('purelib'),batch_binding=b)
    m=json.loads((prepared/'manifest.json').read_text());c.validate_prepared(m,prepared,entry.Path(entry.__file__).resolve().parents[1])
    # Exercise the real contract dispatch up to profile argv, not a validator
    # double. Only expensive/unrelated Git census and physical GPU query are
    # replaced; no collector is launched.
    from exposedpath import gate8_isolated_preflight as isolated
    from scripts.gate8_diagnostic_collect import profile_argv
    root=entry.Path(entry.__file__).resolve().parents[1];out=tmp_path/'collection';out.mkdir()
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:
        '3, GPU-12345678-1234-1234-1234-123456789abc, 00000000:01:00.0')
    monkeypatch.setattr(isolated,'_git_paths',lambda r,o,tracked:set() if not tracked else {'exposedpath/runner.py'})
    monkeypatch.setattr(isolated,'tree',lambda *a,**kw:{'exposedpath/runner.py':sha(root/'exposedpath/runner.py')})
    monkeypatch.setattr(isolated,'git_metadata',lambda *a:dict(role='CPU_GIT_METADATA_BOUNDARY'))
    receipt=isolated.seal(prepared,out,root)
    assert json.loads(receipt.read_text())['run_id']==b['run_id']
    argv=profile_argv('CPU_NOT_NSYS',sys._base_executable,prepared,out,root)
    assert '--duration=300' in argv and 'model-run' in argv
    rec.unlink()
    with pytest.raises(FileNotFoundError):c.validate_prepared(m,prepared,entry.Path(entry.__file__).resolve().parents[1])
