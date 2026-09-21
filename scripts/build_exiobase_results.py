"""Build real-data EWA results from EXIOBASE + World Bank inputs.

Requires a downloaded EXIOBASE archive. The adapter uses pymrio so the original
EXIOBASE labels are preserved. Because satellite-account row names can evolve,
the script fails loudly if labor compensation or hours cannot be identified.
"""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT/"src"))
from ewa.full_mrio import solve_unit_costs,price_residual,embodied_by_origin_destination,fixed_quantity_trade_gap
from ewa.ppp import common_currency_to_real,equal_world_real_wages,real_wage_to_common
from ewa.scenarios import hickel_northern_wage_counterfactual

def find_rows(index,needles):
    """Return all satellite rows matching every needle.

    Some EXIOBASE extensions split an account across categories. Employment
    hours, for example, are reported by skill and gender. For total hours these
    rows must be summed rather than treated as an ambiguity.
    """
    labels=[str(x) for x in index]
    hits=[i for i,s in enumerate(labels) if all(n.lower() in s.lower() for n in needles)]
    if not hits:
        raise RuntimeError(f"Expected at least one row matching {needles}; found none")
    return hits

def find_row(index,needles):
    hits=find_rows(index,needles)
    if len(hits)!=1:
        labels=[str(index[i]) for i in hits]
        raise RuntimeError(f"Expected one row matching {needles}; found {labels}")
    return hits[0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,default=2021); ap.add_argument("--archive",required=True); ap.add_argument("--out",default="site/data/real")
    a=ap.parse_args()
    import pymrio
    mrio=pymrio.parse_exiobase3(a.archive)
    # Satellite rows are discovered rather than hard-coded; ambiguity aborts.
    emp=mrio.employment.F
    fac=mrio.factor_inputs.F
    # EXIOBASE employment hours are disaggregated by skill and gender. EWA's
    # current baseline uses total observed hours per country-sector, so sum all
    # "Employment hours:" rows. This preserves every skill/gender component
    # instead of arbitrarily selecting one.
    hrows=find_rows(emp.index,["employment hours"])
    # Compensation of employees is likewise split by skill. Sum all skill
    # rows so the compensation numerator covers the same aggregate labor scope
    # as the hours denominator.
    crows=find_rows(fac.index,["compensation","employees"])
    hours=emp.iloc[hrows].astype(float).sum(axis=0)
    compensation=fac.iloc[crows].astype(float).sum(axis=0)
    # Align country-sector columns.
    hours=hours.reindex(compensation.index if isinstance(compensation.index,pd.MultiIndex) else compensation.index)
    if not isinstance(compensation.index,pd.MultiIndex):
        compensation.index=fac.F.columns; hours.index=emp.F.columns
    compensation=compensation.reindex(hours.index)
    wb=ROOT/"data/external/world_bank"
    prod=pd.read_csv(wb/f"productivity_{a.year}.csv").set_index("iso3")["value"]
    ppp=pd.read_csv(wb/f"ppp_{a.year}.csv").set_index("iso3")["value"]
    xr_usd=pd.read_csv(wb/f"exchange_usd_{a.year}.csv").set_index("iso3")["value"]
    ecb=json.loads((ROOT/"data/external/ecb"/f"eur_usd_{a.year}.json").read_text())
    usd_per_eur=float(ecb["usd_per_eur"])
    # World Bank PA.NUS.FCRF is LCU/USD. EXIOBASE is EUR, so LCU/EUR =
    # (LCU/USD)*(USD/EUR). This gives the unit-consistent route into PPP space.
    xr_eur=xr_usd*usd_per_eur
    idx=hours.index
    regions=pd.Index(idx.get_level_values(0))
    # pymrio normalizes EXIOBASE country regions to ISO2, while World Bank
    # inputs are keyed by ISO3. Convert direct-country EXIOBASE codes to ISO3
    # before joining. EXIOBASE RoW aggregates (WA/WL/WE/WF/WM) intentionally
    # remain unmapped in this country-level baseline.
    try:
        import pycountry
    except ImportError as exc:
        raise RuntimeError("pycountry is required to map EXIOBASE ISO2 regions to World Bank ISO3 codes") from exc
    def iso3_from_exio(region):
        country=pycountry.countries.get(alpha_2=str(region))
        return country.alpha_3 if country else None
    region_to_iso3={r:iso3_from_exio(r) for r in pd.Index(regions.unique())}
    eligible=prod.index.intersection(ppp.index).intersection(xr_eur.index)
    keep=pd.Index([region_to_iso3.get(r) in eligible for r in regions],dtype=bool)
    hours=hours[keep]; compensation=compensation[keep]
    # EXIOBASE contains structurally zero employment-hour cells. They are
    # valid IO sectors, but an hourly wage is undefined there. Exclude them
    # from the wage construction rather than treating zero hours as bad PPP.
    # Also reject non-finite/negative compensation before division.
    valid_labor=(hours>0) & np.isfinite(hours) & np.isfinite(compensation) & (compensation>=0)
    dropped_zero=int((hours<=0).sum())
    dropped_invalid=int((~np.isfinite(hours) | ~np.isfinite(compensation) | (compensation<0)).sum())
    hours=hours[valid_labor]; compensation=compensation[valid_labor]
    regions_kept=pd.Index(hours.index.get_level_values(0))
    countries=pd.Index([region_to_iso3[r] for r in regions_kept])
    xr_cell=pd.Series(countries.map(xr_eur),index=hours.index,dtype=float)
    ppp_cell=pd.Series(countries.map(ppp),index=hours.index,dtype=float)
    prod_country=prod.reindex(pd.Index(countries.unique()))
    country_hours=hours.groupby(pd.Index(countries)).sum()
    world_prod=float((prod_country*country_hours.reindex(prod_country.index)).sum()/country_hours.reindex(prod_country.index).sum())
    e_country=prod_country/world_prod
    if len(hours)==0:
        raise RuntimeError("No positive-hour EXIOBASE country-sector cells matched World Bank inputs")
    e_cell=pd.Series(countries.map(e_country),index=hours.index,dtype=float)
    valid_inputs=(xr_cell>0) & (ppp_cell>0) & (e_cell>0) & np.isfinite(xr_cell) & np.isfinite(ppp_cell) & np.isfinite(e_cell)
    dropped_macro=int((~valid_inputs).sum())
    if dropped_macro:
        hours=hours[valid_inputs]; compensation=compensation[valid_inputs]
        countries=countries[valid_inputs.to_numpy()]
        xr_cell=xr_cell[valid_inputs]; ppp_cell=ppp_cell[valid_inputs]; e_cell=e_cell[valid_inputs]
    if len(hours)==0:
        raise RuntimeError("No valid labor cells remain after checking hours, PPP, exchange rates and productivity")
    print(f"labor-cell validation: kept={len(hours)}, zero_hours_dropped={dropped_zero}, invalid_labor_dropped={dropped_invalid}, invalid_macro_dropped={dropped_macro}")
    observed=common_currency_to_real(compensation,hours,xr_cell,ppp_cell)
    ustar,equal_real=equal_world_real_wages(observed.real_wage_intl,hours,e_cell)
    back=real_wage_to_common(equal_real,ppp_cell,xr_cell)
    d=pd.DataFrame(index=hours.index)
    d["compensation"]=compensation; d["hours"]=hours
    d["actual_hourly_comp_eur"]=compensation/hours
    d["nominal_local_wage"]=observed.nominal_local_wage
    d["real_wage_intl"]=observed.real_wage_intl
    d["effective_labor"]=e_cell
    d["equal_real_wage_intl"]=equal_real
    d["equal_nominal_local_wage"]=back.equal_nominal_local_wage
    d["equal_hourly_comp_eur"]=back.equal_common_wage
    d["equal_compensation"]=d.equal_hourly_comp_eur*d.hours
    d["wage_gap_eur_per_hour"]=d.equal_hourly_comp_eur-d.actual_hourly_comp_eur
    d["real_wage_gap_intl_per_hour"]=d.equal_real_wage_intl-d.real_wage_intl
    d["ppp_lcu_per_intl_dollar"]=ppp_cell
    d["exchange_lcu_per_eur"]=xr_cell
    # Add ISO3 before scenario construction: EXIOBASE's native index is ISO2.
    d["iso3"]=countries.to_numpy()
    region_cfg=json.loads((ROOT/"config/regions_hickel_2021.json").read_text())
    north=set(region_cfg["north_iso3"])
    hickel,hickel_label=hickel_northern_wage_counterfactual(d,north)
    d["region_group"]=hickel["region_group"]
    d["hickel_hourly_comp_eur"]=hickel["scenario_hourly_comp_eur"]
    d["hickel_gap_eur_per_hour"]=hickel["scenario_gap_eur_per_hour"]

    # --- Complete MRIO system -------------------------------------------------
    # Keep every EXIOBASE sector/region in A, Z and Y. The EWA wage shock is
    # applied only where country PPP/productivity data support it; unsupported
    # cells retain actual labor compensation. This closes the production
    # system instead of deleting intermediate inputs.
    full_index=mrio.A.index
    A_full=mrio.A.to_numpy(float)
    x_full=mrio.x.iloc[:,0].reindex(full_index).to_numpy(float)
    Z_full=mrio.Z.loc[full_index,full_index]
    Y_full=mrio.Y.loc[full_index]
    full_regions=pd.Index(full_index.get_level_values(0))

    # Actual employee compensation on the full system; skill rows summed.
    comp_full=fac.iloc[crows].astype(float).sum(axis=0).reindex(full_index).fillna(0.0)
    hours_full=emp.iloc[hrows].astype(float).sum(axis=0).reindex(full_index).fillna(0.0)
    equal_comp_full=comp_full.copy()
    equal_comp_full.loc[d.index]=d["equal_compensation"]

    # Observed total value added is the residual required by the EXIOBASE
    # technical coefficients. Only labor remuneration is changed; residual
    # non-labor VA is retained. No clipping: a negative residual is surfaced.
    total_va_coeff=1.0-A_full.sum(axis=0)
    lab_a=np.divide(comp_full.to_numpy(float),x_full,out=np.zeros_like(x_full),where=x_full>0)
    lab_e=np.divide(equal_comp_full.to_numpy(float),x_full,out=np.zeros_like(x_full),where=x_full>0)
    nonlabor=total_va_coeff-lab_a
    va_a=lab_a+nonlabor
    va_e=lab_e+nonlabor
    pa=solve_unit_costs(A_full,va_a)
    pe=solve_unit_costs(A_full,va_e)
    res_a=price_residual(A_full,pa,va_a); res_e=price_residual(A_full,pe,va_e)
    if not (np.isfinite(pa).all() and np.isfinite(pe).all()):
        raise RuntimeError("Full MRIO price system produced non-finite values")
    # Sparse LU on the full EXIOBASE system is assessed relative to the scale
    # of the solved price vector. An absolute residual alone is misleading for
    # a large, ill-scaled MRIO system.
    if max(res_a["rel_max"],res_e["rel_max"])>1e-9:
        raise RuntimeError(f"MRIO relative price residual too large: actual={res_a}, equal={res_e}")
    price_ratio=np.divide(pe,pa,out=np.ones_like(pe),where=np.abs(pa)>1e-15)
    price_ratio_s=pd.Series(price_ratio,index=full_index)
    d["actual_price_index"]=1.0
    d["equal_price_index"]=price_ratio_s.reindex(d.index).to_numpy(float)
    d["price_gap"]=d["equal_price_index"]-1.0

    # Fixed-observed-flow trade revaluation. Positive net transfer means that
    # the country would receive more net command at Equal World prices.
    trade_net,trade_exports,trade_imports=fixed_quantity_trade_gap(
        Z_full.to_numpy(float),price_ratio,full_regions.to_numpy())

    # Physical embodied labor uses the complete Leontief system. Hours are
    # coefficients hours/output; no wage valuation enters this calculation.
    labor_coeff=np.divide(hours_full.to_numpy(float),x_full,out=np.zeros_like(x_full),where=x_full>0)
    embodied=embodied_by_origin_destination(A_full,Y_full,labor_coeff,full_regions.to_numpy())
    direct_regions=[r for r in embodied.index if region_to_iso3.get(r)]
    north_iso2={r for r in direct_regions if region_to_iso3.get(r) in north}
    south_iso2=set(direct_regions)-north_iso2
    s_to_n=float(embodied.loc[list(south_iso2),list(north_iso2)].to_numpy().sum()) if north_iso2 and south_iso2 else 0.0
    n_to_s=float(embodied.loc[list(north_iso2),list(south_iso2)].to_numpy().sum()) if north_iso2 and south_iso2 else 0.0
    net_hours=s_to_n-n_to_s

    # Valuation of the same net physical labor at the current all-skill
    # Northern benchmark and at EWA origin wages. These are explicitly
    # comparison valuations, not substitutes for the physical flow.
    north_rows=d[d.region_group=="North"]
    north_wage=float((north_rows.actual_hourly_comp_eur*north_rows.hours).sum()/north_rows.hours.sum())
    hickel_value=net_hours*north_wage
    ewa_wage_by_region={}
    for r in direct_regions:
        iso=region_to_iso3.get(r)
        g=d[d.iso3==iso]
        if len(g): ewa_wage_by_region[r]=float((g.equal_hourly_comp_eur*g.hours).sum()/g.hours.sum())
    s_to_n_ewa=0.0; n_to_s_ewa=0.0
    for o in south_iso2:
        if o in ewa_wage_by_region: s_to_n_ewa += float(embodied.loc[o,list(north_iso2)].sum())*ewa_wage_by_region[o]
    for o in north_iso2:
        if o in ewa_wage_by_region: n_to_s_ewa += float(embodied.loc[o,list(south_iso2)].sum())*ewa_wage_by_region[o]
    ewa_embodied_value=s_to_n_ewa-n_to_s_ewa

    # Validation gates.
    actual_real_pool=float((observed.real_wage_intl*hours).sum())
    equal_real_pool=float((equal_real*hours).sum())
    conservation_rel=abs(equal_real_pool-actual_real_pool)/max(abs(actual_real_pool),1e-30)
    validation={
      "real_remuneration_conservation_relative_error":conservation_rel,
      "actual_price_residual_abs":res_a["abs_max"],"equal_price_residual_abs":res_e["abs_max"],
      "actual_price_residual_relative":res_a["rel_max"],"equal_price_residual_relative":res_e["rel_max"],
      "prices_finite":bool(np.isfinite(pa).all() and np.isfinite(pe).all()),
      "north_country_count":int(d.loc[d.region_group=="North","iso3"].nunique()),
      "south_country_count":int(d.loc[d.region_group=="South","iso3"].nunique())
    }
    validation["passed"]=bool(conservation_rel<1e-10 and max(res_a["rel_max"],res_e["rel_max"])<1e-9 and validation["north_country_count"]>0 and validation["south_country_count"]>0)
    if not validation["passed"]: raise RuntimeError(f"Empirical release validation failed: {validation}")

    out=ROOT/a.out; (out/"countries").mkdir(parents=True,exist_ok=True)
    summary=[]
    for country,g in d.groupby("iso3"):
        w=np.maximum(g["hours"].to_numpy(),0); denom=w.sum()
        payload={"iso3":country,"data_status":"EMPIRICAL","year":a.year,"equal_effective_remuneration_intl_per_hour":ustar,
          "actual_hourly_comp_eur":float(np.average(g.actual_hourly_comp_eur,weights=w)),
          "equal_hourly_comp_eur":float(np.average(g.equal_hourly_comp_eur,weights=w)),
          "wage_gap_eur_per_hour":float(np.average(g.wage_gap_eur_per_hour,weights=w)),
          "mean_price_gap":float(np.average(g.price_gap,weights=np.maximum(mrio.x.iloc[:,0].reindex(g.index).to_numpy(float),1e-30))),
          "trade_hierarchy_net_million_eur":float(trade_net.get(g.index.get_level_values(0)[0],0.0)),
          "region_group":str(g.region_group.iloc[0]),
          "hickel_hourly_comp_eur":float(np.average(g.hickel_hourly_comp_eur,weights=w)),
          "hickel_gap_eur_per_hour":float(np.average(g.hickel_gap_eur_per_hour,weights=w)),
          "sectors":[{"sector":str(i[1]),**{k:(float(row[k]) if pd.notna(row[k]) and np.isfinite(float(row[k])) else None) for k in ["actual_hourly_comp_eur","nominal_local_wage","real_wage_intl","effective_labor","equal_real_wage_intl","equal_nominal_local_wage","equal_hourly_comp_eur","wage_gap_eur_per_hour","real_wage_gap_intl_per_hour","ppp_lcu_per_intl_dollar","exchange_lcu_per_eur","hickel_hourly_comp_eur","hickel_gap_eur_per_hour","actual_price_index","equal_price_index","price_gap"]}} for i,row in g.iterrows()]}
        (out/"countries"/f"{country}.json").write_text(json.dumps(payload,ensure_ascii=False,allow_nan=False)+"\n")
        summary.append({k:payload[k] for k in ["iso3","year","region_group","actual_hourly_comp_eur","equal_hourly_comp_eur","wage_gap_eur_per_hour","hickel_hourly_comp_eur","hickel_gap_eur_per_hour","mean_price_gap","trade_hierarchy_net_million_eur"]})
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,allow_nan=False)+"\n")
    (out/"manifest.json").write_text(json.dumps({"data_status":"EMPIRICAL","year":a.year,"exiobase_archive":Path(a.archive).name,"countries":len(summary),"cells":len(d),"productivity":"World Bank SL.GDP.PCAP.EM.KD","ppp":"World Bank PA.NUS.PPP","exchange_rate":"World Bank PA.NUS.FCRF + ECB USD/EUR annual reference rate","ppp_role":"baseline: EXIOBASE EUR -> LCU via MER -> international dollars via PPP -> EWA -> LCU -> EUR for MRIO prices","hickel_scenario":hickel_label,"north_south_definition":"config/regions_hickel_2021.json","exiobase_year_status":"2021 is a now-cast in EXIOBASE 3.9; see docs/hickel-comparison.md","labor_cell_validation":{"zero_hours_dropped":dropped_zero,"invalid_labor_dropped":dropped_invalid,"invalid_macro_dropped":dropped_macro},"validation":validation,"embodied_labor":{"south_to_north_hours":s_to_n,"north_to_south_hours":n_to_s,"net_south_to_north_hours":net_hours,"hickel_style_all_skill_value_eur":hickel_value,"ewa_origin_wage_value_eur":ewa_embodied_value,"reference_net_hours_billion":826.0},"price_system":"full EXIOBASE A/Z/Y; unsupported wage cells retain actual labor compensation; non-labor VA residual retained","note":"Static EWA. Physical embodied-labor flows are calculated separately from monetary valuation. The Hickel-style value remains an all-skill approximation, not an exact skill-matched replication."},indent=2)+"\n")
    print(f"built {len(summary)} countries / {len(d)} country-sector cells")

if __name__=="__main__": main()
