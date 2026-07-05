# SorryDB v4.4.67 — Law46 Patch007 toFin Law2 variants

Accepted partials carried forward:

- Patch002: proves rhs is a leaf in the leaf/leaf case.
- Patch005: proves x ≠ y using `elems` membership specification.
- Patch006: proves `L = Lf x ≃ Lf y`.

Patch007 attacks:

    have : (Lf x ≃ Lf y).toFin.toNat = Law2 := by
      sorry

This is the final local leaf-case conversion before `Equation2_implies Law46`.
