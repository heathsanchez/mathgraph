# MathGraph SorryDB v4.8.24 - FormalBook Local-Have Scanner

## Purpose

Scan current `mo271/FormalBook` main for the winning target class:

    local `have ... := by sorry` residuals inside already-decomposed proofs

Parked/theorem-scale chapters are excluded.

## Counts

- raw sorry lines scanned: 41
- safe local-have candidates: 14
- watch candidates: 0

## Safe candidates

### 1. score 95 - FormalBook/Chapter_03.lean:158
- current: `sorry`
- reasons: nearby_local_have_by, bare_sorry, nearby_basic_tactic, decomposed_comment, relation_symbols_nearby, nat_int_context
- penalties: 

Window:

        -- STEP (4) : l ≥ 3 by Contradiction
        -- case l ≥ 3
        · have h_3lel : 3 ≤ l := by
            sorry
          -- main work : n < k³
          have h₄ : n < k^3 := by
            sorry
    
          sorry
    
      rcases em (n ≥ 2*k) with h_2k | h
      · exact h_wlog k h_4lek h_klen4 h_2k
      · -- transform ¬(n ≥ 2 * k) into (n < 2 * k)
        simp only [not_le] at h
        -- transform (n.choose k) into (n.choose (n - k))
        have h_klen : k ≤ n := le_trans h_klen4 (Nat.sub_le n 4)
        rw [← choose_symm h_klen]

### 2. score 95 - FormalBook/Chapter_03.lean:173
- current: `sorry`
- reasons: nearby_local_have_by, bare_sorry, nearby_basic_tactic, decomposed_comment, relation_symbols_nearby, nat_int_context
- penalties: 

Window:

        have h_klen : k ≤ n := le_trans h_klen4 (Nat.sub_le n 4)
        rw [← choose_symm h_klen]
        -- define k' as n - k, such that k' can be used for h_wlog as k'
        -- satisfies all required features
        let k' := n - k
        have h_k'_def : k' = n - k := by rfl
        -- third requirement: 2 * k' ≤ n
        have h_2k'len : 2 * k' ≤ n := by
          sorry
        -- second requirement: k ≤ n - 4
        have h_k'len4 : k' ≤ n - 4 := by
          simp only [h_k'_def, tsub_le_iff_right]
          have help : k + k ≤ n - 4 + k := add_le_add_left h_klen4 k
          rw [← (two_mul k)] at help
          exact le_trans (le_of_lt h) help
        -- first requirement: 4 ≤ k
        have h_4lek' : 4 ≤ k' := Iff.mp (le_tsub_iff_le_tsub h_klen (le_trans (le_trans h_4lek h_klen4)

### 3. score 89 - FormalBook/Chapter_03.lean:153
- current: `sorry`
- reasons: nearby_local_have_by, bare_sorry, nearby_basic_tactic, decomposed_comment, relation_symbols_nearby
- penalties: 

Window:

        --have h₃ : a_values l n k = s_1tok k := by
        -- divide in two cases
        cases em (l = 2)
        -- Special Case l = 2 by Contradiction
        ·  sorry
        -- STEP (4) : l ≥ 3 by Contradiction
        -- case l ≥ 3
        · have h_3lel : 3 ≤ l := by
            sorry
          -- main work : n < k³
          have h₄ : n < k^3 := by
            sorry
    
          sorry
    
      rcases em (n ≥ 2*k) with h_2k | h
      · exact h_wlog k h_4lek h_klen4 h_2k

### 4. score 89 - FormalBook/Chapter_03.lean:156
- current: `sorry`
- reasons: nearby_local_have_by, bare_sorry, nearby_basic_tactic, decomposed_comment, relation_symbols_nearby
- penalties: 

Window:

        -- Special Case l = 2 by Contradiction
        ·  sorry
        -- STEP (4) : l ≥ 3 by Contradiction
        -- case l ≥ 3
        · have h_3lel : 3 ≤ l := by
            sorry
          -- main work : n < k³
          have h₄ : n < k^3 := by
            sorry
    
          sorry
    
      rcases em (n ≥ 2*k) with h_2k | h
      · exact h_wlog k h_4lek h_klen4 h_2k
      · -- transform ¬(n ≥ 2 * k) into (n < 2 * k)
        simp only [not_le] at h
        -- transform (n.choose k) into (n.choose (n - k))

### 5. score 89 - FormalBook/Chapter_06.lean:296
- current: `sorry`
- reasons: nearby_local_have_by, bare_sorry, nearby_arithmetic_tactic, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: hard_term_Polynomial

Window:

        simp only [map_cyclotomic]
        have := isPrimitiveRoot_exp n h_n
        rw [cyclotomic_eq_prod_X_sub_primitiveRoots this]
    
      have : 2 ≤ q := Fintype.one_lt_card_iff.mpr (exists_pair_ne { x // x ∈ Z })
      -- here the book uses h_lamb_gt_q_sub_one from above
      have h_gt : ((cyclotomic n ℤ).eval ↑q).natAbs > q - 1 := by
        have hn : 1 < n := by
          sorry
        have hq : q ≠ 1 := by exact Nat.ne_of_gt this
        exact Polynomial.sub_one_lt_natAbs_cyclotomic_eval hn hq
    
      have h_q_sub_one : 0 ≠ (q : ℤ) - 1 := by
        have h1 : (q : ℤ) - 1 = (q - 1 : ℕ) := by
          rw [Int.ofNat_sub $ le_of_lt this]
          norm_num
        rw [h1]

### 6. score 82 - FormalBook/Chapter_06.lean:87
- current: `have : Real.sqrt (((q:ℝ) - 1) ^ 2) = ((q : ℝ) - 1) := by sorry`
- reasons: nearby_local_have_by, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: 

Window:

            --simp only [eval_sub, eval_X, eval_C, norm_eq_abs]
          _ = ‖(q : ℂ) - a - I*b‖^2 := by sorry
          _ = ‖(q : ℂ) - a‖^2 + ‖b‖^2 := by sorry
          _ = (q : ℝ)^2 - 2*‖a‖*q + ‖a‖^2 + ‖b‖^2 := by sorry
          _ > ((q : ℝ) - 1)^2 := by sorry
    
      have : 0 ≤ ((q : ℝ) - 1)^2 := sq_nonneg ((q : ℝ) - 1)
      have g := (Real.sqrt_lt_sqrt_iff (sq_nonneg ((q : ℝ) - 1))).mpr (h_ineq)
      have : Real.sqrt (((q:ℝ) - 1) ^ 2) = ((q : ℝ) - 1) := by sorry
      rw [this, Real.sqrt_sq] at g
      · exact g
      · sorry
    
    lemma div_of_qpoly_div (k n q : ℕ) (hq : 1 < q) (hk : 0 < k) (hn : 0 < n)
        (H : q ^ k - 1 ∣ q ^ n - 1) : k ∣ n := by
      revert H
      revert hn

### 7. score 76 - FormalBook/Chapter_06.lean:78
- current: `_ = ‖q - lamb‖^2 := by sorry`
- reasons: nearby_local_have_by, nearby_basic_tactic, relation_symbols_nearby
- penalties: 

Window:

      let a := lamb.re
      let b := lamb.im
      intro h
      have h_lamb: lamb ≠ 1 := by sorry
      have h_a_lt_one: ‖a‖ < 1 := by sorry
      have h_ineq :
          ‖((X - C lamb).eval (q : ℂ))‖^2 > ((q : ℝ) - 1)^2  := by
        calc
          _ = ‖q - lamb‖^2 := by sorry
            --simp only [eval_sub, eval_X, eval_C, norm_eq_abs]
          _ = ‖(q : ℂ) - a - I*b‖^2 := by sorry
          _ = ‖(q : ℂ) - a‖^2 + ‖b‖^2 := by sorry
          _ = (q : ℝ)^2 - 2*‖a‖*q + ‖a‖^2 + ‖b‖^2 := by sorry
          _ > ((q : ℝ) - 1)^2 := by sorry
    
      have : 0 ≤ ((q : ℝ) - 1)^2 := sq_nonneg ((q : ℝ) - 1)
      have g := (Real.sqrt_lt_sqrt_iff (sq_nonneg ((q : ℝ) - 1))).mpr (h_ineq)

### 8. score 72 - FormalBook/Chapter_03.lean:149
- current: `·  sorry`
- reasons: nearby_local_have_by, decomposed_comment, relation_symbols_nearby, nat_int_context
- penalties: hard_term_∀

Window:

        --have h₂ : ∀ j, (j ≤ k - 1) ∧ (∀ (q : ℕ), q ∣ (aFct l n j) ∧ prime q → q ≤ k) ∧
        --    (∀ i ≤ k - 1, i ≠ j → (aFct l n i) ≠ (aFct l n j)) := by
        -- sorry
        -- Step (3) : a_i are integers 1..k
        --have h₃ : a_values l n k = s_1tok k := by
        -- divide in two cases
        cases em (l = 2)
        -- Special Case l = 2 by Contradiction
        ·  sorry
        -- STEP (4) : l ≥ 3 by Contradiction
        -- case l ≥ 3
        · have h_3lel : 3 ≤ l := by
            sorry
          -- main work : n < k³
          have h₄ : n < k^3 := by
            sorry

### 9. score 72 - FormalBook/Chapter_06.lean:74
- current: `have h_a_lt_one: ‖a‖ < 1 := by sorry`
- reasons: nearby_local_have_by, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: hard_term_Polynomial

Window:

    -- this is currently not needed, because we use Polynomial.sub_one_lt_natAbs_cyclotomic_eval,
    -- TODO: add it later to stay close to the proof in the book.
    theorem h_lamb_gt_q_sub_one (q n : ℕ) (lamb : ℂ):
      lamb ∈ (primitiveRoots n ℂ) → ‖(X - (C lamb)).eval (q : ℂ)‖ > (q - 1) := by
      let a := lamb.re
      let b := lamb.im
      intro h
      have h_lamb: lamb ≠ 1 := by sorry
      have h_a_lt_one: ‖a‖ < 1 := by sorry
      have h_ineq :
          ‖((X - C lamb).eval (q : ℂ))‖^2 > ((q : ℝ) - 1)^2  := by
        calc
          _ = ‖q - lamb‖^2 := by sorry
            --simp only [eval_sub, eval_X, eval_C, norm_eq_abs]
          _ = ‖(q : ℂ) - a - I*b‖^2 := by sorry
          _ = ‖(q : ℂ) - a‖^2 + ‖b‖^2 := by sorry
          _ = (q : ℝ)^2 - 2*‖a‖*q + ‖a‖^2 + ‖b‖^2 := by sorry

### 10. score 72 - FormalBook/Chapter_06.lean:90
- current: `· sorry`
- reasons: nearby_local_have_by, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: hard_term_∀

Window:

          _ = (q : ℝ)^2 - 2*‖a‖*q + ‖a‖^2 + ‖b‖^2 := by sorry
          _ > ((q : ℝ) - 1)^2 := by sorry
    
      have : 0 ≤ ((q : ℝ) - 1)^2 := sq_nonneg ((q : ℝ) - 1)
      have g := (Real.sqrt_lt_sqrt_iff (sq_nonneg ((q : ℝ) - 1))).mpr (h_ineq)
      have : Real.sqrt (((q:ℝ) - 1) ^ 2) = ((q : ℝ) - 1) := by sorry
      rw [this, Real.sqrt_sq] at g
      · exact g
      · sorry
    
    lemma div_of_qpoly_div (k n q : ℕ) (hq : 1 < q) (hk : 0 < k) (hn : 0 < n)
        (H : q ^ k - 1 ∣ q ^ n - 1) : k ∣ n := by
      revert H
      revert hn
      have : ∀ (n : ℕ), (∀ m < n, 0 < m → q ^ k - 1 ∣ q ^ m - 1 → k ∣ m) →
          0 < n → q ^ k - 1 ∣ q ^ n - 1 → k ∣ n := by
        intro m h hm H

### 11. score 72 - FormalBook/Chapter_06.lean:260
- current: `have h_one_neq: 1 ≠ n_k A := by sorry`
- reasons: nearby_local_have_by, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: hard_term_Fintype.card

Window:

      --rest of proof
      have h_phi_dvd_q_sub_one : (phi n).eval (q : ℤ) ∣ (((q - (1 : ℕ)) : ℕ ) : ℤ) := by
        have hq : q = (Fintype.card { x // x ∈ center R }) := by rfl
        have h₁_dvd : (phi n).eval (q : ℤ) ∣ ((X : ℤ[X])  ^ n - 1).eval (q : ℤ)  := by
          exact eval_dvd <| phi_dvd n
        have h₂_dvd :
            (phi n).eval (q : ℤ) ∣ ∑ A : S', (((q ^ n - 1) : ℕ):ℤ) / ((q ^ (n_k A) - 1) : ℕ):= by
          refine Finset.dvd_sum fun A hs ↦ (Int.dvd_div_of_mul_dvd ?_)
          have h_one_neq: 1 ≠ n_k A := by sorry
          have h_k_n_lt_n: n_k A < n := by sorry
          have h_noneval := phi_div_2 n (n_k A) (h_n_k_A_dvd A) h_k_n_lt_n
          have := @eval_dvd ℤ _ _ _ q h_noneval
          simp only [eval_mul, eval_sub, eval_pow, eval_X, eval_one, IsUnit.mul_iff] at this
          rw [← hq] at *
          convert this
          · simp [hq_pow_pos <| n_k A]
          · simp [hq_pow_pos n]

### 12. score 72 - FormalBook/Chapter_06.lean:261
- current: `have h_k_n_lt_n: n_k A < n := by sorry`
- reasons: nearby_local_have_by, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: hard_term_Fintype.card

Window:

      have h_phi_dvd_q_sub_one : (phi n).eval (q : ℤ) ∣ (((q - (1 : ℕ)) : ℕ ) : ℤ) := by
        have hq : q = (Fintype.card { x // x ∈ center R }) := by rfl
        have h₁_dvd : (phi n).eval (q : ℤ) ∣ ((X : ℤ[X])  ^ n - 1).eval (q : ℤ)  := by
          exact eval_dvd <| phi_dvd n
        have h₂_dvd :
            (phi n).eval (q : ℤ) ∣ ∑ A : S', (((q ^ n - 1) : ℕ):ℤ) / ((q ^ (n_k A) - 1) : ℕ):= by
          refine Finset.dvd_sum fun A hs ↦ (Int.dvd_div_of_mul_dvd ?_)
          have h_one_neq: 1 ≠ n_k A := by sorry
          have h_k_n_lt_n: n_k A < n := by sorry
          have h_noneval := phi_div_2 n (n_k A) (h_n_k_A_dvd A) h_k_n_lt_n
          have := @eval_dvd ℤ _ _ _ q h_noneval
          simp only [eval_mul, eval_sub, eval_pow, eval_X, eval_one, IsUnit.mul_iff] at this
          rw [← hq] at *
          convert this
          · simp [hq_pow_pos <| n_k A]
          · simp [hq_pow_pos n]
        simp only [eval_sub, eval_pow, eval_X, eval_one] at h₁_dvd

### 13. score 67 - FormalBook/Chapter_06.lean:247
- current: `sorry`
- reasons: nearby_local_have_by, bare_sorry, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: hard_term_Fintype.card, hard_term_∀

Window:

    
      -- Orbit stabilizer formula for non-singleton conjugacy classes
      have : ∀ A : S', (Fintype.card <| ConjClasses.carrier (A : ConjClasses Rˣ)) * (q ^ (n_k A) - 1)
          = q ^ n - 1 := by
        sorry
    
      have h1 : (q ^ n - 1) = q - 1  + ∑ A : S', (q ^ n - 1) / (q ^ (n_k A) - 1) := by
        convert H1
        sorry
      have hZ : Nonempty <| @Subtype R fun x => x ∈ Z := Zero.instNonempty
      have hq_pow_pos : ∀ m,  1 ≤ q ^ m := fun m ↦ one_le_pow m q Fintype.card_pos
    
      have h_n_k_A_dvd: ∀ A : S', (n_k A ∣ n) := by sorry
      --rest of proof
      have h_phi_dvd_q_sub_one : (phi n).eval (q : ℤ) ∣ (((q - (1 : ℕ)) : ℕ ) : ℤ) := by
        have hq : q = (Fintype.card { x // x ∈ center R }) := by rfl
        have h₁_dvd : (phi n).eval (q : ℤ) ∣ ((X : ℤ[X])  ^ n - 1).eval (q : ℤ)  := by

### 14. score 62 - FormalBook/Chapter_06.lean:251
- current: `have h_n_k_A_dvd: ∀ A : S', (n_k A ∣ n) := by sorry`
- reasons: nearby_local_have_by, nearby_basic_tactic, relation_symbols_nearby, nat_int_context
- penalties: hard_term_Fintype.card, hard_term_∀

Window:

        sorry
    
      have h1 : (q ^ n - 1) = q - 1  + ∑ A : S', (q ^ n - 1) / (q ^ (n_k A) - 1) := by
        convert H1
        sorry
      have hZ : Nonempty <| @Subtype R fun x => x ∈ Z := Zero.instNonempty
      have hq_pow_pos : ∀ m,  1 ≤ q ^ m := fun m ↦ one_le_pow m q Fintype.card_pos
    
      have h_n_k_A_dvd: ∀ A : S', (n_k A ∣ n) := by sorry
      --rest of proof
      have h_phi_dvd_q_sub_one : (phi n).eval (q : ℤ) ∣ (((q - (1 : ℕ)) : ℕ ) : ℤ) := by
        have hq : q = (Fintype.card { x // x ∈ center R }) := by rfl
        have h₁_dvd : (phi n).eval (q : ℤ) ∣ ((X : ℤ[X])  ^ n - 1).eval (q : ℤ)  := by
          exact eval_dvd <| phi_dvd n
        have h₂_dvd :
            (phi n).eval (q : ℤ) ∣ ∑ A : S', (((q ^ n - 1) : ℕ):ℤ) / ((q ^ (n_k A) - 1) : ℕ):= by
          refine Finset.dvd_sum fun A hs ↦ (Int.dvd_div_of_mul_dvd ?_)

## Watch candidates
