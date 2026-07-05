# SorryDB v4.5.12 — PR Watch + Next Target Selector

## Open PRs

- digama0/lean4lean#14 — open
- teorth/equational_theories#1461 — open

## Selection Result

- input targets: 12
- rejected: 6
- remaining: 6
- status: NEXT_TARGET_SELECTED

## Next Candidate

- repo: digama0/lean4lean
- file: Lean4Lean/Experimental/Stratified.lean
- commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- branch: master
- selector_score: -49.9
- active_sorry_count_after_string_strip: 1
- line_count: 332
- imports: ['import Lean4Lean.Theory.Typing.Lemmas', 'import Lean4Lean.Theory.Typing.Strong']
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

### Nearby declarations

- line 9: def DefInv (env : VEnv) (U : Nat) (Γ : List VExpr) : VExpr → VExpr → Prop
- line 75: theorem IsDefEq.induction1
- line 120: theorem HasType1.induction (H : env.HasType1 U defEq Γ e A) : env.HasType U Γ e A := by
- line 135: theorem IsDefEq1.induction
- line 193: theorem IsDefEq1.unique_typing1
- line 211: theorem HasType1.unique_typing'
- line 260: theorem IsDefEq.unique_typing'
- line 290: theorem IsDefEq.weakN_inv (W : Ctx.LiftN n k Γ Γ')
- line 325: theorem HasType.weakN_inv (W : Ctx.LiftN n k Γ Γ')
- line 330: theorem IsType.weakN_inv (W : Ctx.LiftN n k Γ Γ') (H : env.IsType U Γ' (A.liftN n k)) :

### First sorry window

0079:     (hdf : ∀ {Γ e1 e2 A}, IsDefEq1 env U hasType defEq Γ e1 e2 A → defEq Γ e1 e2 A)
0080:     (H : env.IsDefEq U Γ e1 e2 A) :
0081:     HasType1 env U defEq Γ e1 A ∧
0082:     HasType1 env U defEq Γ e2 A ∧
0083:     IsDefEq1 env U hasType defEq Γ e1 e2 A := by
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
0097:     let ⟨hf, hf', ff⟩ := ihf; let ⟨ha, ha', aa⟩ := iha
0098:     exact ⟨.app hf ha, .defeq (hdf ihBa.2.2.symm) (.app hf' ha'), .appDF ff aa⟩
0099:   | lamDF _ _ _ _ _ _ _ ihA ihB _ ihb ihb' =>
0100:     refine ⟨.lam ihA.1 ihb.1, ?_, .lamDF ihA.2.2 ihb.2.2⟩
0101:     exact .defeq (hdf <| .symm <| .forallEDF ihA.2.2 ihB.2.2) <| .lam ihA.2.1 ihb'.2.1
0102:   | forallEDF _ _ _ _ _ ih1 ih2 ih3 =>
0103:     exact ⟨.forallE ih1.1 ih2.1, .forallE ih1.2.1 ih3.2.1, .forallEDF ih1.2.2 ih2.2.2⟩

## Top Remaining Targets

1. digama0/lean4lean :: Lean4Lean/Experimental/Stratified.lean — score -49.9
2. digama0/lean4lean :: Lean4Lean/Experimental/ShapeLogRelAdequacy.lean — score -46.85
3. digama0/lean4lean :: Lean4Lean/Experimental/MoreStepIndexed.lean — score -41.05
4. digama0/lean4lean :: Lean4Lean/Experimental/ParallelReduction.lean — score 45.75
5. leanprover-community/sphere-eversion :: SphereEversion/ToMathlib/Unused/GeometryManifoldMisc.lean — score 54.75
6. leanprover-community/mathlib4 :: Mathlib/Tactic/ITauto.lean — score 83.2

## Rejected Summary

- LEAN4LEAN_VERIFY_STACK_RISK_AFTER_PR14: 5
- PR_OPENED_DIGAMA0_LEAN4LEAN_14: 1