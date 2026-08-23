# V140 precommit — Cross-fitted calibration

## PUSH
Full V135, verified full-data session-grouped LL 0.537463 and +0.001771 vs V97.

## Residual
Representation/applicability refinements V137-V139 did not materially improve V135. Remaining plausible failure level: probability calibration/domain shift under log loss.

## Rival
V135 is already sufficiently calibrated; any apparent calibration gain is meta-overfit and will not transfer across unseen sessions.

## K(rho)
Any admitted calibration must: use only V135 probability at inference; fit labels only on training sessions; transfer to unseen sessions; improve aggregate LL by >=0.003 for phase-change promotion; improve all four outer folds; and beat an equal-protocol shuffled-label control.

## Version space
Exactly three low-capacity calibration families: temperature-only logit scaling, affine Platt scaling, beta calibration. Family selection occurs only by 3-fold session-grouped inner OOF inside each outer-training partition. No isotonic, bins, routers, objective-specific calibration, public-score fitting, or threshold sweep.

## Decision
PROMOTE if gain >=0.003, all 4 folds improve, and shuffled control is materially worse. RETAIN_SMALL_CALIBRATION_LAW if gain >0 and >=3 folds improve. Otherwise CLOSE_GLOBAL_CALIBRATION_AS_PHASE_CHANGE.
