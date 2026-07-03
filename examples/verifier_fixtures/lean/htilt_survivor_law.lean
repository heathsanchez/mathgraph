import Mathlib.Algebra.BigOperators.Field
import Mathlib.Analysis.SpecialFunctions.Pow.Real
import Mathlib.Data.Real.Basic
import Mathlib.Tactic.FieldSimp
import Mathlib.Tactic.Ring

/-!
# Finite H-Tilt survivor law

This file proves only finite algebraic identities under explicit left- and
right-eigenvector assumptions.  It does not supply eigenvectors or prove any
probabilistic, empirical, scheduling, or metaphysical interpretation.
-/

open scoped BigOperators

namespace HTiltSurvivorLaw

variable {ι : Type*} [Fintype ι] [DecidableEq ι]

def delta (i j : ι) : ℝ :=
  if i = j then 1 else 0

noncomputable def doobEntry
    (K : ι → ι → ℝ) (lam : ℝ) (h : ι → ℝ) (i j : ι) : ℝ :=
  ((K i j - lam * delta i j) * h j) / h i

def survivorWeight (q h : ι → ℝ) (i : ι) : ℝ :=
  q i * h i

def survivorNorm (q h : ι → ℝ) : ℝ :=
  ∑ i, survivorWeight q h i

noncomputable def piStar (q h : ι → ℝ) (i : ι) : ℝ :=
  survivorWeight q h i / survivorNorm q h

noncomputable def geometricBridge
    (q h : ι → ℝ) (β : ℝ) (i : ι) : ℝ :=
  (q i) ^ (1 - β) * (piStar q h i) ^ β

noncomputable def geometricBridgeNat
    (q h : ι → ℝ) (n : ℕ) (i : ι) : ℝ :=
  (q i) ^ (1 - n) * (piStar q h i) ^ n

noncomputable def geometricLogExpBridge
    (q h : ι → ℝ) (β : ℝ) (i : ι) : ℝ :=
  Real.exp
    ((1 - β) * Real.log (q i) + β * Real.log (piStar q h i))

/- Backward-compatible names for the original geometric bridge API. -/
noncomputable abbrev powerBridge
    (q h : ι → ℝ) (β : ℝ) (i : ι) : ℝ :=
  geometricBridge q h β i

noncomputable abbrev powerBridgeNat
    (q h : ι → ℝ) (n : ℕ) (i : ι) : ℝ :=
  geometricBridgeNat q h n i

noncomputable abbrev logExpBridge
    (q h : ι → ℝ) (β : ℝ) (i : ι) : ℝ :=
  geometricLogExpBridge q h β i

/- The paper-native normalized bridge `qᵢ hᵢ^β / Σⱼ qⱼ hⱼ^β`. -/
noncomputable def multiplicativeBridgeNat
    (q h : ι → ℝ) (n : ℕ) (i : ι) : ℝ :=
  q i * (h i) ^ n / (∑ j, q j * (h j) ^ n)

noncomputable def multiplicativeBridgeReal
    (q h : ι → ℝ) (β : ℝ) (i : ι) : ℝ :=
  q i * (h i) ^ β / (∑ j, q j * (h j) ^ β)

theorem sum_delta_left (j : ι) :
    ∑ i, delta i j = 1 := by
  classical
  simp [delta]

theorem sum_delta_right (i : ι) :
    ∑ j, delta i j = 1 := by
  classical
  simp [delta]

theorem sum_mul_delta (q : ι → ℝ) (j : ι) :
    ∑ i, q i * delta i j = q j := by
  classical
  simp [delta]

theorem sum_delta_mul (h : ι → ℝ) (i : ι) :
    ∑ j, delta i j * h j = h i := by
  classical
  simp [delta]

theorem htilt_unnormalized_stationary
    (K : ι → ι → ℝ) (lam : ℝ) (q h : ι → ℝ)
    (h_nonzero : ∀ i, h i ≠ 0)
    (left_eigen : ∀ j, (∑ i, q i * K i j) = lam * q j)
    (j : ι) :
    ∑ i, survivorWeight q h i * doobEntry K lam h i j = 0 := by
  classical
  have cancelled :
      (∑ i, survivorWeight q h i * doobEntry K lam h i j) =
        (∑ i, q i * (K i j - lam * delta i j)) * h j := by
    rw [Finset.sum_mul]
    apply Finset.sum_congr rfl
    intro i _
    simp only [survivorWeight, doobEntry]
    field_simp [h_nonzero i]
  have centered :
      (∑ i, q i * (K i j - lam * delta i j)) =
        (∑ i, q i * K i j) - lam * q j := by
    calc
      (∑ i, q i * (K i j - lam * delta i j)) =
          ∑ i, (q i * K i j - lam * (q i * delta i j)) := by
            apply Finset.sum_congr rfl
            intro i _
            ring
      _ = (∑ i, q i * K i j) -
          (∑ i, lam * (q i * delta i j)) := by
            rw [Finset.sum_sub_distrib]
      _ = (∑ i, q i * K i j) -
          lam * (∑ i, q i * delta i j) := by
            rw [Finset.mul_sum]
      _ = (∑ i, q i * K i j) - lam * q j := by
            rw [sum_mul_delta]
  rw [cancelled, centered, left_eigen]
  ring

theorem htilt_normalized_stationary
    (K : ι → ι → ℝ) (lam : ℝ) (q h : ι → ℝ)
    (h_nonzero : ∀ i, h i ≠ 0)
    (left_eigen : ∀ j, (∑ i, q i * K i j) = lam * q j)
    (norm_nonzero : survivorNorm q h ≠ 0)
    (j : ι) :
    ∑ i, piStar q h i * doobEntry K lam h i j = 0 := by
  classical
  calc
    (∑ i, piStar q h i * doobEntry K lam h i j) =
        (∑ i, survivorWeight q h i * doobEntry K lam h i j) /
          survivorNorm q h := by
            rw [Finset.sum_div]
            apply Finset.sum_congr rfl
            intro i _
            simp only [piStar]
            field_simp [norm_nonzero]
    _ = 0 := by
      rw [htilt_unnormalized_stationary K lam q h h_nonzero left_eigen j]
      simp

theorem doob_row_sum_zero
    (K : ι → ι → ℝ) (lam : ℝ) (h : ι → ℝ)
    (h_nonzero : ∀ i, h i ≠ 0)
    (right_eigen : ∀ i, (∑ j, K i j * h j) = lam * h i)
    (i : ι) :
    ∑ j, doobEntry K lam h i j = 0 := by
  classical
  simp only [doobEntry]
  calc
    (∑ j, ((K i j - lam * delta i j) * h j) / h i) =
        (∑ j, (K i j - lam * delta i j) * h j) / h i := by
          rw [Finset.sum_div]
    _ = ((∑ j, K i j * h j) -
          lam * (∑ j, delta i j * h j)) / h i := by
            congr 1
            calc
              (∑ j, (K i j - lam * delta i j) * h j) =
                  ∑ j, (K i j * h j -
                    lam * (delta i j * h j)) := by
                      apply Finset.sum_congr rfl
                      intro j _
                      ring
              _ = (∑ j, K i j * h j) -
                  (∑ j, lam * (delta i j * h j)) := by
                    rw [Finset.sum_sub_distrib]
              _ = (∑ j, K i j * h j) -
                  lam * (∑ j, delta i j * h j) := by
                    rw [Finset.mul_sum]
    _ = 0 := by
      rw [right_eigen, sum_delta_mul]
      field_simp [h_nonzero i]
      ring

omit [DecidableEq ι] in
theorem geometric_bridge_one_eq_piStar
    (q h : ι → ℝ) (i : ι) :
    geometricBridge q h 1 i = piStar q h i := by
  simp [geometricBridge]

omit [DecidableEq ι] in
theorem power_bridge_one_eq_piStar
    (q h : ι → ℝ) (i : ι) :
    powerBridge q h 1 i = piStar q h i :=
  geometric_bridge_one_eq_piStar q h i

omit [DecidableEq ι] in
theorem geometric_bridge_nat_one_eq_piStar
    (q h : ι → ℝ) (i : ι) :
    geometricBridgeNat q h 1 i = piStar q h i := by
  simp [geometricBridgeNat]

omit [DecidableEq ι] in
theorem power_bridge_nat_one_eq_piStar
    (q h : ι → ℝ) (i : ι) :
    powerBridgeNat q h 1 i = piStar q h i :=
  geometric_bridge_nat_one_eq_piStar q h i

omit [DecidableEq ι] in
theorem geometric_log_exp_bridge_eq_geometric_bridge
    (q h : ι → ℝ) (β : ℝ) (i : ι)
    (q_positive : 0 < q i)
    (pi_positive : 0 < piStar q h i) :
    geometricLogExpBridge q h β i = geometricBridge q h β i := by
  rw [geometricBridge, geometricLogExpBridge]
  rw [Real.rpow_def_of_pos q_positive, Real.rpow_def_of_pos pi_positive]
  rw [← Real.exp_add]
  congr 1
  ring

omit [DecidableEq ι] in
theorem log_exp_bridge_eq_power
    (q h : ι → ℝ) (β : ℝ) (i : ι)
    (q_positive : 0 < q i)
    (pi_positive : 0 < piStar q h i) :
    logExpBridge q h β i = powerBridge q h β i :=
  geometric_log_exp_bridge_eq_geometric_bridge
    q h β i q_positive pi_positive

omit [DecidableEq ι] in
theorem multiplicative_bridge_nat_one_eq_piStar
    (q h : ι → ℝ) (i : ι) :
    multiplicativeBridgeNat q h 1 i = piStar q h i := by
  simp [multiplicativeBridgeNat, piStar, survivorWeight, survivorNorm]

omit [DecidableEq ι] in
theorem multiplicative_bridge_real_one_eq_piStar
    (q h : ι → ℝ)
    (i : ι) :
    multiplicativeBridgeReal q h 1 i = piStar q h i := by
  simp [multiplicativeBridgeReal, piStar, survivorWeight, survivorNorm]

omit [Fintype ι] [DecidableEq ι] in
theorem multiplicative_log_exp_pointwise_eq
    (β : ℝ) (q h : ι → ℝ)
    (h_positive : ∀ i, 0 < h i) :
    ∀ i, q i * Real.exp (β * Real.log (h i)) =
      q i * (h i) ^ β := by
  intro i
  rw [Real.rpow_def_of_pos (h_positive i)]
  congr 2
  ring

end HTiltSurvivorLaw
