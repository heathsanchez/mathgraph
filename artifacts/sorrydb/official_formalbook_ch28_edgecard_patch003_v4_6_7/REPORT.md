# SorryDB v4.6.7 — FormalBook Chapter_28 EdgeCard Patch003

## Result

- status: PATCH003_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None
- base_module_build_returncode: 0

## Runner correction

v4.6.6 used `lake env lean FormalBook/Chapter_28.lean`, which failed import resolution with `unknown module prefix FormalBook`. v4.6.7 uses `lake build FormalBook.Chapter_28`.

## Variant Summary

- v01_by_simpa_using_he: module_rc=1, seconds=35.12, target_sorry=False, full_rc=None
- v02_by_simpa: module_rc=1, seconds=33.34, target_sorry=False, full_rc=None
- v03_by_exact_comment_lemma: module_rc=1, seconds=34.34, target_sorry=False, full_rc=None
- v04_by_simpa_comment_lemma: module_rc=1, seconds=34.59, target_sorry=False, full_rc=None
- v05_by_have_comment_lemma: module_rc=1, seconds=37.66, target_sorry=False, full_rc=None
- v06_by_convert_comment_lemma: module_rc=1, seconds=36.8, target_sorry=False, full_rc=None
- v07_by_aesop: module_rc=1, seconds=39.46, target_sorry=False, full_rc=None
- v08_by_simp_all: module_rc=1, seconds=35.55, target_sorry=False, full_rc=None
- v09_by_exact_edge_mem_card: module_rc=1, seconds=36.92, target_sorry=False, full_rc=None
- v10_by_simpa_edge_mem_card: module_rc=1, seconds=34.89, target_sorry=False, full_rc=None
- v11_by_have_edge_mem_card: module_rc=1, seconds=38.14, target_sorry=False, full_rc=None
- v12_by_trace: module_rc=0, seconds=53.54, target_sorry=False, full_rc=None

## Target Window

    55	local notation "d(" v ")" => G.degree v
    56	local notation "I(" v ")" => G.incidenceFinset v
    57	
    58	lemma handshaking : ∑ v, d(v) = 2 * #E := by
    59	  calc  ∑ v, d(v)
    60	    _ = ∑ v, #I(v)             := by simp [G.card_incidenceFinset_eq_degree]
    61	    _ = ∑ v, #{e ∈ E | v ∈ e}  := by simp [G.incidenceFinset_eq_filter]
    62	    _ = ∑ e ∈ E, #{v | v ∈ e}  := Finset.sum_card_bipartiteAbove_eq_sum_card_bipartiteBelow _
    63	    -- FIXME: was (G.card_filter_mem_of_mem_edgeFinset e he)) but is commented out currently in Mathlib.EdgeFinset
    64	    _ = ∑ e ∈ E, 2             := Finset.sum_congr rfl (λ e he ↦ sorry)
    65	    _ = 2 * ∑ e ∈ E, 1         := (Finset.mul_sum E (λ _ ↦ 1) 2).symm
    66	    _ = 2 * #E                 := by rw [Finset.card_eq_sum_ones E]
    67	
    68	end chapter28
