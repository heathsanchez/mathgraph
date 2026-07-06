# MathGraph SorryDB v4.8.33 - vericoding LTvander Nonlinear Nat Bound Retry

## Result

CERTIFIED_PARTIAL_OR_FULL

## Repository

Beneficial-AI-Foundation/vericoding-benchmark

## Accepted variants

LT0479:

    LT0479_v01_calc_nat_succ_mul

LT0480:

    

## Meaning

v4.8.32 showed that raw omega cannot solve these flattened multidimensional index bounds.

v4.8.33 tests explicit Nat multiplication-bound proofs.

## Certification rule

Certified iff:

    lean target succeeds
    and total file sorry/admit count decreases
    and no new sorry/admit is introduced

## Probe table

See:

    probe_results.tsv
