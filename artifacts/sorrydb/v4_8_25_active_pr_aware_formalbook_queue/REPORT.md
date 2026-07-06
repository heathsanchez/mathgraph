# MathGraph SorryDB v4.8.25 - Active PR Aware FormalBook Queue

## Purpose

Refine the FormalBook local-have scanner using what we learned from PR #137 and PR #138.

## Active PR exclusions

- Chapter03 local arithmetic window is promoted in PR #138.
- Chapter06 is deferred while PR #137 is pending on the same file.

## Counts

- raw sorry lines scanned: 80
- ready candidates: 0
- deferred candidates: 16
- excluded / low-score candidates: 80

## Ready candidates

## Deferred candidates

### D1. score -61 - FormalBook/Chapter_06.lean:87
- current: `have : Real.sqrt (((q:ℝ) - 1) ^ 2) = ((q : ℝ) - 1) := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file

### D2. score -71 - FormalBook/Chapter_06.lean:74
- current: `have h_a_lt_one: ‖a‖ < 1 := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file, hard_term_primitiveRoots

### D3. score -76 - FormalBook/Chapter_06.lean:78
- current: `_ = ‖q - lamb‖^2 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file

### D4. score -76 - FormalBook/Chapter_06.lean:80
- current: `_ = ‖(q : ℂ) - a - I*b‖^2 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file

### D5. score -76 - FormalBook/Chapter_06.lean:81
- current: `_ = ‖(q : ℂ) - a‖^2 + ‖b‖^2 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file

### D6. score -76 - FormalBook/Chapter_06.lean:82
- current: `_ = (q : ℝ)^2 - 2*‖a‖*q + ‖a‖^2 + ‖b‖^2 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file

### D7. score -76 - FormalBook/Chapter_06.lean:83
- current: `_ > ((q : ℝ) - 1)^2 := by sorry`
- reasons: calc_step_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file

### D8. score -79 - FormalBook/Chapter_06.lean:296
- current: `sorry`
- reasons: direct_have_nextline_sorry, nearby_arithmetic_tactic, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file, hard_term_Polynomial, hard_term_primitiveRoots, hard_term_cyclotomic

### D9. score -81 - FormalBook/Chapter_06.lean:260
- current: `have h_one_neq: 1 ≠ n_k A := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file, hard_term_Fintype.card, hard_term_center_R

### D10. score -81 - FormalBook/Chapter_06.lean:261
- current: `have h_k_n_lt_n: n_k A < n := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file, hard_term_Fintype.card, hard_term_center_R

### D11. score -91 - FormalBook/Chapter_06.lean:73
- current: `have h_lamb: lamb ≠ 1 := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file, hard_term_Polynomial, hard_term_primitiveRoots, hard_term_cyclotomic

### D12. score -91 - FormalBook/Chapter_06.lean:251
- current: `have h_n_k_A_dvd: ∀ A : S', (n_k A ∣ n) := by sorry`
- reasons: direct_have_inline_sorry, nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: active_pr_137_pending_same_file, hard_term_Fintype.card, hard_term_center_R, hard_term_∀

### D13. score -221 - FormalBook/Chapter_06.lean:90
- current: `· sorry`
- reasons: nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: not_direct_local_have_or_calc_step, active_pr_137_pending_same_file, hard_term_∀

### D14. score -241 - FormalBook/Chapter_06.lean:215
- current: `let n_k : S' → ℕ := sorry -- fun A => Fintype.card`
- reasons: nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: not_direct_local_have_or_calc_step, active_pr_137_pending_same_file, hard_term_Fintype.card, hard_term_ConjClasses, hard_term_center_R

### D15. score -251 - FormalBook/Chapter_06.lean:247
- current: `sorry`
- reasons: nearby_basic_tactic, relation_symbols_nearby, numeric_context
- penalties: not_direct_local_have_or_calc_step, active_pr_137_pending_same_file, hard_term_Fintype.card, hard_term_ConjClasses, hard_term_center_R, hard_term_∀

### D16. score -266 - FormalBook/Chapter_06.lean:243
- current: `sorry`
- reasons: nearby_basic_tactic, relation_symbols_nearby
- penalties: not_direct_local_have_or_calc_step, active_pr_137_pending_same_file, hard_term_Fintype.card, hard_term_Equiv, hard_term_ConjClasses, hard_term_center_R, hard_term_∀

No ready FormalBook candidates remain after active-PR and theorem-scale exclusions.

Next action: wait for PR #137/#138 or scan another repository with the same direct-local-have rule.