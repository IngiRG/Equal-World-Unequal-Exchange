"""Retrieve World Bank PPP conversion factors (PA.NUS.PPP)."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import requests
import pandas as pd

BASE="https://api.worldbank.org/v2/country/all/indicator/PA.NUS.PPP"

def fetch(year:int) -> pd.DataFrame:
    params={"format":"json","date":str(year),"per_page":400}
    r=requests.get(BASE,params=params,timeout=60); r.raise_for_status()
    payload=r.json()
    rows=[]
    for x in payload[1]:
        if x["value"] is not None:
            rows.append({"iso3":x["countryiso3code"],"country":x["country"]["value"],
                         "year":int(x["date"]),"ppp":float(x["value"])})
    return pd.DataFrame(rows).sort_values("iso3")

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,default=2014)
    ap.add_argument("--out",default="data/external/world_bank_ppp.csv")
    a=ap.parse_args(); out=Path(a.out); out.parent.mkdir(parents=True,exist_ok=True)
    df=fetch(a.year); df.to_csv(out,index=False)
    meta={"indicator":"PA.NUS.PPP","year":a.year,"rows":len(df),"source":BASE}
    out.with_suffix(".metadata.json").write_text(json.dumps(meta,indent=2)+"\n")
    print(f"Wrote {len(df)} PPP observations to {out}")
