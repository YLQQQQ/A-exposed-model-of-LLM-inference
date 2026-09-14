"""Gate 5 A/B 的只读 Canonical Raw + S 输入联结。

本模块只验证已经冻结的输入并建立 Canonical 事实索引。它绝不恢复或替换
S 层的 wait set、terminal 或 validity。
"""

from __future__ import annotations

import gzip
import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from .canonical_raw import load_canonical_raw_schema
from .contract import load_contract_bundle
from .s_bundle import load_s_layer_schema
from .sync_semantics import SyncSemanticsError, classify_cuda_api, load_canonical_bundle


class ABInputError(ValueError):
    """A/B 输入的结构、lineage 或 Canonical/S 联结违反冻结合同。"""


_SHA256 = re.compile(r"^[0-9A-F]{64}$")
_IDENTITY_FIELDS = (
    "experiment_id",
    "wmpc_id",
    "run_id",
    "run_role",
    "pass_id",
    "request_id",
    "repeat_id",
)
_WINDOW_PHASES = ("full_request", "prefill", "decode")
_STRUCTURED_PREFIX = "EXPOSEDPATH_JSON_V1:"
_REGISTRY_PATH = Path("docs") / "v1_4_1" / "contracts" / "sync_semantics_registry_v0_2.json"


@dataclass(frozen=True)
class CanonicalBundle:
    """经 Canonical loader 校验后的公开事实及只读事实索引。"""

    manifest: dict[str, Any]
    records: dict[str, tuple[dict[str, Any], ...]]
    schema: dict[str, Any]
    cuda_api_by_id: dict[str, dict[str, Any]]
    activity_by_id: dict[str, dict[str, Any]]
    physical_sync_by_id: dict[str, dict[str, Any]]


@dataclass(frozen=True)
class RequestPhaseWindow:
    """由一条结构化 NVTX 半开 range 直接观察到的 request/phase 窗口。"""

    window_id: str
    experiment_id: str
    wmpc_id: str
    run_id: str
    run_role: str
    pass_id: str
    request_id: str
    repeat_id: str
    phase: str
    start_ns: int
    end_ns: int
    nvtx_record_id: str

    @property
    def window_start_ns(self) -> int:
        return self.start_ns

    @property
    def window_end_ns(self) -> int:
        return self.end_ns


@dataclass(frozen=True)
class WindowDiscoveryIssue:
    """单个逻辑 request identity 的窗口发现 fail-closed 记录。"""

    experiment_id: str | None
    wmpc_id: str | None
    run_id: str | None
    run_role: str | None
    pass_id: str | None
    request_id: str | None
    repeat_id: str | None
    source_nvtx_record_ids: tuple[str, ...]
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ABInputs:
    canonical: CanonicalBundle
    s_manifest: dict[str, object]
    s_records: tuple[dict[str, object], ...]
    windows: tuple[RequestPhaseWindow, ...]
    global_quality_reasons: tuple[str, ...]
    window_discovery_issues: tuple[WindowDiscoveryIssue, ...]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _as_mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ABInputError(f"{label} 必须是对象")
    return value


def _as_text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise ABInputError(f"{label} 必须是非空字符串")
    return value


def _load_canonical(manifest_path: Path) -> CanonicalBundle:
    try:
        loaded = load_canonical_bundle(manifest_path)
    except (SyncSemanticsError, OSError, json.JSONDecodeError) as exc:
        raise ABInputError(f"Canonical bundle 无法加载: {exc}") from exc

    records = {
        kind: tuple(dict(record) for record in rows)
        for kind, rows in loaded["records"].items()
    }
    physical_syncs: dict[str, dict[str, Any]] = {}
    for sync in records["cuda_sync"]:
        classification = classify_cuda_api(str(sync["runtime_api_name"]))
        if classification["role"] == "DEPENDENCY_EDGE":
            continue
        sync_id = str(sync["record_id"])
        if sync_id in physical_syncs:
            raise ABInputError(f"Canonical physical sync_id 重复: {sync_id}")
        physical_syncs[sync_id] = sync
    activity_by_id = {str(record["record_id"]): record for record in records["device_activity"]}
    if len(activity_by_id) != len(records["device_activity"]):
        raise ABInputError("Canonical device activity record_id 重复")
    cuda_api_by_id = {str(record["record_id"]): record for record in records["cuda_api"]}
    if len(cuda_api_by_id) != len(records["cuda_api"]):
        raise ABInputError("Canonical CUDA API record_id 重复")
    return CanonicalBundle(
        manifest=dict(loaded["manifest"]),
        records=records,
        schema=dict(loaded["schema"]),
        cuda_api_by_id=cuda_api_by_id,
        activity_by_id=activity_by_id,
        physical_sync_by_id=physical_syncs,
    )


def _load_s_records(manifest_path: Path) -> tuple[dict[str, Any], tuple[dict[str, Any], ...]]:
    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_file():
        raise ABInputError(f"S manifest 不存在: {manifest_path}")
    try:
        raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ABInputError(f"S manifest 无法读取: {exc}") from exc
    manifest = dict(_as_mapping(raw_manifest, "S manifest"))
    schema = load_s_layer_schema()
    if manifest.get("schema_version") != schema["schema_version"]:
        raise ABInputError("S schema_version 不匹配")
    if manifest.get("measurement_contract_version") != schema["measurement_contract_version"]:
        raise ABInputError("S Measurement Contract 版本不匹配")
    if manifest.get("input_schema_version") != schema["input_schema_version"]:
        raise ABInputError("S Canonical input schema_version 不匹配")

    files = _as_mapping(manifest.get("files"), "S files")
    if set(files) != {"sync_records"}:
        raise ABInputError("S files 集合不匹配")
    entry = _as_mapping(files["sync_records"], "S sync_records 文件条目")
    if entry.get("filename") != schema["sync_records_filename"]:
        raise ABInputError("S sync_records 文件名不匹配")
    record_count = entry.get("record_count")
    if not isinstance(record_count, int) or record_count < 0:
        raise ABInputError("S sync_records record_count 非法")
    expected_hash = entry.get("sha256")
    if not isinstance(expected_hash, str) or not _SHA256.fullmatch(expected_hash):
        raise ABInputError("S sync_records SHA-256 非法")
    expected_size = entry.get("size_bytes")
    if not isinstance(expected_size, int) or expected_size < 0:
        raise ABInputError("S sync_records size_bytes 非法")
    record_path = (manifest_path.parent / str(entry["filename"])).resolve()
    if record_path.parent != manifest_path.parent.resolve():
        raise ABInputError("S sync_records 文件路径越界")
    if not record_path.is_file():
        raise ABInputError("S sync_records 文件不存在")
    if _sha256(record_path) != expected_hash:
        raise ABInputError("S sync_records SHA-256 不匹配")
    if record_path.stat().st_size != expected_size:
        raise ABInputError("S sync_records 文件大小不匹配")

    expected_fields = set(schema["sync_record_fields"])
    records: list[dict[str, Any]] = []
    try:
        with gzip.open(record_path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                value = json.loads(line)
                record = dict(_as_mapping(value, f"S sync record {line_number}"))
                if set(record) != expected_fields:
                    raise ABInputError(f"S sync record {line_number} 字段集合不匹配")
                records.append(record)
    except ABInputError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ABInputError(f"S sync_records 文件无法读取: {exc}") from exc
    if len(records) != record_count:
        raise ABInputError("S sync_records 记录数不匹配")
    return manifest, tuple(records)


def _validate_lineage(
    canonical_manifest: Path,
    canonical: CanonicalBundle,
    s_manifest: Mapping[str, Any],
) -> None:
    source = _as_mapping(s_manifest.get("source"), "S source")
    canonical_manifest = Path(canonical_manifest).resolve()
    if source.get("canonical_manifest_name") != canonical_manifest.name:
        raise ABInputError("S Canonical manifest 名称不匹配")
    if source.get("canonical_manifest_sha256") != _sha256(canonical_manifest):
        raise ABInputError("S Canonical manifest SHA-256 不匹配")
    canonical_source = _as_mapping(canonical.manifest.get("source"), "Canonical source")
    canonical_sqlite = _as_mapping(canonical_source.get("sqlite"), "Canonical source.sqlite")
    if source.get("source_sqlite_sha256") != canonical_sqlite.get("sha256"):
        raise ABInputError("S source SQLite SHA-256 不匹配")
    if s_manifest.get("data_role") != canonical.manifest.get("data_role"):
        raise ABInputError("S data_role 不得改变 Canonical 数据角色")

    registry = _as_mapping(source.get("sync_registry"), "S source.sync_registry")
    contract = load_contract_bundle()["contract"]
    if registry.get("version") != contract["registry_version"]:
        raise ABInputError("S sync registry 版本不匹配")
    registry_path = Path(__file__).resolve().parents[1] / _REGISTRY_PATH
    if registry.get("sha256") != _sha256(registry_path):
        raise ABInputError("S sync registry SHA-256 不匹配")


def _validate_s_record_identity(canonical: CanonicalBundle, record: Mapping[str, Any]) -> None:
    sync_id = _as_text(record.get("sync_id"), "S sync_id")
    raw_sync = canonical.physical_sync_by_id.get(sync_id)
    if raw_sync is None:
        raise ABInputError(f"S sync_id 多余或不属于 Canonical physical sync: {sync_id}")
    expected = classify_cuda_api(str(raw_sync["runtime_api_name"]))
    expected_identity = {
        "registry_rule_id": expected["registry_rule_id"],
        "sync_universe_class": expected["universe_class"],
        "sync_kind": expected["sync_kind"],
        "completion_scope": expected["completion_scope"],
        "host_start_ns": raw_sync["runtime_start_ns"],
        "host_end_ns": raw_sync["runtime_end_ns"],
        "device_id": raw_sync["device_id"],
        "context_id": raw_sync["context_id"],
        "stream_id": raw_sync["stream_id"],
        "event_id": raw_sync["event_id"],
    }
    for field, expected_value in expected_identity.items():
        if record.get(field) != expected_value:
            raise ABInputError(f"S sync {sync_id} 的 {field} 与 Canonical 不匹配")

    wait_set = record.get("wait_set_activity_ids")
    if not isinstance(wait_set, list) or len(wait_set) != len(set(wait_set)):
        raise ABInputError(f"S sync {sync_id} 的 wait_set_activity_ids 非法")
    missing_wait = [activity_id for activity_id in wait_set if activity_id not in canonical.activity_by_id]
    if missing_wait:
        raise ABInputError(f"S sync {sync_id} 的 wait_set activity 不在 Canonical: {missing_wait}")
    terminal = _as_mapping(record.get("terminal"), f"S sync {sync_id} terminal")
    if set(terminal) != {"status", "kind", "activity_id", "end_ns", "clock_domain_id"}:
        raise ABInputError(f"S sync {sync_id} 的 terminal 字段非法")
    validity = record.get("validity")
    if validity not in {"VALID_NONEMPTY", "VALID_EMPTY", "INVALID", "AMBIGUOUS"}:
        raise ABInputError(f"S sync {sync_id} 的 validity 非法")
    if record.get("wait_set_status") != validity:
        raise ABInputError(f"S sync {sync_id} 的 wait_set_status 与 validity 不一致")
    frontier = record.get("semantic_frontier_activity_ids")
    if not isinstance(frontier, list) or any(not isinstance(item, str) for item in frontier):
        raise ABInputError(f"S sync {sync_id} 的 semantic frontier 非法")
    if len(frontier) != len(set(frontier)) or not set(frontier).issubset(wait_set):
        raise ABInputError(f"S sync {sync_id} 的 semantic frontier 不属于 wait_set")
    if validity in {"VALID_NONEMPTY", "VALID_EMPTY"}:
        if (
            record.get("dependency_closure_status") != "COMPLETE"
            or record.get("primary_reason") is not None
            or record.get("secondary_reasons") != []
            or record.get("invocation_bleed") is not False
        ):
            raise ABInputError(f"S sync {sync_id} 的 valid 状态与 closure/reasons/ownership 不一致")
    elif not isinstance(record.get("primary_reason"), str) or not record["primary_reason"]:
        raise ABInputError(f"S sync {sync_id} 的 invalid/ambiguous 缺少 primary_reason")
    if validity == "VALID_NONEMPTY":
        if not wait_set or terminal.get("status") != "VALID":
            raise ABInputError(f"S sync {sync_id} 的 VALID_NONEMPTY 必须有 wait_set 和 valid terminal")
        if terminal.get("kind") not in {"ACTIVITY", "COMPLETION_BOUNDARY"}:
            raise ABInputError(f"S sync {sync_id} 的 valid terminal kind 非法")
        end, clock = terminal.get("end_ns"), terminal.get("clock_domain_id")
        if not isinstance(end, int) or isinstance(end, bool) or end < 0:
            raise ABInputError(f"S sync {sync_id} 的 terminal end_ns 非法")
        if not isinstance(clock, str) or not clock:
            raise ABInputError(f"S sync {sync_id} 的 terminal clock_domain_id 非法")
        if end > record["host_end_ns"]:
            raise ABInputError(f"S sync {sync_id} 的 terminal 晚于 sync end")
        if terminal["kind"] == "COMPLETION_BOUNDARY":
            if terminal.get("activity_id") is not None:
                raise ABInputError(f"S sync {sync_id} 的 completion boundary 不得带 activity_id")
            if clock != raw_sync.get("clock_domain_id"):
                raise ABInputError(
                    f"S sync {sync_id} 的 completion boundary clock_domain_id 与 Canonical 不匹配"
                )
    else:
        expected_status = "NOT_APPLICABLE" if validity == "VALID_EMPTY" else validity
        if (
            terminal.get("status") != expected_status
            or terminal.get("kind") != "NONE"
            or any(terminal.get(field) is not None for field in ("activity_id", "end_ns", "clock_domain_id"))
        ):
            raise ABInputError(f"S sync {sync_id} 的 terminal 与 validity 不一致")
        if validity == "VALID_EMPTY" and wait_set:
            raise ABInputError(f"S sync {sync_id} 的 VALID_EMPTY 必须是空 wait_set")
    if terminal.get("kind") == "ACTIVITY":
        activity_id = terminal.get("activity_id")
        if activity_id not in canonical.activity_by_id:
            raise ABInputError(f"S sync {sync_id} 的 terminal activity 不在 Canonical: {activity_id}")
        if activity_id not in wait_set or activity_id not in frontier:
            raise ABInputError(f"S sync {sync_id} 的 terminal 不属于 wait_set/semantic frontier")
        activity = canonical.activity_by_id[activity_id]
        if any(terminal[field] != activity[field] for field in ("end_ns", "clock_domain_id")):
            raise ABInputError(f"S sync {sync_id} 的 terminal end_ns/clock_domain_id 与 Canonical 不匹配")


def _validate_s_join(canonical: CanonicalBundle, records: tuple[dict[str, Any], ...]) -> None:
    seen: set[str] = set()
    for record in records:
        sync_id = _as_text(record.get("sync_id"), "S sync_id")
        if sync_id in seen:
            raise ABInputError(f"S sync_id 重复: {sync_id}")
        seen.add(sync_id)
        _validate_s_record_identity(canonical, record)
    canonical_ids = set(canonical.physical_sync_by_id)
    missing = sorted(canonical_ids - seen)
    if missing:
        raise ABInputError(f"S 缺少 Canonical physical sync: {missing}")
    extra = sorted(seen - canonical_ids)
    if extra:
        raise ABInputError(f"S 多余 Canonical physical sync: {extra}")


def _window_key(identity: Mapping[str, Any]) -> tuple[str, ...]:
    return tuple(_as_text(identity.get(field), f"NVTX structured identity.{field}") for field in _IDENTITY_FIELDS)


def _issue_for_key(
    key: tuple[str, ...] | None,
    reasons: list[str] | tuple[str, ...],
    source_record_ids: list[str] | tuple[str, ...],
) -> WindowDiscoveryIssue:
    values = key if key is not None else (None,) * len(_IDENTITY_FIELDS)
    return WindowDiscoveryIssue(
        *values,
        source_nvtx_record_ids=tuple(sorted(set(source_record_ids))),
        reasons=tuple(dict.fromkeys(reasons)),
    )


def _text_identity(nvtx: Mapping[str, Any]) -> tuple[Mapping[str, Any] | None, str | None]:
    """把 Canonical text 重新解析为窗口身份事实，并拒绝缓存 identity 伪造。"""

    text = nvtx.get("text")
    if not isinstance(text, str) or not text.startswith(_STRUCTURED_PREFIX):
        cached_identity = nvtx.get("structured_identity")
        if isinstance(cached_identity, Mapping) and cached_identity.get("phase") in _WINDOW_PHASES:
            return None, "STRUCTURED_IDENTITY_TEXT_PREFIX_MISSING"
        return None, None
    try:
        payload = json.loads(text[len(_STRUCTURED_PREFIX) :])
    except json.JSONDecodeError:
        return None, "STRUCTURED_IDENTITY_TEXT_INVALID"
    if not isinstance(payload, Mapping):
        return None, "STRUCTURED_IDENTITY_TEXT_INVALID"
    structured_identity = nvtx.get("structured_identity")
    if not isinstance(structured_identity, Mapping) or dict(payload) != dict(structured_identity):
        return payload, "STRUCTURED_IDENTITY_TEXT_MISMATCH"
    return payload, None


def _discovery_result(
    canonical: CanonicalBundle,
) -> tuple[tuple[RequestPhaseWindow, ...], tuple[WindowDiscoveryIssue, ...]]:
    groups: dict[tuple[str, ...], dict[str, list[tuple[dict[str, Any], Mapping[str, Any]]]]] = {}
    issue_reasons: dict[tuple[str, ...] | None, list[str]] = {}
    issue_sources: dict[tuple[str, ...] | None, list[str]] = {}

    def add_issue(key: tuple[str, ...] | None, reason: str, nvtx: Mapping[str, Any]) -> None:
        issue_reasons.setdefault(key, []).append(reason)
        record_id = nvtx.get("record_id")
        if isinstance(record_id, str) and record_id:
            issue_sources.setdefault(key, []).append(record_id)

    for nvtx in canonical.records["nvtx"]:
        identity, text_reason = _text_identity(nvtx)
        if identity is None:
            if text_reason is not None:
                add_issue(None, text_reason, nvtx)
            continue
        phase = identity.get("phase")
        if phase not in _WINDOW_PHASES:
            continue
        # Structured marker/sync ranges can carry the same invocation identity
        # for provenance or worker-thread ownership, but they never define A
        # request/phase windows.  Only request/phase ranges enter the strict
        # window-validation path below.
        if identity.get("kind") not in {"request", "phase"}:
            continue
        try:
            key = _window_key(identity)
        except ABInputError:
            add_issue(None, "WINDOW_STRUCTURED_IDENTITY_INVALID", nvtx)
            continue
        if text_reason is not None:
            add_issue(key, text_reason, nvtx)
            continue
        groups.setdefault(key, {name: [] for name in _WINDOW_PHASES})[str(phase)].append((nvtx, identity))

    windows: list[RequestPhaseWindow] = []
    for key in sorted(groups):
        if key in issue_reasons:
            continue
        ranges = groups[key]
        if any(len(ranges[phase]) != 1 for phase in _WINDOW_PHASES):
            for phase in _WINDOW_PHASES:
                for nvtx, _ in ranges[phase]:
                    add_issue(key, "WINDOW_PHASE_MISSING_OR_DUPLICATE", nvtx)
            continue
        selected = {phase: ranges[phase][0] for phase in _WINDOW_PHASES}
        valid_times = True
        for nvtx, _ in selected.values():
            start, end = nvtx.get("start_ns"), nvtx.get("end_ns")
            if (
                not isinstance(start, int)
                or isinstance(start, bool)
                or not isinstance(end, int)
                or isinstance(end, bool)
                or start < 0
                or end < start
            ):
                valid_times = False
        if not valid_times:
            for nvtx, _ in selected.values():
                add_issue(key, "WINDOW_RANGE_INVALID", nvtx)
            continue
        full = selected["full_request"][0]
        prefill = selected["prefill"][0]
        decode = selected["decode"][0]
        if not (
            full["start_ns"] == prefill["start_ns"]
            and prefill["end_ns"] == decode["start_ns"]
            and decode["end_ns"] == full["end_ns"]
            and prefill["end_ns"] <= full["end_ns"]
        ):
            for nvtx, _ in selected.values():
                add_issue(key, "WINDOW_PHASE_BOUNDARY_INCONSISTENT", nvtx)
            continue
        for phase in _WINDOW_PHASES:
            nvtx, identity = selected[phase]
            windows.append(
                RequestPhaseWindow(
                    window_id=f"{nvtx['record_id']}:{phase}",
                    experiment_id=key[0],
                    wmpc_id=key[1],
                    run_id=key[2],
                    run_role=key[3],
                    pass_id=key[4],
                    request_id=key[5],
                    repeat_id=key[6],
                    phase=phase,
                    start_ns=nvtx["start_ns"],
                    end_ns=nvtx["end_ns"],
                    nvtx_record_id=str(nvtx["record_id"]),
                )
            )
    # Compare invocation windows only within their shared experiment/run/pass.
    # Never assign concurrent invocation ownership from timestamp overlap.
    # A trustworthy full_request is concurrency evidence even if its phase
    # ranges are missing.  Such a request cannot leave its neighbour valid.
    full_ranges = [
        (key, nvtx) for key, ranges in groups.items()
        for nvtx, _ in ranges["full_request"]
        if all(isinstance(nvtx.get(field), int) and not isinstance(nvtx[field], bool)
               for field in ("start_ns", "end_ns"))
        and 0 <= nvtx["start_ns"] < nvtx["end_ns"]
    ]
    full_ranges.sort(key=lambda item: (item[1]["start_ns"], item[1]["end_ns"], item[0]))
    active: dict[tuple[str, ...], list[tuple[tuple[str, ...], dict[str, Any]]]] = {}
    for key, nvtx in full_ranges:
        context = key[:5]
        previous = [other for other in active.get(context, []) if other[1]["end_ns"] > nvtx["start_ns"]]
        for other_key, other in previous:
            if other_key != key:
                for affected_key in (key, other_key):
                    for source in (nvtx, other):
                        add_issue(affected_key, "WINDOW_CROSS_INVOCATION_OVERLAP", source)
        previous.append((key, nvtx))
        active[context] = previous
    windows = [
        window for window in windows
        if tuple(getattr(window, field) for field in _IDENTITY_FIELDS) not in issue_reasons
    ]
    if not windows and not issue_reasons:
        # Marker-only or absent NVTX has no usable window identity, even when
        # the Canonical manifest and all B rows otherwise look valid.
        issue_reasons[None] = ["WINDOW_DISCOVERY_INVALID"]
        issue_sources[None] = [
            str(nvtx["record_id"]) for nvtx in canonical.records["nvtx"]
            if nvtx.get("record_id")
        ]
    phase_order = {phase: index for index, phase in enumerate(_WINDOW_PHASES)}
    windows.sort(
        key=lambda window: (
            window.experiment_id,
            window.wmpc_id,
            window.run_id,
            window.run_role,
            window.pass_id,
            window.request_id,
            window.repeat_id,
            phase_order[window.phase],
        )
    )
    issues = tuple(
        _issue_for_key(key, reasons, issue_sources.get(key, []))
        for key, reasons in sorted(
            issue_reasons.items(),
            key=lambda item: (item[0] is None, item[0] or ()),
        )
    )
    return tuple(windows), issues


def discover_request_phase_windows(canonical: CanonicalBundle) -> tuple[RequestPhaseWindow, ...]:
    """仅从结构化 NVTX identity 恢复窗口；从不按时间顺序猜测请求。"""

    return _discovery_result(canonical)[0]


def _global_quality_reasons(canonical: CanonicalBundle) -> tuple[str, ...]:
    reasons: list[str] = []
    observation = canonical.manifest.get("observation_validity")
    if not isinstance(observation, Mapping) or str(observation.get("status", "")).lower() != "valid":
        reasons.append("TRACE_DROPPED_RECORDS")
    else:
        issues = observation.get("issues", [])
        if isinstance(issues, list) and any(
            isinstance(issue, Mapping) and "DROP" in str(issue.get("code", "")).upper()
            for issue in issues
        ):
            reasons.append("TRACE_DROPPED_RECORDS")
    if canonical.manifest.get("clock") != canonical.schema.get("clock_model") or any(
        record.get("clock_domain_id") != canonical.schema["clock_model"]["clock_domain_id"]
        for rows in canonical.records.values()
        for record in rows
    ):
        reasons.append("CLOCK_DOMAIN_UNRESOLVED")
    identity = canonical.manifest.get("identity")
    if not isinstance(identity, Mapping) or str(identity.get("status", "")).upper() != "VALID":
        reasons.append("INVOCATION_OWNERSHIP_AMBIGUOUS")
    return tuple(dict.fromkeys(reasons))


def load_ab_inputs(canonical_manifest: Path, s_manifest: Path) -> ABInputs:
    """严格加载且联结 Canonical Raw 与 S bundle，不写出任何 A/B 产物。"""

    canonical_manifest = Path(canonical_manifest).resolve()
    canonical = _load_canonical(canonical_manifest)
    loaded_s_manifest, s_records = _load_s_records(s_manifest)
    _validate_lineage(canonical_manifest, canonical, loaded_s_manifest)
    _validate_s_join(canonical, s_records)
    windows, window_issues = _discovery_result(canonical)
    return ABInputs(
        canonical=canonical,
        s_manifest=dict(loaded_s_manifest),
        s_records=tuple(dict(record) for record in s_records),
        windows=windows,
        global_quality_reasons=_global_quality_reasons(canonical),
        window_discovery_issues=window_issues,
    )
