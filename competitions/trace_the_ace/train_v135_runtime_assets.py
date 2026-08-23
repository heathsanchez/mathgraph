#!/usr/bin/env python3
from pathlib import Path
import argparse,json
import numpy as np
from scipy.sparse import csr_matrix,hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from v75_canonical_trajectory import load_training,trajectory_views,SEED
from v71_mastery_events import load_transcript
from v94_related_control import segmented_control
from v135_nested_supported_stack import prior_apply,feats,fit_stack,ALPHA,EPS

BASE_C=.25

def fit_base_model(X,y): return LogisticRegression(C=BASE_C,max_iter=300,solver='liblinear',random_state=SEED).fit(X,y)
def pred(m,X): return np.clip(m.predict_proba(X)[:,1],EPS,1-EPS)

def main(a):
    f=load_training(a.features,a.labels).reset_index(drop=True); y=f.target.to_numpy(int)
    sessions=f.session_id.astype(str).to_numpy(); support=f.learning_objective.astype(str).to_numpy()
    cache={sid:load_transcript(a.transcripts/f'{sid}.csv') for sid in np.unique(sessions)}
    views=[]; nums=[]; rt=[]; rz=[]
    for i,r in f.iterrows():
        v,n,_=trajectory_views(cache[str(r.session_id)],str(r.learning_objective)); views.append(v); nums.append(n)
        t,z=segmented_control(cache[str(r.session_id)],str(r.learning_objective),'related');rt.append(t);rz.append(z)
        if (i+1)%5000==0: print('ROWS',i+1,flush=True)
    hv75=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    parts=[hv75.transform([f'[OBJECTIVE] {x}' for x in f.learning_objective])]
    for k in views[0].keys(): parts.append(hv75.transform([f'[{k.upper()}] '+v[k] for v in views]))
    N=np.vstack(nums).astype(float); nmean=N.mean(0); nstd=N.std(0)+1e-6; parts.append(csr_matrix((N-nmean)/nstd)); X75=hstack(parts,format='csr')
    hvr=HashingVectorizer(n_features=2**17,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    R=np.vstack(rz).astype(float); rmean=R.mean(0); rstd=R.std(0)+1e-6; Xr=hstack([hvr.transform(rt),csr_matrix((R-rmean)/rstd)],format='csr')
    print('MATRICES',X75.shape,Xr.shape,flush=True)
    # Session-OOF component field for leakage-safe final stack training.
    p75=np.zeros(len(y)); pr=np.zeros(len(y)); pp=np.zeros(len(y)); cc=np.zeros(len(y)); seen=np.zeros(len(y),bool)
    for k,(tr,va) in enumerate(GroupKFold(4).split(np.zeros(len(y)),y,sessions),1):
        m75=fit_base_model(X75[tr],y[tr]); mr=fit_base_model(Xr[tr],y[tr]); p75[va]=pred(m75,X75[va]); pr[va]=pred(mr,Xr[va])
        q,c,s=prior_apply(y,tr,va,support);pp[va]=q;cc[va]=c;seen[va]=s;print('OOF',k,flush=True)
    stack=fit_stack(feats(p75[seen],pr[seen],pp[seen],cc[seen],True),y[seen])
    final75=fit_base_model(X75,y); finalr=fit_base_model(Xr,y)
    global_mean=float(y.mean()); sums={};counts={}
    for k,v in zip(support,y): sums[k]=sums.get(k,0.0)+float(v);counts[k]=counts.get(k,0)+1
    out=Path(a.out);out.mkdir(parents=True,exist_ok=True)
    np.savez_compressed(out/'v135_assets.npz',v75_coef=final75.coef_.ravel(),v75_intercept=final75.intercept_,v75_num_mean=nmean,v75_num_std=nstd,
        related_coef=finalr.coef_.ravel(),related_intercept=finalr.intercept_,related_num_mean=rmean,related_num_std=rstd,
        stack_coef=stack.coef_.ravel(),stack_intercept=stack.intercept_)
    man={'protocol':'V141_V135_RUNTIME_ASSETS','rows':len(y),'base_C':BASE_C,'stack_C':0.10,'prior_alpha':ALPHA,'global_mean':global_mean,
         'objective_counts':counts,'objective_sums':sums,'stack_training':'4-fold session-grouped OOF supported rows only','seed':SEED}
    (out/'manifest.json').write_text(json.dumps(man,indent=2))
    # Save a small exact component fixture for parity checks.
    idx=np.arange(min(512,len(y)))
    np.savez_compressed(out/'parity_fixture.npz',idx=idx,p75=p75[idx],related=pr[idx],prior=pp[idx],count=cc[idx],seen=seen[idx],y=y[idx])
    print(json.dumps({'rows':len(y),'supported_oof':int(seen.sum()),'assets':str(out)},indent=2),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--out',type=Path,required=True);main(p.parse_args())
