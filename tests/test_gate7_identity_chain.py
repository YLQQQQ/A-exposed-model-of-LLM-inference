"""CPU producer-to-consumer regressions: real Git, no CUDA or Nsight."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from exposedpath import manifest, platform_adapter

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "scripts/run_server_smoke_test.ps1"


@pytest.fixture
def producer(tmp_path, monkeypatch):
    repo = tmp_path / "repo with spaces"
    repo.mkdir()
    def git(*args):
        return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()
    git("init", "-q")
    git("-c", "user.name=Test", "-c", "user.email=test@example.invalid",
        "commit", "--allow-empty", "-qm", "fixture")
    monkeypatch.chdir(repo)
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "3")
    monkeypatch.setenv("CUDA_DEVICE_ORDER", "PCI_BUS_ID")
    monkeypatch.setattr(manifest.torch.cuda, "is_available", lambda: False)
    monkeypatch.setattr(platform_adapter, "nvidia_smi", lambda *a, **k: "test-driver")
    monkeypatch.setattr(sys, "path", list(sys.path))
    identity = {"physical_gpu_index": 3, "logical_gpu_index": 0,
        "gpu_uuid": "GPU-12345678-1234-1234-1234-123456789abc", "gpu_pci_bus_id": "00000000:01:00.0"}
    preflight = tmp_path / "preflight.json"
    preflight.write_text(json.dumps(identity))
    prompt = tmp_path / "prompt.json"
    prompt.write_text(json.dumps({"schema_version": "1.0", "tokenizer_id": "synthetic",
        "fixed_input_tokens": 3, "samples": [{"sample_id": "s0", "input_ids": [1, 2, 3]}]}))
    source = LAUNCHER.read_text(encoding="utf-8")
    code = source.split('$manifest_py = @"', 1)[1].split('"@', 1)[0]
    replacements = {"ProjectRoot": repo, "PtFile": prompt, "GpuId": 3,
        "ExperimentId": "synthetic", "ModelPath": tmp_path / "model",
        "FixedOutputTokens": 2, "WarmupCount": 1, "RepeatCount": 2,
        "SmokeDir": tmp_path, "PreflightGpuIdentityPath": preflight}
    code = re.sub(r"\$(\w+)", lambda m: str(replacements[m[1]]), code)
    def run():
        exec(compile(code, "launcher_manifest_producer", "exec"), {})
        path = tmp_path / "wmpc_manifest.json"
        return path, json.loads(path.read_text())
    return run, repo, preflight, identity, git


def test_actual_launcher_producer_preserves_git_gpu_and_prompt_identity(producer):
    run, repo, preflight, identity, git = producer
    path, data = run()
    assert data["runner_git_commit"] == git("rev-parse", "HEAD")
    assert data["runner_git_dirty"] is False
    assert data["gpu_uuid"] == identity["gpu_uuid"]
    assert data["gpu_pci_bus_id"] == identity["gpu_pci_bus_id"]
    from scripts.gate7_smoke_validation import validate_pre_model_identity
    assert validate_pre_model_identity(path, preflight, repo) == []
    assert hashlib.sha256(path.read_bytes()).hexdigest() != data["prompt_tokens_sha256"]


def test_git_adapter_executes_real_git(producer):
    *_, git = producer
    assert platform_adapter.git(["rev-parse", "HEAD"]) == git("rev-parse", "HEAD")


def test_launcher_report_hashes_have_distinct_sources():
    source = LAUNCHER.read_text(encoding="utf-8")
    assert '"^SHA256:' not in source
    assert 'Get-FileHash -LiteralPath $ManifestPath -Algorithm SHA256' in source
    assert '"prompt_tokens_sha256"' in source
    assert source.index('"pre-model"') < source.index('# STEP 4: Pass 0')


@pytest.mark.parametrize("field,value", [
    ("runner_git_commit", None), ("runner_git_commit", "a" * 40),
    ("runner_git_dirty", None), ("runner_git_dirty", True),
    ("gpu_uuid", None), ("gpu_uuid", "GPU-bad"),
    ("gpu_pci_bus_id", None), ("gpu_index", 0),
    ("gpu_index_physical", None), ("gpu_index_logical", 3),
    ("data_role", "Formal"), ("study_mode", "N1_INTERVENTION"),
])
def test_pre_model_rejects_broken_producer_identity(producer, field, value):
    from scripts.gate7_smoke_validation import validate_pre_model_identity
    run, repo, preflight, *_ = producer
    path, data = run()
    data[field] = value
    path.write_text(json.dumps(data))
    assert validate_pre_model_identity(path, preflight, repo)


def test_producer_preserves_git_failure_reason(producer, monkeypatch):
    run, *_ = producer
    def fail(*args, **kwargs):
        raise platform_adapter.ToolExecutionError("synthetic git denied")
    monkeypatch.setattr(platform_adapter, "git", fail)
    with pytest.raises(platform_adapter.ToolExecutionError, match="synthetic git denied"):
        run()


def test_actual_producer_flows_into_runner_parity_and_telemetry(producer, monkeypatch):
    from exposedpath.runner import _write_cross_pass_parity, _sample_gpu_telemetry
    run, _, _, identity, _ = producer
    path, data = run()
    def query(args, **kwargs):
        if any("--query-gpu=driver_version" in arg for arg in args):
            return "test-driver"
        assert args[:2] == ["-i", identity["gpu_uuid"]]
        return f"3, {identity['gpu_uuid']}, {identity['gpu_pci_bus_id']}, test-GPU"
    monkeypatch.setattr(platform_adapter, "nvidia_smi", query)
    for label in ("pass0", "pass1"):
        folder = path.parent / label
        folder.mkdir()
        _write_cross_pass_parity(data, label, folder, path, data["model_id"], "cuda:0")
        _sample_gpu_telemetry(data, label, folder, "synthetic", gpu_index=3)
        parity = json.loads((folder / "cross_pass_parity.json").read_text())
        telemetry = json.loads((folder / "telemetry" / f"{label}_gpu_telemetry.jsonl").read_text())
        assert parity["manifest_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert parity["prompt_tokens_sha256"] == data["prompt_tokens_sha256"]
        assert parity["gpu_uuid"] == telemetry["requested_gpu_uuid"] == identity["gpu_uuid"]
        assert parity["gpu_pci_bus_id"] == telemetry["requested_pci_bus_id"] == identity["gpu_pci_bus_id"]
        assert telemetry["identity_match"] is True


@pytest.mark.parametrize("kind", ["dirty", "git-error", "mask", "order", "preflight-missing", "preflight-conflict"])
def test_pre_model_rejects_current_environment_conflicts(producer, monkeypatch, kind):
    from scripts.gate7_smoke_validation import validate_pre_model_identity
    run, repo, preflight, identity, _ = producer
    path, _ = run()
    if kind == "dirty":
        (repo / "untracked.txt").write_text("changed")
    elif kind == "git-error":
        monkeypatch.setattr(platform_adapter, "git", lambda *a, **k: (_ for _ in ()).throw(
            platform_adapter.ToolExecutionError("diagnostic retained")))
    elif kind == "mask":
        monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "0")
    elif kind == "order":
        monkeypatch.delenv("CUDA_DEVICE_ORDER")
    elif kind == "preflight-missing":
        preflight.unlink()
    else:
        preflight.write_text(json.dumps({**identity, "physical_gpu_index": 0}))
    issues = validate_pre_model_identity(path, preflight, repo)
    assert issues
    if kind == "git-error":
        assert "diagnostic retained" in str(issues)


def test_adapter_explicit_stderr_and_nonzero_diagnostics():
    result = platform_adapter.run_tool(sys.executable, ["-c", "print('ok')"], stderr=subprocess.DEVNULL)
    assert result.returncode == 0 and result.stdout.strip() == "ok"
    with pytest.raises(platform_adapter.ToolExecutionError, match="specific diagnostic"):
        platform_adapter.query_tool(sys.executable,
            ["-c", "import sys; sys.stderr.write('specific diagnostic'); sys.exit(2)"])


@pytest.mark.parametrize("broken", [False, True])
def test_real_powershell_pre_model_block_stops_or_records_file_hash(producer, broken):
    run, repo, preflight, *_ = producer
    path, data = run()
    if broken:
        data["gpu_uuid"] = None
        path.write_text(json.dumps(data))
    exe = shutil.which("powershell")
    if not exe:
        pytest.skip("Windows PowerShell unavailable")
    def q(value):
        return "'" + str(value).replace("'", "''") + "'"
    # Run the actual pre-model block/native wrapper, never STEP 4 or later.
    script = f'''
$env:PSModulePath = (Join-Path $PSHOME 'Modules') + ';' + $env:PSModulePath
$src = Get-Content {q(LAUNCHER)} -Raw
$ast = [System.Management.Automation.Language.Parser]::ParseInput($src,[ref]$null,[ref]$null)
foreach ($name in @('Resolve-Executable','Invoke-Native')) {{
 $fn = $ast.Find({{param($n) $n -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq $name}}, $true)
 . ([scriptblock]::Create($fn.Extent.Text))
}}
function Set-GateFailure {{ param($gate,$reason); throw $reason }}
$ProjectRoot={q(repo)}; $LogDir={q(path.parent / 'logs')}
$PythonExe={q(sys.executable)}; $ManifestPath={q(path)}; $PreflightGpuIdentityPath={q(preflight)}
$Report=@{{environment=@{{}}}}
$block=$src.Split(@('# Pre-model identity gate'),[StringSplitOptions]::None)[1].Split(@('# STEP 4: Pass 0'),[StringSplitOptions]::None)[0]
$block='# Pre-model identity gate'+$block
$block=$block.Replace('$ValidationScript = Join-Path -Path (Join-Path -Path $ProjectRoot -ChildPath "scripts") -ChildPath "gate7_smoke_validation.py"', '$ValidationScript = '+{q(q(ROOT / 'scripts/gate7_smoke_validation.py'))})
try {{ . ([scriptblock]::Create($block)); $Report | ConvertTo-Json -Depth 10 | Set-Content {q(path.parent / 'report.json')} -Encoding UTF8 }}
catch {{ Write-Output $_; exit 1 }}
'''
    result = subprocess.run([exe, "-NoProfile", "-Command", script], capture_output=True, text=True)
    assert result.returncode == (1 if broken else 0), result.stdout + result.stderr
    if broken:
        assert not (path.parent / "report.json").exists()
    else:
        env = json.loads((path.parent / "report.json").read_text(encoding="utf-8-sig"))["environment"]
        assert env["manifest_sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
        assert env["pre_model_identity"]["status"] == "PASS"
