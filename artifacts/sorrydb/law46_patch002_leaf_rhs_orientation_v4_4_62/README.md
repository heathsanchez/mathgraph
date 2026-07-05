# SorryDB v4.4.62 — Law46 Patch002 Leaf RHS Orientation

Patch001 had the right case split but the wrong witness proof orientation.

Lean obstruction:

    hrhs : L.rhs = Lf y

But after case splitting on `L.rhs`, the existential witness proof was expected as a reflexive equality in the rewritten branch.

Patch002 uses:

    exact ⟨y, rfl⟩

in the leaf branch.
