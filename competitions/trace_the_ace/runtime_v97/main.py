#!/usr/bin/env python3
"""Official runtime for V97 fixed exact-support gate."""
from pathlib import Path
import json, sys
import numpy as np, pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
HERE=Path(__file__).resolve().parent; DATA=Path('/code_execution/data'); sys.path.insert(0,str(HERE))
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import trajectory_views
from v94_related_control import segmented_control


def sigmoid(x): return 1/(1+np.exp(-np.clip(np.asarray(x,float),-40,40)))
def main():
    f=pd.read_csv(DATA/'test_features.csv'); fmt=pd.read_csv(DATA/'submission_format.csv')
    a=np.load(HERE/'assets/v97_assets.npz'); man=json.loads((HERE/'assets/manifest.json').read_text())
    cache={}; views=[]; vnums=[]; rt=[];rz=[]
    for r in f.itertuples(index=False):
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(DATA/'test_transcripts'/f'{sid}.csv')
        obj=str(r.learning_objective); v,n,_=trajectory_views(cache[sid],obj); views.append(v);vnums.append(n)
        t,z=segmented_control(cache[sid],obj,'related');rt.append(t);rz.append(z)
    hv75=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    Z=(np.vstack(vnums)-a['v75_num_mean'])/a['v75_num_std']
    X0=hstack([hv75.transform(['[OBJECTIVE] '+str(x) for x in f.learning_objective]),
               hv75.transform(['[RAW] '+v['raw'] for v in views]),hv75.transform(['[STUDENT] '+v['student'] for v in views]),
               hv75.transform(['[LOCAL] '+v['local'] for v in views]),hv75.transform(['[STATE] '+v['canonical'] for v in views]),
               hv75.transform(['[TERMINAL] '+v['terminal'] for v in views]),csr_matrix(Z)],format='csr')
    p0=sigmoid(np.asarray(X0@a['v75_coef']).ravel()+float(a['v75_intercept'][0]))
    hvr=HashingVectorizer(n_features=2**17,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    R=(np.vstack(rz)-a['related_num_mean'])/a['related_num_std']; Xr=hstack([hvr.transform(rt),csr_matrix(R)],format='csr')
    pr=sigmoid(np.asarray(Xr@a['related_coef']).ravel()+float(a['related_intercept'][0]))
    keys=f.learning_objective.astype(str); counts=man['objective_counts']
    w=np.array([man['unseen_weight'] if int(counts.get(str(k),0))==0 else 0.0 for k in keys],float)
    p=np.clip((1-w)*p0+w*pr,1e-5,1-1e-5)
    gen=pd.DataFrame({'response_id':f.response_id.astype(str),'probability':p})
    out=fmt[['response_id']].astype({'response_id':str}).merge(gen,on='response_id',how='left',validate='one_to_one')
    if out.probability.isna().any(): raise RuntimeError('missing predictions')
    out.to_csv(HERE/'submission.csv',index=False)
if __name__=='__main__': main()
