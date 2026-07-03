import Mathlib.Algebra.BigOperators.Field
import Mathlib.Algebra.Order.BigOperators.Ring.Finset
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# Conditional discrete-time H-Tilt Doob stationarity

This file proves finite algebraic identities from explicit left- and
right-eigenvector assumptions. It does not prove Perron--Frobenius existence,
irreducibility consequences, Markov convergence, or any empirical H-Tilt
claim.
-/

open scoped BigOperators

namespace HTiltDiscreteDoob

variable {ι : Type*} [Fintype ι]

noncomputable def discreteDoobEntry
    (A : ι → ι → ℝ) (rho : ℝ) (h : ι → ℝ) (i j : ι) : ℝ :=
  (A i j * h j) / (rho * h i)

def survivorWeight (q h : ι → ℝ) (i : ι) : ℝ :=
  q i * h i

def survivorNorm (q h : ι → ℝ) : ℝ :=
  ∑ i, survivorWeight q h i

noncomputable def piStar (q h : ι → ℝ) (i : ι) : ℝ :=
  survivorWeight q h i / survivorNorm q h

omit [Fintype ι] in
theorem survivorWeight_pos
    (q h : ι → ℝ)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i) :
    ∀ i, 0 < survivorWeight q h i := by
  intro i
  exact mul_pos (q_pos i) (h_pos i)

theorem survivorNorm_pos
    [Nonempty ι]
    (q h : ι → ℝ)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i) :
    0 < survivorNorm q h := by
  classical
  exact Finset.sum_pos
    (fun i _ ↦ survivorWeight_pos q h q_pos h_pos i)
    Finset.univ_nonempty

theorem piStar_pos
    [Nonempty ι]
    (q h : ι → ℝ)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i) :
    ∀ i, 0 < piStar q h i := by
  intro i
  exact div_pos
    (survivorWeight_pos q h q_pos h_pos i)
    (survivorNorm_pos q h q_pos h_pos)

theorem piStar_sum_one
    [Nonempty ι]
    (q h : ι → ℝ)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i) :
    (∑ i, piStar q h i) = 1 := by
  classical
  rw [show (∑ i, piStar q h i) =
      (∑ i, survivorWeight q h i) / survivorNorm q h by
        rw [Finset.sum_div]
        rfl]
  simp only [survivorNorm]
  exact div_self (survivorNorm_pos q h q_pos h_pos).ne'

omit [Fintype ι] in
theorem discreteDoobEntry_nonneg
    (A : ι → ι → ℝ) (rho : ℝ) (h : ι → ℝ)
    (A_nonneg : ∀ i j, 0 ≤ A i j)
    (rho_pos : 0 < rho)
    (h_pos : ∀ i, 0 < h i) :
    ∀ i j, 0 ≤ discreteDoobEntry A rho h i j := by
  intro i j
  exact div_nonneg
    (mul_nonneg (A_nonneg i j) (h_pos j).le)
    (mul_nonneg rho_pos.le (h_pos i).le)

theorem discrete_doob_unnormalized_stationary
    (A : ι → ι → ℝ) (rho : ℝ) (q h : ι → ℝ)
    (rho_ne : rho ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (left_eigen : ∀ j, (∑ i, q i * A i j) = rho * q j)
    (j : ι) :
    ∑ i, survivorWeight q h i * discreteDoobEntry A rho h i j =
      survivorWeight q h j := by
  classical
  calc
    (∑ i, survivorWeight q h i * discreteDoobEntry A rho h i j) =
        ∑ i, (q i * A i j * h j) / rho := by
          apply Finset.sum_congr rfl
          intro i _
          simp only [survivorWeight, discreteDoobEntry]
          field_simp [rho_ne, h_nonzero i]
    _ = ((∑ i, q i * A i j) * h j) / rho := by
          rw [← Finset.sum_div, Finset.sum_mul]
    _ = survivorWeight q h j := by
          rw [left_eigen]
          simp only [survivorWeight]
          field_simp [rho_ne]

theorem discrete_doob_normalized_stationary
    (A : ι → ι → ℝ) (rho : ℝ) (q h : ι → ℝ)
    (rho_ne : rho ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (left_eigen : ∀ j, (∑ i, q i * A i j) = rho * q j)
    (norm_nonzero : survivorNorm q h ≠ 0)
    (j : ι) :
    ∑ i, piStar q h i * discreteDoobEntry A rho h i j =
      piStar q h j := by
  classical
  calc
    (∑ i, piStar q h i * discreteDoobEntry A rho h i j) =
        (∑ i, survivorWeight q h i * discreteDoobEntry A rho h i j) /
          survivorNorm q h := by
            rw [Finset.sum_div]
            apply Finset.sum_congr rfl
            intro i _
            simp only [piStar]
            field_simp [norm_nonzero]
    _ = piStar q h j := by
          rw [discrete_doob_unnormalized_stationary
            A rho q h rho_ne h_nonzero left_eigen j]
          rfl

theorem discrete_doob_row_sum_one
    (A : ι → ι → ℝ) (rho : ℝ) (h : ι → ℝ)
    (rho_ne : rho ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (right_eigen : ∀ i, (∑ j, A i j * h j) = rho * h i)
    (i : ι) :
    ∑ j, discreteDoobEntry A rho h i j = 1 := by
  classical
  simp only [discreteDoobEntry]
  calc
    (∑ j, (A i j * h j) / (rho * h i)) =
        (∑ j, A i j * h j) / (rho * h i) := by
          rw [Finset.sum_div]
    _ = 1 := by
          rw [right_eigen]
          field_simp [rho_ne, h_nonzero i]

theorem piStar_is_stationary_distribution_for_discreteDoob
    [Nonempty ι]
    (A : ι → ι → ℝ) (rho : ℝ) (q h : ι → ℝ)
    (rho_pos : 0 < rho)
    (A_nonneg : ∀ i j, 0 ≤ A i j)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i)
    (left_eigen : ∀ j, (∑ i, q i * A i j) = rho * q j)
    (right_eigen : ∀ i, (∑ j, A i j * h j) = rho * h i) :
    ((∀ i, 0 < piStar q h i) ∧
     (∑ i, piStar q h i) = 1 ∧
     (∀ i j, 0 ≤ discreteDoobEntry A rho h i j) ∧
     (∀ i, (∑ j, discreteDoobEntry A rho h i j) = 1) ∧
     (∀ j, (∑ i, piStar q h i * discreteDoobEntry A rho h i j) =
       piStar q h j)) := by
  have rho_ne : rho ≠ 0 := rho_pos.ne'
  have h_nonzero : ∀ i, h i ≠ 0 := fun i ↦ (h_pos i).ne'
  have norm_nonzero : survivorNorm q h ≠ 0 :=
    (survivorNorm_pos q h q_pos h_pos).ne'
  exact ⟨
    piStar_pos q h q_pos h_pos,
    piStar_sum_one q h q_pos h_pos,
    discreteDoobEntry_nonneg A rho h A_nonneg rho_pos h_pos,
    fun i ↦ discrete_doob_row_sum_one
      A rho h rho_ne h_nonzero right_eigen i,
    fun j ↦ discrete_doob_normalized_stationary
      A rho q h rho_ne h_nonzero left_eigen norm_nonzero j
  ⟩

end HTiltDiscreteDoob
