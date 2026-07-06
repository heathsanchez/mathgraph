# MathGraph SorryDB v4.8.23 - Micro Residual Repair Miner

## Purpose

Mine for the now-winning target class:

    residual local obligation after human proof decomposition

This excludes already-promoted PR targets and parked theorem-scale families.

## Counts

- raw rows loaded: 79
- ranked rows: 79
- micro residual candidates score >= 45: 23
- watch candidates score 25..44: 2

## Scoring pattern

Boost:

- local `have ... := by sorry`
- short arithmetic/equality/relation goals
- nearby `omega`, `simp`, `rw`, `nlinarith`, `rfl` context
- decomposed proof comments like requirement/prove
- known FormalBook context

Penalize:

- top-level theorem sorries
- already-promoted PR137/PR138 targets
- parked FormalBook Chapter04/05/07/08/20
- fixed points, bijections, matrices, series, polynomial theorem-scale goals

## Top micro residual candidates

### 1. score 80
- repo: mo271/FormalBook
- path: FormalBook/Chapter_09.lean:615
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal, known_formalbook
- penalties: 
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `⊢ ∑' (k : ℕ), 1 / (2 * ↑k + 1) ^ 2 = Real.pi ^ 2 / 8`

### 2. score 80
- repo: mo271/FormalBook
- path: FormalBook/Chapter_09.lean:619
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal, known_formalbook
- penalties: 
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `⊢ ∑' (n : ℕ+), 1 / ↑↑n = Real.pi ^ 2 / 6`

### 3. score 68
- repo: mo271/FormalBook
- path: FormalBook/Chapter_24.lean:38
- current: `M ∈ doublyStochastic ℝ (Fin n) → permanent M ≥ (n.factorial)/(n ^ n) := sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal, known_formalbook
- penalties: hard_term_Matrix
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `n : ℕ / M : Matrix (Fin n) (Fin n) ℝ / ⊢ M ∈ doublyStochastic ℝ (Fin n) → M.permanent ≥ ↑n.factorial / ↑n ^ n`

### 4. score 60
- repo: dwrensha/compfiles
- path: Compfiles/Imo2016P5.lean:69
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `case h.refine_4 / hp : ∀ (n : ℕ), (n % 4 = 2 ∨ n % 4 = 3) = ¬(n % 4 = 0 ∨ n % 4 = 1) / x : ℝ / ⊢ ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 2 ∨ n % 4 = 3}, (x - ↑i) ≠ /     ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 0 ∨ n % 4 = 1}, (x - ↑i)`

### 5. score 60
- repo: dwrensha/compfiles
- path: Compfiles/Imo2016P5.lean:69
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀
- source: artifacts/sorrydb/v4_8_9_micro_only_queue/micro_queue.json
- goal: `case h.refine_4 / hp : ∀ (n : ℕ), (n % 4 = 2 ∨ n % 4 = 3) = ¬(n % 4 = 0 ∨ n % 4 = 1) / x : ℝ / ⊢ ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 2 ∨ n % 4 = 3}, (x - ↑i) ≠ /     ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 0 ∨ n % 4 = 1}, (x - ↑i)`

### 6. score 60
- repo: dwrensha/compfiles
- path: Compfiles/Imo2016P5.lean:69
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀
- source: artifacts/sorrydb/v4_8_17_safe_next_target_queue/safe_queue.json
- goal: `case h.refine_4 / hp : ∀ (n : ℕ), (n % 4 = 2 ∨ n % 4 = 3) = ¬(n % 4 = 0 ∨ n % 4 = 1) / x : ℝ / ⊢ ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 2 ∨ n % 4 = 3}, (x - ↑i) ≠ /     ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 0 ∨ n % 4 = 1}, (x - ↑i)`

### 7. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2017P6.lean:32
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `S : Finset (ℤ × ℤ) / hS : ∀ s ∈ S, gcd s.1 s.2 = 1 / ⊢ ∃ n, 0 < n ∧ ∃ a, ∀ s ∈ S, ∑ i ∈ Finset.range n, a i * s.1 ^ i * s.2 ^ (n - i) = 1`

### 8. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2017P6.lean:32
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_9_micro_only_queue/micro_queue.json
- goal: `S : Finset (ℤ × ℤ) / hS : ∀ s ∈ S, gcd s.1 s.2 = 1 / ⊢ ∃ n, 0 < n ∧ ∃ a, ∀ s ∈ S, ∑ i ∈ Finset.range n, a i * s.1 ^ i * s.2 ^ (n - i) = 1`

### 9. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2017P6.lean:32
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_17_safe_next_target_queue/safe_queue.json
- goal: `S : Finset (ℤ × ℤ) / hS : ∀ s ∈ S, gcd s.1 s.2 = 1 / ⊢ ∃ n, 0 < n ∧ ∃ a, ∀ s ∈ S, ∑ i ∈ Finset.range n, a i * s.1 ^ i * s.2 ^ (n - i) = 1`

### 10. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2018P5.lean:37
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `a : ℕ → ℤ / apos : ∀ (n : ℕ), 0 < a n / N : ℕ / hN : 0 < N / h : ∀ (n : ℕ), N ≤ n → ∃ z, ↑z = ∑ i ∈ Finset.range n, ↑(a i) / ↑(a ((i + 1) % n)) / ⊢ ∃ M, ∀ (m : ℕ), M ≤ m → a m = a (m + 1)`

### 11. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2018P5.lean:37
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_9_micro_only_queue/micro_queue.json
- goal: `a : ℕ → ℤ / apos : ∀ (n : ℕ), 0 < a n / N : ℕ / hN : 0 < N / h : ∀ (n : ℕ), N ≤ n → ∃ z, ↑z = ∑ i ∈ Finset.range n, ↑(a i) / ↑(a ((i + 1) % n)) / ⊢ ∃ M, ∀ (m : ℕ), M ≤ m → a m = a (m + 1)`

### 12. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2018P5.lean:37
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_17_safe_next_target_queue/safe_queue.json
- goal: `a : ℕ → ℤ / apos : ∀ (n : ℕ), 0 < a n / N : ℕ / hN : 0 < N / h : ∀ (n : ℕ), N ≤ n → ∃ z, ↑z = ∑ i ∈ Finset.range n, ↑(a i) / ↑(a ((i + 1) % n)) / ⊢ ∃ M, ∀ (m : ℕ), M ≤ m → a m = a (m + 1)`

### 13. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2022P3.lean:39
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `k : ℕ / hk : 0 < k / S : Finset ℕ / hS : ∀ p ∈ S, Odd p ∧ Nat.Prime p / p₁ p₂ : Fin S.card ≃ ↥S / hp₁ : Imo2022P3.Condition k S p₁ / hp₂ : Imo2022P3.Condition k S p₂ / ⊢ (∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j + i)) ∨ ∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j.rev + i)`

### 14. score 48
- repo: dwrensha/compfiles
- path: Compfiles/Imo2022P3.lean:39
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_∀, hard_term_∃
- source: artifacts/sorrydb/v4_8_9_micro_only_queue/micro_queue.json
- goal: `k : ℕ / hk : 0 < k / S : Finset ℕ / hS : ∀ p ∈ S, Odd p ∧ Nat.Prime p / p₁ p₂ : Fin S.card ≃ ↥S / hp₁ : Imo2022P3.Condition k S p₁ / hp₂ : Imo2022P3.Condition k S p₂ / ⊢ (∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j + i)) ∨ ∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j.rev + i)`

### 15. score 48
- repo: google-deepmind/formal-imo
- path: Imo/2007/P3.lean:36
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_SimpleGraph, hard_term_∃
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `n : ℕ / C : SimpleGraph (Fin n) / inst✝ : DecidableRel C.Adj / largest_clique_size_in : Finset (Fin n) → ℕ / h₀ : largest_clique_size_in = fun S => {s ∈ S.powerset | C.IsClique ↑s}.sup Finset.card / h₁ : Even (largest_clique_size_in Finset.univ) / ⊢ ∃ R₁ R₂, IsCompl R₁ R₂ ∧ largest_clique_size_in R₁ = largest_clique_size_in R₂`

### 16. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2021P6.lean:15
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `m : ℕ / hm : 2 ≤ m / A : Finset ℤ / B : Fin m → Finset ℤ / hBA : ∀ (i : Fin m), B i ⊆ A / hB : ∀ (k : Fin m), ∑ i ∈ B k, i = ↑m ^ (↑k + 1) / ⊢ ↑m / 2 ≤ ↑A.card`

### 17. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2021P6.lean:15
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_9_micro_only_queue/micro_queue.json
- goal: `m : ℕ / hm : 2 ≤ m / A : Finset ℤ / B : Fin m → Finset ℤ / hBA : ∀ (i : Fin m), B i ⊆ A / hB : ∀ (k : Fin m), ∑ i ∈ B k, i = ↑m ^ (↑k + 1) / ⊢ ↑m / 2 ≤ ↑A.card`

### 18. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2021P6.lean:15
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_17_safe_next_target_queue/safe_queue.json
- goal: `m : ℕ / hm : 2 ≤ m / A : Finset ℤ / B : Fin m → Finset ℤ / hBA : ∀ (i : Fin m), B i ⊆ A / hB : ∀ (k : Fin m), ∑ i ∈ B k, i = ↑m ^ (↑k + 1) / ⊢ ↑m / 2 ≤ ↑A.card`

### 19. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2024P1.lean:15
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `⊢ {α | ∀ (n : ℕ), 0 < n → ↑n ∣ ∑ i ∈ Finset.Icc 1 n, ⌊↑i * α⌋} = IMO2024P1.answer`

### 20. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2024P1.lean:15
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_9_micro_only_queue/micro_queue.json
- goal: `⊢ {α | ∀ (n : ℕ), 0 < n → ↑n ∣ ∑ i ∈ Finset.Icc 1 n, ⌊↑i * α⌋} = IMO2024P1.answer`

### 21. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2024P1.lean:15
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_17_safe_next_target_queue/safe_queue.json
- goal: `⊢ {α | ∀ (n : ℕ), 0 < n → ↑n ∣ ∑ i ∈ Finset.Icc 1 n, ⌊↑i * α⌋} = IMO2024P1.answer`

### 22. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2024P3.lean:22
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_7_target_type_law_next_queue/next_queue.json
- goal: `a : ℕ → ℕ / N : ℕ / h0 : ∀ (i : ℕ), 0 < a i / ha : ∀ (n : ℕ), N < n → a n = {i ∈ Finset.range n | a i = a (n - 1)}.card / ⊢ (IMO2024P3.EventuallyPeriodic fun i => a (2 * i)) ∨ IMO2024P3.EventuallyPeriodic fun i => a (2 * i + 1)`

### 23. score 48
- repo: jsm28/IMOLean
- path: IMO/IMO2024P3.lean:22
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀
- source: artifacts/sorrydb/v4_8_9_micro_only_queue/micro_queue.json
- goal: `a : ℕ → ℕ / N : ℕ / h0 : ∀ (i : ℕ), 0 < a i / ha : ∀ (n : ℕ), N < n → a n = {i ∈ Finset.range n | a i = a (n - 1)}.card / ⊢ (IMO2024P3.EventuallyPeriodic fun i => a (2 * i)) ∨ IMO2024P3.EventuallyPeriodic fun i => a (2 * i + 1)`

## Watch queue

### W1. score 36
- repo: jsm28/IMOLean
- path: IMO/IMO2022P3.lean:21
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀, hard_term_∃
- goal: `k : ℕ / hk : 0 < k / S : Finset ℕ / hS : ∀ p ∈ S, Odd p ∧ Nat.Prime p / p₁ p₂ : Fin S.card ≃ ↥S / hp₁ : IMO2022P3.Condition k S p₁ / hp₂ : IMO2022P3.Condition k S p₂ / ⊢ (∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j + i)) ∨ ∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j.rev + i)`

### W2. score 36
- repo: jsm28/IMOLean
- path: IMO/IMO2022P3.lean:21
- current: `sorry`
- reasons: sorry_on_current_line, short_goal, relation_goal, arithmetic_goal
- penalties: hard_term_IMO202, hard_term_∀, hard_term_∃
- goal: `k : ℕ / hk : 0 < k / S : Finset ℕ / hS : ∀ p ∈ S, Odd p ∧ Nat.Prime p / p₁ p₂ : Fin S.card ≃ ↥S / hp₁ : IMO2022P3.Condition k S p₁ / hp₂ : IMO2022P3.Condition k S p₂ / ⊢ (∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j + i)) ∨ ∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j.rev + i)`
