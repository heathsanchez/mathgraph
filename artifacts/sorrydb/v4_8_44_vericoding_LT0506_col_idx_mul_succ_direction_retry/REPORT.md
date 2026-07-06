# MathGraph SorryDB v4.8.44 - vericoding LT0506 col_idx mul_succ Direction Retry

## Result

CERTIFIED

## File

specs/LT0506_specs.lean

## Target

Legendre 3D flattened column index bound.

## Correction

The v4.8.43 failure was the multiplication successor rewrite direction.

Use:

    rw [← Nat.mul_succ]

for goals of the form:

    A * p + A = A * (p + 1)

## Accepted variant

v01_mul_succ_reverse

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
