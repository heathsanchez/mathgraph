#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,hashlib,joblib
from pathlib import Path
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import GroupKFold
from v74_semantic_objective_prior import load_training,semantic_prior_predict
from runtime_v74.v74_runtime_core import predict

def fit_model(df,k=16,smooth=2.0):
    global_p=float(df.target.mean())
    stats=df.groupby('learning_objective').target.agg(['sum','count'])
    stats['p']=(stats['sum']+smooth*global_p)/(stats['count']+smooth)
    objs=stats.index.astype(str).tolist()
    vec=TfidfVectorizer(analyzer='char_wb',ngram_range=(3,5),min_df=1,sublinear_tf=True,norm='l2')
    A=vec.fit_transform(objs)
    return {'k':k,'smooth':smooth,'global_p':global_p,'vectorizer':vec,'A':A,'posterior':stats['p'].to_numpy(float),'mapped':{str(k):float(v) for k,v in stats['p'].items()},'counts':{str(k):float(v) for k,v in stats['count'].items()}}

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main(a):
    f=load_training(a.features,a.labels).reset_index(drop=True)
    y=f.target.to_numpy(int); sess=f.session_id.astype(str).to_numpy()
    tr,va=next(iter(GroupKFold(5).split(np.zeros(len(y)),y,sess)))
    ref,_=semantic_prior_predict(f.iloc[tr],f.iloc[va],k=16,smooth=2.0)
    m=fit_model(f.iloc[tr]); got=predict(m,f.iloc[va].learning_objective.astype(str).tolist())
    md=float(np.max(np.abs(ref-got)))
    if md>=1e-8: raise RuntimeError(f'parity failed {md}')
    a.assets.mkdir(parents=True,exist_ok=True)
    model=fit_model(f); mp=a.assets/'v74_model.joblib'; joblib.dump(model,mp,compress=3)
    manifest={'candidate':'V74_PURE_HIERARCHICAL_OBJECTIVE_PRIOR','k':16,'smooth':2.0,'trust_denominator':10.0,'v115b_session_cold':0.5511484894117864,'v115b_objective_cold_stress':0.6013242442331039,'v115b_exact_support_rate':0.9975193886861314,'parity_max_abs_diff':md,'model_sha256':sha(mp)}
    (a.assets/'manifest.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--assets',type=Path,required=True);main(p.parse_args())
