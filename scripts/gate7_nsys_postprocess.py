"""Bounded, fail-closed SQLite export of an existing Gate7 Nsight report.

This is Engineering post-processing only. It never runs collection or analysis,
and it never edits the source .nsys-rep.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.gate7_smoke_validation import validate_sqlite


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def wait_for_rep_ready(
    path: Path,
    *,
    timeout_seconds: float = 60,
    poll_interval_seconds: float = 2,
    stable_samples: int = 3,
    expected_sha256: str | None = None,
) -> dict:
    """Require a nonempty, readable REP with stable size/mtime and SHA256."""
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"REP missing: {path}")
    if path.stat().st_size == 0:
        raise ValueError(f"REP empty: {path}")
    if timeout_seconds <= 0 or poll_interval_seconds <= 0 or stable_samples < 1:
        raise ValueError("Invalid REP readiness bounds")

    deadline = time.monotonic() + timeout_seconds
    previous: tuple[int, int] | None = None
    stable = 0
    last_error = "REP not stable"
    while True:
        try:
            before = path.stat()
            if before.st_size <= 0:
                raise ValueError(f"REP became empty: {path}")
            current = (before.st_size, before.st_mtime_ns)
            stable = stable + 1 if current == previous else 1
            previous = current
            if stable >= stable_samples:
                digest = _sha256(path)  # also proves it is readable
                after = path.stat()
                if (after.st_size, after.st_mtime_ns) == current:
                    if expected_sha256 is not None and digest != expected_sha256:
                        raise ValueError("REP SHA256 changed between export attempts")
                    return {
                        "path": str(path), "size": after.st_size,
                        "last_write_time_ns": after.st_mtime_ns,
                        "sha256": digest, "stable_samples": stable,
                    }
                stable = 0
                last_error = "REP changed while hashing"
        except OSError as exc:
            stable = 0
            last_error = f"REP not readable: {exc}"
        if time.monotonic() >= deadline:
            raise TimeoutError(f"REP readiness timeout: {last_error}")
        time.sleep(min(poll_interval_seconds, max(0, deadline - time.monotonic())))


def _persist(report_path: Path, report: dict) -> None:
    interim = report_path.with_name(report_path.name + ".writing")
    interim.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(interim, report_path)


def _export_attempt(
    *,
    number: int,
    nsys_exe: str,
    export_prefix: Sequence[str],
    rep_path: Path,
    rep_sha256: str,
    output_path: Path,
    report_path: Path,
    timeout_seconds: float,
) -> dict:
    argv = [nsys_exe, *export_prefix, "export", "--type", "sqlite", "--output",
            str(output_path), str(rep_path)]
    stdout_path = report_path.with_name(f"nsys_export_attempt{number}.stdout.txt")
    stderr_path = report_path.with_name(f"nsys_export_attempt{number}.stderr.txt")
    attempt = {
        "number": number, "status": "STARTING", "pid": None,
        "terminated_pid": None, "process_exited": False,
        "started_at": _utc_now(), "ended_at": None, "elapsed_seconds": None,
        "argv": argv, "stdout_path": str(stdout_path), "stderr_path": str(stderr_path),
        "timed_out": False, "exit_code": None, "rep_sha256": rep_sha256,
        "output_path": str(output_path), "sqlite_size": 0, "sqlite_sha256": None,
        "validation_issues": [],
    }
    start = time.monotonic()
    try:
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        with stdout_path.open("x", encoding="utf-8") as stdout, stderr_path.open("x", encoding="utf-8") as stderr:
            process = subprocess.Popen(
                argv, cwd=rep_path.parent, stdout=stdout, stderr=stderr,
                shell=False, creationflags=flags,
            )
            attempt["pid"] = process.pid
            try:
                attempt["exit_code"] = process.wait(timeout=timeout_seconds)
                attempt["process_exited"] = True
            except subprocess.TimeoutExpired:
                attempt["timed_out"] = True
                try:
                    process.kill()  # only this recorded child PID, never a name-wide kill
                    attempt["terminated_pid"] = process.pid
                except OSError as exc:
                    # The process can exit between the timed wait and kill.
                    if process.poll() is None:
                        attempt["validation_issues"].append(f"PID termination error: {exc}")
                try:
                    attempt["exit_code"] = process.wait(timeout=15)
                    attempt["process_exited"] = True
                except subprocess.TimeoutExpired:
                    attempt["validation_issues"].append("Exporter did not exit after PID termination")
    except (OSError, ValueError) as exc:
        attempt["validation_issues"].append(f"Exporter launch/termination error: {exc}")
    finally:
        attempt["ended_at"] = _utc_now()
        attempt["elapsed_seconds"] = round(time.monotonic() - start, 3)
        try:
            if output_path.exists():
                attempt["sqlite_size"] = output_path.stat().st_size
                attempt["sqlite_sha256"] = _sha256(output_path)
        except OSError as exc:
            attempt["validation_issues"].append(f"SQLite output metadata unreadable: {exc}")

    if attempt["timed_out"]:
        attempt["validation_issues"].append("Exporter timeout")
    if attempt["exit_code"] != 0:
        attempt["validation_issues"].append(f"Exporter exit code {attempt['exit_code']}")
    if not attempt["process_exited"]:
        attempt["validation_issues"].append("Exporter exit not confirmed")
    if not attempt["validation_issues"]:
        try:
            attempt["validation_issues"] = validate_sqlite(output_path)
        except OSError as exc:
            attempt["validation_issues"].append(f"SQLite validation I/O error: {exc}")
    attempt["status"] = "PASS" if not attempt["validation_issues"] else "BLOCKED"
    return attempt


def run_postprocess(
    *,
    nsys_exe: str,
    rep_path: Path,
    canonical_path: Path,
    report_path: Path,
    export_prefix: Sequence[str] = (),
    export_timeout_seconds: float = 180,
    readiness_timeout_seconds: float = 60,
    retry_readiness_timeout_seconds: float = 20,
    poll_interval_seconds: float = 2,
    stable_samples: int = 3,
    max_attempts: int = 2,
) -> dict:
    """Export at most twice; only a validated attempt may become canonical."""
    rep_path = Path(rep_path).resolve()
    canonical_path = Path(canonical_path).resolve()
    report_path = Path(report_path).resolve()
    if type(max_attempts) is not int or max_attempts not in (1, 2):
        raise ValueError('max_attempts must be 1 or 2')
    attempt_paths = [canonical_path.with_name(f"{canonical_path.stem}.export_attempt{i}.sqlite")
                     for i in range(1, max_attempts+1)]
    report = {
        "status": "BLOCKED_BY_NSYS", "error": None, "rep_path": str(rep_path),
        "rep_sha256": None, "readiness": None, "retry_readiness": None,
        "export_timeout_seconds": export_timeout_seconds,
        "readiness_timeout_seconds": readiness_timeout_seconds,
        "retry_readiness_timeout_seconds": retry_readiness_timeout_seconds,
        "poll_interval_seconds": poll_interval_seconds,
        "stable_samples_required": stable_samples,
        "attempt_count": 0, "attempts": [], "successful_attempt": None,
        "canonical_sqlite_path": str(canonical_path),
        "canonical_sqlite_sha256": None, "analyzer_allowed": False,
    }
    if report_path.exists():
        raise FileExistsError(f"Post-processing report already exists: {report_path}")
    try:
        if export_timeout_seconds <= 0:
            raise ValueError("Export timeout must be positive")
        if canonical_path.exists():
            raise ValueError(f"Canonical SQLite already exists: {canonical_path}")
        for attempt_path in attempt_paths:
            if attempt_path.exists():
                raise ValueError(f"Export attempt output already exists: {attempt_path}")
        readiness = wait_for_rep_ready(
            rep_path, timeout_seconds=readiness_timeout_seconds,
            poll_interval_seconds=poll_interval_seconds, stable_samples=stable_samples,
        )
        report["readiness"] = readiness
        report["rep_sha256"] = readiness["sha256"]
        _persist(report_path, report)

        for number, attempt_path in enumerate(attempt_paths, 1):
            if number == 2:
                report["retry_readiness"] = wait_for_rep_ready(
                    rep_path, timeout_seconds=retry_readiness_timeout_seconds,
                    poll_interval_seconds=poll_interval_seconds, stable_samples=stable_samples,
                    expected_sha256=report["rep_sha256"],
                )
                _persist(report_path, report)
            attempt = _export_attempt(
                number=number, nsys_exe=nsys_exe, export_prefix=export_prefix,
                rep_path=rep_path, rep_sha256=report["rep_sha256"],
                output_path=attempt_path, report_path=report_path,
                timeout_seconds=export_timeout_seconds,
            )
            report["attempts"].append(attempt)
            report["attempt_count"] = number
            _persist(report_path, report)
            if not attempt["process_exited"]:
                raise RuntimeError("Exporter exit not confirmed; retry forbidden")
            if _sha256(rep_path) != report["rep_sha256"]:
                raise ValueError("REP SHA256 changed between export attempts")
            if attempt["status"] != "PASS":
                continue
            # Same-directory hard link is atomic and refuses an existing target
            # on both Windows and POSIX. Keep the attempt as incident provenance
            # until the canonical alias has passed its own hash/schema checks.
            os.link(attempt_path, canonical_path)
            try:
                canonical_sha256 = _sha256(canonical_path)
                if canonical_sha256 != attempt["sqlite_sha256"]:
                    raise ValueError("Canonical SQLite SHA256 differs from successful attempt")
                issues = validate_sqlite(canonical_path)
                if issues:
                    raise ValueError(f"Canonical SQLite validation failed: {issues}")
            except (OSError, ValueError):
                if canonical_path.samefile(attempt_path):
                    canonical_path.unlink()
                raise
            report["successful_attempt"] = number
            report["canonical_sqlite_sha256"] = canonical_sha256
            report["status"] = "PASS"
            report["analyzer_allowed"] = True
            break
        if report["status"] != "PASS":
            raise RuntimeError("All bounded SQLite export attempts failed")
    except (OSError, ValueError, TimeoutError, RuntimeError) as exc:
        report["error"] = str(exc)
    _persist(report_path, report)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--nsys", required=True)
    parser.add_argument("--rep", type=Path, required=True)
    parser.add_argument("--canonical-sqlite", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument('--max-attempts',type=int,choices=(1,2),default=2)
    args = parser.parse_args()
    report = run_postprocess(
        nsys_exe=args.nsys, rep_path=args.rep,
        canonical_path=args.canonical_sqlite, report_path=args.report, max_attempts=args.max_attempts,
    )
    print(json.dumps({"status": report["status"], "attempt_count": report["attempt_count"],
                      "successful_attempt": report["successful_attempt"], "error": report["error"]}))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
