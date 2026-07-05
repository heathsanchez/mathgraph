# SorryDB v4.5.4 — String-Aware Real Target Filter

## Purpose

Fix v4.5.3 false positive where mathlib Cauchy completion contained `sorry` inside a string literal.

## Result

- input candidates: 660
- rejected: 648
- real target candidates: 12
- status: STRING_AWARE_REAL_TARGET_FOUND

## Recommended Next Target

- repo: digama0/lean4lean
- file: Lean4Lean/Experimental/StratifiedUntyped.lean
- commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- score: -25.65
- active_sorry_count_after_string_strip: 1
- line_count: 317
- import_count: 2
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

Nearby declarations:

- line 55: theorem IsDefEq.inductionU1
- line 102: theorem HasTypeU1.induction (H : env.HasTypeU1 U defEq Γ e A) : env.HasType U Γ e A := by
- line 120: theorem IsDefEqU1.induction
- line 178: theorem IsDefEqU1.unique_typing1
- line 196: theorem HasType1.unique_typing'
- line 245: theorem IsDefEq.unique_typing'
- line 275: theorem IsDefEq.weakN_inv (W : Ctx.LiftN n k Γ Γ')
- line 310: theorem HasType.weakN_inv (W : Ctx.LiftN n k Γ Γ')

First active sorry window:

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
0079:     exact ⟨.app hf ha, .defeq (hdf ihBa.2.1 ihBa.1 (.symm ihBa.2.2)) (.app hf' ha'), .appDF ff aa⟩
0080:   | lamDF _ _ _ _ _ _ _ ihA ihB ihB' ihb ihb' =>
0081:     refine ⟨.lam ihA.1 ihb.1, .defeq ?_ <| .lam ihA.2.1 ihb'.2.1, .lamDF ihA.2.2 ihb.2.2⟩
0082:     exact hdf (.forallE ihA.2.1 ihB'.1) (.forallE ihA.1 ihB.1) <|
0083:       .symm <| .forallEDF ihA.2.2 ihB.2.2
0084:   | forallEDF _ _ _ _ _ ih1 ih2 ih3 =>

## Top String-Aware Targets

### 1. digama0/lean4lean :: Lean4Lean/Experimental/StratifiedUntyped.lean

- score: -25.65
- active_sorry_count_after_string_strip: 1
- line_count: 317
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

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
0079:     exact ⟨.app hf ha, .defeq (hdf ihBa.2.1 ihBa.1 (.symm ihBa.2.2)) (.app hf' ha'), .appDF ff aa⟩
0080:   | lamDF _ _ _ _ _ _ _ ihA ihB ihB' ihb ihb' =>
0081:     refine ⟨.lam ihA.1 ihb.1, .defeq ?_ <| .lam ihA.2.1 ihb'.2.1, .lamDF ihA.2.2 ihb.2.2⟩
0082:     exact hdf (.forallE ihA.2.1 ihB'.1) (.forallE ihA.1 ihB.1) <|
0083:       .symm <| .forallEDF ihA.2.2 ihB.2.2
0084:   | forallEDF _ _ _ _ _ ih1 ih2 ih3 =>

### 2. digama0/lean4lean :: Lean4Lean/Experimental/Stratified.lean

- score: -24.9
- active_sorry_count_after_string_strip: 1
- line_count: 332
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

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

### 3. digama0/lean4lean :: Lean4Lean/Experimental/ShapeLogRelAdequacy.lean

- score: -23.85
- active_sorry_count_after_string_strip: 1
- line_count: 473
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

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

### 4. digama0/lean4lean :: Lean4Lean/Verify/TypeChecker/InferType.lean

- score: -22.05
- active_sorry_count_after_string_strip: 1
- line_count: 509
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": true}

First active sorry window:

0388: theorem inferLet.WF
0389:     (hr : e.FVarsIn (· ∈ c.vlctx.fvars))
0390:     (hinf : inferOnly = true → ∃ e', c.TrExprS e e') :
0391:     (inferLet e inferOnly).WF c s fun ty _ =>
0392:       ∃ e' ty', c.TrTyping e ty e' ty' := by
0393:   refine .stateWF fun wf => ?_
0394:   refine (c.withMLC_self ▸ inferLet.loop.WF (Nat.zero_le _) [] rfl rfl rfl rfl rfl ?_ hr) hinf
0395:   exact fun P hP he => ⟨(AllAbove.wf wf.trctx.wf.fvwf).2 hP, he.mono fun _ h _ => h, fun _ => id⟩
0396: 
0397: theorem inferProj.WF
0398:     (he : c.TrExprS e e') (hty : c.TrExprS ety ety') (hasty : c.HasType e' ty') :
0399:     (inferProj st i e ety).WF c s fun ty _ =>
0400:       ∃ ty', c.TrTyping (.proj st i e) ty e' ty' := sorry
0401: 
0402: theorem literal_is_primitive (H : n = ``Nat ∨ n = ``Char.ofNat ∨ n = ``String.ofList)  :
0403:     Environment.primitives.contains n := by
0404:   simp [Environment.primitives, NameSet.ofList]
0405:   obtain rfl|rfl|rfl := H <;> simp +decide [NameSet.contains]
0406: 
0407: theorem infer_literal {c : VContext} (H : c.venv.ContainsLits l) :
0408:     c.TrTyping (.lit l) l.type (.trLiteral l) (.const l.typeName []) := by
0409:   refine
0410:     have := TrExprS.trLiteral c.Ewf c.hasPrimitives l H
0411:     ⟨fun _ _ _ => .litType, this.1, ?_, this.2⟩
0412:   rw [← Literal.mkConst_typeName]

### 5. digama0/lean4lean :: Lean4Lean/Experimental/MoreStepIndexed.lean

- score: -18.05
- active_sorry_count_after_string_strip: 1
- line_count: 489
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": true, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": true, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0298:   | _+1, .sort, .sort => .sort -- (max i j) (by omega)
0299:   | _+1, .forallE s f, .forallE s' f' => .forallE (join s s') (ShapeFun.join join f f')
0300:   | _+1, .lam f, .lam f' => .lam (ShapeFun.join join f f')
0301:   | _+1, _, _ => .bot
0302: 
0303: def ShapeFun.maxBelow (s : ShapeFun n) : Shape n × Shape n :=
0304:   (s.find? fun (x, _) => s.all fun (x', _) => x' ≤ x).getD (.bot, .bot)
0305: 
0306: def ShapeFun.app (s : ShapeFun n) (a : Shape n) : Shape n :=
0307:   maxBelow (s.filter (·.1 ≤ a)) |>.2
0308: 
0309: theorem ShapeFun.app_mono_l {f f' : ShapeFun n} : f.LE f' → ∀ a, f.app a ≤ f'.app a :=
0310:   sorry
0311: 
0312: def Shape.app : Shape (n + 1) → Shape n → Shape n
0313:   | .lam f, x => ShapeFun.app f x
0314:   | _, _ => .bot
0315: 
0316: theorem Shape.app_mono_l {f f' : Shape (n + 1)} (le : f ≤ f') (a) : f.app a ≤ f'.app a := by
0317:   unfold app; split <;> [split; simp]
0318:   · exact ShapeFun.app_mono_l le _
0319:   · cases f' <;> simp [LE.def] at le; grind
0320: 
0321: def Shape.HasType : ∀ {n}, Shape n → Shape n → Prop
0322:   | 0, _, _ | _+1, .bot, _ => True

### 6. digama0/lean4lean :: Lean4Lean/Verify/Typing/Expr.lean

- score: -3.9
- active_sorry_count_after_string_strip: 1
- line_count: 172
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0055: 
0056: variable (env : VEnv) (U : Nat) in
0057: def VLCtx.WF : VLCtx → Prop
0058:   | [] => True
0059:   | (ofv, d) :: (Δ : VLCtx) =>
0060:     VLCtx.WF Δ ∧ (∀ fv deps, ofv = some (fv, deps) → fv ∉ Δ.fvars ∧ deps ⊆ Δ.fvars) ∧
0061:     VLocalDecl.WF env U Δ.toCtx d
0062: 
0063: def VLCtx.WF.fvwf : ∀ {Δ}, VLCtx.WF env U Δ → Δ.FVWF
0064:   | [], h => h
0065:   | _ :: _, ⟨h1, h2, _⟩ => ⟨h1.fvwf, h2⟩
0066: 
0067: def TrProj : ∀ (Γ : List VExpr) (structName : Name) (idx : Nat) (e : VExpr), VExpr → Prop := sorry
0068: 
0069: def VEnv.ContainsLits (env : VEnv) : Literal → Prop
0070:   | .natVal _ => env.contains ``Nat
0071:   | .strVal _ => env.contains ``Char.ofNat ∧ env.contains ``String.ofList
0072: 
0073: variable (env : VEnv) (Us : List Name) in
0074: inductive TrExprS : VLCtx → Expr → VExpr → Prop
0075:   | bvar : Δ.find? (.inl i) = some (e, A) → TrExprS Δ (.bvar i) e
0076:   | fvar : Δ.find? (.inr fv) = some (e, A) → TrExprS Δ (.fvar fv) e
0077:   | sort : VLevel.ofLevel Us u = some u' → TrExprS Δ (.sort u) (.sort u')
0078:   | const :
0079:     env.constants c = some ci →

### 7. digama0/lean4lean :: Lean4Lean/Verify/Level.lean

- score: -3.9
- active_sorry_count_after_string_strip: 1
- line_count: 592
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": true, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0533:       · simp [evalPath]; split <;> [rename_i nz; simp]
0534:         have hm := (h ▸ mem_orderedInsert).2 (.inl rfl)
0535:         have ⟨p1, p2, a1, a2, a3, a4⟩ := le.of_mem hm
0536:         have := evalPath_le.1 a3 (allNZ_mono a1 nz)
0537:         simp [allNZ] at nz; specialize nz _ hm
0538:         simp [VLevel.eval, ← evalParam_eq hv]
0539:         revert this nz; cases evalParam .. <;> simp; omega
0540:       · rw [NormLevel.addVar_eval H, this, evalPath_cons, evalPath_cons]
0541:         congr 2; split <;> simp [VLevel.eval, ← evalParam_eq hv]
0542: 
0543: theorem NormLevel.subsumption_eval {s : NormLevel} :
0544:     s.subsumption.eval ls ρ = s.eval ls ρ := by
0545:   sorry
0546: 
0547: theorem normalize_eval (hu : VLevel.ofLevel ls u = some u') :
0548:     (normalize u).eval ls ρ = u'.eval ρ := by
0549:   simp [normalize, NormLevel.subsumption_eval]
0550:   exact normalizeAux_eval hu (by simp) .nil
0551: 
0552: theorem Node.eval_congr {a b : Node} (H : a == b) : a.eval ls ρ = b.eval ls ρ := by
0553:   simp +instances [instBEqNode] at H; simp [H, eval]
0554: 
0555: theorem NormLevel.eval_congr {a b : NormLevel} (H : a == b) : a.eval ls ρ = b.eval ls ρ := by
0556:   simp +instances only [instBEqNormLevel, Std.TreeMap.all_eq_all_toList,
0557:     Bool.and_eq_true, List.all_eq_true] at H

### 8. digama0/lean4lean :: Lean4Lean/Verify/TypeChecker/WHNF.lean

- score: 13.3
- active_sorry_count_after_string_strip: 2
- line_count: 176
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0001: import Lean4Lean.Verify.TypeChecker.Reduce
0002: 
0003: namespace Lean4Lean.TypeChecker.Inner
0004: open Lean hiding Environment Exception
0005: 
0006: theorem reduceRecursor.WF {c : VContext} {s : VState} (he : c.TrExprS e e') :
0007:     RecM.WF c s (reduceRecursor e cheapRec cheapProj) fun oe _ =>
0008:       ∀ e₁, oe = some e₁ → c.FVarsBelow e e₁ ∧ c.TrExpr e₁ e' := sorry
0009: 
0010: theorem whnfFVar.WF {c : VContext} {s : VState} (he : c.TrExprS (.fvar fv) e') :
0011:     RecM.WF c s (whnfFVar (.fvar fv) cheapRec cheapProj) fun e₁ _ =>
0012:       c.FVarsBelow (.fvar fv) e₁ ∧ c.TrExpr e₁ e' := by
0013:   refine .getLCtx ?_
0014:   simp [Expr.fvarId!]; split <;> [skip; exact .pure ⟨.rfl, he.trExpr c.Ewf c.Δwf⟩]
0015:   rename_i decl h
0016:   rw [c.trlctx.1.find?_eq_find?_toList] at h
0017:   have := List.find?_some h; simp at this; subst this
0018:   let ⟨e', ty', h1, h2, _, h3, _⟩ :=
0019:     c.trlctx.find?_of_mem c.Ewf (List.mem_of_find?_eq_some h)
0020:   refine (whnfCore.WF h3).mono fun _ _ _ ⟨h4, h5⟩ => ?_

### 9. digama0/lean4lean :: Lean4Lean/Verify/TypeChecker/IsDefEq.lean

- score: 34.35
- active_sorry_count_after_string_strip: 2
- line_count: 557
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0214:   exact (h hb).trans c.Ewf c.Δwf ⟨_, .eta a4⟩
0215: 
0216: theorem tryEtaExpansion.WF {c : VContext} {s : VState}
0217:     (he₁ : c.TrExprS e₁ e₁') (he₂ : c.TrExprS e₂ e₂') :
0218:     RecM.WF c s (tryEtaExpansion e₁ e₂) fun b _ => b → c.IsDefEqU e₁' e₂' := by
0219:   simp [tryEtaExpansion, orM, toBool]
0220:   refine (tryEtaExpansionCore.WF he₁ he₂).bind fun _ _ _ h => ?_
0221:   split <;> [exact .pure fun _ => h rfl; skip]
0222:   exact (tryEtaExpansionCore.WF he₂ he₁).mono fun _ _ _ h hb => (h hb).symm
0223: 
0224: theorem tryEtaStructCore.WF {c : VContext} {s : VState}
0225:     (he₁ : c.TrExprS e₁ e₁') (he₂ : c.TrExprS e₂ e₂') :
0226:     RecM.WF c s (tryEtaStructCore e₁ e₂) fun b _ => b → c.IsDefEqU e₁' e₂' := sorry
0227: 
0228: theorem tryEtaStruct.WF {c : VContext} {s : VState}
0229:     (he₁ : c.TrExprS e₁ e₁') (he₂ : c.TrExprS e₂ e₂') :
0230:     RecM.WF c s (tryEtaStruct e₁ e₂) fun b _ => b → c.IsDefEqU e₁' e₂' := by
0231:   simp [tryEtaStruct, orM, toBool]
0232:   refine (tryEtaStructCore.WF he₁ he₂).bind fun _ _ _ h => ?_
0233:   split <;> [exact .pure fun _ => h rfl; skip]
0234:   exact (tryEtaStructCore.WF he₂ he₁).mono fun _ _ _ h hb => (h hb).symm
0235: 
0236: theorem isDefEqApp.WF {c : VContext} {s : VState}
0237:     (he₁ : c.TrExprS e₁ e₁') (he₂ : c.TrExprS e₂ e₂') :
0238:     RecM.WF c s (isDefEqApp e₁ e₂) fun b _ => b → c.IsDefEqU e₁' e₂' := by

### 10. digama0/lean4lean :: Lean4Lean/Experimental/ParallelReduction.lean

- score: 55.75
- active_sorry_count_after_string_strip: 2
- line_count: 905
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0687: theorem NormalEq.parRed (H1 : NormalEq TY Γ e₁ e₂) (H2 : ParRed TY Γ e₂ e₂') :
0688:     ∃ e₁', ParRedS TY Γ e₁ e₁' ∧ NormalEq TY Γ e₁' e₂' := by
0689:   induction H1 generalizing e₂' with
0690:   | refl l1 => exact ⟨_, .tail .rfl H2, .refl (H2.hasType l1)⟩
0691:   | sortDF l1 l2 l3 =>
0692:     cases H2 with
0693:     | sort => exact ⟨_, .tail .rfl .sort, .sortDF l1 l2 l3⟩
0694:     | extra r1 r2 => cases r2
0695:   | constDF l1 l2 l3 l4 l5 =>
0696:     cases H2 with
0697:     | const => exact ⟨_, .tail .rfl .const, .constDF l1 l2 l3 l4 l5⟩
0698:     | extra r1 r2 r3 r4 =>
0699:       sorry
0700:   | @appDF Γ f A B f₂ a b l1 l2 l3 l4 l5 l6 ih1 ih2 =>
0701:     cases H2 with
0702:     | app r1 r2 =>
0703:       let ⟨_, a1, a2⟩ := ih1 r1
0704:       let ⟨_, b1, b2⟩ := ih2 r2
0705:       exact ⟨_, .app a1 b1,
0706:         .appDF (a1.hasType l1) (r1.hasType l2) (b1.hasType l3) (r2.hasType l4) a2 b2⟩
0707:     | @beta A _ e e' _ b' r1 r2 =>
0708:       let ⟨f', a1, a2⟩ := ih1 (.lam .rfl r1)
0709:       let ⟨a', b1, b2⟩ := ih2 r2
0710:       let ⟨_, _, d1, d2⟩ := TY.lam_inv l2
0711:       let ⟨u1, u2⟩ := TY.forallE_defInv (TY.uniq (TY.lam d1 d2) l2)

### 11. leanprover-community/sphere-eversion :: SphereEversion/ToMathlib/Unused/GeometryManifoldMisc.lean

- score: 69.75
- active_sorry_count_after_string_strip: 3
- line_count: 385
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0069: 
0070: theorem smoothAt_coord_change (e e' : Trivialization F (π F E)) {x₀ : B}
0071:     (hx₀ : x₀ ∈ e.baseSet ∩ e'.baseSet) [MemTrivializationAtlas e] [MemTrivializationAtlas e'] :
0072:     ContMDiffAt IB 𝓘(𝕜, F →L[𝕜] F) ∞ (fun b : B ↦ (e.coordChangeL 𝕜 e' b : F →L[𝕜] F)) x₀ :=
0073:   (contMDiffOn_coordChangeL e e').contMDiffAt <| (e.open_baseSet.inter e'.open_baseSet).mem_nhds hx₀
0074: 
0075: variable {IB}
0076: 
0077: theorem contMDiffAt_coord_change_apply (e e' : Trivialization F (π F E)) {x₀ : M} {f : M → B}
0078:     {g : M → F} (hf : ContMDiffAt IM IB n f x₀) (hg : ContMDiffAt IM 𝓘(𝕜, F) n g x₀)
0079:     (hx₀ : f x₀ ∈ e.baseSet ∩ e'.baseSet) [MemTrivializationAtlas e] [MemTrivializationAtlas e'] :
0080:     ContMDiffAt IM 𝓘(𝕜, F) n (fun x ↦ e.coordChangeL 𝕜 e' (f x) (g x)) x₀ :=
0081:   (((smoothAt_coord_change IB e e' hx₀).of_le sorry).comp x₀ hf).clm_apply hg
0082: 
0083: end VectorBundle
0084: 
0085: section VectorBundle
0086: 
0087: open IsManifold
0088: 
0089: open scoped Bundle ContDiff
0090: 
0091: variable {𝕜 B F M : Type*} {E : B → Type*} [NontriviallyNormedField 𝕜] [∀ x, AddCommMonoid (E x)]
0092:   [∀ x, Module 𝕜 (E x)] [NormedAddCommGroup F] [NormedSpace 𝕜 F] [TopologicalSpace (TotalSpace F E)]
0093:   [∀ x, TopologicalSpace (E x)] {EB : Type*} [NormedAddCommGroup EB] [NormedSpace 𝕜 EB]

### 12. leanprover-community/mathlib4 :: Mathlib/Tactic/ITauto.lean

- score: 71.2
- active_sorry_count_after_string_strip: 3
- line_count: 744
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0162:           .gt, .gt, .gt, .gt, .lt,
0163:           .gt, .gt, .gt, .gt, .gt]
0164: 
0165: instance : LT IProp := ⟨fun p q => p.cmp q = .lt⟩
0166: 
0167: instance : DecidableLT IProp := fun _ _ => inferInstanceAs (Decidable (_ = _))
0168: 
0169: open Lean (Name)
0170: 
0171: /-- A reified inductive proof type for intuitionistic propositional logic. -/
0172: inductive Proof
0173:   /-- `⊢ A`, causes failure during reconstruction -/
0174:   | sorry : Proof
0175:   /-- `(n: A) ⊢ A` -/
0176:   | hyp (n : Name) : Proof
0177:   /-- `⊢ ⊤` -/
0178:   | triv : Proof
0179:   /-- `(p: ⊥) ⊢ A` -/
0180:   | exfalso' (p : Proof) : Proof
0181:   /-- `(p: (x: A) ⊢ B) ⊢ A → B` -/
0182:   | intro (x : Name) (p : Proof) : Proof
0183:   /--
0184:   * `ak = .and`: `(p: A ∧ B) ⊢ A`
0185:   * `ak = .iff`: `(p: A ↔ B) ⊢ A → B`
0186:   * `ak = .eq`: `(p: A = B) ⊢ A → B`

## Rejection Summary

- TEST_FILE: 459
- TEACHING_EXERCISE_REPO: 105
- TEST_HARNESS: 23
- META_OR_MACRO_TARGET: 18
- COMMENT_OR_STRING_ONLY_SORRY: 17
- INTENTIONAL_TEST_SORRY: 11
- TOO_MANY_SORRIES_IN_FILE: 6
- LEAN4LEAN_CORE_THEORY_DEPENDENCY_RISK: 4
- NO_LAKE_BUILD: 2
- PARKED_DEPENDENCY_SORRY_TRAP: 1
- PARKED_NAMED_OBSTRUCTION: 1
- SOLVED_LOCALLY_PR_OPEN: 1