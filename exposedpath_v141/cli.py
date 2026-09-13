"""ExposedPath v1.4.1 analyzer 命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .contract import ContractValidationError, load_contract_bundle
from .canonical_raw import (
    CanonicalRawSchemaError,
    convert_sqlite_to_canonical,
)
from .observation import inspect_sqlite, write_report_new
from .q0_oracle import OracleValidationError, load_oracle_bundle
from .s_bundle import SBundleError, analyze_canonical_to_s
from .ab_bundle import ABBundleError, analyze_ab


def _configure_stdio() -> None:
    if sys.platform != "win32":
        return
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ExposedPath v1.4.1 并行 analyzer（当前提供合同与 observation gate）"
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

    convert_parser = subparsers.add_parser(
        "convert-sqlite", help="只读转换 Nsight SQLite 为 Canonical Raw bundle"
    )
    convert_parser.add_argument("--sqlite", required=True, type=Path)
    convert_parser.add_argument("--output-dir", required=True, type=Path)
    convert_parser.add_argument(
        "--data-role",
        required=True,
        choices=("Prototype", "Engineering", "Pilot", "Formal"),
    )
    convert_parser.add_argument("--raw-sha256")
    convert_parser.add_argument("--collector-version")
    convert_parser.add_argument("--source-manifest", type=Path)

    subparsers.add_parser(
        "validate-contract", help="校验 Measurement Contract 包内部一致性"
    )
    subparsers.add_parser(
        "validate-q0-oracle", help="校验 Q0 独立标准答案的设计与覆盖"
    )
    s_parser = subparsers.add_parser(
        "analyze-s", help="只读分析 Canonical Raw 并生成 S 层 bundle"
    )
    s_parser.add_argument("--canonical-manifest", required=True, type=Path)
    s_parser.add_argument("--output-dir", required=True, type=Path)
    ab_parser = subparsers.add_parser(
        "analyze-ab", help="只读投影 Canonical Raw + S 为版本化 A/B bundle"
    )
    ab_parser.add_argument("--canonical-manifest", required=True, type=Path)
    ab_parser.add_argument("--s-manifest", required=True, type=Path)
    ab_parser.add_argument("--output-dir", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    args = _build_parser().parse_args(argv)

    if args.command == "validate-contract":
        try:
            bundle = load_contract_bundle()
        except ContractValidationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        contract = bundle["contract"]
        registry = bundle["registry"]
        test_map = bundle["test_map"]
        rule_ids = {rule["rule_id"] for rule in contract["rules"]}
        mapped_ids = {
            rule_id for case in test_map["cases"] for rule_id in case["rule_ids"]
        }
        covered = len(rule_ids & mapped_ids)
        total = len(rule_ids)
        coverage = 100 if total and covered == total else round(covered / total * 100)
        print(f"contract_version: {contract['contract_version']}")
        print(f"registry_version: {registry['registry_version']}")
        print(f"registry_rules: {len(registry['rules'])}")
        print(f"validation_cases: {len(test_map['cases'])}")
        print(f"rule_coverage: {covered}/{total} ({coverage}%)")
        print("gate_scope: CONTRACT_INTERNAL_CONSISTENCY_ONLY")
        print("verdict: PASS")
        return 0

    if args.command == "validate-q0-oracle":
        try:
            bundle = load_oracle_bundle()
            from scripts.verify_q0_oracle_independence import check_source

            oracle_path = Path(__file__).resolve().with_name("q0_oracle.py")
            independence_problems = check_source(oracle_path.read_text(encoding="utf-8"))
            if independence_problems:
                raise OracleValidationError("；".join(independence_problems))
        except (OSError, json.JSONDecodeError, OracleValidationError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        cases = bundle["cases"]
        class_counts: dict[str, int] = {}
        for case in cases:
            case_class = case["case_class"]
            class_counts[case_class] = class_counts.get(case_class, 0) + 1
        features = {feature for case in cases for feature in case["features"]}
        required = sum(bool(case["required_for_q0"]) for case in cases)
        print(f"oracle_version: {bundle['oracle_version']}")
        print(f"cases_total: {len(cases)}")
        print(f"required_cases: {required}")
        print(
            "class_counts: "
            + ", ".join(f"{name}={class_counts[name]}" for name in sorted(class_counts))
        )
        print(f"feature_coverage: {len(features)}")
        print("independence_scope: STATIC_EXPECTED_AND_INTERVAL_ARITHMETIC_ONLY")
        print("q0_execution_status: NOT_RUN")
        print("verdict: DESIGN_ONLY_PASS")
        return 0

    if args.command == "convert-sqlite":
        try:
            manifest_path = convert_sqlite_to_canonical(
                sqlite_path=args.sqlite,
                output_dir=args.output_dir,
                data_role=args.data_role,
                raw_sha256=args.raw_sha256,
                collector_version=args.collector_version,
                source_manifest=args.source_manifest,
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (
            CanonicalRawSchemaError,
            FileExistsError,
            OSError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1

        observation_status = manifest["observation_validity"]["status"]
        identity_status = manifest["identity"]["status"]
        print(f"canonical_manifest: {manifest_path}")
        print(f"observation_validity: {observation_status}")
        print(f"identity_validity: {identity_status}")
        print(f"q0_status: {manifest['research_eligibility']['q0_status']}")
        return 2 if "ambiguous" in {observation_status, identity_status.lower()} else 0

    if args.command == "analyze-s":
        try:
            manifest_path = analyze_canonical_to_s(
                args.canonical_manifest, args.output_dir
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (SBundleError, FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        summary = manifest["summary"]
        print(f"s_manifest: {manifest_path}")
        print(f"s_schema_version: {manifest['schema_version']}")
        print(f"physical_sync_count: {summary['physical_sync_count']}")
        print(f"valid_nonempty_count: {summary['valid_nonempty_count']}")
        print(f"valid_empty_count: {summary['valid_empty_count']}")
        print(f"ambiguous_count: {summary['ambiguous_count']}")
        print(f"invalid_count: {summary['invalid_count']}")
        print(f"q0_status: {manifest['research_eligibility']['q0_status']}")
        if summary["invalid_count"]:
            return 3
        if summary["ambiguous_count"] or manifest["input_validity"]["status"] != "VALID":
            return 2
        return 0

    if args.command == "analyze-ab":
        try:
            manifest_path = analyze_ab(
                args.canonical_manifest, args.s_manifest, args.output_dir
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (ABBundleError, FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        summary = manifest["summary"]
        print(f"ab_manifest: {manifest_path}")
        print(f"ab_schema_version: {manifest['schema_version']}")
        print(f"window_count: {summary['window_count']}")
        print(f"physical_sync_count: {summary['physical_sync_count']}")
        print(f"quality_status: {manifest['quality']['status']}")
        print(f"q0_status: {manifest['research_eligibility']['q0_status']}")
        if summary["b_invalid_count"]:
            return 3
        if summary["b_ambiguous_count"] or manifest["quality"]["status"] != "VALID":
            return 2
        return 0

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
