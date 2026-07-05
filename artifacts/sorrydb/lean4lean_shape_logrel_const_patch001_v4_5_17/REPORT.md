# SorryDB v4.5.17 — ShapeLogRelAdequacy const Patch001

## Target

- Repository: digama0/lean4lean
- File: Lean4Lean/Experimental/ShapeLogRelAdequacy.lean
- Theorem: LR.adequacy
- Case: const
- Line: 154

## Result

- status: PATCH001_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Variant Summary

- v01_trace_goal: module_rc=0, seconds=3.21, target_sorry=True, full_rc=None
- v02_exact_hmem: module_rc=1, seconds=3.1, target_sorry=False, full_rc=None
- v03_exact_LR_bot: module_rc=1, seconds=3.13, target_sorry=False, full_rc=None
- v04_exact_refl: module_rc=1, seconds=6.26, target_sorry=False, full_rc=None
- v05_exact_Adequate_refl: module_rc=1, seconds=5.23, target_sorry=False, full_rc=None
- v06_try_constructor: module_rc=1, seconds=6.54, target_sorry=False, full_rc=None
- v07_simp: module_rc=1, seconds=2.85, target_sorry=False, full_rc=None
- v08_simp_all: module_rc=1, seconds=2.8, target_sorry=False, full_rc=None
- v09_first_order_try: module_rc=1, seconds=3.22, target_sorry=False, full_rc=None
- v10_trace_after_have: module_rc=1, seconds=2.58, target_sorry=False, full_rc=None
- v11_try_bot_from_type: module_rc=1, seconds=2.79, target_sorry=False, full_rc=None
- v12_try_cases_a: module_rc=1, seconds=2.8, target_sorry=False, full_rc=None
- v13_try_cases_m_a: module_rc=1, seconds=2.91, target_sorry=False, full_rc=None
- v14_trace_constructor: module_rc=1, seconds=2.68, target_sorry=False, full_rc=None

## Target Window

0130:     have ihs2 := LE_Interp.sound H2.defeq W (m := m.T)
0131:     have ⟨a₂, s₂, b1, b2, b3, b4⟩ := ihs2.2 hM₂
0132:     replace b4 := TShape.HasType.sort.mono_r b3.le_sort b4
0133:     have := TShape.HasType.mono_r hA.le_sort .sort hmem.T
0134:     refine ih2 (ihs1.1.1 hM) (.sort TShape.sort_eqv.1) ?_
0135:     exact WShape.HasType.T_iff.1 <| .mono_r TShape.sort_eqv.2 .sort_T <| this.retype b4 b1
0136:   | @sort _ l =>
0137:     suffices (LR Γ₀).DefEq (.sort l) (.sort l) (.sort l.succ) m a from
0138:       ⟨fun _ _ _ => ⟨this, this⟩, fun _ _ => this⟩
0139:     cases hmem.unfold with
0140:     | bot hm => exact (LR _).bot hm
0141:     | sort => exact (LR _).sort_iff.2 ⟨_, .rfl, .rfl⟩
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
0167:           (.subst (B.inst X) σ) m a by
0168:       refine ⟨fun σ σ' W => ⟨?_, ?_⟩, fun σ W => this W Hf.defeq Ha.defeq HBa.defeq hif hia hA ihf iha ihBa⟩
0169:       · refine this W Hf.defeq.hasType.1 Ha.defeq.hasType.1 HBa.defeq.hasType.1 hif hia hA ?_ ?_ ?_
0170:         · exact fun hf hPi hmf => (ihf hf hPi hmf).left

## Local Definitions Window

0001: import Lean4Lean.Experimental.ShapeLogRel
0002: 
0003: namespace Lean4Lean
0004: 
0005: namespace SExpr
0006: variable [Params]
0007: 
0008: def LR.Adequate (Γ₀ Γ : List SExpr) (ρ : Valuation) (M N A : SExpr) (m a : WShape n) :=
0009:   (∀ {{σ σ'}}, LR.SubstWF Γ₀ σ σ' Γ ρ →
0010:     (LR Γ₀).DefEq (M.subst σ) (M.subst σ') (A.subst σ) m a ∧
0011:     (LR Γ₀).DefEq (N.subst σ) (N.subst σ') (A.subst σ) m a) ∧
0012:   ∀ {{σ}}, LR.SubstWF Γ₀ σ σ Γ ρ → (LR Γ₀).DefEq (M.subst σ) (N.subst σ) (A.subst σ) m a
0013: 
0014: theorem LR.Adequate.bot (ha : a.HasType .type) : Adequate Γ₀ Γ ρ M N A .bot a :=
0015:   ⟨fun _ _ _ => ⟨(LR _).bot ha, (LR _).bot ha⟩, fun _ _ => (LR _).bot ha⟩
0016: 
0017: theorem LR.Adequate.fits
0018:     (H : ρ.Fits Γ₀ Γ → Adequate Γ₀ Γ ρ M N A m a) : Adequate Γ₀ Γ ρ M N A m a :=
0019:   ⟨fun _ _ W => (H W.fits).1 W, fun _ W => (H W.fits).2 W⟩
0020: 
0021: theorem LR.Adequate.refl
0022:     (H : ∀ {{σ σ'}}, LR.SubstWF Γ₀ σ σ' Γ ρ →
0023:       (LR Γ₀).DefEq (M.subst σ) (M.subst σ') (A.subst σ) m a) :
0024:     Adequate Γ₀ Γ ρ M M A m a := ⟨fun _ _ W => ⟨H W, H W⟩, fun _ W => H W⟩
0025: 
0026: theorem LR.Adequate.left : Adequate Γ₀ Γ ρ M N A m a → Adequate Γ₀ Γ ρ M M A m a
0027:   | ⟨h1, _⟩ => .refl fun _ _ W => (h1 W).1
0028: 
0029: theorem LR.Adequate.symm : Adequate Γ₀ Γ ρ M N A m a → Adequate Γ₀ Γ ρ N M A m a
0030:   | ⟨h1, h2⟩ => ⟨fun _ _ W => (h1 W).symm, fun _ W => (LR _).symm (h2 W)⟩
0031: 
0032: theorem LR.Adequate.trans :
0033:     Adequate Γ₀ Γ ρ M₁ M₂ A m a → Adequate Γ₀ Γ ρ M₂ M₃ A m a → Adequate Γ₀ Γ ρ M₁ M₃ A m a
0034:   | ⟨a1, a2⟩, ⟨b1, b2⟩ =>
0035:     ⟨fun _ _ W => ⟨(a1 W).1, (b1 W).2⟩, fun _ W => (LR _).trans (a2 W) (b2 W)⟩
0036: 
0037: theorem LR.Adequate.trans' : Adequate Γ₀ Γ ρ A₁ A₂ (.sort u) a s →
0038:     Adequate Γ₀ Γ ρ A₂ A₃ (.sort v) a (.sort r) → Adequate Γ₀ Γ ρ A₁ A₃ (.sort u) a s
0039:   | ⟨a1, a2⟩, ⟨b1, b2⟩ => by
0040:     refine ⟨fun σ σ' W => ⟨(a1 W).1, ?_⟩, fun _ W => (LR _).trans' (a2 W) (b2 W)⟩
0041:     have h1 := (LR _).trans' (a1 W.left).2 (b2 W.left)
0042:     have h2 := (LR _).trans' (a1 W.symm.left).2 (b2 W.symm.left)
0043:     exact (LR _).trans ((LR _).symm h1) <| (LR _).trans (a1 W).2 h2
0044: 
0045: theorem LR.Adequate.cons
0046:     (ihA : ∀ {ρ n} {m a : WShape n}, LE_Interp ρ m.T A → LE_Interp ρ a.T (.sort u) →
0047:       m.HasType a → Adequate Γ₀ Γ ρ A A' (sort u) m a)
0048:     (HA : Γ ⊢ A ≡ A' : .sort u)
0049:     {{k : Nat}} {{a₁ p : WShape k}} {{x x' σ σ' ρ}}
0050:     (hp : p.HasType a₁) (hA₁ : LE_Interp ρ a₁.T A)
0051:     (hx : Γ₀ ⊢ x ≡ x' : A.subst σ) (hv : (LR Γ₀).DefEq x x' (A.subst σ) p a₁)
0052:     (W : SubstWF Γ₀ σ σ' Γ ρ) : SubstWF Γ₀ (σ.cons x) (σ'.cons x') (A :: Γ) (ρ.push p.T) := by
0053:   refine W.cons (fun hA => ?_) hA₁ hp.T HA.hasType.1 ⟨hx, fun n a' ha' => ?_⟩
0054:   · have ⟨_, _, le_a, hA', hSort, hmem'⟩ := (LE_Interp.sound HA W.fits).2 hA
0055:     exact ⟨_, le_a, hA', (TShape.HasType.mono_r hSort.le_sort .sort hmem').toType⟩
0056:   have ha' := LE_Interp.weak_iff.1 ha'
0057:   refine ⟨fun ht => ⟨⟨_, HA.hasType.1.subst W.toSubstEq⟩, ?_⟩, fun m' hm' ht => ?_⟩
0058:   · have ⟨_, _, _, le_n, le_a, hA', hSort, hmem'⟩ := (LE_Interp.sound HA W.fits).2 ha' |>.out
0059:     refine (TyDefEq.lift le_n ht).1 <| (LR Γ₀).mono_r_2_ty ((TShape.LE.lift_l le_n).1 le_a)
0060:       (WShape.lift_type ▸ (WShape.HasType.lift le_n).2 ht)
0061:       (WShape.HasType.mono_r hSort.le_sort' .sort hmem').toType ?_
0062:     exact (LR Γ₀).toType <| (LR Γ₀).mono_r_1 hSort.le_sort' hmem'
0063:       (.mono_r hSort.le_sort' .sort hmem') .sort ((ihA hA' hSort hmem').1 W).1
0064:   · have le_k := Nat.le_max_left k n; have le_n := Nat.le_max_right k n
0065:     have ht' := (WShape.HasType.lift le_n).2 ht
0066:     have hp' := (WShape.HasType.lift le_k).2 hp
0067:     have hle' := (TShape.LE.def le_n le_k).1 (LE_Interp.bvar_iff.1 hm')
0068:     have hta₁ := WShape.lift_type ▸ (WShape.HasType.lift le_k).2 hp.isType
0069:     have hta' := WShape.lift_type ▸ (WShape.HasType.lift le_n).2 ht.isType
0070:     have hc := hA₁.compat ha'
0071:     have hj := (TShape.Join.def le_k le_n (Nat.le_refl _)).1 (.mk hc)
0072:     rw [TShape.lift_join le_k le_n] at hj
0073:     have ⟨hj1, hj2⟩ := hj.le
0074:     have hJ := hta₁.join' hj hta'
0075:     have hJ' := hJ.mono_r hj1 hp'
0076:     refine (DefEq.lift le_n ht).1 <|
0077:       (LR Γ₀).mono_r_2 hj2 ht' hJ <|
0078:       (LR Γ₀).mono_l hle' (hJ.mono_r hj2 ht') hJ' <|
0079:       (LR Γ₀).mono_r_1 hj1 hp' hJ' ?_ <| (DefEq.lift le_k hp).2 hv
0080:     have valTyA {nd : Nat} {a : WShape nd} (hA : LE_Interp ρ a.T A) (ha : a.HasType .type) :

## Recon

====================================================================================================
PATTERN: inductive .*DefEq
Lean4Lean/Experimental/SExpr.lean:589: inductive IsDefEq : List SExpr → SExpr → SExpr → SExpr → Prop where
Lean4Lean/Experimental/SExpr.lean:643: inductive IsDefEqStrong : List SExpr → SExpr → SExpr → SExpr → Prop where
Lean4Lean/Experimental/SExpr.lean:931: inductive IsDefEqCtx : List SExpr → List SExpr → Prop
Lean4Lean/Experimental/StratifiedUntyped.lean:33: inductive IsDefEqU1 : List VExpr → VExpr → VExpr → Prop where
Lean4Lean/Experimental/StratifiedUntyped.lean:170: inductive IsDefEqU1 : List VExpr → VExpr → VExpr → VLevel → Prop
Lean4Lean/Experimental/Stratified.lean:46: inductive IsDefEq1 : List VExpr → VExpr → VExpr → VExpr → Prop where
Lean4Lean/Experimental/Stratified.lean:185: inductive IsDefEqU1 : List VExpr → VExpr → VExpr → VLevel → Prop
Lean4Lean/Experimental/Stronger.lean:57: inductive IsDefEqStrong : VCtx → VExpr → VExpr → VExpr → VLevel → Prop where
Lean4Lean/Experimental/UniqueTyping.lean:195: inductive IsDefEq' : List SExpr → SExpr → SExpr → SExpr → Prop where
Lean4Lean/Experimental/NormalEq.lean:11: inductive IsDefEqCtx : List VExpr → List VExpr → Prop
Lean4Lean/Verify/Typing/Lemmas.lean:174: inductive VLocalDecl.IsDefEq : VLocalDecl → VLocalDecl → Prop
Lean4Lean/Verify/Typing/Lemmas.lean:670: inductive VLCtx.IsDefEq : VLCtx → VLCtx → Prop
Lean4Lean/Verify/TypeChecker/Basic.lean:48: inductive IsDefEqE : Expr → Expr → Prop
Lean4Lean/Theory/Typing/Lemmas.lean:294: inductive IsDefEqCtx : List VExpr → List VExpr → Prop
Lean4Lean/Theory/Typing/Strong.lean:16: inductive IsDefEqStrong : List VExpr → VExpr → VExpr → VExpr → Prop where
Lean4Lean/Theory/Typing/Basic.lean:17: inductive IsDefEq : List VExpr → VExpr → VExpr → VExpr → Prop where
====================================================================================================
PATTERN: def .*DefEq
Lean4Lean/TypeChecker.lean:150: def isDefEqCore (t s : Expr) : RecM Bool := fun m => m.isDefEqCore t s
Lean4Lean/TypeChecker.lean:152: def isDefEq (t s : Expr) : RecM Bool := do
Lean4Lean/TypeChecker.lean:450: def isDefEqLambda (t s : Expr) (subst : Array Expr := #[]) : RecM Bool :=
Lean4Lean/TypeChecker.lean:466: def isDefEqForall (t s : Expr) (subst : Array Expr := #[]) : RecM Bool :=
Lean4Lean/TypeChecker.lean:482: def quickIsDefEq (t s : Expr) (useHash := false) : RecM LBool := do
Lean4Lean/TypeChecker.lean:496: def isDefEqArgs (t s : Expr) : RecM Bool := do
Lean4Lean/TypeChecker.lean:528: def isDefEqApp (t s : Expr) : RecM Bool := do
Lean4Lean/TypeChecker.lean:542: def isDefEqProofIrrel (t s : Expr) : RecM LBool := do
Lean4Lean/TypeChecker.lean:610: def isDefEqOffset (t s : Expr) : RecM LBool := do
Lean4Lean/TypeChecker.lean:648: def isDefEqUnitLike (t s : Expr) : RecM Bool := do
Lean4Lean/TypeChecker.lean:657: def isDefEqCore' (t s : Expr) : RecM Bool := do
Lean4Lean/TypeChecker.lean:733: def isDefEq (t s : Expr) : M Bool := (Inner.isDefEq t s).run
Lean4Lean/Experimental/SExpr.lean:840: def IsDefEqLift := WithLift IsDefEq
Lean4Lean/Experimental/SExpr.lean:1274: def CRDefEq (Γ : List SExpr) (e₁ e₂ A : SExpr) : Prop :=
Lean4Lean/Experimental/SExpr.lean:1279: def CRDefEqLift := WithLift CRDefEq
Lean4Lean/Experimental/Thierry2.lean:624: def DefEqPiF (B F F' : Expr) (b : Shape n) (f : ShapeFun n) : Prop :=
Lean4Lean/Experimental/Thierry2.lean:631: def DefEqLamF (M M' B F : Expr) (m : ShapeFun n) (b : Shape n) (f : ShapeFun n) : Prop :=
Lean4Lean/Experimental/Thierry2.lean:640: def DefEqF : ∀ {n}, Expr → Expr → Expr → Shape n → Shape n → Prop
Lean4Lean/Experimental/Stronger.lean:139: def VDefEq.WF (env : VEnv') (df : VDefEq) : Prop :=
Lean4Lean/Experimental/Stronger.lean:159: def addDefEq (env : VEnv') (df : VDefEq) : VEnv' :=
Lean4Lean/Experimental/ParallelReduction.lean:795: def Typing.CRDefEq (Γ : List VExpr) (e₁ e₂ : VExpr) : Prop :=
Lean4Lean/Experimental/LogRel.lean:23: def Classifier.DefEq (cl : Classifier Γ A u) (a b : SExpr) : Prop :=
Lean4Lean/Experimental/LogRel.lean:104: def LRDefEq {Γ A u} (a b : SExpr) (H : Γ ⊩[u] A) : Prop := H.1.DefEq a b
Lean4Lean/Experimental/LogRel.lean:345: def LVDefEq {J : ⊩ᵛ Γ} (JA : J ⊩ᵛ[u] A) (a b : SExpr) : Prop :=
Lean4Lean/Experimental/MoreStepIndexed.lean:46: def CRDefEqN (Γ : List SExpr) (A B : SExpr) (n : Nat) : Prop :=
Lean4Lean/Experimental/MoreStepIndexed.lean:346: def Classifier.DefEq (C : Classifier Γ A B (n := n) k) (a b : SExpr) (p : Shape n) : Prop :=
Lean4Lean/Experimental/ShapeLogRel.lean:5288: def LR0.TyDefEq (Γ : List SExpr) (M N : SExpr) : WShape 0 → Prop
Lean4Lean/Experimental/ShapeLogRel.lean:5292: def LR0.DefEq (Γ : List SExpr) (M N : SExpr) (m a : WShape 0) : Prop :=
Lean4Lean/Experimental/ShapeLogRel.lean:5366: def LRS.PiDefEq (IH : LogRel Γ n)
Lean4Lean/Experimental/ShapeLogRel.lean:5384: def LRS.LamDefEq (IH : LogRel Γ n)
Lean4Lean/Experimental/ShapeLogRel.lean:5421: def LRS.TyDefEq (IH : LogRel Γ n) (M N : SExpr) : WShape (n+1) → Prop
Lean4Lean/Experimental/ShapeLogRel.lean:5602: def LRS.DefEq (IH : LogRel Γ n) (M N A : SExpr) (m a : WShape (n+1)) : Prop :=
Lean4Lean/Theory/Quot.lean:11: def quotDefEq := vdefeq(α r β f c a => @Quot.lift α r β f c (Quot.mk r a) ≡ f a)
Lean4Lean/Theory/VEnv.lean:32: def VEnv.addDefEq (env : VEnv) (df : VDefEq) : VEnv :=
Lean4Lean/Theory/VDecl.lean:11: def VDefVal.toDefEq (v : VDefVal) : VDefEq :=
Lean4Lean/Theory/Typing/Basic.lean:65: def IsDefEqU (env : VEnv) (U : Nat) (Γ : List VExpr) (e₁ e₂ : VExpr) :=
Lean4Lean/Theory/Typing/Basic.lean:70: def VExpr.WF (env : VEnv) (U : Nat) (Γ : List VExpr) (e : VExpr) := env.IsDefEqU U Γ e e
Lean4Lean/Theory/Typing/Basic.lean:74: def VDefEq.WF (env : VEnv) (df : VDefEq) : Prop :=
Lean4Lean/Theory/Typing/Env.lean:18:     VDecl.WF env (.def ci) (env'.addDefEq ci.toDefEq)
Lean4Lean/Theory/Typing/ChurchRosser.lean:1292: def CRDefEq (Γ : List VExpr) (e₁ e₂ : VExpr) : Prop :=
====================================================================================================
PATTERN: \.DefEq
Lean4Lean/Experimental/CoinductiveLogRel.lean:55:     (∀ {ρ Δ} W {a b} (ab : (@RA ρ Δ W).DefEq a b), (RB W ab.left).EqTy ((B.lift' ρ.cons).inst b)) →
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:10:     (LR Γ₀).DefEq (M.subst σ) (M.subst σ') (A.subst σ) m a ∧
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:11:     (LR Γ₀).DefEq (N.subst σ) (N.subst σ') (A.subst σ) m a) ∧
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:12:   ∀ {{σ}}, LR.SubstWF Γ₀ σ σ Γ ρ → (LR Γ₀).DefEq (M.subst σ) (N.subst σ) (A.subst σ) m a
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:23:       (LR Γ₀).DefEq (M.subst σ) (M.subst σ') (A.subst σ) m a) :
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:51:     (hx : Γ₀ ⊢ x ≡ x' : A.subst σ) (hv : (LR Γ₀).DefEq x x' (A.subst σ) p a₁)
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:96:     (H : (LR Γ₀).DefEq M N (.sort u) m a) : (LR Γ₀).TyDefEq M N b := by
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:137:     suffices (LR Γ₀).DefEq (.sort l) (.sort l) (.sort l.succ) m a from
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:151:     suffices ∀ {σ}, (LR Γ₀).DefEq (const c ls) (const c ls) (((mk ci.type).instL ls).subst σ) m a
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:166:         (LR Γ₀).DefEq (.subst (.app F X) σ) (.subst (.app F' X') σ')
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:216:     refine (LR.DefEq.lift hk.1 hmem).1 <| (LR Γ₀).mono_r_2 hJ1' hmem_k hJ_t' ?_
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:230:       · rw [LRS.DefEq.lam_forallE] at hAf
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:249:         (LR Γ₀).DefEq (.subst (.lam X Y) σ) (.subst (.lam X' Y') σ')
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:258:         (LR Γ₀).DefEq (.subst (.lam X Y) σ) (.subst (.lam X' Y') σ')
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:283:     simp only [LR, LRS, LRS.DefEq.lam_forallE]
Lean4Lean/Experimental/LogRel.lean:23: def Classifier.DefEq (cl : Classifier Γ A u) (a b : SExpr) : Prop :=
Lean4Lean/Experimental/LogRel.lean:24:   Γ ⊢ a ≫≪ b :↑ A ∧ cl.HasTy' a ∧ cl.HasTy' b ∧ cl.DefEq' a b
Lean4Lean/Experimental/LogRel.lean:26: theorem Classifier.DefEq.symm {cl : Classifier Γ A u} : cl.DefEq a b → cl.DefEq b a
Lean4Lean/Experimental/LogRel.lean:28: theorem Classifier.DefEq.left {cl : Classifier Γ A u} : cl.DefEq a b → cl.HasTy a
Lean4Lean/Experimental/LogRel.lean:31: theorem Classifier.defEq_self {cl : Classifier Γ A u} : cl.DefEq a a ↔ cl.HasTy a :=
Lean4Lean/Experimental/LogRel.lean:34: theorem Classifier.DefEq.imp {Γ A u Γ' A' u'} {cl : Classifier Γ A u} {cl' : Classifier Γ' A' u'}
Lean4Lean/Experimental/LogRel.lean:38:     (H2 : ∀ {a b}, cl.DefEq' a b → cl'.DefEq' (f a) (f b))
Lean4Lean/Experimental/LogRel.lean:39:     {a b} : cl.DefEq a b → cl'.DefEq (f a) (f b)
Lean4Lean/Experimental/LogRel.lean:50:   HasTy' f := ∀ {ρ Δ W a b} (ab : (@RA ρ Δ W).DefEq a b),
Lean4Lean/Experimental/LogRel.lean:51:     (RB W ab.left).DefEq ((f.lift' ρ).app a) ((f.lift' ρ).app b)
Lean4Lean/Experimental/LogRel.lean:53:     (RB W ha).DefEq ((f.lift' ρ).app a) ((g.lift' ρ).app a)
Lean4Lean/Experimental/LogRel.lean:84:     (∀ {ρ Δ} W {a b} (ab : (@RA ρ Δ W).DefEq a b), (RB W ab.left).EqTy ((B.lift' ρ.cons).inst b)) →
Lean4Lean/Experimental/LogRel.lean:104: def LRDefEq {Γ A u} (a b : SExpr) (H : Γ ⊩[u] A) : Prop := H.1.DefEq a b
Lean4Lean/Experimental/LogRel.lean:203:     (J.cast eq).1.DefEq a b ↔ cl.DefEq a b := and_congr_left' (eq ▸ .rfl)
Lean4Lean/Experimental/MoreStepIndexed.lean:346: def Classifier.DefEq (C : Classifier Γ A B (n := n) k) (a b : SExpr) (p : Shape n) : Prop :=
Lean4Lean/Experimental/MoreStepIndexed.lean:347:   CheckType Γ a A ∧ CheckType Γ b B ∧ CRDefEq Γ a b A ∧ C.DefEq' a b p
Lean4Lean/Experimental/MoreStepIndexed.lean:349: theorem Classifier.DefEq.mono {C : Classifier Γ A B k}
Lean4Lean/Experimental/MoreStepIndexed.lean:350:     (le : p ≤ p') : C.DefEq a b p' → C.DefEq a b p
Lean4Lean/Experimental/MoreStepIndexed.lean:354:   mono' : C.DefEq' a b p → C'.DefEq' a b p
Lean4Lean/Experimental/MoreStepIndexed.lean:355:   mono'_r : C.DefEq' a b p → C'.DefEq' a b p
Lean4Lean/Experimental/MoreStepIndexed.lean:363:     C.DefEq a b p → C'.DefEq a b p
Lean4Lean/Experimental/MoreStepIndexed.lean:410:     (∀ a b p, CA.DefEq a b p → (IH (A₁::Γ) A₂ B₂).TypeEq (kB.app p) (CB a b p)) ∧
Lean4Lean/Experimental/MoreStepIndexed.lean:412:       DefEq' f g p := ∀ a b p', CA.DefEq a b p' → (CB a b p').DefEq (f.app a) (g.app b) (p.app p')
Lean4Lean/Experimental/MoreStepIndexed.lean:467:   --         --   ∀ u v, CA.DefEq u v → CF.DefEq (.app _ u)
Lean4Lean/Experimental/MoreStepIndexed.lean:483:   --       --   ∀ u v, CA.DefEq u v → CF.DefEq (.app _ u)
Lean4Lean/Experimental/ShapeLogRel.lean:5292: def LR0.DefEq (Γ : List SExpr) (M N : SExpr) (m a : WShape 0) : Prop :=
Lean4Lean/Experimental/ShapeLogRel.lean:5298:   DefEq M N _ := LR0.DefEq Γ M N
Lean4Lean/Experimental/ShapeLogRel.lean:5300:   sort_iff := by simp [LR0.DefEq, LR0.TyDefEq, WShape.sort]
Lean4Lean/Experimental/ShapeLogRel.lean:5302:   bot {_ _ _ _} _ := by simp only [LR0.DefEq, LR0.TyDefEq, WShape.bot]; split <;> trivial
Lean4Lean/Experimental/ShapeLogRel.lean:5305:     dsimp [LR0.DefEq]; split <;> [trivial; skip]
Lean4Lean/Experimental/ShapeLogRel.lean:5312:     dsimp [LR0.DefEq]; split <;> [trivial; skip]
Lean4Lean/Experimental/ShapeLogRel.lean:5319:     dsimp [LR0.DefEq]; split <;> [trivial; skip]
Lean4Lean/Experimental/ShapeLogRel.lean:5324:     dsimp [LR0.DefEq]; split <;> [(intros; trivial); skip]
Lean4Lean/Experimental/ShapeLogRel.lean:5334:     obtain ⟨⟨⟩, _⟩ := a <;> obtain ⟨⟨⟩, _⟩ := a' <;> simp [LR0.DefEq]; cases le
Lean4Lean/Experimental/ShapeLogRel.lean:5341:     simp only [LR0.DefEq]; split <;> [trivial; skip]
Lean4Lean/Experimental/ShapeLogRel.lean:5350:     dsimp [LR0.DefEq]; split <;> [exact .rfl; skip]
Lean4Lean/Experimental/ShapeLogRel.lean:5368:   (∀ {{a b' p}}, p.HasType b → Γ ⊢ a ≡ b' : B → IH.DefEq a b' B p b →
Lean4Lean/Experimental/ShapeLogRel.lean:5371:   ∀ {{a p}}, p.HasType b → Γ ⊢ a : B → IH.DefEq a a B p b →
Lean4Lean/Experimental/ShapeLogRel.lean:5386:   (∀ {{a b p}}, WShape.HasType p a₁ → Γ ⊢ a ≡ b : A₁ → IH.DefEq a b A₁ p a₁ →
Lean4Lean/Experimental/ShapeLogRel.lean:5387:     IH.DefEq (M.app a) (M.app b) (A₂.inst a) (m.app p) (a₂.app p) ∧
Lean4Lean/Experimental/ShapeLogRel.lean:5388:     IH.DefEq (N.app a) (N.app b) (A₂.inst a) (m.app p) (a₂.app p)) ∧
Lean4Lean/Experimental/ShapeLogRel.lean:5389:   (∀ {{a p}}, WShape.HasType p a₁ → Γ ⊢ a : A₁ → IH.DefEq a a A₁ p a₁ →
Lean4Lean/Experimental/ShapeLogRel.lean:5390:     IH.DefEq (M.app a) (N.app a) (A₂.inst a) (m.app p) (a₂.app p))
Lean4Lean/Experimental/ShapeLogRel.lean:5589: to transport the inner `IH.DefEq` terms. HasType is preserved trivially (doesn't mention M, N). -/
Lean4Lean/Experimental/ShapeLogRel.lean:5602: def LRS.DefEq (IH : LogRel Γ n) (M N A : SExpr) (m a : WShape (n+1)) : Prop :=
Lean4Lean/Experimental/ShapeLogRel.lean:5619: @[simp] theorem LRS.DefEq.bot_a : LRS.DefEq IH M N A m .bot = True := rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5620: @[simp] theorem LRS.DefEq.sort_a : LRS.DefEq IH M N A m (.sort r) = LRS.TyDefEq IH M N m := rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5621: @[simp] theorem LRS.DefEq.bot_m : LRS.DefEq IH M N A .bot (.forallE a₁ a₂) = True := rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5622: @[simp] theorem LRS.DefEq.lam_forallE (IH : LogRel Γ n) :
Lean4Lean/Experimental/ShapeLogRel.lean:5623:     LRS.DefEq IH M N A (.lam f hf) (.forallE a₁ a₂) ↔
Lean4Lean/Experimental/ShapeLogRel.lean:5630: @[simp] theorem LRS.DefEq.sort_forallE :
Lean4Lean/Experimental/ShapeLogRel.lean:5631:     LRS.DefEq IH M N A (.sort r) (.forallE a₁ a₂) ↔ False := .rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5632: @[simp] theorem LRS.DefEq.forallE_forallE :
Lean4Lean/Experimental/ShapeLogRel.lean:5633:     LRS.DefEq IH M N A (.forallE b g) (.forallE a₁ a₂) ↔ False := .rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5634: @[simp] theorem LRS.DefEq.ctor_forallE :
Lean4Lean/Experimental/ShapeLogRel.lean:5635:     LRS.DefEq IH M N A (.ctor c l h) (.forallE a₁ a₂) ↔ False := .rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5636: @[simp] theorem LRS.DefEq.indTy_forallE :
Lean4Lean/Experimental/ShapeLogRel.lean:5637:     LRS.DefEq IH M N A .indTy (.forallE a₁ a₂) ↔ False := .rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5638: @[simp] theorem LRS.DefEq.lam_a : LRS.DefEq IH M N A m (.lam f hf) ↔ False := .rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5639: @[simp] theorem LRS.DefEq.ctor_a {c l h} :
Lean4Lean/Experimental/ShapeLogRel.lean:5640:     LRS.DefEq (n := n) IH M N A m (.ctor c l h) ↔ False := .rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5645: @[simp] theorem LRS.DefEq.indTy_a : LRS.DefEq (n := n) IH M N A m .indTy ↔ True := .rfl
Lean4Lean/Experimental/ShapeLogRel.lean:5648:   DefEq := LRS.DefEq IH
Lean4Lean/Experimental/ShapeLogRel.lean:5655:     dsimp [LRS.DefEq]; split <;> try trivial
Lean4Lean/Experimental/ShapeLogRel.lean:5662:     dsimp [LRS.DefEq]; split <;> try trivial
Lean4Lean/Experimental/ShapeLogRel.lean:5669:     dsimp [LRS.DefEq]; split <;> try trivial
Lean4Lean/Experimental/ShapeLogRel.lean:5676:     dsimp [LRS.DefEq]; split <;> try intros; trivial
Lean4Lean/Experimental/ShapeLogRel.lean:5681:     dsimp [LRS.TyDefEq]; dsimp [LRS.DefEq]; split <;> (try · simp); dsimp
Lean4Lean/Experimental/ShapeLogRel.lean:5706:       | bot => simp [LRS.DefEq.bot_m]
Lean4Lean/Experimental/ShapeLogRel.lean:5708:         simp only [LRS.DefEq.lam_forallE] at h ⊢
Lean4Lean/Experimental/ShapeLogRel.lean:5723:       | sort => simp [LRS.DefEq.sort_forallE] at h
Lean4Lean/Experimental/ShapeLogRel.lean:5724:       | forallE => simp [LRS.DefEq.forallE_forallE] at h
Lean4Lean/Experimental/ShapeLogRel.lean:5725:       | ctor => simp [LRS.DefEq.ctor_forallE] at h
Lean4Lean/Experimental/ShapeLogRel.lean:5726:       | indTy => simp [LRS.DefEq.indTy_forallE] at h
Lean4Lean/Experimental/ShapeLogRel.lean:5729:     | indTy => simp [LRS.DefEq.indTy_a] at h ⊢
Lean4Lean/Experimental/ShapeLogRel.lean:5749:     | bot => simp only [LRS.DefEq.bot_a]
Lean4Lean/Experimental/ShapeLogRel.lean:5752:       · have := ha.bot_r; subst this; simp only [LRS.DefEq.sort_a, LRS.TyDefEq.bot]
Lean4Lean/Experimental/ShapeLogRel.lean:5756:       · have := ha.bot_r; subst this; simp only [LRS.DefEq.bot_m]
Lean4Lean/Experimental/ShapeLogRel.lean:5758:         | bot => simp only [LRS.DefEq.bot_m]
Lean4Lean/Experimental/ShapeLogRel.lean:5760:           simp only [LRS.DefEq.lam_forallE] at h ⊢
Lean4Lean/Experimental/ShapeLogRel.lean:5778:         | sort => exact (LRS.DefEq.sort_forallE.1 h).elim
Lean4Lean/Experimental/ShapeLogRel.lean:5779:         | forallE => exact (LRS.DefEq.forallE_forallE.1 h).elim
Lean4Lean/Experimental/ShapeLogRel.lean:5780:         | ctor => exact (LRS.DefEq.ctor_forallE.1 h).elim
Lean4Lean/Experimental/ShapeLogRel.lean:5781:         | indTy => exact (LRS.DefEq.indTy_forallE.1 h).elim
Lean4Lean/Experimental/ShapeLogRel.lean:5784:     | indTy => simp [LRS.DefEq.indTy_a]
Lean4Lean/Experimental/ShapeLogRel.lean:5787:     | bot => simp only [LRS.DefEq.bot_a]
Lean4Lean/Experimental/ShapeLogRel.lean:5789:       simp only [LRS.DefEq.sort_a] at h ⊢
Lean4Lean/Experimental/ShapeLogRel.lean:5809:       | bot => simp only [LRS.DefEq.bot_m]
Lean4Lean/Experimental/ShapeLogRel.lean:5820:             simp only [LRS.DefEq.lam_forallE] at h ⊢
Lean4Lean/Experimental/ShapeLogRel.lean:5829:     | indTy => simp only [LRS.DefEq.indTy_a]
Lean4Lean/Experimental/ShapeLogRel.lean:5899:       ((LR Γ).DefEq M N A (m.lift n') (a.lift _) ↔ (LR Γ).DefEq M N A m a)) :
Lean4Lean/Experimental/ShapeLogRel.lean:5942:       ((LR Γ).DefEq M N A (m.lift n') (a.lift _) ↔ (LR Γ).DefEq M N A m a))
Lean4Lean/Experimental/ShapeLogRel.lean:5986:       have go {M N} (r : (LR Γ).DefEq M N (A₂.inst a') (g.app qg') (a₂.app qg')) :
Lean4Lean/Experimental/ShapeLogRel.lean:5987:           (LR Γ).DefEq M N (A₂.inst a') (yg.lift n') (ya.lift n') :=
Lean4Lean/Experimental/ShapeLogRel.lean:5998:       (LRS.DefEq (n := n) (LR Γ) M N A (m.lift _) (a.lift _) ↔ (LR Γ).DefEq M N A m a)) := by
Lean4Lean/Experimental/ShapeLogRel.lean:6026:       simp only [LRS.DefEq.lam_forallE]
Lean4Lean/Experimental/ShapeLogRel.lean:6036: theorem LR.DefEq.lift {m a : WShape n} (le : n ≤ n') (hma : WShape.HasType m a) :
Lean4Lean/Experimental/ShapeLogRel.lean:6037:     (LR Γ).DefEq M N A (m.lift n') (a.lift _) ↔ (LR Γ).DefEq M N A m a := by
Lean4Lean/Experimental/ShapeLogRel.lean:6054:     ∀ {{m : WShape n}}, LE_Interp ρ m.T (.bvar i) → m.HasType a → (LR Γ₀).DefEq x x' A m a
====================================================================================================
PATTERN: theorem .*DefEq
Lean4Lean/Experimental/SExpr.lean:678: theorem IsDefEq.strong : Γ ⊢ e1 ≡ e2 : A → IsDefEqStrong Γ e1 e2 A := sorry
Lean4Lean/Experimental/SExpr.lean:679: theorem IsDefEqStrong.defeq : IsDefEqStrong Γ e1 e2 A → Γ ⊢ e1 ≡ e2 : A := sorry
Lean4Lean/Experimental/SExpr.lean:689: theorem IsDefEq.hasType (H : Γ ⊢ e1 ≡ e2 : A) :
Lean4Lean/Experimental/SExpr.lean:785: theorem IsDefEq.subst (W : Ctx.SubstEq Γ₀ σ σ' Γ) :
Lean4Lean/Experimental/SExpr.lean:799: theorem IsDefEq.weak' (W : Ctx.Lift' ρ Γ Γ') (H : Γ ⊢ e1 ≡ e2 : A) :
Lean4Lean/Experimental/SExpr.lean:822: theorem IsDefEq.defeqDF_l' (h1 : Γ ⊢ A ≡ A' : .sort u)
Lean4Lean/Experimental/SExpr.lean:826: theorem IsDefEq.defeqDF_l (h1 : Γ ⊢ A ≡ A' : .sort u)
Lean4Lean/Experimental/SExpr.lean:881: theorem IsDefEqLift.weak' : Ctx.Lift' ρ Γ Δ → Γ ⊢ e1 ≡ e2 :↑ A →
Lean4Lean/Experimental/SExpr.lean:884: theorem IsDefEqLift.subst : Ctx.Subst HasType Δ σ Γ → Γ ⊢ e1 ≡ e2 :↑ A →
Lean4Lean/Experimental/SExpr.lean:902: nonrec theorem IsDefEqLift.weak'_inv : Ctx.Lift' ρ Γ Δ →
Lean4Lean/Experimental/SExpr.lean:912: nonrec theorem IsDefEqLift.symm : Γ ⊢ e1 ≡ e2 :↑ A → Γ ⊢ e2 ≡ e1 :↑ A := .symm .symm
Lean4Lean/Experimental/SExpr.lean:914: theorem WithLift.left (H : WithLift DefEq Γ e1 e2 A) : WithLift DefEq Γ e1 e1 A :=
Lean4Lean/Experimental/SExpr.lean:917: theorem WithLift.right (H : WithLift DefEq Γ e1 e2 A) : WithLift DefEq Γ e2 e2 A :=
Lean4Lean/Experimental/SExpr.lean:920: theorem IsDefEqLift.left (H : Γ ⊢ e1 ≡ e2 :↑ A) : Γ ⊢ e1 :↑ A where
Lean4Lean/Experimental/SExpr.lean:925: theorem WithLift.defeq (H : WithLift DefEq Γ e1 e2 A) : DefEq Γ e1 e2 A :=
Lean4Lean/Experimental/SExpr.lean:928: nonrec theorem IsDefEqLift.defeq (H : Γ ⊢ e1 ≡ e2 :↑ A) : Γ ⊢ e1 ≡ e2 : A := H.defeq
Lean4Lean/Experimental/SExpr.lean:935: theorem IsDefEq.defeqDFC' (h1 : IsDefEqCtx Γ₀ Γ₁ Γ₂)
Lean4Lean/Experimental/SExpr.lean:942: theorem IsDefEq.defeqDFC (h1 : IsDefEqCtx Γ₀ Γ₁ Γ₂)
Lean4Lean/Experimental/SExpr.lean:1216: theorem NormalEq.defeqDFC (W : IsDefEqCtx Γ₀ Γ₁ Γ₂)
Lean4Lean/Experimental/SExpr.lean:1282: theorem CRDefEq.normalEq (H : Γ ⊢ e₁ ≡ₚ e₂ : A) : Γ ⊢ e₁ ≫≪ e₂ : A :=
Lean4Lean/Experimental/SExpr.lean:1285: theorem CRDefEq.refl (H : Γ ⊢ e : A) : Γ ⊢ e ≫≪ e : A :=
Lean4Lean/Experimental/SExpr.lean:1288: theorem CRDefEq.defeq : Γ ⊢ e₁ ≫≪ e₂ : A → Γ ⊢ e₁ ≡ e₂ : A := (·.1)
Lean4Lean/Experimental/SExpr.lean:1290: theorem CRDefEq.symm : Γ ⊢ e₁ ≫≪ e₂ : A → Γ ⊢ e₂ ≫≪ e₁ : A
Lean4Lean/Experimental/SExpr.lean:1293: theorem CRDefEq.trans : Γ ⊢ e₁ ≫≪ e₂ : A → Γ ⊢ e₂ ≫≪ e₃ : A → Γ ⊢ e₁ ≫≪ e₃ : A
Lean4Lean/Experimental/SExpr.lean:1296: theorem CRDefEq.defeqDF : Γ ⊢ e₁ ≫≪ e₂ : A → Γ ⊢ A ≡ B : .sort u → Γ ⊢ e₁ ≫≪ e₂ : B
Lean4Lean/Experimental/SExpr.lean:1299: theorem CRDefEq.weak' (W : Ctx.Lift' ρ Γ Γ') :
Lean4Lean/Experimental/SExpr.lean:1303: theorem WHRedS.crDefEq (H1 : Γ ⊢ e1 : A) (H2 : Γ ⊢ e1 ⤳* e2) : Γ ⊢ e1 ≫≪ e2 : A :=
Lean4Lean/Experimental/SExpr.lean:1306: nonrec theorem CRDefEqLift.symm : Γ ⊢ e1 ≫≪ e2 :↑ A → Γ ⊢ e2 ≫≪ e1 :↑ A := .symm .symm
Lean4Lean/Experimental/SExpr.lean:1308: theorem CRDefEqLift.defeq (H : Γ ⊢ e1 ≫≪ e2 :↑ A) : Γ ⊢ e1 ≡ e2 :↑ A := H.imp (·.1)
Lean4Lean/Experimental/SExpr.lean:1310: theorem CRDefEqLift.left (H : Γ ⊢ e1 ≫≪ e2 :↑ A) : Γ ⊢ e1 :↑ A := H.defeq.left
Lean4Lean/Experimental/SExpr.lean:1312: nonrec theorem CRDefEqLift.refl (H : Γ ⊢ e :↑ A) : Γ ⊢ e ≫≪ e :↑ A :=
Lean4Lean/Experimental/Thierry2.lean:653: theorem DefEqF.U_U : @DefEqF n A A' V .U .U ↔ V ⤳* .U : .U ∧ A ⤳* .U : .U ∧ A' ⤳* .U : .U := by
Lean4Lean/Experimental/Thierry2.lean:656: theorem DefEqPiF.left : DefEqPiF DefEqF B F F' b f → DefEqPiF DefEqF B F F b f := by
Lean4Lean/Experimental/Thierry2.lean:661: theorem DefEqLamF.left : DefEqLamF DefEqF M M' B F m b f → DefEqLamF DefEqF M M B F m b f := by
Lean4Lean/Experimental/Thierry2.lean:666: theorem DefEqF.left {a : Shape n} : DefEqF M M' A u a → DefEqF M M A u a := by
Lean4Lean/Experimental/Thierry2.lean:684: theorem DefEqF.bot : DefEqF (n := n) A A .U a .U → DefEqF M N A .bot a := by
Lean4Lean/Experimental/Thierry2.lean:690: theorem DefEqLamF.bot :
Lean4Lean/Experimental/Thierry2.lean:702: theorem DefEqF.mono {a a' : Shape n} : DefEqF A A .U a .U → a :ᶠ .U → a' ≤ a →
Lean4Lean/Experimental/Thierry2.lean:742: theorem DefEqLamF.mono :
Lean4Lean/Experimental/Thierry2.lean:765: theorem DefEqPiF.mono : DefEqF (n := n) B B .U b .U →
Lean4Lean/Experimental/Thierry2.lean:782: theorem DefEqF.mono_r : DefEqF (n := n) A A .U a .U → a :ᶠ .U → a' ≤ a →
Lean4Lean/Experimental/Thierry2.lean:814: theorem DefEqLamF.mono_r : DefEqF (n := n) B B .U a .U → DefEqPiF DefEqF B F F a f →
Lean4Lean/Experimental/StratifiedUntyped.lean:55: theorem IsDefEq.inductionU1
Lean4Lean/Experimental/StratifiedUntyped.lean:120: theorem IsDefEqU1.induction
Lean4Lean/Experimental/StratifiedUntyped.lean:149: protected theorem IsDefEqU1.hasType_ind
Lean4Lean/Experimental/StratifiedUntyped.lean:178: theorem IsDefEqU1.unique_typing1
Lean4Lean/Experimental/StratifiedUntyped.lean:245: theorem IsDefEq.unique_typing'
Lean4Lean/Experimental/StratifiedUntyped.lean:275: theorem IsDefEq.weakN_inv (W : Ctx.LiftN n k Γ Γ')
Lean4Lean/Experimental/Stratified.lean:75: theorem IsDefEq.induction1
Lean4Lean/Experimental/Stratified.lean:135: theorem IsDefEq1.induction
Lean4Lean/Experimental/Stratified.lean:164: protected theorem IsDefEq1.hasType_ind
Lean4Lean/Experimental/Stratified.lean:193: theorem IsDefEq1.unique_typing1
Lean4Lean/Experimental/Stratified.lean:260: theorem IsDefEq.unique_typing'
Lean4Lean/Experimental/Stratified.lean:290: theorem IsDefEq.weakN_inv (W : Ctx.LiftN n k Γ Γ')
Lean4Lean/Experimental/Stronger.lean:162: @[simp] theorem addDefEq_out {env : VEnv'} :
Lean4Lean/Experimental/Stronger.lean:166: theorem IsDefEqStrong.hasType {env : VEnv'}
Lean4Lean/Experimental/Stronger.lean:193: theorem IsDefEqStrong.out
Lean4Lean/Experimental/Stronger.lean:219: theorem VDefEq.WF.out {ci : VDefEq} (H : ci.WF env) : ci.toVDefEq.WF env.out :=
Lean4Lean/Experimental/Stronger.lean:241: theorem IsDefEqStrong.weakN (W : Ctx.LiftN n k Γ Γ') (H : env.IsDefEqStrong U Γ e1 e2 A u) :
Lean4Lean/Experimental/Stronger.lean:282: theorem IsDefEqStrong.mono
Lean4Lean/Experimental/Stronger.lean:303: theorem IsDefEqStrong.weak0 (H : env.IsDefEqStrong U [] e1 e2 A u) :
Lean4Lean/Experimental/Stronger.lean:316: theorem IsDefEqStrong.instL (H : env.IsDefEqStrong U Γ e1 e2 A u) :
Lean4Lean/Experimental/Stronger.lean:387: theorem IsDefEqStrong.instN (W : Ctx.InstN' Γ₀ e₀ A₀ u₀ k Γ₁ Γ)
Lean4Lean/Experimental/Stronger.lean:456: theorem IsDefEqStrong.defeqDF_l (henv : Ordered env) (hΓ : CtxStrong env U Γ)
Lean4Lean/Experimental/Stronger.lean:475: theorem IsDefEqStrong.forallE_inv' (hΓ : CtxStrong env U Γ)
Lean4Lean/Experimental/Stronger.lean:525: theorem IsDefEqStrong.isType' (hΓ : CtxStrong env U Γ) (H : env.IsDefEqStrong U Γ e1 e2 A u) :
Lean4Lean/Experimental/Stronger.lean:545: theorem IsDefEqStrong.sort_invL {env : VEnv'}
Lean4Lean/Experimental/Stronger.lean:572: theorem IsDefEqStrong.uniqL'
Lean4Lean/Experimental/UniqueTyping.lean:138: theorem IsDefEq.toHasTypeS {Γ : List SExpr} {e₁ e₂ A : SExpr}
Lean4Lean/Experimental/UniqueTyping.lean:174: theorem IsDefEq.uniq_sort {Γ : List SExpr} {e₁ e₂ e₃ : SExpr} {u v : SLevel}
Lean4Lean/Experimental/UniqueTyping.lean:223: theorem IsDefEq'.toIsDefEq {Γ : List SExpr} {e₁ e₂ A : SExpr}
Lean4Lean/Experimental/UniqueTyping.lean:242: theorem IsDefEq.toIsDefEq' {Γ : List SExpr} {e₁ e₂ A : SExpr}
Lean4Lean/Experimental/UniqueTyping.lean:261: theorem IsDefEq.iff_isDefEq' {Γ : List SExpr} {e₁ e₂ A : SExpr} :
Lean4Lean/Experimental/NormalEq.lean:103: theorem Typing.symm_ctx (H : IsDefEqCtx TY.IsDefEqU Γ₀ Γ₁ Γ₂) : IsDefEqCtx TY.IsDefEqU Γ₀ Γ₂ Γ₁ := by
Lean4Lean/Experimental/NormalEq.lean:108: theorem Typing.IsDefEqU.weakN (W : Ctx.LiftN n k Γ Γ') :
Lean4Lean/Experimental/NormalEq.lean:110: theorem Typing.IsDefEq.weakN (W : Ctx.LiftN n k Γ Γ') :
Lean4Lean/Experimental/NormalEq.lean:113: theorem Typing.IsDefEqU.instN : Ctx.InstN Γ₀ e₀ A₀ k Γ₁ Γ → TY.IsDefEqU Γ₁ e1 e2 →
Lean4Lean/Experimental/NormalEq.lean:115: theorem Typing.IsDefEq.instN : Ctx.InstN Γ₀ e₀ A₀ k Γ₁ Γ → TY.IsDefEq Γ₁ e₁ e₂ A →
Lean4Lean/Experimental/NormalEq.lean:133: theorem Typing.IsDefEqU.apply_pat
Lean4Lean/Experimental/NormalEq.lean:201: theorem NormalEq.defeq (H : NormalEq TY Γ e1 e2) : TY.IsDefEqU Γ e1 e2 := by
Lean4Lean/Experimental/NormalEq.lean:315: theorem NormalEq.defeqDFC (W : IsDefEqCtx TY.IsDefEqU Γ₀ Γ₁ Γ₂)
Lean4Lean/Experimental/NormalEq.lean:340: theorem NormalEq.defeq_l (W : TY.IsDefEqU Γ A A') (H : NormalEq TY (A::Γ) e1 e2) :
Lean4Lean/Experimental/NormalEq.lean:343: theorem NormalEq.weakN_inv_DFC (W : Ctx.LiftN n k Γ Γ₂) (W₂ : IsDefEqCtx TY.IsDefEqU Γ₀ Γ₁ Γ₂)
Lean4Lean/Experimental/ParallelReduction.lean:97: theorem ParRed.defeq (H : ParRed TY Γ e e') (he : TY.HasType Γ e A) : TY.IsDefEqU Γ e e' := by
Lean4Lean/Experimental/ParallelReduction.lean:123: theorem ParRed.defeqDFC (W : IsDefEqCtx TY.IsDefEqU Γ₀ Γ₁ Γ₂)
Lean4Lean/Experimental/ParallelReduction.lean:158: -- theorem IsDefEqU.applyL {p : Pattern} (r : p.RHS) {m1 m1' m2}
Lean4Lean/Experimental/ParallelReduction.lean:446: theorem ParRedS.defeq (H : ParRedS TY Γ e e') (h : TY.HasType Γ e A) : TY.IsDefEqU Γ e e' := by
Lean4Lean/Experimental/ParallelReduction.lean:451: theorem ParRedS.defeqDFC (W : IsDefEqCtx TY.IsDefEqU Γ₀ Γ₁ Γ₂)
Lean4Lean/Experimental/ParallelReduction.lean:819: theorem Typing.CRDefEq.normalEq (H : NormalEq TY Γ e₁ e₂) : TY.CRDefEq Γ e₁ e₂ :=
Lean4Lean/Experimental/ParallelReduction.lean:822: theorem Typing.CRDefEq.refl (H : TY.HasType Γ e A) : TY.CRDefEq Γ e e :=
Lean4Lean/Experimental/ParallelReduction.lean:825: theorem Typing.CRDefEq.defeq : TY.CRDefEq Γ e₁ e₂ → TY.IsDefEqU Γ e₁ e₂
Lean4Lean/Experimental/ParallelReduction.lean:829: theorem Typing.CRDefEq.symm : TY.CRDefEq Γ e₁ e₂ → TY.CRDefEq Γ e₂ e₁
Lean4Lean/Experimental/ParallelReduction.lean:832: theorem Typing.CRDefEq.trans : TY.CRDefEq Γ e₁ e₂ → TY.CRDefEq Γ e₂ e₃ → TY.CRDefEq Γ e₁ e₃
Lean4Lean/Experimental/ParallelReduction.lean:839: theorem VEnv.IsDefEq.toTyping (H : TY.env.IsDefEq TY.univs Γ e₁ e₂ A) :
Lean4Lean/Experimental/ParallelReduction.lean:858: theorem VEnv.IsDefEqU.church_rosser
Lean4Lean/Experimental/LogRel.lean:26: theorem Classifier.DefEq.symm {cl : Classifier Γ A u} : cl.DefEq a b → cl.DefEq b a
Lean4Lean/Experimental/LogRel.lean:28: theorem Classifier.DefEq.left {cl : Classifier Γ A u} : cl.DefEq a b → cl.HasTy a
Lean4Lean/Experimental/LogRel.lean:31: theorem Classifier.defEq_self {cl : Classifier Γ A u} : cl.DefEq a a ↔ cl.HasTy a :=
Lean4Lean/Experimental/LogRel.lean:34: theorem Classifier.DefEq.imp {Γ A u Γ' A' u'} {cl : Classifier Γ A u} {cl' : Classifier Γ' A' u'}
Lean4Lean/Experimental/LogRel.lean:110: theorem LRDefEq.defeq {J : Γ ⊩[u] A} (H : J ⊩ a ≡ b) : Γ ⊢ a ≡ b :↑ A := H.1.defeq
Lean4Lean/Experimental/LogRel.lean:111: nonrec theorem LRDefEq.left {Γ A u a b} {J : Γ ⊩[u] A} (H : J ⊩ a ≡ b) : J ⊩ a :=
Lean4Lean/Experimental/LogRel.lean:117: theorem LRDefEq.cast {J : Γ ⊩[u] A} (eq : A = A') : J.cast eq ⊩ a ≡ b ↔ J ⊩ a ≡ b := by
Lean4Lean/Experimental/LogRel.lean:186: theorem LRDefEq.irrel {J J' : Γ ⊩[u] A} (H : J ⊩ a ≡ b) : J' ⊩ a ≡ b := by
Lean4Lean/Experimental/LogRel.lean:232: theorem LRDefEq.weak' (W : Ctx.Lift' ρ Γ Δ) {J : Γ ⊩[u

## Next Move

Use trace tails to identify the exact shape of LR.DefEq and which hM.const fields contain the needed LE_Interp/HasType witnesses.