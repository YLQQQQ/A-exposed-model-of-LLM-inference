"""Finite, predeclared Engineering input axis; no model/CUDA calls."""
from copy import deepcopy
from pathlib import Path

from .gate8_isolated_preflight import sha, write_new
from .workload import load_prompt_tokens

VERSION='G10-WORKLOAD-FEASIBILITY/0.1'
LENGTHS=(128,512)


def require(ok,reason):
    if not ok: raise ValueError('GATE10_'+reason)


def declaration(length):
    require(type(length) is int and length in LENGTHS,'CANDIDATE')
    return dict(version=VERSION,input_tokens=length,output_tokens=2,batch_size=1,
        construction='CYCLE_SEALED_SAMPLE0_32',role='Engineering',warmup=1,repeat=1)


def input_length(manifest):
    if 'pilot' in manifest:
        from .gate11_pilot import validate
        validate(manifest)
        return manifest['fixed_input_tokens']
    if 'gate10_workload' not in manifest: return 32
    d=manifest['gate10_workload']
    require(isinstance(d,dict) and d==declaration(d.get('input_tokens')),'DECLARATION')
    from exposedpath_v141.gate9_domain import G1,declaration as domain
    require(manifest.get('domain_qualification')==domain(G1)
        and manifest.get('fixed_input_tokens')==d['input_tokens'],'DOMAIN_OR_LENGTH')
    return d['input_tokens']


def validate_input(prompt,config,length):
    require(type(length) is int and length in LENGTHS and prompt.get('fixed_input_tokens')==length,'LENGTH')
    require(config.get('model_type')=='qwen2' and type(config.get('vocab_size')) is int
        and type(config.get('max_position_embeddings')) is int
        and length+2<=config['max_position_embeddings'],'MODEL_CONFIG')
    samples=prompt.get('samples')
    require(isinstance(samples,list) and len(samples)==1,'SAMPLE_COUNT')
    ids=samples[0].get('input_ids'); mask=samples[0].get('attention_mask')
    require(isinstance(ids,list) and len(ids)==length and all(type(i) is int and 0<=i<config['vocab_size'] for i in ids),'TOKEN_RANGE')
    require(isinstance(mask,list) and len(mask)==length and all(type(i) is int and i==1 for i in mask),'MASK')
    special=set()
    for source in (prompt.get('special_tokens',{}),config):
        for k in ('bos_token_id','eos_token_id','pad_token_id'):
            v=source.get(k)
            if isinstance(v,list): special.update(v)
            elif v is not None: special.add(v)
    require(not special.intersection(ids),'SPECIAL_TOKEN')
    require(ids==ids[:32]*(length//32),'CONSTRUCTION')


def make_inputs(seed_path,expected_sha,output):
    require(sha(seed_path)==expected_sha.lower(),'SEED_HASH')
    seed=load_prompt_tokens(Path(seed_path))
    require(seed['fixed_input_tokens']==32,'SEED_LENGTH')
    output=Path(output); output.mkdir(parents=True,exist_ok=False)
    paths=[]
    for n in LENGTHS:
        value=deepcopy(seed); value['fixed_input_tokens']=n
        value['samples']=[dict(sample_index=0,input_ids=seed['samples'][0]['input_ids']*(n//32),attention_mask=[1]*n)]
        value['construction']=dict(rule='CYCLE_SEALED_SAMPLE0_32',source_sha256=expected_sha.lower())
        path=output/f'input_{n}.json'; write_new(path,value); paths.append(path)
    return paths
