# SorryDB v4.5.7 — lean4lean StratifiedUntyped constDF Patch003

## Patch003 Insight

Patch002 proved the missing term should come from the recursive IH, but the IH appeared only as an inaccessible name `a_ih✝`. Patch003 binds the IH directly in the `constDF` case pattern.

## Result

- status: PATCH003_ACCEPTED
- accepted_variant: v02_bind_three_premises_two_ihs

## Variant Summary

- v01_bind_two_ihs_after_h5: module_rc=1, module_seconds=2.5, strat_sorry=False, full_rc=None, full_seconds=None
- v02_bind_three_premises_two_ihs: module_rc=0, module_seconds=1.15, strat_sorry=False, full_rc=0, full_seconds=64.41

## Target Window

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

## Next Move

Promote accepted patch into a PR branch if experimental-file proof cleanup is acceptable.