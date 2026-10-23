"""Deployment only: real Git bytes plus explicitly labelled target-tool doubles."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT / '.local/transfer/coe_controlled_c8f3dad_review'
AUTH = ROOT / '.local/transfer/coe_controlled_c8f3dad_authorized.json'
FIXED = 'c8f3dad152659044691f9ff328498c7a127815ea'
OLD_INDEX = '238d31c40ee74cab158eb5ad8de67d753da6b4aa3878c756c7ded467633eaa1a'
AUTH_SHA = '39b46e3189e93b55f1bb21e895d38bbc0ae535e77e45633ee4584ef69ca5c69e'
REPAIR1 = ROOT / '.local/transfer/coe_controlled_c8f3dad_repair1_once.zip'
GIT_STATE = ROOT / '.local/transfer/coe_controlled_git_state_20261023T143900Z_e6097796bac048f2a4d7c6bb78196c5f.zip'


@pytest.fixture(autouse=True)
def no_package_bytecode(monkeypatch):
    # The actual entry is always -B; reproduce that property for in-process checks.
    monkeypatch.setattr(sys, 'dont_write_bytecode', True)
    monkeypatch.setattr(sys, 'path', list(sys.path))
    for name in ('TEMP', 'TMP', 'TMPDIR'):
        if name in os.environ:
            monkeypatch.setenv(name, os.environ[name])
        else:
            monkeypatch.delenv(name, raising=False)
    prefixes = ('analysis', 'exposedpath', 'exposedpath_v141', '_exposedpath_completion_math_v01')
    saved = {n: v for n, v in sys.modules.items() if any(n == p or n.startswith(p + '.') for p in prefixes)}
    yield
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + '.') for p in prefixes):
            del sys.modules[name]
    sys.modules.update(saved)


def module():
    path = (Path(os.environ['COE_REPAIR_TEST_PACKAGE']) / 'coe_controlled_deployment.py'
            if 'COE_REPAIR_TEST_PACKAGE' in os.environ else ROOT / 'scripts/coe_controlled_deployment.py')
    assert path.is_file(), 'binary fixed-blob deployment repair is not implemented'
    spec = importlib.util.spec_from_file_location('repair_under_test', path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                          check=True).stdout


def row(path, data):
    return dict(path=path, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


@pytest.fixture
def tree(tmp_path):
    repo = tmp_path / 'repo (with space)'
    repo.mkdir()
    git(repo, 'init', '-q')
    git(repo, 'config', 'user.name', 'CPU fixture')
    git(repo, 'config', 'user.email', 'fixture@example.invalid')
    git(repo, 'config', 'core.autocrlf', 'false')
    (repo / 'source.cu').write_bytes(b'first\nsecond\n')
    (repo / 'other.py').write_bytes(b'a\nb\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'before')
    before = git(repo, 'rev-parse', 'HEAD').decode().strip()
    (repo / 'unrelated.txt').write_bytes(b'new revision\n')
    git(repo, 'add', '.')
    git(repo, 'commit', '-qm', 'after; source unchanged')
    after = git(repo, 'rev-parse', 'HEAD').decode().strip()
    git(repo, 'checkout', '-q', '--detach', before)
    git(repo, 'config', 'core.autocrlf', 'true')
    (repo / 'source.cu').write_bytes(b'first\r\nsecond\r\n')
    git(repo, '-c', 'core.autocrlf=false', 'checkout', '-q', '--detach', after)
    return repo, after


def test_real_unchanged_checkout_does_not_materialize_lf(tree):
    repo, commit = tree
    assert (repo / 'source.cu').read_bytes() == b'first\r\nsecond\r\n'
    assert git(repo, 'show', commit + ':source.cu') == b'first\nsecond\n'
    assert b'i/lf    w/crlf' in git(repo, 'ls-files', '--eol', '--', 'source.cu')


@pytest.mark.parametrize('ending', ['LF', 'CRLF'])
def test_binary_materialization_uses_fixed_blob_and_preserves_prior_bytes(tree, tmp_path, ending):
    m = module()
    repo, commit = tree
    original = b'first\nsecond\n' if ending == 'LF' else b'first\r\nsecond\r\n'
    (repo / 'source.cu').write_bytes(original)
    report = m.materialize_sources('git', repo, commit,
        [row('source.cu', b'first\nsecond\n')], tmp_path / 'evidence')
    assert (repo / 'source.cu').read_bytes() == b'first\nsecond\n'
    assert report['files'][0]['rewritten'] is (ending == 'CRLF')
    assert report['files'][0]['before_sha256'] == hashlib.sha256(original).hexdigest()
    assert git(repo, 'config', '--get', 'core.autocrlf').strip() == b'true'
    if ending == 'CRLF':
        assert (tmp_path / 'evidence/source_before/source.cu').read_bytes() == original


@pytest.mark.parametrize('bad', [b'a\nchanged\n', b'a\r\nb\n', b'a\rb\r'])
def test_preflight_rejects_unknown_content_before_any_source_write(tree, tmp_path, bad):
    m = module()
    repo, commit = tree
    (repo / 'other.py').write_bytes(bad)
    with pytest.raises(ValueError, match='CONTENT_NOT_PROVEN_EOL:other.py'):
        m.materialize_sources('git', repo, commit,
            [row('source.cu', b'first\nsecond\n'), row('other.py', b'a\nb\n')], tmp_path / 'evidence')
    assert (repo / 'source.cu').read_bytes() == b'first\r\nsecond\r\n'
    assert (repo / 'other.py').read_bytes() == bad


def test_fixed_manifest_hash_and_duplicate_paths_are_not_replaced_by_actual_values(tree, tmp_path):
    m = module()
    repo, commit = tree
    expected = row('source.cu', b'first\nsecond\n')
    with pytest.raises(ValueError, match='BLOB_MANIFEST_CONFLICT'):
        m.materialize_sources('git', repo, commit, [{**expected, 'sha256': '0' * 64}], tmp_path / 'bad')
    with pytest.raises(ValueError, match='DUPLICATE_PATH'):
        m.materialize_sources('git', repo, commit, [expected, expected], tmp_path / 'duplicate')
    assert (repo / 'source.cu').read_bytes() == b'first\r\nsecond\r\n'


def old_receipt():
    return dict(schema_version='coe-controlled-delivery-receipt/0.1.0', action='prepare',
        status='BLOCKED', error='ValueError:CONTROLLED_DELIVERY_FILE_IDENTITY:scripts/gate8_qualification_token.cu',
        execution_commit=FIXED, analysis_commit=FIXED,
        native_collector_commit='6c744bf52daff3fc54571e264a0c34e3207aa1df',
        delivery_index_sha256=OLD_INDEX, authorization_sha256=AUTH_SHA,
        authorization_reference='USER-COE-CONTROLLED-C8F3DAD-20261023-01',
        program=None, run_config_sha256=None, build_receipt_sha256=None,
        automatic_retry=False, role='Engineering', formal_eligible=False,
        qualification='NOT_GRANTED', performance_comparability='NOT_ESTABLISHED')


def make_previous(path):
    (path / 'prepare').mkdir(parents=True)
    (path / 'prepare/receipt.json').write_text(json.dumps(old_receipt()), encoding='utf8')
    (path / 'prepare/checkout.process.json').write_text(json.dumps(dict(
        status='EXITED', exit_code=0, timed_out=False)), encoding='utf8')
    (path / 'prepare/checkout.stdout').write_bytes(b'old immutable evidence\r\n')


def test_continuation_requires_unbuilt_blocked_prepare_and_preserves_unknown(tmp_path):
    m = module()
    previous = tmp_path / 'old'
    make_previous(previous)
    names = ['scripts/gate8_qualification_token.cu']
    approved = json.loads(AUTH.read_text(encoding='utf8'))
    evidence = m.inspect_previous(previous, names, approved)
    assert evidence['receipt_sha256'] == hashlib.sha256((previous / 'prepare/receipt.json').read_bytes()).hexdigest()
    (previous / 'prepare/build').mkdir()
    with pytest.raises(ValueError, match='PREVIOUS_ALREADY_BUILT_OR_EXECUTED'):
        m.inspect_previous(previous, names, approved)
    (previous / 'prepare/build').rmdir()
    (previous / 'prepare/checkout.process.json').write_text(json.dumps(dict(
        status='BLOCKED', exit_code=1, timed_out=True,
        descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY')), encoding='utf8')
    with pytest.raises(ValueError, match='PREVIOUS_WRITER_NOT_CLOSED'):
        m.inspect_previous(previous, names, approved)


def test_continuation_rejects_wrong_authority_or_other_failure(tmp_path):
    m = module()
    previous = tmp_path / 'old'
    make_previous(previous)
    receipt = old_receipt()
    receipt['error'] = 'some different failure'
    (previous / 'prepare/receipt.json').write_text(json.dumps(receipt), encoding='utf8')
    with pytest.raises(ValueError, match='PREVIOUS_NOT_SOURCE_ONLY_FAILURE'):
        m.inspect_previous(previous, ['scripts/gate8_qualification_token.cu'],
            json.loads(AUTH.read_text(encoding='utf8')))


def test_no_staged_or_unrelated_modification_is_silently_repaired(tree, tmp_path):
    m = module()
    repo, commit = tree
    (repo / 'unrelated.txt').write_bytes(b'user change\n')
    with pytest.raises(ValueError, match='UNRELATED_WORKTREE_CHANGE'):
        m.materialize_sources('git', repo, commit,
            [row('source.cu', b'first\nsecond\n')], tmp_path / 'evidence')
    assert (repo / 'source.cu').read_bytes() == b'first\r\nsecond\r\n'


def test_staged_source_change_is_not_overwritten(tree, tmp_path):
    m = module()
    repo, commit = tree
    (repo / 'source.cu').write_bytes(b'intentional staged source\n')
    git(repo, 'add', 'source.cu')
    with pytest.raises(ValueError, match='STAGED_CHANGE'):
        m.materialize_sources('git', repo, commit,
            [row('source.cu', b'first\nsecond\n')], tmp_path / 'evidence')
    assert (repo / 'source.cu').read_bytes() == b'intentional staged source\n'


def package(tmp_path):
    m = module()
    if 'COE_REPAIR_TEST_PACKAGE' in os.environ:
        return Path(os.environ['COE_REPAIR_TEST_PACKAGE'])
    out = tmp_path / 'delivery'
    shutil.copytree(OLD, out / 'original')
    shutil.copyfile(AUTH, out / 'authorization.json')
    shutil.copyfile(ROOT / 'scripts/coe_controlled_deployment.py', out / 'coe_controlled_deployment.py')
    launcher = ROOT / 'scripts/run_coe_controlled_repair.ps1'
    assert launcher.is_file(), 'repaired PS5.1 entry is not implemented'
    shutil.copyfile(launcher, out / launcher.name)
    (out / 'authorization_compatibility.json').write_text(json.dumps(m.BRIDGE), encoding='utf8')
    (out / 'evidence').mkdir()
    shutil.copyfile(REPAIR1, out / 'evidence/repair1_once.zip')
    shutil.copyfile(GIT_STATE, out / 'evidence/git_state_once.zip')
    rows = [row(p.relative_to(out).as_posix(), p.read_bytes())
            for p in sorted(out.rglob('*')) if p.is_file()]
    (out / 'file_index.json').write_text(json.dumps(dict(
        schema_version='coe-controlled-repair-index/0.1.1', control_commit='a' * 40, files=rows)), encoding='utf8')
    return out


def test_real_package_uses_old_authority_without_rewriting_it(tmp_path):
    m = module()
    p = package(tmp_path)
    index = hashlib.sha256((p / 'file_index.json').read_bytes()).hexdigest()
    for action in ('prepare', 'execute'):
        legacy, cfg, approval, reference, control = m.verify_package(p, index, action)
        assert approval['delivery_index_sha256'] == OLD_INDEX
        assert cfg['sources'] == json.loads((OLD / 'delivery.json').read_text())['sources']
        assert (p / 'authorization.json').read_bytes() == AUTH.read_bytes()
    done = subprocess.run([sys.executable, '-I', '-S', '-B', str(p / 'coe_controlled_deployment.py'),
        'verify', '--index-sha256', index], capture_output=True, timeout=20)
    assert done.returncode == 0, done.stderr
    assert json.loads(done.stdout)['status'] == 'PACKAGE_VERIFIED_NO_TARGET_ACCESS'


@pytest.mark.parametrize('change,reason', [('authority','ORIGINAL_AUTHORIZATION_CHANGED'),
    ('bridge','AUTHORIZATION_COMPATIBILITY'), ('old_index','ORIGINAL_INDEX')])
def test_new_manifest_cannot_self_certify_changed_old_approval_or_scope(tmp_path, change, reason):
    m = module()
    original = package(tmp_path / 'seed')
    p = tmp_path / 'changed'
    shutil.copytree(original, p)
    name = {'authority':'authorization.json', 'bridge':'authorization_compatibility.json',
            'old_index':'original/file_index.json'}[change]
    value = json.loads((p / name).read_text(encoding='utf8'))
    value['permission_expansion'] = True
    (p / name).write_text(json.dumps(value), encoding='utf8')
    index = json.loads((p / 'file_index.json').read_text())
    index['files'] = [row(r['path'], (p / r['path']).read_bytes()) for r in index['files']]
    (p / 'file_index.json').write_text(json.dumps(index), encoding='utf8')
    with pytest.raises(ValueError, match=reason):
        m.verify_package(p, hashlib.sha256((p / 'file_index.json').read_bytes()).hexdigest(), 'prepare')


def full_target_double(tmp_path, monkeypatch, m):
    """Real Git checkout and source imports; only target paths/assets/build are doubles."""
    repo = tmp_path / 'target repo'
    repo.mkdir()
    git(repo, 'init', '-q')
    object_root = Path(git(ROOT, 'rev-parse', '--absolute-git-dir').decode().strip()) / 'objects'
    # Read-only Git alternates avoid an unnecessary MSYS upload-pack subprocess
    # which this local sandbox cannot start. HEAD/tree/blob checkout remains real.
    (repo / '.git/objects/info/alternates').write_bytes((object_root.as_posix() + '\n').encode('utf8'))
    git(repo, '-c', 'core.autocrlf=false', 'checkout', '-q', '--detach', FIXED)
    git(repo, 'config', 'core.autocrlf', 'true')
    # Match -I/-S repository selection; do not weaken the real module-origin gate.
    sys.path[:] = [p for p in sys.path if Path(p or Path.cwd()).resolve() != ROOT]
    for name in list(sys.modules):
        if any(name == p or name.startswith(p + '.') for p in ('analysis', 'exposedpath', 'exposedpath_v141')):
            monkeypatch.delitem(sys.modules, name)
    source = repo / 'scripts/gate8_qualification_token.cu'
    source.write_bytes(git(repo, 'show', FIXED + ':scripts/gate8_qualification_token.cu').replace(b'\n', b'\r\n'))
    old = tmp_path / 'old blocked attempt'
    with zipfile.ZipFile(REPAIR1) as z:
        prefix = 'prepare/previous_attempt_files/'
        for name in z.namelist():
            if name.startswith(prefix):
                dest = old / name[len(prefix):]
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(z.read(name))
        prior_repair = tmp_path / 'transfer/coe_controlled_c8f3dad_repair1'
        z.extractall(prior_repair)
    original = json.loads((OLD / 'delivery.json').read_text())
    relocated = {**original, 'code_root': str(repo), 'git': shutil.which('git'),
                 'output_root': str(old), 'transfer_root': str(tmp_path / 'transfer')}
    bound_verify = m.verify_package
    builds = []

    def verify(*args):
        legacy, cfg, approval, reference, control = bound_verify(*args)
        assert cfg == original  # real old contract/receipts are verified before relocation
        monkeypatch.setattr(legacy, 'check_assets', lambda c: None)  # target tool/library checks only
        real_load = legacy.load

        def fake_load(path, name):
            if Path(path).name != 'build_coe_cupti_controlled.py':
                return real_load(path, name)
            class CpuBuilder:
                @staticmethod
                def build(config, output):
                    assert config == original['build']
                    builds.append(output)
                    Path(output).mkdir()
                    dll = Path(output) / 'coe_controlled.dll'
                    dll.write_bytes(b'CPU_TARGET_BUILD_DOUBLE_NEVER_LOADED')
                    built = dict(program=dict(path=str(dll), bytes=dll.stat().st_size,
                        sha256=hashlib.sha256(dll.read_bytes()).hexdigest()),
                        collector_rebuilt=False, program_executed=False, CUDA_initialized=False,
                        local_unsupported_host_compiler=False, test_environment='CPU_BUILD_DOUBLE')
                    (Path(output) / 'build.json').write_text(json.dumps(built), encoding='utf8')
                    return built
            return CpuBuilder
        monkeypatch.setattr(legacy, 'load', fake_load)
        def forbidden_execute(*unused):
            raise AssertionError('NO_GPU_EXECUTION_ALLOWED_IN_CPU_TEST')
        monkeypatch.setattr(legacy, 'execute_worker', forbidden_execute)
        return legacy, relocated, approval, reference, control
    monkeypatch.setattr(m, 'verify_package', verify)
    monkeypatch.setattr(m, 'target_environment', lambda: None)  # local 3.12 vs target 3.11.16
    return repo, old, builds


def test_full_prepare_continues_at_current_c8_without_rollback_or_cuda(tmp_path, monkeypatch):
    m = module()
    p = package(tmp_path)
    index = hashlib.sha256((p / 'file_index.json').read_bytes()).hexdigest()
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    original_receipt = (old / 'prepare/receipt.json').read_bytes()
    assert m.run_stage(p, index, 'prepare') == 0
    out = tmp_path / 'transfer' / m.ATTEMPT / 'prepare'
    receipt = json.loads((out / 'receipt.json').read_text())
    assert receipt['status'] == 'PREPARED_NOT_EXECUTED' and len(builds) == 1
    assert git(repo, 'rev-parse', 'HEAD').decode().strip() == FIXED
    assert (old / 'prepare/receipt.json').read_bytes() == original_receipt
    assert (repo / 'scripts/gate8_qualification_token.cu').stat().st_size == 2465
    assert (out / 'source_repair/source_before/scripts/gate8_qualification_token.cu').stat().st_size == 2519
    assert not (out.parent / 'once').exists()
    config = json.loads((out / 'run_config.json').read_text())
    assert config['budget'] == dict(processes=1,sessions=1,models=0,nsight_profiles=0,hard_seconds=120)
    with pytest.raises(ValueError, match='NO_OVERWRITE_RESUME_RETRY'):
        m.run_stage(p, index, 'prepare')
    assert len(builds) == 1


def test_full_failure_records_new_blocked_zip_without_touching_old_attempt(tmp_path, monkeypatch):
    m = module()
    p = package(tmp_path)
    index = hashlib.sha256((p / 'file_index.json').read_bytes()).hexdigest()
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    original_receipt = (old / 'prepare/receipt.json').read_bytes()
    (repo / 'scripts/gate8_qualification_token.cu').write_bytes(b'unknown user edit\n')
    assert m.run_stage(p, index, 'prepare') == 2
    out = tmp_path / 'transfer' / m.ATTEMPT / 'prepare'
    receipt = json.loads((out / 'receipt.json').read_text())
    assert receipt['status'] == 'BLOCKED' and 'CONTENT_NOT_PROVEN_EOL' in receipt['error']
    assert len(builds) == 0 and (old / 'prepare/receipt.json').read_bytes() == original_receipt
    assert (out.parent.parent / (m.ATTEMPT + '_once.zip')).is_file()


def test_explicit_execute_rejects_changed_built_program_before_worker(tmp_path, monkeypatch):
    m = module()
    p = package(tmp_path)
    index = hashlib.sha256((p / 'file_index.json').read_bytes()).hexdigest()
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    assert m.run_stage(p, index, 'prepare') == 0
    new_root = tmp_path / 'transfer' / m.ATTEMPT
    (new_root / 'prepare/build/coe_controlled.dll').write_bytes(b'changed fake artifact')
    assert m.run_stage(p, index, 'execute') == 2
    receipt = json.loads((new_root / 'once/receipt.json').read_text())
    assert 'FILE_IDENTITY:program' in receipt['error']
    assert len(builds) == 1
    assert (new_root.parent / (m.ATTEMPT + '_once.zip')).is_file()
    with pytest.raises(ValueError, match='NO_OVERWRITE_RESUME_RETRY'):
        m.run_stage(p, index, 'execute')


def test_missing_required_previous_receipt_field_is_not_treated_as_none(tmp_path):
    m = module()
    previous = tmp_path / 'old'
    make_previous(previous)
    data = old_receipt()
    del data['program']
    (previous / 'prepare/receipt.json').write_text(json.dumps(data), encoding='utf8')
    with pytest.raises(ValueError, match='PREVIOUS_RECEIPT_BINDING'):
        m.inspect_previous(previous, ['scripts/gate8_qualification_token.cu'],
            json.loads(AUTH.read_text(encoding='utf8')))


def test_real_ps51_package_entry_rejects_wrong_index_before_target_access(tmp_path):
    p = package(tmp_path)
    shell = Path('C:/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
    env = {**os.environ, 'PSModulePath': str(shell.parent / 'Modules')}
    done = subprocess.run([str(shell), '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File',
        str(p / 'run_coe_controlled_repair.ps1'), '-DeliveryIndexSha256', '0' * 64],
        capture_output=True, timeout=15, env=env)
    assert done.returncode != 0 and b'Repair delivery index conflict' in done.stderr, done.stderr


def fixed_rows():
    return json.loads((OLD / 'delivery.json').read_text(encoding='utf8'))['sources']


def test_returned_snapshot_proves_status_is_not_a_content_diff():
    with zipfile.ZipFile(GIT_STATE) as z:
        receipt = json.loads(z.read('receipt.json'))
        assert len(receipt['sources']) == 13 and all(r['exact_match'] for r in receipt['sources'])
        assert z.read('diff.stdout') == z.read('staged.stdout') == b''
        assert z.read('status.stdout') == (b' M exposedpath/__init__.py\0'
            b' M exposedpath_v141/__init__.py\0 M scripts/gate8_qualification_token.cu\0')
        for name in ('status', 'diff', 'staged', 'eol', 'attributes', 'head'):
            assert json.loads(z.read(name + '.query.json'))['exit_code'] == 0


def replay_status_only(monkeypatch, m, repo, raw):
    real = subprocess.run
    def run(argv, *args, **kwargs):
        if str(repo) in list(map(str, argv)) and 'status' in argv:
            return SimpleNamespace(returncode=0, stdout=raw, stderr=b'')
        return real(argv, *args, **kwargs)
    monkeypatch.setattr(m.subprocess, 'run', run)


def test_sealed_stat_only_status_with_real_git_content_and_index_is_accepted(tmp_path, monkeypatch):
    m = module()
    assert callable(getattr(m, 'check_deployed_tree', None)), 'content-backed clean gate missing'
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    (repo / 'scripts/gate8_qualification_token.cu').write_bytes(
        git(repo, 'show', FIXED + ':scripts/gate8_qualification_token.cu'))
    with zipfile.ZipFile(GIT_STATE) as z:
        archived_status = z.read('status.stdout')
    replay_status_only(monkeypatch, m, repo, archived_status)
    before_entries = git(repo, 'ls-files', '--stage', '-z')
    report = m.check_deployed_tree(shutil.which('git'), repo, FIXED, fixed_rows(), tmp_path / 'check')
    assert report['content_clean'] is True and report['git_status_empty'] is False
    assert report['verified_status_only_paths'] == ['exposedpath/__init__.py',
        'exposedpath_v141/__init__.py', 'scripts/gate8_qualification_token.cu']
    assert (tmp_path / 'check/status.stdout').read_bytes() == archived_status
    # Git may refresh stat-cache metadata; staged blob IDs/modes must not change.
    assert git(repo, 'ls-files', '--stage', '-z') == before_entries


def test_stat_only_gate_does_not_accept_unknown_path_even_when_content_diff_is_empty(tmp_path, monkeypatch):
    m = module()
    assert callable(getattr(m, 'check_deployed_tree', None)), 'content-backed clean gate missing'
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    (repo / 'scripts/gate8_qualification_token.cu').write_bytes(
        git(repo, 'show', FIXED + ':scripts/gate8_qualification_token.cu'))
    replay_status_only(monkeypatch, m, repo, b' M unrelated.txt\0')
    with pytest.raises(ValueError, match='UNRELATED_WORKTREE_CHANGE'):
        m.check_deployed_tree(shutil.which('git'), repo, FIXED, fixed_rows(), tmp_path / 'check')
    assert (tmp_path / 'check/status.stdout').read_bytes() == b' M unrelated.txt\0'


def test_content_gate_rejects_real_modified_source_and_keeps_git_raw_evidence(tmp_path, monkeypatch):
    m = module()
    assert callable(getattr(m, 'check_deployed_tree', None)), 'content-backed clean gate missing'
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    (repo / 'scripts/gate8_qualification_token.cu').write_bytes(b'changed actual source\n')
    with pytest.raises(ValueError, match='CONTENT_IDENTITY'):
        m.check_deployed_tree(shutil.which('git'), repo, FIXED, fixed_rows(), tmp_path / 'check')
    assert (tmp_path / 'check/status.stdout').is_file()


def test_content_gate_rejects_real_staged_change(tmp_path, monkeypatch):
    m = module()
    assert callable(getattr(m, 'check_deployed_tree', None)), 'content-backed clean gate missing'
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    git(repo, 'update-index', '--chmod=+x', 'scripts/gate8_qualification_token.cu')
    with pytest.raises(ValueError, match='STAGED_CHANGE'):
        m.check_deployed_tree(shutil.which('git'), repo, FIXED, fixed_rows(), tmp_path / 'check')
    assert (tmp_path / 'check/staged.stdout').read_bytes()


def test_exact_repair1_failed_tree_is_accepted_but_any_change_is_rejected(tmp_path, monkeypatch):
    m = module()
    assert callable(getattr(m, 'inspect_repair1', None)), 'sealed failed-attempt continuation missing'
    repo, old, builds = full_target_double(tmp_path, monkeypatch, m)
    p = package(tmp_path)
    evidence = m.inspect_repair1(tmp_path / 'transfer', p, old)
    assert evidence['status'] == 'BLOCKED' and evidence['built_or_executed'] is False
    previous = tmp_path / 'transfer/coe_controlled_c8f3dad_repair1/prepare/receipt.json'
    previous.write_bytes(previous.read_bytes() + b' ')
    with pytest.raises(ValueError, match='REPAIR1_EVIDENCE_CHANGED'):
        m.inspect_repair1(tmp_path / 'transfer', p, old)
