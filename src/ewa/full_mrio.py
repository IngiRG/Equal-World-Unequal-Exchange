"""Sparse full-system MRIO calculations for empirical Equal World Analysis."""
from __future__ import annotations
import numpy as np, pandas as pd
from scipy import sparse
from scipy.sparse.linalg import splu

def _lu(A, transpose=False):
    a=sparse.csc_matrix(np.asarray(A,float))
    n=a.shape[0]
    m=sparse.eye(n,format="csc")-(a.T if transpose else a)
    return splu(m)

def solve_unit_costs(A, value_added_coeff):
    lu=_lu(A,transpose=True)
    return lu.solve(np.asarray(value_added_coeff,float))

def price_residual(A,p,v):
    """Return scale-aware diagnostics for p = A.T p + v."""
    p=np.asarray(p,float); v=np.asarray(v,float); A=np.asarray(A,float)
    r=p-(A.T@p+v)
    absmax=float(np.max(np.abs(r)))
    scale=max(float(np.max(np.abs(p))),float(np.max(np.abs(v))),1.0)
    return {"abs_max":absmax,"rel_max":absmax/scale}

def embodied_by_origin_destination(A, final_demand, direct_coeff, sector_regions):
    Y=final_demand
    dest=pd.Index(Y.columns.get_level_values(0))
    destinations=list(dict.fromkeys(dest))
    Yreg=np.column_stack([Y.loc[:,dest==r].sum(axis=1).to_numpy(float) for r in destinations])
    req=_lu(A,transpose=False).solve(Yreg)
    embodied=np.asarray(direct_coeff,float)[:,None]*req
    origins=list(dict.fromkeys(sector_regions))
    out=np.zeros((len(origins),len(destinations)))
    reg=np.asarray(sector_regions)
    for i,r in enumerate(origins): out[i,:]=embodied[reg==r,:].sum(axis=0)
    return pd.DataFrame(out,index=origins,columns=destinations)

def fixed_quantity_trade_gap(Z, price_ratio, sector_regions):
    Z=np.asarray(Z,float); ratio=np.asarray(price_ratio,float)
    delta=Z*(ratio[:,None]-1.0)
    regs=np.asarray(sector_regions); unique=list(dict.fromkeys(regs))
    exports={}; imports={}
    for r in unique:
        mask=regs==r
        exports[r]=float(delta[mask,:].sum())
        imports[r]=float(delta[:,mask].sum())
    return {r:exports[r]-imports[r] for r in unique},exports,imports
