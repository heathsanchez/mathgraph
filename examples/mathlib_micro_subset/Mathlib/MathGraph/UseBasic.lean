import Mathlib.MathGraph.Basic

namespace Mathlib
namespace MathGraph

theorem mgml_uses_true : True := by
  exact mgml_true

theorem mgml_uses_identity (alpha : Type) (x : alpha) : x = x := by
  exact mgml_identity alpha x

end MathGraph
end Mathlib
