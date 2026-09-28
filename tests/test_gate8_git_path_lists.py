"""CPU-only regressions at the real seal entry; no model or CUDA calls."""
import json
import subprocess
import sys

import pytest

from exposedpath import platform_adapter as adapter
from test_gate8_isolated_preflight import case


def query_double(monkeypatch, tracked, *, ignored=b'', stderr=b'', exit_code=0):
    def run(name, args, **kwargs):
        assert name == adapter.TOOL_GIT and 'ls-files' in args and '-z' in args
        assert kwargs['text'] is False
        output = tracked if '--cached' in args else ignored
        return subprocess.CompletedProcess([name, *args], exit_code, output, stderr)
    monkeypatch.setattr(adapter, 'run_tool', run)


def fresh_seal(tmp_path, m, args):
    output = tmp_path / 'fresh-query'
    output.mkdir()
    return output, lambda: m.seal(args['prepared'], output, args['root'])


@pytest.mark.parametrize('raw', [
    None, 'code.py\0', b'', b'code.py', b'\xff\0', b'code.py\0code.py\0',
    b'code.py\0\0', b'../outside\0', b'/absolute\0', b'C:relative\0',
    b'C:/absolute\0', b'\\server\\share\0', b'folder/../code.py\0',
    b'./code.py\0', b'folder//code.py\0', b'code.py/\0',
])
def test_seal_rejects_invalid_tracked_stream_instead_of_empty_set(tmp_path, monkeypatch, raw):
    m, args = case(tmp_path, monkeypatch)
    query_double(monkeypatch, raw)
    output, seal = fresh_seal(tmp_path, m, args)
    with pytest.raises(ValueError, match='GIT_PATH'):
        seal()
    assert not (output / 'auxiliary_preflight.json').exists()


@pytest.mark.parametrize('raw', [None, b'cache/', b'cache/\0cache/\0', b'../\0', b'\xff\0'])
def test_invalid_ignored_stream_cannot_exclude_unknown_content(tmp_path, monkeypatch, raw):
    m, args = case(tmp_path, monkeypatch)
    query_double(monkeypatch, b'code.py\0', ignored=raw)
    output, seal = fresh_seal(tmp_path, m, args)
    with pytest.raises(ValueError, match='GIT_PATH'):
        seal()
    assert not (output / 'auxiliary_preflight.json').exists()


def test_seal_preserves_binary_stderr_and_utf8_nul_names(tmp_path, monkeypatch):
    m, args = case(tmp_path, monkeypatch)
    name = '\u5b9e\u9a8c\u534f\u8bae.py'
    (args['root'] / name).write_text('pass\n', encoding='utf-8')
    raw = ('code.py\0' + name + '\0').encode('utf-8')
    query_double(monkeypatch, raw, stderr=b'\xff\xae')
    output, seal = fresh_seal(tmp_path, m, args)
    value = json.loads(seal().read_text())
    assert set(value['tree_hashes']) == {'code.py', name}
    assert (output / 'git_tracked_paths.stdout.bin').read_bytes() == raw
    assert (output / 'git_tracked_paths.stderr.bin').read_bytes() == b'\xff\xae'
    assert json.loads((output / 'git_tracked_paths.json').read_text())['status'] == 'PASS'


def test_missing_tracked_file_is_rejected_by_real_seal(tmp_path, monkeypatch):
    m, args = case(tmp_path, monkeypatch)
    query_double(monkeypatch, b'code.py\0missing.py\0')
    output, seal = fresh_seal(tmp_path, m, args)
    with pytest.raises(ValueError, match='TRACKED_CONTENT_NOT_SEALED'):
        seal()
    assert not (output / 'auxiliary_preflight.json').exists()


def test_nonzero_query_preserves_bytes_and_blocks(tmp_path, monkeypatch):
    m, args = case(tmp_path, monkeypatch)
    query_double(monkeypatch, b'code.py\0', stderr=b'\xfffailure', exit_code=7)
    output, seal = fresh_seal(tmp_path, m, args)
    with pytest.raises(ValueError, match='GIT_PATH'):
        seal()
    report = json.loads((output / 'git_ignored_paths.json').read_text())
    assert report['exit_code'] == 7 and report['status'] == 'BLOCKED'
    assert (output / 'git_ignored_paths.stderr.bin').read_bytes() == b'\xfffailure'
    assert not (output / 'auxiliary_preflight.json').exists()


def test_subprocess_read_failure_cannot_create_receipt(tmp_path, monkeypatch):
    m, args = case(tmp_path, monkeypatch)
    def failed(*a, **kw):
        raise OSError('independent pipe read failure')
    monkeypatch.setattr(adapter, 'run_tool', failed)
    output, seal = fresh_seal(tmp_path, m, args)
    with pytest.raises(OSError, match='independent pipe read failure'):
        seal()
    assert not (output / 'auxiliary_preflight.json').exists()
    report = json.loads((output / 'git_ignored_paths.json').read_text())
    assert report['error_type'] == 'OSError' and report['status'] == 'BLOCKED'


def test_actual_child_binary_pipe_reaches_seal_without_locale_decode(tmp_path, monkeypatch):
    real_run = adapter.run_tool
    m, args = case(tmp_path, monkeypatch)
    name = '\u5b9e\u9a8c\u534f\u8bae.py'
    (args['root'] / name).write_text('pass\n', encoding='utf-8')
    # Real CPU pipe, with bytes that would fail a GBK text reader.
    def child(name_arg, argv, **kwargs):
        payload = ('code.py\0' + name + '\0').encode() if '--cached' in argv else b''
        return real_run(sys._base_executable, ['-I', '-S', '-c',
            'import sys;sys.stdout.buffer.write(bytes.fromhex(sys.argv[1]));sys.stderr.buffer.write(bytes([255]))',
            payload.hex()], **kwargs)
    monkeypatch.setattr(adapter, 'run_tool', child)
    output, seal = fresh_seal(tmp_path, m, args)
    assert name in json.loads(seal().read_text())['tree_hashes']
    assert (output / 'git_tracked_paths.stderr.bin').read_bytes() == b'\xff'
