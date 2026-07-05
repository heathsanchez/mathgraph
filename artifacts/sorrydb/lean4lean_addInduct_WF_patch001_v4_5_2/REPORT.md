# SorryDB v4.5.2 — lean4lean addInduct_WF Patch001

## Target

- Repository: digama0/lean4lean
- Commit: 97addd51fac964f45c595ec2c21b1b60ff0a2cc8
- File: Lean4Lean/Theory/Typing/InductiveLemmas.lean
- Theorem: VEnv.addInduct_WF

## Baseline

- base_build_returncode: 0
- base_build_seconds: 75.42

## Result

- status: PATCH001_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Variant Summary

- v01_trace_goal: module_rc=0, module_seconds=0.87, full_rc=None, full_seconds=None
- v02_simpa_using_henv: module_rc=1, module_seconds=0.81, full_rc=None, full_seconds=None
- v03_cases_decl_simp: module_rc=1, module_seconds=0.81, full_rc=None, full_seconds=None
- v04_unfold_addInduct_at_henv: module_rc=1, module_seconds=0.71, full_rc=None, full_seconds=None
- v05_unfold_ordered_addInduct: module_rc=1, module_seconds=0.7, full_rc=None, full_seconds=None
- v06_aesop_after_simp: module_rc=1, module_seconds=0.7, full_rc=None, full_seconds=None
- v07_cases_hdecl_simp_all: module_rc=1, module_seconds=0.7, full_rc=None, full_seconds=None

## Target Window

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

## Recon

====================================================================================================
PATTERN: \bdef\s+addInduct\b
====================================================================================================
PATTERN: \btheorem\s+.*addInduct
Lean4Lean/Verify/Environment/Lemmas.lean:65: theorem Aligned.addInduct (H : AddInduct C₁ venv₁ decl C₂ venv₂) :
Lean4Lean/Verify/Environment/Basic.lean:69: nonrec theorem AddInduct.to_addInduct
Lean4Lean/Theory/Typing/InductiveLemmas.lean:8: theorem addInduct_WF (henv : Ordered env) (hdecl : decl.WF env)
====================================================================================================
PATTERN: \blemma\s+.*addInduct
====================================================================================================
PATTERN: \bdef\s+Ordered\b
====================================================================================================
PATTERN: \btheorem\s+.*Ordered
Lean4Lean/Experimental/Stronger.lean:229: theorem Ordered.out (H : Ordered env) : env.out.Ordered := by
Lean4Lean/Experimental/Stronger.lean:456: theorem IsDefEqStrong.defeqDF_l (henv : Ordered env) (hΓ : CtxStrong env U Γ)
Lean4Lean/Verify/Typing/Lemmas.lean:156: nonrec theorem VLocalDecl.WF.weakN (henv : env.Ordered) (W : Ctx.LiftN n k Γ Γ') :
Lean4Lean/Verify/Typing/Lemmas.lean:160: nonrec theorem VLocalDecl.WF.instN (henv : env.Ordered) (W : Ctx.InstN Γ₀ e₀ A₀ k Γ₁ Γ)
Lean4Lean/Verify/Typing/Lemmas.lean:711: theorem VLocalDecl.IsDefEq.defeqDFC (henv : Ordered env) (hΓ : IsDefEqCtx env U Γ₀ Γ₁ Γ₂)
Lean4Lean/Verify/Typing/Lemmas.lean:1181: theorem TrExprS.inst {Δ : VLCtx} (henv : Ordered env)
Lean4Lean/Verify/Typing/Lemmas.lean:1271: theorem TrExprS.inst_let {Δ : VLCtx} (henv : Ordered env)
Lean4Lean/Verify/Typing/Lemmas.lean:1662: theorem VExpr.WF.boolLit_has_type (wf : env.Ordered) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:1675: theorem TrExprS.nat_of_natZero (wf : env.Ordered) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:1725: theorem VEnv.HasPrimitives.nat_of_charOfNat (wf : Ordered env) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:1733: theorem TrExprS.listChar (wf : env.Ordered) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:1747: theorem TrExprS.listCharNil (wf : env.Ordered) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:1760: theorem TrExprS.listCharCons (wf : env.Ordered) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:1774: theorem TrExprS.listCharLit (wf : env.Ordered) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:1792: theorem TrExprS.trLiteral (wf : env.Ordered) (henv : env.HasPrimitives)
Lean4Lean/Verify/Typing/Lemmas.lean:2060: theorem TrExprS.inst_fvar {Δ : VLCtx} (henv : Ordered env)
Lean4Lean/Theory/Typing/QuotLemmas.lean:7: theorem addQuot_WF (henv : Ordered env) (hq : QuotReady env) :
Lean4Lean/Theory/Typing/Lemmas.lean:268: theorem Ordered.induction (motive : VEnv → Nat → VExpr → VExpr → Prop)
Lean4Lean/Theory/Typing/Lemmas.lean:362: theorem Ordered.closed (H : Ordered env) : env.OnTypes fun _ e A => e.ClosedN ∧ A.ClosedN :=
Lean4Lean/Theory/Typing/Lemmas.lean:365: theorem Ordered.closedC (H : Ordered env)
Lean4Lean/Theory/Typing/Lemmas.lean:369: theorem IsDefEq.closedN {env : VEnv} (henv : env.Ordered)
Lean4Lean/Theory/Typing/Lemmas.lean:373: theorem _root_.Lean4Lean.VExpr.WF.closedN {env : VEnv} (henv : env.Ordered)
Lean4Lean/Theory/Typing/Lemmas.lean:427: theorem Ordered.constWF (H : Ordered env) (h : env.constants n = some ci) : ci.WF env := by
Lean4Lean/Theory/Typing/Lemmas.lean:438: theorem Ordered.defEqWF (H : Ordered env) (h : env.defeqs df) : df.WF env := by
Lean4Lean/Theory/Typing/Lemmas.lean:591: theorem IsType.lookup (henv : Ordered env) (h : OnCtx Γ (IsType env U)) (hL : Lookup Γ n A) :
Lean4Lean/Theory/Typing/Lemmas.lean:673: theorem HasType.instN {env : VEnv} (henv : env.Ordered) (W : Ctx.InstN Γ₀ e₀ A₀ k Γ₁ Γ)
Lean4Lean/Theory/Typing/Lemmas.lean:677: theorem IsType.instN {env : VEnv} (henv : env.Ordered) (W : Ctx.InstN Γ₀ e₀ A₀ k Γ₁ Γ)
Lean4Lean/Theory/Typing/Lemmas.lean:681: theorem IsDefEqU.instN {env : VEnv} (henv : env.Ordered) (W : Ctx.InstN Γ₀ e₀ A₀ k Γ₁ Γ)
Lean4Lean/Theory/Typing/Lemmas.lean:685: theorem _root_.Lean4Lean.Ctx.InstN.wf (henv : Ordered env) (W : Ctx.InstN Γ₀ e₀ A₀ k Γ₁ Γ)
Lean4Lean/Theory/Typing/Lemmas.lean:692: theorem IsDefEq.defeqDF_l' (henv : Ordered env) (h1 : env.IsDefEq U Γ A A' (.sort u))
Lean4Lean/Theory/Typing/Lemmas.lean:705: theorem IsDefEq.defeqDF_l (henv : Ordered env) (h1 : env.IsDefEq U Γ A A' (.sort u))
Lean4Lean/Theory/Typing/Lemmas.lean:709: theorem HasType.defeq_l (henv : Ordered env) (h1 : env.IsDefEq U Γ A A' (.sort u))
Lean4Lean/Theory/Typing/Lemmas.lean:712: theorem IsDefEq.defeqDFC' (henv : Ordered env) (h1 : IsDefEqCtx env U Γ₀ Γ₁ Γ₂)
Lean4Lean/Theory/Typing/Lemmas.lean:719: theorem IsDefEq.defeqDFC (henv : Ordered env) (h1 : IsDefEqCtx env U Γ₀ Γ₁ Γ₂)
Lean4Lean/Theory/Typing/Lemmas.lean:722: theorem HasType.defeqDFC (henv : Ordered env) (h1 : IsDefEqCtx env U Γ₀ Γ₁ Γ₂)
Lean4Lean/Theory/Typing/Lemmas.lean:725: theorem IsType.defeqDFC (henv : Ordered env) (h1 : IsDefEqCtx env U Γ₀ Γ₁ Γ₂)
Lean4Lean/Theory/Typing/Lemmas.lean:728: theorem IsDefEqU.defeqDFC (henv : Ordered env) (h1 : IsDefEqCtx env U Γ₀ Γ₁ Γ₂)
Lean4Lean/Theory/Typing/Lemmas.lean:732: theorem IsDefEqCtx.symm (henv : Ordered env) :
Lean4Lean/Theory/Typing/Lemmas.lean:786: theorem HasType.forallE_inv (henv : Ordered env) (H : env.HasType U Γ (A.forallE B) V) :
Lean4Lean/Theory/Typing/Lemmas.lean:794: theorem IsType.forallE_inv (henv : Ordered env) (H : env.IsType U Γ (A.forallE B)) :
Lean4Lean/Theory/Typing/Lemmas.lean:826: theorem IsDefEq.sort_inv_l (henv : Ordered env) (H : env.IsDefEq U Γ (.sort u) e2 V) : u.WF U :=
Lean4Lean/Theory/Typing/Lemmas.lean:829: theorem IsDefEq.sort_inv_r (henv : Ordered env) (H : env.IsDefEq U Γ e2 (.sort u) V) : u.WF U :=
Lean4Lean/Theory/Typing/Lemmas.lean:832: theorem HasType.sort_inv (henv : Ordered env) (H : env.HasType U Γ (.sort u) V) : u.WF U :=
Lean4Lean/Theory/Typing/Lemmas.lean:835: theorem IsType.sort_inv (henv : Ordered env) (H : env.IsType U Γ (.sort u)) : u.WF U :=
Lean4Lean/Theory/Typing/Lemmas.lean:866: theorem Ordered.isType (H : Ordered env) :
Lean4Lean/Theory/Typing/Lemmas.lean:872: theorem IsDefEq.isType (henv : Ordered env) (hΓ : OnCtx Γ (env.IsType U))
Lean4Lean/Theory/Typing/Lemmas.lean:875: theorem IsDefEq.sort_r (henv : Ordered env)
Lean4Lean/Theory/Typing/Strong.lean:419: theorem IsDefEqStrong.defeqDF_l (henv : Ordered env) (hΓ : CtxStrong env U Γ)
Lean4Lean/Theory/Typing/Strong.lean:666: theorem CtxStrong.strong' (henv : Ordered env) (envIH : env.OnTypes (EnvStrong env))
Lean4Lean/Theory/Typing/Strong.lean:672: theorem Ordered.strong (henv : Ordered env) : OnTypes env (EnvStrong env) := by
====================================================================================================
PATTERN: \blemma\s+.*Ordered
====================================================================================================
PATTERN: \bdef\s+WF\b
Lean4Lean/Verify/TypeChecker/Basic.lean:7: def WF (x : Except ε α) (Q : α → Prop) : Prop := ∀ a, x = .ok a → Q a
Lean4Lean/Theory/VLevel.lean:19: def WF : VLevel → Prop
====================================================================================================
PATTERN: \btheorem\s+.*WF
Lean4Lean/Experimental/Stronger.lean:216: nonrec theorem VConstant.WF.out {ci : VConstant} (H : ci.WF env) : ci.toVConstant.WF env.out :=
Lean4Lean/Experimental/Stronger.lean:219: theorem VDefEq.WF.out {ci : VDefEq} (H : ci.WF env) : ci.toVDefEq.WF env.out :=
Lean4Lean/Experimental/ShapeLogRel.lean:865: theorem Shape.WF.lift_iff (le : n ≤ m) : WF (x.lift m) ↔ WF (n := n) x := by
Lean4Lean/Experimental/ShapeLogRel.lean:891: theorem ShapeFun.WF.lift_iff {x : ShapeFun n} (le : n ≤ m) :
Lean4Lean/Experimental/ShapeLogRel.lean:895: protected theorem Shape.WF.lift (le : n ≤ m) : WF (n := n) x → WF (x.lift m) := (lift_iff le).2
Lean4Lean/Experimental/ShapeLogRel.lean:897: protected theorem ShapeFun.WF.lift {x : ShapeFun n} (le : n ≤ m) : WF Shape.WF x →
Lean4Lean/Experimental/ShapeLogRel.lean:900: protected theorem Shape.WF.olift {x : Shape n} (H : x.olift (m := m) = some x') :
Lean4Lean/Experimental/ShapeLogRel.lean:906: protected theorem ShapeFun.WF.olift {x : ShapeFun n}
Lean4Lean/Experimental/ShapeLogRel.lean:912: protected theorem Shape.WF.bot : (Shape.bot (n := n)).WF := by cases n <;> trivial
Lean4Lean/Experimental/ShapeLogRel.lean:913: protected theorem Shape.WF.sort : (Shape.sort (n := n) r).WF := by cases n <;> trivial
Lean4Lean/Experimental/ShapeLogRel.lean:915: protected theorem ShapeFun.WF.bot : (ShapeFun.bot (n := n)).WF Shape.WF := by
Lean4Lean/Experimental/ShapeLogRel.lean:972: theorem WShape.mk_ctor {n} (l : List (Shape n)) (wf : Shape.WF (n := n+1) (.ctor c l)) :
Lean4Lean/Experimental/ShapeLogRel.lean:1655: protected theorem Shape.WF.plift (x : WShape n) :
Lean4Lean/Experimental/ShapeLogRel.lean:1713: -- theorem ShapeFun.WF'.plift (h : WF (n := n) Shape.WF x) :
Lean4Lean/Experimental/ShapeLogRel.lean:1718: -- theorem Shape.WF.plift (h : WF (n := n) x) : WF (n := m) x.plift.1 := sorry
Lean4Lean/Experimental/ShapeLogRel.lean:1719: -- theorem ShapeFun.WF.plift (h : WF (n := n) Shape.WF x) :
Lean4Lean/Experimental/ShapeLogRel.lean:2243: theorem ShapeFun.WF.bot_le (wf : WF Shape.WF f) : ShapeFun.bot.LE f := by
Lean4Lean/Experimental/ShapeLogRel.lean:2247: theorem Shape.WF.lam_non_bot (wf : WF (n := n+1) (.lam f)) : ∃ x y, (x, y) ∈ f ∧ y ≠ .bot :=
Lean4Lean/Experimental/ShapeLogRel.lean:2402: protected theorem ShapeFun.WF.single (x y : WShape n) : WF Shape.WF (single x.1 y.1) := by
Lean4Lean/Experimental/ShapeLogRel.lean:3433: theorem LE_Interp.Matches.head_wf (H : Matches p c rargs m) (wf : p.WF cl top k) :
Lean4Lean/Experimental/ShapeLogRel.lean:3440: theorem LE_Interp.Matches.head_wf_eq (H : Matches p c rargs m) (wf : p.WF cl top k) :
Lean4Lean/Experimental/ShapeLogRel.lean:3451: theorem LE_Interp.Matches.mono_l {rargs rargs'} (wfp : p.WF Params.classify b k)
Lean4Lean/Experimental/ShapeLogRel.lean:6065: theorem LR.SubstWF.fits : LR.SubstWF Γ₀ σ σ' Γ ρ → ρ.Fits Γ₀ Γ
Lean4Lean/Experimental/ShapeLogRel.lean:6069: theorem LR.SubstWF.toSubstEq : LR.SubstWF Γ₀ σ σ' Γ ρ → Ctx.SubstEq Γ₀ σ σ' Γ
Lean4Lean/Experimental/ShapeLogRel.lean:6073: theorem LR.SubstWF.left (W : LR.SubstWF Γ₀ σ σ' Γ ρ) : LR.SubstWF Γ₀ σ σ Γ ρ := by
Lean4Lean/Experimental/ShapeLogRel.lean:6081: theorem LR.SubstWF.symm (W : LR.SubstWF Γ₀ σ σ' Γ ρ) : LR.SubstWF Γ₀ σ' σ Γ ρ := by
Lean4Lean/Verify/EquivManager.lean:163: theorem IsDefEqE.uniq (henv : env.WF) (noBV : Δ.NoBV) (hΔ : Δ.WF env Us.length)
Lean4Lean/Verify/EquivManager.lean:184: theorem M.WF.stateWF {P : α → EquivManager → Prop}
Lean4Lean/Verify/EquivManager.lean:188: protected theorem M.WF.pure {a : α} {P : α → EquivManager → Prop} (H : P a m) :
Lean4Lean/Verify/EquivManager.lean:192: protected theorem M.WF.bind {x : StateM EquivManager β} {f : β → StateM EquivManager γ}
Lean4Lean/Verify/EquivManager.lean:200: protected theorem M.WF.mono {x : StateM EquivManager β}
Lean4Lean/Verify/EquivManager.lean:205: protected theorem M.WF.bind_le {x : StateM EquivManager β} {f : β → StateM EquivManager γ}
Lean4Lean/Verify/EquivManager.lean:210: protected theorem M.WF.andM {x y : StateM EquivManager Bool}
Lean4Lean/Verify/EquivManager.lean:217: theorem find.WF : M.WF env Us Δ m (EquivManager.find i) fun j m => m.uf.Equiv i j := by
Lean4Lean/Verify/EquivManager.lean:225: theorem merge.WF (wf : m.WF env Us Δ)
Lean4Lean/Verify/EquivManager.lean:238: theorem toNode.WF :
Lean4Lean/Verify/EquivManager.lean:262: theorem isEquiv.WF :
Lean4Lean/Verify/EquivManager.lean:315: theorem addEquiv.WF {c : VContext} {s : VState} (he₁ : c.TrExprS e₁ e') (he₂ : c.TrExpr e₂ e') :
Lean4Lean/Verify/EquivManager.lean:327: theorem isDefEq.WF {c : VContext} {s : VState}
Lean4Lean/Verify/LocalContext.lean:126: theorem WF.map_wf {lctx : LocalContext} : lctx.WF → lctx.fvarIdToDecl.WF
Lean4Lean/Verify/LocalContext.lean:130: theorem WF.decls_wf {lctx : LocalContext} : lctx.WF → lctx.decls.WF
Lean4Lean/Verify/LocalContext.lean:136: theorem WF.map_toList : WF lctx →
Lean4Lean/Verify/LocalContext.lean:148: theorem WF.find?_eq_find?_toList (H : WF lctx) :
Lean4Lean/Verify/LocalContext.lean:153: theorem WF.nodup : WF lctx → (lctx.toList.map (·.fvarId)).Nodup
Lean4Lean/Verify/LocalContext.lean:161: protected theorem WF.mkLocalDecl
Lean4Lean/Verify/LocalContext.lean:165: protected theorem WF.mkLetDecl
Lean4Lean/Verify/LocalContext.lean:197: theorem TrLocalDecl.wf : TrLocalDecl env Us Δ d d' → d'.WF env Us.length Δ.toCtx
Lean4Lean/Verify/LocalContext.lean:264: theorem TrLCtx'.wf : TrLCtx' env Us ds Δ → (ds.map (·.fvarId)).Nodup → Δ.WF env Us.length
Lean4Lean/Verify/LocalContext.lean:270: theorem TrLCtx.wf (H : TrLCtx env Us lctx Δ) : Δ.WF env Us.length := H.2.wf H.1.nodup
Lean4Lean/Verify/LocalContext.lean:276: theorem TrLCtx'.find?_of_mem (henv : env.WF) (H : TrLCtx' env Us ds Δ)
====================================================================================================
PATTERN: \blemma\s+.*WF
====================================================================================================
PATTERN: \bnamespace\s+VEnv\b
Lean4Lean/Experimental/CoinductiveLogRel.lean:4: namespace VEnv
Lean4Lean/Experimental/StratifiedUntyped.lean:5: namespace VEnv
Lean4Lean/Experimental/Stratified.lean:5: namespace VEnv
Lean4Lean/Experimental/Stronger.lean:17: namespace VEnv'
Lean4Lean/Theory/Typing/QuotLemmas.lean:5: namespace VEnv
Lean4Lean/Theory/Typing/Lemmas.lean:184: namespace VEnv
Lean4Lean/Theory/Typing/Lemmas.lean:425: namespace VEnv
Lean4Lean/Theory/Typing/Strong.lean:4: namespace VEnv
Lean4Lean/Theory/Typing/Meta.lean:4: namespace VEnv
Lean4Lean/Theory/Typing/Basic.lean:9: namespace VEnv
Lean4Lean/Theory/Typing/HeadReduction.lean:14: namespace VEnv
Lean4Lean/Theory/Typing/UniqueTyping.lean:7: namespace VEnv
Lean4Lean/Theory/Typing/InductiveLemmas.lean:6: namespace VEnv
Lean4Lean/Theory/Typing/Injectivity.lean:9: namespace VEnv
Lean4Lean/Theory/Typing/ChurchRosser.lean:6: namespace VEnv

## Next Move

Use the first diagnostic goal from v01_trace_goal and the failed variants to build Patch002.