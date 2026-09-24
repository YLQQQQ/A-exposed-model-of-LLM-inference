"""Synthetic legacy producer shape; no private trace or server paths."""
import copy
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts/run_server_smoke_test.ps1'
COMMIT = 'a' * 40


@pytest.fixture
def artifacts(tmp_path):
    analysis = tmp_path / 'analysis'
    analysis.mkdir()
    sqlite = tmp_path / 'pass1_profile.sqlite'
    sqlite.write_bytes(b'input identity only; SQLite gate is separate')
    manifest = tmp_path / 'manifest.json'
    manifest.write_text(json.dumps({'runner_git_commit': COMMIT,
        'run_id': 'test-run', 'wmpc_id': 'test-wmpc', 'data_role': 'Engineering'}))
    categories = ('host_path', 'cuda_api', 'device_wait', 'sync_residual', 'unattributed')
    result = {
        'metric_definition_version': 'exposedpath-v2',
        'metadata': {'metric_definition_version': 'exposedpath-v2',
            'parser_version': 'exposedpath-v2', 'workload_id': sqlite.stem,
            'git_commit': COMMIT[:12], 'schema_version': '3.25.0',
            'nsys_product_version': '2026.2.1.210'},
        'trace_quality': {'fatal_errors': [], 'warnings': ['CUDA event activity table unavailable'],
            'missing_optional_tables': ['CUDA event activity table unavailable'],
            'dropped_records_status': 'unknown', 'request_count': 1, 'repeat_count': 1},
        'A_summary': {phase: {f'A_{c}_ms_mean': 1.0 for c in categories}
            for phase in ('prefill', 'decode', 'full_request')},
        'raw_summary': {p: {'window_duration_ms_mean': 5} for p in ('prefill', 'decode', 'full_request')},
        'overlap_summary': {p: {'O_api_gpu_mean': None} for p in ('prefill', 'decode', 'full_request')},
        'B_summary': {p: {'total_syncs': 1, 'B_valid': 0, 'B_invalid': 1, 'valid_wait_sets': 0}
                      for p in ('prefill', 'decode', 'full_request')},
        'repeat_results': [{'request_id': 1, 'repeat_id': 1, 'phase': 'full_request',
            'window_duration_ms': 5, **{f'A_{c}_ms': 1.0 for c in categories}}],
        'b_sync_details': [{'physical_sync_uid': 'corr=4:start=1:end=2',
            'request_id': 1, 'repeat_id': 1, 'phase': 'unresolved-legacy-label',
            'sync_start_ns': 1, 'sync_end_ns': 2, 'wait_set_valid': False,
            'B_valid': False, 'invalid_reason': 'NO_PENDING_ACTIVITY'}],
        'legacy_compatibility': {'note': 'synthetic fixture'},
    }
    path = analysis / 'accounting_result.json'
    path.write_text(json.dumps(result))
    (analysis / 'accounting_summary.csv').write_text('request_id,repeat_id,phase\n1,1,full_request\n')
    (analysis / 'b_sync_detail.csv').write_text('physical_sync_uid\ncorr=4:start=1:end=2\n')
    return path, sqlite, manifest, result


def launch_validation(artifacts, tmp_path, exit_code=0):
    exe = shutil.which('powershell') or str(Path(os.environ.get('SystemRoot', r'C:\Windows')) /
        'System32/WindowsPowerShell/v1.0/powershell.exe')
    if not Path(exe).is_file():
        pytest.skip('Windows PowerShell unavailable')
    path, sqlite, manifest, _ = artifacts
    def q(value):
        return "'" + str(value).replace("'", "''") + "'"
    # Execute the real validator block and native-process wrapper, never the GPU launcher.
    command = f'''
$src = Get-Content {q(SCRIPT)} -Raw
$ast = [System.Management.Automation.Language.Parser]::ParseInput($src,[ref]$null,[ref]$null)
foreach ($name in @('Resolve-Executable','Invoke-Native')) {{
 $fn = $ast.Find({{param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name}}, $true)
 . ([scriptblock]::Create($fn.Extent.Text))
}}
$ProjectRoot={q(ROOT)}; $LogDir={q(tmp_path / 'logs')}
$PythonExe={q(sys.executable)}; $AnalysisDir={q(path.parent)}
$NsysSqliteFile={q(sqlite)}; $ManifestPath={q(manifest)}
$ValidationScript={q(ROOT / 'scripts/gate7_smoke_validation.py')}
$Report=@{{analyzer=@{{}}; errors=@()}}
$r=@{{ExitCode={exit_code}}}
$block=$src.Split(@('# --- Analyzer validation: must pass ALL gates ---'),[StringSplitOptions]::None)[1].Split(@('$Report.analyzer["status"]'),[StringSplitOptions]::None)[0]
. ([scriptblock]::Create($block))
@{{ok=$analysis_ok; errors=$gate_errors; analyzer=$Report.analyzer}} | ConvertTo-Json -Depth 30 | Set-Content {q(tmp_path / 'observed.json')} -Encoding UTF8
'''
    run = subprocess.run([exe, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', command],
                         capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr
    return json.loads((tmp_path / 'observed.json').read_text(encoding='utf-8-sig'))


def test_real_launcher_accepts_known_legacy_shape_without_sync_coverage(artifacts, tmp_path):
    observed = launch_validation(artifacts, tmp_path)
    assert observed['ok'] is True, observed
    report = observed['analyzer']['acceptance']
    assert report['acceptance_version'] == 'gate7-legacy-analyzer/1'
    assert report['measurement_validity'] == 'NOT_ASSESSED'
    assert report['window_coverage']['status'] == 'unknown'
    assert report['window_coverage']['count'] is None
    assert report['window_coverage']['duration'] is None
    assert report['diagnostics']['dropped_records_status'] == 'unknown'


def test_real_launcher_blocks_analyzer_exit(artifacts, tmp_path):
    assert launch_validation(artifacts, tmp_path, exit_code=1)['ok'] is False


@pytest.mark.parametrize('mutation', ['empty', 'version', 'a_empty', 'a_nan', 'a_bool',
    'a_missing', 'diagnostics_missing', 'fatal', 'warnings_bad', 'dropped', 'commit',
    'workload', 'details_bad', 'repeat_empty', 'csv_missing', 'json_bad', 'manifest_bad',
    'csv_bad', 'unreviewed_warning', 'duplicate_uid', 'time_reversal', 'contradictory_validity',
    'diagnostic_nan', 'b_summary_bad', 'raw_summary_bad', 'csv_identity'])
def test_legacy_validation_rejects_bad_artifacts(artifacts, mutation):
    from scripts.gate7_smoke_validation import validate_analyzer
    path, sqlite, manifest, original = artifacts
    data = copy.deepcopy(original)
    if mutation == 'empty': data = {}
    elif mutation == 'version': data['metric_definition_version'] = 'future-version'
    elif mutation == 'a_empty': data['A_summary'] = {}
    elif mutation == 'a_nan': data['A_summary']['full_request']['A_host_path_ms_mean'] = float('nan')
    elif mutation == 'a_bool': data['A_summary']['full_request']['A_host_path_ms_mean'] = True
    elif mutation == 'a_missing': del data['A_summary']['decode']['A_cuda_api_ms_mean']
    elif mutation == 'diagnostics_missing': del data['trace_quality']
    elif mutation == 'fatal': data['trace_quality']['fatal_errors'] = ['missing required data']
    elif mutation == 'warnings_bad': data['trace_quality']['warnings'] = 'not a list'
    elif mutation == 'dropped': data['trace_quality']['dropped_records_status'] = 'dropped'
    elif mutation == 'commit': data['metadata']['git_commit'] = 'b' * 12
    elif mutation == 'workload': data['metadata']['workload_id'] = 'other-input'
    elif mutation == 'details_bad': data['b_sync_details'][0]['B_valid'] = 'false'
    elif mutation == 'repeat_empty': data['repeat_results'] = []
    elif mutation == 'csv_missing': (path.parent / 'accounting_summary.csv').unlink()
    elif mutation == 'manifest_bad': manifest.write_text('{}')
    elif mutation == 'csv_bad': (path.parent / 'b_sync_detail.csv').write_text('wrong\nfield\n')
    elif mutation == 'unreviewed_warning': data['trace_quality']['warnings'].append('records lost')
    elif mutation == 'duplicate_uid': data['b_sync_details'].append(copy.deepcopy(data['b_sync_details'][0]))
    elif mutation == 'time_reversal': data['b_sync_details'][0]['sync_end_ns'] = 0
    elif mutation == 'contradictory_validity': data['b_sync_details'][0]['B_valid'] = True
    elif mutation == 'diagnostic_nan': data['trace_quality']['conservation_error_max'] = float('nan')
    elif mutation == 'b_summary_bad': data['B_summary']['full_request']['B_valid'] = 'yes'
    elif mutation == 'raw_summary_bad': data['raw_summary']['full_request'] = []
    elif mutation == 'csv_identity': (path.parent / 'b_sync_detail.csv').write_text('physical_sync_uid\nother-input\n')
    path.write_text('{' if mutation == 'json_bad' else json.dumps(data))
    report = validate_analyzer(path, sqlite, manifest)
    assert report['status'] == 'BLOCKED', report
    assert report['issues']


def test_validator_preserves_legacy_diagnostics_and_binds_hashes(artifacts):
    from scripts.gate7_smoke_validation import validate_analyzer
    path, sqlite, manifest, original = artifacts
    report = validate_analyzer(path, sqlite, manifest)
    assert report['status'] == 'PASS', report
    assert report['diagnostics'] == original['trace_quality']
    assert report['legacy_sync_diagnostics'] == original['b_sync_details']
    assert report['identity']['run_id'] == 'test-run'
    assert len(report['identity']['sqlite_sha256']) == 64
    assert report['a_structure_status'] == 'VALIDATED_STRUCTURE_ONLY'


@pytest.mark.parametrize('bad', [False, True])
def test_analyzer_cli_exit_and_machine_output_agree(artifacts, bad):
    path, sqlite, manifest, data = artifacts
    if bad:
        path.write_text('{}')
    run = subprocess.run([sys.executable, str(ROOT / 'scripts/gate7_smoke_validation.py'),
        'analyzer', '--result', str(path), '--sqlite', str(sqlite), '--manifest', str(manifest)],
        capture_output=True, text=True)
    assert run.returncode == (1 if bad else 0), run.stderr
    assert json.loads(run.stdout)['status'] == ('BLOCKED' if bad else 'PASS')


def test_real_launcher_blocks_malformed_legacy_output(artifacts, tmp_path):
    artifacts[0].write_text('{}')
    observed = launch_validation(artifacts, tmp_path)
    assert observed['ok'] is False
    assert observed['analyzer']['acceptance']['status'] == 'BLOCKED'


def test_revised_acceptance_cannot_resume_historical_attempt(tmp_path):
    exe = shutil.which('powershell') or str(Path(os.environ.get('SystemRoot', r'C:\Windows')) /
        'System32/WindowsPowerShell/v1.0/powershell.exe')
    if not Path(exe).is_file():
        pytest.skip('Windows PowerShell unavailable')
    run = subprocess.run([exe, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(SCRIPT),
        '-ModelPath', str(tmp_path), '-GpuId', '3', '-NsysPath', sys.executable,
        '-PythonExe', sys.executable, '-ExistingSmokeDir', str(tmp_path), '-ResumeFrom', 'Analyzer',
        '-DryRun'], capture_output=True, text=True)
    assert run.returncode == 1
    assert 'gate7-legacy-analyzer/1 requires a fresh attempt' in run.stdout
    assert not list(tmp_path.iterdir())
