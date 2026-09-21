import numpy as np, pandas as pd
from ewa.ppp import common_currency_to_real,equal_world_real_wages,real_wage_to_common

def test_ppp_pipeline_and_real_conservation():
    idx=pd.Index(["N","S"])
    # common currency wages/hour: 20 and 4; LCU/common: 1 and 2; PPP: 1 and 1
    comp=pd.Series([2000.,400.],idx); h=pd.Series([100.,100.],idx)
    xr=pd.Series([1.,2.],idx); ppp=pd.Series([1.,1.],idx)
    t=common_currency_to_real(comp,h,xr,ppp)
    e=pd.Series([1.,.5],idx)
    u,w=equal_world_real_wages(t.real_wage_intl,h,e)
    back=real_wage_to_common(w,ppp,xr)
    assert np.isclose((t.real_wage_intl*h).sum(),(w*h).sum())
    assert back.equal_common_wage.loc["S"] != back.equal_common_wage.loc["N"]

def test_ppp_changes_equal_nominal_wage():
    e=pd.Series([1.,1.],index=["A","B"]); h=pd.Series([1.,1.],index=e.index)
    real=pd.Series([20.,20.],index=e.index); _,w=equal_world_real_wages(real,h,e)
    back=real_wage_to_common(w,pd.Series([1.,.4],index=e.index),pd.Series([1.,1.],index=e.index))
    assert np.isclose(back.equal_nominal_local_wage.loc["B"],8.)
    assert np.isclose(back.equal_nominal_local_wage.loc["A"],20.)
