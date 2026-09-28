"""CPU only: real files/receipts, external GPU observations are explicit doubles."""
import importlib
import importlib.util
import json
import os
from pathlib import Path
import uuid

import pytest


def api():
    assert importlib.util.find_spec('exposedpath.gate8_isolated_preflight'), 'missing isolated preflight'
    return importlib.import_module('exposedpath.gate8_isolated_preflight')


def case(tmp_path, monkeypatch):
    m=api()
    root=tmp_path/'repo'; root.mkdir()
    (root/'.git').mkdir(); (root/'.git/HEAD').write_text('ref: refs/heads/main\n')
    (root/'code.py').write_text('pass\n')
    prepared=tmp_path/'prepared'; prepared.mkdir()
    manifest=dict(run_id='fresh-run',runner_git_commit='a'*40,runner_git_dirty=False,
        isolated_preflight_version=m.VERSION,gpu_index_physical=3,gpu_index_logical=0,
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='00000000:01:00.0')
    for name,value in [('manifest.json',manifest),('preflight.json',{}),('prompt.json',{})]:
        (prepared/name).write_text(json.dumps(value))
    (prepared/'model_inventory.csv').write_text('inventory')
    from exposedpath import platform_adapter
    def git(args,**kw):
        if 'rev-parse' in args: return 'a'*40
        if 'status' in args or 'ls-files' in args: return ''
        raise AssertionError(args)
    monkeypatch.setattr(platform_adapter,'git',git)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:
        '3, GPU-12345678-1234-1234-1234-123456789abc, 00000000:01:00.0')
    monkeypatch.setattr(m,'validate_pre_model_identity',lambda *a:[])
    monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID'); monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3')
    output=tmp_path/'new'; output.mkdir()
    receipt=m.seal(prepared,output,root)
    value=json.loads(receipt.read_text())
    args=dict(receipt=receipt,expected_sha=m.sha(receipt),nonce=value['nonce'],
              prepared=prepared,output=output,root=root)
    return m,args


def test_target_checks_current_files_without_external_commands_and_consumes_once(tmp_path,monkeypatch):
    m,args=case(tmp_path,monkeypatch)
    from exposedpath import platform_adapter
    monkeypatch.setattr(platform_adapter,'run_tool',lambda *a,**kw:pytest.fail('target external command'))
    observed=m.consume(**args)
    assert observed['target_pid']==os.getpid()
    assert observed['git_observation_role']=='PREFLIGHT_NOT_TARGET_GIT_QUERY'
    with pytest.raises(FileExistsError): m.consume(**args)


@pytest.mark.parametrize('damage',['stale','future','run','code','new-file','git','input','missing','nonce','output','mask','receipt','version'])
def test_changed_or_replayed_preflight_rejected_before_model(tmp_path,monkeypatch,damage):
    m,args=case(tmp_path,monkeypatch)
    if damage in ('stale','future'):
        value=json.loads(args['receipt'].read_text())
        value['issued_wall_ns']+=(-121 if damage=='stale' else 10)*10**9
        args['receipt'].write_text(json.dumps(value)); args['expected_sha']=m.sha(args['receipt'])
    elif damage=='run':
        p=args['prepared']/'manifest.json'; v=json.loads(p.read_text()); v['run_id']='wrong'; p.write_text(json.dumps(v))
    elif damage=='code': (args['root']/'code.py').write_text('changed')
    elif damage=='new-file': (args['root']/'injected.py').write_text('new')
    elif damage=='git': (args['root']/'.git/HEAD').write_text('b'*40)
    elif damage=='input': (args['prepared']/'prompt.json').write_text('changed')
    elif damage=='missing': (args['prepared']/'prompt.json').unlink()
    elif damage=='nonce': args['nonce']=uuid.uuid4().hex
    elif damage=='output': args['output']=args['output'].parent/'wrong'
    elif damage=='mask': monkeypatch.setenv('CUDA_VISIBLE_DEVICES','2')
    elif damage=='receipt': args['expected_sha']='0'*64
    elif damage=='version':
        value=json.loads(args['receipt'].read_text()); value['schema_version']='future'
        args['receipt'].write_text(json.dumps(value)); args['expected_sha']=m.sha(args['receipt'])
    with pytest.raises((ValueError,FileNotFoundError)): m.consume(**args)


def test_expiry_during_snapshot_check_does_not_allow_claim(tmp_path,monkeypatch):
    m,args=case(tmp_path,monkeypatch)
    original=m.verify_snapshot; clock=m.time.time_ns; offset=[0]
    def slow(*a):
        original(*a); offset[0]=121*10**9
    monkeypatch.setattr(m,'verify_snapshot',slow)
    monkeypatch.setattr(m.time,'time_ns',lambda:clock()+offset[0])
    with pytest.raises(ValueError,match='EXPIRED'): m.consume(**args)
    assert not (args['output']/'auxiliary_preflight.claim.json').exists()


def test_post_execution_content_change_rejected(tmp_path,monkeypatch):
    m,args=case(tmp_path,monkeypatch); m.consume(**args)
    (args['root']/'code.py').write_text('changed during execution')
    with pytest.raises(ValueError): m.verify_snapshot(json.loads(args['receipt'].read_text()),args['prepared'],args['root'])


def test_gpu_actual_conflict_during_seal_rejected(tmp_path,monkeypatch):
    m,args=case(tmp_path,monkeypatch)
    from exposedpath import platform_adapter
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'3, GPU-00000000-0000-0000-0000-000000000000, 00000000:01:00.0')
    other=tmp_path/'other'; other.mkdir()
    with pytest.raises(ValueError): m.seal(args['prepared'],other,args['root'])


@pytest.mark.parametrize('conflict',[False,True])
def test_native_cuda_identity_joins_uuid_not_device_number(monkeypatch,conflict):
    from exposedpath import platform_adapter as p
    assert callable(getattr(p,'cuda_identity_native',None)), 'missing native identity'
    from types import SimpleNamespace
    fake=SimpleNamespace(device_count=lambda:1,current_device=lambda:0,
        get_device_properties=lambda n:SimpleNamespace(uuid='GPU-12345678-1234-1234-1234-123456789abc'))
    monkeypatch.setattr(p,'_cuda_driver_identity',lambda n:dict(
        gpu_uuid='GPU-'+('00000000-0000-0000-0000-000000000000' if conflict else '12345678-1234-1234-1234-123456789abc'),
        pci_bus_id='00000000:01:00.0'))
    monkeypatch.setattr(p,'run_tool',lambda *a,**kw:pytest.fail('external process'))
    if conflict:
        with pytest.raises(ValueError): p.cuda_identity_native(fake)
    else:
        assert p.cuda_identity_native(fake)==dict(gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')


@pytest.mark.parametrize('conflict',[False,True])
def test_real_diagnostic_file_entry_uses_receipt_and_native_device_not_tools(tmp_path,monkeypatch,conflict):
    from test_gate8_diagnostic_entry import case as producer_case
    from exposedpath import gate8_diagnostic as diagnostic,platform_adapter,runner
    from exposedpath.gate8_engineering_contract import declaration
    from exposedpath_v141 import gate8_target_python as target,gate8_source_probe
    from types import SimpleNamespace
    m,args=case(tmp_path,monkeypatch)
    workload=tmp_path/'workload'; workload.mkdir()
    entry,state=producer_case(monkeypatch,workload)
    value=json.loads(entry['manifest_path'].read_text())
    value.update(isolated_preflight_version=m.VERSION,target_python={},attention_backend='sdpa',
        engineering_scope=declaration('sdpa'),model_content_snapshot={'inventory_sha256':'0'*64},
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='00000000:01:00.0')
    entry['manifest_path'].write_text(json.dumps(value))
    entry['preflight_path'].write_text(json.dumps(dict(physical_gpu_index=3,logical_gpu_index=0,
        gpu_uuid=value['gpu_uuid'],gpu_pci_bus_id=value['gpu_pci_bus_id'])))
    (workload/'model_inventory.csv').write_text('CPU inventory double')
    entry.update(project_root=args['root'],output_dir=args['output']/'diagnostic')
    monkeypatch.setattr(diagnostic,'__file__',str(args['root']/'exposedpath/gate8_diagnostic.py'))
    monkeypatch.setattr(target,'current',lambda _:dict(pid=os.getpid(),snapshot={}))
    monkeypatch.setattr(diagnostic,'verify_model_inventory',lambda *a,**kw:{})
    # A new output is required: never replace or refresh the earlier sealed receipt.
    output=tmp_path/'fresh-collection'; output.mkdir(); entry['output_dir']=output/'diagnostic'
    monkeypatch.setattr(platform_adapter,'git',lambda command,**kw:
        value['runner_git_commit'] if 'rev-parse' in command else '')
    receipt=m.seal(workload,output,args['root']); sealed=json.loads(receipt.read_text())
    entry.update(auxiliary_receipt=receipt,auxiliary_sha256=m.sha(receipt),launch_nonce=sealed['nonce'])
    monkeypatch.setattr(platform_adapter,'run_tool',lambda *a,**kw:pytest.fail('target external command'))
    monkeypatch.setattr(diagnostic,'validate_pre_model_identity',lambda *a:pytest.fail('target Git validator'))
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(cuda=SimpleNamespace(
        device_count=lambda:1,current_device=lambda:0,get_device_properties=lambda n:SimpleNamespace(uuid=value['gpu_uuid']))))
    monkeypatch.setattr(platform_adapter,'_cuda_driver_identity',lambda n:dict(
        gpu_uuid=value['gpu_uuid'],pci_bus_id='00000000:02:00.0' if conflict else value['gpu_pci_bus_id']))
    load=runner.load_model
    def configured(*a,**kw):
        result=load(*a,**kw); result[0].config=SimpleNamespace(_attn_implementation='sdpa',model_type='qwen2',use_cache=True)
        return result
    monkeypatch.setattr(runner,'load_model',configured)
    if conflict:
        with pytest.raises(ValueError,match='PROBE_CONFLICT'): diagnostic.run_diagnostic(**entry)
        assert state['loads']==0
    else:
        report=diagnostic.run_diagnostic(**entry)
        assert json.loads(report.read_text())['status']=='DIAGNOSTIC_COMPLETE'
        ledger=json.loads((report.parent/'producer/pass_identity.json').read_text())
        assert len(ledger['requests'][1]['observed_boundary_ids'])==3
        assert json.loads((report.parent/'isolated_preflight_target.json').read_text())['target_pid']==ledger['pid']


def test_driver_abi_reads_actual_uuid_and_pci_with_no_fallback(monkeypatch):
    from exposedpath import platform_adapter as p
    import ctypes as c
    class Function:
        def __init__(self,call): self.call=call
        def __call__(self,*args): return self.call(*args)
    class Driver: pass
    driver=Driver()
    driver.cuInit=Function(lambda flags:0)
    def device(out,ordinal):
        assert ordinal==0; c.cast(out,c.POINTER(c.c_int))[0]=42; return 0
    def identifier(out,device):
        assert device==42; c.memmove(out,bytes.fromhex('12345678123412341234123456789abc'),16); return 0
    def pci(out,length,device):
        assert device==42 and length>=13; c.memmove(out,b'0000:01:00.0\0',13); return 0
    driver.cuDeviceGet=Function(device); driver.cuDeviceGetUuid_v2=Function(identifier); driver.cuDeviceGetPCIBusId=Function(pci)
    monkeypatch.setattr(p,'_load_cuda_driver',lambda:driver)
    assert p._cuda_driver_identity(0)==dict(gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='0000:01:00.0')
    driver.cuDeviceGet=Function(lambda *a:101)
    with pytest.raises(ValueError,match='101'): p._cuda_driver_identity(0)


def test_profile_command_carries_exact_receipt_hash_nonce_and_refuses_missing(tmp_path,monkeypatch):
    from scripts import gate8_diagnostic_collect as collector
    from exposedpath_v141 import gate8_target_python as target
    import sys,sysconfig
    m,args=case(tmp_path,monkeypatch)
    value=json.loads((args['prepared']/'manifest.json').read_text())
    value['target_python']=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    (args['prepared']/'manifest.json').write_text(json.dumps(value))
    output=tmp_path/'launch'; output.mkdir()
    with pytest.raises(ValueError,match='PREFLIGHT'):
        collector.profile_argv('nsys',sys._base_executable,args['prepared'],output,args['root'])
    receipt=m.seal(args['prepared'],output,args['root'])
    command=collector.profile_argv('nsys',sys._base_executable,args['prepared'],output,args['root'])
    assert command[command.index('--auxiliary-receipt')+1]==str(receipt)
    assert command[command.index('--auxiliary-sha256')+1]==m.sha(receipt)
    assert command[command.index('--launch-nonce')+1]==json.loads(receipt.read_text())['nonce']


def test_real_git_preflight_then_isolated_cpu_child_consumes_without_tools(tmp_path,monkeypatch):
    from exposedpath import platform_adapter as adapter
    real_git=adapter.git
    m,args=case(tmp_path,monkeypatch)
    monkeypatch.setattr(adapter,'git',real_git)
    root=args['root']
    git=lambda *a:real_git(['-C',str(root),*a])
    git('init'); git('config','user.name','CPU Fixture'); git('config','user.email','fixture@example.invalid')
    (root/'.gitignore').write_text('.local/\n__pycache__/\n')
    git('add','code.py','.gitignore'); git('commit','-m','deterministic fixture')
    manifest=json.loads((args['prepared']/'manifest.json').read_text())
    manifest['runner_git_commit']=git('rev-parse','HEAD')
    (args['prepared']/'manifest.json').write_text(json.dumps(manifest))
    (root/'.local').mkdir(); (root/'.local/private.txt').write_text('never copied')
    output=tmp_path/'real-run'; output.mkdir()
    receipt=m.seal(args['prepared'],output,root); sealed=json.loads(receipt.read_text())
    assert set(sealed['tree_hashes'])=={'.gitignore','code.py'}
    import sys,subprocess
    command=("import sys,json;sys.path.insert(0,sys.argv[1]);"
        "from exposedpath import gate8_isolated_preflight as m,platform_adapter as a;"
        "a.run_tool=lambda *a,**k:(_ for _ in ()).throw(AssertionError('external child tool'));"
        "print(json.dumps(m.consume(receipt=sys.argv[2],expected_sha=sys.argv[3],nonce=sys.argv[4],"
        "prepared=sys.argv[5],output=sys.argv[6],root=sys.argv[7])))")
    result=subprocess.run([sys._base_executable,'-I','-S','-c',command,str(Path(__file__).resolve().parents[1]),
        str(receipt),m.sha(receipt),sealed['nonce'],str(args['prepared']),str(output),str(root)],capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    claim=json.loads(result.stdout)
    assert claim['parent_pid']==os.getpid() and claim['target_pid']!=os.getpid()
    m.finalize(receipt,args['prepared'],root)
    (root/'code.py').write_text('changed')
    with pytest.raises(ValueError): m.finalize(receipt,args['prepared'],root)


def test_collector_seals_before_profile_and_finalizes_before_export(tmp_path,monkeypatch):
    from scripts import gate8_diagnostic_collect as collector
    from exposedpath.gate8_engineering_contract import declaration
    from exposedpath_v141 import gate8_target_python as target
    from scripts import gate7_nsys_postprocess
    import sys,sysconfig
    m,args=case(tmp_path,monkeypatch)
    value=json.loads((args['prepared']/'manifest.json').read_text())
    value.update(target_python=target.probe(sys._base_executable,sysconfig.get_path('purelib')),
        engineering_scope=declaration('sdpa'),attention_backend='sdpa',batch_size=1,
        execution_mode='eager',run_role='ENGINEERING',data_role='Engineering')
    (args['prepared']/'manifest.json').write_text(json.dumps(value))
    output=tmp_path/'collector-run'; nsys=tmp_path/'nsys.exe'; nsys.touch()
    monkeypatch.setattr(collector,'ROOT',args['root'])
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(args['prepared']),'--output',str(output),'--execute-engineering-diagnostic','--engineering-a-only'])
    from types import SimpleNamespace
    monkeypatch.setattr(collector.subprocess,'run',lambda *a,**k:SimpleNamespace(stdout='2026.2.1.210'))
    def child(argv,*a,**kw):
        claim=m.consume(receipt=argv[argv.index('--auxiliary-receipt')+1],
            expected_sha=argv[argv.index('--auxiliary-sha256')+1],nonce=argv[argv.index('--launch-nonce')+1],
            prepared=args['prepared'],output=output,root=args['root'])
        assert claim['run_id']=='fresh-run'
        (output/'diagnostic').mkdir()
        (output/'diagnostic/diagnostic_report.json').write_text(json.dumps(dict(status='DIAGNOSTIC_COMPLETE',
            qualification='NOT_QUALIFIED',scientific_outputs_allowed=False)))
        return dict(status='COMPLETE')
    monkeypatch.setattr(collector,'run_once',child)
    def export(**kw):
        assert json.loads((output/'auxiliary_preflight.final.json').read_text())['status']=='PASS'
        return dict(status='BLOCKED')  # Stop fake execution before any analyzer; not real Nsight.
    monkeypatch.setattr(gate7_nsys_postprocess,'run_postprocess',export)
    assert collector.main()==1
    assert 'Single export failed' in json.loads((output/'collection_report.json').read_text())['error']
    # A different output directory must not reuse the same prepared run after failure.
    sys.argv[sys.argv.index('--output')+1]=str(tmp_path/'retry-forbidden')
    with pytest.raises(FileExistsError): collector.main()
