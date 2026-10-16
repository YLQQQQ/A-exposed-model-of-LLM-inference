"""Read-only storage binding regression; no scan, permissions, model or CUDA.

Real sealed archives/current file bytes are used. Only target Git state and
Python 3.11.16 are CPU boundary doubles (local Python is not target Python).
"""
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace, ModuleType
import zipfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
COMMIT = '4f1c3b55caf33cd669aeee05e95be98c96ef0e11'
STATIC = ROOT / '.local/transfer/coe_4f1c3b55caf3_static.zip'
RETURN = ROOT / '.local/transfer/coe_storage_once_20261016T062302Z_3c389ee5c2154154a29334199d92f7d9.zip'
PATHS = ('analysis/coe_candidate.py', 'analysis/coe_helper_identity.py',
         'scripts/run_coe_candidate_pilot.ps1')
LAUNCHER_SHA = '99ba960b7cc5f59d8c64ff1cbfba5d353c46f9cbb2d3240b9e66dcfcf28d6b47'


def binding_module():
    # RED replay is the actual, sealed failed program, not a reimplementation.
    if os.environ.get('COE_BINDING_RED_REPLAY') == '1':
        assert hashlib.sha256(RETURN.read_bytes()).hexdigest() == '88e527a15d6a970a448b1c438349891c83e56d0b8ea8949468482aab2f519409'
        with zipfile.ZipFile(RETURN) as z:
            code = z.read('query_source.py')
        m = ModuleType('sealed_failed_binding_not_main')
        exec(compile(code, 'sealed_query_source.py', 'exec'), m.__dict__)
        return m
    return importlib.import_module('scripts.coe_storage_binding')


@pytest.fixture
def actual_reference(tmp_path, monkeypatch):
    if not STATIC.is_file():
        pytest.skip('local sealed static ZIP required; not a target-platform check')
    assert STATIC.stat().st_size == 85783
    assert hashlib.sha256(STATIC.read_bytes()).hexdigest() == 'b062b9502e2796cdbd91b47a1d0de17c549062036cc361948a9d6d131e8e13bc'
    with zipfile.ZipFile(STATIC) as z:
        assert z.testzip() is None
        receipt = z.read('receipt.json')
        source = json.loads(z.read('source_bytes.json'))
        launcher = z.read('executed.ps1')
    root = tmp_path / 'YLQ'
    code = root / 'checkout'
    for path in PATHS:
        # Fixed Git blobs, NOT bytes or hashes invented from the current fixture.
        data = subprocess.run(['git', 'show', f'{COMMIT}:{path}'], cwd=ROOT,
                              check=True, capture_output=True).stdout
        file = code / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_bytes(data)
    old = root / 'logs/coe_4f1c3b55caf3_static/receipt.json'
    old.parent.mkdir(parents=True)
    old.write_bytes(receipt)
    m = binding_module()

    def target_git(argv, **kw):
        assert argv[:3] == ['git', '-C', str(code)]
        assert kw == dict(capture_output=True, timeout=20)
        tail = argv[3:]
        if tail == ['rev-parse', 'HEAD']:
            output = (COMMIT + '\n').encode()
        elif tail == ['status', '--porcelain']:
            output = b''
        else:
            raise AssertionError('Unexpected command: ' + repr(argv))
        return SimpleNamespace(returncode=0, stdout=output, stderr=b'')

    # Exact explicit OS boundary doubles only; archive/file hashing is real.
    monkeypatch.setattr(m.subprocess, 'run', target_git)
    monkeypatch.setattr(m.sys, 'version_info', (3, 11, 16))
    return SimpleNamespace(m=m, root=root, code=code, old=old, source=source, launcher=launcher)


def test_real_sealed_zip_to_current_bytes_full_binding(actual_reference):
    f = actual_reference
    result = f.m.bind(f.root, f.code, STATIC)
    assert result['status'] == 'MATCH'
    with zipfile.ZipFile(STATIC) as z:
        assert f.old.read_bytes() == z.read('receipt.json')
    assert result['original_receipt_sha256'] == '988de2ec87d9c427e2a5c76a6d33b3f2ea798f2adc88f6e752977570c12bc0b5'
    items = result['current_selected_sources']
    assert [v['path'] for v in items] == list(PATHS)
    assert [v['basis'] for v in items] == ['SOURCE_BYTES_JSON', 'SOURCE_BYTES_JSON', 'STATIC_ZIP_EXECUTED_PS1']
    assert items[2]['sha256'] == items[2]['expected_sha256'] == LAUNCHER_SHA
    assert items[2]['bytes'] == items[2]['expected_bytes'] == 11714
    assert result['collection_authorized'] is False


@pytest.mark.parametrize('path', PATHS)
@pytest.mark.parametrize('damage', ['missing', 'tamper'])
def test_current_files_missing_or_changed_reject_with_actual_details(actual_reference, path, damage):
    f = actual_reference
    file = f.code / path
    if damage == 'missing':
        file.unlink()
    else:
        file.write_bytes(file.read_bytes() + b'\n# tampered\n')
    reason = ('CURRENT_SOURCE_MISSING:' if damage == 'missing' else 'CURRENT_SOURCE_CONFLICT:') + path
    with pytest.raises(ValueError) as error:
        f.m.bind(f.root, f.code, STATIC)
    assert str(error.value) == reason
    assert error.value.details['path'] == path
    assert error.value.details['expected_sha256']
    if damage == 'missing':
        assert error.value.details['actual_sha256'] is None
    else:
        assert error.value.details['actual_sha256'] == hashlib.sha256(file.read_bytes()).hexdigest()
        assert error.value.details['actual_bytes'] == file.stat().st_size


@pytest.mark.parametrize('damage', ['missing', 'tamper'])
def test_original_receipt_is_bound_not_just_reparsed(actual_reference, damage):
    f = actual_reference
    if damage == 'missing':
        f.old.unlink()
    else:
        f.old.write_bytes(f.old.read_bytes() + b'\n')
    with pytest.raises(ValueError) as error:
        f.m.bind(f.root, f.code, STATIC)
    assert str(error.value) == ('OLD_RECEIPT_MISSING' if damage == 'missing' else 'OLD_RECEIPT_CHANGED')


@pytest.mark.parametrize('damage,reason', [
    ('missing', 'SOURCE_RECORD_MISSING:analysis/coe_candidate.py'),
    ('duplicate', 'SOURCE_RECORD_DUPLICATE:analysis/coe_candidate.py'),
    ('unmatched', 'SOURCE_RECORD_NOT_VERIFIED:analysis/coe_candidate.py'),
    ('launcher_missing', 'LAUNCHER_REFERENCE_MISSING'),
    ('launcher_tamper', 'LAUNCHER_REFERENCE_CONFLICT'),
])
def test_reference_selection_rejects_exact_reason_not_upstream_hash_failure(actual_reference, damage, reason):
    # Selection-layer negatives derived from genuine archive metadata. Altered
    # metadata is NOT presented as a sealed ZIP that passed its outer hash gate.
    f = actual_reference
    source = copy.deepcopy(f.source)
    launcher = f.launcher
    row = next(r for r in source if r['path'] == PATHS[0])
    if damage == 'missing':
        source.remove(row)
    elif damage == 'duplicate':
        source.append(copy.deepcopy(row))
    elif damage == 'unmatched':
        row['matched'] = False
    elif damage == 'launcher_missing':
        launcher = None
    else:
        launcher += b'\n'
    with pytest.raises(ValueError) as error:
        f.m.select_references(source, launcher)
    assert str(error.value) == reason


@pytest.mark.parametrize('kind', ['missing', 'duplicate'])
def test_archive_member_ambiguity_has_explicit_reason(actual_reference, kind):
    f = actual_reference
    with zipfile.ZipFile(STATIC) as z:
        names = z.namelist()
    if kind == 'missing':
        names.remove('executed.ps1')
    else:
        names.append('executed.ps1')
    with pytest.raises(ValueError) as error:
        f.m.require_member(names, 'executed.ps1')
    assert str(error.value) == 'ARCHIVE_MEMBER_' + kind.upper() + ':executed.ps1'


def test_wrong_archive_cannot_certify_modified_reference(actual_reference, tmp_path):
    f = actual_reference
    archive = tmp_path / 'changed.zip'
    archive.write_bytes(STATIC.read_bytes() + b'not sealed')
    with pytest.raises(ValueError) as error:
        f.m.bind(f.root, f.code, archive)
    assert str(error.value) == 'ORIGINAL_ARCHIVE_IDENTITY'


@pytest.mark.parametrize('condition,reason', [
    ('git_head', 'CURRENT_CHECKOUT_CONFLICT'), ('dirty', 'CURRENT_CHECKOUT_CONFLICT'),
    ('python', 'TARGET_PYTHON_VERSION_CONFLICT'),
])
def test_target_environment_is_not_silently_certified(actual_reference, monkeypatch, condition, reason):
    f = actual_reference
    if condition == 'python':
        monkeypatch.setattr(f.m.sys, 'version_info', (3, 12, 7))
    else:
        def conflict(argv, **kw):
            if argv[3:] == ['rev-parse', 'HEAD']:
                output = (('0' * 40 if condition == 'git_head' else COMMIT) + '\n').encode()
            else:
                output = b' M changed.py\n' if condition == 'dirty' else b''
            return SimpleNamespace(returncode=0, stdout=output, stderr=b'')
        monkeypatch.setattr(f.m.subprocess, 'run', conflict)
    with pytest.raises(ValueError) as error:
        f.m.bind(f.root, f.code, STATIC)
    assert str(error.value) == reason
