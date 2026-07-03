# Finite H-Tilt Shifted Stationarity Transfer v1

## Purpose

This artifact verifies that generator-style stationarity transfers through the
shift bridge to the shifted discrete Doob kernel.

## Statement

If

$$
\sum_i q_i h_i \widetilde L^K_{ij}=0,
$$

then for $A=cI+K$,

$$
\sum_i q_i h_i D^A_{ij}=q_jh_j.
$$

The normalized version follows under the additional nonzero survivor
normalization hypothesis.

## Reason

The shifted kernel decomposes as

$$
D^A_{ij}
=
\delta_{ij}
+\frac{\widetilde L^K_{ij}}{c+\lambda}.
$$

The generator-style term vanishes by assumption and the delta term selects
$q_jh_j$.

## What this closes

It closes stationarity transfer from the generator-style object to the
shifted discrete object.

## What remains open

- irreducibility transfer;
- PF invocation on $A=cI+K$;
- Markov convergence, ergodicity, mixing, and spectral gap;
- empirical or interpretive claims.

## Lean declarations

- `HTiltShiftBridge.shifted_stationarity_transfer`
- `HTiltShiftBridge.shifted_normalized_stationarity_transfer`

Source:
`examples/verifier_fixtures/lean/htilt_shift_bridge.lean`

## Follow-up artifact

`finite_htilt_construct_shift_c_v1` constructs
$c=\sum_i |K_{ii}|$ and verifies entrywise nonnegativity of $A=cI+K$ under
off-diagonal nonnegativity. Perron–Frobenius and irreducibility claims remain
outside both artifacts.
