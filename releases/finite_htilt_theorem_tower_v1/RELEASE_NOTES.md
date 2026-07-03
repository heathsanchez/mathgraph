# Finite H-Tilt Survivor Law: Verified Theorem Tower v1

## Executive Summary

This release freezes a three-layer verified theorem tower for finite H-Tilt
survivor laws. It separates conditional generator algebra, conditional
discrete Doob algebra, and a discrete Perron–Frobenius existence portal.

## What Is Verified

### Layer 1 — Conditional killed-generator algebra

`finite_htilt_survivor_law_v1` verifies the generator-style survivor
cancellation and zero-row-sum identity from explicit left and right
eigen-equations. The modes are assumptions.

### Layer 2 — Conditional discrete Doob algebra

`finite_htilt_discrete_doob_stationary_v1` verifies stationarity and row
normalization for

```text
D_ij = A_ij h_j / (rho h_i).
```

Under explicit positivity and nonnegativity hypotheses, `D` is nonnegative and
row-stochastic and `piStar ∝ q ⊙ h` is a strictly positive normalized
stationary distribution.

### Layer 3 — Perron–Frobenius discrete portal

`finite_htilt_pf_discrete_survivor_law_v1` verifies that a finite irreducible
nonnegative real matrix admits `rho > 0` and strictly positive right and
transpose-right modes. Their shared Perron eigenvalue discharges Layer 2's
assumptions.

## Trust Boundary

- Layers 1 and 2 compile under Lean 4.28.0 and pinned Mathlib
  `8f9d9cff6bd728b17a24e163c9402775d9e6a365`.
- Layer 3 compiles under HopfieldNet commit
  `0bbb8999d1703776516f37f412334e01e07a30a0`, Lean 4.27.0-rc1, and Mathlib
  `ae0143cded18d09875e12c3056f428090484d9a4`.
- The project proof files contain no `sorry`, `admit`, custom `axiom`, or
  `unsafe`.
- The promoted PF theorem's axiom audit has no `sorryAx`.
- The external subtree contains one unrelated `sorry`; this release claims a
  clean dependency graph for the promoted theorem, not global cleanliness of
  the external repository.

## What Is Not Claimed

- a killed-generator bridge;
- Markov convergence;
- ergodicity, mixing, or a spectral gap;
- empirical h-band universality;
- consciousness;
- scheduler performance.

## Replay

See [replay_commands.md](replay_commands.md).

## Papers

- Main survivor-law note:
  `papers/finite_htilt_survivor_law/finite_htilt_survivor_law.tex`
- PF portal addendum:
  `papers/finite_htilt_pf_portal/finite_htilt_pf_portal.tex`

See [paper_bundle_index.md](paper_bundle_index.md) for scope and publication
order.

## Next Theorem Boundary

`killed_generator_bridge_from_discrete_pf` remains open. Candidate future
portals are a verified shift, exponential, or resolvent bridge. This release
does not select among them.
