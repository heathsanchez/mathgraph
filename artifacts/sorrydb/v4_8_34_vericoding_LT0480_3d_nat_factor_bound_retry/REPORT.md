# MathGraph SorryDB v4.8.34 - vericoding LT0480 3D Nat Factor Bound Retry

## Result

CERTIFIED

## Repository

Beneficial-AI-Foundation/vericoding-benchmark

## File

specs/LT0480_specs.lean

## Target

    have h_idx : idx < (xdeg + 1) * (ydeg + 1) * (zdeg + 1) := by sorry

## Strategy

Reduce the 3D flattened index to a 2D row bound, then extend by the z dimension.

## Accepted variant

v01_row_then_depth_bound

## Certification rule

Certified iff:

    lean specs/LT0480_specs.lean succeeds
    and total file sorry/admit count decreases
    and no new sorry/admit is introduced
