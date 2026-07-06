# MathGraph SorryDB v4.8.19B - Disk-Safe FormalBook Chapter03 Bullet-Regex Probe

## Correction from v4.8.19

The regex missed `h_3lel` because the line begins with a Lean bullet:

    · have h_3lel : 3 ≤ l := by

This run uses a bullet-aware regex.

## Target

`FormalBook/Chapter_03.lean`

Local arithmetic holes:

1. `have h_3lel : 3 ≤ l := by sorry`
2. `have h_2k'len : 2 * k' ≤ n := by sorry`

## Disk-safe mode

This run reuses the persistent clone:

    external/FormalBook

It skips fresh clone/cache loops and stores only capped build tails.

## Certification rule

A variant is certified only if:

    lake build FormalBook.Chapter_03 succeeds
    and total file sorry/admit count decreases
