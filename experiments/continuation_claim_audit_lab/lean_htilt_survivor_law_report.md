# Lean H-Tilt Survivor Law Formalization

## Executive Result

The Lean file compiled with exit code 0 under Lean 4.28.0 and pinned Mathlib
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`. It contains no proof
placeholders or target-specific axioms. Tiers 1, 2, and 3 are
`VERIFIED_PROOF`. The bridge names are now aligned with their mathematical
content.

## Scope

The formalization uses a finite index type and a real-valued function
representation of the matrix. It assumes the left and right eigenvector
equations, nonzero entries of `h`, and a nonzero survivor normalization where
those hypotheses are needed. The geometric log-exp theorem assumes strict
positivity of `q(i)` and `piStar(i)`. The paper-native pointwise log-exp
theorem assumes `h(i) > 0`.

No Perron-Frobenius existence theorem is asserted or proved.

## Verified Theorems

- `htilt_unnormalized_stationary`
- `htilt_normalized_stationary`
- `doob_row_sum_zero`
- `geometric_bridge_one_eq_piStar`
- `geometric_bridge_nat_one_eq_piStar`
- `geometric_log_exp_bridge_eq_geometric_bridge`
- `multiplicative_bridge_nat_one_eq_piStar`
- `multiplicative_bridge_real_one_eq_piStar`
- `multiplicative_log_exp_pointwise_eq`

The previous theorem names `power_bridge_one_eq_piStar`,
`power_bridge_nat_one_eq_piStar`, and `log_exp_bridge_eq_power` remain checked
compatibility theorems for the geometric API.

Supporting Kronecker-delta lemmas:

- `sum_delta_left`
- `sum_delta_right`
- `sum_mul_delta`
- `sum_delta_mul`

## Bridge Alignment Patch

The first Lean version used `powerBridge` for a geometric interpolation between
`q` and `piStar`. This patch separates that object from the paper-native
multiplicative bridge:

- `geometricBridge`
- `geometricLogExpBridge`
- `multiplicativeBridgeNat`
- `multiplicativeBridgeReal`

The old `powerBridge`, `powerBridgeNat`, and `logExpBridge` names remain
backward-compatible abbreviations of the geometric definitions. They do not
name the paper-native bridge.

The paper-native exact-containment theorems are
`multiplicative_bridge_nat_one_eq_piStar` and
`multiplicative_bridge_real_one_eq_piStar`. The real-exponent theorem is
stronger than the provisional contract: at `β = 1`, no positivity assumption
is needed. Positivity of `h(i)` is required only for the general real log-exp
identity `multiplicative_log_exp_pointwise_eq`.

## Corrected Claim Boundary

`C_HTILT_002` is `VERIFIED_PROOF` for the paper-native normalized
multiplicative bridge at `n = 1` and real `β = 1`.

`C_HTILT_003` is `VERIFIED_PROOF` for the positive-domain pointwise identity

```text
q_i * exp(β * log(h_i)) = q_i * h_i^β.
```

The geometric bridge theorems remain verified separately and are not used to
inflate the paper-native claim.

## Obstructions

None in the requested theorem tiers. The first attempt to install the
repository's separate Lean 4.30-rc2 Mathlib cache exhausted available disk
space. That environment failure was removed and bypassed with the small pinned
Lean 4.28 source-only project recorded beside this report; it is not a theorem
obstruction.

## Non-Claims

- No consciousness claim.
- No empirical h-band or universality claim.
- No scheduler claim.
- No Perron-Frobenius existence claim.
- No Markov-process construction or convergence claim.
- No empirical bridge optimality or universal β-band claim.

## Commands Run

From `experiments/continuation_claim_audit_lab/lean_project`:

```text
env MATHLIB_NO_CACHE_ON_UPDATE=1 lake update
```

Output: exit code 0; the manifest pinned Mathlib v4.28.0 at
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`.

```text
lake build Mathlib.Algebra.BigOperators.Field \
  Mathlib.Analysis.SpecialFunctions.Pow.Real \
  Mathlib.Data.Real.Basic \
  Mathlib.Tactic.FieldSimp \
  Mathlib.Tactic.Ring
```

Output:

```text
Build completed successfully (1957 jobs).
```

```text
lake env lean '/Users/heath/Documents/New project/examples/verifier_fixtures/lean/htilt_survivor_law.lean'
```

Output: exit code 0 with empty stdout/stderr.

```text
rg -n '\b(sorry|admit|axiom|unsafe)\b' \
  examples/verifier_fixtures/lean/htilt_survivor_law.lean
```

Output: exit code 1 with no matches, as expected.

From the repository root:

```text
python -m pytest -q tests/test_lean_htilt_survivor_law_artifacts.py
```

Output:

```text
8 passed in 39.25s
```

```text
python -m pytest -q
```

Output:

```text
1729 passed in 680.38s (0:11:20)
```

## Next Step

The separate Lean claim update preserves `C_HTILT_001` and records the
correctly scoped paper-native statements for `C_HTILT_002` and
`C_HTILT_003` as `VERIFIED_PROOF`. Empirical h-band, scheduler,
consciousness, and Perron-Frobenius existence claims remain outside the
theorem boundary.
