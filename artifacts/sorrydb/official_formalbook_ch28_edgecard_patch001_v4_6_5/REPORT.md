# SorryDB v4.6.5 — FormalBook Chapter_28 EdgeCard Patch001

## Target

- Official SorryDB ID: 589ac7b645ccf7c434f7686051ee627a04704b3141a80debcd2d2ed4358562b3
- Repo: https://github.com/mo271/FormalBook
- Commit: 865934361ca7005e0a874efb39f5809117052e85
- File: FormalBook/Chapter_28.lean
- Line: 64
- Goal: `e ∈ G.edgeFinset ⊢ {v | v ∈ e}.card = 2`

## Result

- status: PATCH001_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Variant Summary

- v01_simpa_using_he: file_rc=1, seconds=35.2, target_sorry=False, module_rc=None
- v02_simpa: file_rc=1, seconds=30.8, target_sorry=False, module_rc=None
- v03_exact_e_card: file_rc=1, seconds=35.51, target_sorry=False, module_rc=None
- v04_simpa_using_e_card: file_rc=1, seconds=32.75, target_sorry=False, module_rc=None
- v05_exact_sym2_card: file_rc=1, seconds=32.99, target_sorry=False, module_rc=None
- v06_simpa_using_sym2_card: file_rc=1, seconds=40.82, target_sorry=False, module_rc=None
- v07_have_then_simpa: file_rc=1, seconds=32.33, target_sorry=False, module_rc=None
- v08_aesop: file_rc=1, seconds=31.5, target_sorry=False, module_rc=None
- v09_tauto: file_rc=1, seconds=32.47, target_sorry=False, module_rc=None
- v10_trace: file_rc=1, seconds=34.9, target_sorry=False, module_rc=None

## Target Window

0055: local notation "d(" v ")" => G.degree v
0056: local notation "I(" v ")" => G.incidenceFinset v
0057: 
0058: lemma handshaking : ∑ v, d(v) = 2 * #E := by
0059:   calc  ∑ v, d(v)
0060:     _ = ∑ v, #I(v)             := by simp [G.card_incidenceFinset_eq_degree]
0061:     _ = ∑ v, #{e ∈ E | v ∈ e}  := by simp [G.incidenceFinset_eq_filter]
0062:     _ = ∑ e ∈ E, #{v | v ∈ e}  := Finset.sum_card_bipartiteAbove_eq_sum_card_bipartiteBelow _
0063:     -- FIXME: was (G.card_filter_mem_of_mem_edgeFinset e he)) but is commented out currently in Mathlib.EdgeFinset
0064:     _ = ∑ e ∈ E, 2             := Finset.sum_congr rfl (λ e he ↦ sorry)
0065:     _ = 2 * ∑ e ∈ E, 1         := (Finset.mul_sum E (λ _ ↦ 1) 2).symm
0066:     _ = 2 * #E                 := by rw [Finset.card_eq_sum_ones E]
0067: 
0068: end chapter28

## Recon

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
====================================================================================================
PATTERN: Sym2
FormalBook/Chapter_20.lean:154:   let sum_deg (e : Sym2 α) : ℕ := Sym2.lift ⟨λ x y ↦ d(x) + d(y), by simp [Nat.add_comm]⟩ e
FormalBook/Chapter_20.lean:157:   have adj_degree_bnd' (e : Sym2 α) (he: e ∈ E) : sum_deg e ≤ n := by
FormalBook/Chapter_45.lean:315:                   ∀ (e : G.edgeSet) (v : V) (h : v ∈ (e : Sym2 V)),
FormalBook/Chapter_45.lean:316:                     ({v, Sym2.Mem.other h} :Set V).image c = (Coe.coe ⁻¹' ({0,1} : set ℝ)).image (f e) ∧
FormalBook/Mathlib/EdgeFinset.lean:7: section Mathlib.Data.Sym.Sym2
FormalBook/Mathlib/EdgeFinset.lean:9: namespace Sym2
FormalBook/Mathlib/EdgeFinset.lean:13: theorem exists_eq (z : Sym2 α) : ∃ x y, z = s(x, y) :=
FormalBook/Mathlib/EdgeFinset.lean:16: @[simp] theorem setOf_mem_eq {z : Sym2 α} : {v | v ∈ z} = z := rfl
FormalBook/Mathlib/EdgeFinset.lean:21: theorem isDiag_iff_exists {z : Sym2 α} : z.IsDiag ↔ ∃ x, z = s(x, x) := by
FormalBook/Mathlib/EdgeFinset.lean:24: theorem not_isDiag_iff_exists {z : Sym2 α} : ¬ z.IsDiag ↔ ∃ x y, x ≠ y ∧ z = s(x, y) := by
FormalBook/Mathlib/EdgeFinset.lean:33: instance : Coe (Sym2 α) (Multiset α) := ⟨Sym2.toMultiset⟩
FormalBook/Mathlib/EdgeFinset.lean:40: instance : Coe (Sym2 α) (Finset α) := ⟨Sym2.toFinset⟩
FormalBook/Mathlib/EdgeFinset.lean:43:   ext; rw [Sym2.toFinset, Sym2.toMultiset]; simp
FormalBook/Mathlib/EdgeFinset.lean:45: @[simp] lemma toFinset_toMultiset {s : Sym2 α} : (s : Multiset α).toFinset = (s : Finset α) := rfl
FormalBook/Mathlib/EdgeFinset.lean:47: @[simp] lemma coe_toFinset {z : Sym2 α} : ((z : Finset α) : Set α) = z := by
FormalBook/Mathlib/EdgeFinset.lean:50: lemma toFinset_eq [Fintype α] {e : Sym2 α} : (e : Finset α) = {v | v ∈ e}.toFinset := by
FormalBook/Mathlib/EdgeFinset.lean:59: lemma one_le_card_toFinset {z : Sym2 α} : 1 ≤ z.toFinset.card := by
FormalBook/Mathlib/EdgeFinset.lean:62: lemma card_toFinset_le_two {z : Sym2 α} : z.toFinset.card ≤ 2 := by
FormalBook/Mathlib/EdgeFinset.lean:65: end Sym2
FormalBook/Mathlib/EdgeFinset.lean:67: end Mathlib.Data.Sym.Sym2
FormalBook/Mathlib/EdgeFinset.lean:77: -- lemma card_toFinset_of_mem_edgeSet (e : Sym2 α) (he : e ∈ G.edgeSet) :
FormalBook/Mathlib/EdgeFinset.lean:79: --   refine Sym2.card_toFinset_of_not_isDiag ?_
FormalBook/Mathlib/EdgeFinset.lean:85: -- lemma card_filter_mem_of_mem_edgeSet [Fintype α] (e : Sym2 α) (he : e ∈ G.edgeSet) :
FormalBook/Mathlib/EdgeFinset.lean:102: -- lemma card_toFinset_of_mem_edgeFinset (e : Sym2 α) (he : e ∈ G.edgeFinset) :
FormalBook/Mathlib/EdgeFinset.lean:104: --   Sym2.card_toFinset_of_not_isDiag (not_isDiag_of_mem_edgeSet _ (mem_edgeFinset.mp he))
FormalBook/Mathlib/EdgeFinset.lean:106: -- lemma card_filter_mem_of_mem_edgeFinset (e : Sym2 α) (he : e ∈ G.edgeFinset) :
.lake/packages/mathlib/Mathlib.lean:4006: public import Mathlib.Data.Sym.Sym2
.lake/packages/mathlib/Mathlib.lean:4007: public import Mathlib.Data.Sym.Sym2.Finsupp
.lake/packages/mathlib/Mathlib.lean:4008: public import Mathlib.Data.Sym.Sym2.Init
.lake/packages/mathlib/Mathlib.lean:4009: public import Mathlib.Data.Sym.Sym2.Order
.lake/packages/mathlib/Mathlib/Tactic/MinImports.lean:30: import Mathlib.Data.Sym.Sym2.Init -- the actual minimal import
.lake/packages/mathlib/Mathlib/Tactic/MinImports.lean:37: @[aesop (rule_sets := [Sym2]) [safe [constructors, cases], norm]]
.lake/packages/mathlib/Mathlib/Tactic/MinImports.lean:42: -- `import Mathlib.Data.Sym.Sym2.Init` is not detected by `#min_imports in`.
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:8: public import Mathlib.Data.Sym.Sym2
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:19: We also define `Sym2.GameAdd`, which is the unordered pair analog of `Prod.GameAdd`.
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:27: - `Sym2.GameAdd`: the game addition relation on unordered pairs.
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:52:   See `Sym2.GameAdd` for the unordered pair analog. -/
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:133: /-! ### `Sym2.GameAdd` -/
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:135: namespace Sym2
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:137: /-- `Sym2.GameAdd rα x y` means that `x` can be reached from `y` by decreasing either entry with
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:141: def GameAdd (rα : α → α → Prop) : Sym2 α → Sym2 α → Prop :=
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:142:   Sym2.lift₂
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:150:     GameAdd rα (Sym2.mk x) (Sym2.mk y) ↔ Prod.GameAdd rα rα x y ∨ Prod.GameAdd rα rα x.swap y := by
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:160:     Sym2.GameAdd rα s(a₁, b₁) s(a₂, b₂) :=
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:170:   rw [Sym2.eq_swap]
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:174:   rw [Sym2.eq_swap]
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:177: end Sym2
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:180:     Acc (Sym2.GameAdd rα) s(a, b) := by
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:185:   rw [Sym2.GameAdd]
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:190:   · rw [Sym2.eq_swap]
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:192:   · rw [Sym2.eq_swap]
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:195: /-- The `Sym2.GameAdd` relation on well-founded inputs is well-founded. -/
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:196: theorem WellFounded.sym2_gameAdd (h : WellFounded rα) : WellFounded (Sym2.GameAdd rα) :=
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:197:   ⟨fun i => Sym2.inductionOn i fun x y => (h.apply x).sym2_gameAdd (h.apply y)⟩
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:199: namespace Sym2
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:201: attribute [local instance] Sym2.Rel.setoid
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:203: /-- Recursion on the well-founded `Sym2.GameAdd` relation. -/
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:205:     (IH : ∀ a₁ b₁, (∀ a₂ b₂, Sym2.GameAdd rα s(a₂, b₂) s(a₁, b₁) → C a₂ b₂) → C a₁ b₁) (a b : α) :
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:209:     (by simpa [← Sym2.gameAdd_iff] using hr.sym2_gameAdd.onFun)
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:213:     (IH : ∀ a₁ b₁, (∀ a₂ b₂, Sym2.GameAdd rα s(a₂, b₂) s(a₁, b₁) → C a₂ b₂) → C a₁ b₁) (a b : α) :
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:217: /-- Induction on the well-founded `Sym2.GameAdd` relation. -/
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:220:       (∀ a₁ b₁, (∀ a₂ b₂, Sym2.GameAdd rα s(a₂, b₂) s(a₁, b₁) → C a₂ b₂) → C a₁ b₁) →
.lake/packages/mathlib/Mathlib/Order/GameAdd.lean:224: end Sym2
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:9: public import Mathlib.Data.Sym.Sym2
.lake/packages/mathlib/Mathlib/Combinatorics/Graph/Basic.lean:167:   rw [h.isLink_iff, Sym2.eq_iff]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:170:     (e : Sym2 V) : p.edges.count e ≤ 1 :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:174:     {e : Sym2 V} (he : e ∈ p.edges) : p.edges.count e = 1 :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:435:   rw [← cons_tail_eq _ hnil, edges_cons, List.mem_cons, Sym2.eq, Sym2.rel_iff'] at hmem
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:621: theorem count_edges_eq_one [DecidableEq V] {u v : V} {p : G.Path u v} (e : Sym2 V)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:634: theorem notMem_edges_of_loop {v : V} {e : Sym2 V} {p : G.Path v v} :
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:814:     rw [← Sym2.map_pair_eq, edges_map, ← List.mem_map_of_injective (Sym2.map.injective hinj)]
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:907: protected theorem IsPath.toDeleteEdges (s : Set (Sym2 V))
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:911: protected theorem IsCycle.toDeleteEdges (s : Set (Sym2 V))
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Paths.lean:916: theorem toDeleteEdges_copy {v u u' v' : V} (s : Set (Sym2 V))
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:50: variable {V : Type*} (G : SimpleGraph V) {e : Sym2 V}
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:57: abbrev edgeFinset : Finset (Sym2 V) :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:61: theorem coe_edgeFinset : (G.edgeFinset : Set (Sym2 V)) = G.edgeSet :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:74:     (e : Sym2 V).toFinset.card = 2 :=
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:75:   Sym2.card_toFinset_of_not_isDiag e.val (G.not_isDiag_of_mem_edgeFinset e.prop)
.lake/packages/mathlib/Mathlib/Combinatorics/SimpleGraph/Finite.lean:123:     (⊤ : SimpleGraph V).edgeFinset = Sym2.diagSetᶜ.toFinset := by simp [← coe_inj]
====================================================================================================
PATTERN: \.card
FormalBook/Chapter_20.lean:130: local prefix:100 "#" => Finset.card
FormalBook/Chapter_20.lean:135: local notation "n" => Fintype.card α
FormalBook/Chapter_01.lean:151:     convert Subgroup.card_subgroup_dvd_card (Subgroup.zpowers (two))
FormalBook/Chapter_01.lean:153:       exact Fintype.card_zpowers.symm
FormalBook/Chapter_01.lean:154:     · rw [card_eq_fintype_card, ZMod.card_units_eq_totient]
FormalBook/Chapter_01.lean:353:   ∃ c : ℕ, ∀ k : ℕ, ∃ h : Set.Finite {n : ℕ | S n = k }, (Set.Finite.toFinset h).card ≤ c
FormalBook/Chapter_06.lean:156:   Fintype.card Rˣ = (Fintype.card A.carrier) *
FormalBook/Chapter_06.lean:157:     (@Fintype.card  (Set.centralizer {ConjClasses.exists_rep A|>.choose}) (
FormalBook/Chapter_06.lean:164:   have := MulAction.card_orbit_mul_card_stabilizer_eq_card_group (ConjAct Rˣ)
FormalBook/Chapter_06.lean:167:   rw [Fintype.card_congr <| ConjAct_stabilizer_centralizer_eq (ConjClasses.exists_rep A|>.choose)]
FormalBook/Chapter_06.lean:178:   obtain ⟨n, h_card⟩ := VectorSpace.card_fintype Z R
FormalBook/Chapter_06.lean:188:     exact Fintype.card_le_one_iff.mp (Nat.le_of_eq h_card) x y
FormalBook/Chapter_06.lean:190:   set q := Fintype.card Z
FormalBook/Chapter_06.lean:201:       have := finclassa A; Fintype.card ↑(ConjClasses.carrier A) > 1} :=
FormalBook/Chapter_06.lean:203:           setFintype {A | let_fun this := finclassa A; Fintype.card ↑(ConjClasses.carrier A) > 1}
FormalBook/Chapter_06.lean:206:       have := finclassa A;  Fintype.card ↑(ConjClasses.carrier A) > 1} :=
FormalBook/Chapter_06.lean:209:                   Fintype.card ↑(ConjClasses.carrier A) > 1}
FormalBook/Chapter_06.lean:215:   let n_k : S' → ℕ := sorry -- fun A => Fintype.card
FormalBook/Chapter_06.lean:218:   have h_R: Fintype.card Rˣ = q ^ n - 1 := by
FormalBook/Chapter_06.lean:219:     have : Fintype.card Rˣ + 1 = Fintype.card R := (Fintype.card_eq_card_units_add_one R).symm
FormalBook/Chapter_06.lean:221:     simp only [ge_iff_le, add_le_iff_nonpos_left, nonpos_iff_eq_zero, Fintype.card_ne_zero,
FormalBook/Chapter_06.lean:224:   have h_Z : Fintype.card Zˣ = q - 1 := by
FormalBook/Chapter_06.lean:225:     have h : Fintype.card Zˣ + 1 = Fintype.card Z := (Fintype.card_eq_card_units_add_one _).symm
FormalBook/Chapter_06.lean:226:     have : Fintype.card Z = q := rfl
FormalBook/Chapter_06.lean:229:       add_le_iff_nonpos_left, nonpos_iff_eq_zero, Fintype.card_ne_zero, add_tsub_cancel_right]
FormalBook/Chapter_06.lean:233:   have H1:= (Group.card_center_add_sum_card_noncenter_eq_card Rˣ).symm
FormalBook/Chapter_06.lean:238:   rw [h_R, Fintype.card_congr (e.toEquiv.trans f), h_Z] at H1
FormalBook/Chapter_06.lean:241:   have : ∀ A : S', (Fintype.card <| ConjClasses.carrier (A : ConjClasses Rˣ)) * (q ^ (n_k A) - 1)
FormalBook/Chapter_06.lean:249:   have hq_pow_pos : ∀ m,  1 ≤ q ^ m := fun m ↦ one_le_pow m q Fintype.card_pos
FormalBook/Chapter_06.lean:254:     have hq : q = (Fintype.card { x // x ∈ center R }) := by rfl
FormalBook/Chapter_06.lean:308:     have : 1 ≤ q := Fintype.card_pos
FormalBook/Chapter_06.lean:313:   have : 1 ≤ Fintype.card { x // x ∈ center R } :=
FormalBook/Chapter_06.lean:314:     Fintype.card_pos_iff.mpr (⟨1, Subring.one_mem (center R)⟩)
FormalBook/Chapter_28.lean:53: local prefix:100 "#" => Finset.card
FormalBook/Chapter_28.lean:60:     _ = ∑ v, #I(v)             := by simp [G.card_incidenceFinset_eq_degree]
FormalBook/Chapter_28.lean:63:     -- FIXME: was (G.card_filter_mem_of_mem_edgeFinset e he)) but is commented out currently in Mathlib.EdgeFinset
FormalBook/Chapter_28.lean:66:     _ = 2 * #E                 := by rw [Finset.card_eq_sum_ones E]
FormalBook/Chapter_04.lean:43:     let num_solutions := Finset.card { s : ZMod p | s ^ 2 = - 1 }
FormalBook/Chapter_04.lean:184: theorem sameCard : Fintype.card (U k) = Fintype.card (T k) := by
FormalBook/Chapter_04.lean:243: theorem card_fixedPoints_eq_one : Fintype.card (fixedPoints (secondInvo k)) = 1 := by
FormalBook/Chapter_04.lean:247: theorem card_T_odd : Odd <| Fintype.card <| T k := by
FormalBook/Chapter_45.lean:47:   (∀ A ∈ 𝓕, A.card = d) ∧  ¬ two_colorable 𝓕 := by
FormalBook/Chapter_45.lean:50:   use (Finset.powerset univ).filter (Finset.card · = d)
FormalBook/Chapter_45.lean:55:   by_cases h : d ≤ (Finset.univ.filter (coloring · = 1)).card
FormalBook/Chapter_45.lean:60:     have : d ≤ (Finset.univ.filter (coloring · = 0)).card := by
FormalBook/Chapter_45.lean:64:       simp only [this, filter_not, card_sdiff, card_attach, card_univ, Fintype.card_fin] at h
FormalBook/Chapter_45.lean:118:   (H_𝓕 : ∀ (A : Finset X), A ∈ 𝓕 → A.card = d)
FormalBook/Chapter_45.lean:119:   : 𝓕.card ≤ 2 ^ (d-1) → two_colorable 𝓕 := by
FormalBook/Chapter_45.lean:121:   by_cases base :  2 ≤ 𝓕.card
FormalBook/Chapter_45.lean:127:         rw [← H_𝓕 A hA] ; convert (card_le_univ A) ; simp only [Fintype.card_coe]
FormalBook/Chapter_45.lean:129:       · nth_rw 2 [← Nat.card_eq_fintype_card]
FormalBook/Chapter_45.lean:130:         rw [Nat.card_fun, Nat.card_fin, Nat.card_eq_fintype_card,Fintype.card_coe]
FormalBook/Chapter_45.lean:131:         simp only [coe_sort_coe, Fintype.card_coe]
FormalBook/Chapter_45.lean:145:             rw [show #X = Fintype.card X from by simp only [Fintype.card_coe]]
FormalBook/Chapter_45.lean:148:               = Nat.card ({x // x ∈ Aᶜ} → Fin 2) := by
FormalBook/Chapter_45.lean:149:                 rw [Nat.card_eq_fintype_card,← card_univ,eq_comm]
FormalBook/Chapter_45.lean:168:             rwa [Nat.card_fun, Nat.card_fin, Nat.card_eq_fintype_card, Fintype.card_coe] at main
FormalBook/Chapter_45.lean:230:     interval_cases q : 𝓕.card
FormalBook/Chapter_45.lean:322:   (H : m ≥ 4 * n) (h_n : n = Fintype.card V) (h_m : m = Fintype.card G.edgeSet) :
FormalBook/Chapter_32.lean:11: import data.fintype.card
FormalBook/Chapter_44.lean:40:     (h : ∀ ⦃v w : V⦄, v ≠ w → Fintype.card (G.commonNeighbors v w) = 1) :
FormalBook/Chapter_44.lean:50:   let n := Fintype.card V
FormalBook/Chapter_44.lean:56:     exact Nat.eq_add_of_sub_eq Fintype.card_pos rfl
FormalBook/Chapter_44.lean:72:         have : 1 < Fintype.card V := by
FormalBook/Chapter_44.lean:76:         rw [(show Fintype.card V = n by rfl), eq₁] at this
FormalBook/Chapter_44.lean:94:         · convert_to _ = Fintype.card V - 1
FormalBook/Chapter_44.lean:95:           · rw [(show Fintype.card V = n by rfl), eq₁]
FormalBook/Chapter_44.lean:96:           · exact Finset.card_erase_of_mem (Finset.mem_univ _)
FormalBook/Chapter_05.lean:78:    Finset.card ((Icc (1 : ℤ) (((p : ℤ)-1)/2)).image r ∩ (Icc (-((p: ℤ) - 1)/2) (-1))) := by
FormalBook/Chapter_05.lean:102:   (h_pq : p ≠ q) (K : Type _) [Field K] [Fintype K] (H : Fintype.card K = q ^ (p - 1)) :
FormalBook/Chapter_02.lean:148:     have : (Finset.Icc 1 (Nat.sqrt (2 * n))).card = Nat.sqrt (2 * n) := by rw [card_Icc, Nat.add_sub_cancel]
FormalBook/Chapter_02.lean:150:     refine' pow_le_pow_right₀ n2_pos ((Finset.card_le_card fun x hx => _).trans this.le)
FormalBook/Mathlib/EdgeFinset.lean:54: lemma card_toFinset_mk_of_ne {x y : α} (h : x ≠ y) : s(x, y).toFinset.card = 2 := by
FormalBook/Mathlib/EdgeFinset.lean:55:   rw [Finset.card_eq_two]
FormalBook/Mathlib/EdgeFinset.lean:59: lemma one_le_card_toFinset {z : Sym2 α} : 1 ≤ z.toFinset.card := by
FormalBook/Mathlib/EdgeFinset.lean:62: lemma card_toFinset_le_two {z : Sym2 α} : z.toFinset.card ≤ 2 := by
FormalBook/Mathlib/EdgeFinset.lean:78: --     (e : Finset α).card = 2 := by
FormalBook/Mathlib/EdgeFinset.lean:79: --   refine Sym2.card_toFinset_of_not_isDiag ?_
FormalBook/Mathlib/EdgeFinset.lean:86: --     Finset.card {v | v ∈ e} = 2 := by
FormalBook/Mathlib/EdgeFinset.lean:87: --   rw [← SimpleGraph.card_toFinset_of_mem_edgeSet _ he]
====================================================================================================
PATTERN: card_eq
FormalBook/Chapter_01.lean:152:     · rw [← orderOf_eq_prime h_two two_ne_one, card_eq_fintype_card]
FormalBook/Chapter_01.lean:154:     · rw [card_eq_fintype_card, ZMod.card_units_eq_totient]
FormalBook/Chapter_06.lean:219:     have : Fintype.card Rˣ + 1 = Fintype.card R := (Fintype.card_eq_card_units_add_one R).symm
FormalBook/Chapter_06.lean:225:     have h : Fintype.card Zˣ + 1 = Fintype.card Z := (Fintype.card_eq_card_units_add_one _).symm
FormalBook/Chapter_28.lean:66:     _ = 2 * #E                 := by rw [Finset.card_eq_sum_ones E]
FormalBook/Chapter_45.lean:56:   · refine (Finset.exists_subset_card_eq h).imp ?_
FormalBook/Chapter_45.lean:67:     refine (Finset.exists_subset_card_eq this).imp ?_
FormalBook/Chapter_45.lean:129:       · nth_rw 2 [← Nat.card_eq_fintype_card]
FormalBook/Chapter_45.lean:130:         rw [Nat.card_fun, Nat.card_fin, Nat.card_eq_fintype_card,Fintype.card_coe]
FormalBook/Chapter_45.lean:149:                 rw [Nat.card_eq_fintype_card,← card_univ,eq_comm]
FormalBook/Chapter_45.lean:168:             rwa [Nat.card_fun, Nat.card_fin, Nat.card_eq_fintype_card, Fintype.card_coe] at main
FormalBook/Chapter_45.lean:186:       obtain ⟨Ah,Ahdef,Ahprop⟩ := exists_subset_card_eq base
FormalBook/Chapter_45.lean:187:       obtain ⟨x,y,xney,Aha⟩ := card_eq_two.mp Ahprop
FormalBook/Chapter_45.lean:234:     · obtain ⟨A,Adef⟩ := card_eq_one.mp q
FormalBook/Chapter_45.lean:238:       obtain ⟨Ah,Ahdef,Ahprop⟩ := exists_subset_card_eq h_d
FormalBook/Chapter_45.lean:239:       obtain ⟨x,y,xney,Aha⟩ := card_eq_two.mp Ahprop
FormalBook/Mathlib/EdgeFinset.lean:55:   rw [Finset.card_eq_two]
.lake/packages/mathlib/Mathlib/Order/Disjointed.lean:127:     simp only [Nat.le_zero, card_eq_zero] at hi
.lake/packages/mathlib/Mathlib/Order/Height.lean:63:     obtain ⟨u, hu₁, hu₂⟩ := exists_subset_encard_eq ht₃
.lake/packages/mathlib/Mathlib/Order/Height.lean:80: theorem encard_eq_chainHeight_of_isChain {r} (s : Set α) (hc : IsChain r s) :
.lake/packages/mathlib/Mathlib/Order/Height.lean:107:   · simp only [chainHeight, iSup_eq_zero, encard_eq_zero, Subtype.forall, and_imp] at h
.lake/packages/mathlib/Mathlib/Order/Partition/Finpartitio