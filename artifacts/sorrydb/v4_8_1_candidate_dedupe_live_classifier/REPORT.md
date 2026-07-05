# MathGraph SorryDB v4.8.1 — Candidate Dedupe + Live/Stale Classifier

- input rows: 200
- deduped rows: 154
- classified rows: 80

## CURRENT_MAIN_PR_CANDIDATE — 54

### rank 2 score 59 — 63db8ffc0199cc1a713aeb07f33c5fcf900a66b1af2ab8a71cc96740cc9dd99b
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_05.lean:53
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  have : units_finset = image_finset := by sorry`
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / units_finset : Finset (ZMod p) := univ.erase 0 / image_finset : Finset (ZMod p) := image (fun x => ↑a * x) units_finset / ⊢ units_finset = image_finset`

### rank 3 score 59 — 1d90823a9b08f76f3b0edc5bda1886cc28d47c4f846b149aeb6e1666efbac94f
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_05.lean:54
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  sorry`
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / units_finset : Finset (ZMod p) := univ.erase 0 / image_finset : Finset (ZMod p) := image (fun x => ↑a * x) units_finset / this : units_finset = image_finset / ⊢ ↑a ≠ 0 → ↑a ^ (p - 1) = -1`

### rank 6 score 56 — 8335cf4f29731301b3bd5d17cf0c43d7fc3130a2328288efb263a59369451fd9
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_20.lean:96
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: ``
- goal: `n : ℕ / hn : 1 ≤ n / a : ↥(Finset.Icc 1 n) → ℝ / hpos : ∀ (i : ↥(Finset.Icc 1 n)), 0 < a i / ⊢ let harmonic := ↑n / ∑ i, 1 / a i; /   let geometric := (∏ i, a i) ^ (1 / ↑n); /   let arithmetic := (∑ i, a i) / ↑n; /   let all_equal := ∀ (i : ↥(Finset.Icc 1 n)), a i = a ⟨1, ⋯⟩; /   harmonic ≤ geometric ∧ /     geometric ≤ arithmetic ∧ (harmonic = geometric ↔ all_equal) ∧ (geometric = arithmetic ↔ al`

### rank 7 score 51 — 7d588d7ae944f63fa0740a194ef64639dc06e9cafdf4362755e400ac34277a39
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_05.lean:59
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  sorry`
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a : ℤ / ⊢ ↑a ≠ 0 → ↑(book.quadratic_reciprocity.legendre_sym p inst✝ a) = ↑a ^ ((p - 1) / 2)`

### rank 8 score 51 — ffa953c8de92b5d64ee0bac067a51eedd95321e583b8133058a2474c6543d316
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_05.lean:63
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  sorry`
- goal: `p : ℕ / inst✝ : Fact (Nat.Prime p) / a b : ℤ / ⊢ book.quadratic_reciprocity.legendre_sym p inst✝ (a * b) = /     book.quadratic_reciprocity.legendre_sym p inst✝ a * book.quadratic_reciprocity.legendre_sym p inst✝ b`

### rank 9 score 51 — 5344347634ad66d64488f8ee4c91b5b044a07a33eb1cdc47e16c3f270b6aae73
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_05.lean:84
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  sorry`
- goal: `p q : ℕ / hp : p ≠ 2 / hq : q ≠ 2 / inst✝¹ : Fact (Nat.Prime p) / inst✝ : Fact (Nat.Prime q) / ⊢ book.quadratic_reciprocity.legendre_sym p inst✝¹ ↑q * book.quadratic_reciprocity.legendre_sym q inst✝ ↑p = /     -1 ^ ((p - 1) / 2 * (q - 1) / 2)`

### rank 10 score 51 — fcd7001b7b076fe7885f3358723d519d3b14e481b2439a23f90b98b5f7f9f99f
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_05.lean:113
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  sorry`
- goal: `p : ℕ / inst✝¹ : Fact (Prime p) / K : Type u_1 / inst✝ : Field K / ζ : Kˣ / h_1 : ζ ^ p = 1 / h_2 : ζ ≠ 1 / ⊢ X ^ (p - 1) - 1 = ∏ i ∈ Icc 1 p, (X - Polynomial.C ↑ζ ^ i)`

### rank 11 score 51 — 0c61aa8c3887d83d28dcf0e2da0b2af5f25c08b40055095f06cb28e43d533d7c
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_09.lean:619
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  sorry`
- goal: `⊢ ∑' (n : ℕ+), 1 / ↑↑n = Real.pi ^ 2 / 6`

### rank 12 score 51 — 69053d06c5a730c0428d85a84b5a3c1f2b0aeacdc44a92fcb01a2b19cd76dde6
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_09.lean:615
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  sorry`
- goal: `⊢ ∑' (k : ℕ), 1 / (2 * ↑k + 1) ^ 2 = Real.pi ^ 2 / 8`

### rank 13 score 51 — 5e44f965721b80762f0079dcc54d0d29fcd3f7e7b200ea577332f68b0bf2a10c
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_06.lean:73
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  have h_lamb: lamb ≠ 1 := by sorry`
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / ⊢ lamb ≠ 1`

### rank 14 score 51 — 7cb57d82c952c79e9bf4aae30f33232a11f45a9adee401673e8d8ebe31fb16b1
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_06.lean:74
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `  have h_a_lt_one: ‖a‖ < 1 := by sorry`
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / ⊢ ‖a‖ < 1`

### rank 15 score 51 — 86cb618467cd206603b0a29384c83e22f508f3c834b6a6cf9d120ae95cec7ff2
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_06.lean:78
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `      _ = ‖q - lamb‖^2 := by sorry`
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖eval (↑q) (X - C lamb)‖ ^ 2 = ‖↑q - lamb‖ ^ 2`

### rank 16 score 51 — 06cf2147b64b191a85609b13daee7c622ce13953c387135490b797c700b7cc7f
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_06.lean:80
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `      _ = ‖(q : ℂ) - a - I*b‖^2 := by sorry`
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖↑q - lamb‖ ^ 2 = ‖↑q - ↑a - I * ↑b‖ ^ 2`

### rank 17 score 51 — a1bf38dbf70d95262bf67567f247446bbfb6d9a7c6c82e4a3fc61301452cbdab
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_06.lean:81
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `      _ = ‖(q : ℂ) - a‖^2 + ‖b‖^2 := by sorry`
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖↑q - ↑a - I * ↑b‖ ^ 2 = ‖↑q - ↑a‖ ^ 2 + ‖b‖ ^ 2`

### rank 18 score 51 — e9028f141e2b41dcba2414ce7a97ab219d53718e8baa8007693cdbd7970b2561
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_06.lean:82
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: sorry_near_original_line
- current line: `      _ = (q : ℝ)^2 - 2*‖a‖*q + ‖a‖^2 + ‖b‖^2 := by sorry`
- goal: `q n : ℕ / lamb : ℂ / a : ℝ := lamb.re / b : ℝ := lamb.im / h : lamb ∈ primitiveRoots n ℂ / h_lamb : lamb ≠ 1 / h_a_lt_one : ‖a‖ < 1 / ⊢ ‖↑q - ↑a‖ ^ 2 + ‖b‖ ^ 2 = ↑q ^ 2 - 2 * ‖a‖ * ↑q + ‖a‖ ^ 2 + ‖b‖ ^ 2`


## CURRENT_MAIN_FILE_MISSING_OR_PRIVATE — 9

### rank 29 score 49 — ec38ec32f348527bb348a9e223d9d30e0f53b4b03d10613229a5e4575dd97163
- repo: https://github.com/Verified-zkEVM/VCV-io
- path: VCVio/OracleComp/Constructions/UniformSelect.lean:350
- commit: 2049180482d07341e984f723c047d6d030a839bb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `α : Type / hα : OracleComp.SampleableType α / x y : Bool / ⊢ Pr[=x | /       @OracleComp.HasUniformSelect!.uniformSelect! (Vector Bool 2) Bool (OracleComp.hasUniformSelectVector Bool 1) /         #v[true, false]] = /     Pr[=y | /       @OracleComp.HasUniformSelect!.uniformSelect! (Vector Bool 2) Bool (OracleComp.hasUniformSelectVector Bool 1) /         #v[true, false]]`

### rank 30 score 49 — 4156353ec6b044543bb1b6dd23b5bb3daa4cb027bd632c458fe5f969f617f431
- repo: https://github.com/Verified-zkEVM/VCV-io
- path: VCVio/OracleComp/Constructions/UniformSelect.lean:351
- commit: 2049180482d07341e984f723c047d6d030a839bb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `α : Type / hα : OracleComp.SampleableType α / ⊢ Pr[⊥ | /       @OracleComp.HasUniformSelect!.uniformSelect! (Vector Bool 2) Bool (OracleComp.hasUniformSelectVector Bool 1) /         #v[true, false]] = /     0`

### rank 31 score 49 — ffc6faed4144e96c9783a450bf686e55cd936854ccd9a01999463def7171461e
- repo: https://github.com/Verified-zkEVM/VCV-io
- path: VCVio/OracleComp/Constructions/UniformSelect.lean:417
- commit: 2049180482d07341e984f723c047d6d030a839bb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `α✝ : Type / hα : OracleComp.SampleableType α✝ / α : Type / n : ℕ / inst✝ : OracleComp.SampleableType α / ⊢ Pr[⊥ | Nat.recAux (pure #v[]) (fun m ih => Vector.push <$> ih <*> OracleComp.uniformSample α inst✝) n] = 0`

### rank 34 score 49 — 0c9341ebe0d6c4cb72f03c0e9171c32d4bc729aab161ac9472ec96c1eab72286
- repo: https://github.com/YaelDillies/MiscYD
- path: MiscYD/PhD/VCDim/SmallAvDegImpExistsSmallOutDeg.lean:13
- commit: 27148468f2c268580e0d652a005a6ca6be6c10cb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `V : Type u_1 / inst✝ : Fintype V / G : SimpleGraph V / d : ℕ / hGcolorable : G.Colorable 2 / hGdeg : ∀ (s : Finset V), (induce (↑s) G).edgeFinset.card ≤ d * s.card / ⊢ ∃ r, Irreflexive r ∧ IsAsymm V r`

### rank 35 score 49 — c0acbf98edc41814cc15dbabda0a9e424741e334592233e83e057ca2bc642b8a
- repo: https://github.com/YaelDillies/MiscYD
- path: MiscYD/PhD/VCDim/HypercubeEdges.lean:113
- commit: 27148468f2c268580e0d652a005a6ca6be6c10cb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `α : Type u_1 / 𝓒 : Finset (Set α) / A : Set α / hA : A ∈ ↑𝓒 / B : Set α / hB : B ∈ ↑𝓒 / hAB : /   Subtype.val '' (Subtype.val ⁻¹' symmDiff A (⋂ B ∈ 𝓒, B)) = Subtype.val '' (Subtype.val ⁻¹' symmDiff B (⋂ B ∈ 𝓒, B)) / this : symmDiff (⋃ A ∈ 𝓒, A) (⋂ B ∈ 𝓒, B) = (⋃ A ∈ 𝓒, A) \ ⋂ B ∈ 𝓒, B / ⊢ A = B`

### rank 36 score 49 — b9ed920d243de604401e1327f9e8641bd8fea8bd555a9d823163685fba4c9e3b
- repo: https://github.com/YaelDillies/MiscYD
- path: MiscYD/PhD/VCDim/HypercubeEdges.lean:145
- commit: 27148468f2c268580e0d652a005a6ca6be6c10cb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `α : Type u_1 / 𝓕 : Finset (Set α) / d : ℕ / h𝓕 : IsNIPWith d ↑𝓕 / 𝓒 : Finset (Set α) / h𝓒 : failed to pretty print expression (use 'set_option pp.rawOnError true' for raw representation) / this : Finite ↑((⋃ A ∈ 𝓒, A) \ ⋂ A ∈ 𝓒, A) / ⊢ card (@SetFamily.hypercubeEdgeFinset α 𝓒) = /     card /       (@SetFamily.hypercubeEdgeFinset (↑((⋃ A ∈ 𝓒, A) \ ⋂ A ∈ 𝓒, A)) (@SetFamily.restrictFiniteSymmDiffComp`

### rank 37 score 49 — df663dfe8d8316f12f4c7042a38f0f6f2ffaafa71f29ee1075d22f1e1089c526
- repo: https://github.com/YaelDillies/MiscYD
- path: MiscYD/PhD/VCDim/HausslerPacking.lean:35
- commit: 27148468f2c268580e0d652a005a6ca6be6c10cb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `α : Type u_1 / inst✝ : Fintype α / 𝓕 : Finset (Set α) / k d : ℕ / isNIPWith_𝓕 : IsNIPWith d ↑𝓕 / isSeparated_𝓕 : /   IsSeparated (↑k / ↑(card α)) ((fun A => ((WithLp.equiv 1 ((α → ℝ) → α → ℝ)).symm A.indicator).ofLp 1) '' ↑𝓕) / hk : k ≤ card α / ⊢ ↑𝓕.card ≤ exp 1 * (↑d + 1) * (2 * exp 1 * (↑(card α) + 1) / (↑k + 2 * ↑d + 2))`

### rank 56 score 46 — c0c8d7af4231789ce7e0607fd31a063e2c6cc50a9d440c5210f2188662087067
- repo: https://github.com/Verified-zkEVM/VCV-io
- path: VCVio/OracleComp/Constructions/UniformSelect.lean:392
- commit: 2049180482d07341e984f723c047d6d030a839bb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `case succ / α✝ : Type / hα : OracleComp.SampleableType α✝ / α : Type / inst✝ : OracleComp.SampleableType α / m : ℕ / ih : /   ∀ (x : Vector α m), /     x ∈ support (Nat.recAux (pure #v[]) (fun m ih => Vector.push <$> ih <*> OracleComp.uniformSample α inst✝) m) / x : Vector α (m + 1) / ⊢ x ∈ support (Nat.recAux (pure #v[]) (fun m ih => Vector.push <$> ih <*> OracleComp.uniformSample α inst✝) (m + 1`

### rank 58 score 46 — 3710ba3423a4621a9550c92cdf5af001bbe76d544c470e3ae4112783128b997b
- repo: https://github.com/YaelDillies/MiscYD
- path: MiscYD/PhD/VCDim/SmallVCImpSmallCondVar.lean:36
- commit: 27148468f2c268580e0d652a005a6ca6be6c10cb
- lean: v4.26.0
- reason: gh: Not Found (HTTP 404)
- current line: `None`
- goal: `Ω : Type u_1 / X : Type u_2 / inst✝ : MeasurableSpace Ω / μ : Measure Ω / A : Ω → Set X / 𝓕 : Finset (Set X) / x : X / d : ℕ / isNIPWith_𝓕 : IsNIPWith d ↑𝓕 / hA : ∀ᵐ (ω : Ω) ∂μ, A ω ∈ 𝓕 / ⊢ condVar (MeasurableSpace.generateFrom sorry) (fun ω => (A ω).indicator 1 x) μ ≤ sorry`


## STALE_ALREADY_FIXED_OR_REMOVED — 9

### rank 1 score 67 — 589ac7b645ccf7c434f7686051ee627a04704b3141a80debcd2d2ed4358562b3
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_28.lean:64
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: no_sorry_in_current_file
- current line: ``
- goal: `α : Type u_1 / inst✝² : Fintype α / inst✝¹ : DecidableEq α / G : SimpleGraph α / inst✝ : DecidableRel G.Adj / e : Sym2 α / he : e ∈ G.edgeFinset / ⊢ {v | v ∈ e}.card = 2`

### rank 4 score 56 — 906671815dfd025bb15ea27e0ce0128125d71aedecd06eedbd4e38cedc0f9d12
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_44.lean:47
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: no_sorry_in_current_file
- current line: ``p₁ = m·q - ⌊p/q⌋·p`. This is the "smallest denominator" argument in pure arithmetic.`
- goal: `V : Type u / inst✝¹ : Fintype V / G : SimpleGraph V / inst✝ : Nonempty V / h : ∀ ⦃v w : V⦄, v ≠ w → Fintype.card ↑(G.commonNeighbors v w) = 1 / no_politician : ¬∃ v, ∀ (w : V), v ≠ w → G.Adj v w / ⊢ ∃ k, G.IsRegularOfDegree k`

### rank 5 score 56 — da24e07fcb6bd291f0b0bf6e660884ed7d2d36ec51111fd6df7a50e7818f17b7
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_44.lean:53
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: no_sorry_in_current_file
- current line: ``
- goal: `V : Type u / inst✝¹ : Fintype V / G : SimpleGraph V / inst✝ : Nonempty V / h : ∀ ⦃v w : V⦄, v ≠ w → Fintype.card ↑(G.commonNeighbors v w) = 1 / no_politician : ¬∃ v, ∀ (w : V), v ≠ w → G.Adj v w / lemma₁ : ∃ k, G.IsRegularOfDegree k / k : ℕ / hregular : G.IsRegularOfDegree k / n : ℕ := Fintype.card V / ⊢ k + (n - 1) = k * k`

### rank 27 score 50 — b07683f6ab18e151fdf78413c11904c30039715a77b63111086c28ea9aacdee2
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_44.lean:106
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: no_sorry_in_current_file
- current line: `  have hAsq : (G.adjMatrix ℝ) ^ 2 = ((d : ℝ) - 1) • (1 : Matrix V V ℝ) + J := by`
- goal: `V : Type u / inst✝¹ : Fintype V / G : SimpleGraph V / inst✝ : Nonempty V / h : ∀ ⦃v w : V⦄, v ≠ w → Fintype.card ↑(G.commonNeighbors v w) = 1 / no_politician : ¬∃ v, ∀ (w : V), v ≠ w → G.Adj v w / lemma₁ : ∃ k, G.IsRegularOfDegree k / k : ℕ / hregular : G.IsRegularOfDegree k / n : ℕ := Fintype.card V / eq₁ : n = k ^ 2 - k + 1 / this : 2 < k / A : Matrix V V ℝ := adjMatrix ℝ G / ⊢ A ^ 2 = (k - 1) •`

### rank 28 score 50 — 5da45fd1b0757696c95175b26e7447967d88379d49946377f8bff41fcd423517
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_44.lean:108
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: no_sorry_in_current_file
- current line: `    ext i j`
- goal: `V : Type u / inst✝¹ : Fintype V / G : SimpleGraph V / inst✝ : Nonempty V / h : ∀ ⦃v w : V⦄, v ≠ w → Fintype.card ↑(G.commonNeighbors v w) = 1 / no_politician : ¬∃ v, ∀ (w : V), v ≠ w → G.Adj v w / lemma₁ : ∃ k, G.IsRegularOfDegree k / k : ℕ / hregular : G.IsRegularOfDegree k / n : ℕ := Fintype.card V / eq₁ : n = k ^ 2 - k + 1 / this✝ : 2 < k / A : Matrix V V ℝ := adjMatrix ℝ G / this : A ^ 2 = (k `

### rank 32 score 49 — 55551c0e4cda44dfa713bd61c3b86c2bb98bb60043db9166fc216eba1364739d
- repo: https://github.com/Verified-zkEVM/VCV-io
- path: VCVio/EvalDist/Monad/Basic.lean:168
- commit: 2049180482d07341e984f723c047d6d030a839bb
- lean: v4.26.0
- reason: no_sorry_in_current_file
- current line: `  rw [ENNReal.tsum_comm]`
- goal: `α β : Type u / m : Type u → Type v / inst✝³ : Monad m / inst✝² : HasEvalSPMF m / inst✝¹ : HasEvalFinset m / mx : m α / my : α → m β / inst✝ : DecidableEq α / y : β / ⊢ (Function.support fun x => Pr[=x | mx] * Pr[=y | my x]) ⊆ ↑(finSupport mx)`

### rank 33 score 49 — 9ae44a37f90f25f7f3579cbc988e35d4cbd192aa1f3eed6c3b816da37f0b066a
- repo: https://github.com/Verified-zkEVM/VCV-io
- path: VCVio/EvalDist/Monad/Basic.lean:173
- commit: 2049180482d07341e984f723c047d6d030a839bb
- lean: v4.26.0
- reason: no_sorry_in_current_file
- current line: `    (my : α → m β) :`
- goal: `α β : Type u / m : Type u → Type v / inst✝³ : Monad m / inst✝² : HasEvalSPMF m / inst✝¹ : HasEvalFinset m / mx : m α / my : α → m β / inst✝ : DecidableEq α / q : β → Prop / ⊢ (Function.support fun x => Pr[=x | mx] * Pr[q | my x]) ⊆ ↑(finSupport mx)`

### rank 62 score 46 — 5b74d6f2a86f1a585ea29c3f7223d38423d944547d9ea18bebafa29358a577fe
- repo: https://github.com/dwrensha/compfiles
- path: Compfiles/Imo2021P6.lean:28
- commit: a2ff4bb1396c3bc8047103a0a45a00e2c57571c4
- lean: v4.27.0-rc1
- reason: no_sorry_in_current_file
- current line: `attribute [local instance] Matrix.seminormedAddCommGroup`
- goal: `m : ℕ / hm : 2 ≤ m / A : Finset ℤ / B : Fin m → Finset ℤ / hB : ∀ (k : Fin m), B k ⊆ A / hs : ∀ (k : Fin m), ∑ b ∈ B k, b = ↑m ^ (↑k + 1) / ⊢ m ≤ 2 * A.card`

### rank 63 score 46 — 1d993ef3cbe15f104a66533331da727f7e5349c23c946339c14cc17fb5644a13
- repo: https://github.com/dwrensha/compfiles
- path: Compfiles/Imo2018P3.lean:68
- commit: a2ff4bb1396c3bc8047103a0a45a00e2c57571c4
- lean: v4.27.0-rc1
- reason: no_sorry_in_current_file
- current line: `private lemma TN_def : (∑ i ∈ Finset.range NR, (i + 1)) = TN := rfl`
- goal: `t : Imo2018P3.antipascal_triangle 2018 / ht : /   ∀ (n : ℕ), /     1 ≤ n → /       n ≤ ∑ i ∈ Finset.range 2018, (i + 1) → /         ∃ r ≤ 2018, ∃ c < r, Imo2018P3.antipascal_triangle.f 2018 t (Imo2018P3.Coords.mk r c) = n / ⊢ False`


## CURRENT_MAIN_HAS_OTHER_SORRIES — 8

### rank 21 score 51 — 8016f8985acb6660eed960814e007951f849259a5af1b841a776b0f4f04a28b5
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_01.lean:345
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: file_has_sorry_but_not_near_original_line
- current line: `        assumption`
- goal: `⊢ Tendsto (fun n => ∑ p ∈ range n with Nat.Prime p, 1 / ↑p) atTop atTop`

### rank 55 score 46 — 6a64518766b8ed911bd5e11491be757a2cb2e94557e0fa67725b13bc6a2d0466
- repo: https://github.com/Verified-zkEVM/ArkLib
- path: ArkLib/Data/MvPolynomial/Interpolation.lean:171
- commit: f04465d1faac1b46505a53fa5af90cfa223ad823
- lean: v4.26.0
- reason: file_has_sorry_but_not_near_original_line
- current line: `    (hEval : ∀ x ∈ piFinset fun i ↦ S i, eval x p = 0) :`
- goal: `σ : Type u_1 / inst✝³ : DecidableEq σ / inst✝² : Fintype σ / R : Type u_2 / inst✝¹ : CommRing R / inst✝ : IsDomain R / p q : MvPolynomial σ R / S : σ → Finset R / hDegree : ∀ (i : σ), degreeOf i p < (S i).card / hEval : ∀ x ∈ piFinset fun i => S i, (eval x) p = (eval x) q / ⊢ p = q`

### rank 73 score 46 — a78ca65b87970fabbb5521a907ce4ba2f71b6713d4a4543a6efc2f9edbf87d37
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_01.lean:187
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: file_has_sorry_but_not_near_original_line
- current line: `  { toFun := fun n => (n : ℝ)⁻¹`
- goal: `n : ℕ / x : ℝ / hxge : x ≥ ↑n / hxlt : x < ↑n + 1 / ⊢ Real.log x ≤ ∑ k ∈ Icc 1 n, (↑k)⁻¹`

### rank 74 score 46 — 3a6b2a478e05ba710523dd9b9db72e3f36a1bd7e3f0668bd4b09d4bc65d6d646
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_01.lean:188
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: file_has_sorry_but_not_near_original_line
- current line: `    map_one' := by`
- goal: `n : ℕ / x : ℝ / hxge : x ≥ ↑n / hxlt : x < ↑n + 1 / ⊢ ∑ k ∈ Icc 1 n, (↑k)⁻¹ ≤ ∑' (m : ↑(S₁ x)), (↑↑m)⁻¹`

### rank 75 score 46 — 23148bda427a6f78e69b003d58a8a7ac9ca69d51fdc533e4ff0ab1688d783ecc
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_01.lean:189
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: file_has_sorry_but_not_near_original_line
- current line: `      -- The inverse of 1 is 1.`
- goal: `n : ℕ / x : ℝ / hxge : x ≥ ↑n / hxlt : x < ↑n + 1 / ⊢ ∑' (m : ↑(S₁ x)), (↑↑m)⁻¹ ≤ ∏ p ∈ ⌊x⌋.natAbs.primesBelow, ∑' (k : ℕ), (↑p ^ k)⁻¹`

### rank 76 score 46 — 96336aaeb19b31c66ae605692b4f9d1cfd72a2867b2778a68a60cda20153bd18
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_01.lean:190
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: file_has_sorry_but_not_near_original_line
- current line: `      norm_num`
- goal: `n : ℕ / x : ℝ / hxge : x ≥ ↑n / hxlt : x < ↑n + 1 / ⊢ ∏ p ∈ ⌊x⌋.natAbs.primesBelow, ∑' (k : ℕ), (↑p ^ k)⁻¹ ≤ /     ↑(∏ k ∈ Icc 1 (primeCountingReal x), nth Nat.Prime k / (nth Nat.Prime k - 1))`

### rank 77 score 46 — 1404fd8c29641a0312cb9c9f79fb69017a1274c372110ba04643eb4dca1d0478
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_01.lean:191
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: file_has_sorry_but_not_near_original_line
- current line: `    map_zero' := by`
- goal: `n : ℕ / x : ℝ / hxge : x ≥ ↑n / hxlt : x < ↑n + 1 / ⊢ ↑(∏ k ∈ Icc 1 (primeCountingReal x), nth Nat.Prime k / (nth Nat.Prime k - 1)) ≤ /     ↑(∏ k ∈ Icc 1 (primeCountingReal x), (k + 1) / k)`

### rank 78 score 46 — e6222c1b47231ce76b117b9dc77d5c31227fdac08612cffc73b09c011e9c48c0
- repo: https://github.com/mo271/FormalBook
- path: FormalBook/Chapter_01.lean:192
- commit: 865934361ca7005e0a874efb39f5809117052e85
- lean: v4.27.0-rc1
- reason: file_has_sorry_but_not_near_original_line
- current line: `      -- By definition of division, we know that $0 / 0 = 0$.`
- goal: `n : ℕ / x : ℝ / hxge : x ≥ ↑n / hxlt : x < ↑n + 1 / ⊢ ↑(∏ k ∈ Icc 1 (primeCountingReal x), (k + 1) / k) ≤ ↑(primeCountingReal x) + 1`


## Recommended next queue

- CURRENT_MAIN_PR_CANDIDATE | rank 2 | score 59 | mo271/FormalBook | FormalBook/Chapter_05.lean:53 | 63db8ffc0199cc1a713aeb07f33c5fcf900a66b1af2ab8a71cc96740cc9dd99b
- CURRENT_MAIN_PR_CANDIDATE | rank 3 | score 59 | mo271/FormalBook | FormalBook/Chapter_05.lean:54 | 1d90823a9b08f76f3b0edc5bda1886cc28d47c4f846b149aeb6e1666efbac94f
- CURRENT_MAIN_PR_CANDIDATE | rank 6 | score 56 | mo271/FormalBook | FormalBook/Chapter_20.lean:96 | 8335cf4f29731301b3bd5d17cf0c43d7fc3130a2328288efb263a59369451fd9
- CURRENT_MAIN_PR_CANDIDATE | rank 7 | score 51 | mo271/FormalBook | FormalBook/Chapter_05.lean:59 | 7d588d7ae944f63fa0740a194ef64639dc06e9cafdf4362755e400ac34277a39
- CURRENT_MAIN_PR_CANDIDATE | rank 8 | score 51 | mo271/FormalBook | FormalBook/Chapter_05.lean:63 | ffa953c8de92b5d64ee0bac067a51eedd95321e583b8133058a2474c6543d316
- CURRENT_MAIN_PR_CANDIDATE | rank 9 | score 51 | mo271/FormalBook | FormalBook/Chapter_05.lean:84 | 5344347634ad66d64488f8ee4c91b5b044a07a33eb1cdc47e16c3f270b6aae73
- CURRENT_MAIN_PR_CANDIDATE | rank 10 | score 51 | mo271/FormalBook | FormalBook/Chapter_05.lean:113 | fcd7001b7b076fe7885f3358723d519d3b14e481b2439a23f90b98b5f7f9f99f
- CURRENT_MAIN_PR_CANDIDATE | rank 11 | score 51 | mo271/FormalBook | FormalBook/Chapter_09.lean:619 | 0c61aa8c3887d83d28dcf0e2da0b2af5f25c08b40055095f06cb28e43d533d7c
- CURRENT_MAIN_PR_CANDIDATE | rank 12 | score 51 | mo271/FormalBook | FormalBook/Chapter_09.lean:615 | 69053d06c5a730c0428d85a84b5a3c1f2b0aeacdc44a92fcb01a2b19cd76dde6
- CURRENT_MAIN_PR_CANDIDATE | rank 13 | score 51 | mo271/FormalBook | FormalBook/Chapter_06.lean:73 | 5e44f965721b80762f0079dcc54d0d29fcd3f7e7b200ea577332f68b0bf2a10c