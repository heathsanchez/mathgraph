# MathGraph SorryDB v4.8.9 — Micro-Only Queue

## Purpose

After Chapter04 `sameCard` failed simple probes, sharpen queue toward local proof repairs rather than theorem-scale targets.

## Exclusions

- already solved/probed targets
- full theorem-scale statements
- known false Chapter05 Fermat-minus-one trap
- AM-GM/HM, exp series, matrix spectral, Legendre/quadratic reciprocity, graph labeling

## Queue

### micro_score 81 — rank 2 score 59
- id: 63db8ffc0199cc1a713aeb07f33c5fcf900a66b1af2ab8a71cc96740cc9dd99b
- repo: mo271/FormalBook
- path: FormalBook/Chapter_05.lean:53
- current line: `  have : units_finset = image_finset := by sorry`
- reasons: sorry_on_current_line, single_by_sorry_line, local_have_sorry, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / units_finset : Finset (ZMod p) := univ.erase 0 / image_finset : Finset (ZMod p) := image (fun x => ↑a * x) units_finset / ⊢ units_finset = image_finset`

### micro_score 61 — rank 80 score 46
- id: 3f4ef9e3cfcb5ab03b7b0e0387a4f687a6c7f5c0a8570e52e0d8e8b42e24c8c3
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:287
- current line: `theorem trivialInvo_fixedPoints : (fixedPoints (trivialInvo k)).Nonempty := by sorry`
- reasons: sorry_on_current_line, single_by_sorry_line, short_goal, arithmetic_context, known_formalbook
- goal: `k : ℕ / hk : Fact (Nat.Prime (4 * k + 1)) / ⊢ (fixedPoints (ch04.trivialInvo k)).Nonempty`

### micro_score 51 — rank 42 score 48
- id: 904966eb43ab8d49d0ccb2bc98ae6aa019b66643b56ac6447298be0a3a8eb6db
- repo: mo271/FormalBook
- path: FormalBook/Chapter_05.lean:104
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context, known_formalbook
- goal: `p q : ℕ / hp : p ≠ 2 / hq : q ≠ 2 / inst✝³ : Fact (Nat.Prime p) / inst✝² : Fact (Nat.Prime q) / h_pq : p ≠ q / K : Type u_1 / inst✝¹ : Field K / inst✝ : Fintype K / H : Fintype.card K = q ^ (p - 1) / ⊢ ∀ (a b : K), (a + b) ^ q = a ^ q + b ^ q`

### micro_score 51 — rank 43 score 48
- id: 6efe22035b6d2b8a940d3b739225fa4daf690e311ada66793f66edd825e9054f
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:48
- current line: `  · sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context, known_formalbook
- goal: `case left / p : ℕ / h : Fact (Nat.Prime p) / ⊢ ∃ m, p = 4 * m + 1 → {s | s ^ 2 = -1}.card = 2`

### micro_score 51 — rank 44 score 48
- id: 902e699746fa16082ff6bede94130834cc8c8f9b2d42f496487c4920fa3ea4df
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:53
- current line: `    · sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context, known_formalbook
- goal: `case right.right / p : ℕ / h : Fact (Nat.Prime p) / ⊢ ∃ m, p = 4 * m + 1 → {s | s ^ 2 = -1}.card = 0`

### micro_score 46 — rank 3 score 59
- id: 1d90823a9b08f76f3b0edc5bda1886cc28d47c4f846b149aeb6e1666efbac94f
- repo: mo271/FormalBook
- path: FormalBook/Chapter_05.lean:54
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / units_finset : Finset (ZMod p) := univ.erase 0 / image_finset : Finset (ZMod p) := image (fun x => ↑a * x) units_finset / this : units_finset = image_finset / ⊢ ↑a ≠ 0 → ↑a ^ (p - 1) = -1`

### micro_score 46 — rank 10 score 51
- id: fcd7001b7b076fe7885f3358723d519d3b14e481b2439a23f90b98b5f7f9f99f
- repo: mo271/FormalBook
- path: FormalBook/Chapter_05.lean:113
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `p : ℕ / inst✝¹ : Fact (Prime p) / K : Type u_1 / inst✝ : Field K / ζ : Kˣ / h_1 : ζ ^ p = 1 / h_2 : ζ ≠ 1 / ⊢ X ^ (p - 1) - 1 = ∏ i ∈ Icc 1 p, (X - Polynomial.C ↑ζ ^ i)`

### micro_score 46 — rank 23 score 51
- id: ed95579168afee87333af9d50b4d41cd2c6d6c298657a682a3eb2e1f74a79edf
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:239
- current line: `    sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `case h.mp / k : ℕ / hk : Fact (Nat.Prime (4 * k + 1)) / t : ↑(ch04.U k) / ht : ⟨⟨(t.1.1.1 - t.1.1.2.1 + t.1.1.2.2, t.1.1.2.1, 2 * t.1.1.2.1 - t.1.1.2.2), ⋯⟩, ⋯⟩ = t / ⊢ t ∈ {⟨⟨(↑k, 1), ⋯⟩, ⋯⟩}`

### micro_score 46 — rank 45 score 48
- id: 659955bd12943dc092ffff0415886e102945c72ce6a93756779728aced5fa683
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:85
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `p : ℕ / h : Fact (Nat.Prime p) / hp : p % 4 = 1 / ⊢ ∃ a b, a ^ 2 + b ^ 2 = p`

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

### micro_score 46 — rank 48 score 48
- id: 124881b068dc2ef9331986b7c06ab43a691b7851e932911530cb70c312bcddcf
- repo: mo271/FormalBook
- path: FormalBook/Chapter_08.lean:76
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `n : ℕ / h_n : n ≠ 0 / ⊢ ¬2 ^ n ∣ n.factorial ∧ (2 ^ (n - 1) ∣ n.factorial ↔ ∃ m, n = 2 ^ m)`

### micro_score 46 — rank 49 score 48
- id: e83129dc9324c17bbf79171ccdf0ba07bc7c57e4f7771fbbe122bcd9242789ad
- repo: mo271/FormalBook
- path: FormalBook/Chapter_08.lean:98
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `n : ℕ / x : ℝ / ⊢ ∃ c, book.irrational.f_aux n x = ∑ i ∈ Icc n (2 * n), ↑(c i) * x ^ i`

### micro_score 46 — rank 51 score 48
- id: dbf737e3353a5e457c1493f6a6b5cba1c4e180edb6a322247420dbd98b784f34
- repo: mo271/FormalBook
- path: FormalBook/Chapter_07.lean:38
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `n : ℕ / ⊢ ∃ M, (∀ (i j : Fin n), M i j = -1 ∨ M i j = 1) ∧ ↑M.det > √↑n.factorial`

### micro_score 46 — rank 52 score 48
- id: 78459de26b2396bde524d5a8618acdf4290bd374eabd5e833ae95182438c4b46
- repo: mo271/FormalBook
- path: FormalBook/Chapter_07.lean:38
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, arithmetic_context, known_formalbook
- goal: `n : ℕ / hn : 1 < n / ⊢ ∃ M, (∀ (i j : Fin n), M i j = -1 ∨ M i j = 1) ∧ ↑M.det > √↑n.factorial`

### micro_score 46 — rank 79 score 46
- id: 5658635a134b6404fb24addedbb23bcb9364dab0ce6a5d9e187369034dced759
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:248
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, cardinality_shape, arithmetic_context, known_formalbook
- goal: `k : ℕ / hk : Fact (Nat.Prime (4 * k + 1)) / ⊢ Odd (Fintype.card ↑(ch04.T k))`

### micro_score 45 — rank 61 score 46
- id: c5b4411d81f9283149345807b335c1e053d17833438e668c96fa082cacd0fe50
- repo: dwrensha/compfiles
- path: Compfiles/Imo2022P3.lean:39
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context
- goal: `k : ℕ / hk : 0 < k / S : Finset ℕ / hS : ∀ p ∈ S, Odd p ∧ Nat.Prime p / p₁ p₂ : Fin S.card ≃ ↥S / hp₁ : Imo2022P3.Condition k S p₁ / hp₂ : Imo2022P3.Condition k S p₂ / ⊢ (∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j + i)) ∨ ∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j.rev + i)`

### micro_score 45 — rank 67 score 46
- id: 4dc775391e2ccdb337f257b6295182e79519b1c024be82c92d539b129872c216
- repo: jsm28/IMOLean
- path: IMO/IMO2022P3.lean:21
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context
- goal: `k : ℕ / hk : 0 < k / S : Finset ℕ / hS : ∀ p ∈ S, Odd p ∧ Nat.Prime p / p₁ p₂ : Fin S.card ≃ ↥S / hp₁ : IMO2022P3.Condition k S p₁ / hp₂ : IMO2022P3.Condition k S p₂ / ⊢ (∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j + i)) ∨ ∃ i, ∀ (j : Fin S.card), p₂ j = p₁ (j.rev + i)`

### micro_score 45 — rank 69 score 46
- id: a6c38e91196693b217e470bb1a6d7f5c5e4f7bf16c2f57f87773d26d0fb8d71d
- repo: jsm28/IMOLean
- path: IMO/IMO2024P3.lean:22
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context
- goal: `a : ℕ → ℕ / N : ℕ / h0 : ∀ (i : ℕ), 0 < a i / ha : ∀ (n : ℕ), N < n → a n = {i ∈ Finset.range n | a i = a (n - 1)}.card / ⊢ (IMO2024P3.EventuallyPeriodic fun i => a (2 * i)) ∨ IMO2024P3.EventuallyPeriodic fun i => a (2 * i + 1)`

### micro_score 45 — rank 70 score 46
- id: 370d81df19a05812cf92b2e173e4df4a50ee669023e531d14b5e89309727ca49
- repo: jsm28/IMOLean
- path: IMO/IMO2021P6.lean:15
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context
- goal: `m : ℕ / hm : 2 ≤ m / A : Finset ℤ / B : Fin m → Finset ℤ / hBA : ∀ (i : Fin m), B i ⊆ A / hB : ∀ (k : Fin m), ∑ i ∈ B k, i = ↑m ^ (↑k + 1) / ⊢ ↑m / 2 ≤ ↑A.card`

### micro_score 43 — rank 41 score 48
- id: 3ce6110359e3c92ba29fb1c338f5618b13946ed1e61b9de5ea29ccfcbf0cfeda
- repo: mo271/FormalBook
- path: FormalBook/Chapter_05.lean:98
- current line: `  sorry`
- reasons: sorry_on_current_line, short_goal, basic_logic_or_relation, known_formalbook
- goal: `K : Type u_1 / inst✝¹ : Field K / inst✝ : Fintype K / ⊢ ∃ ζ, ∀ (α : Kˣ), ∃ k, α = ζ ^ k`

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

### micro_score 25 — rank 57 score 46
- id: f844d1774b4d08300f0fb1a35dd0f00130405b260c5fcfbfd5c854dbd1eb5b90
- repo: YaelDillies/LeanCamCombi
- path: LeanCamCombi/GrowthInGroups/Lecture4.lean:41
- current line: `          A ⊆ F * H := showcased`
- reasons: short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context
- goal: `C : ℝ / G : Type u_2 / inst✝¹ : Group G / inst✝ : DecidableEq G / S : Finset G / hSsymm : S⁻¹ = S / hSgen : ↑(Subgroup.closure ↑S) = Set.univ / d : ℕ / hS : ∀ (n : ℕ), ↑(S ^ n).card ≤ C * ↑n ^ d / ⊢ IsVirtuallyNilpotent G`

### micro_score 22 — rank 38 score 49
- id: ff875a6a368978b85a72e83db6a289f0f39497669c77a1b1f9268f83fee5781e
- repo: YaelDillies/MiscYD
- path: MiscYD/SetFamily/PosDiffs.lean:117
- current line: ``
- reasons: short_goal, basic_logic_or_relation, cardinality_shape
- goal: `α : Type u_1 / inst✝³ : Sub α / inst✝² : Preorder α / inst✝¹ : DecidableRel fun x1 x2 => x1 ≤ x2 / inst✝ : DecidableEq α / s : Finset α / hs : (↑s).OrdConnected / ⊢ card (@Finset.posSub α inst✝³ inst✝² inst✝¹ inst✝ s s) ≤ s.card`

### micro_score 9 — rank 59 score 46
- id: fcd6a735ca62c6f2eacf6dd1a3981a36c7f65663716071ed80004a1ae82905f5
- repo: dwrensha/compfiles
- path: Compfiles/Usa1999P1.lean:46
- current line: `    n^2 ≤ c.card * 3 + 2 := by`
- reasons: short_goal, basic_logic_or_relation, cardinality_shape, arithmetic_context, existential_theorem_risk, universal_theorem_risk
- goal: `n : ℕ / c : Finset (Usa1999P1.checkerboard n) / ha : failed to pretty print expression (use 'set_option pp.rawOnError true' for raw representation) / hb : ∀ x ∈ c, ∀ y ∈ c, ∃ p, List.IsChain (Usa1999P1.adjacent n) p ∧ p.head? = some x ∧ p.getLast? = some y / ⊢ n ^ 2 ≤ c.card * 3 + 2`
