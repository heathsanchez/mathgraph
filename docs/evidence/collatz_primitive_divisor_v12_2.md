# Collatz Primitive Divisor v12.2

Canonical evidence pack:
`examples/evidence_packs/collatz_primitive_divisor_v12_2/`

## Status

This is not a Collatz proof. It is a fixation-stage candidate-law result and a
proof-template extraction target.

## Metrics

- pairs processed: `5,000`
- primitive growth pairs: `4,999`
- partial primitive growth pairs: `0`
- primitive growth pair rate: `0.9998`
- positive novelty rate: `0.9998009090909091`
- average pair median novelty ratio: `0.9987621562844179`
- median pair median novelty ratio: `0.9991694347067428`
- total exact excluded count: `1,100,000`
- total integer candidate count: `0`
- integer candidate rate: `0.0`
- remaining CSV rows: `1`

## Obstruction

`UNCANCELLED_PRIMITIVE_DIVISOR_GROWTH`

For nontrivial prefix-tail inverse Collatz families `U * W^r`, the reduced
denominator `R_r = D_r / gcd(D_r, N_r)` persistently contains fresh uncancelled
divisor mass as `r` grows, preventing integer fixed points except known
trivial or degenerate cases.

The one preserved residual is `LOW_NOVELTY_RECURRENCE_RESIDUAL`.

## Trust Boundary

The pack promotes an obstruction to a proof-template candidate, not to a
theorem. It does not prove Collatz, and failed search does not become TRUE.
