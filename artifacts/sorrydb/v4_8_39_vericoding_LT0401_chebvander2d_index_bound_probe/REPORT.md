# MathGraph SorryDB v4.8.39 - vericoding LT0401 Chebyshev 2D Index Bound Probe

## Result

CERTIFIED

## Repository

Beneficial-AI-Foundation/vericoding-benchmark

## File

specs/LT0401_specs.lean

## Target

    (result.get k).get ⟨idx, by sorry⟩

where:

    idx = i.val * (ydeg + 1) + j.val

## Strategy

Reuse the certified LT0479 2D flattened-index Nat proof.

## Accepted variant

v01_lt0479_shape

## Certification rule

Certified iff:

    lean specs/LT0401_specs.lean succeeds
    and total file sorry/admit count decreases
    and no new sorry/admit is introduced
