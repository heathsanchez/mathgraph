#!/usr/bin/env python3
"""V122 — metadata-only ID morphology regime audit.

Question: do session/objective identifier string patterns encode a stable provider / assessment-process
regime that could explain leaderboard behavior? This is deliberately metadata-only and fast.

Frozen protocol:
- inspect headers first
- join train features/labels by response_id
- evaluate char-ngram morphology of session_id, learning_objective_id, and both together
- two untouched geometries: GroupKFold by session_id and GroupKFold by learning_objective_id
- compare against intercept-only fold baseline
- shuffled-label control with same folds
- promotion only if a real ID family gains >= .003 log loss in BOTH geometries and exceeds shuffle by >= .002
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GroupKFold
from sklearn.metrics import log_loss

EPS=1e-5
SEED=20260818

def fold_intercept(ytr,n):
    p=float(np.clip(np.mean(ytr),EPS,1-EPS)); return np.full(n,p,float)

def oof(texts,y,groups):
    q=np.zeros(len(y),float); b=np.zeros(len(y),float)
    hv=HashingVectorizer(analyzer='char',ngram_range=(2,5),n_features=2**15,alternate_sign=False,norm='l2',lowercase=False)
    X=hv.transform(texts)
    k=min(5,len(np.unique(groups)))
    for tr,va in GroupKFold(k).split(X,y,groups):
        b[va]=fold_intercept(y[tr],len(va))
        m=LogisticRegression(C=.15,max_iter=220,solver='liblinear',random_state=SEED)
        m.fit(X[tr],y[tr]); q[va]=m.predict_proba(X[va])[:,1]
    return float(log_loss(y,np.clip(q,EPS,1-EPS))), float(log_loss(y,np.clip(b,EPS,1-EPS)))

def run(a):
    print('train_features headers',list(pd.read_csv(a.features,nrows=0).columns),flush=True)
    print('train_labels headers',list(pd.read_csv(a.labels,nrows=0).columns),flush=True)
    f=pd.read_csv(a.features); l=pd.read_csv(a.labels)
    f=f.merge(l,on='response_id',how='inner',validate='one_to_one')
    y=f.is_correct.to_numpy(int)
    sess=f.session_id.astype(str).to_numpy(); oid=f.learning_objective_id.astype(str).to_numpy()
    families={
      'SESSION_ID':np.array(['S:'+x for x in sess],object),
      'OBJECTIVE_ID':np.array(['O:'+x for x in oid],object),
      'SESSION_X_OBJECTIVE':np.array(['S:'+s+'|O:'+o for s,o in zip(sess,oid)],object),
    }
    geoms={'session_cold':sess,'objective_cold':oid}
    rng=np.random.default_rng(SEED); ys=y.copy(); rng.shuffle(ys)
    out={'rows':int(len(f)),'sessions':int(len(np.unique(sess))),'objectives':int(len(np.unique(oid))), 'families':{}, 'shuffle':{}}
    gains=[]
    for name,txt in families.items():
        out['families'][name]={}
        out['shuffle'][name]={}
        for gname,g in geoms.items():
            ll,base=oof(txt,y,g); sll,sbase=oof(txt,ys,g)
            gain=base-ll; sgain=sbase-sll
            out['families'][name][gname]={'ll':ll,'baseline_ll':base,'gain':gain}
            out['shuffle'][name][gname]={'gain':sgain}
        g1=out['families'][name]['session_cold']['gain']; g2=out['families'][name]['objective_cold']['gain']
        sh=max(out['shuffle'][name]['session_cold']['gain'],out['shuffle'][name]['objective_cold']['gain'])
        gains.append((min(g1,g2)-sh,name,g1,g2,sh))
    gains.sort(reverse=True)
    margin,name,g1,g2,sh=gains[0]
    promote=(g1>=.003 and g2>=.003 and min(g1,g2)-sh>=.002)
    out['decision']={'winner':name,'session_gain':g1,'objective_gain':g2,'max_shuffle_gain':sh,'margin':margin,
      'verdict':'ID_REGIME_SIGNAL' if promote else 'ID_MORPHOLOGY_NOT_DECISION_CHANGING',
      'rule':'Promote only if >=.003 gain in both geometries and >=.002 above shuffled control.'}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--out',default='v122_id_morphology_regime_audit.json'); run(p.parse_args())
