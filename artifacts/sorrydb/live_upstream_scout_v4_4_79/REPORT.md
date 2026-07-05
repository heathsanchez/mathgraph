# SorryDB v4.4.79 — Live Upstream Active-Sorry Scout

## Target

- Repository: teorth/equational_theories
- Branch: main
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938

## Result

- active candidate count: 2
- comment-only false positives: 1
- status: LIVE_ACTIVE_TARGET_FOUND

## Top Candidates

### 1. equational_theories/Definability/Law43.lean

- score: 492.55
- active_sorry_count: 1
- line_count: 31
- import_count: 3
- flags: {"known_parked": false, "known_solved": true, "definability": true, "equations_all": true, "toFin": false, "satisfies_or_models": false, "models_iff": false, "termdef": true, "macro_or_elab": false, "category_theory": false, "uses_aesop": false, "uses_decide": true, "small_imports": true}

Nearby declarations:
- line 10: theorem Equation43_termDefinableFrom_swapped_args {L : NatMagmaLaw}
- line 18: theorem Equation43_termDefinableFrom_Equation40 : Law43.TermDefinableFrom Law40 :=
- line 22: theorem Equation43_termDefinableFrom_Equation4343 : Law43.TermDefinableFrom Law4343 :=
- line 26: theorem Equation43_termDefinableFrom_Equation4293 : Law43.TermDefinableFrom Law4293 :=
- line 30: theorem Equation43_termDefinableFrom_Equation4321 : Law43.TermDefinableFrom Law4321 :=

First active sorry window:

0003: import equational_theories.Equations.All
0004: 
0005: open FirstOrder.Language
0006: open Law
0007: open Law.MagmaLaw
0008: 
0009: --TODO: the commutative law is definable from anything of the form f(x,y) ≃ f(y,x).
0010: theorem Equation43_termDefinableFrom_swapped_args {L : NatMagmaLaw}
0011:     (hL2args : ∀ e ∈ L.lhs.elems.1, e ∈ [0,1] := by decide +kernel)
0012:     (hR2args : ∀ e ∈ L.rhs.elems.1, e ∈ [0,1] := by decide +kernel)
0013:     (hSymm : L.lhs ⬝ (fun x ↦ Lf $ Equiv.swap 0 1 x) = L.rhs := by rfl)
0014:     : Law43.TermDefinableFrom L := by
0015:   sorry
0016: 
0017: /-- The commutative law 43 `x ◇ y = y ◇ x` is TermDefinable from 40 `x ◇ x = y ◇ y`. -/
0018: theorem Equation43_termDefinableFrom_Equation40 : Law43.TermDefinableFrom Law40 :=
0019:   Equation43_termDefinableFrom_swapped_args
0020: 
0021: /-- The commutative law 43 `x ◇ y = y ◇ x` is TermDefinable from 4343 `x ◇ (y ◇ y) = y ◇ (x ◇ x)`. -/
0022: theorem Equation43_termDefinableFrom_Equation4343 : Law43.TermDefinableFrom Law4343 :=
0023:   Equation43_termDefinableFrom_swapped_args
0024: 
0025: /-- The commutative law 43 `x ◇ y = y ◇ x` is TermDefinable from 4293 `x ◇ (x ◇ y) = y ◇ (y ◇ x)`. -/
0026: theorem Equation43_termDefinableFrom_Equation4293 : Law43.TermDefinableFrom Law4293 :=
0027:   Equation43_termDefinableFrom_swapped_args

### 2. equational_theories/Definability/Law46.lean

- score: 1176.7
- active_sorry_count: 7
- line_count: 74
- import_count: 3
- flags: {"known_parked": true, "known_solved": false, "definability": true, "equations_all": true, "toFin": true, "satisfies_or_models": true, "models_iff": true, "termdef": true, "macro_or_elab": false, "category_theory": false, "uses_aesop": false, "uses_decide": true, "small_imports": true}

Nearby declarations:
- line 11: theorem Equation46_termDefinableFrom_equalShape {L : NatMagmaLaw}
- line 57: theorem Equation46_termDefinableFrom_Equation40 : Law46.TermDefinableFrom Law40 :=
- line 61: theorem Equation46_termDefinableFrom_Equation4276 : Law46.TermDefinableFrom Law4276 :=
- line 65: theorem Equation46_termDefinableFrom_Equation4308 : Law46.TermDefinableFrom Law4308 :=
- line 69: theorem Equation46_termDefinableFrom_Equation4336 : Law46.TermDefinableFrom Law4336 :=

First active sorry window:

0007: open Law.MagmaLaw
0008: 
0009: /-- The constant law 46 `x ◇ y = z ◇ w` is TermDefinable from any law `lhs = rhs`, where
0010: lhs and rhs are the same shape, but with disjoint sets of variables. -/
0011: theorem Equation46_termDefinableFrom_equalShape {L : NatMagmaLaw}
0012:   (hShape : L.lhs ⬝ (fun _ ↦ Lf 0) = L.rhs ⬝ (fun _ ↦ Lf 0) := by rfl)
0013:   (hDisjoint : L.lhs.elems.val.Disjoint L.rhs.elems := by rw [List.Disjoint]; decide +kernel)
0014:   : Law46.TermDefinableFrom L := by
0015:   --There are two cases: there is at least one function application, or both sides of L are leaves.
0016:   cases hlhs : L.lhs
0017:   next x =>
0018:     --In this case, the law is of the form x = y. Thus, it is (equivalent to) equation 2
0019:     obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := sorry
0020:     have hxy : x ≠ y := sorry
0021:     rw [show L = Lf x ≃ Lf y from sorry]
0022:     clear hlhs hy hShape hDisjoint
0023:     apply termDefinable_of_termStructural
0024:     apply termStructural_of_implies
0025:     have : (Lf x ≃ Lf y).toFin.toNat = Law2 := by
0026:       -- have h₁ : (Lf x ≃ Lf y : NatMagmaLaw).elems.1 = [x,y] := by
0027:       --   sorry
0028:       -- have h₂ : Fin ((Lf x ≃ Lf y : NatMagmaLaw).elems).1.length = Fin 2 := by
0029:       --   rw [h₁]
0030:       --   simp
0031:       -- simp [toFin, h₁]

## Recommended Next Target

equational_theories/Definability/Law43.lean

Reason: lowest score after penalizing Law46-like semantic/toFin/model/canonicalization traps.