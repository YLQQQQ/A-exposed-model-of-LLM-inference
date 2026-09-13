"""Gate 5 Task 6: versioned A/B bundle integration tests."""

from __future__ import annotations

import json
import gzip
import hashlib
from pathlib import Path

import pytest

from exposedpath_v141.ab_bundle import ABBundleError, analyze_ab, load_ab_bundle
from exposedpath_v141.cli import main
from tests.test_v141_ab_inputs import _write_canonical, _write_s_bundle


def _make_inputs(tmp_path: Path) -> tuple[Path, Path]:
    canonical = _write_canonical(tmp_path / "canonical")
    return canonical, _write_s_bundle(tmp_path / "s", canonical)


def _rewrite_gzip_jsonl(path: Path, records: list[dict[str, object]]) -> None:
    """Rewrite a record file and its manifest metadata as a capable tamperer could."""

    with path.open("wb") as raw_handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw_handle, mtime=0) as handle:
            for record in records:
                handle.write(
                    (json.dumps(record, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")
                )


def _update_file_metadata(manifest_path: Path, file_key: str) -> None:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    entry = manifest["files"][file_key]
    record_path = manifest_path.parent / entry["filename"]
    entry["size_bytes"] = record_path.stat().st_size
    entry["sha256"] = hashlib.sha256(record_path.read_bytes()).hexdigest().upper()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")


def test_analyze_ab_writes_reloadable_deterministic_bundle(tmp_path):
    """Changing gzip metadata or omitting a record must break this observable bundle contract."""

    canonical, s_manifest = _make_inputs(tmp_path)
    first = analyze_ab(canonical, s_manifest, tmp_path / "first")
    second = analyze_ab(canonical, s_manifest, tmp_path / "second")

    first_bundle = load_ab_bundle(first)
    second_manifest = json.loads(second.read_text(encoding="utf-8"))
    first_manifest = first_bundle["manifest"]
    assert first_manifest["files"] == second_manifest["files"]
    assert first_manifest["summary"] == {
        "window_count": 3,
        "physical_sync_count": 1,
        "b_valid_count": 1,
        "b_not_applicable_count": 0,
        "b_ambiguous_count": 0,
        "b_invalid_count": 0,
    }
    assert len(first_bundle["a_window_records"]) == 3
    assert len(first_bundle["b_sync_records"]) == 1
    assert first_manifest["research_eligibility"] == {
        "formal_evidence": False,
        "q0_status": "NOT_RUN",
        "scope": "A_B_LAYER_ONLY",
    }


def test_ab_loader_rejects_tampered_record_file_and_analyze_refuses_output_reuse(tmp_path):
    """A stale hash or an existing destination must never be treated as a valid new analysis."""

    canonical, s_manifest = _make_inputs(tmp_path)
    manifest_path = analyze_ab(canonical, s_manifest, tmp_path / "ab")
    records_path = manifest_path.parent / "a_window_records.jsonl.gz"
    records_path.write_bytes(records_path.read_bytes() + b"tamper")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["a_window_records"]["size_bytes"] = records_path.stat().st_size
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ABBundleError, match="SHA-256"):
        load_ab_bundle(manifest_path)
    with pytest.raises(FileExistsError, match="拒绝覆盖"):
        analyze_ab(canonical, s_manifest, manifest_path.parent)


def test_ab_loader_rechecks_a_runtime_conservation_after_metadata_matched_tampering(tmp_path):
    """Would fail if a hash-correct record could bypass frozen A accounting invariants."""

    canonical, s_manifest = _make_inputs(tmp_path)
    manifest_path = analyze_ab(canonical, s_manifest, tmp_path / "ab")
    records_path = manifest_path.parent / "a_window_records.jsonl.gz"
    with gzip.open(records_path, "rt", encoding="utf-8") as handle:
        records = [json.loads(line) for line in handle]
    records[0]["A_host_path_ns"] += 1
    _rewrite_gzip_jsonl(records_path, records)
    _update_file_metadata(manifest_path, "a_window_records")

    with pytest.raises(ABBundleError, match="A 顶层守恒失败"):
        load_ab_bundle(manifest_path)


def test_ab_loader_rejects_s_lineage_conflict_when_only_s_source_is_available(tmp_path):
    """Would fail if an S manifest could point at another Canonical bundle after its hash changed."""

    canonical, s_manifest = _make_inputs(tmp_path)
    manifest_path = analyze_ab(canonical, s_manifest, tmp_path / "ab")
    s = json.loads(s_manifest.read_text(encoding="utf-8"))
    s["source"]["canonical_manifest_sha256"] = "B" * 64
    s_manifest.write_text(json.dumps(s), encoding="utf-8")
    ab_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    ab_manifest["source"]["s_manifest_sha256"] = hashlib.sha256(
        s_manifest.read_bytes()
    ).hexdigest().upper()
    manifest_path.write_text(json.dumps(ab_manifest), encoding="utf-8")

    with pytest.raises(ABBundleError, match="S-to-Canonical lineage"):
        load_ab_bundle(manifest_path, s_manifest=s_manifest)


@pytest.mark.parametrize("source_name", ["canonical_manifest", "s_manifest"])
def test_ab_loader_fail_closes_missing_requested_lineage_source(tmp_path, source_name):
    """A requested external lineage edge must not leak a filesystem exception."""

    canonical, s_manifest = _make_inputs(tmp_path)
    manifest_path = analyze_ab(canonical, s_manifest, tmp_path / "ab")

    with pytest.raises(ABBundleError, match="manifest"):
        load_ab_bundle(
            manifest_path,
            **{source_name: tmp_path / "missing" / ("canonical_manifest.json" if source_name == "canonical_manifest" else "s_manifest.json")},
        )


def test_analyze_ab_invalid_input_leaves_no_partial_output_directory(tmp_path):
    """A lineage failure must occur before a caller can observe an A/B destination."""

    canonical, s_manifest = _make_inputs(tmp_path)
    manifest = json.loads(s_manifest.read_text(encoding="utf-8"))
    manifest["source"]["canonical_manifest_sha256"] = "B" * 64
    s_manifest.write_text(json.dumps(manifest), encoding="utf-8")
    output_dir = tmp_path / "ab"

    with pytest.raises(ABBundleError, match="输入或计算失败"):
        analyze_ab(canonical, s_manifest, output_dir)

    assert not output_dir.exists()


def test_analyze_ab_cli_preserves_not_run_qualification(tmp_path, capsys):
    """CLI success must report a bundle without upgrading Q0 or Formal evidence eligibility."""

    canonical, s_manifest = _make_inputs(tmp_path)
    status = main(
        [
            "analyze-ab",
            "--canonical-manifest", str(canonical),
            "--s-manifest", str(s_manifest),
            "--output-dir", str(tmp_path / "ab"),
        ]
    )

    assert status == 0
    assert "q0_status: NOT_RUN" in capsys.readouterr().out
