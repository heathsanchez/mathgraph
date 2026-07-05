# SorryDB v4.6.8 — FormalBook EdgeCard Patch004

## Result

- status: PATCH004_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Probe available names

- SimpleGraph.mem_edgeFinset
- SimpleGraph.mem_edgeSet
- SimpleGraph.edgeSet
- SimpleGraph.edgeFinset
- Sym2.IsDiag
- Sym2.mem_iff
- Sym2.mk_eq_mk_iff
- Sym2.ind
- Sym2.exists
- Sym2.toFinset
- Sym2.mem_toFinset
- Sym2.card_toFinset

## Variant Summary

- v01_by_simpa_edgeSet: module_rc=1, seconds=40.29, target_sorry=False
- v02_by_simp_edgeFinset_at_he: module_rc=1, seconds=41.69, target_sorry=False
- v03_by_simp_edgeSet_at_he: module_rc=1, seconds=33.31, target_sorry=False
- v04_by_cases_sym2_ind: module_rc=1, seconds=35.36, target_sorry=False
- v05_by_cases_sym2_ind_simp_all: module_rc=1, seconds=34.72, target_sorry=False
- v06_by_cases_sym2_ind_aesop: module_rc=1, seconds=36.89, target_sorry=False
- v07_by_by_contra_diag: module_rc=1, seconds=38.19, target_sorry=False
- v08_by_exact_sym2_card_eq_two: module_rc=1, seconds=33.33, target_sorry=False
- v09_by_simpa_sym2_card_eq_two: module_rc=1, seconds=36.4, target_sorry=False
- v10_by_exact_card_eq_two_iff: module_rc=1, seconds=35.73, target_sorry=False
- v11_by_trace_after_simp_he: module_rc=0, seconds=37.03, target_sorry=False
- v12_by_trace_raw: module_rc=0, seconds=40.77, target_sorry=False

## Grep Recon

====================================================================================================
PATTERN: card.*Sym2
FormalBook/Mathlib/EdgeFinset.lean:59: lemma one_le_card_toFinset {z : Sym2 α} : 1 ≤ z.toFinset.card := by
FormalBook/Mathlib/EdgeFinset.lean:62: lemma card_toFinset_le_two {z : Sym2 α} : z.toFinset.card ≤ 2 := by
FormalBook/Mathlib/EdgeFinset.lean:77: -- lemma card_toFinset_of_mem_edgeSet (e : Sym2 α) (he : e ∈ G.edgeSet) :
FormalBook/Mathlib/EdgeFinset.lean:85: -- lemma card_filter_mem_of_mem_edgeSet [Fintype α] (e : Sym2 α) (he : e ∈ G.edgeSet) :
FormalBook/Mathlib/EdgeFinset.lean:102: -- lemma card_toFinset_of_mem_edgeFinset (e : Sym2 α) (he : e ∈ G.edgeFinset) :
FormalBook/Mathlib/EdgeFinset.lean:106: -- lemma card_filter_mem_of_mem_edgeFinset (e : Sym2 α) (he : e ∈ G.edgeFinset) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:128:   simp_rw [Set.toFinset_card, edgeSet_top, ← Sym2.card_diagSet_compl]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Hamiltonian.lean:192:     (h_order : 3 ≤ Fintype.card V) (e : Sym2 V) (he : G.IsBridge e) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DegreeSum.lean:81: theorem dart_edge_fiber_card [DecidableEq V] (e : Sym2 V) (h : e ∈ G.edgeSet) :
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:126: theorem card_image_diag (s : Finset α) : #(s.diag.image Sym2.mk) = #s := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:134: lemma two_mul_card_image_offDiag (s : Finset α) : 2 * #(s.offDiag.image Sym2.mk) = #s.offDiag := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:135:   rw [card_eq_sum_card_image (Sym2.mk : α × α → _), sum_const_nat (Sym2.ind _), mul_comm]
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:156: theorem card_image_offDiag (s : Finset α) : #(s.offDiag.image Sym2.mk) = (#s).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:160: theorem card_subtype_diag [Fintype α] : card { a : Sym2 α // a.IsDiag } = card α := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:169:     card { a : Sym2 α // ¬a.IsDiag } = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:178:     Fintype.card ((@Sym2.diagSet α)ᶜ : Set _) = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:179:   simp only [← card_subtype_not_diag, Sym2.diagSet_compl_eq_setOf_not_isDiag, Set.coe_setOf]
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:182: protected theorem card {α} [Fintype α] : card (Sym2 α) = Nat.choose (card α + 1) 2 :=
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:24: multiset of cardinality two (see `Sym2.equivMultiset`), there is a
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:666: lemma card_toMultiset {α : Type*} (z : Sym2 α) : z.toMultiset.card = 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:695: theorem card_toFinset_of_isDiag (z : Sym2 α) (h : z.IsDiag) : #(z : Sym2 α).toFinset = 1 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:701: theorem card_toFinset_of_not_isDiag (z : Sym2 α) (h : ¬z.IsDiag) : #(z : Sym2 α).toFinset = 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:708: theorem card_toFinset (z : Sym2 α) : #(z : Sym2 α).toFinset = if z.IsDiag then 1 else 2 := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:128:   simp_rw [Set.toFinset_card, edgeSet_top, ← Sym2.card_diagSet_compl]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Hamiltonian.lean:192:     (h_order : 3 ≤ Fintype.card V) (e : Sym2 V) (he : G.IsBridge e) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DegreeSum.lean:81: theorem dart_edge_fiber_card [DecidableEq V] (e : Sym2 V) (h : e ∈ G.edgeSet) :
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:126: theorem card_image_diag (s : Finset α) : #(s.diag.image Sym2.mk) = #s := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:134: lemma two_mul_card_image_offDiag (s : Finset α) : 2 * #(s.offDiag.image Sym2.mk) = #s.offDiag := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:135:   rw [card_eq_sum_card_image (Sym2.mk : α × α → _), sum_const_nat (Sym2.ind _), mul_comm]
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:156: theorem card_image_offDiag (s : Finset α) : #(s.offDiag.image Sym2.mk) = (#s).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:160: theorem card_subtype_diag [Fintype α] : card { a : Sym2 α // a.IsDiag } = card α := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:169:     card { a : Sym2 α // ¬a.IsDiag } = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:178:     Fintype.card ((@Sym2.diagSet α)ᶜ : Set _) = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:179:   simp only [← card_subtype_not_diag, Sym2.diagSet_compl_eq_setOf_not_isDiag, Set.coe_setOf]
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:182: protected theorem card {α} [Fintype α] : card (Sym2 α) = Nat.choose (card α + 1) 2 :=
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:24: multiset of cardinality two (see `Sym2.equivMultiset`), there is a
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:666: lemma card_toMultiset {α : Type*} (z : Sym2 α) : z.toMultiset.card = 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:695: theorem card_toFinset_of_isDiag (z : Sym2 α) (h : z.IsDiag) : #(z : Sym2 α).toFinset = 1 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:701: theorem card_toFinset_of_not_isDiag (z : Sym2 α) (h : ¬z.IsDiag) : #(z : Sym2 α).toFinset = 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:708: theorem card_toFinset (z : Sym2 α) : #(z : Sym2 α).toFinset = if z.IsDiag then 1 else 2 := by
====================================================================================================
PATTERN: Sym2.*card
FormalBook/Chapter_28.lean:65:       #check Sym2.card_support
FormalBook/Mathlib/EdgeFinset.lean:59: lemma one_le_card_toFinset {z : Sym2 α} : 1 ≤ z.toFinset.card := by
FormalBook/Mathlib/EdgeFinset.lean:62: lemma card_toFinset_le_two {z : Sym2 α} : z.toFinset.card ≤ 2 := by
FormalBook/Mathlib/EdgeFinset.lean:79: --   refine Sym2.card_toFinset_of_not_isDiag ?_
FormalBook/Mathlib/EdgeFinset.lean:104: --   Sym2.card_toFinset_of_not_isDiag (not_isDiag_of_mem_edgeSet _ (mem_edgeFinset.mp he))
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:74:     (e : Sym2 V).toFinset.card = 2 :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:75:   Sym2.card_toFinset_of_not_isDiag e.val (G.not_isDiag_of_mem_edgeFinset e.prop)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:128:   simp_rw [Set.toFinset_card, edgeSet_top, ← Sym2.card_diagSet_compl]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean:842:   ∀ ⦃s : Set (Sym2 V)⦄, s.encard < k → (G.deleteEdges s).Reachable u v
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Triangle/Basic.lean:166:   · simpa [Sym2.forall, Nat.one_le_iff_ne_zero, -Finset.card_eq_zero, Finset.card_ne_zero,
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:125: /-- The `diag` of `s : Finset α` is sent on a finset of `Sym2 α` of card `#s`. -/
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:153: /-- The `offDiag` of `s : Finset α` is sent on a finset of `Sym2 α` of card `#s.offDiag / 2`.
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:160: theorem card_subtype_diag [Fintype α] : card { a : Sym2 α // a.IsDiag } = card α := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:169:     card { a : Sym2 α // ¬a.IsDiag } = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:178:     Fintype.card ((@Sym2.diagSet α)ᶜ : Set _) = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:182: protected theorem card {α} [Fintype α] : card (Sym2 α) = Nat.choose (card α + 1) 2 :=
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:666: lemma card_toMultiset {α : Type*} (z : Sym2 α) : z.toMultiset.card = 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:788: def equivMultiset (α : Type*) : Sym2 α ≃ { s : Multiset α // Multiset.card s = 2 } :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:74:     (e : Sym2 V).toFinset.card = 2 :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:75:   Sym2.card_toFinset_of_not_isDiag e.val (G.not_isDiag_of_mem_edgeFinset e.prop)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:128:   simp_rw [Set.toFinset_card, edgeSet_top, ← Sym2.card_diagSet_compl]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Connectivity/Connected.lean:842:   ∀ ⦃s : Set (Sym2 V)⦄, s.encard < k → (G.deleteEdges s).Reachable u v
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Triangle/Basic.lean:166:   · simpa [Sym2.forall, Nat.one_le_iff_ne_zero, -Finset.card_eq_zero, Finset.card_ne_zero,
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:125: /-- The `diag` of `s : Finset α` is sent on a finset of `Sym2 α` of card `#s`. -/
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:153: /-- The `offDiag` of `s : Finset α` is sent on a finset of `Sym2 α` of card `#s.offDiag / 2`.
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:160: theorem card_subtype_diag [Fintype α] : card { a : Sym2 α // a.IsDiag } = card α := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:169:     card { a : Sym2 α // ¬a.IsDiag } = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:178:     Fintype.card ((@Sym2.diagSet α)ᶜ : Set _) = (card α).choose 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Card.lean:182: protected theorem card {α} [Fintype α] : card (Sym2 α) = Nat.choose (card α + 1) 2 :=
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:666: lemma card_toMultiset {α : Type*} (z : Sym2 α) : z.toMultiset.card = 2 := by
.lake/packages/mathlib/Mathlib/Data/Sym/Sym2.lean:788: def equivMultiset (α : Type*) : Sym2 α ≃ { s : Multiset α // Multiset.card s = 2 } :=
====================================================================================================
PATTERN: edgeFinset
FormalBook/Chapter_20.lean:132: local notation "E" => G.edgeFinset
FormalBook/Chapter_28.lean:54: local notation "E" => G.edgeFinset
FormalBook/Chapter_28.lean:63:     -- FIXME: was (G.card_filter_mem_of_mem_edgeFinset e he)) but is commented out currently in Mathlib.EdgeFinset
FormalBook/Mathlib/EdgeFinset.lean:102: -- lemma card_toFinset_of_mem_edgeFinset (e : Sym2 α) (he : e ∈ G.edgeFinset) :
FormalBook/Mathlib/EdgeFinset.lean:104: --   Sym2.card_toFinset_of_not_isDiag (not_isDiag_of_mem_edgeSet _ (mem_edgeFinset.mp he))
FormalBook/Mathlib/EdgeFinset.lean:106: -- lemma card_filter_mem_of_mem_edgeFinset (e : Sym2 α) (he : e ∈ G.edgeFinset) :
FormalBook/Mathlib/EdgeFinset.lean:108: --   rw [← SimpleGraph.card_toFinset_of_mem_edgeFinset _ he]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:177: theorem IsTrail.length_le_card_edgeFinset [Fintype G.edgeSet] {u v : V}
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:178:     {w : G.Walk u v} (h : w.IsTrail) : w.length ≤ G.edgeFinset.card := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:183:   have : edges ⊆ G.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:185:     refine mem_edgeFinset.mpr ?_
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:339:   have : s.Finite := Set.Finite.subset (Set.finite_le_nat G.edgeFinset.card)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:340:     fun n ⟨_, _, _, hp, hn⟩ ↦ hn ▸ hp.length_le_card_edgeFinset
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:354:   have : s.Finite := Set.Finite.subset (Set.finite_le_nat G.edgeFinset.card)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:355:     fun n ⟨_, _, _, hp, hn⟩ ↦ hn ▸ hp.isTrail.length_le_card_edgeFinset
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:25: * `SimpleGraph.edgeFinset` is the `Finset` of edges in a graph, if `edgeSet` is finite
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:57: abbrev edgeFinset : Finset (Sym2 V) :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:61: theorem coe_edgeFinset : (G.edgeFinset : Set (Sym2 V)) = G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:66: theorem mem_edgeFinset : e ∈ G.edgeFinset ↔ e ∈ G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:69: theorem not_isDiag_of_mem_edgeFinset : e ∈ G.edgeFinset → ¬e.IsDiag :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:70:   not_isDiag_of_mem_edgeSet _ ∘ mem_edgeFinset.1
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:73: theorem card_toFinset_mem_edgeFinset [DecidableEq V] (e : G.edgeFinset) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:75:   Sym2.card_toFinset_of_not_isDiag e.val (G.not_isDiag_of_mem_edgeFinset e.prop)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:77: theorem edgeFinset_inj : G₁.edgeFinset = G₂.edgeFinset ↔ G₁ = G₂ := by simp
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:79: theorem edgeFinset_subset_edgeFinset : G₁.edgeFinset ⊆ G₂.edgeFinset ↔ G₁ ≤ G₂ := by simp
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:81: theorem edgeFinset_ssubset_edgeFinset : G₁.edgeFinset ⊂ G₂.edgeFinset ↔ G₁ < G₂ := by simp
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:83: @[mono, gcongr] alias ⟨_, edgeFinset_mono⟩ := edgeFinset_subset_edgeFinset
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:86: alias ⟨_, edgeFinset_strict_mono⟩ := edgeFinset_ssubset_edgeFinset
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:89: theorem edgeFinset_bot : (⊥ : SimpleGraph V).edgeFinset = ∅ := by simp [edgeFinset]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:92: theorem edgeFinset_sup [Fintype (edgeSet (G₁ ⊔ G₂))] [DecidableEq V] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:93:     (G₁ ⊔ G₂).edgeFinset = G₁.edgeFinset ∪ G₂.edgeFinset := by simp [edgeFinset]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:96: theorem edgeFinset_inf [DecidableEq V] : (G₁ ⊓ G₂).edgeFinset = G₁.edgeFinset ∩ G₂.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:97:   simp [edgeFinset]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:100: theorem edgeFinset_sdiff [DecidableEq V] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:101:     (G₁ \ G₂).edgeFinset = G₁.edgeFinset \ G₂.edgeFinset := by simp [edgeFinset]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:103: lemma disjoint_edgeFinset : Disjoint G₁.edgeFinset G₂.edgeFinset ↔ Disjoint G₁ G₂ := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:104:   simp_rw [← Finset.disjoint_coe, coe_edgeFinset, disjoint_edgeSet]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:106: lemma edgeFinset_eq_empty : G.edgeFinset = ∅ ↔ G = ⊥ := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:107:   rw [← edgeFinset_bot, edgeFinset_inj]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:109: lemma edgeFinset_nonempty : G.edgeFinset.Nonempty ↔ G ≠ ⊥ := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:110:   rw [Finset.nonempty_iff_ne_empty, edgeFinset_eq_empty.ne]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:112: theorem edgeFinset_card : #G.edgeFinset = Fintype.card G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:116: theorem edgeSet_univ_card : #(univ : Finset G.edgeSet) = #G.edgeFinset :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:117:   Fintype.card_of_subtype G.edgeFinset fun _ => mem_edgeFinset
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:122: theorem edgeFinset_top [DecidableEq V] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:123:     (⊤ : SimpleGraph V).edgeFinset = Sym2.diagSetᶜ.toFinset := by simp [← coe_inj]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:126: theorem card_edgeFinset_top_eq_card_choose_two [DecidableEq V] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:127:     #(⊤ : SimpleGraph V).edgeFinset = (Fintype.card V).choose 2 := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:131: theorem card_edgeFinset_le_card_choose_two : #G.edgeFinset ≤ (Fintype.card V).choose 2 := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:133:   rw [← card_edgeFinset_top_eq_card_choose_two]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:134:   exact card_le_card (edgeFinset_mono le_top)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:244:     G.incidenceFinset v = {e ∈ G.edgeFinset | v ∈ e} := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:250:     G.incidenceFinset v ⊆ G.edgeFinset :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:254: theorem degree_le_card_edgeFinset [Fintype G.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:255:     G.degree v ≤ #G.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:492: theorem card_edgeFinset_eq (f : G ≃g G') [Fintype G.edgeSet] [Fintype G'.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:493:     #G.edgeFinset = #G'.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:532: lemma edgeFinset_subset_sym2_of_support_subset (h : G.support ⊆ s) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:533:     G.edgeFinset ⊆ s.toFinset.sym2 := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:535:     mem_edgeFinset, mem_edgeSet, mk_mem_sym2_iff, Set.mem_toFinset]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:542: theorem map_edgeFinset_induce [DecidableEq V] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:543:     (G.induce s).edgeFinset.map (Embedding.subtype s).sym2Map
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:544:       = G.edgeFinset ∩ s.toFinset.sym2 := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:558: theorem map_edgeFinset_induce_of_support_subset (h : G.support ⊆ s) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:559:     (G.induce s).edgeFinset.map (Embedding.subtype s).sym2Map = G.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:561:   simpa [map_edgeFinset_induce] using edgeFinset_subset_sym2_of_support_subset h
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:565: theorem card_edgeFinset_induce_of_support_subset (h : G.support ⊆ s) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:566:     #(G.induce s).edgeFinset = #G.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:567:   rw [← map_edgeFinset_induce_of_support_subset h, card_map]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:569: theorem card_edgeFinset_induce_support :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:570:     #(G.induce G.support).edgeFinset = #G.edgeFinset :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:571:   card_edgeFinset_induce_of_support_subset subset_rfl
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:608: theorem edgeFinset_map (f : V ↪ W) (G : SimpleGraph V) [DecidableRel G.Adj] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:609:     (G.map f).edgeFinset = G.edgeFinset.map f.sym2Map := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:613: theorem card_edgeFinset_map (f : V ↪ W) (G : SimpleGraph V) [DecidableRel G.Adj] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:614:     #(G.map f).edgeFinset = #G.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:615:   rw [edgeFinset_map]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:616:   exact G.edgeFinset.card_map f.sym2Map
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/CompleteMultipartite.lean:293: theorem card_edgeFinset_completeEquipartiteGraph :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/CompleteMultipartite.lean:294:     #(completeEquipartiteGraph r t).edgeFinset = r.choose 2 * t ^ 2 := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:294: lemma IsTree.card_edgeFinset [Fintype V] [Fintype G.edgeSet] (hG : G.IsTree) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:295:     Finset.card G.edgeFinset + 1 = Fintype.card V := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:324:     simp only [mem_edgeFinset, Finset.mem_compl, Finset.mem_singleton, Sym2.forall, mem_edgeSet]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:371:   rw [Nat.card_eq_fintype_card, ← hT.card_edgeFinset, add_le_add_iff_right,
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:372:     Nat.card_eq_fintype_card, ← edgeFinset_card]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:379:   refine ⟨fun h ↦ ⟨h.isConnected, by simpa using h.card_edgeFinset⟩, fun ⟨h₁, h₂⟩ ↦ ⟨h₁, ?_⟩⟩
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:383:   rw [Nat.card_eq_fintype_card, ← edgeFinset_card, ← h₂, Nat.card_eq_fintype_card,
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:384:     ← edgeFinset_card, add_lt_add_iff_right]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:391:   · have := h.card_edgeFinset
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Matching.lean:224:   use M.coe.edgeFinset.card
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:90: @[simp] theorem edgeFinset_deleteEdges [DecidableEq V] [Fintype G.edgeSet] (s : Finset (Sym2 V))
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:92:     (G.deleteEdges s).edgeFinset = G.edgeFinset \ s := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:154: theorem card_edgeFinset_induce_compl_singleton (G : SimpleGraph V) [DecidableRel G.Adj] (x : V) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:155:     #(G.induce {x}ᶜ).edgeFinset = #(G.deleteIncidenceSet x).edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:159:   apply card_edgeFinset_induce_of_support_subset
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:167: theorem edgeFinset_deleteIncidenceSet_eq_sdiff (G : SimpleGraph V) [DecidableRel G.Adj] (x : V) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:168:     (G.deleteIncidenceSet x).edgeFinset = G.edgeFinset \ G.incidenceFinset x := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:174: theorem card_edgeFinset_deleteIncidenceSet (G : SimpleGraph V) [DecidableRel G.Adj] (x : V) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:175:     #(G.deleteIncidenceSet x).edgeFinset = #G.edgeFinset - G.degree x := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:177:     edgeFinset_deleteIncidenceSet_eq_sdiff]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:181: theorem edgeFinset_deleteIncidenceSet_eq_filter (G : SimpleGraph V) [DecidableRel G.Adj] (x : V) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:182:     (G.deleteIncidenceSet x).edgeFinset = G.edgeFinset.filter (x ∉ ·) := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:183:   rw [edgeFinset_deleteIncidenceSet_eq_sdiff, sdiff_eq_filter]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:189:   rwa [mem_edgeFinset] at h
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:213:   ∀ ⦃s⦄, s ⊆ G.edgeFinset → p (G.deleteEdges s) → r ≤ #s
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:219:       H ≤ G → p H → r ≤ #G.edgeFinset - #H.edgeFinset := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:222:   · have := h (sdiff_subset (t := H.edgeFinset))
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:223:     simp only [deleteEdges_sdiff_eq_of_le hHG, edgeFinset_mono hHG, card_sdiff_of_subset,
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:224:       card_le_card, coe_sdiff, coe_edgeFinset, Nat.cast_sub] at this
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:227:     simpa [card_sdiff_of_subset hs, edgeFinset_deleteEdges, -Set.toFinset_card, Nat.cast_sub,
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/DeleteEdges.lean:235: lemma DeleteFar.le_card_edgeFinset (h : G.DeleteFar p r) (hp : p ⊥) : r ≤ #G.edgeFinset :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:87: theorem edgeFinset_replaceVertex_of_not_adj (hn : ¬G.Adj s t) : (G.replaceVertex s t).edgeFinset =
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:88:     G.edgeFinset \ G.incidenceFinset t ∪ (G.neighborFinset s).image (s(·, t)) := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:93: theorem edgeFinset_replaceVertex_of_adj (ha : G.Adj s t) : (G.replaceVertex s t).edgeFinset =
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:94:     (G.edgeFinset \ G.incidenceFinset t ∪ (G.neighborFinset s).image (s(·, t))) \ {s(t, t)} := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:100:     Disjoint (G.edgeFinset \ G.incidenceFinset t) ((G.neighborFinset s).image (s(·, t))) := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:110: theorem card_edgeFinset_replaceVertex_of_not_adj (hn : ¬G.Adj s t) :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:111:     #(G.replaceVertex s t).edgeFinset = #G.edgeFinset + G.degree s - G.degree t := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:112:   have inc : G.incidenceFinset t ⊆ G.edgeFinset := by simp [incidenceFinset, incidenceSet_subset]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Operations.lean:113:   rw [G.edgeFinset_replaceVertex_of_not_adj hn,
====================================================================================================
PATTERN: edgeSet
FormalBook/Chapter_45.lean:258:   ∀ c : (completeGraph (Fin N)).edgeSet → Fin 2,
FormalBook/Chapter_45.lean:259:   ( ∃ g : completeGraph (Fin m) →g completeGraph (Fin N), ∀ e : (completeGraph (Fin m)).edgeSet,
FormalBook/Chapter_45.lean:261:   ( ∃ h : completeGraph (Fin n) →g completeGraph (Fin N), ∀ e : (completeGraph (Fin n)).edgeSet,
FormalBook/Chapter_45.lean:313:   Inf {N : ℕ | ∃ (c : V → ℝ × ℝ) (f : G.edgeSet → (Set.Icc (0:ℝ) 1) → ℝ × ℝ),
FormalBook/Chapter_45.lean:315:                   ∀ (e : G.edgeSet) (v : V) (h : v ∈ (e : Sym2 V)),
FormalBook/Chapter_45.lean:321: theorem theorem_4 {V : Type _} [Fintype V] (G : SimpleGraph V) [Fintype G.edgeSet] (m n : ℕ)
FormalBook/Chapter_45.lean:322:   (H : m ≥ 4 * n) (h_n : n = Fintype.card V) (h_m : m = Fintype.card G.edgeSet) :
FormalBook/Mathlib/EdgeFinset.lean:77: -- lemma card_toFinset_of_mem_edgeSet (e : Sym2 α) (he : e ∈ G.edgeSet) :
FormalBook/Mathlib/EdgeFinset.lean:81: --   have := (not_isDiag_of_mem_edgeSet _ he)
FormalBook/Mathlib/EdgeFinset.lean:85: -- lemma card_filter_mem_of_mem_edgeSet [Fintype α] (e : Sym2 α) (he : e ∈ G.edgeSet) :
FormalBook/Mathlib/EdgeFinset.lean:87: --   rw [← SimpleGraph.card_toFinset_of_mem_edgeSet _ he]
FormalBook/Mathlib/EdgeFinset.lean:104: --   Sym2.card_toFinset_of_not_isDiag (not_isDiag_of_mem_edgeSet _ (mem_edgeFinset.mp he))
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:62: refer to the `vertexSet` and `edgeSet` of `G : Graph α β`.
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:73: as described by vertex and edge sets `vertexSet : Set α` and `edgeSet : Set β`,
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:76: The `edgeSet` structure field can be inferred from `IsLink`
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:78: for `edgeSet` and `edge_mem_iff_exists_isLink` that use `IsLink`).
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:81: and furthermore having `edgeSet` separate can be convenient for
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:91:   edgeSet : Set β := {e | ∃ x y, IsLink e x y}
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:93:   isLink_symm : ∀ ⦃e⦄, e ∈ edgeSet → (Symmetric <| IsLink e)
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:97:   edge_mem_iff_exists_isLink : ∀ e, e ∈ edgeSet ↔ ∃ x y, IsLink e x y := by exact fun _ ↦ Iff.rfl
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:108: /-- `E(G)` denotes the `edgeSet` of a graph `G`. -/
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:109: scoped notation "E(" G ")" => Graph.edgeSet G
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:128: lemma exists_isLink_of_mem_edgeSet (h : e ∈ E(G)) : ∃ x y, G.IsLink e x y :=
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:131: lemma edgeSet_eq_setOf_exists_isLink : E(G) = {e | ∃ x y, G.IsLink e x y} :=
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:308: /-- `edgeSet` can be determined using `IsLink`, so the graph constructed from `G.vertexSet` and
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:309: `G.IsLink` using any value for `edgeSet` is equal to `G` itself. -/
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:330:   simp [edgeSet_eq_setOf_exists_isLink, h]
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:346: theorem incidenceSet_subset_edgeSet (x : α) : G.incidenceSet x ⊆ E(G) :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:177: theorem IsTrail.length_le_card_edgeFinset [Fintype G.edgeSet] {u v : V}
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:186:     apply w.edges_subset_edgeSet
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:334:     [Finite G.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:337:   have := Fintype.ofFinite G.edgeSet
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:349:     [Finite G.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:352:   have := Fintype.ofFinite G.edgeSet
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:15: This file defines finite versions of `edgeSet`, `neighborSet` and `incidenceSet` and proves some
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:25: * `SimpleGraph.edgeFinset` is the `Finset` of edges in a graph, if `edgeSet` is finite
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:54: variable {G₁ G₂ : SimpleGraph V} [Fintype G.edgeSet] [Fintype G₁.edgeSet] [Fintype G₂.edgeSet]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:56: /-- The `edgeSet` of the graph as a `Finset`. -/
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:58:   Set.toFinset G.edgeSet
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:61: theorem coe_edgeFinset : (G.edgeFinset : Set (Sym2 V)) = G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:66: theorem mem_edgeFinset : e ∈ G.edgeFinset ↔ e ∈ G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:70:   not_isDiag_of_mem_edgeSet _ ∘ mem_edgeFinset.1
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:92: theorem edgeFinset_sup [Fintype (edgeSet (G₁ ⊔ G₂))] [DecidableEq V] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:104:   simp_rw [← Finset.disjoint_coe, coe_edgeFinset, disjoint_edgeSet]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:112: theorem edgeFinset_card : #G.edgeFinset = Fintype.card G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:116: theorem edgeSet_univ_card : #(univ : Finset G.edgeSet) = #G.edgeFinset :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:128:   simp_rw [Set.toFinset_card, edgeSet_top, ← Sym2.card_diagSet_compl]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:243: theorem incidenceFinset_eq_filter [DecidableEq V] [Fintype G.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:249: theorem incidenceFinset_subset [DecidableEq V] [Fintype G.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:254: theorem degree_le_card_edgeFinset [Fintype G.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:492: theorem card_edgeFinset_eq (f : G ≃g G') [Fintype G.edgeSet] [Fintype G'.edgeSet] :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:535:     mem_edgeFinset, mem_edgeSet, mk_mem_sym2_iff, Set.mem_toFinset]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:546:     Set.mem_toFinset, mem_edgeSet, comap_adj, Embedding.sym2Map_apply, Embedding.coe_subtype,
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:611:   exact G.edgeSet_map f
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/CompleteMultipartite.lean:259:   rw [← edgeSet_nonempty, ← Nat.succ_le_iff, ← Fin.nontrivial_iff_two_le, ← Nat.pos_iff_ne_zero,
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/CompleteMultipartite.lean:263:     rw [mem_edgeSet, completeEquipartiteGraph_adj] at he
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/CompleteMultipartite.lean:266:     rw [mem_edgeSet, completeEquipartiteGraph_adj]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Dart.lean:69: theorem Dart.edge_mem (d : G.Dart) : d.edge ∈ G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:105:     ∃ H ∈ Hs, ∀ e ∈ p.edges, e ∈ H.edgeSet := by
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:112:     simpa using ⟨H, hH, (le_iff_adj.mp h₂) _ _ h_adj, fun a ha => edgeSet_mono h₁ (ih a ha)⟩
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Acyclic.lean:174:     G.IsAcyclic ↔ ∀ ⦃e⦄, e ∈ (G.edgeSet) → G.IsBridge e := by
.lake/packages