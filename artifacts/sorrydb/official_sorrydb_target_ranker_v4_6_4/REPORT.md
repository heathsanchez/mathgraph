# SorryDB v4.6.4 — Official Target Ranker

## Result

- input tasks: 1000
- malformed records: 0
- status: TARGETS_RANKED

## Lean versions

- 318: v4.27.0-rc1
- 218: v4.26.0
- 145: v4.24.0
- 97: v4.26.0-rc2
- 72: v4.22.0
- 37: v4.23.0-rc2
- 36: v4.24.0-rc1
- 22: v4.25.0-rc2
- 14: v4.18.0-rc1
- 12: v4.25.0
- 11: v4.18.0
- 10: v4.26.0-rc1
- 7: v4.21.0
- 1: v4.22.0-rc4

## Top 20 candidates

### 1. score -41 — split_index 527 — id 589ac7b645ccf7c434f7686051ee627a04704b3141a80debcd2d2ed4358562b3

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_28.lean
- start: 64:65
- end: 64:70
- reasons: lean_4_27, educational_problem_repo, tactic_hint, short_goal, exercise_like_path
- goal: α : Type u_1 inst✝² : Fintype α inst✝¹ : DecidableEq α G : SimpleGraph α inst✝ : DecidableRel G.Adj e : Sym2 α he : e ∈ G.edgeFinset ⊢ {v | v ∈ e}.card = 2

### 2. score -38 — split_index 392 — id a0fb95b1a0baea3d3412576625bd86683b560faa7b95b4e4d68e8e2689e166f4

- repo: https://github.com/fpvandoorn/LeanCourse25
- branch: master
- commit: cd0f32f5b07311e08a9e89733a1375f54eb790c0
- lean: v4.24.0
- path: LeanCourse25/Lectures/Lecture20Before.lean
- start: 409:25
- end: 409:30
- reasons: lean_4_24_25, educational_problem_repo, true_goal, short_goal
- goal: A✝¹ : Type u B✝¹ : A✝¹ → Type v A✝ : Type u B✝ : A✝ → Prop A : Sort u B : A → Sort v ⊢ True

### 3. score -38 — split_index 277 — id b5bd9f98d658acbbfbf98ae0c9cf2ac12f8f23e98c31b40f020dc4303477694c

- repo: https://github.com/fpvandoorn/LeanCourse25
- branch: master
- commit: cd0f32f5b07311e08a9e89733a1375f54eb790c0
- lean: v4.24.0
- path: LeanCourse25/Lectures/Lecture20.lean
- start: 421:25
- end: 421:30
- reasons: lean_4_24_25, educational_problem_repo, true_goal, short_goal
- goal: f : (n : ℕ) → Fin n n : ℕ A✝² : Type u B✝² : Type v A✝¹ : Type u B✝¹ : A✝¹ → Type v A✝ : Type u B✝ : A✝ → Prop A : Sort u B : A → Sort v ⊢ True

### 4. score -38 — split_index 195 — id 86cb618467cd206603b0a29384c83e22f508f3c834b6a6cf9d120ae95cec7ff2

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean
- start: 78:29
- end: 78:34
- reasons: lean_4_27, educational_problem_repo, negation_or_contradiction, short_goal, exercise_like_path
- goal: q n : ℕ lamb : ℂ a : ℝ := lamb.re b : ℝ := lamb.im h : lamb ∈ primitiveRoots n ℂ h_lamb : lamb ≠ 1 h_a_lt_one : ‖a‖ < 1 ⊢ ‖eval (↑q) (X - C lamb)‖ ^ 2 = ‖↑q - lamb‖ ^ 2

### 5. score -38 — split_index 575 — id d4b4aea0a504a532f3211c605cc8bc1ba852b5b14e610e8af733a17f169bb74a

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean
- start: 90:4
- end: 90:9
- reasons: lean_4_27, educational_problem_repo, negation_or_contradiction, short_goal, exercise_like_path
- goal: q n : ℕ lamb : ℂ a : ℝ := lamb.re b : ℝ := lamb.im h : lamb ∈ primitiveRoots n ℂ h_lamb : lamb ≠ 1 h_a_lt_one : ‖a‖ < 1 h_ineq : ‖eval (↑q) (X - C lamb)‖ ^ 2 > (↑q - 1) ^ 2 this✝ : 0 ≤ (↑q - 1) ^ 2 g : ↑q - 1 < √(‖eval (↑q) (X - C lamb)‖ ^ 2) this : √((↑q - 1) ^ 2) = ↑q - 1 ⊢ 0 ≤ ‖eval (↑q) (X - C lamb)‖

### 6. score -36 — split_index 878 — id 5f63aa96f6ab4c2fdcfe7b133c9d7582069a26bab74decda4bf6db0233db44ba

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_04.lean
- start: 185:2
- end: 185:7
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: k : ℕ ⊢ Fintype.card ↑(ch04.U k) = Fintype.card ↑(ch04.T k)

### 7. score -36 — split_index 64 — id ca4a5d8256fb5bd3104fcfd32887a170fb933a093273c74530c869b781e977a6

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_02.lean
- start: 221:38
- end: 221:43
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: n : ℕ hn : 1 < n ⊢ ↑n.factorial > chapter2.e * (↑n / chapter2.e) ^ n

### 8. score -36 — split_index 953 — id 5658635a134b6404fb24addedbb23bcb9364dab0ce6a5d9e187369034dced759

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_04.lean
- start: 248:2
- end: 248:7
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: k : ℕ hk : Fact (Nat.Prime (4 * k + 1)) ⊢ Odd (Fintype.card ↑(ch04.T k))

### 9. score -36 — split_index 316 — id a78ca65b87970fabbb5521a907ce4ba2f71b6713d4a4543a6efc2f9edbf87d37

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_01.lean
- start: 187:50
- end: 187:55
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: n : ℕ x : ℝ hxge : x ≥ ↑n hxlt : x < ↑n + 1 ⊢ Real.log x ≤ ∑ k ∈ Icc 1 n, (↑k)⁻¹

### 10. score -36 — split_index 989 — id 3f4ef9e3cfcb5ab03b7b0e0387a4f687a6c7f5c0a8570e52e0d8e8b42e24c8c3

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_04.lean
- start: 287:79
- end: 287:84
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: k : ℕ hk : Fact (Nat.Prime (4 * k + 1)) ⊢ (fixedPoints (ch04.trivialInvo k)).Nonempty

### 11. score -36 — split_index 132 — id 85b49489509ec0b01e4a1df0173345e0e168acd0d179fac6932bb46a1d8dcc78

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_02.lean
- start: 225:56
- end: 225:61
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: k n : ℕ ⊢ ↑(n.choose k) ≤ ↑n ^ k / ↑k.factorial ∧ ↑n ^ k / ↑k.factorial ≤ ↑n ^ k / 2 ^ (k - 1)

### 12. score -36 — split_index 622 — id fafb865c35ed180a88ec7877c6fb3432fc771002d0021d4e0dd67de1341ec201

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_24.lean
- start: 38:76
- end: 38:81
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: n : ℕ M : Matrix (Fin n) (Fin n) ℝ ⊢ M ∈ doublyStochastic ℝ (Fin n) → M.permanent ≥ ↑n.factorial / ↑n ^ n

### 13. score -36 — split_index 374 — id 23148bda427a6f78e69b003d58a8a7ac9ca69d51fdc533e4ff0ab1688d783ecc

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_01.lean
- start: 189:74
- end: 189:79
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: n : ℕ x : ℝ hxge : x ≥ ↑n hxlt : x < ↑n + 1 ⊢ ∑' (m : ↑(S₁ x)), (↑↑m)⁻¹ ≤ ∏ p ∈ ⌊x⌋.natAbs.primesBelow, ∑' (k : ℕ), (↑p ^ k)⁻¹

### 14. score -36 — split_index 477 — id 1404fd8c29641a0312cb9c9f79fb69017a1274c372110ba04643eb4dca1d0478

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_01.lean
- start: 191:65
- end: 191:70
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: n : ℕ x : ℝ hxge : x ≥ ↑n hxlt : x < ↑n + 1 ⊢ ↑(∏ k ∈ Icc 1 (primeCountingReal x), nth Nat.Prime k / (nth Nat.Prime k - 1)) ≤     ↑(∏ k ∈ Icc 1 (primeCountingReal x), (k + 1) / k)

### 15. score -36 — split_index 427 — id 96336aaeb19b31c66ae605692b4f9d1cfd72a2867b2778a68a60cda20153bd18

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_01.lean
- start: 190:97
- end: 190:102
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: n : ℕ x : ℝ hxge : x ≥ ↑n hxlt : x < ↑n + 1 ⊢ ∏ p ∈ ⌊x⌋.natAbs.primesBelow, ∑' (k : ℕ), (↑p ^ k)⁻¹ ≤     ↑(∏ k ∈ Icc 1 (primeCountingReal x), nth Nat.Prime k / (nth Nat.Prime k - 1))

### 16. score -36 — split_index 916 — id ed95579168afee87333af9d50b4d41cd2c6d6c298657a682a3eb2e1f74a79edf

- repo: https://github.com/mo271/FormalBook
- branch: main
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_04.lean
- start: 239:4
- end: 239:9
- reasons: lean_4_27, educational_problem_repo, short_goal, exercise_like_path
- goal: case h.mp k : ℕ hk : Fact (Nat.Prime (4 * k + 1)) t : ↑(ch04.U k) ht : ⟨⟨(t.1.1.1 - t.1.1.2.1 + t.1.1.2.2, t.1.1.2.1, 2 * t.1.1.2.1 - t.1.1.2.2), ⋯⟩, ⋯⟩ = t ⊢ t ∈ {⟨⟨(↑k, 1), ⋯⟩, ⋯⟩}

### 17. score -34 — split_index 370 — id b4d345ad1d3f7441b59f93f76f7041de9119dbd22ce9f96b637ae36a1ab933b2

- repo: https://github.com/leanprover-community/batteries
- branch: weak.backward.privateInPublic
- commit: fce4da76bae6a8daa1503009abb00587253c4177
- lean: v4.25.0-rc2
- path: BatteriesTest/lintunused.lean
- start: 7:2
- end: 7:7
- reasons: lean_4_24_25, true_goal, short_goal, exercise_like_path
- goal: h : 1 = 1 ⊢ True

### 18. score -34 — split_index 237 — id d07abd6472334451129fc38084a82a564546548b8cebc419be814b3029019605

- repo: https://github.com/djvelleman/HTPILeanPackage
- branch: master
- commit: 12ca2d2d0f0d12e6c2a158cf01268df350a7c884
- lean: v4.26.0
- path: Chap8Ex.lean
- start: 33:55
- end: 33:60
- reasons: lean_4_26, educational_problem_repo, short_goal, exercise_like_path
- goal: ⊢ denum ↑{n | even n}

### 19. score -34 — split_index 978 — id 71df22034435c40ccf64fc56a3915dccb30d1fd475a9232b45498910519b73f1

- repo: https://github.com/djvelleman/HTPILeanPackage
- branch: master
- commit: 12ca2d2d0f0d12e6c2a158cf01268df350a7c884
- lean: v4.26.0
- path: Chap8Ex.lean
- start: 104:69
- end: 104:74
- reasons: lean_4_26, educational_problem_repo, short_goal, exercise_like_path
- goal: n : ℕ h : ↑(I 0) ∼ ↑(I n) ⊢ n = 0

### 20. score -34 — split_index 410 — id b4a0b17a6112b4f5b728ae25a5f17b6c7ef0d5ab8c96a3f2d37f4bf54e1a712f

- repo: https://github.com/djvelleman/HTPILeanPackage
- branch: master
- commit: 12ca2d2d0f0d12e6c2a158cf01268df350a7c884
- lean: v4.26.0
- path: Chap8Ex.lean
- start: 45:35
- end: 45:40
- reasons: lean_4_26, educational_problem_repo, short_goal, exercise_like_path
- goal: U V : Type h : U ∼ V ⊢ Set U ∼ Set V
