#!/usr/bin/env python3
"""V83: task-supervised TalkMove-BERT on V81 multi-resolution evidence.

R10 repair only: TalkMove-BERT ships with a 5-class head, while this experiment
uses a 1-logit binary head. Inject ignore_mismatched_sizes=True so the pretrained
encoder is retained and the task head is lawfully reinitialized. Hypothesis,
folds, representation and metrics remain unchanged.
"""
import argparse
from pathlib import Path
import v82_modernbert_supervised as base

_orig = base.AutoModelForSequenceClassification.from_pretrained

def _from_pretrained(*args, **kwargs):
    kwargs['ignore_mismatched_sizes'] = True
    return _orig(*args, **kwargs)

base.AutoModelForSequenceClassification.from_pretrained = _from_pretrained

if __name__=='__main__':
    p=argparse.ArgumentParser()
    p.add_argument('--features',type=Path,required=True)
    p.add_argument('--labels',type=Path,required=True)
    p.add_argument('--transcripts',type=Path,required=True)
    p.add_argument('--out',default='v83_talkmove_supervised.json')
    p.add_argument('--model',default='saroyehun/Talkmove-bert')
    p.add_argument('--folds',type=int,default=1)
    p.add_argument('--epochs',type=int,default=2)
    p.add_argument('--top-blocks',type=int,default=4)
    p.add_argument('--lr',type=float,default=2e-5)
    p.add_argument('--max-len',type=int,default=512)
    p.add_argument('--max-chars',type=int,default=14000)
    p.add_argument('--batch',type=int,default=8)
    p.add_argument('--eval-batch',type=int,default=16)
    p.add_argument('--limit',type=int,default=0)
    base.run(p.parse_args())
