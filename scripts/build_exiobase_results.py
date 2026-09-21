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
from ewa.exiobase import counterfactual_prices
from ewa.ppp import common_currency_to_real,equal_world_real_wages,real_wage_to_common
from ewa.scenarios import hickel_northern_wage_counterfactual

def find_row(index,needles):
    labels=[str(x) for x in index]
    hits=[(i,s) for i,s in enumerate(labels) if all(n.lower() in s.lower() for n in needles)]
    if len(hits)!=1: raise RuntimeError(f"Expected one row matching {needles}; found {[x[1] for x in hits]}")
    return hits[0][0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,default=2021); ap.add_argument("--archive",required=True); ap.add_argument("--out",default="site/data/real")
    a=ap.parse_args()
    import pymrio
    mrio=pymrio.parse_exiobase3(a.archive)
    # Satellite rows are discovered rather than hard-coded; ambiguity aborts.
    emp=mrio.employment.F
    fac=mrio.factor_inputs.F
    hrow=find_row(emp.index,["hours"])
    crow=find_row(fac.index,["compensation","employees"])
    hours=emp.iloc[hrow].astype(float)
    compensation=fac.iloc[crow].astype(float)
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
    eligible=prod.index.intersection(ppp.index).intersection(xr_eur.index)
    keep=regions.isin(eligible)
    hours=hours[keep]; compensation=compensation[keep]
    countries=pd.Index(hours.index.get_level_values(0))
    xr_cell=pd.Series(countries.map(xr_eur),index=hours.index,dtype=float)
    ppp_cell=pd.Series(countries.map(ppp),index=hours.index,dtype=float)
    prod_country=prod.reindex(pd.Index(countries.unique()))
    country_hours=hours.groupby(level=0).sum()
    world_prod=float((prod_country*country_hours.reindex(prod_country.index)).sum()/country_hours.reindex(prod_country.index).sum())
    e_country=prod_country/world_prod
    e_cell=pd.Series(countries.map(e_country),index=hours.index,dtype=float)
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
    region_cfg=json.loads((ROOT/"config/regions_hickel_2021.json").read_text())
    north=set(region_cfg["north_iso3"])
    hickel,hickel_label=hickel_northern_wage_counterfactual(d,north)
    d["region_group"]=hickel["region_group"]
    d["hickel_hourly_comp_eur"]=hickel["scenario_hourly_comp_eur"]
    d["hickel_gap_eur_per_hour"]=hickel["scenario_gap_eur_per_hour"]

    # Technical coefficients are kept fixed. Unit labor VA is compensation/x.
    A=mrio.A.loc[d.index,d.index].to_numpy(float)
    x=mrio.x.loc[d.index].iloc[:,0].to_numpy(float)
    lab_a=d["compensation"].to_numpy(float)/x
    lab_e=d["equal_compensation"].to_numpy(float)/x
    # Residual non-labor VA preserves observed non-labor distributive claims in
    # baseline. This is a named assumption and must be varied in robustness.
    total_va=1-A.sum(axis=0)
    nonlabor=np.maximum(total_va-lab_a,0)
    pa,pe=counterfactual_prices(A,lab_a,lab_e,nonlabor)
    d["actual_price_index"]=pa; d["equal_price_index"]=pe; d["price_gap"]=pe-pa

    out=ROOT/a.out; (out/"countries").mkdir(parents=True,exist_ok=True)
    summary=[]
    for country,g in d.groupby(level=0):
        w=np.maximum(g["hours"].to_numpy(),0); denom=w.sum()
        payload={"iso3":country,"data_status":"EMPIRICAL","year":a.year,"equal_effective_remuneration_intl_per_hour":ustar,
          "actual_hourly_comp_eur":float(np.average(g.actual_hourly_comp_eur,weights=w)),
          "equal_hourly_comp_eur":float(np.average(g.equal_hourly_comp_eur,weights=w)),
          "wage_gap_eur_per_hour":float(np.average(g.wage_gap_eur_per_hour,weights=w)),
          "mean_price_gap":float(np.average(g.price_gap,weights=np.maximum(x[[d.index.get_loc(i) for i in g.index]],1e-30))),
          "region_group":str(g.region_group.iloc[0]),
          "hickel_hourly_comp_eur":float(np.average(g.hickel_hourly_comp_eur,weights=w)),
          "hickel_gap_eur_per_hour":float(np.average(g.hickel_gap_eur_per_hour,weights=w)),
          "sectors":[{"sector":str(i[1]),**{k:float(row[k]) for k in ["actual_hourly_comp_eur","nominal_local_wage","real_wage_intl","effective_labor","equal_real_wage_intl","equal_nominal_local_wage","equal_hourly_comp_eur","wage_gap_eur_per_hour","real_wage_gap_intl_per_hour","ppp_lcu_per_intl_dollar","exchange_lcu_per_eur","hickel_hourly_comp_eur","hickel_gap_eur_per_hour","actual_price_index","equal_price_index","price_gap"]}} for i,row in g.iterrows()]}
        (out/"countries"/f"{country}.json").write_text(json.dumps(payload,ensure_ascii=False)+"\n")
        summary.append({k:payload[k] for k in ["iso3","year","region_group","actual_hourly_comp_eur","equal_hourly_comp_eur","wage_gap_eur_per_hour","hickel_hourly_comp_eur","hickel_gap_eur_per_hour","mean_price_gap"]})
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False)+"\n")
    (out/"manifest.json").write_text(json.dumps({"data_status":"EMPIRICAL","year":a.year,"exiobase_archive":Path(a.archive).name,"countries":len(summary),"cells":len(d),"productivity":"World Bank SL.GDP.PCAP.EM.KD","ppp":"World Bank PA.NUS.PPP","exchange_rate":"World Bank PA.NUS.FCRF + ECB USD/EUR annual reference rate","ppp_role":"baseline: EXIOBASE EUR -> LCU via MER -> international dollars via PPP -> EWA -> LCU -> EUR for MRIO prices","hickel_scenario":hickel_label,"north_south_definition":"config/regions_hickel_2021.json","exiobase_year_status":"2021 is a now-cast in EXIOBASE 3.9; see docs/hickel-comparison.md","note":"Static EWA plus Hickel-style comparison. Current technology/productivity retained. RoW aggregates excluded where no direct country productivity mapping exists."},indent=2)+"\n")
    print(f"built {len(summary)} countries / {len(d)} country-sector cells")

if __name__=="__main__": main()
