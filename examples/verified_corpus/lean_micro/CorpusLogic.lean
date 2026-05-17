theorem corpus_and_comm (p q : Prop) : p ∧ q → q ∧ p := by
  intro h
  exact And.intro h.right h.left

theorem corpus_imp_trans (p q r : Prop) : (p → q) → (q → r) → p → r := by
  intro hpq hqr hp
  exact hqr (hpq hp)
