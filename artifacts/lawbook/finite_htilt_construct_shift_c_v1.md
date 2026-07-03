# Finite H-Tilt Constructed Diagonal Shift

## Status

`VERIFIED_PROOF`

## Verified claim

For finite $I$ and a real operator $K : I \to I \to \mathbb R$, define

$$
c=\sum_i |K_{ii}|.
$$

Lean verifies:

$$
\forall i,\quad 0\le K_{ii}+c.
$$

If additionally $K_{ij}\ge 0$ for $i\ne j$, then

$$
\forall i,j,\quad 0\le (cI+K)_{ij}.
$$

## Lean boundary

This constructs a nonnegative shifted operator under explicit off-diagonal
nonnegativity. The witness is finite and uses only the absolute values of
diagonal entries.

## Non-claims

This does not prove irreducibility transfer, PF invocation,
eigenvalue/Perron-root alignment, convergence, ergodicity, mixing, a spectral
gap, or empirical or interpretive claims.
