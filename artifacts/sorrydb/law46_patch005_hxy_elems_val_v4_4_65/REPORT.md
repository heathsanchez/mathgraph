# SorryDB v4.4.65 — Law46 Patch005 hxy elems.val Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Prior Accepted Partial

Patch002 accepted the first local sorry:

    obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := ...

## Patch005 Goal

Replace:

    have hxy : x ≠ y := sorry

using `elems.val`, avoiding the subtype-membership obstruction from Patch004.

## Variant Results

- v01_rw_then_elems_val_exact: rc=1, seconds=40.08, error=True, warning=False
- v02_rw_then_apply_elems_val: rc=1, seconds=5.13, error=True, warning=False
- v03_rw_then_have_notmem: rc=1, seconds=2.71, error=True, warning=False
- v04_subst_then_elems_val: rc=1, seconds=3.11, error=True, warning=False
- v05_original_hDisjoint_elems_val_no_rw: rc=1, seconds=2.54, error=True, warning=False
- v06_original_apply_elems_val_no_rw: rc=1, seconds=2.38, error=True, warning=False
- v07_use_elems_spec_mem_leaf: rc=0, seconds=2.46, error=False, warning=True

## Status

PATCH005_ACCEPTED_WITH_REMAINING_SORRIES

## Accepted Variant

v07_use_elems_spec_mem_leaf

## Obstruction

NONE

## Next Move

If accepted, carry Patch002 + Patch005 forward and attack:

    rw [show L = Lf x ≃ Lf y from sorry]

Likely next route:

    show the whole law `L` equals `Lf x ≃ Lf y` using extensionality or cases on `L` plus `hlhs` and `hy`.
