"""New provider Stage A only. Reuse the reviewed deployment/retention helpers.

No model, GPU micro, profiler, or capture opt-in exists in this entry.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import sys


# -I intentionally ignores PYTHONDONTWRITEBYTECODE. Set the interpreter flag
# before importing a sibling, so the exact package manifest is not polluted.
sys.dont_write_bytecode=True
_base_path=Path(__file__).with_name('independent_cupti_stage.py')
_spec=importlib.util.spec_from_file_location('_timeline_deployment_base',_base_path)
base=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(base)
CPU_TESTS=['tests/test_submit_effect_bridge.py','tests/test_cupti_timeline_adapter.py',
    'tests/test_cupti_timeline_session.py','tests/test_cupti_timeline_native.py','tests/test_cupti_timeline_stage.py']


def validate_delivery(c):
    version=c.get('schema_version')
    diagnostic_ok=(version=='cupti-timeline-stage-a/0.1.0' and 'startup_diagnostic_version' not in c and 'activity_policy_version' not in c or
        version=='cupti-timeline-stage-a/0.1.1' and
        c.get('startup_diagnostic_version')=='cupti-timeline-startup/0.1.0' and 'activity_policy_version' not in c or
        version=='cupti-timeline-stage-a/0.1.2' and c.get('startup_diagnostic_version')=='cupti-timeline-startup/0.2.0' and
        c.get('activity_policy_version')=='cupti-api22-activity-policy/0.2.0')
    ok=(diagnostic_ok and
        c.get('default_stage')=='A_ONLY_NO_B_ENTRY' and
        all(type(c.get(k)) is int and c[k]==0 for k in ('model_process_budget','profile_budget','micro_process_budget')) and
        c.get('execution_commit')==c.get('analysis_commit') and
        re.fullmatch('[0-9a-f]{40}',c.get('execution_commit','')) and
        re.fullmatch('[0-9a-f]{40}',c.get('prerequisite','')) and
        c.get('sdk_files') and c.get('cupti_files') and type(c.get('cpu_test_count')) is int and c['cpu_test_count']>0)
    if not ok:raise ValueError('CUPTI_TIMELINE_A_ONLY_DELIVERY')


def selected_cpu_tests(c):
    validate_delivery(c)
    if c['schema_version']=='cupti-timeline-stage-a/0.1.0':return list(CPU_TESTS)
    if c['schema_version']=='cupti-timeline-stage-a/0.1.2':
        return ['tests/test_cupti_activity_policy.py','tests/test_cupti_timeline_startup.py',
            'tests/test_cupti_timeline_session.py','tests/test_cupti_timeline_native.py',
            'tests/test_cupti_event_probe.py','tests/test_cupti_timeline_stage.py',
            'tests/test_cupti_timeline_adapter.py::test_historical_event_is_closed_only_by_explicit_callback_and_later_drain']
    return CPU_TESTS+['tests/test_cupti_timeline_startup.py','tests/test_cupti_timeline_b.py']


def validate_build_policy(c,built):
    new=c['schema_version']=='cupti-timeline-stage-a/0.1.2'
    if not (built.get('activity_policy_version')==c['activity_policy_version'] if new else 'activity_policy_version' not in built):
        raise ValueError('CUPTI_TIMELINE_A_BUILD_POLICY_CONFLICT')


def stage_a(package):
    m=base.support();package=Path(package).resolve();index=m.verify_package(package)
    cfg=json.loads((package/'delivery.json').read_text(encoding='utf8'));validate_delivery(cfg)
    root=Path(cfg['server_root']);code=Path(cfg['code_root']);tag=cfg['execution_commit'][:12]
    out=m.safe(root,'diagnostics/cupti_timeline_'+tag+'_static')
    archive=m.safe(root,'transfer/cupti_timeline_'+tag+'_static.zip')
    m.require(not out.exists() and not archive.exists(),'NO_OVERWRITE_RESUME_RETRY')
    out.mkdir(parents=True,exist_ok=False);archive.parent.mkdir(parents=True,exist_ok=True)
    for name in ('delivery.json','package_manifest.json','prerequisite_reference.json','dependency_sources.json'):
        if (package/name).is_file():shutil.copyfile(package/name,out/name)
    status='BLOCKED';error=None
    try:
        m.require(list(sys.version_info[:3])==cfg['python_version'],'PYTHON_VERSION')
        base.deploy(cfg,package,out);m.tree(cfg,cfg['execution_commit'])
        m.write(out/'source_bytes.json',base.verify_sources(code,cfg['source_representations']))
        m.write(out/'checkout_imports.json',base.bind_checkout_modules(cfg))
        m.write(out/'resources.json',base.startup_resources(out,archive,cfg))
        for name,fact in cfg['toolchain_files'].items():m.require(m.file_fact(fact['path'])==fact,'TOOLCHAIN:'+name)
        runtime=m.runtime_fact(cfg['runtime_path']);m.write(out/'runtime_file.json',runtime)
        m.require(runtime==cfg['runtime_file'],'RUNTIME_FILE_IDENTITY')
        m.extract(package/'sdk.zip',out/'sdk');m.extract(package/'cupti.zip',out/'cupti')
        m.verify_rows(out/'sdk',cfg['sdk_files']);m.verify_rows(out/'cupti',cfg['cupti_files'])
        cupti=out/'cupti/lib/cupti64_2024.1.1.dll'
        m.require(m.sha(cupti)==cfg['cupti_dll_sha256'],'CUPTI_FILE_IDENTITY')
        m.write(out/'cupti_file.json',m.file_fact(cupti))
        build=dict(cfg['build'],source_root=str(code),runtime_path=cfg['runtime_path'],
            cuda_include=str(out/'sdk/include'),crt_include=str(out/'sdk/include'),cupti_include=str(out/'cupti/include'))
        base.inspect_exports(build,cfg['runtime_path'],cupti,out/'export_inspection')
        exported=(out/'export_inspection/cupti_exports.stdout').read_bytes().decode('utf8',errors='replace')
        m.require(all(re.search(r'\b'+name+r'\b',exported) for name in ('cuptiGetTimestamp','cuptiActivityEnableAndDump')),'NEW_PROVIDER_EXPORTS')
        path=code/'scripts/build_cupti_timeline.py'
        spec=importlib.util.spec_from_file_location('_verified_timeline_build',path)
        builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(builder)
        built=builder.build(build,out/'build');validate_build_policy(cfg,built);m.write(out/'build_configuration.json',build)
        env=os.environ.copy()
        for k in ('PYTEST_ADDOPTS','PYTEST_PLUGINS'):env.pop(k,None)
        env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',CUDA_VISIBLE_DEVICES='-1',
            CUPTI_TIMELINE_CPU_CONFIG=str(out/'build_configuration.json'),
            CUPTI_TIMELINE_BUILT_JSON=str(out/'build/build.json'))
        m.command([cfg['python'],'-X','utf8','-m','pytest','-q','-ra','-p','no:cacheprovider',*selected_cpu_tests(cfg),
            '--basetemp',str(out/'cpu_tmp'),'--junitxml',str(out/'cpu.xml')],code,out/'cpu',env=env,timeout=600)
        import xml.etree.ElementTree as ET
        suites=ET.parse(out/'cpu.xml').getroot().findall('testsuite')
        m.require(suites and sum(int(s.attrib['tests']) for s in suites)==cfg['cpu_test_count'] and
            all(s.attrib[k]=='0' for s in suites for k in ('failures','errors','skipped')),'CPU_RESULT')
        base.verify_sources(code,cfg['source_representations']);m.verify_rows(out/'build',built['binaries'])
        m.verify_rows(out/'sdk',cfg['sdk_files']);m.verify_rows(out/'cupti',cfg['cupti_files'])
        m.require(runtime==m.runtime_fact(cfg['runtime_path']),'RUNTIME_CHANGED_DURING_A')
        m.tree(cfg,cfg['execution_commit']);status='STATIC_READY_FOR_REVIEW'
    except BaseException as exc:error=type(exc).__name__+':'+str(exc)
    facts={p.name:m.sha(p) for p in out.iterdir() if p.is_file()}
    receipt=dict(schema_version='cupti-timeline-stage-a-receipt/0.1.0',phase='A',
        status=status,error=error,execution_commit=cfg['execution_commit'],analysis_commit=cfg['analysis_commit'],
        package_index_sha256=index,static_files=facts,stage_a_cuda_programs_executed=0,
        model_process_budget=0,micro_process_budget=0,profile_budget=0,B_authorized=False,
        automatic_retry=False,A_COE_admission='NOT_ASSESSED',pytorch_coverage='NOT_ASSESSED',
        historical_ylq_total_bytes=None,long_term_target_exclusive_bytes=50000000000)
    if cfg['schema_version'] in ('cupti-timeline-stage-a/0.1.1','cupti-timeline-stage-a/0.1.2'):
        receipt.update(schema_version=cfg['schema_version'].replace('stage-a/','stage-a-receipt/'),
            startup_diagnostic_version=cfg['startup_diagnostic_version'],cpu_tests=selected_cpu_tests(cfg))
    if cfg['schema_version']=='cupti-timeline-stage-a/0.1.2':receipt['activity_policy_version']=cfg['activity_policy_version']
    m.write(out/'receipt.json',receipt)
    try:print(json.dumps(m.pack(out,archive)),flush=True)
    except BaseException as exc:print('PACK_REFUSED_PRESERVE_SCENE:'+str(exc),flush=True);return 2
    if error:print('STOP:'+error,flush=True);return 2
    return 0


def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--package',required=True,type=Path)
    return stage_a(p.parse_args(argv).package)


if __name__=='__main__':raise SystemExit(main())
