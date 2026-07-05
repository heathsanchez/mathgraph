# SorryDB v4.5.14 — Stratified constDF Patch002

## Result

- status: PATCH002_ACCEPTED
- accepted_variant: v01_try_no_explicit_u

## Core Obstruction

The Stratified target differs from StratifiedUntyped by a universe index:

    wanted: defEq Γ (instL ls₂ ci.type) (instL ls₁ ci.type) (sort (u.inst ls₁))
    IH:     IsDefEq1 ... (instL ls₁ ci.type) (instL ls₂ ci.type) (sort u)

## Variant Summary

- v01_try_no_explicit_u: module_rc=0, seconds=1.19, strat_sorry=False, full_rc=0

## Target Window

0001: import Lean4Lean.Theory.Typing.Lemmas
0002: import Lean4Lean.Theory.Typing.Strong
0003: 
0004: namespace Lean4Lean
0005: namespace VEnv
0006: 
0007: open VExpr
0008: 
0009: def DefInv (env : VEnv) (U : Nat) (Γ : List VExpr) : VExpr → VExpr → Prop
0010:   | .forallE A B, .forallE A' B' =>
0011:     ∃ u v, env.IsDefEq U Γ A A' (.sort u) ∧ env.IsDefEq U (A::Γ) B B' (.sort v)
0012:   | .forallE .., .sort .. | .sort .., .forallE .. => False
0013:   | .sort u, .sort v => u ≈ v
0014:   | _, _ => True
0015: 
0016: variable! (henv : Ordered env) in
0017: nonrec theorem DefInv.symm (h : DefInv env U Γ e1 e2) : DefInv env U Γ e2 e1 := by
0018:   cases e1 <;> cases e2 <;> try trivial
0019:   · exact h.symm
0020:   · let ⟨u, v, h1, h2⟩ := h; exact ⟨u, v, h1.symm, h1.defeqDF_l henv h2.symm⟩
0021: 
0022: section
0023: set_option hygiene false
0024: local notation:65 Γ " ⊢ " e " : " A:30 => HasType1 Γ e A
0025: local notation:65 Γ " ⊢ " e1 " ≡ " e2 " : " A:30 => IsDefEq1 Γ e1 e2 A
0026: 
0027: variable (env : VEnv) (uvars : Nat)
0028: 
0029: variable (IsDefEq1 : List VExpr → VExpr → VExpr → VExpr → Prop) in
0030: inductive HasType1 : List VExpr → VExpr → VExpr → Prop where
0031:   | bvar : Lookup Γ i A → Γ ⊢ .bvar i : A
0032:   | const :
0033:     env.constants c = some ci →
0034:     (∀ l ∈ ls, l.WF uvars) →
0035:     ls.length = ci.uvars →
0036:     Γ ⊢ .const c ls : ci.type.instL ls
0037:   | sort : l.WF uvars → Γ ⊢ .sort l : .sort (.succ l)
0038:   | app : Γ ⊢ f : .forallE A B → Γ ⊢ a : A → Γ ⊢ .app f a : B.inst a
0039:   | lam : Γ ⊢ A : .sort u → A::Γ ⊢ body : B → Γ ⊢ .lam A body : .forallE A B
0040:   | forallE : Γ ⊢ A : .sort u → A::Γ ⊢ body : .sort v → Γ ⊢ .forallE A body : .sort (.imax u v)
0041:   | defeq : Γ ⊢ A ≡ B : .sort u → Γ ⊢ e : A → Γ ⊢ e : B
0042: 
0043: variable
0044:   (HasType1 : List VExpr → VExpr → VExpr → Prop)
0045:   (defEq : List VExpr → VExpr → VExpr → VExpr → Prop) in
0046: inductive IsDefEq1 : List VExpr → VExpr → VExpr → VExpr → Prop where
0047:   | refl : Γ ⊢ e : A → Γ ⊢ e ≡ e : A
0048:   | symm : Γ ⊢ e ≡ e' : A → Γ ⊢ e' ≡ e : A
0049:   | trans : Γ ⊢ e₁ ≡ e₂ : A → Γ ⊢ e₂ ≡ e₃ : A → Γ ⊢ e₁ ≡ e₃ : A
0050:   | constDF :
0051:     env.constants c = some ci →
0052:     (∀ l ∈ ls, l.WF uvars) →
0053:     (∀ l ∈ ls', l.WF uvars) →
0054:     ls.length = ci.uvars →
0055:     List.Forall₂ (· ≈ ·) ls ls' →
0056:     Γ ⊢ .const c ls ≡ .const c ls' : ci.type.instL ls
0057:   | sortDF : l.WF uvars → l'.WF uvars → l ≈ l' → Γ ⊢ .sort l ≡ .sort l' : .sort l.succ
0058:   | appDF :
0059:     Γ ⊢ f ≡ f' : .forallE A B → Γ ⊢ a ≡ a' : A → Γ ⊢ .app f a ≡ .app f' a' : B.inst a
0060:   | lamDF : Γ ⊢ A ≡ A' : .sort u → A::Γ ⊢ b ≡ b' : B → Γ ⊢ .lam A b ≡ .lam A' b' : .forallE A B
0061:   | forallEDF :
0062:     Γ ⊢ A ≡ A' : .sort u → A::Γ ⊢ B ≡ B' : .sort v →
0063:     Γ ⊢ .forallE A B ≡ .forallE A' B' : .sort (.imax u v)
0064:   | defeqDF : defEq Γ A B (.sort u) → Γ ⊢ e₁ ≡ e₂ : A → Γ ⊢ e₁ ≡ e₂ : B
0065:   | beta : A::Γ ⊢ e : B → Γ ⊢ e' : A → Γ ⊢ .app (.lam A e) e' ≡ e.inst e' : B.inst e'
0066:   | eta : Γ ⊢ e : .forallE A B → Γ ⊢ .lam A (.app e.lift (.bvar 0)) ≡ e : .forallE A B
0067:   | proofIrrel : Γ ⊢ p : .sort .zero → Γ ⊢ h : p → Γ ⊢ h' : p → Γ ⊢ h ≡ h' : p
0068:   | extra :
0069:     env.defeqs df → (∀ l ∈ ls, l.WF uvars) → ls.length = df.uvars →
0070:     Γ ⊢ df.lhs.instL ls ≡ df.rhs.instL ls : df.type.instL ls
0071: 
0072: end
0073: 
0074: variable! (henv : Ordered env) (hΓ : OnCtx Γ (env.IsType U)) in
0075: theorem IsDefEq.induction1
0076:     (defEq : List VExpr → VExpr → VExpr → VExpr → Prop)
0077:     (hasType : List VExpr → VExpr → VExpr → Prop)
0078:     (hty : ∀ {Γ e A}, HasType1 env U defEq Γ e A → hasType Γ e A)
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
0104:   | defeqDF _ _ _ ih1 ih2 =>
0105:     exact ⟨.defeq (hdf ih1.2.2) ih2.1, .defeq (hdf ih1.2.2) ih2.2.1, .defeqDF (hdf ih1.2.2) ih2.2.2⟩
0106:   | beta _ _ _ _ _ _ _ _ ihA _ ihe ihe' _ ihee =>
0107:     exact ⟨.app (.lam ihA.1 ihe.1) ihe'.1, ihee.1, .beta (hty ihe.1) (hty ihe'.1)⟩
0108:   | eta _ _ _ _ _ _ _ _ ihA _ _ ihe ihe' =>
0109:     have := HasType1.app ihe'.1 (.bvar .zero)
0110:     rw [instN_bvar0] at this
0111:     exact ⟨.lam ihA.1 this, ihe.1, .eta (hty ihe.1)⟩
0112:   | proofIrrel _ _ _ ih1 ih2 ih3 =>
0113:     exact ⟨ih2.1, ih3.1, .proofIrrel (hty ih1.1) (hty ih2.1) (hty ih3.1)⟩
0114:   | extra h1 h2 h3 _ _ _ _ _ _ _ _ _ ihl' ihr' =>
0115:     exact ⟨ihl'.1, ihr'.1, .extra h1 h2 h3⟩
0116: 
0117: variable! {env : VEnv}
0118:   {defEq : List VExpr → VExpr → VExpr → VExpr → Prop}
0119:   (IH : ∀ {Γ e1 e2 A}, defEq Γ e1 e2 A → env.IsDefEq U Γ e1 e2 A) in
0120: theorem HasType1.induction (H : env.HasType1 U defEq Γ e A) : env.HasType U Γ e A := by

## Recon

====================================================================================================
PATTERN: def DefInv
Lean4Lean/Experimental/Stratified.lean:9: def DefInv (env : VEnv) (U : Nat) (Γ : List VExpr) : VExpr → VExpr → Prop
====================================================================================================
PATTERN: DefInv
Lean4Lean/Experimental/Stratified.lean:9: def DefInv (env : VEnv) (U : Nat) (Γ : List VExpr) : VExpr → VExpr → Prop
Lean4Lean/Experimental/Stratified.lean:17: nonrec theorem DefInv.symm (h : DefInv env U Γ e1 e2) : DefInv env U Γ e2 e1 := by
====================================================================================================
PATTERN: inductive .*IsDefEq1
Lean4Lean/Experimental/Stratified.lean:46: inductive IsDefEq1 : List VExpr → VExpr → VExpr → VExpr → Prop where
====================================================================================================
PATTERN: IsDefEq1\.
Lean4Lean/Experimental/Stratified.lean:135: theorem IsDefEq1.induction
Lean4Lean/Experimental/Stratified.lean:164: protected theorem IsDefEq1.hasType_ind
Lean4Lean/Experimental/Stratified.lean:193: theorem IsDefEq1.unique_typing1
====================================================================================================
PATTERN: \|.*defeq
Lean4Lean/Experimental/SExpr.lean:536:   | .defeq a b rest => (a.applyS m1 m2, b.applyS m1 m2) :: rest.defeqsS m1 m2
Lean4Lean/Experimental/SExpr.lean:604:   | defeqDF : Γ ⊢ A ≡ B : .sort u → Γ ⊢ e1 ≡ e2 : A → Γ ⊢ e1 ≡ e2 : B
Lean4Lean/Experimental/SExpr.lean:608:   -- | extra : Pat p r → p.MatchesS e m1 m2 → (dfs : List _).map (·.2) = r.2.defeqsS m1 m2 →
Lean4Lean/Experimental/SExpr.lean:610:   | extra : env.defeqs df → ls.length = df.uvars →
Lean4Lean/Experimental/SExpr.lean:665:   | defeqDF : Γ ⊢ A ≡ B : .sort u → Γ ⊢ e1 ≡ e2 : A → Γ ⊢ e1 ≡ e2 : B
Lean4Lean/Experimental/SExpr.lean:672:   | extra : env.defeqs df → ls.length = df.uvars →
Lean4Lean/Experimental/SExpr.lean:725:   | defeq : Γ ⊢ A ≡ B : .sort u →
Lean4Lean/Experimental/SExpr.lean:791:   | cons W hA h ih => exact .cons ih hA (.defeqDF (.subst W hA) h.symm)
Lean4Lean/Experimental/SExpr.lean:811:   | defeqDF _ _ ih1 ih2 => exact .defeqDF (ih1 W) (ih2 W)
Lean4Lean/Experimental/SExpr.lean:949:   | extra : Pat p r → p.MatchesS e m1 m2 → (dfs : List _).map (·.2) = r.2.defeqsS m1 m2 →
Lean4Lean/Experimental/SExpr.lean:1055:   | extra : Pat p r → p.MatchesS e m1 m2 → (dfs : List _).map (·.2) = r.2.defeqsS m1 m2 →
Lean4Lean/Experimental/SExpr.lean:1214:   | defeqDF : Γ ⊢ A ≡ B : .sort u → Γ ⊢ e1 ≡ₚ e2 : A → Γ ⊢ e1 ≡ₚ e2 : B
Lean4Lean/Experimental/SExpr.lean:1219:   | refl h => refine .refl (h.defeqDFC W)
Lean4Lean/Experimental/SExpr.lean:1230:   | proofIrrel h1 h2 h3 => exact .proofIrrel (h1.defeqDFC W) (h2.defeqDFC W) (h3.defeqDFC W)
Lean4Lean/Experimental/SExpr.lean:1231:   | defeqDF h1 _ ih => exact .defeqDF (h1.defeqDFC W) (ih W)
Lean4Lean/Experimental/SExpr.lean:1245:   | defeqDF h1 _ ih => exact .defeqDF h1 ih
Lean4Lean/Experimental/SExpr.lean:1250:   | appDF h1 h2 ih1 ih2 => exact .defeqDF sorry (u := sorry) <| .appDF ih1 ih2
Lean4Lean/Experimental/SExpr.lean:1256:   | defeqDF h1 _ ih => exact .defeqDF h1 ih
Lean4Lean/Experimental/SExpr.lean:1262:   | appDF h1 h2 ih1 ih2 => exact .defeqDF sorry (u := sorry) <| .appDF (ih1 W) (ih2 W)
Lean4Lean/Experimental/SExpr.lean:1272:   | defeqDF h1 _ ih => exact .defeqDF (h1.weak' W) (ih W)
Lean4Lean/Experimental/SExpr.lean:1297:   | ⟨l1, _, _, l3, l4, l5⟩, H => ⟨H.defeqDF l1, _, _, l3, l4, l5.defeqDF H⟩
Lean4Lean/Experimental/StratifiedUntyped.lean:28:   | defeq : Γ ⊢ A ≡ B → Γ ⊢ e : A → Γ ⊢ e : B
Lean4Lean/Experimental/StratifiedUntyped.lean:86:   | defeqDF _ _ _ ih1 ih2 =>
Lean4Lean/Experimental/StratifiedUntyped.lean:110:   | defeq h1 _ ih =>
Lean4Lean/Experimental/StratifiedUntyped.lean:161:   | defeqDF h1 _ ih => exact .defeqDF (hdf h1) ih
Lean4Lean/Experimental/StratifiedUntyped.lean:189:   | defeqDF h1 _ ih => exact .defeqDF (hdf h1) ih
Lean4Lean/Experimental/StratifiedUntyped.lean:202:   | defeq h1 _ ih =>
Lean4Lean/Experimental/StratifiedUntyped.lean:234:   -- | defeqDF _ _ ih1 ih2 => exact .defeqDF ih1 ih2
Lean4Lean/Experimental/StratifiedUntyped.lean:263:   | defeqDF _ _ ih1 ih2 => exact .defeqDF ih1 ih2
Lean4Lean/Experimental/StratifiedUntyped.lean:293:   -- | defeqDF _ _ ih1 ih2 => exact .defeqDF (ih1 W) (ih2 W)
Lean4Lean/Experimental/Stratified.lean:41:   | defeq : Γ ⊢ A ≡ B : .sort u → Γ ⊢ e : A → Γ ⊢ e : B
Lean4Lean/Experimental/Stratified.lean:64:   | defeqDF : defEq Γ A B (.sort u) → Γ ⊢ e₁ ≡ e₂ : A → Γ ⊢ e₁ ≡ e₂ : B
Lean4Lean/Experimental/Stratified.lean:104:   | defeqDF _ _ _ ih1 ih2 =>
Lean4Lean/Experimental/Stratified.lean:128:   | defeq h1 _ ih => exact (IH h1).defeq ih
Lean4Lean/Experimental/Stratified.lean:146:   | defeqDF h1 _ ih => exact .defeqDF (hdf h1) ih
Lean4Lean/Experimental/Stratified.lean:176:   | defeqDF h1 _ ih => exact .defeqDF (hdf h1) ih
Lean4Lean/Experimental/Stratified.lean:204:   | defeqDF h1 _ ih => exact .defeqDF (hdf h1) ih
Lean4Lean/Experimental/Stratified.lean:217:   | defeq h1 _ ih =>
Lean4Lean/Experimental/Stratified.lean:249:   -- | defeqDF _ _ ih1 ih2 => exact .defeqDF ih1 ih2
Lean4Lean/Experimental/Stratified.lean:278:   | defeqDF _ _ ih1 ih2 => exact .defeqDF ih1 ih2
Lean4Lean/Experimental/Stratified.lean:308:   -- | defeqDF _ _ ih1 ih2 => exact .defeqDF (ih1 W) (ih2 W)
Lean4Lean/Experimental/Stronger.lean:98:   | defeqDF :
Lean4Lean/Experimental/Stronger.lean:100:   | defeqL :
Lean4Lean/Experimental/Stronger.lean:204:   | defeqDF _ _ _ ih1 ih2 => exact .defeqDF ih1 ih2
Lean4Lean/Experimental/Stronger.lean:205:   | defeqL _ _ _ _ ih => exact ih
Lean4Lean/Experimental/Stronger.lean:209:   | extra h1 h2 h3 => exact .extra (defeqs_out h1) h2 h3
Lean4Lean/Experimental/Stronger.lean:227:   | defeq : Ordered env → df.WF env → Ordered (env.addDefEq df)
Lean4Lean/Experimental/Stronger.lean:233:   | defeq h1 h2 ih => exact addDefEq_out ▸ .defeq ih h2.out
Lean4Lean/Experimental/Stronger.lean:257:   | defeqDF h1 _ _ ih1 ih2 => exact .defeqDF h1 (ih1 W) (ih2 W)
Lean4Lean/Experimental/Stronger.lean:258:   | defeqL h1 h2 h3 _ ih => exact .defeqL h1 h2 h3 (ih W)
Lean4Lean/Experimental/Stronger.lean:294:   | defeqDF h1 _ _ ih1 ih2 => exact .defeqDF h1 ih1 ih2
Lean4Lean/Experimental/Stronger.lean:295:   | defeqL h1 h2 h3 _ ih => exact .defeqL h1 h2 h3 ih
Lean4Lean/Experimental/Stronger.lean:338:   | defeqDF _ _ _ ih1 ih2 => exact .defeqDF (.inst hls) ih1 ih2
Lean4Lean/Experimental/Stronger.lean:339:   | defeqL _ _ h3 _ ih => exact .defeqL (.inst hls) (.inst hls) (VLevel.inst_congr_l h3) ih
Lean4Lean/Experimental/Stronger.lean:424:   | defeqDF h1 _ _ ih1 ih2 => exact .defeqDF h1 (ih1 W hΓ) (ih2 W hΓ)
Lean4Lean/Experimental/Stronger.lean:425:   | defeqL h1 h2 h3 _ ih => exact .defeqL h1 h2 h3 (ih W hΓ)
Lean4Lean/Experimental/Stronger.lean:464:       |>.symm.defeqDF hu (.bvar .zero hu (h1.hasType.2.weakN henv (.zero [(A', u)])))
Lean4Lean/Experimental/Stronger.lean:490:   | defeqDF _ _ _ _ ih | defeqL _ _ _ _ ih => exact ih hΓ eq
Lean4Lean/Experimental/Stronger.lean:536:   | defeqDF _ h2 => exact h2.hasType.2
Lean4Lean/Experimental/Stronger.lean:537:   | defeqL h1 h2 h3 _ ih =>
Lean4Lean/Experimental/Stronger.lean:539:       |>.defeqL (by exact h1) (by exact h2) (VLevel.succ_congr h3)
Lean4Lean/Experimental/Stronger.lean:562:   | defeqDF _ _ _ ih1 ih2 => exact ⟨ih2.1, ih2.2.1, fun h => VLevel.succ_congr_iff.1 <| ih1.2.1 h⟩
Lean4Lean/Experimental/Stronger.lean:563:   | defeqL _ _ h1 _ ih =>
Lean4Lean/Experimental/Stronger.lean:592:     | defeqDF _ _ _ _ ih => exact ih H1
Lean4Lean/Experimental/Stronger.lean:593:     | defeqL _ _ h _ ih => exact propext (VLevel.equiv_congr_right h) ▸ ih H1
Lean4Lean/Experimental/Stronger.lean:613:     | defeqDF _ _ _ _ ih => exact ih
Lean4Lean/Experimental/Stronger.lean:614:     | defeqL _ _ h _ ih => exact propext (VLevel.equiv_congr_right h) ▸ ih
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:121:   | symm H ih => exact .fits fun W => (ih ((LE_Interp.sound H.defeq W).1.2 hM) hA hmem).symm
Lean4Lean/Experimental/ShapeLogRelAdequacy.lean:379:   | @defeqDF Γ A' B' u' _ _ Hty He ihTy ihE =>
Lean4Lean/Experimental/UniqueTyping.lean:46:   | defeq :
Lean4Lean/Experimental/UniqueTyping.lean:66:   | defeq d _ ihe => exact d.defeqDF ihe
Lean4Lean/Experimental/UniqueTyping.lean:77:   | defeq d _ ihe =>
Lean4Lean/Experimental/UniqueTyping.lean:132:   | defeq d _ ihe =>
Lean4Lean/Experimental/UniqueTyping.lean:157:     exact .defeq (.symm <| .forallEDF h_A.defeq ih_B.1.hasType) (.base (.lam ih_A.2 ih_body'.2))
Lean4Lean/Experimental/UniqueTyping.lean:160:   | defeqDF d _ _ ih2 =>
Lean4Lean/Experimental/UniqueTyping.lean:208:   | defeqDF : Γ ⊢' A ≡ B : .sort u → Γ ⊢' e1 ≡ e2 : A → Γ ⊢' e1 ≡ e2 : B
Lean4Lean/Experimental/UniqueTyping.lean:214:   | extra : env.defeqs df → ls.length = df.uvars →
Lean4Lean/Experimental/UniqueTyping.lean:234:   | defeqDF _ _ ih1 ih2 => exact .defeqDF ih1 ih2
Lean4Lean/Experimental/UniqueTyping.lean:254:   | defeqDF _ _ ih1 ih2 => exact .defeqDF ih1 ih2
Lean4Lean/Experimental/NormalEq.lean:486:   | .proofIrrel l1 l2 l3, H2 => .proofIrrel l1 l2 (TY.defeq_l H2.defeq l3)
Lean4Lean/Experimental/NormalEq.lean:498:   | H1, .proofIrrel h1 h2 h3 => .proofIrrel h1 (TY.defeq_l H1.symm.defeq h2) h3
Lean4Lean/Experimental/ParallelReduction.lean:313:       have := TY.symm <| TY.trans (r1.defeq l1) (p1.defeq (r1.hasType l1))
Lean4Lean/Experimental/ParallelReduction.lean:323:         .forallEDF l1 (TY.symm <| TY.trans (r1.defeq l1) (p1.defeq (r1.hasType l1)))
Lean4Lean/Experimental/ParallelReduction.lean:449:   | tail h1 h2 ih => refine TY.trans ih (h2.defeq (hasType h1 h))
Lean4Lean/Experimental/ParallelReduction.lean:455:   | tail h1 h2 ih => refine .tail ih (h2.defeqDFC W (hasType h1 h))
Lean4Lean/Experimental/ParallelReduction.lean:764:         exact .inl ⟨_, h1.tail <| .lam .rfl (a1.defeqDFC (.succ .zero (TY.symm h2))
Lean4Lean/Experimental/ParallelReduction.lean:827:     TY.trans (h3.defeq h1) <| TY.trans h5.defeq (TY.symm (h4.defeq h2))
Lean4Lean/Experimental/ParallelReduction.lean:843:   | symm _ ih => exact ⟨TY.symm ih.1, TY.defeq_l ih.1 ih.2⟩
Lean4Lean/Experimental/ParallelReduction.lean:850:   | defeqDF h1 h2 ih1 ih2 => exact ⟨ih2.1, TY.defeq_r ih1.1 ih2.2⟩
Lean4Lean/Experimental/ParallelReduction.lean:854:   | eta h1 ih1 => have h := TY.eta ih1.2; exact ⟨h, TY.defeq_l (TY.symm h) ih1.2⟩
Lean4Lean/Experimental/ParallelReduction.lean:892:   | defeqDF _ _ _ ih2 => exact ih2
Lean4Lean/Experimental/ShapeLogRel.lean:5031:       have := WShape.sort_le.1 <| .of_T ((h_imax_defeq W).1 h_LE_zero).le_sort
Lean4Lean/Experimental/ShapeLogRel.lean:5114:   | defeqDF h1 h2 ih1 ih2 =>
Lean4Lean/Verify/EquivManager.lean:129:   | defeq h1 h2 =>
Lean4Lean/Verify/EquivManager.lean:235:     · refine (wf.defeq h1 hi h3).trans he |>.trans (wf.defeq hj h2 h4)
Lean4Lean/Verify/EquivManager.lean:236:     · exact (wf.defeq h1 hj h3).trans he.symm |>.trans (wf.defeq hi h2 h4)
Lean4Lean/Verify/EquivManager.lean:290:     exact (wf.defeq a1 hr₁ a2).symm.trans <| .trans (H ‹_›) (wf.defeq b1 hr₂ b2)
Lean4Lean/Verify/Typing/Lemmas.lean:690:   | .cons h1 _ (.vlam h2) => .succ h1.defeqCtx h2
Lean4Lean/Verify/Typing/Lemmas.lean:691:   | .cons h1 _ (.vlet ..) => h1.defeqCtx
Lean4Lean/Verify/Typing/Lemmas.lean:709:   | .vlet h1 h2 => .vlet (h2.defeqDF h1.symm) h2.symm
Lean4Lean/Verify/Typing/Lemmas.lean:713:   | .vlam h1 => .vlam (h1.defeqDFC henv hΓ)
Lean4Lean/Verify/Typing/Lemmas.lean:714:   | .vlet h1 h2 => .vlet (h1.defeqDFC henv hΓ) (h2.defeqDFC henv hΓ)
Lean4Lean/Verify/Typing/Lemmas.lean:890:   | proj _ l2 ih1 => let .proj r1 r2 := H2; exact l2.uniq henv hΔ.defeqCtx r2 (ih1 hΔ r1)
Lean4Lean/Verify/Typing/Lemmas.lean:903:   | bvar h1 => have ⟨_, _, h1⟩ := hΔ.find?_defeqDFC h1; exact ⟨_, .bvar h1⟩
Lean4Lean/Verify/Typing/Lemmas.lean:904:   | fvar h1 => have ⟨_, _, h1⟩ := hΔ.find?_defeqDFC h1; exact ⟨_, .fvar h1⟩
Lean4Lean/Verify/Typing/Lemmas.lean:1006:   have h1' := h1.defeqU_r henv hΔ h2.symm |>.defeqU_l henv hΔ h3.symm
Lean4Lean/Verify/Typing/Lemmas.lean:1065:       |>.1 (htt.hasType.2.defeqDFC henv hΔ.defeqCtx)
Lean4Lean/Verify/Typing/Lemmas.lean:1080:       |>.hasType.2.defeqDFC henv (.succ hΔ.defeqCtx htt)
Lean4Lean/Verify/Typing/Lemmas.lean:1092:       |>.1 ((htt.defeqDF hvv).hasType.2.defeqDFC henv hΔ.defeqCtx)
Lean4Lean/Verify/Typing/Lemmas.lean:2082:   | nil => exact h2.defeq henv hΔ (he.uniq henv (.refl henv hΔ) h1)
Lean4Lean/Verify/Typing/ConditionallyTyped.lean:71:   have h4 := h4.defeqU_r henv hΔ.toCtx AA |>.defeqU_l henv hΔ.toCtx ee
Lean4Lean/Verify/Environment/Lemmas.lean:31:   | defeq : Aligned C venv → Aligned C (venv.addDefEq df)
Lean4Lean/Verify/Environment/Lemmas.lean:38:   | defeq _ ih => exact ih
Lean4Lean/Verify/Environment/Lemmas.lean:51:   | defeq _ ih => exact ih
Lean4Lean/Verify/Environment/Lemmas.lean:74:   | defn h1 h2 _ h _ ih => exact (ih.const h2 h1.1.1 h rfl).defeq
Lean4Lean/Verify/Environment/Lemmas.lean:100:   | defeq h1 ih => let ⟨_, h1, h2⟩ := ih h; exact ⟨_, h1, h2.mono VEnv.addDefEq_le⟩
Lean4Lean/Verify/Environment/Lemmas.lean:118:   | defeq h1 ih => let ⟨h1, h2⟩ := ih h hs; exact ⟨h1, h2.mono VEnv.addDefEq_le⟩
Lean4Lean/Verify/TypeChecker/WHNF.lean:165:     exact ⟨h1.trans <| a1.trans b1, b2.defeq c.Ewf c.Δwf <| eq'.trans c.Ewf c.Δwf eq⟩
Lean4Lean/Verify/TypeChecker/Basic.lean:51:   | defeq : TrExprS env Us Δ e₁ e' → TrExpr env Us Δ e₂ e' → IsDefEqE e₁ e₂
Lean4Lean/Verify/TypeChecker/Basic.lean:64:   | defeq h1 h2 => let ⟨_, h2, h3⟩ := h2; exact .defeq h2 ⟨_, h1, h3.symm⟩
====================================================================================================
PATTERN: \|.*constDF
Lean4Lean/Experimental/StratifiedUntyped.lean:37:   | constDF : List.Forall₂ (· ≈ ·) ls ls' → Γ ⊢ .const c ls ≡ .const c ls'
Lean4Lean/Experimental/StratifiedUntyped.lean:71:   | @constDF _ _ ls₁ ls₂ _ _ h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/StratifiedUntyped.lean:72:     exact ⟨.const h1 h2 h4, .defeq sorry <| .const h1 h3 (h5.length_eq.symm.trans h4), .constDF h5⟩
Lean4Lean/Experimental/Stratified.lean:50:   | constDF :
Lean4Lean/Experimental/Stratified.lean:89:   | @constDF _ _ ls₁ ls₂ u _ h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/Stratified.lean:141:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/Stronger.lean:64:   | constDF :
Lean4Lean/Experimental/Stronger.lean:200:   | constDF h1 h2 h3 h4 h5 => exact .constDF (constants_out h1) h2 h3 h4 h5
Lean4Lean/Experimental/Stronger.lean:248:   | constDF h1 h2 h3 h4 h5 h6 h7 h8 h9 _ _ _ _ ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:289:   | constDF h1 h2 h3 h4 h5 h6 h7 _ _ _ _ ih1 ih2 ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:321:   | constDF h1 h2 h3 h4 h5 h6 _ _ _ _ _ ih1 ih2 ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:409:   | constDF h1 h2 h3 h4 h5 h6 h7 h8 h9 _ _ _ _ ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:532:   | constDF _ _ _ _ _ _ _ _ _ h => exact h
Lean4Lean/Experimental/Stronger.lean:552:   | constDF _ _ _ _ _ _ _ _ _ _ _ _ _ ih
Lean4Lean/Experimental/Stronger.lean:596:   | @constDF c ci ls _ _ _ h1 _ _ _ h2 hu _ d1 d2 d3 d4 ih1 ih2 ih3 ih4 =>
Lean4Lean/Experimental/Stronger.lean:599:     | @constDF c' _ ls' _ _ _ h1' _ _ _ h2' hu' =>
Lean4Lean/Experimental/NormalEq.lean:167:   | constDF :
Lean4Lean/Experimental/NormalEq.lean:206:   | constDF h1 h2 h3 h4 h5 => exact TY.constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:228:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/NormalEq.lean:243:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:266:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:320:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Experimental/NormalEq.lean:356:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Experimental/NormalEq.lean:452:   | .constDF l1 l2 _ l4 l5, .constDF _ _ r3 r4 r5 =>
Lean4Lean/Experimental/ParallelReduction.lean:695:   | constDF l1 l2 l3 l4 l5 =>
Lean4Lean/Experimental/ParallelReduction.lean:697:     | const => exact ⟨_, .tail .rfl .const, .constDF l1 l2 l3 l4 l5⟩
Lean4Lean/Experimental/ParallelReduction.lean:846:   | constDF h1 h2 h3 h4 h5 => exact ⟨TY.constDF h1 h2 h3 h4 h5, TY.const h1 h2 h4⟩
Lean4Lean/Experimental/ParallelReduction.lean:869:   | constDF h1 h2 h3 h4 h5 => exact .normalEq (.constDF h1 h2 h3 h4 h5)
Lean4Lean/Theory/Typing/Lemmas.lean:325:   | constDF h1 =>
Lean4Lean/Theory/Typing/Lemmas.lean:389:   | constDF h1 h2 h3 h4 h5 => exact .constDF (henv.1 h1) h2 h3 h4 h5
Lean4Lean/Theory/Typing/Lemmas.lean:468:   | constDF _ h2 h3 => exact ⟨h2, h3, .instL h2⟩
Lean4Lean/Theory/Typing/Lemmas.lean:508:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Lemmas.lean:603:   | @constDF _ _ ls₁ ls₂ _ h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Lemmas.lean:651:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Lemmas.lean:849:   | constDF h1 h2 =>
Lean4Lean/Theory/Typing/Strong.lean:23:   | constDF :
Lean4Lean/Theory/Typing/Strong.lean:149:   | constDF h1 h2 h3 h4 h5 h6 h7 _ _ ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:189:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/Strong.lean:207:   | constDF h1 h2 h3 h4 h5 h6 _ _ ih1 ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:246:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Strong.lean:303:   | constDF h1 h2 h3 h4 h5 _ _ _ ih1 ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:372:   | constDF h1 h2 h3 h4 h5 h6 h7 _ _ ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:486:   | constDF h1 h2 =>
Lean4Lean/Theory/Typing/Strong.lean:535:   | constDF h1 h2 h3 h4 h5 h6 _ _ ih1 ih2 =>
Lean4Lean/Theory/Typing/Strong.lean:620:   | @constDF _ _ ls₁ ls₂ _ h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/Strong.lean:714:   | constDF h1 h2 h3 h4 h5 h6 h7 h8 ih1 ih2 =>
Lean4Lean/Theory/Typing/Basic.lean:24:   | constDF :
Lean4Lean/Theory/Typing/ChurchRosser.lean:82:   | constDF :
Lean4Lean/Theory/Typing/ChurchRosser.lean:121:   | constDF h1 h2 h3 h4 h5 => exact ⟨_, .constDF h1 h2 h3 h4 h5⟩
Lean4Lean/Theory/Typing/ChurchRosser.lean:146:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/ChurchRosser.lean:167:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/ChurchRosser.lean:192:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/ChurchRosser.lean:251:   | constDF h1 h2 h3 h4 h5 => exact .constDF h1 h2 h3 h4 h5
Lean4Lean/Theory/Typing/ChurchRosser.lean:289:   | constDF h1 h2 h3 h4 h5 =>
Lean4Lean/Theory/Typing/ChurchRosser.lean:398:   | .constDF l1 l2 _ l4 l5, .constDF _ _ r3 r4 r5 =>
Lean4Lean/Theory/Typing/ChurchRosser.lean:1184:   | constDF l1 l2 l3 l4 l5 =>
Lean4Lean/Theory/Typing/ChurchRosser.lean:1186:     | const => exact ⟨_, .tail .rfl .const, .constDF l1 l2 l3 l4 l5⟩
Lean4Lean/Theory/Typing/ChurchRosser.lean:1352:   | constDF h1 h2 h3 h4 h5 => exact .normalEq hΓ (.constDF h1 h2 h3 h4 h5)
====================================================================================================
PATTERN: instL
Lean4Lean/Experimental/SExpr.lean:42:   --   ∃ p r m1 m2, Pat p r ∧ p.Matches (df.lhs.instL ls) m1 m2 ∧ r.2.OK (IsDefEqU env univs Γ) m1 m2 ∧
Lean4Lean/Experimental/SExpr.lean:43:   --   df.rhs.instL ls = r.1.apply m1 m2
Lean4Lean/Experimental/SExpr.lean:139: def instL : SExpr → SExpr
Lean4Lean/Experimental/SExpr.lean:143:   | .app fn arg => .app fn.instL arg.instL
Lean4Lean/Experimental/SExpr.lean:144:   | .lam ty body => .lam ty.instL body.instL
Lean4Lean/Experimental/SExpr.lean:145:   | .forallE ty body => .forallE ty.instL body.instL
Lean4Lean/Experimental/SExpr.lean:147: theorem ClosedN.instL : ∀ {e}, ClosedN e k → ClosedN (e.instL ls) k
Lean4Lean/Experimental/SExpr.lean:149:   | .app .., h | .lam .., h | .forallE .., h => ⟨h.1.instL, h.2.instL⟩
Lean4Lean/Experimental/SExpr.lean:239: @[simp] theorem instL_lift' : (lift' e ρ).instL ls = lift' (e.instL ls) ρ := by
Lean4Lean/Experimental/SExpr.lean:240:   cases e <;> simp [lift', instL, instL_lift']
Lean4Lean/Experimental/SExpr.lean:278: nonrec def Subst.instL (ls : List SLevel) (σ : Subst) : Subst := instL ls ∘ σ
Lean4Lean/Experimental/SExpr.lean:280: theorem Subst.instL_lift {σ : Subst} : (σ.instL ls).lift = σ.lift.instL ls := by
Lean4Lean/Experimental/SExpr.lean:281:   funext i; obtain _|i := i <;> simp [Subst.instL, lift, SExpr.instL]
Lean4Lean/Experimental/SExpr.lean:283: @[simp] theorem instL_subst : (subst e σ).instL ls = subst (e.instL ls) (σ.instL ls) := by
Lean4Lean/Experimental/SExpr.lean:284:   cases e <;> simp [subst, instL, instL_subst, Subst.instL_lift] <;> simp [Subst.instL]
Lean4Lean/Experimental/SExpr.lean:518:   | .fixed c _ => .instL m1 (.mk c)
Lean4Lean/Experimental/SExpr.lean:529:   | .fixed .., h1, _ => h1.mkS.instL.mono (Nat.zero_le _)
Lean4Lean/Experimental/SExpr.lean:597:     Γ ⊢ .const c ls : (SExpr.mk ci.type).instL ls
Lean4Lean/Experimental/SExpr.lean:611:     Γ ⊢ .instL ls (.mk df.lhs) ≡ .instL ls (.mk df.rhs) : .instL ls (.mk df.type)
Lean4Lean/Experimental/SExpr.lean:614:   ∃ p r m1 m2 dfs, Pat p r ∧ p.MatchesS (.instL ls (.mk df.lhs)) m1 m2 ∧
Lean4Lean/Experimental/SExpr.lean:617:     .instL ls (.mk df.rhs) = r.1.applyS m1 m2
Lean4Lean/Experimental/SExpr.lean:651:     Γ ⊢ (SExpr.mk ci.type).instL ls : .sort u →
Lean4Lean/Experimental/SExpr.lean:653:     (∀ cl, Γ ⊢ (SExpr.mk ci.type).instL ls ≡ (F cl).rhs ls : .sort (F cl).u) →
Lean4Lean/Experimental/SExpr.lean:654:     Γ ⊢ .const c ls : (SExpr.mk ci.type).instL ls
Lean4Lean/Experimental/SExpr.lean:673:     Γ ⊢ .instL ls (.mk df.lhs) : .instL ls (.mk df.type) →
Lean4Lean/Experimental/SExpr.lean:674:     Γ ⊢ .instL ls (.mk df.rhs) : .instL ls (.mk df.type) →
Lean4Lean/Experimental/SExpr.lean:675:     Γ ⊢ .instL ls (.mk df.lhs) ≡ .instL ls (.mk df.rhs) : .instL ls (.mk df.type)
Lean4Lean/Experimental/SExpr.lean:686:       Γ ⊢ (SExpr.mk ci.type).instL ls ≡
Lean4Lean/Experimental/SExpr.lean:705:     Γ ⊢ (mk ci.type).instL ls : .sort u !! n →
Lean4Lean/Experimental/SExpr.lean:706:     Γ ⊢ .const c ls :! (mk ci.type).instL ls !! n+1
Lean4Lean/Experimental/SExpr.lean:807:   | const h1 h2 => rw [(henv.closedC h1).mkS.instL.lift'_eq .zero]; exact .const h1 h2
Lean4Lean/Experimental/SExpr.lean:819:     rw [hA1.mkS.instL.lift'_eq .zero, hA2.mkS.instL.lift'_eq .zero, hA3.mkS.instL.lift'_eq .zero]
Lean4Lean/Experimental/SExpr.lean:1084:     Γ ⊢ .const c ls ▷ (SExpr.mk ci.type).instL ls
Lean4Lean/Experimental/SExpr.lean:1108:   | .const h1 h2 => by rw [(henv.closedC h1).mkS.instL.lift'_eq .zero]; exact .const h1 h2
Lean4Lean/Experimental/SExpr.lean:1121:     exact ⟨_, ((henv.closedC h1).mkS.instL.lift'_eq .zero).symm, .const h1 h2⟩
Lean4Lean/Experimental/SExpr.lean:1153:     rw [(henv.closedC h1).mkS.instL.subst_eq .zero]
Lean4Lean/Experimental/StratifiedUntyped.lean:23:     Γ ⊢ .const c ls : ci.type.instL ls
Lean4Lean/Experimental/StratifiedUntyped.lean:50:     Γ ⊢ df.lhs.instL ls ≡ df.rhs.instL ls
Lean4Lean/Experimental/StratifiedUntyped.lean:225:   --   refine .bvar h.instL
Lean4Lean/Experimental/StratifiedUntyped.lean:227:   --   simp [instL, instL_instL]
Lean4Lean/Experimental/StratifiedUntyped.lean:231:   -- | app _ _ ih1 ih2 => exact instL_instN ▸ .appDF ih1 ih2
Lean4Lean/Experimental/StratifiedUntyped.lean:236:   -- | eta _ ih => simpa [instL] using .eta ih
Lean4Lean/Experimental/StratifiedUntyped.lean:239:   --   simp [instL, instL_instL]
Lean4Lean/Experimental/StratifiedUntyped.lean:252:     refine .bvar h.instL
Lean4Lean/Experimental/StratifiedUntyped.lean:254:     simp [instL, instL_instL]
Lean4Lean/Experimental/StratifiedUntyped.lean:260:   | appDF _ _ ih1 ih2 => exact instL_instN ▸ .appDF ih1 ih2
Lean4Lean/Experimental/StratifiedUntyped.lean:265:   | eta _ ih => simpa [instL] using .eta ih
Lean4Lean/Experimental/StratifiedUntyped.lean:268:     simp [instL, instL_instL]
Lean4Lean/Experimental/StratifiedUntyped.lean:285:     rw [ClosedN.liftN_eq_rev (eqA ▸ (henv.closedC h1).instL) (Nat.zero_le _)] at eqA
Lean4Lean/Experimental/StratifiedUntyped.lean:303:   --     hA1.instL.liftN_eq (Nat.zero_le _),
Lean4Lean/Experimental/StratifiedUntyped.lean:304:   --     hA2.instL.liftN_eq (Nat.zero_le _),
Lean4Lean/Experimental/StratifiedUntyped.lean:305:   --     hA3.instL.liftN_eq (Nat.zero_le _)]
Lean4Lean/Experimental/Stratified.lean:36:     Γ ⊢ .const c ls : ci.type.instL ls
Lean4Lean/Experimental/Stratified.lean:56:     Γ ⊢ .const c ls ≡ .const c ls' : ci.type.instL ls
Lean4Lean/Experimental/Stratified.lean:70:     Γ ⊢ df.lhs.instL ls ≡ df.rhs.instL ls : df.type.instL ls
Lean4Lean/Experimental/Stratified.lean:240:   --   refine .bvar h.instL
Lean4Lean/Experimental/Stratified.lean:242:   --   simp [instL, instL_instL]
Lean4Lean/Experimental/Stratified.lean:246:   -- | app _ _ ih1 ih2 => exact instL_instN ▸ .appDF ih1 ih2
Lean4Lean/Experimental/Stratified.lean:251:   -- | eta _ ih => simpa [instL] using .eta ih
Lean4Lean/Experiment