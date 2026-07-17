#!/usr/bin/env python3
"""
Matrix workload runner.

Reads a YAML workload file and runs bench_eager.py for each workload
via subprocess.  Failures in one workload do NOT stop the remaining ones.
"""

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml


def load_workloads(yaml_path: str) -> list:
    """Load workload list from YAML file. Returns list of dicts."""
    with open(yaml_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not data or "workloads" not in data:
        raise ValueError(f"YAML file '{yaml_path}' missing 'workloads' key")

    workloads = data["workloads"]
    print(f"[run_matrix] Loaded {len(workloads)} workload(s) from {yaml_path}")
    for w in workloads:
        print(f"  {w['id']}: prompt={w['prompt_len']}, batch={w['batch_size']}, "
              f"output={w['output_len']}")
    return workloads


def main():
    parser = argparse.ArgumentParser(
        description="Run benchmark matrix from YAML workload file"
    )
    parser.add_argument("--model-path", required=True, help="Path to model directory")
    parser.add_argument("--workload", required=True, help="Path to workload YAML file")
    parser.add_argument("--warmup-iters", type=int, default=5)
    parser.add_argument("--repeat-iters", type=int, default=10)
    parser.add_argument("--dtype", default="fp16")
    parser.add_argument("--gpu", type=int, default=0, help="GPU device ID to use")
    parser.add_argument("--output-root", default="results_matrix",
                        help="Root directory for all run outputs")
    parser.add_argument("--streaming", action="store_true",
                        help="Enable streaming mode (per-step sync)")
    parser.add_argument("--reverse", action="store_true",
                        help="Run workloads in reverse order")
    args = parser.parse_args()

    # ---- Setup ----
    script_dir = Path(__file__).resolve().parent
    bench_script = script_dir / "bench_eager.py"
    output_root = Path(args.output_root)
    output_root.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    matrix_dir = output_root / f"matrix_{timestamp}"
    matrix_dir.mkdir(parents=True, exist_ok=True)

    print(f"[run_matrix] Output root: {matrix_dir.resolve()}")

    # ---- Load workloads ----
    workloads = load_workloads(args.workload)

    # ---- Reverse order if requested ----
    if args.reverse:
        workloads.reverse()
        print("[run_matrix] Reverse order enabled — workloads reversed")

    # ---- Run each workload ----
    succeeded = []
    failed = []

    for i, w in enumerate(workloads):
        wid = w["id"]
        batch_size = w.get("batch_size", 1)
        output_len = w["output_len"]
        prompt_text = w.get("prompt")        # optional real prompt
        prompt_len = w.get("prompt_len")      # synthetic (if no prompt)

        print(f"\n{'='*60}")
        print(f"[run_matrix] Workload {i+1}/{len(workloads)}: {wid}")
        if prompt_text:
            print(f"[run_matrix]   prompt='{prompt_text[:50]}...', batch_size={batch_size}, "
                  f"output_len={output_len}")
        else:
            print(f"[run_matrix]   prompt_len={prompt_len}, batch_size={batch_size}, "
                  f"output_len={output_len}")
        print(f"{'='*60}")

        run_dir = matrix_dir / wid
        run_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable, str(bench_script),
            "--model-path", args.model_path,
            "--batch-size", str(batch_size),
            "--output-len", str(output_len),
            "--warmup-iters", str(args.warmup_iters),
            "--repeat-iters", str(args.repeat_iters),
            "--dtype", args.dtype,
            "--gpu", str(args.gpu),
            "--output-dir", str(run_dir),
            "--run-name", wid,
        ]
        if prompt_text:
            cmd.extend(["--prompt", prompt_text])
        elif prompt_len is not None:
            cmd.extend(["--prompt-len", str(prompt_len)])
        if args.streaming:
            cmd.append("--streaming")

        # Save command.txt
        cmd_path = run_dir / "command.txt"
        with open(cmd_path, "w", encoding="utf-8") as f:
            f.write(" ".join(cmd) + "\n")
        print(f"[run_matrix] Command saved: {cmd_path}")

        # Run
        t0 = time.perf_counter()
        result = subprocess.run(cmd, cwd=str(script_dir))
        elapsed = time.perf_counter() - t0

        if result.returncode == 0:
            print(f"[run_matrix] {wid}: SUCCESS ({elapsed:.1f}s)")
            succeeded.append({
                "id": wid,
                "elapsed_s": round(elapsed, 1),
                "output_dir": str(run_dir),
            })
        else:
            print(f"[run_matrix] {wid}: FAILED (rc={result.returncode}, {elapsed:.1f}s)")
            failed.append({
                "id": wid,
                "returncode": result.returncode,
                "elapsed_s": round(elapsed, 1),
                "output_dir": str(run_dir),
            })

    # ---- Summary ----
    print(f"\n{'='*60}")
    print(f"[run_matrix] MATRIX COMPLETE")
    print(f"[run_matrix]   Succeeded: {len(succeeded)}/{len(workloads)}")
    print(f"[run_matrix]   Failed:    {len(failed)}/{len(workloads)}")
    print(f"{'='*60}")

    matrix_summary = {
        "timestamp": timestamp,
        "workload_file": str(Path(args.workload).resolve()),
        "model_path": args.model_path,
        "total": len(workloads),
        "succeeded": len(succeeded),
        "failed": len(failed),
        "succeeded_workloads": succeeded,
        "failed_workloads": failed,
    }

    summary_path = matrix_dir / "matrix_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(matrix_summary, f, indent=2, ensure_ascii=False)
    print(f"[run_matrix] Summary: {summary_path}")

    if failed:
        failed_path = matrix_dir / "failed_workloads.json"
        with open(failed_path, "w", encoding="utf-8") as f:
            json.dump(failed, f, indent=2, ensure_ascii=False)
        print(f"[run_matrix] Failed list: {failed_path}")

    # Exit 0 as long as matrix runner itself didn't crash;
    # individual failures are recorded in the summary.
    print("[run_matrix] Done.")


if __name__ == "__main__":
    main()
