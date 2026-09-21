"""Download a pinned EXIOBASE archive from Zenodo and verify its checksum."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import requests

RECORD="15689391"
API=f"https://zenodo.org/api/records/{RECORD}"

def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""): h.update(b)
    return h.hexdigest()

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("--year",type=int,default=2020); ap.add_argument("--format",choices=["ixi","pxp"],default="ixi"); ap.add_argument("--out",default="data/raw/exiobase")
    a=ap.parse_args(); name=f"IOT_{a.year}_{a.format}.zip"; root=Path(a.out); root.mkdir(parents=True,exist_ok=True); dest=root/name
    meta=requests.get(API,timeout=90); meta.raise_for_status(); rec=meta.json()
    f=next((x for x in rec["files"] if x["key"]==name),None)
    if not f: raise SystemExit(f"{name} not present in pinned Zenodo record {RECORD}")
    url=f["links"]["self"]; expected=f.get("checksum","")
    with requests.get(url,stream=True,timeout=120) as r:
        r.raise_for_status()
        with dest.open("wb") as out:
            for chunk in r.iter_content(1024*1024):
                if chunk: out.write(chunk)
    actual_md5=hashlib.md5(dest.read_bytes()).hexdigest()
    if expected.startswith("md5:") and actual_md5 != expected.split(":",1)[1]:
        dest.unlink(missing_ok=True); raise SystemExit("EXIOBASE checksum mismatch")
    manifest={"record":RECORD,"file":name,"url":url,"zenodo_checksum":expected,"sha256":sha256(dest),"bytes":dest.stat().st_size}
    (root/f"{name}.metadata.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print(dest)
