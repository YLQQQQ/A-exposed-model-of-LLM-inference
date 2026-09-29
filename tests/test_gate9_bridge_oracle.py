import importlib
import pytest


def oracle():
    assert importlib.util.find_spec('exposedpath_v141.gate9_bridge_oracle'), 'independent bridge oracle missing'
    return importlib.import_module('exposedpath_v141.gate9_bridge_oracle')


def test_independent_union_oracle_with_nested_api_and_completed_prefix():
    # Contract hand arithmetic. Nested non-submit [6,7) counted once.
    assert oracle().account((0,100),[(5,10),(6,7),(45,50),(60,65)],[(25,40),(75,100)],
        [(-20,-10),(10,30),(50,85)])==[45,15,15,25,0]
    assert oracle().account((0,40),[(5,10),(6,7),(45,50),(60,65)],[(25,40),(75,100)],
        [(-20,-10),(10,30),(50,85)])==[20,5,5,10,0]


def test_oracle_rejects_activity_after_sync_return():
    with pytest.raises(ValueError): oracle().per_sync([(10,45)],(25,40))


def test_full_prefix_hidden_not_sum_of_request_exposure():
    assert oracle().per_sync([(-20,-10),(10,30),(50,85)],(75,100))==[55,10,15]
