# Finite H-Tilt Construct Shift c v1

## Purpose

This artifact verifies an explicit finite diagonal shift that makes $A=cI+K$
entrywise nonnegative under off-diagonal nonnegativity.

## Statement

For finite $I$ and a real operator $K$, define

$$
c=\sum_i |K_{ii}|.
$$

Then

$$
\forall i,\quad 0\le K_{ii}+c.
$$

If

$$
i\ne j \Longrightarrow 0\le K_{ij},
$$

then

$$
\forall i,j,\quad 0\le (cI+K)_{ij}.
$$

## Why this matters

This closes the “construct suitable $c$” boundary needed before applying a
discrete Perron–Frobenius portal to $A=cI+K$.

## What remains open

- irreducibility transfer;
- PF invocation on $A=cI+K$;
- Perron-root alignment for $c+\lambda$;
- Markov convergence, ergodicity, mixing, and spectral gap;
- empirical or interpretive claims.

## Lean declarations

- `HTiltShiftBridge.diagonalAbsShift`
- `HTiltShiftBridge.diagonalAbsShift_nonneg`
- `HTiltShiftBridge.diagonal_le_diagonalAbsShift`
- `HTiltShiftBridge.diagonal_shift_nonneg_of_diagonalAbsShift`
- `HTiltShiftBridge.exists_shift_makes_diagonal_nonneg`
- `HTiltShiftBridge.shiftedOperator_nonneg_of_offdiag_with_diagonalAbsShift`
- `HTiltShiftBridge.exists_shift_makes_shiftedOperator_nonneg`

Source:
`examples/verifier_fixtures/lean/htilt_shift_bridge.lean`
