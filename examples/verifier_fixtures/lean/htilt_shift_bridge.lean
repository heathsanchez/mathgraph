import Mathlib.Algebra.BigOperators.Field
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# Finite H-Tilt shift bridge

This file proves a finite algebraic adapter from a generator-style operator
`K` to the shifted discrete operator `A = cI + K`. It does not prove
Perron--Frobenius existence, irreducibility transfer, convergence, or any
empirical or interpretive claim.
-/

open scoped BigOperators

namespace HTiltShiftBridge

variable {I : Type*} [Fintype I] [DecidableEq I]

def delta (i j : I) : ℝ :=
  if i = j then 1 else 0

def shiftedOperator (K : I → I → ℝ) (c : ℝ) (i j : I) : ℝ :=
  K i j + c * delta i j

noncomputable def generatorDoobEntry
    (K : I → I → ℝ) (lam : ℝ) (h : I → ℝ) (i j : I) : ℝ :=
  ((K i j - lam * delta i j) * h j) / h i

noncomputable def discreteDoobEntry
    (A : I → I → ℝ) (rho : ℝ) (h : I → ℝ) (i j : I) : ℝ :=
  (A i j * h j) / (rho * h i)

theorem sum_delta_mul (h : I → ℝ) (i : I) :
    (∑ j, delta i j * h j) = h i := by
  classical
  simp [delta]

theorem sum_mul_delta (q : I → ℝ) (j : I) :
    (∑ i, q i * delta i j) = q j := by
  classical
  simp [delta]

omit [Fintype I] in
theorem delta_mul_right_eq_delta_mul_left
    (h : I → ℝ) (i j : I) :
    delta i j * h j = delta i j * h i := by
  by_cases hij : i = j
  · subst j
    simp [delta]
  · simp [delta, hij]

theorem shifted_right_eigen
    (K : I → I → ℝ) (c lam : ℝ) (h : I → ℝ)
    (right_eigen : ∀ i, (∑ j, K i j * h j) = lam * h i)
    (i : I) :
    (∑ j, shiftedOperator K c i j * h j) = (c + lam) * h i := by
  classical
  calc
    (∑ j, shiftedOperator K c i j * h j) =
        ∑ j, (K i j * h j + c * (delta i j * h j)) := by
          apply Finset.sum_congr rfl
          intro j _
          simp only [shiftedOperator]
          ring
    _ = (∑ j, K i j * h j) +
        (∑ j, c * (delta i j * h j)) := by
          rw [Finset.sum_add_distrib]
    _ = (∑ j, K i j * h j) +
        c * (∑ j, delta i j * h j) := by
          rw [Finset.mul_sum]
    _ = (c + lam) * h i := by
          rw [right_eigen, sum_delta_mul]
          ring

theorem shifted_left_eigen
    (K : I → I → ℝ) (c lam : ℝ) (q : I → ℝ)
    (left_eigen : ∀ j, (∑ i, q i * K i j) = lam * q j)
    (j : I) :
    (∑ i, q i * shiftedOperator K c i j) = (c + lam) * q j := by
  classical
  calc
    (∑ i, q i * shiftedOperator K c i j) =
        ∑ i, (q i * K i j + c * (q i * delta i j)) := by
          apply Finset.sum_congr rfl
          intro i _
          simp only [shiftedOperator]
          ring
    _ = (∑ i, q i * K i j) +
        (∑ i, c * (q i * delta i j)) := by
          rw [Finset.sum_add_distrib]
    _ = (∑ i, q i * K i j) +
        c * (∑ i, q i * delta i j) := by
          rw [Finset.mul_sum]
    _ = (c + lam) * q j := by
          rw [left_eigen, sum_mul_delta]
          ring

omit [Fintype I] in
theorem shifted_doob_bridge
    (K : I → I → ℝ) (c lam : ℝ) (h : I → ℝ)
    (rho_ne : c + lam ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (i j : I) :
    discreteDoobEntry (shiftedOperator K c) (c + lam) h i j =
      delta i j + generatorDoobEntry K lam h i j / (c + lam) := by
  by_cases hij : i = j
  · subst j
    simp only [discreteDoobEntry, shiftedOperator, generatorDoobEntry]
    simp [delta]
    field_simp [rho_ne, h_nonzero i]
    ring
  · simp only [discreteDoobEntry, shiftedOperator, generatorDoobEntry]
    simp [delta, hij]
    field_simp [rho_ne, h_nonzero i]

omit [Fintype I] in
theorem shiftedOperator_nonneg
    (K : I → I → ℝ) (c : ℝ)
    (offdiag_nonneg : ∀ i j, i ≠ j → 0 ≤ K i j)
    (diag_shift_nonneg : ∀ i, 0 ≤ K i i + c) :
    ∀ i j, 0 ≤ shiftedOperator K c i j := by
  intro i j
  by_cases hij : i = j
  · subst j
    simpa [shiftedOperator, delta] using diag_shift_nonneg i
  · have hK : 0 ≤ K i j := offdiag_nonneg i j hij
    simpa [shiftedOperator, delta, hij] using hK

theorem sum_survivorWeight_delta
    (q h : I → ℝ) (j : I) :
    (∑ i, (q i * h i) * delta i j) = q j * h j := by
  exact sum_mul_delta (fun i ↦ q i * h i) j

theorem shifted_stationarity_transfer
    (K : I → I → ℝ) (c lam : ℝ) (q h : I → ℝ)
    (rho_ne : c + lam ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (gen_stationary :
      ∀ j, (∑ i, (q i * h i) * generatorDoobEntry K lam h i j) = 0)
    (j : I) :
    (∑ i, (q i * h i) *
      discreteDoobEntry (shiftedOperator K c) (c + lam) h i j) =
    q j * h j := by
  classical
  calc
    (∑ i, (q i * h i) *
      discreteDoobEntry (shiftedOperator K c) (c + lam) h i j) =
        ∑ i, ((q i * h i) * delta i j +
          ((q i * h i) * generatorDoobEntry K lam h i j) / (c + lam)) := by
            apply Finset.sum_congr rfl
            intro i _
            rw [shifted_doob_bridge K c lam h rho_ne h_nonzero i j]
            ring
    _ = (∑ i, (q i * h i) * delta i j) +
        (∑ i, ((q i * h i) * generatorDoobEntry K lam h i j) /
          (c + lam)) := by
            rw [Finset.sum_add_distrib]
    _ = q j * h j +
        (∑ i, (q i * h i) * generatorDoobEntry K lam h i j) /
          (c + lam) := by
            rw [sum_survivorWeight_delta, Finset.sum_div]
    _ = q j * h j := by
            rw [gen_stationary]
            simp

theorem shifted_normalized_stationarity_transfer
    (K : I → I → ℝ) (c lam : ℝ) (q h : I → ℝ)
    (rho_ne : c + lam ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (Z_ne : (∑ k, q k * h k) ≠ 0)
    (gen_stationary :
      ∀ j, (∑ i, (q i * h i) * generatorDoobEntry K lam h i j) = 0)
    (j : I) :
    (∑ i, ((q i * h i) / (∑ k, q k * h k)) *
      discreteDoobEntry (shiftedOperator K c) (c + lam) h i j) =
    (q j * h j) / (∑ k, q k * h k) := by
  classical
  calc
    (∑ i, ((q i * h i) / (∑ k, q k * h k)) *
      discreteDoobEntry (shiftedOperator K c) (c + lam) h i j) =
        (∑ i, (q i * h i) *
          discreteDoobEntry (shiftedOperator K c) (c + lam) h i j) /
            (∑ k, q k * h k) := by
              rw [Finset.sum_div]
              apply Finset.sum_congr rfl
              intro i _
              field_simp [Z_ne]
    _ = (q j * h j) / (∑ k, q k * h k) := by
          rw [shifted_stationarity_transfer
            K c lam q h rho_ne h_nonzero gen_stationary j]

end HTiltShiftBridge
