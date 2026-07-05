# SorryDB v4.4.68 — Law46 Patch008 toFin Law2 with +revert

Patch007 obstruction:

    Expected type must not contain free variables
      (Lf x ≃ Lf y).toFin.toNat = Law2

Lean suggested:

    Use the `+revert` option

Patch008 tests `decide +kernel +revert` and nearby variants.
