"""Helper identity is structural, not CPython's versioned ast.dump format.

The absent type_params fixture models the older AST shape; it is NOT a claim
that Python 3.11 was executed. Pinned source commits are the independent input.
"""
import ast
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def source():
    return (ROOT / 'exposedpath/runner.py').read_text(encoding='utf-8-sig')


def helper(text=None):
    return next(n for n in ast.parse(text or source()).body
                if isinstance(n, ast.FunctionDef) and n.name == 'observe_token_ready_boundary')


def old_source():
    # Exact later-hook delta, independently checked against the pinned legacy
    # Git function in the local audit. This is not a permissive runtime adapter.
    return source().replace('    completion_controller=None,\n', '').replace(
        '    if completion_controller is not None:\n'
        '        completion_controller.before_copy(identity_base,token_index,phase)\n', '')


@pytest.mark.parametrize('profile,text', [
    ('COE_PILOT_NATURAL', source()), ('LEGACY_NATURAL', old_source())], ids=['pilot', 'legacy'])
def test_same_source_known_ast_shapes_and_line_endings(profile, text):
    from analysis.coe_helper_identity import fingerprint, validate_source
    node = helper(text)
    fields = tuple(f for f in node._fields if f != 'type_params')
    old = type('FunctionDef', (ast.AST,), {'_fields': fields})()
    for field in fields:
        setattr(old, field, copy.deepcopy(getattr(node, field)))
    new = type('FunctionDef', (ast.AST,), {'_fields': fields + ('type_params',)})()
    for field in fields:
        setattr(new, field, copy.deepcopy(getattr(node, field)))
    new.type_params = []
    result = validate_source(text, profile)
    assert result['sha256'] == fingerprint(old) == fingerprint(new)
    assert validate_source(text.replace('\n', '\r\n'), profile) == result
    assert result['version'] == 'coe-helper-structure/0.1.0'


@pytest.mark.parametrize('damage,reason', [
    ('nonempty_type_params', 'COE_HELPER_AST_NONEMPTY_TYPE_PARAMS'),
    ('unknown_field', 'COE_HELPER_AST_FIELDS:FunctionDef'),
    ('unknown_attribute', 'COE_HELPER_AST_ATTRIBUTES:FunctionDef'),
    ('missing_field', 'COE_HELPER_AST_MISSING:FunctionDef.name'),
    ('unknown_node', 'COE_HELPER_AST_NODE:Pass')])
def test_closed_ast_schema(damage, reason):
    from analysis.coe_helper_identity import fingerprint
    node = helper()
    if damage == 'nonempty_type_params':
        # Do not mutate instance _fields on older CPython: that would add an
        # unknown attribute and mask the intended nonempty-type-params gate.
        if 'type_params' not in node._fields:
            old = node
            node = type('FunctionDef', (ast.AST,), {'_fields': old._fields + ('type_params',)})()
            for field in old._fields:
                setattr(node, field, copy.deepcopy(getattr(old, field)))
        node.type_params = [ast.Name(id='T', ctx=ast.Load())]
    elif damage == 'unknown_field':
        # An empty new field is NOT silently stripped as "harmless".
        node = type('FunctionDef', (ast.AST,), {'_fields': node._fields + ('future_empty',)})()
        node.future_empty = []
    elif damage == 'unknown_attribute':
        node.future_empty = []
    elif damage == 'missing_field':
        del node.name
    elif damage == 'unknown_node':
        node.body.append(ast.Pass())
    with pytest.raises(ValueError) as error:
        fingerprint(node)
    assert str(error.value) == reason


@pytest.mark.parametrize('profile,text', [
    ('COE_PILOT_NATURAL', source()), ('LEGACY_NATURAL', old_source())], ids=['pilot', 'legacy'])
@pytest.mark.parametrize('before,after', [
    ('.detach().cpu().reshape', '.detach().reshape'),
    ('completed_ns = clock_ns()', 'completed_ns = 0'),
    ('sync_ordinal=token_index', 'sync_ordinal=0'),
    ('phase=phase,', 'phase="decode",'),
    ('values = token_tensor', 'torch.cuda.synchronize()\n        values = token_tensor')])
def test_real_behavior_changes_fail_at_helper_gate(profile, text, before, after):
    from analysis.coe_helper_identity import validate_source
    assert before in text
    changed = text.replace(before, after)
    with pytest.raises(ValueError) as error:
        validate_source(changed, profile)
    assert str(error.value) == 'COE_HELPER_PROFILE_OUT_OF_SCOPE'


def test_profiles_do_not_borrow_each_others_identity():
    from analysis.coe_helper_identity import validate_source
    for text, profile in [(source(), 'LEGACY_NATURAL'), (old_source(), 'COE_PILOT_NATURAL'),
                          (source(), 'future')]:
        with pytest.raises(ValueError) as error:
            validate_source(text, profile)
        assert str(error.value) == 'COE_HELPER_PROFILE_OUT_OF_SCOPE'


def test_pinned_source_provenance_and_real_isolated_python(tmp_path):
    from analysis.coe_helper_identity import EXPECTED
    contract = json.loads((ROOT / 'docs/v1_4_1/contracts/coe_candidate_analysis_v0_2_1.json').read_text())
    for name, text in [('COE_PILOT_NATURAL', source()), ('LEGACY_NATURAL', old_source())]:
        function = ast.get_source_segment(text, helper(text))
        item = contract['helper_identity']['profiles'][name]
        assert hashlib.sha256(function.encode()).hexdigest() == item['function_source_sha256']
        assert EXPECTED[name] == item['structure_sha256']
    # Real isolated interpreter, imports stdlib + this identity module only.
    # A target Stage A run executes this under its actual Python, not a double.
    launcher = (ROOT / 'scripts/run_coe_candidate_pilot.ps1').read_text()
    code = launcher.split("$HelperCode=@'\n", 1)[1].split("\n'@", 1)[0]
    # Real target receipt code, legacy source supplied from this independent
    # pinned-source fixture, never executing/importing the runner.
    legacy = tmp_path / 'legacy.py'
    legacy.write_text(old_source(), encoding='utf8')
    proc = subprocess.run([sys._base_executable, '-I', '-S', '-B', '-c', code,
        str(ROOT / 'analysis/coe_helper_identity.py'), str(ROOT / 'exposedpath/runner.py'), str(legacy),
        '.'.join(map(str,sys.version_info[:3]))],capture_output=True, text=True, timeout=30)
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result['python'] == sys.version and result['cuda_initialized'] is False
    assert [r['identity']['sha256'] for r in result['rows']] == [EXPECTED['COE_PILOT_NATURAL'], EXPECTED['LEGACY_NATURAL']]
