# MathGraph SorryDB v4.8.27 - Cross-Repo Direct Local-Have Batch Scanner

## Purpose

Scan queued repos for the winning target class:

    direct local `have ... := by sorry`, calc-step sorry, or local case residual

No Lean build was run.

## Repo summaries

- google-deepmind/formal-imo: scanned, sorries=310, ready=0, watch=0
- jsm28/IMOLean: scanned, sorries=50, ready=0, watch=0
- yangky11/miniF2F-lean4: scanned, sorries=488, ready=0, watch=0
- djvelleman/HTPILeanPackage: scanned, sorries=306, ready=0, watch=0
- Verified-zkEVM/ArkLib: scanned, sorries=277, ready=2, watch=0
- ATOMSLab/LFSE2024: scanned, sorries=57, ready=16, watch=0
- Beneficial-AI-Foundation/FloatSpec: scanned, sorries=406, ready=0, watch=9
- Beneficial-AI-Foundation/deductive-vericoding: scanned, sorries=4, ready=0, watch=0
- Beneficial-AI-Foundation/vericoding-benchmark: scanned, sorries=30863, ready=6, watch=135
- Brkhu/lean: scanned, sorries=56, ready=6, watch=0
- ByteDance-Seed/Seed-Prover: scanned, sorries=258, ready=0, watch=0
- GaloisInc/lean-protocol-support: scanned, sorries=16, ready=0, watch=0

## Counts

- total sorry rows scanned: 33091
- ready candidates score >= 65: 30
- watch candidates score 40..64: 144

## Ready candidates

### 1. score 137 - Verified-zkEVM/ArkLib ArkLib/ProofSystem/Binius/BinaryBasefold/QueryPhase.lean:271
- current: `sorry`
- reasons: direct_have_nextline_sorry, nearby_refine_apply_exact, nearby_arithmetic_tactic, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

                rw [h] at fiber_point_num_repr
                exact fiber_point_num_repr
              let x_point := finToSDomain 𝔽q β (h_ℓ_add_R_rate := h_ℓ_add_R_rate) ⟨i, by omega⟩ (by
                  apply Nat.lt_add_of_pos_right_of_le; simp only; omega) x
              queryCodeword 𝔽q β (ϑ:=ϑ) (h_ℓ_add_R_rate := h_ℓ_add_R_rate)
                (j := k_th_oracleIdx) (point := x_point)
            )
    
            have h_f_i_on_fiber_length: f_i_on_fiber.length = 2 ^ ϑ := by
              sorry
    
            if i > 0 then
              -- cᵢ ?= f^(i)(vᵢ, ..., v_{ℓ+R-1})
              let oracle_point_idx := extractMiddleFinMask 𝔽q β (h_ℓ_add_R_rate := h_ℓ_add_R_rate)
                (v:=v) (i:=⟨i, by exact h_i_lt_ℓ⟩) (steps:=ϑ)
    
              let f_i_val := f_i_on_fiber.get ⟨oracle_point_idx.val, by
                rw [h_f_i_on_fiber_length]; exact oracle_point_idx.isLt⟩
              unless c_cur = f_i_val do

### 2. score 104 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:63
- current: `_ = -1 - 2 * s := by sorry`
- reasons: calc_step_inline_sorry, nearby_arithmetic_tactic, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      calc
        (a + b) ^ 2 = (a - b) ^ 2 + 4 * (a * b) := by sorry -- algebraic rearrangement
        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification
    
    -- Example 1.2.2 from MoP
    example {r s : ℝ} (h1 : s = 3) (h2 : r + 2 * s = -1) : r = -7 :=
      calc
        r = r + 2 * s - 2 * s := by sorry
        _ = -1 - 2 * s := by sorry
        _ = -1 - 2 * 3 := by sorry
        _ = -7 := by sorry
    
    -- rw is "rewrite" - useful for substitution
    -- "algebraic rearrangement" can be accomplished by tactics like simp, ring, linarith, norm_num
    
    
    -- Example 1.2.3 from MoP
    example {a b m n : ℤ} (h1 : a * m + b * n = 1) (h2 : b ^ 2 = 2 * a ^ 2) :

### 3. score 104 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:64
- current: `_ = -1 - 2 * 3 := by sorry`
- reasons: calc_step_inline_sorry, nearby_arithmetic_tactic, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

        (a + b) ^ 2 = (a - b) ^ 2 + 4 * (a * b) := by sorry -- algebraic rearrangement
        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification
    
    -- Example 1.2.2 from MoP
    example {r s : ℝ} (h1 : s = 3) (h2 : r + 2 * s = -1) : r = -7 :=
      calc
        r = r + 2 * s - 2 * s := by sorry
        _ = -1 - 2 * s := by sorry
        _ = -1 - 2 * 3 := by sorry
        _ = -7 := by sorry
    
    -- rw is "rewrite" - useful for substitution
    -- "algebraic rearrangement" can be accomplished by tactics like simp, ring, linarith, norm_num
    
    
    -- Example 1.2.3 from MoP
    example {a b m n : ℤ} (h1 : a * m + b * n = 1) (h2 : b ^ 2 = 2 * a ^ 2) :
        (2 * a * n + b * m) ^ 2 = 2 :=

### 4. score 104 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:65
- current: `_ = -7 := by sorry`
- reasons: calc_step_inline_sorry, nearby_arithmetic_tactic, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification
    
    -- Example 1.2.2 from MoP
    example {r s : ℝ} (h1 : s = 3) (h2 : r + 2 * s = -1) : r = -7 :=
      calc
        r = r + 2 * s - 2 * s := by sorry
        _ = -1 - 2 * s := by sorry
        _ = -1 - 2 * 3 := by sorry
        _ = -7 := by sorry
    
    -- rw is "rewrite" - useful for substitution
    -- "algebraic rearrangement" can be accomplished by tactics like simp, ring, linarith, norm_num
    
    
    -- Example 1.2.3 from MoP
    example {a b m n : ℤ} (h1 : a * m + b * n = 1) (h2 : b ^ 2 = 2 * a ^ 2) :
        (2 * a * n + b * m) ^ 2 = 2 :=
      calc

### 5. score 104 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:77
- current: `_ = 2 * 1 ^ 2 + (m ^ 2 - 2 * n ^ 2) * (2 * a ^ 2 - 2 * a ^ 2) := by sorry`
- reasons: calc_step_inline_sorry, nearby_arithmetic_tactic, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -- "algebraic rearrangement" can be accomplished by tactics like simp, ring, linarith, norm_num
    
    
    -- Example 1.2.3 from MoP
    example {a b m n : ℤ} (h1 : a * m + b * n = 1) (h2 : b ^ 2 = 2 * a ^ 2) :
        (2 * a * n + b * m) ^ 2 = 2 :=
      calc
        (2 * a * n + b * m) ^ 2
          = 2 * (a * m + b * n) ^ 2 + (m ^ 2 - 2 * n ^ 2) * (b ^ 2 - 2 * a ^ 2) := by sorry
        _ = 2 * 1 ^ 2 + (m ^ 2 - 2 * n ^ 2) * (2 * a ^ 2 - 2 * a ^ 2) := by sorry
        _ = 2 := by sorry
    
    -- Example 1.2.4 from MoP
    -- No roadmap for you! Can you figure out how to start?
    example {a b c d e f : ℤ} (h1 : a * d = b * c) (h2 : c * f = d * e) :
        d * (a * f - b * e) = 0 :=
      sorry
    
    -- Inequalities

### 6. score 98 - Verified-zkEVM/ArkLib ArkLib/ProofSystem/Binius/BinaryBasefold/Steps.lean:392
- current: `have h_oStmt : oStmtLast = oStmtOut := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby
- penalties: 

Window:

        rcases h_relOut with ⟨stmtOut, ⟨oStmtOut, h_conj⟩⟩
        have h_simulateQ := h_conj.1
        have h_foldStepRelOut := h_conj.2
        set witLast := (foldRbrExtractor (mp:=mp) 𝔽q β (h_ℓ_add_R_rate := h_ℓ_add_R_rate) i).extractOut
          ⟨stmtLast, oStmtLast⟩ tr witOut
        simp only [Fin.reduceLast, Fin.isValue]
        -- ⊢ foldKStateProp 𝔽q β 2 tr stmtLast witLast oStmtLast
        -- TODO : prove this via the relations between stmtLast & stmtOut,
          -- witLast & witOut, oStmtLast & oStmtOut
        have h_oStmt : oStmtLast = oStmtOut := by sorry
        sorry
    
    /-- RBR knowledge soundness for a single round oracle verifier -/
    theorem foldOracleVerifier_rbrKnowledgeSoundness (i : Fin ℓ) :
        (foldOracleVerifier (mp := mp) 𝔽q β (h_ℓ_add_R_rate := h_ℓ_add_R_rate) i).rbrKnowledgeSoundness
          init impl
          (relIn := roundRelation (mp := mp) 𝔽q β (ϑ := ϑ) (h_ℓ_add_R_rate := h_ℓ_add_R_rate)
             i.castSucc)
          (relOut := foldStepRelOut (mp := mp) 𝔽q β (ϑ := ϑ) (h_ℓ_add_R_rate := h_ℓ_add_R_rate)

### 7. score 97 - Beneficial-AI-Foundation/vericoding-benchmark specs/LA0521_specs.lean:37
- current: `have h_valid : ValidQuery k n a b := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def solve_postcond (queries : List (Int × Int × Int × Int)) (results : List Int) (h_precond : solve_precond queries) : Prop :=
      results.length = queries.length ∧
      (∀ i, 0 ≤ i ∧ i < queries.length → 
        let (k, n, a, b) := queries[i]!
        have h_valid : ValidQuery k n a b := by sorry
        results[i]! = MaxActionATurns k n a b h_valid) ∧
      (∀ i, 0 ≤ i ∧ i < results.length → 
        let (k, n, a, b) := queries[i]!
        have h_valid : ValidQuery k n a b := by sorry
        ValidResult results[i]! k n a b h_valid)
    
    theorem solve_spec_satisfied (queries : List (Int × Int × Int × Int)) (h_precond : solve_precond queries) :
        solve_postcond queries (solve queries h_precond) h_precond := by
      sorry

### 8. score 97 - Beneficial-AI-Foundation/vericoding-benchmark specs/LA0521_specs.lean:41
- current: `have h_valid : ValidQuery k n a b := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

    @[reducible, simp]
    def solve_postcond (queries : List (Int × Int × Int × Int)) (results : List Int) (h_precond : solve_precond queries) : Prop :=
      results.length = queries.length ∧
      (∀ i, 0 ≤ i ∧ i < queries.length → 
        let (k, n, a, b) := queries[i]!
        have h_valid : ValidQuery k n a b := by sorry
        results[i]! = MaxActionATurns k n a b h_valid) ∧
      (∀ i, 0 ≤ i ∧ i < results.length → 
        let (k, n, a, b) := queries[i]!
        have h_valid : ValidQuery k n a b := by sorry
        ValidResult results[i]! k n a b h_valid)
    
    theorem solve_spec_satisfied (queries : List (Int × Int × Int × Int)) (h_precond : solve_precond queries) :
        solve_postcond queries (solve queries h_precond) h_precond := by
      sorry
    -- </vc-theorems>

### 9. score 94 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:126
- current: `_ ≤ (3 + (s + 3) - s) / 2 := by sorry`
- reasons: calc_step_inline_sorry, nearby_arithmetic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -- Note that the powerful linarith tactic proves this in one shot
    example {x y : ℤ} (hx : x + 3 ≤ 2) (hy : y + 2 * x ≥ 3) : y > 3 :=
      calc
        y > 3 := by linarith
    
    -- Example 1.4.2 from MoP
    example {r s : ℚ} (h1 : s + 3 ≥ r) (h2 : s + r ≤ 3) : r ≤ 3 :=
      calc
        r = (s + r + r - s) / 2 := by sorry
        _ ≤ (3 + (s + 3) - s) / 2 := by sorry
        _ = 3 := by sorry
    
    -- Example 1.4.3 from MoP
    -- No "roadmap" for this one - can you figure out how to start?
    example {x y : ℝ} (h1 : y ≤ x + 5) (h2 : x ≤ -2) : x + y < 2 :=
      sorry
    
    
    -- MoP Ch 1 has many more practice problems

### 10. score 94 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:127
- current: `_ = 3 := by sorry`
- reasons: calc_step_inline_sorry, nearby_arithmetic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    example {x y : ℤ} (hx : x + 3 ≤ 2) (hy : y + 2 * x ≥ 3) : y > 3 :=
      calc
        y > 3 := by linarith
    
    -- Example 1.4.2 from MoP
    example {r s : ℚ} (h1 : s + 3 ≥ r) (h2 : s + r ≤ 3) : r ≤ 3 :=
      calc
        r = (s + r + r - s) / 2 := by sorry
        _ ≤ (3 + (s + 3) - s) / 2 := by sorry
        _ = 3 := by sorry
    
    -- Example 1.4.3 from MoP
    -- No "roadmap" for this one - can you figure out how to start?
    example {x y : ℝ} (h1 : y ≤ x + 5) (h2 : x ≤ -2) : x + y < 2 :=
      sorry
    
    
    -- MoP Ch 1 has many more practice problems

### 11. score 88 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:48
- current: `_ = 3 * R := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    A resistor has a resistance of 4 Ohms and a current of 3 Amps flows through it.
    Prove that the voltage across the resistor is 12 Volts.
    -/
    example {v I R : ℝ}
    (h1 : I = 3)
    (h2 : R = 4)
    (h3 : v = I * R) : v = 12 :=
    calc
    v = I * R := by sorry
    _ = 3 * R := by sorry
    _ = 3 * 4 := by sorry
    _ = 12 := by sorry
    
    -- Example 1.2.1 from MoP
    example {a b : ℚ} (h1 : a - b = 4) (h2 : a * b = 1) : (a + b) ^ 2 = 20 :=
      calc
        (a + b) ^ 2 = (a - b) ^ 2 + 4 * (a * b) := by sorry -- algebraic rearrangement
        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification

### 12. score 88 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:49
- current: `_ = 3 * 4 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    Prove that the voltage across the resistor is 12 Volts.
    -/
    example {v I R : ℝ}
    (h1 : I = 3)
    (h2 : R = 4)
    (h3 : v = I * R) : v = 12 :=
    calc
    v = I * R := by sorry
    _ = 3 * R := by sorry
    _ = 3 * 4 := by sorry
    _ = 12 := by sorry
    
    -- Example 1.2.1 from MoP
    example {a b : ℚ} (h1 : a - b = 4) (h2 : a * b = 1) : (a + b) ^ 2 = 20 :=
      calc
        (a + b) ^ 2 = (a - b) ^ 2 + 4 * (a * b) := by sorry -- algebraic rearrangement
        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification

### 13. score 88 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:50
- current: `_ = 12 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -/
    example {v I R : ℝ}
    (h1 : I = 3)
    (h2 : R = 4)
    (h3 : v = I * R) : v = 12 :=
    calc
    v = I * R := by sorry
    _ = 3 * R := by sorry
    _ = 3 * 4 := by sorry
    _ = 12 := by sorry
    
    -- Example 1.2.1 from MoP
    example {a b : ℚ} (h1 : a - b = 4) (h2 : a * b = 1) : (a + b) ^ 2 = 20 :=
      calc
        (a + b) ^ 2 = (a - b) ^ 2 + 4 * (a * b) := by sorry -- algebraic rearrangement
        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification
    
    -- Example 1.2.2 from MoP

### 14. score 88 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:56
- current: `_ = 4 ^ 2 + 4 * 1 := by sorry -- substitution`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    v = I * R := by sorry
    _ = 3 * R := by sorry
    _ = 3 * 4 := by sorry
    _ = 12 := by sorry
    
    -- Example 1.2.1 from MoP
    example {a b : ℚ} (h1 : a - b = 4) (h2 : a * b = 1) : (a + b) ^ 2 = 20 :=
      calc
        (a + b) ^ 2 = (a - b) ^ 2 + 4 * (a * b) := by sorry -- algebraic rearrangement
        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification
    
    -- Example 1.2.2 from MoP
    example {r s : ℝ} (h1 : s = 3) (h2 : r + 2 * s = -1) : r = -7 :=
      calc
        r = r + 2 * s - 2 * s := by sorry
        _ = -1 - 2 * s := by sorry
        _ = -1 - 2 * 3 := by sorry
        _ = -7 := by sorry

### 15. score 88 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:57
- current: `_ = 20 := by sorry -- simplification`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    _ = 3 * R := by sorry
    _ = 3 * 4 := by sorry
    _ = 12 := by sorry
    
    -- Example 1.2.1 from MoP
    example {a b : ℚ} (h1 : a - b = 4) (h2 : a * b = 1) : (a + b) ^ 2 = 20 :=
      calc
        (a + b) ^ 2 = (a - b) ^ 2 + 4 * (a * b) := by sorry -- algebraic rearrangement
        _ = 4 ^ 2 + 4 * 1 := by sorry -- substitution
        _ = 20 := by sorry -- simplification
    
    -- Example 1.2.2 from MoP
    example {r s : ℝ} (h1 : s = 3) (h2 : r + 2 * s = -1) : r = -7 :=
      calc
        r = r + 2 * s - 2 * s := by sorry
        _ = -1 - 2 * s := by sorry
        _ = -1 - 2 * 3 := by sorry
        _ = -7 := by sorry

### 16. score 88 - ATOMSLab/LFSE2024 Lean Code/Lecture6.lean:30
- current: `example : deriv (fun _ => c) x = 0 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
    
    /-
    Thanks to Colin Jones for all these examples!
    https://github.com/Colin166/Lean4/blob/main/DerivEx.lean
    -/
    variable (x y c : ℝ)
    
    /-! Simple goals like these can be solved using `simp?` or `aesop?`. -/
    example : deriv (fun _ => c) x = 0 := by sorry
    
    example : deriv (fun x => x ^ 2) x = 2 * x := by sorry
    
    example : deriv (fun x => log x) x = 1 / x := by sorry
    
    example : deriv (fun x => exp x) x = exp x := by sorry
    
    example : deriv (fun x => sin x) x = cos x := by sorry

### 17. score 87 - Beneficial-AI-Foundation/vericoding-benchmark specs/LT0032_specs.lean:26
- current: `have hi : i < rows := by sorry`
- reasons: direct_have_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

    theorem tril_spec {rows cols : Nat} (m : Vector (Vector Float cols) rows) (k : Int := 0) :
        ⦃⌜True⌝⦄
        tril m k
        ⦃⇓result => ⌜-- Element-wise specification (core property)
                      (∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 
                          if (i : Int) ≥ (j : Int) - k then (m.get i).get j else 0) ∧
                      -- Sanity check: diagonal elements are preserved when k = 0
                      (k = 0 → ∀ i : Fin (min rows cols), 
                        have hi : i < rows := by sorry
                        have hj : i < cols := by sorry
                        (result.get ⟨i, hi⟩).get ⟨i, hj⟩ = (m.get ⟨i, hi⟩).get ⟨i, hj⟩) ∧
                      -- Sanity check: all elements preserved when k is very large
                      (k ≥ (cols : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = (m.get i).get j) ∧
                      -- Sanity check: all elements zeroed when k is very negative
                      (k ≤ -(rows : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 0) ∧
                      -- Idempotency property: tril(tril(m, k), k) = tril(m, k)

### 18. score 87 - Beneficial-AI-Foundation/vericoding-benchmark specs/LT0032_specs.lean:27
- current: `have hj : i < cols := by sorry`
- reasons: direct_have_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

        ⦃⌜True⌝⦄
        tril m k
        ⦃⇓result => ⌜-- Element-wise specification (core property)
                      (∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 
                          if (i : Int) ≥ (j : Int) - k then (m.get i).get j else 0) ∧
                      -- Sanity check: diagonal elements are preserved when k = 0
                      (k = 0 → ∀ i : Fin (min rows cols), 
                        have hi : i < rows := by sorry
                        have hj : i < cols := by sorry
                        (result.get ⟨i, hi⟩).get ⟨i, hj⟩ = (m.get ⟨i, hi⟩).get ⟨i, hj⟩) ∧
                      -- Sanity check: all elements preserved when k is very large
                      (k ≥ (cols : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = (m.get i).get j) ∧
                      -- Sanity check: all elements zeroed when k is very negative
                      (k ≤ -(rows : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 0) ∧
                      -- Idempotency property: tril(tril(m, k), k) = tril(m, k)
                      (∀ (i : Fin rows) (j : Fin cols),

### 19. score 85 - Brkhu/lean P6011/not_used/P6011_old.lean:163
- current: `sorry`
- reasons: direct_have_nextline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: hard_term_Equiv, soft_hard_term_∃

Window:

      -- let P2 : Ideal ℤ := Ideal.span {2}
      -- have h_ramify_2 : ¬ IsUnramifiedAt ℤ (𝓞 F) _ _ _ P2 P2_prime := sorry
    
      -- 通过 (7) 分歧说明 p = 7 整除 Δ_F：
      -- have h_ramify_7 : ¬ ∃ (k : ℤ), f.discr = (7 * k)^2 * NumberField.discr F := sorry
    
      -- 结合以上两点，-588 中不存在使得指数大于 1 的平方因子。
      -- 也就是说 ℤ[y] 已经是极大阶，即 𝓞_F = ℤ[y]
      have h_maximal_order : 𝓞 F = Algebra.adjoin ℤ { (⟨y, hy_integral⟩ : 𝓞 F) } := by
        sorry
    
    
      -- 7. 因为 𝓞_F = ℤ[y] 是极大极大阶，数域 F 的判别式等于多项式 f 的判别式
      have h_discr_eq : NumberField.discr F = f.discr := by
    
        -- 第一种思路: 去到 ℚ 上工作
    
        have h := @IntermediateField.topEquiv ℚ _ F _ _
        rw [NumberField.discr_eq_discr_of_algEquiv F h.symm, ← hy_gen_top]

### 20. score 78 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:78
- current: `_ = 2 := by sorry`
- reasons: calc_step_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
    
    -- Example 1.2.3 from MoP
    example {a b m n : ℤ} (h1 : a * m + b * n = 1) (h2 : b ^ 2 = 2 * a ^ 2) :
        (2 * a * n + b * m) ^ 2 = 2 :=
      calc
        (2 * a * n + b * m) ^ 2
          = 2 * (a * m + b * n) ^ 2 + (m ^ 2 - 2 * n ^ 2) * (b ^ 2 - 2 * a ^ 2) := by sorry
        _ = 2 * 1 ^ 2 + (m ^ 2 - 2 * n ^ 2) * (2 * a ^ 2 - 2 * a ^ 2) := by sorry
        _ = 2 := by sorry
    
    -- Example 1.2.4 from MoP
    -- No roadmap for you! Can you figure out how to start?
    example {a b c d e f : ℤ} (h1 : a * d = b * c) (h2 : c * f = d * e) :
        d * (a * f - b * e) = 0 :=
      sorry
    
    -- Inequalities

### 21. score 78 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:102
- current: `_=m*((v₁ - v₀) / t ):= by sorry`
- reasons: calc_step_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    theorem toy_mouse_force_limit {f :ℝ }
    (h1:v₀=2)
    (h2:v₁=0)
    (h3:m=0.1)
    (h4:t=2)
    (h5:a=(v₁ - v₀) / t)
    (h6:f= m *a) :f < 2 := by
    calc
    f=m * a := by sorry
    _=m*((v₁ - v₀) / t ):= by sorry
    _= 0.1*((0  - 2) / 2 ) := by sorry
    _ < 2 :=by sorry
    
    
    -- Example 1.4.1 from MoP
    -- Introduces the tactic 'rel' for relational substitution
    example {x y : ℤ} (hx : x + 3 ≤ 2) (hy : y + 2 * x ≥ 3) : y > 3 :=
      calc
        y = y + 2 * x - 2 * x := by ring

### 22. score 78 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:103
- current: `_= 0.1*((0  - 2) / 2 ) := by sorry`
- reasons: calc_step_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    (h1:v₀=2)
    (h2:v₁=0)
    (h3:m=0.1)
    (h4:t=2)
    (h5:a=(v₁ - v₀) / t)
    (h6:f= m *a) :f < 2 := by
    calc
    f=m * a := by sorry
    _=m*((v₁ - v₀) / t ):= by sorry
    _= 0.1*((0  - 2) / 2 ) := by sorry
    _ < 2 :=by sorry
    
    
    -- Example 1.4.1 from MoP
    -- Introduces the tactic 'rel' for relational substitution
    example {x y : ℤ} (hx : x + 3 ≤ 2) (hy : y + 2 * x ≥ 3) : y > 3 :=
      calc
        y = y + 2 * x - 2 * x := by ring
        _ ≥ 3 - 2 * x := by rel [hy]

### 23. score 78 - ATOMSLab/LFSE2024 Lean Code/Lecture2.lean:104
- current: `_ < 2 :=by sorry`
- reasons: calc_step_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    (h2:v₁=0)
    (h3:m=0.1)
    (h4:t=2)
    (h5:a=(v₁ - v₀) / t)
    (h6:f= m *a) :f < 2 := by
    calc
    f=m * a := by sorry
    _=m*((v₁ - v₀) / t ):= by sorry
    _= 0.1*((0  - 2) / 2 ) := by sorry
    _ < 2 :=by sorry
    
    
    -- Example 1.4.1 from MoP
    -- Introduces the tactic 'rel' for relational substitution
    example {x y : ℤ} (hx : x + 3 ≤ 2) (hy : y + 2 * x ≥ 3) : y > 3 :=
      calc
        y = y + 2 * x - 2 * x := by ring
        _ ≥ 3 - 2 * x := by rel [hy]
        _ = 9 - 2 * (x + 3) := by ring

### 24. score 75 - Beneficial-AI-Foundation/vericoding-benchmark specs/LT0479_specs.lean:45
- current: `have h_idx : idx < (xdeg + 1) * (ydeg + 1) := by sorry`
- reasons: direct_have_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: hard_term_Polynomial, soft_hard_term_∀

Window:

        2. Each element V[k, (ydeg + 1)*i + j] = L_i(x[k]) * L_j(y[k])
        3. The ordering follows the pattern: (0,0), (0,1), ..., (0,ydeg), (1,0), (1,1), ..., (xdeg,ydeg)
        4. For the first column (i=0, j=0), all values are 1 since L_0(x) * L_0(y) = 1
    -/
    theorem lagvander2d_spec {n : Nat} (x y : Vector Float n) (xdeg ydeg : Nat) :
        ⦃⌜True⌝⦄
        lagvander2d x y xdeg ydeg
        ⦃⇓result => ⌜(∀ k : Fin n, ∀ i : Fin (xdeg + 1), ∀ j : Fin (ydeg + 1),
                        let idx := i.val * (ydeg + 1) + j.val
                        have h_idx : idx < (xdeg + 1) * (ydeg + 1) := by sorry
                        (result.get k).get ⟨idx, h_idx⟩ = 
                          laguerrePolynomial i.val (x.get k) * laguerrePolynomial j.val (y.get k))⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>

### 25. score 75 - Beneficial-AI-Foundation/vericoding-benchmark specs/LT0480_specs.lean:46
- current: `have h_idx : idx < (xdeg + 1) * (ydeg + 1) * (zdeg + 1) := by sorry`
- reasons: direct_have_inline_sorry, relation_symbols_nearby, numeric_context
- penalties: hard_term_Polynomial, soft_hard_term_∀

Window:

        2. Each element V[p, (ydeg+1)*(zdeg+1)*i + (zdeg+1)*j + k] = L_i(x[p]) * L_j(y[p]) * L_k(z[p])
        3. The ordering follows: (0,0,0), (0,0,1), ..., (0,0,zdeg), (0,1,0), ..., (xdeg,ydeg,zdeg)
        4. For the first column (i=0, j=0, k=0), all values are 1 since L_0(x) * L_0(y) * L_0(z) = 1
    -/
    theorem lagvander3d_spec {n : Nat} (x y z : Vector Float n) (xdeg ydeg zdeg : Nat) :
        ⦃⌜True⌝⦄
        lagvander3d x y z xdeg ydeg zdeg
        ⦃⇓result => ⌜(∀ p : Fin n, ∀ i : Fin (xdeg + 1), ∀ j : Fin (ydeg + 1), ∀ k : Fin (zdeg + 1),
                        let idx := i.val * (ydeg + 1) * (zdeg + 1) + j.val * (zdeg + 1) + k.val
                        have h_idx : idx < (xdeg + 1) * (ydeg + 1) * (zdeg + 1) := by sorry
                        (result.get p).get ⟨idx, h_idx⟩ = 
                          laguerrePolynomial i.val (x.get p) * 
                          laguerrePolynomial j.val (y.get p) * 
                          laguerrePolynomial k.val (z.get p))⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>

### 26. score 75 - Brkhu/lean P6011/not_used/P6011_old_check.lean:207
- current: `sorry`
- reasons: direct_have_nextline_sorry, relation_symbols_nearby, numeric_context
- penalties: hard_term_Equiv, soft_hard_term_∃

Window:

      -- let P2 : Ideal ℤ := Ideal.span {2}
      -- have h_ramify_2 : ¬ IsUnramifiedAt ℤ (𝓞 F) _ _ _ P2 P2_prime := sorry
    
      -- 通过 (7) 分歧说明 p = 7 整除 Δ_F：
      -- have h_ramify_7 : ¬ ∃ (k : ℤ), f.discr = (7 * k)^2 * NumberField.discr F := sorry
    
      -- 结合以上两点，-588 中不存在使得指数大于 1 的平方因子。
      -- 也就是说 ℤ[y] 已经是极大阶，即 𝓞_F = ℤ[y]
      have h_maximal_order : 𝓞 F = Algebra.adjoin ℤ { (⟨y, hy_integral⟩ : 𝓞 F) } := by
        sorry
    
    
      -- 7. 因为 𝓞_F = ℤ[y] 是极大极大阶，数域 F 的判别式等于多项式 f 的判别式
      have h_discr_eq : NumberField.discr F = f.discr := by
    
        -- 第一种思路: 去到 ℚ 上工作
    
        -- #check @IntermediateField.topEquiv ℚ _ F _ _
        have h := @IntermediateField.topEquiv ℚ _ F _ _

### 27. score 73 - Brkhu/lean P6011/not_used/P6011_old.lean:180
- current: `have h1 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix b pb.basis i j) := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: hard_term_Matrix, hard_term_Equiv, soft_hard_term_∀

Window:

        have h := @IntermediateField.topEquiv ℚ _ F _ _
        rw [NumberField.discr_eq_discr_of_algEquiv F h.symm, ← hy_gen_top]
    
        qify
        rw [NumberField.coe_discr]
    
        let pb := IntermediateField.adjoin.powerBasis hy_integral'
        let b := integralBasis ℚ⟮y⟯
    
        have h1 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix b pb.basis i j) := by sorry
        have h2 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix pb.basis b i j) := by sorry
    
        rw [Algebra.discr_eq_discr_of_toMatrix_coeff_isIntegral ℚ⟮y⟯ h1 h2]
    
    
    
        sorry
    
      have h_discr_eq' : NumberField.discr F = f.discr := by

### 28. score 73 - Brkhu/lean P6011/not_used/P6011_old.lean:181
- current: `have h2 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix pb.basis b i j) := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: hard_term_Matrix, hard_term_Equiv, soft_hard_term_∀

Window:

        rw [NumberField.discr_eq_discr_of_algEquiv F h.symm, ← hy_gen_top]
    
        qify
        rw [NumberField.coe_discr]
    
        let pb := IntermediateField.adjoin.powerBasis hy_integral'
        let b := integralBasis ℚ⟮y⟯
    
        have h1 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix b pb.basis i j) := by sorry
        have h2 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix pb.basis b i j) := by sorry
    
        rw [Algebra.discr_eq_discr_of_toMatrix_coeff_isIntegral ℚ⟮y⟯ h1 h2]
    
    
    
        sorry
    
      have h_discr_eq' : NumberField.discr F = f.discr := by

### 29. score 73 - Brkhu/lean P6011/not_used/P6011_old_check.lean:232
- current: `have h1 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix b pb.basis i j) := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: hard_term_Matrix, hard_term_Monic, soft_hard_term_∀

Window:

        let pb := IntermediateField.adjoin.powerBasis hy_integral'
        let b := integralBasis ℚ⟮y⟯
    
        -- #check Algebra.discr_powerBasis_eq_norm ℚ pb
        -- #check Algebra.adjoin.powerBasis
        -- #check Algebra.adjoin.powerBasis hy_integral
        -- #check IsAdjoinRootMonic.basis
        -- #check @PowerBasis.ofAdjoinEqTop' ℤ (𝓞 F) _ _ _ _ _ _ _ yO hyO_integral
        -- #check Algebra.discr
        have h1 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix b pb.basis i j) := by sorry
        have h2 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix pb.basis b i j) := by sorry
        -- #check @Algebra.discr_eq_discr_of_toMatrix_coeff_isIntegral (Module.Free.ChooseBasisIndex ℤ (𝓞 ↥ℚ⟮y⟯)) (Fin pb.dim) ℚ⟮y⟯ _ _ _ _ _ _ b pb.basis h1 h2
        -- #check IntermediateField.adjoin.powerBasis hy_integral
    
        rw [Algebra.discr_eq_discr_of_toMatrix_coeff_isIntegral ℚ⟮y⟯ h1 h2]
    
    
    
        sorry

### 30. score 73 - Brkhu/lean P6011/not_used/P6011_old_check.lean:233
- current: `have h2 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix pb.basis b i j) := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: hard_term_Matrix, hard_term_Monic, soft_hard_term_∀

Window:

        let b := integralBasis ℚ⟮y⟯
    
        -- #check Algebra.discr_powerBasis_eq_norm ℚ pb
        -- #check Algebra.adjoin.powerBasis
        -- #check Algebra.adjoin.powerBasis hy_integral
        -- #check IsAdjoinRootMonic.basis
        -- #check @PowerBasis.ofAdjoinEqTop' ℤ (𝓞 F) _ _ _ _ _ _ _ yO hyO_integral
        -- #check Algebra.discr
        have h1 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix b pb.basis i j) := by sorry
        have h2 : ∀ i j, IsIntegral ℤ (Module.Basis.toMatrix pb.basis b i j) := by sorry
        -- #check @Algebra.discr_eq_discr_of_toMatrix_coeff_isIntegral (Module.Free.ChooseBasisIndex ℤ (𝓞 ↥ℚ⟮y⟯)) (Fin pb.dim) ℚ⟮y⟯ _ _ _ _ _ _ b pb.basis h1 h2
        -- #check IntermediateField.adjoin.powerBasis hy_integral
    
        rw [Algebra.discr_eq_discr_of_toMatrix_coeff_isIntegral ℚ⟮y⟯ h1 h2]
    
    
    
        sorry

## Watch candidates

### W1. score 59 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Prop/Double_rounding.lean:715
- current: `sorry`
- reasons: case_sorry, nearby_arithmetic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      (choice1 choice2 : Int → Bool)
      (Hexp : round_round_div_hyp fexp1 fexp2)
      (x y : ℝ)
      (hx_pos : 0 < x) (hy_pos : 0 < y)
      (Fx : generic_format beta fexp1 x) (Fy : generic_format beta fexp1 y)
      (hplace : fexp1 ((FloatSpec.Core.Raux.mag beta (x / y)))
                = (FloatSpec.Core.Raux.mag beta (x / y)) + 1) :
      ¬ ((beta : ℝ) ^ ((FloatSpec.Core.Raux.mag beta (x / y)))
            - (1/2) * (ulp beta fexp2 (x / y)) ≤ x / y) := by
      sorry
    
    /-- Coq: `round_round_div_aux1`
        In the division setting, under `round_round_div_hyp` and assuming
        positivity and genericity hypotheses, the mid-interval above `x/y`
        cannot occur when `fexp1 (mag (x / y)) ≤ mag (x / y)`.
        This is used as a case in the all-mid-cases analysis. -/
    lemma round_round_div_aux1
      (fexp1 fexp2 : Int → Int)
      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp1]

### W2. score 53 - Beneficial-AI-Foundation/vericoding-benchmark specs/LJ0094_specs.lean:23
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    @[reducible, simp]
    def countUppercase_precond (text : Array Char) : Prop := True
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def countUppercase (text : Array Char) (h_precond : countUppercase_precond text) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def countUppercase_postcond (text : Array Char) (count : Nat) (h_precond : countUppercase_precond text) : Prop :=
      count ≤ text.size ∧ countUppercaseRecursively text.toList = count
    
    theorem countUppercase_spec_satisfied (text : Array Char) (h_precond : countUppercase_precond text) :
        countUppercase_postcond text (countUppercase text h_precond) h_precond := by

### W3. score 48 - Beneficial-AI-Foundation/vericoding-benchmark specs/LA0551_specs.lean:21
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby
- penalties: 

Window:

    def solve_precond (input : String) : Prop :=
      True
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def solve (input : String) (_ : solve_precond input) : String :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def solve_postcond (input : String) (result : String) (_ : solve_precond input) : Prop :=
      ValidOutput result ∧ 
      (AllLowercase input → result = "a") ∧
      ((input.length = 0 ∨ ¬AllLowercase input) → result = "A")

### W4. score 48 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF4697_specs.lean:29
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby
- penalties: 

Window:

    
    -- <vc-theorems>
    theorem valid_output_range (town: List String)
      (h1: town.length > 0)
      (h2: listSum (town.map (fun row => countChar row 'P')) = 1)
      : let total_rats := listSum (town.map (fun row =>
          listSum ((DIRS.map Prod.fst).map (fun c => countChar row c))))
        let result := count_deaf_rats town
        0 ≤ result ∧ result ≤ total_rats :=
    sorry
    
    theorem empty_town :
      count_deaf_rats [" P "] = 0 :=
    sorry
    
    theorem simple_case :
      count_deaf_rats ["P →", "← ←"] = 2 :=
    sorry

### W5. score 48 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF4697_specs.lean:44
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby
- penalties: 

Window:

    theorem simple_case :
      count_deaf_rats ["P →", "← ←"] = 2 :=
    sorry
    
    theorem all_directions :
      let dirChars := DIRS.map Prod.fst
      let town := ["P " ++ String.mk dirChars]
      let result := count_deaf_rats town
      0 ≤ result ∧ result ≤ DIRS.length :=
    sorry
    -- </vc-theorems>

### W6. score 47 - Beneficial-AI-Foundation/vericoding-benchmark specs/LJ0098_specs.lean:19
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

    def shift32Spec (c : Char) : Char :=
      Char.ofNat ((c.toNat) + 32)
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def toLowercase (str1 : Array Char) (h_precond : toLowercase_precond (str1)) : Array Char :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def toLowercase_postcond (str1 : Array Char) (result: Array Char) (h_precond : toLowercase_precond (str1)) :=
      str1.size = result.size ∧ 
      (∀ i, i < str1.size → result[i]! = (if isUpperCase (str1[i]!) then shift32Spec (str1[i]!) else str1[i]!))
    
    theorem toLowercase_spec_satisfied (str1: Array Char) (h_precond : toLowercase_precond (str1)) :

### W7. score 47 - Beneficial-AI-Foundation/vericoding-benchmark specs/LJ0114_specs.lean:29
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

    def toUppercase_precond (str1 : Array Char) : Prop :=
      True
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def toUppercase (str1 : Array Char) (h_precond : toUppercase_precond str1) : Array Char :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def toUppercase_postcond (str1 : Array Char) (result : Array Char) (h_precond : toUppercase_precond str1) : Prop :=
      str1.size = result.size ∧ 
      (∀ i : Nat, i < str1.size → result[i]! = innerExprToUppercase str1 i)
    
    theorem toUppercase_spec_satisfied (str1 : Array Char) (h_precond : toUppercase_precond str1) :

### W8. score 47 - Beneficial-AI-Foundation/vericoding-benchmark specs/LT0449_specs.lean:69
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

        where H_j is the j-th Hermite polynomial.
        
        Additionally, we verify the Clenshaw recursion implementation matches
        the mathematical definition. -/
    theorem hermval_spec {m n : Nat} (x : Vector Float m) (c : Vector Float n) :
        ⦃⌜True⌝⦄
        hermval x c
        ⦃⇓result => ⌜∀ i : Fin m,
          result.get i = hermiteSeriesSum c (x.get i)⌝⦄ := by
      sorry
    
    /-- Additional specification for the empty coefficient case -/
    theorem hermval_empty_coeff {m : Nat} (x : Vector Float m) :
        ⦃⌜True⌝⦄
        hermval x (Vector.mk #[] rfl)
        ⦃⇓result => ⌜∀ i : Fin m, result.get i = 0⌝⦄ := by
      sorry
    
    /-- Additional specification for single coefficient (constant polynomial) -/

### W9. score 47 - Beneficial-AI-Foundation/vericoding-benchmark specs/LT0449_specs.lean:76
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

        ⦃⇓result => ⌜∀ i : Fin m,
          result.get i = hermiteSeriesSum c (x.get i)⌝⦄ := by
      sorry
    
    /-- Additional specification for the empty coefficient case -/
    theorem hermval_empty_coeff {m : Nat} (x : Vector Float m) :
        ⦃⌜True⌝⦄
        hermval x (Vector.mk #[] rfl)
        ⦃⇓result => ⌜∀ i : Fin m, result.get i = 0⌝⦄ := by
      sorry
    
    /-- Additional specification for single coefficient (constant polynomial) -/
    theorem hermval_single_coeff {m : Nat} (x : Vector Float m) (c0 : Float) :
        ⦃⌜True⌝⦄
        hermval x (Vector.mk #[c0] rfl)
        ⦃⇓result => ⌜∀ i : Fin m, result.get i = c0⌝⦄ := by
      sorry
    
    /-- Helper function to create a linear combination of two coefficient vectors -/

### W10. score 47 - Beneficial-AI-Foundation/vericoding-benchmark specs/LV0097_specs.lean:17
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

    def isUpperCase (c : Char) : Bool :=
      'A' ≤ c ∧ c ≤ 'Z'
    
    def shift32 (c : Char) : Char :=
      Char.ofNat (c.toNat + 32)
    -- </vc-helpers>
    
    -- <vc-definitions>
    def toLowercase (s : String) (h_precond : toLowercase_precond (s)) : String :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def toLowercase_postcond (s : String) (result: String) (h_precond : toLowercase_precond (s)) :=
      let cs := s.toList
      let cs' := result.toList
      (result.length = s.length) ∧
      (∀ i : Nat, i < s.length →

### W11. score 47 - Beneficial-AI-Foundation/vericoding-benchmark specs/LV0111_specs.lean:17
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

    def isLowerCase (c : Char) : Bool :=
      'a' ≤ c ∧ c ≤ 'z'
    
    def shiftMinus32 (c : Char) : Char :=
      Char.ofNat ((c.toNat - 32) % 128)
    -- </vc-helpers>
    
    -- <vc-definitions>
    def toUppercase (s : String) (h_precond : toUppercase_precond (s)) : String :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def toUppercase_postcond (s : String) (result: String) (h_precond : toUppercase_precond (s)) :=
      let cs := s.toList
      let cs' := result.toList
      (result.length = s.length) ∧
      (∀ i, i < s.length →

### W12. score 47 - Beneficial-AI-Foundation/vericoding-benchmark specs/LV0147_specs.lean:19
- current: `sorry`
- reasons: case_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: soft_hard_term_∀

Window:

        match x[i]?, x[j]? with
        | some ci, some cj =>
          if ci ≠ cj then false else isPalindromeHelper x (i + 1) (j - 1)
        | _, _ => false  -- This case should not occur due to valid indices
      else true
    -- </vc-helpers>
    
    -- <vc-definitions>
    def IsPalindrome (x : List Char) (h_precond : IsPalindrome_precond (x)) : Bool :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    @[reducible, simp]
    def IsPalindrome_postcond (x : List Char) (result: Bool) (h_precond : IsPalindrome_precond (x)) :=
      result ↔ ∀ i : Nat, i < x.length → (x[i]! = x[x.length - i - 1]!)
    
    theorem IsPalindrome_spec_satisfied (x: List Char) (h_precond : IsPalindrome_precond (x)) :
        IsPalindrome_postcond (x) (IsPalindrome (x) h_precond) h_precond := by

### W13. score 46 - Beneficial-AI-Foundation/vericoding-benchmark specs/LT0215_specs.lean:20
- current: `sorry`
- reasons: case_sorry, nearby_refine_apply_exact, relation_symbols_nearby
- penalties: large_window

Window:

      "description": "Save an array to a text file",
      "url": "https://numpy.org/doc/stable/reference/generated/numpy.savetxt.html",
      "doc": "Save an array to a text file",
      "code": "@array_function_dispatch(_savetxt_dispatcher)\ndef savetxt(fname, X, fmt='%.18e', delimiter=' ', newline='\\n', header='',\n            footer='', comments='# ', encoding=None):\n    \"\"\"\n    Save an array to a text file.\n\n    Parameters\n    ----------\n    fname : filename, file handle or pathlib.Path\n        If the filename ends in \`\`.gz\`\`, the file is automatically saved in\n        compressed gzip format.  \`loadtxt\` understands gzipped files\n        transparently.\n    X : 1D or 2D array_like\n        Data to be saved to a text file.\n    fmt : str or sequence of strs, optional\n        A single format (%10.5f), a sequence of formats, or a\n        multi-format string, e.g. 'Iteration %d -- %10.5f', in which\n        case \`delimiter\` is ignored. For complex \`X\`, the legal options\n        for \`fmt\` are:\n\n        * a single specifier, \`\`fmt='%.4e'\`\`, resulting in numbers formatted\n          like \`\`' (%s+%sj)' % (fmt, fmt)\`\`\n        * a full string specifying every real and imaginary part, e.g.\n          \`\`' %.4e %+.4ej %.4e %+.4ej %.4e %+.4ej'\`\` for 3 columns\n        * a list of specifiers, one per column - in this case, the real\n          and imaginary part must have separate specifiers,\n          e.g. \`\`['%.3e + %.3ej', '(%.15e%+.15ej)']\`\` for 2 columns\n    delimiter : str, optional\n        String or character separating columns.\n    newline : str, optional\n        String or character separating lines.\n    header : str, optional\n        String that will be written at the beginning of the file.\n    footer : str, optional\n        String that will be written at the end of the file.\n    comments : str, optional\n        String that will be prepended to the \`\`header\`\` and \`\`footer\`\` strings,\n        to mark them as comments. Default: '# ',  as expected by e.g.\n        \`\`numpy.loadtxt\`\`.\n    encoding : {None, str}, optional\n        Encoding used to encode the outputfile. Does not apply to output\n        streams. If the encoding is something other than 'bytes' or 'latin1'\n        you will not be able to load the file in NumPy versions < 1.14. Default\n        is 'latin1'.\n\n    See Also\n    --------\n    save : Save an array to a binary file in NumPy \`\`.npy\`\` format\n    savez : Save several arrays into an uncompressed \`\`.npz\`\` archive\n    savez_compressed : Save several arrays into a compressed \`\`.npz\`\` archive\n\n    Notes\n    -----\n    Further explanation of the \`fmt\` parameter\n    (\`\`%[flag]width[.precision]specifier\`\`):\n\n    flags:\n        \`\`-\`\` : left justify\n\n        \`\`+\`\` : Forces to precede result with + or -.\n\n        \`\`0\`\` : Left pad the number with zeros instead of space (see width).\n\n    width:\n        Minimum number of characters to be printed. The value is not truncated\n        if it has more characters.\n\n    precision:\n        - For integer specifiers (eg. \`\`d,i,o,x\`\`), the minimum number of\n          digits.\n        - For \`\`e, E\`\` and \`\`f\`\` specifiers, the number of digits to print\n          after the decimal point.\n        - For \`\`g\`\` and \`\`G\`\`, the maximum number of significant digits.\n        - For \`\`s\`\`, the maximum number of characters.\n\n    specifiers:\n        \`\`c\`\` : character\n\n        \`\`d\`\` or \`\`i\`\` : signed decimal integer\n\n        \`\`e\`\` or \`\`E\`\` : scientific notation with \`\`e\`\` or \`\`E\`\`.\n\n        \`\`f\`\` : decimal floating point\n\n        \`\`g,G\`\` : use the shorter of \`\`e,E\`\` or \`\`f\`\`\n\n        \`\`o\`\` : signed octal\n\n        \`\`s\`\` : string of characters\n\n        \`\`u\`\` : unsigned decimal integer\n\n        \`\`x,X\`\` : unsigned hexadecimal integer\n\n    This explanation of \`\`fmt\`\` is not complete, for an exhaustive\n    specification see [1]_.\n\n    References\n    ----------\n    .. [1] \`Format Specification Mini-Language\n           <https://docs.python.org/library/string.html#format-specification-mini-language>\`_,\n           Python Documentation.\n\n    Examples\n    --------\n    >>> import numpy as np\n    >>> x = y = z = np.arange(0.0,5.0,1.0)\n    >>> np.savetxt('test.out', x, delimiter=',')   # X is an array\n    >>> np.savetxt('test.out', (x,y,z))   # x,y,z equal sized 1D arrays\n    >>> np.savetxt('test.out', x, fmt='%1.4e')   # use exponential notation"
    }
    -/
    
    /-- Helper function to format a float according to a format string -/
    def formatFloat (val : Float) (fmt : String) : String :=
      sorry
    
    /-- Helper function to join a list of strings with a delimiter -/
    def joinStrings (strings : List String) (delimiter : String) : String :=
      sorry
    
    /-- Save an array to a text file with specified formatting options.
        This function converts the vector data into a formatted string representation
        that can be written to a file. The delimiter separates elements, and the
        format string controls the numeric representation of each element. -/

### W14. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Core/Ulp.lean:2754
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      -- pred x = -(succ(-x))
      -- succ x = x + ulp x (for x ≥ 0) or -(pred_pos(-x)) (for x < 0)
      -- The key identity pred(succ x) = x follows from the inverse relationship
      -- between succ and pred on format points.
      --
      -- NOTE: The proof requires careful case analysis with ulp_succ_pos_theorem
      -- for x > 0, handling of x = 0 with negligible_exp, and the negative case
      -- which requires succ_pred_pos. These edge cases involve complex interactions
      -- with pred_pos boundary detection. Full proof pending.
      sorry
    
    /-- Coq (Ulp.v):
    Lemma {coq}`pred_succ_pos`:
      {lit}`forall x, F x -> 0 < x -> pred (succ x) = x`.
    -/
    theorem pred_succ_pos
        (x : ℝ)
        (Fx : (FloatSpec.Core.Generic_fmt.generic_format beta fexp x))
        (hx : 0 < x) :

### W15. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Pff/Pff.lean:11169
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
    -- Coq: `digitMore` — |q| < Zpower_nat n (digit q)
    noncomputable def digitMore_check (n : Int) (q : Int) : Unit :=
      ()
    
    theorem digitMore (n : Int) (q : Int) :
        ⦃⌜True⌝⦄
        (pure (digitMore_check n q) : Id Unit)
        ⦃⇓_ => ⌜|q| < Zpower_nat n (digit n q)⌝⦄ := by
      sorry
    
    -- Coq: `digitAuxMore` — complementary case for digit auxiliary
    noncomputable def digitAuxMore_check (n : Int) (v r : Int) (p : Positive) : Unit :=
      ()
    
    theorem digitAuxMore (n : Int) (v r : Int) (p : Positive) :
        ⦃⌜True⌝⦄
        (pure (digitAuxMore_check n v r p) : Id Unit)
        ⦃⇓_ => ⌜match digitAux n v r p with

### W16. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Prop/Double_rounding.lean:160
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      (rnd : ℝ → Int)
      [FloatSpec.Core.Generic_fmt.Valid_rnd rnd]
      (x y : ℝ)
      (Hemin : emin' + prec' ≤ 2 * emin + prec) (Hprec : 2 * prec ≤ prec')
      (Fx : generic_format beta (FTZ_exp emin prec) x)
      (Fy : generic_format beta (FTZ_exp emin prec) y) :
      FloatSpec.Calc.Round.round beta (FTZ_exp emin prec) rnd
        (FloatSpec.Calc.Round.round beta (FTZ_exp emin' prec') rnd (x * y))
      = FloatSpec.Calc.Round.round beta (FTZ_exp emin prec) rnd (x * y) := by
      sorry
    
    
    /-- Coq: `round_round_mid_cases`
        Midpoint case splitter: assuming `0 < x`, a place relation
        `fexp2 (mag x) ≤ fexp1 (mag x) - 1`, and `fexp1 (mag x) ≤ mag x`,
        if the absolute gap to the `fexp1`-midpoint is at most
        `1/2 * ulp fexp2 x`, then double rounding (nearest-on-nearest)
        from `fexp2` to `fexp1` equals a single rounding at `fexp1`. -/
    lemma round_round_mid_cases

### W17. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Prop/Double_rounding.lean:188
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

                    ≤ (FloatSpec.Core.Raux.mag beta x))
      (Cmid : |x - midp (beta := beta) fexp1 x|
                ≤ (1/2) * (ulp beta fexp2 x) →
              FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1)
                (FloatSpec.Calc.Round.round beta fexp2 (Znearest choice2) x)
              = FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1) x) :
      FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1)
        (FloatSpec.Calc.Round.round beta fexp2 (Znearest choice2) x)
      = FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1) x := by
      sorry
    
    /-- Coq: `round_round_eq_mid_beta_even`
        Midpoint equality case under an even-base assumption on `beta`.
        If `x` equals the `fexp1`-midpoint, with `fexp2 (mag x) ≤ fexp1 (mag x) - 1`
        and `fexp1 (mag x) ≤ mag x`, then nearest-on-nearest double rounding
        from `fexp2` to `fexp1` is innocuous. -/
    lemma round_round_eq_mid_beta_even
      (fexp1 fexp2 : Int → Int)
      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp1]

### W18. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Prop/Double_rounding.lean:229
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp2]
      (choice1 choice2 : Int → Bool)
      (x : ℝ)
      (hx_pos : 0 < x)
      (h_f1 : (FloatSpec.Core.Raux.mag beta x)
                ≤ fexp1 ((FloatSpec.Core.Raux.mag beta x)) - 2) :
      FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1)
        (FloatSpec.Calc.Round.round beta fexp2 (Znearest choice2) x)
      = FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1) x := by
      sorry
    
    /-- Coq: `round_round_zero`
        Special case where `fexp1 (mag x) = mag x + 1` and `x` lies strictly
        below `bpow (mag x) - 1/2 * ulp fexp2 x`; double rounding is innocuous. -/
    lemma round_round_zero
      (fexp1 fexp2 : Int → Int)
      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp1]
      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp2]
      (choice1 choice2 : Int → Bool)

### W19. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Prop/Double_rounding.lean:248
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      (x : ℝ)
      (hx_pos : 0 < x)
      (h_f1 : fexp1 ((FloatSpec.Core.Raux.mag beta x))
                = (FloatSpec.Core.Raux.mag beta x) + 1)
      (hx_lt : x < (beta : ℝ) ^ ((FloatSpec.Core.Raux.mag beta x))
                  - (1/2) * (ulp beta fexp2 x)) :
      FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1)
        (FloatSpec.Calc.Round.round beta fexp2 (Znearest choice2) x)
      = FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1) x := by
      sorry
    
    /-- Coq: `round_round_all_mid_cases`
        All-mid-cases splitter used by the division lemmas later: under
        `fexp2 (mag x) ≤ fexp1 (mag x) - 1`, reduce to near-midpoint cases
        or to the equality midpoint case guarded by an even `beta` premise. -/
    lemma round_round_all_mid_cases
      (fexp1 fexp2 : Int → Int)
      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp1]
      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp2]

### W20. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Prop/Double_rounding.lean:1336
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      (x y : ℝ)
      (hy_pos : 0 < y) (hyx : y < x)
      (Hly : (FloatSpec.Core.Raux.mag beta y) ≤ fexp1 ((FloatSpec.Core.Raux.mag beta x)) - 1)
      (Hly' : (FloatSpec.Core.Raux.mag beta y) ≤ fexp1 ((FloatSpec.Core.Raux.mag beta (x - y))) - 1)
      (Fx : generic_format beta fexp1 x)
      (Fy : generic_format beta fexp1 y) :
      FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1)
        (FloatSpec.Calc.Round.round beta fexp2 (Znearest choice2) (x - y))
      = FloatSpec.Calc.Round.round beta fexp1 (Znearest choice1) (x - y) := by
      sorry
    
    /-- Coq: `round_round_minus_radix_ge_3_aux3`
        Combination lemma for the subtraction case under radix-≥3: for
        `0 < y ≤ x` with both operands `fexp1`-generic, nearest-on-nearest
        double rounding of `x - y` collapses to a single rounding at `fexp1`. -/
    lemma round_round_minus_radix_ge_3_aux3
      (Hbeta : 3 ≤ beta)
      (fexp1 fexp2 : Int → Int)
      [FloatSpec.Core.Generic_fmt.Valid_exp beta fexp1]

### W21. score 43 - Beneficial-AI-Foundation/FloatSpec FloatSpec/src/Prop/Double_rounding.lean:1573
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

        `fexp1 (mag x)` and `fexp1 (mag y)`, then the difference of two
        `fexp1`-generic numbers is `fexp2`-generic. -/
    lemma round_round_minus_aux0_aux
      (fexp1 fexp2 : Int → Int)
      (x y : ℝ)
      (Hlnx : fexp2 ((FloatSpec.Core.Raux.mag beta (x - y))) ≤ fexp1 ((FloatSpec.Core.Raux.mag beta x)))
      (Hlny : fexp2 ((FloatSpec.Core.Raux.mag beta (x - y))) ≤ fexp1 ((FloatSpec.Core.Raux.mag beta y)))
      (Fx : generic_format beta fexp1 x) (Fy : generic_format beta fexp1 y) :
      generic_format beta fexp2 (x - y) := by
      sorry
    
    /-- Coq: `round_round_minus_aux0`
        Exact-subtraction case in the largest precision captured by
        `round_round_plus_hyp`. -/
    lemma round_round_minus_aux0
      (fexp1 fexp2 : Int → Int)
      (Hexp : round_round_plus_hyp fexp1 fexp2)
      (x y : ℝ)
      (hy_pos : 0 < y) (hyx : y < x)

### W22. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LD0733_specs.lean:11
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    def IsUpperCase (c : Char) : Bool :=
    65 ≤ c.toNat ∧ c.toNat ≤ 90
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def CountUppercase (s : String) : Int :=
    sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem CountUppercase_spec (s : String) :
    let count := CountUppercase s
    count ≥ 0 ∧
    count = (s.toList.filterMap (fun c => if IsUpperCase c then some c else none)).length
    :=
    sorry

### W23. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0051_specs.lean:17
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    def can_have_no_winner (n k d1 d2 : Nat) : Bool := 
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem no_winner_properties (n k d1 d2 : Nat) :
      (n % 3 ≠ 0 → ¬(can_have_no_winner n k d1 d2 = true)) ∧ 
      (k > n ∨ d1 > n ∨ d2 > n → ¬(can_have_no_winner n k d1 d2 = true)) ∧
      (d1 = 0 ∧ d2 = 0 ∧ k % 3 = 0 ∧ k ≤ n → can_have_no_winner n k d1 d2 = true) :=
      sorry
    
    theorem no_winner_trivial_case (n : Nat) :
      can_have_no_winner n 0 0 0 = true :=
      sorry
    
    theorem no_winner_board_size_multiple_three (n k d1 d2 : Nat) :
      n % 3 ≠ 0 → can_have_no_winner n k d1 d2 = false :=
      sorry

### W24. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0104_specs.lean:9
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def solve_magic_candies (n : Nat) (k : Nat) (candies : List Nat) : Nat :=
      sorry
    
    def list_minimum (l : List Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem solve_magic_candies_minimum_case
      (k : Nat)
      (h1 : k ≥ 1) (h2 : k ≤ 1000) :

### W25. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0104_specs.lean:12
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def solve_magic_candies (n : Nat) (k : Nat) (candies : List Nat) : Nat :=
      sorry
    
    def list_minimum (l : List Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem solve_magic_candies_minimum_case
      (k : Nat)
      (h1 : k ≥ 1) (h2 : k ≤ 1000) :
      solve_magic_candies 2 k [1, 1] = k - 1 :=
    sorry
    -- </vc-theorems>

### W26. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0104_specs.lean:20
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    def list_minimum (l : List Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem solve_magic_candies_minimum_case
      (k : Nat)
      (h1 : k ≥ 1) (h2 : k ≤ 1000) :
      solve_magic_candies 2 k [1, 1] = k - 1 :=
    sorry
    -- </vc-theorems>

### W27. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0127_specs.lean:9
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def max_score_sightseeing_pair (values: List Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem max_score_basic_case (values: List Nat) :
      values = [8,1,5,2,6] → max_score_sightseeing_pair values = 11 :=
      sorry
    
    theorem max_score_min_case (values: List Nat) :
      values = [1,2] → max_score_sightseeing_pair values = 2 :=

### W28. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0263_specs.lean:35
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
      (s.length = n ∨ s.length = 0) ∧
    
      all_chars_abc s ∧
    
      (s.length > 1 → no_adjacent_same s) ∧
    
      ((k > max_possible → s.length = 0) ∧
       (k ≤ max_possible → s.length = n)) :=
    sorry
    
    theorem n1_special_case (k : Nat)
      (h1 : 0 < k) (h2 : k ≤ 10) :
      let s := get_happy_string 1 k
      (k ≤ 3 → (s = "a" ∨ s = "b" ∨ s = "c")) ∧
      (k > 3 → s = "") :=
    sorry
    
    theorem k1_special_case (n : Nat)

### W29. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0263_specs.lean:42
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      ((k > max_possible → s.length = 0) ∧
       (k ≤ max_possible → s.length = n)) :=
    sorry
    
    theorem n1_special_case (k : Nat)
      (h1 : 0 < k) (h2 : k ≤ 10) :
      let s := get_happy_string 1 k
      (k ≤ 3 → (s = "a" ∨ s = "b" ∨ s = "c")) ∧
      (k > 3 → s = "") :=
    sorry
    
    theorem k1_special_case (n : Nat)
      (h1 : 0 < n) (h2 : n ≤ 5) :
      let s := get_happy_string n 1
      s.length = n ∧
      starts_with_a s :=
    sorry
    -- </vc-theorems>

### W30. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0263_specs.lean:49
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      (k ≤ 3 → (s = "a" ∨ s = "b" ∨ s = "c")) ∧
      (k > 3 → s = "") :=
    sorry
    
    theorem k1_special_case (n : Nat)
      (h1 : 0 < n) (h2 : n ≤ 5) :
      let s := get_happy_string n 1
      s.length = n ∧
      starts_with_a s :=
    sorry
    -- </vc-theorems>

### W31. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0292_specs.lean:11
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def Grid := List (List Nat)
    
    def min_cost_to_valid_path (grid: Grid) : Int :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem output_constraints (grid: Grid) :
      let result := min_cost_to_valid_path grid
      result = -1 ∨ result ≥ 0 :=
    sorry
    
    theorem single_cell_case (grid: Grid) :

### W32. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0292_specs.lean:18
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
    def min_cost_to_valid_path (grid: Grid) : Int :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem output_constraints (grid: Grid) :
      let result := min_cost_to_valid_path grid
      result = -1 ∨ result ≥ 0 :=
    sorry
    
    theorem single_cell_case (grid: Grid) :
      grid.length = 1 → 
      (grid.head?.map List.head?).isSome →
      min_cost_to_valid_path grid = 0 :=
    sorry
    
    theorem size_bound (grid: Grid) (h: grid.length ≥ 2) :
      let result := min_cost_to_valid_path grid

### W33. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0417_specs.lean:11
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def M := 10^9 + 7
    
    def count_valid_delivery_orders (n : Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem count_valid_delivery_orders_positive (n : Nat) 
      (h : n > 0) : 
      count_valid_delivery_orders n > 0 :=
      sorry
    
    theorem count_valid_delivery_orders_base_case :

### W34. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0417_specs.lean:18
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
    def count_valid_delivery_orders (n : Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem count_valid_delivery_orders_positive (n : Nat) 
      (h : n > 0) : 
      count_valid_delivery_orders n > 0 :=
      sorry
    
    theorem count_valid_delivery_orders_base_case :
      count_valid_delivery_orders 1 = 1 :=
      sorry
    -- </vc-theorems>

### W35. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0470_specs.lean:27
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      1 ≤ numWays steps arrLen ∧ numWays steps arrLen ≤ 10^9 + 7 :=
      sorry
    
    -- Array length truncation property 
    
    theorem numWays_max_length
      (steps: Nat) (arrLen: Nat) (h1: steps ≥ 1) (h2: arrLen ≥ 1) :
      let maxPos := min arrLen (steps/2 + 1)
      numWays steps arrLen = numWays steps maxPos :=
      sorry
    
    -- Small case properties
    
    theorem numWays_small_cases
      (steps: Nat) (arrLen: Nat) (h1: steps ≥ 1) (h2: steps ≤ 10)
      (h3: arrLen ≥ 2) (h4: arrLen ≤ 10) :
      numWays steps arrLen = numWays steps arrLen ∧ 
      numWays steps arrLen ≥ 1 := 
      sorry

### W36. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0470_specs.lean:36
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      sorry
    
    -- Small case properties
    
    theorem numWays_small_cases
      (steps: Nat) (arrLen: Nat) (h1: steps ≥ 1) (h2: steps ≤ 10)
      (h3: arrLen ≥ 2) (h4: arrLen ≤ 10) :
      numWays steps arrLen = numWays steps arrLen ∧ 
      numWays steps arrLen ≥ 1 := 
      sorry
    
    -- Edge cases
    
    theorem numWays_single_step :
      numWays 1 1 = 1 :=
      sorry
    
    theorem numWays_two_steps_min_array :
      numWays 2 1 = 1 :=

### W37. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0586_specs.lean:18
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

      | [_] => 0 
      | x::y::xs => (if x > y then 1 else 0) + countDescendingPairs (y::xs)
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def findKDescendingPairs (k : Nat) : List Char :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem count_is_k (k : Nat) (k_pos : k > 0) :
      let result := findKDescendingPairs k
      countDescendingPairs result = k :=
    sorry
    
    theorem all_lowercase (k : Nat) (k_pos : k > 0) :

### W38. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0645_specs.lean:18
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    
    def solve_ipl_rooms (p q r : Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem output_in_valid_range (p q r : Nat) (h1 : p > 0) (h2 : q > 0) (h3 : r > 0) :
      let result := solve_ipl_rooms p q r
      0 ≤ result ∧ result < MOD :=
    sorry
    
    theorem empty_when_insufficient_rooms (p q r : Nat) (h1 : p > 0) (h2 : q > 0) (h3 : r > 0) :
      p + q/2 < r → solve_ipl_rooms p q r = 0 :=
    sorry
    
    theorem symmetric_case (n : Nat) (h : n > 0) :
      solve_ipl_rooms n n 1 = solve_ipl_rooms n n 1 :=
    sorry
    -- </vc-theorems>

### W39. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0693_specs.lean:27
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    sorry
    
    theorem single_number_case (x : Int) :
      can_find_odd_multiple 1 [x] = (!isEven x) :=
    sorry
    
    theorem gcd_property {n : Nat} {arr : List Int} :
      n = arr.length →
      can_find_odd_multiple n arr = true ∨ can_find_odd_multiple n arr = false :=
    sorry
    
    theorem parity_preservation {n : Nat} {arr : List Int} :
      can_find_odd_multiple n arr = can_find_odd_multiple n arr :=
    sorry
    -- </vc-theorems>

### W40. score 43 - Beneficial-AI-Foundation/vericoding-benchmark specs/LF0769_specs.lean:9
- current: `sorry`
- reasons: case_sorry, relation_symbols_nearby, numeric_context
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def solve_n_cube (m r : Nat) : Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem solve_n_cube_output_bounds {m r : Nat} (hm : m ≥ 2) (hm2 : m ≤ 5) (hr : r ≥ 2) (hr2 : r ≤ 3) :
      solve_n_cube m r < 1000000007 :=
    sorry
    
    theorem solve_n_cube_base_case {m : Nat} (hm : m ≥ 2) (hm2 : m ≤ 5) :
      solve_n_cube m 2 = 1 :=
