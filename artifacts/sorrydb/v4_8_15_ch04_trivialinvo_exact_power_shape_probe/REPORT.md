# MathGraph SorryDB v4.8.15 — Chapter04 Exact Power-Shape Parity Probe

## Target

`trivialInvo_fixedPoints`

## Correction from v4.8.14

`Equiv.Perm.card_fixedPoints_modEq` expected square proofs in the shape:

    f ^ 2 ^ 1 = 1

not merely:

    f ^ 2 = 1

This probe coerces both `trivialInvo` and `secondInvo` square proofs into the exact shape before applying the parity theorem.

## Acceptance rule

Build passes and file sorry/admit count decreases.
