# Short Paper Outline: Finite H-Tilt Survivor Law

## Title Candidates

1. **A Lean-Verified Finite Survivor Law for Doob-Conditioned Killed Dynamics**
2. **A Verified Biorthogonal Survivor Law for Finite H-Tilt Dynamics**
3. **From H-Tilt Heuristic to Verified Survivor Law: A Lean Formalization**

Preferred title: **A Lean-Verified Finite Survivor Law for Doob-Conditioned
Killed Dynamics**.

Target length: 4–6 pages, excluding the compact artifact appendix.

## Abstract

We formalize the finite-state algebraic core of an enhanced H-Tilt framework.
Given a killed operator `K`, a scalar `λ`, and left/right modes `q,h`
satisfying the corresponding eigenvector equations, the Doob-transformed
dynamics admit the normalized biorthogonal law `piStar_i ∝ q_i h_i` as a
stationary law. We verify this identity in Lean, together with row-sum
cancellation for the Doob transform, exact containment of `piStar` by the
paper-native multiplicative bridge at `β = 1`, and the positive-domain log-exp
bridge identity. The result does not prove Perron-Frobenius existence,
empirical h-band universality, consciousness, or scheduling performance. Its
contribution is a small verified kernel separating exact survivor algebra from
empirical and philosophical conjecture.

## 1. Introduction

- Problem: H-Tilt began as heuristic reweighting inside a much broader
  speculative corpus.
- Risk: numerical identities, empirical patterns, and philosophical claims can
  inherit authority from one another if their boundaries are not explicit.
- Contribution: extract and Lean-check the exact finite algebraic survivor law.
- State the intentionally narrow result and list the principal non-claims.

## 2. Informal Mathematical Setup

- Finite state index `ι`.
- Real-valued operator entries `K_ij`, scalar `λ`, right mode `h`, left mode
  `q`.
- Assumed left/right eigen-equations.
- Doob entry `((K_ij - λδ_ij)h_j)/h_i`.
- Unnormalized survivor weight `q_i h_i`.
- Normalized law `piStar_i = q_i h_i / Σ_j q_j h_j`.
- Explain why nonzero hypotheses are algebraic domain conditions, not existence
  results.

## 3. Verified Theorems

- `htilt_unnormalized_stationary`: finite-sum cancellation through the left
  eigen-equation.
- `htilt_normalized_stationary`: normalization preserves stationarity.
- `doob_row_sum_zero`: right eigen-equation cancels every transformed row.
- Four Kronecker-delta sum lemmas supporting the calculation.
- Give the six-line core calculation from the Reason Atlas record.

## 4. Bridge Alignment

- Define `geometricBridge` as interpolation from `q` to `piStar`.
- Define the paper-native `multiplicativeBridgeNat` and
  `multiplicativeBridgeReal` as normalized `q_i h_i^β`.
- Explain the corrected naming boundary.
- State exact exponent-one containment theorems.
- State `multiplicative_log_exp_pointwise_eq` under `h_i > 0`.

## 5. Claim Boundary

- Verified: finite algebraic identities under explicit hypotheses.
- Not proved: eigenmode existence, positivity of a Markov generator, or
  convergence.
- Not promoted: h-band universality, consciousness, scheduling performance,
  shared viability geometry, or bridge optimality.
- Include the companion claim-boundary table verbatim or in condensed form.

## 6. MathGraph Method

- Claim inventory from the speculative corpus.
- Numerical replay as diagnostics, not proof.
- Exact kernel extraction.
- Lean verification with pinned toolchain and no proof placeholders.
- Bridge-definition audit and correction.
- Durable Lawbook entry plus active obstruction record.

## 7. Future Work

- Optional Matrix API restatement.
- Separate Perron-Frobenius existence theorem.
- Markov-generator positivity and stochastic interpretation.
- Held-out shared-geometry and h-band confound tests.
- Keep every extension in its own verification or empirical boundary.

## Appendix A. Lean Artifact

- File: `examples/verifier_fixtures/lean/htilt_survivor_law.lean`
- Lean: `4.28.0`
- Mathlib: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`
- Command:
  `lake env lean '/Users/heath/Documents/New project/examples/verifier_fixtures/lean/htilt_survivor_law.lean'`
- SHA-256:
  `900842961b5cecce2e85cfe26272a8cd24eadbd0d784c5e8994220fa7cf63e29`
- Lawbook entry: `artifacts/lawbook/finite_htilt_survivor_law_v1.json`
