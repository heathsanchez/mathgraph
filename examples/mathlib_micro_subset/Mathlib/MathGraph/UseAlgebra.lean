import Mathlib.MathGraph.Algebra
import Mathlib.MathGraph.Logic

namespace Mathlib
namespace MathGraph

theorem mgml_uses_nat_eq_self (n : Nat) : n = n := by
  exact mgml_nat_eq_self n

theorem mgml_uses_and_comm (p q : Prop) : p ∧ q → q ∧ p := by
  exact mgml_and_comm p q

end MathGraph
end Mathlib
