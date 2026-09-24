"""Platform adapter: the single boundary for platform-specific behaviour.

Runner and manifest core must stay platform agnostic. Everything that depends
on the host platform lives here:

  * platform identity and executable naming (``.exe`` vs. suffix-less);
  * host-tool resolution (PATH lookup, platform default install locations);
  * structured external-process invocation.

Contract (EP-G7-10):

  * No shell is ever used. Every external call is a structured argv list with
    ``shell=False``; arguments containing spaces or shell metacharacters reach
    the child process literally.
  * A tool that cannot be resolved fails closed with ``ToolUnavailableError``.
    The adapter never substitutes a default value (no zero / ``unknown`` /
    empty-string fallback); the *caller* decides how to record the failure.
  * A tool that exits non-zero fails closed with ``ToolExecutionError`` when
    queried; raw invocation via ``run_tool`` still returns the completed
    process unchanged.
  * Inside the ``exposedpath`` package, only this module imports ``subprocess``.

Platform scope note: the currently declared target stack is Windows. Linux
support is expressed here as naming/suffix rules and default tool locations
only; it is not yet a validated platform for ExposedPath.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Mapping, Optional, Sequence

__all__ = [
    "KNOWN_PLATFORMS",
    "PLATFORM_LINUX",
    "PLATFORM_MACOS",
    "PLATFORM_UNKNOWN",
    "PLATFORM_WINDOWS",
    "TOOL_GIT",
    "TOOL_NVIDIA_SMI",
    "ToolExecutionError",
    "ToolUnavailableError",
    "default_tool_locations",
    "executable_suffix",
    "git",
    "is_windows",
    "nvidia_smi",
    "platform_id",
    "query_tool",
    "resolve_tool",
    "run_tool",
    "tool_argv",
    "tool_candidates",
]

PLATFORM_WINDOWS = "windows"
PLATFORM_LINUX = "linux"
PLATFORM_MACOS = "macos"
PLATFORM_UNKNOWN = "unknown"

KNOWN_PLATFORMS = (PLATFORM_WINDOWS, PLATFORM_LINUX, PLATFORM_MACOS, PLATFORM_UNKNOWN)

# Host tools referenced by the runner core. The core names these constants
# instead of spelling out platform executables.
TOOL_NVIDIA_SMI = "nvidia-smi"
TOOL_GIT = "git"


class ToolUnavailableError(RuntimeError):
    """Raised when a required host tool cannot be resolved on this platform."""


class ToolExecutionError(RuntimeError):
    """Raised when a host tool was resolved but failed (non-zero exit)."""


def platform_id() -> str:
    """Return the normalised platform identity for this interpreter."""
    if os.name == "nt" or sys.platform.startswith("win"):
        return PLATFORM_WINDOWS
    if sys.platform.startswith("linux"):
        return PLATFORM_LINUX
    if sys.platform == "darwin":
        return PLATFORM_MACOS
    return PLATFORM_UNKNOWN


def is_windows() -> bool:
    return platform_id() == PLATFORM_WINDOWS


def executable_suffix() -> str:
    """Platform executable suffix (``.exe`` on Windows, empty elsewhere)."""
    return ".exe" if is_windows() else ""


def tool_candidates(name: str) -> tuple[str, ...]:
    """Candidate executable names for ``name`` on this platform."""
    suffix = executable_suffix()
    if suffix and not name.lower().endswith(suffix):
        return (name, name + suffix)
    return (name,)


def default_tool_locations(name: str) -> tuple[str, ...]:
    """Platform default install locations, used only after PATH lookup fails."""
    if name == TOOL_NVIDIA_SMI:
        if is_windows():
            program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
            return (
                str(Path(program_files) / "NVIDIA Corporation" / "NVSMI" / "nvidia-smi.exe"),
                str(Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32" / "nvidia-smi.exe"),
            )
        return ("/usr/bin/nvidia-smi", "/usr/local/bin/nvidia-smi")
    return ()


def _existing_file(candidate: str) -> Optional[str]:
    try:
        path = Path(candidate)
        if path.is_file():
            return str(path.resolve())
    except OSError:
        return None
    return None


def resolve_tool(
    name: str,
    *,
    extra_candidates: Iterable[str] = (),
    env: Optional[Mapping[str, str]] = None,
) -> Optional[str]:
    """Resolve ``name`` to an absolute path, or return ``None``.

    Resolution order: explicit path -> PATH lookup -> caller candidates ->
    platform default locations. No shell is involved.
    """
    if not name:
        return None

    direct = _existing_file(name)
    if direct is not None:
        return direct

    which_env = dict(env) if env is not None else None
    for candidate in tool_candidates(name):
        found = shutil.which(candidate, path=(which_env or {}).get("PATH") if which_env else None)
        resolved = _existing_file(found) if found else None
        if resolved is not None:
            return resolved

    for candidate in extra_candidates:
        resolved = _existing_file(candidate)
        if resolved is not None:
            return resolved

    for candidate in default_tool_locations(name):
        resolved = _existing_file(candidate)
        if resolved is not None:
            return resolved

    return None


def tool_argv(
    name: str,
    args: Sequence[str] = (),
    *,
    extra_candidates: Iterable[str] = (),
    env: Optional[Mapping[str, str]] = None,
) -> list[str]:
    """Build a structured argv list for ``name``; fail closed if unresolvable."""
    resolved = resolve_tool(name, extra_candidates=extra_candidates, env=env)
    if resolved is None:
        raise ToolUnavailableError(
            f"host tool not resolvable on platform '{platform_id()}': {name}"
        )
    return [resolved, *[str(a) for a in args]]


def run_tool(
    name: str,
    args: Sequence[str] = (),
    *,
    timeout: float = 10,
    text: bool = True,
    stderr=None,
    env: Optional[Mapping[str, str]] = None,
    cwd=None,
    extra_candidates: Iterable[str] = (),
) -> subprocess.CompletedProcess:
    """Run ``name`` with structured arguments (never through a shell).

    Only resolution failures raise; the completed process (including a
    non-zero exit code) is returned unchanged so the caller can record it.
    """
    argv = tool_argv(name, args, extra_candidates=extra_candidates, env=env)
    return subprocess.run(
        argv,
        stdout=subprocess.PIPE,
        text=text,
        timeout=timeout,
        stderr=subprocess.PIPE if stderr is None else stderr,
        env=dict(env) if env is not None else None,
        cwd=str(cwd) if cwd is not None else None,
        shell=False,
        check=False,
    )


def query_tool(
    name: str,
    args: Sequence[str] = (),
    *,
    timeout: float = 10,
    stderr=None,
    env: Optional[Mapping[str, str]] = None,
    extra_candidates: Iterable[str] = (),
) -> str:
    """Run ``name`` and return stripped stdout; fail closed on any failure."""
    completed = run_tool(
        name,
        args,
        timeout=timeout,
        stderr=stderr,
        env=env,
        extra_candidates=extra_candidates,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or "").strip()
        raise ToolExecutionError(
            f"{name} exited with code {completed.returncode}"
            + (f": {detail}" if detail else "")
        )
    return (completed.stdout or "").strip()


def nvidia_smi(args: Sequence[str] = (), *, timeout: float = 10) -> str:
    """Structured ``nvidia-smi`` query through the adapter."""
    return query_tool(TOOL_NVIDIA_SMI, args, timeout=timeout)


def git(args: Sequence[str] = (), *, timeout: float = 5) -> str:
    """Structured ``git`` query; retain stderr to explain failed provenance."""
    return query_tool(TOOL_GIT, args, timeout=timeout)
