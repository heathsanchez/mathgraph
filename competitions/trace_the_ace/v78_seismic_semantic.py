#!/usr/bin/env python3
"""V78 seismic test: pretrained semantic interaction + learned episode mastery + V75 ensemble.

Tests three model-class shifts under identical frozen group folds:
1) objective<->dialogue pretrained semantic interaction;
2) learned episode/trajectory mastery from semantic episode views;
3) nested-safe convex ensemble with the sparse V75 all-views model.

Development-time model: sentence-transformers/all-MiniLM-L6-v2 (open, and preloaded in official runtime).
Only aggregate metrics are written.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler
from sentence_transformers import SentenceTransformer

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training, trajectory_views, SEED


def folds(groups, n=5):
    g=groups.astype(str).to_numpy(); z=np.zeros(len(g))
    return list(GroupKFold(n_splits=n).split(z,z,g))

def sigmoid(x):
    x=np.asarray(x,float); return 1/(1+np.exp(-np.clip(x,-40,40)))

def encode(model, texts, batch=128):
    return model.encode(texts,batch_size=batch,show_progress_bar=True,normalize_embeddings=True,convert_to_numpy=True).astype(np.float32)

def dense_semantic_features(Eo, Es, El, Et, numeric):
    # Explicit cross-view interaction features, not just independent embeddings.
    cos_os=np.sum(Eo*Es,1,keepdims=True); cos_ol=np.sum(Eo*El,1,keepdims=True); cos_ot=np.sum(Eo*Et,1,keepdims=True)
    cos_sl=np.sum(Es*El,1,keepdims=True); cos_lt=np.sum(El*Et,1,keepdims=True)
    # Pairwise products preserve dimensions while explicitly representing relevance/alignment.
    prod_ol=Eo*El; prod_ot=Eo*Et
    return np.hstack([Eo,Es,El,Et,prod_ol,prod_ot,cos_os,cos_ol,cos_ot,cos_sl,cos_lt,numeric]).astype(np.float32)

def build_v75_sparse(frame, view_rows, numeric):
    hv=HashingVectorizer(n_features=2**18,alternate_sign=False,norm='l2',ngram_range=(1,2),lowercase=True)
    obj=hv.transform(['[OBJECTIVE] '+str(x) for x in frame.learning_objective])
    raw=hv.transform(['[RAW] '+v['raw'] for v in view_rows])
    stu=hv.transform(['[STUDENT] '+v['student'] for v in view_rows])
    loc=hv.transform(['[LOCAL] '+v['local'] for v in view_rows])
    can=hv.transform(['[STATE] '+v['canonical'] for v in view_rows])
    ter=hv.transform(['[TERMINAL] '+v['terminal'] for v in view_rows])
    z=(numeric-numeric.mean(0))/(numeric.std(0)+1e-6)
    return hstack([obj,raw,stu,loc,can,ter,csr_matrix(z)],format='csr')

def eval_regime(Xv75, Xsem, y, split, name):
    p75=np.zeros(len(y)); psem=np.zeros(len(y)); fold_rows=[]
    for k,(tr,va) in enumerate(split,1):
        m75=LogisticRegression(C=.25,max_iter=300,solver='liblinear',random_state=SEED).fit(Xv75[tr],y[tr])
        a=np.clip(m75.predict_proba(Xv75[va])[:,1],1e-5,1-1e-5); p75[va]=a
        sc=StandardScaler().fit(Xsem[tr]); A=sc.transform(Xsem[tr]); B=sc.transform(Xsem[va])
        ms=LogisticRegression(C=.05,max_iter=500,solver='liblinear',random_state=SEED).fit(A,y[tr])
        b=np.clip(ms.predict_proba(B)[:,1],1e-5,1-1e-5); psem[va]=b
        fold_rows.append({'fold':k,'rows':len(va),'v75':float(log_loss(y[va],a)),'semantic':float(log_loss(y[va],b))})
        print(name,fold_rows[-1])
    # Blend selected globally from OOF only; report grid transparently. This is model comparison, not final stacking fit.
    grid=[]; best=None
    for w in np.linspace(0,1,21):
        p=np.clip((1-w)*p75+w*psem,1e-5,1-1e-5); ll=float(log_loss(y,p))
        row={'semantic_weight':float(w),'logloss':ll}; grid.append(row)
        if best is None or ll<best['logloss']: best=row
    pb=np.clip((1-best['semantic_weight'])*p75+best['semantic_weight']*psem,1e-5,1-1e-5)
    return {'v75_logloss':float(log_loss(y,p75)),'semantic_logloss':float(log_loss(y,psem)),'best_blend':best,'blend_auc':float(roc_auc_score(y,pb)),'folds':fold_rows,'blend_grid':grid}

def run(args):
    frame=load_training(args.features,args.labels).reset_index(drop=True)
    if args.limit: frame=frame.iloc[:args.limit].copy().reset_index(drop=True)
    cache={}; views=[]; nums=[]
    for i,r in frame.iterrows():
        sid=str(r.session_id)
        if sid not in cache: cache[sid]=load_transcript(args.transcripts/f'{sid}.csv')
        v,n,_=trajectory_views(cache[sid],str(r.learning_objective)); views.append(v); nums.append(n)
        if (i+1)%2500==0: print('views',i+1)
    numeric=np.vstack(nums).astype(np.float32)
    numz=(numeric-numeric.mean(0))/(numeric.std(0)+1e-6)
    model=SentenceTransformer(args.model)
    Eo=encode(model,[str(x) for x in frame.learning_objective],args.batch)
    Es=encode(model,[v['student'] or ' ' for v in views],args.batch)
    El=encode(model,[v['local'] or ' ' for v in views],args.batch)
    Et=encode(model,[v['terminal'] or ' ' for v in views],args.batch)
    Xsem=dense_semantic_features(Eo,Es,El,Et,numz)
    X75=build_v75_sparse(frame,views,numeric)
    y=frame.target.to_numpy(int)
    objgrp=frame.learning_objective_id if 'learning_objective_id' in frame else frame.learning_objective
    result={
      'diagnostics':{'rows':len(frame),'sessions':int(frame.session_id.nunique()),'objectives':int(frame.learning_objective.nunique()),'embedding_dim':int(Eo.shape[1]),'semantic_features':int(Xsem.shape[1]),'model':args.model},
      'session':eval_regime(X75,Xsem,y,folds(frame.session_id),'session'),
      'objective':eval_regime(X75,Xsem,y,folds(objgrp),'objective'),
    }
    Path(args.out).write_text(json.dumps(result,indent=2)); print(json.dumps(result,indent=2))

def parse():
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v78_seismic_semantic.json'); p.add_argument('--model',default='sentence-transformers/all-MiniLM-L6-v2'); p.add_argument('--batch',type=int,default=128); p.add_argument('--limit',type=int,default=0); return p.parse_args()
if __name__=='__main__': run(parse())
