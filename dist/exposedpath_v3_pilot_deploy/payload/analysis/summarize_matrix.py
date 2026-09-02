#!/usr/bin/env python3
"""
Aggregate v2 accounting results into matrix summary JSON + CSV.

Phase-split B distributions, tiered quality (hard_gate / latency_stability /
decomposition_stability), rerun candidates, invalid reason breakdowns.

Usage:
    python analysis/summarize_matrix.py <matrix_dir> [<output_path>]
    python analysis/summarize_matrix.py --results-dir <dir> --strict
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

METRIC_VERSION = "exposedpath-v2"

A_CATEGORIES = [
    "A_host_path", "A_cuda_api", "A_device_wait",
    "A_sync_residual", "A_unattributed",
]

OVERLAP_METRICS = ["O_api_gpu", "O_hostpath_gpu"]

B_PHASES = ["prefill", "decode"]

B_DIST_KEYS = [
    "B_predecessor_ms", "B_stream_gap_ms", "B_self_ms",
    "sync_return_tail_ms", "device_overlap_with_sync_ms",
    "wait_set_size",
]

ALL_INVALID_REASONS = [
    "NO_SYNC_RECORD", "MISSING_STREAM_ID", "MISSING_CONTEXT_ID",
    "MISSING_EVENT_MAP", "MISSING_CORRELATION", "DROPPED_TRACE_RECORDS",
    "NO_PENDING_ACTIVITY", "EXTERNAL_ACTIVITY", "UNSUPPORTED_SYNC_TYPE",
    "UNSUPPORTED_EVENT_DEPENDENCY", "TRACE_ORDERING_ERROR", "MULTI_TERMINAL",
]

# Small-component CV filtering: only components with >=5% share OR >=1ms mean
SMALL_COMPONENT_PCT_THRESHOLD = 5.0
SMALL_COMPONENT_MS_THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_git_commit() -> str | None:
    try:
        import subprocess
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=5,
        )
        return r.stdout.strip()[:12] if r.returncode == 0 else None
    except Exception:
        return None


def sample_std(values: list[float]) -> float | None:
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (n - 1))


def percentile(values: list[float], p: float) -> float | None:
    if not values:
        return None
    s = sorted(values)
    k = (p / 100) * (len(s) - 1)
    f = int(k)
    c = k - f
    if f + 1 < len(s):
        return s[f] + c * (s[f + 1] - s[f])
    return s[f]


def cv_pct(values: list[float]) -> float | None:
    """CV = sample_std / |mean| * 100. None if n<2 or mean≈0."""
    n = len(values)
    if n < 2:
        return None
    mean = sum(values) / n
    if abs(mean) < 1e-9:
        return None
    std = sample_std(values)
    if std is None:
        return None
    return std / abs(mean) * 100


def _agg(values: list[float]) -> dict:
    if not values:
        return {"mean": None, "std": None, "median": None, "IQR": None,
                "CV": None, "p90": None, "p95": None}
    n = len(values)
    mean = sum(values) / n
    std = sample_std(values)
    med = percentile(values, 50)
    q1 = percentile(values, 25)
    q3 = percentile(values, 75)
    iqr = (q3 - q1) if q1 is not None and q3 is not None else None
    cv = cv_pct(values)
    return {
        "mean": round(mean, 4),
        "std": round(std, 4) if std is not None else None,
        "median": round(med, 4) if med is not None else None,
        "IQR": round(iqr, 4) if iqr is not None else None,
        "CV": round(cv, 2) if cv is not None else None,
        "p90": round(percentile(values, 90), 4) if percentile(values, 90) is not None else None,
        "p95": round(percentile(values, 95), 4) if percentile(values, 95) is not None else None,
    }


def _latency_stability(cv: float | None) -> str:
    if cv is None:
        return "stable"
    if cv <= 5:
        return "stable"
    if cv <= 10:
        return "warning"
    if cv <= 15:
        return "rerun_recommended"
    return "unstable"


def _component_is_significant(mean_val: float | None, pct_val: float | None) -> bool:
    """True if this A component should contribute to decomposition stability."""
    if mean_val is None:
        return False
    if mean_val >= SMALL_COMPONENT_MS_THRESHOLD:
        return True
    if pct_val is not None and pct_val >= SMALL_COMPONENT_PCT_THRESHOLD:
        return True
    return False


# ---------------------------------------------------------------------------
# Load + validate
# ---------------------------------------------------------------------------

def load_accounting(acc_dir: Path) -> dict | None:
    f = acc_dir / "accounting_result.json"
    if not f.exists():
        return None
    with open(f, encoding="utf-8") as fh:
        return json.load(fh)


def validate_workload(acc: dict, strict: bool = False) -> tuple[list[str], list[str]]:
    errors, warnings = [], []
    ver = acc.get("metric_definition_version", "")
    if ver != METRIC_VERSION:
        errors.append(f"version mismatch: {ver}")
    gc = acc.get("metadata", {}).get("git_commit")
    if gc is None:
        if strict:
            errors.append("git_commit is null")
        else:
            warnings.append("git_commit is null")
    return errors, warnings


# ---------------------------------------------------------------------------
# Per-workload extraction
# ---------------------------------------------------------------------------

def _phase_b_stats(b_details: list, phase: str) -> dict:
    """Extract per-phase B distribution from canonical b_sync_details."""
    phase_b = [bd for bd in b_details if bd.get("phase") == phase]
    out: dict = {}
    out[f"{phase}_physical_sync_count"] = len(phase_b)
    out[f"{phase}_B_valid_count"] = sum(1 for bd in phase_b if bd.get("B_valid"))
    out[f"{phase}_B_invalid_count"] = out[f"{phase}_physical_sync_count"] - out[f"{phase}_B_valid_count"]
    out[f"{phase}_B_valid_coverage"] = round(
        out[f"{phase}_B_valid_count"] / max(out[f"{phase}_physical_sync_count"], 1), 4
    ) if out[f"{phase}_physical_sync_count"] > 0 else None

    # B distribution (B_valid only)
    valid_b = [bd for bd in phase_b if bd.get("B_valid")]
    for dk in B_DIST_KEYS:
        d_vals = [bd.get(dk) for bd in valid_b if bd.get(dk) is not None]
        if d_vals:
            da = _agg(d_vals)
            for stat in ["median", "p90", "p95"]:
                out[f"{phase}_{dk}_{stat}"] = da.get(stat)

    # Terminal types
    t_k = sum(1 for bd in valid_b if bd.get("terminal_type") == "kernel")
    t_m = sum(1 for bd in valid_b if bd.get("terminal_type") == "memcpy")
    t_ms = sum(1 for bd in valid_b if bd.get("terminal_type") == "memset")
    out[f"{phase}_terminal_kernel_count"] = t_k
    out[f"{phase}_terminal_memcpy_count"] = t_m
    out[f"{phase}_terminal_memset_count"] = t_ms
    n = max(len(valid_b), 1)
    out[f"{phase}_terminal_kernel_share"] = round(t_k / n, 4)
    out[f"{phase}_terminal_memcpy_share"] = round(t_m / n, 4)
    out[f"{phase}_terminal_memset_share"] = round(t_ms / n, 4)

    # Sync types
    out[f"{phase}_stream_sync_count"] = sum(1 for bd in phase_b if bd.get("sync_type") == "stream")
    out[f"{phase}_device_sync_count"] = sum(1 for bd in phase_b if bd.get("sync_type") == "device")
    out[f"{phase}_event_sync_count"] = sum(1 for bd in phase_b if bd.get("sync_type") == "event")

    # Ownership (B_valid syncs only)
    valid_phase_b = [bd for bd in phase_b if bd.get("B_valid")]
    out[f"{phase}_terminal_ownership_valid_count"] = sum(1 for bd in valid_phase_b if bd.get("terminal_ownership_valid"))
    out[f"{phase}_terminal_ownership_coverage"] = round(
        out[f"{phase}_terminal_ownership_valid_count"] / max(len(valid_phase_b), 1), 4
    ) if valid_phase_b else None
    out[f"{phase}_wait_set_external_count"] = sum(bd.get("wait_set_external_count", 0) or 0 for bd in phase_b)
    out[f"{phase}_wait_set_unassigned_count"] = sum(bd.get("wait_set_unassigned_count", 0) or 0 for bd in phase_b)
    out[f"{phase}_cross_phase_terminal_count"] = sum(1 for bd in phase_b if bd.get("cross_phase_wait_flag"))
    out[f"{phase}_timestamp_tolerance_applied_count"] = sum(1 for bd in phase_b if bd.get("timestamp_tolerance_applied"))

    # Invalid reason counts
    ir_counts: dict[str, int] = defaultdict(int)
    for bd in phase_b:
        reason = bd.get("invalid_reason", "")
        if reason:
            ir_counts[reason] += 1
    for reason in ALL_INVALID_REASONS:
        out[f"{phase}_B_invalid_{reason}_count"] = ir_counts.get(reason, 0)

    return out


def extract_workload(acc: dict, workload_id: str) -> dict:
    """Extract per-workload aggregate from v2 accounting_result."""
    repeat_results = acc.get("repeat_results", [])
    b_details_raw = acc.get("b_sync_details", [])
    meta = acc.get("metadata", {})
    tq = acc.get("trace_quality", {})

    if not repeat_results:
        return {}

    # Normalize b_sync_details (may be dataclass objects or dicts)
    b_details = []
    for bd in (b_details_raw or []):
        if hasattr(bd, 'get'):
            b_details.append(bd)

    by_phase: dict[str, list[dict]] = defaultdict(list)
    for row in repeat_results:
        by_phase[row.get("phase", "")].append(row)

    out: dict = {
        "workload_id": workload_id,
        "metric_definition_version": acc.get("metric_definition_version", ""),
        "gpu_name": meta.get("gpu_name"),
        "prompt_len": meta.get("prompt_len", 0),
        "batch_size": meta.get("batch_size", 0),
        "output_len": meta.get("output_len", 0),
        "num_repeats": len(by_phase.get("full_request", [])),
        "schema_version": meta.get("schema_version"),
        "nsys_product_version": meta.get("nsys_product_version"),
        # Profiling overhead placeholder
        "profiling_overhead_pct": None,
        "profiling_overhead_measured": False,
    }

    # ---- Per-phase A, Raw, Overlap, Throughput ----
    for phase in ["prefill", "decode", "full_request"]:
        rows = by_phase.get(phase, [])
        if not rows:
            continue

        # Window latency
        win_vals = [r.get("window_duration_ms", 0) or 0 for r in rows]
        w = _agg(win_vals)
        for stat in ["mean", "std", "median", "IQR", "CV"]:
            out[f"{phase}_latency_ms_{stat}"] = w.get(stat)

        # A categories
        for cat in A_CATEGORIES:
            ms_vals = [r.get(f"{cat}_ms", 0) or 0 for r in rows]
            pct_vals = [r.get(f"{cat}_pct", 0) or 0 for r in rows]
            a = _agg(ms_vals)
            for stat in ["mean", "std", "median", "IQR", "CV"]:
                out[f"{phase}_{cat}_ms_{stat}"] = a.get(stat)
            pct_a = _agg(pct_vals)
            out[f"{phase}_{cat}_pct_mean"] = pct_a.get("mean")

        # Conservation
        cons_vals = [r.get("conservation_error_pct", 0) or 0 for r in rows]
        out[f"{phase}_conservation_error_pct_max"] = round(max(cons_vals), 4) if cons_vals else None

        # Overlap
        for om in OVERLAP_METRICS:
            ov_vals = [r.get(om) for r in rows if r.get(om) is not None]
            if ov_vals:
                oa = _agg(ov_vals)
                out[f"{phase}_{om}_mean"] = oa.get("mean")
                out[f"{phase}_{om}_std"] = oa.get("std")

        # Throughput: ratio-of-sums = sum(tokens) / sum(latency_s)
        token_vals = [r.get("tokens_in_phase") for r in rows if r.get("tokens_in_phase") is not None]
        lat_vals = [r.get("window_duration_ms") for r in rows if r.get("window_duration_ms") is not None]
        if token_vals and lat_vals and len(token_vals) == len(lat_vals):
            total_tokens = sum(token_vals)
            total_latency_s = sum(lat_vals) / 1000.0
            if total_latency_s > 0 and total_tokens > 0:
                if phase == "prefill":
                    out["prefill_input_tokens_per_second"] = round(total_tokens / total_latency_s, 1)
                elif phase == "decode":
                    out["decode_output_tokens_per_second"] = round(total_tokens / total_latency_s, 1)
                elif phase == "full_request":
                    out["full_request_total_tokens_per_second"] = round(total_tokens / total_latency_s, 1)

        # TTFT / TPOT proxies
        if phase == "prefill":
            for tk in ["ttft_proxy_ms"]:
                t_vals = [r.get(tk) for r in rows if r.get(tk) is not None]
                if t_vals:
                    ta = _agg(t_vals)
                    out[f"{phase}_{tk}_mean"] = ta.get("mean")
        if phase == "decode":
            for tk in ["tpot_proxy_ms"]:
                t_vals = [r.get(tk) for r in rows if r.get(tk) is not None]
                if t_vals:
                    ta = _agg(t_vals)
                    out[f"{phase}_{tk}_mean"] = ta.get("mean")

        # Raw
        raw_keys = [
            "cuda_api_count", "cuda_api_union_ms", "launch_api_count", "sync_api_count",
            "kernel_count", "kernel_union_ms",
            "memcpy_count", "memcpy_bytes", "memcpy_union_ms",
            "memset_count", "gpu_activity_union_ms", "gpu_active_ratio",
            "distinct_stream_count", "multistream_ratio",
        ]
        for rk in raw_keys:
            r_vals = [r.get(rk) for r in rows if r.get(rk) is not None]
            if r_vals:
                ra = _agg(r_vals)
                out[f"{phase}_{rk}_mean"] = ra.get("mean")
                out[f"{phase}_{rk}_std"] = ra.get("std")

    # ---- Phase-split B ----
    if b_details:
        for ph in B_PHASES:
            out.update(_phase_b_stats(b_details, ph))

        # Global B (keep for backward compat)
        b_count = len(b_details)
        b_valid = sum(1 for bd in b_details if bd.get("B_valid"))
        out["physical_sync_count"] = b_count
        out["unique_physical_sync_uid_count"] = len(set(bd.get("physical_sync_uid", "") for bd in b_details))
        out["duplicate_physical_sync_count"] = b_count - out["unique_physical_sync_uid_count"]
        out["B_valid_count"] = b_valid
        out["B_invalid_count"] = b_count - b_valid

        # Global B valid coverage (count-weighted from repeat_results)
        valid_total = sum(r.get("B_valid_count", 0) or 0 for r in repeat_results)
        supp_total = sum(r.get("sync_supported_count", 0) or 0 for r in repeat_results)
        out["B_valid_coverage"] = round(valid_total / supp_total, 4) if supp_total > 0 else None

        # Global terminal ownership (B_valid syncs only)
        b_valid_list = [bd for bd in b_details if bd.get("B_valid")]
        out["terminal_ownership_valid_count"] = sum(1 for bd in b_valid_list if bd.get("terminal_ownership_valid"))
        out["terminal_ownership_coverage"] = round(
            out["terminal_ownership_valid_count"] / max(len(b_valid_list), 1), 4
        ) if b_valid_list else None
    else:
        out["physical_sync_count"] = 0

    # ---- Trace quality passthrough ----
    out["gpu_api_correlation_coverage"] = tq.get("correlation_coverage")
    out["conservation_error_pct_max"] = tq.get("conservation_error_max")
    out["dropped_records_status"] = tq.get("dropped_records_status", "unknown")
    out["global_nvtx_assignment_coverage"] = tq.get("global_api_assignment_coverage")
    out["request_api_assignment_coverage"] = tq.get("in_request_api_assignment_coverage")

    # ---- Quality: tiered ----
    # Hard gate
    hard_fail = False
    if b_details:
        if out.get("duplicate_physical_sync_count", 0) != 0:
            hard_fail = True
        if out.get("terminal_ownership_coverage") is not None and out["terminal_ownership_coverage"] < 1.0:
            hard_fail = True
        if sum(out.get(f"{ph}_wait_set_external_count", 0) or 0 for ph in B_PHASES) > 0:
            hard_fail = True
        if sum(out.get(f"{ph}_wait_set_unassigned_count", 0) or 0 for ph in B_PHASES) > 0:
            hard_fail = True
    out["hard_gate_status"] = "fail" if hard_fail else "pass"

    # Latency stability (window duration CV only)
    lat_cvs = []
    for phase in ["prefill", "decode", "full_request"]:
        cv = out.get(f"{phase}_latency_ms_CV")
        if cv is not None:
            lat_cvs.append(cv)
    max_lat_cv = max(lat_cvs) if lat_cvs else None
    out["latency_stability_status"] = _latency_stability(max_lat_cv)
    out["latency_stability_max_CV"] = round(max_lat_cv, 2) if max_lat_cv is not None else None

    # Decomposition stability (significant A components only)
    decomp_cvs = []
    decomp_details = []
    for phase in ["prefill", "decode", "full_request"]:
        for cat in A_CATEGORIES:
            ms_mean = out.get(f"{phase}_{cat}_ms_mean")
            pct_mean = out.get(f"{phase}_{cat}_pct_mean")
            cv_val = out.get(f"{phase}_{cat}_ms_CV")
            if cv_val is not None and _component_is_significant(ms_mean, pct_mean):
                decomp_cvs.append(cv_val)
            elif cv_val is not None and cv_val > 15:
                decomp_details.append(f"{phase}/{cat} CV={cv_val:.1f}% (small component, diagnostic only)")
    max_decomp_cv = max(decomp_cvs) if decomp_cvs else None
    out["decomposition_stability_status"] = _latency_stability(max_decomp_cv)
    out["decomposition_stability_max_CV"] = round(max_decomp_cv, 2) if max_decomp_cv is not None else None
    out["decomposition_stability_diagnostics"] = decomp_details

    # Overall
    if hard_fail:
        overall = "fail"
    elif out["latency_stability_status"] in ("unstable", "rerun_recommended"):
        overall = out["latency_stability_status"]
    elif out["decomposition_stability_status"] in ("unstable", "rerun_recommended"):
        overall = "warning"
    else:
        overall = "pass"
    out["overall_quality_status"] = overall
    out["rerun_recommended"] = overall in ("rerun_recommended", "unstable", "fail")

    return out


# ---------------------------------------------------------------------------
# Matrix-level
# ---------------------------------------------------------------------------

def _build_rerun_candidates(workloads: list[dict]) -> list[dict]:
    candidates = []
    for w in workloads:
        for phase in ["prefill", "decode", "full_request"]:
            cv = w.get(f"{phase}_latency_ms_CV")
            if cv is not None and cv > 10:
                candidates.append({
                    "workload_id": w["workload_id"],
                    "gpu_name": w.get("gpu_name"),
                    "phase": phase,
                    "metric": f"{phase}_latency_ms",
                    "CV": cv,
                    "reason": _latency_stability(cv),
                })
    candidates.sort(key=lambda x: x["CV"], reverse=True)
    return candidates


def _flatten_workloads(workloads: list[dict]) -> list[str]:
    fixed = [
        "workload_id", "gpu_name", "prompt_len", "batch_size", "output_len",
        "num_repeats", "metric_definition_version",
    ]
    seen = set(fixed)
    cols = list(fixed)
    for wd in workloads:
        for key in sorted(wd.keys()):
            if key not in seen:
                seen.add(key)
                cols.append(key)
    return cols


def write_matrix_csv(path: Path, workloads: list[dict]):
    if not workloads:
        return
    columns = _flatten_workloads(workloads)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for wd in workloads:
            writer.writerow(wd)
    print(f"  → {path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="ExposedPath v2 Matrix Summary")
    parser.add_argument("results_dir", nargs="?", default=".")
    parser.add_argument("output_path", nargs="?", default=None)
    parser.add_argument("--accounting-dir-name", default="accounting")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    matrix_dir = Path(args.results_dir)
    if not matrix_dir.exists():
        print(f"ERROR: Directory not found: {matrix_dir}")
        sys.exit(1)

    out_path = Path(args.output_path) if args.output_path else (matrix_dir / "matrix_summary.json")
    acc_name = args.accounting_dir_name

    acc_dirs = sorted(matrix_dir.glob(f"*/{acc_name}"))
    if not acc_dirs:
        acc_dirs = sorted(matrix_dir.glob(f"*/*/{acc_name}"))
    print(f"  Found {len(acc_dirs)} accounting dir(s)")

    if not acc_dirs:
        print("No accounting results found.")
        return

    git_commit_current = _get_git_commit()
    workloads_data, excluded, failed, warnings = [], [], [], []
    git_commits: set[str] = set()
    schema_versions: set[str] = set()
    nsys_versions: set[str] = set()
    gpu_names: set[str] = set()

    for acc_dir in acc_dirs:
        wid = acc_dir.parent.name
        acc = load_accounting(acc_dir)
        if acc is None:
            excluded.append({"workload": wid, "reason": "no accounting_result.json"})
            print(f"  SKIP {wid}: no accounting_result.json")
            continue

        errors, warns = validate_workload(acc, strict=args.strict)
        if errors:
            excluded.append({"workload": wid, "reason": "; ".join(errors)})
            print(f"  SKIP {wid}: {'; '.join(errors)}")
            continue
        if warns:
            print(f"  WARNING {wid}: {'; '.join(warns)}")

        meta = acc.get("metadata", {})
        gc = meta.get("git_commit")
        if gc:
            git_commits.add(gc)
        sv = meta.get("schema_version")
        if sv:
            schema_versions.add(str(sv))
        nv = meta.get("nsys_product_version")
        if nv:
            nsys_versions.add(str(nv))
        gn = meta.get("gpu_name")
        if gn:
            gpu_names.add(str(gn))

        flat = extract_workload(acc, wid)
        if not flat or flat.get("num_repeats", 0) == 0:
            excluded.append({"workload": wid, "reason": "no repeat_results"})
            print(f"  SKIP {wid}: no repeat results")
            continue

        workloads_data.append(flat)
        qs = flat.get("overall_quality_status", "?")
        hg = flat.get("hard_gate_status", "?")
        flag = f"  hard={hg} overall={qs}"
        if hg == "fail":
            failed.append(wid)
        elif flat.get("rerun_recommended"):
            warnings.append(wid)
        print(f"  {wid}: {flat['num_repeats']} reps, {flat.get('physical_sync_count', 0)} syncs, {flag}")

    if not workloads_data:
        print("No valid v2 workloads found.")
        return

    # Git consistency
    if len(git_commits) > 1:
        msg = f"Mixed git commits: {git_commits}"
        warnings.append(msg)
        print(f"  WARNING: {msg}")
        if args.strict:
            print("ERROR: strict mode — mixed git commits")
            sys.exit(1)

    rerun = _build_rerun_candidates(workloads_data)

    matrix_quality = {
        "included_workload_count": len(workloads_data),
        "excluded_workload_count": len(excluded),
        "failed_workload_count": len(failed),
        "warning_count": len(warnings),
        "git_commits": sorted(git_commits),
        "git_commit_current": git_commit_current,
        "schema_versions": sorted(schema_versions),
        "nsys_product_versions": sorted(nsys_versions),
        "gpu_names": sorted(gpu_names),
    }

    summary = {
        "metadata": {
            "metric_definition_version": METRIC_VERSION,
            "parser_version": METRIC_VERSION,
            "git_commit": git_commit_current,
            "schema_versions": sorted(schema_versions),
            "nsys_product_versions": sorted(nsys_versions),
            "gpu_names": sorted(gpu_names),
            "generation_timestamp": __import__('datetime').datetime.now(
                __import__('datetime').timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "source_root": str(matrix_dir.resolve()),
            "workload_count": len(workloads_data),
            "included_workload_count": len(workloads_data),
            "excluded_workload_count": len(excluded),
            "failed_workload_count": len(failed),
            "warning_count": len(warnings),
            "accounting_dir_name": acc_name,
        },
        "quality_policy": {
            "latency_cv_stable": 5.0,
            "latency_cv_warning": 10.0,
            "latency_cv_rerun": 15.0,
            "small_component_pct_threshold": SMALL_COMPONENT_PCT_THRESHOLD,
            "small_component_ms_threshold": SMALL_COMPONENT_MS_THRESHOLD,
            "hard_gates": [
                "duplicate_physical_sync_count == 0",
                "terminal_ownership_coverage == 1.0",
                "wait_set_external_count == 0",
                "wait_set_unassigned_count == 0",
            ],
        },
        "matrix_quality": matrix_quality,
        "rerun_candidates": rerun,
        "legacy_removed_fields": [
            "A_device_compute", "A_memory_transfer", "A_submit", "A_host_runtime",
            "b_exposed_ms", "b_self_block_ms", "b_kernel_block_ms",
            "b_memory_block_ms", "b_device_gap_ms", "b_top_motif",
            "exposed_total_ms", "hidden_total_ms", "coverage_pct",
        ],
        "workloads": workloads_data,
        "excluded_workloads": excluded,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n  Wrote {out_path} ({len(workloads_data)} workloads)")

    csv_path = out_path.with_suffix(".csv")
    write_matrix_csv(csv_path, workloads_data)

    print(f"\n{'='*60}")
    print(f"  Matrix Summary Complete")
    print(f"  Workloads included: {len(workloads_data)}")
    print(f"  Quality passed:     {len(workloads_data) - len(failed)}")
    print(f"  Quality warned:     {len(warnings)}")
    print(f"  Quality failed:     {len(failed)}")
    print(f"  Rerun candidates:   {len(rerun)}")
    print(f"  matrix_summary.json: {out_path}")
    print(f"  matrix_summary.csv:  {csv_path}")
    print(f"{'='*60}")

    if args.strict and failed:
        print("strict mode: hard gate failures")
        sys.exit(1)


if __name__ == "__main__":
    main()
