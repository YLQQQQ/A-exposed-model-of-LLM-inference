"""Real CPU threads and Futures; independent outcomes, no target GPU packages."""
import inspect
import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest


def observer_type():
    from exposedpath import gate8_stages
    assert hasattr(gate8_stages, 'LoadTaskObserver'), 'load task observer missing'
    return gate8_stages.LoadTaskObserver


def source():
    from exposedpath.gate8_load_tasks import TARGET_SOURCE_HASHES
    return dict(profile='hf-load-tasks/0.1.0', source_files=[
        dict(package_relative_path='transformers/'+name,sha256=digest,size_bytes=100)
        for name,digest in TARGET_SOURCE_HASHES.items()],
        qualification='NOT_ASSESSED')


@pytest.mark.parametrize('changed',[False,True])
def test_resolver_compares_loaded_code_with_hashed_source(monkeypatch,tmp_path,changed):
    import hashlib,importlib,importlib.metadata
    from exposedpath import gate8_load_tasks as tasks
    path=tmp_path/'core_model_loading.py'
    data=b'def spawn_materialize(pool):\n    return 1\n'
    path.write_bytes(data)
    altered={}
    exec(compile(data if not changed else b'def spawn_materialize(pool):\n    return 2\n',str(path),'exec'),altered)
    module=SimpleNamespace(__file__=str(path),spawn_materialize=altered['spawn_materialize'])
    monkeypatch.setattr(importlib,'import_module',lambda _:module)
    monkeypatch.setattr(importlib.metadata,'version',lambda _:'5.17.0')
    monkeypatch.setattr(tasks,'TARGET_SOURCE_HASHES',{'core_model_loading.py':hashlib.sha256(data).hexdigest()})
    if changed:
        with pytest.raises(ValueError,match='HOOK'):
            tasks.resolve_target_source()
    else:
        resolved,descriptor,hook=tasks.resolve_target_source()
        assert resolved is module and hook is module.spawn_materialize
        assert descriptor['qualification']=='NOT_ASSESSED'


@pytest.mark.parametrize('pop_fails',[False,True])
def test_seal_during_marker_cleanup_stays_in_flight_without_wait(pop_fails):
    observer,module,_=new_observer()
    entered,release=threading.Event(),threading.Event()
    def pop():
        entered.set()
        assert release.wait(5)
        if pop_fails:
            raise RuntimeError('marker cleanup failed')
    observer.pop=pop
    pool=ThreadPoolExecutor(max_workers=1)
    try:
        future=observer.run_attempt(module,lambda:module.spawn_materialize(pool,lambda:23),
                                    branch='trust_remote_code')
        assert entered.wait(5)
        snapshot=observer.seal()
        assert snapshot['tasks'][0]['status']=='IN_FLIGHT'
        assert snapshot['tasks'][0]['host_end_ns'] is None
        assert snapshot['observation_status']=='INCOMPLETE'
    finally:
        release.set()
        pool.shutdown(wait=True)  # test cleanup only, never production observation
    assert future.result()==23
    assert observer.seal()==snapshot


def original_spawn(pool, tensor, device=None, dtype=None, sharding_op=None, tensor_idx=None):
    def job():
        return tensor()
    return pool.submit(job) if pool is not None else job


def test_hook_is_resolved_inside_scope_lock_not_before_it():
    from exposedpath.gate8_load_tasks import _PATCH_LOCK
    observer,_,_=new_observer()
    reads=[]
    class Module:
        spawn_materialize=staticmethod(original_spawn)
        def __getattribute__(self,name):
            if name=='spawn_materialize':
                reads.append(_PATCH_LOCK.locked())
            return object.__getattribute__(self,name)
    module=Module()
    assert observer.run_attempt(module,lambda:23,branch='trust_remote_code')==23
    assert reads and all(reads)
    assert module.spawn_materialize is original_spawn


def test_actual_source_thread_pool_keyword_is_preserved():
    observer,_,_=new_observer()
    def actual_signature(thread_pool,tensor,device=None,dtype=None,sharding_op=None,tensor_idx=None):
        return original_spawn(thread_pool,tensor,device,dtype,sharding_op,tensor_idx)
    module=SimpleNamespace(spawn_materialize=actual_signature)
    with ThreadPoolExecutor(max_workers=1) as pool:
        value=observer.run_attempt(module,lambda:module.spawn_materialize(thread_pool=pool,tensor=lambda:17).result(),
                                   branch='trust_remote_code')
    assert value==17 and module.spawn_materialize is actual_signature


def new_observer(pass_id='pass1'):
    from test_gate8_identity import producer_pass
    from exposedpath.gate8_identity import PASS_FIELDS
    ledger=producer_pass()
    ledger['pass_id']=pass_id
    identity={k:ledger[k] for k in PASS_FIELDS}
    events=[]
    observer=observer_type()(identity=identity,pid=__import__('os').getpid(),
        parent_stage_id='b'*64,source=source(),push=events.append,pop=lambda:events.append('POP'))
    module=SimpleNamespace(spawn_materialize=original_spawn)
    return observer,module,events


@pytest.mark.parametrize('pass_id',['pass0','pass1'])
def test_tasks_keep_future_return_value_order_and_same_thread_ids(pass_id):
    observer,module,events=new_observer(pass_id)
    returned=[]
    class Pool(ThreadPoolExecutor):
        def submit(self,*args,**kwargs):
            future=super().submit(*args,**kwargs)
            returned.append(future)
            return future
    token=object()
    with Pool(max_workers=1) as pool:
        def action():
            first=module.spawn_materialize(pool,lambda:token)
            second=module.spawn_materialize(pool,lambda:23)
            assert first is returned[0] and second is returned[1]
            assert first.result() is token
            return second.result()
        assert observer.run_attempt(module,action,branch='trust_remote_code')==23
    assert module.spawn_materialize is original_spawn
    value=observer.seal()
    assert [t['status'] for t in value['tasks']]==['COMPLETE','COMPLETE']
    assert value['tasks'][0]['native_tid']==value['tasks'][1]['native_tid']
    assert value['tasks'][0]['native_tid']!=threading.get_native_id()
    assert len({t['task_id'] for t in value['tasks']})==2
    assert value['observation_status']=='COMPLETE'
    assert value['ownership_status']=='NOT_ASSESSED'
    assert len(events)==(4 if pass_id=='pass1' else 0)


def test_two_workers_one_attempt_and_exception_identity():
    observer,module,_=new_observer()
    barrier=threading.Barrier(2)
    error=RuntimeError('original failure')
    def good():
        barrier.wait(timeout=3)
        return 9
    def bad():
        barrier.wait(timeout=3)
        raise error
    with ThreadPoolExecutor(max_workers=2) as pool:
        def action():
            a=module.spawn_materialize(pool,good)
            b=module.spawn_materialize(pool,bad)
            assert a.result()==9
            b.result()
        with pytest.raises(RuntimeError) as caught:
            observer.run_attempt(module,action,branch='trust_remote_code')
    assert caught.value is error
    value=observer.seal()
    assert {t['status'] for t in value['tasks']}=={'COMPLETE','FAILED'}
    assert len({t['native_tid'] for t in value['tasks']})==2
    assert value['attempts'][0]['status']=='FAILED'
    assert module.spawn_materialize is original_spawn


def test_retry_does_not_wait_for_or_reassign_prior_attempt_worker():
    observer,module,_=new_observer()
    started,release=threading.Event(),threading.Event()
    pool=ThreadPoolExecutor(max_workers=1)
    try:
        def slow():
            started.set()
            assert release.wait(5)
            return 1
        def fail():
            module.spawn_materialize(pool,slow)
            assert started.wait(3)
            raise ValueError('load attempt failed')
        with pytest.raises(ValueError):
            observer.run_attempt(module,fail,branch='trust_remote_code')
        assert observer.run_attempt(module,lambda:7,branch='fallback')==7
        frozen=observer.seal()
        assert [a['status'] for a in frozen['attempts']]==['FAILED','COMPLETE']
        assert frozen['tasks'][0]['status']=='IN_FLIGHT'
        assert frozen['tasks'][0]['attempt_id']==frozen['attempts'][0]['attempt_id']
        assert frozen['observation_status']=='INCOMPLETE'
        release.set()
    finally:
        release.set()
        pool.shutdown(wait=True)  # test cleanup only; observer must never do this
    assert observer.seal()==frozen  # late worker completion cannot rewrite sealed evidence


def test_cancelled_future_kept_without_result_consumption_or_shutdown_change():
    observer,module,_=new_observer()
    entered,release=threading.Event(),threading.Event()
    with ThreadPoolExecutor(max_workers=1) as pool:
        blocker=pool.submit(lambda:(entered.set(),release.wait(5)))
        assert entered.wait(3)
        try:
            def action():
                future=module.spawn_materialize(pool,lambda:pytest.fail('cancelled task ran'))
                assert future.cancel()
                return future
            future=observer.run_attempt(module,action,branch='trust_remote_code')
            assert future.cancelled()
            value=observer.seal()
            assert value['tasks'][0]['status']=='CANCELLED'
            assert value['tasks'][0]['native_tid'] is None
        finally:
            release.set()
            blocker.result()


def test_sync_callable_is_preserved_but_not_falsely_observed():
    observer,module,_=new_observer()
    callback=lambda:8
    returned=observer.run_attempt(module,lambda:module.spawn_materialize(None,callback),branch='fallback')
    assert inspect.isfunction(returned) and returned()==8
    value=observer.seal()
    assert value['tasks'][0]['status']=='UNOBSERVED_SYNC_CALLABLE'
    assert value['tasks'][0]['native_tid'] is None
    assert value['observation_status']=='INCOMPLETE'


def test_cross_thread_submission_is_not_owned_by_active_attempt():
    observer,module,_=new_observer()
    with ThreadPoolExecutor(max_workers=1) as pool:
        def outsider():
            return module.spawn_materialize(None,lambda:5)()
        assert observer.run_attempt(module,lambda:pool.submit(outsider).result(),branch='fallback')==5
    value=observer.seal()
    assert value['tasks']==[]
    assert 'OTHER_SUBMIT_THREAD' in value['issues']
    assert value['observation_status']=='INCOMPLETE'


def test_missing_hook_does_not_leak_scope_lock():
    observer,module,_=new_observer()
    with pytest.raises((ValueError,AttributeError)):
        observer.run_attempt(SimpleNamespace(),lambda:None,branch='fallback')
    assert observer.run_attempt(module,lambda:9,branch='fallback')==9


def test_seal_during_active_attempt_is_rejected():
    observer,module,_=new_observer()
    with pytest.raises(ValueError,match='ACTIVE'):
        observer.run_attempt(module,observer.seal,branch='fallback')
    assert module.spawn_materialize is original_spawn


def test_source_file_hash_and_redirect_fail_before_hook(tmp_path):
    from exposedpath import gate8_load_tasks as tasks
    assert hasattr(tasks,'verify_source_files'), 'bounded source verifier missing'
    import hashlib
    file=tmp_path/'core.py'
    file.write_bytes(b'synthetic source\n')
    expected={'core.py':hashlib.sha256(file.read_bytes()).hexdigest()}
    assert tasks.verify_source_files(tmp_path,expected)[0]['sha256']==expected['core.py']
    file.write_bytes(b'changed')
    with pytest.raises(ValueError,match='SOURCE'):
        tasks.verify_source_files(tmp_path,expected)
    with pytest.raises(ValueError,match='SOURCE'):
        tasks.verify_source_files(tmp_path,{'../outside.py':'f'*64})
