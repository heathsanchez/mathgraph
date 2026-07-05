# SorryDB v4.5.0 — Multi-Repo Live Sorry Scout

## Purpose

Find fresh active Lean `sorry` targets outside the exhausted `teorth/equational_theories` pinned campaign.

## Result

- repos attempted: 13
- active sorry candidates: 660
- actionable candidates: 658
- comment-only false positives: 138
- status: ACTIONABLE_TARGET_FOUND

## Repo Summary

- leanprover-community/mathlib4: clone_ok=True, has_lake=True, lean_files=8773, active_candidates=35, comment_only=45
- leanprover-community/batteries: clone_ok=True, has_lake=True, lean_files=255, active_candidates=7, comment_only=6
- leanprover/lean4: clone_ok=True, has_lake=False, lean_files=6864, active_candidates=484, comment_only=76
- teorth/equational_theories: clone_ok=True, has_lake=True, lean_files=1301, active_candidates=2, comment_only=1
- ImperialCollegeLondon/formalising-mathematics-2024: clone_ok=True, has_lake=True, lean_files=176, active_candidates=82, comment_only=1
- ImperialCollegeLondon/formalising-mathematics: clone_ok=True, has_lake=False, lean_files=45, active_candidates=23, comment_only=1
- leanprover-community/flt-regular: clone_ok=True, has_lake=True, lean_files=32, active_candidates=0, comment_only=0
- leanprover-community/sphere-eversion: clone_ok=True, has_lake=True, lean_files=65, active_candidates=1, comment_only=2
- leanprover-community/mathlib4_docs: clone_ok=True, has_lake=True, lean_files=0, active_candidates=0, comment_only=0
- ProofWidgets/ProofWidgets4: clone_ok=False, has_lake=False, lean_files=0, active_candidates=0, comment_only=0
- leanprover-community/aesop: clone_ok=True, has_lake=True, lean_files=250, active_candidates=5, comment_only=4
- digama0/lean4lean: clone_ok=True, has_lake=True, lean_files=82, active_candidates=21, comment_only=2
- reservoir-data/reservoir: clone_ok=False, has_lake=False, lean_files=0, active_candidates=0, comment_only=0

## Recommended Next Target

- repo: leanprover-community/mathlib4
- file: MathlibTest/BasicFiles/TacticCommon.lean
- commit: d3716e6d2ea114ae7d9f994e5ebf3c064d80c8a7
- score: -45.15
- active_sorry_count: 1
- line_count: 37
- import_count: 1
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

Nearby declarations:

- line 14: theorem test_check_tactic : True := by
- line 24: theorem test_whatsnew : True := trivial
- line 28: theorem test_count_heartbeats : True := trivial
- line 32: theorem test_print_sorries : True := sorry

First active sorry window:

0020: #simp only [] => 0
0021: 
0022: #guard_msgs (substring := true) in
0023: whatsnew in
0024: theorem test_whatsnew : True := trivial
0025: 
0026: #guard_msgs (substring := true) in
0027: #count_heartbeats in
0028: theorem test_count_heartbeats : True := trivial
0029: 
0030: #guard_msgs (substring := true) in
0031: #print sorries in
0032: theorem test_print_sorries : True := sorry
0033: 
0034: -- Guard against the shake tool modifying our imports
0035: /-- info: [public import Init, public meta import Init, import Mathlib.Tactic.Common] -/
0036: #guard_msgs in
0037: run_elab Lean.logInfo m!"{(← Lean.MonadEnv.getEnv).imports}"

## Top Actionable Candidates

### 1. leanprover-community/mathlib4 :: MathlibTest/BasicFiles/TacticCommon.lean

- score: -45.15
- active_sorry_count: 1
- line_count: 37
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0020: #simp only [] => 0
0021: 
0022: #guard_msgs (substring := true) in
0023: whatsnew in
0024: theorem test_whatsnew : True := trivial
0025: 
0026: #guard_msgs (substring := true) in
0027: #count_heartbeats in
0028: theorem test_count_heartbeats : True := trivial
0029: 
0030: #guard_msgs (substring := true) in
0031: #print sorries in
0032: theorem test_print_sorries : True := sorry
0033: 
0034: -- Guard against the shake tool modifying our imports
0035: /-- info: [public import Init, public meta import Init, import Mathlib.Tactic.Common] -/
0036: #guard_msgs in
0037: run_elab Lean.logInfo m!"{(← Lean.MonadEnv.getEnv).imports}"

### 2. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section15numberTheory/Sheet7.lean

- score: -35.75
- active_sorry_count: 1
- line_count: 25
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0011: 
0012: # Prove that for every positive integer n the number 3 × (1⁵ +2⁵ +...+n⁵)
0013: # is divisible by 1³+2³+...+n³
0014: 
0015: This is question 9 in Sierpinski's book
0016: 
0017: -/
0018: 
0019: open scoped BigOperators
0020: 
0021: open Finset
0022: 
0023: example (n : ℕ) : ∑ i in range n, i ^ 3 ∣ 3 * ∑ i in range n, i ^ 5 := sorry
0024: 
0025: end Section15Sheet7

### 3. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section06orderingsAndLattices/Sheet3.lean

- score: -35.6
- active_sorry_count: 1
- line_count: 28
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0016: of a lattice where neither `A ⊓ (B ⊔ C) = (A ⊔ B) ⊓ (A ⊔ C)` nor `A ⊓ (B ⊔ C) = (A ⊓ B) ⊔ (A ⊓ C)`
0017: held. But it turns out that in a general lattice, one of these equalities holds if and only if the
0018: other one does! This was quite surprising to me.
0019: 
0020: The challenge is to prove it in Lean. My strategy would be to prove it on paper first
0021: and then formalise the proof. If you're not in to puzzles like this, then feel free to skip
0022: this question.
0023: 
0024: -/
0025: 
0026: example (L : Type) [Lattice L] :
0027:     (∀ a b c : L, a ⊔ b ⊓ c = (a ⊔ b) ⊓ (a ⊔ c)) ↔ ∀ a b c : L, a ⊓ (b ⊔ c) = a ⊓ b ⊔ a ⊓ c := by
0028:   sorry

### 4. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section15numberTheory/Sheet4.lean

- score: -35.1
- active_sorry_count: 1
- line_count: 38
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0024: and we want it to divide `3³⁽ᵈ⁺¹⁾⁺³-26(d+1)-27`
0025: 
0026: so we're done if it divides the difference, which is
0027: `-26d-26-27+26*27d+27*27`
0028: which is `26*26n+26*26 = 13*13*something`
0029: -/
0030: 
0031: -- The statement has subtraction in, so we use integers.
0032: example (n : ℕ) (hn : 0 < n) : -- remark; not going to use hn
0033:     (169 : ℤ) ∣ 3 ^ (3 * n + 3) - 26 * n - 27 := by
0034:   clear hn
0035:   -- told you
0036:   sorry
0037: 
0038: end Section15Sheet4

### 5. leanprover-community/mathlib4 :: MathlibTest/JacobiSymbol.lean

- score: -34.45
- active_sorry_count: 1
- line_count: 51
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0037: instance prime_1000003 : Fact (Nat.Prime 1000003) := ⟨by norm_num1⟩
0038: /-- info: -1 -/
0039: #guard_msgs in
0040: #eval @legendreSym 1000003 prime_1000003 7
0041: 
0042: -- Should replace `legendreSym` with `fastJacobiSym` without using `Fact p.Prime`
0043: /--
0044: info: 1
0045: ---
0046: warning: declaration uses `sorry`
0047: -/
0048: #guard_msgs in
0049: #eval! @legendreSym (2 ^ 11213 - 1) sorry 7
0050: 
0051: end Csimp

### 6. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section15numberTheory/Sheet5.lean

- score: -33.35
- active_sorry_count: 1
- line_count: 33
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0019: thoughts
0020: 
0021: if a(k)=2^(2⁶ᵏ⁺²)
0022: then a(k+1)=2^(2⁶*2⁶ᵏ⁺²)=a(k)^64
0023: 
0024: Note that 16^64 is 16 mod 19 according to a brute force calculation
0025: and so all of the a(k) are 16 mod 19 and we're done
0026: 
0027: -/
0028: 
0029: theorem sixteen_pow_sixtyfour_mod_nineteen : (16 : ZMod 19) ^ 64 = 16 := by rfl
0030: 
0031: example (k : ℕ) : 19 ∣ 2 ^ 2 ^ (6 * k + 2) + 3 := sorry
0032: 
0033: end Section15Sheet5

### 7. leanprover-community/mathlib4 :: MathlibTest/Simproc/VecPerm.lean

- score: -32.95
- active_sorry_count: 1
- line_count: 41
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0022:   simp [vecPerm, Equiv.swap_apply_def]
0023: 
0024: example : ![a, b, c, d] ∘ ![1, 3, 1, 3] = ![b, d, b, d] := by
0025:   simp [vecPerm]
0026: 
0027: set_option linter.unusedSimpArgs false
0028: 
0029: /-- warning: declaration uses `sorry` -/
0030: #guard_msgs in
0031: example (u v w x : Fin 4) : ![a, b, c, d] ∘ ![u, v, w, x] = ![b, d, b, d] := by
0032:   simp [vecPerm]
0033:   guard_target = ![a, b, c, d] ∘ ![u, v, w, x] = ![b, d, b, d]
0034:   sorry
0035: 
0036: /--
0037: error: `simp` made no progress
0038: -/
0039: #guard_msgs in
0040: example {n : Nat} (p q r : Fin n → Fin n) : p ∘ q = r := by
0041:   simp [vecPerm]

### 8. leanprover-community/mathlib4 :: MathlibTest/Tactic/AesopCat.lean

- score: -32.85
- active_sorry_count: 1
- line_count: 23
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": true, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": true, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0001: import Mathlib.CategoryTheory.Category.Basic
0002: 
0003: structure Foo where
0004:   x : Nat
0005:   w : x = 37 := by cat_disch
0006: 
0007: /-- warning: declaration uses `sorry` -/
0008: #guard_msgs in
0009: example : Foo where
0010:   x := sorry
0011: 
0012: /--
0013: error: could not synthesize default value for field 'w' of 'Foo' using tactics
0014: ---
0015: error: tactic 'aesop' failed, failed to prove the goal after exhaustive search.
0016: Initial goal:
0017:   ⊢ 35 = 37
0018: Remaining goals after safe rules:
0019:   ⊢ False
0020: -/
0021: #guard_msgs in
0022: example : Foo where

### 9. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section15numberTheory/Sheet8.lean

- score: -31.35
- active_sorry_count: 1
- line_count: 33
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0019: `((p-1)/2)!` works!
0020: 
0021: Why does it work: claim `1*2*...*(p-1)/2` squared is `-1`
0022: `1*2*....*(p-1)/2 - p` is 1 mod 4 so this is also
0023: `-1 * -2 * ... * -((p-1)/2)`, and mod p this is the same
0024: `(p-1) * (p-2) * ... ((p+1)/2)`, so `i²=1*2*....*(p-2)*(p-1)=(p-1)!`
0025: Wilson's theorem tells us that `(p-1)! = -1 mod p` if p is prime.
0026: 
0027: -/
0028: 
0029: theorem exists_sqrt_neg_one_of_one_mod_four
0030:     (p : ℕ) (hp : p.Prime) (hp2 : ∃ n, p = 4 * n + 1) :
0031:     ∃ i : ZMod p, i ^ 2 = -1 := sorry
0032: 
0033: end Section15Sheet8

### 10. leanprover-community/batteries :: BatteriesTest/lintunused.lean

- score: -30.95
- active_sorry_count: 1
- line_count: 51
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0001: import Batteries.Tactic.Lint
0002: 
0003: -- should be ignored as the proof contains sorry
0004: /-- warning: declaration uses `sorry` -/
0005: #guard_msgs in
0006: def foo (h : 1 = 1) : Bool := sorry
0007: 
0008: -- should be ignored since it uses `_h`
0009: def foo' (_h : 1 = 1) : Bool := true
0010: 
0011: -- should not be ignored
0012: set_option linter.unusedVariables false in
0013: def fooBad (h : 1 = 1) : Bool := true
0014: 
0015: theorem foo1_ok (_h : 1 = 2) : True := trivial
0016: 
0017: set_option linter.unusedVariables false in
0018: theorem foo2_bad (h : 1 = 1) : True := trivial

### 11. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section15numberTheory/Sheet6.lean

- score: -30.1
- active_sorry_count: 1
- line_count: 18
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0004: import Mathlib.Data.Nat.PrimeNormNum
0005: 
0006: section Section15Sheet6
0007: /-
0008: 
0009: # Prove the theorem, due to Kraichik, asserting that 13|2⁷⁰+3⁷⁰
0010: 
0011: This is the sixth question in Sierpinski's book "250 elementary problems
0012: in number theory".
0013: 
0014: -/
0015: 
0016: example : 13 ∣ 2 ^ 70 + 3 ^ 70 := sorry
0017: 
0018: end Section15Sheet6

### 12. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section10TopologicalSpaces/Sheet2.lean

- score: -26.95
- active_sorry_count: 1
- line_count: 41
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0019:     Continuous f ↔ ∀ U : Set Y, IsOpen U → IsOpen (f ⁻¹' U) := by
0020:   -- exact? solves this
0021:   exact continuous_def -- proof is not `rfl`, but who cares
0022: 
0023: example (X Y : Type) [MetricSpace X] [MetricSpace Y] (f : X → Y) :
0024:     Continuous f ↔ ∀ x : X, ∀ ε > 0, ∃ δ > 0, ∀ x' : X, dist x' x < δ → dist (f x') (f x) < ε := by
0025:   -- exact? solves this
0026:   exact Metric.continuous_iff -- proof is not `rfl`, but who cares
0027: 
0028: example (X Y Z : Type) [TopologicalSpace X] [TopologicalSpace Y] [TopologicalSpace Z]
0029:     (f : X → Y) (g : Y → Z) (hf : Continuous f) (hg : Continuous g) : Continuous (g ∘ f) := by
0030:   -- can you prove this from first principles? Start with `rw [continuous_def] at *`.
0031:   sorry
0032: 
0033: example (X Y Z : Type) [TopologicalSpace X] [TopologicalSpace Y] [TopologicalSpace Z]
0034:     (f : X → Y) (g : Y → Z) (hf : Continuous f) (hg : Continuous g) : Continuous (g ∘ f) := by
0035:   -- There's a tactic for continuity proofs by the way
0036:   continuity
0037: 
0038: example (X Y Z : Type) [TopologicalSpace X] [TopologicalSpace Y] [TopologicalSpace Z]
0039:     (f : X → Y) (g : Y → Z) (hf : Continuous f) (hg : Continuous g) : Continuous (g ∘ f) := by
0040:   -- And of course it's already in the library.
0041:   exact Continuous.comp hg hf

### 13. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section21galoisTheory/Sheet6.lean

- score: -25.95
- active_sorry_count: 1
- line_count: 61
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0047: 
0048: -- The Abel-Ruffini theorem is that the min poly of an element in `IsSolvableByRad E F` has solvable Galois group
0049: example (a : solvableByRad E F) : IsSolvable (minpoly E a).Gal :=
0050:   solvableByRad.isSolvable a
0051: 
0052: -- This was hard won! It was only finished a year or so ago.
0053: -- A symmetric group of size 5 or more is known not to be solvable:
0054: example (X : Type) (hX : 5 ≤ Cardinal.mk X) : ¬IsSolvable (Equiv.Perm X) :=
0055:   Equiv.Perm.not_solvable X hX
0056: 
0057: -- Using a root of x^5-4x+2 and the machinery in this section, Browning proves
0058: example : ∃ x : ℂ, IsAlgebraic ℚ x ∧ ¬IsSolvableByRad ℚ x :=
0059:   sorry
0060: 
0061: -- See the file `archive.100-theorems-list.16_abel_ruffini`.

### 14. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section11vectorSpaces/Sheet2.lean

- score: -25.65
- active_sorry_count: 1
- line_count: 67
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0055: # An example sheet question
0056: 
0057: A 2019 University of Edinburgh example sheet question (set to me as a challenge by a lecturer
0058: there): prove that if `V` is a 9-dimensional
0059: vector space and `A, B` are two subspaces of dimension 5, then `A ∩ B` cannot be
0060: the zero vector space.
0061: 
0062: -/
0063: open FiniteDimensional -- now we can just write `finrank`.
0064: 
0065: example (A B : Subspace k V) (hV : finrank k V = 9) (hA : finrank k A = 5) (hB : finrank k B = 5) :
0066:     A ⊓ B ≠ ⊥ := by
0067:   sorry

### 15. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section17curvesAndSurfaces/Sheet5.lean

- score: -24.65
- active_sorry_count: 1
- line_count: 47
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0035: example : Prop :=
0036:   Memℒp f p μ
0037: 
0038: -- The reason it's called `snorm` not `norm`, is because we didn't yet quotient out by
0039: -- the things whose integral is zero. This quotient is called `Lp`
0040: example : Type :=
0041:   Lp F p μ
0042: 
0043: example : AddCommGroup (Lp F p μ) := by infer_instance
0044: 
0045: -- sum of two p-integrable functions is p-integrable
0046: -- If 1 ≤ p then it's a normed group
0047: noncomputable example [Fact (1 ≤ p)] : NormedAddCommGroup (Lp F p μ) := by sorry

### 16. leanprover-community/mathlib4 :: MathlibTest/Linter/GlobalAttributeIn.lean

- score: -24.45
- active_sorry_count: 1
- line_count: 91
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0041: please remove the `in` or make this a `local simp`
0042: -/
0043: #guard_msgs in
0044: attribute [simp] Int.add in
0045: instance : Inhabited Int where
0046:   default := 0
0047: 
0048: namespace X
0049: 
0050: -- Here's another example, with nested attributes.
0051: /-- warning: declaration uses `sorry` -/
0052: #guard_msgs in
0053: theorem foo (x y : Nat) : x = y := sorry
0054: 
0055: /--
0056: error: Despite the `in`, the attribute simp is added globally to foo
0057: please remove the `in` or make this a `local simp`
0058: ---
0059: error: Despite the `in`, the attribute ext is added globally to foo
0060: please remove the `in` or make this a `local ext`
0061: -/
0062: #guard_msgs in
0063: set_option warning.simp.varHead false in
0064: attribute [simp, local simp, ext, -simp, -ext] foo in
0065: def bar := False

### 17. leanprover-community/aesop :: AesopTest/SplitScript.lean

- score: -24.35
- active_sorry_count: 1
- line_count: 53
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": true, "aesop_nearby": true, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0015: /--
0016: info: Try this:
0017: 
0018:   [apply]     split
0019:     next h => sorry
0020:     next h => sorry
0021: ---
0022: warning: declaration uses `sorry`
0023: -/
0024: #guard_msgs in
0025: example {A B : Prop} : if P then A else B := by
0026:   aesop? (config := { warnOnNonterminal := false })
0027:   all_goals sorry
0028: 
0029: /--
0030: info: Try this:
0031: 
0032:   [apply]     split at h
0033:     next h_1 => simp_all only [true_or]
0034:     next h_1 => simp_all only [or_true]
0035: -/
0036: #guard_msgs in
0037: example (h : if P then A else B) : A ∨ B := by
0038:   aesop?
0039: 

### 18. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section16commutativeAlgebra/Sheet1.lean

- score: -23.8
- active_sorry_count: 1
- line_count: 64
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0049:   -- Hence K is a monotone function.
0050:   -- So by Noetherian-ness of `R`, there exists `n` such that `Kₙ=Kₙ₊₁=Kₙ₊₂=…`
0051:   -- It suffices to prove that every element of ker(φ) is 0
0052:   -- so say r ∈ ker(φ)
0053:   -- and let's prove r=0
0054:   -- For all naturals m, The map φ^m is surjective
0055:   -- (by an easy induction)
0056:   -- so r = φ^n r' for some r' ∈ R
0057:   -- Thus 0 = φ(r)=φ^{n+1}(r')
0058:   -- Therefore r' ∈ ker(φ^{n+1})
0059:   -- ...=ker(φ^n)
0060:   -- and hence r=φ^n(r')=0 as required
0061:   sorry
0062: 
0063: 
0064: end Section16Sheet1

### 19. ImperialCollegeLondon/formalising-mathematics-2024 :: FormalisingMathematics2024/Section19algebraicNumberTheory/Sheet2.lean

- score: -22.65
- active_sorry_count: 1
- line_count: 47
- flags: {"test_file": false, "example_file": false, "generated_file": false, "definability": false, "toFin": false, "satisfies_or_models": false, "category_theory": false, "macro_or_elab": false, "metaprogramming": false, "unsafe": false, "axiom": false, "simp_nearby": false, "aesop_nearby": false, "omega_nearby": false, "linarith_nearby": false, "decide_nearby": false}

First active sorry window:

0032:   constructor
0033:   -- Both directions are delicate to do in Lean, but there already
0034:   · exact IsIntegral.fg_adjoin_singleton
0035:   · intro h
0036:     exact IsIntegral.of_mem_of_fg _ h _ (Algebra.self_mem_adjoin_singleton R a)
0037: 
0038: -- One can use this lemma to prove that if `a` and `b` are integral then `R[a]` is finitely-generated
0039: -- as an R-module, and `R[a][b]` is finitely-generated as an R[a]-module, so finitely-generated
0040: -- as an `R`-module. If furthermore `R` is Noetherian (for example `R=ℤ` then the subalgebras `R[a+b]` and `R[ab]`
0041: -- are finitely-generated as `R`-modules, so by the lemma applied the other way we deduce
0042: -- that these elements are integral. This is still a hard exercise (despite the lemma)
0043: -- because you have to move between `R` and `R[a]`.
0044: example (a b : K) (ha : IsIntegral ℤ a) (hb : IsIntegral ℤ b) : IsIntegral ℤ (a + b) := by sorry
0045: 
0046: -- I don't finish this in the solutions
0047: end Section19sheet2

### 20. digama0/lean4lean :: Lean4Lean/Theory/Typing/InductiveLemmas.lean

- score: -22.0
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

## Known Skips

- teorth/equational_theories :: equational_theories/Definability/Law43.lean => SOLVED_LOCALLY_PR_OPEN
- teorth/equational_theories :: equational_theories/Definability/Law46.lean => PARKED_NAMED_OBSTRUCTION