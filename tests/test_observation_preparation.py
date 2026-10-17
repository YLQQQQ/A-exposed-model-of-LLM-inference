"""O/P CPU evidence, not target CUDA or sensitivity evidence."""
import importlib
import importlib.util
import json
from copy import deepcopy

import pytest


def api():
    assert importlib.util.find_spec('exposedpath.observation_preparation'), 'missing bounded O/P adapter'
    return importlib.import_module('exposedpath.observation_preparation')


def binding(variant='P', length=32):
    return next(b for b in api().schedule('cpu-prep','a'*40)
                if b['block']==1 and b['variant']==variant and b['input_tokens']==length)


def test_closed_eight_schedule():
    rows=api().schedule('cpu-prep','a'*40)
    assert [(r['input_tokens'],r['variant']) for r in rows]==[
        (32,'O'),(32,'P'),(512,'P'),(512,'O'),(512,'O'),(512,'P'),(32,'P'),(32,'O')]
    assert len({r['run_id'] for r in rows})==8
    assert all(r['pass_id']=='pass1' and r['batch_size']==1 and r['warmup_count']==3 for r in rows)


def test_labels_equivalent_and_only_p_eliminates_onsite_preparation(monkeypatch):
    from exposedpath import runner
    from test_runner_token_ready import _identity_base,_FakeToken,_patch_cpu_torch
    _patch_cpu_torch(monkeypatch)
    identity=_identity_base();events=[];labels=[];counts={'identity':0,'encode':0}
    make,encode=runner.make_natural_token_ready_identity,runner.make_structured_nvtx_label
    def observed_make(*a,**kw):counts['identity']+=1;return make(*a,**kw)
    def observed_encode(*a,**kw):counts['encode']+=1;return encode(*a,**kw)
    monkeypatch.setattr(runner,'make_natural_token_ready_identity',observed_make)
    monkeypatch.setattr(runner,'make_structured_nvtx_label',observed_encode)
    monkeypatch.setattr(runner.torch.cuda.nvtx,'range_push',lambda label:labels.append(label))
    monkeypatch.setattr(runner.torch.cuda.nvtx,'range_pop',lambda:events.append('pop'))
    comparable=[]
    for variant in ('O','P'):
        execution=api().Execution(binding(variant))
        # Same logical identity for direct equivalence; run binding checked separately.
        identity['run_id']=execution.binding['run_id']
        pre=dict(counts)
        ready=execution.prepare(identity,2,runner)
        assert {k:counts[k]-pre[k] for k in counts}==({'identity':2,'encode':2} if variant=='P' else {'identity':0,'encode':0})
        before=dict(counts)
        for i,phase in enumerate(('prefill','decode')):
            ready(_FakeToken([10+i],events),token_index=i,identity_base=identity,phase=phase,
                  clock_ns=lambda:events.append('clock') or 123,emit_nvtx=True)
        onsite={k:counts[k]-before[k] for k in counts}
        assert onsite==({'identity':2,'encode':2} if variant=='O' else {'identity':0,'encode':0})
        report=execution.finish(identity)
        assert report['prepared_count']==(2 if variant=='P' else 0)
        expected=[encode(make(identity,phase=p,token_index=i,callsite_id=f'{p}.token_ready',
            sync_ordinal=i,token_ready_mechanism=runner.TOKEN_READY_MECHANISM)) for i,p in enumerate(('prefill','decode'))]
        assert labels[-2:]==expected
        payloads=[json.loads(label.split(':',1)[1]) for label in labels[-2:]]
        assert all(p.pop('run_id')==execution.binding['run_id'] for p in payloads)
        comparable.append(payloads)
    assert comparable[0]==comparable[1] # only predeclared run namespace differs
    assert events==['host_read','clock','pop']*4


@pytest.mark.parametrize('damage',['run','request','token','phase','repeat','stale','thread'])
def test_prepared_binding_fails_closed(monkeypatch,damage):
    from exposedpath import runner
    from test_runner_token_ready import _identity_base,_FakeToken,_patch_cpu_torch
    _patch_cpu_torch(monkeypatch);e=api().Execution(binding());i=_identity_base();i['run_id']=e.binding['run_id']
    ready=e.prepare(i,2,runner);wrong=deepcopy(i);ti=0;phase='prefill'
    if damage in ('run','request'):wrong[damage+'_id']='wrong'
    if damage=='token':ti=1
    if damage=='phase':phase='decode'
    if damage=='repeat':wrong['repeat_id']='other'
    if damage=='stale':e.invalidate()
    if damage=='thread':monkeypatch.setattr(api().threading,'get_native_id',lambda:-1)
    with pytest.raises(ValueError,match='OBS_PREP_CACHE'):
        ready(_FakeToken([10],[]),token_index=ti,identity_base=wrong,phase=phase,emit_nvtx=True)


def test_o_uses_original_helper_without_reimplementation():
    from exposedpath import runner
    from test_runner_token_ready import _identity_base
    e=api().Execution(binding('O'));i=_identity_base();i['run_id']=e.binding['run_id']
    assert e.prepare(i,2,runner) is runner.observe_token_ready_boundary


@pytest.mark.parametrize('variant',['O','P'])
@pytest.mark.parametrize('length',[32,512])
def test_actual_producer_canonical_both_tokens(tmp_path,monkeypatch,variant,length):
    from test_n1_model_domain import source
    from exposedpath_v141.gate8_files import load_input_receipt
    from analysis.observation_preparation import process
    m=api();b=binding(variant,length)
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=b)
    _,paths=load_input_receipt(receipt)
    read=lambda p:json.loads(p.read_text(encoding='utf8'))
    manifest=read(paths['wmpc_manifest']);ledger=read(paths['pass_identity']);e=read(execution)
    assert m.validate_tokens(paths['batch_tokens'],manifest,ledger,e,paths['wmpc_manifest'],paths['producer_receipt'])==[[17],[18]]
    assert e['observation_preparation']['prepared_count']==(2 if variant=='P' else 0)
    r=read(process(receipt,execution,tmp_path/'analysis'))
    assert r['status']==m.STATUS and r['binding']==b
    assert len(r['operations'])==2 and {o['phase'] for o in r['operations']}=={'prefill','decode'}
    # Independent prescribed CPU Raw: kernel completes before copy, necessary
    # D2H is [copy.end,copy.end+2), sync starts later. Both COE=2, sync=0.
    assert [o['candidate_ns'] for o in r['operations']]==[2,2]
    assert [o['original_sync_ns'] for o in r['operations']]==[0,0]
    assert all(type(o['positions']['H_ns']) is int and type(o['positions']['D_ns']) is int for o in r['operations'])
    assert len(r['windows'])==2 and all(w['a']['A_unattributed_ns']==0 for w in r['windows'])
    assert not list((tmp_path/'analysis').rglob('domain.json'))


def test_fixed_blocks_signed_contrasts_and_fail_stop(tmp_path):
    m=api();seen=[]
    def collect(b,out):
        seen.append(b)
        if len(seen)==6:raise ValueError('hard quality failure')
        n=b['input_tokens']//32;v=3 if b['variant']=='P' else 8
        return dict(status=m.STATUS,binding=b,token_ids=[[10],[11]],
            preparation=dict(prepared_count=2 if b['variant']=='P' else 0),
            operations=[dict(token_index=i,phase=p,candidate_ns=n+v,positions=dict(H_ns=v,D_ns=n),
                kernel_ns=n,memop_ns=2,original_sync_ns=0,copy_wall_ns=10,wall_ns=20,uncovered_ns=20-n-v,
                same_operation_all_gpu_union_ns=n+v,sync_wall_ns=5)
                for i,p in enumerate(('prefill','decode'))],windows=[])
    r=m.run_batch('cpu-prep','a'*40,tmp_path/'batch',collect)
    assert r['status']=='BLOCKED' and len(seen)==6 and r['incomplete_blocks']==[2]
    assert [s['status'] for s in r['runs']]==['COMPLETE']*5+['BLOCKED']+['NOT_RUN']*2
    assert len(r['blocks'])==1
    q=r['blocks'][0]
    assert q['per_token'][0]['P_minus_O']['32']['candidate_ns']==-5
    assert q['per_token'][0]['length_512_minus_32']['O']['candidate_ns']==15


def test_prepare_before_drain_and_no_added_completion_calls(monkeypatch):
    from exposedpath import runner
    from test_runner_token_ready import _identity_base,_FakeToken,_FakeModel,_FakeInput,_patch_cpu_torch,_clock
    _patch_cpu_torch(monkeypatch);events=[];e=api().Execution(binding())
    identity=_identity_base();identity['run_id']=e.binding['run_id']
    original=e.prepare
    def prepare(*a):events.append('prepare');return original(*a)
    e.prepare=prepare
    monkeypatch.setattr(runner.torch.cuda,'synchronize',lambda:events.append('drain'))
    r=runner.run_one_invocation(model=_FakeModel(iter([_FakeToken([10],events),_FakeToken([11],events)])),
        input_ids=_FakeInput(),attention_mask=object(),output_len=2,device='cpu',nvtx_invocation_label='',
        nvtx_full_request_label='',nvtx_prefill_label='',nvtx_decode_label='',token_ready_identity_base=identity,
        observation_preparation=e,clock_ns=_clock(100,110,120))
    assert events==['prepare','drain','host_read','host_read']
    assert r['inference_end_ns']==120
    assert e.finish(identity)['consumed_token_indices']==[0,1]


@pytest.mark.parametrize('damage,reason',[('drain','DRAIN'),('dependency','API_SEMANTICS_UNBOUNDED:cudaStreamWaitEvent'),
    ('prefill_gap','STAGE|SUBMIT|SEMANTICS'),('future_gap','STAGE|SUBMIT|SEMANTICS'),
    ('unmarked_token','TOKEN'),('stream','STREAM|OTHER_STREAM')])
def test_existing_quality_rejections_still_stop_both_token_chain(tmp_path,monkeypatch,damage,reason):
    from test_n1_model_domain import source
    from analysis.observation_preparation import process
    api()
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=binding(),damage=damage)
    with pytest.raises(ValueError,match=reason):process(receipt,execution,tmp_path/'analysis')
    assert not (tmp_path/'analysis/sensitivity.json').exists()


@pytest.mark.parametrize('damage',['token','role','variant','source','cache'])
def test_real_producer_evidence_tampering_rejected(tmp_path,monkeypatch,damage):
    from test_n1_model_domain import source
    from exposedpath_v141.gate8_files import load_input_receipt
    from test_gate8_identity import write_json
    m=api();receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=binding())
    _,paths=load_input_receipt(receipt)
    read=lambda p:json.loads(p.read_text(encoding='utf8'))
    mf=read(paths['wmpc_manifest']);ledger=read(paths['pass_identity']);e=read(execution)
    if damage=='token':
        t=read(paths['batch_tokens']);t['requests'][0]['token_ids'][0][0]=None;write_json(paths['batch_tokens'],t)
    elif damage=='role':mf['run_role']='FORMAL'
    elif damage=='variant':mf['batch_load']['variant']='O'
    elif damage=='source':mf['runner_git_commit']='b'*40
    else:e['observation_preparation']['prepared_labels'][0]+='changed'
    with pytest.raises(ValueError):m.validate_tokens(paths['batch_tokens'],mf,ledger,e,paths['wmpc_manifest'],paths['producer_receipt'])


@pytest.mark.parametrize('variant',['O','P'])
@pytest.mark.parametrize('length',[32,512])
def test_actual_prepare_seal_collector_boundary(tmp_path,monkeypatch,variant,length):
    import csv,subprocess,sys,sysconfig
    from pathlib import Path
    from types import SimpleNamespace
    from exposedpath import gate8_diagnostic as entry,platform_adapter,gate8_isolated_preflight as isolated
    from exposedpath_v141 import gate8_source_probe
    from scripts import gate8_diagnostic_collect as collector
    from test_gate8_identity import sha,write_json
    b=binding(variant,length);m=api()
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3');monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(platform_adapter,'git',lambda args,**kw:'' if 'status' in args else 'a'*40)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'3, GPU-12345678-1234-1234-1234-123456789abc, 00000000:01:00.0')
    # Explicit external CUDA identity double; never instantiate target backend.
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')))
    model=tmp_path/'model';model.mkdir()
    write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    inventory=tmp_path/'inventory.csv'
    with inventory.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['RelativePath','Bytes','SHA256']);w.writeheader()
        w.writerow(dict(RelativePath='config.json',Bytes=(model/'config.json').stat().st_size,SHA256=sha(model/'config.json')))
    prompt=write_json(tmp_path/'prompt.json',dict(schema_version='exposedpath-prompt-tokens/1',tokenizer_id='cpu',
        fixed_input_tokens=length,samples=[dict(sample_index=0,input_ids=[7]*length,attention_mask=[1]*length)]))
    prepared=entry.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,inventory_path=inventory,
        inventory_sha256=sha(inventory),prompt_path=prompt,prompt_sha256=sha(prompt),expected_commit='a'*40,
        physical_gpu=3,engineering_attention_backend='sdpa',target_python=sys._base_executable,
        site_root=sysconfig.get_path('purelib'),batch_binding=b)
    mf=json.loads((prepared/'manifest.json').read_text());assert m.validate(mf)==b
    assert mf['fixed_input_tokens']==length and mf['warmup_count']==3
    assert mf['preparation_source_sha256']==sha(Path(m.__file__))
    root=tmp_path/'repo';(root/'.git').mkdir(parents=True);(root/'.git/HEAD').write_text('a'*40)
    files=('exposedpath/runner.py','exposedpath/observation_preparation.py')
    real=Path(__file__).resolve().parents[1]
    for p in files:
        target=root/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((real/p).read_bytes())
    def paths(tool,args,**kw):
        return subprocess.CompletedProcess(args,0,('\0'.join(files)+'\0').encode() if '--cached' in args else b'',b'')
    monkeypatch.setattr(platform_adapter,'run_tool',paths)
    out=tmp_path/'collection';nsys=tmp_path/'nsys.exe';nsys.touch();calls=[]
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(out),'--execute-engineering-diagnostic',
        '--engineering-a-only','--observation-preparation'])
    monkeypatch.setattr(collector.subprocess,'run',lambda *a,**kw:subprocess.CompletedProcess(a[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    def stop_at_profile(argv,*a,**kw):
        calls.append(argv);assert argv[1]=='profile' and 'model-run' in argv
        sealed=isolated.read(out/'auxiliary_preflight.json')
        claim=isolated.consume(receipt=out/'auxiliary_preflight.json',expected_sha=sha(out/'auxiliary_preflight.json'),
            nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==b['run_id']
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_MODEL_OR_CUDA')
    monkeypatch.setattr(collector,'run_once',stop_at_profile)
    assert collector.main()==1 and len(calls)==1


def test_batch_entry_default_is_not_opted_in(tmp_path):
    from scripts.observation_preparation_batch import run
    with pytest.raises(ValueError,match='OPT_IN_REQUIRED'):run({},tmp_path/'out')
    assert not (tmp_path/'out').exists()


def test_explicit_ablation_cannot_use_legacy_diagnostic_entry(tmp_path,monkeypatch):
    import sys
    from scripts import gate8_diagnostic_collect as collector
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(tmp_path/'not-nsys'),
        '--python',sys._base_executable,'--prepared',str(tmp_path/'missing'),
        '--output',str(tmp_path/'out'),'--execute-engineering-diagnostic','--observation-preparation'])
    with pytest.raises(ValueError,match='OBS_PREP_DOMAIN_ENTRY_REQUIRED'):collector.main()
    assert not (tmp_path/'out').exists()


@pytest.mark.parametrize('damage',[None,'result_hash','token','exit','version'])
def test_real_result_consumer_file_chain(tmp_path,monkeypatch,damage):
    from pathlib import Path
    from test_n1_model_domain import source
    from scripts.observation_preparation_batch import consume_collection
    from scripts.gate8_diagnostic_collect import analyze_receipt
    from exposedpath_v141.gate8_files import load_input_receipt
    from test_gate8_identity import write_json,sha
    # Import actual analysis/JSON helpers before isolated OS boundary doubles.
    from analysis.observation_preparation import process
    b=binding();source_receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=b)
    receipt=tmp_path/'input_receipt.json';receipt.write_bytes(source_receipt.read_bytes())
    read=lambda p:json.loads(p.read_text(encoding='utf8'))
    _,paths=load_input_receipt(receipt);mf=read(paths['wmpc_manifest']);ledger=read(paths['pass_identity'])
    result,value=analyze_receipt(mf,receipt,execution,tmp_path/'analyzed')
    write_json(tmp_path/'target_launch.json',dict(role='CPU_LAUNCH_BOUNDARY'))
    exitdir=tmp_path/'diagnostic-entry';exitdir.mkdir(exist_ok=True)
    write_json(exitdir/'exit.json',dict(status='EXITED',exit_code=0,pid=ledger['pid']))
    report=dict(schema_version='observation-preparation-collection/0.1.0',status=api().STATUS,qualification='NOT_QUALIFIED',
        scientific_outputs_allowed=False,export_status='PASS',result_filename='sensitivity.json',batch_load=b,
        q0_status='NOT_RUN',dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        collection=dict(status='COMPLETE',exit_code=0,timed_out=False),result_sha256=sha(result),
        manifest_sha256=sha(paths['wmpc_manifest']),target_runtime_sha256=sha(tmp_path/'diagnostic/target_runtime.json'),
        target_launch_sha256=sha(tmp_path/'target_launch.json'))
    if damage=='result_hash':report['result_sha256']='0'*64
    elif damage=='version':report['schema_version']='future'
    elif damage=='token':
        t=read(paths['batch_tokens']);t['requests'][0]['token_ids'][0][0]=-1;write_json(paths['batch_tokens'],t)
    elif damage=='exit':write_json(exitdir/'exit.json',dict(status='EXITED',exit_code=2,pid=ledger['pid']))
    write_json(tmp_path/'collection_report.json',report)
    if damage:
        with pytest.raises(ValueError):consume_collection(tmp_path,b,'a'*40)
    else:
        r=consume_collection(tmp_path,b,'a'*40)
        assert r['token_ids']==[[17],[18]] and len(r['operations'])==2
        assert 'error' not in report # actual successful report contract permits absence
