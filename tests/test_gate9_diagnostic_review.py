"""Independent warning-scope examples plus actual producer/file-chain wiring."""
import copy
import json
import sqlite3
import pytest

from test_gate8_identity import sha, write_json

MESSAGES=(
    'Not all NVTX events might have been collected.',
    'No NVTX events collected. Does the process use NVTX?',
    'CUDA profiling might have not been started correctly.',
    'No CUDA events collected. Does the process use CUDA?',
)


def evidence():
    target=(1<<48)+(12<<24); other=(1<<48)+(34<<24)
    rows=[dict(source_rowid=i+1,text=text,severity_id=2,source_id=3,timestamp_type=2,
        global_pid=other,process_id=34,process_relation='OTHER_PROCESS') for i,text in enumerate(MESSAGES)]
    diagnostic=dict(records=rows,target_global_pid=target,target_pid=12,source_sqlite_sha256='a'*64,
        target_nvtx_refs=[dict(source_table='NVTX_EVENTS',source_rowid=1,global_pid=target,global_tid=target+5)])
    bundle=dict(manifest=dict(source=dict(sqlite=dict(sha256='a'*64),export=dict(
        platform='windows-desktop',product_version='2026.2.1.210'))),records=dict(
        nvtx=[dict(record_id='n1',source_table='NVTX_EVENTS',source_rowid=1,global_tid=target+5)],
        device_activity=[dict(record_id='k1',global_pid=target)]))
    return diagnostic,bundle


def test_official_basis_is_separate_from_original_classifier_and_unknown():
    from exposedpath_v141.gate9_diagnostic_review import review
    from exposedpath_v141.gate8_engineering_scope import _diagnostics
    diagnostic,bundle=evidence(); before=copy.deepcopy(diagnostic)
    result=review(diagnostic,bundle)
    assert result['accepted_rowids']==[1,2,3,4]
    assert result['basis']=='G8-WARNING-EVIDENCE/0.1'
    assert result['source_status']=='USER_RELAYED_OFFICIAL_RESPONSE'
    assert result['dropped_records_status']=='UNKNOWN'
    assert all(r['disposition']=='IMPACT_UNBOUNDED' for r in _diagnostics(diagnostic))
    assert diagnostic==before


@pytest.mark.parametrize('damage',['target','unknown_pid','namespace','new_message','partial',
    'severity','source','timestamp','no_nvtx','no_cuda','hash','version','platform','target_zero','aux_activity'])
def test_warning_rule_cannot_generalize(damage):
    from exposedpath_v141.gate9_diagnostic_review import review
    d,b=evidence()
    if damage=='target':
        d['records'][0].update(global_pid=d['target_global_pid'],process_id=12,process_relation='TARGET_PROCESS')
    if damage=='unknown_pid': d['records'][0].update(global_pid=None,process_id=None,process_relation='UNKNOWN')
    if damage=='namespace':
        for r in d['records']: r['global_pid']+=1<<48
    if damage=='new_message': d['records'][0]['text']='CUDA buffers lost.'
    if damage=='partial': d['records'].pop()
    if damage=='severity': d['records'][0]['severity_id']=3
    if damage=='source': d['records'][0]['source_id']=1
    if damage=='timestamp': d['records'][0]['timestamp_type']=1
    if damage=='no_nvtx': b['records']['nvtx']=[]
    if damage=='no_cuda': b['records']['device_activity']=[]
    if damage=='hash': b['manifest']['source']['sqlite']['sha256']='b'*64
    if damage=='version': b['manifest']['source']['export']['product_version']='2025.1'
    if damage=='platform': b['manifest']['source']['export']['platform']='linux'
    if damage=='target_zero':
        d['records'].append(dict(d['records'][0],source_rowid=5,text='Number of CUDA events collected: 0.',
            severity_id=1,global_pid=d['target_global_pid'],process_id=12,process_relation='TARGET_PROCESS'))
    if damage=='aux_activity': b['records']['device_activity'].append(dict(record_id='k2',global_pid=d['records'][0]['global_pid']))
    with pytest.raises(ValueError,match='DOMAIN_DIAGNOSTIC_IMPACT_UNBOUNDED'): review(d,b)


@pytest.mark.parametrize('target_warning',[False,True])
def test_actual_producer_file_chain_warning_wiring(tmp_path,monkeypatch,target_warning):
    from test_gate9_bridge_files import source
    from exposedpath_v141.gate8_files import load_input_receipt,write_input_receipt
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    from exposedpath_v141.gate9_bridge_oracle import check
    receipt,execution,producer,sqlite=source(tmp_path,monkeypatch)
    _,paths=load_input_receipt(receipt)
    with sqlite3.connect(sqlite) as db:
        db.execute("UPDATE META_DATA_EXPORT SET value='2026.2.1.210' WHERE name='EXPORT_PRODUCT_VERSION'")
        db.execute("UPDATE META_DATA_EXPORT SET value='3.25.0' WHERE name='EXPORT_SCHEMA_VERSION'")
        db.execute("INSERT INTO META_DATA_EXPORT VALUES ('EXPORT_PLATFORM','windows-desktop')")
        cols={r[1] for r in db.execute('pragma table_info(DIAGNOSTIC_EVENT)')}
        for col in ('globalPid','timestampType'):
            if col not in cols: db.execute('alter table DIAGNOSTIC_EVENT add column '+col+' INTEGER')
        tid=db.execute('select globalTid from NVTX_EVENTS limit 1').fetchone()[0]
        pid=tid-tid%2**24
        for text in MESSAGES:
            db.execute('insert into DIAGNOSTIC_EVENT(timestamp,source,severity,text,globalPid,timestampType) values(0,3,2,?,?,2)',
                (text,pid if target_warning else pid+(1<<24)))
    report=json.loads(paths['export_report'].read_text(encoding='utf-8'))
    report['canonical_sqlite_sha256']=sha(sqlite)
    report['attempts'][0].update(sqlite_sha256=sha(sqlite),sqlite_size=sqlite.stat().st_size)
    write_json(paths['export_report'],report)
    receipt=write_input_receipt(tmp_path/'warning-input.json',artifacts=paths,collector_version='2026.2.1.210',capture_session_id='CPU-SYNTHETIC')
    data=json.loads(execution.read_text(encoding='utf-8')); data['input_receipt_sha256']=sha(receipt)
    execution=write_json(tmp_path/'warning-execution.json',data)
    if target_warning:
        with pytest.raises(ValueError,match='DIAGNOSTIC_IMPACT_UNBOUNDED'):
            process_domain(receipt,execution,tmp_path/'result',bridge_path=producer/'bridge.json')
        return
    result=process_domain(receipt,execution,tmp_path/'result',bridge_path=producer/'bridge.json')
    value=load_domain(result,receipt,execution,bridge_path=producer/'bridge.json')
    assert len(value['diagnostic_review']['accepted_rowids'])==4
    assert value['dropped_records_status']=='UNKNOWN'
    assert check(sqlite,producer,value)['status']=='MATCH_REVIEW_REQUIRED'


@pytest.mark.parametrize('target_warning,damage',[(False,None),(True,None),(False,'correlation')])
def test_g1_official_review_preserves_original_rows_and_other_gates(tmp_path,monkeypatch,target_warning,damage):
    from test_gate9_domain import source
    from exposedpath_v141.gate8_files import write_input_receipt
    from exposedpath_v141.gate9_domain import process_domain,load_domain
    receipt,execution,paths=source(tmp_path,monkeypatch,damage=damage)
    with sqlite3.connect(paths['sqlite']) as db:
        db.execute("UPDATE META_DATA_EXPORT SET value='2026.2.1.210' WHERE name='EXPORT_PRODUCT_VERSION'")
        db.execute("UPDATE META_DATA_EXPORT SET value='3.25.0' WHERE name='EXPORT_SCHEMA_VERSION'")
        db.execute("INSERT INTO META_DATA_EXPORT VALUES ('EXPORT_PLATFORM','windows-desktop')")
        tid=db.execute('select globalTid from NVTX_EVENTS limit 1').fetchone()[0]
        pid=tid-tid%2**24
        for text in MESSAGES:
            db.execute('insert into DIAGNOSTIC_EVENT(timestamp,source,severity,text,globalPid,timestampType) values(0,3,2,?,?,2)',
                (text,pid if target_warning else pid+(1<<24)))
    report=json.loads(paths['export_report'].read_text())
    report['canonical_sqlite_sha256']=sha(paths['sqlite'])
    report['attempts'][0].update(sqlite_sha256=sha(paths['sqlite']),sqlite_size=paths['sqlite'].stat().st_size)
    write_json(paths['export_report'],report)
    receipt=write_input_receipt(tmp_path/'warning-input.json',artifacts=paths,collector_version='2026.2.1.210',capture_session_id='CPU-SYNTHETIC')
    if target_warning:
        try: out=process_domain(receipt,execution,tmp_path/'result')
        except ValueError: return
        assert json.loads(out.read_text())['status']=='BLOCKED'
    else:
        out=process_domain(receipt,execution,tmp_path/'result')
        value=load_domain(out,receipt,execution)
        if damage:
            assert value['status']=='BLOCKED'
            assert not value['requests'][1]['a_records']
            return
        assert value['status']=='QUALITY_CHECK_PASSED_NOT_QUALIFICATION'
        assert len(value['diagnostic_review']['accepted_rowids'])==4
        assert sum(r['disposition']=='IMPACT_UNBOUNDED' for r in value['diagnostic_dispositions'])==4
        assert value['dropped_records_status']=='UNKNOWN'
