# Finite Perron–Frobenius Discrete Survivor Law

**Artifact:** `finite_htilt_pf_discrete_survivor_law_v1`
**Status:** `VERIFIED_PROOF`

## Verified claim

For a finite nonempty index type and an irreducible nonnegative real matrix
`A`, there exist a scalar `rho` and modes `h`, `q` such that:

```text
0 < rho
∀ i, 0 < h i
∀ i, 0 < q i
A h = rho h
Aᵀ q = rho q
```

For the discrete Doob transform

```text
D_ij = A_ij h_j / (rho h_i),
```

the normalized distribution

```text
piStar_i = q_i h_i / sum_k q_k h_k
```

is strictly positive, sums to one, and is stationary. The matrix `D` is
entrywise nonnegative and every row sums to one:

```text
∀ i, piStar_i > 0
Σ_i piStar_i = 1
∀ i j, D_ij ≥ 0
∀ i, Σ_j D_ij = 1
∀ j, Σ_i piStar_i D_ij = piStar_j
```

## Lean boundary

- Lean: 4.27.0-rc1
- Mathlib: `ae0143cded18d09875e12c3056f428090484d9a4`
- External source:
  [mkaratarakis/HopfieldNet](https://github.com/mkaratarakis/HopfieldNet)
- External commit: `0bbb8999d1703776516f37f412334e01e07a30a0`
- Source:
  `examples/verifier_fixtures/lean/htilt_pf_discrete_survivor_law.lean`
- Source SHA-256:
  `bf73941821609b6f11ab68c4daf3459b28a00c95d609aa51e6999f904c55d31d`

Verified declarations:

```lean
HTiltPFDiscreteSurvivor.discrete_doob_unnormalized_stationary
HTiltPFDiscreteSurvivor.exists_positive_survivor_weight_of_irreducible
HTiltPFDiscreteSurvivor.exists_positive_stationary_distribution_of_irreducible
```

The exact axiom audit for the strongest normalized portal theorem reports only `propext`,
`Classical.choice`, and `Quot.sound`; it does not report `sorryAx`.

## Dependency precision

The external PF subtree contains one unrelated `sorry` in a quiver-path
declaration. The verified portal theorem does not depend on that declaration,
as established by Lean's axiom audit. This entry therefore claims a clean
theorem dependency graph, not a globally placeholder-free external repository.

## Claim boundary

This entry does not prove Markov convergence, ergodicity, mixing, a spectral
gap, the killed-generator case, or a shift/exponential/resolvent bridge. It
does not claim compatibility with the repository's separate Lean 4.28.0
environment.
