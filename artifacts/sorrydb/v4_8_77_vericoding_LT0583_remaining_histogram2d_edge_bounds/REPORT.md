# MathGraph SorryDB v4.8.77 - vericoding LT0583 Remaining Histogram2d Edge Bounds

## Result

CERTIFIED

## File

specs/LT0583_specs.lean

## Starting point

The certified v4.8.76R monotone edge proof was applied first.

## Targets

Remaining obvious edge bounds:

    0 < nbins + 1
    nbins < nbins + 1
    i < nbins + 1
    i + 1 < nbins + 1
    j < nbins + 1
    j + 1 < nbins + 1

## Accepted variant

v01_combined_endpoints_partition

## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit line count decreases, occurrence count decreases, and no new sorry/admit is introduced.
