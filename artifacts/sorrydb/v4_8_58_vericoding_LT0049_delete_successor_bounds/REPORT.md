# MathGraph SorryDB v4.8.58 - vericoding LT0049 Delete Successor Bounds

## Result

CERTIFIED

## File

specs/LT0049_specs.lean

## Target

Vector delete index bounds into an array of length n + 1.

## Expected certified proofs

    i.val < n + 1
    i.val + 1 < n + 1

## Accepted variant

v01_left_index_only

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
