# MathGraph SorryDB v4.8.13 — Chapter04 trivialInvo Zagier Parity Probe

## Correction

The direct candidate `(k, 1, 1)` is not fixed by `trivialInvo`; it maps to `(1, k, 1)`.

## Portal

Use the parity argument from `Archive/ZagierTwoSquares.lean`:

    Equiv.Perm.card_fixedPoints_modEq

Compare fixed points of `trivialInvo` and `secondInvo` modulo 2. Since `secondInvo` has exactly one fixed point, `trivialInvo` must have a fixed point.

## Acceptance rule

Build must pass and file sorry/admit count must decrease.
