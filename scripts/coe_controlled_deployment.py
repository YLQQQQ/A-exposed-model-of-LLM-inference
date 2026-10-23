"""Fixed-c8 deployment repair only; the reviewed CUDA/S/COE code is unchanged.

The new index binds an unchanged authorization through an explicit compatibility
record. This is not a new approval, new GPU budget, or a measurement version.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import zipfile

EXECUTION = 'c8f3dad152659044691f9ff328498c7a127815ea'
OLD_INDEX = '238d31c40ee74cab158eb5ad8de67d753da6b4aa3878c756c7ded467633eaa1a'
AUTH_SHA = '39b46e3189e93b55f1bb21e895d38bbc0ae535e77e45633ee4584ef69ca5c69e'
ATTEMPT = 'coe_controlled_c8f3dad_repair2'
REPAIR1_SHA = '88daa7e8e2204375af22bf411272b4ba1486b44c02848a7e638e12a1a75484c6'
GIT_STATE_SHA = '6deed68b01d03f7cbc73719a89664a043de05baf4c320712c51009dbce956201'
BRIDGE = dict(schema_version='coe-controlled-authorization-compatibility/0.1.1',
    original_authorization_sha256=AUTH_SHA, approved_delivery_index_sha256=OLD_INDEX,
    execution_commit=EXECUTION, permission_expansion=False,
    scope='ONE_CONTROLLED_NO_MODEL_NO_NSIGHT_120S',
    changes=['fixed_blob_binary_materialization', 'content_verified_source_only_git_status',
             'new_attempt_after_sealed_unbuilt_clean_gate_failure'],
    authority='ORIGINAL_DIRECT_USER_APPROVAL_PLUS_EXPLICIT_LOCAL_DEPLOYMENT_REPAIR_REQUEST',
    not_a_new_approval=True)


def require(ok, reason):
    if not ok:
        raise ValueError('CONTROLLED_REPAIR_' + reason)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    with Path(path).open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2)


def no_reparse(path):
    for p in (Path(path), *Path(path).parents):
        require(not p.is_symlink() and not (p.exists() and
            getattr(p.lstat(), 'st_file_attributes', 0) & 0x400), 'REPARSE:' + str(p))


def relative(root, name):
    require(type(name) is str and name and '\\' not in name and ':' not in name,
            'PATH')
    rel = Path(name)
    require(not rel.is_absolute() and '..' not in rel.parts and rel.as_posix() == name,
            'PATH')
    target = Path(root) / rel
    no_reparse(target)
    require(target.resolve().is_relative_to(Path(root).resolve()), 'PATH')
    return target


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def git_bytes(git, repo, *args):
    # Binary PIPE: no decoding/re-encoding of Git blob stdout, no PS pipeline.
    result = subprocess.run([str(git), '-C', str(repo), '-c', 'core.fsmonitor=false', *args],
                            capture_output=True, timeout=30,
                            env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
    require(result.returncode == 0, 'GIT_EXIT:' + str(result.returncode) + ':' + args[0]
            + ':stderr_bytes=' + repr(result.stderr))
    return result.stdout


def check_deployed_tree(git, repo, commit, rows, evidence):
    """A status flag is not proof of a diff; no unknown dirty path is allowed."""
    repo, evidence = Path(repo), Path(evidence)
    evidence.mkdir(parents=True, exist_ok=False)
    def query(label, *args, diff=False):
        argv = [str(git), '-C', str(repo), '-c', 'core.fsmonitor=false', *args]
        try:
            result = subprocess.run(argv, capture_output=True, timeout=30,
                                    env=dict(os.environ, GIT_OPTIONAL_LOCKS='0'))
        except subprocess.TimeoutExpired:
            write(evidence / (label + '.query.json'), dict(argv=argv, status='TIMEOUT_UNKNOWN_STOP'))
            raise
        for suffix, data in (('stdout', result.stdout), ('stderr', result.stderr)):
            with (evidence / (label + '.' + suffix)).open('xb') as stream:
                stream.write(data)
        write(evidence / (label + '.query.json'), dict(argv=argv, status='EXITED',
            exit_code=result.returncode, optional_git_locks=False))
        require(result.returncode in ((0, 1) if diff else (0,)), 'GIT_QUERY_EXIT:' + label)
        return result
    require(query('head', 'rev-parse', 'HEAD').stdout.decode('ascii').strip() == commit, 'CHECKOUT_COMMIT')
    status = query('status', 'status', '--porcelain=v1', '-z', '--untracked-files=all').stdout
    staged = query('staged', 'diff', '--cached', '--raw', '-z', '--exit-code',
                   '--no-ext-diff', '--no-textconv', diff=True)
    require(staged.returncode == 0 and staged.stdout == b'', 'STAGED_CHANGE')
    content = query('content', 'diff', '--raw', '-z', '--exit-code',
                    '--no-ext-diff', '--no-textconv', diff=True)
    names = [r['path'] for r in rows]
    require(len(names) == len({n.casefold() for n in names}), 'DUPLICATE_PATH')
    tree = query('head_tree', 'ls-tree', '-z', commit, '--', *names).stdout
    index = query('index', 'ls-files', '--stage', '-z', '--', *names).stdout
    def entries(raw, is_index):
        result = {}
        require(not raw or raw.endswith(b'\0'), 'GIT_ENTRY_ENCODING')
        for entry in raw.split(b'\0'):
            if not entry:
                continue
            fields, path = entry.split(b'\t', 1)
            mode, middle, last = fields.split(b' ')
            require(mode in (b'100644', b'100755'), 'NONREGULAR_GIT_BLOB')
            if is_index:
                require(last == b'0', 'INDEX_STAGE')
                oid = middle
            else:
                require(middle == b'blob', 'NONREGULAR_GIT_BLOB')
                oid = last
            name = path.decode('utf8')
            require(name not in result, 'DUPLICATE_PATH')
            result[name] = (mode.decode('ascii'), oid.decode('ascii'))
        return result
    head_entries, index_entries = entries(tree, False), entries(index, True)
    require(set(head_entries) == set(names) and head_entries == index_entries, 'INDEX_HEAD_CONFLICT')
    for row in rows:
        path = relative(repo, row['path'])
        blob = git_bytes(git, repo, 'cat-file', 'blob', commit + ':' + row['path'])
        require(len(blob) == row['bytes'] and digest(blob) == row['sha256'], 'BLOB_MANIFEST_CONFLICT')
        require(path.is_file() and path.read_bytes() == blob, 'CONTENT_IDENTITY:' + row['path'])
    require(content.returncode == 0 and content.stdout == b'', 'CONTENT_DIFF')
    require(not status or status.endswith(b'\0'), 'GIT_STATUS_ENCODING')
    allowed = set(names)
    status_only = []
    for entry in status.split(b'\0'):
        if entry:
            name = entry[3:].decode('utf8')
            require(entry[:3] == b' M ' and name in allowed, 'UNRELATED_WORKTREE_CHANGE')
            require(name not in status_only, 'DUPLICATE_PATH')
            status_only.append(name)
    report = dict(schema_version='coe-content-verified-worktree/0.1.0', execution_commit=commit,
        content_clean=True, git_status_empty=not status, verified_status_only_paths=sorted(status_only),
        staged_diff_empty=True, content_diff_empty=True, index_matches_HEAD=True,
        frozen_source_bytes_exact=True, staged_content_and_modes_changed=False,
        git_configuration_modified=False, index_stat_cache_preservation='NOT_CLAIMED',
        cause_of_status_content_disagreement='NOT_INFERRED')
    write(evidence / 'check.json', report)
    return report


def materialize_sources(git, repo, commit, rows, evidence):
    repo, evidence = Path(repo), Path(evidence)
    require(git_bytes(git, repo, 'rev-parse', 'HEAD').decode('ascii').strip() == commit,
            'CHECKOUT_COMMIT')
    require(git_bytes(git, repo, 'diff', '--cached', '--name-only') == b'', 'STAGED_CHANGE')
    require(type(rows) is list and rows, 'EMPTY_INDEX')
    seen, prepared = set(), []
    # Preflight EVERY source before the first write; never normalize arbitrary data.
    for row in rows:
        name = row['path']
        path = relative(repo, name)
        require(name.casefold() not in seen, 'DUPLICATE_PATH')
        seen.add(name.casefold())
        require(path.is_file(), 'MISSING:' + name)
        mode = git_bytes(git, repo, 'ls-tree', commit, '--', name)
        require(mode.startswith((b'100644 blob ', b'100755 blob ')), 'NONREGULAR_GIT_BLOB')
        blob = git_bytes(git, repo, 'cat-file', 'blob', commit + ':' + name)
        require(len(blob) == row['bytes'] and digest(blob) == row['sha256'],
                'BLOB_MANIFEST_CONFLICT:' + name)
        before = path.read_bytes()
        exact = before == blob
        known_eol = b'\r' not in blob and b'\n' in blob and before == blob.replace(b'\n', b'\r\n')
        require(exact or known_eol, 'CONTENT_NOT_PROVEN_EOL:' + name)
        prepared.append((row, path, blob, before, not exact))
    status = git_bytes(git, repo, 'status', '--porcelain=v1', '-z', '--untracked-files=all')
    for entry in status.split(b'\0'):
        if entry:
            require(entry[:3] == b' M ' and entry[3:].decode('utf8').casefold() in seen,
                    'UNRELATED_WORKTREE_CHANGE')
    evidence.mkdir(parents=True, exist_ok=False)
    write(evidence / 'preflight.json', dict(execution_commit=commit, files=[dict(
        path=r['path'], before_bytes=len(before), before_sha256=digest(before),
        expected_bytes=r['bytes'], expected_sha256=r['sha256'], rewrite=changed)
        for r, path, blob, before, changed in prepared]))
    facts = []
    for row, path, blob, before, changed in prepared:
        # Recheck against concurrent edits immediately before any replacement.
        no_reparse(path)
        require(path.read_bytes() == before, 'SOURCE_CHANGED_DURING_REPAIR:' + row['path'])
        if changed:
            backup = relative(evidence / 'source_before', row['path'])
            backup.parent.mkdir(parents=True, exist_ok=True)
            with backup.open('xb') as stream:
                stream.write(before)
            with path.open('wb') as stream:
                stream.write(blob)
                stream.flush()
                os.fsync(stream.fileno())
        require(path.read_bytes() == blob, 'POST_WRITE_IDENTITY:' + row['path'])
        facts.append(dict(path=row['path'], before_bytes=len(before),
            before_sha256=digest(before), after_bytes=len(blob), after_sha256=digest(blob),
            rewritten=changed, evidence='EXACT_LF_TO_CRLF_EXPANSION' if changed else 'EXACT_BLOB'))
    check_deployed_tree(git, repo, commit, rows, evidence / 'git_after_write')
    report = dict(schema_version='coe-fixed-blob-materialization/0.1.0',
                  execution_commit=commit, files=facts, global_git_config_modified=False)
    write(evidence / 'materialization.json', report)
    return report


def snapshot(root):
    root = Path(root)
    no_reparse(root)
    rows = []
    for path in sorted(root.rglob('*')):
        no_reparse(path)
        if path.is_file():
            data = path.read_bytes()
            rows.append(dict(path=path.relative_to(root).as_posix(), bytes=len(data), sha256=digest(data)))
    return rows


def inspect_previous(root, source_names, approval):
    root = Path(root)
    no_reparse(root)
    receipt_path = root / 'prepare/receipt.json'
    no_reparse(receipt_path)
    require(receipt_path.is_file(), 'PREVIOUS_RECEIPT_MISSING')
    value = read(receipt_path)
    required = dict(schema_version='coe-controlled-delivery-receipt/0.1.0', action='prepare',
        status='BLOCKED', execution_commit=EXECUTION, analysis_commit=EXECUTION,
        native_collector_commit='6c744bf52daff3fc54571e264a0c34e3207aa1df',
        delivery_index_sha256=OLD_INDEX, authorization_sha256=AUTH_SHA,
        authorization_reference=approval['approval_reference'], program=None,
        run_config_sha256=None, build_receipt_sha256=None, automatic_retry=False)
    require(all(key in value and value[key] == want for key, want in required.items()),
            'PREVIOUS_RECEIPT_BINDING')
    errors = {'ValueError:CONTROLLED_DELIVERY_FILE_IDENTITY:' + name for name in source_names}
    errors |= {'ValueError:COE_CONTROLLED_SOURCE_HASH:' + name for name in source_names}
    require(value.get('error') in errors, 'PREVIOUS_NOT_SOURCE_ONLY_FAILURE')
    require(not any((root / p).exists() for p in
        ('once', 'prepare/build', 'prepare/run_config.json')), 'PREVIOUS_ALREADY_BUILT_OR_EXECUTED')
    rows = snapshot(root)
    for row in rows:
        require(not Path(row['path']).name.endswith('.active'), 'PREVIOUS_WRITER_NOT_CLOSED')
        if row['path'].endswith('.process.json'):
            process = read(root / row['path'])
            require(process.get('status') == 'EXITED' and type(process.get('exit_code')) is int
                and process['exit_code'] == 0 and process.get('timed_out') is False
                and process.get('descendant_exit_status') != 'UNKNOWN_STOP_AND_INSPECT_NO_RETRY',
                'PREVIOUS_WRITER_NOT_CLOSED')
    return dict(receipt_sha256=digest(receipt_path.read_bytes()), files=rows,
                original_status='BLOCKED', original_unchanged=True)


def verified_evidence_archive(path, expected_size, expected_sha, manifest_name, manifest_sha):
    path = Path(path)
    no_reparse(path)
    require(path.is_file() and path.stat().st_size == expected_size
        and digest(path.read_bytes()) == expected_sha, 'SEALED_EVIDENCE_ARCHIVE')
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        require(len(names) == len({n.casefold() for n in names}) and z.testzip() is None, 'EVIDENCE_CRC_PATHS')
        for name in names:
            rel = Path(name)
            require(not rel.is_absolute() and '..' not in rel.parts and ':' not in name
                    and '\\' not in name and rel.as_posix() == name, 'EVIDENCE_CRC_PATHS')
        require(digest(z.read(manifest_name)) == manifest_sha, 'EVIDENCE_MANIFEST')
        rows = json.loads(z.read(manifest_name))['files']
        require(len(rows) == len({r['path'].casefold() for r in rows})
            and {r['path'] for r in rows} | {manifest_name} == set(names), 'EVIDENCE_COVERAGE')
        data = {name: z.read(name) for name in names}
        for row in rows:
            value = data[row['path']]
            require(len(value) == row['bytes'] and digest(value) == row['sha256'], 'EVIDENCE_MEMBER')
    return data


def inspect_repair1(transfer, package, original_root):
    data = verified_evidence_archive(Path(package) / 'evidence/repair1_once.zip', 24761, REPAIR1_SHA,
        'artifact_manifest.json', 'ade6ac4642c9c36931face65da1303767a704c8964cf85e44ee2d6068e6b62d0')
    root = Path(transfer) / 'coe_controlled_c8f3dad_repair1'
    require(not any((root / p).exists() for p in ('once', 'prepare/build', 'prepare/run_config.json')),
            'PREVIOUS_ALREADY_BUILT_OR_EXECUTED')
    expected = sorted([dict(path=name, bytes=len(value), sha256=digest(value)) for name, value in data.items()],
                      key=lambda row: row['path'])
    observed = sorted(snapshot(root), key=lambda row: row['path'])
    require(observed == expected, 'REPAIR1_EVIDENCE_CHANGED')
    receipt = json.loads(data['prepare/receipt.json'])
    require(receipt['status'] == 'BLOCKED' and receipt['action'] == 'prepare'
        and receipt['error'] == 'ValueError:CONTROLLED_REPAIR_WORKTREE_NOT_CLEAN_AFTER_REPAIR'
        and receipt['execution_commit'] == receipt['analysis_commit'] == EXECUTION
        and receipt['authorization_sha256'] == AUTH_SHA and receipt['program'] is None
        and receipt['run_config_sha256'] is None and receipt['build_receipt_sha256'] is None
        and receipt['previous_evidence_unchanged'] is True, 'REPAIR1_RECEIPT_BINDING')
    require(digest((Path(original_root) / 'prepare/receipt.json').read_bytes())
            == receipt['previous_receipt_sha256'], 'PREVIOUS_RECEIPT_BINDING')
    return dict(status='BLOCKED', built_or_executed=False, archive_sha256=REPAIR1_SHA,
                receipt_sha256=digest(data['prepare/receipt.json']), files=observed)


def verify_package(package, index_sha, action):
    package = Path(package)
    index_path = package / 'file_index.json'
    require(digest(index_path.read_bytes()) == index_sha, 'DELIVERY_INDEX_HASH')
    index = read(index_path)
    require(index.get('schema_version') == 'coe-controlled-repair-index/0.1.1'
        and re.fullmatch('[0-9a-f]{40}', index.get('control_commit', '')) is not None,
        'INDEX_VERSION')
    names = set()
    for row in index['files']:
        path = relative(package, row['path'])
        require(row['path'].casefold() not in names, 'DUPLICATE_PATH')
        names.add(row['path'].casefold())
        require(path.is_file() and path.stat().st_size == row['bytes']
            and digest(path.read_bytes()) == row['sha256'], 'FILE_IDENTITY:' + row['path'])
    actual = {p.relative_to(package).as_posix().casefold() for p in package.rglob('*') if p.is_file()}
    require(actual == names | {'file_index.json'}, 'DELIVERY_COVERAGE')
    original = package / 'original'
    require(digest((original / 'file_index.json').read_bytes()) == OLD_INDEX, 'ORIGINAL_INDEX')
    original_index = read(original / 'file_index.json')
    entry = [r for r in original_index['files'] if r['path'] == 'controlled_delivery.py']
    require(len(entry) == 1 and (original / entry[0]['path']).stat().st_size == entry[0]['bytes']
        and digest((original / entry[0]['path']).read_bytes()) == entry[0]['sha256'], 'ORIGINAL_BOOTSTRAP')
    legacy = load(original / 'controlled_delivery.py', 'reviewed_controlled_delivery')
    legacy.verify_rows(original, original_index['files'])
    require(read(package / 'authorization_compatibility.json') == BRIDGE, 'AUTHORIZATION_COMPATIBILITY')
    auth_path = package / 'authorization.json'
    require(digest(auth_path.read_bytes()) == AUTH_SHA, 'ORIGINAL_AUTHORIZATION_CHANGED')
    approval = read(auth_path)
    reference = legacy.authorize(approval, action, OLD_INDEX)
    cfg = legacy.read(original / 'delivery.json')
    require(cfg['execution_commit'] == EXECUTION and cfg['schema_version'] == 'coe-controlled-handoff/0.1.0'
        and cfg['budget'] == dict(processes=1, sessions=1, models=0, nsight_profiles=0, hard_seconds=120),
        'ORIGINAL_CONTRACT')
    legacy.checked_references(original, cfg)
    verified_evidence_archive(package / 'evidence/git_state_once.zip', 8059, GIT_STATE_SHA,
        'manifest.json', '046cc54b54af25f292493c67f4b1a2cf84f16d7d1d8f5a37fe89818ccd3ef464')
    return legacy, cfg, approval, reference, index['control_commit']


def target_environment():
    require(os.name == 'nt' and sys.flags.isolated and sys.flags.no_site
        and list(sys.version_info[:3]) == [3, 11, 16], 'TARGET_ISOLATED_PYTHON')


def attempt_configuration(original):
    cfg = dict(original)
    transfer = Path(cfg['transfer_root'])
    cfg.update(output_root=str(transfer / ATTEMPT),
               return_zip=str(transfer / (ATTEMPT + '_once.zip')),
               run_id='coe-controlled-c8f3dad-repair2-once')
    return cfg


def build_program(legacy, cfg, out, binding):
    builder = legacy.load(Path(cfg['code_root']) / 'scripts/build_coe_cupti_controlled.py',
                          'controlled_existing_build')
    shutil.copyfile(Path(cfg['code_root']) / 'configs/coe_cupti_controlled_v0_1.json',
                    out / 'construction_plan.json')
    built = builder.build(cfg['build'], out / 'build')
    require(built['collector_rebuilt'] is False and built['program_executed'] is False
        and built['CUDA_initialized'] is False and built['local_unsupported_host_compiler'] is False,
        'BUILD_SCOPE')
    program = built['program']
    config = dict(schema_version='coe-cupti-controlled-run/0.1.0', role='Engineering',
        plan_sha256=next(r['sha256'] for r in cfg['sources'] if r['path']=='configs/coe_cupti_controlled_v0_1.json'),
        budget=cfg['budget'], run_id=cfg['run_id'], program=program['path'], program_sha256=program['sha256'],
        runtime=cfg['runtime']['path'], gpu_uuid=cfg['gpu_uuid'], gpu_pci=cfg['gpu_cuda_pci'],
        cuda_visible_devices=cfg['gpu_uuid'], source_sha256=binding['source_sha256'],
        session=dict(session_id=cfg['run_id'], client=cfg['client']['path'], client_sha256=cfg['client']['sha256'],
            cupti=cfg['cupti']['path'], cupti_sha256=cfg['cupti']['sha256'],
            activity_policy_version='cupti-api22-activity-policy/0.2.0'))
    write(out / 'run_config.json', config)
    return program


def run_stage(package, index_sha, action):
    package = Path(package)
    legacy, original, approval, reference, control = verify_package(package, index_sha, action)
    if action == 'verify':
        print(json.dumps(dict(status='PACKAGE_VERIFIED_NO_TARGET_ACCESS', control_commit=control,
                              execution_commit=EXECUTION, original_authorization_sha256=AUTH_SHA)))
        return 0
    target_environment()
    cfg = attempt_configuration(original)
    root, old = Path(cfg['output_root']), Path(original['output_root'])
    require(root != old and root.resolve().is_relative_to(Path(cfg['transfer_root']).resolve()), 'NEW_TRANSFER_ROOT')
    no_reparse(root)
    out = root / ('prepare' if action == 'prepare' else 'once')
    require(not out.exists(), 'NO_OVERWRITE_RESUME_RETRY')
    require(not root.exists() if action == 'prepare' else root.is_dir(), 'ATTEMPT_STATE')
    require(not Path(cfg['return_zip']).exists(), 'RETURN_ARCHIVE_EXISTS')
    out.mkdir(parents=True)
    temporary = root / 'temporary'
    temporary.mkdir(exist_ok=action == 'execute')
    os.environ.update(TEMP=str(temporary), TMP=str(temporary), TMPDIR=str(temporary))
    tools = legacy.load(package / 'original/process_support.py', 'reviewed_process_support')
    status, error, program = 'BLOCKED', None, None
    prior = None
    prior_repair = None
    try:
        write(out / 'startup_disk.json', legacy.fresh_disk(root, cfg['temporary_required_bytes']))
        shutil.copyfile(package / 'file_index.json', out / 'delivery_index.json')
        shutil.copyfile(package / 'authorization.json', out / 'authorization.json')
        shutil.copyfile(package / 'authorization_compatibility.json', out / 'authorization_compatibility.json')
        prior = inspect_previous(old, [r['path'] for r in cfg['sources']], approval)
        write(out / 'previous_attempt.json', prior)
        prior_repair = inspect_repair1(cfg['transfer_root'], package, old)
        write(out / 'previous_repair_attempt.json', prior_repair)
        shutil.copyfile(package / 'evidence/repair1_once.zip', out / 'sealed_repair1_once.zip')
        shutil.copyfile(package / 'evidence/git_state_once.zip', out / 'sealed_git_state_once.zip')
        legacy.check_assets(cfg)
        if action == 'prepare':
            for row in prior['files']:
                dest = relative(out / 'previous_attempt_files', row['path'])
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(old / row['path'], dest)
            materialize_sources(cfg['git'], cfg['code_root'], EXECUTION, cfg['sources'], out / 'source_repair')
        else:
            previous = read(root / 'prepare/previous_attempt.json')
            require(previous == prior, 'PREVIOUS_EVIDENCE_CHANGED')
        check_deployed_tree(cfg['git'], cfg['code_root'], EXECUTION, cfg['sources'], out / 'tree_before_action')
        binding = legacy.source_binding(cfg)
        write(out / 'source_binding.json', dict(execution_commit=EXECUTION, sources=cfg['sources'], verified=binding))
        if action == 'prepare':
            program = build_program(legacy, cfg, out, binding)
            status = 'PREPARED_NOT_EXECUTED'
        else:
            prepared = read(root / 'prepare/receipt.json')
            require(prepared.get('schema_version') == 'coe-controlled-repair-receipt/0.1.1'
                and prepared.get('authorization_sha256') == AUTH_SHA
                and prepared.get('control_commit') == control, 'PREPARED_REPAIR_BINDING')
            program = legacy.check_prepared(prepared, index_sha)
            require(prepared['run_config_sha256'] == digest((root / 'prepare/run_config.json').read_bytes())
                and prepared['build_receipt_sha256'] == digest((root / 'prepare/build/build.json').read_bytes()),
                'PREPARED_FILES_CHANGED')
            legacy.execute_worker(tools, cfg, root, out, root / 'prepare/run_config.json')
            status = 'CONTROLLED_EVIDENCE_COMPLETE_PENDING_REVIEW'
        require(snapshot(old) == prior['files'], 'PREVIOUS_EVIDENCE_CHANGED')
        legacy.check_assets(cfg)
        check_deployed_tree(cfg['git'], cfg['code_root'], EXECUTION, cfg['sources'], out / 'tree_after_action')
        legacy.source_binding(cfg)
        require(inspect_repair1(cfg['transfer_root'], package, old) == prior_repair, 'REPAIR1_EVIDENCE_CHANGED')
    except BaseException as exc:
        error = type(exc).__name__ + ':' + str(exc)
    previous_unchanged = None
    if prior is not None:
        try:
            previous_unchanged = snapshot(old) == prior['files']
            require(previous_unchanged, 'PREVIOUS_EVIDENCE_CHANGED')
        except BaseException as exc:
            error = (error + ';' if error else '') + type(exc).__name__ + ':' + str(exc)
    receipt = dict(schema_version='coe-controlled-repair-receipt/0.1.1', action=action,
        status=status if error is None else 'BLOCKED', error=error,
        execution_commit=EXECUTION, analysis_commit=EXECUTION, control_commit=control,
        native_collector_commit=legacy.PREREQUISITE, delivery_index_sha256=index_sha,
        authorization_sha256=AUTH_SHA, authorization_reference=reference,
        approved_original_index_sha256=OLD_INDEX, previous_receipt_sha256=prior['receipt_sha256'] if prior else None,
        previous_evidence_unchanged=previous_unchanged,
        previous_repair_receipt_sha256=prior_repair['receipt_sha256'] if prior_repair else None,
        program=program, run_config_sha256=digest((root / 'prepare/run_config.json').read_bytes())
            if (root / 'prepare/run_config.json').is_file() else None,
        build_receipt_sha256=digest((root / 'prepare/build/build.json').read_bytes())
            if (root / 'prepare/build/build.json').is_file() else None,
        automatic_retry=False, role='Engineering', qualification='NOT_GRANTED', formal_eligible=False,
        performance_comparability='NOT_ESTABLISHED', gpu_processes_authorized=1, hard_seconds=120)
    write(out / 'receipt.json', receipt)
    print(json.dumps(receipt), flush=True)
    if action == 'execute' or error is not None:
        try:
            print(json.dumps(tools.pack(root, Path(cfg['return_zip']))), flush=True)
        except BaseException as exc:
            print('PACK_REFUSED_PRESERVE_DIRECTORY:' + str(exc), flush=True)
            return 2
    return 0 if error is None else 2


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'execute', 'verify'], nargs='?', default='prepare')
    parser.add_argument('--index-sha256', required=True)
    args = parser.parse_args()
    return run_stage(Path(__file__).resolve().parent, args.index_sha256, args.action)


if __name__ == '__main__':
    raise SystemExit(main())
