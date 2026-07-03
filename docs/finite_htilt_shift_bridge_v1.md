# Finite H-Tilt Shift Bridge v1

## Purpose

This artifact verifies the algebraic adapter from the generator-style H-Tilt
operator to the discrete Doob setting.

## Bridge

Let $A=cI+K$ and $\rho=c+\lambda$. Under the explicit nonzero-denominator
hypotheses in the Lean theorem,

$$
D^A_{ij}
=
\delta_{ij}+\frac{\widetilde L^K_{ij}}{c+\lambda}.
$$

The same shift preserves left and right eigenmodes while changing their
eigenvalue from $\lambda$ to $c+\lambda$.

## What this closes

It closes the algebraic adapter boundary between Layer 1 and Layer 2 of the
released theorem tower. It also verifies entrywise nonnegativity of $A$ from
explicit off-diagonal nonnegativity and diagonal-shift hypotheses.

## What remains open

- irreducibility transfer;
- PF invocation on $A=cI+K$;
- Markov convergence, ergodicity, mixing, and spectral gap;
- empirical or interpretive claims.

## Lean declarations

- `HTiltShiftBridge.sum_delta_mul`
- `HTiltShiftBridge.sum_mul_delta`
- `HTiltShiftBridge.shifted_right_eigen`
- `HTiltShiftBridge.shifted_left_eigen`
- `HTiltShiftBridge.shifted_doob_bridge`
- `HTiltShiftBridge.shiftedOperator_nonneg`

Source:
`examples/verifier_fixtures/lean/htilt_shift_bridge.lean`

## Boundary

This is a finite algebraic bridge. It does not prove Perron–Frobenius
existence for killed generators, irreducibility transfer, or stochastic
convergence.

## Follow-up artifact

`finite_htilt_shift_stationarity_transfer_v1` verifies that generator-style
stationarity transfers to the shifted discrete Doob kernel through the bridge
identity. It remains independent of shift construction, irreducibility
transfer, and Perron–Frobenius invocation.

`finite_htilt_construct_shift_c_v1` supplies the explicit finite witness
$c=\sum_i |K_{ii}|$, which makes $A=cI+K$ entrywise nonnegative under
off-diagonal nonnegativity. It does not prove irreducibility transfer or
invoke Perron–Frobenius.
