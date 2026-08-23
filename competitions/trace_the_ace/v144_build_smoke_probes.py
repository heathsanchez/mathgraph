#!/usr/bin/env python3
from __future__ import annotations
import argparse, shutil, zipfile
from pathlib import Path

LEVELS = (0.08, 0.16, 0.24, 0.30)

HELPER = r'''
def apply_v144_shrink(p135,p75,pr,seen,amount):
    # V97 law: supported objective -> V75; unsupported -> .65 V75 + .35 RELATED.
    p97=np.clip(.65*np.asarray(p75)+.35*np.asarray(pr),EPS,1-EPS)
    p97=np.asarray(p97,float)
    p97[np.asarray(seen,bool)]=np.asarray(p75,float)[np.asarray(seen,bool)]
    z=logit(p135)
    z97=logit(p97)
    return np.clip(sigmoid(z+float(amount)*(z97-z)),EPS,1-EPS)
'''

def patch_main(src: str, amount: float) -> str:
    anchor = "def build_base_predictions(frame,transcripts,assets):"
    if HELPER.strip() not in src:
        src = src.replace(anchor, HELPER + "\n" + anchor)
    old = "p,_,_,_=predict_components(p75,pr,f.learning_objective.astype(str).to_numpy(),assets,manifest)"
    new = (
        "p,pp,n,seen=predict_components(p75,pr,f.learning_objective.astype(str).to_numpy(),assets,manifest)\n"
        f"    p=apply_v144_shrink(p,p75,pr,seen,{amount:.2f})"
    )
    if old not in src:
        raise RuntimeError('baseline prediction anchor not found')
    return src.replace(old,new)

def zip_tree(root: Path, out: Path):
    with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(root.rglob('*')):
            if p.is_file(): z.write(p,p.relative_to(root).as_posix())

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--baseline',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args()
    baseline=Path(a.baseline); out=Path(a.out); out.mkdir(parents=True,exist_ok=True)
    for amount in LEVELS:
        tag=f"shrink_{int(round(amount*100)):02d}"
        work=out/tag
        if work.exists(): shutil.rmtree(work)
        shutil.copytree(baseline,work)
        mp=work/'main.py'
        mp.write_text(patch_main(mp.read_text(),amount))
        zip_tree(work,out/f'V144_{tag}.zip')
        shutil.rmtree(work)

if __name__=='__main__': main()
