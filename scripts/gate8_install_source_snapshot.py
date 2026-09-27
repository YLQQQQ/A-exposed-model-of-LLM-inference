"""Bounded Windows install evidence; stdlib only, no package imports or CUDA calls.

Run a transferred copy with the fixed checkout's .venv Python and -I -S.
This is a source inventory, NOT a stream-mode/ownership/qualification adapter.
"""

import argparse
import ast
import base64
import csv
from datetime import datetime, timezone
from email.parser import BytesParser
import hashlib
import io
import json
from pathlib import Path
import sys


VERSION = "gate8-install-source-snapshot/0.1.0"
TARGETS = {
    "torch": ("2.6.0+cu124", (
        "torch/version.py", "torch/cuda/__init__.py", "torch/cuda/streams.py",
        "torch/include/c10/cuda/CUDAFunctions.h", "torch/include/c10/cuda/CUDAStream.h",
        "torch/lib/c10_cuda.dll", "torch/lib/torch_cuda.dll",
    )),
    "transformers": ("5.17.0", (
        "transformers/modeling_utils.py", "transformers/core_model_loading.py",
        "transformers/integrations/accelerate.py",
    )),
}
REQUEST_TARGETS = {
    'torch': ('2.6.0+cu124', ('torch/version.py',)),
    'transformers': ('5.17.0', (
        'transformers/modeling_utils.py',
        'transformers/models/qwen2/modeling_qwen2.py',
        'transformers/models/qwen2/configuration_qwen2.py',
        'transformers/masking_utils.py', 'transformers/cache_utils.py',
        'transformers/integrations/sdpa_attention.py',
    )),
}
TEXT_LIMIT = 2 * 1024 * 1024
BINARY_LIMIT = 4 * 1024 * 1024 * 1024


def _contained(path, root):
    resolved = path.resolve()
    if not resolved.is_relative_to(root) or resolved != path.absolute():
        raise ValueError("SELECTED_PATH_REDIRECTED")
    return resolved


def _bytes(path, root, limit):
    path = _contained(path, root)
    if path.stat().st_size > limit:
        raise ValueError("SELECTED_FILE_TOO_LARGE")
    data = path.read_bytes()
    if len(data) > limit:
        raise ValueError("SELECTED_FILE_TOO_LARGE")
    return data


def _identity(data):
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _write_json(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        json.dump(value, handle, ensure_ascii=True, sort_keys=True, indent=2)
        handle.write("\n")


def _literals(data):
    result = {"__version__": None, "cuda": None, "git_version": None}
    tree = ast.parse(data.decode("utf-8-sig"))
    for node in tree.body:
        targets = node.targets if isinstance(node, ast.Assign) else (
            [node.target] if isinstance(node, ast.AnnAssign) else [])
        for target in targets:
            if isinstance(target, ast.Name) and target.id in result:
                try:
                    value = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    value = None
                result[target.id] = value if isinstance(value, str) else None
    return result


def snapshot(site, output, *, profile='installation'):
    """Read an explicit site-packages root, write a fresh independent receipt."""
    if profile not in {'installation','qwen-request'}:
        raise ValueError('UNKNOWN_SELECTION_PROFILE')
    targets = REQUEST_TARGETS if profile=='qwen-request' else TARGETS
    site, output = Path(site).resolve(strict=True), Path(output).absolute()
    resolved_output = output.resolve()
    if resolved_output.is_relative_to(site) or site.is_relative_to(resolved_output):
        raise ValueError("OUTPUT_OVERLAPS_INPUT")
    output.mkdir(parents=False, exist_ok=False)
    report = {
        "schema_version": VERSION,
        "role": "ENGINEERING_SOURCE_IDENTITY_ONLY",
        "collected_utc": datetime.now(timezone.utc).isoformat(),
        "interpreter": {"executable": sys.executable, "version": sys.version.split()[0],
                        "isolated": bool(sys.flags.isolated), "no_site": bool(sys.flags.no_site)},
        "site_packages": str(site),
        "tool": _identity(Path(__file__).read_bytes()),
        "packages": {}, "files": [], "issues": [], "torch_source_literals": {},
        "default_stream_mode": "UNKNOWN", "worker_trace_ownership": "UNKNOWN",
        "qualification": "NOT_ASSESSED",
    }
    if profile=='qwen-request':
        report.update(schema_version='gate8-install-source-snapshot/0.2.0',
                      selection_profile='qwen-request/0.1.0',
                      actual_attention_backend='UNKNOWN_NOT_EXECUTED')
    artifacts = {}

    def issue(code, relative):
        report["issues"].append({"code": code, "relative_path": relative})

    for name, (expected, selected) in targets.items():
        infos = sorted(site.glob(f"{name}-*.dist-info"))
        if len(infos) != 1:
            issue("PACKAGE_NOT_UNIQUE", name)
            continue
        info = infos[0]
        try:
            _contained(info, site)
            metadata_bytes = _bytes(info / "METADATA", site, TEXT_LIMIT)
            metadata = BytesParser().parsebytes(metadata_bytes, headersonly=True)
            names, versions = metadata.get_all("Name", []), metadata.get_all("Version", [])
            if len(names) != 1 or len(versions) != 1:
                raise ValueError("PACKAGE_METADATA_AMBIGUOUS")
            actual_name, actual_version = names[0], versions[0]
            report["packages"][name] = {
                "name": actual_name, "version": actual_version,
                "metadata_identity": _identity(metadata_bytes),
            }
            if actual_name != name or actual_version != expected:
                issue("PACKAGE_VERSION_MISMATCH", name)
                continue
            wheel = _bytes(info / "WHEEL", site, TEXT_LIMIT)
            report["packages"][name]["wheel_identity"] = _identity(wheel)
            report["packages"][name]["wheel_tags"] = [
                line[5:].strip() for line in wheel.decode("utf-8").splitlines()
                if line.startswith("Tag: ")]
            record = _bytes(info / "RECORD", site, 8 * TEXT_LIMIT)
            report["packages"][name]["record_identity"] = _identity(record)
            rows = {}
            for row in csv.reader(io.StringIO(record.decode("utf-8"))):
                if row and row[0] in selected:
                    if len(row) != 3 or row[0] in rows:
                        raise ValueError("RECORD_AMBIGUOUS")
                    rows[row[0]] = row[1:]
        except (OSError, ValueError, UnicodeError) as exc:
            issue(str(exc) if isinstance(exc, ValueError) else type(exc).__name__, name)
            continue

        for relative in selected:
            item = {"relative_path": relative, "kind": "BINARY_HASH_ONLY" if relative.endswith(".dll") else "SOURCE_COPY",
                    "status": "UNKNOWN", "record_match": None}
            report["files"].append(item)
            try:
                path = _contained(site / relative, site)
                before = path.stat()
                limit = BINARY_LIMIT if relative.endswith(".dll") else TEXT_LIMIT
                if before.st_size > limit:
                    raise ValueError("SELECTED_FILE_TOO_LARGE")
                if relative.endswith(".dll"):
                    digest, size = hashlib.sha256(), 0
                    with path.open("rb") as handle:
                        while chunk := handle.read(1024 * 1024):
                            size += len(chunk)
                            if size > limit:
                                raise ValueError("SELECTED_FILE_TOO_LARGE")
                            digest.update(chunk)
                    identity = {"bytes": size, "sha256": digest.hexdigest()}
                else:
                    data = _bytes(path, site, limit)
                    identity = _identity(data)
                after = path.stat()
                if (before.st_size, before.st_mtime_ns, before.st_ino) != (
                        after.st_size, after.st_mtime_ns, after.st_ino):
                    raise ValueError("SELECTED_FILE_CHANGED_DURING_READ")
                item.update(identity)
                row = rows.get(relative)
                encoded = base64.urlsafe_b64encode(bytes.fromhex(identity["sha256"])).decode().rstrip("=")
                item["record_match"] = row == ["sha256=" + encoded, str(identity["bytes"])]
                if not item["record_match"]:
                    issue("RECORD_HASH_MISMATCH", relative)
                if not relative.endswith(".dll"):
                    target = output / "selected_sources" / relative
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with target.open("xb") as handle:
                        handle.write(data)
                    artifacts[target.relative_to(output).as_posix()] = identity
                if relative == "torch/version.py":
                    report["torch_source_literals"] = _literals(data)
                    literals = report["torch_source_literals"]
                    if literals["__version__"] != "2.6.0+cu124" or literals["cuda"] != "12.4":
                        issue("TORCH_LITERAL_MISMATCH", relative)
                item["status"] = "READ"
            except FileNotFoundError:
                issue("SELECTED_FILE_MISSING", relative)
            except (OSError, ValueError, SyntaxError, UnicodeError) as exc:
                issue(str(exc) if isinstance(exc, ValueError) else type(exc).__name__, relative)
    report["status"] = "SNAPSHOT_INCOMPLETE" if report["issues"] else "SNAPSHOT_COMPLETE_NOT_QUALIFICATION"
    receipt = output / "source_snapshot.json"
    _write_json(receipt, report)
    artifacts[receipt.name] = _identity(receipt.read_bytes())
    # Explicit completed outputs only. Never enumerate a manifest while writing it.
    _write_json(output / "artifact_manifest.json", artifacts)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument('--profile', choices=('installation','qwen-request'), default='installation')
    args = parser.parse_args()
    if not sys.flags.isolated or not sys.flags.no_site:
        parser.error("REQUIRE_ISOLATED_NO_SITE: launch Python with -I -S")
    executable = args.repo / ".venv/Scripts/python.exe"
    if sys.platform != "win32" or not executable.is_file() or not executable.samefile(sys.executable):
        parser.error("REQUIRE_REPO_VENV: use the fixed checkout .venv/Scripts/python.exe")
    report = snapshot(args.repo / ".venv/Lib/site-packages", args.output, profile=args.profile)
    print(report["status"])
    return 1 if report["issues"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
