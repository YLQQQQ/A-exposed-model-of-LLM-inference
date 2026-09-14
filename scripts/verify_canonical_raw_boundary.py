"""禁止 S/A/B 等下游模块直接读取 Nsight SQLite 私有表。"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


FORBIDDEN_TEXT = (
    "CUPTI_ACTIVITY_KIND_",
    "NVTX_EVENTS",
    "StringIds",
    "TARGET_INFO_CUDA_",
    "DIAGNOSTIC_EVENT",
)
DOWNSTREAM_MODULES = (
    "sync_semantics.py",
    "s_bundle.py",
    "ab_inputs.py",
    "a_accounting.py",
    "b_provenance.py",
    "ab_bundle.py",
    "derived.py",
)
_FORBIDDEN_OLD_ACCOUNTING_MODULE = "analysis.exposed_accounting"
_DERIVED_FORBIDDEN_MODULES = {
    "canonical_raw", "s_bundle", "sync_semantics", "ab_inputs", "a_accounting", "b_provenance",
}
_DERIVED_AB_SYMBOLS = {"ABBundleError", "load_ab_bundle"}
_DERIVED_FORBIDDEN_TIME_FIELDS = {
    "start_ns", "end_ns", "sync_start_ns", "sync_end_ns", "host_start_ns", "host_end_ns",
    "window_start_ns", "window_end_ns", "runtime_start_ns", "runtime_end_ns",
}


def check_source(source: str) -> list[str]:
    tree = ast.parse(source)
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "sqlite3" for alias in node.names):
            problems.append("下游模块禁止导入 sqlite3")
        if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
            problems.append("下游模块禁止导入 sqlite3")
        if isinstance(node, ast.Import) and any(
            alias.name == _FORBIDDEN_OLD_ACCOUNTING_MODULE for alias in node.names
        ):
            problems.append("下游模块禁止导入旧 accounting")
        if isinstance(node, ast.ImportFrom) and node.module == _FORBIDDEN_OLD_ACCOUNTING_MODULE:
            problems.append("下游模块禁止导入旧 accounting")
        if (
            isinstance(node, ast.ImportFrom)
            and node.module == "analysis"
            and any(alias.name == "exposed_accounting" for alias in node.names)
        ):
            problems.append("下游模块禁止导入旧 accounting")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for token in FORBIDDEN_TEXT:
                if token in node.value:
                    problems.append(f"下游模块出现 Nsight 私有表名: {token}")
    return sorted(set(problems))


def check_derived_source(source: str) -> list[str]:
    """Reject a derived module that reaches below the validated A/B interface."""

    tree = ast.parse(source)
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "sqlite3" for alias in node.names):
            problems.append("Derived 禁止导入 sqlite3")
        if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
            problems.append("Derived 禁止导入 sqlite3")
        if isinstance(node, ast.ImportFrom):
            imported_names = {alias.name for alias in node.names}
            allowed_ab_import = (
                (node.level == 1 and node.module == "ab_bundle")
                or (node.level == 0 and node.module == "exposedpath_v141.ab_bundle")
            ) and imported_names.issubset(_DERIVED_AB_SYMBOLS)
            project_module = node.module in _DERIVED_FORBIDDEN_MODULES or (
                isinstance(node.module, str)
                and (node.module == "exposedpath_v141" or node.module.startswith("exposedpath_v141."))
            )
            if (node.level or project_module) and not allowed_ab_import:
                problems.append("Derived 只能从 A/B bundle 接口导入项目模块")
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "exposedpath_v141" or alias.name.startswith("exposedpath_v141."):
                    problems.append("Derived 只能导入 A/B bundle 接口")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if node.value in _DERIVED_FORBIDDEN_TIME_FIELDS:
                problems.append("Derived 禁止读取 Raw/S 时间字段")
            if any(token in node.value for token in FORBIDDEN_TEXT):
                problems.append("Derived 禁止出现 Nsight 私有表名")
        if isinstance(node, ast.Attribute) and node.attr in _DERIVED_FORBIDDEN_TIME_FIELDS:
            problems.append("Derived 禁止读取 Raw/S 时间字段")
    return sorted(set(problems))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[1]
    if args:
        paths = [Path(value) for value in args]
    else:
        package = root / "exposedpath_v141"
        paths = [package / name for name in DOWNSTREAM_MODULES]
    failures: list[str] = []
    for path in paths:
        for problem in check_source(path.read_text(encoding="utf-8")):
            failures.append(f"{path}: {problem}")
        if path.name == "derived.py":
            for problem in check_derived_source(path.read_text(encoding="utf-8")):
                failures.append(f"{path}: {problem}")
    if failures:
        print("canonical_raw_boundary: FAIL")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("canonical_raw_boundary: PASS")
    print(f"downstream_modules_checked: {len(paths)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
