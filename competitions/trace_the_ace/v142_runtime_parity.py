#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os,shutil,subprocess,sys
from pathlib import Path
import numpy as np,pandas as pd
from scipy.sparse import csr_matrix,hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import log_loss
from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training,trajectory_views
from v94_related_control import segmented_control

EPS=1e-5

def sig(x): return 1/(1+np.exp(-np.clip(np.asarray(x,float),-40,40)))
def logit(p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS); return np.log(p/(1-p))

def reference(frame,tdir,a,m):
    cache={};views=[];nums=[];rt=[];rz=[]
    for r in frame.itertuples(index=False):
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(tdir/f'{sid}.csv')
        obj=str(r.learning_objective);v,n,_=trajectory_views(cache[sid],obj);views.append(v);nums.append(n)
        t,z=segmented_control(cache[sid],obj,'related');rt.append(t);rz.append(z)
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    Z=(np.vstack(nums)-a['v75_num_mean'])/a['v75_num_std']
    X=hstack([hv.transform(['[OBJECTIVE] '+str(x) for x in frame.learning_objective]),hv.transform(['[RAW] '+v['raw'] for v in views]),hv.transform(['[STUDENT] '+v['student'] for v in views]),hv.transform(['[LOCAL] '+v['local'] for v in views]),hv.transform(['[STATE] '+v['canonical'] for v in views]),hv.transform(['[TERMINAL] '+v['terminal'] for v in views]),csr_matrix(Z)],format='csr')
    p75=sig(np.asarray(X@a['v75_coef']).ravel()+float(a['v75_intercept'][0]))
    hvr=HashingVectorizer(n_features=2**17,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    R=(np.vstack(rz)-a['related_num_mean'])/a['related_num_std'];Xr=hstack([hvr.transform(rt),csr_matrix(R)],format='csr')
    pr=sig(np.asarray(Xr@a['related_coef']).ravel()+float(a['related_intercept'][0]))
    obj=frame.learning_objective.astype(str).to_numpy();counts=m['objective_counts'];sums=m['objective_sums'];alpha=float(m['prior_alpha']);g=float(m['global_mean'])
    c=np.array([counts.get(x,0) for x in obj],float);s=np.array([sums.get(x,0.0) for x in obj],float);seen=c>0;pp=np.clip((s+alpha*g)/(c+alpha),EPS,1-EPS)
    q=np.clip(.65*p75+.35*pr,EPS,1-EPS)
    F=np.column_stack([logit(p75),logit(pr),logit(p75)-logit(pr),logit(pp),np.log1p(c)])
    q[seen]=sig(F[seen]@a['stack_coef']+float(a['stack_intercept'][0]));return np.clip(q,EPS,1-EPS)

def invoke(runtime,data,out):
    env=os.environ.copy();env['TRACE_ACE_DATA_DIR']=str(data);env['TRACE_ACE_OUTPUT']=str(out)
    subprocess.run([sys.executable,str(runtime/'main.py')],check=True,env=env,cwd=runtime)
    return pd.read_csv(out).probability.to_numpy(float)

def main(args):
    out=Path(args.out);out.mkdir(parents=True,exist_ok=True); runtime=Path(args.runtime); assets=runtime/'assets'
    a=np.load(assets/'v135_assets.npz');m=json.loads((assets/'manifest.json').read_text())
    full=load_training(args.features,args.labels).reset_index(drop=True); n=min(args.rows,len(full)); frame=full.iloc[:n].copy().reset_index(drop=True)
    ref=reference(frame,args.transcripts,a,m)
    data=out/'pseudo_data';(data/'test_transcripts').mkdir(parents=True,exist_ok=True)
    cols=['response_id','session_id','learning_objective_id','learning_objective']; frame[cols].to_csv(data/'test_features.csv',index=False);frame[['response_id']].to_csv(data/'submission_format.csv',index=False)
    for sid in frame.session_id.astype(str).unique(): shutil.copy2(args.transcripts/f'{sid}.csv',data/'test_transcripts'/f'{sid}.csv')
    pred=invoke(runtime,data,out/'submission.csv'); d=float(np.max(np.abs(pred-ref)))
    # sample-independence: same first row alone vs inside/reordered small batch
    k=min(32,n); small=frame.iloc[:k].copy(); sd=out/'meta_data';(sd/'test_transcripts').mkdir(parents=True,exist_ok=True)
    for sid in small.session_id.astype(str).unique(): shutil.copy2(args.transcripts/f'{sid}.csv',sd/'test_transcripts'/f'{sid}.csv')
    small[cols].iloc[::-1].to_csv(sd/'test_features.csv',index=False);small[['response_id']].iloc[::-1].to_csv(sd/'submission_format.csv',index=False); p_rev=invoke(runtime,sd,out/'rev.csv')
    one=small.iloc[[0]]; one[cols].to_csv(sd/'test_features.csv',index=False);one[['response_id']].to_csv(sd/'submission_format.csv',index=False); p_one=invoke(runtime,sd,out/'one.csv')[0]
    rev_ids=small.response_id.astype(str).iloc[::-1].tolist(); p_in=float(p_rev[rev_ids.index(str(small.response_id.iloc[0]))]); meta_diff=abs(p_one-p_in)
    y=frame.target.to_numpy(int); result={'protocol':'V142_RUNTIME_PARITY','rows':n,'max_abs_runtime_reference_diff':d,'heldout_logloss':float(log_loss(y,pred,labels=[0,1])),'sample_independence_diff':float(meta_diff),'parity_pass':bool(d<1e-8),'sample_independence_pass':bool(meta_diff<1e-12)}
    (out/'v142_runtime_parity.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
    if not result['parity_pass'] or not result['sample_independence_pass']: raise SystemExit(2)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--runtime',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--rows',type=int,default=512);main(p.parse_args())
