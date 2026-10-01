"""Exactly 30 new Pass0 runs; no profile, continuation or automatic retry."""
import argparse
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from exposedpath.gate11_pilot import require,sha
from exposedpath.gate11_warmup import VERSION,validate_binding
from exposedpath.gate8_isolated_preflight import read,write_new
from scripts.gate11_pilot_batch import run_batch as _run,collect_run,inspect_run,COMMON,GLOBAL_COMMON


def run_batch(output,batch_id,execute,summarize):
    return _run(output,batch_id,execute,summarize,warmup_control=True)


def summarize_pair(first,second,output):
    bindings=[validate_binding(x['binding']) for x in (first,second)]
    require(bindings[0]['pair_id']==bindings[1]['pair_id'] and bindings[0]['run_id']!=bindings[1]['run_id']
        and [b['warmup_count'] for b in bindings]==bindings[0]['warmup_order'],'WARMUP_PAIR_ORDER')
    runs={r['binding']['warmup_count']:inspect_run(r['output'],r['binding']) for r in (first,second)}
    require(set(runs)=={1,3},'WARMUP_PAIR_COUNTS')
    a,b=runs[1],runs[3];ma,mb=a['manifest'],b['manifest']
    require(all(k in ma and k in mb and ma[k]==mb[k] for k in COMMON if k!='warmup_count'),'WARMUP_PAIR_COMMON')
    require(ma.get('n1_model')==mb.get('n1_model'),'WARMUP_PAIR_N1')
    if 'n1_model' in ma:
        require({k:v for k,v in ma['n1_model_execution'].items() if k!='warmup_count'}==
                {k:v for k,v in mb['n1_model_execution'].items() if k!='warmup_count'},'WARMUP_PAIR_STREAM_POLICY')
    require(ma['target_python']['actual']['snapshot']==mb['target_python']['actual']['snapshot']
        and a['loaded_configuration']==b['loaded_configuration'],'WARMUP_PAIR_RUNTIME')
    require(a['token_ids']==b['token_ids'],'WARMUP_PAIR_TOKEN_VALUES')
    require({k:v for k,v in a['cuda_probe'].items() if k!='pid'}==
            {k:v for k,v in b['cuda_probe'].items() if k!='pid'},'WARMUP_PAIR_DEVICE')
    result=dict(version=VERSION,status='PAIR_COMPLETE_PENDING_REVIEW',pair_id=bindings[0]['pair_id'],
        condition=bindings[0]['condition'],block=bindings[0]['block'],order=bindings[0]['warmup_order'],
        environment=dict(manifest={k:ma[k] for k in GLOBAL_COMMON if k!='warmup_count'},
            runtime=ma['target_python']['actual']['snapshot'],loaded_configuration=a['loaded_configuration']),
        run_role='PILOT',data_role='Pilot',gate11_verdict='BLOCKED',formal_eligible=False,
        token_ids=a['token_ids'],output_token_value_parity='EXACT_MATCH',
        measured_difference={k:dict(warmup1_ns=a['timing_ns'][k],warmup3_ns=b['timing_ns'][k],
            delta_ns=b['timing_ns'][k]-a['timing_ns'][k],
            relative_delta=(b['timing_ns'][k]-a['timing_ns'][k])/a['timing_ns'][k] if a['timing_ns'][k]>0 else None)
            for k in a['timing_ns']},warmup1=a,warmup3=b,
        clock='PYTHON_PERF_COUNTER_NS',measurement_validity='NOT_ASSESSED',dropped_records_status='UNKNOWN',
        interpretation='warmup policy plus order/run variation; no profiler overhead estimate',
        statistical_stability='NOT_ASSESSED',remaining_process_budget=0)
    write_new(Path(output)/(bindings[0]['pair_id']+'.json'),result)
    return result


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--batch-id',required=True)
    p.add_argument('--execute-reviewed-warmup-control',required=True,action='store_true')
    a=p.parse_args();config=read(a.config)
    require(config.get('warmup_control_version')==VERSION,'WARMUP_CONFIG_VERSION')
    result=run_batch(a.output,a.batch_id,lambda b,path:collect_run(b,path,config),summarize_pair)
    return 0 if result['status']=='WARMUP_BATCH_COMPLETE_STOP_FOR_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main())
