# SorryDB v4.4.69 — Law46 Patch009 toFin API

Patch008 showed that `decide +revert` over-generalizes and fails to synthesize decidability for:

    ∀ x y, x ≠ y → (Lf x ≃ Lf y).toFin.toNat = Law2

Patch009 inspects the local API for `toFin`, `toNat`, and `Law2`, then tests explicit variants.
