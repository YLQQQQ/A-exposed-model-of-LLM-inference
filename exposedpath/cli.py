"""
CLI entry points for ExposedPath v3 Pilot.

Commands:
  python -m exposedpath validate-manifest --manifest <path>
  python -m exposedpath prepare-prompt-tokens ...
  python -m exposedpath update-prompt-sha --manifest <path>
  python -m exposedpath run-pass0 --manifest <path>
  python -m exposedpath run-pass1 --manifest <path>
"""

import argparse
import sys
from pathlib import Path

from exposedpath.manifest import (
    load_manifest, save_manifest, create_manifest, finalize_manifest,
    update_prompt_sha,
)
from exposedpath.validation import (
    validate_manifest_core, validate_manifest_wmpc_stability,
    validate_prompt_tokens_sha256_match, compute_prompt_tokens_sha256,
)
from exposedpath.workload import load_prompt_tokens
from exposedpath.runner import execute_pass


def cmd_validate_manifest(args):
    """Validate a WMPC manifest file."""
    path = Path(args.manifest)
    if not path.is_file():
        print(f"ERROR: File not found: {path}")
        sys.exit(1)

    try:
        manifest = load_manifest(path)
    except (FileNotFoundError, ValueError) as e:
        print(f"ERROR: {e}")
        sys.exit(1)

    # Check core fields
    errors = validate_manifest_core(manifest)
    if errors:
        print("Manifest core validation FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # Check wmpc stability
    wmpc_err = validate_manifest_wmpc_stability(manifest)
    if wmpc_err:
        print(f"WMPC stability check FAILED: {wmpc_err}")
        sys.exit(1)

    # Verify prompt_tokens exists and SHA-256 matches
    pt_path = Path(manifest.get("prompt_tokens_file", ""))
    if not pt_path.is_file():
        print(f"ERROR: prompt_tokens_file not found: {pt_path}")
        sys.exit(1)

    try:
        load_prompt_tokens(pt_path)
        print(f"prompt_tokens structure valid: {pt_path}")
    except (ValueError, FileNotFoundError) as e:
        print(f"prompt_tokens validation FAILED: {e}")
        sys.exit(1)

    # Hard SHA-256 check — must pass for any run_role
    sha_err = validate_prompt_tokens_sha256_match(manifest)
    if sha_err:
        print(f"ERROR: prompt_tokens_sha256 verification FAILED:\n  {sha_err}")
        sys.exit(1)
    print(f"prompt_tokens_sha256 verified OK")

    print("Manifest validation PASSED.")
    print(f"  experiment_id: {manifest['experiment_id']}")
    print(f"  wmpc_id:       {manifest['wmpc_id']}")
    print(f"  run_id:        {manifest['run_id']}")
    print(f"  run_role:      {manifest.get('run_role', 'FORMAL')}")


def cmd_prepare_prompt_tokens(args):
    """Prepare a prompt_tokens.json file from a tokenizer (offline, no inference)."""
    from transformers import AutoTokenizer

    model_path = args.model_path
    output = Path(args.output) if args.output else Path("prompt_tokens.json")
    fixed_input_tokens = args.fixed_input_tokens
    num_samples = args.num_samples

    print(f"[prepare-prompt-tokens] Loading tokenizer from: {model_path}")
    tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print(f"[prepare-prompt-tokens] Tokenizer loaded. vocab_size={tokenizer.vocab_size}")

    # Generate synthetic samples (random valid token IDs)
    import random
    random.seed(42)

    samples = []
    for i in range(num_samples):
        # Use different random seeds per sample to ensure distinctness
        random.seed(42 + i * 1000)
        input_ids = [random.randint(0, tokenizer.vocab_size - 1) for _ in range(fixed_input_tokens)]
        samples.append({
            "sample_index": i,
            "input_ids": input_ids,
            "source_text": f"synthetic sample {i}",
        })

    data = {
        "schema_version": "exposedpath-v3",
        "tokenizer_id": model_path,
        "tokenizer_revision": "unknown",
        "chat_template": None,
        "special_tokens": {
            "eos_token_id": tokenizer.eos_token_id,
            "pad_token_id": tokenizer.pad_token_id,
            "bos_token_id": tokenizer.bos_token_id,
        },
        "fixed_input_tokens": fixed_input_tokens,
        "samples": samples,
    }

    import json

    # Atomic write: temp file then rename
    import os
    import tempfile as tmpmod
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(data, indent=2, ensure_ascii=False)
    tmp_fd, tmp_path = tmpmod.mkstemp(
        suffix=".json", prefix=".prompt_tokens_", dir=str(output.parent),
    )
    try:
        with os.fdopen(tmp_fd, "w", encoding="utf-8") as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_path, str(output))
    except BaseException:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass
        raise

    sha = compute_prompt_tokens_sha256(output)
    print(f"[prepare-prompt-tokens] Wrote {num_samples} samples to: {output}")
    print(f"[prepare-prompt-tokens] SHA-256: {sha}")


def cmd_run_pass(args):
    """Run Pass 0 or Pass 1."""
    pass_label = args.pass_label
    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir) if args.output_dir else Path(f"./{pass_label}")

    # Validate manifest first
    manifest = load_manifest(manifest_path)
    errors = validate_manifest_core(manifest)
    if errors:
        print("ERROR: Manifest validation failed:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    # SHA-256 check BEFORE any GPU work (also done inside execute_pass)
    sha_err = validate_prompt_tokens_sha256_match(manifest)
    if sha_err:
        print(f"ERROR: prompt_tokens_sha256 verification FAILED:\n  {sha_err}")
        sys.exit(1)
    print(f"prompt_tokens_sha256 verified: {manifest['prompt_tokens_sha256'][:16]}...")

    use_nvtx = (pass_label == "pass1")
    execute_pass(
        manifest_path=manifest_path,
        pass_label=pass_label,
        output_dir=output_dir,
        use_nvtx=use_nvtx,
    )


def cmd_update_prompt_sha(args):
    """Explicitly recompute and update prompt_tokens_sha256 in a manifest."""
    manifest_path = Path(args.manifest)
    if not manifest_path.is_file():
        print(f"ERROR: Manifest file not found: {manifest_path}")
        sys.exit(1)

    try:
        updated = update_prompt_sha(manifest_path)
    except (FileNotFoundError, ValueError, OSError) as e:
        print(f"ERROR: update-prompt-sha failed: {e}")
        sys.exit(1)

    print(f"Updated prompt_tokens_sha256 in: {manifest_path}")
    print(f"  new SHA-256: {updated['prompt_tokens_sha256']}")


def main():
    parser = argparse.ArgumentParser(
        description="ExposedPath v3 — LLM Inference Exposed-Latency Accounting (Pilot)",
    )
    sub = parser.add_subparsers(dest="command", help="Available commands")

    # validate-manifest
    p_validate = sub.add_parser("validate-manifest", help="Validate a WMPC manifest")
    p_validate.add_argument("--manifest", required=True, help="Path to wmpc_manifest.json")

    # prepare-prompt-tokens
    p_prep = sub.add_parser("prepare-prompt-tokens", help="Generate prompt_tokens.json offline")
    p_prep.add_argument("--model-path", required=True, help="Path to tokenizer/model directory")
    p_prep.add_argument("--fixed-input-tokens", type=int, required=True, help="Fixed input token count")
    p_prep.add_argument("--num-samples", type=int, default=16, help="Number of distinct samples to generate")
    p_prep.add_argument("--output", default="prompt_tokens.json", help="Output path")

    # update-prompt-sha
    p_upsha = sub.add_parser("update-prompt-sha", help="Recompute and update prompt_tokens_sha256 in manifest")
    p_upsha.add_argument("--manifest", required=True, help="Path to wmpc_manifest.json")

    # run-pass0 / run-pass1
    for pl in ["pass0", "pass1"]:
        p_pass = sub.add_parser(f"run-{pl}", help=f"Execute {pl.upper()} (no profiler)" if pl == "pass0" else f"Execute {pl.upper()} (with NVTX, for nsys wrapping)")
        p_pass.add_argument("--manifest", required=True, help="Path to wmpc_manifest.json")
        p_pass.add_argument("--output-dir", default=None, help="Output directory for results")

    args = parser.parse_args()

    if args.command == "validate-manifest":
        cmd_validate_manifest(args)
    elif args.command == "prepare-prompt-tokens":
        cmd_prepare_prompt_tokens(args)
    elif args.command == "update-prompt-sha":
        cmd_update_prompt_sha(args)
    elif args.command in ("run-pass0", "run-pass1"):
        args.pass_label = "pass0" if args.command == "run-pass0" else "pass1"
        cmd_run_pass(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
