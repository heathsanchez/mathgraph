# MathGraph SorryDB v4.8.82 - vericoding LT0420 Hermemulx Successor Bounds

## Result

CERTIFIED

## File

specs/LT0420_specs.lean

## Target

Hermite multiplication-by-x local successor/index bounds.

Likely safe route:

    result.get ⟨i.val + 1, by exact Nat.succ_lt_succ i.isLt⟩

Possible guarded route:

    result.get ⟨1, by exact Nat.succ_lt_succ h⟩

## Accepted variant

v01_result_i_succ_only

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit line count decreases, occurrence count decreases, and no new sorry/admit is introduced.
