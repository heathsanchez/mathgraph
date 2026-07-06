# MathGraph SorryDB v4.8.42 - vericoding LT0506 col_idx Local Hypothesis Retry

## Result

NO_CERTIFIED_VARIANT

## Repository

Beneficial-AI-Foundation/vericoding-benchmark

## File

specs/LT0506_specs.lean

## Target

The col_idx bound inside the Legendre 3D matrix access.

## Strategy

Use the immediately preceding local arrow hypothesis:

    col_idx < (deg_x + 1) * (deg_y + 1) * (deg_z + 1)

as the Fin bound proof.

## Accepted variant



## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
