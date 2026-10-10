"""Forensic preservation is not a quiescence or scientific acceptance gate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import zipfile

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/gate13_forensic_copy.py"


@pytest.fixture
def tool():
    assert SCRIPT.is_file(), "Missing standalone UNKNOWN-preserving forensic tool"
    spec = importlib.util.spec_from_file_location("forensic", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def scene(tmp_path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "partial").mkdir()
    (source / "中文.bin").write_bytes(b"\x00\xff\r\n")
    (source / ".active").write_bytes(b"keep")
    (source / "receipt.json").write_text('{"status":"BLOCKED","writer":"UNKNOWN"}')
    identity = tmp_path / "instance_receipt.json"
    identity.write_text(json.dumps({"role": "TARGETED_PROCESS_INSTANCE_READONLY_ONCE",
                                  "historical_descendant_exit_status": "UNKNOWN_STOP_AND_INSPECT_NO_RETRY"}))
    return source, identity, hashlib.sha256(identity.read_bytes()).hexdigest()


def test_complete_archive_preserves_unknown_marker_binary_and_empty_dirs(tool, scene, tmp_path):
    source, identity, digest = scene
    before = {p.name: p.read_bytes() for p in source.iterdir() if p.is_file()}
    result = tool.capture(source, tmp_path / "diagnostic", tmp_path / "evidence.zip", identity, digest)
    assert result["status"] == "FORENSIC_BYTE_COPY_VERIFIED_NOT_ACCEPTANCE"
    assert result["absence_of_writers_proven"] is False
    assert result["historical_descendant_exit_status"] == "UNKNOWN_STOP_AND_INSPECT_NO_RETRY"
    assert {p.name: p.read_bytes() for p in source.iterdir() if p.is_file()} == before
    with zipfile.ZipFile(tmp_path / "evidence.zip") as archive:
        assert archive.read("source/中文.bin") == b"\x00\xff\r\n"
        assert archive.read("source/.active") == b"keep"
        assert "source/partial/" in archive.namelist()
        assert archive.testzip() is None
        manifest = json.loads(archive.read("forensic_manifest.json"))
        assert {r["path"] for r in manifest["entries"]} | {"forensic_manifest.json"} == set(archive.namelist())


@pytest.mark.parametrize("name", ["../outside", "C:/bad", "/bad", "a\\b", "a//b", "a/./b", "CON", "a. "])
def test_unsafe_portable_paths_rejected(tool, name):
    with pytest.raises(ValueError, match="PATH"):
        tool.safe_name(name)


def test_case_colliding_paths_rejected(tool):
    with pytest.raises(ValueError, match="DUPLICATE"):
        tool.unique_names(["a", "A"])


def test_reparse_attribute_rejected_without_following(tool):
    class FakeStat:
        st_file_attributes = 0x400
    with pytest.raises(ValueError, match="REPARSE"):
        tool.check_stat(FakeStat())


def test_actual_symlink_rejected(tool, scene, tmp_path):
    source, _, _ = scene
    link = source / "outside"
    try:
        link.symlink_to(tmp_path, target_is_directory=True)
    except OSError:
        pytest.skip("OS does not grant creation of symlinks")
    with pytest.raises(ValueError, match="REPARSE"):
        tool.snapshot(source)


@pytest.mark.parametrize("kind", ["changed", "added", "missing", "empty_dir"])
def test_fixed_source_changes_cannot_be_accepted(tool, scene, kind):
    source, _, _ = scene
    frozen = tool.snapshot(source)
    if kind == "changed":
        (source / "中文.bin").write_bytes(b"tampered")
    elif kind == "added":
        (source / "extra").write_bytes(b"new")
    elif kind == "missing":
        (source / ".active").unlink()
    else:
        (source / "partial").rmdir()
    with pytest.raises(ValueError, match="SOURCE_CHANGED"):
        tool.assert_snapshot(source, frozen)


@pytest.mark.parametrize("kind", ["extra", "missing", "tamper", "duplicate"])
def test_zip_full_coverage_and_hash_reject_faults(tool, scene, tmp_path, kind):
    source, identity, digest = scene
    archive = tmp_path / "evidence.zip"
    tool.capture(source, tmp_path / "diagnostic", archive, identity, digest)
    with zipfile.ZipFile(archive) as original:
        items = [(i.filename, original.read(i.filename)) for i in original.infolist()]
    manifest = next(data for name, data in items if name == "forensic_manifest.json")
    if kind == "missing":
        items = [(name, data) for name, data in items if name != "source/.active"]
    elif kind == "tamper":
        items = [(name, b"evil" if name == "source/.active" else data) for name, data in items]
    elif kind == "extra":
        items.append(("unlisted", b"evil"))
    else:
        items.append(("SOURCE/.ACTIVE", b"evil"))
    bad = tmp_path / "bad.zip"
    with zipfile.ZipFile(bad, "w") as output:
        for name, data in items:
            output.writestr(name, data)
    with pytest.raises(ValueError):
        tool.verify_zip(bad, manifest)


def test_wrong_identity_hash_stops_before_archive(tool, scene, tmp_path):
    source, identity, _ = scene
    with pytest.raises(ValueError, match="IDENTITY_HASH"):
        tool.capture(source, tmp_path / "diagnostic", tmp_path / "evidence.zip", identity, "0" * 64)
    assert not (tmp_path / "evidence.zip").exists()


def test_outputs_inside_source_rejected_before_writes(tool, scene):
    source, identity, digest = scene
    with pytest.raises(ValueError, match="OUTPUT_SCOPE"):
        tool.capture(source, source / "new", source / "bad.zip", identity, digest)
    assert not (source / "new").exists()


def test_mid_copy_change_preserves_failed_copy_and_external_failure_receipt(tool, scene, tmp_path, monkeypatch):
    source, identity, digest = scene
    original = tool.verify_zip
    def mutate_after_copy(archive, manifest):
        original(archive, manifest)
        (source / "中文.bin").write_bytes(b"changed after copy")
    monkeypatch.setattr(tool, "verify_zip", mutate_after_copy)
    with pytest.raises(ValueError, match="SOURCE_CHANGED"):
        tool.capture(source, tmp_path / "diagnostic", tmp_path / "evidence.zip", identity, digest)
    assert (tmp_path / "evidence.zip.partial").exists()
    assert not (tmp_path / "evidence.zip").exists()
    failure = json.loads((tmp_path / "diagnostic/forensic_receipt.json").read_text())
    assert failure["status"] == "FAILED_PRESERVE_COPY_STOP"


def test_existing_output_never_overwritten(tool, scene, tmp_path):
    source, identity, digest = scene
    archive = tmp_path / "existing.zip"
    archive.write_bytes(b"keep")
    with pytest.raises(ValueError, match="OUTPUT_EXISTS"):
        tool.capture(source, tmp_path / "diagnostic", archive, identity, digest)
    assert archive.read_bytes() == b"keep"


def test_zip_crc_corruption_rejected(tool, scene, tmp_path):
    source, identity, digest = scene
    archive = tmp_path / "evidence.zip"
    tool.capture(source, tmp_path / "diagnostic", archive, identity, digest)
    with zipfile.ZipFile(archive) as package:
        info = package.getinfo("source/.active")
        manifest = package.read("forensic_manifest.json")
    data = bytearray(archive.read_bytes())
    # Alter the central-directory CRC explicitly; changing a deflate padding bit
    # need not change any uncompressed byte and is not a corruption oracle.
    offset = data.find(b"PK\x01\x02")
    while data[offset + 46:offset + 46 + len(info.filename)] != info.filename.encode():
        offset = data.find(b"PK\x01\x02", offset + 4)
        assert offset >= 0
    data[offset + 16] ^= 1
    corrupt = tmp_path / "corrupt.zip"
    corrupt.write_bytes(data)
    with pytest.raises(zipfile.BadZipFile, match="CRC"):
        tool.verify_zip(corrupt, manifest)


def test_insufficient_space_cannot_publish_archive(tool, scene, tmp_path, monkeypatch):
    source, identity, digest = scene
    class Space:
        free = 0
    monkeypatch.setattr(tool.shutil, "disk_usage", lambda _: Space())
    with pytest.raises(ValueError, match="SPACE"):
        tool.capture(source, tmp_path / "diagnostic", tmp_path / "evidence.zip", identity, digest)
    assert not (tmp_path / "evidence.zip").exists()
    receipt = json.loads((tmp_path / "diagnostic/forensic_receipt.json").read_text())
    assert receipt["status"] == "FAILED_PRESERVE_COPY_STOP"


def test_real_cli_uses_receipt_and_never_imports_or_rewrites_source(tool, scene, tmp_path):
    source, identity, digest = scene
    out = tmp_path / "evidence.zip"
    process = subprocess.run([sys.executable, "-I", "-X", "utf8", str(SCRIPT), "--source", str(source),
                              "--workspace", str(tmp_path / "diagnostic"), "--archive", str(out),
                              "--identity", str(identity), "--identity-sha256", digest],
                             capture_output=True, timeout=20)
    assert process.returncode == 0, process.stderr
    assert (source / ".active").read_bytes() == b"keep"
    assert json.loads((tmp_path / "diagnostic/forensic_receipt.json").read_text())["archive_sha256"] == hashlib.sha256(out.read_bytes()).hexdigest()


@pytest.mark.parametrize("original_failure", [True, False])
def test_external_receipt_io_cannot_mask_original_error_or_succeed(tool, scene, tmp_path, monkeypatch, original_failure):
    source, identity, digest = scene
    original_write = Path.write_bytes
    def fail_receipt(path, value):
        if path.name == "forensic_receipt.json":
            raise OSError("deliberate receipt IO failure")
        return original_write(path, value)
    monkeypatch.setattr(Path, "write_bytes", fail_receipt)
    if original_failure:
        original_verify = tool.verify_zip
        def mutate(archive, manifest):
            original_verify(archive, manifest)
            (source / ".active").write_bytes(b"changed")
        monkeypatch.setattr(tool, "verify_zip", mutate)
        with pytest.raises(ValueError, match="SOURCE_CHANGED"):
            tool.capture(source, tmp_path / "diagnostic", tmp_path / "evidence.zip", identity, digest)
    else:
        with pytest.raises(OSError, match="receipt IO"):
            tool.capture(source, tmp_path / "diagnostic", tmp_path / "evidence.zip", identity, digest)
