# MathGraph SorryDB v4.8.21 - Combined Chapter03 Two-Omega Patch

## Target

FormalBook/Chapter_03.lean

## Combined patch

Two independently certified arithmetic holes are patched together.

Patch 1:

    have h_3lel : 3 ≤ l := by
      omega

Patch 2:

    have h_2k'len : 2 * k' ≤ n := by
      omega

## Certification rule

Certified iff:

    lake build FormalBook.Chapter_03 succeeds
    and total file sorry/admit count decreases

## Prior certificates

- v4.8.19B certified h_3lel.
- v4.8.20R certified h_2k'len.
