# Axiom Audit

## Layer 1

`examples/verifier_fixtures/lean/htilt_survivor_law.lean` contains no `sorry`,
`admit`, custom `axiom`, or `unsafe`.

## Layer 2

`examples/verifier_fixtures/lean/htilt_discrete_doob_stationary.lean` contains
no `sorry`, `admit`, custom `axiom`, or `unsafe`.

## Layer 3

The external PF subtree contains one unrelated `sorry` at:

```text
MCMC/PF/Combinatorics/Quiver/Path.lean:1112
```

The exact command used for the strongest promoted theorem was:

```lean
#print axioms HTiltPFDiscreteSurvivor.exists_positive_stationary_distribution_of_irreducible
```

Lean reported:

```text
[propext, Classical.choice, Quot.sound]
```

There is no `sorryAx` dependency.

## Boundary

This release claims a clean theorem dependency graph for the promoted PF
theorem, not global placeholder-freedom of the external repository.
