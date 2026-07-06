# MathGraph SorryDB v4.8.62 - vericoding LT0445 h2 Branch Bound Retry

## Result

CERTIFIED

## File

specs/LT0445_specs.lean

## Target

Second if-branch coefficient bound:

    k.val + 1 < n

## Starting point

The certified v4.8.61 h1 proof was applied first.

## Accepted variant

v01_exact_h2

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
