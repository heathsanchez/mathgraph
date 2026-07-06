# MathGraph SorryDB v4.8.79R - vericoding LT0579 Correlate Window Bound Repair

## Result

CERTIFIED

## File

specs/LT0579_specs.lean

## Repair

The file uses:

    a.get ⟨k.val + i.val, by sorry⟩

not:

    a.get ⟨k.val + i.val, sorry⟩

## Target

Correlate sliding-window source bound:

    k.val + i.val < m

## Accepted variant

v01_first_omega

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit line count decreases, occurrence count decreases, and no new sorry/admit is introduced.
