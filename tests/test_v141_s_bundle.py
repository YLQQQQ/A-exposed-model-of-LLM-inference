"""S 层版本化产物与 CLI 测试。"""

from __future__ import annotations

import gzip
import hashlib
import json
from pathlib import Path

import pytest

from exposedpath_v141.canonical_raw import load_canonical_raw_schema
from exposedpath_v141.cli import main
from exposedpath_v141.contract import load_contract_bundle
from exposedpath_v141.s_bundle import (
    SBundleError,
    analyze_canonical_to_s,
    load_s_layer_schema,
    validate_s_layer_schema,
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_empty_canonical(path: Path) -> Path:
    path.mkdir()
    schema = load_canonical_raw_schema()
    files = {}
    for kind, spec in schema["record_types"].items():
        target = path / spec["filename"]
        with target.open("xb") as raw_handle:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0):
                pass
        files[kind] = {
            "filename": target.name,
            "record_count": 0,
            "sha256": _sha256(target),
            "size_bytes": target.stat().st_size,
        }
    manifest = {
        "schema_version": schema["schema_version"],
        "measurement_contract_version": schema["measurement_contract_version"],
        "adapter_id": schema["adapter_id"],
        "analyzer_version": "test",
        "generated_at_utc": "2026-09-11T00:00:00+00:00",
        "data_role": "Engineering",
        "source": {"sqlite": {"sha256": "A" * 64}},
        "clock": schema["clock_model"],
        "identity": {"status": "VALID", "issues": []},
        "execution_context": {"default_stream_mode": "NO_DEFAULT_STREAM_OBSERVED", "selected_device_id": 0},
        "files": files,
        "observation_validity": {"status": "valid", "issues": []},
        "research_eligibility": {"formal_evidence": False, "q0_status": "NOT_RUN"},
    }
    manifest_path = path / "canonical_manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    return manifest_path


def _read_records(path: Path) -> list[dict]:
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle]


def test_committed_s_schema_covers_frozen_contract_output_fields():
    schema = load_s_layer_schema()
    validate_s_layer_schema(schema)
    required = set(load_contract_bundle()["contract"]["s_layer"]["output_fields"])

    assert schema["schema_version"] == "exposedpath-s-layer/0.2.0"
    assert required <= set(schema["sync_record_fields"])
    assert schema["input_schema_version"] == "exposedpath-canonical-raw/0.2.0"


def test_empty_canonical_bundle_produces_versioned_immutable_s_bundle(tmp_path):
    canonical_manifest = _write_empty_canonical(tmp_path / "canonical")
    output = tmp_path / "s-output"

    manifest_path = analyze_canonical_to_s(canonical_manifest, output)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert manifest["schema_version"] == "exposedpath-s-layer/0.2.0"
    assert manifest["source"]["canonical_manifest_sha256"] == _sha256(canonical_manifest)
    assert manifest["source"]["sync_registry"]["version"] == (
        "exposedpath-sync-registry-0.2.0"
    )
    assert len(manifest["source"]["sync_registry"]["sha256"]) == 64
    assert manifest["summary"] == {
        "physical_sync_count": 0,
        "valid_nonempty_count": 0,
        "valid_empty_count": 0,
        "ambiguous_count": 0,
        "invalid_count": 0,
    }
    assert _read_records(output / "s_sync_records.jsonl.gz") == []
    with pytest.raises(FileExistsError, match="拒绝覆盖"):
        analyze_canonical_to_s(canonical_manifest, output)


def test_s_cli_reports_scope_without_claiming_q0(tmp_path, capsys):
    canonical_manifest = _write_empty_canonical(tmp_path / "canonical")
    output = tmp_path / "s-output"

    exit_code = main([
        "analyze-s", "--canonical-manifest", str(canonical_manifest),
        "--output-dir", str(output),
    ])
    printed = capsys.readouterr().out

    assert exit_code == 0
    assert "s_schema_version: exposedpath-s-layer/0.2.0" in printed
    assert "q0_status: NOT_RUN" in printed
    assert "Gate 4" not in printed


def test_s_schema_rejects_missing_contract_field():
    schema = dict(load_s_layer_schema())
    schema["sync_record_fields"] = list(schema["sync_record_fields"])
    schema["sync_record_fields"].remove("terminal")

    with pytest.raises(SBundleError, match="合同字段"):
        validate_s_layer_schema(schema)
