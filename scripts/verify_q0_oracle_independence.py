"""静态检查 Q0 oracle 是否独立于被测 analyzer。"""

from __future__ import annotations

import ast
import sys
from pathlib import Path


FORBIDDEN_IMPORT_PREFIXES = (
    "analysis",
    "exposedpath",
    "exposedpath_v141.raw",
    "exposedpath_v141.sync",
    "exposedpath_v141.accounting",
)

EVALUATOR_FORBIDDEN_MODULES = {
    "ab_bundle",
    "accounting_a",
    "accounting_b",
    "canonical_raw",
    "s_bundle",
    "sync_semantics",
}


def _is_forbidden(module: str) -> bool:
    return any(
        module == prefix or module.startswith(prefix + ".")
        for prefix in FORBIDDEN_IMPORT_PREFIXES
    )


def check_source(source: str) -> list[str]:
    """返回违反 oracle 独立性约束的问题列表。"""

    tree = ast.parse(source)
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if _is_forbidden(alias.name):
                    problems.append(f"禁止导入: {alias.name}")
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if _is_forbidden(module):
                problems.append(f"禁止导入: {module}")

    timing_function = next(
        (
            node
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == "calculate_expected_timing"
        ),
        None,
    )
    if timing_function is None:
        problems.append("缺少 calculate_expected_timing")
    else:
        for node in ast.walk(timing_function):
            if isinstance(node, ast.Constant) and node.value == "dependency_edges":
                problems.append("区间函数禁止读取 dependency_edges")
            if isinstance(node, ast.Name) and node.id in {
                "recover_wait_set",
                "select_terminal",
                "classify_sync",
            }:
                problems.append(f"区间函数禁止调用被测逻辑: {node.id}")
    return problems


def check_evaluator_source(source: str) -> list[str]:
    """禁止独立 evaluator 导入任何被测 S/A/B 实现。"""

    tree = ast.parse(source)
    problems: list[str] = []
    for node in ast.walk(tree):
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            modules.append(node.module or "")
        for module in modules:
            leaf = module.rsplit(".", 1)[-1]
            if leaf in EVALUATOR_FORBIDDEN_MODULES:
                problems.append(f"evaluator 禁止导入被测模块: {leaf}")
    return problems


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[1]
    target = Path(args[0]) if args else root / "exposedpath_v141" / "q0_oracle.py"
    source = target.read_text(encoding="utf-8")
    problems = check_source(source)
    if not args:
        evaluator = root / "exposedpath_v141" / "q0_evaluator.py"
        problems.extend(check_evaluator_source(evaluator.read_text(encoding="utf-8")))
    if problems:
        print("oracle_independence: FAIL")
        for problem in problems:
            print(f"- {problem}")
        return 1
    print("oracle_independence: PASS")
    print("scope: STATIC_ORACLE_AND_EVALUATOR_INDEPENDENCE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
