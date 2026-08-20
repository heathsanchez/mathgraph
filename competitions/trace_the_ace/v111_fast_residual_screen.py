#!/usr/bin/env python3
"""Temporary isolated-runner shim: execute frozen V112 fast raw-observable screen."""
from v112_fast_raw_observable_screen import main
import argparse
from pathlib import Path
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--features',type=Path,required=True);p.add_argument('--labels',type=Path,required=True);p.add_argument('--transcripts',type=Path,required=True);p.add_argument('--rows',type=int,default=2500);p.add_argument('--out',default='v111_fast_residual_screen.json');main(p.parse_args())
