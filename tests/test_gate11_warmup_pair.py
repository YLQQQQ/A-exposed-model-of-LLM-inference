"""Common-w3 producer/file-chain checks; devices, model and Raw are CPU doubles."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from test_gate8_identity import write_json


def api():
    assert importlib.util.find_spec('exposedpath.gate11_warmup_pair'), 'Missing common-w3 paired contract'
    from exposedpath import gate11_warmup_pair
    return gate11_warmup_pair


def files(tmp_path,monkeypatch,condition='N16'):
    import test_n1_model_domain as fixture
    import test_n1_model_calls as model_fixture
    from exposedpath import runner
    from test_runner_token_ready import _FakeToken
    from test_gate11_pilot_files import pair_files
    original=fixture.entry_source
    def expanded(*a,**kw):
        value=original(*a,**kw)
        handles=iter([123,124,125,456])
        monkeypatch.setattr(runner.torch.cuda,'Stream',lambda **kw:SimpleNamespace(
            cuda_stream=next(handles),device=SimpleNamespace(index=0),synchronize=lambda:None))
        return value
    monkeypatch.setattr(fixture,'entry_source',expanded)
    monkeypatch.setattr(model_fixture,'_FakeToken',lambda values,events:_FakeToken(
        [13 if values[0]%2 else 14],events))
    bindings=[b for b in api().schedule('common-w3') if b['condition']==condition and b['block']==1]
    return pair_files(tmp_path,monkeypatch,condition,bindings)


def test_fixed_budget_and_independent_orders():
    rows=api().schedule('pair3')
    assert len(rows)==30 and len({r['run_id'] for r in rows})==30
    assert [r['condition'] for r in rows[::2]]==[
        'G32','N0','Nm','N16','G512','G512','Nm','N16','N0','G32','G32','N16','N0','Nm','G512']
    assert [r['pass_id'] for r in rows[:10]]==[
        'pass0','pass1','pass1','pass0','pass0','pass1','pass1','pass0','pass0','pass1']
    assert sum(r['pass_id']=='pass1' for r in rows)==15
    assert all(r['warmup_count']==3 for r in rows)
    for field,value in [('warmup_count',1),('version','G11-LIMITED-PILOT/0.1'),
                        ('pass_order',['pass1','pass0']),('variant','Vsync'),('extra',True)]:
        bad=deepcopy(rows[0]);bad[field]=value
        with pytest.raises(ValueError):api().validate_binding(bad)


@pytest.mark.parametrize('condition',['G32','G512','N0','Nm','N16'])
def test_real_common_w3_producer_canonical_domain_and_pair(tmp_path,monkeypatch,condition):
    from scripts.gate11_pilot_batch import summarize_pair
    rows=files(tmp_path,monkeypatch,condition)
    pair=summarize_pair(*rows,tmp_path)
    assert pair['version']==api().VERSION and pair['gate11_verdict']=='BLOCKED'
    assert pair['token_ids']==[[13],[14]]
    for pass_id in ('pass0','pass1'):
        value=pair[pass_id]
        assert len(value['warmups'])==3 and [w['ordinal'] for w in value['warmups']]==[0,1,2]
        assert all(w['status']=='COMPLETE' and w['actual_output_tokens'] is None and w['early_eos'] is None
                   for w in value['warmups'])
        root=Path(next(r['output'] for r in rows if r['binding']['pass_id']==pass_id))
        ledger=json.loads((root/'diagnostic/producer/pass_identity.json').read_text())
        assert [r['identity']['request_id'] for r in ledger['requests']]==['warmup-0','warmup-1','warmup-2','request-0']
        if condition.startswith('N'):
            calls=json.loads((root/'diagnostic/n1_model_calls.json').read_text())['requests']
            assert [c['native_handle'] for c in calls]==[123,124,125,456]
            assert [len(c['interventions']) for c in calls]==[0 if condition=='N0' else 1]*4
            assert [sum(i['synchronize_called'] for i in c['interventions']) for c in calls]==[int(condition=='N16')]*4
    domain=json.loads((Path(next(r['output'] for r in rows if r['binding']['pass_id']=='pass1'))/'analyzed/domain.json').read_text())
    assert domain['pilot']['version']==api().VERSION and domain['measurement_validity']=='NOT_ASSESSED'
    assert domain['dropped_records_status']=='UNKNOWN' and not domain['formal_eligible']
    a=domain['requests'][0]['a_records']
    assert next(r for r in a if r['phase']=='full_request')['A_cuda_api_ns']==60
    if condition.startswith('N'):
        assert sorted(len(r['wait_set_activity_ids']) for r in domain['b_records'])==([3,5,6] if condition=='N16' else [3,6])
    for d in pair['overhead'].values():assert d['delta_ns']==d['pass1_ns']-d['pass0_ns']


@pytest.mark.parametrize('damage',['count','order','tokens','role','pass','variant','missing_stage','foreign_batch'])
def test_common_w3_pair_rejects_wrong_actual_files(tmp_path,monkeypatch,damage):
    from scripts.gate11_pilot_batch import summarize_pair
    rows=files(tmp_path,monkeypatch)
    root=Path(rows[0]['output'])/'diagnostic'
    if damage=='missing_stage':(root/'producer/stage_ledger.json').unlink()
    elif damage in ('count','order'):
        path=root/'producer/pass_identity.json';value=json.loads(path.read_text())
        if damage=='count':value['requests'].pop(0)
        else:value['requests'][0],value['requests'][1]=value['requests'][1],value['requests'][0]
        write_json(path,value)
    elif damage=='tokens':
        path=root/'pilot_tokens.json';value=json.loads(path.read_text());value['requests'][0]['token_ids'][1]=[98];write_json(path,value)
    else:
        path=root/'manifest.json';value=json.loads(path.read_text())
        if damage=='role':value['data_role']='Engineering'
        elif damage=='variant':value['n1_model']['variant']='V0'
        elif damage=='pass':value['pilot']['pass_id']='pass0' if value['pilot']['pass_id']=='pass1' else 'pass1'
        else:value['pilot']['batch_id']='foreign'
        write_json(path,value)
    with pytest.raises((ValueError,FileNotFoundError)):summarize_pair(*rows,tmp_path)


@pytest.mark.parametrize('stop',[None,0,7,29])
def test_fixed_pair_budget_no_retry_or_continuation(tmp_path,stop):
    api()
    from scripts.gate11_pilot_batch import run_batch
    calls=[]
    def execute(b,path):
        calls.append(b);path.mkdir();(path/'partial').touch()
        if len(calls)-1==stop:raise RuntimeError('deliberate failure')
        return dict(binding=b,status='RUN_COMPLETE_PENDING_REVIEW')
    def pair(a,b,out):return dict(pair_id=a['binding']['pair_id'],status='PAIR_COMPLETE_PENDING_REVIEW')
    result=run_batch(tmp_path/'batch','budget',execute,pair,warmup_pair=True)
    assert len(calls)==(30 if stop is None else stop+1) and not result['automatic_retry']
    assert result['gate11_verdict']=='BLOCKED'
    assert result['status']==('WARMUP3_PAIR_BATCH_COMPLETE_STOP_FOR_REVIEW' if stop is None else 'BLOCKED')
    plan=json.loads((tmp_path/'batch/planned_runs.json').read_text())
    assert plan['model_process_budget']==30 and plan['profile_budget']==15
    assert plan['cumulative_authorized_process_cap']==90
    if stop is not None:assert all(r['status']=='NOT_RUN' for r in result['runs'][stop+1:])
    with pytest.raises(FileExistsError):run_batch(tmp_path/'batch','budget',execute,pair,warmup_pair=True)


@pytest.mark.parametrize('condition',['G32','N0','Nm','N16'])
def test_preprofile_seal_uses_actual_new_version_cpu_stop(tmp_path,monkeypatch,condition):
    from test_n1_preprofile_identity import prepared_case
    from exposedpath import gate11_pilot as pilot,gate8_isolated_preflight as isolated
    root,prepared,m=prepared_case(tmp_path,monkeypatch)
    b=next(b for b in api().schedule('seal') if b['condition']==condition and b['pass_id']=='pass1')
    if not b['variant']:m.pop('n1_model');m.pop('n1_model_execution')
    m.update(pilot.minimal_fields(b));write_json(prepared/'manifest.json',m)
    out=tmp_path/'collection';out.mkdir()
    receipt=isolated.seal(prepared,out,root)
    sealed=isolated.read(receipt)
    claim=isolated.consume(receipt=receipt,expected_sha=pilot.sha(receipt),nonce=sealed['nonce'],prepared=prepared,output=out,root=root)
    assert claim['run_id']==b['run_id']


@pytest.mark.parametrize('condition',['G32','G512','N0','Nm','N16'])
def test_actual_prepare_to_verified_common_w3_entry(tmp_path,monkeypatch,condition):
    from exposedpath import gate11_pilot as pilot,runner
    import test_n1_verified_entry as fixture
    from test_gate11_pilot import test_actual_prepare_to_verified_cpu_entry as actual
    rows=api().schedule('prepared')
    monkeypatch.setattr(pilot,'schedule',lambda *a:rows)
    original=fixture.source
    def expanded(*a,**kw):
        value=original(*a,**kw);handles=iter([123,124,125,456])
        monkeypatch.setattr(runner.torch.cuda,'Stream',lambda **kw:SimpleNamespace(
            cuda_stream=next(handles),device=SimpleNamespace(index=0),synchronize=lambda:None))
        return value
    monkeypatch.setattr(fixture,'source',expanded)
    actual(tmp_path,monkeypatch,condition)


def test_second_warmup_failure_never_enters_measured(tmp_path,monkeypatch):
    import test_gate11_warmup as control
    module=api();monkeypatch.setattr(control,'api',lambda:module)
    control.test_partial_warmup_failure_stops_before_measured_and_preserves_records(tmp_path,monkeypatch)


@pytest.mark.parametrize('damage',['null_measured','invented_warmup','invented_eos','order','count'])
def test_request_semantics_rejected_even_without_hash_checks(tmp_path,monkeypatch,damage):
    from exposedpath.gate11_pilot import validate_actual_requests
    rows=files(tmp_path,monkeypatch)
    root=Path(rows[0]['output'])/'diagnostic'
    manifest=json.loads((root/'manifest.json').read_text())
    ledger=json.loads((root/'producer/pass_identity.json').read_text())
    if damage=='null_measured':ledger['requests'][-1]['actual_output_tokens']=None
    elif damage=='invented_warmup':ledger['requests'][0]['actual_output_tokens']=2
    elif damage=='invented_eos':ledger['requests'][0]['early_eos']=False
    elif damage=='order':ledger['requests'][0],ledger['requests'][1]=ledger['requests'][1],ledger['requests'][0]
    else:ledger['requests'].pop(0)
    with pytest.raises(ValueError):validate_actual_requests(manifest,ledger)


def test_powershell_delivery_dispatch_is_closed_and_parses_ps51(tmp_path):
    import subprocess
    script=Path(__file__).resolve().parents[1]/'scripts/run_gate11_pilot.ps1'
    # Extract only pure config dispatch. Do not execute launcher/deployment body.
    command=r'''
$ErrorActionPreference='Stop'
$Tokens=$null;$Errors=$null
$Ast=[System.Management.Automation.Language.Parser]::ParseFile($env:G11_SCRIPT,[ref]$Tokens,[ref]$Errors)
if ($Errors.Count) { throw 'parse failure' }
$F=@($Ast.FindAll({param($N) $N -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $N.Name -eq 'DeliveryKind'},$true))
if ($F.Count -ne 1) {throw 'missing dispatch'}
Invoke-Expression $F[0].Extent.Text
$V=[pscustomobject]@{schema_version='gate11-pilot-delivery/0.2';pilot_contract_version='G11-WARMUP3-PAIR/0.1';model_process_budget=30;profile_budget=15;warmup_count=3;additional_budget_authorized=$true}
if ((DeliveryKind $V) -ne 'warmup3_pair') {throw 'wrong path'}
foreach ($Key in @('warmup_count','profile_budget','pilot_contract_version','additional_budget_authorized')) {
  $Bad=$V | ConvertTo-Json | ConvertFrom-Json
  $Bad.$Key=0
  $Rejected=$false
  try {DeliveryKind $Bad | Out-Null} catch {$Rejected=$true}
  if (!$Rejected) {throw 'bad config accepted'}
}
if ((DeliveryKind ([pscustomobject]@{schema_version='gate11-pilot-delivery/0.1'})) -ne 'first') {throw 'legacy broken'}
Write-Output 'DISPATCH_PASS'
'''
    import os
    result=subprocess.run(['powershell.exe','-NoProfile','-Command',command],env=dict(os.environ,G11_SCRIPT=str(script)),capture_output=True,text=True)
    assert result.returncode==0, result.stdout+result.stderr
    assert 'DISPATCH_PASS' in result.stdout


@pytest.mark.parametrize('condition',['G32','N0','Nm','N16'])
def test_actual_new_binding_reaches_profile_argv_only_after_seal(tmp_path,monkeypatch,condition):
    from exposedpath import gate11_pilot as pilot
    from test_gate11_pilot_files import test_actual_pilot_seal_and_target_claim_before_profile_cpu_stop as actual
    rows=api().schedule('seal')
    monkeypatch.setattr(pilot,'schedule',lambda *a:rows)
    actual(tmp_path,monkeypatch,condition)


@pytest.mark.parametrize('wrong_version',[False,True])
def test_cli_config_optin_and_fixed_batch_reach_collect_boundary(tmp_path,monkeypatch,wrong_version):
    import sys
    from scripts import gate11_pilot_batch as batch
    config=tmp_path/'config.json';write_json(config,dict(pilot_contract_version='unrecognized' if wrong_version else api().VERSION))
    out=tmp_path/'batch';calls=[]
    def collect(binding,path,config):
        calls.append(binding);return dict(binding=binding,status='RUN_COMPLETE_PENDING_REVIEW')
    def pair(a,b,path):return dict(pair_id=a['binding']['pair_id'],status='PAIR_COMPLETE_PENDING_REVIEW')
    monkeypatch.setattr(batch,'collect_run',collect);monkeypatch.setattr(batch,'summarize_pair',pair)
    monkeypatch.setattr(sys,'argv',['batch','--config',str(config),'--output',str(out),
        '--batch-id','cli','--execute-reviewed-warmup3-pair'])
    if wrong_version:
        with pytest.raises(ValueError,match='CONFIG_VERSION'):batch.main()
        assert calls==[] and not out.exists()
    else:
        assert batch.main()==0 and len(calls)==30
        assert all(b['warmup_count']==3 for b in calls) and sum(b['pass_id']=='pass1' for b in calls)==15
        result=json.loads((out/'batch_report.json').read_text())
        assert result['status']=='WARMUP3_PAIR_BATCH_COMPLETE_STOP_FOR_REVIEW' and result['gate11_verdict']=='BLOCKED'
