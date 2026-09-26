"""Revalidated file-backed proof for the explicit controlled construction only."""
import json
from pathlib import Path

from .gate8_adapter import digest
from .gate8_controlled_raw import check_controlled_raw
from .gate8_files import load_input_receipt

SOURCE_KEYS={'plan','execution','collection','controlled_receipt','operation_ledger'}
PROFILE='G8-CONTROLLED-CUDA-NVTX/0.1.0'


class ControlledEvidence:
    def __init__(self,receipt_path,sources):
        if set(sources)!=SOURCE_KEYS: raise ValueError('CONTROLLED_SOURCE_SET_INVALID')
        self.receipt_path=Path(receipt_path).resolve()
        self.sources={k:Path(p).resolve() for k,p in sources.items()}
        self.hashes={k:digest(p) for k,p in self.sources.items()}
        self.receipt_hash=digest(self.receipt_path)
        self.review()

    def review(self):
        from .gate8_controlled_cli import SOURCE,NATIVE,PLAN_VERSION
        if digest(self.receipt_path)!=self.receipt_hash or any(digest(p)!=self.hashes[k] for k,p in self.sources.items()):
            raise ValueError('CONTROLLED_INPUT_CHANGED')
        receipt,paths=load_input_receipt(self.receipt_path)
        docs={k:json.loads(p.read_text(encoding='utf-8')) for k,p in self.sources.items()}
        plan,execution,collection=docs['plan'],docs['execution'],docs['collection']
        producer=paths['producer_receipt'].parent
        manifest=json.loads(paths['wmpc_manifest'].read_text())
        ledger=json.loads(paths['pass_identity'].read_text())
        if (self.sources['controlled_receipt']!=producer/'controlled_receipt.json'
                or self.sources['operation_ledger']!=producer/'operation_ledger.json'
                or plan.get('schema_version')!=PLAN_VERSION or plan.get('construction')!='CONTROLLED-D2H-REQUEST/0.1.0'
                or plan['expected_commit']!=manifest['runner_git_commit']
                or any(plan['identity'][k]!=manifest[k] for k in plan['identity'])
                or manifest['runner_source_sha256']!=digest(SOURCE)
                or plan['native_source_sha256']!=digest(NATIVE)
                or manifest['native_source_sha256']!=digest(NATIVE)
                or manifest['native_library_sha256']!=plan['library']['sha256']):
            raise ValueError('CONTROLLED_SOURCE_IDENTITY_CONFLICT')
        for key in ('wmpc_manifest','prompt','preflight','runner_source'):
            if plan['inputs'][key]['sha256']!=digest(paths[key]):
                raise ValueError('CONTROLLED_PLAN_INPUT_HASH_CONFLICT')
        if (execution.get('schema_version')!='exposedpath-controlled-execution/0.1.0'
                or execution.get('status')!='COMPLETE' or execution.get('errors')!=[]
                or type(execution.get('process_exit_code')) is not int or execution['process_exit_code']!=0
                or any(execution.get(k)!='COMPLETE' for k in ('init_status','warmup_status','cleanup_status'))
                or execution.get('plan_sha256')!=self.hashes['plan']
                or execution.get('commit')!=manifest['runner_git_commit']
                or execution.get('process_id')!=ledger['pid']
                or execution.get('producer_receipt_sha256')!=digest(paths['producer_receipt'])):
            raise ValueError('CONTROLLED_EXECUTION_NOT_ACCEPTABLE')
        if (collection.get('schema_version')!='exposedpath-controlled-collection/0.1.0'
                or type(collection.get('process_exit_code')) is not int or collection['process_exit_code']!=0
                or collection.get('execution_receipt_sha256')!=self.hashes['execution']
                or collection.get('plan_sha256')!=self.hashes['plan']
                or collection.get('rep_sha256')!=digest(paths['raw']) or collection.get('observation_profile')!=PROFILE):
            raise ValueError('CONTROLLED_COLLECTION_NOT_ACCEPTABLE')
        expected_flags=('--trace=cuda,nvtx','--sample=none','--cpuctxsw=none','--cuda-memory-usage=false',
                        '--cuda-trace-scope=process-tree','--isr=false')
        argv=collection.get('argv',[])
        if (not isinstance(argv,list) or any(not isinstance(a,str) for a in argv)
                or len(argv)!=19 or not argv[0] or argv[1:8]!=['profile',*expected_flags]
                or argv[8]!='--output' or not argv[9]
                or collection.get('rep_path')!=argv[9]+'.nsys-rep'
                or any(not isinstance(execution.get(k),str) or not execution[k]
                       for k in ('python_executable','plan_path','output_dir'))
                or argv[10:]!=[execution['python_executable'],'-m','exposedpath_v141.gate8_controlled_cli',
                               'run','--plan',execution['plan_path'],'--output-dir',execution['output_dir'],
                               '--execute-controlled']):
            raise ValueError('CONTROLLED_OBSERVATION_ARGV_CONFLICT')
        result=check_controlled_raw(paths['sqlite'],producer)
        result['input_receipt_sha256']=self.receipt_hash
        result['source_hashes']=dict(self.hashes)
        result['source_raw_sha256']=digest(paths['raw'])
        return result

    def validate_projection_and_s(self,canonical,projections,s_records):
        report=self.review()
        if canonical['source']['sqlite']['sha256'].lower()!=report['source_sqlite_sha256']:
            raise ValueError('CONTROLLED_CANONICAL_SOURCE_CONFLICT')
        full={(p['identity']['request_id'],p['identity']['repeat_id']):(p['start_ns'],p['end_ns'])
              for p in projections if p['phase']=='full_request'}
        if full!={(w['request_id'],w['repeat_id']):(w['start_ns'],w['end_ns']) for w in report['windows']}:
            raise ValueError('CONTROLLED_PROJECTION_CONFLICT')
        by_id={r['sync_id']:r for r in s_records}
        def key(kind,ref): return f"{kind}:{ref['source_table']}:{ref['source_rowid']}"
        issues=[]
        expected_ids={key('cuda_sync',e['sync_ref']) for e in report['sync_expectations']}
        actual_ids={r['sync_id'] for r in s_records
                    if (r.get('request_id'),r.get('repeat_id')) in full}
        if actual_ids!=expected_ids:
            issues.append('CONTROLLED_INDEPENDENT_ORACLE_SYNC_SET_MISMATCH')
        for expected in report['sync_expectations']:
            observed=by_id.get(key('cuda_sync',expected['sync_ref']))
            if (observed is None or observed['validity']!='VALID_NONEMPTY'
                    or observed['request_id']!=expected['request_id'] or observed['repeat_id']!=expected['repeat_id']
                    or set(observed['wait_set_activity_ids'])!={key('device_activity',r) for r in expected['wait_set_refs']}
                    or observed['terminal']['activity_id']!=key('device_activity',expected['terminal_ref'])):
                issues.append('CONTROLLED_INDEPENDENT_ORACLE_S_MISMATCH')
        report['s_comparison_issues']=sorted(set(issues))
        return report
