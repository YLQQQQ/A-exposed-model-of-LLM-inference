#!/usr/bin/env python3
"""
[LEGACY — use python -m exposedpath run-pass0 or run-pass1 instead]

LLM Inference Benchmark with NVTX Annotations (PyTorch Eager).

This is the LEGACY benchmark script. For new Pilot runs, use the exposedpath
package CLI (python -m exposedpath ...) with WMPC manifests and prompt_tokens.json.
This script is kept for backward compatibility with existing results and the old
run_nsys_single.ps1 / run_nsys_matrix.ps1 workflow.

Supports two input modes:
  --prompt "text..."   →  real tokenizer, streaming-ready
  --prompt-len N       →  synthetic input_ids (backward compat)

Streaming mode (--streaming):
  Each decode step syncs via CUDA event → token returned to user immediately.
  NVTX per-step ranges INCLUDE the sync, reflecting real per-token latency.

Key constraints:
  - PyTorch eager (no torch.compile, no CUDA Graph)
  - No model.generate()
  - tokenizer outside NVTX core window
  - torch.cuda.synchronize() only at benchmark / streaming boundaries
  - NVTX: full_request, prefill, decode, decode_step_i
"""

import argparse
import json
import sys
import time
import traceback
from pathlib import Path

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def get_env_versions():
    gpu_name = torch.cuda.get_device_name(0) if torch.cuda.is_available() else "unknown"
    cuda_ver = torch.version.cuda or "unknown"
    torch_ver = torch.__version__
    try:
        import transformers
        tf_ver = transformers.__version__
    except ImportError:
        tf_ver = "unknown"
    return gpu_name, cuda_ver, torch_ver, tf_ver


def load_model_and_tokenizer(model_path: str, gpu: int = 0):
    """Load model (FP16) + tokenizer on specified GPU."""
    device = f"cuda:{gpu}"

    # ---- Check local path FIRST (before transformers fallback to HF hub) ----
    model_dir = Path(model_path)
    if not model_dir.is_dir():
        print(f"[bench_eager] ERROR: Model path does not exist: {model_path}")
        print(f"[bench_eager]   Please verify the path or download the model first.")
        print(f"[bench_eager]   Example: hf download Qwen/Qwen2.5-3B-Instruct --local-dir \"{model_path}\"")
        sys.exit(1)
    if not (model_dir / "config.json").exists():
        print(f"[bench_eager] ERROR: Model directory found but missing config.json: {model_path}")
        print(f"[bench_eager]   The directory may be incomplete. Try re-downloading the model.")
        sys.exit(1)

    print(f"[bench_eager] Loading model from: {model_path}  → {device}")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.float16,
            device_map=device,
            trust_remote_code=True,
        )
    except Exception:
        print("[bench_eager] trust_remote_code=True failed, retrying without...")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.float16,
            device_map=device,
        )
    model.eval()
    vocab_size = model.config.vocab_size

    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    print(f"[bench_eager] Model + tokenizer loaded. Vocab size: {vocab_size}")
    return model, tokenizer, vocab_size


def prepare_inputs(tokenizer, prompt: str, device: str, max_tokens: int = None):
    """Tokenize prompt → input_ids, attention_mask. Optionally truncate to max_tokens."""
    enc = tokenizer(prompt, return_tensors="pt", padding=False,
                    truncation=True if max_tokens else False,
                    max_length=max_tokens if max_tokens else None)
    input_ids = enc["input_ids"].to(device)
    attention_mask = enc["attention_mask"].to(device)
    return input_ids, attention_mask


def run_warmup(model, input_ids, attention_mask,
               output_len: int, warmup_iters: int, streaming: bool):
    """Warmup using the real input (no NVTX, no recording)."""
    print(f"[bench_eager] Running {warmup_iters} warmup iteration(s)...")
    batch_size, prompt_len = input_ids.shape
    for w in range(warmup_iters):
        print(f"[bench_eager]   Warmup {w + 1}/{warmup_iters}")
        torch.cuda.synchronize()
        with torch.inference_mode():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask,
                            use_cache=True)
        next_token = outputs.logits[:, -1, :].argmax(dim=-1)
        past_key_values = outputs.past_key_values
        for _ in range(1, output_len):
            current_input = next_token.unsqueeze(1)
            with torch.inference_mode():
                outputs = model(input_ids=current_input,
                                past_key_values=past_key_values, use_cache=True)
            next_token = outputs.logits[:, -1, :].argmax(dim=-1)
            past_key_values = outputs.past_key_values
        torch.cuda.synchronize()
    print("[bench_eager] Warmup complete.")


def run_one_repeat(model, tokenizer, prompt_text: str, prompt_len: int,
                   batch_size: int,
                   output_len: int, device: str, streaming: bool,
                   vocab_size: int, use_synthetic: bool,
                   canonical_ids=None) -> dict:
    """Single complete request-response cycle with NVTX.

    NVTX structure (per-repeat):
      prepare_input  – receive prompt → tokenize  (outside core inference)
      full_request   – core inference
        prefill      – 1× model() + TTFT sync (first token)
        decode       – (output_len-1)× model() + per-step sync if streaming
          decode_step_i  – per-token

    Each repeat is an independent user request.
    """

    # ============ NVTX: prepare_input ============
    torch.cuda.nvtx.range_push("prepare_input")
    if use_synthetic:
        seq = canonical_ids[:, :prompt_len] if canonical_ids is not None else \
              torch.randint(0, vocab_size, (1, prompt_len))
        input_ids = seq.repeat(batch_size, 1).to(device)
        attention_mask = torch.ones(batch_size, prompt_len, dtype=torch.long,
                                    device=device)
    else:
        # Real prompt: truncate to prompt_len tokens (canonical text mode)
        input_ids, attention_mask = prepare_inputs(
            tokenizer, prompt_text, device, max_tokens=prompt_len)
    torch.cuda.nvtx.range_pop()  # prepare_input

    # ---- drain GPU before timing ----
    torch.cuda.synchronize()
    t_start = time.perf_counter()

    # ==================== NVTX: full_request ====================
    torch.cuda.nvtx.range_push("full_request")

    # ==================== PREFILL ====================
    torch.cuda.nvtx.range_push("prefill")

    with torch.inference_mode():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask,
                        use_cache=True)

    next_token = outputs.logits[:, -1, :].argmax(dim=-1)
    past_key_values = outputs.past_key_values

    # TTFT — first token ready
    torch.cuda.synchronize()
    t_first_token = time.perf_counter()

    torch.cuda.nvtx.range_pop()  # prefill

    # ==================== DECODE ====================
    torch.cuda.nvtx.range_push("decode")

    for step_i in range(1, output_len):
        torch.cuda.nvtx.range_push(f"decode_step_{step_i}")

        current_input = next_token.unsqueeze(1)
        with torch.inference_mode():
            outputs = model(input_ids=current_input,
                            past_key_values=past_key_values, use_cache=True)
        next_token = outputs.logits[:, -1, :].argmax(dim=-1)
        past_key_values = outputs.past_key_values

        if streaming:
            # This token is now on GPU — sync to make it available to user
            torch.cuda.synchronize()

        torch.cuda.nvtx.range_pop()  # decode_step_i

    torch.cuda.nvtx.range_pop()  # decode

    # ---- streaming: last decode_step sync already got the complete response ----
    if streaming:
        # In streaming mode, the last decode step's sync already delivered the
        # final token.  No extra sync needed — full_request boundary = last token.
        t_end = time.perf_counter()
    else:
        # Batch mode: decode launched all kernels async — sync to catch GPU tail.
        torch.cuda.synchronize()
        t_end = time.perf_counter()

    torch.cuda.nvtx.range_pop()  # full_request

    # ---- Metrics ----
    prefill_ms = (t_first_token - t_start) * 1000.0
    decode_ms = (t_end - t_first_token) * 1000.0
    full_ms = (t_end - t_start) * 1000.0
    ttft_ms = prefill_ms
    tpot_ms = decode_ms / max(output_len - 1, 1)

    result = {
        "prompt_len": input_ids.shape[1],       # actual tokenized length
        "batch_size": input_ids.shape[0],       # actual batch
        "prefill_latency_ms": round(prefill_ms, 3),
        "decode_latency_ms": round(decode_ms, 3),
        "full_latency_ms": round(full_ms, 3),
        "ttft_ms": round(ttft_ms, 3),
        "tpot_ms": round(tpot_ms, 3),
    }

    return result


def main():
    parser = argparse.ArgumentParser(
        description="LLM Inference Benchmark with NVTX (PyTorch Eager)"
    )
    parser.add_argument("--model-path", required=True, help="Path to local model")

    # Input: real prompt OR synthetic
    parser.add_argument("--prompt", default=None,
                        help="Real text prompt (uses tokenizer; overrides --prompt-len)")
    parser.add_argument("--prompt-len", type=int, default=None,
                        help="Synthetic prompt length (ignored if --prompt given)")

    parser.add_argument("--batch-size", type=int, default=1)
    parser.add_argument("--output-len", type=int, required=True)
    parser.add_argument("--warmup-iters", type=int, default=5)
    parser.add_argument("--repeat-iters", type=int, default=10)
    parser.add_argument("--dtype", default="fp16")
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--gpu", type=int, default=0)
    parser.add_argument("--output-dir", default=".")
    parser.add_argument("--run-name", default=None)
    parser.add_argument("--streaming", action="store_true",
                        help="Per-step sync (streaming token-by-token to user)")

    args = parser.parse_args()

    if args.dtype != "fp16":
        print(f"[bench_eager] ERROR: Only fp16 supported, got '{args.dtype}'")
        sys.exit(1)
    if not torch.cuda.is_available():
        print("[bench_eager] ERROR: CUDA is not available")
        sys.exit(1)
    if args.gpu >= torch.cuda.device_count():
        print(f"[bench_eager] ERROR: GPU {args.gpu} not available")
        sys.exit(1)

    torch.cuda.set_device(args.gpu)
    print(f"[bench_eager] Using GPU {args.gpu}: {torch.cuda.get_device_name(args.gpu)}")

    gpu_name, cuda_ver, torch_ver, tf_ver = get_env_versions()
    gpu_name = torch.cuda.get_device_name(args.gpu)
    print(f"[bench_eager] GPU:        {gpu_name}")
    print(f"[bench_eager] CUDA:       {cuda_ver}")
    print(f"[bench_eager] PyTorch:    {torch_ver}")
    print(f"[bench_eager] Transformers: {tf_ver}")

    # ---- Output dir ----
    out_path = Path(args.output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    # ---- Load model + tokenizer ----
    model, tokenizer, vocab_size = load_model_and_tokenizer(args.model_path, args.gpu)

    # ---- Determine config (no actual work yet) ----
    use_synthetic = args.prompt is None
    if use_synthetic:
        if args.prompt_len is None:
            print("[bench_eager] ERROR: --prompt or --prompt-len required")
            sys.exit(1)
        prompt_len = args.prompt_len
        batch_size = args.batch_size
        # Pre-generate a shared canonical sequence (max prompt_len across all
        # workloads that share the same seed).  Shorter prompts truncate it,
        # ensuring same-prompt_len = same-tokens across different matrix rows.
        torch.manual_seed(42)
        _canonical = torch.randint(0, vocab_size, (1, prompt_len), device='cpu')
        prompt_label = f"synthetic_len{prompt_len}"
    else:
        prompt_len = 0   # will be set after tokenization (post-warmup)
        batch_size = args.batch_size
        _canonical = None
        prompt_label = f"real_{args.prompt[:20].replace(' ','_')}"

    run_name = args.run_name or f"{prompt_label}_b{batch_size}_o{args.output_len}"
    if args.streaming:
        run_name += "_streaming"

    print(f"[bench_eager] Run name:   {run_name}")
    print(f"[bench_eager] Output dir: {out_path.resolve()}")
    print(f"[bench_eager] Config:     prompt_len={prompt_len}, batch_size={batch_size}, "
          f"output_len={args.output_len}, streaming={args.streaming}")
    print(f"[bench_eager] Warmup:     {args.warmup_iters} iters")
    print(f"[bench_eager] Repeats:    {args.repeat_iters} iters")

    try:
        # ================================================================
        # 1. WARMUP — use SAME input as benchmark (real prompt or synthetic)
        #    CUDA JIT compiles during warmup → all repeats identical.
        # ================================================================
        if use_synthetic:
            # Same canonical sequence as benchmark repeats
            warm_input_ids = _canonical[:, :prompt_len].repeat(batch_size, 1).to(args.device)
            warm_attn_mask = torch.ones(batch_size, prompt_len, dtype=torch.long,
                                        device=args.device)
        else:
            warm_input_ids, warm_attn_mask = prepare_inputs(
                tokenizer, args.prompt, args.device, max_tokens=prompt_len)
        run_warmup(model, warm_input_ids, warm_attn_mask,
                   args.output_len, args.warmup_iters, args.streaming)

        if not use_synthetic:
            prompt_len = warm_input_ids.shape[1]   # actual tokenized length
            batch_size = warm_input_ids.shape[0]

        # ================================================================
        # 2. BENCHMARK REPEATS — each is an independent request-response
        # ================================================================
        results = []
        for repeat_idx in range(args.repeat_iters):
            print(f"\n[bench_eager] === Repeat {repeat_idx + 1}/{args.repeat_iters} ===")
            torch.cuda.reset_peak_memory_stats(args.gpu)
            metrics = run_one_repeat(
                model, tokenizer, args.prompt, prompt_len, batch_size,
                args.output_len, args.device, args.streaming,
                vocab_size, use_synthetic, _canonical,
            )
            record = {
                "run_name": run_name,
                "prompt_len": metrics.pop("prompt_len", prompt_len),
                "batch_size": metrics.pop("batch_size", batch_size),
                "output_len": args.output_len,
                "streaming": args.streaming,
                **metrics,
                "gpu_name": gpu_name,
                "cuda_version": cuda_ver,
                "torch_version": torch_ver,
                "transformers_version": tf_ver,
            }
            results.append(record)
            print(f"  prefill={record['prefill_latency_ms']:.1f}ms  "
                  f"decode={record['decode_latency_ms']:.1f}ms  "
                  f"full={record['full_latency_ms']:.1f}ms  "
                  f"ttft={record['ttft_ms']:.1f}ms  "
                  f"tpot={record['tpot_ms']:.1f}ms")

        # ---- Output ----
        jsonl_path = out_path / "results.jsonl"
        with open(jsonl_path, "w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"\n[bench_eager] Wrote: {jsonl_path}")

        avg = lambda key: round(sum(r[key] for r in results) / len(results), 3)
        summary = {
            "run_name": run_name,
            "prompt_len": prompt_len,
            "batch_size": batch_size,
            "output_len": args.output_len,
            "streaming": args.streaming,
            "num_repeats": args.repeat_iters,
            "avg_prefill_latency_ms": avg("prefill_latency_ms"),
            "avg_decode_latency_ms": avg("decode_latency_ms"),
            "avg_full_latency_ms": avg("full_latency_ms"),
            "avg_ttft_ms": avg("ttft_ms"),
            "avg_tpot_ms": avg("tpot_ms"),
            "gpu_name": gpu_name,
            "cuda_version": cuda_ver,
            "torch_version": torch_ver,
            "transformers_version": tf_ver,
            "individual_results": results,
        }
        summary_path = out_path / "summary.json"
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        print(f"[bench_eager] Wrote: {summary_path}")

        csv_keys = [
            "run_name", "prompt_len", "batch_size", "output_len",
            "prefill_latency_ms", "decode_latency_ms", "full_latency_ms",
            "ttft_ms", "tpot_ms", "gpu_name", "cuda_version",
            "torch_version", "transformers_version",
        ]
        csv_path = out_path / "results.csv"
        with open(csv_path, "w", encoding="utf-8") as f:
            f.write(",".join(csv_keys) + "\n")
            for r in results:
                f.write(",".join(str(r[k]) for k in csv_keys) + "\n")
        print(f"[bench_eager] Wrote: {csv_path}")
        print("\n[bench_eager] Done.")

    except RuntimeError as e:
        msg = str(e)
        if "out of memory" in msg.lower() or "oom" in msg.lower():
            print(f"\n[bench_eager] OOM ERROR: {e}")
            traceback.print_exc()
            out_path = Path(args.output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            failed_info = {
                "error": "OOM", "message": msg,
                "run_name": run_name,
                "prompt_len": prompt_len, "batch_size": batch_size,
                "output_len": args.output_len,
                "gpu_name": gpu_name, "cuda_version": cuda_ver,
                "torch_version": torch_ver,
            }
            with open(out_path / "failed.json", "w", encoding="utf-8") as f:
                json.dump(failed_info, f, indent=2, ensure_ascii=False)
            sys.exit(1)
        else:
            raise


if __name__ == "__main__":
    main()
