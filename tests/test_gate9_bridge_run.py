import importlib
from pathlib import Path


def test_profile_uses_direct_interpreter_and_explicit_single_target():
    assert importlib.util.find_spec('scripts.gate9_bridge_run'), 'bridge collection adapter missing'
    from scripts.gate9_bridge_run import profile_argv
    args=profile_argv('nsys.exe','direct python.exe','site packages',Path('plan.json'),Path('out'))
    assert args[:3]==['nsys.exe','profile','--trace=cuda,nvtx']
    assert '--sample=none' in args and '--cpuctxsw=none' in args
    assert args[args.index('direct python.exe')+1:args.index('direct python.exe')+3]==['-I','-S']
    assert args[-1]=='--execute-controlled'
    assert not any('force-overwrite' in a for a in args)


def test_bad_git_identity_stops_before_any_profile(tmp_path,monkeypatch):
    from scripts.gate9_bridge_run import main
    from exposedpath_v141.gate8_files import _json
    def reject(_): raise ValueError('test identity conflict')
    monkeypatch.setattr('exposedpath_v141.gate8_controlled_cli.check_git',reject)
    def forbidden(*a,**k): raise AssertionError('profile must not start')
    monkeypatch.setattr('scripts.gate8_diagnostic_collect.run_once',forbidden)
    argv=[]
    for name,value in dict(python='direct.exe',site='site',nsys='nsys.exe',library='lib.dll',
        commit='a'*40,uuid='unused',pci='unused',output=str(tmp_path/'out')).items():
        argv+=['--'+name,value]
    assert main([*argv,'--execute-controlled'])==1
    report=_json(tmp_path/'out/collection_report.json')
    assert report['status']=='BLOCKED' and 'test identity conflict' in report['error']
    assert report['gate9_verdict']=='NOT_RUN'


def test_real_isolated_target_imports_preserve_probe_snapshot(tmp_path):
    import json
    import subprocess
    import sys
    import sysconfig
    from exposedpath_v141.gate8_target_python import probe,ROOT
    site=sysconfig.get_path('purelib')
    contract=probe(sys._base_executable,site)
    path=tmp_path/'probe.json'; path.write_text(json.dumps(contract),encoding='utf-8')
    code=('import sys,json;sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];'
          'from scripts.gate9_bridge_target import execute;'
          'from exposedpath_v141.gate8_files import _json,_write,_entry,_resolve;'
          'from exposedpath_v141.gate8_adapter import digest,normalized_uuid,normalized_pci;'
          'from exposedpath_v141.gate8_target_python import current;'
          'assert "torch" not in sys.modules;'
          'print(json.dumps(current(_json(sys.argv[1]))))')
    child=subprocess.run([sys._base_executable,'-I','-S','-c',code,str(ROOT),site,str(path)],
        cwd=ROOT,capture_output=True,timeout=20,check=True)
    assert json.loads(child.stdout)['snapshot']==contract['actual']['snapshot']
