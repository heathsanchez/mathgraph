# Finite H-Tilt Survivor Law Paper

This directory contains the short paper for the Lean-verified finite H-Tilt
survivor law.

## Main file

`finite_htilt_survivor_law.tex`

Supporting inputs:

- `claim_boundary_table.tex`
- `artifact_appendix.tex`

## Verified artifact

`examples/verifier_fixtures/lean/htilt_survivor_law.lean`

## Build

```bash
latexmk -pdf finite_htilt_survivor_law.tex
```

## Status

`VERIFIED_PROOF` for the finite algebraic survivor law and bridge identities.

## Non-claims

No empirical h-band, consciousness, scheduler, Perron-Frobenius existence,
Markov convergence, or empirical bridge optimality claim is made.
