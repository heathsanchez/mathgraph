# SorryDB v4.6.6 — FormalBook Chapter_28 EdgeCard Patch002

## Result

- status: PATCH002_REJECTED_OR_DIAGNOSTIC
- accepted_variant: None

## Why v4.6.5 failed

v4.6.5 replaced the entire calc line with raw tactic text. This target needs a lambda proof term: `λ e he ↦ by ...`.

## Variant Summary

- v01_by_simpa_using_he: file_rc=1, seconds=3.86, target_sorry=False, module_rc=None
- v02_by_simpa: file_rc=1, seconds=4.46, target_sorry=False, module_rc=None
- v03_by_exact_comment_lemma: file_rc=1, seconds=5.75, target_sorry=False, module_rc=None
- v04_by_simpa_comment_lemma: file_rc=1, seconds=4.22, target_sorry=False, module_rc=None
- v05_by_exact_edgeFinset_card: file_rc=1, seconds=4.97, target_sorry=False, module_rc=None
- v06_by_have_comment_lemma: file_rc=1, seconds=2.88, target_sorry=False, module_rc=None
- v07_by_convert_comment_lemma: file_rc=1, seconds=2.34, target_sorry=False, module_rc=None
- v08_by_aesop: file_rc=1, seconds=2.19, target_sorry=False, module_rc=None
- v09_by_simp_all: file_rc=1, seconds=2.26, target_sorry=False, module_rc=None
- v10_by_trace: file_rc=1, seconds=2.37, target_sorry=False, module_rc=None

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