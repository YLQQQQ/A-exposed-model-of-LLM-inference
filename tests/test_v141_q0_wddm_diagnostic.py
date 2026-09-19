"""Q0 KERNEL-MEMOP 独立 WDDM Engineering diagnostic 测试。"""

from __future__ import annotations

import json
import sqlite3
import subprocess
from pathlib import Path

import pytest

from exposedpath_v141.q0_wddm_diagnostic import (
    WDDMDiagnosticError,
    build_wddm_collection_argv,
    run_wddm_diagnostic,
    summarize_wddm_sqlite,
)
from exposedpath_v141.cli import main


PREFIX = "EXPOSEDPATH_JSON_V1:"


def _global_id(pid: int, tid: int) -> int:
    return (1 << 56) | (2 << 48) | (pid << 24) | tid


def _sqlite_fixture(path: Path, *, include_target_packet: bool = True) -> None:
    connection = sqlite3.connect(path)
    connection.executescript(
        """
        CREATE TABLE NVTX_EVENTS (
            start INTEGER NOT NULL, end INTEGER, text TEXT, textId INTEGER,
            globalTid INTEGER
        );
        CREATE TABLE StringIds (id INTEGER PRIMARY KEY, value TEXT);
        CREATE TABLE WDDM_QUEUE_PACKET_START_EVENTS (
            start INTEGER NOT NULL, end INTEGER NOT NULL, globalTid INTEGER,
            gpu INTEGER NOT NULL, context INTEGER NOT NULL,
            dmaBufferSize INTEGER NOT NULL, dmaBuffer INTEGER NOT NULL,
            queuePacket INTEGER NOT NULL, progressFenceValue INTEGER NOT NULL,
            packetType INTEGER NOT NULL, submitSequence INTEGER NOT NULL,
            allocationListSize INTEGER NOT NULL,
            patchLocationListSize INTEGER NOT NULL, present INTEGER NOT NULL,
            engineType INTEGER NOT NULL, syncObject INTEGER
        );
        CREATE TABLE ENUM_WDDM_ENGINE_TYPE (
            id INTEGER PRIMARY KEY, name TEXT, label TEXT
        );
        CREATE TABLE TARGET_INFO_WDDM_CONTEXTS (
            context INTEGER NOT NULL, engineType INTEGER NOT NULL,
            nodeOrdinal INTEGER NOT NULL, friendlyName TEXT NOT NULL
        );
        INSERT INTO ENUM_WDDM_ENGINE_TYPE VALUES
            (1, 'DXGK_ENGINE_TYPE_3D', '3D'),
            (6, 'DXGK_ENGINE_TYPE_COPY', 'Copy');
        INSERT INTO TARGET_INFO_WDDM_CONTEXTS VALUES
            (77, 1, 0, 'target-compute');
        """
    )
    identity = {
        "kind": "request",
        "experiment_id": "exposedpath-q0",
        "wmpc_id": "q0-controlled",
        "run_id": "q0-win-4090-20260917-kernel-memop-wddm-diag-01.q0-kernel-memop-001",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "request_id": "Q0-KERNEL-MEMOP-001",
        "repeat_id": "repeat-0",
        "phase": "full_request",
    }
    connection.execute(
        "INSERT INTO NVTX_EVENTS VALUES (?,?,?,?,?)",
        (100, 500, PREFIX + json.dumps(identity), None, _global_id(42, 7)),
    )
    if include_target_packet:
        connection.execute(
            "INSERT INTO WDDM_QUEUE_PACKET_START_EVENTS VALUES "
            "(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (200, 210, _global_id(42, 9), 0, 77, 4096, 1, 2, 3, 0, 5, 0, 0, 0, 1, None),
        )
    connection.commit()
    connection.close()


def _source_manifest() -> dict[str, object]:
    return {
        "experiment_id": "exposedpath-q0",
        "wmpc_id": "q0-controlled",
        "run_id": "q0-win-4090-20260917-kernel-memop-wddm-diag-01.q0-kernel-memop-001",
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "repeat_id": "repeat-0",
        "q0_case_id": "Q0-KERNEL-MEMOP-001",
    }


def test_wddm_collection_argv_is_dedicated_and_explicit(tmp_path):
    argv = build_wddm_collection_argv(
        tmp_path / "nsys.exe",
        tmp_path / "q0.exe",
        tmp_path / "trace",
        "q0-win-4090-20260917-kernel-memop-wddm-diag-01.q0-kernel-memop-001",
    )

    assert argv.count("--trace=cuda,nvtx,wddm") == 1
    assert argv.count("--wddm-additional-events=true") == 1
    assert argv.count("--wddm-memory-trace=false") == 1
    assert argv.count("--wddm-backtraces=false") == 1
    assert "--capture-range=cudaProfilerApi" in argv
    assert argv[-4:] == [
        "--case", "Q0-KERNEL-MEMOP-001", "--run-id",
        "q0-win-4090-20260917-kernel-memop-wddm-diag-01.q0-kernel-memop-001",
    ]


def test_wddm_summary_never_claims_strict_cuda_packet_mapping(tmp_path):
    sqlite_path = tmp_path / "trace.sqlite"
    _sqlite_fixture(sqlite_path)

    summary, timeline = summarize_wddm_sqlite(
        sqlite_path,
        source_manifest=_source_manifest(),
        hags={"status": "ENABLED", "raw_value": 2},
    )

    assert summary["evidence_status"] == "TIMELINE_ATTRIBUTION_AVAILABLE"
    assert summary["attribution_semantics"] == "PID_CONTEXT_ENGINE_TIME_WINDOW_INFERENCE_ONLY"
    assert summary["strict_cuda_wddm_mapping"] is False
    assert summary["causal_verdict"] == "NOT_ESTABLISHED"
    assert summary["target_request"]["process_id"] == 42
    assert len(timeline) == 1
    assert timeline[0]["process_id"] == 42
    assert timeline[0]["engine_label"] == "3D"


@pytest.mark.parametrize(
    ("hags", "include_packet", "reason"),
    [
        ({"status": "DISABLED", "raw_value": 1}, True, "HAGS_NOT_CONFIRMED_ENABLED"),
        ({"status": "UNRESOLVED", "raw_value": None}, True, "HAGS_NOT_CONFIRMED_ENABLED"),
        ({"status": "ENABLED", "raw_value": 2}, False, "NO_TARGET_WDDM_PACKET_IN_REQUEST"),
    ],
)
def test_wddm_summary_fails_closed_when_evidence_is_insufficient(
    tmp_path, hags, include_packet, reason
):
    sqlite_path = tmp_path / "trace.sqlite"
    _sqlite_fixture(sqlite_path, include_target_packet=include_packet)

    summary, _timeline = summarize_wddm_sqlite(
        sqlite_path, source_manifest=_source_manifest(), hags=hags
    )

    assert summary["evidence_status"] == "EVIDENCE_INSUFFICIENT"
    assert reason in summary["insufficient_reasons"]
    assert summary["causal_verdict"] == "NOT_ESTABLISHED"


def test_wddm_context_row_without_target_packet_is_still_insufficient(tmp_path):
    sqlite_path = tmp_path / "trace.sqlite"
    _sqlite_fixture(sqlite_path, include_target_packet=False)
    connection = sqlite3.connect(sqlite_path)
    connection.execute(
        "CREATE TABLE WDDM_HW_QUEUE_EVENTS ("
        "start INTEGER, end INTEGER, globalTid INTEGER, gpu INTEGER, "
        "context INTEGER, hwQueue INTEGER, parentDxgHwQueue INTEGER)"
    )
    connection.execute(
        "INSERT INTO WDDM_HW_QUEUE_EVENTS VALUES (?,?,?,?,?,?,?)",
        (200, 210, _global_id(42, 9), 0, 77, 1, 2),
    )
    connection.commit()
    connection.close()

    summary, timeline = summarize_wddm_sqlite(
        sqlite_path,
        source_manifest=_source_manifest(),
        hags={"status": "ENABLED", "raw_value": 2},
    )

    assert summary["evidence_status"] == "EVIDENCE_INSUFFICIENT"
    assert "NO_TARGET_WDDM_PACKET_IN_REQUEST" in summary["insufficient_reasons"]
    assert timeline == []


def test_wddm_summary_rejects_non_engineering_or_wrong_case(tmp_path):
    sqlite_path = tmp_path / "trace.sqlite"
    _sqlite_fixture(sqlite_path)
    manifest = _source_manifest()
    manifest["run_role"] = "Formal"

    with pytest.raises(WDDMDiagnosticError, match="Engineering"):
        summarize_wddm_sqlite(
            sqlite_path, source_manifest=manifest, hags={"status": "ENABLED"}
        )

    manifest = _source_manifest()
    manifest["q0_case_id"] = "Q0-STREAM-001"
    with pytest.raises(WDDMDiagnosticError, match="KERNEL-MEMOP"):
        summarize_wddm_sqlite(
            sqlite_path, source_manifest=manifest, hags={"status": "ENABLED"}
        )


def _environment() -> dict[str, object]:
    return {
        "selected_gpu": {
            "physical_index": None,
            "logical_index": 0,
            "uuid": "GPU-ABC",
            "name": "NVIDIA GeForce RTX 4090",
            "memory_total_mib": 24563,
            "async_engine_count": 2,
            "device_overlap": 1,
            "concurrent_kernels": 1,
            "can_map_host_memory": 1,
        },
        "driver_version": 12050,
        "cuda_driver_version": 12050,
        "cuda_runtime_version": 12040,
        "nsight_systems": "NVIDIA Nsight Systems version 2026.2.1.210",
        "os": "Windows-test",
    }


def _diagnostic_runner(seen: list[list[str]]):
    def run(argv, **_kwargs):
        command = [str(value) for value in argv]
        seen.append(command)
        if command[1:] == ["--version"]:
            return subprocess.CompletedProcess(
                command, 0, "NVIDIA Nsight Systems version 2026.2.1.210", ""
            )
        if command[1:] == ["profile", "--help"]:
            return subprocess.CompletedProcess(
                command,
                0,
                "--trace cuda,nvtx,wddm\n"
                "--wddm-additional-events true,false\n"
                "--wddm-memory-trace true,false\n"
                "--wddm-backtraces true,false\n",
                "",
            )
        if len(command) > 1 and command[1] == "profile":
            Path(command[command.index("-o") + 1]).with_suffix(".nsys-rep").write_bytes(
                b"wddm-raw"
            )
            return subprocess.CompletedProcess(command, 0, "profile ok", "")
        if len(command) > 1 and command[1] == "export":
            output = Path(command[command.index("--output") + 1])
            _sqlite_fixture(output)
            return subprocess.CompletedProcess(command, 0, "export ok", "")
        raise AssertionError(command)

    return run


def test_run_wddm_diagnostic_saves_immutable_engineering_evidence(tmp_path):
    binary = tmp_path / "exposedpath_q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"same-existing-binary")
    nsys.write_bytes(b"nsys")
    output = tmp_path / "wddm-diag"
    seen: list[list[str]] = []

    summary_path = run_wddm_diagnostic(
        output,
        binary,
        nsys,
        run_id="q0-win-4090-20260917-kernel-memop-wddm-diag-01",
        cuda_visible_device="GPU-ABC",
        process_runner=_diagnostic_runner(seen),
        environment_probe=lambda *_: _environment(),
        hags_probe=lambda: {"status": "ENABLED", "raw_value": 2},
    )

    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    receipt = json.loads(
        (output / "wddm_diagnostic_receipt.json").read_text(encoding="utf-8")
    )
    compatibility_receipt = json.loads(
        (output / "collection_receipt.json").read_text(encoding="utf-8")
    )
    assert summary["evidence_status"] == "TIMELINE_ATTRIBUTION_AVAILABLE"
    assert receipt["data_role"] == "Engineering"
    assert receipt["diagnostic_only"] is True
    assert receipt["q0_status"] == "NOT_RUN"
    assert receipt["research_eligibility"]["formal_evidence"] is False
    assert receipt["source"]["binary"]["sha256"]
    assert compatibility_receipt["schema_version"] == "exposedpath-q0-collection/0.2.0"
    assert compatibility_receipt["status"] == "COLLECTED"
    assert compatibility_receipt["research_eligibility"]["scope"] == (
        "WDDM_ENGINEERING_DIAGNOSTIC_ONLY"
    )
    assert (output / "trace.nsys-rep").read_bytes() == b"wddm-raw"
    assert (output / "trace.sqlite").is_file()
    assert (output / "nsys_version.txt").is_file()
    assert (output / "nsys_profile_help.txt").is_file()
    assert (output / "nsys_profile_help_wddm.txt").is_file()
    assert (output / "hags_status.json").is_file()
    assert (output / "wddm_timeline.json").is_file()
    profile = next(command for command in seen if len(command) > 1 and command[1] == "profile" and "--help" not in command)
    assert "--trace=cuda,nvtx,wddm" in profile
    assert "--wddm-additional-events=true" in profile

    with pytest.raises(WDDMDiagnosticError, match="拒绝覆盖"):
        run_wddm_diagnostic(
            output,
            binary,
            nsys,
            run_id="q0-win-4090-20260917-kernel-memop-wddm-diag-01",
            cuda_visible_device="GPU-ABC",
        )


def test_wddm_diagnostic_fails_before_collection_when_installed_help_lacks_flag(
    tmp_path
):
    binary = tmp_path / "q0.exe"
    nsys = tmp_path / "nsys.exe"
    binary.write_bytes(b"binary")
    nsys.write_bytes(b"nsys")
    seen: list[list[str]] = []

    def runner(argv, **_kwargs):
        command = [str(value) for value in argv]
        seen.append(command)
        if command[1:] == ["--version"]:
            return subprocess.CompletedProcess(command, 0, "2026.2.1.210", "")
        if command[1:] == ["profile", "--help"]:
            return subprocess.CompletedProcess(command, 0, "--trace cuda,nvtx,wddm", "")
        raise AssertionError("不应开始采集")

    output = tmp_path / "missing-help"
    with pytest.raises(WDDMDiagnosticError, match="帮助输出缺少"):
        run_wddm_diagnostic(
            output,
            binary,
            nsys,
            run_id="q0-win-4090-20260917-kernel-memop-wddm-diag-01",
            cuda_visible_device="GPU-ABC",
            process_runner=runner,
            environment_probe=lambda *_: _environment(),
            hags_probe=lambda: {"status": "ENABLED", "raw_value": 2},
        )
    assert not any(len(command) > 1 and command[1] == "profile" and "--help" not in command for command in seen)
    assert (output / "nsys_profile_help.txt").is_file()


def test_wddm_diagnostic_cli_remains_not_q0(monkeypatch, tmp_path, capsys):
    summary = tmp_path / "wddm_summary.json"
    summary.write_text('{"evidence_status":"EVIDENCE_INSUFFICIENT"}', encoding="utf-8")
    monkeypatch.setattr(
        "exposedpath_v141.cli.run_wddm_diagnostic", lambda *_args, **_kwargs: summary
    )

    status = main(
        [
            "run-q0-wddm-diagnostic",
            "--output-dir", str(tmp_path / "out"),
            "--binary", str(tmp_path / "q0.exe"),
            "--nsys", str(tmp_path / "nsys.exe"),
            "--run-id", "q0-win-4090-20260917-kernel-memop-wddm-diag-01",
            "--cuda-visible-device", "GPU-ABC",
        ]
    )

    output = capsys.readouterr().out
    assert status == 0
    assert "diagnostic_scope: ENGINEERING_ONLY" in output
    assert "evidence_status: EVIDENCE_INSUFFICIENT" in output
    assert "q0_execution_status: NOT_RUN" in output
