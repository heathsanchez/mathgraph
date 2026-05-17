import MathGraphMicro.Logic

theorem mg_uses_and_comm (p q : Prop) : p ∧ q → q ∧ p := by
  exact mg_and_comm p q

theorem mg_uses_imp_trans (p q r : Prop) : (p → q) → (q → r) → p → r := by
  exact mg_imp_trans p q r
