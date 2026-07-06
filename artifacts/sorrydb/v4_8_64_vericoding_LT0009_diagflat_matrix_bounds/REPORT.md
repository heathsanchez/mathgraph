# MathGraph SorryDB v4.8.64 - vericoding LT0009 Diagflat Matrix Bounds

## Result

CERTIFIED

## File

specs/LT0009_specs.lean

## Target

Flattened matrix bounds:

    i.val * n + i.val < n * n
    i.val * n + j.val < n * n

## Accepted variant

v01_diag_only_calc

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
