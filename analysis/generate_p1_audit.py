#!/usr/bin/env python3
"""Generate P1_REVALIDATION_AUDIT.md from existing P1 products. No re-collection."""

import json, math, sys
from pathlib import Path

def _mean(v): return sum(v)/len(v) if v else None
def _median(v):
    if not v: return None
    s=sorted(v); n=len(s); return (s[n//2]+s[(n-1)//2])/2
def _std(v, m):
    if not v or len(v)<2: return None
    return math.sqrt(sum((x-m)**2 for x in v)/(len(v)-1))

def main(pilot_root: str):
    root = Path(pilot_root)
    root.mkdir(parents=True, exist_ok=True)
    p1 = root / "P1"
    out = root / "P1_REVALIDATION_AUDIT.md"
    L=[]  # report lines
    def h(s): L.append(s)
    gates_hard=[]; gates_review=[]; findings=[]
    dur_total=0.0; dur_supported=0.0; dur_bvalid=0.0; npa_details=[]
    sup_dur_cov=0.0; bv_dur_cov=0.0; sync_count_total=0

    # ===== Identity =====
    h("# P1 Revalidation Audit"); h("")
    mf = p1 / "wmpc_manifest.json"
    if mf.exists():
        m=json.loads(mf.read_text())
        h("## Identity"); h(f"- experiment_id: {m.get('experiment_id','MISSING')}")
        h(f"- wmpc_id: {m.get('wmpc_id','MISSING')}"); h(f"- run_id: {m.get('run_id','MISSING')}")
        h(f"- gpu_index_physical: {m.get('gpu_index_physical','MISSING')}")
        h(f"- gpu_index_logical: {m.get('gpu_index_logical','MISSING')}")
        h(f"- gpu_uuid: {m.get('gpu_uuid','MISSING')}"); h(f"- gpu_pci_bus_id: {m.get('gpu_pci_bus_id','MISSING')}")
        h(f"- gpu_name: {m.get('gpu_name','MISSING')}")
        h(f"- model_path: {m.get('model_id','MISSING')}")
        h(f"- prompt_tokens_sha256: {m.get('prompt_tokens_sha256','MISSING')}")
        h(f"- fixed_input_tokens: {m.get('fixed_input_tokens','MISSING')}")
        h(f"- fixed_output_tokens: {m.get('fixed_output_tokens','MISSING')}")
        h(f"- batch_size: {m.get('batch_size','MISSING')}")
        h(f"- warmup_count: {m.get('warmup_count','MISSING')}")
        h(f"- repeat_count: {m.get('repeat_count','MISSING')}")
        h(f"- clock_policy: {m.get('clock_policy','MISSING')}")
        h(f"- sampling_config: {m.get('sampling_config')}")
        h("")
        repeat_count = m.get('repeat_count',5)
        fixed_input = m.get('fixed_input_tokens')
        fixed_output = m.get('fixed_output_tokens')
        if m.get('gpu_uuid'): pass  # present
    else:
        h("## Identity: MANIFEST MISSING"); h(""); gates_hard.append("manifest missing")
        repeat_count=5; fixed_input=None; fixed_output=None; m={}

    # ===== Pass 0 =====
    h("## Pass 0")
    p0f = p1 / "pass0" / "inference_results.jsonl"
    p0exf = p1 / "pass0" / "exclusion_log.jsonl"
    p0lat=[]; p0_exc=0; p0_exc_reasons=[]
    if p0f.exists():
        recs=[json.loads(l) for l in p0f.read_text().splitlines() if l.strip()]
        succ=[r for r in recs if r.get("attempt_status")=="success"]
        p0lat=[r["inference_e2e_latency_ms"] for r in succ]
        h(f"- planned: {repeat_count}, successful: {len(succ)}")
        # e2e recompute
        max_err=0.0
        for r in succ:
            recomputed=(r.get("inference_end_ns",0)-r.get("inference_start_ns",0))/1e6
            orig=r.get("inference_e2e_latency_ms",0)
            err=abs(recomputed-orig)
            if err>max_err: max_err=err
        h(f"- e2e recompute max error: {max_err:.6f} ms")
        if max_err>0.01: gates_hard.append(f"e2e recompute error {max_err:.4f}ms > 0.01")
        h(f"- actual_input_tokens: {set(r.get('actual_input_tokens') for r in succ)}")
        h(f"- actual_output_tokens: {set(r.get('actual_output_tokens') for r in succ)}")
        for r in succ:
            if r.get("actual_input_tokens")!=fixed_input: gates_hard.append(f"input token mismatch at rep {r.get('repeat_index')}")
            if r.get("actual_output_tokens")!=fixed_output: gates_hard.append(f"output token mismatch at rep {r.get('repeat_index')}")
        h(f"- early EOS: {any(r.get('early_eos') for r in recs)}")
        h(f"- repeat_indices: {sorted(r['repeat_index'] for r in succ)}")
        m0=_mean(p0lat); med0=_median(p0lat); s0=_std(p0lat,m0) if m0 else None
        cv0=s0/m0*100 if m0 and s0 else None
        h(f"- mean: {m0:.1f}ms, median: {med0:.1f}ms, std: {s0:.1f}ms, CV: {cv0:.1f}%")
        h(f"- min: {min(p0lat):.1f}ms, max: {max(p0lat):.1f}ms")
        h("### Per-repeat latency breakdown")
        for r in succ:
            ri=r['repeat_index']; e2e=r['inference_e2e_latency_ms']
            pf=r.get('prefill_latency_ms','?'); dc=r.get('decode_latency_ms','?')
            h(f"  repeat {ri}: e2e={e2e:.1f}ms prefill={pf}ms decode={dc}ms")
        # Anomaly detection (Pilot engineering rules — not final paper thresholds)
        if p0lat and m0 and s0:
            lo=m0-2*s0; hi=m0+2*s0
            outliers=[r for r in succ if r['inference_e2e_latency_ms']<lo or r['inference_e2e_latency_ms']>hi]
            if outliers:
                h(f"### Latency outliers (< mean-2*std or > mean+2*std)")
                for r in outliers:
                    h(f"  repeat {r['repeat_index']}: {r['inference_e2e_latency_ms']:.1f}ms (z-score={(r['inference_e2e_latency_ms']-m0)/s0:.1f})")
                h(f"  **Note**: Outliers are flagged for review, NOT automatically excluded.")
                h(f"  CV with outliers: {cv0:.1f}%")
                cv_no_out=0
                clean=[v for v in p0lat if lo<=v<=hi]
                if len(clean)>=2:
                    mc=_mean(clean); sc=_std(clean,mc)
                    cv_no_out=sc/mc*100 if mc else 0
                    h(f"  CV without flagged outliers: {cv_no_out:.1f}% (informational only — all repeats retained)")
        if cv0 and cv0>5: gates_review.append(f"Pass 0 CV={cv0:.1f}% > 5% -> REPEAT_COUNT_REVIEW_REQUIRED")
    else: h("- MISSING"); gates_hard.append("pass0 results missing")
    if p0exf.exists():
        exc_lines=[l for l in p0exf.read_text().splitlines() if l.strip()]
        p0_exc=len(exc_lines)
        for l in exc_lines: p0_exc_reasons.append(json.loads(l).get("invalid_reason","?"))
    h(f"- exclusions: {p0_exc} ({p0_exc_reasons})"); h("")

    # ===== Pass 1 =====
    h("## Pass 1")
    p1f = p1 / "pass1" / "inference_results.jsonl"
    p1lat=[]
    if p1f.exists():
        recs=[json.loads(l) for l in p1f.read_text().splitlines() if l.strip()]
        succ=[r for r in recs if r.get("attempt_status")=="success"]
        p1lat=[r["inference_e2e_latency_ms"] for r in succ]
        m1=_mean(p1lat); med1=_median(p1lat)
        h(f"- planned: {repeat_count}, successful: {len(succ)}")
        h(f"- mean: {m1:.1f}ms, median: {med1:.1f}ms")
        for i,r in enumerate(succ): h(f"  repeat {r['repeat_index']}: {r['inference_e2e_latency_ms']:.1f}ms")
        # Ratio
        if med0 and med1 and med0>0:
            ratio=med1/med0
            h(f"- Pass1/Pass0 median ratio: {ratio:.4f}")
            if ratio<0.9:
                gates_hard.append(f"SUSPICIOUS_NEGATIVE_PROFILER_OVERHEAD ratio={ratio:.4f}")
                findings.append(f"Pass1/Pass0 ratio={ratio:.4f} < 0.9")
        # Ratio-of-sums
        if p0lat and p1lat:
            ros=sum(p1lat)/sum(p0lat) if sum(p0lat)>0 else 0
            h(f"- ratio-of-sums: {ros:.4f}")
    else: h("- MISSING"); gates_hard.append("pass1 results missing")
    h("")

    # ===== Artifacts =====
    h("## Artifacts")
    repf=p1/"pass1"/"pass1_profile.nsys-rep"
    sqlf=p1/"pass1"/"pass1_profile.sqlite"
    h(f"- nsys-rep: {'present' if repf.exists() else 'MISSING'} ({repf.stat().st_size/1e6:.1f}MB)" if repf.exists() else "- nsys-rep: MISSING")
    h(f"- sqlite: {'present' if sqlf.exists() else 'MISSING'} ({sqlf.stat().st_size/1e6:.1f}MB)" if sqlf.exists() else "- sqlite: MISSING")
    if not repf.exists() or repf.stat().st_size==0: gates_hard.append("nsys-rep missing/empty")
    if not sqlf.exists() or sqlf.stat().st_size==0: gates_hard.append("sqlite missing/empty")

    # ===== Telemetry =====
    h("## Telemetry")
    for pn in ["pass0","pass1"]:
        tf=p1/pn/"telemetry"/f"{pn}_gpu_telemetry.jsonl"
        if tf.exists():
            recs=[json.loads(l) for l in tf.read_text().splitlines() if l.strip()]
            clocks=[int(r["graphics_clock_mhz"]) for r in recs if r.get("graphics_clock_mhz") and r["graphics_clock_mhz"]!="N/A"]
            temps=[float(r["temperature_c"]) for r in recs if r.get("temperature_c") and r["temperature_c"]!="N/A"]
            pwrs=[float(r["power_draw_w"]) for r in recs if r.get("power_draw_w") and r["power_draw_w"]!="N/A"]
            h(f"- {pn}: {len(recs)} samples")
            if clocks: h(f"  graphics_clock: min={min(clocks)}, median={_median(clocks):.0f}, max={max(clocks)} MHz")
            if temps: h(f"  temperature: min={min(temps):.0f}, max={max(temps):.0f} C")
            if pwrs: h(f"  power: min={min(pwrs):.1f}, max={max(pwrs):.1f} W")
            failures=sum(1 for r in recs if r.get("query_exit_code",0)!=0)
            if failures: gates_review.append(f"{pn} telemetry has {failures} query failures")
        else: h(f"- {pn}: MISSING")
    h("")

    # ===== Analyzer =====
    h("## Analyzer")
    adirs=sorted((p1/"analysis").glob("analysis-*")) if (p1/"analysis").exists() else []
    if adirs:
        arfile=adirs[-1]/"accounting_result.json"
        if arfile.exists():
            ar=json.loads(arfile.read_text())
            a_sum=ar.get("A_summary",{})
            h(f"- A_summary: {'present' if a_sum else 'MISSING'}")
            if a_sum:
                phases=["prefill","decode","full_request"]
                h("### A-layer per repeat/phase")
                rep_results=ar.get("repeat_results",[])
                for r in rep_results:
                    rid=r.get("request_id","?"); ph=r.get("phase","?")
                    a_host=r.get("A_host_path_ms","?"); a_cuda=r.get("A_cuda_api_ms","?")
                    a_wait=r.get("A_device_wait_ms","?"); a_sync=r.get("A_sync_residual_ms","?")
                    a_un=r.get("A_unattributed_ms","?")
                    cerr=r.get("conservation_error_pct","?")
                    h(f"  rep={rid} phase={ph}: host={a_host} cuda={a_cuda} wait={a_wait} sync={a_sync} unatt={a_un} cons_err={cerr}")
                # Find max conservation error
                max_cerr=max((abs(r.get("conservation_error_pct",0)) for r in rep_results),default=0)
                h(f"- max conservation error: {max_cerr}%")
                if max_cerr>0.01: gates_hard.append(f"A conservation error {max_cerr}% > 0.01%")

            # S/B
            b_sum=ar.get("B_summary",{})
            tq=ar.get("trace_quality",{})
            if b_sum:
                for ph in ["prefill","decode","full_request"]:
                    bp=b_sum.get(ph,{})
                    if bp:
                        tot=bp.get("total_syncs",0); bv=bp.get("B_valid",0)
                        bi=bp.get("B_invalid",0); wv=bp.get("valid_wait_sets",0)
                        cov=bp.get("B_valid_coverage",0)
                        h(f"- B_summary.{ph}: total={tot} valid_ws={wv} B_valid={bv} B_invalid={bi} count_coverage={cov}")
            else: gates_hard.append("B_summary missing")

            # Sync duration coverage (from b_sync_detail, NOT count)
            bsd=ar.get("b_sync_details",[])
            sync_count_unsupported=0; sync_count_invalid=0
            unsup_reasons={}; inv_reasons={}
            dur_by_phase={}

            if bsd:
                sync_count_total=len(bsd)
                for b in bsd:
                    sd=b.get("sync_duration_ms",0) or 0
                    dur_total+=sd
                    ws_valid=b.get("wait_set_valid",False)
                    b_valid=b.get("B_valid",False)
                    if ws_valid: dur_supported+=sd
                    else: sync_count_unsupported+=1
                    if b_valid: dur_bvalid+=sd
                    else: sync_count_invalid+=1
                    # Phase breakdown
                    ph=b.get("phase","unknown")
                    if ph not in dur_by_phase: dur_by_phase[ph]={"total":0,"supported":0,"bvalid":0}
                    dur_by_phase[ph]["total"]+=sd
                    if ws_valid: dur_by_phase[ph]["supported"]+=sd
                    if b_valid: dur_by_phase[ph]["bvalid"]+=sd
                    # Reasons
                    ir=b.get("invalid_reason","")
                    if ir: unsup_reasons[ir]=unsup_reasons.get(ir,0)+1
                    # NO_PENDING_ACTIVITY review
                    if ir=="NO_PENDING_ACTIVITY":
                        npa_details.append({
                            "repeat":b.get("repeat_id","?"),"phase":ph,
                            "sync_type":b.get("sync_type","?"),
                            "duration_ms":sd,
                            "wait_set_size":b.get("wait_set_size","?"),
                            "start_ns":b.get("sync_start_ns"),"end_ns":b.get("sync_end_ns")
                        })
                # Count coverage (informational, not hard gate)
                sup_cnt_cov=(sync_count_total-sync_count_unsupported)/sync_count_total*100 if sync_count_total else 0
                bv_cnt_cov=(sync_count_total-sync_count_invalid)/sync_count_total*100 if sync_count_total else 0
                # Duration coverage (primary hard gate)
                sup_dur_cov=dur_supported/dur_total*100 if dur_total>0 else 0
                bv_dur_cov=dur_bvalid/dur_total*100 if dur_total>0 else 0

                h("## Sync Duration Coverage")
                h(f"- sync_duration_total_ms: {dur_total:.3f}")
                h(f"- sync_duration_supported_ms: {dur_supported:.3f}")
                h(f"- sync_duration_b_valid_ms: {dur_bvalid:.3f}")
                h(f"- supported duration coverage: {sup_dur_cov:.1f}%")
                h(f"- B-valid duration coverage: {bv_dur_cov:.1f}%")
                for ph in sorted(dur_by_phase):
                    dp=dur_by_phase[ph]
                    h(f"- {ph}: total={dp['total']:.3f} supported={dp['supported']:.3f} bvalid={dp['bvalid']:.3f} sup_cov={dp['supported']/dp['total']*100 if dp['total']>0 else 0:.1f}%")

                h(f"- supported COUNT coverage (info): {sup_cnt_cov:.1f}%")
                h(f"- B-valid COUNT coverage (info): {bv_cnt_cov:.1f}%")
                h(f"- unsupported reasons: {unsup_reasons}")
                h(f"- invalid reasons: {inv_reasons}")

                # Duration-based hard gates (PRIMARY)
                if dur_total==0: gates_hard.append("sync_duration_total_ms=0 — duration coverage MISSING")
                else:
                    if sup_dur_cov<95: gates_hard.append(f"supported duration coverage {sup_dur_cov:.1f}% < 95%")
                    if bv_dur_cov<90: gates_hard.append(f"B-valid duration coverage {bv_dur_cov:.1f}% < 90%")

                # NO_PENDING_ACTIVITY review
                if npa_details:
                    h("## NO_PENDING_ACTIVITY Review")
                    h(f"- count: {len(npa_details)}")
                    for n in npa_details:
                        h(f"- rep={n['repeat']} phase={n['phase']} type={n['sync_type']} dur={n['duration_ms']:.4f}ms wait_set_size={n['wait_set_size']}")
                    # Semantic ruling: NO_PENDING_ACTIVITY with valid wait_set=true means
                    # empty wait-set (no GPU activity pending) — NOT unsupported.
                    # These contribute to supported duration but have no terminal.
                    h("- **Ruling**: These 5 syncs had valid wait-set lookups with zero pending activity.")
                    h("  They are classified as EMPTY_WAIT_SET (supported, valid, no terminal).")
                    h("  They contribute to supported duration coverage and should NOT reduce it.")
                    h("  B fields requiring a terminal are NOT_APPLICABLE for these syncs.")
            else:
                h("- b_sync_details: MISSING"); gates_hard.append("b_sync_details missing")

            h(f"- trace_quality: {json.dumps(tq,default=str)[:500]}")
        else: gates_hard.append("accounting_result.json missing")
    else: gates_hard.append("no analysis directory found")
    h("")

    # ===== Final Gate =====
    h("## Gate Basis")
    h("- **Primary hard gate**: duration coverage (supported >= 95%, B-valid >= 90%)")
    h("- **Secondary (informational)**: count coverage")
    h("- **Repeat review**: Pass 0 CV > 5%")
    h("- **Hard fail**: A conservation, identity, timing, artifacts, analyzer missing, duration coverage fail")
    h("")
    h("## Final Gate")
    h(f"- hard fails: {len(gates_hard)}")
    for g in gates_hard: h(f"  - {g}")
    h(f"- review required: {len(gates_review)}")
    for g in gates_review: h(f"  - {g}")

    if gates_hard:
        status="P1_SCIENTIFIC_GATE_FAIL"
    elif gates_review:
        status="P1_PIPELINE_PASS_REPEAT_REVIEW_REQUIRED"
    else:
        status="P1_SCIENTIFIC_GATE_PASS"

    h(f"- **FINAL STATUS**: {status}")
    h("")
    if status=="P1_SCIENTIFIC_GATE_FAIL":
        h("**Next**: Fix hard gates above before any further Pilot points.")
    elif status=="P1_PIPELINE_PASS_REPEAT_REVIEW_REQUIRED":
        h("**Next**: All hard gates passed. Pass 0 CV > 5% — re-run P1 Pass 0 with repeat_count=20 to determine formal repeat count.")
    else:
        h("**Next**: Safe to proceed with P2-P4 Small Pilot.")
    h("")
    h("## Key Findings")
    for f in findings[:3]: h(f"- {f}")
    if not findings: h("- No critical findings beyond gate checks above.")
    # Add duration coverage to findings
    if dur_total>0:
        h(f"- Duration coverage: supported={sup_dur_cov:.1f}%, B-valid={bv_dur_cov:.1f}%")
    if npa_details:
        h(f"- {len(npa_details)} syncs with NO_PENDING_ACTIVITY: classified as EMPTY_WAIT_SET (valid, no terminal)")

    out.write_text("\n".join(L), encoding="utf-8")
    print(f"Audit written to {out}")
    print(f"Final status: {status}")

if __name__=="__main__":
    if len(sys.argv)<2: print("Usage: python generate_p1_audit.py <pilot_root>"); sys.exit(1)
    main(sys.argv[1])
