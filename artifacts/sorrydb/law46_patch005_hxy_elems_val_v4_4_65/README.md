# SorryDB v4.4.65 — Law46 Patch005 hxy elems.val variants

Patch004 showed that direct membership in `↑(Lf x).elems` fails because `elems` is a subtype.

New route:

    use `(Lf x).elems.val`

rather than `↑(Lf x).elems`.

Goal remains:

    have hxy : x ≠ y := sorry
