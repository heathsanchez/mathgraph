# SorryDB v4.4.67 — Law46 Patch007 toFin Law2 Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Prior Accepted Partials

Patch002 accepted rhs-is-leaf.
Patch005 accepted hxy : x ≠ y.
Patch006 accepted L = Lf x ≃ Lf y.

## Patch007 Goal

Replace:

    have : (Lf x ≃ Lf y).toFin.toNat = Law2 := by
      sorry

## Variant Results

- v01_decide_kernel: rc=1, seconds=42.01, error=True, warning=False
- v02_native_decide: rc=1, seconds=3.94, error=True, warning=False
- v03_rfl: rc=1, seconds=2.77, error=True, warning=False
- v04_simp_hxy: rc=1, seconds=2.65, error=True, warning=False
- v05_unfold_toFin_simp_hxy: rc=1, seconds=3.53, error=True, warning=False
- v06_unfold_toNat_toFin_simp_hxy: rc=1, seconds=2.84, error=True, warning=True
- v07_with_elems_list: rc=1, seconds=2.49, error=True, warning=True
- v08_with_elems_val: rc=1, seconds=2.36, error=True, warning=True
- v09_convert_decide_after_subst_not_possible: rc=1, seconds=2.35, error=True, warning=True
- v10_aesop: rc=1, seconds=2.35, error=True, warning=True
- v11_try_simp_all: rc=1, seconds=2.68, error=True, warning=False
- v12_exact_original_hint_short: rc=1, seconds=2.48, error=True, warning=True

## Status

PATCH007_REJECTED_OBSTRUCTION

## Accepted Variant

None

## Obstruction

## v01_decide_kernel
error: equational_theories/Definability/Law46.lean:44:6: Expected type must not contain free variables
  (Lf x ≃ Lf y).toFin.toNat = Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v02_native_decide
error: equational_theories/Definability/Law46.lean:44:6: Expected type must not contain free variables
  (Lf x ≃ Lf y).toFin.toNat = Law2

Hint: Use the `+revert` option to automatically clean up and revert free variables
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v03_rfl
error: equational_theories/Definability/Law46.lean:44:6: Tactic `rfl` failed: The left-hand side
  (Lf x ≃ Lf y).toFin.toNat
is not definitionally equal to the right-hand side
  Law2

L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
⊢ (Lf x ≃ Lf y).toFin.toNat = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v04_simp_hxy
error: equational_theories/Definability/Law46.lean:44:6: `simp` made no progress
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v05_unfold_toFin_simp_hxy
error: equational_theories/Definability/Law46.lean:44:12: Unknown constant `Law.NatMagmaLaw.toFin`
error: equational_theories/Definability/Law46.lean:44:6: `simp` made no progress
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v06_unfold_toNat_toFin_simp_hxy
error: equational_theories/Definability/Law46.lean:44:12: Unknown constant `Law.NatMagmaLaw.toFin`
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
warning: equational_theories/Definability/Law46.lean:44:47: This simp argument is unused:
  hxy

Hint: Omit it from the simp argument list.
  simp [NatMagmaLaw.toFin, MagmaLaw.toNat,̵ ̵h̵x̵y̵]

Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v07_with_elems_list
error: equational_theories/Definability/Law46.lean:45:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:46:12: Unknown constant `Law.NatMagmaLaw.toFin`
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
h₁ : ↑(Lf x ≃ Lf y).elems = [x, y]
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
warning: equational_theories/Definability/Law46.lean:46:47: This simp argument is unused:
  h₁

Hint: Omit it from the simp argument list.
  simp [NatMagmaLaw.toFin, MagmaLaw.toNat, h₁̵,̵ ̵h̵xy]

Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
warning: equational_theories/Definability/Law46.lean:46:51: This simp argument is unused:
  hxy
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v08_with_elems_val
error: equational_theories/Definability/Law46.lean:45:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:46:12: Unknown constant `Law.NatMagmaLaw.toFin`
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
h₁ : ↑(Lf x ≃ Lf y).elems = [x, y]
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
warning: equational_theories/Definability/Law46.lean:46:47: This simp argument is unused:
  h₁

Hint: Omit it from the simp argument list.
  simp [NatMagmaLaw.toFin, MagmaLaw.toNat, h₁̵,̵ ̵h̵xy]

Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
warning: equational_theories/Definability/Law46.lean:46:51: This simp argument is unused:
  hxy
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v09_convert_decide_after_subst_not_possible
error: equational_theories/Definability/Law46.lean:45:12: Unknown constant `Law.NatMagmaLaw.toFin`
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy hneq : x ≠ y
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
warning: equational_theories/Definability/Law46.lean:45:47: This simp argument is unused:
  hneq

Hint: Omit it from the simp argument list.
  simp [NatMagmaLaw.toFin, MagmaLaw.toNat,̵ ̵h̵n̵e̵q̵]

Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v10_aesop
warning: equational_theories/Definability/Law46.lean:44:6: aesop: failed to prove the goal after exhaustive search.
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : ¬x = y
⊢ (Lf x ≃ Lf y).toFin.toNat = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v11_try_simp_all
error: equational_theories/Definability/Law46.lean:44:16: Unknown constant `Law.NatMagmaLaw.toFin`
error: equational_theories/Definability/Law46.lean:43:47: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : ¬x = y
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v12_exact_original_hint_short
error: equational_theories/Definability/Law46.lean:45:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:47:14: Unknown constant `Law.NatMagmaLaw.toFin`
error: equational_theories/Definability/Law46.lean:46:68: unsolved goals
L : NatMagmaLaw
x y : ℕ
hxy : x ≠ y
h₁ : ↑(Lf x ≃ Lf y).elems = [x, y]
⊢ map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2
warning: equational_theories/Definability/Law46.lean:47:49: This simp argument is unused:
  h₁

Hint: Omit it from the simp argument list.
  simp [NatMagmaLaw.toFin, MagmaLaw.toNat, h₁̵,̵ ̵h̵xy]

Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
warning: equational_theories/Definability/Law46.lean:47:53: This simp argument is unused:
  hxy
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed

## Next Move

If accepted, the leaf/leaf branch is probably complete. Carry Patch002 + Patch005 + Patch006 + Patch007 and verify whether the first section still has remaining sorries.

If rejected, use `tofin_recon.json` plus the best error to write a dedicated API-inspection micro-file for `toFin`.
