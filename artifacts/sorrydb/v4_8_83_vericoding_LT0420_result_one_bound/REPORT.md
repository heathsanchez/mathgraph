# MathGraph SorryDB v4.8.83 - vericoding LT0420 Result One Bound

## Result

CERTIFIED

## File

specs/LT0420_specs.lean

## Starting point

The certified v4.8.82 successor proof was applied first.

## Target

Bound for:

    result.get ⟨1, sorry⟩

inside:

    ∀ (h : n > 0), ...

## Accepted variant

v01_succ_lt_succ_h

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit line count decreases, occurrence count decreases, and no new sorry/admit is introduced.
