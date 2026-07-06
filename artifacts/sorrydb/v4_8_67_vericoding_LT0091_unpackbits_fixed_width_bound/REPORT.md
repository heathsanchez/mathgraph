# MathGraph SorryDB v4.8.67 - vericoding LT0091 Unpackbits Fixed-width Bound

## Result

CERTIFIED

## File

specs/LT0091_specs.lean

## Target

Fixed-width flattened bit index bound:

    i.val * 8 + j.val < n * 8

## Accepted variant

v01_calc

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
