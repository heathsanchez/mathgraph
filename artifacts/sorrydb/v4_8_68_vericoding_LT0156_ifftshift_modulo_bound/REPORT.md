# MathGraph SorryDB v4.8.68 - vericoding LT0156 Ifftshift Modulo Bound

## Result

NO_CERTIFIED_VARIANT

## File

specs/LT0156_specs.lean

## Target

Modulo index bound:

    (i.val + n / 2) % n < n

## Route

Use i : Fin n to establish n > 0, then Nat.mod_lt.

## Accepted variant



## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
