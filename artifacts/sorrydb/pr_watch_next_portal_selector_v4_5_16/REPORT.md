# SorryDB v4.5.16 — PR Watch + Next Reusable Portal Selector

## Open PRs

- digama0/lean4lean#14 — open
- digama0/lean4lean#15 — open
- teorth/equational_theories#1461 — open

## Result

- input targets: 12
- rejected: 7
- remaining: 5
- status: NEXT_PORTAL_SELECTED

## Next Candidate

- repo: digama0/lean4lean
- file: Lean4Lean/Experimental/ShapeLogRelAdequacy.lean
- commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- branch: master
- selector_score: -42.85
- active_sorry_count_after_string_strip: 1
- line_count: 473

### Nearby declarations

- line 8: def LR.Adequate (Γ₀ Γ : List SExpr) (ρ : Valuation) (M N A : SExpr) (m a : WShape n) :=
- line 14: theorem LR.Adequate.bot (ha : a.HasType .type) : Adequate Γ₀ Γ ρ M N A .bot a :=
- line 17: theorem LR.Adequate.fits
- line 21: theorem LR.Adequate.refl
- line 26: theorem LR.Adequate.left : Adequate Γ₀ Γ ρ M N A m a → Adequate Γ₀ Γ ρ M M A m a
- line 29: theorem LR.Adequate.symm : Adequate Γ₀ Γ ρ M N A m a → Adequate Γ₀ Γ ρ N M A m a
- line 32: theorem LR.Adequate.trans :
- line 37: theorem LR.Adequate.trans' : Adequate Γ₀ Γ ρ A₁ A₂ (.sort u) a s →
- line 45: theorem LR.Adequate.cons
- line 94: theorem LR.toValTy {m : WShape n'} {b : WShape n} (le_n : n ≤ n') (le_a : b.T ≤ m.T)
- line 106: theorem LR.adequacy (H : Γ ⊢ M ≡ N : A)
- line 434: theorem forallE_whRed_l (d : Γ ⊢ A₀ ≡ SExpr.forallE B₁ F₁ : .sort s) :

### First sorry window

0142:     | _ =>
0143:       obtain h | h := WShape.le_sort.1 hM.le_sort'
0144:       · dsimp only at h; rw [h]; exact (LR _).bot hmem.isType
0145:       · simp [WShape.ext_iff, WShape.forallE, WShape.sort, Shape.sort,
0146:           WShape.lam', WShape.lam, WShape.bot, WShape.ctor, WShape.indTy,
0147:           Shape.bot] at h <;> first | split at h <;> simp_all only [reduceCtorEq] | simp_all
0148:   | @const c ci Γ ls _ h1 h2 h3 =>
0149:     cases hM with | bot => exact .bot hmem.isType | const a1 _ a3 a4 a5 a6
0150:     cases h1.symm.trans a1
0151:     suffices ∀ {σ}, (LR Γ₀).DefEq (const c ls) (const c ls) (((mk ci.type).instL ls).subst σ) m a
0152:       from ⟨fun _ _ _ => ⟨this, this⟩, fun _ _ => this⟩
0153:     intro σ; rw [(Params.henv.closedC h1).mkS.instL.subst_eq .zero]; clear σ
0154:     sorry
0155:   | @appDF Γ A u F F' B X X' v _ Hf Ha HBa _ ihf iha ihBa =>
0156:     cases hM with | bot => exact .bot hmem.isType | @app _ nf_app f _ _ _ x hif hia le_m
0157:     suffices ∀ {F F' X X' σ σ'}, SubstWF Γ₀ σ σ' Γ ρ →
0158:         Γ ⊢ F ≡ F' : A.forallE B → Γ ⊢ X ≡ X' : A → Γ ⊢ B.inst X ≡ B.inst X' : .sort v →
0159:         LE_Interp ρ f.T F → LE_Interp ρ x.T X → LE_Interp ρ a.T (B.inst X) →
0160:         (∀ {n'} {mf af : WShape n'}, LE_Interp ρ mf.T F → LE_Interp ρ af.T (.forallE A B) →
0161:           mf.HasType af → Adequate Γ₀ Γ ρ F F' (.forallE A B) mf af) →
0162:         (∀ {n'} {ma aa : WShape n'}, LE_Interp ρ ma.T X → LE_Interp ρ aa.T A →
0163:           ma.HasType aa → Adequate Γ₀ Γ ρ X X' A ma aa) →
0164:         (∀ {n'} {mb av : WShape n'}, LE_Interp ρ mb.T (B.inst X) → LE_Interp ρ av.T (.sort v) →
0165:           mb.HasType av → Adequate Γ₀ Γ ρ (B.inst X) (B.inst X') (.sort v) mb av) →
0166:         (LR Γ₀).DefEq (.subst (.app F X) σ) (.subst (.app F' X') σ')

## Top Remaining

1. digama0/lean4lean :: Lean4Lean/Experimental/ShapeLogRelAdequacy.lean — score -42.85
2. digama0/lean4lean :: Lean4Lean/Experimental/MoreStepIndexed.lean — score -37.05
3. leanprover-community/sphere-eversion :: SphereEversion/ToMathlib/Unused/GeometryManifoldMisc.lean — score 47.75
4. digama0/lean4lean :: Lean4Lean/Experimental/ParallelReduction.lean — score 60.75
5. leanprover-community/mathlib4 :: Mathlib/Tactic/ITauto.lean — score 87.2

## Rejected Summary

- LEAN4LEAN_VERIFY_STACK_RISK: 5
- PR_OPENED_DIGAMA0_LEAN4LEAN_14: 1
- PR_OPENED_DIGAMA0_LEAN4LEAN_15: 1