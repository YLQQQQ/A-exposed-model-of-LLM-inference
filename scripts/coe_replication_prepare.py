"""CPU-only statement -> existing finite plan -> whole-block summary.

No execution/deployment entry, vendor loading, new role, or S/COE calculation.
Source reports still require the existing upstream identity/quality validator.
"""
from copy import deepcopy
from fractions import Fraction
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import statistics

ROOT=Path(__file__).resolve().parents[1]
VERSION='COE-ENDPOINT-REPLICATION-PREPARATION/0.1.0'
COMPONENTS=('scripts/cupti_input_contract.py','scripts/cupti_input_pilot.py',
    'scripts/cupti_timeline_model.py','exposedpath/gate11_pilot.py')


def require(ok,reason):
    if not ok:raise ValueError('COE_REPLICATION_'+reason)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def load(name):
    spec=importlib.util.spec_from_file_location('_replication_'+name,ROOT/'scripts'/(name+'.py'))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


def contract():return load('cupti_input_contract')
def pilot():return load('cupti_input_pilot')


def validate(statement):
    require(statement.get('schema_version')==VERSION and statement.get('gpu_authorized') is False and
        statement.get('formal_eligible') is False and statement.get('execution_commit') is None,'STATEMENT_VERSION_OR_AUTHORITY')
    p=statement['execution_plan'];require(p.get('role')=='Pilot','PLAN_ROLE')
    h=contract();h.role_policy().validate_cupti_plan(p)
    require(p['input_lengths']==[512,2048] and p['blocks']==4 and p['comparisons']==[
        dict(low=512,high=2048,role='PRIMARY',token_indices=[0]),
        dict(low=512,high=2048,role='SECONDARY',token_indices=[1])],'PRIMARY_PLAN')
    require(p['orders']==[[512,2048],[2048,512],[2048,512],[512,2048]],'BALANCE')
    a=statement['analysis']
    expected=dict(unit='COMPLETE_NEW_BLOCK_NOT_TOKEN_KERNEL_OR_SYNC',primary_token=0,
        primary_statistic='EQUAL_BLOCK_MEAN_R_NS',R='COE2048-COE512*(G2048/G512)',
        G='OBSERVED_PID_DEVICE_CONTEXT_SAME_PHASE_GPU_UNION_NOT_CUMULATIVE_W',
        invalid_denominator='NULL_UNDEFINED_NO_EPSILON_NO_IMPUTATION',bootstrap=None,p_value=None,
        precision_guarantee=False,numeric_quality_threshold=None,old_samples_pooled=False)
    require(all(type(a.get(k)) is type(v) and a[k]==v for k,v in expected.items()),'ANALYSIS_POLICY')
    require(statement['fixed_execution']==dict(batch_size=1,output_tokens=2,warmup_count=3,repeat_count=1,
        dtype='fp16',execution_mode='eager',attention_backend='sdpa',completion_policy='HOST_READABLE_P',
        **{'pass':'pass1'},fresh_process_per_slot=True),'EXECUTION_POLICY')
    require(statement['components']==dict(native_commit=h.NATIVE,
        client_sha256='5e0ffa4b332652c6107cb278ed300ddc9b1bc0e201a370dbe1040cb463d2247a',
        activity_policy='cupti-api22-activity-policy/0.2.0',consumer=h.POLICIES['consumer_version'],
        timing_policy=h.POLICIES['timing_policy'],driver_queries=h.POLICIES['driver_query_policy'],
        runtime_queries=h.POLICIES['runtime_query_policy']),'COMPONENT_VERSION')
    b=statement['budget'];budget=pilot().fixed_budget(p)
    require(b['model_processes']==b['cupti_sessions']==8 and b['nsight_profiles']==0 and
        b['model_seconds_per_run']==budget['per_model_seconds'] and
        b['analysis_seconds_per_run']==budget['per_analysis_seconds'] and
        b['temporary_reserve_bytes']==budget['temporary_required_bytes'] and
        b['subprocess_limit_sum_seconds']==8*(300+180),'BUDGET')
    require(statement['quality_and_stop']==dict(policy='UNCHANGED_BOTH_TOKEN_IDENTITY_INPUT_TOKEN_DRAIN_EFFECT_DEPENDENCY_TERMINAL_SCOPE_LOSS_CAPACITY',
        hard_failure_stop=True,fixed_slots_stop=8,retry=False,replacement=False,automatic_more_budget=False,
        splice_incomplete_blocks=False,exclude_by_direction=False),'STOP_POLICY')
    return p


def prepare(statement_path,input_root,batch_id,proposed_commit,output):
    statement_path=Path(statement_path);s=json.loads(statement_path.read_text(encoding='utf8'));p=validate(s)
    h=contract();inputs=deepcopy(s['input_reference']['inputs']);base=Path(input_root).resolve()
    require(set(inputs)=={'512','2048'},'INPUT_COVERAGE')
    for key,r in inputs.items():
        require(r['path']==f'input_{key}.json','INPUT_PATH')
        source=base/r['path'];require(source.is_file() and source.stat().st_size==r['bytes'] and sha(source)==r['sha256'],'INPUT_HASH')
        require(h.input_identity(json.loads(source.read_text(encoding='utf8')),int(key))==r['identity'],'INPUT_IDENTITY')
        h.validate_output_policy(r['output_validation'],'Pilot')
    slots=h.schedule(batch_id,proposed_commit,plan=p)
    out=Path(output);require(not out.exists(),'NEW_OUTPUT');out.mkdir(parents=True)
    value=dict(schema_version=VERSION,status='CPU_PREPARATION_NOT_EXECUTION_AUTHORIZATION',gpu_authorized=False,
        statement_sha256=sha(statement_path),execution_plan=deepcopy(p),execution_plan_digest=digest(p),
        proposed_controller_commit=proposed_commit,slots=slots,inputs=inputs,budget=pilot().fixed_budget(p),
        source_sha256={n:sha(ROOT/n) for n in COMPONENTS},formal_eligible=False)
    for name,v in [('execution_plan.json',p),('preparation.json',value)]:
        with (out/name).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
    return value


def summarize(statement_path,prepared,rows):
    require(sha(statement_path)==prepared['statement_sha256'],'STATEMENT_CHANGED')
    s=json.loads(Path(statement_path).read_text(encoding='utf8'));p=validate(s);h=contract()
    require(prepared['source_sha256']=={n:sha(ROOT/n) for n in COMPONENTS},'SOURCE_COMPONENT_CHANGED')
    require(prepared['execution_plan']==p and prepared['execution_plan_digest']==digest(p) and
        prepared['gpu_authorized'] is False,'PLAN_BINDING')
    require(prepared['slots'] and prepared['slots']==h.schedule(prepared['slots'][0]['batch_id'],
        prepared['proposed_controller_commit'],plan=p),'PREPARED_SLOT_BINDING')
    require(all(isinstance(r.get(k),str) and re.fullmatch('[0-9a-f]{64}',r[k]) for r in rows
        for k in ('report_sha256','capture_sha256')),'SOURCE_HASH')
    result=h.summarize(prepared['slots'],rows,plan=p) # existing exact signed R, no new arithmetic model
    descriptions=[]
    for token in (0,1):
        comparisons=[v for v in result['comparisons'] if v['token_index']==token]
        values=[Fraction(v['R_exact']['numerator'],v['R_exact']['denominator']) if v['R_exact'] else None for v in comparisons]
        mean=lambda vs:float(sum(vs)/len(vs)) if vs and all(v is not None for v in vs) else None
        by_order={}
        for order in ((512,2048),(2048,512)):
            subset=[v for v,c in zip(values,comparisons) if p['orders'][c['block']-1]==list(order)]
            by_order['_'.join(map(str,order))]=mean(subset)
        complete=all(v is not None for v in values)
        descriptions.append(dict(token_index=token,R_mean_ns=mean(values),
            R_median_ns=float(statistics.median(values)) if complete else None,
            R_range_ns=[float(min(values)),float(max(values))] if complete else None,
            R_undefined_blocks=[c['block'] for v,c in zip(values,comparisons) if v is None],
            by_order_R_mean_ns=by_order,first_two_R_mean_ns=mean(values[:2]),last_two_R_mean_ns=mean(values[2:]),
            leave_one_out_R_mean_ns=[dict(omitted_block=c['block'],R_mean_ns=mean(values[:i]+values[i+1:]))
                for i,c in enumerate(comparisons)]))
    result.update(statement_sha256=prepared['statement_sha256'],descriptive=descriptions,
        scientific_verdict='REVIEW_REQUIRED_NOT_DATA_QUALITY_PASS',paper_increment='NOT_GRANTED',
        source_quality_verdict='REQUIRES_UPSTREAM_AUTHENTICATED_REPORTS_NOT_PROVED_BY_THIS_SUMMARY',
        status='DESCRIPTIVE_COMPLETE_STOP_FOR_REVIEW',bootstrap=None,p_value=None)
    return result
