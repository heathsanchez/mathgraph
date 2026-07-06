# MathGraph SorryDB v4.8.22 - Publish FormalBook Chapter03 Two-Omega PR

## Patch

Repository:

    mo271/FormalBook

File:

    FormalBook/Chapter_03.lean

Branch:

    heathsanchez:fix-chapter03-local-arithmetic-omega

Patch:

    have h_3lel : 3 ≤ l := by
      omega

and

    have h_2k'len : 2 * k' ≤ n := by
      omega

## Local verifier

    lake build FormalBook.Chapter_03

## Certification result

The combined patch was previously certified in v4.8.21:

    rc = 0
    sorry_delta = -2

This publish run rechecks before pushing.

## Certification rule

Certified iff:

    build_success
    and no new sorry/admit
    and sorry/admit count decreases
