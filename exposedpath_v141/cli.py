"""ExposedPath v1.4.1 analyzer 命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .observation import inspect_sqlite, write_report_new


def _configure_stdio() -> None:
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ExposedPath v1.4.1 并行 analyzer（当前仅做 observation gate）"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    inspect_parser = subparsers.add_parser(
        "inspect-sqlite", help="只读检查 Nsight SQLite 的 observation contract"
    )
    inspect_parser.add_argument("--sqlite", required=True, type=Path)
    inspect_parser.add_argument("--output-dir", required=True, type=Path)
    inspect_parser.add_argument(
        "--data-role",
        required=True,
        choices=("Prototype", "Engineering", "Pilot", "Formal"),
    )
    inspect_parser.add_argument("--raw-sha256")
    inspect_parser.add_argument("--collector-version")
    inspect_parser.add_argument("--source-manifest", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    args = _build_parser().parse_args(argv)
    if args.command != "inspect-sqlite":
        return 1

    try:
        report = inspect_sqlite(
            sqlite_path=args.sqlite,
            data_role=args.data_role,
            raw_sha256=args.raw_sha256,
            collector_version=args.collector_version,
            source_manifest=args.source_manifest,
        )
        output_path = write_report_new(args.output_dir, report)
    except (OSError, ValueError, RuntimeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    status = report["validity"]["status"]
    print(f"observation_report: {output_path}")
    print(f"validity: {status}")
    for issue in report["validity"]["issues"]:
        print(f"  - {issue['level']}: {issue['code']}")
    return {"valid": 0, "ambiguous": 2, "invalid": 3}[status]
