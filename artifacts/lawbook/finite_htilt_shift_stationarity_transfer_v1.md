# Finite H-Tilt Shifted Stationarity Transfer

## Status

`VERIFIED_PROOF`

## Verified claim

If

$$
\sum_i q_i h_i \widetilde L^K_{ij}=0,
$$

then for $A=cI+K$,

$$
\sum_i q_i h_i D^A_{ij}=q_jh_j.
$$

The proof uses the previously verified bridge:

$$
D^A_{ij}
=
\delta_{ij}+\frac{\widetilde L^K_{ij}}{c+\lambda}.
$$

Lean also verifies the normalized corollary when
$\sum_k q_kh_k\ne 0$.

## Lean boundary

- Lean: 4.28.0
- Mathlib: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`
- Source:
  `examples/verifier_fixtures/lean/htilt_shift_bridge.lean`
- The bridge denominator `c + lam` and required entries of `h` are assumed
  nonzero.
- Generator-style stationarity is an explicit hypothesis.

## Non-claims

This does not construct $c$, prove irreducibility transfer, invoke
Perron–Frobenius, or prove convergence, ergodicity, mixing, a spectral gap,
empirical h-band universality, consciousness, or scheduler performance.
