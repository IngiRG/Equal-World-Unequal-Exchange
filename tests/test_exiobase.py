import numpy as np, pandas as pd
from ewa.exiobase import construct_counterfactual
from ewa.full_mrio import solve_unit_costs,price_residual,embodied_by_origin_destination

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
    pa=solve_unit_costs(A,la+nl); pe=solve_unit_costs(A,le+nl)
    assert np.allclose(pa,A.T@pa+la+nl)
    assert np.allclose(pe,A.T@pe+le+nl)
    assert price_residual(A,pa,la+nl)<1e-12

def test_embodied_factor_conserves_simple_final_demand():
    A=np.zeros((2,2))
    idx=pd.MultiIndex.from_tuples([("AA","s"),("BB","s")])
    cols=pd.MultiIndex.from_tuples([("AA","fd"),("BB","fd")])
    Y=pd.DataFrame([[2.,3.],[5.,7.]],index=idx,columns=cols)
    out=embodied_by_origin_destination(A,Y,np.array([10.,20.]),np.array(["AA","BB"]))
    assert np.isclose(out.loc["AA","BB"],30.)
    assert np.isclose(out.loc["BB","AA"],100.)
