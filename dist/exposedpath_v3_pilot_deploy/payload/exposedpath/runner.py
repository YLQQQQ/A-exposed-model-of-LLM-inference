"""
Runner: Pass 0 (no profiler) and Pass 1 (nsys-wrapped) inference execution.

Key constraints:
  - No per-token torch.cuda.synchronize()
  - No tokenizer inside the timing path
  - Batch samples must be distinct (no cloning)
  - fixed_output_tokens must be generated exactly
  - Early EOS / wrong output count → exclusion
"""

import sys
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from exposedpath.manifest import load_manifest
from exposedpath.nvtx import make_invocation_label, make_phase_label
from exposedpath.results import record_exclusion, record_success
from exposedpath.validation import validate_prompt_tokens_sha256_match
from exposedpath.workload import get_batch_inputs, load_prompt_tokens


def load_model(model_path: str, gpu: int = 0):
    """Load model (FP16) + tokenizer on specified GPU."""
    device = f"cuda:{gpu}"
    print(f"[runner] Loading model from: {model_path}  -> {device}")
    try:
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            dtype=torch.float16,
            device_map=device,
            trust_remote_code=True,
        )
    except Exception:
        print("[runner] trust_remote_code=True failed, retrying without...")
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

    print(f"[runner] Model + tokenizer loaded. Vocab size: {vocab_size}")
    return model, tokenizer, vocab_size, device


def run_warmup(
    model,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    output_len: int,
    warmup_iters: int,
):
    """Warmup without NVTX, without results recording."""
    print(f"[runner] Running {warmup_iters} warmup iteration(s)...")
    batch_size, prompt_len = input_ids.shape
    for w in range(warmup_iters):
        print(f"[runner]   Warmup {w + 1}/{warmup_iters}")
        torch.cuda.synchronize()
        with torch.inference_mode():
            outputs = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=True)
        next_token = outputs.logits[:, -1, :].argmax(dim=-1)
        past_key_values = outputs.past_key_values
        for _ in range(1, output_len):
            current_input = next_token.unsqueeze(1)
            with torch.inference_mode():
                outputs = model(input_ids=current_input, past_key_values=past_key_values, use_cache=True)
            next_token = outputs.logits[:, -1, :].argmax(dim=-1)
            past_key_values = outputs.past_key_values
        torch.cuda.synchronize()
    print("[runner] Warmup complete.")


def run_one_invocation(
    model,
    input_ids: torch.Tensor,
    attention_mask: torch.Tensor,
    output_len: int,
    device: str,
    nvtx_invocation_label: str,
    nvtx_full_request_label: str,
    nvtx_prefill_label: str,
    nvtx_decode_label: str,
    eos_token_id: Optional[int] = None,
) -> Dict:
    """Execute a single inference invocation with NVTX annotation.

    No per-token sync. Single final sync inside full_request boundary.
    Returns result dict for record_success.
    """
    batch_size, prompt_len = input_ids.shape

    # ---- Final drain before timing ----
    torch.cuda.synchronize()

    # ==================== NVTX: invocation ====================
    torch.cuda.nvtx.range_push(nvtx_invocation_label)

    t_start_ns = time.perf_counter_ns()

    # ==================== NVTX: full_request ====================
    torch.cuda.nvtx.range_push(nvtx_full_request_label)

    # ==================== PREFILL ====================
    torch.cuda.nvtx.range_push(nvtx_prefill_label)

    with torch.inference_mode():
        outputs = model(input_ids=input_ids, attention_mask=attention_mask, use_cache=True)

    next_token = outputs.logits[:, -1, :].argmax(dim=-1)
    past_key_values = outputs.past_key_values

    # TTFT — first token computed (no separate sync needed; model() already done)
    t_first_token_ns = time.perf_counter_ns()

    torch.cuda.nvtx.range_pop()  # prefill

    # ==================== DECODE ====================
    torch.cuda.nvtx.range_push(nvtx_decode_label)

    actual_output_tokens = 1  # first token from prefill
    early_eos = False

    for step_i in range(1, output_len):
        current_input = next_token.unsqueeze(1)
        with torch.inference_mode():
            outputs = model(input_ids=current_input, past_key_values=past_key_values, use_cache=True)
        next_token = outputs.logits[:, -1, :].argmax(dim=-1)
        past_key_values = outputs.past_key_values
        actual_output_tokens += 1

        # Check for early EOS
        if eos_token_id is not None and (next_token == eos_token_id).any():
            early_eos = True
            break

    # ---- Final sync inside full_request boundary ----
    torch.cuda.synchronize()
    t_end_ns = time.perf_counter_ns()

    torch.cuda.nvtx.range_pop()  # decode
    torch.cuda.nvtx.range_pop()  # full_request
    torch.cuda.nvtx.range_pop()  # invocation

    # ---- Metrics ----
    prefill_ms = (t_first_token_ns - t_start_ns) / 1_000_000.0
    decode_ms = (t_end_ns - t_first_token_ns) / 1_000_000.0

    return {
        "inference_start_ns": t_start_ns,
        "inference_end_ns": t_end_ns,
        "prefill_latency_ms": round(prefill_ms, 3),
        "decode_latency_ms": round(decode_ms, 3),
        "actual_input_tokens": prompt_len,
        "actual_output_tokens": actual_output_tokens,
        "batch_size": batch_size,
        "early_eos": early_eos,
        "output_len_expected": output_len,
    }


def execute_pass(
    manifest_path: Path,
    pass_label: str,
    output_dir: Path,
    use_nvtx: bool = True,
):
    """Execute a full Pass (0 or 1).

    Args:
        manifest_path: Path to wmpc_manifest.json.
        pass_label: 'pass0' or 'pass1'.
        output_dir: Directory for results (created if needed).
        use_nvtx: Whether to emit NVTX ranges (True for pass1, False for pass0).
    """
    manifest = load_manifest(manifest_path)
    run_id = manifest["run_id"]
    experiment_id = manifest["experiment_id"]
    wmpc_id = manifest["wmpc_id"]
    model_path = manifest["model_id"]
    batch_size = manifest["batch_size"]
    fixed_output_tokens = manifest["fixed_output_tokens"]
    warmup_count = manifest["warmup_count"]
    repeat_count = manifest["repeat_count"]
    run_role = manifest.get("run_role", "FORMAL")
    gpu = 0  # TODO: from manifest or CLI

    # ---- SHA-256 integrity check (before any GPU work) ----
    sha_err = validate_prompt_tokens_sha256_match(manifest)
    if sha_err:
        print(f"[runner] FATAL: prompt_tokens_sha256 verification failed:\n  {sha_err}")
        sys.exit(1)
    print(f"[runner] prompt_tokens_sha256 verified: {manifest['prompt_tokens_sha256'][:16]}...")

    # Load prompt_tokens
    pt_path = Path(manifest["prompt_tokens_file"])
    prompt_tokens = load_prompt_tokens(pt_path)
    batch_inputs = get_batch_inputs(prompt_tokens, batch_size, run_role=run_role)
    fixed_input_tokens = batch_inputs["fixed_input_tokens"]

    # Load model
    model, tokenizer, vocab_size, device = load_model(model_path, gpu)
    eos_token_id = tokenizer.eos_token_id

    # Prepare tensors
    input_ids = torch.tensor(batch_inputs["input_ids"], dtype=torch.long, device=device)
    attention_mask = torch.tensor(batch_inputs["attention_mask"], dtype=torch.long, device=device)

    # ---- Warmup (no NVTX, no results) ----
    run_warmup(model, input_ids, attention_mask, fixed_output_tokens, warmup_count)

    # ---- NVTX labels ----
    nvtx_invocation = ""  # placeholder template
    nvtx_full = make_phase_label("full_request") if use_nvtx else ""
    nvtx_prefill = make_phase_label("prefill") if use_nvtx else ""
    nvtx_decode = make_phase_label("decode") if use_nvtx else ""

    # ---- Formal repeats ----
    print(f"[runner] Starting {repeat_count} repeat(s) for {pass_label}...")
    for rep in range(repeat_count):
        print(f"\n[runner] === Repeat {rep + 1}/{repeat_count} ===")
        label = make_invocation_label(experiment_id, wmpc_id, run_id, pass_label, rep) if use_nvtx else ""

        try:
            result = run_one_invocation(
                model=model,
                input_ids=input_ids,
                attention_mask=attention_mask,
                output_len=fixed_output_tokens,
                device=device,
                nvtx_invocation_label=label,
                nvtx_full_request_label=nvtx_full,
                nvtx_prefill_label=nvtx_prefill,
                nvtx_decode_label=nvtx_decode,
                eos_token_id=eos_token_id,
            )

            # Validate output
            if result["actual_output_tokens"] != fixed_output_tokens:
                reason = (
                    f"output token count mismatch: expected {fixed_output_tokens}, "
                    f"got {result['actual_output_tokens']}"
                    + (" (early EOS)" if result["early_eos"] else "")
                )
                record_exclusion(output_dir, run_id, rep, reason)
                print(f"  EXCLUDED: {reason}")
                continue

            if result["early_eos"]:
                record_exclusion(output_dir, run_id, rep, "early EOS before fixed_output_tokens")
                print(f"  EXCLUDED: early EOS")
                continue

            record_success(
                output_dir=output_dir,
                run_id=run_id,
                repeat_index=rep,
                inference_start_ns=result["inference_start_ns"],
                inference_end_ns=result["inference_end_ns"],
                prefill_latency_ms=result["prefill_latency_ms"],
                decode_latency_ms=result["decode_latency_ms"],
                actual_input_tokens=result["actual_input_tokens"],
                actual_output_tokens=result["actual_output_tokens"],
                batch_size=result["batch_size"],
            )
            print(
                f"  prefill={result['prefill_latency_ms']:.1f}ms  "
                f"decode={result['decode_latency_ms']:.1f}ms  "
                f"e2e={result['inference_end_ns'] - result['inference_start_ns']:.1f}ms"
            )

        except torch.cuda.OutOfMemoryError as e:
            record_exclusion(output_dir, run_id, rep, "OOM", exception=str(e))
            print(f"  EXCLUDED: OOM")
        except Exception as e:
            record_exclusion(output_dir, run_id, rep, "runtime_error", exception=str(e))
            traceback.print_exc()
            print(f"  EXCLUDED: {e}")

    print(f"\n[runner] {pass_label} complete.")
