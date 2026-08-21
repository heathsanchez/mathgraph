#!/usr/bin/env python3
"""V130 label-free audit of explicit transcript structural regime markers.

No labels and no fitting. Tests whether the newly surfaced `background` role and
closely related role/timestamp structure form a clean low-cardinality partition
that could correspond to a true data-generation/provider regime. This is a
precondition audit only; it does not claim predictive value.
"""
from __future__ import annotations
import argparse,csv,io,json,zipfile,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np

def sec(s):
    p=str(s).split(':')
    try:return int(p[0])*3600+int(p[1])*60+float(p[2]) if len(p)==3 else np.nan
    except:return np.nan

def main(a):
    with zipfile.ZipFile(a.archive) as z:
        members=sorted(n for n in z.namelist() if n.endswith('.csv'))
        sig=Counter(); bg_counts=Counter(); first_roles=Counter(); role_seq=Counter(); bg_text_hash=Counter(); durations=[]; rows_total=[]
        examples=defaultdict(list)
        for n in members:
            with z.open(n) as f: rows=list(csv.DictReader(io.TextIOWrapper(f,encoding='utf-8-sig',newline='')))
            roles=[str(r.get('role','')).lower() for r in rows]
            bg=[str(r.get('content','')) for r in rows if str(r.get('role','')).lower()=='background']
            bgc=len(bg); bg_counts[bgc]+=1; first=roles[0] if roles else ''; first_roles[first]+=1
            seq='>'.join(roles[:8]); role_seq[seq]+=1
            t=[sec(r.get('timestamp','')) for r in rows]; t=[x for x in t if np.isfinite(x)]
            dur=max(0,t[-1]-t[0]) if len(t)>=2 else 0
            durations.append(dur); rows_total.append(len(rows))
            # Frozen low-cardinality structural signature; no lexical contents except existence/count.
            s=(int(bgc>0), min(bgc,3), first, int(roles[-1]=='background') if roles else 0,
               min(sum(r=='tutor' for r in roles)//10,9), min(sum(r=='student' for r in roles)//10,9),
               min(len(rows)//20,9), min(int(dur)//300,9))
            sig[s]+=1
            if len(examples[s])<3: examples[s].append(n)
            for b in bg:
                # audit repeated templates only, not semantics
                norm=' '.join(b.lower().split())
                bg_text_hash[hashlib.sha256(norm.encode()).hexdigest()[:12]]+=1
        total=len(members)
        top=sig.most_common(30)
        out={'protocol':'V130_BACKGROUND_REGIME_AUDIT','sessions':total,
             'background_count_distribution':bg_counts.most_common(),
             'background_presence_fraction':float(sum(v for k,v in bg_counts.items() if k>0)/max(1,total)),
             'first_role_distribution':first_roles.most_common(),
             'top_role_prefixes':role_seq.most_common(20),
             'structural_signature_count':len(sig),
             'top_structural_signatures':[{'signature':list(k),'count':v,'fraction':v/total,'examples':examples[k]} for k,v in top],
             'top_background_template_hash_counts':bg_text_hash.most_common(20),
             'duration_quantiles_seconds':{str(q):float(np.quantile(durations,q)) for q in [0,.1,.25,.5,.75,.9,1]},
             'row_count_quantiles':{str(q):float(np.quantile(rows_total,q)) for q in [0,.1,.25,.5,.75,.9,1]},
             'decision':{}}
        p=out['background_presence_fraction']; top2=sum(v for _,v in sig.most_common(2))/max(1,total)
        if .1<=p<=.9 and top2>=.7:
            verdict='CANDIDATE_EXPLICIT_STRUCTURAL_REGIME'
        elif .05<=p<=.95:
            verdict='BACKGROUND_MARKER_PRESENT_BUT_NOT_CLEAN_REGIME'
        else:
            verdict='NO_BALANCED_BACKGROUND_REGIME'
        out['decision']={'verdict':verdict,'top2_signature_coverage':top2,'labels_used':False}
        Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--archive',required=True); p.add_argument('--out',required=True); main(p.parse_args())
