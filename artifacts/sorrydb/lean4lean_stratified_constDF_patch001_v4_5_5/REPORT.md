# SorryDB v4.5.5 — lean4lean StratifiedUntyped constDF Patch001

## Target

- Repository: digama0/lean4lean
- Commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- File: Lean4Lean/Experimental/StratifiedUntyped.lean
- Theorem: IsDefEq.inductionU1
- Line: 72

## Hypothesis

The missing term is probably the `defEq` argument for `.defeq`, produced by `hdf` from the two `.const` typings and `.constDF h5`.

## Result

- status: PATCH001_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Variant Summary

- v01_trace_missing_defeq_goal: module_rc=0, module_seconds=1.07, full_rc=None, full_seconds=None
- v02_hdf_const_forward: module_rc=1, module_seconds=0.92, full_rc=None, full_seconds=None
- v03_hdf_const_reverse_symm: module_rc=1, module_seconds=0.92, full_rc=None, full_seconds=None
- v04_hdf_const_forward_symm_result: module_rc=1, module_seconds=0.91, full_rc=None, full_seconds=None
- v05_have_defs_then_exact_forward: module_rc=1, module_seconds=0.81, full_rc=None, full_seconds=None
- v06_have_defs_then_exact_reverse: module_rc=1, module_seconds=0.8, full_rc=None, full_seconds=None
- v07_trace_with_have_htypes: module_rc=1, module_seconds=0.91, full_rc=None, full_seconds=None

## Target Window

0055: theorem IsDefEq.inductionU1
0056:     (defEq : List VExpr → VExpr → VExpr → Prop)
0057:     (hasType : List VExpr → VExpr → VExpr → Prop)
0058:     (hty : ∀ {Γ e A}, HasTypeU1 env U defEq Γ e A → hasType Γ e A)
0059:     (hdf : ∀ {Γ e1 e2 A1 A2},
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
0085:     exact ⟨.forallE ih1.1 ih2.1, .forallE ih1.2.1 ih3.2.1, .forallEDF ih1.2.2 ih2.2.2⟩
0086:   | defeqDF _ _ _ ih1 ih2 =>
0087:     have h := hdf ih1.1 ih1.2.1 ih1.2.2; exact ⟨.defeq h ih2.1, .defeq h ih2.2.1, ih2.2.2⟩
0088:   | beta _ _ _ _ _ _ _ _ ihA _ ihe ihe' _ ihee =>
0089:     exact ⟨.app (.lam ihA.1 ihe.1) ihe'.1, ihee.1, .beta (hty ihe.1) (hty ihe'.1)⟩
0090:   | eta _ _ _ _ _ _ _ _ ihA _ _ ihe ihe' =>

## Recon

====================================================================================================
PATTERN: \btheorem\s+IsDefEq\.inductionU1\b
Lean4Lean/Experimental/StratifiedUntyped.lean:55: theorem IsDefEq.inductionU1
====================================================================================================
PATTERN: \btheorem\s+HasTypeU1\.induction\b
Lean4Lean/Experimental/StratifiedUntyped.lean:102: theorem HasTypeU1.induction (H : env.HasTypeU1 U defEq Γ e A) : env.HasType U Γ e A := by
====================================================================================================
PATTERN: \btheorem\s+IsDefEqU1\.induction\b
Lean4Lean/Experimental/StratifiedUntyped.lean:120: theorem IsDefEqU1.induction
====================================================================================================
PATTERN: \bunique_typing
Lean4Lean/Experimental/StratifiedUntyped.lean:178: theorem IsDefEqU1.unique_typing1
Lean4Lean/Experimental/StratifiedUntyped.lean:196: theorem HasType1.unique_typing'
Lean4Lean/Experimental/StratifiedUntyped.lean:245: theorem IsDefEq.unique_typing'
Lean4Lean/Experimental/Stratified.lean:193: theorem IsDefEq1.unique_typing1
Lean4Lean/Experimental/Stratified.lean:211: theorem HasType1.unique_typing'
Lean4Lean/Experimental/Stratified.lean:260: theorem IsDefEq.unique_typing'
====================================================================================================
PATTERN: \bconstDF\b
Lean4Lean/Experimental/StratifiedUntyped.lean:37:   | constDF : List.Forall₂ (· ≈ ·) ls ls' → Γ ⊢ .const c ls ≡ .const c ls'
Lean4Lean/Experimental/StratifiedUntyped.lean:71:   | @constDF _ _ ls₁ ls₂ _ _ h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/StratifiedUntyped.lean:72:     exact ⟨.const h1 h2 h4, .defeq sorry <| .const h1 h3 (h5.length_eq.symm.trans h4), .constDF h5⟩
Lean4Lean/Experimental/Stratified.lean:50:   | constDF :
Lean4Lean/Experimental/Stratified.lean:89:   | @constDF _ _ ls₁ ls₂ u _ h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/Stratified.lean:92:       .constDF h1 h2 h3 h4 h5⟩
Lean4Lean/Experimental/Stratified.lean:141:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/Stronger.lean:64:   | constDF :
Lean4Lean/Experimental/Stronger.lean:200:   | constDF h1 h2 h3 h4 h5 => exact .constDF (constants_out h1) h2 h3 h4 h5
Lean4Lean/Experimental/Stronger.lean:248:   | constDF h1 h2 h3 h4 h5 h6 h7 h8 h9 _ _ _ _ ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:250:     exact .constDF h1 h2 h3 h4 h5 h6 h7 h8 h9 (ih3 W) (ih4 W)
Lean4Lean/Experimental/Stronger.lean:289:   | constDF h1 h2 h3 h4 h5 h6 h7 _ _ _ _ ih1 ih2 ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:290:     exact .constDF (henv.1 h1) h2 h3 h4 h5 h6 h7 ih1 ih2 ih3 ih4
Lean4Lean/Experimental/Stronger.lean:321:   | constDF h1 h2 h3 h4 h5 h6 _ _ _ _ _ ih1 ih2 ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:323:     exact .constDF h1
Lean4Lean/Experimental/Stronger.lean:409:   | constDF h1 h2 h3 h4 h5 h6 h7 h8 h9 _ _ _ _ ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:411:     exact .constDF h1 h2 h3 h4 h5 h6 h7 h8 h9 (ih3 W hΓ) (ih4 W hΓ)
Lean4Lean/Experimental/Stronger.lean:532:   | constDF _ _ _ _ _ _ _ _ _ h => exact h
Lean4Lean/Experimental/Stronger.lean:552:   | constDF _ _ _ _ _ _ _ _ _ _ _ _ _ ih
Lean4Lean/Experimental/Stronger.lean:596:   | @constDF c ci ls _ _ _ h1 _ _ _ h2 hu _ d1 d2 d3 d4 ih1 ih2 ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:599:     | @constDF c' _ ls' _ _ _ h1' _ _ _ h2' hu' =>
Lean4Lean/Experimental/NormalEq.lean:34:   constDF :
Lean4Lean/Experimental/NormalEq.lean:167:   | constDF :
Lean4Lean/Experimental/NormalEq.lean:206:   | constDF h1 h2 h3 h4 h5 => exact TY.constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:228:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/NormalEq.lean:229:     exact .constDF h1 h3 h2 (h5.length_eq.symm.trans h4) (h5.flip.imp (fun _ _ h => h.symm))
Lean4Lean/Experimental/NormalEq.lean:243:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:266:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:320:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:356:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/NormalEq.lean:359:     exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:452:   | .constDF l1 l2 _ l4 l5, .constDF _ _ r3 r4 r5 =>
Lean4Lean/Experimental/NormalEq.lean:453:     .constDF l1 l2 r3 l4 (l5.trans (fun _ _ _ h1 => h1.trans) r5)
Lean4Lean/Experimental/ParallelReduction.lean:695:   | constDF l1 l2 l3 l4 l5 =>
Lean4Lean/Experimental/ParallelReduction.lean:697:     | const => exact ⟨_, .tail .rfl .const, .constDF l1 l2 l3 l4 l5⟩
Lean4Lean/Experimental/ParallelReduction.lean:846:   | constDF h1 h2 h3 h4 h5 => exact ⟨TY.constDF h1 h2 h3 h4 h5, TY.const h1 h2 h4⟩
Lean4Lean/Experimental/ParallelReduction.lean:869:   | constDF h1 h2 h3 h4 h5 => exact .normalEq (.constDF h1 h2 h3 h4 h5)
Lean4Lean/Verify/Typing/Lemmas.lean:1497:     refine ⟨_, .const h1 a1 (by simp [h3]), _, .constDF h1 (.of_mapM_ofLevel a1) ?_ ?_ a2⟩
Lean4Lean/Verify/TypeChecker/IsDefEq.lean:384:   have := VEnv.IsDefEq.constDF c1₁
Lean4Lean/Verify/TypeChecker/IsDefEq.lean:526:       have := VEnv.IsDefEq.constDF c1
Lean4Lean/Theory/Typing/Lemmas.lean:227:   .constDF h1 h2 h2 h3 (.rfl fun _ _ => rfl)
Lean4Lean/Theory/Typing/Lemmas.lean:325:   | constDF h1 =>
Lean4Lean/Theory/Typing/Lemmas.lean:389:   | constDF h1 h2 h3 h4 h5 => exact .constDF (henv.1 h1) h2 h3 h4 h5
Lean4Lean/Theory/Typing/Lemmas.lean:468:   | constDF _ h2 h3 => exact ⟨h2, h3, .instL h2⟩
Lean4Lean/Theory/Typing/Lemmas.lean:508:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Lemmas.lean:510:     exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/Lemmas.lean:603:   | @constDF _ _ ls₁ ls₂ _ h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Lemmas.lean:605:     exact .constDF h1 (by simp [VLevel.WF.inst hls]) (by simp [VLevel.WF.inst hls])
Lean4Lean/Theory/Typing/Lemmas.lean:651:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Lemmas.lean:653:     exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/Lemmas.lean:849:   | constDF h1 h2 =>
Lean4Lean/Theory/Typing/Strong.lean:23:   | constDF :
Lean4Lean/Theory/Typing/Strong.lean:149:   | constDF h1 h2 h3 h4 h5 h6 h7 _ _ ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:151:     exact .constDF h1 h2 h3 h4 h5 h6 h7 (ih2 W)
Lean4Lean/Theory/Typing/Strong.lean:189:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/Strong.lean:207:   | constDF h1 h2 h3 h4 h5 h6 _ _ ih1 ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:208:     exact .constDF (henv.1 h1) h2 h3 h4 h5 h6 ih1 ih2
Lean4Lean/Theory/Typing/Strong.lean:246:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Strong.lean:303:   | constDF h1 h2 h3 h4 h5 _ _ _ ih1 ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:305:     exact .constDF h1
Lean4Lean/Theory/Typing/Strong.lean:372:   | constDF h1 h2 h3 h4 h5 h6 h7 _ _ ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:374:     exact .constDF h1 h2 h3 h4 h5 h6 h7 (ih2 W hΓ)
Lean4Lean/Theory/Typing/Strong.lean:486:   | constDF h1 h2 =>
Lean4Lean/Theory/Typing/Strong.lean:535:   | constDF h1 h2 h3 h4 h5 h6 _ _ ih1 ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:543:       .constDF h1 a2 b2 (a3.length_eq.symm.trans h4) c2 (.inst a2) this (this.weak0 henv)
Lean4Lean/Theory/Typing/Strong.lean:620:   | @constDF _ _ ls₁ ls₂ _ h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Strong.lean:623:     exact .constDF h1 h2 h3 h4 h5 (.inst h2) this (this.weak0 henv)
Lean4Lean/Theory/Typing/Strong.lean:714:   | constDF h1 h2 h3 h4 h5 h6 h7 h8 ih1 ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:752:     exact .constDF h1 h2 h2 h3 (.rfl fun _ _ => rfl) h4 ih1 ih2
Lean4Lean/Theory/Typing/Basic.lean:24:   | constDF :
Lean4Lean/Theory/Typing/ChurchRosser.lean:82:   | constDF :
Lean4Lean/Theory/Typing/ChurchRosser.lean:121:   | constDF h1 h2 h3 h4 h5 => exact ⟨_, .constDF h1 h2 h3 h4 h5⟩
Lean4Lean/Theory/Typing/ChurchRosser.lean:146:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/ChurchRosser.lean:147:     exact .constDF h1 h3 h2 (h5.length_eq.symm.trans h4) (h5.flip.imp (fun _ _ h => h.symm))
Lean4Lean/Theory/Typing/ChurchRosser.lean:167:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/ChurchRosser.lean:192:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/ChurchRosser.lean:251:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/ChurchRosser.lean:289:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/ChurchRosser.lean:292:     exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/ChurchRosser.lean:398:   | .constDF l1 l2 _ l4 l5, .constDF _ _ r3 r4 r5 =>
====================================================================================================
PATTERN: \bdefeq\b
Lean4Lean/Experimental/SExpr.lean:536:   | .defeq a b rest => (a.applyS m1 m2, b.applyS m1 m2) :: rest.defeqsS m1 m2
Lean4Lean/Experimental/SExpr.lean:679: theorem IsDefEqStrong.defeq : IsDefEqStrong Γ e1 e2 A → Γ ⊢ e1 ≡ e2 : A := sorry
Lean4Lean/Experimental/SExpr.lean:725:   | defeq : Γ ⊢ A ≡ B : .sort u →
Lean4Lean/Experimental/SExpr.lean:835:   defeq' {{Δ ρ e1' e2' A'}} : Ctx.Lift' ρ Δ Γ →
Lean4Lean/Experimental/SExpr.lean:847:   defeq' _ _ _ _ _ W' h1 h2 h3 := imp (H.defeq' W' h1 h2 h3)
Lean4Lean/Experimental/SExpr.lean:855:   defeq' _ _ _ _ _ W := by rintro rfl he rfl; cases SExpr.lift'_inj.1 he; exact refl W rfl rfl
Lean4Lean/Experimental/SExpr.lean:864:   defeq' Δ' ρ' e1' e2' A' W' h1 h2 hA := by
Lean4Lean/Experimental/SExpr.lean:869:     exact weak I.diff (H.defeq' I.symm.diff rfl rfl rfl)
Lean4Lean/Experimental/SExpr.lean:889:   defeq' Δ' ρ' _ _ _ W' := by
Lean4Lean/Experimental/SExpr.lean:892:     exact H.defeq' (W'.comp W) rfl rfl rfl
Lean4Lean/Experimental/SExpr.lean:908:   defeq' _ _ _ _ _ W' h1 h2 h3 := symm (H.defeq' W' h2 h1 h3)
Lean4Lean/Experimental/SExpr.lean:921:   defeq' _ _ _ _ _ W' := by rintro rfl he hA; exact SExpr.lift'_inj.1 he ▸ H.left' W' rfl hA
Lean4Lean/Experimental/SExpr.lean:925: theorem WithLift.defeq (H : WithLift DefEq Γ e1 e2 A) : DefEq Γ e1 e2 A :=
Lean4Lean/Experimental/SExpr.lean:926:   H.defeq' .refl SExpr.lift'_refl.symm SExpr.lift'_refl.symm SExpr.lift'_refl.symm
Lean4Lean/Experimental/SExpr.lean:928: nonrec theorem IsDefEqLift.defeq (H : Γ ⊢ e1 ≡ e2 :↑ A) : Γ ⊢ e1 ≡ e2 : A := H.defeq
Lean4Lean/Experimental/SExpr.lean:1007: theorem WHRedS.defeq (H : Γ ⊢ e1 ⤳* e2) (he : Γ ⊢ e1 : A) : Γ ⊢ e1 ≡ e2 : A := sorry
Lean4Lean/Experimental/SExpr.lean:1233: theorem NormalEq.defeq (H : Γ ⊢ e1 ≡ₚ e2 : A) : Γ ⊢ e1 ≡ e2 : A := by
Lean4Lean/Experimental/SExpr.lean:1283:   ⟨H.defeq, _, _, .rfl, .rfl, H⟩
Lean4Lean/Experimental/SExpr.lean:1288: theorem CRDefEq.defeq : Γ ⊢ e₁ ≫≪ e₂ : A → Γ ⊢ e₁ ≡ e₂ : A := (·.1)
Lean4Lean/Experimental/SExpr.lean:1304:   ⟨H2.defeq H1, _, _, H2.parRedS, .rfl, .refl (H2.defeq H1).hasType.2⟩
Lean4Lean/Experimental/SExpr.lean:1308: theorem CRDefEqLift.defeq (H : Γ ⊢ e1 ≫≪ e2 :↑ A) : Γ ⊢ e1 ≡ e2 :↑ A := H.imp (·.1)
Lean4Lean/Experimental/SExpr.lean:1310: theorem CRDefEqLift.left (H : Γ ⊢ e1 ≫≪ e2 :↑ A) : Γ ⊢ e1 :↑ A := H.defeq.left
Lean4Lean/Experimental/StratifiedUntyped.lean:28:   | defeq : Γ ⊢ A ≡ B → Γ ⊢ e : A → Γ ⊢ e : B
Lean4Lean/Experimental/StratifiedUntyped.lean:72:     exact ⟨.const h1 h2 h4, .defeq sorry <| .const h1 h3 (h5.length_eq.symm.trans h4), .constDF h5⟩
Lean4Lean/Experimental/StratifiedUntyped.lean:75:     exact .defeq (hdf (.sort (l := l'.succ) h2) (.sort (l := l.succ) h1)
Lean4Lean/Experimental/StratifiedUntyped.lean:79:     exact ⟨.app hf ha, .defeq (hdf ihBa.2.1 ihBa.1 (.symm ihBa.2.2)) (.app hf' ha'), .appDF ff aa⟩
Lean4Lean/Experimental/StratifiedUntyped.lean:81:     refine ⟨.lam ihA.1 ihb.1, .defeq ?_ <| .lam ihA.2.1 ihb'.2.1, .lamDF ihA.2.2 ihb.2.2⟩
Lean4Lean/Experimental/StratifiedUntyped.lean:87:     have h := hdf ih1.1 ih1.2.1 ih1.2.2; exact ⟨.defeq h ih2.1, .defeq h ih2.2.1, ih2.2.2⟩
Lean4Lean/Experimental/StratifiedUntyped.lean:110:   | defeq h1 _ ih =>
Lean4Lean/Experimental/StratifiedUntyped.lean:112:     exact (IH h h1).defeq (ih hΓ)
Lean4Lean/Experimental/StratifiedUntyped.lean:202:   | defeq h1 _ ih =>
Lean4Lean/Experimental/StratifiedUntyped.lean:221:   case defeq.defeq _ _ _ =>
Lean4Lean/Experimental/Stratified.lean:41:   | defeq : Γ ⊢ A ≡ B : .sort u → Γ ⊢ e : A → Γ ⊢ e : B
Lean4Lean/Experimental/Stratified.lean:91:       .defeq (u := u.inst ls₁) sorry <| .const h1 h3 (h5.length_eq.symm.trans h4),
Lean4Lean/Experimental/Stratified.lean:95:     exact .defeq (hdf <| .symm <| .sortDF (l' := l'.succ) h1 h2 (VLevel.succ_congr h3)) (.sort h2)
Lean4Lean/Experimental/Stratified.lean:98:     exact ⟨.app hf ha, .defeq (hdf ihBa.2.2.symm) (.app hf' ha'), .appDF ff aa⟩
Lean4Lean/Experimental/Stratified.lean:101:     exact .defeq (hdf <| .symm <| .forallEDF ihA.2.2 ihB.2.2) <| .lam ihA.2.1 ihb'.2.1
Lean4Lean/Experimental/Stratified.lean:105:     exact ⟨.defeq (hdf ih1.2.2) ih2.1, .defeq (hdf ih1.2.2) ih2.2.1, .defeqDF (hdf ih1.2.2) ih2.2.2⟩
Lean4Lean/Experimental/Stratified.lean:128:   | defeq h1 _ ih => exact (IH h1).defeq ih
Lean4Lean/Experimental/Stratified.lean:217:   | defeq h1 _ ih =>
Lean4Lean/Experimental/Stratified.lean:236:   case defeq.defeq _ _ _ =>
Lean4Lean/Experimental/Stronger.lean:227:   | defeq : Ordered env → df.WF env → Ordered (env.addDefEq df)
Lean4Lean/Experimental/Stronger.lean:233:   | defeq h1 h2 ih => exact addDefEq_out ▸ .defeq ih h2.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:121:   | symm H ih => exact .fits fun W => (ih ((LE_Interp.sound H.defeq W).1.2 hM) hA hmem).symm
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:123:     exact .fits fun W => (ih1 hM hA hmem).trans (ih2 ((LE_Interp.sound H1.defeq W).1.1 hM) hA hmem)
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:129:     refine have ihs1 := LE_Interp.sound H1.defeq W; have hM₂ := ihs1.1.1 hM; ?_
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:130:     have ihs2 := LE_Interp.sound H2.defeq W (m := m.T)
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:168:       refine ⟨fun σ σ' W => ⟨?_, ?_⟩, fun σ W => this W Hf.defeq Ha.defeq HBa.defeq hif hia hA ihf iha ihBa⟩
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:169:       · refine this W Hf.defeq.hasType.1 Ha.defeq.hasType.1 HBa.defeq.hasType.1 hif hia hA ?_ ?_ ?_
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:174:           Hf.defeq.hasType.2 Ha.defeq.hasType.2 HBa.defeq.hasType.2
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:175:           ((LE_Interp.sound Hf.defeq W.fits).1.1 hif) ((LE_Interp.sound Ha.defeq W.fits).1.1 hia)
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:176:           ((LE_Interp.sound HBa.defeq W.fits).1.1 hA)
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:178:         · have ⟨_, _, _, le, le', iB, iv, hmb⟩ := (LE_Interp.sound HBa.defeq W.fits).2 hA |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:180:         · exact (ihf ((LE_Interp.sound Hf.defeq W.left.fits).1.2 hf) hPi hmf).symm.left
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:181:         · exact (iha ((LE_Interp.sound Ha.defeq W.left.fits).1.2 ha) hA hma).symm.left
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:182:         · exact (ihBa ((LE_Interp.sound HBa.defeq W.left.fits).1.2 hB) hv hmb).symm.left
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:254:         · exact (LE_Interp.sound (.lamDF HA.defeq HBody.defeq) W.fits).1.1 hM
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:255:         · exact (ihBody ((LE_Interp.sound HBody.defeq W).1.2 hMb') hBb hmb).symm.left
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:273:       HA.defeq.hasType.1.subst W.left.toSubstEq
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:275:       HB.defeq.subst (W.left.toSubstEq.lift hTypA)
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:278:       (LE_Interp.sound HA.defeq W.left.fits).2 hA1 |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:279:     have cons := Adequate.cons ihA HA.defeq
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:293:         (LE_Interp.sound HB.defeq W'.fits).2 (hA.forallE_inv'.2 p) |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:306:         have ha' : Γ₀ ⊢ x ≡ x' : A.subst σ' := (HA.defeq.hasType.1.subst W.toSubstEq).defeqDF ha
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:308:         have ⟨n', _, _, le, le', iB, iv, hmb⟩ := (LE_Interp.sound HB.defeq W'.fits).2 hBb_sd |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:331:     have cons := Adequate.cons ihA HA.defeq
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:334:         (LE_Interp.sound HA.defeq W.left.fits).2 hA1 |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:335:       have HAAσ := HA.defeq.subst W.left.toSubstEq
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:337:     · have HAσ := HA.defeq.hasType.1.subst W.toSubstEq
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:338:       have HA'σ := HA.defeq.hasType.2.subst W.toSubstEq
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:341:           .rfl, .rfl, HAσ, HBody.defeq.hasType.1.subst S', ?_, ?_⟩
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:351:             (LE_Interp.sound HBody.defeq W'.fits).2 hB |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:354:           .rfl, .rfl, HA'σ, HAAσ.defeqDF_l (HBody.defeq.hasType.2.subst S'), ?_, ?_⟩
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:366:         · have ⟨_, _, _, le, le', iB, iv, hmb⟩ := (LE_Interp.sound HBody.defeq W'.fits).2 hB |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:369:         .rfl, .rfl, HAAσ, HBody.defeq.subst S', ?_, ?_⟩
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:375:         have ⟨_, _, _, le, le', iB, iv, hmb⟩ := (LE_Interp.sound HBody.defeq W'.fits).2 hB |>.out)
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:381:       have hA' := (LE_Interp.sound Hty.defeq W.fits).1.2 hA
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:383:         (LE_Interp.sound Hty.defeq W.fits).2 hA' |>.out
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:386:       have hA' := (LE_Interp.sound Hty.defeq W.left.fits).1.2 hA
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:393:     · exact ((ihinst ((LE_Interp.sound (.beta He.defeq Ha.defeq) W.fits).1.1 hM) hA hmem).1 W).2
====================================================================================================
PATTERN: \binductive\s+HasTypeU1\b
Lean4Lean/Experimental/StratifiedUntyped.lean:17: inductive HasTypeU1 : List VExpr → VExpr → VExpr → Prop where
====================================================================================================
PATTERN: \binductive\s+IsDefEqU1\b
Lean4Lean/Experimental/StratifiedUntyped.lean:33: inductive IsDefEqU1 : List VExpr → VExpr → VExpr → Prop where
Lean4Lean/Experimental/StratifiedUntyped.lean:170: inductive IsDefEqU1 : List VExpr → VExpr → VExpr → VLevel → Prop
Lean4Lean/Experimental/Stratified.lean:185: inductive IsDefEqU1 : List VExpr → VExpr → VExpr → VLevel → Prop
====================================================================================================
PATTERN: \binductive\s+HasType\b
====================================================================================================
PATTERN: \binductive\s+IsDefEq\b
Lean4Lean/Experimental/SExpr.lean:589: inductive IsDefEq : List SExpr → SExpr → SExpr → SExpr → Prop where
Lean4Lean/Experimental/UniqueTyping.lean:195: inductive IsDefEq' : List SExpr → SExpr → SExpr → SExpr → Prop where
Lean4Lean/Theory/Typing/Basic.lean:17: inductive IsDefEq : List VExpr → VExpr → VExpr → VExpr → Prop where

## Next Move

Use v01 trace and hdf constructor mismatch diagnostics to build Patch002, or park if this depends on unfinished core theory.