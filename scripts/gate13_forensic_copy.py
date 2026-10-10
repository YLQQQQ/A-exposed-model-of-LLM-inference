"""Standalone stdlib byte preservation; NOT a writer/retention/Formal gate.

No process query, package import, analysis, database open, cleanup or retry.
Every receipt/index is outside the source. Failed partial archives stay put.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import unicodedata
import zipfile


VERSION = "gate13-forensic-byte-copy/0.1"
CHUNK = 4 * 1024 * 1024
UNKNOWN = "UNKNOWN_STOP_AND_INSPECT_NO_RETRY"


def require(value, reason):
    if not value:
        raise ValueError("FORENSIC_" + reason)


def encoded(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def safe_name(name):
    require(isinstance(name, str) and name and "\\" not in name, "PATH")
    parts = name.removesuffix("/").split("/")
    reserved = {"CON", "PRN", "AUX", "NUL"} | {f"{s}{n}" for s in ("COM", "LPT") for n in range(1, 10)}
    require(all(p not in ("", ".", "..") and not p.endswith((".", " ")) and
                not any(ord(c) < 32 or c in ':<>"|?*' for c in p) and
                p.split(".")[0].upper() not in reserved for p in parts), "PATH")
    return name


def unique_names(names):
    seen = set()
    for name in names:
        safe_name(name)
        key = unicodedata.normalize("NFC", name.removesuffix("/")).casefold()
        require(key not in seen, "DUPLICATE_PATH")
        seen.add(key)


def check_stat(info):
    require(not (getattr(info, "st_file_attributes", 0) & 0x400), "REPARSE_POINT")
    require(not stat.S_ISLNK(getattr(info, "st_mode", 0)), "REPARSE_POINT")


def guarded(path):
    path = Path(os.path.abspath(path))
    for part in reversed((path, *path.parents)):
        if part.exists() or part.is_symlink():
            check_stat(part.lstat())
    return path


def signature(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)


def read_hash(path, sink=None):
    guarded(path)
    before = path.lstat()
    require(stat.S_ISREG(before.st_mode), "NOT_REGULAR_FILE")
    digest, length = hashlib.sha256(), 0
    with path.open("rb") as handle:
        opened = os.fstat(handle.fileno())
        # Windows Python versions can expose different ctime semantics through
        # stat and fstat (creation versus change time). Compare common identity,
        # size and mtime across APIs, then full signatures within each API.
        require(signature(opened)[:4] == signature(before)[:4], "FILE_CHANGED_OPEN")
        while block := handle.read(CHUNK):
            digest.update(block)
            length += len(block)
            if sink is not None:
                sink.write(block)
        require(signature(os.fstat(handle.fileno())) == signature(opened), "FILE_CHANGED_READ")
    require(signature(path.lstat()) == signature(before) and length == before.st_size, "FILE_CHANGED_READ")
    return {"length": length, "sha256": digest.hexdigest(),
            "mtime_ns": before.st_mtime_ns, "ctime_ns": before.st_ctime_ns,
            "device": before.st_dev, "inode": before.st_ino}


def inventory(root):
    root = guarded(root)
    require(root.is_dir(), "SOURCE_DIRECTORY_MISSING")
    files, dirs, empty = [], [], []
    def walk(directory):
        with os.scandir(directory) as entries:
            children = sorted(entries, key=lambda e: e.name)
        if not children:
            empty.append(directory.relative_to(root).as_posix())
        for entry in children:
            path = Path(entry.path)
            info = entry.stat(follow_symlinks=False)
            check_stat(info)
            require(path.resolve().is_relative_to(root), "PATH_OUTSIDE_SOURCE")
            name = safe_name(path.relative_to(root).as_posix())
            if stat.S_ISDIR(info.st_mode):
                dirs.append(name)
                walk(path)
            else:
                require(stat.S_ISREG(info.st_mode), "NOT_REGULAR_FILE")
                files.append(name)
    walk(root)
    unique_names(files + dirs)
    return {"files": sorted(files), "directories": sorted(dirs), "empty_directories": sorted(empty)}


def snapshot(root):
    root = guarded(root)
    listing = inventory(root)
    rows = []
    for number, name in enumerate(listing["files"], 1):
        rows.append({"path": name, **read_hash(root / name)})
        if number % 100 == 0:
            print(f"[forensic] hashed_files={number}/{len(listing['files'])}", flush=True)
    result = {**listing, "files": rows}
    require(inventory(root) == listing, "SOURCE_CHANGED_DURING_FREEZE")
    return result


def assert_snapshot(root, expected):
    require(snapshot(root) == expected, "SOURCE_CHANGED")


def verify_zip(archive, manifest_bytes):
    manifest = json.loads(manifest_bytes)
    rows = manifest["entries"]
    unique_names([r["path"] for r in rows] + ["forensic_manifest.json"])
    expected = {r["path"]: r for r in rows}
    expected["forensic_manifest.json"] = {"length": len(manifest_bytes), "sha256": hashlib.sha256(manifest_bytes).hexdigest()}
    with zipfile.ZipFile(archive) as package:
        infos = package.infolist()
        unique_names([i.filename for i in infos])
        require({i.filename for i in infos} == set(expected), "ZIP_COVERAGE")
        for info in infos:
            require(not (info.flag_bits & 1), "ZIP_ENCRYPTED")
            digest, count = hashlib.sha256(), 0
            with package.open(info) as handle:
                while block := handle.read(CHUNK):
                    digest.update(block)
                    count += len(block)
            # zipfile verifies each member CRC while reading to EOF.
            row = expected[info.filename]
            require(count == info.file_size == row["length"] and digest.hexdigest() == row["sha256"], "ZIP_CONTENT")
        require(package.read("forensic_manifest.json") == manifest_bytes, "ZIP_MANIFEST")


def capture(source, workspace, archive, identity, identity_sha256, quiescence=None, quiescence_sha256=None):
    source, workspace, archive = map(guarded, (source, workspace, archive))
    partial = Path(str(archive) + ".partial")
    require(not workspace.is_relative_to(source) and not archive.is_relative_to(source) and
            not source.is_relative_to(workspace), "OUTPUT_SCOPE")
    require(not workspace.exists() and not archive.exists() and not partial.exists(), "OUTPUT_EXISTS")
    require(archive.parent.is_dir() and workspace.parent.is_dir(), "OUTPUT_PARENT_MISSING")
    # Inputs are loaded once and embedded unchanged; unknown is retained, not overridden.
    assets = {}
    for label, path, wanted in (("instance_receipt.json", identity, identity_sha256),
                                 ("quiescence_original.zip", quiescence, quiescence_sha256)):
        if path is None:
            continue
        path = guarded(path)
        value = path.read_bytes()
        require(hashlib.sha256(value).hexdigest() == str(wanted).lower(), "IDENTITY_HASH" if label.startswith("instance") else "QUIESCENCE_HASH")
        assets["provenance/" + label] = value
    observed = json.loads(assets["provenance/instance_receipt.json"].decode("utf-8-sig"))
    require(observed["role"] == "TARGETED_PROCESS_INSTANCE_READONLY_ONCE" and
            observed["historical_descendant_exit_status"] == UNKNOWN, "IDENTITY_RECEIPT_ROLE")
    assets["provenance/forensic_tool.py"] = Path(__file__).read_bytes()
    workspace.mkdir()
    receipt = {"version": VERSION, "role": "FORENSIC_PRESERVATION_NOT_ACCEPTANCE",
               "status": "FAILED_PRESERVE_COPY_STOP", "error": None,
               "source": str(source), "archive": str(archive),
               "historical_descendant_exit_status": UNKNOWN, "gate13": "BLOCKED",
               "absence_of_writers_proven": False, "source_modified_by_tool": False,
               "started_utc": datetime.now(timezone.utc).isoformat()}
    original_error = None
    try:
        print("[forensic] FREEZE_SOURCE_HASHES START", flush=True)
        frozen = snapshot(source)
        require(frozen["files"], "EMPTY_SOURCE")
        frozen_bytes = encoded(frozen)
        (workspace / "source_before.json").write_bytes(frozen_bytes)
        assets["provenance/source_before.json"] = frozen_bytes
        total = sum(r["length"] for r in frozen["files"])
        # Conservative capacity bound; do not assume a useful compression ratio.
        reserve = 2 * 1024**3 + 8192 * (len(frozen["files"]) + len(frozen["directories"]))
        required = total + sum(len(b) for b in assets.values()) + reserve
        free = shutil.disk_usage(archive.parent).free
        require(free >= required, "INSUFFICIENT_ARCHIVE_SPACE")
        require(shutil.disk_usage(workspace.parent).free >= reserve, "INSUFFICIENT_INDEX_SPACE")
        receipt.update(source_file_count=len(frozen["files"]), source_bytes=total,
                       required_free_bytes=required, free_bytes_observed=free,
                       empty_directories=frozen["empty_directories"])
        print(f"[forensic] source_bytes={total} required_free_bytes={required}; COPY START", flush=True)
        require(inventory(source) == {**frozen, "files": [r["path"] for r in frozen["files"]]}, "SOURCE_CHANGED_BEFORE_COPY")
        rows = []
        with zipfile.ZipFile(partial, "x", compression=zipfile.ZIP_DEFLATED, compresslevel=1, allowZip64=True) as package:
            for index, row in enumerate(frozen["files"], 1):
                name = "source/" + row["path"]
                with package.open(name, "w", force_zip64=True) as sink:
                    actual = read_hash(source / row["path"], sink)
                require(actual == {k: v for k, v in row.items() if k != "path"}, "SOURCE_CHANGED_COPY")
                rows.append({"path": name, "length": row["length"], "sha256": row["sha256"]})
                if index % 50 == 0 or index == len(frozen["files"]):
                    print(f"[forensic] copied_files={index}/{len(frozen['files'])}", flush=True)
            for name in frozen["directories"]:
                name = "source/" + name + "/"
                package.writestr(name, b"")
                rows.append({"path": name, "length": 0, "sha256": hashlib.sha256(b"").hexdigest()})
            print("[forensic] POST_COPY_SOURCE_HASHES START", flush=True)
            after = snapshot(source)
            (workspace / "source_after_copy.json").write_bytes(encoded(after))
            require(after == frozen, "SOURCE_CHANGED_AFTER_COPY")
            assets["provenance/copy_checkpoint.json"] = encoded({
                "status": "SOURCE_COPY_CHECKED_FINAL_ZIP_VERIFICATION_PENDING",
                "source_before_sha256": hashlib.sha256(frozen_bytes).hexdigest(),
                "source_after_copy_matches": True, "historical_descendant_exit_status": UNKNOWN,
                "absence_of_writers_proven": False, "gate13": "BLOCKED"})
            for name, value in assets.items():
                package.writestr(name, value)
                rows.append({"path": name, "length": len(value), "sha256": hashlib.sha256(value).hexdigest()})
            unique_names([r["path"] for r in rows])
            manifest_bytes = encoded({"version": VERSION, "role": receipt["role"],
                                      "entries": rows, "manifest_self_hash_excluded": True,
                                      "empty_directories": frozen["empty_directories"],
                                      "historical_descendant_exit_status": UNKNOWN,
                                      "absence_of_writers_proven": False, "gate13": "BLOCKED"})
            (workspace / "forensic_manifest.json").write_bytes(manifest_bytes)
            package.writestr("forensic_manifest.json", manifest_bytes)
        print("[forensic] ZIP_CRC_FULL_COVERAGE_HASHES START", flush=True)
        verify_zip(partial, manifest_bytes)
        archive_hash = read_hash(partial)
        print("[forensic] POST_ARCHIVE_SOURCE_HASHES START", flush=True)
        final = snapshot(source)
        (workspace / "source_after_archive.json").write_bytes(encoded(final))
        require(final == frozen, "SOURCE_CHANGED_AFTER_ARCHIVE")
        require(not archive.exists(), "OUTPUT_EXISTS")
        # Link fails if the destination exists; unlike replace(), never overwrites.
        os.link(partial, archive)
        partial.unlink()  # Only our new verified partial name, never anything in source.
        receipt.update(status="FORENSIC_BYTE_COPY_VERIFIED_NOT_ACCEPTANCE",
                       archive_length=archive_hash["length"], archive_sha256=archive_hash["sha256"],
                       manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
                       zip_member_count=len(rows) + 1)
    except Exception as error:
        original_error = error
        receipt["error"] = f"{type(error).__name__}: {error}"
        raise
    finally:
        receipt["ended_utc"] = datetime.now(timezone.utc).isoformat()
        try:
            (workspace / "forensic_receipt.json").write_bytes(encoded(receipt))
            print(json.dumps(receipt, ensure_ascii=False), flush=True)
        except Exception as persistence_error:
            if original_error is None:
                raise  # Successful copy cannot silently succeed without its receipt.
            original_error.add_note(f"External receipt/output failed: {persistence_error!r}")
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("source", "workspace", "archive", "identity", "identity-sha256"):
        parser.add_argument("--" + name, required=True)
    parser.add_argument("--quiescence")
    parser.add_argument("--quiescence-sha256")
    args = parser.parse_args()
    capture(Path(args.source), Path(args.workspace), Path(args.archive), Path(args.identity),
            args.identity_sha256, args.quiescence, args.quiescence_sha256)


if __name__ == "__main__":
    main()
