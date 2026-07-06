# MathGraph SorryDB v4.8.37 - vericoding LA0521 First ValidQuery Only

## Result

NO_CERTIFIED_VARIANT

## Repository

Beneficial-AI-Foundation/vericoding-benchmark

## File

specs/LA0521_specs.lean

## Target

Only the first occurrence:

    ∀ i, 0 ≤ i ∧ i < queries.length →
      let (k, n, a, b) := queries[i]!
      have h_valid : ValidQuery k n a b := by sorry

## Reason for first-only probe

The second occurrence has only:

    i < results.length

inside the same postcondition where:

    results.length = queries.length

is a sibling conjunct, not a local hypothesis.

So the second occurrence is likely a postcondition-shape obstruction unless the spec is refactored.

## Accepted variant



## Certification rule

Certified iff:

    lean specs/LA0521_specs.lean succeeds
    and total file sorry/admit count decreases
    and no new sorry/admit is introduced
