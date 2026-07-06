# MathGraph SorryDB v4.8.80 - vericoding LT0579 Second Correlate Window Bound

## Result

CERTIFIED

## File

specs/LT0579_specs.lean

## Starting point

The certified v4.8.79R first window proof was applied first.

## Target

Second correlate sliding-window source bound:

    k.val + i.val < m

## Accepted variant

v01_second_omega

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit line count decreases, occurrence count decreases, and no new sorry/admit is introduced.
