"""Explicit pre-execution Engineering declaration, not a completeness claim."""
PROFILE = 'TARGET_SCOPE_ENGINEERING_SUFFICIENCY/0.1'
EXECUTION_VERSION = 'exposedpath-engineering-execution/0.1.0'
ASSUMPTIONS = ['NO_USER_CONCURRENCY', 'NO_EXPLICIT_IPC_OR_EVENT_DEPENDENCY',
               'NO_UNRECORDED_INCOMING_DEPENDENCY']


def declaration(attention_backend):
    if attention_backend not in ('sdpa', 'eager'):
        raise ValueError('ENGINEERING_BACKEND_UNSUPPORTED')
    return dict(profile=PROFILE, attention_backend=attention_backend,
                assumptions=list(ASSUMPTIONS), declaration_role='PRE_EXECUTION')


def validate_declaration(manifest):
    value = manifest.get('engineering_scope')
    if (not isinstance(value, dict) or value != declaration(value.get('attention_backend'))
            or manifest.get('execution_mode') != 'eager'
            or type(manifest.get('batch_size')) is not int or manifest['batch_size'] != 1
            or manifest.get('attention_backend') != value['attention_backend']
            or manifest.get('run_role') != 'ENGINEERING' or manifest.get('data_role') != 'Engineering'):
        raise ValueError('ENGINEERING_DECLARATION_REQUIRED')
    return value
