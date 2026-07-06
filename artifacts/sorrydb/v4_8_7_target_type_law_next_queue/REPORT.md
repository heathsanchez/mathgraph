# MathGraph SorryDB v4.8.7 — Target-Type Law + Next Queue

## Target-Type Law

SorryDB targets are not all PR targets. Every target must be split before proof search.

### Terminal target classes

1. `CURRENT_MAIN_PR_CANDIDATE`
2. `SNAPSHOT_REPLAY_CERTIFICATE`
3. `STALE_ALREADY_FIXED`
4. `FALSE_OR_BAD_STATEMENT`
5. `NON_ACTIONABLE`

## Current campaign facts

- `teorth/equational_theories#1461`: open, clean, Law43 definability proof.
- `mo271/FormalBook#136`: closed, valid snapshot replay, obsolete upstream.
- `mo271/FormalBook#137`: open, clean, CI green, current-main live proof repair.

## Discovery

The ranker correctly selected the Chapter 28 edge-cardinality repair as the top target, but upstream freshness made it snapshot-only. The live-current-main classifier then surfaced Chapter 06, where a micro-probe found a one-line `simp` repair that passed local and GitHub CI.

## Counts by MathGraph action

- NEXT_PROBE_CANDIDATE: 34
- PARK_COMPLEX_OR_THEOREM_SCALE: 10
- STALE_ALREADY_FIXED_OR_REMOVED: 9
- FALSE_OR_BAD_STATEMENT_RISK: 9
- CURRENT_MAIN_FILE_MISSING_OR_PRIVATE: 9
- CURRENT_MAIN_HAS_OTHER_SORRIES: 8
- ALREADY_PROMOTED_PR137: 1

## Next queue

### NEXT_PROBE_CANDIDATE — rank 6 score 56
- id: 8335cf4f29731301b3bd5d17cf0c43d7fc3130a2328288efb263a59369451fd9
- repo: mo271/FormalBook
- path: FormalBook/Chapter_20.lean:96
- current line: ``
- tags: short_or_medium_goal, finset_shape, known_formalbook
- goal: `n : ℕ / hn : 1 ≤ n / a : ↥(Finset.Icc 1 n) → ℝ / hpos : ∀ (i : ↥(Finset.Icc 1 n)), 0 < a i / ⊢ let harmonic := ↑n / ∑ i, 1 / a i; /   let geometric := (∏ i, a i) ^ (1 / ↑n); /   let arithmetic := (∑ i, a i) / ↑n; /   let all_equal := ∀ (i : ↥(Finset.Icc 1 n)), a i = a ⟨1, ⋯⟩; /   harmonic ≤ geometric ∧ /     geometric ≤ arithmetic ∧ (harmonic = geometric ↔ all_equal) ∧ (geometric = arithmetic ↔ all_equal)`

### NEXT_PROBE_CANDIDATE — rank 22 score 51
- id: 5f63aa96f6ab4c2fdcfe7b133c9d7582069a26bab74decda4bf6db0233db44ba
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:185
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `k : ℕ / ⊢ Fintype.card ↑(ch04.U k) = Fintype.card ↑(ch04.T k)`

### NEXT_PROBE_CANDIDATE — rank 23 score 51
- id: ed95579168afee87333af9d50b4d41cd2c6d6c298657a682a3eb2e1f74a79edf
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:239
- current line: `    sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `case h.mp / k : ℕ / hk : Fact (Nat.Prime (4 * k + 1)) / t : ↑(ch04.U k) / ht : ⟨⟨(t.1.1.1 - t.1.1.2.1 + t.1.1.2.2, t.1.1.2.1, 2 * t.1.1.2.1 - t.1.1.2.2), ⋯⟩, ⋯⟩ = t / ⊢ t ∈ {⟨⟨(↑k, 1), ⋯⟩, ⋯⟩}`

### NEXT_PROBE_CANDIDATE — rank 24 score 51
- id: 337995f8ca1f5af035eb2bbacfd85e7dc9aeacff891b88bdeba3197f520e2f98
- repo: mo271/FormalBook
- path: FormalBook/Chapter_08.lean:57
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `x : ℝ / ⊢ HasSum (fun n => x ^ n / ↑n.factorial) (exp x)`

### NEXT_PROBE_CANDIDATE — rank 25 score 51
- id: 6a29708883663ee508701b0a2a81bcd3be768555516e4e0c131edf89eef71a56
- repo: mo271/FormalBook
- path: FormalBook/Chapter_08.lean:110
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `n k : ℕ / ⊢ (iteratedDeriv k (book.irrational.f_aux n) 0 ∈ Set.range fun q => ↑q) ∧ /     iteratedDeriv k (book.irrational.f_aux n) 1 ∈ Set.range fun q => ↑q`

### NEXT_PROBE_CANDIDATE — rank 38 score 49
- id: ff875a6a368978b85a72e83db6a289f0f39497669c77a1b1f9268f83fee5781e
- repo: YaelDillies/MiscYD
- path: MiscYD/SetFamily/PosDiffs.lean:117
- current line: ``
- tags: short_or_medium_goal, finset_shape
- goal: `α : Type u_1 / inst✝³ : Sub α / inst✝² : Preorder α / inst✝¹ : DecidableRel fun x1 x2 => x1 ≤ x2 / inst✝ : DecidableEq α / s : Finset α / hs : (↑s).OrdConnected / ⊢ card (@Finset.posSub α inst✝³ inst✝² inst✝¹ inst✝ s s) ≤ s.card`

### NEXT_PROBE_CANDIDATE — rank 39 score 49
- id: 7823477ef62b4ddbd373b452af68ca5536b6b05e6ee29aef81c0ba74a1c81676
- repo: mo271/FormalBook
- path: FormalBook/Chapter_20.lean:96
- current line: ``
- tags: short_or_medium_goal, finset_shape, known_formalbook
- goal: `n : ℕ / hn : 1 ≤ n / a : { x // x ∈ Finset.Icc 1 n } → ℝ / hpos : ∀ (i : { x // x ∈ Finset.Icc 1 n }), 0 < a i / ⊢ let harmonic := ↑n / ∑ i, 1 / a i; /   let geometric := (∏ i, a i) ^ (1 / ↑n); /   let arithmetic := (∑ i, a i) / ↑n; /   let all_equal := ∀ (i : { x // x ∈ Finset.Icc 1 n }), a i = a ⟨1, ⋯⟩; /   harmonic ≤ geometric ∧ /     geometric ≤ arithmetic ∧ (harmonic = geometric ↔ all_equal) ∧ (geometric = arithmetic ↔ all_equal)`

### NEXT_PROBE_CANDIDATE — rank 43 score 48
- id: 6efe22035b6d2b8a940d3b739225fa4daf690e311ada66793f66edd825e9054f
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:48
- current line: `  · sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `case left / p : ℕ / h : Fact (Nat.Prime p) / ⊢ ∃ m, p = 4 * m + 1 → {s | s ^ 2 = -1}.card = 2`

### NEXT_PROBE_CANDIDATE — rank 44 score 48
- id: 902e699746fa16082ff6bede94130834cc8c8f9b2d42f496487c4920fa3ea4df
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:53
- current line: `    · sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `case right.right / p : ℕ / h : Fact (Nat.Prime p) / ⊢ ∃ m, p = 4 * m + 1 → {s | s ^ 2 = -1}.card = 0`

### NEXT_PROBE_CANDIDATE — rank 45 score 48
- id: 659955bd12943dc092ffff0415886e102945c72ce6a93756779728aced5fa683
- repo: mo271/FormalBook
- path: FormalBook/Chapter_04.lean:85
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `p : ℕ / h : Fact (Nat.Prime p) / hp : p % 4 = 1 / ⊢ ∃ a b, a ^ 2 + b ^ 2 = p`

### NEXT_PROBE_CANDIDATE — rank 46 score 48
- id: e3495f5c9e15a09f8fb227dc09c18272f2f5952aebbbc2dd2a2f8059a1ec314d
- repo: mo271/FormalBook
- path: FormalBook/Chapter_03.lean:153
- current line: `        sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `l m n : ℕ / h_2lel : 2 ≤ l / k : ℕ / h_4lek : 4 ≤ k / h_klen4 : k ≤ n - 4 / h : 2 * k ≤ n / h_klen : k ≤ n / h_1lel : 1 ≤ l / H : n.choose k = m ^ l / h₁ : ∃ p, Nat.Prime p ∧ p ^ l ≤ n ∧ k ^ l < p ^ l ∧ k ^ 2 ≤ k ^ l / h✝ : ¬l = 2 / ⊢ 3 ≤ l`

### NEXT_PROBE_CANDIDATE — rank 47 score 48
- id: bfad037cde20475fabf127cc96ef202f7cdc6ab019ba5d3e387fc4b6ce4c5b21
- repo: mo271/FormalBook
- path: FormalBook/Chapter_03.lean:173
- current line: `      sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `k l m n : ℕ / h_2lel : 2 ≤ l / h_4lek : 4 ≤ k / h_klen4 : k ≤ n - 4 / h_wlog : ∀ (k' : ℕ), 4 ≤ k' → k' ≤ n - 4 → 2 * k' ≤ n → n.choose k' ≠ m ^ l / h : n < 2 * k / h_klen : k ≤ n / k' : ℕ := n - k / h_k'_def : k' = n - k / ⊢ 2 * k' ≤ n`

### NEXT_PROBE_CANDIDATE — rank 48 score 48
- id: 124881b068dc2ef9331986b7c06ab43a691b7851e932911530cb70c312bcddcf
- repo: mo271/FormalBook
- path: FormalBook/Chapter_08.lean:76
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `n : ℕ / h_n : n ≠ 0 / ⊢ ¬2 ^ n ∣ n.factorial ∧ (2 ^ (n - 1) ∣ n.factorial ↔ ∃ m, n = 2 ^ m)`

### NEXT_PROBE_CANDIDATE — rank 49 score 48
- id: e83129dc9324c17bbf79171ccdf0ba07bc7c57e4f7771fbbe122bcd9242789ad
- repo: mo271/FormalBook
- path: FormalBook/Chapter_08.lean:98
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `n : ℕ / x : ℝ / ⊢ ∃ c, book.irrational.f_aux n x = ∑ i ∈ Icc n (2 * n), ↑(c i) * x ^ i`

### NEXT_PROBE_CANDIDATE — rank 50 score 48
- id: 3c45928b7f6b9645a3d1804a7863ad1560c515ebef44608963364e0a41b034c2
- repo: mo271/FormalBook
- path: FormalBook/Chapter_07.lean:32
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `n : ℕ / A : Matrix (Fin n) (Fin n) ℝ / h : A.IsHermitian / ⊢ ∃ Q ∈ orthogonalGroup (Fin n) ℝ, ∃ d, diagonal d = Q.conjTranspose * A * Q`

### NEXT_PROBE_CANDIDATE — rank 51 score 48
- id: dbf737e3353a5e457c1493f6a6b5cba1c4e180edb6a322247420dbd98b784f34
- repo: mo271/FormalBook
- path: FormalBook/Chapter_07.lean:38
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `n : ℕ / ⊢ ∃ M, (∀ (i j : Fin n), M i j = -1 ∨ M i j = 1) ∧ ↑M.det > √↑n.factorial`

### NEXT_PROBE_CANDIDATE — rank 52 score 48
- id: 78459de26b2396bde524d5a8618acdf4290bd374eabd5e833ae95182438c4b46
- repo: mo271/FormalBook
- path: FormalBook/Chapter_07.lean:38
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, known_formalbook
- goal: `n : ℕ / hn : 1 < n / ⊢ ∃ M, (∀ (i j : Fin n), M i j = -1 ∨ M i j = 1) ∧ ↑M.det > √↑n.factorial`

### NEXT_PROBE_CANDIDATE — rank 53 score 47
- id: a776603a4a27ee7b6e3fb5762268b15d54d8b8ca3de38eb077493781dd751b4c
- repo: google-deepmind/formal-imo
- path: Imo/1991/P4.lean:33
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, finset_shape
- goal: `n k : ℕ / G : SimpleGraph (Fin (n + 1)) / inst✝ : DecidableRel G.Adj / h₀ : G.Connected / h₃ : G.edgeFinset.card = k / ⊢ ∃ labels, /     ∃ (_ : Set.BijOn labels ((SimpleGraph.edgeSetEmbedding (Fin (n + 1))) G) (Set.Icc 1 k)), /       ∀ (v : Fin (n + 1)), (G.incidenceFinset v).card ≥ 2 → (G.incidenceFinset v).gcd labels = 1`

### NEXT_PROBE_CANDIDATE — rank 54 score 47
- id: 9420420afb8501ff9c82315e7d0be090e6107c4edd1249fa110f5cefcb1df827
- repo: google-deepmind/formal-imo
- path: Imo/2007/P3.lean:36
- current line: `  sorry`
- tags: short_or_medium_goal, sorry_on_current_line, finset_shape
- goal: `n : ℕ / C : SimpleGraph (Fin n) / inst✝ : DecidableRel C.Adj / largest_clique_size_in : Finset (Fin n) → ℕ / h₀ : largest_clique_size_in = fun S => {s ∈ S.powerset | C.IsClique ↑s}.sup Finset.card / h₁ : Even (largest_clique_size_in Finset.univ) / ⊢ ∃ R₁ R₂, IsCompl R₁ R₂ ∧ largest_clique_size_in R₁ = largest_clique_size_in R₂`

### NEXT_PROBE_CANDIDATE — rank 57 score 46
- id: f844d1774b4d08300f0fb1a35dd0f00130405b260c5fcfbfd5c854dbd1eb5b90
- repo: YaelDillies/LeanCamCombi
- path: LeanCamCombi/GrowthInGroups/Lecture4.lean:41
- current line: `          A ⊆ F * H := showcased`
- tags: short_or_medium_goal, finset_shape
- goal: `C : ℝ / G : Type u_2 / inst✝¹ : Group G / inst✝ : DecidableEq G / S : Finset G / hSsymm : S⁻¹ = S / hSgen : ↑(Subgroup.closure ↑S) = Set.univ / d : ℕ / hS : ∀ (n : ℕ), ↑(S ^ n).card ≤ C * ↑n ^ d / ⊢ IsVirtuallyNilpotent G`

## Next execution rule

Pick the first `NEXT_MICRO_PROBE_CANDIDATE`. Use one fresh current-main clone, one module build, and a tiny tactic bank. Stop after first accepted proof unless nearby same-shape sorries are trivial.