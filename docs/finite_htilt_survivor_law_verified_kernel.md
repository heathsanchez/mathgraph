# Finite H-Tilt Survivor Law: Verified Kernel

## What Was Verified

MathGraph contains a Lean-checked finite algebraic survivor law. Under explicit
left/right eigenmode equations, the Doob-transformed entries have zero row
sums, and the biorthogonal weight `q_i h_i`—both unnormalized and normalized as
`piStar`—is stationary.

The paper-native normalized multiplicative bridge `q_i h_i^β / Σ_j q_j
h_j^β` recovers `piStar` at `β = 1`. A positive-domain pointwise theorem also
identifies `q_i exp(β log h_i)` with `q_i h_i^β`.

## Lean Artifact

- Source: `examples/verifier_fixtures/lean/htilt_survivor_law.lean`
- Lean: `4.28.0`
- Mathlib: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`
- SHA-256:
  `900842961b5cecce2e85cfe26272a8cd24eadbd0d784c5e8994220fa7cf63e29`
- Lawbook JSON: `artifacts/lawbook/finite_htilt_survivor_law_v1.json`

## Mathematical Setup

For finite `ι`, real `K : ι → ι → ℝ`, scalar `λ`, and functions `q,h`, define

```text
doobEntry(i,j) = ((K(i,j) - λδ(i,j)) h(j)) / h(i)
survivorWeight(i) = q(i) h(i)
piStar(i) = survivorWeight(i) / Σ_j survivorWeight(j).
```

Stationarity assumes `Σ_i q(i)K(i,j) = λq(j)`. Row-sum cancellation assumes
`Σ_j K(i,j)h(j) = λh(i)`. The relevant denominators are explicitly assumed
nonzero.

## Theorem Statements

Survivor law:

- `htilt_unnormalized_stationary`
- `htilt_normalized_stationary`
- `doob_row_sum_zero`

Bridge results:

- `geometric_bridge_one_eq_piStar`
- `geometric_bridge_nat_one_eq_piStar`
- `geometric_log_exp_bridge_eq_geometric_bridge`
- `multiplicative_bridge_nat_one_eq_piStar`
- `multiplicative_bridge_real_one_eq_piStar`
- `multiplicative_log_exp_pointwise_eq`

## Bridge Definitions

`geometricBridge` interpolates between `q` and `piStar`. The legacy
`powerBridge` name is only a compatibility alias for this object.

`multiplicativeBridgeNat` and `multiplicativeBridgeReal` are the paper-native
normalized `q_i h_i^β` bridges. Their separate names make the two constructions
impossible to conflate in the formal API or Lawbook record.

## Boundary / Non-Claims

The proof does not establish:

- Perron-Frobenius existence, uniqueness, or positivity;
- Markov-process convergence;
- empirical h-band universality;
- consciousness;
- H-Tilt scheduler performance;
- empirical bridge optimality;
- a universal beta band or shared viability geometry.

These are recorded as blocked overclaims, not silently implied corollaries.

## How To Re-run

```bash
cd experiments/continuation_claim_audit_lab/lean_project
lake env lean '/Users/heath/Documents/New project/examples/verifier_fixtures/lean/htilt_survivor_law.lean'
cd -
rg -n '\b(sorry|admit|axiom|unsafe)\b' \
  examples/verifier_fixtures/lean/htilt_survivor_law.lean
python -m pytest -q tests/test_lean_htilt_survivor_law_artifacts.py
python -m pytest -q tests/test_finite_htilt_lawbook_artifact.py
```

The Lean command must exit `0`. The marker audit should print no matches.

## Why This Matters

This is verified map-making in the narrow MathGraph sense: a broad speculative
claim family was decomposed, the exact algebraic atom was isolated, numerical
replay remained diagnostic, Lean supplied the truth boundary, and explicit
obstruction records prevent nearby empirical or metaphysical claims from
borrowing that authority.
