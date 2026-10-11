import copy
import pytest
from scripts import gate13_offline_binding as binding


def authorization():
    return dict(version='G13-OFFLINE-PERFORMANCE-AUTHORIZATION/0.1',
        authority='HUMAN_USER',purpose='LOCAL_IMMUTABLE_FORMAL_REVIEW',
        execution_commit='9'*40,analysis_commit='e'*40,protocol_sha256='a'*64,
        archive_sha256='b'*64,manifest_sha256='c'*64,
        measurement_or_statistical_amendment=False)


def test_explicit_offline_binding_keeps_execution_and_analysis_distinct():
    a=authorization()
    binding.validate_authorization(a,execution='9'*40,analysis='e'*40,
        protocol='a'*64,archive='b'*64,manifest='c'*64)
    assert a['execution_commit'] != a['analysis_commit']


@pytest.mark.parametrize('field,value',[
    ('authority','SCRIPT'),('archive_sha256','d'*64),('analysis_commit','f'*40),
    ('protocol_sha256','d'*64),('measurement_or_statistical_amendment',True),
    ('version','G13-OFFLINE-PERFORMANCE-AUTHORIZATION/999')])
def test_wrong_authorization_cannot_relax_frozen_identity(field,value):
    a=authorization();a[field]=value
    with pytest.raises(ValueError):
        binding.validate_authorization(a,execution='9'*40,analysis='e'*40,
            protocol='a'*64,archive='b'*64,manifest='c'*64)


def example():
    actual=dict(schema_version='domain/0.1',identity={'run_id':'one'},
        status='QUALITY_CHECK_PASSED_NOT_QUALIFICATION',
        dropped_records_status='UNKNOWN',measurement_validity='NOT_ASSESSED',
        physical_s_records=[dict(W=['a','b'],terminal='b')],
        requests=[dict(a_records=[dict(A_device_wait_ns=5,A_unattributed_ns=0)])])
    saved=copy.deepcopy(actual);saved.update(schema_version='exposedpath-formal-domain-check/0.1.0',
        formal={'run_id':'one'},run_role='FORMAL',data_role='Formal',
        usage='LIMITED_PROTOCOL_ANALYSIS_NOT_GLOBAL_CERTIFICATION',files=[{'filename':'raw'}],
        formal_admission={'status':'ADMITTED_LIMITED_PROTOCOL','analysis_sources':{'old':'seal'}})
    return saved,actual


def test_semantic_equality_does_not_reuse_old_analysis_seal():
    saved,actual=example()
    binding.compare_domain_payload(saved,actual)
    assert 'formal_admission' not in actual
    assert saved['formal_admission']['analysis_sources']=={'old':'seal'}


@pytest.mark.parametrize('field,value',[
    ('physical_s_records',[dict(W=['b'],terminal='b')]),
    ('dropped_records_status','ZERO_CONFIRMED'),('identity',{'run_id':'other'}),
    ('requests',[dict(a_records=[dict(A_device_wait_ns=0,A_unattributed_ns=5)])])])
def test_changed_dependency_quality_scope_or_accounting_rejected(field,value):
    saved,actual=example();actual[field]=value
    with pytest.raises(ValueError,match='DOMAIN_PAYLOAD'):
        binding.compare_domain_payload(saved,actual)


def test_incomplete_or_legacy_saved_result_is_not_formal_evidence():
    saved,actual=example();saved['formal_admission']['status']='REJECTED'
    with pytest.raises(ValueError):binding.compare_domain_payload(saved,actual)
