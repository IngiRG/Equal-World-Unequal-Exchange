import pandas as pd
from ewa.labor import equal_world_wages
from ewa.validation import remuneration_conservation

def test_conservation():
    d=pd.DataFrame({"nominal_wage":[20.,4.],"ppp":[1.,.5],
                    "effective_labor":[1.,.5],"hours":[100.,100.]})
    out,b=equal_world_wages(d)
    ok,a,e=remuneration_conservation(out)
    assert ok
    assert abs(a-e)<1e-9
    assert b>0
