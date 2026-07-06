# MathGraph SorryDB v4.8.38 - vericoding Local Nat Bound Miner

## Purpose

After LA0521 classified as a postcondition-shape obstruction, mine vericoding specs for the proven-winning family:

    local Fin/Nat/index bounds

No proof patches were attempted.

## Counts

- all sorry rows scanned: 30844
- candidate bound holes: 25
- watch bound holes: 510

## Top candidate bound holes

### 1. score 125 - specs/LT0479_specs.lean:45
- current: `have h_idx : idx < (xdeg + 1) * (ydeg + 1) := by sorry`
- reasons: direct_have_bound, index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

        1. The result has shape (n, (xdeg + 1) * (ydeg + 1))
        2. Each element V[k, (ydeg + 1)*i + j] = L_i(x[k]) * L_j(y[k])
        3. The ordering follows the pattern: (0,0), (0,1), ..., (0,ydeg), (1,0), (1,1), ..., (xdeg,ydeg)
        4. For the first column (i=0, j=0), all values are 1 since L_0(x) * L_0(y) = 1
    -/
    theorem lagvander2d_spec {n : Nat} (x y : Vector Float n) (xdeg ydeg : Nat) :
        ⦃⌜True⌝⦄
        lagvander2d x y xdeg ydeg
        ⦃⇓result => ⌜(∀ k : Fin n, ∀ i : Fin (xdeg + 1), ∀ j : Fin (ydeg + 1),
                        let idx := i.val * (ydeg + 1) + j.val
                        have h_idx : idx < (xdeg + 1) * (ydeg + 1) := by sorry
                        (result.get k).get ⟨idx, h_idx⟩ = 
                          laguerrePolynomial i.val (x.get k) * laguerrePolynomial j.val (y.get k))⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    -- </vc-definitions>

### 2. score 125 - specs/LT0480_specs.lean:46
- current: `have h_idx : idx < (xdeg + 1) * (ydeg + 1) * (zdeg + 1) := by sorry`
- reasons: direct_have_bound, index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

        1. The result has shape (n, (xdeg + 1) * (ydeg + 1) * (zdeg + 1))
        2. Each element V[p, (ydeg+1)*(zdeg+1)*i + (zdeg+1)*j + k] = L_i(x[p]) * L_j(y[p]) * L_k(z[p])
        3. The ordering follows: (0,0,0), (0,0,1), ..., (0,0,zdeg), (0,1,0), ..., (xdeg,ydeg,zdeg)
        4. For the first column (i=0, j=0, k=0), all values are 1 since L_0(x) * L_0(y) * L_0(z) = 1
    -/
    theorem lagvander3d_spec {n : Nat} (x y z : Vector Float n) (xdeg ydeg zdeg : Nat) :
        ⦃⌜True⌝⦄
        lagvander3d x y z xdeg ydeg zdeg
        ⦃⇓result => ⌜(∀ p : Fin n, ∀ i : Fin (xdeg + 1), ∀ j : Fin (ydeg + 1), ∀ k : Fin (zdeg + 1),
                        let idx := i.val * (ydeg + 1) * (zdeg + 1) + j.val * (zdeg + 1) + k.val
                        have h_idx : idx < (xdeg + 1) * (ydeg + 1) * (zdeg + 1) := by sorry
                        (result.get p).get ⟨idx, h_idx⟩ = 
                          laguerrePolynomial i.val (x.get p) * 
                          laguerrePolynomial j.val (y.get p) * 
                          laguerrePolynomial k.val (z.get p))⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>

### 3. score 100 - specs/LT0032_specs.lean:26
- current: `have hi : i < rows := by sorry`
- reasons: direct_have_bound, fin_context, vector_get_context, min_bound_context
- penalties: forall_context

Window:

    -- <vc-theorems>
    theorem tril_spec {rows cols : Nat} (m : Vector (Vector Float cols) rows) (k : Int := 0) :
        ⦃⌜True⌝⦄
        tril m k
        ⦃⇓result => ⌜-- Element-wise specification (core property)
                      (∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 
                          if (i : Int) ≥ (j : Int) - k then (m.get i).get j else 0) ∧
                      -- Sanity check: diagonal elements are preserved when k = 0
                      (k = 0 → ∀ i : Fin (min rows cols), 
                        have hi : i < rows := by sorry
                        have hj : i < cols := by sorry
                        (result.get ⟨i, hi⟩).get ⟨i, hj⟩ = (m.get ⟨i, hi⟩).get ⟨i, hj⟩) ∧
                      -- Sanity check: all elements preserved when k is very large
                      (k ≥ (cols : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = (m.get i).get j) ∧
                      -- Sanity check: all elements zeroed when k is very negative
                      (k ≤ -(rows : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 0) ∧
                      -- Idempotency property: tril(tril(m, k), k) = tril(m, k)
                      (∀ (i : Fin rows) (j : Fin cols),

### 4. score 100 - specs/LT0032_specs.lean:27
- current: `have hj : i < cols := by sorry`
- reasons: direct_have_bound, fin_context, vector_get_context, min_bound_context
- penalties: forall_context

Window:

    theorem tril_spec {rows cols : Nat} (m : Vector (Vector Float cols) rows) (k : Int := 0) :
        ⦃⌜True⌝⦄
        tril m k
        ⦃⇓result => ⌜-- Element-wise specification (core property)
                      (∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 
                          if (i : Int) ≥ (j : Int) - k then (m.get i).get j else 0) ∧
                      -- Sanity check: diagonal elements are preserved when k = 0
                      (k = 0 → ∀ i : Fin (min rows cols), 
                        have hi : i < rows := by sorry
                        have hj : i < cols := by sorry
                        (result.get ⟨i, hi⟩).get ⟨i, hj⟩ = (m.get ⟨i, hi⟩).get ⟨i, hj⟩) ∧
                      -- Sanity check: all elements preserved when k is very large
                      (k ≥ (cols : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = (m.get i).get j) ∧
                      -- Sanity check: all elements zeroed when k is very negative
                      (k ≤ -(rows : Int) → ∀ (i : Fin rows) (j : Fin cols), 
                        (result.get i).get j = 0) ∧
                      -- Idempotency property: tril(tril(m, k), k) = tril(m, k)
                      (∀ (i : Fin rows) (j : Fin cols),
                        let twice_applied := tril result k

### 5. score 70 - specs/LT0653_specs.lean:81
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: 

Window:

      sorry
    
    -- Additional properties for comprehensive specification
    theorem at_length_preservation {n m : Nat} (_a : Vector Int n) (_indices : Vector (Fin n) m) (_b : Vector Int m) :
        True := by
      trivial
    
    theorem at_accumulation {n : Nat} (a : Vector Int n) (idx : Fin n) (val : Int) :
        «at» a (Vector.replicate 2 idx) (Vector.replicate 2 val) = 
        a.set idx (a.get idx + 2 * val) := by
      sorry
    
    theorem at_single_index {n : Nat} (a : Vector Int n) (idx : Fin n) (val : Int) :
        «at» a (Vector.singleton idx) (Vector.singleton val) = 
        a.set idx (a.get idx + val) := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>

### 6. score 70 - specs/LT0653_specs.lean:86
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: 

Window:

      trivial
    
    theorem at_accumulation {n : Nat} (a : Vector Int n) (idx : Fin n) (val : Int) :
        «at» a (Vector.replicate 2 idx) (Vector.replicate 2 val) = 
        a.set idx (a.get idx + 2 * val) := by
      sorry
    
    theorem at_single_index {n : Nat} (a : Vector Int n) (idx : Fin n) (val : Int) :
        «at» a (Vector.singleton idx) (Vector.singleton val) = 
        a.set idx (a.get idx + val) := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    -- </vc-definitions>
    
    -- <vc-theorems>
    -- </vc-theorems>

### 7. score 65 - specs/LT0056_specs.lean:24
- current: `arr.get ⟨part_idx.val * (n / k) + elem_idx.val, by sorry⟩) ∧`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem hsplit_spec {n k : Nat} (arr : Vector Float n) 
        (h_divides : k > 0 ∧ n % k = 0) :
        ⦃⌜k > 0 ∧ n % k = 0⌝⦄
        hsplit arr h_divides
        ⦃⇓result => ⌜(∀ (part_idx : Fin k) (elem_idx : Fin (n / k)),
                      (result.get part_idx).get elem_idx = 
                      arr.get ⟨part_idx.val * (n / k) + elem_idx.val, by sorry⟩) ∧
                     (∀ i : Fin n, ∃ (p : Fin k) (e : Fin (n / k)), 
                      i.val = p.val * (n / k) + e.val ∧
                      arr.get i = (result.get p).get e)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 8. score 65 - specs/LT0183_specs.lean:12
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

    import Std.Do.Triple
    import Std.Tactic.Do
    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def ndindex {m n : Nat} (shape : Nat × Nat) : Id (Vector (Fin m × Fin n) (m * n)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem ndindex_spec {m n : Nat} (shape : Nat × Nat) (h_shape : shape = (m, n)) :
        ⦃⌜shape = (m, n)⌝⦄
        ndindex shape
        ⦃⇓indices => ⌜indices.size = m * n ∧
                       (∀ k : Fin (m * n), 
                          let (i, j) := indices.get k
                          i.val < m ∧ j.val < n) ∧

### 9. score 65 - specs/LT0191_specs.lean:15
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def ravel_multi_index {n : Nat} (row_indices col_indices : Vector Nat n) 
        (rows cols : Nat) 
        (h_rows_valid : ∀ i : Fin n, row_indices.get i < rows)
        (h_cols_valid : ∀ i : Fin n, col_indices.get i < cols) : Id (Vector Nat n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem ravel_multi_index_spec {n : Nat} (row_indices col_indices : Vector Nat n) 
        (rows cols : Nat) 
        (h_rows_valid : ∀ i : Fin n, row_indices.get i < rows)
        (h_cols_valid : ∀ i : Fin n, col_indices.get i < cols) :
        ⦃⌜∀ i : Fin n, row_indices.get i < rows ∧ col_indices.get i < cols⌝⦄
        ravel_multi_index row_indices col_indices rows cols h_rows_valid h_cols_valid
        ⦃⇓result => ⌜∀ i : Fin n, result.get i = row_indices.get i * cols + col_indices.get i ∧

### 10. score 65 - specs/LT0191_specs.lean:27
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

    
    -- <vc-theorems>
    theorem ravel_multi_index_spec {n : Nat} (row_indices col_indices : Vector Nat n) 
        (rows cols : Nat) 
        (h_rows_valid : ∀ i : Fin n, row_indices.get i < rows)
        (h_cols_valid : ∀ i : Fin n, col_indices.get i < cols) :
        ⦃⌜∀ i : Fin n, row_indices.get i < rows ∧ col_indices.get i < cols⌝⦄
        ravel_multi_index row_indices col_indices rows cols h_rows_valid h_cols_valid
        ⦃⇓result => ⌜∀ i : Fin n, result.get i = row_indices.get i * cols + col_indices.get i ∧
                                  result.get i < rows * cols⌝⦄ := by
      sorry
    -- </vc-theorems>

### 11. score 65 - specs/LT0198_specs.lean:12
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

    import Std.Do.Triple
    import Std.Tactic.Do
    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def unravel_index {n d : Nat} (indices : Vector Nat n) (shape : Vector Nat d) : Id (Vector (Vector Nat d) n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem unravel_index_spec {n d : Nat} (indices : Vector Nat n) (shape : Vector Nat d) 
        (h_shape_pos : ∀ i : Fin d, shape.get i > 0)
        (h_indices_valid : ∀ i : Fin n, indices.get i < (shape.toList.foldl (· * ·) 1)) :
        ⦃⌜(∀ i : Fin d, shape.get i > 0) ∧ (∀ i : Fin n, indices.get i < (shape.toList.foldl (· * ·) 1))⌝⦄
        unravel_index indices shape
        ⦃⇓coords => ⌜
          -- Each result has the same size as the number of dimensions

### 12. score 65 - specs/LT0341_specs.lean:24
- current: `result.get i = (List.range (i.val + 1)).foldl (fun acc idx => acc * arr.get ⟨idx, by sorry⟩) 1.0 ∧`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

    
    -- <vc-theorems>
    theorem nancumprod_spec {n : Nat} (arr : Vector Float n) :
        ⦃⌜True⌝⦄
        nancumprod arr
        ⦃⇓result => ⌜∀ i : Fin n, 
          -- If all elements from start to i are NaN, result[i] = 1
          (∀ j : Fin n, j.val ≤ i.val → Float.isNaN (arr.get j)) → result.get i = 1.0 ∧
          -- If no elements from start to i are NaN, result[i] = product of all elements from start to i
          (∀ j : Fin n, j.val ≤ i.val → ¬Float.isNaN (arr.get j)) → 
            result.get i = (List.range (i.val + 1)).foldl (fun acc idx => acc * arr.get ⟨idx, by sorry⟩) 1.0 ∧
          -- General case: result[i] = product of all non-NaN elements from start to i
          result.get i = (List.range (i.val + 1)).foldl (fun acc idx => 
            let val := arr.get ⟨idx, by sorry⟩
            if Float.isNaN val then acc else acc * val) 1.0⌝⦄ := by
      sorry
    -- </vc-theorems>

### 13. score 65 - specs/LT0341_specs.lean:27
- current: `let val := arr.get ⟨idx, by sorry⟩`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

        ⦃⌜True⌝⦄
        nancumprod arr
        ⦃⇓result => ⌜∀ i : Fin n, 
          -- If all elements from start to i are NaN, result[i] = 1
          (∀ j : Fin n, j.val ≤ i.val → Float.isNaN (arr.get j)) → result.get i = 1.0 ∧
          -- If no elements from start to i are NaN, result[i] = product of all elements from start to i
          (∀ j : Fin n, j.val ≤ i.val → ¬Float.isNaN (arr.get j)) → 
            result.get i = (List.range (i.val + 1)).foldl (fun acc idx => acc * arr.get ⟨idx, by sorry⟩) 1.0 ∧
          -- General case: result[i] = product of all non-NaN elements from start to i
          result.get i = (List.range (i.val + 1)).foldl (fun acc idx => 
            let val := arr.get ⟨idx, by sorry⟩
            if Float.isNaN val then acc else acc * val) 1.0⌝⦄ := by
      sorry
    -- </vc-theorems>

### 14. score 65 - specs/LT0401_specs.lean:49
- current: `(result.get k).get ⟨idx, by sorry⟩ =`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

        - Each row has (xdeg + 1) * (ydeg + 1) elements
        - For each point k and degrees (i, j), the element at position 
          (ydeg + 1) * i + j equals T_i(x[k]) * T_j(y[k])
        - The elements are ordered column-major: varying j (y-degree) fastest
    -/
    theorem chebvander2d_spec {n : Nat} (x y : Vector Float n) (xdeg ydeg : Nat) :
        ⦃⌜True⌝⦄
        chebvander2d x y xdeg ydeg
        ⦃⇓result => ⌜∀ (k : Fin n) (i : Fin (xdeg + 1)) (j : Fin (ydeg + 1)),
                      let idx := i.val * (ydeg + 1) + j.val
                      (result.get k).get ⟨idx, by sorry⟩ = 
                      (chebyshevT i.val (x.get k)) * (chebyshevT j.val (y.get k))⌝⦄ := by
      sorry
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    -- </vc-definitions>

### 15. score 65 - specs/LT0428_specs.lean:50
- current: `acc + (result.get point_idx).get ⟨k, sorry⟩ * flattened_coeff.get ⟨k, sorry⟩`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

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

### 16. score 65 - specs/LT0429_specs.lean:45
- current: `(result.get p).get ⟨col_idx, by sorry⟩ =`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

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

### 17. score 65 - specs/LT0429_specs.lean:57
- current: `(result.get p).get ⟨col_idx₁, by sorry⟩ ≠ (result.get p).get ⟨col_idx₂, by sorry⟩ ∨`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

    
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

### 18. score 65 - specs/LT0429_specs.lean:76
- current: `(result.get p).get ⟨col_idx, by sorry⟩ =`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

    
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

### 19. score 65 - specs/LT0451_specs.lean:43
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

        The result at each index is the sum of all terms c[i,j,k] * H_i(x) * H_j(y) * H_k(z)
        where H_i, H_j, H_k are Hermite polynomials. -/
    theorem hermval3d_spec {n : Nat} 
      (x y z : Vector Float n)
      {ni nj nk : Nat}
      (c : Vector (Vector (Vector Float nk) nj) ni) :
        ⦃⌜True⌝⦄
        hermval3d x y z c
        ⦃⇓result => ⌜∀ idx : Fin n, 
          result.get idx = hermiteTripleSum c (x.get idx) (y.get idx) (z.get idx)⌝⦄ := by
      sorry
    
    /-- Alternative detailed specification showing the mathematical property directly -/
    theorem hermval3d_spec_detailed {n : Nat} 
      (x y z : Vector Float n)
      {ni nj nk : Nat}
      (c : Vector (Vector (Vector Float nk) nj) ni)
      (h_ni : ni > 0) (h_nj : nj > 0) (h_nk : nk > 0) :
        ⦃⌜ni > 0 ∧ nj > 0 ∧ nk > 0⌝⦄
        hermval3d x y z c
        ⦃⇓result => ⌜∀ idx : Fin n,

### 20. score 65 - specs/LT0505_specs.lean:29
- current: `(result.get i).get ⟨col_idx, sorry⟩ = L_p_x * L_q_y)`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

        ⦃⇓result => ⌜
          -- Matrix has correct dimensions
          (∀ i : Fin n, ∀ j : Fin ((deg_x + 1) * (deg_y + 1)), ∃ val : Float, (result.get i).get j = val) ∧
          -- First column corresponds to L_0(x) * L_0(y) = 1 * 1 = 1
          (∀ i : Fin n, (result.get i).get ⟨0, sorry⟩ = 1) ∧
          -- Entries are products of Legendre polynomial evaluations
          (∀ i : Fin n, ∀ p : Fin (deg_x + 1), ∀ q : Fin (deg_y + 1), 
            let col_idx := (deg_y + 1) * p.val + q.val
            col_idx < (deg_x + 1) * (deg_y + 1) →
            ∃ L_p_x L_q_y : Float, 
              (result.get i).get ⟨col_idx, sorry⟩ = L_p_x * L_q_y)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 21. score 65 - specs/LT0506_specs.lean:31
- current: `(result.get i).get ⟨col_idx, sorry⟩ = L_p_x * L_q_y * L_r_z)`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

          -- Matrix has correct dimensions
          (∀ i : Fin n, ∀ j : Fin ((deg_x + 1) * (deg_y + 1) * (deg_z + 1)), 
            ∃ val : Float, (result.get i).get j = val) ∧
          -- First column corresponds to L_0(x) * L_0(y) * L_0(z) = 1 * 1 * 1 = 1
          (∀ i : Fin n, (result.get i).get ⟨0, sorry⟩ = 1) ∧
          -- Entries are products of Legendre polynomial evaluations
          (∀ i : Fin n, ∀ p : Fin (deg_x + 1), ∀ q : Fin (deg_y + 1), ∀ r : Fin (deg_z + 1), 
            let col_idx := (deg_y + 1) * (deg_z + 1) * p.val + (deg_z + 1) * q.val + r.val
            col_idx < (deg_x + 1) * (deg_y + 1) * (deg_z + 1) →
            ∃ L_p_x L_q_y L_r_z : Float, 
              (result.get i).get ⟨col_idx, sorry⟩ = L_p_x * L_q_y * L_r_z)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 22. score 65 - specs/LT0513_specs.lean:35
- current: `result.get i = c.get ⟨original_idx, sorry⟩ * factorial_factor * scale_factor`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

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

### 23. score 65 - specs/LT0653_specs.lean:71
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context, mul_or_flattened_index_shape
- penalties: forall_context

Window:

        5. Preserves array length: result has same length as input array
    
        Precondition: All indices must be valid (within bounds of array a)
        Postcondition: For each index i in indices, the value at a[indices[i]] is
        modified by the operation with b[i], with accumulation for repeated indices
    -/
    theorem at_spec {n m : Nat} (a : Vector Int n) (indices : Vector (Fin n) m) (b : Vector Int m) :
        ⦃⌜True⌝⦄
        «at» a indices b
        ⦃⇓result => ⌜∀ i : Fin n, ∃ acc : Int, result.get i = a.get i + acc ∧ acc ≥ 0⌝⦄ := by
      sorry
    
    -- Additional properties for comprehensive specification
    theorem at_length_preservation {n m : Nat} (_a : Vector Int n) (_indices : Vector (Fin n) m) (_b : Vector Int m) :
        True := by
      trivial
    
    theorem at_accumulation {n : Nat} (a : Vector Int n) (idx : Fin n) (val : Int) :
        «at» a (Vector.replicate 2 idx) (Vector.replicate 2 val) = 
        a.set idx (a.get idx + 2 * val) := by
      sorry

### 24. score 60 - specs/LT0588_specs.lean:37
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: 

Window:

                (if h : (n + 1) % 2 = 1 then
                  -- odd case: middle element at index n/2
                  m = sorted.get ⟨n / 2, by
                    have : n / 2 < n + 1 :=
      sorry
                    exact this⟩
                else
                  -- even case: average of two middle elements  
                  m = (sorted.get ⟨n / 2, by
                    have : n / 2 < n + 1 :=
      sorry
                    exact this⟩ + 
                       sorted.get ⟨(n + 1) / 2, by
                    have : (n + 1) / 2 < n + 1 :=
      sorry
                    exact this⟩) / 2) ∧
                -- median property: it's a value that appears in the original vector
                -- or can be computed from values in the vector
                (∃ i : Fin (n + 1), m = sorted.get i ∨ 
                 ∃ i j : Fin (n + 1), m = (sorted.get i + sorted.get j) / 2)⌝⦄ := by
      sorry

### 25. score 60 - specs/LT0653_specs.lean:51
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: 

Window:

    
        Mathematical Properties:
        1. In-place modification: modifies the original array a
        2. Accumulation with repeated indices: when an index appears multiple times,
           the operation is applied multiple times
        3. Unbuffered operation: does not suffer from buffering issues of regular indexing
        4. Preserves array shape: only modifies values, not structure
        5. Index bounds checking: indices must be valid for the array
    -/
    def «at» {n m : Nat} (a : Vector Int n) (indices : Vector (Fin n) m) (b : Vector Int m) : Id (Vector Int n) :=
      sorry
    
    /-- Specification: ufunc.at performs in-place operation at specified indices
        with proper handling of repeated indices.
    
        Mathematical Properties:
        1. In-place semantics: modifies the original array values
        2. Accumulation property: for repeated indices, operations accumulate
        3. Index correspondence: indices[i] determines where b[i] is applied
        4. Bounds safety: all indices must be valid for the array
        5. Preserves array length: result has same length as input array

## Watch bound holes

### W1. score 55 - specs/LS0024_specs.lean:9
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W2. score 55 - specs/LS0024_specs.lean:12
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W3. score 55 - specs/LT0038_specs.lean:36
- current: `v.get ⟨start_indices.get i + j.val, by sorry⟩))`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W4. score 55 - specs/LT0049_specs.lean:13
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W5. score 55 - specs/LT0049_specs.lean:22
- current: `result.get i = arr.get ⟨i.val, by sorry⟩`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W6. score 55 - specs/LT0049_specs.lean:24
- current: `result.get i = arr.get ⟨i.val + 1, by sorry⟩) ∧`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W7. score 55 - specs/LT0049_specs.lean:27
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W8. score 55 - specs/LT0051_specs.lean:31
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W9. score 55 - specs/LT0058_specs.lean:12
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W10. score 55 - specs/LT0058_specs.lean:31
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W11. score 55 - specs/LT0185_specs.lean:23
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W12. score 55 - specs/LT0185_specs.lean:31
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W13. score 55 - specs/LT0581_specs.lean:58
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W14. score 55 - specs/LT0588_specs.lean:31
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W15. score 55 - specs/LT0614_specs.lean:12
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W16. score 55 - specs/LT0636_specs.lean:12
- current: `sorry`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W17. score 55 - specs/LT0656_specs.lean:29
- current: `let end_idx := indices.get ⟨i.val + 1, sorry⟩`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W18. score 55 - specs/LT0656_specs.lean:35
- current: `(fun offset => arr.get ⟨start_idx.val + offset, sorry⟩) ∧`
- reasons: index_bound, fin_context, vector_get_context
- penalties: forall_context

### W19. score 50 - specs/LF1634_specs.lean:28
- current: `sorry`
- reasons: index_bound, vector_get_context, min_bound_context
- penalties: 

### W20. score 50 - specs/LF1634_specs.lean:35
- current: `lst.get ⟨result.toNat, sorry⟩ = min ∧`
- reasons: index_bound, vector_get_context, min_bound_context
- penalties: 

### W21. score 50 - specs/LF1634_specs.lean:37
- current: `sorry`
- reasons: index_bound, vector_get_context, min_bound_context
- penalties: 

### W22. score 50 - specs/LF1634_specs.lean:43
- current: `sorry`
- reasons: index_bound, vector_get_context, min_bound_context
- penalties: 

### W23. score 50 - specs/LF1634_specs.lean:47
- current: `sorry`
- reasons: index_bound, vector_get_context, min_bound_context
- penalties: 

### W24. score 50 - specs/LT0183_specs.lean:28
- current: `sorry`
- reasons: index_bound, fin_context, mul_or_flattened_index_shape
- penalties: forall_context

### W25. score 50 - specs/LT0198_specs.lean:28
- current: `sorry`
- reasons: index_bound, fin_context, mul_or_flattened_index_shape
- penalties: forall_context

### W26. score 50 - specs/LT0243_specs.lean:45
- current: `sorry`
- reasons: fin_context, vector_get_context, min_bound_context, mul_or_flattened_index_shape
- penalties: forall_context

### W27. score 50 - specs/LT0384_specs.lean:12
- current: `sorry`
- reasons: index_bound, vector_get_context, mul_or_flattened_index_shape
- penalties: 

### W28. score 50 - specs/LT0401_specs.lean:30
- current: `sorry`
- reasons: index_bound, vector_get_context, mul_or_flattened_index_shape
- penalties: 

### W29. score 50 - specs/LT0402_specs.lean:21
- current: `sorry`
- reasons: index_bound, vector_get_context, mul_or_flattened_index_shape
- penalties: 

### W30. score 50 - specs/LT0402_specs.lean:33
- current: `sorry`
- reasons: index_bound, vector_get_context, mul_or_flattened_index_shape
- penalties: 
