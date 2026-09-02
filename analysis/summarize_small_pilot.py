#!/usr/bin/env python3
"""Summarize small-pilot results. Reads canonical analyzer output fields."""

from __future__ import annotations
import argparse, csv, json, math, sys
from collections import Counter
from pathlib import Path

def _mean(vals): return sum(vals)/len(vals) if vals else None
def _std(vals):
    if not vals or len(vals)<2: return None
    m=_mean(vals); return math.sqrt(sum((x-m)**2 for x in vals)/(len(vals)-1))
def _cv(vals):
    if not vals: return None
    m=_mean(vals); return _std(vals)/m if m and m!=0 else None
def _median(vals):
    if not vals: return None
    s=sorted(vals); n=len(s); return (s[n//2]+s[(n-1)//2])/2

FIELD_MAP = {
    "sync_count_total":     "total_syncs",
    "sync_count_valid":     "B_valid",
    "sync_count_supported": "total_syncs",
    "B_valid_coverage":     "B_valid_coverage",
}

def _read_analyzer_sync(ar: dict, phase="full_request"):
    """Extract sync fields from canonical analyzer output (B_summary.<phase>)."""
    bs = ar.get("B_summary", {})
    ph = bs.get(phase, {})
    # Also try prefill+decode aggregate
    if not ph:
        pf = bs.get("prefill", {}); dc = bs.get("decode", {})
        ph = {
            "total_syncs": pf.get("total_syncs",0)+dc.get("total_syncs",0),
            "B_valid": pf.get("B_valid",0)+dc.get("B_valid",0),
            "B_invalid": pf.get("B_invalid",0)+dc.get("B_invalid",0),
            "B_valid_coverage": None,
        }
        total = ph["total_syncs"]
        if total:
            ph["B_valid_coverage"] = round(ph["B_valid"]/total, 4)
    tq = ar.get("trace_quality", {})
    return {
        "sync_count_total": ph.get("total_syncs"),
        "sync_count_supported": ph.get("total_syncs"),
        "sync_count_valid": ph.get("B_valid"),
        "sync_duration_total_ms":  None,  # not in canonical A_summary
        "sync_duration_supported_ms": None,
        "sync_duration_valid_ms": None,
        "count_coverage_pct": round(ph.get("B_valid_coverage",0)*100,1) if ph.get("B_valid_coverage") is not None else None,
        "duration_coverage_pct": None,
        "a_conservation": "present" if ar.get("A_summary") else "missing",
        "conservation_error_max": tq.get("conservation_error_max"),
        "B_valid_coverage_global": tq.get("B_valid_coverage"),
    }

def summarize(pilot_root: Path):
    rows=[]
    gpu_uuids = {}
    for wmpc_dir in sorted(pilot_root.iterdir()):
        if not wmpc_dir.is_dir(): continue
        wid=wmpc_dir.name
        row={"id":wid}

        # GPU identity: pilot_identity.json FIRST, then wmpc_manifest.json
        idf = wmpc_dir / "pilot_identity.json"
        mf  = wmpc_dir / "wmpc_manifest.json"
        if idf.exists():
            try:
                ident=json.loads(idf.read_text())
                row["gpu_uuid"]=ident.get("gpu_uuid")
                row["gpu_name"]=ident.get("gpu_name")
                row["gpu_pci_bus_id"]=ident.get("gpu_pci_bus_id")
                row["gpu_index"]=ident.get("requested_gpu_index")
                if row.get("gpu_uuid"): gpu_uuids[wid]=row["gpu_uuid"]
            except: pass
        if not row.get("gpu_uuid") and mf.exists():
            try:
                m=json.loads(mf.read_text())
                row["gpu_uuid"]=m.get("gpu_uuid")
                row["gpu_name"]=m.get("gpu_name")
                row["gpu_pci_bus_id"]=m.get("gpu_pci_bus_id")
                row["gpu_index"]=m.get("gpu_index")
                if row.get("gpu_uuid"): gpu_uuids[wid]=row["gpu_uuid"]
            except: pass

        # Pass 0
        p0f = wmpc_dir / "pass0" / "inference_results.jsonl"
        p0_exf = wmpc_dir / "pass0" / "exclusion_log.jsonl"
        p0_latency=[]
        p0_exc=0
        if p0f.exists():
            try:
                recs=[json.loads(l) for l in p0f.read_text().splitlines() if l.strip()]
                p0_latency=[r["inference_e2e_latency_ms"] for r in recs if r.get("attempt_status")=="success"]
            except: pass
        if p0_exf.exists():
            try: p0_exc=len([l for l in p0_exf.read_text().splitlines() if l.strip()])
            except: pass
        row["pass0_count"]=len(p0_latency)
        row["pass0_exclusions"]=p0_exc
        row["pass0_mean_ms"]=round(_mean(p0_latency),3) if p0_latency else None
        row["pass0_median_ms"]=round(_median(p0_latency),3) if p0_latency else None
        row["pass0_std_ms"]=round(_std(p0_latency),3) if p0_latency else None
        row["pass0_cv_pct"]=round(_cv(p0_latency)*100,2) if p0_latency and _cv(p0_latency) else None
        row["pass0_min_ms"]=round(min(p0_latency),3) if p0_latency else None
        row["pass0_max_ms"]=round(max(p0_latency),3) if p0_latency else None

        # Pass 1
        p1f = wmpc_dir / "pass1" / "inference_results.jsonl"
        p1_latency=[]
        if p1f.exists():
            try:
                recs=[json.loads(l) for l in p1f.read_text().splitlines() if l.strip()]
                p1_latency=[r["inference_e2e_latency_ms"] for r in recs if r.get("attempt_status")=="success"]
            except: pass
        row["pass1_count"]=len(p1_latency)
        row["pass1_mean_ms"]=round(_mean(p1_latency),3) if p1_latency else None
        row["pass1_median_ms"]=round(_median(p1_latency),3) if p1_latency else None

        # Profiler overhead: use MEDIAN (robust to outliers)
        p0_med = _median(p0_latency); p1_med = _median(p1_latency)
        if p0_med and p0_med > 0 and p1_med:
            row["pass1_to_pass0_ratio"] = round(p1_med / p0_med, 4)
            row["profiler_overhead_pct"] = round((p1_med - p0_med) / p0_med * 100, 2)
        else:
            row["pass1_to_pass0_ratio"] = None
            row["profiler_overhead_pct"] = None

        # Timing sanity check
        ratio = row.get("pass1_to_pass0_ratio")
        row["timing_anomaly"] = None
        if ratio is not None and ratio < 0.9:
            row["timing_anomaly"] = "PASS_TIMING_MISMATCH"
        elif ratio is not None and ratio < 1.0:
            row["timing_anomaly"] = "PASS1_FASTER_THAN_PASS0_UNEXPECTED"

        # Throughput
        if p0_latency and p0f.exists():
            try:
                recs=[json.loads(l) for l in p0f.read_text().splitlines() if l.strip()]
                total_tokens=sum(r.get("actual_output_tokens",0) for r in recs)
                total_lat=sum(p0_latency)
                row["throughput_tokens_per_sec"]=round(total_tokens/total_lat*1000,1) if total_lat>0 else None
            except: row["throughput_tokens_per_sec"]=None
        else:
            row["throughput_tokens_per_sec"]=None

        # REP / SQLite size
        rep = wmpc_dir / "pass1" / "pass1_profile.nsys-rep"
        sql = wmpc_dir / "pass1" / "pass1_profile.sqlite"
        row["rep_size_mb"]=round(rep.stat().st_size/1e6,2) if rep.exists() else None
        row["sqlite_size_mb"]=round(sql.stat().st_size/1e6,2) if sql.exists() else None

        # Analyzer: read canonical fields from accounting_result.json
        a_dirs=sorted((wmpc_dir/"analysis").iterdir()) if (wmpc_dir/"analysis").is_dir() else []
        if a_dirs:
            ar_file=a_dirs[-1]/"accounting_result.json"
            if ar_file.exists():
                try:
                    ar=json.loads(ar_file.read_text())
                    sync=_read_analyzer_sync(ar)
                    row.update(sync)
                except: pass

        # Repeat advice: separate CV-based from quality
        p0_cv=_cv(p0_latency)
        excl_rate=(p0_exc/max(row["pass0_count"]+p0_exc,1))*100 if row["pass0_count"] is not None else None
        if p0_cv is None: row["pass0_cv_based_advice"]="PASS0_5_LIKELY_ENOUGH"
        elif p0_cv<=0.03: row["pass0_cv_based_advice"]="PASS0_5_LIKELY_ENOUGH"
        elif p0_cv<=0.05: row["pass0_cv_based_advice"]="CONSIDER_PASS0_10"
        else: row["pass0_cv_based_advice"]="CONSIDER_PASS0_20"

        # Data quality
        qual_issues=[]
        cov = row.get("count_coverage_pct")
        if cov is not None and cov < 90: qual_issues.append(f"count_coverage={cov}%")
        if excl_rate is not None and excl_rate > 5: qual_issues.append(f"exclusion_rate={excl_rate:.1f}%")
        row["data_quality_status"]="OK" if not qual_issues else "BLOCKED: "+"; ".join(qual_issues)
        row["final_repeat_advice"]="DATA_QUALITY_BLOCKED" if qual_issues else row["pass0_cv_based_advice"]
        rows.append(row)

    # GPU UUID consistency
    unique_uuids = set(v for v in gpu_uuids.values() if v)
    if len(unique_uuids) > 1:
        for r in rows: r["pilot_status"]="INVALID_MIXED_GPU"
    elif len(unique_uuids)==0:
        for r in rows: r["pilot_status"]="NO_GPU_UUID"
    else:
        for r in rows: r["pilot_status"]="OK"

    return rows

def main():
    p=argparse.ArgumentParser(description="Summarize small pilot results")
    p.add_argument("--pilot-root",required=True)
    args=p.parse_args()
    root=Path(args.pilot_root)
    if not root.is_dir(): print(f"ERROR: {root} not found"); sys.exit(1)
    rows=summarize(root)
    if not rows: print("No WMPC directories found"); sys.exit(1)

    # Uniform key order
    all_keys = ["id","gpu_uuid","gpu_name","gpu_pci_bus_id","gpu_index",
        "pass0_count","pass0_exclusions","pass0_mean_ms","pass0_median_ms","pass0_std_ms",
        "pass0_cv_pct","pass0_min_ms","pass0_max_ms",
        "pass1_count","pass1_mean_ms","pass1_median_ms",
        "pass1_to_pass0_ratio","profiler_overhead_pct","timing_anomaly",
        "throughput_tokens_per_sec","rep_size_mb","sqlite_size_mb",
        "sync_count_total","sync_count_supported","sync_count_valid",
        "sync_duration_total_ms","sync_duration_supported_ms","sync_duration_valid_ms",
        "count_coverage_pct","duration_coverage_pct","a_conservation","conservation_error_max",
        "pass0_cv_based_advice","data_quality_status","final_repeat_advice","pilot_status"]
    # Ensure all rows have all keys
    for r in rows:
        for k in all_keys:
            if k not in r: r[k]=None

    (root/"pilot_summary.json").write_text(json.dumps(rows,indent=2,ensure_ascii=False),encoding="utf-8")
    with open(root/"pilot_summary.csv","w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=all_keys,extrasaction='ignore'); w.writeheader(); w.writerows(rows)

    # PILOT_REPORT.md
    lines=["# Small Pilot Report","","## Repeat Advice Rules (Pilot Engineering)","",
        "- CV <= 3%: PASS0_5_LIKELY_ENOUGH","- 3% < CV <= 5%: CONSIDER_PASS0_10",
        "- CV > 5%: CONSIDER_PASS0_20","- count_coverage < 90%: DATA_QUALITY_BLOCKED",
        "- exclusion_rate > 5%: DATA_QUALITY_BLOCKED","",
        "These are Pilot engineering rules, NOT final paper thresholds.","","## Results",""]
    for r in rows:
        lines.append(f"### {r['id']}")
        for k in all_keys:
            if k!="id" and r.get(k) is not None: lines.append(f"- **{k}**: {r[k]}")
        lines.append("")
    (root/"PILOT_REPORT.md").write_text("\n".join(lines),encoding="utf-8")

    # PILOT_DIAGNOSTIC.md
    diag=["# Pilot Diagnostic Report",""]
    for r in rows:
        diag.append(f"## {r['id']}")
        if not r.get("gpu_uuid"): diag.append("- GPU identity: MISSING. pilot_identity.json absent; manifest has no gpu_uuid. Run with -Resume to backfill, or regenerate manifest with GPU info.")
        cov=r.get("count_coverage_pct")
        if cov is None: diag.append("- sync/coverage: MISSING. Analyzer output has no B_summary sync counts. The .sqlite may lack NVTX events or CUPTI_ACTIVITY_KIND_SYNCHRONIZATION table.")
        if r.get("a_conservation")=="missing": diag.append("- A conservation: MISSING. A_summary key absent from accounting_result.json. Analyzer may have failed to compute phase windows.")
        if r.get("timing_anomaly"): diag.append(f"- Timing: {r['timing_anomaly']}. pass1_to_pass0_ratio={r.get('pass1_to_pass0_ratio')}. Pass 1 (nsys) should be >= Pass 0. Possible causes: (a) different runner versions between passes, (b) Pass 0 data from old code with ns->ms bug, (c) summarizer read wrong field. Verify inference_e2e_latency_ms is in ms for both passes.")
        diag.append("")
    (root/"PILOT_DIAGNOSTIC.md").write_text("\n".join(diag),encoding="utf-8")

    print(f"Wrote {len(rows)} WMPCs to {root}")

if __name__=="__main__": main()
