"""Fixed Route-A paired descriptions. No collector, significance or optional stop."""
import csv
from copy import deepcopy
import html
import json
from pathlib import Path
import random
import statistics

VERSION='exposedpath-block-statistics/0.1.0'
CONDITIONS=('G32','G512','N0','Nm','N16')
PHASES=('full_request','prefill','decode')


def require(ok,reason):
    if not ok:raise ValueError('STATISTICS_'+reason)


def validate_rows(rows):
    require(isinstance(rows,list) and len(rows)==60,'INCOMPLETE_BATCH')
    by={}
    for r in rows:
        require(type(r['block']) is int and 1<=r['block']<=6 and r['condition'] in CONDITIONS
            and r['pass_id'] in ('pass0','pass1'),'SLOT')
        key=(r['block'],r['condition'],r['pass_id'])
        require(key not in by,'DUPLICATE_SLOT')
        require(isinstance(r['pair_id'],str) and r['pair_id'] and isinstance(r['run_id'],str)
            and r['run_id'] and type(r['order']) is int and 1<=r['order']<=60,'IDENTITY')
        t=r['host_ns'];require(set(t)==set(PHASES) and all(type(v) is int and 0<=v<2**63 for v in t.values()),'TIME_RANGE')
        require(t['full_request']==t['prefill']+t['decode'],'PHASE_ADDITIVITY')
        require((r['p1_a'] is None)==(r['pass_id']=='pass0'),'PASS_A')
        if r['pass_id']=='pass1':
            require(isinstance(r['p1_a'],dict),'A_STRUCTURE')
        by[key]=r
    require(len({r['run_id'] for r in rows})==60 and len({r['order'] for r in rows})==60,'DUPLICATE_RUN_OR_ORDER')
    for b in range(1,7):
        for c in CONDITIONS:
            p0,p1=by[b,c,'pass0'],by[b,c,'pass1']
            require(p0['pair_id']==p1['pair_id'] and abs(p0['order']-p1['order'])==1,'PAIR_MISALIGNMENT')
    require(len({r['pair_id'] for r in rows})==30,'DUPLICATE_PAIR')
    return by


def read_formal_batch(index_path):
    """Read complete *actual* files, not a table whose role can be relabelled.

    The index only locates immutable inputs; it cannot supply measured values.
    CPU fixtures exercise these interfaces with explicit synthetic approvals.
    """
    from exposedpath.formal_protocol import validate,ORDERS,reference
    from .gate8_adapter import digest
    from .gate9_domain import DomainReview,FORMAL_VERSION,analysis_stage
    from scripts.gate8_pair import inspect_execution
    from scripts.gate11_pilot_batch import COMMON,GLOBAL_COMMON
    index_path=Path(index_path).resolve();root=index_path.parent
    value=json.loads(index_path.read_text(encoding='utf-8'))
    require(set(value)=={'schema_version','runs'} and value['schema_version']=='exposedpath-formal-batch-index/0.1.0','INDEX_VERSION')
    require(isinstance(value['runs'],list) and len(value['runs'])==60,'INCOMPLETE_BATCH')
    rows=[];observed=[];protocol=None;approval=None;batch=None;source_refs=[]
    for order,item in enumerate(value['runs'],1):
        require(set(item)=={'output_dir','manifest_sha256','execution_sha256','domain_sha256','baseline_sha256'},'INDEX_ENTRY')
        relative=Path(item['output_dir']);out=(root/relative).resolve()
        require(not relative.is_absolute() and '..' not in relative.parts and out.is_relative_to(root),'INDEX_PATH')
        mpath=out/'diagnostic/manifest.json';epath=out/'diagnostic/engineering_execution.json'
        require(digest(mpath)==item['manifest_sha256'] and digest(epath)==item['execution_sha256'],'INDEX_HASH')
        m=json.loads(mpath.read_text(encoding='utf-8'));b=validate(m)
        if protocol is None:protocol,approval,batch=b['protocol'],b['approval'],b['batch_id']
        require(b['protocol']==protocol and b['approval']==approval and b['batch_id']==batch,'MIXED_RELEASE')
        block=(order-1)//10+1;position=((order-1)%10)//2
        condition=ORDERS[block-1][position]
        require(b['block']==block and b['condition']==condition and b['pass_id']==b['pass_order'][(order-1)%2],'PLAN_ORDER')
        facts=inspect_execution(out,b['pass_id']);require(facts['formal']==b,'RUN_BINDING')
        if b['pass_id']=='pass0':
            require(item['domain_sha256'] is None and item['baseline_sha256'] is None,'P0_ANALYSIS')
            report=json.loads((out/'baseline_report.json').read_text(encoding='utf-8'))
            require(report.get('formal')==b and report.get('role')=='UNPROFILED_LIMITED_FORMAL'
                and report['status']=='BASELINE_COMPLETE_NOT_ACCEPTANCE','P0_REPORT')
            a=None;physical_b=[];baseline=None
        else:
            dpath=out/'analyzed/domain.json';base=out/'baseline/baseline.json'
            require(digest(dpath)==item['domain_sha256'] and digest(base)==item['baseline_sha256'],'DERIVED_HASH')
            report=json.loads((out/'collection_report.json').read_text(encoding='utf-8'))
            require(report.get('formal')==b and report.get('status')=='FORMAL_RUN_COMPLETE_PENDING_REVIEW'
                and report.get('error') is None and report['collection']['status']=='COMPLETE'
                and report['export_status']=='PASS' and report['result_sha256']==digest(dpath),'P1_REPORT')
            bridge={'bridge_path':out/'diagnostic/n1_model_calls.json'} if b['variant'] else {}
            # One verified object for this run only; no batch-sized cache.
            print(f'[review] order={order}/60 block={block} condition={condition} pass=pass1',flush=True)
            with DomainReview() as review:
                with analysis_stage('formal_domain_review'):
                    domain=review.load(dpath,out/'input_receipt.json',epath,**bridge)
                require(domain['schema_version']==FORMAL_VERSION and domain.get('formal')==b
                    and domain['formal_admission']['status']=='ADMITTED_LIMITED_PROTOCOL','DOMAIN_ADMISSION')
                from .activity_baseline import load_baseline
                with analysis_stage('formal_baseline_review'):
                    baseline=load_baseline(base,dpath,out/'input_receipt.json',epath,
                        domain_review=review,**bridge)
            arecords=[a for r in domain['requests'] for a in r['a_records']]
            require(len(arecords)==3 and {a['phase'] for a in arecords}==set(PHASES),'A_WINDOWS')
            a={r['phase']:r for r in arecords}
            physical_b=domain.get('b_records',[]) if b['variant'] else []
            del domain  # Release large physical S/W records before the next run.
        observed.append(facts)
        rows.append(dict(block=block,condition=condition,pass_id=b['pass_id'],pair_id=b['pair_id'],
            run_id=b['run_id'],order=order,host_ns=facts['timing_ns'],p1_a=a,
            b_records=physical_b,baseline=baseline,source_sha256=digest(epath),formal_reference=reference(b)))
        source_refs.append(dict(item,run_id=b['run_id']))
    by=validate_rows(rows)
    for j in range(0,60,2):
        a,z=observed[j:j+2];ma,mz=a['manifest'],z['manifest']
        require(all(ma.get(k)==mz.get(k) and k in ma and k in mz for k in COMMON)
            and ma.get('n1_model')==mz.get('n1_model') and ma.get('n1_model_execution')==mz.get('n1_model_execution'),'PAIR_CONFIGURATION')
        require(a['loaded_configuration']==z['loaded_configuration'] and a['token_ids']==z['token_ids']
            and ma['target_python']['actual']['snapshot']==mz['target_python']['actual']['snapshot'],'PAIR_ACTUAL')
    first=observed[0]
    for x in observed:
        require(all(first['manifest'][k]==x['manifest'][k] for k in GLOBAL_COMMON)
            and first['loaded_configuration']==x['loaded_configuration']
            and first['manifest']['target_python']['actual']['snapshot']==x['manifest']['target_python']['actual']['snapshot'],'BATCH_CONFIGURATION')
        token_reference=next(v for v in observed if v['manifest']['fixed_input_tokens']==x['manifest']['fixed_input_tokens'])
        require(x['token_ids']==token_reference['token_ids'],'CROSS_CONDITION_TOKENS')
    return rows,dict(index_sha256=digest(index_path),protocol=protocol,approval=approval,inputs=source_refs)


def resample_blocks(rows,indices):
    validate_rows(rows)
    require(len(indices)==6 and all(type(b) is int and 1<=b<=6 for b in indices),'RESAMPLE_UNIT')
    return [deepcopy(r) for b in indices for r in sorted(rows,key=lambda r:r['order']) if r['block']==b]


def quantile(values,p):
    ordered=sorted(values);i=p*(len(values)-1);low=int(i);fraction=i-low
    return ordered[low]*(1-fraction)+ordered[min(low+1,len(values)-1)]*fraction


def summarize(rows,*,bootstrap_count=10000):
    by=validate_rows(rows)
    require(type(bootstrap_count) is int and bootstrap_count>0,'BOOTSTRAP_COUNT')
    contrasts={}
    def add(name,values):contrasts[name]=values
    for phase in PHASES:
        for c in CONDITIONS:
            add(f'profile:{c}:{phase}',[by[b,c,'pass1']['host_ns'][phase]-by[b,c,'pass0']['host_ns'][phase] for b in range(1,7)])
        for name,hi,lo in (('G1','G512','G32'),('N1_marker','Nm','N0'),('N1_sync','N16','Nm')):
            for pid in ('pass0','pass1'):
                add(f'{name}:{pid}:{phase}',[by[b,hi,pid]['host_ns'][phase]-by[b,lo,pid]['host_ns'][phase] for b in range(1,7)])
            if name!='G1':
                add(f'interaction_{"marker" if name=="N1_marker" else "sync"}:{phase}',[
                    contrasts[f'{name}:pass1:{phase}'][j]-contrasts[f'{name}:pass0:{phase}'][j] for j in range(6)])
            # Preselected A components. Missing is unknown, never zero.
            for field in ('A_host_path_ns','A_cuda_api_ns','A_cuda_api_submit_ns','A_cuda_api_non_submit_ns',
                          'A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns'):
                values=[]
                for b in range(1,7):
                    a=by[b,hi,'pass1']['p1_a'].get(phase,{}).get(field)
                    z=by[b,lo,'pass1']['p1_a'].get(phase,{}).get(field)
                    values.append(a-z if type(a) is int and type(z) is int else None)
                add(f'{name}:P1_A:{phase}:{field}',values)
    rng=random.Random(20261001)
    # Same draws for every quantity: the complete joint block is the unit.
    draws=[[rng.randrange(6) for _ in range(6)] for _ in range(bootstrap_count)]
    described={}
    for name,values in contrasts.items():
        if any(v is None for v in values):
            described[name]=dict(values_ns=values,status='MISSING_COMPONENT',mean_ns=None,bootstrap_95_ns=None)
            continue
        means=[statistics.mean([values[j] for j in ids]) for ids in draws]
        leave=[statistics.mean(values[:j]+values[j+1:]) for j in range(6)]
        described[name]=dict(values_ns=values,status='DESCRIPTIVE_ONLY',mean_ns=statistics.mean(values),
            median_ns=statistics.median(values),min_ns=min(values),max_ns=max(values),sample_sd_ns=statistics.stdev(values),
            bootstrap_95_ns=[quantile(means,.025),quantile(means,.975)],leave_one_block_mean_ns=leave,
            first_three_ns=values[:3],last_three_ns=values[3:],
            observed_direction='POSITIVE' if all(x>0 for x in values+leave) else 'NEGATIVE' if all(x<0 for x in values+leave) else 'MIXED_OR_ZERO')
    return dict(schema_version=VERSION,status='DESCRIPTIVE_NOT_QUALIFICATION',raw_rows=rows,contrasts=described,
        relative_profile=[dict(block=b,condition=c,phase=p,
            ratio=(by[b,c,'pass1']['host_ns'][p]-by[b,c,'pass0']['host_ns'][p])/by[b,c,'pass0']['host_ns'][p]
            if by[b,c,'pass0']['host_ns'][p] else None) for b in range(1,7) for c in CONDITIONS for p in PHASES],
        bootstrap=dict(unit='WHOLE_COMPLETE_BLOCK',seed=20261001,count=bootstrap_count,coverage_guaranteed=False),
        p0_composition_transfer=False,a_overhead_subtracted=False,b_cross_sync_aggregation=False,
        precision_candidates_ms={'request_prefill':10,'decode':5,'guaranteed':False},
        measurement_validity='NOT_ASSESSED',statistical_stability='NOT_ESTABLISHED')


def _plot(rows):
    """Raw P0/P1 panels per condition and phase, not corrected A or fitted trends."""
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="1080">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<text x="20" y="22">Host paired durations (ms): blue P0 / red P1; no overhead correction</text>']
    for panel,(c,p) in enumerate((c,p) for c in CONDITIONS for p in PHASES):
        x=20+(panel%3)*325;y=50+(panel//3)*200
        values=[r['host_ns'][p]/1e6 for r in rows if r['condition']==c];peak=max(values) or 1
        svg.append(f'<text x="{x}" y="{y}">{html.escape(c+" / "+p)} [0,{peak:.3f}] ms</text>')
        for b in range(1,7):
            pair=[next(r for r in rows if r['condition']==c and r['block']==b and r['pass_id']==pid) for pid in ('pass0','pass1')]
            coords=[(x+20+40*(b-1)+off,y+150-130*r['host_ns'][p]/1e6/peak) for r,off in zip(pair,(0,12))]
            svg.append(f'<line x1="{coords[0][0]}" y1="{coords[0][1]}" x2="{coords[1][0]}" y2="{coords[1][1]}" stroke="gray"/>')
            for xy,color in zip(coords,('blue','red')):svg.append(f'<circle cx="{xy[0]}" cy="{xy[1]}" r="3" fill="{color}"/>')
            svg.append(f'<text x="{x+20+40*(b-1)}" y="{y+175}">b{b}</text>')
    return '\n'.join(svg+['</svg>'])


def write_report(input_path,output_dir,*,bootstrap_count=10000):
    from .gate8_files import _write
    from .gate8_adapter import digest
    input_path,output_dir=Path(input_path),Path(output_dir)
    if output_dir.exists():raise FileExistsError(output_dir)
    rows=json.loads(input_path.read_text(encoding='utf-8'))
    return _write_report(rows,output_dir,bootstrap_count=bootstrap_count,sources=dict(input_sha256=digest(input_path)))


def write_formal_report(index_path,output_dir):
    """No execution option. Only a complete signed, qualified batch is read."""
    rows,sources=read_formal_batch(index_path)
    return _write_report(rows,Path(output_dir),bootstrap_count=10000,sources=dict(formal_sources=sources))


def _a_plot(rows):
    fields=('A_host_path_ns','A_cuda_api_ns','A_device_wait_ns','A_sync_residual_ns','A_unattributed_ns')
    colors=('#268a46','#426ab3','#dd8033','#888888','#b63259')
    svg=['<svg xmlns="http://www.w3.org/2000/svg" width="1150" height="680">',
         '<rect width="100%" height="100%" fill="white"/>',
         '<text x="20" y="20">P1 A only (ms), no P0 composition transfer / overhead subtraction</text>',
         '<text x="20" y="42">Host green; CUDA API blue (opaque included); device wait orange; residual gray; unknown pink</text>']
    for k,phase in enumerate(PHASES):
        selected=[r for r in sorted(rows,key=lambda x:x['order']) if r['pass_id']=='pass1']
        complete=all(all(type(r['p1_a'].get(phase,{}).get(f)) is int for f in fields) for r in selected)
        y=90+k*185
        svg.append(f'<text x="20" y="{y}">{phase}</text>')
        if not complete:
            svg.append(f'<text x="20" y="{y+24}">MISSING COMPONENT — no invented zero bars</text>');continue
        peak=max(sum(r['p1_a'][phase][f] for f in fields)/1e6 for r in selected) or 1
        svg.append(f'<text x="940" y="{y}">scale 0 to {peak:.3f} ms</text>')
        for j,r in enumerate(selected):
            x=22+j*35;bottom=y+145
            for f,color in zip(fields,colors):
                h=130*(r['p1_a'][phase][f]/1e6)/peak
                bottom-=h;svg.append(f'<rect x="{x}" y="{bottom}" width="25" height="{h}" fill="{color}"/>')
            svg.append(f'<text x="{x}" y="{y+165}" font-size="8">b{r["block"]}{r["condition"]}</text>')
    return '\n'.join(svg+['</svg>'])


def _write_report(rows,output_dir,*,bootstrap_count,sources):
    from .gate8_files import _write
    from .gate8_adapter import digest
    output_dir=Path(output_dir)
    if output_dir.exists():raise FileExistsError(output_dir)
    value=summarize(rows,bootstrap_count=bootstrap_count)
    value.update(sources)
    output_dir.mkdir(parents=True)
    with (output_dir/'originals.csv').open('x',encoding='utf-8',newline='') as f:
        writer=csv.writer(f);writer.writerow(['block','condition','pass','pair','run','order',*PHASES])
        for r in sorted(rows,key=lambda x:x['order']):writer.writerow([r[k] for k in ('block','condition','pass_id','pair_id','run_id','order')]+[r['host_ns'][p] for p in PHASES])
    (output_dir/'paired.svg').write_text(_plot(rows),encoding='utf-8')
    (output_dir/'p1_a.svg').write_text(_a_plot(rows),encoding='utf-8')
    _write(output_dir/'individual_b.json',dict(aggregation='FORBIDDEN',runs=[
        dict(run_id=r['run_id'],block=r['block'],condition=r['condition'],records=r.get('b_records',[]),
             status='N1_PER_SYNC_ONLY' if r['condition'].startswith('N') else 'NOT_QUALIFIED_FOR_G1')
        for r in rows if r['pass_id']=='pass1']))
    value['artifacts']={name:digest(output_dir/name) for name in ('originals.csv','paired.svg','p1_a.svg','individual_b.json')}
    _write(output_dir/'statistics.json',value)
    return output_dir/'statistics.json'
