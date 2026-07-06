# MathGraph SorryDB v4.8.36 - vericoding LA0521 ValidQuery Probe

## Result

NO_CERTIFIED_VARIANT

## Repository

Beneficial-AI-Foundation/vericoding-benchmark

## File

specs/LA0521_specs.lean

## Target

    have h_valid : ValidQuery k n a b := by sorry

There are two occurrences in the postcondition.

## Accepted variant



## Certification rule

Certified iff:

    lean specs/LA0521_specs.lean succeeds
    and total file sorry/admit count decreases
    and no new sorry/admit is introduced
