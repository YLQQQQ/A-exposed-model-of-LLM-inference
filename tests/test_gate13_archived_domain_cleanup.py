"""Small real PowerShell/ZIP fixtures only; never touch research evidence."""
import csv
import hashlib
import json
import shutil
import stat
import subprocess
import zipfile
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts/gate13_archived_domain_cleanup.ps1'
PS = shutil.which('powershell.exe')
pytestmark = pytest.mark.skipif(PS is None, reason='PowerShell 5.1 adapter test')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def fixture(tmp_path):
    root = tmp_path / 'formal-99f3bae966f2-20261010-sixblock'
    inventory = tmp_path / 'inventory'
    inventory.mkdir()
    (inventory / 'errors.json').write_text(json.dumps([
        {'path': str(tmp_path / 'other' / 'unreadable.json'), 'error': 'Access denied'},
        {'path': str(tmp_path / 'other' / 'cache'), 'error': 'Reparse skipped'},
    ]), encoding='utf8')
    rows = []
    for block in range(1, 7):
        for condition in ['G32', 'G512', 'N0', 'Nm', 'N16']:
            rel = f'batch/{root.name}-b{block}-{condition}-pass1/collection/analyzed/domain.json'
            path = root / rel
            path.parent.mkdir(parents=True)
            path.write_bytes(b'abc')
            rows.append(dict(server_relative_path=rel, server_absolute_path=str(path), bytes=3,
                             sha256='ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
                             archive_member='source/' + rel, classification='EXACT_ARCHIVED_DERIVED_COPY'))
    # This protected original is deliberately outside the deletion list.
    (root / 'receipt.json').write_bytes(b'BLOCKED UNKNOWN')
    plan = tmp_path / 'candidates.csv'
    with plan.open('w', encoding='utf8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
        w.writeheader()
        w.writerows(rows)
    entries = [{'path': r['archive_member'], 'length': 3, 'sha256': r['sha256']} for r in rows]
    manifest = json.dumps(dict(version='gate13-forensic-byte-copy/0.1', entries=entries)).encode()
    archive = tmp_path / 'sealed.zip'
    with zipfile.ZipFile(archive, 'w') as z:
        z.writestr('forensic_manifest.json', manifest)
        for r in rows:
            z.writestr(r['archive_member'], b'abc')
    receipt = tmp_path / 'forensic_receipt.json'
    receipt.write_text(json.dumps(dict(status='FORENSIC_BYTE_COPY_VERIFIED_NOT_ACCEPTANCE', error=None,
        archive=str(archive), source=str(root), archive_sha256=sha(archive.read_bytes()),
        archive_length=archive.stat().st_size, manifest_sha256=sha(manifest),
        historical_descendant_exit_status='UNKNOWN_STOP_AND_INSPECT_NO_RETRY',
        absence_of_writers_proven=False)), encoding='utf8')
    args = {'SourceRoot': root, 'Archive': archive, 'CandidateCsv': plan,
            'ForensicReceipt': receipt, 'InventoryRoot': inventory, 'ReceiptDirectory': tmp_path / 'cleanup',
            'ArchiveSHA256': sha(archive.read_bytes()), 'ManifestSHA256': sha(manifest),
            'CandidatesSHA256': sha(plan.read_bytes()), 'ForensicReceiptSHA256': sha(receipt.read_bytes())}
    return root, rows, args


def run(args, apply=True):
    command = [PS, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(SCRIPT)]
    for k, v in args.items():
        command += ['-' + k, str(v)]
    if apply:
        command += ['-Apply', '-NoActiveAnalysisConfirmed']
    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=35)


def audit(args):
    return json.loads((args['ReceiptDirectory'] / 'cleanup_receipt.json').read_text(encoding='utf-8-sig'))


def test_archive_bound_closed_list_deletes_only_30_named_files(tmp_path):
    root, rows, args = fixture(tmp_path)
    result = run(args)
    assert result.returncode == 0, result.stderr
    assert all(not (root / r['server_relative_path']).exists() for r in rows)
    assert (root / 'receipt.json').read_bytes() == b'BLOCKED UNKNOWN'
    assert args['Archive'].is_file()
    report = audit(args)
    assert report['status'] == 'CLEANED_ARCHIVED_DERIVED_COPIES'
    assert report['deleted_bytes'] == 90
    assert report['deleted_count'] == 30
    assert report['absence_of_all_writers_proven'] is False


@pytest.mark.parametrize('fault', ['last_hash', 'last_missing', 'duplicate', 'escape', 'zip', 'receipt', 'issues_missing', 'issue_path_unknown'])
def test_any_precheck_fault_prevents_first_delete(tmp_path, fault):
    root, rows, args = fixture(tmp_path)
    last = root / rows[-1]['server_relative_path']
    if fault == 'last_hash':
        last.write_bytes(b'xyz')
    elif fault == 'last_missing':
        last.unlink()
    elif fault in ['duplicate', 'escape']:
        rows[-1] = dict(rows[0]) if fault == 'duplicate' else dict(rows[-1], server_absolute_path=str(tmp_path / 'outside.json'))
        with args['CandidateCsv'].open('w', encoding='utf8', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), lineterminator='\n')
            w.writeheader(); w.writerows(rows)
        args['CandidatesSHA256'] = sha(args['CandidateCsv'].read_bytes())
    elif fault == 'zip':
        with args['Archive'].open('ab') as f:
            f.write(b'changed')
    elif fault == 'receipt':
        value = json.loads(args['ForensicReceipt'].read_text())
        value['source'] = str(tmp_path / 'other-source')
        args['ForensicReceipt'].write_text(json.dumps(value))
        args['ForensicReceiptSHA256'] = sha(args['ForensicReceipt'].read_bytes())
    elif fault == 'issues_missing':
        (args['InventoryRoot'] / 'errors.json').unlink()
    else:
        (args['InventoryRoot'] / 'errors.json').write_text('[{"error":"Unknown path"},{"path":"relative","error":"Bad"}]')
    result = run(args)
    assert result.returncode != 0
    assert (root / rows[0]['server_relative_path']).is_file()
    assert audit(args)['deleted_count'] == 0
    assert audit(args)['status'] == 'STOPPED'
    expected = {'last_hash': 'TARGET_BYTES_CHANGED', 'last_missing': 'TARGET_MISSING',
                'duplicate': 'DUPLICATE_TARGET', 'escape': 'TARGET_PATH_CONFLICT',
                'zip': 'FORENSIC_RECEIPT_ARCHIVE_BINDING', 'receipt': 'FORENSIC_RECEIPT_PATH_BINDING',
                'issues_missing': 'INVENTORY_TWO_ISSUES_NOT_IDENTIFIED',
                'issue_path_unknown': 'INVENTORY_ISSUE_SCOPE_UNKNOWN'}
    assert expected[fault] in audit(args)['error']


def test_default_is_precheck_only_and_retains_all_files(tmp_path):
    root, rows, args = fixture(tmp_path)
    result = run(args, apply=False)
    assert result.returncode == 0, result.stderr
    assert all((root / r['server_relative_path']).exists() for r in rows)
    assert audit(args)['status'] == 'PRECHECK_PASS_NO_DELETION'


def test_held_writer_blocks_precheck_without_pid_queries(tmp_path):
    root, rows, args = fixture(tmp_path)
    # A real exclusive Windows file handle, not a source-code string check.
    import ctypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateFileW.restype = ctypes.c_void_p
    handle = kernel.CreateFileW(str(root / rows[-1]['server_relative_path']), 0x40000000, 0, None, 3, 0, None)
    assert handle not in (None, ctypes.c_void_p(-1).value)
    try:
        result = run(args)
        assert result.returncode != 0
        assert audit(args)['deleted_count'] == 0
    finally:
        kernel.CloseHandle(ctypes.c_void_p(handle))


def test_delete_failure_records_deleted_and_all_not_deleted_without_retry(tmp_path):
    root, rows, args = fixture(tmp_path)
    second = root / rows[1]['server_relative_path']
    second.chmod(stat.S_IREAD)
    try:
        result = run(args)
        assert result.returncode != 0
        report = audit(args)
        assert report['deleted_count'] == 1
        assert report['deleted_bytes'] == 3
        assert report['remaining_count'] == 29
        assert len(report['not_deleted_paths']) == 29
        assert not (root / rows[0]['server_relative_path']).exists()
        assert second.is_file()
    finally:
        second.chmod(stat.S_IWRITE | stat.S_IREAD)


def test_precheck_failure_receipt_still_lists_all_30_targets(tmp_path):
    root, rows, args = fixture(tmp_path)
    (root / rows[0]['server_relative_path']).write_bytes(b'xyz')
    assert run(args).returncode != 0
    assert len(audit(args)['not_deleted_paths']) == 30


def test_reparse_ancestor_is_rejected_without_following_it_for_deletion(tmp_path):
    root, rows, args = fixture(tmp_path)
    parent = (root / rows[-1]['server_relative_path']).parent
    real = parent.with_name('real')
    parent.rename(real)
    made = subprocess.run([PS, '-NoProfile', '-Command',
        f"New-Item -ItemType Junction -Path '{parent}' -Target '{real}' | Out-Null"],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    assert made.returncode == 0, made.stderr
    try:
        assert run(args).returncode != 0
        assert 'CLEANUP_REPARSE' in audit(args)['error']
        assert (real / 'domain.json').read_bytes() == b'abc'
        assert audit(args)['deleted_count'] == 0
    finally:
        # Remove only the test junction itself, not its target directory.
        parent.rmdir()


def test_inventory_ancestor_error_resolves_only_directly_checked_targets(tmp_path):
    root, rows, args = fixture(tmp_path)
    (args['InventoryRoot'] / 'errors.json').write_text(json.dumps([
        {'path': str(root), 'error': 'Earlier inventory access failure'},
        {'path': str(tmp_path / 'other'), 'error': 'Unrelated cache skipped'},
    ]), encoding='utf8')
    result = run(args, apply=False)
    assert result.returncode == 0, result.stderr
    issues = audit(args)['inventory_issues']
    assert len(issues[0]['candidate_matches']) == 30
    assert issues[0]['disposition'] == 'ONLY_NAMED_TARGETS_RESOLVED_BY_DIRECT_LOCKED_BYTE_CHECK'
    assert issues[1]['disposition'] == 'OUTSIDE_TARGET_SCOPE_NOT_CHANGED'
    assert audit(args)['absence_of_all_writers_proven'] is False
