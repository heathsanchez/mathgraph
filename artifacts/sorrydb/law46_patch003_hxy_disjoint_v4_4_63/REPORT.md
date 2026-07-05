# SorryDB v4.4.63 — Law46 Patch003 hxy Disjointness Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Prior Accepted Partial

Patch002 accepted the first local sorry:

    obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := ...

## Patch003 Goal

Replace:

    have hxy : x ≠ y := sorry

using disjointness of `L.lhs.elems` and `L.rhs.elems`.

## Variant Results

- v01_rw_List_Disjoint_direct: rc=1, seconds=49.12, error=True, warning=False
- v02_disjoint_direct_without_rw: rc=1, seconds=5.96, error=True, warning=False
- v03_simp_at_hDisjoint: rc=1, seconds=3.83, error=True, warning=True
- v04_simpa_List_Disjoint: rc=1, seconds=3.36, error=True, warning=False
- v05_not_disjoint_singletons: rc=1, seconds=2.88, error=True, warning=False
- v06_contradiction_after_simp: rc=1, seconds=4.13, error=True, warning=False

## Status

PATCH003_REJECTED_OBSTRUCTION

## Accepted Variant

None

## Obstruction

## v01_rw_List_Disjoint_direct
error: equational_theories/Definability/Law46.lean:32:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:33:20: failed to synthesize instance of type class
error: equational_theories/Definability/Law46.lean:36:22: Application type mismatch: The argument
error: Lean exited with code 1
error: build failed
## v02_disjoint_direct_without_rw
error: equational_theories/Definability/Law46.lean:31:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:32:20: failed to synthesize instance of type class
error: Lean exited with code 1
error: build failed
## v03_simp_at_hDisjoint
error: equational_theories/Definability/Law46.lean:27:24: unsolved goals
error: Lean exited with code 1
error: build failed
## v04_simpa_List_Disjoint
error: equational_theories/Definability/Law46.lean:30:6: Type mismatch: After simplification, term
error: Lean exited with code 1
error: build failed
## v05_not_disjoint_singletons
error: equational_theories/Definability/Law46.lean:33:22: Application type mismatch: The argument
error: Lean exited with code 1
error: build failed
## v06_contradiction_after_simp
error: equational_theories/Definability/Law46.lean:31:22: Application type mismatch: The argument
error: Lean exited with code 1
error: build failed

## Next Move

If accepted, carry Patch002 + Patch003 forward and attack:

    rw [show L = Lf x ≃ Lf y from sorry]

If rejected, use the best error to inspect the exact type of `hDisjoint` after rewriting `hlhs` and `hy`.
