# Finite H-Tilt Shift Bridge

## Status

`VERIFIED_PROOF`

## Verified claim

Define $A=cI+K$. Lean verifies:

1. right eigenmodes shift from $K$ to $A$ with eigenvalue
   $\rho=c+\lambda$;
2. left eigenmodes shift by the same amount;
3. the discrete Doob kernel of $A$ is related to the generator-style
   transform of $K$ by

   $$
   D^A_{ij}=\delta_{ij}
     +\frac{\widetilde L^K_{ij}}{c+\lambda};
   $$

4. $A$ is entrywise nonnegative under explicit off-diagonal nonnegativity and
   diagonal-shift hypotheses.

## Lean boundary

- Lean: 4.28.0
- Mathlib: `8f9d9cff6bd728b17a24e163c9402775d9e6a365`
- Source:
  `examples/verifier_fixtures/lean/htilt_shift_bridge.lean`
- The proof is finite and algebraic.
- The bridge theorem assumes `c + lam ≠ 0` and nonzero entries of `h`.
- Nonnegativity is conditional on explicit off-diagonal and diagonal-shift
  hypotheses; this artifact does not construct `c`.

## Non-claims

This does not prove the full killed-generator PF bridge. It does not prove
irreducibility transfer, invoke the PF portal, or prove convergence,
ergodicity, mixing, a spectral gap, empirical h-band universality,
consciousness, or scheduler performance.
