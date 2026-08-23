#!/usr/bin/env python3
from __future__ import annotations
from pathlib import Path
import json, os, sys
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer

HERE=Path(__file__).resolve().parent
DATA=Path(os.environ.get('TRACE_ACE_DATA_DIR','/code_execution/data'))
OUTPUT=Path(os.environ.get('TRACE_ACE_OUTPUT','/code_execution/submission.csv'))
sys.path.insert(0,str(HERE))
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import trajectory_views
from v94_related_control import segmented_control

EPS=1e-5

def sigmoid(x):
    return 1/(1+np.exp(-np.clip(np.asarray(x,float),-40,40)))

def logit(p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS)
    return np.log(p/(1-p))

def stack_features(p75,pr,pp,count):
    return np.column_stack([logit(p75),logit(pr),logit(p75)-logit(pr),logit(pp),np.log1p(np.asarray(count,float))])

def predict_components(p75,pr,objectives,assets,manifest):
    counts=manifest['objective_counts']; sums=manifest['objective_sums']; alpha=float(manifest['prior_alpha']); g=float(manifest['global_mean'])
    n=np.asarray([float(counts.get(str(k),0)) for k in objectives],float)
    s=np.asarray([float(sums.get(str(k),0.0)) for k in objectives],float)
    seen=n>0
    pp=np.clip((s+alpha*g)/(n+alpha),EPS,1-EPS)
    q=np.clip(.65*np.asarray(p75)+.35*np.asarray(pr),EPS,1-EPS)
    if np.any(seen):
        X=stack_features(np.asarray(p75)[seen],np.asarray(pr)[seen],pp[seen],n[seen])
        q[seen]=sigmoid(X@assets['stack_coef']+float(assets['stack_intercept'][0]))
    return np.clip(q,EPS,1-EPS),pp,n,seen

def build_base_predictions(frame,transcripts,assets):
    cache={}; views=[]; vnums=[]; rt=[]; rz=[]
    for r in frame.itertuples(index=False):
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(transcripts/f'{sid}.csv')
        obj=str(r.learning_objective)
        v,n,_=trajectory_views(cache[sid],obj); views.append(v); vnums.append(n)
        t,z=segmented_control(cache[sid],obj,'related'); rt.append(t); rz.append(z)
    hv75=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    Z=(np.vstack(vnums)-assets['v75_num_mean'])/assets['v75_num_std']
    X75=hstack([
        hv75.transform(['[OBJECTIVE] '+str(x) for x in frame.learning_objective]),
        hv75.transform(['[RAW] '+v['raw'] for v in views]),
        hv75.transform(['[STUDENT] '+v['student'] for v in views]),
        hv75.transform(['[LOCAL] '+v['local'] for v in views]),
        hv75.transform(['[STATE] '+v['canonical'] for v in views]),
        hv75.transform(['[TERMINAL] '+v['terminal'] for v in views]),
        csr_matrix(Z)],format='csr')
    p75=sigmoid(np.asarray(X75@assets['v75_coef']).ravel()+float(assets['v75_intercept'][0]))
    hvr=HashingVectorizer(n_features=2**17,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    R=(np.vstack(rz)-assets['related_num_mean'])/assets['related_num_std']
    Xr=hstack([hvr.transform(rt),csr_matrix(R)],format='csr')
    pr=sigmoid(np.asarray(Xr@assets['related_coef']).ravel()+float(assets['related_intercept'][0]))
    return p75,pr

def main():
    f=pd.read_csv(DATA/'test_features.csv')
    fmt=pd.read_csv(DATA/'submission_format.csv')
    assets=np.load(HERE/'assets/v135_assets.npz')
    manifest=json.loads((HERE/'assets/manifest.json').read_text())
    p75,pr=build_base_predictions(f,DATA/'test_transcripts',assets)
    p,_,_,_=predict_components(p75,pr,f.learning_objective.astype(str).to_numpy(),assets,manifest)
    gen=pd.DataFrame({'response_id':f.response_id.astype(str),'probability':p})
    out=fmt[['response_id']].astype({'response_id':str}).merge(gen,on='response_id',how='left',validate='one_to_one')
    if len(out)!=len(fmt) or out.probability.isna().any(): raise RuntimeError('output integrity failure')
    if not np.isfinite(out.probability).all() or ((out.probability<0)|(out.probability>1)).any(): raise RuntimeError('invalid probability')
    OUTPUT.parent.mkdir(parents=True,exist_ok=True); out.to_csv(OUTPUT,index=False)

if __name__=='__main__': main()
