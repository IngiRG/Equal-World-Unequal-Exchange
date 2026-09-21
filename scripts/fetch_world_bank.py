"""Fetch PPP and country labor-productivity series from World Bank WDI."""
from __future__ import annotations
import argparse, json
from pathlib import Path
import pandas as pd, requests

API="https://api.worldbank.org/v2/country/all/indicator/{indicator}"
INDICATORS={"ppp":"PA.NUS.PPP","productivity":"SL.GDP.PCAP.EM.KD"}

def fetch(indicator,year):
    r=requests.get(API.format(indicator=indicator),params={"format":"json","date":year,"per_page":400},timeout=90)
    r.raise_for_status(); payload=r.json()
    rows=[]
    for x in payload[1]:
        if x.get("value") is not None and x.get("countryiso3code"):
            rows.append({"iso3":x["countryiso3code"],"country":x["country"]["value"],"year":int(x["date"]),"value":float(x["value"])})
    return pd.DataFrame(rows)

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,default=2020); ap.add_argument("--out",default="data/external/world_bank")
    a=ap.parse_args(); root=Path(a.out); root.mkdir(parents=True,exist_ok=True)
    for name,indicator in INDICATORS.items():
        df=fetch(indicator,a.year); df.to_csv(root/f"{name}_{a.year}.csv",index=False)
        (root/f"{name}_{a.year}.metadata.json").write_text(json.dumps({"indicator":indicator,"year":a.year,"rows":len(df),"api":API.format(indicator=indicator)},indent=2)+"\n")
        print(name,len(df))
