from __future__ import annotations
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def predict(model, objectives):
    obj=[str(x) for x in objectives]
    B=model['vectorizer'].transform(obj)
    sims=cosine_similarity(B,model['A'])
    kk=min(int(model['k']),sims.shape[1])
    idx=np.argpartition(-sims,kth=kk-1,axis=1)[:,:kk]
    rows=np.arange(len(obj))[:,None]
    w=sims[rows,idx]
    npv=model['posterior'][idx]
    sem=(w*npv).sum(axis=1)/(w.sum(axis=1)+1e-9)
    sem=np.where(w.sum(axis=1)>1e-8,sem,float(model['global_p']))
    mp=model['mapped']; ct=model['counts']
    mapped=np.array([mp.get(x,np.nan) for x in obj],float)
    missing=np.isnan(mapped); mapped[missing]=sem[missing]
    counts=np.array([ct.get(x,0.0) for x in obj],float)
    trust=counts/(counts+10.0)
    p=trust*mapped+(1-trust)*sem
    return np.clip(p,1e-5,1-1e-5)
