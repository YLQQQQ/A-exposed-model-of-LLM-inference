"""Explicit local performance-analysis authorization; no collection or seal rewrite."""
def validate_authorization(value, *, execution, analysis, protocol, archive, manifest):
    expected=dict(version='G13-OFFLINE-PERFORMANCE-AUTHORIZATION/0.1',
        authority='HUMAN_USER',purpose='LOCAL_IMMUTABLE_FORMAL_REVIEW',
        execution_commit=execution,analysis_commit=analysis,protocol_sha256=protocol,
        archive_sha256=archive,manifest_sha256=manifest,
        measurement_or_statistical_amendment=False)
    if value != expected or any(type(value.get(k)) is not type(v) for k,v in expected.items()):
        raise ValueError('OFFLINE_AUTHORIZATION_IDENTITY')


def compare_domain_payload(saved, actual):
    if (saved.get('schema_version')!='exposedpath-formal-domain-check/0.1.0'
            or saved.get('run_role')!='FORMAL' or saved.get('data_role')!='Formal'
            or saved.get('formal_admission',{}).get('status')!='ADMITTED_LIMITED_PROTOCOL'):
        raise ValueError('OFFLINE_FORMAL_SOURCE')
    # These fields attest the historical analysis execution, not S/A/B values.
    # They must be validated separately, never reused to authorize a new runtime.
    envelope={'files','formal','formal_admission','run_role','data_role','usage','schema_version'}
    original={k:v for k,v in saved.items() if k not in envelope}
    computed={k:v for k,v in actual.items() if k not in envelope}
    if original!=computed:
        raise ValueError('OFFLINE_DOMAIN_PAYLOAD_MISMATCH')
