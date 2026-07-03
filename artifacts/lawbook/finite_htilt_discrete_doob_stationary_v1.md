# Conditional Finite Discrete Doob Stationarity

**Artifact:** `finite_htilt_discrete_doob_stationary_v1`
**Status:** `VERIFIED_PROOF`

## Verified claim

Let `A` be a real matrix on a finite index type, let `rho ≠ 0`, and let every
entry of `h` be nonzero. Define

```text
D_ij = A_ij h_j / (rho h_i).
```

If `q` is a left eigenmode of `A` with eigenvalue `rho`, then
`q_i h_i` is a stationary weight for `D`. If its finite normalization is
nonzero, the normalized weight is stationary. If `h` is a right eigenmode with
the same eigenvalue, every row of `D` sums to one.

Under explicit positivity of `rho,q,h` and entrywise nonnegativity of `A`,
Lean also verifies that `D` is nonnegative and that `piStar` is strictly
positive, sums to one, and is stationary.

## Lean boundary

- Lean: 4.28.0
- Mathlib: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`
- Source:
  `examples/verifier_fixtures/lean/htilt_discrete_doob_stationary.lean`
- Source SHA-256:
  `7e8e00b2ad5c7d5129cc0d58939dd6a40adc2fe12d5995db15b5a0bfa2ebd3b2`

Verified declarations:

```lean
HTiltDiscreteDoob.discrete_doob_unnormalized_stationary
HTiltDiscreteDoob.discrete_doob_normalized_stationary
HTiltDiscreteDoob.discrete_doob_row_sum_one
HTiltDiscreteDoob.survivorWeight_pos
HTiltDiscreteDoob.survivorNorm_pos
HTiltDiscreteDoob.piStar_pos
HTiltDiscreteDoob.piStar_sum_one
HTiltDiscreteDoob.discreteDoobEntry_nonneg
HTiltDiscreteDoob.piStar_is_stationary_distribution_for_discreteDoob
```

## Claim boundary

This entry is conditional algebra. It does not prove Perron–Frobenius
existence, positivity or uniqueness of eigenmodes, irreducibility consequences,
Markov convergence, ergodicity, mixing, the killed-generator case, or empirical
H-Tilt performance.
