# SorryDB v4.5.3 — Park lean4lean addInduct and Rotate

## Verdict

Park `digama0/lean4lean :: Lean4Lean/Theory/Typing/InductiveLemmas.lean`.

## Why

Patch001 showed the target is not a clean theorem hole.

The diagnostic goal was:

    env : VEnv
    decl : VInductDecl
    env' : VEnv
    henv : env.Ordered
    hdecl : VInductDecl.WF env decl
    henv' : env.addInduct decl = some env'
    goal: env'.Ordered

But after unfolding/simplification, Lean exposed:

    henv' : sorry = some env'

That means the theorem depends on unfinished core definitions, especially around `addInduct`, rather than a local proof gap.

## Classification

    PARKED_DEPENDENCY_SORRY_TRAP

## Rotation Result

- input candidates: 16
- rejected by rotation: 5
- remaining candidates: 11
- status: NEXT_TARGET_FOUND

## Next Candidate

- repo: leanprover-community/mathlib4
- file: Mathlib/Algebra/Order/CauSeq/Completion.lean
- commit: d3716e6d2ea114ae7d9f994e5ebf3c064d80c8a7
- real_target_score: -21.25
- active_sorry_count: 1
- line_count: 415
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": true, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

Nearby declarations:

- line 33: def Cauchy :=
- line 39: def mk : CauSeq _ abv → Cauchy abv :=
- line 43: theorem mk_eq_mk (f : CauSeq _ abv) : @Eq (Cauchy abv) ⟦f⟧ (mk f) :=
- line 46: theorem mk_eq {f g : CauSeq _ abv} : mk f = mk g ↔ LimZero (f - g) :=
- line 50: def ofRat (x : β) : Cauchy abv :=
- line 53: instance : Zero (Cauchy abv) :=
- line 56: instance : One (Cauchy abv) :=
- line 59: instance : Inhabited (Cauchy abv) :=

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

## Rejected During Rotation

- digama0/lean4lean :: Lean4Lean/Theory/Typing/InductiveLemmas.lean => DEPENDENCY_SORRY_TRAP: target theorem depends on addInduct, but addInduct unfolds to upstream `sorry`; diagnostic showed henv' : sorry = some env'.
- digama0/lean4lean :: Lean4Lean/Theory/Typing/UniqueTyping.lean => LEAN4LEAN_CORE_THEORY_DEPENDENCY_RISK
- digama0/lean4lean :: Lean4Lean/Theory/Typing/Injectivity.lean => LEAN4LEAN_CORE_THEORY_DEPENDENCY_RISK
- digama0/lean4lean :: Lean4Lean/Theory/Inductive.lean => LEAN4LEAN_CORE_THEORY_DEPENDENCY_RISK
- digama0/lean4lean :: Lean4Lean/Theory/Typing/ChurchRosser.lean => LEAN4LEAN_CORE_THEORY_DEPENDENCY_RISK