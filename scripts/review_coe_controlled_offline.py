"""Read one sealed controlled run; never executes/rebuilds a CUDA program.

The construction reference is evaluated before S and survives a downstream
refusal. Original BLOCKED receipts, correlations and API intervals are immutable.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

from scripts.coe_controlled_deployment import verified_evidence_archive
from scripts import coe_cupti_controlled as controlled
from analysis.cupti_call_instances import POLICY,CallInstances,normal

ROOT=Path(__file__).resolve().parents[1]
SOURCE_FILES=('scripts/review_coe_controlled_offline.py','scripts/coe_cupti_controlled.py',
    'scripts/coe_controlled_deployment.py','analysis/cupti_call_instances.py','analysis/cupti_timeline.py',
    'exposedpath_v141/submit_effect_bridge.py','exposedpath_v141/cupti_driver_queries.py',
    'exposedpath_v141/cupti_nested_launch_control.py',
    'scripts/analyze_completion_operation_candidate.py')


def sha(data):return hashlib.sha256(data).hexdigest()


def write(path,v):
    with Path(path).open('x',encoding='utf8') as f:json.dump(v,f,indent=2)


def review(archive,expected_sha,output,*,nested_launch_policy=None):
    from exposedpath_v141.cupti_nested_launch_control import POLICY as NESTED_POLICY
    controlled.require(nested_launch_policy in (None,NESTED_POLICY),'NESTED_LAUNCH_POLICY')
    archive,out=Path(archive),Path(output)
    controlled.require(not out.exists() and not archive.resolve().is_relative_to(out.resolve()),'NEW_OUTPUT')
    original=archive.read_bytes()
    controlled.require(sha(original)==expected_sha,'ARCHIVE_HASH')
    with zipfile.ZipFile(archive) as z:manifest_sha=sha(z.read('artifact_manifest.json'))
    files=verified_evidence_archive(archive,len(original),expected_sha,'artifact_manifest.json',manifest_sha)
    get=lambda name:json.loads(files[name])
    raw=get('once/bounded/run/timeline/capture.json');side=get('once/bounded/run/side.json')
    receipt=get('once/bounded/run/receipt.json');session=get('once/bounded/run/timeline/receipt.json')
    config=get('prepare/run_config.json');build=get('prepare/build/build.json')
    process=get('once/bounded/process.process.json')
    controlled.require(process['pid']==raw['pid']==side['pid']==session['pid'] and
        process['status']=='EXITED' and process['timed_out'] is False,'PROCESS_IDENTITY')
    controlled.require(raw['source']=='TARGET_CUPTI' and session['open_code']==session['close_code']==0 and
        session['session_id']==raw['session_id']==side['session_id']==config['run_id'],'SESSION_BINDING')
    controlled.require(session['capture_sha256']==sha(files['once/bounded/run/timeline/capture.json']) and
        receipt['config_sha256']==sha(files['prepare/run_config.json']) and
        config['program_sha256']==sha(files['prepare/build/coe_controlled.dll'])==build['program']['sha256'],
        'INPUT_BINDING')
    controlled.require(session['client_sha256']==controlled.CLIENT_SHA and
        session['cupti_sha256']==controlled.CUPTI_SHA,'LIBRARY_IDENTITY')
    source_hashes={n:sha((ROOT/n).read_bytes()) for n in SOURCE_FILES}
    commit=subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,check=True).stdout.decode().strip()
    exact=all(sha(subprocess.run(['git','show',commit+':'+n],cwd=ROOT,capture_output=True).stdout)==s
              for n,s in source_hashes.items())
    out.mkdir(parents=True)
    report=dict(schema_version='coe-controlled-offline-review/0.3.0' if nested_launch_policy else
                              'coe-controlled-offline-review/0.2.0',status='BLOCKED',
        target_execution='EXECUTED',execution_commit=get('once/receipt.json')['execution_commit'],
        analysis_commit=commit if exact else None,analysis_source_sha256=source_hashes,
        call_instance_policy=POLICY,archive_sha256=expected_sha,manifest_sha256=manifest_sha,
        capture_sha256=session['capture_sha256'],side_sha256=sha(files['once/bounded/run/side.json']),
        original_status=receipt['status'],original_error=receipt['error'],original_process_exit=process['exit_code'],
        original_reports_rewritten=False,original_post_control_status='NOT_REACHED_AFTER_WORKER_REFUSAL',
        reference=None,consumer_result=None,remaining_semantic_gaps=[],error=None,
        qualification='NOT_GRANTED',formal_eligible=False,server_action_required=False)
    if nested_launch_policy:
        report.update(nested_launch_policy=nested_launch_policy,full_Q0='NOT_GRANTED',
            verdicts=dict(independent_reference='NOT_RUN',consumer_admission='NOT_RUN',
                          controlled_connection='NOT_RUN'))
    try:
        # This fixes MEMBERS from the prior construction and times from Raw;
        # it never calls S to create an expected answer.
        ref=controlled.independent_reference(raw,side,call_instance_policy=POLICY)
        report['reference']=ref;write(out/'reference.json',ref)
        if nested_launch_policy:report['verdicts']['independent_reference']='PASS'
        ix=CallInstances(raw['callbacks'],raw['pid'])
        write(out/'correlation_groups.json',ix.inventory())
        from analysis.cupti_timeline import select_scope,to_evidence,analyze_scope
        producer=dict(session_id=side['session_id'],pid=side['pid'],tid=side['tid'],run_id=side['run_id'],
                      actual_token_ids=side['actual_token_ids'],**side['labels'])
        scope=select_scope(raw,producer,timing_policy=controlled.TIMING,driver_query_policy=controlled.QUERIES,
                           call_instance_policy=POLICY,nested_launch_policy=nested_launch_policy)
        write(out/'scope.json',scope)
        evidence=to_evidence(raw,scope,timing_policy=controlled.TIMING,driver_query_policy=controlled.QUERIES,
                             call_instance_policy=POLICY,nested_launch_policy=nested_launch_policy)
        write(out/'evidence.json',evidence)
        nested_controls=[]
        if nested_launch_policy:
            from exposedpath_v141.cupti_nested_launch_control import validate_nested_launch_controls
            nested_controls=validate_nested_launch_controls(evidence)
            write(out/'nested_launch_controls.json',nested_controls)
        nested_ids={c['callback_id'] for c in nested_controls}
        from exposedpath_v141.cupti_driver_queries import RULES,DRIVER_OPERATIONS,NESTED_HELPERS
        for c in evidence['callbacks']:
            if c['domain']!='DRIVER' or c.get('parent_id') is None:continue
            if not scope['request_start']<=c['start']<scope['completion_end']:continue
            if c['id'] in nested_ids:continue
            root=ix.root(c)
            if c['name'] in RULES or (c['name'],c['cbid']) in DRIVER_OPERATIONS or \
                NESTED_HELPERS.get((c['name'],c['cbid']))==normal(root['name']):
                continue
            report['remaining_semantic_gaps'].append(dict(callback_id=c['id'],parent_id=c['parent_id'],
                name=c['name'],domain=c['domain'],cbid=c['cbid'],correlation=c['correlation'],
                runtime_root_id=root['id'],runtime_root_name=root['name'],
                callback_interval_ns=[c['start'],c['end']],params=c['params'],
                reason='NOT_IN_EXISTING_EXACT_NESTED_DRIVER_SUPPORT_RULES; NOT_PROVEN_NO_EFFECT'))
        result=analyze_scope(evidence)
        report['consumer_result']=result
        if nested_launch_policy:report['verdicts']['consumer_admission']='PASS'
        controlled.require(result['members']==ref['members'] and result['terminal']==ref['terminal'] and
            result['logical_zero_call_ids']==ref['logical_zero_call_ids'],'MEMBER_OR_TERMINAL_MISMATCH')
        controlled.require(result['coe_ns']==ref['expected_coe_ns'] and
            result['sync_intersection_ns']==ref['expected_sync_ns'] and
            result['operation_wall_ns']==ref['wall_ns'],'ARITHMETIC_MISMATCH')
        if nested_launch_policy:
            report['verdicts']['controlled_connection']='PASS'
            report['status']='LIMITED_CONTROLLED_CONNECTION_PASS'
        else:report['status']='CONTROLLED_REFERENCE_MATCH_PENDING_REVIEW'
        write(out/'consumer.json',result)
    except Exception as exc:
        report['error']=type(exc).__name__+':'+str(exc)
        if nested_launch_policy:
            first=next((k for k,v in report['verdicts'].items() if v=='NOT_RUN'),None)
            if first:report['verdicts'][first]='BLOCKED'
    controlled.require(archive.read_bytes()==original,'SOURCE_CHANGED')
    write(out/'review.json',report)
    return report


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive',type=Path,required=True)
    p.add_argument('--archive-sha256',required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--nested-launch-policy',default=None)
    a=p.parse_args();r=review(a.archive,a.archive_sha256,a.output,nested_launch_policy=a.nested_launch_policy)
    print(json.dumps(dict(status=r['status'],error=r['error'],target_execution=r['target_execution'])))
    return 0 if r['status'] in ('CONTROLLED_REFERENCE_MATCH_PENDING_REVIEW','LIMITED_CONTROLLED_CONNECTION_PASS') else 2


if __name__=='__main__':raise SystemExit(main())
