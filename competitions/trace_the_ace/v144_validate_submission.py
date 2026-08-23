#!/usr/bin/env python3
from __future__ import annotations
import argparse,csv,json,math
from pathlib import Path

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--format',required=True)
    ap.add_argument('--submission',required=True)
    ap.add_argument('--tag',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    with open(a.format,newline='') as f: fmt=list(csv.DictReader(f))
    with open(a.submission,newline='') as f:
        r=csv.DictReader(f)
        assert r.fieldnames==['response_id','probability'],r.fieldnames
        out=list(r)
    assert len(out)==len(fmt),(len(out),len(fmt))
    assert [str(x['response_id']) for x in out]==[str(x['response_id']) for x in fmt]
    p=[float(x['probability']) for x in out]
    assert all(math.isfinite(x) and 0.0<=x<=1.0 for x in p)
    result={'tag':a.tag,'rows':len(out),'p_min':min(p),'p_max':max(p),'p_mean':sum(p)/len(p)}
    Path(a.out).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__': main()
