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
from ewa.exiobase import construct_counterfactual,counterfactual_prices

def find_row(index,needles):
    labels=[str(x) for x in index]
    hits=[(i,s) for i,s in enumerate(labels) if all(n.lower() in s.lower() for n in needles)]
    if len(hits)!=1: raise RuntimeError(f"Expected one row matching {needles}; found {[x[1] for x in hits]}")
    return hits[0][0]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,default=2020); ap.add_argument("--archive",required=True); ap.add_argument("--out",default="site/data/real")
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
    # EXIOBASE uses region codes; most individual countries are ISO-like. RoW
    # aggregates are excluded from country-productivity EWA until an explicit
    # aggregation rule is supplied.
    idx=hours.index
    regions=pd.Index(idx.get_level_values(0))
    keep=regions.isin(prod.index)
    hours=hours[keep]; compensation=compensation[keep]
    d,ustar=construct_counterfactual(compensation,hours,prod,ppp)

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
        payload={"iso3":country,"data_status":"EMPIRICAL","year":a.year,"equal_effective_remuneration_eur_per_hour":ustar,
          "actual_hourly_comp_eur":float(np.average(g.actual_hourly_comp_eur,weights=w)),
          "equal_hourly_comp_eur":float(np.average(g.equal_hourly_comp_eur,weights=w)),
          "wage_gap_eur_per_hour":float(np.average(g.wage_gap_eur_per_hour,weights=w)),
          "mean_price_gap":float(np.average(g.price_gap,weights=np.maximum(x[[d.index.get_loc(i) for i in g.index]],1e-30))),
          "sectors":[{"sector":str(i[1]),**{k:float(row[k]) for k in ["actual_hourly_comp_eur","effective_labor","equal_hourly_comp_eur","wage_gap_eur_per_hour","actual_price_index","equal_price_index","price_gap"]}} for i,row in g.iterrows()]}
        (out/"countries"/f"{country}.json").write_text(json.dumps(payload,ensure_ascii=False)+"\n")
        summary.append({k:payload[k] for k in ["iso3","year","actual_hourly_comp_eur","equal_hourly_comp_eur","wage_gap_eur_per_hour","mean_price_gap"]})
    (out/"summary.json").write_text(json.dumps(summary,ensure_ascii=False)+"\n")
    (out/"manifest.json").write_text(json.dumps({"data_status":"EMPIRICAL","year":a.year,"exiobase_archive":Path(a.archive).name,"countries":len(summary),"cells":len(d),"productivity":"World Bank SL.GDP.PCAP.EM.KD","ppp":"World Bank PA.NUS.PPP","note":"Static EWA; current technology/productivity retained. RoW aggregates excluded where no direct country productivity mapping exists."},indent=2)+"\n")
    print(f"built {len(summary)} countries / {len(d)} country-sector cells")

if __name__=="__main__": main()
