# PF Port Lab Report

## Executive Result

**Classification: `NEW_VERIFIED_PF_PORTAL`.**

The bounded sprint produced both intended gains:

1. a Lean-verified conditional discrete Doob stationarity kernel in the main
   Lean 4.28.0 environment; and
2. a Lean-verified Perron–Frobenius existence portal in the quarantined
   external repository's exact-pin environment.

The portal supplies strictly positive right and transpose-right modes with a
shared positive Perron eigenvalue and proves that their pointwise product is
stationary for the discrete Doob transform.

No killed-generator, convergence, ergodicity, mixing, or empirical claim is
made.

## External Repo Build

- Repository: [mkaratarakis/HopfieldNet](https://github.com/mkaratarakis/HopfieldNet)
- Commit: `0bbb8999d1703776516f37f412334e01e07a30a0`
- Lean: 4.27.0-rc1
- Mathlib: `ae0143cded18d09875e12c3056f428090484d9a4`

Build results:

```text
MCMC.PF.LinearAlgebra.Matrix.PerronFrobenius.Irreducible
  passed — 3239 jobs

MCMC.PF.LinearAlgebra.Matrix.PerronFrobenius.Dominance
  passed — 3245 jobs
```

The earlier Reservoir failure badge did not reproduce for these targeted
modules when the exact manifest, toolchain, and Mathlib cache were used.

## Minimal PF Dependency Closure

The PF subtree contains 16 Lean files. The built route used 12 external files,
listed in `pf_port_obstruction_trace.md`, and stayed below the 20-file kill
condition.

Key declarations:

- `Matrix.exists_positive_eigenvector_of_irreducible`
- `Matrix.perron_root_eq_positive_eigenvalue`
- `Matrix.perronRoot_transpose_eq`
- `Matrix.IsIrreducible.transpose`

The route is:

```text
PF(A) -> positive rho,h
PF(A transpose) -> positive rhoT,q
perronRoot_transpose_eq -> rhoT = rho
discrete cancellation -> q*h stationary for Doob(A,rho,h)
```

## Port Attempt

The experiment did not modify main project dependencies. It quarantined the
external checkout under `experiments/pf_port_lab/vendor/HopfieldNet/`, ignored
that checkout in Git, and compiled the portal file against the external
environment.

The first cache attempt exhausted disk space. After removing only disposable
cache/build/doc data, the exact cache and both targeted modules built
successfully.

For the normalized theorem replay, the cache was restricted to the 30 direct
Mathlib roots of the external closure. This downloaded 3,218 cached files
instead of the full 7,868-file library cache and reproduced the successful
`Dominance` build within disk limits.

## Conditional Discrete Doob Theorem

The file
`examples/verifier_fixtures/lean/htilt_discrete_doob_stationary.lean` compiles
under Lean 4.28.0 with pinned Mathlib
`8f9d9cff6bd728b17a24e163c9402775d9e6a365`.

It verifies:

- `discrete_doob_unnormalized_stationary`
- `discrete_doob_normalized_stationary`
- `discrete_doob_row_sum_one`

Lawbook entry:
`finite_htilt_discrete_doob_stationary_v1` (`VERIFIED_PROOF`).

Its scope remains conditional: it assumes the eigenmodes.

## PF Existence Portal

The file
`examples/verifier_fixtures/lean/htilt_pf_discrete_survivor_law.lean` compiles
under the external exact pins.

The theorem
`exists_positive_survivor_weight_of_irreducible` proves that an irreducible
nonnegative finite real matrix admits:

- `rho > 0`;
- a strictly positive right eigenmode `h`;
- a strictly positive transpose-right mode `q`;
- one shared eigenvalue `rho`; and
- stationary unnormalized survivor weight `q_i h_i`.

The stronger theorem
`exists_positive_stationary_distribution_of_irreducible` additionally proves
that the discrete Doob transform is nonnegative and row-stochastic and that
the normalized `piStar` is strictly positive, sums to one, and is stationary.

Lawbook entry:
`finite_htilt_pf_discrete_survivor_law_v1` (`VERIFIED_PROOF`).

An exact `#print axioms` check on the stronger theorem reports only `propext`, `Classical.choice`, and
`Quot.sound`; it does not report `sorryAx`. The external PF source subtree does
contain one unrelated `sorry`, so the artifact claims a clean dependency graph
for this theorem, not global cleanliness of the external project.

## Lawbook Updates

- `finite_htilt_discrete_doob_stationary_v1` — `VERIFIED_PROOF`
- `finite_htilt_pf_discrete_survivor_law_v1` — `VERIFIED_PROOF`

The existing `finite_htilt_survivor_law_v1` is unchanged and remains the
conditional killed-generator algebraic kernel.

## Kill Conditions

No hard kill condition was hit:

- built external closure: 12 files, below 20;
- no broad Mathlib source modification;
- external PF modules build at their own pins;
- transpose-root equality is available;
- main Lean project was not changed or broken.

The disk incident was recoverable infrastructure pressure, not a theorem or
scope failure.

## Verification

- Focused release, theorem-tower, paper, and port-lab tests: `24 passed`
- Full repository regression: `1774 passed`

## Next Step

Freeze a reproducible minimal source bundle for the 12-file closure or port
that closure to the main Lean 4.28.0 pin. Then add normalized positivity and row
stochasticity directly to the PF portal by invoking the conditional discrete
kernel. Keep the killed-generator bridge as a separate future theorem.
