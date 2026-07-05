# SorryDB v4.4.71 — Law46 direct-route scout

Patch010 established the obstruction:

`Law2.toFin` and `(Lf x ≃ Lf y).toFin.toFin` live over different dependent `Fin (elems.length)` types.

Therefore this run stops trying to prove `toFin.toNat = Law2` directly. It inspects the downstream Law46 proof body and available definability / implication APIs, then tests direct replacements of the Law2-normalization section.
