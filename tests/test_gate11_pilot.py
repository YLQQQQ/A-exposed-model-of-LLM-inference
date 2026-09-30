"""Pilot role and real producer wiring. CPU doubles are not Pilot evidence."""
import json
from copy import deepcopy
import pytest
from test_gate8_identity import write_json


def pilot():
    from exposedpath import gate11_pilot
    return gate11_pilot


def test_fixed_first_batch_order_and_no_budget_expansion():
    p = pilot(); rows = p.schedule('batch-test')
    assert len(rows) == 30 and len({r['run_id'] for r in rows}) == 30
    assert [r['condition'] for r in rows[::2]] == [
        'G32','N0','Nm','N16','G512', 'G512','Nm','N16','N0','G32', 'G32','N16','N0','Nm','G512']
    assert [r['pass_id'] for r in rows[:6]] == ['pass0','pass1','pass1','pass0','pass0','pass1']
    assert sum(r['pass_id']=='pass1' for r in rows) == 15
    with pytest.raises(ValueError): p.schedule('batch-test', blocks=4)


@pytest.mark.parametrize('condition,variant', [('G32',None),('G512',None),('N0','V0'),('Nm','Vmarker'),('N16','Vsync')])
def test_closed_role_declaration_and_conflict(condition,variant):
    p=pilot(); binding=next(r for r in p.schedule('batch') if r['condition']==condition)
    manifest=p.minimal_fields(binding)
    assert manifest['run_role']=='PILOT' and manifest['data_role']=='Pilot'
    assert p.validate(manifest)==binding
    assert binding['variant']==variant
    for field,value in [('run_role','ENGINEERING'),('data_role','Formal'),('run_id','other'),('fixed_input_tokens',77)]:
        bad=deepcopy(manifest); bad[field]=value
        with pytest.raises(ValueError): p.validate(bad)
    bad=deepcopy(manifest); bad['pilot']['pass_id']='invalid'
    with pytest.raises(ValueError): p.validate(bad)


@pytest.mark.parametrize('variant,condition,count', [('V0','N0',0),('Vmarker','Nm',1),('Vsync','N16',1)])
@pytest.mark.parametrize('pass_id',['pass0','pass1'])
def test_real_verified_n1_pilot_producer_keeps_interventions_and_host_tokens(tmp_path,monkeypatch,variant,condition,count,pass_id):
    from test_n1_verified_entry import source
    p=pilot(); entry,args,state,events=source(tmp_path,monkeypatch,variant)
    manifest=json.loads(args['manifest_path'].read_text())
    binding=next(r for r in p.schedule('cpu-batch') if r['condition']==condition and r['pass_id']==pass_id)
    manifest.update(p.minimal_fields(binding)); write_json(args['manifest_path'],manifest)
    report=entry.run_diagnostic(**args)
    root=report.parent
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    assert ledger['schema_version']=='exposedpath-pass-identity/0.2.0'
    assert ledger['pilot']==binding and ledger['run_role']=='PILOT' and ledger['pass_id']==pass_id
    calls=json.loads((root/'n1_model_calls.json').read_text())['requests']
    assert [len(c['interventions']) for c in calls]==[count,count]
    assert [sum(i['synchronize_called'] for i in c['interventions']) for c in calls]==[int(variant=='Vsync')]*2
    tokens=json.loads((root/'pilot_tokens.json').read_text())
    assert tokens['requests'][0]['token_ids']==[[13],[14]]
    assert tokens['requests'][0]['identity']==ledger['requests'][1]['identity']
    execution=json.loads((root/'engineering_execution.json').read_text())
    assert execution['pilot']==binding and execution['data_role']=='Pilot'
    assert execution['pilot_tokens_sha256']==p.sha(root/'pilot_tokens.json')
    assert json.loads(report.read_text())['pilot']==binding
    assert state['loads']==1


def test_engineering_cannot_be_relabelled_with_old_pass_schema(tmp_path,monkeypatch):
    from test_n1_verified_entry import source
    from exposedpath.gate8_identity import validate_pass_identity
    entry,args,_,_=source(tmp_path,monkeypatch,'V0'); report=entry.run_diagnostic(**args)
    ledger=json.loads((report.parent/'producer/pass_identity.json').read_text())
    ledger.update(run_role='PILOT',data_role='Pilot')
    with pytest.raises(ValueError): validate_pass_identity(ledger)


@pytest.mark.parametrize('stop',[None,0,7,29])
def test_batch_partial_stop_no_retry_or_budget_extension(tmp_path,stop):
    from scripts import gate11_pilot_batch as batch
    calls=[]
    def execute(binding,path):
        calls.append(binding)
        path.mkdir(); write_json(path/'partial.json',{'called':True})
        if len(calls)-1==stop: raise RuntimeError('deliberate failure')
        return {'status':'RUN_COMPLETE_PENDING_REVIEW','binding':binding}
    def pair(a,b,path):
        return {'status':'PAIR_COMPLETE_PENDING_REVIEW','pair_id':a['binding']['pair_id']}
    out=tmp_path/'batch'
    result=batch.run_batch(out,'cpu-batch',execute,pair)
    assert len(calls)==(30 if stop is None else stop+1)
    assert result['status']==('FIRST_BATCH_COMPLETE_STOP_FOR_REVIEW' if stop is None else 'BLOCKED')
    assert len(result['runs'])==30 and result['gate11_verdict']=='NOT_RUN'
    assert result['automatic_retry'] is False
    if stop is not None:
        assert all(r['status']=='NOT_RUN' for r in result['runs'][stop+1:])
        assert (out/pilot().schedule('cpu-batch')[stop]['run_id']/'partial.json').is_file()
    with pytest.raises(FileExistsError): batch.run_batch(out,'cpu-batch',execute,pair)


def test_changed_callback_run_identity_stops_before_next_process(tmp_path):
    from scripts import gate11_pilot_batch as batch
    calls=[]
    def execute(binding,path):
        calls.append(binding); b=deepcopy(binding); b['run_id']='other'
        return {'status':'RUN_COMPLETE_PENDING_REVIEW','binding':b}
    result=batch.run_batch(tmp_path/'out','cpu-batch',execute,lambda *a:None)
    assert len(calls)==1 and result['status']=='BLOCKED'


@pytest.mark.parametrize('damage',['environment','g512_tokens'])
def test_batch_rejects_cross_pair_drift(tmp_path,damage):
    from scripts import gate11_pilot_batch as batch
    def execute(b,path): return dict(status='RUN_COMPLETE_PENDING_REVIEW',binding=b)
    def pair(a,b,path):
        row=a['binding']; later=row['block']==2
        return dict(status='PAIR_COMPLETE_PENDING_REVIEW',pair_id=row['pair_id'],condition=row['condition'],
            token_ids=[[9 if later and damage=='g512_tokens' and row['condition']=='G512' else 8],[7]],
            environment={'driver':'changed' if later and damage=='environment' else 'fixed'})
    result=batch.run_batch(tmp_path/'out','cpu-batch',execute,pair)
    assert result['status']=='BLOCKED'
    assert ('ENVIRONMENT' if damage=='environment' else 'TOKEN') in result['error']
    assert sum(r['status']=='NOT_RUN' for r in result['runs'])>0


@pytest.mark.parametrize('pass_id',['pass0','pass1'])
def test_g512_real_entry_and_no_n1_intervention(tmp_path,monkeypatch,pass_id):
    from test_n1_verified_entry import source
    from exposedpath import runner
    from types import SimpleNamespace
    entry,args,state,events=source(tmp_path,monkeypatch,'V0')
    p=pilot(); binding=next(r for r in p.schedule('cpu-batch') if r['condition']=='G512' and r['pass_id']==pass_id)
    manifest=json.loads(args['manifest_path'].read_text()); manifest.pop('n1_model'); manifest.pop('n1_model_execution')
    manifest.update(p.minimal_fields(binding))
    prompt=json.loads(args['prompt_path'].read_text()); prompt['fixed_input_tokens']=512
    prompt['samples']=[dict(input_ids=[1]*512,attention_mask=[1]*512)]
    write_json(args['prompt_path'],prompt); manifest['prompt_tokens_sha256']=p.sha(args['prompt_path'])
    modeldir=tmp_path/'model'; modeldir.mkdir(); write_json(modeldir/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=1024))
    manifest['model_id']=str(modeldir); write_json(args['manifest_path'],manifest)
    monkeypatch.setattr(runner.torch,'tensor',lambda data,**kw:SimpleNamespace(shape=(len(data),len(data[0]))))
    report=entry.run_diagnostic(**args)
    assert json.loads(report.read_text())['status']=='DIAGNOSTIC_COMPLETE'
    assert not (report.parent/'n1_model_calls.json').exists()
    assert json.loads((report.parent/'workload_observed.json').read_text())['observations'][0]['actual_input_tokens']==512


def test_progress_retains_raw_invalid_utf8_bytes(tmp_path,capsys):
    import sys
    from scripts.gate8_diagnostic_collect import run_once
    result=run_once([sys.executable,'-c',"import sys;sys.stdout.buffer.write(b'[stage] test COMPLETE\\n\\xff');sys.stdout.flush()"],tmp_path/'log',progress=True)
    assert result['status']=='COMPLETE'
    assert (tmp_path/'log/stdout.txt').read_bytes()==b'[stage] test COMPLETE\n\xff'
    assert '[stage] test COMPLETE' in capsys.readouterr().out


@pytest.mark.parametrize('condition,variant', [('G32','V0'),('N0','V0'),('Nm','Vmarker'),('N16','Vsync')])
def test_pilot_producer_raw_canonical_domain_chain_with_independent_expected_members(tmp_path,monkeypatch,condition,variant):
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    b=next(r for r in pilot().schedule('cpu-trace') if r['condition']==condition and r['pass_id']=='pass1')
    receipt,execution,calls=source(tmp_path,monkeypatch,variant,pilot_binding=b)
    kwargs={} if condition=='G32' else dict(bridge_path=calls)
    path=process_domain(receipt,execution,tmp_path/'derived',**kwargs)
    value=load_domain(path,receipt,execution,**kwargs)
    assert value['pilot']==b and value['data_role']=='Pilot'
    assert value['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
    assert value['measurement_validity']=='NOT_ASSESSED' and value['dropped_records_status']=='UNKNOWN'
    assert not value['formal_eligible'] and not value['d_score_allowed']
    if condition!='G32':
        assert sorted(len(x['wait_set_activity_ids']) for x in value['b_records'])==([3,5,6] if variant=='Vsync' else [3,6])
    a=value['requests'][0]['a_records']
    assert len(a)==3 and all(x['A_unattributed_ns']==0 for x in a)
    assert next(x for x in a if x['phase']=='full_request')['A_cuda_api_ns']==60


@pytest.mark.parametrize('damage',['correlation','warning','boundary','drain','thread','stream'])
def test_pilot_keeps_scientific_refusals(tmp_path,monkeypatch,damage):
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain
    b=next(r for r in pilot().schedule('cpu-trace') if r['condition']=='N16' and r['pass_id']=='pass1')
    receipt,execution,calls=source(tmp_path,monkeypatch,'Vsync',pilot_binding=b,damage=damage)
    with pytest.raises(ValueError): process_domain(receipt,execution,tmp_path/'derived',bridge_path=calls)
    assert not (tmp_path/'derived/domain.json').exists()


@pytest.mark.parametrize('condition',['G32','G512','N0','Nm','N16'])
def test_actual_prepare_to_verified_cpu_entry(tmp_path,monkeypatch,condition):
    from test_n1_verified_entry import source
    from exposedpath import platform_adapter,manifest as manifests
    from exposedpath_v141 import gate8_source_probe,gate8_target_python as target
    from types import SimpleNamespace
    p=pilot(); binding=next(r for r in p.schedule('prepared') if r['condition']==condition and r['pass_id']=='pass0')
    entry,args,state,events=source(tmp_path,monkeypatch,binding['variant'] or 'V0')
    model=tmp_path/'model';model.mkdir()
    write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=1024))
    length=p.CONDITIONS[condition][0]
    prompt=json.loads(args['prompt_path'].read_text()); prompt['fixed_input_tokens']=length
    prompt['samples']=[dict(input_ids=[1]*length,attention_mask=[1]*length)]
    write_json(args['prompt_path'],prompt)
    inventory=tmp_path/'model_inventory.csv'; inventory.write_text('CPU fixture inventory')
    monkeypatch.setattr(platform_adapter,'git',lambda argv,**kw:'c'*40 if argv[-1]=='HEAD' else '')
    monkeypatch.setattr(manifests,'_get_nvidia_driver',lambda:'CPU_DOUBLE')
    monkeypatch.setattr(target,'probe',lambda *a:{'cpu_fixture':True})
    from exposedpath import runner
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(cuda=runner.torch.cuda,
        identity=lambda:dict(gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='0000:01:00.0')))
    monkeypatch.setattr(entry,'verify_model_inventory',lambda *a,**kw:{'inventory_sha256':p.sha(inventory)})
    prepared=entry.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,
        inventory_path=inventory,inventory_sha256=p.sha(inventory),prompt_path=args['prompt_path'],
        prompt_sha256=p.sha(args['prompt_path']),expected_commit='c'*40,physical_gpu=3,
        engineering_attention_backend='sdpa',target_python='cpu-double',site_root='cpu-site',pilot_binding=binding)
    args.update(manifest_path=prepared/'manifest.json',prompt_path=prepared/'prompt.json',preflight_path=prepared/'preflight.json')
    result=entry.run_diagnostic(**args)
    assert json.loads(result.read_text())['status']=='DIAGNOSTIC_COMPLETE'
    assert json.loads((result.parent/'producer/pass_identity.json').read_text())['pilot']==binding
    assert state['loads']==1
