# MathGraph SorryDB v4.8.17 — Safe Next Target Queue

## Purpose

Remove targets that previous evidence shows are not micro-repairs.

## Excluded families

- FormalBook Chapter 04: parked dependent-subtype involution parity boundary.
- FormalBook Chapter 05: false/Legendre/Fermat-adjacent risk.
- FormalBook Chapter 07: matrix/spectral theorem-scale.
- FormalBook Chapter 08: exp series/factorial theorem-scale.
- FormalBook Chapter 20: AM-GM/HM theorem-scale.

## Counts

- safe targets: 9
- excluded targets: 21

## Safe queue

### micro_score 46 — rank 46 score 48
- id: e3495f5c9e15a09f8fb227dc09c18272f2f5952aebbbc2dd2a2f8059a1ec314d
- repo: mo271/FormalBook
- path: FormalBook/Chapter_03.lean:153
- current line: `        sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `l m n : ℕ / h_2lel : 2 ≤ l / k : ℕ / h_4lek : 4 ≤ k / h_klen4 : k ≤ n - 4 / h : 2 * k ≤ n / h_klen : k ≤ n / h_1lel : 1 ≤ l / H : n.choose k = m ^ l / h₁ : ∃ p, Nat.Prime p ∧ p ^ l ≤ n ∧ k ^ l < p ^ l ∧ k ^ 2 ≤ k ^ l / h✝ : ¬l = 2 / ⊢ 3 ≤ l`

### micro_score 46 — rank 47 score 48
- id: bfad037cde20475fabf127cc96ef202f7cdc6ab019ba5d3e387fc4b6ce4c5b21
- repo: mo271/FormalBook
- path: FormalBook/Chapter_03.lean:173
- current line: `      sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `k l m n : ℕ / h_2lel : 2 ≤ l / h_4lek : 4 ≤ k / h_klen4 : k ≤ n - 4 / h_wlog : ∀ (k' : ℕ), 4 ≤ k' → k' ≤ n - 4 → 2 * k' ≤ n → n.choose k' ≠ m ^ l / h : n < 2 * k / h_klen : k ≤ n / k' : ℕ := n - k / h_k'_def : k' = n - k / ⊢ 2 * k' ≤ n`

### micro_score 45 — rank 70 score 46
- id: 370d81df19a05812cf92b2e173e4df4a50ee669023e531d14b5e89309727ca49
- repo: jsm28/IMOLean
- path: IMO/IMO2021P6.lean:15
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context
- goal: `m : ℕ / hm : 2 ≤ m / A : Finset ℤ / B : Fin m → Finset ℤ / hBA : ∀ (i : Fin m), B i ⊆ A / hB : ∀ (k : Fin m), ∑ i ∈ B k, i = ↑m ^ (↑k + 1) / ⊢ ↑m / 2 ≤ ↑A.card`

### micro_score 40 — rank 60 score 46
- id: e274e715813c128bb0b34f05fcbad0206ad018e5a8b22dbb7906231f5dd6c76b
- repo: dwrensha/compfiles
- path: Compfiles/Imo2023P3.lean:39
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context
- goal: `k : ℕ / hk : 2 ≤ k / a : ℕ+ → ℕ+ / ⊢ a ∈ Imo2023P3.SolutionSet k hk ↔ /     ∃ P, /       P.Monic ∧ /         P.degree = ↑k ∧ /           (∀ n ≤ k, 0 ≤ P.coeff n) ∧ /             ∀ (n : ℕ+), Polynomial.eval (↑↑(a n)) P = ↑↑(∏ i ∈ Finset.range k, a ⟨↑n + i + 1, ⋯⟩)`

### micro_score 40 — rank 64 score 46
- id: 9c44352afd07ad4a915b781d2993bdab5820ec33f22ff13634c0a756d3e2eafd
- repo: dwrensha/compfiles
- path: Compfiles/Imo2018P5.lean:37
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context
- goal: `a : ℕ → ℤ / apos : ∀ (n : ℕ), 0 < a n / N : ℕ / hN : 0 < N / h : ∀ (n : ℕ), N ≤ n → ∃ z, ↑z = ∑ i ∈ Finset.range n, ↑(a i) / ↑(a ((i + 1) % n)) / ⊢ ∃ M, ∀ (m : ℕ), M ≤ m → a m = a (m + 1)`

### micro_score 40 — rank 65 score 46
- id: c9f848ad84eb3e477e5e10ce2a09daf49eb61f0f3dcffa8ac4b31c9cb30215be
- repo: dwrensha/compfiles
- path: Compfiles/Imo2017P6.lean:32
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context
- goal: `S : Finset (ℤ × ℤ) / hS : ∀ s ∈ S, gcd s.1 s.2 = 1 / ⊢ ∃ n, 0 < n ∧ ∃ a, ∀ s ∈ S, ∑ i ∈ Finset.range n, a i * s.1 ^ i * s.2 ^ (n - i) = 1`

### micro_score 40 — rank 68 score 46
- id: 97bd69736a277c80081d2194de7c55c92f84969b7e4761bd62894be46b68d048
- repo: jsm28/IMOLean
- path: IMO/IMO2023P3.lean:19
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context
- goal: `⊢ (fun k => /       {a | /         (∀ (i : ℕ), 0 < a i) ∧ /           ∃ P, /             P.Monic ∧ P.degree = ↑↑k ∧ ∀ (n : ℕ), Polynomial.eval (a n) P = ∏ i ∈ Finset.Icc (n + 1) (n + ↑k), a i}) = /     IMO2023P3.answer`

### micro_score 40 — rank 71 score 46
- id: 69c604791ac0724139ed2090446c0136588fe18f96d32e8bd1e4061ebe391eea
- repo: jsm28/IMOLean
- path: IMO/IMO2024P1.lean:15
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context
- goal: `⊢ {α | ∀ (n : ℕ), 0 < n → ↑n ∣ ∑ i ∈ Finset.Icc 1 n, ⌊↑i * α⌋} = IMO2024P1.answer`

### micro_score 32 — rank 66 score 46
- id: 1eb3a5430ac4a81ae6fad5345fdc09342737ec30147070aa9d5d45d47b9ebaeb
- repo: dwrensha/compfiles
- path: Compfiles/Imo2016P5.lean:69
- current line: `      sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, universal_theorem_risk
- goal: `case h.refine_4 / hp : ∀ (n : ℕ), (n % 4 = 2 ∨ n % 4 = 3) = ¬(n % 4 = 0 ∨ n % 4 = 1) / x : ℝ / ⊢ ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 2 ∨ n % 4 = 3}, (x - ↑i) ≠ /     ∏ i ∈ Finset.Icc 1 2016 \ {n ∈ Finset.Icc 1 2016 | n % 4 = 0 ∨ n % 4 = 1}, (x - ↑i)`
