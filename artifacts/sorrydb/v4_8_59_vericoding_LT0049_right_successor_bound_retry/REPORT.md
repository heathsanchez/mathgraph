# MathGraph SorryDB v4.8.59 - vericoding LT0049 Right Successor Bound Retry

## Result

CERTIFIED

## File

specs/LT0049_specs.lean

## Target

Second delete branch successor bound:

    i.val + 1 < n + 1

## Starting point

The certified v4.8.58 left-branch proof was applied first.

## Accepted variant

v01_succ_lt_succ

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
