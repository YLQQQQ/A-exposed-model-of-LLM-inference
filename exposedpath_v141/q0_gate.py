"""聚合策略匹配的真实/合成 Q0 证据，产生唯一 Gate 6 判定。"""

from __future__ import annotations

from collections.abc import Sequence
import hashlib
import json
from pathlib import Path
import tempfile
from typing import Any

from .q0_execution import load_q0_execution_manifest


class Q0GateError(ValueError):
    """Q0 聚合输入损坏或相互冲突。"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _load(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise Q0GateError(f"无法读取 Q0 证据: {path}") from exc
    if not isinstance(value, dict):
        raise Q0GateError(f"Q0 证据必须是对象: {path}")
    return value


def aggregate_q0_evidence(
    real_evidence_paths: Sequence[Path], synthetic_report_path: Path
) -> dict[str, Any]:
    """严格要求 native/fault 走真实证据，synthetic-only 只走合成证据。"""

    execution = load_q0_execution_manifest()
    expected = {case["case_id"]: case for case in execution["cases"] if case["required_for_q0"]}
    real: dict[str, dict[str, Any]] = {}
    global_mismatches: list[str] = []
    run_ids: set[str] = set()
    environments: set[str] = set()
    for raw_path in real_evidence_paths:
        path = Path(raw_path).resolve()
        item = _load(path)
        case_id = item.get("case_id")
        if item.get("schema_version") != "exposedpath-q0-real-evidence/0.2.0":
            global_mismatches.append(f"真实 evidence schema 非法: {path}")
            continue
        if not isinstance(case_id, str) or case_id in real:
            global_mismatches.append(f"真实 case identity 缺失或重复: {case_id}")
            continue
        report_info = item.get("report", {})
        report_path = path.parent / str(report_info.get("name", ""))
        if not report_path.is_file() or _sha256(report_path) != report_info.get("sha256"):
            global_mismatches.append(f"{case_id} report 缺失或哈希错误")
            continue
        report = _load(report_path)
        case_reports = report.get("cases", [])
        if (
            item.get("verdict") != "REAL_CASE_PASS"
            or report.get("verdict") != "REAL_CASE_PASS"
            or report.get("evidence_scope") != "REAL_CASE_ONLY"
            or report.get("q0_status") != "NOT_RUN"
            or len(case_reports) != 1
            or case_reports[0].get("case_id") != case_id
            or case_reports[0].get("status") != "PASS"
        ):
            global_mismatches.append(f"{case_id} 不是合格 REAL_CASE_PASS")
            continue
        real[case_id] = item
        run_ids.add(str(item.get("run_id")))
        environments.add(json.dumps(item.get("environment"), sort_keys=True))

    synthetic_path = Path(synthetic_report_path).resolve()
    synthetic = _load(synthetic_path)
    synthetic_pass = (
        synthetic.get("verdict") == "SYNTHETIC_PASS"
        and synthetic.get("evidence_scope") == "SYNTHETIC_ONLY"
        and synthetic.get("q0_status") == "NOT_RUN"
    )
    if not synthetic_pass:
        global_mismatches.append("合成回归不是 SYNTHETIC_PASS")
    synthetic_cases = {
        case.get("case_id"): case
        for case in synthetic.get("cases", [])
        if isinstance(case, dict)
    }

    case_reports = []
    for case_id, spec in expected.items():
        strategy = spec["execution_strategy"]
        if strategy == "SYNTHETIC_CANONICAL":
            evidence_kind = "SYNTHETIC_CANONICAL"
            passed = synthetic_pass and synthetic_cases.get(case_id, {}).get("status") == "PASS"
        else:
            evidence_kind = "REAL_CONTROLLED_TRACE"
            passed = case_id in real
        case_reports.append({
            "case_id": case_id,
            "execution_strategy": strategy,
            "evidence_kind": evidence_kind,
            "status": "PASS" if passed else "FAIL",
        })
    if len(run_ids) > 1:
        global_mismatches.append(f"真实证据混用了多个 run_id: {sorted(run_ids)}")
    if len(environments) > 1:
        global_mismatches.append("真实证据混用了不同 GPU/driver/CUDA/Nsight/OS 环境")
    failed = sum(case["status"] == "FAIL" for case in case_reports)
    verdict = "PASS" if failed == 0 and not global_mismatches else "FAIL"
    return {
        "schema_version": "exposedpath-q0-gate/0.2.0",
        "gate": "Gate 6",
        "verdict": verdict,
        "q0_status": verdict,
        "data_role": "Engineering",
        "formal_evidence": False,
        "evidence_scope": "Q0_QUALIFICATION_ONLY",
        "run_id": next(iter(run_ids)) if len(run_ids) == 1 else None,
        "global_mismatches": global_mismatches,
        "summary": {"required_case_count": len(case_reports), "passed_case_count": len(case_reports) - failed, "failed_case_count": failed},
        "cases": case_reports,
    }


def write_q0_gate(
    real_evidence_paths: Sequence[Path], synthetic_report_path: Path, output_dir: Path
) -> Path:
    output = Path(output_dir).resolve()
    if output.exists():
        raise FileExistsError(f"拒绝覆盖 Q0 gate 输出: {output}")
    report = aggregate_q0_evidence(real_evidence_paths, synthetic_report_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        path = staging / "q0_gate_report.json"
        path.write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        staging.replace(output)
        return output / path.name
    except Exception:
        import shutil
        shutil.rmtree(staging, ignore_errors=True)
        raise
