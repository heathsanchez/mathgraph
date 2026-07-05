# SorryDB v4.5.13 — lean4lean Stratified constDF Patch001

## Target

- Repository: digama0/lean4lean
- Commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- File: Lean4Lean/Experimental/Stratified.lean
- Theorem: IsDefEq.induction1
- Line: 91

## Insight

This is the stratified analogue of the accepted PR #14 patch in `StratifiedUntyped.lean`.

## Result

- status: PATCH001_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Variant Summary

- v01_trace_original_goal: module_rc=0, module_seconds=1.37, strat_sorry=True, full_rc=None, full_seconds=None
- v02_bind_like_untyped_use_ih_symm: module_rc=1, module_seconds=1.02, strat_sorry=False, full_rc=None, full_seconds=None
- v03_bind_like_untyped_use_IsDefEq1_symm: module_rc=1, module_seconds=1.02, strat_sorry=False, full_rc=None, full_seconds=None
- v04_bind_like_untyped_refine: module_rc=1, module_seconds=1.09, strat_sorry=False, full_rc=None, full_seconds=None
- v05_bind_like_untyped_trace: module_rc=0, module_seconds=1.07, strat_sorry=True, full_rc=None, full_seconds=None
- v06_bind_short_after_h5_trace: module_rc=0, module_seconds=1.02, strat_sorry=True, full_rc=None, full_seconds=None
- v07_bind_like_untyped_destructure: module_rc=1, module_seconds=1.02, strat_sorry=False, full_rc=None, full_seconds=None

## Target Window

0084:   have H' := H.strong henv hΓ; clear hΓ H
0085:   induction H' with
0086:   | bvar h => exact ⟨.bvar h, .bvar h, .refl (hty (.bvar h))⟩
0087:   | symm _ ih => exact ⟨ih.2.1, ih.1, .symm ih.2.2⟩
0088:   | trans _ _ ih1 ih2 => exact ⟨ih1.1, ih2.2.1, .trans ih1.2.2 ih2.2.2⟩
0089:   | @constDF _ _ ls₁ ls₂ u _ h1 h2 h3 h4 h5 =>
0090:     exact ⟨.const h1 h2 h4,
0091:       .defeq (u := u.inst ls₁) sorry <| .const h1 h3 (h5.length_eq.symm.trans h4),
0092:       .constDF h1 h2 h3 h4 h5⟩
0093:   | @sortDF l l' _ h1 h2 h3 =>
0094:     refine ⟨.sort h1, ?_, .sortDF h1 h2 h3⟩
0095:     exact .defeq (hdf <| .symm <| .sortDF (l' := l'.succ) h1 h2 (VLevel.succ_congr h3)) (.sort h2)
0096:   | appDF _ _ _ _ _ _ _ _ _ ihf iha ihBa =>

## Next Move

Use trace diagnostics to identify the exact constructor argument order or the required hdf term.