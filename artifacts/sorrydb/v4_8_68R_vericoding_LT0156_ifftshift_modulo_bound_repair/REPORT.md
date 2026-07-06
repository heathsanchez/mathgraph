# MathGraph SorryDB v4.8.68R - vericoding LT0156 Ifftshift Modulo Bound Repair

## Result

CERTIFIED

## File

specs/LT0156_specs.lean

## Target

Modulo index bound:

    (i.val + n / 2) % n < n

## Accepted variant

v02_have_ne_zero

## Repair note

v4.8.68 failed because Nat.pos_of_gt is unavailable here and omega could not see i.isLt inside the embedded proof. This repair uses case analysis on n.

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
