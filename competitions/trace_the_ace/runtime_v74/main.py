#!/usr/bin/env python3
from pathlib import Path
import joblib,pandas as pd
HERE=Path(__file__).resolve().parent
DATA=Path('/code_execution/data')
from v74_runtime_core import predict

def main():
    f=pd.read_csv(DATA/'test_features.csv')
    fmt=pd.read_csv(DATA/'submission_format.csv')
    model=joblib.load(HERE/'assets/v74_model.joblib')
    p=predict(model,f.learning_objective.astype(str).tolist())
    gen=pd.DataFrame({'response_id':f.response_id.astype(str),'probability':p})
    out=fmt[['response_id']].astype({'response_id':str}).merge(gen,on='response_id',how='left',validate='one_to_one')
    if out.probability.isna().any(): raise RuntimeError('missing predictions')
    if not ((out.probability>=0)&(out.probability<=1)).all(): raise RuntimeError('invalid probability')
    out.to_csv(DATA.parent/'submission.csv',index=False)
if __name__=='__main__': main()
