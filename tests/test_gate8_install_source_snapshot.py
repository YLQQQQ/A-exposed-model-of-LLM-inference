"""Read-only source snapshot: file fixtures, never installed GPU packages."""

import base64
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/gate8_install_source_snapshot.py"


def tool():
    assert SCRIPT.is_file(), "bounded, non-importing source snapshot entry is missing"
    spec = importlib.util.spec_from_file_location("install_snapshot_under_test", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_site(root):
    site = root / "site packages"
    # Importing these modules would execute attacker-controlled code. They are DATA.
    source = b'raise RuntimeError("PACKAGE_MUST_NOT_BE_IMPORTED")\n'
    paths = {
        "torch": ["torch/version.py", "torch/cuda/__init__.py", "torch/cuda/streams.py",
                  "torch/include/c10/cuda/CUDAFunctions.h", "torch/include/c10/cuda/CUDAStream.h",
                  "torch/lib/c10_cuda.dll", "torch/lib/torch_cuda.dll"],
        "transformers": ["transformers/modeling_utils.py", "transformers/core_model_loading.py",
                         "transformers/integrations/accelerate.py"],
    }
    for name, version in [("torch", "2.6.0+cu124"), ("transformers", "5.17.0")]:
        info = site / f"{name}-{version}.dist-info"
        info.mkdir(parents=True)
        (info / "METADATA").write_text(f"Name: {name}\nVersion: {version}\n", encoding="utf-8")
        (info / "WHEEL").write_text("Wheel-Version: 1.0\nTag: cp311-cp311-win_amd64\n", encoding="utf-8")
        rows = []
        for relative in paths[name]:
            data = source
            if relative == "torch/version.py":
                data = b"__version__ = '2.6.0+cu124'\ncuda = '12.4'\ngit_version = '" + b"a" * 40 + b"'\n"
            if relative.endswith(".dll"):
                data = b"FAKE_DLL_NOT_LOADED"
            path = site / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
            rows.append(f"{relative},sha256={digest},{len(data)}")
        (info / "RECORD").write_text("\n".join(rows), encoding="utf-8")
        (site / name / "__init__.py").write_bytes(source)
    (site / "private.env").write_text("DO_NOT_COLLECT", encoding="utf-8")
    return site


def test_snapshot_copies_only_selected_sources_and_hashes_binaries(tmp_path):
    site = make_site(tmp_path)
    before = {p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()}
    out = tmp_path / "new diagnostic"
    result = tool().snapshot(site, out)
    assert result["status"] == "SNAPSHOT_COMPLETE_NOT_QUALIFICATION"
    assert result["default_stream_mode"] == "UNKNOWN"
    assert result["worker_trace_ownership"] == "UNKNOWN"
    assert result["torch_source_literals"]["cuda"] == "12.4"
    assert len(result["files"]) == 10
    assert all(x["record_match"] is True for x in result["files"])
    assert len(list((out / "selected_sources").rglob("*.py"))) == 6
    assert (out / "selected_sources/transformers/integrations/accelerate.py").read_bytes() == (
        site / "transformers/integrations/accelerate.py").read_bytes()
    assert not list(out.rglob("*.dll"))
    assert not list(out.rglob("*.env"))
    assert before == {p.relative_to(site): p.read_bytes() for p in site.rglob("*") if p.is_file()}
    manifest = json.loads((out / "artifact_manifest.json").read_text())
    actual = {p.relative_to(out).as_posix() for p in out.rglob("*") if p.is_file()}
    assert set(manifest) == actual - {"artifact_manifest.json"}
    for relative, item in manifest.items():
        data = (out / relative).read_bytes()
        assert item == {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


@pytest.mark.parametrize("change,issue", [
    ("version", "PACKAGE_VERSION_MISMATCH"),
    ("missing", "SELECTED_FILE_MISSING"),
    ("record", "RECORD_HASH_MISMATCH"),
    ("duplicate", "PACKAGE_NOT_UNIQUE"),
    ("literal", "TORCH_LITERAL_MISMATCH"),
])
def test_incomplete_or_conflicting_install_does_not_claim_source_match(tmp_path, change, issue):
    site = make_site(tmp_path)
    if change == "version":
        (site / "torch-2.6.0+cu124.dist-info/METADATA").write_text("Name: torch\nVersion: 9.0\n")
    elif change == "missing":
        (site / "transformers/core_model_loading.py").unlink()
    elif change == "record":
        (site / "torch/cuda/streams.py").write_bytes(b"changed")
    elif change == "duplicate":
        dup = site / "torch-other.dist-info"
        dup.mkdir()
        (dup / "METADATA").write_text("Name: torch\nVersion: 2.6.0+cu124\n")
    else:
        (site / "torch/version.py").write_text("__version__='2.6.0+cu124'\ncuda='13.0'\n")
    result = tool().snapshot(site, tmp_path / "out")
    assert result["status"] == "SNAPSHOT_INCOMPLETE"
    assert any(x["code"] == issue for x in result["issues"])
    assert result["default_stream_mode"] == "UNKNOWN"


def test_existing_output_cannot_be_reused(tmp_path):
    site = make_site(tmp_path)
    out = tmp_path / "existing"
    out.mkdir()
    with pytest.raises(FileExistsError):
        tool().snapshot(site, out)
    assert not list(out.iterdir())


def test_snapshot_cannot_write_into_input_site(tmp_path):
    site = make_site(tmp_path)
    with pytest.raises(ValueError, match="OUTPUT_OVERLAPS_INPUT"):
        tool().snapshot(site, site / "new output")
    assert not (site / "new output").exists()


def test_nonliteral_version_source_is_not_executed(tmp_path):
    site = make_site(tmp_path)
    (site / "torch/version.py").write_text("raise RuntimeError('NEVER_EXECUTE')\ncuda = str(12.4)\n")
    result = tool().snapshot(site, tmp_path / "out")
    assert result["status"] == "SNAPSHOT_INCOMPLETE"
    assert result["torch_source_literals"]["cuda"] is None


def test_cli_requires_isolated_no_site_startup_and_fixed_venv(tmp_path):
    assert SCRIPT.is_file(), "source snapshot CLI missing"
    for flags, reason in [([], "REQUIRE_ISOLATED_NO_SITE"), (["-I", "-S"], "REQUIRE_REPO_VENV")]:
        run = subprocess.run([sys.executable, *flags, str(SCRIPT), "--repo", str(tmp_path),
                              "--output", str(tmp_path / "out")], capture_output=True, text=True)
        assert run.returncode != 0
        assert reason in run.stdout + run.stderr
        assert not (tmp_path / "out").exists()


@pytest.mark.parametrize('profile',['installation','qwen-request'])
def test_isolated_snapshot_never_imports_target_packages_or_native_loaders(tmp_path,profile):
    site = make_site(tmp_path) if profile=='installation' else request_site(tmp_path)
    # A fresh -I -S process proves no site/.pth or installed-package side effects.
    code = """
import builtins, runpy, sys
original = builtins.__import__
def guarded(name, *args, **kwargs):
    if name.split('.')[0] in {'torch', 'transformers'}:
        raise AssertionError('FORBIDDEN_IMPORT:' + name)
    return original(name, *args, **kwargs)
def audit(event, args):
    if event in {'ctypes.dlopen', 'subprocess.Popen', 'socket.connect', 'socket.bind', 'socket.getaddrinfo'}:
        raise AssertionError('FORBIDDEN_ACTION:' + event)
builtins.__import__ = guarded
sys.addaudithook(audit)
api = runpy.run_path(sys.argv[1])
report = api['snapshot'](sys.argv[2], sys.argv[3], profile=sys.argv[4])
assert report['status'] == 'SNAPSHOT_COMPLETE_NOT_QUALIFICATION'
"""
    run = subprocess.run([sys.executable, "-I", "-S", "-c", code, str(SCRIPT),
                          str(site), str(tmp_path / "out"),profile], capture_output=True, text=True)
    assert run.returncode == 0, run.stdout + run.stderr


def test_selected_record_cannot_silently_duplicate_identity(tmp_path):
    site = make_site(tmp_path)
    record = site / "torch-2.6.0+cu124.dist-info/RECORD"
    with record.open("a") as handle:
        handle.write("\ntorch/version.py,sha256=conflict,10\n")
    result = tool().snapshot(site, tmp_path / "out")
    assert result["status"] == "SNAPSHOT_INCOMPLETE"
    assert any(x["code"] == "RECORD_AMBIGUOUS" for x in result["issues"])


@pytest.mark.parametrize("extra", ["Version: 9.0\n", "Name: other\n", "Name: torch\n"])
def test_duplicate_metadata_identity_headers_fail_closed(tmp_path, extra):
    site = make_site(tmp_path)
    metadata = site / "torch-2.6.0+cu124.dist-info/METADATA"
    with metadata.open("a") as handle:
        handle.write(extra)
    result = tool().snapshot(site, tmp_path / "out")
    assert result["status"] == "SNAPSHOT_INCOMPLETE"
    assert any(x["code"] == "PACKAGE_METADATA_AMBIGUOUS" for x in result["issues"])


REQUEST_FILES = (
    'transformers/models/qwen2/modeling_qwen2.py',
    'transformers/models/qwen2/configuration_qwen2.py',
    'transformers/masking_utils.py', 'transformers/cache_utils.py',
    'transformers/integrations/sdpa_attention.py',
)


def request_site(tmp_path):
    site = make_site(tmp_path)
    record = site/'transformers-5.17.0.dist-info/RECORD'
    for relative in REQUEST_FILES:
        path=site/relative
        path.parent.mkdir(parents=True,exist_ok=True)
        data=b"raise RuntimeError('MUST_NEVER_IMPORT_REQUEST_SOURCE')\n"
        path.write_bytes(data)
        digest=base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        with record.open('a') as out:
            out.write(f'\n{relative},sha256={digest},{len(data)}')
    return site


def test_request_profile_is_narrow_and_never_loads_binary(tmp_path,monkeypatch):
    module=tool()
    import inspect
    assert 'profile' in inspect.signature(module.snapshot).parameters, 'Need explicit bounded request-only selection'
    site=request_site(tmp_path)
    # Make previously selected DLLs unavailable: the new profile must not touch them.
    for path in (site/'torch/lib').glob('*.dll'):
        path.unlink()
    result=module.snapshot(site,tmp_path/'out',profile='qwen-request')
    assert result['status']=='SNAPSHOT_COMPLETE_NOT_QUALIFICATION'
    assert result['schema_version']=='gate8-install-source-snapshot/0.2.0'
    assert result['selection_profile']=='qwen-request/0.1.0'
    assert {r['relative_path'] for r in result['files']}==set(REQUEST_FILES)|{'torch/version.py','transformers/modeling_utils.py'}
    assert result['actual_attention_backend']=='UNKNOWN_NOT_EXECUTED'
    assert result['default_stream_mode']=='UNKNOWN'
    assert result['qualification']=='NOT_ASSESSED'


@pytest.mark.parametrize('damage',['missing','changed','version'])
def test_request_profile_stops_on_missing_or_changed_source(tmp_path,damage):
    module=tool(); site=request_site(tmp_path)
    path=site/REQUEST_FILES[0]
    if damage=='missing': path.unlink()
    elif damage=='changed': path.write_bytes(b'changed')
    else: (site/'transformers-5.17.0.dist-info/METADATA').write_text('Name: transformers\nVersion: unknown\n')
    result=module.snapshot(site,tmp_path/'out',profile='qwen-request')
    assert result['status']=='SNAPSHOT_INCOMPLETE'
    assert result['issues']


def test_unknown_selection_profile_refuses_before_writing(tmp_path):
    with pytest.raises(ValueError,match='UNKNOWN_SELECTION_PROFILE'):
        tool().snapshot(make_site(tmp_path),tmp_path/'out',profile='all-files')
    assert not (tmp_path/'out').exists()
