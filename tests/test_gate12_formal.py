"""Synthetic signatures only; no real protocol approval or CUDA qualification."""
from copy import deepcopy
import hashlib
import json
import pytest


def release():
    from exposedpath.formal_protocol import REQUIRED_ARTIFACTS
    from pathlib import Path
    # Test authority only. Production never creates a SIGNED approval.
    p = dict(version='G12-ROUTEA/0.1', status='FREEZE_CANDIDATE',
             execution_commit='a'*40, analysis_commit='a'*40,
             artifact_hashes={name:hashlib.sha256(Path(name).read_bytes().replace(b'\r\n',b'\n')).hexdigest() for name in REQUIRED_ARTIFACTS},
             warmup_count=3, blocks=6, input_hashes={'G32':'c'*64,'G512':'d'*64},
             execution_constraints=cpu_constraints(),
             supported_domains=['G1_NATURAL_PROJECTED_A/0.1.0','N1_EXPLICIT_STREAM_AB/0.1.0'],
             claims=['P0_PERFORMANCE','P1_ACCOUNTING_AND_SINGLE_SYNC_B'],
             p0_composition_transfer=False, d_signature=False)
    raw=(json.dumps(p,sort_keys=True,separators=(',',':'))+'\n').encode()
    a=dict(version='exposedpath-protocol-approval/0.1.0',status='SIGNED',
           protocol_sha256=hashlib.sha256(raw).hexdigest(),authority='HUMAN_USER',
           signed_at='2026-10-02T00:00:00Z',approval_id='synthetic-test-only',
           scope='LIMITED_ROUTE_A',budget_approved=True)
    return p,a


def cpu_constraints():
    # Explicit synthetic device/software facts, not values from the protocol.
    import platform,torch
    from test_gate8_identity import UUID
    return dict(model_inventory_sha256='a'*64,gpu=dict(physical_index=3,logical_index=0,
        uuid=UUID,pci='0000:E1:00.0'),software=dict(nvidia_driver_version='CPU_TEST_NO_DRIVER',
        cuda_version_used=torch.version.cuda or 'unknown',inference_framework_version='torch'+torch.__version__,
        runtime_version='python'+platform.python_version()),collector_version='2026.2.1.210')


def observed_cpu_manifest(m):
    c=cpu_constraints()
    m.update(c['software'],model_content_snapshot={'inventory_sha256':'a'*64},
        gpu_index_physical=3,gpu_index_logical=0,gpu_uuid=c['gpu']['uuid'],gpu_pci_bus_id=c['gpu']['pci'])
    return m


def binding(condition='N16',pass_id='pass1',block=1):
    from exposedpath import formal_protocol as f
    p,a=release()
    return f.make_binding(p,a,batch_id='new-formal',block=block,condition=condition,
                          pass_id=pass_id,declared_at='2026-10-03T00:00:00Z')


def test_unsigned_candidate_never_admits_formal():
    from exposedpath import formal_protocol as f
    p,a=release(); a['status']='PENDING_USER_SIGNATURE'
    with pytest.raises(ValueError,match='UNSIGNED'):
        f.make_binding(p,a,batch_id='new',block=1,condition='G32',pass_id='pass1',declared_at='2026-10-03T00:00:00Z')


@pytest.mark.parametrize('damage',['hash','commit','claim','time','role','pair','legacy'])
def test_formal_role_is_not_a_relabel_or_loose_signature(damage):
    from exposedpath import formal_protocol as f
    from exposedpath.gate11_pilot import roles
    b=binding(); m=observed_cpu_manifest(f.minimal_fields(b))
    m.update(runner_git_commit='a'*40,runner_git_dirty=False,prompt_tokens_sha256='c'*64)
    if damage=='hash': m['formal']['approval']['protocol_sha256']='0'*64
    if damage=='commit': m['runner_git_commit']='e'*40
    if damage=='claim': m['formal']['protocol']['p0_composition_transfer']=True
    if damage=='time': m['formal']['declared_at']='2026-10-01T00:00:00Z'
    if damage=='role': m['data_role']='Pilot'
    if damage=='pair': m['formal']['run_id']='wrong'
    if damage=='legacy': m['pilot']={'version':'G11-LIMITED-PILOT/0.1'}
    with pytest.raises(ValueError): roles(m)


def test_formal_producer_and_nvtx_bind_signed_protocol():
    from exposedpath import formal_protocol as f
    from exposedpath.gate8_identity import make_gate8_pass_identity,validate_pass_identity
    from exposedpath.nvtx import make_natural_token_ready_identity
    b=binding('G32'); ref=f.reference(b)
    ledger=make_gate8_pass_identity(formal=b,experiment_id='e',wmpc_id='w',run_id=b['run_id'],
        run_role='FORMAL',data_role='Formal',pass_id='pass1',attempt_id='a',pid=3,
        wmpc_manifest_sha256='e'*64,prompt_sha256='c'*64,runner_source_sha256='f'*64,
        runner_git_commit='a'*40,runner_git_dirty=False,requests=[dict(
            request_id='request-0',repeat_id='0',request_role='measured',expected_output_tokens=2,
            actual_output_tokens=2,expected_boundary_ids=['r','t0','t1'],observed_boundary_ids=['r','t0','t1'],
            outcome='COMPLETE',early_eos=False,reasons=[])])
    identity=ledger['requests'][0]['identity']
    assert identity['formal_reference']==ref
    label=make_natural_token_ready_identity(identity,phase='prefill',token_index=0,
        callsite_id='token',sync_ordinal=0,token_ready_mechanism='device_to_host_token_ids')
    assert label['formal_reference']==ref
    broken=deepcopy(ledger); broken['requests'][0]['identity']['formal_reference']['protocol_sha256']='0'*64
    with pytest.raises(ValueError):validate_pass_identity(broken)


@pytest.mark.parametrize('condition',['G32','N0','Nm','N16'])
def test_signed_producer_to_canonical_and_domain_real_files(tmp_path,monkeypatch,condition):
    from test_n1_model_domain import source
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    b=binding(condition)
    receipt,execution,calls=source(tmp_path,monkeypatch,b['variant'] or 'V0',formal_binding=b)
    path=process_domain(receipt,execution,tmp_path/'formal-result',
        **({'bridge_path':calls} if b['variant'] else {}))
    value=load_domain(path,receipt,execution,**({'bridge_path':calls} if b['variant'] else {}))
    assert value['formal_admission']['status']=='ADMITTED_LIMITED_PROTOCOL'
    assert value['formal_eligible'] is False  # Never a global scientific certificate.
    assert value['measurement_validity']=='NOT_ASSESSED' and value['dropped_records_status']=='UNKNOWN'
    canonical=json.loads((path.parent/'canonical/canonical_manifest.json').read_text())
    assert canonical['formal_reference']==value['formal_admission']['reference']


def test_old_raw_role_cannot_be_promoted_to_formal(tmp_path,monkeypatch):
    from test_n1_model_domain import source
    from exposedpath_v141.gate8_files import write_input_receipt
    from test_gate8_identity import write_json
    receipt,_,_=source(tmp_path,monkeypatch,'V0')
    original=json.loads(receipt.read_text());root=receipt.parent
    mpath=root/original['artifacts']['wmpc_manifest']['filename']
    m=json.loads(mpath.read_text());m.update(run_role='FORMAL',data_role='Formal')
    write_json(mpath,m)
    artifacts={k:root/v['filename'] for k,v in original['artifacts'].items()}
    with pytest.raises(ValueError):write_input_receipt(tmp_path/'upgraded.json',artifacts=artifacts,
        collector_version='2026.2.1.210',capture_session_id='CPU')


@pytest.mark.parametrize('damage',['unsigned','wrong_hash'])
def test_prepare_unsigned_or_bad_content_stops_before_any_device_probe(tmp_path,monkeypatch,damage):
    from exposedpath.gate8_diagnostic import prepare_diagnostic
    b=binding()
    if damage=='unsigned':b['approval']['status']='PENDING_USER_SIGNATURE'
    else:b['protocol']['artifact_hashes']['docs/v1_4_1/contracts/a_api_registry_v0_2.json']='0'*64
    with pytest.raises(ValueError,match='FORMAL_'):
        prepare_diagnostic(output_dir=tmp_path/'out',model_path=tmp_path/'no-model',
            inventory_path=tmp_path/'none',inventory_sha256='a'*64,prompt_path=tmp_path/'none',
            prompt_sha256='c'*64,expected_commit='a'*40,physical_gpu=3,
            engineering_attention_backend='sdpa',target_python='never',site_root='never',formal_binding=b)


def test_formal_g512_uses_declared_input_not_engineering_default():
    from exposedpath import formal_protocol as f
    from exposedpath.gate10_workload import input_length
    m=f.minimal_fields(binding('G512'))
    observed_cpu_manifest(m)
    m.update(runner_git_commit='a'*40,runner_git_dirty=False,prompt_tokens_sha256='d'*64)
    assert input_length(m)==512


@pytest.mark.parametrize('damage',['missing','tampered','escape','empty'])
def test_artifact_content_lock_is_not_shape_only(tmp_path,damage):
    from exposedpath.formal_protocol import validate_artifacts
    data=b'line1\nline2\n';(tmp_path/'source.py').write_bytes(data.replace(b'\n',b'\r\n'))
    p={'artifact_hashes':{'source.py':hashlib.sha256(data).hexdigest()}}
    if damage=='missing':(tmp_path/'source.py').unlink()
    if damage=='tampered':(tmp_path/'source.py').write_bytes(b'changed\r\n')
    if damage=='escape':p['artifact_hashes']={'../source.py':hashlib.sha256(data).hexdigest()}
    if damage=='empty':p['artifact_hashes']={}
    with pytest.raises(ValueError):validate_artifacts(tmp_path,p)


def test_actual_bytes_separate_from_explicit_crlf_source_proof(tmp_path):
    from exposedpath.formal_protocol import validate_artifacts
    data=b'# same source\n';lf=hashlib.sha256(data).hexdigest()
    (tmp_path/'source.py').write_bytes(data)
    p={'artifact_hashes':{'source.py':lf}}
    assert validate_artifacts(tmp_path,p)['source.py']['representation']=='EXACT'
    crlf=data.replace(b'\n',b'\r\n');(tmp_path/'source.py').write_bytes(crlf)
    v=validate_artifacts(tmp_path,p)['source.py']
    assert v['git_content_sha256']==lf and v['actual_sha256']==hashlib.sha256(crlf).hexdigest()
    assert v['representation']=='CRLF_GIT_CONTENT_EQUIVALENT'


@pytest.mark.parametrize('damage',[None,'unsigned','source','gpu','model'])
def test_signed_prepared_real_seal_reaches_only_cpu_profile_boundary(tmp_path,monkeypatch,damage):
    from test_n1_preprofile_identity import prepared_case
    from test_gate8_identity import sha,write_json
    from pathlib import Path
    from exposedpath import formal_protocol as f,gate8_isolated_preflight as isolated,platform_adapter
    from scripts import gate8_diagnostic_collect as collector
    import subprocess,sys
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    for name in f.REQUIRED_ARTIFACTS:
        if name=='exposedpath/runner.py':continue
        dest=root/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(Path(name).read_bytes())
    p,a=release();p['artifact_hashes']={name:sha(root/name) for name in f.REQUIRED_ARTIFACTS}
    p['input_hashes']['G32']=sha(prepared/'prompt.json')
    a['protocol_sha256']=f.content_hash(p)
    b=f.make_binding(p,a,batch_id='cpu-seal',block=1,condition='N0',pass_id='pass1',declared_at='2026-10-03T00:00:00Z')
    m.update(f.minimal_fields(b));observed_cpu_manifest(m)
    m.update(gpu_uuid='GPU-12345678-1234-1234-1234-123456789abc',gpu_pci_bus_id='00000000:E1:00.0')
    write_json(prepared/'preflight.json',dict(physical_gpu_index=3,logical_gpu_index=0,
        gpu_uuid=m['gpu_uuid'],gpu_pci_bus_id=m['gpu_pci_bus_id']))
    monkeypatch.setattr(platform_adapter,'nvidia_smi',lambda *args,**kw:'3, GPU-12345678-1234-1234-1234-123456789abc, 00000000:E1:00.0')
    if damage=='unsigned':m['formal']['approval']['status']='PENDING'
    if damage=='source':(root/'exposedpath/runner.py').write_bytes(b'changed')
    if damage=='gpu':m['gpu_index_physical']=2
    if damage=='model':m['model_content_snapshot']['inventory_sha256']='0'*64
    write_json(prepared/'manifest.json',m)
    nsys=tmp_path/'never_nsys.exe';nsys.touch();out=tmp_path/'out'
    monkeypatch.setattr(collector,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['collect','--nsys',str(nsys),'--python',sys._base_executable,
        '--prepared',str(prepared),'--output',str(out),'--execute-engineering-diagnostic','--engineering-domain','--signed-formal-protocol'])
    monkeypatch.setattr(collector.subprocess,'run',lambda *args,**kw:subprocess.CompletedProcess(args[0],0,'NVIDIA Nsight Systems version 2026.2.1.210',''))
    called=[]
    def stop(argv,*args,**kw):
        called.append(argv);assert argv[1]=='profile' and 'model-run' in argv
        receipt=out/'auxiliary_preflight.json';s=isolated.read(receipt)
        assert s['execution_contract']==f.VERSION
        claim=isolated.consume(receipt=receipt,expected_sha=sha(receipt),nonce=s['nonce'],prepared=prepared,output=out,root=root)
        assert claim['run_id']==b['run_id']
        return dict(status='BLOCKED',reason='CPU_STOP_BEFORE_ANY_REAL_PROFILE')
    monkeypatch.setattr(collector,'run_once',stop)
    if damage is None:
        assert collector.main()==1 and len(called)==1
        assert json.loads((out/'collection_report.json').read_text())['formal']==b
    else:
        with pytest.raises(ValueError):collector.main()
        assert called==[]


@pytest.mark.parametrize('damage',[None,'tokens','unsigned','missing'])
def test_formal_real_paired_execution_consumer(tmp_path,monkeypatch,damage):
    from test_gate11_pilot_files import pair_files
    from scripts.gate8_pair import inspect_execution
    rows=pair_files(tmp_path,monkeypatch,'N16',[binding('N16',pid) for pid in ('pass0','pass1')])
    from pathlib import Path
    root=Path(rows[0]['output'])/'diagnostic'
    if damage=='tokens':
        path=root/'formal_tokens.json';v=json.loads(path.read_text());v['requests'][0]['token_ids'][0]=[99];path.write_text(json.dumps(v))
    if damage=='unsigned':
        path=root/'manifest.json';v=json.loads(path.read_text());v['formal']['approval']['status']='PENDING';path.write_text(json.dumps(v))
    if damage=='missing':(root/'producer/drain_ledger.json').unlink()
    if damage is not None:
        with pytest.raises((ValueError,FileNotFoundError)):inspect_execution(rows[0]['output'],'pass0')
    else:
        value=inspect_execution(rows[0]['output'],'pass0')
        assert value['formal']['condition']=='N16' and len(value['warmups'])==3
        assert value['token_ids']==json.loads((root/'formal_tokens.json').read_text())['requests'][0]['token_ids']
