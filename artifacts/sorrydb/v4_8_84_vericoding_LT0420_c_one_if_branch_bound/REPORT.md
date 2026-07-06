# MathGraph SorryDB v4.8.84 - vericoding LT0420 C One If-branch Bound

## Result

NO_CERTIFIED_VARIANT

## File

specs/LT0420_specs.lean

## Starting point

The certified v4.8.83 result bounds were applied first.

## Target

Anonymous if-branch bound:

    if n > 1 then c.get ⟨1, sorry⟩ else 0

## Accepted variant



## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit line count decreases, occurrence count decreases, and no new sorry/admit is introduced.
