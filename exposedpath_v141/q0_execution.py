"""Gate 6 的 Q0 执行合同与 GPU 前运行准备。

本模块只描述如何执行已冻结的 oracle case，不生成标准答案，也不执行 GPU。
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .q0_oracle import load_oracle_bundle


class Q0ExecutionError(ValueError):
    """Q0 执行合同、运行准备或资格字段不合法。"""


_MANIFEST_PATH = Path("q0") / "execution_manifest_v0_2.json"
_SCHEMA_PATH = (
    Path("docs") / "v1_4_1" / "contracts" / "q0_execution_schema_v0_2.json"
)
_STRATEGIES = {
    "NATIVE_CUDA",
    "NATIVE_WITH_CANONICAL_FAULT",
    "SYNTHETIC_CANONICAL",
}
_FAULTS = {
    "REMOVE_ACTIVITY_CORRELATION",
    "MARK_TRACE_DROPPED",
    "REMOVE_GRAPH_NODE_MAPPING",
}


def _root(root: Path | None) -> Path:
    return Path(__file__).resolve().parents[1] if root is None else Path(root)


def _labels(items: Any, key: str, label: str) -> list[str]:
    if items is None:
        items = []
    if not isinstance(items, list):
        raise Q0ExecutionError(f"{label} 必须是数组")
    result: list[str] = []
    for item in items:
        if not isinstance(item, Mapping):
            raise Q0ExecutionError(f"{label} 成员必须是对象")
        value = item.get(key)
        if not isinstance(value, str) or not value:
            raise Q0ExecutionError(f"{label}.{key} 必须是非空字符串")
        result.append(value)
    return result


def _unique(values: list[str], label: str) -> None:
    if len(values) != len(set(values)):
        raise Q0ExecutionError(f"{label} 存在重复值")


def validate_q0_execution_manifest(
    manifest: Mapping[str, Any], oracle: Mapping[str, Any]
) -> None:
    """验证执行 manifest 与人工 oracle 的一一对应关系。"""

    if not isinstance(manifest, Mapping):
        raise Q0ExecutionError("Q0 execution manifest 必须是对象")
    eligibility = manifest.get("research_eligibility")
    if eligibility != {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "Q0_PRE_GPU_ONLY",
    }:
        raise Q0ExecutionError("Q0 GPU 前执行资格不得升级")
    schema_path = _root(None) / _SCHEMA_PATH
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    errors = sorted(
        Draft202012Validator(schema).iter_errors(manifest),
        key=lambda error: tuple(str(part) for part in error.absolute_path),
    )
    if errors:
        location = ".".join(str(part) for part in errors[0].absolute_path) or "root"
        raise Q0ExecutionError(f"Q0 execution schema 失败 {location}: {errors[0].message}")

    if manifest.get("oracle_version") != oracle.get("oracle_version"):
        raise Q0ExecutionError("oracle_version 不匹配")
    if manifest.get("contract_version") != oracle.get("contract_version"):
        raise Q0ExecutionError("contract_version 不匹配")

    raw_cases = manifest.get("cases")
    oracle_cases = oracle.get("cases")
    if not isinstance(raw_cases, list) or not isinstance(oracle_cases, list):
        raise Q0ExecutionError("cases 必须是数组")
    case_ids = [case.get("case_id") for case in raw_cases if isinstance(case, Mapping)]
    oracle_ids = [case.get("case_id") for case in oracle_cases if isinstance(case, Mapping)]
    _unique([str(value) for value in case_ids], "execution case_id")
    _unique([str(value) for value in oracle_ids], "oracle case_id")
    if set(case_ids) != set(oracle_ids) or len(case_ids) != len(oracle_ids):
        raise Q0ExecutionError("execution case 集合必须与 oracle case 集合完全一致")

    oracle_by_id = {case["case_id"]: case for case in oracle_cases}
    for case in raw_cases:
        if not isinstance(case, Mapping):
            raise Q0ExecutionError("execution case 必须是对象")
        case_id = case["case_id"]
        expected_case = oracle_by_id[case_id]
        if case.get("required_for_q0") is not expected_case.get("required_for_q0"):
            raise Q0ExecutionError(f"{case_id} required_for_q0 不匹配")
        construction = expected_case["construction"]
        expected_activities = _labels(
            construction.get("activities", []), "activity_label", f"{case_id}.activities"
        )
        expected_syncs = _labels(
            construction.get("syncs", []), "sync_label", f"{case_id}.syncs"
        )
        expected_apis = _labels(
            construction.get("api_calls", []), "api_label", f"{case_id}.api_calls"
        )
        for field, expected_labels in (
            ("activity_labels", expected_activities),
            ("sync_labels", expected_syncs),
            ("non_sync_api_labels", expected_apis),
        ):
            if case.get(field) != expected_labels:
                raise Q0ExecutionError(f"{case_id}.{field} 必须与 oracle construction 完全一致")

        profile = case.get("synthetic_profile")
        if profile != case_id:
            raise Q0ExecutionError(f"{case_id}.synthetic_profile 必须显式等于 case_id")
        strategy = case.get("execution_strategy")
        seed = case.get("native_seed_case_id")
        fault = case.get("fault_injection")
        if strategy not in _STRATEGIES:
            raise Q0ExecutionError(f"{case_id} 执行策略非法")
        if strategy == "NATIVE_CUDA":
            valid = seed == case_id and fault is None
        elif strategy == "NATIVE_WITH_CANONICAL_FAULT":
            valid = seed == case_id and fault in _FAULTS
        else:
            valid = seed is None and fault is None
        if not valid:
            raise Q0ExecutionError(f"{case_id} 策略字段组合非法")


def load_q0_execution_manifest(root: Path | None = None) -> dict[str, Any]:
    """加载并验证仓库内 Q0 执行 manifest。"""

    repository_root = _root(root)
    manifest = json.loads((repository_root / _MANIFEST_PATH).read_text(encoding="utf-8"))
    oracle = load_oracle_bundle(repository_root)
    validate_q0_execution_manifest(manifest, oracle)
    return manifest
