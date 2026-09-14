"""对 Canonical Raw 派生副本执行 Gate 2 预定义的三种 Q0 故障。"""

from __future__ import annotations

import copy
import gzip
import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .q0_execution import load_q0_execution_manifest
from .sync_semantics import load_canonical_bundle


class Q0FaultError(ValueError):
    """故障身份、命中数或 Canonical 派生边界不合法。"""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_records(path: Path, records: list[dict[str, Any]]) -> dict[str, Any]:
    payload = b"".join(
        (json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")
        for record in records
    )
    with path.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as zipped:
            zipped.write(payload)
    return {
        "filename": path.name,
        "record_count": len(records),
        "sha256": _sha256(path),
        "size_bytes": path.stat().st_size,
    }


def apply_q0_fault(
    canonical_manifest: Path, case_id: str, output_dir: Path
) -> Path:
    """创建不可覆盖的受控故障副本；源 Canonical 永远只读。"""

    source_path = Path(canonical_manifest).resolve()
    output = Path(output_dir).resolve()
    if output.exists():
        raise Q0FaultError(f"拒绝覆盖已有故障输出目录: {output}")
    execution = load_q0_execution_manifest()
    matches = [case for case in execution["cases"] if case["case_id"] == case_id]
    if len(matches) != 1:
        raise Q0FaultError(f"未知 Q0 case: {case_id}")
    case = matches[0]
    if case["execution_strategy"] != "NATIVE_WITH_CANONICAL_FAULT":
        raise Q0FaultError(f"{case_id} 不使用 Canonical fault")
    fault = case["fault_injection"]

    bundle = load_canonical_bundle(source_path)
    records = copy.deepcopy(bundle["records"])
    manifest = copy.deepcopy(bundle["manifest"])
    mutation_count = 0
    if fault == "REMOVE_ACTIVITY_CORRELATION":
        targets = [
            record for record in records["device_activity"]
            if record.get("correlation_id") is not None
        ]
        if len(targets) == 1:
            targets[0]["correlation_id"] = None
            mutation_count = 1
    elif fault == "REMOVE_GRAPH_NODE_MAPPING":
        targets = [
            record for record in records["device_activity"]
            if record.get("graph_id") is not None and record.get("graph_node_id") is not None
        ]
        if len(targets) == 1:
            targets[0]["graph_node_id"] = None
            mutation_count = 1
    elif fault == "MARK_TRACE_DROPPED":
        manifest["observation_validity"] = {
            "status": "invalid",
            "issues": [{
                "level": "error",
                "code": "TRACE_DROPPED_RECORDS",
                "detail": {"injected_by": fault},
            }],
        }
        mutation_count = 1
    else:
        raise Q0FaultError(f"未实现的 Q0 fault: {fault}")
    if mutation_count != 1:
        raise Q0FaultError(f"{fault} 必须恰好命中一个受控目标")

    manifest["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    manifest.setdefault("source", {})["q0_fault"] = {
        "case_id": case_id,
        "fault_injection": fault,
        "mutation_count": mutation_count,
        "source_canonical_manifest_sha256": _sha256(source_path),
    }
    manifest["research_eligibility"] = {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "blocking_reasons": ["Q0_CONTROLLED_CANONICAL_FAULT", "Q0_NOT_RUN"],
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{output.name}.tmp-", dir=output.parent))
    try:
        files = {}
        for kind, spec in bundle["schema"]["record_types"].items():
            files[kind] = _write_records(staging / spec["filename"], records[kind])
        manifest["files"] = files
        target_manifest = staging / "canonical_manifest.json"
        target_manifest.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        load_canonical_bundle(target_manifest)
        staging.replace(output)
    except BaseException:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    return output / "canonical_manifest.json"
