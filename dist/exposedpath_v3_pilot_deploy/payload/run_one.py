#!/usr/bin/env python3
"""
[LEGACY — use python -m exposedpath run-pass0 instead]

Convenience wrapper: run a single benchmark configuration.
This is the legacy entry point. For new Pilot runs, use the exposedpath package.
"""

import subprocess
import sys
import argparse
from pathlib import Path


def run_single(
    model_path: str,
    output_len: int,
    prompt: str = None,
    prompt_len: int = None,
    batch_size: int = 1,
    warmup_iters: int = 2,
    repeat_iters: int = 3,
    dtype: str = "fp16",
    device: str = "cuda",
    gpu: int = 0,
    output_dir: str = ".",
    run_name: str = None,
    streaming: bool = False,
):
    script_dir = Path(__file__).resolve().parent
    bench_script = script_dir / "bench_eager.py"

    cmd = [
        sys.executable, str(bench_script),
        "--model-path", model_path,
        "--batch-size", str(batch_size),
        "--output-len", str(output_len),
        "--warmup-iters", str(warmup_iters),
        "--repeat-iters", str(repeat_iters),
        "--dtype", dtype,
        "--device", device,
        "--gpu", str(gpu),
        "--output-dir", output_dir,
    ]
    if prompt:
        cmd.extend(["--prompt", prompt])
    elif prompt_len is not None:
        cmd.extend(["--prompt-len", str(prompt_len)])
    if run_name:
        cmd.extend(["--run-name", run_name])
    if streaming:
        cmd.append("--streaming")

    print(f"[run_one] Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=str(script_dir))
    return result


def main():
    parser = argparse.ArgumentParser(
        description="Run a single LLM inference benchmark"
    )
    parser.add_argument("--model-path", required=True)
    parser.add_argument("--prompt", default=None, help="Real text prompt")
    parser.add_argument("--prompt-len", type=int, default=None,
                        help="Synthetic prompt len (if --prompt not given)")
    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--output-len", type=int, required=True)
    parser.add_argument("--warmup-iters", type=int, default=5)
    parser.add_argument("--repeat-iters", type=int, default=10)
    parser.add_argument("--dtype", default="fp16")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--streaming", action="store_true")

    args = parser.parse_args()
    result = run_single(
        model_path=args.model_path,
        output_len=args.output_len,
        prompt=args.prompt,
        prompt_len=args.prompt_len,
        batch_size=args.batch_size,
        warmup_iters=args.warmup_iters,
        repeat_iters=args.repeat_iters,
        dtype=args.dtype,
        device=args.device,
        gpu=args.gpu,
        output_dir=args.output_dir,
        run_name=args.run_name,
        streaming=args.streaming,
    )
    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
