# MathGraph SorryDB v4.8.70 - vericoding LT0151 Fftshift Modulo Bound

## Result

CERTIFIED

## File

specs/LT0151_specs.lean

## Target

Modulo index bound:

    (i.val + n - n / 2) % n < n

## Route

Use i : Fin n to establish n != 0, then Nat.mod_lt.

## Accepted variant

v01_have_ne_zero

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
