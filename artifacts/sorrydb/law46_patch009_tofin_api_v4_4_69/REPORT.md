# SorryDB v4.4.69 — Law46 Patch009 toFin API Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Prior Accepted Partials

Patch002 accepted rhs-is-leaf.
Patch005 accepted hxy : x ≠ y.
Patch006 accepted L = Lf x ≃ Lf y.

## Patch009 Goal

Replace:

    have : (Lf x ≃ Lf y).toFin.toNat = Law2 := by
      sorry

by inspecting the actual `toFin`/`toNat` API and testing explicit variants.

## Micro Recon

- micro_returncode: 1

### Micro Tail

equational_theories/Definability/Law46ToFinRecon.lean:1:0: error: unknown module prefix 'equational_theories'

No directory 'equational_theories' or file 'equational_theories.olean' in the search path entries:
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/Cli/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/batteries/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/Qq/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/aesop/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/proofwidgets/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/importGraph/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/LeanSearchClient/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/plausible/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/mathlib/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/packages/checkdecls/.lake/build/lib/lean
/private/tmp/sorrydb_law46_patch009_v4_4_69/.lake/build/lib/lean
/Users/heath/.elan/toolchains/leanprover--lean4---v4.29.1/lib/lean
/Users/heath/.elan/toolchains/leanprover--lean4---v4.29.1/lib/lean

info: checkdecls: cloning https://github.com/PatrickMassot/checkdecls.git
info: checkdecls: checking out revision '3d425859e73fcfbef85b9638c2a91708ef4a22d4'
info: mathlib: cloning https://github.com/leanprover-community/mathlib4.git
info: mathlib: checking out revision '5e932f97dd25535344f80f9dd8da3aab83df0fe6'
info: plausible: cloning https://github.com/leanprover-community/plausible
info: plausible: checking out revision '83e90935a17ca19ebe4b7893c7f7066e266f50d3'
info: LeanSearchClient: cloning https://github.com/leanprover-community/LeanSearchClient
info: LeanSearchClient: checking out revision 'c5d5b8fe6e5158def25cd28eb94e4141ad97c843'
info: importGraph: cloning https://github.com/leanprover-community/import-graph
info: importGraph: checking out revision '48d5698bc464786347c1b0d859b18f938420f060'
info: proofwidgets: cloning https://github.com/leanprover-community/ProofWidgets4
info: proofwidgets: checking out revision '4dd0959c44d1af0462bd604d0f87c5781307d709'
info: aesop: cloning https://github.com/leanprover-community/aesop
info: aesop: checking out revision '7152850e7b216a0d409701617721b6e469d34bf6'
info: Qq: cloning https://github.com/leanprover-community/quote4
info: Qq: checking out revision '707efb56d0696634e9e965523a1bbe9ac6ce141d'
info: batteries: cloning https://github.com/leanprover-community/batteries
info: batteries: checking out revision '756e3321fd3b02a85ffda19fef789916223e578c'
info: Cli: cloning https://github.com/leanprover/lean4-cli
info: Cli: checking out revision '7802da01beb530bf051ab657443f9cd9bc3e1a29'


## Variant Results

- v01_unfold_MagmaLaw_toFin_toNat: rc=1, seconds=66.18, error=True, warning=False
- v02_unfold_MagmaLaw_toFin_toNat_decide: rc=1, seconds=5.45, error=True, warning=False
- v03_show_map_goal_unfold_toFin: rc=1, seconds=5.83, error=True, warning=False
- v04_specialize_by_cases_x_y_then_native: rc=1, seconds=2.98, error=True, warning=False
- v05_match_x_y_decEq_then_decide: rc=1, seconds=2.79, error=True, warning=False
- v06_use_congr_after_toFin_eval_zero_one: rc=1, seconds=2.88, error=True, warning=False
- v07_try_original_commented_route: rc=1, seconds=2.9, error=True, warning=False
- v08_try_tofin_tofin_eq: rc=1, seconds=3.62, error=True, warning=True
- v09_try_aesop_after_unfold: rc=1, seconds=2.77, error=True, warning=True
- v10_try_simp_all_after_unfold: rc=1, seconds=3.36, error=True, warning=False

## Status

PATCH009_REJECTED_OBSTRUCTION

## Accepted Variant

None

## Obstruction

## v01_unfold_MagmaLaw_toFin_toNat
error: equational_theories/Definability/Law46.lean:46:6: `simp` made no progress
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v02_unfold_MagmaLaw_toFin_toNat_decide
error: equational_theories/Definability/Law46.lean:46:6: Expected type must not contain free variables
  map (fun x_1 ↦ ↑x_1)
      (map (⇑(map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).finEquiv.symm)
        (map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).attach) =
    Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v03_show_map_goal_unfold_toFin
error: equational_theories/Definability/Law46.lean:47:6: `simp` made no progress
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v04_specialize_by_cases_x_y_then_native
error: equational_theories/Definability/Law46.lean:47:8: Expected type must not contain free variables
  (Lf x ≃ Lf y).toFin.toNat = Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v05_match_x_y_decEq_then_decide
error: equational_theories/Definability/Law46.lean:51:22: Expected type must not contain free variables
  ¬0 = y + 1 → (Lf 0 ≃ Lf (y + 1)).toFin.toNat = Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: equational_theories/Definability/Law46.lean:55:20: Expected type must not contain free variables
  ¬x + 1 = 0 → (Lf (x + 1) ≃ Lf 0).toFin.toNat = Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: equational_theories/Definability/Law46.lean:61:14: Expected type must not contain free variables
  ¬x + 1 = y + 1 → (Lf (x + 1) ≃ Lf (y + 1)).toFin.toNat = Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v06_use_congr_after_toFin_eval_zero_one
error: equational_theories/Definability/Law46.lean:46:6: `simp` made no progress
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v07_try_original_commented_route
error: equational_theories/Definability/Law46.lean:46:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:48:6: `simp` made no progress
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v08_try_tofin_tofin_eq
error: equational_theories/Definability/Law46.lean:45:58: Type mismatch
  Law2
has type
  NatMagmaLaw
but is expected to have type
  MagmaLaw (Fin 2)
error: equational_theories/Definability/Law46.lean:45:87: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
⊢ map (⇑(map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).finEquiv.symm)
      (map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).attach =
    sorry ()
error: equational_theories/Definability/Law46.lean:48:6: Tactic `assumption` failed

L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
h₂ : (Lf x ≃ Lf y).toFin.toFin = sorry
⊢ map (fun x_1 ↦ ↑x_1) (sorry ()) = Law2
warning: equational_theories/Definability/Law46.lean:47:14: This simp argument is unused:
  hxy

Hint: Omit it from the simp argument list.
  simp ̵[̵h̵x̵y̵]̵

Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v09_try_aesop_after_unfold
warning: equational_theories/Definability/Law46.lean:46:6: aesop: failed to prove the goal after exhaustive search.
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : ¬x = y
⊢ map (fun x_1 ↦ ↑x_1)
      (map (⇑(map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).finEquiv.symm)
        (map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).attach) =
    Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v10_try_simp_all_after_unfold
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : ¬x = y
⊢ map (fun x_1 ↦ ↑x_1)
      (map (⇑(map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).finEquiv.symm)
        (map (⇑(Lf x ≃ Lf y).finEquiv.symm) (Lf x ≃ Lf y).attach).attach) =
    Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed

## Next Move

If accepted, carry Patch002 + Patch005 + Patch006 + Patch009 and verify the leaf/leaf branch.

If rejected, the next step is no longer blind variants. Use the exact `tofin_micro` output and `grep_recon.json` to write a dedicated lemma for the leaf/leaf `toFin.toNat = Law2` fact.
