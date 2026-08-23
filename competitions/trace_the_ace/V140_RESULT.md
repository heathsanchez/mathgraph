# V140 result — Cross-fitted calibration

Frozen V140 tested temperature-only, affine Platt, and beta calibration on the saved V139 OOF V135 probabilities, with family selection by inner session-grouped OOF and untouched outer session folds.

Baseline V135 LL: `0.537463296386217`.
Cross-fitted calibrated LL: `0.5375339575528875`.
Delta: `-0.0000706611666705` (worse).

Temperature scaling was selected in all four outer folds. Outer fold baseline -> calibrated:
1. 0.53834858 -> 0.53835494
2. 0.53871046 -> 0.53870493
3. 0.54345854 -> 0.54354845
4. 0.52933561 -> 0.52952751

Only 1/4 folds improved. Shuffled-label control LL was 0.57408505.

Verdict: `CLOSE_GLOBAL_CALIBRATION_AS_PHASE_CHANGE`.
Retained law: low-capacity global post-hoc calibration does not improve the current V135 OOF probability field under session transfer.