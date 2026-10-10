"""Independent integer pairs. Blocks, not kernels/tokens, are repeats."""
from copy import deepcopy
import json
import pytest


def rows():
    values=[]
    for b in range(1,7):
        for j,c in enumerate(('G32','G512','N0','Nm','N16')):
            for pid in ('pass0','pass1'):
                # P1-P0=-2; Nmarker delta=10, sync delta=10; Gdelta=10.
                t=100+b+10*j-(2 if pid=='pass1' else 0)
                values.append(dict(block=b,condition=c,pass_id=pid,pair_id=f'b{b}-{c}',
                    run_id=f'b{b}-{c}-{pid}',order=len(values)+1,
                    host_ns={'full_request':t,'prefill':t-20,'decode':20},
                    p1_a=None if pid=='pass0' else {'full_request':{'A_host_path_ns':t}},
                    source_sha256='a'*64))
    return values


def test_signed_fixed_contrasts_and_joint_resampling():
    from exposedpath_v141.paired_statistics import summarize,resample_blocks
    r=summarize(rows(),bootstrap_count=100)
    assert r['contrasts']['profile:G32:full_request']['values_ns']==[-2]*6
    assert r['contrasts']['G1:pass0:full_request']['values_ns']==[10]*6
    assert r['contrasts']['N1_sync:pass1:full_request']['values_ns']==[10]*6
    assert r['contrasts']['interaction_sync:full_request']['values_ns']==[0]*6
    assert r['contrasts']['profile:G32:full_request']['bootstrap_95_ns']==[-2,-2]
    sample=resample_blocks(rows(),[6,1,6,2,3,4])
    assert [r['block'] for r in sample[::10]]==[6,1,6,2,3,4]
    assert len(sample)==60 and len({x['condition'] for x in sample[:10]})==5


@pytest.mark.parametrize('damage',['partial','duplicate','pair','pass','conservation','noninteger'])
def test_incomplete_or_misaligned_blocks_cannot_be_repaired(damage):
    from exposedpath_v141.paired_statistics import summarize
    r=rows()
    if damage=='partial':r.pop()
    if damage=='duplicate':r[-1]=deepcopy(r[0])
    if damage=='pair':r[1]['pair_id']='wrong'
    if damage=='pass':r[0]['pass_id']='future'
    if damage=='conservation':r[0]['host_ns']['prefill']+=1
    if damage=='noninteger':r[0]['host_ns']['decode']=False
    with pytest.raises(ValueError): summarize(r,bootstrap_count=10)


def test_file_report_keeps_raw_values_and_plot_scope(tmp_path):
    from exposedpath_v141.paired_statistics import write_report
    path=tmp_path/'input.json';path.write_text(json.dumps(rows()),encoding='utf-8')
    out=write_report(path,tmp_path/'out',bootstrap_count=100)
    r=json.loads(out.read_text())
    assert r['raw_rows']==rows() and r['p0_composition_transfer'] is False
    assert (out.parent/'paired.svg').is_file() and (out.parent/'originals.csv').is_file()
    with pytest.raises(FileExistsError):write_report(path,out.parent)


@pytest.mark.parametrize('damage',['empty','escape','missing'])
def test_formal_file_index_cannot_fill_missing_blocks(tmp_path,damage):
    from exposedpath_v141.paired_statistics import read_formal_batch
    path=tmp_path/'index.json'
    item=dict(output_dir='../outside' if damage=='escape' else 'missing',
        manifest_sha256='a'*64,execution_sha256='b'*64,domain_sha256=None,baseline_sha256=None)
    path.write_text(json.dumps(dict(schema_version='exposedpath-formal-batch-index/0.1.0',
        runs=[] if damage=='empty' else [item]*60)))
    with pytest.raises((ValueError,FileNotFoundError)):read_formal_batch(path)


def test_complete_signed_cpu_file_batch_to_block_report(tmp_path,monkeypatch):
    """Real files/producer/consumers; fake model, device, collector and signature.

    Sixty CPU doubles are not sixty model experiments or new qualification.
    """
    from pathlib import Path
    from test_gate12_formal import release
    from test_gate11_pilot_files import pair_files
    from test_gate8_diagnostic_entry import case
    from test_gate8_identity import sha
    from exposedpath import formal_protocol as f,platform_adapter
    from exposedpath_v141.activity_baseline import write_baseline
    from exposedpath_v141.paired_statistics import read_formal_batch,write_formal_report
    import test_n1_model_calls as model_fixture
    from test_runner_token_ready import _FakeToken
    monkeypatch.setattr(model_fixture,'_FakeToken',lambda values,events:_FakeToken([13 if values[0]%2 else 14],events))
    seed=tmp_path/'seed';seed.mkdir();args,_=case(monkeypatch,seed)
    prompt=json.loads(args['prompt_path'].read_text());long=deepcopy(prompt);long['fixed_input_tokens']=512
    long['samples']=[dict(input_ids=[1]*512,attention_mask=[1]*512)]
    import hashlib
    p,a=release();p['input_hashes']={'G32':sha(args['prompt_path']),'G512':hashlib.sha256(json.dumps(long).encode()).hexdigest()}
    commit=json.loads(args['manifest_path'].read_text())['runner_git_commit']
    p['execution_commit']=p['analysis_commit']=commit;a['protocol_sha256']=f.content_hash(p)
    monkeypatch.setattr(platform_adapter,'git',lambda argv:commit if 'rev-parse' in argv else '')
    shared_model=tmp_path/'shared_cpu_model';shared_model.mkdir()
    runs=[]
    for block,conditions in enumerate(f.ORDERS,1):
        for condition in conditions:
            first=f.make_binding(p,a,batch_id='cpu-full',block=block,condition=condition,
                pass_id='pass0',declared_at='2026-10-03T00:00:00Z')
            bindings=[f.make_binding(p,a,batch_id='cpu-full',block=block,condition=condition,
                pass_id=pid,declared_at='2026-10-03T00:00:00Z') for pid in first['pass_order']]
            pairroot=tmp_path/f'b{block}-{condition}';pairroot.mkdir()
            outputs=pair_files(pairroot,monkeypatch,condition,bindings,shared_model=shared_model)
            for item in outputs:
                out=Path(item['output']);root=out/'diagnostic';pid=item['binding']['pass_id']
                if pid=='pass1':
                    write_baseline(out/'analyzed/domain.json',out/'input_receipt.json',root/'engineering_execution.json',
                        out/'baseline',**({'bridge_path':root/'n1_model_calls.json'} if first['variant'] else {}))
                runs.append(dict(output_dir=out.relative_to(tmp_path).as_posix(),manifest_sha256=sha(root/'manifest.json'),
                    execution_sha256=sha(root/'engineering_execution.json'),
                    domain_sha256=sha(out/'analyzed/domain.json') if pid=='pass1' else None,
                    baseline_sha256=sha(out/'baseline/baseline.json') if pid=='pass1' else None))
    index=tmp_path/'index.json';index.write_text(json.dumps(dict(schema_version='exposedpath-formal-batch-index/0.1.0',runs=runs)))
    from exposedpath_v141 import gate9_domain as domain_module
    original_load=domain_module.load_domain
    verifications=[]
    def counted_load(path,*args,**kwargs):
        verifications.append(str(path))
        return original_load(path,*args,**kwargs)
    monkeypatch.setattr(domain_module,'load_domain',counted_load)
    rows,sources=read_formal_batch(index)
    assert len(verifications)==len(set(verifications))==30  # Exactly one full check per P1 run.
    monkeypatch.setattr(domain_module,'load_domain',original_load)
    assert len(rows)==60 and len({r['pair_id'] for r in rows})==30
    assert rows[0]['condition']=='G32' and rows[-1]['condition']=='G32'
    output=write_formal_report(index,tmp_path/'report')
    report=json.loads(output.read_text())
    assert report['formal_sources']['protocol']==p
    assert not report['a_overhead_subtracted'] and not report['bootstrap']['coverage_guaranteed']
    # Tamper actual content: the signed role cannot make mismatched bytes valid.
    path=tmp_path/runs[0]['output_dir']/'diagnostic/formal_tokens.json'
    value=json.loads(path.read_text());value['requests'][0]['token_ids'][0]=[999];path.write_text(json.dumps(value))
    with pytest.raises(ValueError):read_formal_batch(index)
