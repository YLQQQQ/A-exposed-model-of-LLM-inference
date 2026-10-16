"""Real COE file consumers with explicit synthetic process/collector boundaries."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from test_gate8_identity import sha,write_json
from test_coe_pilot import api,binding,prompt


def collection(tmp_path,monkeypatch):
    from test_n1_model_domain import source
    from analysis.coe_pilot import process
    from scripts.coe_pilot_batch import consume_collection
    api()
    receipt,execution,_=source(tmp_path,monkeypatch,pilot_binding=binding())
    target=tmp_path
    (target/'input_receipt.json').write_bytes(receipt.read_bytes())
    result=process(target/'input_receipt.json',execution,target/'analyzed')
    ledger=json.loads((target/'diagnostic/producer/pass_identity.json').read_text())
    write_json(target/'target_launch.json',dict(pid=ledger['pid'],role='CPU_TRACE_RECORDER_NOT_GPU'))
    (target/'diagnostic-entry').mkdir()
    write_json(target/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=0,pid=ledger['pid']))
    write_json(target/'collection_report.json',dict(schema_version='coe-pilot-collection/0.1.0',
        status='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW',qualification='NOT_QUALIFIED',
        scientific_outputs_allowed=False,export_status='PASS',result_filename='prefill.json',
        run_role='PILOT',data_role='Pilot',pilot=binding(),q0_status='NOT_RUN',
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        collection=dict(status='COMPLETE',exit_code=0,timed_out=False),result_sha256=sha(result),
        manifest_sha256=sha(target/'diagnostic/manifest.json'),
        target_runtime_sha256=sha(target/'diagnostic/target_runtime.json'),target_launch_sha256=sha(target/'target_launch.json')))
    return target,consume_collection


@pytest.mark.parametrize('damage',[None,'report_version','result_hash','missing_result','role','pid','token','binding'])
def test_actual_producer_to_result_consumer(tmp_path,monkeypatch,damage):
    target,consume=collection(tmp_path,monkeypatch)
    if damage in ('report_version','result_hash','role'):
        path=target/'collection_report.json';v=json.loads(path.read_text())
        k,value={'report_version':('schema_version','future'),'result_hash':('result_sha256','0'*64),
                 'role':('data_role','Formal')}[damage]
        v[k]=value;write_json(path,v)
    elif damage=='missing_result':(target/'analyzed/prefill.json').unlink()
    elif damage=='pid':write_json(target/'diagnostic-entry/exit.json',dict(status='EXITED',exit_code=0,pid=-1))
    elif damage=='token':
        path=target/'diagnostic/pilot_tokens.json';v=json.loads(path.read_text());v['requests'][0]['token_ids'][0][1]=None;write_json(path,v)
    b=binding()
    if damage=='binding':b['run_id']='wrong-run'
    if damage:
        with pytest.raises((ValueError,FileNotFoundError)):consume(target,b,'a'*40)
    else:
        r=consume(target,b,'a'*40)
        assert r['token_ids']==[[17,17],[18,18]] and r['coe']['candidate_ns']==2
        assert r['baseline']['gpu_activity']['status']=='KNOWN'


@pytest.mark.parametrize('batch',[1,2,4])
def test_actual_prepare_binds_whole_input_before_seal(tmp_path,monkeypatch,batch):
    import sys,sysconfig,csv
    from exposedpath import platform_adapter,gate8_diagnostic as entry
    from exposedpath_v141 import gate8_source_probe
    api()
    monkeypatch.setenv('CUDA_VISIBLE_DEVICES','3');monkeypatch.setenv('CUDA_DEVICE_ORDER','PCI_BUS_ID')
    monkeypatch.setattr(platform_adapter,'git',lambda argv,**kw:'' if 'status' in argv else 'a'*40)
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *a,**kw:'555.99')
    monkeypatch.setattr(gate8_source_probe,'TorchBackend',lambda:SimpleNamespace(identity=lambda:dict(
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',pci_bus_id='00000000:01:00.0')))
    model=tmp_path/'model';model.mkdir();config=write_json(model/'config.json',dict(model_type='qwen2',vocab_size=100,max_position_embeddings=4096))
    inventory=tmp_path/'model.csv'
    with inventory.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=['RelativePath','Bytes','SHA256']);w.writeheader()
        w.writerow(dict(RelativePath='config.json',Bytes=config.stat().st_size,SHA256=sha(config)))
    p=write_json(tmp_path/'prompt.json',prompt(batch))
    prepared=entry.prepare_diagnostic(output_dir=tmp_path/'prepared',model_path=model,inventory_path=inventory,
        inventory_sha256=sha(inventory),prompt_path=p,prompt_sha256=sha(p),expected_commit='a'*40,
        physical_gpu=3,engineering_attention_backend='sdpa',target_python=sys._base_executable,
        site_root=sysconfig.get_path('purelib'),pilot_binding=binding(batch))
    mf=json.loads((prepared/'manifest.json').read_text())
    assert mf['coe_input']==api().input_identity(prompt(batch))
    assert mf['prompt_tokens_sha256']==sha(prepared/'prompt.json') and mf['batch_size']==batch
    api().validate_prepared(mf,prepared,Path(entry.__file__).resolve().parents[1])


def test_runtime_entry_nine_slots_uses_real_prepare_and_consume_boundaries(tmp_path,monkeypatch):
    from scripts import coe_pilot_batch as driver,gate8_diagnostic_collect as collector
    from exposedpath import platform_adapter,gate8_diagnostic as entry
    m=api();seed=write_json(tmp_path/'seed.json',prompt(1));nsys=tmp_path/'nsys.exe';nsys.write_bytes(b'CPU not nsys')
    cfg=dict(schema_version='coe-pilot-delivery/0.1',commit='a'*40,analysis_commit='a'*40,
        model_process_budget=9,profile_budget=9,batch_id='cpu-coe',seed_input=str(seed),prompt_512_sha256=sha(seed),
        nsys=str(nsys),nsys_sha256=sha(nsys),model='CPU',inventory='CPU',inventory_sha256='f'*64,
        code_root=str(driver.ROOT),target_python='CPU-PYTHON',site_root='CPU-SITE',
        gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='0000:E1:00.0')
    monkeypatch.setattr(platform_adapter,'git',lambda argv:'' if 'status' in argv else 'a'*40)
    calls=[];prepared={}
    def prepare(**kw):
        # Boundary double verifies actual new arguments and real batched input.
        b=kw['pilot_binding'];p=Path(kw['prompt_path']);v=json.loads(p.read_text())
        assert len(v['samples'])==b['batch_size'] and all(len(s['input_ids'])==512 for s in v['samples'])
        folder=Path(kw['output_dir']);folder.mkdir();prepared[str(folder)]=b
        write_json(folder/'manifest.json',dict(gpu_uuid=cfg['gpu_uuid'],gpu_pci_bus_id=cfg['gpu_pci_bus_id']))
        return folder
    def collect(argv,*a,**kw):
        assert '--pilot' in argv and '--engineering-a-only' in argv
        assert '--signed-formal-protocol' not in argv
        calls.append(prepared[argv[argv.index('--prepared')+1]])
        return dict(status='COMPLETE',exit_code=0,timed_out=False)
    def consume(target,b,commit):
        assert b==calls[-1] and commit=='a'*40
        return dict(status='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW',binding=b,token_ids=[[17]*b['batch_size'],[18]*b['batch_size']],
                    coe={'candidate_ns':{1:10,2:7,4:3}[b['batch_size']]},result_sha256='f'*64)
    monkeypatch.setattr(entry,'prepare_diagnostic',prepare);monkeypatch.setattr(collector,'run_once',collect)
    monkeypatch.setattr(driver,'consume_collection',consume)
    r=driver.run(cfg,tmp_path/'out',execute=True)
    assert r['status']=='FIXED_NINE_COMPLETE_STOP_FOR_REVIEW' and len(calls)==9
    assert [b['batch_size'] for b in calls]==[1,2,4,2,4,1,4,1,2]
    assert [b['b4_minus_b1_candidate_ns'] for b in r['blocks']]==[-7]*3


def test_actual_collector_postexport_dispatch_uses_local_candidate_not_domain(tmp_path,monkeypatch):
    import os,sys,sysconfig,shutil
    from exposedpath_v141 import gate8_target_python as target
    from test_n1_model_domain import source
    from scripts import gate8_diagnostic_collect as collector
    from analysis import coe_pilot # preload before the explicit OS doubles
    api();probe=target.probe(sys._base_executable,sysconfig.get_path('purelib'))
    receipt,execution,_=source(tmp_path,monkeypatch,pilot_binding=binding(),collector_contract=probe)
    for old,new in [('synthetic.rep','capture.nsys-rep'),('trace.sqlite','capture.sqlite'),('export.json','postprocess_report.json')]:
        shutil.copyfile(tmp_path/old,tmp_path/new)
    from exposedpath.gate8_isolated_preflight import VERSION
    aux=write_json(tmp_path/'auxiliary_preflight.json',dict(schema_version=VERSION,run_id=binding()['run_id'],nonce='cpu'))
    claim=dict(target_pid=os.getpid(),nonce='cpu',preflight_sha256=sha(aux))
    write_json(tmp_path/'auxiliary_preflight.claim.json',claim)
    write_json(tmp_path/'diagnostic/isolated_preflight_target.json',claim)
    write_json(tmp_path/'auxiliary_preflight.final.json',dict(status='PASS',preflight_sha256=sha(aux),
        target_claim_sha256=sha(tmp_path/'auxiliary_preflight.claim.json')))
    result=collector.analyze_model(tmp_path,tmp_path,'2026.2.1.210')
    r=json.loads(result.read_text())
    assert r['status']=='COE_PILOT_PREFILL_ONLY_PENDING_REVIEW' and r['coe']['candidate_ns']==2
    assert not list(tmp_path.rglob('domain.json'))


def test_review_launcher_parses_in_windows_powershell51_without_execution():
    import os,subprocess
    if os.name!='nt':pytest.skip('Windows-only deployment parser; no Linux support claimed')
    path=Path(__file__).resolve().parents[1]/'scripts/run_coe_candidate_pilot.ps1'
    script="$e=$null;$t=$null;[System.Management.Automation.Language.Parser]::ParseFile($args[0],[ref]$t,[ref]$e)|Out-Null;if($e.Count){$e;exit 1};$PSVersionTable.PSVersion.ToString()"
    # Command is fixed except the literal path; parser never invokes the file.
    script=script.replace('$args[0]',"'"+str(path).replace("'","''")+"'")
    p=subprocess.run(['powershell.exe','-NoProfile','-Command',script],capture_output=True,text=True,timeout=30)
    assert p.returncode==0 and p.stdout.strip().startswith('5.1.')
    text=path.read_text()
    assert 'param([switch]$CollectReviewedPilot' in text
    assert 'ReviewedStaticReceiptSHA256' in text and '50000000000' in text
    assert "'--collect-reviewed-coe-pilot'" in text
