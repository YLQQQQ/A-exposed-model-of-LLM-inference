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
DOWNSTREAM_PATTERNS = ("sync*.py", "accounting*.py", "derived*.py", "signature*.py")


def check_source(source: str) -> list[str]:
    tree = ast.parse(source)
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import) and any(alias.name == "sqlite3" for alias in node.names):
            problems.append("下游模块禁止导入 sqlite3")
        if isinstance(node, ast.ImportFrom) and node.module == "sqlite3":
            problems.append("下游模块禁止导入 sqlite3")
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            for token in FORBIDDEN_TEXT:
                if token in node.value:
                    problems.append(f"下游模块出现 Nsight 私有表名: {token}")
    return sorted(set(problems))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    root = Path(__file__).resolve().parents[1]
    if args:
        paths = [Path(value) for value in args]
    else:
        package = root / "exposedpath_v141"
        paths = sorted(
            {path for pattern in DOWNSTREAM_PATTERNS for path in package.glob(pattern)}
        )
    failures: list[str] = []
    for path in paths:
        for problem in check_source(path.read_text(encoding="utf-8")):
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
