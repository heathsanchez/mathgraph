import MathGraphMicro.Basic

theorem mg_uses_basic_true : True := by
  exact mg_basic_true

theorem mg_uses_identity (alpha : Type) (x : alpha) : x = x := by
  exact mg_identity alpha x
