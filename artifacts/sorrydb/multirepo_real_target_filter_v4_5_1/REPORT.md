# SorryDB v4.5.1 — Real Target Filter

## Purpose

Filter v4.5.0 active `sorry` hits into genuine proof-repair targets.

The v4.5.0 top hit was `MathlibTest/BasicFiles/TacticCommon.lean`, which is an intentional `#print sorries` test, not a proof hole.

## Result

- input candidates: 660
- rejected: 644
- real target candidates: 16
- status: REAL_TARGET_FOUND

## Recommended Next Target

- repo: digama0/lean4lean
- file: Lean4Lean/Theory/Typing/InductiveLemmas.lean
- commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- real_target_score: -62.0
- active_sorry_count: 1
- line_count: 10
- import_count: 3
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

Nearby declarations:

- line 8: theorem addInduct_WF (henv : Ordered env) (hdecl : decl.WF env)

First active sorry window:

0001: import Std
0002: import Lean4Lean.Theory.Typing.Lemmas
0003: import Lean4Lean.Theory.Typing.Env
0004: 
0005: namespace Lean4Lean
0006: namespace VEnv
0007: 
0008: theorem addInduct_WF (henv : Ordered env) (hdecl : decl.WF env)
0009:     (henv' : addInduct env decl = some env') : Ordered env' :=
0010:   sorry

## Top Real Targets

### 1. digama0/lean4lean :: Lean4Lean/Theory/Typing/InductiveLemmas.lean

- real_target_score: -62.0
- original_score: -22.0
- active_sorry_count: 1
- line_count: 10
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0001: import Std
0002: import Lean4Lean.Theory.Typing.Lemmas
0003: import Lean4Lean.Theory.Typing.Env
0004: 
0005: namespace Lean4Lean
0006: namespace VEnv
0007: 
0008: theorem addInduct_WF (henv : Ordered env) (hdecl : decl.WF env)
0009:     (henv' : addInduct env decl = some env') : Ordered env' :=
0010:   sorry

### 2. leanprover-community/mathlib4 :: Mathlib/Algebra/Order/CauSeq/Completion.lean

- real_target_score: -21.25
- original_score: 13.75
- active_sorry_count: 1
- line_count: 415
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": true, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0249:   nnqsmul_def _ x := Quotient.inductionOn x fun _ ↦ congr_arg mk <| ext fun _ ↦ NNRat.smul_def _ _
0250:   qsmul_def _ x := Quotient.inductionOn x fun _ ↦ congr_arg mk <| ext fun _ ↦ Rat.smul_def _ _
0251: 
0252: /-- Show the first 10 items of a representative of this equivalence class of Cauchy sequences.
0253: 
0254: The representative chosen is the one passed in the VM to `Quot.mk`, so two Cauchy sequences
0255: converging to the same number may be printed differently.
0256: -/
0257: unsafe instance [Repr β] : Repr (Cauchy abv) where
0258:   reprPrec r _ :=
0259:     let N := 10
0260:     let seq := r.unquot
0261:     "(sorry /- " ++ Std.Format.joinSep ((List.range N).map <| repr ∘ seq) ", " ++ ", ... -/)"
0262: 
0263: end
0264: 
0265: section
0266: 
0267: variable {α : Type*} [Field α] [LinearOrder α] [IsStrictOrderedRing α]
0268: variable {β : Type*} [Field β] {abv : β → α} [IsAbsoluteValue abv]
0269: 
0270: /-- The Cauchy completion forms a field. -/
0271: noncomputable instance Cauchy.field : Field (Cauchy abv) :=
0272:   { Cauchy.divisionRing, Cauchy.commRing with }
0273: 

### 3. digama0/lean4lean :: Lean4Lean/Theory/Typing/UniqueTyping.lean

- real_target_score: -17.55
- original_score: 17.45
- active_sorry_count: 1
- line_count: 279
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0162: 
0163: theorem HasType.defeqU_r (henv : VEnv.WF env) (hΓ : OnCtx Γ (env.IsType U))
0164:     (h1 : env.IsDefEqU U Γ A₁ A₂) (h2 : env.HasType U Γ e A₁) :
0165:     env.HasType U Γ e A₂ := h1.defeqDF henv hΓ h2
0166: 
0167: theorem IsDefEqU.trans (henv : VEnv.WF env) (hΓ : OnCtx Γ (env.IsType U))
0168:     (h1 : env.IsDefEqU U Γ e₁ e₂) (h2 : env.IsDefEqU U Γ e₂ e₃) :
0169:     env.IsDefEqU U Γ e₁ e₃ := h1.imp fun _ h1 => let ⟨_, h2⟩ := h2; h1.trans_l henv hΓ h2
0170: 
0171: variable! (henv : VEnv.WF env) (hΓ : OnCtx Γ' (env.IsType U)) in
0172: theorem IsDefEqU.weakN_iff (W : Ctx.LiftN n k Γ Γ') :
0173:     env.IsDefEqU U Γ' (e1.liftN n k) (e2.liftN n k) ↔ env.IsDefEqU U Γ e1 e2 := by
0174:   refine ⟨fun h => have := henv; have := hΓ; sorry, fun h => h.weakN henv W⟩
0175: 
0176: variable! (henv : VEnv.WF env) (hΓ : OnCtx Γ' (env.IsType U)) in
0177: theorem _root_.Lean4Lean.VExpr.WF.weakN_iff (W : Ctx.LiftN n k Γ Γ') :
0178:     VExpr.WF env U Γ' (e.liftN n k) ↔ VExpr.WF env U Γ e := IsDefEqU.weakN_iff henv hΓ W
0179: 
0180: theorem IsDefEq.skips (henv : VEnv.WF env) (hΓ : OnCtx Γ' (env.IsType U))
0181:     (W : Ctx.LiftN n k Γ Γ')
0182:     (H : env.IsDefEq U Γ' e₁ e₂ A) (h1 : e₁.Skips n k) (h2 : e₂.Skips n k) :
0183:     ∃ B, env.IsDefEq U Γ' e₁ e₂ B ∧ B.Skips n k := by
0184:   obtain ⟨e₁, rfl⟩ := VExpr.skips_iff_exists.1 h1
0185:   obtain ⟨e₂, rfl⟩ := VExpr.skips_iff_exists.1 h2
0186:   have ⟨_, H⟩ := (IsDefEqU.weakN_iff henv hΓ W).1 ⟨_, H⟩

### 4. digama0/lean4lean :: Lean4Lean/Experimental/StratifiedUntyped.lean

- real_target_score: -15.65
- original_score: 19.35
- active_sorry_count: 1
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

### 5. digama0/lean4lean :: Lean4Lean/Experimental/Stratified.lean

- real_target_score: -14.9
- original_score: 20.1
- active_sorry_count: 1
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

### 6. digama0/lean4lean :: Lean4Lean/Experimental/ShapeLogRelAdequacy.lean

- real_target_score: -13.85
- original_score: 21.15
- active_sorry_count: 1
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

### 7. digama0/lean4lean :: Lean4Lean/Verify/TypeChecker/InferType.lean

- real_target_score: -12.05
- original_score: 22.95
- active_sorry_count: 1
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

### 8. digama0/lean4lean :: Lean4Lean/Experimental/MoreStepIndexed.lean

- real_target_score: -8.05
- original_score: 26.95
- active_sorry_count: 1
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

### 9. digama0/lean4lean :: Lean4Lean/Theory/Typing/Injectivity.lean

- real_target_score: -3.8
- original_score: 26.2
- active_sorry_count: 3
- line_count: 34
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0001: import Lean4Lean.Theory.Typing.EnvLemmas
0002: import Lean4Lean.Theory.Typing.Strong
0003: 
0004: /-!
0005: A bunch of important structural theorems which we can't prove :(
0006: -/
0007: 
0008: namespace Lean4Lean
0009: namespace VEnv
0010: 
0011: theorem IsDefEqU.sort_inv (henv : VEnv.WF env) (hΓ : OnCtx Γ (env.IsType U))
0012:     (h1 : env.IsDefEqU U Γ (.sort u) (.sort v)) : u ≈ v := sorry
0013: 
0014: theorem IsDefEqU.forallE_inv_stratified (henv : VEnv.WF env) (hΓ : OnCtx Γ (env.IsType U))
0015:     (h1 : env.IsDefEqU U Γ (.forallE A B) (.forallE A' B'))
0016:     (h2 : env.HasTypeStratified U Γ (.forallE A B) V true n)
0017:     (h3 : env.HasTypeStratified U Γ (.forallE A' B') V' true n') :
0018:     (∃ u, env.IsDefEq U Γ A A' (.sort u) ∧ env.HasTypeStratified U Γ A (.sort u) true n) ∧
0019:     ∃ u, env.IsDefEq U (A::Γ) B B' (.sort u) ∧
0020:       env.HasTypeStratified U (A::Γ) B (.sort u) true n ∧
0021:       env.HasTypeStratified U (A'::Γ) B' (.sort u) true n' := sorry
0022: 
0023: theorem IsDefEqU.forallE_inv (henv : VEnv.WF env) (hΓ : OnCtx Γ (env.IsType U))
0024:     (h1 : env.IsDefEqU U Γ (.forallE A B) (.forallE A' B')) :

### 10. digama0/lean4lean :: Lean4Lean/Theory/Inductive.lean

- real_target_score: 0.85
- original_score: 10.85
- active_sorry_count: 2
- line_count: 7
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0001: import Lean4Lean.Theory.VDecl
0002: 
0003: namespace Lean4Lean
0004: 
0005: def VInductDecl.WF (env : VEnv) (decl : VInductDecl) : Prop := sorry
0006: 
0007: def VEnv.addInduct (env : VEnv) (decl : VInductDecl) : Option VEnv := sorry

### 11. digama0/lean4lean :: Lean4Lean/Verify/Typing/Expr.lean

- real_target_score: 1.1
- original_score: 16.1
- active_sorry_count: 1
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

### 12. digama0/lean4lean :: Lean4Lean/Verify/Level.lean

- real_target_score: 6.1
- original_score: 36.1
- active_sorry_count: 1
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

### 13. digama0/lean4lean :: Lean4Lean/Verify/TypeChecker/WHNF.lean

- real_target_score: 18.3
- original_score: 43.3
- active_sorry_count: 2
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

### 14. digama0/lean4lean :: Lean4Lean/Verify/TypeChecker/IsDefEq.lean

- real_target_score: 39.35
- original_score: 64.35
- active_sorry_count: 2
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

### 15. digama0/lean4lean :: Lean4Lean/Experimental/ParallelReduction.lean

- real_target_score: 60.75
- original_score: 85.75
- active_sorry_count: 2
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

### 16. digama0/lean4lean :: Lean4Lean/Theory/Typing/ChurchRosser.lean

- real_target_score: 86.7
- original_score: 111.7
- active_sorry_count: 2
- line_count: 1384
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

1176: theorem NormalEq.parRed (H1 : Γ ⊢ e₁ ≡ₚ e₂) (H2 : Γ ⊢ e₂ ≫ e₂') :
1177:     ∃ e₁', Γ ⊢ e₁ ≫* e₁' ∧ Γ ⊢ e₁' ≡ₚ e₂' := by
1178:   induction H1 generalizing e₂' with
1179:   | refl l1 => exact ⟨_, .tail .rfl H2, .refl (H2.hasType hΓ l1)⟩
1180:   | sortDF l1 l2 l3 =>
1181:     cases H2 with
1182:     | sort => exact ⟨_, .tail .rfl .sort, .sortDF l1 l2 l3⟩
1183:     | extra r1 r2 => cases r2
1184:   | constDF l1 l2 l3 l4 l5 =>
1185:     cases H2 with
1186:     | const => exact ⟨_, .tail .rfl .const, .constDF l1 l2 l3 l4 l5⟩
1187:     | extra r1 r2 r3 r4 =>
1188:       sorry
1189:   | @appDF Γ f A B f₂ a b l1 l2 l3 l4 l5 l6 ih1 ih2 =>
1190:     cases H2 with
1191:     | app r1 r2 =>
1192:       let ⟨_, a1, a2⟩ := ih1 hΓ r1
1193:       let ⟨_, b1, b2⟩ := ih2 hΓ r2
1194:       exact ⟨_, .app a1 b1,
1195:         .appDF (a1.hasType hΓ l1) (r1.hasType hΓ l2) (b1.hasType hΓ l3) (r2.hasType hΓ l4) a2 b2⟩
1196:     | @beta A _ e e' _ b' r1 r2 =>
1197:       let ⟨f', a1, a2⟩ := ih1 hΓ (.lam .rfl r1)
1198:       let ⟨a', b1, b2⟩ := ih2 hΓ r2
1199:       let ⟨⟨_, d1⟩, _, d2⟩ := l2.lam_inv henv hΓ
1200:       let ⟨⟨_, u1⟩, _, u2⟩ := ((d1.lam d2).uniqU henv hΓ l2).forallE_inv henv hΓ

## Rejection Summary

- TEST_FILE: 459
- TEACHING_EXERCISE_REPO: 105
- META_OR_MACRO_TARGET: 30
- TEST_HARNESS: 24
- INTENTIONAL_TEST_SORRY: 13
- TOO_MANY_SORRIES_IN_FILE: 8
- NO_LAKE_BUILD: 3
- PARKED_NAMED_OBSTRUCTION: 1
- SOLVED_LOCALLY_PR_OPEN: 1