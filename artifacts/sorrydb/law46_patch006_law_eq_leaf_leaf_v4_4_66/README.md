# SorryDB v4.4.66 — Law46 Patch006 law equality variants

Patch002 solved:

    obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := ...

Patch005 solved:

    have hxy : x ≠ y := ...

Patch006 attacks:

    rw [show L = Lf x ≃ Lf y from sorry]

Goal: show the whole law `L` equals the leaf law `Lf x ≃ Lf y` using `hlhs : L.lhs = Lf x` and `hy : L.rhs = Lf y`.
