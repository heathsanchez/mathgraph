#!/usr/bin/env python3
"""V118 hidden test geometry probe.

Frozen historical probe table supplied by actual DrivenData submissions on 2026-08-18.
Question: does smoke rank candidates like public, and what does V74 smoke imply?
No competition labels are used; only user-observed submission scores.
"""
import json
from pathlib import Path
import numpy as np
from scipy.stats import spearmanr, pearsonr

PROBES = [
    ("V37", 0.4801, 0.7384),
    ("V48", 0.5052, 0.6179),
    ("V54", 0.5192, 0.6329),
    ("V57", 0.5216, 0.6211),
    ("V63", 0.4880, 0.6284),
    ("V75", 0.4693, 0.6047),
    ("V97", 0.4693, 0.6044),
]
V74_SMOKE = 0.5181
V74_SESSION = 0.5511484894117864
V74_OBJECTIVE = 0.6013242442331039

def metrics(rows):
    s=np.array([r[1] for r in rows],float); p=np.array([r[2] for r in rows],float)
    sp=spearmanr(s,p); pe=pearsonr(s,p)
    b,a=np.polyfit(s,p,1)
    pred=float(a+b*V74_SMOKE)
    return {"n":len(rows),"spearman":float(sp.statistic),"spearman_p":float(sp.pvalue),"pearson":float(pe.statistic),"pearson_p":float(pe.pvalue),"ols_intercept":float(a),"ols_slope":float(b),"v74_public_projection":pred}

def main():
    allm=metrics(PROBES)
    loo=[]
    for i,r in enumerate(PROBES):
        m=metrics(PROBES[:i]+PROBES[i+1:]); loo.append({"excluded":r[0],**m})
    best=max(loo,key=lambda x:x["spearman"])
    nonout=[r for r in PROBES if r[0]!=best["excluded"]]
    robust=metrics(nonout)
    # Ranking only: lower score is better.
    smoke_order=[r[0] for r in sorted(PROBES,key=lambda r:r[1])]
    public_order=[r[0] for r in sorted(PROBES,key=lambda r:r[2])]
    out={
      "probe_table":[{"model":m,"smoke":s,"public":p} for m,s,p in PROBES],
      "v74":{"smoke":V74_SMOKE,"session_cold":V74_SESSION,"objective_cold":V74_OBJECTIVE},
      "all_probes":allm,
      "leave_one_out":loo,
      "most_influential_outlier":best["excluded"],
      "robust_without_outlier":robust,
      "smoke_rank":smoke_order,
      "public_rank":public_order,
    }
    # Precommit: smoke is not an adequate optimization target if rank rho < .8 or if one probe changes rho by >= .2.
    influence=best["spearman"]-allm["spearman"]
    if allm["spearman"]<0.8 or influence>=0.2:
        verdict="SMOKE_NOT_PUBLIC_PROXY"
    else:
        verdict="SMOKE_USABLE_PUBLIC_PROXY"
    # A V74 full submission is suppressed if robust smoke->public projection is >= current V97 public 0.6044.
    v74_decision="SUPPRESS_V74_FULL" if robust["v74_public_projection"]>=0.6044 else "V74_FULL_STILL_PLAUSIBLE"
    out["decision"]={
      "verdict":verdict,
      "outlier_influence_on_spearman":float(influence),
      "v74_decision":v74_decision,
      "rule":"Smoke proxy requires Spearman >=0.8 and no single-probe rho improvement >=0.2. Suppress V74 full if robust smoke->public projection is not better than V97 public 0.6044.",
      "next":"Infer public-aligned validation geometry from historical candidate response vectors; do not optimize smoke directly." if verdict=="SMOKE_NOT_PUBLIC_PROXY" else "Use smoke as a secondary ranking probe."
    }
    Path("v118_hidden_test_geometry_probe.json").write_text(json.dumps(out,indent=2))
    print(json.dumps(out,indent=2))
if __name__=="__main__": main()
