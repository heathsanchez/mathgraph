# SorryDB v4.4.61 — Law46 Patch001 Leaf RHS

Target: `equational_theories/Definability/Law46.lean`

Goal: attack the first leaf-case sorry only:

    obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := sorry

Idea:

If `L.lhs = Lf x`, then `hShape` says that substituting all variables by `Lf 0` makes lhs and rhs equal. The lhs becomes `Lf 0`. If rhs were a fork, the rhs substituted by all `Lf 0` would still be a fork, impossible. Therefore rhs must be a leaf.

This is a bounded verifier-contact attempt, not a final proof.
