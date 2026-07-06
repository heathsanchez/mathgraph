# MathGraph SorryDB v4.8.16 — Park Chapter04 Involution Parity Boundary

## Target family

`mo271/FormalBook`, `FormalBook/Chapter_04.lean`

Targets probed:

- `sameCard`
- `trivialInvo_fixedPoints`

## Result

No certified no-sorry proof found.

## Important correction

v4.8.10 produced a false positive because Lean accepted a replacement that still contained `sorry`.

From v4.8.11 onward, acceptance requires:

1. `lake build <module>` returns 0;
2. replacement contains no `sorry` or `admit`;
3. total file sorry/admit count decreases.

## Obstruction

Named obstruction:

    dependent-subtype involution parity boundary

## Why parked

The proof appears to require the full Zagier parity route:

    Equiv.Perm.card_fixedPoints_modEq

plus a correctly typed square proof for `trivialInvo` and `secondInvo` in the exact power shape required by the theorem.

This is no longer a micro-repair. It is a focused proof-session target.

## Status

Classify Chapter04 involution targets as:

    PARK_COMPLEX_OR_THEOREM_SCALE

until a dedicated parity/involution lemma is built.

## Lawbook update

Build success alone is not certification for sorry repair.

A proof repair is certified only when:

    build_success && no_new_sorry && sorry_count_decreases
