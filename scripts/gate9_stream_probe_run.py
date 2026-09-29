"""CPU supervisor: fixed direct interpreter, binary identity, hard timeout, one ZIP."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parents[1]
BOOT = ('import sys;sys.path[:0]=sys.argv[1:3];del sys.argv[1:3];'
        'from scripts.gate9_stream_probe import main;'
        'raise SystemExit(main(sys.argv[1:]+["--expected-pid",sys.stdin.readline().strip()]))')
BINARIES = {
    'c10_cuda.dll': 'ff798a3e18a09291e993e9bba452152447c7507b605d683c8289bf5112efe024',
    'torch_cuda.dll': '37fcaf926c486739e4cb505acb167a55d8f2ffd021c78f8822365478935c4630',
}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def supervise(argv, cwd, timeout, stdout_path, stderr_path):
    """Direct executable only; no tree-wide kill, no shell, no retries."""
    with Path(stdout_path).open('xb') as out, Path(stderr_path).open('xb') as err:
        p = subprocess.Popen(argv, cwd=cwd, stdin=subprocess.PIPE, stdout=out, stderr=err, shell=False)
        try:
            p.communicate(input=(str(p.pid) + '\n').encode('ascii'), timeout=timeout)
            return dict(pid=p.pid, exit_code=p.returncode, timed_out=False)
        except subprocess.TimeoutExpired:
            p.kill()
            p.wait(timeout=10)
            return dict(pid=p.pid, exit_code=p.returncode, timed_out=True)


def main():
    p = argparse.ArgumentParser()
    for name in ('python', 'site', 'output', 'commit', 'uuid', 'pci'): p.add_argument('--'+name, required=True)
    p.add_argument('--cuda-probe-authorized', action='store_true')
    a = p.parse_args()
    if not a.cuda_probe_authorized: raise ValueError('Explicit CUDA probe authorization required')
    out = Path(a.output).resolve()
    if out.exists() or out.with_suffix('.zip').exists(): raise ValueError('No overwrite/resume')
    out.mkdir(parents=True)
    result = dict(status='BLOCKED', error=None, role='ENGINEERING_RELATION_PROBE_NOT_FORMAL')
    def save(name, value): (out/name).write_text(json.dumps(value, indent=2), encoding='utf-8')
    try:
        def git(*args): return subprocess.check_output(['git', '-C', str(ROOT), *args]).decode('utf-8').strip()
        if git('rev-parse','HEAD') != a.commit or git('status','--porcelain'):
            raise ValueError('Commit/clean mismatch')
        hashes = {name: sha(Path(a.site)/'torch'/'lib'/name) for name in BINARIES}
        save('binary_identity.json', hashes)
        if hashes != BINARIES: raise ValueError('Target torch binary changed')
        from exposedpath_v141.gate8_target_python import probe
        contract = probe(a.python, a.site)
        save('runtime_contract.json', contract)
        command = [a.python, '-I', '-S', '-c', BOOT, str(ROOT), a.site,
                   '--output', str(out/'observation'), '--uuid', a.uuid, '--pci', a.pci,
                   '--runtime-contract', str(out/'runtime_contract.json')]
        save('invocation.json', dict(argv=command, commit=a.commit, timeout_seconds=45,
                                    source_sha256=sha(ROOT/'scripts/gate9_stream_probe.py')))
        proc = supervise(command, ROOT, 45, out/'stdout.bin', out/'stderr.bin')
        result['process'] = proc
        if proc['timed_out']: raise TimeoutError('No retry after timeout')
        r = json.loads((out/'observation/report.json').read_text(encoding='utf-8'))
        if r['pid'] != proc['pid']: raise ValueError('Producer PID mismatch')
        if git('rev-parse','HEAD') != a.commit or git('status','--porcelain'): raise ValueError('Tree changed')
        if {n: sha(Path(a.site)/'torch'/'lib'/n) for n in BINARIES} != hashes: raise ValueError('Binary changed')
        if proc['exit_code'] == 0 and r['status'] == 'NOT_SHARED_FOR_PROBED_CALL':
            result['status'] = 'RELATION_OBSERVED_REVIEW_REQUIRED'
        elif proc['exit_code'] == 2 and r['status'] == 'INCONCLUSIVE':
            result['status'] = 'INCONCLUSIVE'
        else: raise ValueError('Target failure; inspect original report and byte logs')
    except BaseException:
        result['error'] = traceback.format_exc()
    save('supervisor.json', result)
    files = sorted(x for x in out.rglob('*') if x.is_file())
    save('artifact_manifest.json', [dict(path=x.relative_to(out).as_posix(), bytes=x.stat().st_size,
                                      sha256=sha(x)) for x in files])
    # The reviewed PowerShell delivery wraps deployment/CPU/probe in ONE ZIP.
    print(json.dumps(dict(output=str(out), status=result['status'])))
    return 0 if result['status'] == 'RELATION_OBSERVED_REVIEW_REQUIRED' else 2


if __name__ == '__main__': raise SystemExit(main())
