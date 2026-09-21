"""Alternative counterfactual valuation scenarios for direct comparison."""
from __future__ import annotations
import numpy as np, pandas as pd

def assign_north_south(index, north_iso3:set[str], iso3=None):
    # EXIOBASE's MultiIndex uses ISO2 region codes, while the published
    # North/South classification is ISO3. Prefer an explicit ISO3 vector.
    c=pd.Index(iso3) if iso3 is not None else pd.Index(index.get_level_values(0))
    return pd.Series(np.where(c.isin(north_iso3),"North","South"),index=index)

def hickel_northern_wage_counterfactual(df, north_iso3:set[str], skill_col=None):
    """Northern-wage valuation comparable in concept to Hickel et al.

    If skill_col is supplied, North benchmark wages are hours-weighted within
    skill class. Without skill-resolved inputs, this function returns an
    explicitly labelled all-skill approximation and MUST NOT be described as
    a replication of Hickel et al.
    """
    d=df.copy()
    iso3=d["iso3"].to_numpy() if "iso3" in d.columns else None
    d["region_group"]=assign_north_south(d.index,north_iso3,iso3=iso3).values
    group=[skill_col] if skill_col and skill_col in d.columns else []
    north=d[d.region_group=="North"]
    if group:
        benchmarks=(north.assign(wx=north.actual_hourly_comp_eur*north.hours)
                    .groupby(group).agg(wx=("wx","sum"),h=("hours","sum")))
        benchmarks["north_wage"]=benchmarks.wx/benchmarks.h
        d=d.join(benchmarks[["north_wage"]],on=group)
        label="Hickel-style Northern wage, skill-matched"
    else:
        nw=float((north.actual_hourly_comp_eur*north.hours).sum()/north.hours.sum())
        d["north_wage"]=nw
        label="Northern wage, all-skill approximation"
    d["scenario_hourly_comp_eur"]=np.where(d.region_group=="South",d.north_wage,d.actual_hourly_comp_eur)
    d["scenario_compensation"]=d.scenario_hourly_comp_eur*d.hours
    d["scenario_gap_eur_per_hour"]=d.scenario_hourly_comp_eur-d.actual_hourly_comp_eur
    return d,label

def ewa_scenario(df):
    d=df.copy()
    d["scenario_hourly_comp_eur"]=d["equal_hourly_comp_eur"]
    d["scenario_compensation"]=d["equal_compensation"]
    d["scenario_gap_eur_per_hour"]=d["wage_gap_eur_per_hour"]
    return d,"EWA aggregate-conserving effective-labor benchmark"
