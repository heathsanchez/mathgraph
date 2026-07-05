# SorryDB v4.4.68 — Law46 Patch008 toFin revert Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Prior Accepted Partials

Patch002 accepted rhs-is-leaf.
Patch005 accepted hxy : x ≠ y.
Patch006 accepted L = Lf x ≃ Lf y.

## Patch008 Goal

Replace:

    have : (Lf x ≃ Lf y).toFin.toNat = Law2 := by
      sorry

using Lean's suggested `+revert` route.

## Variant Results

- v01_decide_kernel_revert: rc=1, seconds=37.13, error=True, warning=False
- v02_decide_revert: rc=1, seconds=4.94, error=True, warning=False
- v03_native_decide_revert: rc=1, seconds=2.87, error=True, warning=False
- v04_unfold_toNat_decide_kernel_revert: rc=1, seconds=2.97, error=True, warning=False
- v05_change_map_then_decide_kernel_revert: rc=1, seconds=2.85, error=True, warning=False
- v06_exact_by_have_general: rc=1, seconds=2.95, error=True, warning=False
- v07_exact_by_have_general_revert: rc=1, seconds=2.9, error=True, warning=False
- v08_by_cases_decide_kernel_revert: rc=1, seconds=2.84, error=True, warning=False
- v09_have_ne_then_decide_kernel_revert: rc=1, seconds=3.68, error=True, warning=False
- v10_simp_toNat_then_decide_kernel_revert: rc=1, seconds=2.88, error=True, warning=False

## Status

PATCH008_REJECTED_OBSTRUCTION

## Accepted Variant

None

## Obstruction

## v01_decide_kernel_revert
error: equational_theories/Definability/Law46.lean:44:6: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → (Lf x ≃ Lf y).toFin.toNat = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v02_decide_revert
error: equational_theories/Definability/Law46.lean:44:6: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → (Lf x ≃ Lf y).toFin.toNat = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v03_native_decide_revert
error: equational_theories/Definability/Law46.lean:44:6: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → (Lf x ≃ Lf y).toFin.toNat = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v04_unfold_toNat_decide_kernel_revert
error: equational_theories/Definability/Law46.lean:45:6: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v05_change_map_then_decide_kernel_revert
error: equational_theories/Definability/Law46.lean:45:6: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v06_exact_by_have_general
error: equational_theories/Definability/Law46.lean:45:8: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → (Lf x ≃ Lf y).toFin.toNat = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v07_exact_by_have_general_revert
error: equational_theories/Definability/Law46.lean:45:8: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → (Lf x ≃ Lf y).toFin.toNat = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v08_by_cases_decide_kernel_revert
error: equational_theories/Definability/Law46.lean:46:8: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → ¬x = y → (Lf x ≃ Lf y).toFin.toNat = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v09_have_ne_then_decide_kernel_revert
error: equational_theories/Definability/Law46.lean:45:6: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → ¬x = y → (Lf x ≃ Lf y).toFin.toNat = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v10_simp_toNat_then_decide_kernel_revert
error: equational_theories/Definability/Law46.lean:45:6: failed to synthesize
  Decidable (∀ (x y : ℕ), x ≠ y → map (fun x_1 ↦ ↑x_1) (Lf x ≃ Lf y).toFin.toFin = Law2)

Hint: Additional diagnostic information may be available using the `set_option diagnostics true` command.
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed

## Next Move

If accepted, carry Patch002 + Patch005 + Patch006 + Patch008 and verify the leaf/leaf branch has no remaining sorry.

If rejected, inspect `api_recon.json`; the next move is an API micro-file that prints/checks the actual theorem shape for `.toFin.toFin` and `Law2`.
