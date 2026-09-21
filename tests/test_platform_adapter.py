"""EP-G7-10: platform adaptation isolation for the runner core.

The runner/manifest core must stay platform agnostic. Everything that depends
on the host platform (executable naming, host-tool resolution, structured
subprocess invocation) belongs to ``exposedpath.platform_adapter``.

These tests are pure CPU checks: no GPU, no nsys, no Q0 collection.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

from exposedpath import manifest, platform_adapter, runner


# ---------------------------------------------------------------------------
# platform identity
# ---------------------------------------------------------------------------

def test_platform_id_is_normalised_and_matches_host():
    pid = platform_adapter.platform_id()
    assert pid in platform_adapter.KNOWN_PLATFORMS
    expected = "windows" if os.name == "nt" else ("macos" if sys.platform == "darwin" else "linux")
    assert pid == expected


def test_executable_suffix_follows_platform():
    expected = ".exe" if platform_adapter.is_windows() else ""
    assert platform_adapter.executable_suffix() == expected


def test_tool_candidates_add_exe_suffix_only_on_windows():
    candidates = platform_adapter.tool_candidates("nsys")
    assert candidates[0] == "nsys"
    if platform_adapter.is_windows():
        assert "nsys.exe" in candidates
    else:
        assert not any(c.endswith(".exe") for c in candidates)


# ---------------------------------------------------------------------------
# tool resolution
# ---------------------------------------------------------------------------

def test_resolve_tool_returns_absolute_path_for_existing_path():
    resolved = platform_adapter.resolve_tool(sys.executable)
    assert resolved is not None
    assert os.path.isabs(resolved)
    assert Path(resolved).exists()


def test_resolve_tool_returns_none_for_unknown_tool():
    assert platform_adapter.resolve_tool("exposedpath-no-such-tool-xyz") is None


def test_resolve_tool_considers_explicit_extra_candidates(tmp_path):
    fake = tmp_path / ("faketool" + platform_adapter.executable_suffix())
    fake.write_text("stub", encoding="utf-8")
    assert platform_adapter.resolve_tool("faketool") is None
    resolved = platform_adapter.resolve_tool("faketool", extra_candidates=(str(fake),))
    assert resolved is not None and os.path.isabs(resolved)


def test_tool_argv_fails_closed_when_tool_is_unresolvable():
    with pytest.raises(platform_adapter.ToolUnavailableError):
        platform_adapter.tool_argv("exposedpath-no-such-tool-xyz", ["--version"])


def test_tool_argv_uses_resolved_executable_and_keeps_argument_order():
    argv = platform_adapter.tool_argv(sys.executable, ["--flag", "value"])
    assert os.path.isabs(argv[0])
    assert argv[1:] == ["--flag", "value"]


# ---------------------------------------------------------------------------
# structured invocation (never a shell)
# ---------------------------------------------------------------------------

def test_run_tool_uses_structured_argv_without_shell(tmp_path):
    """Shell metacharacters and spaces must reach the child process literally."""
    program = "import sys; print(repr(sys.argv[1:]))"
    tricky = "a & b | c > d && e ; f"
    completed = platform_adapter.run_tool(sys.executable, ["-c", program, tricky], timeout=60)
    assert completed.returncode == 0
    assert repr([tricky]) in completed.stdout


def test_run_tool_reports_nonzero_exit_code():
    completed = platform_adapter.run_tool(
        sys.executable, ["-c", "raise SystemExit(3)"], timeout=60,
    )
    assert completed.returncode == 3


def test_query_tool_returns_stripped_stdout():
    out = platform_adapter.query_tool(
        sys.executable, ["-c", "print('  hello  ')"], timeout=60,
    )
    assert out == "hello"


def test_query_tool_fails_closed_on_nonzero_exit():
    with pytest.raises(platform_adapter.ToolExecutionError):
        platform_adapter.query_tool(
            sys.executable, ["-c", "import sys; sys.exit(9)"], timeout=60,
        )


def test_query_tool_fails_closed_when_tool_is_missing():
    with pytest.raises(platform_adapter.ToolUnavailableError):
        platform_adapter.query_tool("exposedpath-no-such-tool-xyz", [], timeout=60)


def test_nvidia_smi_helper_fails_closed_when_tool_is_missing(monkeypatch):
    monkeypatch.setattr(
        platform_adapter, "resolve_tool", lambda *a, **k: None,
    )
    with pytest.raises(platform_adapter.ToolUnavailableError):
        platform_adapter.nvidia_smi(["--query-gpu=driver_version"])


# ---------------------------------------------------------------------------
# isolation invariants for the runner core
# ---------------------------------------------------------------------------

CORE_MODULES = (
    "runner.py",
    "manifest.py",
    "validation.py",
    "results.py",
    "ids.py",
    "nvtx.py",
    "workload.py",
    "cli.py",
    "cross_pass_validator.py",
    "__init__.py",
    "__main__.py",
)


HOST_TOOL_EXECUTABLES = (
    "nvidia-smi", "nvidia-smi.exe",
    "nsys", "nsys.exe",
    "nvcc", "nvcc.exe",
    "powershell", "powershell.exe", "pwsh", "pwsh.exe",
)


def _module_imports_and_literals(path: Path) -> tuple[set[str], list[str]]:
    """Import names and string literals of a module, ignoring comments/docstrings."""
    import ast

    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstring_ids: set[int] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)) and node.body:
            first = node.body[0]
            if (
                isinstance(first, ast.Expr)
                and isinstance(first.value, ast.Constant)
                and isinstance(first.value.value, str)
            ):
                docstring_ids.add(id(first.value))
    imports: set[str] = set()
    literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module.split(".")[0])
        elif (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and id(node) not in docstring_ids
        ):
            literals.append(node.value)
    return imports, literals


def _core_module_paths() -> list[Path]:
    package_dir = Path(platform_adapter.__file__).resolve().parent
    return [package_dir / name for name in CORE_MODULES]


def test_only_adapter_imports_subprocess_in_core_package():
    offenders = []
    for path in _core_module_paths():
        imports, _ = _module_imports_and_literals(path)
        if "subprocess" in imports:
            offenders.append(path.name)
    assert offenders == [], f"core modules must not touch subprocess: {offenders}"


def test_core_modules_do_not_name_host_tools_or_shell_out():
    offenders = []
    for path in _core_module_paths():
        _, literals = _module_imports_and_literals(path)
        for literal in literals:
            if literal.lower() in HOST_TOOL_EXECUTABLES:
                offenders.append(f"{path.name}:{literal}")
            if "shell=True" in literal:
                offenders.append(f"{path.name}:shell=True")
        source = path.read_text(encoding="utf-8")
        if "shell=True" in source:
            offenders.append(f"{path.name}:shell=True(source)")
    assert offenders == [], f"platform specifics must live in the adapter: {offenders}"


# ---------------------------------------------------------------------------
# adapter wiring in the runner core (behaviour preserved)
# ---------------------------------------------------------------------------

def _parity_manifest() -> dict:
    return {
        "experiment_id": "gate7-platform",
        "wmpc_id": "wmpc-0123456789abcdef",
        "run_id": "run-20260921T000000Z-test0001",
        "prompt_tokens_sha256": "a" * 64,
        "fixed_input_tokens": 128,
        "fixed_output_tokens": 8,
        "batch_size": 1,
        "warmup_count": 1,
        "repeat_count": 2,
        "gpu_index": 0,
        "gpu_uuid": "GPU-test-uuid",
        "gpu_pci_bus_id": "00000000:01:00.0",
        "gpu_name": "Test GPU",
        "study_mode": "G1_NATURAL",
        "data_role": "PILOT",
        "run_role": "PILOT",
        "model_id": "test-model",
    }


def _write_parity(tmp_path: Path, manifest_dict: dict) -> dict:
    import json

    manifest_path = tmp_path / "wmpc_manifest.json"
    manifest_path.write_text(json.dumps(manifest_dict), encoding="utf-8")
    output_dir = tmp_path / "pass0"
    runner._write_cross_pass_parity(
        manifest_dict, "pass0", output_dir, manifest_path, manifest_dict["model_id"], "cpu",
    )
    return json.loads((output_dir / "cross_pass_parity.json").read_text(encoding="utf-8"))


def test_runner_parity_uses_adapter_for_driver_version(tmp_path, monkeypatch):
    monkeypatch.setattr(platform_adapter, "nvidia_smi", lambda args, timeout=10: "555.99\n")
    parity = _write_parity(tmp_path, _parity_manifest())
    assert parity["nvidia_driver_version"] == "555.99"


def test_runner_parity_keeps_unknown_when_driver_query_fails(tmp_path, monkeypatch):
    def _boom(args, timeout=10):
        raise platform_adapter.ToolUnavailableError("nvidia-smi not resolvable")

    monkeypatch.setattr(platform_adapter, "nvidia_smi", _boom)
    parity = _write_parity(tmp_path, _parity_manifest())
    assert parity["nvidia_driver_version"] == "unknown"
    assert "nvidia_driver_query_error" not in parity


def test_manifest_driver_version_is_unknown_when_tool_missing(monkeypatch):
    monkeypatch.setattr(platform_adapter, "nvidia_smi", lambda args, timeout=10: _raise())
    assert manifest._get_nvidia_driver() == "unknown"


def test_manifest_git_provenance_is_none_when_tool_missing(monkeypatch):
    monkeypatch.setattr(platform_adapter, "git", lambda args, timeout=5: _raise())
    assert manifest._get_git_commit() is None
    assert manifest._get_git_dirty() is None


def _raise():
    raise platform_adapter.ToolUnavailableError("tool not resolvable")
