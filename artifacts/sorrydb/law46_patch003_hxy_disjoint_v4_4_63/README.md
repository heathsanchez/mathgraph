# SorryDB v4.4.63 — Law46 Patch003 hxy Disjointness Variants

Patch002 accepted the first Law46 leaf-case sorry.

This run carries Patch002 forward and attacks the next sorry:

    have hxy : x ≠ y := sorry

Expected proof idea:

If `x = y`, then the same variable appears in both `L.lhs.elems` and `L.rhs.elems`.
But `hDisjoint` says those lists are disjoint. Contradiction.

This run tests several Lean formulations because the exact shape of `List.Disjoint` / `elems` is the current obstruction boundary.
