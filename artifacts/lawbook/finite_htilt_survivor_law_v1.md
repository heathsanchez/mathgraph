# Finite H-Tilt Survivor Law v1

## Status

`VERIFIED_PROOF`

## One-Line Claim

Under finite-state algebraic assumptions, the Doob-transformed killed dynamics
admit the biorthogonal survivor law `piStar ∝ q ⊙ h` as a stationary law, and
the paper-native normalized multiplicative bridge recovers `piStar` at
`β = 1`.

## Formal Boundary

- Lean: `4.28.0`
- Mathlib revision: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`
- Proof file: `examples/verifier_fixtures/lean/htilt_survivor_law.lean`
- Check command: `lake env lean '/Users/heath/Documents/New project/examples/verifier_fixtures/lean/htilt_survivor_law.lean'`
- Proof return code: `0`
- Packaging regression: `1737 passed`
- Proof placeholders and target-specific axioms: none

## Mathematical Setup

Let `ι` be a finite index type. Let `K i j`, `λ`, `h i`, and `q i` be real.
Define

```text
delta(i,j) = 1 if i = j, otherwise 0
doobEntry(i,j) = ((K(i,j) - λ delta(i,j)) h(j)) / h(i)
survivorWeight(i) = q(i) h(i)
survivorNorm = Σ_i q(i) h(i)
piStar(i) = survivorWeight(i) / survivorNorm.
```

Stationarity assumes the left eigen-equation
`Σ_i q(i) K(i,j) = λ q(j)`. Zero row sums assume the right eigen-equation
`Σ_j K(i,j) h(j) = λ h(i)`. Division uses explicit nonzero hypotheses.

## Verified Theorems

Survivor law:

- `htilt_unnormalized_stationary`
- `htilt_normalized_stationary`
- `doob_row_sum_zero`

Geometric bridge:

- `geometric_bridge_one_eq_piStar`
- `geometric_bridge_nat_one_eq_piStar`
- `geometric_log_exp_bridge_eq_geometric_bridge`

Paper-native multiplicative bridge:

- `multiplicative_bridge_nat_one_eq_piStar`
- `multiplicative_bridge_real_one_eq_piStar`
- `multiplicative_log_exp_pointwise_eq`

Supporting finite-sum lemmas:

- `sum_delta_left`
- `sum_delta_right`
- `sum_mul_delta`
- `sum_delta_mul`

## Bridge Alignment

`geometricBridge` interpolates between `q` and `piStar`. It is not the
paper-native bridge.

`multiplicativeBridgeNat` and `multiplicativeBridgeReal` normalize
`q_i h_i^β` by `Σ_j q_j h_j^β`. Both recover `piStar` at exponent one. The
old `powerBridge` API is retained only as a compatibility alias for the
geometric bridge. This resolves the earlier naming ambiguity.

## What This Proves

The proof establishes finite algebraic stationarity of the unnormalized weight
`q ⊙ h` and its normalized form `piStar` under the stated eigen-equations. It
also establishes row-sum cancellation for the Doob entries, exact bridge
containment at exponent one, and the positive-domain pointwise identity
`q_i exp(β log h_i) = q_i h_i^β`.

## What This Does Not Prove

- Perron-Frobenius existence.
- Markov-process convergence.
- Empirical H-band universality or a universal beta band.
- Consciousness.
- H-Tilt scheduler performance or promotion.
- Empirical bridge optimality.

## Why This Matters for MathGraph

This artifact records a complete claim-boundary path:

```text
speculative corpus
→ claim audit
→ exact finite kernel
→ numerical replay
→ Lean verification
→ bridge-definition correction
→ Lawbook entry.
```

Only the Lean-checked algebra is admitted as `VERIFIED_PROOF`; empirical and
philosophical continuations remain outside the entry.

## Next Steps

Formal options are a Matrix API presentation, a separate Perron-Frobenius
existence theorem, and positivity conditions for a Markov-generator
interpretation. Empirical options remain held-out shared-geometry, h-band
confound, and pre-transition drift tests. None is part of this entry.
