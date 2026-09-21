from ewa.hierarchy import trade_revaluation

def test_revaluation():
    r=trade_revaluation([10,5],[2,4],[3,3])
    assert r["actual_value"]==40
    assert r["equal_world_value"]==45
    assert r["hierarchy_gap"]==5
