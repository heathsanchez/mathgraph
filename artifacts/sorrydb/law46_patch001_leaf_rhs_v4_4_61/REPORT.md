# SorryDB v4.4.61 — Law46 Patch001 Leaf RHS Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Patch Goal

Replace the first sorry:

    obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := sorry

with a case split on `L.rhs`.

## Verifier Judgment

- build_returncode: 1
- build_completed: False
- has_error: True
- has_warning: False
- remaining_sorry_warning: False
- seconds: 113.98

## Status

PATCH001_REJECTED_OBSTRUCTION

## Obstruction

error: equational_theories/Definability/Law46.lean:22:20: Application type mismatch: The argument
error: Lean exited with code 1
error: build failed

## Next Move

If accepted, patch the next leaf-case sorry:

    have hxy : x ≠ y := sorry

using `hDisjoint`, `hlhs`, and `hy`.

If rejected, inspect the exact shape of `hShape` after `rw [hlhs, hrhs]` and add the needed FreeMagma no-confusion route.
