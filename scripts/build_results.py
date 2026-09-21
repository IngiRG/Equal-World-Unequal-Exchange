"""Build auditable static JSON consumed by the GitHub Pages site."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from ewa.labor import equal_world_wages
from ewa.validation import remuneration_conservation

def main():
    source=ROOT/"data/demo/country_sector.csv"
    df=pd.read_csv(source)
    out,benchmark=equal_world_wages(df)
    ok,actual_pool,equal_pool=remuneration_conservation(out)
    if not ok: raise RuntimeError("Aggregate remuneration conservation failed")
    dest=ROOT/"site/data"; (dest/"countries").mkdir(parents=True,exist_ok=True)
    summary=[]
    for iso3,g in out.groupby("iso3"):
        r=g.iloc[0]
        actual=float((g.real_wage*g.hours).sum()/g.hours.sum())
        equal=float((g.equal_real_wage*g.hours).sum()/g.hours.sum())
        gap=equal-actual
        payload={"iso3":iso3,"country":r["country"],"status":"DEMONSTRATION — NOT AN EMPIRICAL ESTIMATE",
          "steps":[
            {"id":1,"title":"Observed nominal remuneration","equation":"wᴺ","value":float(r.nominal_wage),"unit":"local currency / hour"},
            {"id":2,"title":"PPP adjustment","equation":"wᴿ = wᴺ / q","inputs":{"wᴺ":float(r.nominal_wage),"q":float(r.ppp)},"value":float(r.real_wage),"unit":"international $ / hour"},
            {"id":3,"title":"Effective-labor remuneration","equation":"uᴬ = wᴿ / e","inputs":{"wᴿ":float(r.real_wage),"e":float(r.effective_labor)},"value":float(r.actual_effective_remuneration),"unit":"international $ / effective hour"},
            {"id":4,"title":"Global Equal World benchmark","equation":"ū* = Σ(wᴿL) / Σ(eL)","value":benchmark,"unit":"international $ / effective hour"},
            {"id":5,"title":"Equal World real wage","equation":"w* = ū*e","inputs":{"ū*":benchmark,"e":float(r.effective_labor)},"value":float(r.equal_real_wage),"unit":"international $ / hour"},
            {"id":6,"title":"Static remuneration hierarchy gap","equation":"Hʷ = w* − wᴿ","value":float(r.real_wage_gap),"unit":"international $ / hour"}],
          "sectors":g[["sector","real_wage","effective_labor","actual_effective_remuneration","equal_real_wage","real_wage_gap"]].to_dict("records"),
          "interpretation":{"actual_real_wage":actual,"equal_real_wage":equal,"gap":gap,
             "note":"Positive means remuneration would be higher under this specified Equal World. This demo does not establish an empirical transfer or imperialism."}}
        (dest/"countries"/f"{iso3}.json").write_text(json.dumps(payload,indent=2)+"\n")
        summary.append({"iso3":iso3,"country":r.country,"gap":gap,"actual":actual,"equal":equal})
    (dest/"summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    manifest={"model_version":"0.1.0","data_status":"synthetic demonstration","source":"data/demo/country_sector.csv",
      "equal_effective_remuneration":benchmark,"actual_real_remuneration_pool":actual_pool,
      "equal_world_real_remuneration_pool":equal_pool,"conservation_passed":ok}
    (dest/"manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"Built {len(summary)} country result files; conservation={ok}")

if __name__=="__main__": main()
