"""Real fresh-process test-helper resolution, without native/CUDA execution."""
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


REPO=Path(__file__).resolve().parents[1]


def external_tests(tmp_path):
    external=tmp_path/'external';package=external/'tests';package.mkdir(parents=True)
    marker=tmp_path/'external-imported'
    (package/'__init__.py').write_text('from pathlib import Path\nPath('+repr(str(marker))+').write_text("external tests imported")\n',encoding='utf-8')
    gguf=tmp_path/'engine/gguf-py';gguf.mkdir(parents=True)
    return external,gguf,marker


def test_native_helper_forward_and_reverse_imports_survive_external_tests_package(tmp_path):
    external,gguf,marker=external_tests(tmp_path)
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,(gguf,external))),CUDA_VISIBLE_DEVICES='-1',PYTHONDONTWRITEBYTECODE='1')
    nodes=['tests/test_native_ninja.py::test_build_receipt_versions_cannot_disguise_generator',
        'tests/test_native_ninja.py::test_actual_stage1_file_consumer_reuses_cpu_and_gates_native_on_both_prechecks',
        'tests/test_native_ninja.py::test_new_receipt_refuses_changed_compile_evidence_even_if_rehashed']
    result=subprocess.run([sys.executable,'-X','utf8','-m','pytest','-q','-rs','-p','no:cacheprovider',
        *nodes,'--basetemp',str(tmp_path/'child-tests')],cwd=REPO,env=env,capture_output=True,timeout=120)
    assert result.returncode==0,result.stdout.decode('utf-8')+result.stderr.decode('utf-8')
    assert b'6 passed' in result.stdout and not marker.exists()


def test_actual_cpu_plan_binds_local_modules_and_retains_skip_reporting(tmp_path):
    from exposedpath import native_stage1 as s
    external,gguf,marker=external_tests(tmp_path)
    root=tmp_path/'run';root.mkdir()
    cfg=dict(test_python=sys.executable)
    env=dict(os.environ,PYTHONPATH=os.pathsep.join(map(str,(gguf,external))),CUDA_VISIBLE_DEVICES='-1')
    plan=s.cpu_regression_plan(cfg,REPO,root,env,tmp_path/'fixed-cmake.exe',True)
    assert plan['argv'][:6]==[sys.executable,'-X','utf8','-m','pytest','-q']
    assert '-rs' in plan['argv'] and plan['cwd']==REPO
    assert plan['env']['PYTHONPATH'].split(os.pathsep)[:2]==[str(REPO/'tests'),str(REPO)]
    assert plan['argv'][plan['argv'].index('--basetemp')+1]==str(root/'cpu-tests')
    result=s.bind_cpu_regression_environment(plan,root,s.Runner(root))
    assert Path(result['executable']).resolve()==Path(sys.executable).resolve()
    assert Path(result['cwd'])==REPO and result['environment']['PYTHONPATH']==plan['env']['PYTHONPATH']
    assert result['status']=='CPU_TEST_ENVIRONMENT_BOUND_NOT_BUILD_QUALIFICATION'
    assert result['modules']['test_native_ninja']['origin']==str(REPO/'tests/test_native_ninja.py')
    assert not marker.exists() # finding an unrelated tests package does not import it
    # Same command/file list as production, but only collect: no compiler/model.
    collected=subprocess.run([*plan['argv'],'--collect-only'],cwd=plan['cwd'],env=plan['env'],capture_output=True,timeout=60)
    assert collected.returncode==0,collected.stdout.decode('utf-8')+collected.stderr.decode('utf-8')


def test_environment_probe_rejects_wrong_helper_origin_and_records_actual(tmp_path):
    from exposedpath import native_stage1 as s
    root=tmp_path/'run';root.mkdir();other=tmp_path/'other';other.mkdir()
    (other/'test_native_ninja.py').write_text('# unrelated module, must not be imported\n')
    plan=s.cpu_regression_plan(dict(test_python=sys.executable),REPO,root,dict(os.environ),tmp_path/'cmake',True)
    plan['env']['PYTHONPATH']=os.pathsep.join((str(other),plan['env']['PYTHONPATH']))
    with pytest.raises(ValueError,match='CPU_TEST_MODULE_ORIGIN'):
        s.bind_cpu_regression_environment(plan,root,s.Runner(root))
    raw=json.loads((root/'logs/cpu_regression_environment.stdout.txt').read_text(encoding='utf-8'))
    assert raw['modules']['test_native_ninja']['origin']==str(other/'test_native_ninja.py')


def test_native_configure_uses_verified_git_even_when_build_path_has_no_git(tmp_path):
    from exposedpath import native_stage1 as s
    from test_native_ninja import tools
    actual_git=tmp_path/'verified/git.exe'
    plan=s.command_plan(tmp_path/'code',tmp_path/'engine',tmp_path/'new',tmp_path/'hf',
        tmp_path/'nvtx',tmp_path/'cuda',tools=tools(tmp_path),git_executable=actual_git)
    assert '-DGIT_EXECUTABLE:FILEPATH='+actual_git.as_posix() in plan[0]['arguments']


def test_stage1_entry_consumes_bound_cpu_environment_before_compile(tmp_path,monkeypatch):
    from test_native_stage1 import test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts
    from exposedpath import native_stage1 as s
    test_cpu_file_chain_runs_all_stage1_steps_and_creates_bound_receipts(tmp_path,monkeypatch,ninja=True,cpu_entry=True)
    root=tmp_path/'diagnostics/new'
    observed=s.read(root/'cpu_regression_environment.json')
    assert observed['status']=='CPU_TEST_ENVIRONMENT_BOUND_NOT_BUILD_QUALIFICATION'
    assert observed['cwd']==str(tmp_path/'code')
    steps=[x['name'] for x in s.read(root/'receipt.json')['steps']]
    assert steps.index('cpu_regression_environment')<steps.index('cpu_regression')<steps.index('cxx_configure')
