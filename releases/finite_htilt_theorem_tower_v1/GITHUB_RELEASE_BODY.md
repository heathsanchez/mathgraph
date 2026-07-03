# Finite H-Tilt Survivor Law: Verified Theorem Tower v1

This release records a three-layer Lean-verified theorem tower for finite
H-Tilt survivor laws.

## Verified layers

### Layer 1 — Conditional killed-generator-style algebra

Given explicit finite real-valued data and left/right eigen-equations, the
survivor weight and normalized survivor identity are verified for the
generator-style Doob transform.

Artifact:
`artifacts/lawbook/finite_htilt_survivor_law_v1.json`

### Layer 2 — Conditional discrete Doob algebra

For the discrete Doob transform

$$
D_{ij} = \frac{A_{ij}h_j}{\rho h_i},
$$

Lean verifies row-stochasticity and a positive normalized stationary
distribution under explicit eigenmode, positivity, and nonnegativity
assumptions.

Artifact:
`artifacts/lawbook/finite_htilt_discrete_doob_stationary_v1.json`

### Layer 3 — Perron–Frobenius discrete portal

For finite irreducible nonnegative matrices, a quarantined exact-pin
Perron–Frobenius portal supplies positive modes $h,q$ and $\rho>0$. The
resulting discrete Doob matrix is row-stochastic, and

$$
\pi^*_i = \frac{q_i h_i}{\sum_k q_k h_k}
$$

is a strictly positive normalized stationary distribution.

Artifact:
`artifacts/lawbook/finite_htilt_pf_discrete_survivor_law_v1.json`

## Trust boundary

Layers 1 and 2 compile under the main Lean 4.28.0 environment.

Layer 3 compiles under the quarantined HopfieldNet exact-pin environment:

- HopfieldNet commit: `0bbb8999d1703776516f37f412334e01e07a30a0`
- Lean: `4.27.0-rc1`
- Mathlib: `ae0143cded18d09875e12c3056f428090484d9a4`

The promoted PF theorem has no `sorryAx` dependency by Lean axiom audit. The
external PF subtree contains one unrelated `sorry`; this release claims a
clean dependency graph for the promoted theorem, not global
placeholder-freedom of the external repository.

## What this release does not claim

This release does not prove:

- a killed-generator bridge;
- Markov convergence;
- ergodicity;
- mixing;
- a spectral gap;
- empirical h-band universality;
- consciousness;
- scheduler performance.

## Replay

See:
`releases/finite_htilt_theorem_tower_v1/replay_commands.md`

## Papers and docs

- Theorem tower: `docs/finite_htilt_theorem_tower.md`
- Release overview: `docs/finite_htilt_release_v1.md`
- Main note: `papers/finite_htilt_survivor_law/finite_htilt_survivor_law.tex`
- PF portal addendum: `papers/finite_htilt_pf_portal/finite_htilt_pf_portal.tex`

## Tag

`finite-htilt-theorem-tower-v1`
