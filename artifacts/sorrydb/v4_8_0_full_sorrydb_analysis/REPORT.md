# MathGraph SorryDB v4.8.0 — Full Analysis

## Repository purpose

SorryDB is a dataset + verifier + strategy harness for Lean `sorry` repair.

## Dataset summary

### SorryDB_2601
- exists: True
- count: 5663
- unique repos: 78
- unique commits: 140
- goal median length: 138
- top repos:
  - https://github.com/google-deepmind/formal-conjectures: 1698
  - https://github.com/yangky11/miniF2F-lean4: 488
  - https://github.com/fpvandoorn/LeanCourse25: 443
  - https://github.com/Verified-zkEVM/ArkLib: 431
  - https://github.com/google-deepmind/formal-imo: 301
  - https://github.com/djvelleman/HTPILeanPackage: 259
  - https://github.com/thefundamentaltheor3m/Sphere-Packing-Lean: 152
  - https://github.com/Timeroot/Lean-QuantumInfo: 137
  - https://github.com/AlexKontorovich/PrimeNumberTheoremAnd: 136
  - https://github.com/dwrensha/compfiles: 120
- Lean versions:
  - v4.22.0: 2310
  - v4.24.0: 1108
  - v4.26.0: 871
  - v4.27.0-rc1: 716
  - v4.24.0-rc1: 203
  - v4.26.0-rc2: 142
  - v4.23.0-rc2: 98
  - v4.25.0-rc2: 66
  - v4.18.0-rc1: 54
  - v4.25.0: 43

### SorryDB_2601_eval1000
- exists: True
- count: 1000
- unique repos: 78
- unique commits: 107
- goal median length: 241.5
- top repos:
  - https://github.com/AlexKontorovich/PrimeNumberTheoremAnd: 21
  - https://github.com/AlexKontorovich/RealAnalysisGame: 21
  - https://github.com/Beneficial-AI-Foundation/curve25519-dalek-lean-verify: 21
  - https://github.com/FormalizedFormalLogic/Foundation: 21
  - https://github.com/rkirov/category-theory-in-context-lean: 21
  - https://github.com/FredRaj3/SemicircleLaw: 21
  - https://github.com/HEPLean/PhysLean: 21
  - https://github.com/ImperialCollegeLondon/FLT: 21
  - https://github.com/fpvandoorn/LeanCourse25: 20
  - https://github.com/PatrickMassot/GlimpseOfLean: 20
- Lean versions:
  - v4.27.0-rc1: 318
  - v4.26.0: 218
  - v4.24.0: 145
  - v4.26.0-rc2: 97
  - v4.22.0: 72
  - v4.23.0-rc2: 37
  - v4.24.0-rc1: 36
  - v4.25.0-rc2: 22
  - v4.18.0-rc1: 14
  - v4.25.0: 12

## MathGraph interpretation

SorryDB gives MathGraph a hard external judge: replace a concrete `sorry` at a concrete repo commit with a proof string and replay the project.

The primary opportunity is not one-shot LLM proof generation. It is replay-stable memory:

1. classify sorries by goal signature;
2. mine typed residuals from Lean failures;
3. promote reusable proof motifs to a Lawbook;
4. separate snapshot-only replay certificates from current-main PR candidates;
5. maintain disk-safe persistent build pools.

## Top 20 MathGraph candidate records

### 67 — 589ac7b645ccf7c434f7686051ee627a04704b3141a80debcd2d2ed4358562b3
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_28.lean:64
- reasons: short_goal, lean_file, educational_repo, finset_goal, equality_goal, simplegraph_goal, few_goal_lines, recent_lean
- goal: `α : Type u_1 / inst✝² : Fintype α / inst✝¹ : DecidableEq α / G : SimpleGraph α / inst✝ : DecidableRel G.Adj / e : Sym2 α / he : e ∈ G.edgeFinset / ⊢ {v | v ∈ e}.card = 2`

### 67 — 589ac7b645ccf7c434f7686051ee627a04704b3141a80debcd2d2ed4358562b3
- dataset: SorryDB_2601_eval1000
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_28.lean:64
- reasons: short_goal, lean_file, educational_repo, finset_goal, equality_goal, simplegraph_goal, few_goal_lines, recent_lean
- goal: `α : Type u_1 / inst✝² : Fintype α / inst✝¹ : DecidableEq α / G : SimpleGraph α / inst✝ : DecidableRel G.Adj / e : Sym2 α / he : e ∈ G.edgeFinset / ⊢ {v | v ∈ e}.card = 2`

### 59 — 63db8ffc0199cc1a713aeb07f33c5fcf900a66b1af2ab8a71cc96740cc9dd99b
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_05.lean:53
- reasons: short_goal, lean_file, educational_repo, finset_goal, equality_goal, few_goal_lines, recent_lean
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / units_finset : Finset (ZMod p) := univ.erase 0 / image_finset : Finset (ZMod p) := image (fun x => ↑a * x) units_finset / ⊢ units_finset = image_finset`

### 59 — 1d90823a9b08f76f3b0edc5bda1886cc28d47c4f846b149aeb6e1666efbac94f
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_05.lean:54
- reasons: short_goal, lean_file, educational_repo, finset_goal, equality_goal, few_goal_lines, recent_lean
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / units_finset : Finset (ZMod p) := univ.erase 0 / image_finset : Finset (ZMod p) := image (fun x => ↑a * x) units_finset / this : units_finset = image_finset / ⊢ ↑a ≠ 0 → ↑a ^ (p - 1) = -1`

### 56 — 906671815dfd025bb15ea27e0ce0128125d71aedecd06eedbd4e38cedc0f9d12
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_44.lean:47
- reasons: short_goal, lean_file, educational_repo, equality_goal, simplegraph_goal, quantifier_goal, few_goal_lines, recent_lean
- goal: `V : Type u / inst✝¹ : Fintype V / G : SimpleGraph V / inst✝ : Nonempty V / h : ∀ ⦃v w : V⦄, v ≠ w → Fintype.card ↑(G.commonNeighbors v w) = 1 / no_politician : ¬∃ v, ∀ (w : V), v ≠ w → G.Adj v w / ⊢ ∃ k, G.IsRegularOfDegree k`

### 56 — da24e07fcb6bd291f0b0bf6e660884ed7d2d36ec51111fd6df7a50e7818f17b7
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_44.lean:53
- reasons: short_goal, lean_file, educational_repo, equality_goal, simplegraph_goal, quantifier_goal, few_goal_lines, recent_lean
- goal: `V : Type u / inst✝¹ : Fintype V / G : SimpleGraph V / inst✝ : Nonempty V / h : ∀ ⦃v w : V⦄, v ≠ w → Fintype.card ↑(G.commonNeighbors v w) = 1 / no_politician : ¬∃ v, ∀ (w : V), v ≠ w → G.Adj v w / lemma₁ : ∃ k, G.IsRegularOfDegree k / k : ℕ / hregular : G.IsRegularOfDegree k / n : ℕ := Fintype.card V / ⊢ k + (n - 1) = k * k`

### 56 — 8335cf4f29731301b3bd5d17cf0c43d7fc3130a2328288efb263a59369451fd9
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_20.lean:96
- reasons: short_goal, lean_file, educational_repo, finset_goal, equality_goal, quantifier_goal, few_goal_lines, recent_lean
- goal: `n : ℕ / hn : 1 ≤ n / a : ↥(Finset.Icc 1 n) → ℝ / hpos : ∀ (i : ↥(Finset.Icc 1 n)), 0 < a i / ⊢ let harmonic := ↑n / ∑ i, 1 / a i; /   let geometric := (∏ i, a i) ^ (1 / ↑n); /   let arithmetic := (∑ i, a i) / ↑n; /   let all_equal := ∀ (i : ↥(Finset.Icc 1 n)), a i = a ⟨1, ⋯⟩; /   harmonic ≤ geometric ∧ /     geometric ≤ arithmetic ∧ (harmonic = geometric ↔ all_equal) ∧ (geometric = arithmetic ↔ all_equal)`

### 51 — 7d588d7ae944f63fa0740a194ef64639dc06e9cafdf4362755e400ac34277a39
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_05.lean:59
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / ⊢ ↑a ≠ 0 → ↑(book.quadratic_reciprocity.legendre_sym p inst✝ a) = ↑a ^ ((p - 1) / 2)`

### 51 — ffa953c8de92b5d64ee0bac067a51eedd95321e583b8133058a2474c6543d316
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_05.lean:63
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a b : ℤ / ⊢ book.quadratic_reciprocity.legendre_sym p inst✝ (a * b) = /     book.quadratic_reciprocity.legendre_sym p inst✝ a * book.quadratic_reciprocity.legendre_sym p inst✝ b`

### 51 — 5344347634ad66d64488f8ee4c91b5b044a07a33eb1cdc47e16c3f270b6aae73
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_05.lean:84
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `p q : ℕ / hp : p ≠ 2 / hq : q ≠ 2 / inst✝¹ : Fact (Nat.Prime p) / inst✝ : Fact (Nat.Prime q) / ⊢ book.quadratic_reciprocity.legendre_sym p inst✝¹ ↑q * book.quadratic_reciprocity.legendre_sym q inst✝ ↑p = /     -1 ^ ((p - 1) / 2 * (q - 1) / 2)`

### 51 — fcd7001b7b076fe7885f3358723d519d3b14e481b2439a23f90b98b5f7f9f99f
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_05.lean:113
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `p : ℕ / inst✝¹ : Fact (Prime p) / K : Type u_1 / inst✝ : Field K / ζ : Kˣ / h_1 : ζ ^ p = 1 / h_2 : ζ ≠ 1 / ⊢ X ^ (p - 1) - 1 = ∏ i ∈ Icc 1 p, (X - Polynomial.C ↑ζ ^ i)`

### 51 — 0c61aa8c3887d83d28dcf0e2da0b2af5f25c08b40055095f06cb28e43d533d7c
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_09.lean:619
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `⊢ ∑' (n : ℕ+), 1 / ↑↑n = Real.pi ^ 2 / 6`

### 51 — 69053d06c5a730c0428d85a84b5a3c1f2b0aeacdc44a92fcb01a2b19cd76dde6
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_09.lean:615
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `⊢ ∑' (k : ℕ), 1 / (2 * ↑k + 1) ^ 2 = Real.pi ^ 2 / 8`

### 51 — 5e44f965721b80762f0079dcc54d0d29fcd3f7e7b200ea577332f68b0bf2a10c
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean:73
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / ⊢ lamb ≠ 1`

### 51 — 7cb57d82c952c79e9bf4aae30f33232a11f45a9adee401673e8d8ebe31fb16b1
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean:74
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / ⊢ ‖a‖ < 1`

### 51 — 86cb618467cd206603b0a29384c83e22f508f3c834b6a6cf9d120ae95cec7ff2
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean:78
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖eval (↑q) (X - C lamb)‖ ^ 2 = ‖↑q - lamb‖ ^ 2`

### 51 — 06cf2147b64b191a85609b13daee7c622ce13953c387135490b797c700b7cc7f
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean:80
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖↑q - lamb‖ ^ 2 = ‖↑q - ↑a - I * ↑b‖ ^ 2`

### 51 — a1bf38dbf70d95262bf67567f247446bbfb6d9a7c6c82e4a3fc61301452cbdab
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean:81
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖↑q - ↑a - I * ↑b‖ ^ 2 = ‖↑q - ↑a‖ ^ 2 + ‖b‖ ^ 2`

### 51 — e9028f141e2b41dcba2414ce7a97ab219d53718e8baa8007693cdbd7970b2561
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean:82
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖↑q - ↑a‖ ^ 2 + ‖b‖ ^ 2 = ↑q ^ 2 - 2 * ‖a‖ * ↑q + ‖a‖ ^ 2 + ‖b‖ ^ 2`

### 51 — 87b5af226dc1c9fad6f03bad08a9067b3e742930c3c38f84b19c72dd8a406cb2
- dataset: SorryDB_2601
- remote: https://github.com/mo271/FormalBook
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- path: FormalBook/Chapter_06.lean:83
- reasons: short_goal, lean_file, educational_repo, equality_goal, few_goal_lines, recent_lean
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ↑q ^ 2 - 2 * ‖a‖ * ↑q + ‖a‖ ^ 2 + ‖b‖ ^ 2 > (↑q - 1) ^ 2`

## Immediate next experiment

Build a `SorryDB triage compiler` that labels each target as:

- `CURRENT_MAIN_PR_CANDIDATE`
- `SNAPSHOT_REPLAY_CERTIFICATE`
- `STALE_ALREADY_FIXED`
- `NON_ACTIONABLE`

Then run proof search only after target-existence and disk-budget checks.