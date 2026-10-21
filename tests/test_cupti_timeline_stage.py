import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


ROOT=Path(__file__).resolve().parents[1]


def module():
    p=ROOT/'scripts/cupti_timeline_stage.py'
    assert p.is_file(), 'bounded timeline stage A entry missing'
    s=importlib.util.spec_from_file_location('_timeline_stage_test',p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def valid():
    return dict(schema_version='cupti-timeline-stage-a/0.1.0',default_stage='A_ONLY_NO_B_ENTRY',
        execution_commit='a'*40,analysis_commit='a'*40,prerequisite='b'*40,
        model_process_budget=0,profile_budget=0,micro_process_budget=0,sdk_files=[1],cupti_files=[1],
        cpu_test_count=1)


def test_static_contract_and_exact_cpu_selection():
    m=module();m.validate_delivery(valid())
    assert m.CPU_TESTS==['tests/test_submit_effect_bridge.py','tests/test_cupti_timeline_adapter.py',
        'tests/test_cupti_timeline_session.py','tests/test_cupti_timeline_native.py','tests/test_cupti_timeline_stage.py']


def startup_delivery():
    c=valid();c.update(schema_version='cupti-timeline-stage-a/0.1.1',
        startup_diagnostic_version='cupti-timeline-startup/0.1.0')
    return c


def test_versioned_stage_selects_real_startup_dll_and_failed_process_checks():
    m=module();c=startup_delivery();m.validate_delivery(c)
    assert m.selected_cpu_tests(c)==m.CPU_TESTS+[
        'tests/test_cupti_timeline_startup.py','tests/test_cupti_timeline_b.py']
    assert m.selected_cpu_tests(valid())==m.CPU_TESTS


def test_activity_policy_stage_is_separate_from_old_diagnostic_stage():
    c=valid();c.update(schema_version='cupti-timeline-stage-a/0.1.2',startup_diagnostic_version='cupti-timeline-startup/0.2.0',
        activity_policy_version='cupti-api22-activity-policy/0.2.0')
    m=module();m.validate_delivery(c)
    assert m.selected_cpu_tests(c)==['tests/test_cupti_activity_policy.py','tests/test_cupti_timeline_startup.py',
        'tests/test_cupti_timeline_session.py','tests/test_cupti_timeline_native.py','tests/test_cupti_event_probe.py','tests/test_cupti_timeline_stage.py',
        'tests/test_cupti_timeline_adapter.py::test_historical_event_is_closed_only_by_explicit_callback_and_later_drain']
    for key,value in [('startup_diagnostic_version','cupti-timeline-startup/0.1.0'),('activity_policy_version','unknown'),
        ('schema_version','cupti-timeline-stage-a/0.1.1')]:
        with pytest.raises(ValueError):m.validate_delivery({**c,key:value})


def test_built_policy_cannot_be_mislabelled_as_legacy_diagnostic():
    m=module();old=startup_delivery()
    with pytest.raises(ValueError,match='BUILD_POLICY'):m.validate_build_policy(old,dict(activity_policy_version='cupti-api22-activity-policy/0.2.0'))
    m.validate_build_policy(old,{})
    new={**old,'schema_version':'cupti-timeline-stage-a/0.1.2','startup_diagnostic_version':'cupti-timeline-startup/0.2.0',
        'activity_policy_version':'cupti-api22-activity-policy/0.2.0'}
    with pytest.raises(ValueError,match='BUILD_POLICY'):m.validate_build_policy(new,{})
    m.validate_build_policy(new,dict(activity_policy_version='cupti-api22-activity-policy/0.2.0'))


@pytest.mark.parametrize('version',[None,'cupti-timeline-startup/0.2.0',False])
def test_new_static_delivery_cannot_silently_drop_or_guess_diagnostic_version(version):
    c=startup_delivery();c['startup_diagnostic_version']=version
    with pytest.raises(ValueError):module().validate_delivery(c)


def test_legacy_static_contract_cannot_claim_new_startup_diagnostic():
    c=valid();c['startup_diagnostic_version']='cupti-timeline-startup/0.1.0'
    with pytest.raises(ValueError):module().validate_delivery(c)


@pytest.mark.parametrize('key,value', [('model_process_budget',1),('profile_budget',1),
    ('micro_process_budget',1),('default_stage','B'),('schema_version','old'),('analysis_commit','c'*40)])
def test_stage_A_cannot_silently_become_a_capture(key,value):
    c=valid();c[key]=value
    with pytest.raises(ValueError):module().validate_delivery(c)


def test_real_isolated_stage_CLI_has_no_collection_opt_in(tmp_path):
    p=ROOT/'scripts/cupti_timeline_stage.py';assert p.is_file(), 'bounded timeline stage A entry missing'
    r=subprocess.run([sys.executable,'-I','-S','-B',str(p),'--collect-reviewed-input-pilot'],
        cwd=tmp_path,capture_output=True,text=True,timeout=20)
    assert r.returncode==2 and 'usage:' in r.stderr and 'Traceback' not in r.stderr


def test_powershell51_launcher_rejects_capture_before_any_configuration_or_deployment():
    import os
    p=ROOT/'scripts/run_cupti_timeline_a.ps1'
    assert p.is_file(), 'new Stage A launcher missing'
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    r=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(p),'-Capture'],
        cwd=ROOT,capture_output=True,timeout=20)
    assert r.returncode!=0 and b'Stage A only' in r.stderr and b'delivery.json' not in r.stderr


def test_real_ps51_positive_hash_gate_reaches_only_a_cpu_driver_double(tmp_path):
    import hashlib,json,os
    p=ROOT/'scripts/run_cupti_timeline_a.ps1'
    (tmp_path/p.name).write_bytes(p.read_bytes())
    assets={'cupti_timeline_stage.py':'from pathlib import Path\nPath(__file__).with_name("entered.txt").write_text("CPU_DOUBLE")\n',
        'micro_support.py':'# CPU support double\n','independent_cupti_stage.py':'# CPU parent double\n'}
    for name,text in assets.items():(tmp_path/name).write_text(text,encoding='utf8')
    digest=lambda name:hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()
    cfg=dict(python=sys.executable,bootstrap_sha256=digest('cupti_timeline_stage.py'),
        support_sha256=digest('micro_support.py'),parent_stage_sha256=digest('independent_cupti_stage.py'))
    (tmp_path/'delivery.json').write_text(json.dumps(cfg),encoding='utf8')
    ps=Path(os.environ['SystemRoot'])/'System32/WindowsPowerShell/v1.0/powershell.exe'
    r=subprocess.run([str(ps),'-NoProfile','-ExecutionPolicy','Bypass','-File',str(tmp_path/p.name)],
        cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    assert (tmp_path/'entered.txt').read_text()=='CPU_DOUBLE'


def test_packaged_isolated_bootstrap_does_not_pollute_its_own_exact_manifest_directory(tmp_path):
    for src,dst in [('cupti_timeline_stage.py','cupti_timeline_stage.py'),
        ('independent_cupti_stage.py','independent_cupti_stage.py'),('memset_micro.py','micro_support.py')]:
        (tmp_path/dst).write_bytes((ROOT/'scripts'/src).read_bytes())
    before={p.name for p in tmp_path.iterdir()}
    r=subprocess.run([sys.executable,'-I',str(tmp_path/'cupti_timeline_stage.py'),'--help'],
        cwd=tmp_path,capture_output=True,timeout=20)
    assert r.returncode==0,r.stderr.decode(errors='replace')
    assert {p.name for p in tmp_path.iterdir()}==before
