"""Portability guard for the Gate 7 smoke target interpreter.

The Windows / RTX 4090 smoke host may run an older CPython than the development
box. PEP 701 (Python 3.12) relaxed f-string tokenisation: before it, an f-string
expression part could not contain a backslash, and the f-string delimiter quote
terminated the literal even inside an expression part.

``analysis/exposed_accounting.py`` relied on both relaxations, so it failed to
compile on the smoke host with ``SyntaxError: unterminated triple-quoted string
literal``, which also broke ``scripts/run_server_smoke_test.ps1`` STEP 6 because
that step executes the module directly.

``dist/`` is intentionally out of scope: it is a frozen deployment payload
pinned by ``dist/exposedpath_v3_pilot_deploy.sha256`` and must not be rewritten.

These tests are pure CPU checks: no GPU, no nsys, no Q0 collection.
"""

from __future__ import annotations

import io
import re
import tokenize
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_DIRS = ("analysis", "exposedpath", "exposedpath_v141", "q0", "scripts", "tests")


def _scanned_sources():
    for directory in SCAN_DIRS:
        for path in sorted((REPO_ROOT / directory).rglob("*.py")):
            yield path


def _line_offsets(source: str):
    offsets = [0]
    for line in source.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))
    return lambda position: offsets[position[0] - 1] + position[1]


def _pep701_only_fstring_reasons(path: Path):
    """Return ``(line, reason)`` for every f-string needing Python 3.12 syntax."""
    source = path.read_text(encoding="utf-8")
    to_index = _line_offsets(source)
    reasons = []
    open_fstrings = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type == tokenize.FSTRING_START:
            open_fstrings.append(token)
            continue
        if token.type != tokenize.FSTRING_END or not open_fstrings:
            continue
        start = open_fstrings.pop()
        literal = source[to_index(start.start):to_index(token.end)]
        prefix = re.match(r"[A-Za-z]*", literal).group(0)
        body = literal[len(prefix):]
        quote = body[0]
        delimiter = quote * 3 if body.startswith(quote * 3) else quote
        inner = body[len(delimiter):]
        if inner.endswith(delimiter):
            inner = inner[:-len(delimiter)]
        depth = 0
        index = 0
        while index < len(inner):
            if inner.startswith(quote * 2, index):  # ``{{`` / ``}}`` or an escape
                index += 2
                continue
            char = inner[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth = max(0, depth - 1)
            elif depth > 0 and char == "\\":
                reasons.append((start.start[0], "backslash inside f-string expression"))
                break
            elif depth > 0 and len(delimiter) == 1 and char == quote:
                reasons.append((start.start[0], "f-string delimiter quote inside expression"))
                break
            index += 1
    return reasons


def test_scanned_sources_compile_on_the_host_interpreter():
    """On a pre-3.12 interpreter this is the check that catches the defect."""
    failures = []
    for path in _scanned_sources():
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except SyntaxError as exc:
            failures.append(f"{path.relative_to(REPO_ROOT)}:{exc.lineno}: {exc.msg}")
    assert failures == [], "uncompilable sources: " + "; ".join(failures)


@pytest.mark.skipif(
    not hasattr(tokenize, "FSTRING_START"),
    reason="pre-3.12 interpreters already reject these f-strings at compile time",
)
def test_sources_avoid_pep701_only_fstrings():
    offenders = []
    for path in _scanned_sources():
        for line, reason in _pep701_only_fstring_reasons(path):
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{line}: {reason}")
    assert offenders == [], "PEP 701 only f-strings: " + "; ".join(offenders)


def test_smoke_analyzer_entry_point_is_compilable():
    """``run_server_smoke_test.ps1`` STEP 6 executes this module directly."""
    path = REPO_ROOT / "analysis" / "exposed_accounting.py"
    compile(path.read_text(encoding="utf-8"), str(path), "exec")
