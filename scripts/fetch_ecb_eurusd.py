"""Fetch ECB annual EUR/USD reference rate through the ECB Data API."""
from __future__ import annotations
import argparse,csv,io,json
from pathlib import Path
import requests

URL="https://data-api.ecb.europa.eu/service/data/EXR/A.USD.EUR.SP00.A"

def fetch(year):
    r=requests.get(URL,params={"startPeriod":year,"endPeriod":year,"format":"csvdata"},timeout=60)
    r.raise_for_status()
    rows=list(csv.DictReader(io.StringIO(r.text)))
    if not rows: raise RuntimeError(f"No ECB EUR/USD annual observation for {year}")
    # OBS_VALUE is USD per EUR for EXR.A.USD.EUR.SP00.A.
    return float(rows[-1]["OBS_VALUE"])

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,default=2021); ap.add_argument("--out",default="data/external/ecb")
    a=ap.parse_args(); root=Path(a.out); root.mkdir(parents=True,exist_ok=True)
    value=fetch(a.year)
    (root/f"eur_usd_{a.year}.json").write_text(json.dumps({"year":a.year,"usd_per_eur":value,"series":"EXR.A.USD.EUR.SP00.A","source":URL},indent=2)+"\n")
    print(value)
