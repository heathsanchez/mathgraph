# MathGraph SorryDB v4.8.49 - vericoding LT0429 Local order-bound Probe

## Result

NO_CERTIFIED_VARIANT

## File

specs/LT0429_specs.lean

## Target

HermiteE 3D Vandermonde local order-bound holes.

## Strategy

Use directly preceding local hypotheses of the form col_idx < order as Fin bound proofs.

## Accepted variant



## Certification rule

Certified iff lean on the target succeeds, total file sorry/admit count decreases, and no new sorry/admit is introduced.
