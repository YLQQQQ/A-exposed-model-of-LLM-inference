"""Versioned, closed structural identity for two reviewed token-ready helpers.

Never uses ast.dump formatting or an observed runtime digest as its expectation.
Only FunctionDef's *empty* type_params field may be absent across AST versions.
Source file bytes, role and execution identity remain separately verified.
"""
from __future__ import annotations

import ast
import hashlib
import json


VERSION = 'coe-helper-structure/0.1.0'
# Field order is this contract's order, not a runtime's dump/repr convention.
FIELDS = {
    'FunctionDef': ('name', 'args', 'body', 'decorator_list', 'returns', 'type_comment'),
    'arguments': ('posonlyargs', 'args', 'vararg', 'kwonlyargs', 'kw_defaults', 'kwarg', 'defaults'),
    'Expr': ('value',), 'Assign': ('targets', 'value', 'type_comment'),
    'If': ('test', 'body', 'orelse'), 'Try': ('body', 'handlers', 'orelse', 'finalbody'),
    'Return': ('value',), 'Name': ('id', 'ctx'), 'arg': ('arg', 'annotation', 'type_comment'),
    'Attribute': ('value', 'attr', 'ctx'), 'Constant': ('value', 'kind'),
    'Call': ('func', 'args', 'keywords'), 'Load': (),
    'Subscript': ('value', 'slice', 'ctx'), 'Store': (), 'keyword': ('arg', 'value'),
    'UnaryOp': ('op', 'operand'), 'Raise': ('exc', 'cause'),
    'Compare': ('left', 'ops', 'comparators'), 'Tuple': ('elts', 'ctx'),
    'JoinedStr': ('values',), 'GeneratorExp': ('elt', 'generators'),
    'Not': (), 'IsNot': (), 'List': ('elts', 'ctx'),
    'FormattedValue': ('value', 'conversion', 'format_spec'),
    'comprehension': ('target', 'iter', 'ifs', 'is_async'), 'USub': (),
}
LOCATIONS = {'lineno', 'col_offset', 'end_lineno', 'end_col_offset'}
EXPECTED = {
    'LEGACY_NATURAL': '8fb94439753b53d792d5c81d797fefd21a7fff6a5ba77d3a27f2d61a7dcbcd9a',
    'COE_PILOT_NATURAL': '205ef13d491d6a30850cd3a3b15fd883832887cc3dd72a5e702966dd68c80c1f',
}


def _require(ok, reason):
    if not ok:
        raise ValueError('COE_HELPER_' + reason)


def _structure(value):
    if isinstance(value, ast.AST):
        name = type(value).__name__
        _require(name in FIELDS, 'AST_NODE:' + name)
        fields = FIELDS[name]
        actual = tuple(value._fields)
        allowed = (fields, fields + ('type_params',)) if name == 'FunctionDef' else (fields,)
        _require(actual in allowed, 'AST_FIELDS:' + name)
        _require(not (set(vars(value)) - set(actual) - LOCATIONS), 'AST_ATTRIBUTES:' + name)
        if 'type_params' in actual:
            _require('type_params' in vars(value), 'AST_MISSING:' + name + '.type_params')
            _require(type(value.type_params) is list and not value.type_params, 'AST_NONEMPTY_TYPE_PARAMS')
        for field in fields:
            _require(field in vars(value), 'AST_MISSING:' + name + '.' + field)
        return [name, [[field, _structure(getattr(value, field))] for field in fields]]
    if type(value) is list:
        return [_structure(v) for v in value]
    _require(value is None or type(value) in (str, int, bool), 'AST_VALUE_TYPE')
    return value


def fingerprint(helper):
    encoded = json.dumps([VERSION, _structure(helper)], ensure_ascii=True,
                         separators=(',', ':'), allow_nan=False).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()


def validate_source(source, profile):
    nodes = [n for n in ast.parse(source, type_comments=True).body
             if isinstance(n, ast.FunctionDef) and n.name == 'observe_token_ready_boundary']
    _require(len(nodes) == 1, 'SOURCE')
    digest = fingerprint(nodes[0])
    _require(profile in EXPECTED and digest == EXPECTED[profile], 'PROFILE_OUT_OF_SCOPE')
    return dict(version=VERSION, profile=profile, sha256=digest)
