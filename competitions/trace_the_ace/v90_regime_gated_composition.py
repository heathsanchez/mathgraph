#!/usr/bin/env python3
"""V90: R5 applicability separator for V88 composition.

Hypothesis: the globally useful V75/EvidenceEvent blend averages over latent
session regimes. Learn regime membership from sample-local transcript style only,
then tune V75/Evidence weights per regime using training folds only.
"""
from __future__ import annotations
import argparse,json,re
from pathlib import Path
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import log_loss
from sklearn.model_selection import GroupKFold
from sklearn.preprocessing import StandardScaler

from v71_mastery_events import load_transcript
from v75_canonical_trajectory import load_training
from v81_target_segment_phase import choose_target_segment, split_segments
from v85_evidence_state import evidence_events,render,nums,build_sparse,build_v75,oof


def style_features(df):
    roles=df.role.astype(str).str.lower().tolist(); text=df.content.fillna('').astype(str).tolist(); n=max(1,len(df))
    stu=[t for r,t in zip(roles,text) if r=='student']; tut=[t for r,t in zip(roles,text) if r=='tutor']
    sl=[len(x.split()) for x in stu] or [0]; tl=[len(x.split()) for x in tut] or [0]
    math=sum(bool(re.search(r'\d|[=+\-*/%]',x)) for x in text)/n
    q=sum('?' in x for x in tut)/max(1,len(tut))
    praise=sum(bool(re.search(r'\b(?:great|correct|right|well done|brilliant|perfect)\b',x,re.I)) for x in tut)/max(1,len(tut))
    markers=sum(bool(re.search(r'\b(?:learning objective|learning goal|i do|we do|you do|application|prior learning)\b',x,re.I)) for x in tut)/max(1,len(tut))
    return np.asarray([len(df),len(stu)/n,len(tut)/n,np.mean(sl),np.mean(tl),np.median(sl),np.median(tl),math,q,praise,markers,len(split_segments(df))],float)


def run(a):
    f=load_training(a.features,a.labels).reset_index(drop=True); cache={}
    for sid in f.session_id.astype(str).unique(): cache[sid]=load_transcript(a.transcripts/f'{sid}.csv')
    et=[]; ez=[]; S=[]
    for i,r in f.iterrows():
        d=cache[str(r.session_id)]; obj=str(r.learning_objective); seg,_=choose_target_segment(d,obj); ev=evidence_events(seg,obj)
        et.append(render(ev,obj,ablate=True)); ez.append(nums(ev,ablate=True)); S.append(style_features(d))
        if (i+1)%2500==0: print('rows',i+1)
    S=np.vstack(S); y=f.target.to_numpy(int); groups=(f.learning_objective_id if 'learning_objective_id' in f else f.learning_objective).astype(str).to_numpy()
    sp=list(GroupKFold(5).split(np.zeros(len(y)),y,groups)); fold=np.empty(len(y),int)
    for k,(_,va) in enumerate(sp): fold[va]=k
    p0,_=oof(build_v75(f,cache),y,sp,'V75'); pe,_=oof(build_sparse(et,ez,'EVIDENCE_ABL'),y,sp,'EVIDENCE')
    global_q=np.zeros(len(y)); gated_q=np.zeros(len(y)); selected=[]; grid=np.linspace(0,0.8,33)
    for k,(_,va) in enumerate(sp):
        tune=np.where(fold!=k)[0]
        # global cross-fitted reference
        bg=min(((float(log_loss(y[tune],np.clip((1-w)*p0[tune]+w*pe[tune],1e-5,1-1e-5))),float(w)) for w in grid),key=lambda x:x[0])
        global_q[va]=np.clip((1-bg[1])*p0[va]+bg[1]*pe[va],1e-5,1-1e-5)
        sc=StandardScaler().fit(S[tune]); Xt=sc.transform(S[tune]); Xv=sc.transform(S[va])
        best=None
        for K in (2,3,4,5):
            km=KMeans(n_clusters=K,random_state=20260816,n_init=20).fit(Xt); rt=km.labels_; rv=km.predict(Xv)
            weights={}; total=0.0; ok=True
            for r in range(K):
                idx=tune[rt==r]
                if len(idx)<500: ok=False; break
                b=min(((float(log_loss(y[idx],np.clip((1-w)*p0[idx]+w*pe[idx],1e-5,1-1e-5))),float(w)) for w in grid),key=lambda x:x[0])
                weights[r]=b[1]; total += b[0]*len(idx)
            if not ok: continue
            total/=len(tune)
            if best is None or total<best['tune_logloss']: best={'K':K,'weights':weights,'tune_logloss':total,'km':km,'rv':rv}
        if best is None:
            gated_q[va]=global_q[va]; rec={'fold':k+1,'K':1,'weights':{'0':bg[1]},'fallback':True}
        else:
            for j,ix in enumerate(va):
                w=best['weights'][int(best['rv'][j])]; gated_q[ix]=np.clip((1-w)*p0[ix]+w*pe[ix],1e-5,1-1e-5)
            rec={'fold':k+1,'K':best['K'],'weights':{str(r):float(w) for r,w in best['weights'].items()},'fallback':False}
        rec['heldout_logloss']=float(log_loss(y[va],gated_q[va])); selected.append(rec); print(rec)
    ll0=float(log_loss(y,p0)); llg=float(log_loss(y,global_q)); llr=float(log_loss(y,gated_q))
    out={'primary':'objective-cold-crossfitted','v75':ll0,'global_crossfit':llg,'regime_gated':llr,
         'gain_vs_v75':ll0-llr,'gain_vs_global':llg-llr,'selected_by_fold':selected,
         'decision':'R5_SEPARATOR_FOUND' if llg-llr>=.0015 else ('R5_WEAK' if llg-llr>=.0005 else 'R5_REJECT_STYLE_REGIMES')}
    Path(a.out).write_text(json.dumps(out,indent=2)); print(json.dumps(out,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--features',type=Path,required=True); p.add_argument('--labels',type=Path,required=True); p.add_argument('--transcripts',type=Path,required=True); p.add_argument('--out',default='v90_regime_gated.json'); run(p.parse_args())
