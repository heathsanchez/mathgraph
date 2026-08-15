#!/usr/bin/env python3
"""V83: task-supervised TalkMove-BERT on V81 multi-resolution evidence.

This reuses the V82 training harness but swaps in a tutoring-dialogue-domain
encoder already present in the official runtime preload list. The goal is a fast,
genuinely supervised objective-cold probe that can run on CPU and still update
upper language-model layers from the competition labels.
"""
from v82_modernbert_supervised import run
import argparse
from pathlib import Path

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
    run(p.parse_args())
