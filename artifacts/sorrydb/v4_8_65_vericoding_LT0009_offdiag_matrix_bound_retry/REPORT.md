# MathGraph SorryDB v4.8.65 - vericoding LT0009 Offdiag Matrix Bound Retry

## Result

CERTIFIED

## File

specs/LT0009_specs.lean

## Target

Off-diagonal flattened matrix bound:

    i.val * n + j.val < n * n

## Starting point

The certified v4.8.64 diagonal proof was applied first.

## Accepted variant

v01_offdiag_calc

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
