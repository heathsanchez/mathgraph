#!/usr/bin/env python3
"""Infrastructure-only memory-safe embedding transport for frozen V121.

No scientific representation, model, sample, ordering, folds, controls, or gates
are changed. Each text is embedded independently with the same frozen Jina model;
batch_size=1 only lowers peak ONNX attention memory.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from fastembed import TextEmbedding

MODEL_NAME = "jinaai/jina-embeddings-v2-small-en"

def embed1(model, seq):
    arr = np.vstack(list(model.embed(seq, batch_size=1))).astype(np.float32)
    if not np.isfinite(arr).all():
        raise RuntimeError("non-finite embedding")
    return arr

def main(a):
    d=Path(a.dir)
    texts=json.loads((d/'texts.json').read_text())
    n=len(texts['semantic']); shard=int(a.shard); shards=int(a.shards)
    if shards < 1 or not (0 <= shard < shards): raise ValueError(f'invalid shard {shard}/{shards}')
    start=(n*shard)//shards; end=(n*(shard+1))//shards
    obj=texts['objective'][start:end]; sem=texts['semantic'][start:end]
    print('frozen shard',shard,'of',shards,'rows',start,end,flush=True)
    model=TextEmbedding(model_name=MODEL_NAME, threads=4)
    E_obj=embed1(model,obj)
    E_sem=embed1(model,sem)
    if E_obj.shape[0] != end-start or E_sem.shape[0] != end-start: raise RuntimeError('row mismatch')
    np.savez_compressed(Path(a.out),E_obj=E_obj,E_sem=E_sem,start=np.array(start),end=np.array(end),total=np.array(n),shard=np.array(shard),shards=np.array(shards))
    print('complete',shard,E_obj.shape,E_sem.shape,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--dir',required=True); p.add_argument('--out',required=True); p.add_argument('--shard',type=int,required=True); p.add_argument('--shards',type=int,required=True); main(p.parse_args())
