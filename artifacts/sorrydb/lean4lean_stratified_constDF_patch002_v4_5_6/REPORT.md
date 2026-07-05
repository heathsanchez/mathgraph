# SorryDB v4.5.6 — lean4lean StratifiedUntyped constDF Patch002

## Target

- Repository: digama0/lean4lean
- Commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- File: Lean4Lean/Experimental/StratifiedUntyped.lean
- Theorem: IsDefEq.inductionU1
- Line: 72

## Patch002 Insight

Patch001 trace showed the missing term is:

    defEq Γ (VExpr.instL ls₂ ci.type) (VExpr.instL ls₁ ci.type)

The recursive induction hypothesis `a_ih` contains type-level definitional equality in the forward direction. The patch tries to reverse it and feed it to `hdf`.

## Result

- status: PATCH002_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Variant Summary

- v01_use_type_ih_reverse_direct: module_rc=1, module_seconds=2.73, strat_sorry=False, full_rc=None, full_seconds=None
- v02_use_type_ih_reverse_explicit_IsDefEqU1_symm: module_rc=1, module_seconds=1.12, strat_sorry=False, full_rc=None, full_seconds=None
- v03_have_hd_from_type_ih_reverse: module_rc=1, module_seconds=0.91, strat_sorry=False, full_rc=None, full_seconds=None
- v04_trace_a_ih_names: module_rc=0, module_seconds=1.02, strat_sorry=True, full_rc=None, full_seconds=None
- v05_destructure_a_ih_then_hdf_reverse: module_rc=1, module_seconds=0.91, strat_sorry=False, full_rc=None, full_seconds=None
- v06_destructure_a_ih_explicit_symm: module_rc=1, module_seconds=0.92, strat_sorry=False, full_rc=None, full_seconds=None
- v07_refine_then_exact_goal: module_rc=1, module_seconds=0.91, strat_sorry=False, full_rc=None, full_seconds=None
- v08_refine_then_explicit_symm: module_rc=1, module_seconds=0.81, strat_sorry=False, full_rc=None, full_seconds=None

## Target Window

0060:       HasTypeU1 env U defEq Γ e1 A1 → HasTypeU1 env U defEq Γ e2 A2 →
0061:       IsDefEqU1 env U hasType Γ e1 e2 → defEq Γ e1 e2)
0062:     (H : env.IsDefEq U Γ e1 e2 A) :
0063:     HasTypeU1 env U defEq Γ e1 A ∧
0064:     HasTypeU1 env U defEq Γ e2 A ∧
0065:     IsDefEqU1 env U hasType Γ e1 e2 := by
0066:   have H' := H.strong henv hΓ; clear hΓ H
0067:   induction H' with
0068:   | bvar h => exact ⟨.bvar h, .bvar h, .refl⟩
0069:   | symm _ ih => exact ⟨ih.2.1, ih.1, .symm ih.2.2⟩
0070:   | trans _ _ ih1 ih2 => exact ⟨ih1.1, ih2.2.1, .trans ih1.2.2 ih2.2.2⟩
0071:   | @constDF _ _ ls₁ ls₂ _ _ h1 h2 h3 h4 h5 =>
0072:     exact ⟨.const h1 h2 h4, .defeq sorry <| .const h1 h3 (h5.length_eq.symm.trans h4), .constDF h5⟩
0073:   | @sortDF l l' _ h1 h2 h3 =>
0074:     refine ⟨.sort h1, ?_, .sortDF h3⟩
0075:     exact .defeq (hdf (.sort (l := l'.succ) h2) (.sort (l := l.succ) h1)
0076:       (.sortDF <| VLevel.succ_congr h3.symm)) (.sort h2)
0077:   | appDF _ _ _ _ _ _ _ _ _ ihf iha ihBa =>
0078:     let ⟨hf, hf', ff⟩ := ihf; let ⟨ha, ha', aa⟩ := iha

## Next Move

Use the diagnostics to determine whether the IH name is inaccessible, whether the induction case name differs, or whether `hdf` expects the strong type proof rather than the U1 induction proof.