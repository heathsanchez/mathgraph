# SorryDB v4.4.64 — Law46 Patch004 hxy implicit-disjoint variants

Patch003 exposed the exact obstruction.

After rewriting `hlhs` and `hy`, Lean gives:

    hDisjoint : ∀ ⦃a : ℕ⦄, a ∈ ↑(Lf x).elems → a ∉ ↑(Lf y).elems

The error was caused by applying `hDisjoint x`, but `x` is implicit.
Patch004 tests direct implicit application with membership proofs.
