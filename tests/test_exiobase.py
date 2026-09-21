import numpy as np, pandas as pd
from ewa.exiobase import construct_counterfactual,counterfactual_prices

def test_counterfactual_conserves_compensation():
    idx=pd.MultiIndex.from_tuples([("AAA","s1"),("BBB","s1")])
    comp=pd.Series([100.,80.],index=idx); hours=pd.Series([10.,20.],index=idx)
    prod=pd.Series({"AAA":2.,"BBB":1.})
    d,u=construct_counterfactual(comp,hours,prod)
    assert np.isclose(d.compensation.sum(),d.equal_compensation.sum())
    assert u>0

def test_counterfactual_price_identity():
    A=np.array([[.2,.1],[.1,.2]])
    la=np.array([.4,.4]); le=np.array([.5,.3]); nl=np.array([.2,.2])
    pa,pe=counterfactual_prices(A,la,le,nl)
    assert np.allclose(pa,A@pa+la+nl)
    assert np.allclose(pe,A@pe+le+nl)
