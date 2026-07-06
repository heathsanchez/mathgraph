# MathGraph SorryDB v4.8.73 - vericoding LT0179 Mgrid Zero Bounds

## Result

CERTIFIED

## File

specs/LT0179_specs.lean

## Target

Mgrid first row/column zero-index bounds.

## Expected proofs

    by exact h_rows
    by exact h_cols

## Accepted variant

v01_row_zero_only

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
