"""Real producer/SQLite/Canonical/consumer chain, synthetic CPU trace only."""
import json
from pathlib import Path
import pytest
from test_gate8_identity import sha


@pytest.mark.parametrize('damage',[None,'side','count','domain','token','scope','missing'])
def test_real_parameter_file_chain_preserves_rejections(tmp_path,monkeypatch,damage):
    from exposedpath import memset_prefill as c
    from analysis import memset_prefill as consumer
    from test_n1_model_domain import source
    from exposedpath import gate8_isolated_preflight as isolated
    real_read=isolated.read
    assert hasattr(consumer,'process'),'missing actual Canonical consumption entry'
    rt=tmp_path/'rt.dll';rt.write_bytes(b'CPU runtime');rec=tmp_path/'rec.dll';rec.write_bytes(b'CPU recorder')
    b=c.binding('a'*32,'d'*40,dict(path=str(rec),sha256=sha(rec)),dict(path=str(rt),sha256=sha(rt)))
    receipt,execution,_=source(tmp_path,monkeypatch,batch_binding=b)
    monkeypatch.setattr(isolated,'read',real_read) # Keep real artifact reads, only OS boundary was doubled.
    side=execution.parent/'memset_parameters.json'
    if damage in ('side','count','domain'):
        v=json.loads(side.read_text())
        if damage=='side':v['run_id']='b'*32
        if damage=='count':v['calls'][0]['count']=64
        if damage=='domain':v['calls'][0]['tid']+=1
        side.write_text(json.dumps(v))
        # Rebind deliberate semantic conflicts to exercise the semantic gate,
        # not merely the already tested byte-seal gate.
        e=json.loads(execution.read_text());e['memset_parameters_sha256']=sha(side);execution.write_text(json.dumps(e))
    if damage=='missing':side.unlink()
    if damage=='token':
        p=execution.parent/'batch_tokens.json';v=json.loads(p.read_text());v['requests'][0]['token_ids'][0][0]=None;p.write_text(json.dumps(v))
    if damage=='scope':
        p=execution.parent/'manifest.json';v=json.loads(p.read_text());v['batch_size']=4;p.write_text(json.dumps(v))
    if damage:
        with pytest.raises((ValueError,FileNotFoundError)):consumer.process(receipt,execution,tmp_path/'derived')
        assert not (tmp_path/'derived/parameters.json').exists()
    else:
        from scripts.gate8_diagnostic_collect import analyze_receipt
        p,v=analyze_receipt(json.loads((execution.parent/'manifest.json').read_text()),receipt,execution,tmp_path/'derived')
        assert v['status']=='MEMSET_PREFILL_EVIDENCE_COMPLETE_PENDING_REVIEW'
        assert v['coverage']['calls'][0]['count']==0 and len(v['scope_proof']['real_members'])==3
        assert v['scope_proof']['synthetic_activities']==[]
        assert v['a_admission']==v['coe_admission']=='NOT_ASSESSED'
        assert not list(tmp_path.rglob('domain.json'))
