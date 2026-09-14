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
from .q0_execution import Q0ExecutionError, compile_q0_microbench, prepare_q0_run
from .q0_collection import Q0CollectionError, execute_q0_case
from .q0_faults import Q0FaultError, apply_q0_fault
from .q0_real import Q0RealObservedError, run_real_q0_case
from .q0_gate import Q0GateError, write_q0_gate
from .q0_synthetic import run_synthetic_q0
from .s_bundle import SBundleError, analyze_canonical_to_s
from .ab_bundle import ABBundleError, analyze_ab
from .derived import DerivedBundleError, derive_exposure


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
    build_q0_parser = subparsers.add_parser(
        "build-q0-microbench", help="只编译 Gate 6 Q0 CUDA 微程序，不执行 GPU"
    )
    build_q0_parser.add_argument("--nvcc", required=True, type=Path)
    build_q0_parser.add_argument("--output", required=True, type=Path)
    build_q0_parser.add_argument(
        "--platform", required=True, choices=("windows", "linux")
    )
    prepare_q0_parser = subparsers.add_parser(
        "prepare-q0-run", help="生成 Gate 6 Q0 dry-run，不执行 GPU 或 Nsight"
    )
    prepare_q0_parser.add_argument("--output-dir", required=True, type=Path)
    prepare_q0_parser.add_argument("--binary", required=True, type=Path)
    prepare_q0_parser.add_argument("--nsys", required=True, type=Path)
    prepare_q0_parser.add_argument(
        "--platform", required=True, choices=("windows", "linux")
    )
    prepare_q0_parser.add_argument("--run-id", required=True)
    prepare_q0_parser.add_argument("--cuda-visible-device", required=True)
    execute_q0_parser = subparsers.add_parser(
        "execute-q0-case", help="按预备 manifest 采集一个真实 Q0 native case"
    )
    execute_q0_parser.add_argument("--run-manifest", required=True, type=Path)
    execute_q0_parser.add_argument("--case", required=True)
    fault_q0_parser = subparsers.add_parser(
        "apply-q0-fault", help="对 Canonical 派生副本应用预定义 Q0 故障"
    )
    fault_q0_parser.add_argument("--canonical-manifest", required=True, type=Path)
    fault_q0_parser.add_argument("--case", required=True)
    fault_q0_parser.add_argument("--output-dir", required=True, type=Path)
    real_q0_parser = subparsers.add_parser(
        "evaluate-q0-real-case", help="将一个真实 case 的 Canonical/S/A/B 与 oracle 独立对照"
    )
    real_q0_parser.add_argument("--case", required=True)
    real_q0_parser.add_argument("--canonical-manifest", required=True, type=Path)
    real_q0_parser.add_argument("--s-manifest", required=True, type=Path)
    real_q0_parser.add_argument("--ab-manifest", required=True, type=Path)
    real_q0_parser.add_argument("--collection-receipt", required=True, type=Path)
    real_q0_parser.add_argument("--output-dir", required=True, type=Path)
    gate_q0_parser = subparsers.add_parser(
        "aggregate-q0-gate", help="按 execution strategy 聚合全部必需 Q0 case"
    )
    gate_q0_parser.add_argument("--real-evidence-dir", required=True, type=Path)
    gate_q0_parser.add_argument("--synthetic-report", required=True, type=Path)
    gate_q0_parser.add_argument("--output-dir", required=True, type=Path)
    synthetic_q0_parser = subparsers.add_parser(
        "run-q0-synthetic", help="运行合成 Canonical 的 S/A/B 回归，不执行真实 Q0"
    )
    synthetic_q0_parser.add_argument("--output-dir", required=True, type=Path)
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
    derived_parser = subparsers.add_parser(
        "derive-exposure", help="仅从已验证 A/B bundle 派生 D 与 Exposure Signature"
    )
    derived_parser.add_argument("--ab-manifest", required=True, type=Path)
    derived_parser.add_argument("--output-dir", required=True, type=Path)
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

    if args.command == "build-q0-microbench":
        try:
            output_path = compile_q0_microbench(
                args.nvcc, args.output, platform=args.platform
            )
        except (OSError, Q0ExecutionError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"q0_binary: {output_path}")
        print("compile_status: PASS")
        print("q0_execution_status: NOT_RUN")
        return 0

    if args.command == "prepare-q0-run":
        try:
            manifest_path = prepare_q0_run(
                args.output_dir,
                args.binary,
                args.nsys,
                platform=args.platform,
                run_id=args.run_id,
                cuda_visible_device=args.cuda_visible_device,
            )
        except (OSError, Q0ExecutionError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"q0_run_manifest: {manifest_path}")
        print("run_status: PREPARED_NOT_EXECUTED")
        print("q0_execution_status: NOT_RUN")
        print("verdict: DRY_RUN_ONLY")
        return 0

    if args.command == "run-q0-synthetic":
        try:
            report_path = run_synthetic_q0(args.output_dir)
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"q0_synthetic_report: {report_path}")
        print(f"evidence_scope: {report['evidence_scope']}")
        print(f"q0_execution_status: {report['q0_status']}")
        print(f"verdict: {report['verdict']}")
        return 0 if report["verdict"] == "SYNTHETIC_PASS" else 1

    if args.command == "execute-q0-case":
        try:
            receipt_path = execute_q0_case(args.run_manifest, args.case)
        except (OSError, Q0CollectionError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"collection_receipt: {receipt_path}")
        print("collection_status: COLLECTED")
        print("q0_execution_status: NOT_RUN")
        return 0

    if args.command == "apply-q0-fault":
        try:
            manifest_path = apply_q0_fault(
                args.canonical_manifest, args.case, args.output_dir
            )
        except (OSError, Q0FaultError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"fault_canonical_manifest: {manifest_path}")
        print("fault_status: APPLIED")
        print("q0_execution_status: NOT_RUN")
        return 0

    if args.command == "evaluate-q0-real-case":
        try:
            evidence_path = run_real_q0_case(
                args.case,
                args.canonical_manifest,
                args.s_manifest,
                args.ab_manifest,
                args.collection_receipt,
                args.output_dir,
            )
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, Q0RealObservedError, FileExistsError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"q0_real_evidence: {evidence_path}")
        print(f"case_id: {evidence['case_id']}")
        print(f"verdict: {evidence['verdict']}")
        print("q0_execution_status: NOT_RUN")
        return 0 if evidence["verdict"] == "REAL_CASE_PASS" else 3

    if args.command == "aggregate-q0-gate":
        try:
            evidence_paths = sorted(args.real_evidence_dir.rglob("q0_real_evidence.json"))
            report_path = write_q0_gate(
                evidence_paths, args.synthetic_report, args.output_dir
            )
            report = json.loads(report_path.read_text(encoding="utf-8"))
        except (OSError, Q0GateError, FileExistsError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(f"q0_gate_report: {report_path}")
        print(f"required_cases: {report['summary']['required_case_count']}")
        print(f"passed_cases: {report['summary']['passed_case_count']}")
        print(f"q0_status: {report['q0_status']}")
        print(f"verdict: {report['verdict']}")
        return 0 if report["verdict"] == "PASS" else 3

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

    if args.command == "derive-exposure":
        try:
            manifest_path = derive_exposure(args.ab_manifest, args.output_dir)
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (DerivedBundleError, FileExistsError, OSError, ValueError, json.JSONDecodeError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        summary = manifest["summary"]
        print(f"derived_manifest: {manifest_path}")
        print(f"derived_schema_version: {manifest['schema_version']}")
        print(f"d_window_count: {summary['d_window_count']}")
        print(f"exposure_signature_count: {summary['exposure_signature_count']}")
        print(f"q0_status: {manifest['research_eligibility']['q0_status']}")
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
