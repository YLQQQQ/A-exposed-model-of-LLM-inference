"""Gate 6 的 Q0 执行合同与 GPU 前运行准备。

本模块只描述如何执行已冻结的 oracle case，不生成标准答案，也不执行 GPU。
"""

from __future__ import annotations

import json
import os
import hashlib
import re
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
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
_CUDA_SOURCE_PATH = Path("q0") / "cuda" / "exposedpath_q0.cu"
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
_RUN_ID = re.compile(r"^[A-Za-z0-9._-]+$")
_CUDA_VISIBLE_DEVICE = re.compile(r"^[A-Za-z0-9._:-]+$")

# Gate 6 construction amendment（`docs/v1_4_1/gate6_construction_amendment_v0_1.md`）冻结的
# measurement initialization policy：每个 case 必须显式声明，缺失或未知值一律 fail closed。
# 这里是唯一枚举来源，manifest、run provenance 与 collection 校验都引用它。
MEASUREMENT_INITIALIZATIONS = frozenset(
    {
        "NONE",
        "PRE_CAPTURE_SAME_KERNEL_WARMUP",
    }
)
MEASUREMENT_INITIALIZATION_FIELD = "measurement_initialization"
MEASUREMENT_INITIALIZATION_FLAG = "--measurement-initialization"

# 只有 execution path 产生该版本；collection 兼容读取历史 `0.2.0` run manifest。
RUN_SCHEMA_VERSION = "exposedpath-q0-run/0.2.1"
LEGACY_RUN_SCHEMA_VERSION = "exposedpath-q0-run/0.2.0"

# Q0 build contract amendment（`docs/v1_4_1/gate6_q0_build_contract_amendment_v0_1.md`）
# 冻结的 codegen architecture：整份 Q0 binary 统一使用显式 target，不依赖 nvcc 默认值、
# 不依赖 build host 可见 GPU，也不允许通过环境变量注入。
Q0_GPU_ARCH = "sm_89"
Q0_BUILD_RECEIPT_VERSION = "exposedpath-q0-build-receipt/0.1.0"
Q0_BUILD_RECEIPT_SUFFIX = ".build_receipt.json"


def measurement_initialization_policy(case: Mapping[str, Any]) -> str:
    """读取并校验单个 case 的初始化 policy；缺失或未知值 fail closed。"""

    policy = case.get(MEASUREMENT_INITIALIZATION_FIELD)
    case_id = case.get("case_id")
    if policy not in MEASUREMENT_INITIALIZATIONS:
        raise Q0ExecutionError(
            f"{case_id}.{MEASUREMENT_INITIALIZATION_FIELD} 缺失或未知: {policy!r}"
        )
    return str(policy)


def _root(root: Path | None) -> Path:
    return Path(__file__).resolve().parents[1] if root is None else Path(root)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


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
        # policy 必须显式且可识别；缺失或未知值一律 fail closed，不得隐式猜测。
        measurement_initialization_policy(case)
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


def build_q0_compile_command(
    nvcc: Path, source: Path, output: Path, *, platform: str
) -> tuple[str, ...]:
    """构造不经 shell 的 Q0 CUDA 编译参数。"""

    if platform not in {"windows", "linux"}:
        raise ValueError("platform 必须是 windows 或 linux")
    command = [
        str(Path(nvcc)),
        f"-arch={Q0_GPU_ARCH}",
        "-std=c++17",
        "-O2",
        "-lineinfo",
        str(Path(source)),
    ]
    if platform == "windows":
        command.append("-Xcompiler=/EHsc")
    else:
        command.append("-Xcompiler=-pthread")
    command.append("-lcuda")
    command.extend(("-o", str(Path(output))))
    return tuple(command)


def q0_build_receipt_path(output: Path) -> Path:
    """返回 `<binary>.build_receipt.json` 的冻结路径。"""

    return Path(f"{Path(output)}{Q0_BUILD_RECEIPT_SUFFIX}")


def _nvcc_version_output(
    nvcc: Path, environment: Mapping[str, str]
) -> str:
    """读取 nvcc `--version` 的完整输出；失败即 fail closed。"""

    completed = subprocess.run(
        [str(nvcc), "--version"],
        cwd=_root(None),
        env=dict(environment),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        raise Q0ExecutionError(
            f"nvcc --version 失败 ({completed.returncode}): "
            f"{(completed.stdout + completed.stderr).strip()}"
        )
    version_output = (completed.stdout + completed.stderr).strip()
    if not version_output:
        raise Q0ExecutionError("nvcc --version 未返回版本信息")
    return version_output


def _write_json_document(path: Path, payload: Mapping[str, Any]) -> None:
    """原子写入 JSON 文档，避免留下半成品产物。"""

    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            stream.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        temporary.replace(path)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise


def compile_q0_microbench(
    nvcc: Path,
    output: Path,
    *,
    platform: str,
    source: Path | None = None,
) -> Path:
    """编译 Q0 微程序；只构建，不运行任何 CUDA case。"""

    source_path = _root(None) / _CUDA_SOURCE_PATH if source is None else Path(source)
    output_path = Path(output)
    nvcc_path = Path(nvcc)
    receipt_path = q0_build_receipt_path(output_path)
    if not nvcc_path.is_file():
        raise Q0ExecutionError(f"nvcc 不存在: {nvcc_path}")
    if not source_path.is_file():
        raise Q0ExecutionError(f"Q0 CUDA 源文件不存在: {source_path}")
    if output_path.exists():
        raise Q0ExecutionError(f"拒绝覆盖已有 Q0 binary: {output_path}")
    if receipt_path.exists():
        raise Q0ExecutionError(f"拒绝覆盖已有 Q0 build receipt: {receipt_path}")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.pop("CL", None)
    environment.pop("_CL_", None)
    # Gate 6 Q0 build contract amendment §2/§8：codegen 只能来自本文件的冻结 argv。
    # ambient nvcc flag 注入变量一律摘除，避免 arch / 编译选项被静默追加或覆盖。
    for injected in ("NVCC_APPEND_FLAGS", "NVCC_PREPEND_FLAGS"):
        environment.pop(injected, None)
    command = build_q0_compile_command(
        nvcc_path, source_path, output_path, platform=platform
    )
    version_output = _nvcc_version_output(nvcc_path, environment)
    completed = subprocess.run(
        command,
        cwd=_root(None),
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stdout + completed.stderr).strip()
        raise Q0ExecutionError(f"Q0 CUDA 编译失败 ({completed.returncode}): {detail}")
    if not output_path.is_file():
        raise Q0ExecutionError("nvcc 返回成功但未生成 Q0 binary")
    receipt = {
        "receipt_version": Q0_BUILD_RECEIPT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "platform": platform,
        "gpu_arch": Q0_GPU_ARCH,
        "cuda_source": {
            "path": str(source_path),
            "sha256": _sha256(source_path),
        },
        "nvcc": {"path": str(nvcc_path), "version_output": version_output},
        "compile_command": list(command),
        "binary": {
            "path": str(output_path),
            "size_bytes": output_path.stat().st_size,
            "sha256": _sha256(output_path),
        },
    }
    _write_json_document(receipt_path, receipt)
    return output_path


def _source_manifest(
    case_id: str, case_run_id: str, cuda_visible_device: str
) -> dict[str, Any]:
    return {
        "experiment_id": "exposedpath-q0",
        "wmpc_id": "q0-controlled",
        "run_id": case_run_id,
        "run_role": "Engineering",
        "pass_id": "Pass1",
        "repeat_id": "repeat-0",
        "default_stream_mode": (
            "LEGACY" if case_id == "Q0-DEFAULT-LEGACY-001" else "PER_THREAD"
        ),
        "gpu_index": 0,
        "selected_device_id": 0,
        "cuda_visible_device": cuda_visible_device,
        "q0_case_id": case_id,
        "q0_status": "NOT_RUN",
    }


def prepare_q0_run(
    output_dir: Path,
    binary: Path,
    nsys: Path,
    *,
    platform: str,
    run_id: str,
    cuda_visible_device: str,
) -> Path:
    """生成 Q0 Engineering dry-run；不执行二进制或 Nsight。"""

    if platform not in {"windows", "linux"}:
        raise Q0ExecutionError("platform 必须是 windows 或 linux")
    if not _RUN_ID.fullmatch(run_id):
        raise Q0ExecutionError("run_id 只能包含字母、数字、点、下划线和连字符")
    if not _CUDA_VISIBLE_DEVICE.fullmatch(cuda_visible_device):
        raise Q0ExecutionError(
            "CUDA_VISIBLE_DEVICES 必须显式选择单个 GPU index 或 UUID"
        )
    output_path = Path(output_dir).resolve()
    binary_path = Path(binary).resolve()
    nsys_path = Path(nsys).resolve()
    if output_path.exists():
        raise Q0ExecutionError(f"拒绝覆盖已有 Q0 输出目录: {output_path}")
    if not binary_path.is_file():
        raise Q0ExecutionError(f"Q0 binary 不存在: {binary_path}")
    if not nsys_path.is_file():
        raise Q0ExecutionError(f"nsys 不存在: {nsys_path}")

    root = _root(None)
    execution_path = root / _MANIFEST_PATH
    oracle_path = root / "q0" / "oracle_cases_v0_2.json"
    source_path = root / _CUDA_SOURCE_PATH
    execution = load_q0_execution_manifest(root)
    cases: list[dict[str, Any]] = []
    source_manifest_bytes: dict[str, bytes] = {}
    for case in execution["cases"]:
        case_id = case["case_id"]
        policy = measurement_initialization_policy(case)
        case_run_id = f"{run_id}.{case_id.lower()}"
        native_seed = case["native_seed_case_id"]
        case_dir = output_path / "cases" / case_id
        trace_prefix = case_dir / "trace" if native_seed is not None else None
        argv = None
        if native_seed is not None:
            case_profile_args = (
                ["--cuda-graph-trace=node"]
                if case_id == "Q0-GRAPH-UNSUPPORTED-001"
                else []
            )
            argv = [
                str(nsys_path),
                "profile",
                "--trace=cuda,nvtx",
                "--capture-range=cudaProfilerApi",
                "--capture-range-end=stop",
                "--force-overwrite=false",
                *case_profile_args,
                "-o",
                str(trace_prefix),
                str(binary_path),
                "--case",
                native_seed,
                "--run-id",
                case_run_id,
                MEASUREMENT_INITIALIZATION_FLAG,
                policy,
            ]
        source_content = (
            json.dumps(
                _source_manifest(case_id, case_run_id, cuda_visible_device),
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("utf-8")
        source_manifest_bytes[case_id] = source_content
        cases.append(
            {
                "case_id": case_id,
                "execution_strategy": case["execution_strategy"],
                "native_seed_case_id": native_seed,
                "fault_injection": case["fault_injection"],
                "synthetic_profile": case["synthetic_profile"],
                "measurement_initialization": policy,
                "source_manifest": str(Path("cases") / case_id / "source_manifest.json"),
                "source_manifest_sha256": hashlib.sha256(source_content).hexdigest().upper(),
                "trace_prefix": str(trace_prefix) if trace_prefix is not None else None,
                "command_argv": argv,
                "status": "PREPARED_NOT_EXECUTED",
            }
        )

    manifest = {
        "schema_version": RUN_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PREPARED_NOT_EXECUTED",
        "run_id": run_id,
        "data_role": "Engineering",
        "platform": platform,
        "gpu_selection": {
            "cuda_visible_device": cuda_visible_device,
            "logical_device_id": 0,
        },
        "source": {
            "binary": {"path": str(binary_path), "sha256": _sha256(binary_path)},
            "nsys": {"path": str(nsys_path), "sha256": _sha256(nsys_path)},
            "cuda_source": {"name": source_path.name, "sha256": _sha256(source_path)},
            "execution_manifest": {
                "name": execution_path.name,
                "sha256": _sha256(execution_path),
            },
            "oracle": {"name": oracle_path.name, "sha256": _sha256(oracle_path)},
        },
        "environment": {
            "gpu": None,
            "driver": None,
            "cuda_runtime": None,
            "nsight_systems": None,
            "os": platform,
        },
        "research_eligibility": {
            "formal_evidence": False,
            "q0_status": "NOT_RUN",
            "scope": "Q0_DRY_RUN_ONLY",
        },
        "cases": cases,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(prefix=f".{output_path.name}.tmp-", dir=output_path.parent)
    )
    try:
        for case in cases:
            case_dir = temporary / "cases" / case["case_id"]
            case_dir.mkdir(parents=True)
            (case_dir / "source_manifest.json").write_bytes(
                source_manifest_bytes[case["case_id"]]
            )
        (temporary / "q0_run_manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        temporary.replace(output_path)
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise
    return output_path / "q0_run_manifest.json"
