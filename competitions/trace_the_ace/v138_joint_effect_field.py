#!/usr/bin/env python3
"""V138: full developmental-controller test on the saved V137 OOF effect field.

Controller state (frozen before result):
PUSH: full V135, the strongest retained supported-objective composition.
READ: V136/V137 establish +0.001771 full-data gain, all folds positive, but V137 one-scalar gating loses 0.000121 vs full V135.
DIAGNOSE: primary=applicability/composition; secondary=representation of applicability. One-dimensional routing is closed.
ZOOM: ask whether V135 benefit has stable JOINT structure in current runtime-visible observables.
IMPORT/JOIN: V137 fold rules repeatedly implicated support_log, prior_disp, expert_disagree; treat this only as hypothesis generation.
RIVAL: no stable deployable applicability structure exists in the current observable field; apparent inner structure is selection noise.
K(rho): any admitted refinement must be label-free at inference, learned only from meta-training OOF effects, improve untouched meta-folds over full V135, beat an equal-capacity shuffled-effect selector, and preserve V97 outside its selected region.
VERSION SPACE: the smallest language beyond V137: conjunction of exactly two threshold literals on distinct frozen fields. No trees, learned router, OR clauses, or parameter sweep outside the frozen grid.
DECIDE: 4-fold session-grouped meta-OOF separator.
ATTACK: identical rule search on deterministically shuffled training benefits.
DESCAFFOLD: inference receives only the six runtime fields, never labels/benefits.
TRANSFER: each selected rule is applied to an unseen session fold.
COMPRESS/RETAIN: output a scoped verdict and next-action law.
"""
from __future__ import annotations
import argparse, json
from pathlib import Path
import numpy as np
from sklearn.model_selection import GroupKFold

EPS=1e-6
SEED=20260823
FIELDS=['support_log','prior_disp','expert_disagree','prior_conf','v75_conf','prior_shift']
QS=(.2,.4,.6,.8)
MIN_COVER=.08
MAX_COVER=.80

def sample_loss(y,p):
    p=np.clip(np.asarray(p,float),EPS,1-EPS); y=np.asarray(y,float)
    return -(y*np.log(p)+(1-y)*np.log(1-p))

def ll(y,p): return float(np.mean(sample_loss(y,p)))

def literal(x,th,direction): return x<=th if direction=='le' else x>th

def thresholds(x): return [(q,float(np.quantile(x,q))) for q in QS]

def choose_pair(field,benefit):
    """Choose one two-literal conjunction maximizing mean all-row benefit."""
    best=None
    for ia,a in enumerate(FIELDS):
        xa=np.asarray(field[a],float)
        for b in FIELDS[ia+1:]:
            xb=np.asarray(field[b],float)
            for qa,tha in thresholds(xa):
                for da in ('le','gt'):
                    ma=literal(xa,tha,da)
                    for qb,thb in thresholds(xb):
                        for db in ('le','gt'):
                            m=ma & literal(xb,thb,db)
                            cov=float(m.mean())
                            if cov<MIN_COVER or cov>MAX_COVER: continue
                            gain=float(np.mean(np.where(m,benefit,0.0)))
                            rec={'a':a,'qa':qa,'tha':tha,'da':da,'b':b,'qb':qb,'thb':thb,'db':db,
                                 'coverage':cov,'train_gain':gain}
                            if best is None or gain>best['train_gain']+1e-15:
                                best=rec
    if best is None: raise RuntimeError('no admissible pair rule')
    return best

def apply_pair(field,r):
    return literal(np.asarray(field[r['a']],float),r['tha'],r['da']) & literal(np.asarray(field[r['b']],float),r['thb'],r['db'])

def main(a):
    z=np.load(a.field,allow_pickle=True)
    y=z['y'].astype(int); sessions=z['sessions'].astype(str); objectives=z['objectives'].astype(str)
    p0=z['p_v97'].astype(float); p2=z['p_v135'].astype(float)
    field={k:z[f'field_{k}'].astype(float) for k in FIELDS}
    n=len(y)
    assert n==35072 and all(len(v)==n for v in field.values())
    base_gain=ll(y,p0)-ll(y,p2)
    benefit=sample_loss(y,p0)-sample_loss(y,p2)
    pg=np.zeros(n); pc=np.zeros(n); mask_all=np.zeros(n,bool); control_all=np.zeros(n,bool)
    folds=[]; rng=np.random.default_rng(SEED)
    splitter=GroupKFold(4)
    for k,(tr,va) in enumerate(splitter.split(np.zeros(n),y,sessions),1):
        ftr={x:v[tr] for x,v in field.items()}; fva={x:v[va] for x,v in field.items()}
        rule=choose_pair(ftr,benefit[tr])
        shuffled=benefit[tr].copy(); rng.shuffle(shuffled)
        crule=choose_pair(ftr,shuffled)
        m=apply_pair(fva,rule); cm=apply_pair(fva,crule)
        q=p0[va].copy(); q[m]=p2[va][m]
        qc=p0[va].copy(); qc[cm]=p2[va][cm]
        pg[va]=q;pc[va]=qc;mask_all[va]=m;control_all[va]=cm
        fr={'fold':k,'rows':int(len(va)),'v97_ll':ll(y[va],p0[va]),'v135_ll':ll(y[va],p2[va]),
            'pair_ll':ll(y[va],q),'control_ll':ll(y[va],qc),'coverage':float(m.mean()),
            'control_coverage':float(cm.mean()),'rule':rule,'control_rule':crule}
        folds.append(fr); print('FOLD',json.dumps(fr),flush=True)
    l0=ll(y,p0); l2=ll(y,p2); lg=ll(y,pg); lc=ll(y,pc)
    gain=l0-lg; inc=l2-lg; causal=lc-lg
    all_nonreg=all(r['pair_ll']<=r['v97_ll']+1e-12 for r in folds)
    beats_v135_folds=sum(r['pair_ll']<r['v135_ll'] for r in folds)
    # Strong pass: material and causal. Structured-signal retain: positive incremental + causal, majority folds.
    if gain>=.003 and inc>=.001 and causal>=.001 and all_nonreg and beats_v135_folds>=3:
        verdict='PROMOTE_TWO_LITERAL_REGIME_REFINEMENT'; next_action='attack_boundary_then_runtime_parity'
    elif inc>0 and causal>=.0005 and beats_v135_folds>=3:
        verdict='RETAIN_JOINT_APPLICABILITY_SIGNAL'; next_action='attack_and_descaffold_joint_structure'
    else:
        verdict='CLOSE_TWO_LITERAL_APPLICABILITY_SPACE'; next_action='zoom_out_current_observable_applicability_exhausted'
    out={
      'protocol':'V138_JOINT_EFFECT_FIELD_CONTROLLER',
      'controller':{
        'push':'full_v135',
        'residual':{'v135_full_gain':base_gain,'v137_incremental_vs_v135':-0.00012105436555076565,
                    'statement':'real distributed V135 gain; one-scalar applicability refinement closed'},
        'diagnosis':{'primary':'applicability_composition','secondary':['applicability_representation'],'closed':['one_scalar_gate']},
        'zoom':'test stable joint structure before increasing router capacity',
        'import_join':'recurring V137 coordinates support/prior displacement/expert disagreement motivate relational view only',
        'rival':'no stable deployable applicability exists in current runtime-visible field',
        'K_effect':['label_free_inference','meta_train_only_selection','untouched_session_transfer','beat_full_v135','beat_equal_capacity_shuffle','v97_outside_gate'],
        'version_space':{'operator':'AND of exactly two threshold literals','fields':FIELDS,'quantiles':list(QS),'directions':['le','gt'],'min_coverage':MIN_COVER,'max_coverage':MAX_COVER},
        'attack':'equal-capacity shuffled-benefit selector','descaffold':'six runtime fields only','transfer':'4 unseen-session meta folds'
      },
      'rows':n,'v97_ll':l0,'v135_ll':l2,'v135_gain':l0-l2,'pair_ll':lg,'pair_gain':gain,
      'incremental_vs_v135':inc,'control_ll':lc,'gain_vs_control':causal,
      'pair_coverage':float(mask_all.mean()),'control_coverage':float(control_all.mean()),
      'all_fold_nonregression':bool(all_nonreg),'folds_beating_v135':int(beats_v135_folds),'folds':folds,
      'decision':{'verdict':verdict,'next_action':next_action},
      'retained_law':('two_literal_joint_structure_admitted' if verdict.startswith('PROMOTE') else
                      'joint_signal_provisional' if verdict.startswith('RETAIN') else
                      'NOT_SUPPORTED_UNDER(two_literal_current_observable_applicability,V137_OOF,shuffle_control)')
    }
    Path(a.out).write_text(json.dumps(out,indent=2)); print('FINAL',json.dumps(out,indent=2),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser(); p.add_argument('--field',type=Path,required=True); p.add_argument('--out',type=Path,default=Path('v138_joint_effect_field.json')); main(p.parse_args())
