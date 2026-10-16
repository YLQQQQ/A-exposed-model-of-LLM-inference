"""Binding-only repair for the retired COE storage supplement.

No CLI, traversal, permission query, deployment or collection. References come
from the pinned, sealed static report, never from current runtime hashes. This
does not change the production launcher's storage policy or grant acceptance.
"""
import csv
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import sys
import zipfile

VERSION = 'coe-storage-binding/0.2.0'
EXPECTED_COMMIT = '4f1c3b55caf33cd669aeee05e95be98c96ef0e11'
ARCHIVE_SHA = 'b062b9502e2796cdbd91b47a1d0de17c549062036cc361948a9d6d131e8e13bc'
MANIFEST_SHA = 'd2e11bfb636eae91be0ba754a019b1ae6571c8c7316a6617122fdd3bcb1e66c0'
RECEIPT_SHA = '988de2ec87d9c427e2a5c76a6d33b3f2ea798f2adc88f6e752977570c12bc0b5'
LAUNCHER_SHA = '99ba960b7cc5f59d8c64ff1cbfba5d353c46f9cbb2d3240b9e66dcfcf28d6b47'
PYTHON_PATHS = ('analysis/coe_candidate.py', 'analysis/coe_helper_identity.py')
LAUNCHER_PATH = 'scripts/run_coe_candidate_pilot.ps1'


class BindingError(ValueError):
    def __init__(self, reason, **details):
        super().__init__(reason)
        self.details = details


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require_member(names, path):
    count = names.count(path)
    if count != 1:
        raise BindingError('ARCHIVE_MEMBER_' + ('MISSING:' if count == 0 else 'DUPLICATE:') + path)


def _read_file(path, missing_reason):
    path = Path(path)
    try:
        # Check the path and all existing ancestors without following reparse.
        for item in (path, *path.parents):
            value = os.stat(item, follow_symlinks=False)
            if stat.S_ISLNK(value.st_mode) or getattr(value, 'st_file_attributes', 0) & 0x400:
                raise BindingError('REPARSE_PATH', path=str(item))
        if not path.is_file():
            raise BindingError('NOT_REGULAR_FILE', path=str(path))
        return path.read_bytes()
    except FileNotFoundError as exc:
        raise BindingError(missing_reason, path=str(path)) from exc
    except OSError as exc:
        raise BindingError('FILE_READ_FAILED', path=str(path), type=type(exc).__name__,
                           errno=exc.errno, winerror=getattr(exc, 'winerror', None)) from exc


def select_references(source, launcher):
    """Validate references AFTER sealed archive verification by bind()."""
    if not isinstance(source, list) or any(not isinstance(r, dict) or not isinstance(r.get('path'), str) for r in source):
        raise BindingError('SOURCE_RECORD_SCHEMA')
    result = []
    for path in PYTHON_PATHS:
        matches = [r for r in source if r['path'] == path]
        if len(matches) != 1:
            raise BindingError(('SOURCE_RECORD_MISSING:' if not matches else 'SOURCE_RECORD_DUPLICATE:') + path)
        row = matches[0]
        if row.get('matched') is not True:
            raise BindingError('SOURCE_RECORD_NOT_VERIFIED:' + path)
        if type(row.get('actual_bytes')) is not int or row['actual_bytes'] < 0 or not isinstance(row.get('actual_sha256'), str) or len(row['actual_sha256']) != 64:
            raise BindingError('SOURCE_RECORD_SCHEMA:' + path)
        result.append(dict(path=path, basis='SOURCE_BYTES_JSON', expected_bytes=row['actual_bytes'],
                           expected_sha256=row['actual_sha256']))
    if launcher is None:
        raise BindingError('LAUNCHER_REFERENCE_MISSING')
    if len(launcher) != 11714 or sha(launcher) != LAUNCHER_SHA:
        raise BindingError('LAUNCHER_REFERENCE_CONFLICT', expected_sha256=LAUNCHER_SHA,
                           actual_sha256=sha(launcher), expected_bytes=11714, actual_bytes=len(launcher))
    result.append(dict(path=LAUNCHER_PATH, basis='STATIC_ZIP_EXECUTED_PS1',
                       expected_bytes=11714, expected_sha256=LAUNCHER_SHA))
    return result


def _static_reference(archive):
    data = _read_file(archive, 'ORIGINAL_ARCHIVE_MISSING')
    if len(data) != 85783 or sha(data) != ARCHIVE_SHA:
        raise BindingError('ORIGINAL_ARCHIVE_IDENTITY', expected_sha256=ARCHIVE_SHA,
                           actual_sha256=sha(data), expected_bytes=85783, actual_bytes=len(data))
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = z.namelist()
        for name in ('artifact_sha256.csv', 'receipt.json', 'source_bytes.json', 'executed.ps1'):
            require_member(names, name)
        if len(names) != len(set(names)) or len(names) != 20 or z.testzip() is not None:
            raise BindingError('ARCHIVE_CRC_MEMBERS')
        for name in names:
            p = PurePosixPath(name)
            if p.is_absolute() or '..' in p.parts or ':' in name or '\\' in name:
                raise BindingError('ARCHIVE_PATH', path=name)
        manifest = z.read('artifact_sha256.csv')
        if sha(manifest) != MANIFEST_SHA:
            raise BindingError('MANIFEST_IDENTITY')
        rows = list(csv.DictReader(io.StringIO(manifest.decode('utf-8-sig'))))
        if len(rows) != 19 or len({r['path'] for r in rows}) != 19 or {r['path'] for r in rows} | {'artifact_sha256.csv'} != set(names):
            raise BindingError('MANIFEST_COVERAGE')
        for row in rows:
            value = z.read(row['path'])
            if len(value) != int(row['bytes']) or sha(value) != row['sha256']:
                raise BindingError('MANIFEST_HASH:' + row['path'])
        receipt_bytes = z.read('receipt.json')
        if sha(receipt_bytes) != RECEIPT_SHA:
            raise BindingError('ORIGINAL_RECEIPT_IDENTITY')
        receipt = json.loads(receipt_bytes.decode('utf-8-sig'))
        if receipt.get('execution_commit') != EXPECTED_COMMIT or receipt.get('status') != 'BLOCKED' or receipt.get('error') != 'storage failed; no retry; exit=1':
            raise BindingError('ORIGINAL_RECEIPT')
        return select_references(json.loads(z.read('source_bytes.json').decode('utf-8-sig')), z.read('executed.ps1'))


def bind(root, code, archive):
    """Verify the original reference AND current files/checkout independently."""
    root, code = Path(root), Path(code)
    references = _static_reference(archive)
    current = []
    for item in references:
        path = item['path']
        try:
            data = _read_file(code / path, 'CURRENT_SOURCE_MISSING:' + path)
        except BindingError as exc:
            exc.details.update(path=path, expected_sha256=item['expected_sha256'],
                               expected_bytes=item['expected_bytes'], actual_sha256=None, actual_bytes=None)
            raise
        observed = dict(item, bytes=len(data), sha256=sha(data))
        if observed['bytes'] != item['expected_bytes'] or observed['sha256'] != item['expected_sha256']:
            raise BindingError('CURRENT_SOURCE_CONFLICT:' + path, path=path,
                               expected_sha256=item['expected_sha256'], actual_sha256=observed['sha256'],
                               expected_bytes=item['expected_bytes'], actual_bytes=observed['bytes'])
        current.append(observed)
    old = _read_file(root / 'logs/coe_4f1c3b55caf3_static/receipt.json', 'OLD_RECEIPT_MISSING')
    if sha(old) != RECEIPT_SHA:
        raise BindingError('OLD_RECEIPT_CHANGED', expected_sha256=RECEIPT_SHA,
                           actual_sha256=sha(old), expected_bytes=660, actual_bytes=len(old))
    git = []
    for args in (['rev-parse', 'HEAD'], ['status', '--porcelain']):
        value = subprocess.run(['git', '-C', str(code), *args], capture_output=True, timeout=20)
        git.append(dict(argv=args, exit_code=value.returncode, stdout=value.stdout.decode('utf8', 'strict'),
                        stderr=value.stderr.decode('utf8', 'strict')))
    if any(v['exit_code'] for v in git) or git[0]['stdout'].strip() != EXPECTED_COMMIT or git[1]['stdout'].strip():
        raise BindingError('CURRENT_CHECKOUT_CONFLICT', git=git)
    if sys.version_info[:3] != (3, 11, 16):
        raise BindingError('TARGET_PYTHON_VERSION_CONFLICT', actual=list(sys.version_info[:3]))
    return dict(schema_version=VERSION, status='MATCH', archive_sha256=ARCHIVE_SHA, manifest_sha256=MANIFEST_SHA,
                original_receipt_sha256=RECEIPT_SHA, execution_commit=EXPECTED_COMMIT, git=git,
                current_selected_sources=current, original_311_sources_reused_not_rehashed=True,
                cpu_110_compile_helper_receipts_reused_not_rerun=True, collection_authorized=False,
                original_status_changed=False)
