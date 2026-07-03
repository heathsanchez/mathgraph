import MCMC.PF.LinearAlgebra.Matrix.PerronFrobenius.Dominance
import Mathlib.Tactic

/-!
# Perron--Frobenius portal for a finite discrete H-Tilt survivor weight

This file is compiled in the quarantined `experiments/pf_port_lab` external-pin
Lake environment. It proves existence of positive left and right modes for an
irreducible nonnegative real matrix and the resulting unnormalized discrete
Doob stationary-weight identity.

It does not prove a killed-generator theorem, Markov convergence, ergodicity,
mixing, or any empirical H-Tilt claim.
-/

open scoped BigOperators

namespace HTiltPFDiscreteSurvivor

variable {ι : Type*} [Fintype ι] [Nonempty ι] [DecidableEq ι]

noncomputable def discreteDoobEntry
    (A : Matrix ι ι ℝ) (rho : ℝ) (h : ι → ℝ) (i j : ι) : ℝ :=
  (A i j * h j) / (rho * h i)

def survivorWeight (q h : ι → ℝ) (i : ι) : ℝ :=
  q i * h i

def survivorNorm (q h : ι → ℝ) : ℝ :=
  ∑ i, survivorWeight q h i

noncomputable def piStar (q h : ι → ℝ) (i : ι) : ℝ :=
  survivorWeight q h i / survivorNorm q h

omit [Fintype ι] [Nonempty ι] [DecidableEq ι] in
theorem survivorWeight_pos
    (q h : ι → ℝ)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i) :
    ∀ i, 0 < survivorWeight q h i := by
  intro i
  exact mul_pos (q_pos i) (h_pos i)

omit [DecidableEq ι] in
theorem survivorNorm_pos
    (q h : ι → ℝ)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i) :
    0 < survivorNorm q h := by
  classical
  exact Finset.sum_pos
    (fun i _ ↦ survivorWeight_pos q h q_pos h_pos i)
    Finset.univ_nonempty

omit [DecidableEq ι] in
theorem piStar_pos
    (q h : ι → ℝ)
    (q_pos : ∀ i, 0 < q i)
    (h_pos : ∀ i, 0 < h i) :
    ∀ i, 0 < piStar q h i := by
  intro i
  exact div_pos
    (survivorWeight_pos q h q_pos h_pos i)
    (survivorNorm_pos q h q_pos h_pos)

omit [DecidableEq ι] in
theorem piStar_sum_one
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

omit [Fintype ι] [Nonempty ι] [DecidableEq ι] in
theorem discreteDoobEntry_nonneg
    (A : Matrix ι ι ℝ) (rho : ℝ) (h : ι → ℝ)
    (A_nonneg : ∀ i j, 0 ≤ A i j)
    (rho_pos : 0 < rho)
    (h_pos : ∀ i, 0 < h i) :
    ∀ i j, 0 ≤ discreteDoobEntry A rho h i j := by
  intro i j
  exact div_nonneg
    (mul_nonneg (A_nonneg i j) (h_pos j).le)
    (mul_nonneg rho_pos.le (h_pos i).le)

omit [Nonempty ι] [DecidableEq ι] in
theorem discrete_doob_unnormalized_stationary
    (A : Matrix ι ι ℝ) (rho : ℝ) (q h : ι → ℝ)
    (rho_ne : rho ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (left_eigen : Matrix.mulVec (Matrix.transpose A) q = rho • q)
    (j : ι) :
    ∑ i, survivorWeight q h i * discreteDoobEntry A rho h i j =
      survivorWeight q h j := by
  classical
  have left_eigen_apply : (∑ i, q i * A i j) = rho * q j := by
    have := congrFun left_eigen j
    simpa [Matrix.mulVec, mul_comm] using this
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
          rw [left_eigen_apply]
          simp only [survivorWeight]
          field_simp [rho_ne]

omit [Nonempty ι] [DecidableEq ι] in
theorem discrete_doob_normalized_stationary
    (A : Matrix ι ι ℝ) (rho : ℝ) (q h : ι → ℝ)
    (rho_ne : rho ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (left_eigen : Matrix.mulVec (Matrix.transpose A) q = rho • q)
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

omit [Nonempty ι] [DecidableEq ι] in
theorem discrete_doob_row_sum_one
    (A : Matrix ι ι ℝ) (rho : ℝ) (h : ι → ℝ)
    (rho_ne : rho ≠ 0)
    (h_nonzero : ∀ i, h i ≠ 0)
    (right_eigen : Matrix.mulVec A h = rho • h)
    (i : ι) :
    ∑ j, discreteDoobEntry A rho h i j = 1 := by
  classical
  have right_eigen_apply : (∑ j, A i j * h j) = rho * h i := by
    have := congrFun right_eigen i
    simpa [Matrix.mulVec] using this
  simp only [discreteDoobEntry]
  calc
    (∑ j, (A i j * h j) / (rho * h i)) =
        (∑ j, A i j * h j) / (rho * h i) := by
          rw [Finset.sum_div]
    _ = 1 := by
          rw [right_eigen_apply]
          field_simp [rho_ne, h_nonzero i]

/--
An irreducible nonnegative real matrix has positive right and transpose-right
modes with one Perron eigenvalue. Their pointwise product is stationary for the
corresponding discrete Doob transform.
-/
theorem exists_positive_survivor_weight_of_irreducible
    (A : Matrix ι ι ℝ)
    (hA : A.IsIrreducible) :
    ∃ rho h q,
      0 < rho ∧
      (∀ i, 0 < h i) ∧
      (∀ i, 0 < q i) ∧
      Matrix.mulVec A h = rho • h ∧
      Matrix.mulVec (Matrix.transpose A) q = rho • q ∧
      (∀ j,
        ∑ i, survivorWeight q h i * discreteDoobEntry A rho h i j =
          survivorWeight q h j) := by
  obtain ⟨rho, h, rho_pos, h_pos, right_eigen, rho_root⟩ :=
    Matrix.perron_root_eq_positive_eigenvalue hA hA.nonneg
  have hAT : (Matrix.transpose A).IsIrreducible :=
    Matrix.IsIrreducible.transpose hA
  obtain ⟨rhoT, q, rhoT_pos, q_pos, transpose_eigen, rhoT_root⟩ :=
    Matrix.perron_root_eq_positive_eigenvalue hAT hAT.nonneg
  have root_transpose :=
    Matrix.perronRoot_transpose_eq A hA
  have rhoT_eq_rho : rhoT = rho := by
    calc
      rhoT = Matrix.CollatzWielandt.perronRoot_alt (Matrix.transpose A) :=
        rhoT_root.symm
      _ = Matrix.CollatzWielandt.perronRoot_alt A := root_transpose.symm
      _ = rho := rho_root
  have transpose_eigen_rho :
      Matrix.mulVec (Matrix.transpose A) q = rho • q := by
    simpa [rhoT_eq_rho] using transpose_eigen
  refine ⟨rho, h, q, rho_pos, h_pos, q_pos, right_eigen,
    transpose_eigen_rho, ?_⟩
  intro j
  exact discrete_doob_unnormalized_stationary
    A rho q h rho_pos.ne' (fun i ↦ (h_pos i).ne') transpose_eigen_rho j

/--
Every irreducible nonnegative finite real matrix admits a positive Perron
eigenvalue and positive left/right modes whose discrete Doob transform is
nonnegative and row-stochastic, with a strictly positive normalized stationary
distribution proportional to their pointwise product.
-/
theorem exists_positive_stationary_distribution_of_irreducible
    (A : Matrix ι ι ℝ)
    (hA : A.IsIrreducible) :
    ∃ rho h q,
      0 < rho ∧
      (∀ i, 0 < h i) ∧
      (∀ i, 0 < q i) ∧
      Matrix.mulVec A h = rho • h ∧
      Matrix.mulVec (Matrix.transpose A) q = rho • q ∧
      (∀ i, 0 < piStar q h i) ∧
      (∑ i, piStar q h i) = 1 ∧
      (∀ i j, 0 ≤ discreteDoobEntry A rho h i j) ∧
      (∀ i, (∑ j, discreteDoobEntry A rho h i j) = 1) ∧
      (∀ j, (∑ i, piStar q h i * discreteDoobEntry A rho h i j) =
        piStar q h j) := by
  obtain ⟨rho, h, q, rho_pos, h_pos, q_pos, right_eigen,
      left_eigen, _⟩ :=
    exists_positive_survivor_weight_of_irreducible A hA
  have rho_ne : rho ≠ 0 := rho_pos.ne'
  have h_nonzero : ∀ i, h i ≠ 0 := fun i ↦ (h_pos i).ne'
  have norm_nonzero : survivorNorm q h ≠ 0 :=
    (survivorNorm_pos q h q_pos h_pos).ne'
  refine ⟨rho, h, q, rho_pos, h_pos, q_pos, right_eigen, left_eigen,
    piStar_pos q h q_pos h_pos,
    piStar_sum_one q h q_pos h_pos,
    discreteDoobEntry_nonneg A rho h hA.nonneg rho_pos h_pos,
    ?_, ?_⟩
  · intro i
    exact discrete_doob_row_sum_one
      A rho h rho_ne h_nonzero right_eigen i
  · intro j
    exact discrete_doob_normalized_stationary
      A rho q h rho_ne h_nonzero left_eigen norm_nonzero j

end HTiltPFDiscreteSurvivor
