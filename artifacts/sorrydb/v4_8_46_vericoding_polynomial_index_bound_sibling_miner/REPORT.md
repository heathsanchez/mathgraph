# MathGraph SorryDB v4.8.46 - vericoding Polynomial Index-Bound Sibling Miner

## Purpose

Find next transfer targets for the certified route law:

    polynomial/Vandermonde flattened index + Fin degree bounds -> Nat product bound proof

Already-covered PR #12 files were excluded.

## Excluded files

- `specs/LT0032_specs.lean`
- `specs/LT0401_specs.lean`
- `specs/LT0479_specs.lean`
- `specs/LT0480_specs.lean`
- `specs/LT0505_specs.lean`
- `specs/LT0506_specs.lean`

## Candidate count

- candidates: 236

## Top candidates

### 1. score 130 - specs/LT0429_specs.lean:30
- current: `(∀ p : Fin n, order > 0 → (result.get p).get ⟨0, by sorry⟩ = 1) ∧`
- reasons: polynomial_file_keywords:vander,vander3d,polynomial,hermite, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape, 3d_shape, degree_successor_product, explicit_bound_statement_nearby
- penalties: existential_context, abstract_order_may_need_definition

Window:

    -- <vc-theorems>
    theorem hermevander3d_spec {n : Nat} (x y z : Vector Float n) (deg : Vector Nat 3) :
        ⦃⌜True⌝⦄
        hermevander3d x y z deg
        ⦃⇓result => ⌜
          let x_deg := deg.get ⟨0, by simp⟩
          let y_deg := deg.get ⟨1, by simp⟩
          let z_deg := deg.get ⟨2, by simp⟩
          let order := (x_deg + 1) * (y_deg + 1) * (z_deg + 1)
    
          -- Shape property: result has n rows, each with order elements (enforced by types)
          True ∧
    
          -- Base case: first column is all ones (He_0(x)*He_0(y)*He_0(z) = 1*1*1 = 1)
          (∀ p : Fin n, order > 0 → (result.get p).get ⟨0, by sorry⟩ = 1) ∧
    
          -- Mathematical consistency: tensor product structure
          (∃ hermite_poly : Nat → Float → Float,
            -- HermiteE polynomial base cases
            (∀ t : Float, hermite_poly 0 t = 1) ∧
            (∀ t : Float, hermite_poly 1 t = t) ∧
            -- HermiteE polynomial recurrence relation
            (∀ k : Nat, k ≥ 2 → ∀ t : Float, 
              hermite_poly k t = t * hermite_poly (k-1) t - Float.ofNat (k-1) * hermite_poly (k-2) t) ∧
            -- Each matrix element follows the 3D product formula
            (∀ p : Fin n, ∀ i : Nat, ∀ j : Nat, ∀ k : Nat,
              i ≤ x_deg → j ≤ y_deg → k ≤ z_deg →
              let col_idx := (y_deg + 1) * (z_deg + 1) * i + (z_deg + 1) * j + k
              col_idx < order →

### 2. score 130 - specs/LT0429_specs.lean:45
- current: `(result.get p).get ⟨col_idx, by sorry⟩ =`
- reasons: polynomial_file_keywords:vander,vander3d,polynomial,hermite, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape, 3d_shape, degree_successor_product, explicit_bound_statement_nearby
- penalties: existential_context, abstract_order_may_need_definition

Window:

    
          -- Mathematical consistency: tensor product structure
          (∃ hermite_poly : Nat → Float → Float,
            -- HermiteE polynomial base cases
            (∀ t : Float, hermite_poly 0 t = 1) ∧
            (∀ t : Float, hermite_poly 1 t = t) ∧
            -- HermiteE polynomial recurrence relation
            (∀ k : Nat, k ≥ 2 → ∀ t : Float, 
              hermite_poly k t = t * hermite_poly (k-1) t - Float.ofNat (k-1) * hermite_poly (k-2) t) ∧
            -- Each matrix element follows the 3D product formula
            (∀ p : Fin n, ∀ i : Nat, ∀ j : Nat, ∀ k : Nat,
              i ≤ x_deg → j ≤ y_deg → k ≤ z_deg →
              let col_idx := (y_deg + 1) * (z_deg + 1) * i + (z_deg + 1) * j + k
              col_idx < order →
              (result.get p).get ⟨col_idx, by sorry⟩ = 
                hermite_poly i (x.get p) * hermite_poly j (y.get p) * hermite_poly k (z.get p))) ∧
    
          -- Orthogonality property: HermiteE polynomials are orthogonal with respect to Gaussian weight
          (∀ p : Fin n, ∀ i₁ j₁ k₁ i₂ j₂ k₂ : Nat,
            i₁ ≤ x_deg → j₁ ≤ y_deg → k₁ ≤ z_deg →
            i₂ ≤ x_deg → j₂ ≤ y_deg → k₂ ≤ z_deg →
            (i₁ ≠ i₂ ∨ j₁ ≠ j₂ ∨ k₁ ≠ k₂) →
            let col_idx₁ := (y_deg + 1) * (z_deg + 1) * i₁ + (z_deg + 1) * j₁ + k₁
            let col_idx₂ := (y_deg + 1) * (z_deg + 1) * i₂ + (z_deg + 1) * j₂ + k₂
            col_idx₁ < order → col_idx₂ < order →
            -- Different polynomial products are linearly independent
            (result.get p).get ⟨col_idx₁, by sorry⟩ ≠ (result.get p).get ⟨col_idx₂, by sorry⟩ ∨ 
            x.get p = 0 ∧ y.get p = 0 ∧ z.get p = 0) ∧

### 3. score 130 - specs/LT0429_specs.lean:57
- current: `(result.get p).get ⟨col_idx₁, by sorry⟩ ≠ (result.get p).get ⟨col_idx₂, by sorry⟩ ∨`
- reasons: polynomial_file_keywords:vander,vander3d,polynomial,hermite, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape, 3d_shape, degree_successor_product, explicit_bound_statement_nearby
- penalties: existential_context, abstract_order_may_need_definition

Window:

              let col_idx := (y_deg + 1) * (z_deg + 1) * i + (z_deg + 1) * j + k
              col_idx < order →
              (result.get p).get ⟨col_idx, by sorry⟩ = 
                hermite_poly i (x.get p) * hermite_poly j (y.get p) * hermite_poly k (z.get p))) ∧
    
          -- Orthogonality property: HermiteE polynomials are orthogonal with respect to Gaussian weight
          (∀ p : Fin n, ∀ i₁ j₁ k₁ i₂ j₂ k₂ : Nat,
            i₁ ≤ x_deg → j₁ ≤ y_deg → k₁ ≤ z_deg →
            i₂ ≤ x_deg → j₂ ≤ y_deg → k₂ ≤ z_deg →
            (i₁ ≠ i₂ ∨ j₁ ≠ j₂ ∨ k₁ ≠ k₂) →
            let col_idx₁ := (y_deg + 1) * (z_deg + 1) * i₁ + (z_deg + 1) * j₁ + k₁
            let col_idx₂ := (y_deg + 1) * (z_deg + 1) * i₂ + (z_deg + 1) * j₂ + k₂
            col_idx₁ < order → col_idx₂ < order →
            -- Different polynomial products are linearly independent
            (result.get p).get ⟨col_idx₁, by sorry⟩ ≠ (result.get p).get ⟨col_idx₂, by sorry⟩ ∨ 
            x.get p = 0 ∧ y.get p = 0 ∧ z.get p = 0) ∧
    
          -- Consistency with evaluation: dot product with coefficients equals 3D polynomial evaluation
          (∀ p : Fin n, ∀ coeff : Vector Float order,
            ∃ polynomial_value : Float,
              -- The dot product of the Vandermonde row with coefficients
              -- equals the evaluation of the 3D HermiteE polynomial expansion
              polynomial_value = (List.sum (List.ofFn (fun i : Fin order => (result.get p).get i * coeff.get i)))) ∧
    
          -- Parity property: HermiteE polynomials satisfy He_n(-x) = (-1)^n * He_n(x)
          (∃ hermite_poly : Nat → Float → Float,
            (∀ k : Nat, k ≤ max (max x_deg y_deg) z_deg → ∀ t : Float,
              hermite_poly k (-t) = (if k % 2 = 0 then 1 else -1) * hermite_poly k t) ∧
            -- This parity property is reflected in the matrix structure

### 4. score 130 - specs/LT0429_specs.lean:76
- current: `(result.get p).get ⟨col_idx, by sorry⟩ =`
- reasons: polynomial_file_keywords:vander,vander3d,polynomial,hermite, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape, 3d_shape, degree_successor_product, explicit_bound_statement_nearby
- penalties: existential_context, abstract_order_may_need_definition

Window:

            ∃ polynomial_value : Float,
              -- The dot product of the Vandermonde row with coefficients
              -- equals the evaluation of the 3D HermiteE polynomial expansion
              polynomial_value = (List.sum (List.ofFn (fun i : Fin order => (result.get p).get i * coeff.get i)))) ∧
    
          -- Parity property: HermiteE polynomials satisfy He_n(-x) = (-1)^n * He_n(x)
          (∃ hermite_poly : Nat → Float → Float,
            (∀ k : Nat, k ≤ max (max x_deg y_deg) z_deg → ∀ t : Float,
              hermite_poly k (-t) = (if k % 2 = 0 then 1 else -1) * hermite_poly k t) ∧
            -- This parity property is reflected in the matrix structure
            (∀ p : Fin n, ∀ i j k : Nat,
              i ≤ x_deg → j ≤ y_deg → k ≤ z_deg →
              let col_idx := (y_deg + 1) * (z_deg + 1) * i + (z_deg + 1) * j + k
              col_idx < order →
              (result.get p).get ⟨col_idx, by sorry⟩ = 
                hermite_poly i (x.get p) * hermite_poly j (y.get p) * hermite_poly k (z.get p)))
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 5. score 110 - specs/LT0513_specs.lean:23
- current: `(m = 0 → ∀ i : Fin n, result.get ⟨i.val, sorry⟩ = c.get i) ∧`
- reasons: polynomial_file_keywords:polynomial, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    
    -- <vc-definitions>
    def polyder {n : Nat} (c : Vector Float n) (m : Nat := 1) (scl : Float := 1) 
        (h : m ≤ n) : Id (Vector Float (n - m)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem polyder_spec {n : Nat} (c : Vector Float n) (m : Nat) (scl : Float) 
        (h : m ≤ n) :
        ⦃⌜m ≤ n⌝⦄
        polyder c m scl h
        ⦃⇓result => ⌜
          -- Special case: m = 0 returns original polynomial
          (m = 0 → ∀ i : Fin n, result.get ⟨i.val, sorry⟩ = c.get i) ∧
          -- General case: m > 0
          (m > 0 → 
            ∀ i : Fin (n - m), 
              -- The coefficient at position i comes from original position i+m
              -- It's multiplied by m consecutive factors: (i+m) * (i+m-1) * ... * (i+1)
              -- and scaled by scl^m
              let original_idx := i.val + m
              let factorial_factor := (List.range m).foldl 
                (fun acc k => acc * (original_idx - k).toFloat) 1.0
              let scale_factor := (List.range m).foldl 
                (fun acc _ => acc * scl) 1.0
              result.get i = c.get ⟨original_idx, sorry⟩ * factorial_factor * scale_factor
          )
        ⌝⦄ := by

### 6. score 110 - specs/LT0513_specs.lean:35
- current: `result.get i = c.get ⟨original_idx, sorry⟩ * factorial_factor * scale_factor`
- reasons: polynomial_file_keywords:polynomial, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

        ⦃⇓result => ⌜
          -- Special case: m = 0 returns original polynomial
          (m = 0 → ∀ i : Fin n, result.get ⟨i.val, sorry⟩ = c.get i) ∧
          -- General case: m > 0
          (m > 0 → 
            ∀ i : Fin (n - m), 
              -- The coefficient at position i comes from original position i+m
              -- It's multiplied by m consecutive factors: (i+m) * (i+m-1) * ... * (i+1)
              -- and scaled by scl^m
              let original_idx := i.val + m
              let factorial_factor := (List.range m).foldl 
                (fun acc k => acc * (original_idx - k).toFloat) 1.0
              let scale_factor := (List.range m).foldl 
                (fun acc _ => acc * scl) 1.0
              result.get i = c.get ⟨original_idx, sorry⟩ * factorial_factor * scale_factor
          )
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 7. score 100 - specs/LT0429_specs.lean:79
- current: `sorry`
- reasons: polynomial_file_keywords:vander,vander3d,polynomial,hermite, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape, degree_successor_product, explicit_bound_statement_nearby
- penalties: bare_theorem_or_def_sorry, existential_context, abstract_order_may_need_definition

Window:

              polynomial_value = (List.sum (List.ofFn (fun i : Fin order => (result.get p).get i * coeff.get i)))) ∧
    
          -- Parity property: HermiteE polynomials satisfy He_n(-x) = (-1)^n * He_n(x)
          (∃ hermite_poly : Nat → Float → Float,
            (∀ k : Nat, k ≤ max (max x_deg y_deg) z_deg → ∀ t : Float,
              hermite_poly k (-t) = (if k % 2 = 0 then 1 else -1) * hermite_poly k t) ∧
            -- This parity property is reflected in the matrix structure
            (∀ p : Fin n, ∀ i j k : Nat,
              i ≤ x_deg → j ≤ y_deg → k ≤ z_deg →
              let col_idx := (y_deg + 1) * (z_deg + 1) * i + (z_deg + 1) * j + k
              col_idx < order →
              (result.get p).get ⟨col_idx, by sorry⟩ = 
                hermite_poly i (x.get p) * hermite_poly j (y.get p) * hermite_poly k (z.get p)))
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 8. score 95 - specs/LT0428_specs.lean:45
- current: `flattened_coeff.get ⟨(y_deg + 1) * i.val + j.val, sorry⟩ =`
- reasons: polynomial_file_keywords:vander,vander2d,polynomial,hermite, fin_get_sorry, fin_context, mul_plus_flatten_shape, 2d_shape, degree_successor_product
- penalties: existential_context

Window:

                         hermite_basis (k + 1) t = t * hermite_basis k t - Float.ofNat k * hermite_basis (k - 1) t) ∧
                       -- Matrix entries computed correctly using basis functions
                       (∀ point_idx : Fin n, ∀ basis_idx : Fin ((x_deg + 1) * (y_deg + 1)),
                         -- Extract degree indices from basis index
                         ∃ i j : Nat, i ≤ x_deg ∧ j ≤ y_deg ∧ 
                         basis_idx.val = (y_deg + 1) * i + j ∧
                         -- Matrix entry is the product of HermiteE basis functions
                         (result.get point_idx).get basis_idx = 
                           hermite_basis i (x.get point_idx) * hermite_basis j (y.get point_idx))) ∧
                     -- Polynomial evaluation equivalence property exists
                     (∀ coeff_matrix : Vector (Vector Float (y_deg + 1)) (x_deg + 1),
                       ∃ flattened_coeff : Vector Float ((x_deg + 1) * (y_deg + 1)),
                       -- Coefficient flattening follows row-major order
                       (∀ i : Fin (x_deg + 1), ∀ j : Fin (y_deg + 1),
                         flattened_coeff.get ⟨(y_deg + 1) * i.val + j.val, sorry⟩ = 
                         (coeff_matrix.get i).get j) ∧
                       -- Matrix-vector multiplication gives polynomial evaluation
                       ∀ point_idx : Fin n,
                       (List.range ((x_deg + 1) * (y_deg + 1))).foldl (fun acc k =>
                         acc + (result.get point_idx).get ⟨k, sorry⟩ * flattened_coeff.get ⟨k, sorry⟩
                       ) 0 = 
                       -- Equivalent to direct 2D polynomial evaluation  
                       (List.range (x_deg + 1)).foldl (fun acc_i i =>
                         acc_i + (List.range (y_deg + 1)).foldl (fun acc_j j =>
                           acc_j + (coeff_matrix.get ⟨i, sorry⟩).get ⟨j, sorry⟩ * 
                           -- Note: hermite_basis exists from above, this is evaluation at point
                           1.0  -- Placeholder for correct hermite evaluation
                         ) 0
                       ) 0) ∧

### 9. score 95 - specs/LT0428_specs.lean:50
- current: `acc + (result.get point_idx).get ⟨k, sorry⟩ * flattened_coeff.get ⟨k, sorry⟩`
- reasons: polynomial_file_keywords:vander,vander2d,polynomial,hermite, fin_get_sorry, fin_context, mul_plus_flatten_shape, 2d_shape, degree_successor_product
- penalties: existential_context

Window:

                         basis_idx.val = (y_deg + 1) * i + j ∧
                         -- Matrix entry is the product of HermiteE basis functions
                         (result.get point_idx).get basis_idx = 
                           hermite_basis i (x.get point_idx) * hermite_basis j (y.get point_idx))) ∧
                     -- Polynomial evaluation equivalence property exists
                     (∀ coeff_matrix : Vector (Vector Float (y_deg + 1)) (x_deg + 1),
                       ∃ flattened_coeff : Vector Float ((x_deg + 1) * (y_deg + 1)),
                       -- Coefficient flattening follows row-major order
                       (∀ i : Fin (x_deg + 1), ∀ j : Fin (y_deg + 1),
                         flattened_coeff.get ⟨(y_deg + 1) * i.val + j.val, sorry⟩ = 
                         (coeff_matrix.get i).get j) ∧
                       -- Matrix-vector multiplication gives polynomial evaluation
                       ∀ point_idx : Fin n,
                       (List.range ((x_deg + 1) * (y_deg + 1))).foldl (fun acc k =>
                         acc + (result.get point_idx).get ⟨k, sorry⟩ * flattened_coeff.get ⟨k, sorry⟩
                       ) 0 = 
                       -- Equivalent to direct 2D polynomial evaluation  
                       (List.range (x_deg + 1)).foldl (fun acc_i i =>
                         acc_i + (List.range (y_deg + 1)).foldl (fun acc_j j =>
                           acc_j + (coeff_matrix.get ⟨i, sorry⟩).get ⟨j, sorry⟩ * 
                           -- Note: hermite_basis exists from above, this is evaluation at point
                           1.0  -- Placeholder for correct hermite evaluation
                         ) 0
                       ) 0) ∧
                     -- Vandermonde matrix properties for polynomial fitting
                     (n ≥ (x_deg + 1) * (y_deg + 1) → 
                       -- Full rank condition for overdetermined systems
                       ∃ rank_val : Nat, rank_val = (x_deg + 1) * (y_deg + 1) ∧
                       -- Matrix has full column rank for unique least squares solution

### 10. score 95 - specs/LT0428_specs.lean:55
- current: `acc_j + (coeff_matrix.get ⟨i, sorry⟩).get ⟨j, sorry⟩ *`
- reasons: polynomial_file_keywords:vander,vander2d,polynomial,hermite, fin_get_sorry, fin_context, mul_plus_flatten_shape, 2d_shape, degree_successor_product
- penalties: existential_context

Window:

                     (∀ coeff_matrix : Vector (Vector Float (y_deg + 1)) (x_deg + 1),
                       ∃ flattened_coeff : Vector Float ((x_deg + 1) * (y_deg + 1)),
                       -- Coefficient flattening follows row-major order
                       (∀ i : Fin (x_deg + 1), ∀ j : Fin (y_deg + 1),
                         flattened_coeff.get ⟨(y_deg + 1) * i.val + j.val, sorry⟩ = 
                         (coeff_matrix.get i).get j) ∧
                       -- Matrix-vector multiplication gives polynomial evaluation
                       ∀ point_idx : Fin n,
                       (List.range ((x_deg + 1) * (y_deg + 1))).foldl (fun acc k =>
                         acc + (result.get point_idx).get ⟨k, sorry⟩ * flattened_coeff.get ⟨k, sorry⟩
                       ) 0 = 
                       -- Equivalent to direct 2D polynomial evaluation  
                       (List.range (x_deg + 1)).foldl (fun acc_i i =>
                         acc_i + (List.range (y_deg + 1)).foldl (fun acc_j j =>
                           acc_j + (coeff_matrix.get ⟨i, sorry⟩).get ⟨j, sorry⟩ * 
                           -- Note: hermite_basis exists from above, this is evaluation at point
                           1.0  -- Placeholder for correct hermite evaluation
                         ) 0
                       ) 0) ∧
                     -- Vandermonde matrix properties for polynomial fitting
                     (n ≥ (x_deg + 1) * (y_deg + 1) → 
                       -- Full rank condition for overdetermined systems
                       ∃ rank_val : Nat, rank_val = (x_deg + 1) * (y_deg + 1) ∧
                       -- Matrix has full column rank for unique least squares solution
                       True) ∧
                     -- Basic symmetry when degrees are equal
                     (x_deg = y_deg → 
                       ∀ point_idx : Fin n, ∀ i j : Nat, i ≤ x_deg → j ≤ y_deg →
                       ∃ basis_idx1 basis_idx2 : Fin ((x_deg + 1) * (y_deg + 1)),

### 11. score 90 - specs/LT0513_specs.lean:38
- current: `sorry`
- reasons: polynomial_file_keywords:polynomial, local_flattened_index_name, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: bare_theorem_or_def_sorry

Window:

          -- General case: m > 0
          (m > 0 → 
            ∀ i : Fin (n - m), 
              -- The coefficient at position i comes from original position i+m
              -- It's multiplied by m consecutive factors: (i+m) * (i+m-1) * ... * (i+1)
              -- and scaled by scl^m
              let original_idx := i.val + m
              let factorial_factor := (List.range m).foldl 
                (fun acc k => acc * (original_idx - k).toFloat) 1.0
              let scale_factor := (List.range m).foldl 
                (fun acc _ => acc * scl) 1.0
              result.get i = c.get ⟨original_idx, sorry⟩ * factorial_factor * scale_factor
          )
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 12. score 80 - specs/LT0380_specs.lean:23
- current: `(n > 0 → result.get ⟨0, by sorry⟩ = scl * c.get ⟨1, by sorry⟩) ∧`
- reasons: polynomial_file_keywords:chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    -- </vc-helpers>
    
    -- <vc-definitions>
    def chebder {n : Nat} (c : Vector Float (n + 1)) (scl : Float := 1) :
        Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebder_spec {n : Nat} (c : Vector Float (n + 1)) (scl : Float := 1) :
        ⦃⌜True⌝⦄
        chebder c scl
        ⦃⇓result => ⌜result.size = n ∧
                  -- Base cases for the derivative
                  (n > 0 → result.get ⟨0, by sorry⟩ = scl * c.get ⟨1, by sorry⟩) ∧
                  (n > 1 → result.get ⟨1, by sorry⟩ = scl * 4 * c.get ⟨2, by sorry⟩) ∧
                  -- General recurrence for j ≥ 2
                  (∀ j : Fin n, j.val ≥ 2 →
                    result.get j = scl * (2 * Float.ofNat (j.val + 1)) * c.get ⟨j.val + 1, by sorry⟩) ∧
                  -- Mathematical property: result represents the derivative
                  -- For formal verification, we'd need to define what it means for
                  -- a vector to represent a Chebyshev series and its derivative
                  -- This is captured by the recurrence relations above
                  True⌝⦄ := by
      sorry
    -- </vc-theorems>

### 13. score 80 - specs/LT0380_specs.lean:24
- current: `(n > 1 → result.get ⟨1, by sorry⟩ = scl * 4 * c.get ⟨2, by sorry⟩) ∧`
- reasons: polynomial_file_keywords:chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    
    -- <vc-definitions>
    def chebder {n : Nat} (c : Vector Float (n + 1)) (scl : Float := 1) :
        Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebder_spec {n : Nat} (c : Vector Float (n + 1)) (scl : Float := 1) :
        ⦃⌜True⌝⦄
        chebder c scl
        ⦃⇓result => ⌜result.size = n ∧
                  -- Base cases for the derivative
                  (n > 0 → result.get ⟨0, by sorry⟩ = scl * c.get ⟨1, by sorry⟩) ∧
                  (n > 1 → result.get ⟨1, by sorry⟩ = scl * 4 * c.get ⟨2, by sorry⟩) ∧
                  -- General recurrence for j ≥ 2
                  (∀ j : Fin n, j.val ≥ 2 →
                    result.get j = scl * (2 * Float.ofNat (j.val + 1)) * c.get ⟨j.val + 1, by sorry⟩) ∧
                  -- Mathematical property: result represents the derivative
                  -- For formal verification, we'd need to define what it means for
                  -- a vector to represent a Chebyshev series and its derivative
                  -- This is captured by the recurrence relations above
                  True⌝⦄ := by
      sorry
    -- </vc-theorems>

### 14. score 80 - specs/LT0380_specs.lean:27
- current: `result.get j = scl * (2 * Float.ofNat (j.val + 1)) * c.get ⟨j.val + 1, by sorry⟩) ∧`
- reasons: polynomial_file_keywords:chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

        Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebder_spec {n : Nat} (c : Vector Float (n + 1)) (scl : Float := 1) :
        ⦃⌜True⌝⦄
        chebder c scl
        ⦃⇓result => ⌜result.size = n ∧
                  -- Base cases for the derivative
                  (n > 0 → result.get ⟨0, by sorry⟩ = scl * c.get ⟨1, by sorry⟩) ∧
                  (n > 1 → result.get ⟨1, by sorry⟩ = scl * 4 * c.get ⟨2, by sorry⟩) ∧
                  -- General recurrence for j ≥ 2
                  (∀ j : Fin n, j.val ≥ 2 →
                    result.get j = scl * (2 * Float.ofNat (j.val + 1)) * c.get ⟨j.val + 1, by sorry⟩) ∧
                  -- Mathematical property: result represents the derivative
                  -- For formal verification, we'd need to define what it means for
                  -- a vector to represent a Chebyshev series and its derivative
                  -- This is captured by the recurrence relations above
                  True⌝⦄ := by
      sorry
    -- </vc-theorems>

### 15. score 80 - specs/LT0390_specs.lean:24
- current: `(∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a →`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    -- <vc-definitions>
    def chebmul {m n : Nat} (c1 : Vector Float m) (c2 : Vector Float n) 
        (hm : m > 0) (hn : n > 0) : Id (Vector Float (m + n - 1)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebmul_spec {m n : Nat} (c1 : Vector Float m) (c2 : Vector Float n) 
        (hm : m > 0) (hn : n > 0) :
        ⦃⌜m > 0 ∧ n > 0⌝⦄
        chebmul c1 c2 hm hn
        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧

### 16. score 80 - specs/LT0390_specs.lean:25
- current: `∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    def chebmul {m n : Nat} (c1 : Vector Float m) (c2 : Vector Float n) 
        (hm : m > 0) (hn : n > 0) : Id (Vector Float (m + n - 1)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebmul_spec {m n : Nat} (c1 : Vector Float m) (c2 : Vector Float n) 
        (hm : m > 0) (hn : n > 0) :
        ⦃⌜m > 0 ∧ n > 0⌝⦄
        chebmul c1 c2 hm hn
        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]

### 17. score 80 - specs/LT0390_specs.lean:27
- current: `(m = 1 → c1.get ⟨0, sorry⟩ = 1 →`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebmul_spec {m n : Nat} (c1 : Vector Float m) (c2 : Vector Float n) 
        (hm : m > 0) (hn : n > 0) :
        ⦃⌜m > 0 ∧ n > 0⌝⦄
        chebmul c1 c2 hm hn
        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →

### 18. score 80 - specs/LT0390_specs.lean:28
- current: `∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebmul_spec {m n : Nat} (c1 : Vector Float m) (c2 : Vector Float n) 
        (hm : m > 0) (hn : n > 0) :
        ⦃⌜m > 0 ∧ n > 0⌝⦄
        chebmul c1 c2 hm hn
        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →

### 19. score 80 - specs/LT0390_specs.lean:32
- current: `let a := c1.get ⟨0, sorry⟩`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

        (hm : m > 0) (hn : n > 0) :
        ⦃⌜m > 0 ∧ n > 0⌝⦄
        chebmul c1 c2 hm hn
        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧

### 20. score 80 - specs/LT0390_specs.lean:33
- current: `let b := c1.get ⟨1, sorry⟩`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

        ⦃⌜m > 0 ∧ n > 0⌝⦄
        chebmul c1 c2 hm hn
        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by

### 21. score 80 - specs/LT0390_specs.lean:34
- current: `let c := c2.get ⟨0, sorry⟩`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

        chebmul c1 c2 hm hn
        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by
      sorry

### 22. score 80 - specs/LT0390_specs.lean:35
- current: `let d := c2.get ⟨1, sorry⟩`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

        ⦃⇓result => ⌜-- The result vector has the correct length
                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 23. score 80 - specs/LT0390_specs.lean:36
- current: `result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

                    result.toList.length = m + n - 1 ∧
                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 24. score 80 - specs/LT0390_specs.lean:37
- current: `result.get ⟨1, sorry⟩ = a * d + b * c ∧`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

                    -- Example property: multiplying by the constant polynomial [a] scales all coefficients
                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 25. score 80 - specs/LT0390_specs.lean:38
- current: `result.get ⟨2, sorry⟩ = b * d / 2) ∧`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

                    (∀ a : Float, n = 1 → c2.get ⟨0, sorry⟩ = a → 
                      ∀ i : Fin m, result.get ⟨i.val, sorry⟩ = a * c1.get i) ∧
                    -- Another example: multiplying [1,0,...] (T_0) by any polynomial preserves it
                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 26. score 80 - specs/LT0390_specs.lean:41
- current: `c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

                    (m = 1 → c1.get ⟨0, sorry⟩ = 1 → 
                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 27. score 80 - specs/LT0390_specs.lean:42
- current: `c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →`
- reasons: polynomial_file_keywords:polynomial, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

                      ∀ j : Fin n, result.get ⟨j.val, sorry⟩ = c2.get j) ∧
                    -- Special case: multiplying two linear polynomials [a,b] * [c,d]
                    -- Result should be [ac + bd/2, ad + bc, bd/2]
                    (m = 2 ∧ n = 2 → 
                      let a := c1.get ⟨0, sorry⟩
                      let b := c1.get ⟨1, sorry⟩
                      let c := c2.get ⟨0, sorry⟩
                      let d := c2.get ⟨1, sorry⟩
                      result.get ⟨0, sorry⟩ = a * c + b * d / 2 ∧
                      result.get ⟨1, sorry⟩ = a * d + b * c ∧
                      result.get ⟨2, sorry⟩ = b * d / 2) ∧
                    -- Verify the example from documentation: [1,2,3] * [3,2,1]
                    (m = 3 ∧ n = 3 → 
                      c1.get ⟨0, sorry⟩ = 1 ∧ c1.get ⟨1, sorry⟩ = 2 ∧ c1.get ⟨2, sorry⟩ = 3 →
                      c2.get ⟨0, sorry⟩ = 3 ∧ c2.get ⟨1, sorry⟩ = 2 ∧ c2.get ⟨2, sorry⟩ = 1 →
                      result.get ⟨0, sorry⟩ = 6.5 ∧
                      result.get ⟨1, sorry⟩ = 12 ∧
                      result.get ⟨2, sorry⟩ = 12 ∧
                      result.get ⟨3, sorry⟩ = 4 ∧
                      result.get ⟨4, sorry⟩ = 1.5)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 28. score 80 - specs/LT0397_specs.lean:59
- current: `(n = 1 → ∀ i : Fin m, result.get i = c.get ⟨0, sorry⟩) ∧`
- reasons: polynomial_file_keywords:polynomial,chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    /-- Specification: chebval evaluates the Chebyshev series correctly.
        The result at each point x[i] equals the sum of c[k] * T_k(x[i])
        for k from 0 to n-1, where T_k is the k-th Chebyshev polynomial.
        
        Special cases for numerical stability:
        - When n = 0, the result is the zero vector
        - When n = 1, the result is c[0] at each point (constant polynomial)
        - When n = 2, the result is c[0] + c[1] * x[i] (linear polynomial)
        
        The implementation uses Clenshaw recursion for efficient and stable evaluation. -/
    theorem chebval_spec {m n : Nat} (x : Vector Float m) (c : Vector Float n) :
        ⦃⌜True⌝⦄
        chebval x c
        ⦃⇓result => ⌜(n = 0 → ∀ i : Fin m, result.get i = 0) ∧
                    (n = 1 → ∀ i : Fin m, result.get i = c.get ⟨0, sorry⟩) ∧
                    (n = 2 → ∀ i : Fin m, result.get i = c.get ⟨0, sorry⟩ + c.get ⟨1, sorry⟩ * x.get i) ∧
                    (∀ i : Fin m, result.get i = chebyshevSeriesSum c (x.get i))⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    -- </vc-definitions>
    
    -- <vc-theorems>
    -- </vc-theorems>

### 29. score 80 - specs/LT0397_specs.lean:60
- current: `(n = 2 → ∀ i : Fin m, result.get i = c.get ⟨0, sorry⟩ + c.get ⟨1, sorry⟩ * x.get i) ∧`
- reasons: polynomial_file_keywords:polynomial,chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

        The result at each point x[i] equals the sum of c[k] * T_k(x[i])
        for k from 0 to n-1, where T_k is the k-th Chebyshev polynomial.
        
        Special cases for numerical stability:
        - When n = 0, the result is the zero vector
        - When n = 1, the result is c[0] at each point (constant polynomial)
        - When n = 2, the result is c[0] + c[1] * x[i] (linear polynomial)
        
        The implementation uses Clenshaw recursion for efficient and stable evaluation. -/
    theorem chebval_spec {m n : Nat} (x : Vector Float m) (c : Vector Float n) :
        ⦃⌜True⌝⦄
        chebval x c
        ⦃⇓result => ⌜(n = 0 → ∀ i : Fin m, result.get i = 0) ∧
                    (n = 1 → ∀ i : Fin m, result.get i = c.get ⟨0, sorry⟩) ∧
                    (n = 2 → ∀ i : Fin m, result.get i = c.get ⟨0, sorry⟩ + c.get ⟨1, sorry⟩ * x.get i) ∧
                    (∀ i : Fin m, result.get i = chebyshevSeriesSum c (x.get i))⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    -- </vc-definitions>
    
    -- <vc-theorems>
    -- </vc-theorems>

### 30. score 80 - specs/LT0400_specs.lean:20
- current: `(∀ i : Fin n, (V.get i).get ⟨0, sorry⟩ = 1) ∧`
- reasons: polynomial_file_keywords:vander,chebvander,polynomial,chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def chebvander {n : Nat} (x : Vector Float n) (deg : Nat) : Id (Vector (Vector Float (deg + 1)) n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebvander_spec {n : Nat} (x : Vector Float n) (deg : Nat) :
        ⦃⌜True⌝⦄
        chebvander x deg
        ⦃⇓V => ⌜-- T_0(x) = 1 for all x
                (∀ i : Fin n, (V.get i).get ⟨0, sorry⟩ = 1) ∧
                -- T_1(x) = x when deg ≥ 1
                (deg ≥ 1 → ∀ i : Fin n, (V.get i).get ⟨1, sorry⟩ = x.get i) ∧
                -- Recurrence relation: T_{k+1}(x) = 2x*T_k(x) - T_{k-1}(x) for k ≥ 1
                (∀ k : Nat, 1 ≤ k ∧ k < deg → 
                  ∀ i : Fin n, 
                    (V.get i).get ⟨k + 1, sorry⟩ = 
                      2 * (x.get i) * (V.get i).get ⟨k, sorry⟩ - 
                      (V.get i).get ⟨k - 1, sorry⟩) ∧
                -- Mathematical property: Chebyshev polynomials are bounded by 1 on [-1,1]
                (∀ i : Fin n, -1 ≤ x.get i ∧ x.get i ≤ 1 → 
                  ∀ j : Fin (deg + 1), -1 ≤ (V.get i).get j ∧ (V.get i).get j ≤ 1) ∧
                -- Symmetry property: T_n(-x) = (-1)^n * T_n(x)
                (∀ i j : Fin n, x.get i = -(x.get j) → 
                  ∀ k : Fin (deg + 1), 

### 31. score 80 - specs/LT0400_specs.lean:22
- current: `(deg ≥ 1 → ∀ i : Fin n, (V.get i).get ⟨1, sorry⟩ = x.get i) ∧`
- reasons: polynomial_file_keywords:vander,chebvander,polynomial,chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    -- </vc-helpers>
    
    -- <vc-definitions>
    def chebvander {n : Nat} (x : Vector Float n) (deg : Nat) : Id (Vector (Vector Float (deg + 1)) n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebvander_spec {n : Nat} (x : Vector Float n) (deg : Nat) :
        ⦃⌜True⌝⦄
        chebvander x deg
        ⦃⇓V => ⌜-- T_0(x) = 1 for all x
                (∀ i : Fin n, (V.get i).get ⟨0, sorry⟩ = 1) ∧
                -- T_1(x) = x when deg ≥ 1
                (deg ≥ 1 → ∀ i : Fin n, (V.get i).get ⟨1, sorry⟩ = x.get i) ∧
                -- Recurrence relation: T_{k+1}(x) = 2x*T_k(x) - T_{k-1}(x) for k ≥ 1
                (∀ k : Nat, 1 ≤ k ∧ k < deg → 
                  ∀ i : Fin n, 
                    (V.get i).get ⟨k + 1, sorry⟩ = 
                      2 * (x.get i) * (V.get i).get ⟨k, sorry⟩ - 
                      (V.get i).get ⟨k - 1, sorry⟩) ∧
                -- Mathematical property: Chebyshev polynomials are bounded by 1 on [-1,1]
                (∀ i : Fin n, -1 ≤ x.get i ∧ x.get i ≤ 1 → 
                  ∀ j : Fin (deg + 1), -1 ≤ (V.get i).get j ∧ (V.get i).get j ≤ 1) ∧
                -- Symmetry property: T_n(-x) = (-1)^n * T_n(x)
                (∀ i j : Fin n, x.get i = -(x.get j) → 
                  ∀ k : Fin (deg + 1), 
                    (V.get i).get k = (if k.val % 2 = 0 then 1 else -1) * (V.get j).get k)⌝⦄ := by
      sorry

### 32. score 80 - specs/LT0400_specs.lean:26
- current: `(V.get i).get ⟨k + 1, sorry⟩ =`
- reasons: polynomial_file_keywords:vander,chebvander,polynomial,chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebvander_spec {n : Nat} (x : Vector Float n) (deg : Nat) :
        ⦃⌜True⌝⦄
        chebvander x deg
        ⦃⇓V => ⌜-- T_0(x) = 1 for all x
                (∀ i : Fin n, (V.get i).get ⟨0, sorry⟩ = 1) ∧
                -- T_1(x) = x when deg ≥ 1
                (deg ≥ 1 → ∀ i : Fin n, (V.get i).get ⟨1, sorry⟩ = x.get i) ∧
                -- Recurrence relation: T_{k+1}(x) = 2x*T_k(x) - T_{k-1}(x) for k ≥ 1
                (∀ k : Nat, 1 ≤ k ∧ k < deg → 
                  ∀ i : Fin n, 
                    (V.get i).get ⟨k + 1, sorry⟩ = 
                      2 * (x.get i) * (V.get i).get ⟨k, sorry⟩ - 
                      (V.get i).get ⟨k - 1, sorry⟩) ∧
                -- Mathematical property: Chebyshev polynomials are bounded by 1 on [-1,1]
                (∀ i : Fin n, -1 ≤ x.get i ∧ x.get i ≤ 1 → 
                  ∀ j : Fin (deg + 1), -1 ≤ (V.get i).get j ∧ (V.get i).get j ≤ 1) ∧
                -- Symmetry property: T_n(-x) = (-1)^n * T_n(x)
                (∀ i j : Fin n, x.get i = -(x.get j) → 
                  ∀ k : Fin (deg + 1), 
                    (V.get i).get k = (if k.val % 2 = 0 then 1 else -1) * (V.get j).get k)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 33. score 80 - specs/LT0400_specs.lean:27
- current: `2 * (x.get i) * (V.get i).get ⟨k, sorry⟩ -`
- reasons: polynomial_file_keywords:vander,chebvander,polynomial,chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem chebvander_spec {n : Nat} (x : Vector Float n) (deg : Nat) :
        ⦃⌜True⌝⦄
        chebvander x deg
        ⦃⇓V => ⌜-- T_0(x) = 1 for all x
                (∀ i : Fin n, (V.get i).get ⟨0, sorry⟩ = 1) ∧
                -- T_1(x) = x when deg ≥ 1
                (deg ≥ 1 → ∀ i : Fin n, (V.get i).get ⟨1, sorry⟩ = x.get i) ∧
                -- Recurrence relation: T_{k+1}(x) = 2x*T_k(x) - T_{k-1}(x) for k ≥ 1
                (∀ k : Nat, 1 ≤ k ∧ k < deg → 
                  ∀ i : Fin n, 
                    (V.get i).get ⟨k + 1, sorry⟩ = 
                      2 * (x.get i) * (V.get i).get ⟨k, sorry⟩ - 
                      (V.get i).get ⟨k - 1, sorry⟩) ∧
                -- Mathematical property: Chebyshev polynomials are bounded by 1 on [-1,1]
                (∀ i : Fin n, -1 ≤ x.get i ∧ x.get i ≤ 1 → 
                  ∀ j : Fin (deg + 1), -1 ≤ (V.get i).get j ∧ (V.get i).get j ≤ 1) ∧
                -- Symmetry property: T_n(-x) = (-1)^n * T_n(x)
                (∀ i j : Fin n, x.get i = -(x.get j) → 
                  ∀ k : Fin (deg + 1), 
                    (V.get i).get k = (if k.val % 2 = 0 then 1 else -1) * (V.get j).get k)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 34. score 80 - specs/LT0400_specs.lean:28
- current: `(V.get i).get ⟨k - 1, sorry⟩) ∧`
- reasons: polynomial_file_keywords:vander,chebvander,polynomial,chebyshev, fin_get_sorry, fin_context, mul_plus_flatten_shape
- penalties: 

Window:

    
    -- <vc-theorems>
    theorem chebvander_spec {n : Nat} (x : Vector Float n) (deg : Nat) :
        ⦃⌜True⌝⦄
        chebvander x deg
        ⦃⇓V => ⌜-- T_0(x) = 1 for all x
                (∀ i : Fin n, (V.get i).get ⟨0, sorry⟩ = 1) ∧
                -- T_1(x) = x when deg ≥ 1
                (deg ≥ 1 → ∀ i : Fin n, (V.get i).get ⟨1, sorry⟩ = x.get i) ∧
                -- Recurrence relation: T_{k+1}(x) = 2x*T_k(x) - T_{k-1}(x) for k ≥ 1
                (∀ k : Nat, 1 ≤ k ∧ k < deg → 
                  ∀ i : Fin n, 
                    (V.get i).get ⟨k + 1, sorry⟩ = 
                      2 * (x.get i) * (V.get i).get ⟨k, sorry⟩ - 
                      (V.get i).get ⟨k - 1, sorry⟩) ∧
                -- Mathematical property: Chebyshev polynomials are bounded by 1 on [-1,1]
                (∀ i : Fin n, -1 ≤ x.get i ∧ x.get i ≤ 1 → 
                  ∀ j : Fin (deg + 1), -1 ≤ (V.get i).get j ∧ (V.get i).get j ≤ 1) ∧
                -- Symmetry property: T_n(-x) = (-1)^n * T_n(x)
                (∀ i j : Fin n, x.get i = -(x.get j) → 
                  ∀ k : Fin (deg + 1), 
                    (V.get i).get k = (if k.val % 2 = 0 then 1 else -1) * (V.get j).get k)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 35. score 80 - specs/LT0402_specs.lean:48
- current: `⟨(ydeg + 1) * (zdeg + 1) * i.val + (zdeg + 1) * j.val + k.val, sorry⟩`
- reasons: polynomial_file_keywords:vander,vander3d,chebvander,polynomial,chebyshev, fin_context, mul_plus_flatten_shape, 3d_shape, degree_successor_product
- penalties: 

Window:

    
    /-- Specification: chebvander3d constructs a 3D pseudo-Vandermonde matrix where
        each entry V[p, idx] equals the product of Chebyshev polynomials evaluated
        at the p-th sample point, with the column index encoding the polynomial degrees.
    
        The key mathematical properties are:
        1. Column ordering follows the pattern (i,j,k) lexicographically
        2. Each matrix entry equals T_i(x[p]) * T_j(y[p]) * T_k(z[p])
        3. The matrix enables efficient evaluation of 3D Chebyshev series -/
    theorem chebvander3d_spec {n : Nat} (x y z : Vector Float n) (xdeg ydeg zdeg : Nat) :
        ⦃⌜True⌝⦄
        chebvander3d x y z xdeg ydeg zdeg
        ⦃⇓V => ⌜∀ (p : Fin n) (i : Fin (xdeg + 1)) (j : Fin (ydeg + 1)) (k : Fin (zdeg + 1)),
                let col_idx : Fin ((xdeg + 1) * (ydeg + 1) * (zdeg + 1)) :=
                  ⟨(ydeg + 1) * (zdeg + 1) * i.val + (zdeg + 1) * j.val + k.val, sorry⟩
                (V.get p).get col_idx =
                  chebyshevT i.val (x.get p) * chebyshevT j.val (y.get p) * chebyshevT k.val (z.get p)⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    -- </vc-definitions>
    
    -- <vc-theorems>
    -- </vc-theorems>
