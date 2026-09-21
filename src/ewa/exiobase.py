"""EXIOBASE adapter and Equal World counterfactual construction."""
from __future__ import annotations
import numpy as np, pandas as pd

def normalize_productivity(productivity:pd.Series, weights:pd.Series)->pd.Series:
    """Normalize country productivity to a world weighted mean of one."""
    p=productivity.astype(float); w=weights.astype(float)
    mean=float((p*w).sum()/w.sum())
    return p/mean

def construct_counterfactual(compensation, hours, productivity, ppp=None):
    """Country/sector wage construction using EXIOBASE labor accounts.

    compensation: monetary compensation of employees by country-sector.
    hours: hours worked by country-sector.
    productivity: country productivity index, normalized internally.
    Monetary EXIOBASE tables are already in a common EUR valuation. PPP is
    retained in outputs as a robustness/reference variable; it is not applied
    a second time to EUR compensation.
    """
    d=pd.DataFrame({"compensation":compensation,"hours":hours}).copy()
    if (d["hours"]<=0).any(): raise ValueError("Hours must be positive")
    d["actual_hourly_comp_eur"]=d["compensation"]/d["hours"]
    countries=d.index.get_level_values(0)
    country_hours=d["hours"].groupby(level=0).sum()
    e_country=normalize_productivity(productivity.reindex(country_hours.index),country_hours)
    d["effective_labor"]=countries.map(e_country)
    pool=float(d["compensation"].sum())
    effective_hours=float((d["hours"]*d["effective_labor"]).sum())
    ustar=pool/effective_hours
    d["equal_hourly_comp_eur"]=ustar*d["effective_labor"]
    d["equal_compensation"]=d["equal_hourly_comp_eur"]*d["hours"]
    d["wage_gap_eur_per_hour"]=d["equal_hourly_comp_eur"]-d["actual_hourly_comp_eur"]
    if ppp is not None: d["ppp_lcu_per_intl_dollar"]=countries.map(ppp)
    return d,ustar

def counterfactual_prices(A, actual_labor_va, equal_labor_va, nonlabor_va):
    """Solve actual and Equal World unit-cost systems with technology fixed."""
    A=np.asarray(A,float)
    I=np.eye(A.shape[0])
    va_a=np.asarray(actual_labor_va,float)+np.asarray(nonlabor_va,float)
    va_e=np.asarray(equal_labor_va,float)+np.asarray(nonlabor_va,float)
    return np.linalg.solve(I-A,va_a),np.linalg.solve(I-A,va_e)

def bilateral_fixed_quantity_gap(Z, p_actual, p_equal, regions):
    """Revalue intermediate bilateral flows at counterfactual relative prices.

    Z is the observed monetary transactions matrix. q proxy is Z/p_actual.
    This is a static fixed-bundle revaluation, not a behavioral trade simulation.
    """
    Z=np.asarray(Z,float); pa=np.asarray(p_actual,float); pe=np.asarray(p_equal,float)
    q=np.divide(Z,pa[:,None],out=np.zeros_like(Z),where=pa[:,None]!=0)
    cf=q*pe[:,None]; gap=cf-Z
    return q,cf,gap
