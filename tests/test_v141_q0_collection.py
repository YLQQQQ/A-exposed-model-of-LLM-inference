"""真实 Q0 单 case 采集的不可覆盖 receipt 测试。"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from exposedpath_v141.cli import main
from exposedpath_v141.q0_collection import Q0CollectionError, execute_q0_case
from exposedpath_v141.q0_execution import prepare_q0_run


def _prepared(tmp_path: Path, cuda_visible_device: str = "GPU-ABC") -> Path:
    tools = tmp_path / "tools"
    tools.mkdir(parents=True)
    binary = tools / "q0.exe"
    nsys = tools / "nsys.exe"
    binary.write_bytes(b"binary-v1")
    nsys.write_bytes(b"nsys-v1")
    return prepare_q0_run(
        tmp_path / "run", binary, nsys,
        platform="windows", run_id="real-q0-001", cuda_visible_device=cuda_visible_device,
    )


def _environment() -> dict[str, object]:
    return {
        "selected_gpu": {
            "physical_index": 1,
            "logical_index": 0,
            "uuid": "GPU-ABC",
            "name": "NVIDIA RTX 6000 Ada Generation",
            "memory_total_mib": 49140,
        },
        "driver_version": "999.1",
        "cuda_driver_version": 13000,
        "cuda_runtime_version": 13000,
        "nsight_systems": "test-nsys",
        "os": "Windows-test",
    }


def _successful_runner(seen: dict[str, object]):
    def run(argv, **kwargs):
        seen["argv"] = list(argv)
        seen["env"] = dict(kwargs["env"])
        prefix = Path(argv[argv.index("-o") + 1])
        prefix.with_suffix(".nsys-rep").write_bytes(b"real-raw-trace")
        return subprocess.CompletedProcess(argv, 0, "collector stdout", "collector stderr")

    return run


def test_execute_native_case_writes_hashed_receipt_and_preserves_gpu_mapping(tmp_path):
    manifest = _prepared(tmp_path)
    seen: dict[str, object] = {}

    receipt_path = execute_q0_case(
        manifest, "Q0-STREAM-001", process_runner=_successful_runner(seen),
        environment_probe=lambda *_: _environment(),
    )
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))

    raw = receipt_path.parent / receipt["raw_trace"]["name"]
    assert receipt["status"] == "COLLECTED"
    assert receipt["q0_status"] == "NOT_RUN"
    assert receipt["environment"]["selected_gpu"]["uuid"] == "GPU-ABC"
    assert seen["env"]["CUDA_VISIBLE_DEVICES"] == "GPU-ABC"
    assert receipt["raw_trace"]["sha256"] == hashlib.sha256(raw.read_bytes()).hexdigest().upper()
    assert (receipt_path.parent / "collection_stdout.txt").read_text(encoding="utf-8") == "collector stdout"


def test_gpu_uuid_with_or_without_internal_hyphens_is_equivalent(tmp_path):
    selector = "GPU-0d8fafe6-a1e9-33cc-25fb-632316736455"
    manifest = _prepared(tmp_path, selector)
    environment = _environment()
    environment["selected_gpu"]["uuid"] = "GPU-0d8fafe6a1e933cc25fb632316736455"

    receipt_path = execute_q0_case(
        manifest,
        "Q0-STREAM-001",
        process_runner=_successful_runner({}),
        environment_probe=lambda *_: environment,
    )

    assert json.loads(receipt_path.read_text(encoding="utf-8"))["status"] == "COLLECTED"


def test_different_gpu_uuids_are_not_equivalent(tmp_path):
    selector = "GPU-0d8fafe6-a1e9-33cc-25fb-632316736455"
    manifest = _prepared(tmp_path, selector)
    environment = _environment()
    environment["selected_gpu"]["uuid"] = "GPU-1d8fafe6a1e933cc25fb632316736455"

    with pytest.raises(Q0CollectionError, match="GPU UUID"):
        execute_q0_case(
            manifest,
            "Q0-STREAM-001",
            process_runner=_successful_runner({}),
            environment_probe=lambda *_: environment,
        )


def test_execute_rejects_tool_hash_change_existing_output_and_synthetic_case(tmp_path):
    manifest = _prepared(tmp_path)
    plan = json.loads(manifest.read_text(encoding="utf-8"))
    Path(plan["source"]["binary"]["path"]).write_bytes(b"changed")
    with pytest.raises(Q0CollectionError, match="binary.*哈希"):
        execute_q0_case(
            manifest, "Q0-STREAM-001", process_runner=_successful_runner({}),
            environment_probe=lambda *_: _environment(),
        )

    manifest = _prepared(tmp_path / "second")
    execute_q0_case(
        manifest, "Q0-STREAM-001", process_runner=_successful_runner({}),
        environment_probe=lambda *_: _environment(),
    )
    with pytest.raises(Q0CollectionError, match="拒绝覆盖"):
        execute_q0_case(
            manifest, "Q0-STREAM-001", process_runner=_successful_runner({}),
            environment_probe=lambda *_: _environment(),
        )
    with pytest.raises(Q0CollectionError, match="没有原生采集命令"):
        execute_q0_case(
            manifest, "Q0-TERMINAL-TIE-001", process_runner=_successful_runner({}),
            environment_probe=lambda *_: _environment(),
        )


def test_failed_collector_keeps_failure_evidence_but_never_success_receipt(tmp_path):
    manifest = _prepared(tmp_path)

    def failed(argv, **kwargs):
        return subprocess.CompletedProcess(argv, 7, "partial out", "fatal collector")

    with pytest.raises(Q0CollectionError, match="采集失败"):
        execute_q0_case(
            manifest, "Q0-STREAM-001", process_runner=failed,
            environment_probe=lambda *_: _environment(),
        )

    case_dir = manifest.parent / "cases" / "Q0-STREAM-001"
    assert not (case_dir / "collection_receipt.json").exists()
    failure = json.loads((case_dir / "collection_failure.json").read_text(encoding="utf-8"))
    assert failure["status"] == "COLLECTION_FAILED"
    assert failure["returncode"] == 7


def test_default_environment_probe_is_part_of_real_execution(tmp_path):
    manifest = _prepared(tmp_path)

    def runner(argv, **kwargs):
        if argv[-1] == "--environment-json":
            return subprocess.CompletedProcess(
                argv, 0,
                json.dumps({
                    "uuid": "GPU-ABC", "name": "RTX TEST", "memory_total_mib": 1024,
                    "driver_version": 13000, "cuda_driver_version": 13000,
                    "cuda_runtime_version": 13000,
                }),
                "",
            )
        if argv[-1] == "--version":
            return subprocess.CompletedProcess(argv, 0, "Nsight Systems 1.0", "")
        prefix = Path(argv[argv.index("-o") + 1])
        prefix.with_suffix(".nsys-rep").write_bytes(b"trace")
        return subprocess.CompletedProcess(argv, 0, "", "")

    receipt = json.loads(
        execute_q0_case(manifest, "Q0-STREAM-001", process_runner=runner).read_text(
            encoding="utf-8"
        )
    )

    assert receipt["environment"]["cuda_runtime_version"] == 13000
    assert receipt["environment"]["selected_gpu"]["logical_index"] == 0


def test_execute_q0_case_cli_reports_collection_without_q0_upgrade(
    tmp_path, monkeypatch, capsys
):
    receipt = tmp_path / "collection_receipt.json"
    receipt.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        "exposedpath_v141.cli.execute_q0_case", lambda *_args, **_kwargs: receipt
    )

    assert main([
        "execute-q0-case", "--run-manifest", str(tmp_path / "run.json"),
        "--case", "Q0-STREAM-001",
    ]) == 0

    output = capsys.readouterr().out
    assert f"collection_receipt: {receipt}" in output
    assert "q0_execution_status: NOT_RUN" in output
