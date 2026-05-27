# MathGraph / Collatz v12.2 — Checkpoint-Safe Primitive Divisor Growth Run

This is not a Collatz proof. It is a fixation-stage candidate-law test.

## Current Stage

**FIXATION_CANDIDATE**

## Summary

- **pairs_processed:** 5000
- **primitive_growth_pairs:** 4999
- **partial_primitive_growth_pairs:** 0
- **primitive_growth_pair_rate:** 0.9998
- **partial_or_full_primitive_growth_pair_rate:** 0.9998
- **positive_novelty_rate:** 0.9998009090909091
- **avg_pair_median_novelty_ratio:** 0.9987621562844179
- **median_pair_median_novelty_ratio:** 0.9991694347067428
- **avg_pair_mean_novelty_ratio:** 0.9975527567958967
- **total_exact_excluded_count:** 1100000
- **total_integer_candidate_count:** 0
- **integer_candidate_rate:** 0.0
- **remaining_csv_rows:** 1
- **runtime_sec:** 2338.987667

## Pair Status Counts

- **PAIR_LOW_NOVELTY_RECURRENCE_RESIDUAL:** 1
- **PAIR_PRIMITIVE_GROWTH_COMPRESSED:** 4999

## Obstructions

### UNCANCELLED_PRIMITIVE_DIVISOR_GROWTH

- support_pairs: 4999
- root_score: 126.99664500159416
- description: Reduced denominator R_r repeatedly contributes fresh divisor mass not explained by rolling prior R-values.
- next_action: Promote to proof-template candidate. Replace rolling novelty proxy with exact primitive-divisor lemma.

### LOW_NOVELTY_RECURRENCE_RESIDUAL

- support_pairs: 1
- root_score: 4.434868437320833
- description: R_r > 1 but novelty is weak; exact gcd cancellation structure should be studied.
- next_action: Move to exact gcd cancellation recurrence analysis.

## Candidate Law

### UNCANCELLED_PRIMITIVE_DIVISOR_GROWTH

For nontrivial prefix-tail inverse Collatz families U·W^r in the tested residual basin, the reduced denominator R_r = D_r/gcd(D_r,N_r) persistently contains fresh uncancelled divisor mass as r grows, preventing integer fixed points except known trivial cases.

## Proof Obligations

- Replace rolling-bank novelty proxy with exact primitive-divisor theorem.
- Show fresh divisor mass in D_r is not cancelled by N_r.
- Classify exceptional low-novelty or known-cycle cases.
- Formalize prefix-tail fixed-point denominator obstruction.