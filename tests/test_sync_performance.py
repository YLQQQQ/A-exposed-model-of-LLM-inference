"""Independent graph expectations and work bounds, not wall-clock thresholds."""
from collections import defaultdict
from exposedpath_v141 import sync_semantics as s
from exposedpath_v141 import a_accounting as a
import pytest


def test_candidate_batch_reads_registry_once(monkeypatch):
    real=s.load_sync_registry
    reads=[]
    def load():
        reads.append(1)
        return real()
    monkeypatch.setattr(s,'load_sync_registry',load)
    assert s.build_semantic_sync_candidates({'cuda_api':[
        {'api_name':'cudaStreamQuery_v3020'} for _ in range(100)]},[])==[]
    assert len(reads)==1


class Counted(dict):
    reads=0
    def get(self,*args):
        type(self).reads+=1
        return super().get(*args)


def activity(i,stream=0,context=1):
    return Counted(record_id=str(i), context_id=context,stream_id=stream,
                   enqueue_start_ns=i*10,enqueue_end_ns=i*10+1)


def inventory(activities):
    return dict(activities=activities,contexts=[{'context_id':1,'null_stream_id':0}],
        streams=[{'context_id':1,'stream_id':2,'flag':1}],
        execution_context={'default_stream_mode':'LEGACY'})


def test_same_stream_default_pairs_are_not_scanned():
    inv=inventory([activity(i) for i in range(100)])
    Counted.reads=0
    edges=[]
    assert s._add_default_stream_edges(inv,{'host_start_ns':10000},defaultdict(set),edges)==[]
    assert edges==[]
    assert Counted.reads<3000  # Linear filtering, not 100 x 100 get-pairs.


def test_default_edges_keep_order_conflicts_and_nonblocking_exclusion():
    a=activity(1); b=activity(2,1); c=activity(3); d=activity(4,2)
    edges=[]
    assert s._add_default_stream_edges(inventory([a,b,c,d]),{'host_start_ns':100},defaultdict(set),edges)==[]
    assert [(e['from'],e['to']) for e in edges]==[('1','2'),('2','3')]
    b['enqueue_start_ns']=10; b['enqueue_end_ns']=15
    assert s._add_default_stream_edges(inventory([a,b]),{'host_start_ns':100},defaultdict(set),[])==['DEPENDENCY_CLOSURE_AMBIGUOUS']


def test_sweep_preserves_half_open_nested_order_and_empty_intervals():
    records=[('outer',(-5,8)),('nested',(0,3)),('touch',(3,8)),
             ('empty',(3,3)),('outside',(9,10))]
    segments=[(-2,0),(0,3),(3,8),(8,9)]
    assert [[r[0] for r in rows] for rows in a._covering_by_segment(records,segments)]==[
        ['outer'],['outer','nested'],['outer','touch'],[]]


def test_sweep_does_not_scan_all_records_for_each_segment():
    class Interval(tuple):
        reads=0
        def __getitem__(self,i):
            type(self).reads+=1
            return super().__getitem__(i)
    records=[(i,Interval((i,i+1))) for i in range(100)]
    assert [[r[0] for r in rows] for rows in a._covering_by_segment(records,[(i,i+1) for i in range(100)])]==[[i] for i in range(100)]
    assert Interval.reads<1000


def test_phase_progress_does_not_mask_failure(capsys):
    from exposedpath_v141.gate9_domain import analysis_stage
    with pytest.raises(ValueError,match='original'):
        with analysis_stage('fixture'):
            raise ValueError('original')
    out=capsys.readouterr().out
    assert 'fixture START' in out and 'fixture FAILED' in out
    assert 'fixture COMPLETE' not in out


def test_reviewed_remaining_point_never_executes_128(tmp_path):
    from scripts.gate10_feasibility import run_candidates
    seen=[]
    def run(n,path):
        seen.append(n)
        return {'status':'FEASIBLE_ONCE_NOT_STABILITY'}
    report=run_candidates(tmp_path/'new',run,remaining_512_only=True)
    assert seen==[512]
    assert report['points']==[{'input_tokens':512,'status':'FEASIBLE_ONCE_NOT_STABILITY'}]


def test_actual_a_entry_does_not_scan_unrelated_apis_per_segment(monkeypatch):
    from test_v141_a_accounting import _inputs,_api,_window
    rows=tuple(_api(str(i),2*i,2*i+1,'cudaStreamIsCapturing_v10000',None) for i in range(100))
    calls=[]
    original=a._covers
    def count(interval,segment):
        calls.append(1)
        return original(interval,segment)
    monkeypatch.setattr(a,'_covers',count)
    record,=a.calculate_a_windows(_inputs(apis=rows,syncs=(),activities=(),windows=(_window(end=200),)))
    assert (record['A_host_path_ns'],record['A_cuda_api_ns'],record['A_unattributed_ns'])==(100,100,0)
    assert len(calls)<1000
