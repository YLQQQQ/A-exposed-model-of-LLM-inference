"""Exported ranges, not the implementation-dependent NVTX return, prove recording."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sqlite3
import zipfile

import pytest

from analysis import memset_same_capture as consumer
from tests.test_memset_same_capture import fixture


def observed_fixture():
    side,raw,expected=fixture()
    for c in side['calls']:c.update(push_level=-1,pop_level=-1)
    raw['micro_scope']=dict(record_id='scope',event_type=59,pid=7,tid=9,
        domain_id=0,start=9,end=70)
    raw['domains']=[dict(record_id='domain',event_type=75,pid=7,tid=9,
        domain_id=1,name='EP_MEMSET_MICRO',start=8)]
    for r in raw['ranges']:r['domain_id']=1
    return side,raw,expected


def test_minus_one_returns_need_actual_ranges_and_are_preserved():
    side,raw,expected=observed_fixture()
    result=consumer.review(side,raw,expected)
    assert result['schema_version']=='memset-same-capture-review/0.1.1'
    assert result['calls'][1]['effect_ids']==['m1']
    assert result['calls'][0]['nvtx_recording']==dict(
        evidence='EXPORTED_DOMAIN_RANGE_AND_UNIQUE_RUNTIME',domain_id=1,
        domain_record_id='domain',push_return=-1,pop_return=-1,
        return_interpretation='UNAVAILABLE_LEVEL_NOT_RECORDING_PROOF')
    assert side['calls'][0]['push_level']==side['calls'][0]['pop_level']==-1
    assert result['coe_admission']=='NOT_ASSESSED'


@pytest.mark.parametrize('change,reason',[
    ('missing','RANGE_PAIR'),('duplicate','RANGE_PAIR'),('domain','NVTX_DOMAIN'),
    ('domain_missing','NVTX_DOMAIN'),('domain_process','NVTX_DOMAIN'),
    ('thread','RANGE_PAIR'),('run','RANGE_PAIR'),('unclosed','RANGE_PAIR'),
    ('runtime_boundary','RUNTIME_PAIR'),('overlap','RANGE_ORDER'),
    ('scope_boundary','MICRO_SCOPE'),('effect_missing','NONZERO_EFFECT_MISSING'),
    ('unknown_negative','NVTX_RECORDING'),('mixed_returns','NVTX_RECORDING')])
def test_negative_return_never_bypasses_specific_missing_evidence(change,reason):
    side,raw,expected=observed_fixture()
    if change=='missing':raw['ranges'].pop()
    elif change=='duplicate':raw['ranges'].append(deepcopy(raw['ranges'][0]))
    elif change=='domain':raw['domains'][0]['name']='OTHER'
    elif change=='domain_missing':raw['domains']=[]
    elif change=='domain_process':raw['domains'][0]['pid']=8
    elif change=='thread':raw['ranges'][1]['tid']=10
    elif change=='run':raw['ranges'][1]['run_id']='b'*32
    elif change=='unclosed':raw['ranges'][1]['end']=None
    elif change=='runtime_boundary':raw['ranges'][1]['end']=48
    elif change=='overlap':raw['ranges'][1]['start']=19
    elif change=='scope_boundary':raw['micro_scope']['end']=40
    elif change=='effect_missing':raw['effects']=[]
    elif change=='unknown_negative':side['calls'][0].update(push_level=-2,pop_level=-2)
    elif change=='mixed_returns':side['calls'][0]['pop_level']=0
    with pytest.raises(ValueError,match='^MEMSET_MICRO_'+reason+'$'):
        consumer.review(side,raw,expected)


def test_sealed_real_trace_minus_one_ranges_complete_whole_consumer(tmp_path):
    archive=Path(__file__).resolve().parents[1]/'.local/transfer/memset_micro_002f3ae9fcc2_once.zip'
    if not archive.is_file():pytest.skip('Sealed target micro archive not present; synthetic tests remain mandatory')
    original=archive.read_bytes()
    assert len(original)==68580 and hashlib.sha256(original).hexdigest()=='29e4413ad7c2895d261718c54fd301266c01a94e647fe2d265475865f22ab3b8'
    with zipfile.ZipFile(archive) as z:
        cfg=json.loads(z.read('delivery.json'));old=z.read('receipt.json')
        assert json.loads(old)['status']=='BLOCKED'
        for name in ['capture.sqlite','side.json']:(tmp_path/name).write_bytes(z.read(name))
    expected=dict(run_id=cfg['run_id'],runtime_path=cfg['runtime_path'],
        gpu_uuid=cfg['gpu_uuid'],pci_bus_id=cfg['gpu_pci'])
    result=consumer.review_files(tmp_path/'capture.sqlite',tmp_path/'side.json',expected,tmp_path/'new_derived')
    assert [(r['runtime_id'],r['effect_ids']) for r in result['calls']]==[('API:8',[]),('API:11',['MEMSET:2'])]
    assert all(r['nvtx_recording']['push_return']==r['nvtx_recording']['pop_return']==-1 for r in result['calls'])
    assert result['pytorch_internal_coverage']=='NOT_PROVEN'
    assert archive.read_bytes()==original


@pytest.mark.parametrize('sql,reason',[
    ("UPDATE NVTX_EVENTS SET text='OTHER' WHERE eventType=75",'NVTX_DOMAIN'),
    ('UPDATE NVTX_EVENTS SET endGlobalTid=117440600 WHERE domainId=1 AND eventType=59','RANGE_PAIR'),
    ('DELETE FROM CUPTI_ACTIVITY_KIND_MEMSET','NONZERO_EFFECT_MISSING')])
def test_sqlite_evidence_not_return_or_message_controls_recording(tmp_path,sql,reason):
    from tests.test_memset_same_capture import test_file_consumer_binds_exact_side_and_sqlite_bytes
    test_file_consumer_binds_exact_side_and_sqlite_bytes(tmp_path)
    side=json.loads((tmp_path/'side.json').read_text(encoding='utf8'))
    for c in side['calls']:c.update(push_level=-1,pop_level=-1)
    (tmp_path/'side.json').write_text(json.dumps(side),encoding='utf8')
    with sqlite3.connect(tmp_path/'capture.sqlite') as db:db.execute(sql)
    _,_,expected=fixture()
    with pytest.raises(ValueError,match='^MEMSET_MICRO_'+reason+'$'):
        consumer.review_files(tmp_path/'capture.sqlite',tmp_path/'side.json',expected,tmp_path/'rejected_derived')
