# MathGraph SorryDB v4.8.57 - vericoding Unguarded Fin-bound Residual Miner

## Purpose

Find next proof-repair targets where the bound is likely available from unconditional Fin structure, not hidden behind implication arrows.

## Excluded PR #12 files

- `specs/LT0032_specs.lean`
- `specs/LT0380_specs.lean`
- `specs/LT0400_specs.lean`
- `specs/LT0401_specs.lean`
- `specs/LT0402_specs.lean`
- `specs/LT0428_specs.lean`
- `specs/LT0479_specs.lean`
- `specs/LT0480_specs.lean`
- `specs/LT0505_specs.lean`
- `specs/LT0506_specs.lean`
- `specs/LT0513_specs.lean`

## Counts

- raw candidates: 131
- baseline-ready candidates among top files: 42

## Top baseline-ready candidates

### 1. score 100 - specs/LT0049_specs.lean:24
- baseline rc: 0
- current: `result.get i = arr.get ⟨i.val + 1, by sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: 

Window:

    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def delete {n : Nat} (arr : Vector Float (n + 1)) (index : Fin (n + 1)) : 
        Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem delete_spec {n : Nat} (arr : Vector Float (n + 1)) (index : Fin (n + 1)) :
        ⦃⌜True⌝⦄
        delete arr index
        ⦃⇓result => ⌜(∀ i : Fin n, 
                       if h : i.val < index.val then 
                         result.get i = arr.get ⟨i.val, by sorry⟩
                       else 
                         result.get i = arr.get ⟨i.val + 1, by sorry⟩) ∧
                     (∀ i : Fin (n + 1), i ≠ index → 
                       ∃ j : Fin n, result.get j = arr.get i)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 2. score 100 - specs/LT0420_specs.lean:23
- baseline rc: 0
- current: `(∀ (h : n > 0), result.get ⟨1, sorry⟩ = c.get ⟨0, h⟩ +`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: 

Window:

    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def hermemulx {n : Nat} (c : Vector Float n) : Id (Vector Float (n + 1)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem hermemulx_spec {n : Nat} (c : Vector Float n) :
        ⦃⌜True⌝⦄
        hermemulx c
        ⦃⇓result => ⌜
          -- Coefficient at position 0 is always 0 (no constant term in x*polynomial)
          result.get ⟨0, by simp⟩ = 0 ∧
          -- For n > 0: coefficient at position 1 comes from c[0] plus recursive contributions  
          (∀ (h : n > 0), result.get ⟨1, sorry⟩ = c.get ⟨0, h⟩ + 
            (if n > 1 then (c.get ⟨1, sorry⟩) * (1 : Float) else 0)) ∧
          -- For i ≥ 1: result[i+1] gets c[i] (coefficient shift up)
          (∀ i : Fin n, i.val ≥ 1 → result.get ⟨i.val + 1, sorry⟩ = c.get i)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 3. score 100 - specs/LT0420_specs.lean:24
- baseline rc: 0
- current: `(if n > 1 then (c.get ⟨1, sorry⟩) * (1 : Float) else 0)) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: 

Window:

    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def hermemulx {n : Nat} (c : Vector Float n) : Id (Vector Float (n + 1)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem hermemulx_spec {n : Nat} (c : Vector Float n) :
        ⦃⌜True⌝⦄
        hermemulx c
        ⦃⇓result => ⌜
          -- Coefficient at position 0 is always 0 (no constant term in x*polynomial)
          result.get ⟨0, by simp⟩ = 0 ∧
          -- For n > 0: coefficient at position 1 comes from c[0] plus recursive contributions  
          (∀ (h : n > 0), result.get ⟨1, sorry⟩ = c.get ⟨0, h⟩ + 
            (if n > 1 then (c.get ⟨1, sorry⟩) * (1 : Float) else 0)) ∧
          -- For i ≥ 1: result[i+1] gets c[i] (coefficient shift up)
          (∀ i : Fin n, i.val ≥ 1 → result.get ⟨i.val + 1, sorry⟩ = c.get i)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 4. score 100 - specs/LT0445_specs.lean:29
- baseline rc: 0
- current: `(if h1 : k.val > 0 ∧ k.val - 1 < n then c.get ⟨k.val - 1, sorry⟩ / 2 else 0) +`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: 

Window:

    def hermmulx {n : Nat} (c : Vector Float n) : Id (Vector Float (n + 1)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem hermmulx_spec {n : Nat} (c : Vector Float n) :
        ⦃⌜True⌝⦄
        hermmulx c
        ⦃⇓result =>
          -- The output has exactly n+1 coefficients
          ⌜result.size = n + 1⌝ ∧
          -- Mathematical property: each position in result is the sum of contributions
          -- from the recursion formula $xP_i(x) = (P_{i+1}(x)/2 + i*P_{i-1}(x))$
          ⌜∀ k : Fin (n + 1),
            result.get k =
              -- Base case: position 0 starts at 0
              (if k.val = 0 then 0 else 0) +
              -- Contribution from c[k-1]/2 when k > 0 and k-1 < n
              (if h1 : k.val > 0 ∧ k.val - 1 < n then c.get ⟨k.val - 1, sorry⟩ / 2 else 0) +
              -- Contribution from c[k+1]*(k+1) when k+1 < n
              (if h2 : k.val + 1 < n then c.get ⟨k.val + 1, sorry⟩ * Float.ofNat (k.val + 1) else 0)⌝
        ⦄ := by
      sorry
    -- </vc-theorems>

### 5. score 100 - specs/LT0445_specs.lean:31
- baseline rc: 0
- current: `(if h2 : k.val + 1 < n then c.get ⟨k.val + 1, sorry⟩ * Float.ofNat (k.val + 1) else 0)⌝`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: 

Window:

    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem hermmulx_spec {n : Nat} (c : Vector Float n) :
        ⦃⌜True⌝⦄
        hermmulx c
        ⦃⇓result =>
          -- The output has exactly n+1 coefficients
          ⌜result.size = n + 1⌝ ∧
          -- Mathematical property: each position in result is the sum of contributions
          -- from the recursion formula $xP_i(x) = (P_{i+1}(x)/2 + i*P_{i-1}(x))$
          ⌜∀ k : Fin (n + 1),
            result.get k =
              -- Base case: position 0 starts at 0
              (if k.val = 0 then 0 else 0) +
              -- Contribution from c[k-1]/2 when k > 0 and k-1 < n
              (if h1 : k.val > 0 ∧ k.val - 1 < n then c.get ⟨k.val - 1, sorry⟩ / 2 else 0) +
              -- Contribution from c[k+1]*(k+1) when k+1 < n
              (if h2 : k.val + 1 < n then c.get ⟨k.val + 1, sorry⟩ * Float.ofNat (k.val + 1) else 0)⌝
        ⦄ := by
      sorry
    -- </vc-theorems>

### 6. score 90 - specs/LF0093_specs.lean:19
- baseline rc: 0
- current: `(result.get ⟨i.val, sorry⟩) ≠ (result.get ⟨i.val + 1, sorry⟩) :=`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def solve_color_array (n : Nat) (t : Nat) (arr : List Nat) : List Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem solve_color_array_equal_values_alternate
      {n : Nat} {arr : List Nat} (h : arr.length > 0) :
      let firstVal := arr.get ⟨0, sorry⟩
      let t := 2 * firstVal
      let result := solve_color_array n t (List.replicate arr.length firstVal)
      ∀ i : Fin (result.length - 1),
        (result.get ⟨i.val, sorry⟩) ≠ (result.get ⟨i.val + 1, sorry⟩) :=
      sorry
    
    theorem solve_color_array_length_matches_input
      {n : Nat} {t : Nat} {arr : List Nat} :
      (solve_color_array n t arr).length = arr.length :=
      sorry
    -- </vc-theorems>

### 7. score 90 - specs/LT0009_specs.lean:21
- baseline rc: 0
- current: `(∀ i : Fin n, result.get ⟨i.val * n + i.val, sorry⟩ = v.get i) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    import Std.Tactic.Do
    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def diagflat {n : Nat} (v : Vector Float n) : Id (Vector Float (n * n)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem diagflat_spec {n : Nat} (v : Vector Float n) :
        ⦃⌜True⌝⦄
        diagflat v
        ⦃⇓result => ⌜
          -- Elements on the main diagonal are from the input vector
          (∀ i : Fin n, result.get ⟨i.val * n + i.val, sorry⟩ = v.get i) ∧
          -- All other elements are zero
          (∀ i j : Fin n, i ≠ j → result.get ⟨i.val * n + j.val, sorry⟩ = 0)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 8. score 90 - specs/LT0014_specs.lean:20
- baseline rc: 0
- current: `⦃⇓result => ⌜∀ i : Fin count, result.get i = buffer.get ⟨offset + i.val, sorry⟩⌝⦄ := by`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    import Std.Do.Triple
    import Std.Tactic.Do
    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def frombuffer {n : Nat} (buffer : Vector UInt8 n) (count : Nat) (offset : Nat) : Id (Vector UInt8 count) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem frombuffer_spec {n : Nat} (buffer : Vector UInt8 n) (count : Nat) (offset : Nat)
        (h_bounds : offset + count ≤ n) (h_offset : offset < n ∨ count = 0) :
        ⦃⌜offset + count ≤ n ∧ (offset < n ∨ count = 0)⌝⦄
        frombuffer buffer count offset
        ⦃⇓result => ⌜∀ i : Fin count, result.get i = buffer.get ⟨offset + i.val, sorry⟩⌝⦄ := by
      sorry
    -- </vc-theorems>

### 9. score 90 - specs/LT0056_specs.lean:24
- baseline rc: 0
- current: `arr.get ⟨part_idx.val * (n / k) + elem_idx.val, by sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def hsplit {n k : Nat} (arr : Vector Float n) 
        (h_divides : k > 0 ∧ n % k = 0) : 
        Id (Vector (Vector Float (n / k)) k) :=
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

### 10. score 90 - specs/LT0091_specs.lean:21
- baseline rc: 0
- current: `result.get ⟨i.val * 8 + j.val, sorry⟩ =`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    import Std.Tactic.Do
    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def numpy_unpackbits {n : Nat} (a : Vector Nat n) : Id (Vector Nat (n * 8)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem numpy_unpackbits_spec {n : Nat} (a : Vector Nat n) 
        (h_uint8 : ∀ i : Fin n, a.get i < 256) :
        ⦃⌜∀ i : Fin n, a.get i < 256⌝⦄
        numpy_unpackbits a
        ⦃⇓result => ⌜∀ i : Fin n, ∀ j : Fin 8,
                      result.get ⟨i.val * 8 + j.val, sorry⟩ = 
                      (a.get i / (2 ^ (7 - j.val))) % 2⌝⦄ := by
      sorry
    -- </vc-theorems>

### 11. score 90 - specs/LT0151_specs.lean:19
- baseline rc: 0
- current: `⦃⇓result => ⌜∀ i : Fin n, result.get i = x.get ⟨(i.val + n - n / 2) % n, sorry⟩ ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    -- <vc-preamble>
    import Std.Do.Triple
    import Std.Tactic.Do
    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def fftshift {n : Nat} (x : Vector Float n) : Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem fftshift_spec {n : Nat} (x : Vector Float n) :
        ⦃⌜True⌝⦄
        fftshift x
        ⦃⇓result => ⌜∀ i : Fin n, result.get i = x.get ⟨(i.val + n - n / 2) % n, sorry⟩ ∧
                      (∀ j : Fin n, ∃ k : Fin n, result.get k = x.get j) ∧
                      (∀ val : Float, (∃ j : Fin n, x.get j = val) ↔ (∃ k : Fin n, result.get k = val))⌝⦄ := by
      sorry
    -- </vc-theorems>

### 12. score 90 - specs/LT0156_specs.lean:19
- baseline rc: 0
- current: `⦃⇓result => ⌜∀ i : Fin n, result.get i = x.get ⟨(i.val + n / 2) % n, sorry⟩⌝⦄ := by`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    -- <vc-preamble>
    import Std.Do.Triple
    import Std.Tactic.Do
    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def ifftshift {n : Nat} (x : Vector Float n) : Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem ifftshift_spec {n : Nat} (x : Vector Float n) :
        ⦃⌜True⌝⦄
        ifftshift x
        ⦃⇓result => ⌜∀ i : Fin n, result.get i = x.get ⟨(i.val + n / 2) % n, sorry⟩⌝⦄ := by
      sorry
    -- </vc-theorems>

### 13. score 90 - specs/LT0171_specs.lean:14
- baseline rc: 0
- current: `∀ i : Fin n, (diag matrix).get i = matrix.get ⟨i.val * n + i.val, by sorry⟩ := by`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def diag {n : Nat} (matrix : Vector Float (n * n)) : Vector Float n :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem diag_spec {n : Nat} (matrix : Vector Float (n * n)) : 
        ∀ i : Fin n, (diag matrix).get i = matrix.get ⟨i.val * n + i.val, by sorry⟩ := by
      sorry
    -- </vc-theorems>

### 14. score 90 - specs/LT0173_specs.lean:28
- baseline rc: 0
- current: `result.get i = (a.get ⟨i.val, by sorry⟩).get ⟨i.val + offset.natAbs, by sorry⟩`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    -- <vc-definitions>
    def diagonal {rows cols : Nat} (a : Vector (Vector Float cols) rows) (offset : Int := 0) : 
      Id (Vector Float (if offset ≥ 0 then min rows (cols - offset.natAbs) else min (rows - offset.natAbs) cols)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem diagonal_spec {rows cols : Nat} (a : Vector (Vector Float cols) rows) (offset : Int := 0) 
        (h_valid : if offset ≥ 0 then offset.natAbs ≤ cols else offset.natAbs ≤ rows) :
        ⦃⌜if offset ≥ 0 then offset.natAbs ≤ cols else offset.natAbs ≤ rows⌝⦄
        diagonal a offset
        ⦃⇓result => ⌜
          -- Result size matches the diagonal size
          result.size = (if offset ≥ 0 then min rows (cols - offset.natAbs) else min (rows - offset.natAbs) cols) ∧
          -- Each element is from the correct diagonal position
          (∀ i : Fin result.size, 
            if offset ≥ 0 then
              -- For non-negative offset: a[i, i+offset]
              result.get i = (a.get ⟨i.val, by sorry⟩).get ⟨i.val + offset.natAbs, by sorry⟩
            else
              -- For negative offset: a[i+|offset|, i]
              result.get i = (a.get ⟨i.val + offset.natAbs, by sorry⟩).get ⟨i.val, by sorry⟩) ∧
          -- Sanity check: result is non-empty when matrix is non-empty and offset is valid
          (rows > 0 ∧ cols > 0 → result.size > 0)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 15. score 90 - specs/LT0173_specs.lean:31
- baseline rc: 0
- current: `result.get i = (a.get ⟨i.val + offset.natAbs, by sorry⟩).get ⟨i.val, by sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem diagonal_spec {rows cols : Nat} (a : Vector (Vector Float cols) rows) (offset : Int := 0) 
        (h_valid : if offset ≥ 0 then offset.natAbs ≤ cols else offset.natAbs ≤ rows) :
        ⦃⌜if offset ≥ 0 then offset.natAbs ≤ cols else offset.natAbs ≤ rows⌝⦄
        diagonal a offset
        ⦃⇓result => ⌜
          -- Result size matches the diagonal size
          result.size = (if offset ≥ 0 then min rows (cols - offset.natAbs) else min (rows - offset.natAbs) cols) ∧
          -- Each element is from the correct diagonal position
          (∀ i : Fin result.size, 
            if offset ≥ 0 then
              -- For non-negative offset: a[i, i+offset]
              result.get i = (a.get ⟨i.val, by sorry⟩).get ⟨i.val + offset.natAbs, by sorry⟩
            else
              -- For negative offset: a[i+|offset|, i]
              result.get i = (a.get ⟨i.val + offset.natAbs, by sorry⟩).get ⟨i.val, by sorry⟩) ∧
          -- Sanity check: result is non-empty when matrix is non-empty and offset is valid
          (rows > 0 ∧ cols > 0 → result.size > 0)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 16. score 90 - specs/LT0579_specs.lean:28
- baseline rc: 0
- current: `result.get k = (Vector.ofFn (fun i : Fin n => a.get ⟨k.val + i.val, by sorry⟩ * v.get i)).toList.sum) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: 

Window:

    -- <vc-definitions>
    def correlate {m n : Nat} (a : Vector Float m) (v : Vector Float n) (h : n ≤ m) (h_pos : 0 < n) : Id (Vector Float (m + 1 - n)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem correlate_spec {m n : Nat} (a : Vector Float m) (v : Vector Float n) (h : n ≤ m) (h_pos : 0 < n) :
        ⦃⌜n ≤ m ∧ 0 < n⌝⦄
        correlate a v h h_pos
        ⦃⇓result => ⌜-- Cross-correlation computation property: each output element is the sum of products
                     (∀ k : Fin (m + 1 - n), 
                       ∃ products : Fin n → Float,
                       (∀ i : Fin n, products i = a.get ⟨k.val + i.val, by sorry⟩ * v.get i) ∧
                       result.get k = (Vector.ofFn products).toList.sum) ∧
                     -- Boundary condition: all indices are valid for the computation
                     (∀ k : Fin (m + 1 - n), ∀ i : Fin n, k.val + i.val < m) ∧
                     -- Mathematical property: correlation is bilinear in its arguments
                     (∀ k : Fin (m + 1 - n), 
                       result.get k = (Vector.ofFn (fun i : Fin n => a.get ⟨k.val + i.val, by sorry⟩ * v.get i)).toList.sum) ∧
                     -- Non-negativity when both sequences are non-negative
                     ((∀ i : Fin m, 0 ≤ a.get i) ∧ (∀ i : Fin n, 0 ≤ v.get i) →
                       ∀ k : Fin (m + 1 - n), 0 ≤ result.get k)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 17. score 85 - specs/LT0049_specs.lean:22
- baseline rc: 0
- current: `result.get i = arr.get ⟨i.val, by sorry⟩`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, successor_bound_shape
- penalties: 

Window:

    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def delete {n : Nat} (arr : Vector Float (n + 1)) (index : Fin (n + 1)) : 
        Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem delete_spec {n : Nat} (arr : Vector Float (n + 1)) (index : Fin (n + 1)) :
        ⦃⌜True⌝⦄
        delete arr index
        ⦃⇓result => ⌜(∀ i : Fin n, 
                       if h : i.val < index.val then 
                         result.get i = arr.get ⟨i.val, by sorry⟩
                       else 
                         result.get i = arr.get ⟨i.val + 1, by sorry⟩) ∧
                     (∀ i : Fin (n + 1), i ≠ index → 
                       ∃ j : Fin n, result.get j = arr.get i)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 18. score 80 - specs/LT0583_specs.lean:30
- baseline rc: 0
- current: `(∀ i : Fin nbins, x_edges.get ⟨i, sorry⟩ < x_edges.get ⟨i + 1, sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, arithmetic_index, successor_bound_shape
- penalties: 

Window:

        (h_bins_pos : bins > 0) (h_nbins_eq : nbins = bins) : Id (Vector (Vector Nat nbins) nbins × Vector Float (nbins + 1) × Vector Float (nbins + 1)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem histogram2d_spec {n : Nat} {nbins : Nat} (x y : Vector Float n) (bins : Nat) 
        (h_bins_pos : bins > 0) (h_nbins_eq : nbins = bins) :
        ⦃⌜bins > 0⌝⦄
        histogram2d x y bins h_bins_pos h_nbins_eq
        ⦃⇓result => ⌜-- Destructure the result tuple
                     let (hist, x_edges, y_edges) := result
                     -- 1. All histogram values are non-negative
                     (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≥ 0) ∧
                     -- 2. Total count conservation: sum of all bins equals input length
                     (∃ total : Nat, 
                       (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≤ n) ∧
                       total = n) ∧
                     -- 3. Bin edges are monotonically increasing
                     (∀ i : Fin nbins, x_edges.get ⟨i, sorry⟩ < x_edges.get ⟨i + 1, sorry⟩) ∧
                     (∀ i : Fin nbins, y_edges.get ⟨i, sorry⟩ < y_edges.get ⟨i + 1, sorry⟩) ∧
                     -- 4. Bin edges span the data range appropriately
                     (∃ x_min x_max y_min y_max : Float,
                       (∀ i : Fin n, x_min ≤ x.get i ∧ x.get i ≤ x_max) ∧
                       (∀ i : Fin n, y_min ≤ y.get i ∧ y.get i ≤ y_max) ∧
                       x_edges.get ⟨0, sorry⟩ ≤ x_min ∧ x_max ≤ x_edges.get ⟨nbins, sorry⟩ ∧
                       y_edges.get ⟨0, sorry⟩ ≤ y_min ∧ y_max ≤ y_edges.get ⟨nbins, sorry⟩) ∧
                     -- 5. Histogram correctly partitions the data space
                     (∀ i : Fin nbins, ∀ j : Fin nbins,
                       ∀ k : Fin n,
                       let x_val := x.get k
                       let y_val := y.get k
                       let x_left := x_edges.get ⟨i, sorry⟩
                       let x_right := x_edges.get ⟨i + 1, sorry⟩  
                       let y_left := y_edges.get ⟨j, sorry⟩
                       let y_right := y_edges.get ⟨j + 1, sorry⟩
                       (x_left ≤ x_val ∧ x_val < x_right ∧ y_left ≤ y_val ∧ y_val < y_right) ∨

### 19. score 75 - specs/LF0093_specs.lean:15
- baseline rc: 0
- current: `let firstVal := arr.get ⟨0, sorry⟩`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def solve_color_array (n : Nat) (t : Nat) (arr : List Nat) : List Nat :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem solve_color_array_equal_values_alternate
      {n : Nat} {arr : List Nat} (h : arr.length > 0) :
      let firstVal := arr.get ⟨0, sorry⟩
      let t := 2 * firstVal
      let result := solve_color_array n t (List.replicate arr.length firstVal)
      ∀ i : Fin (result.length - 1),
        (result.get ⟨i.val, sorry⟩) ≠ (result.get ⟨i.val + 1, sorry⟩) :=
      sorry
    
    theorem solve_color_array_length_matches_input
      {n : Nat} {t : Nat} {arr : List Nat} :
      (solve_color_array n t arr).length = arr.length :=
      sorry
    -- </vc-theorems>

### 20. score 75 - specs/LF3983_specs.lean:17
- baseline rc: 0
- current: `(ulamSequence u0 u1 n).get ⟨0, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def ulamSequence (u0 u1 n : Nat) : List Nat := sorry
    
    theorem ulam_sequence_length (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) :
      List.length (ulamSequence u0 u1 n) = n := sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem ulam_sequence_first_elements (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ulamSequence u0 u1 n ≠ [] ∧
      (ulamSequence u0 u1 n).get ⟨0, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 ∧
      (ulamSequence u0 u1 n).get ⟨1, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u1 := sorry
    
    theorem ulam_sequence_strictly_increasing (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, i.val + 1 < n →
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2
        (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) <
        (seq.get ⟨i.val + 1, by {rw [h_length]; sorry}⟩) := sorry
    
    theorem ulam_sequence_third_element (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      (ulamSequence u0 u1 n).get ⟨2, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 + u1 := sorry
    
    theorem ulam_sequence_unique_sum (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, 2 ≤ i.val → 
      ∃ (p : Nat × Nat), (∀ q : Nat × Nat,
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2

### 21. score 75 - specs/LF3983_specs.lean:18
- baseline rc: 0
- current: `(ulamSequence u0 u1 n).get ⟨1, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u1 := sorry`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val
- penalties: 

Window:

    -- <vc-preamble>
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def ulamSequence (u0 u1 n : Nat) : List Nat := sorry
    
    theorem ulam_sequence_length (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) :
      List.length (ulamSequence u0 u1 n) = n := sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem ulam_sequence_first_elements (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ulamSequence u0 u1 n ≠ [] ∧
      (ulamSequence u0 u1 n).get ⟨0, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 ∧
      (ulamSequence u0 u1 n).get ⟨1, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u1 := sorry
    
    theorem ulam_sequence_strictly_increasing (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, i.val + 1 < n →
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2
        (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) <
        (seq.get ⟨i.val + 1, by {rw [h_length]; sorry}⟩) := sorry
    
    theorem ulam_sequence_third_element (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      (ulamSequence u0 u1 n).get ⟨2, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 + u1 := sorry
    
    theorem ulam_sequence_unique_sum (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, 2 ≤ i.val → 
      ∃ (p : Nat × Nat), (∀ q : Nat × Nat,
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2
        p.1 < p.2 ∧ 

### 22. score 75 - specs/LT0179_specs.lean:36
- baseline rc: 0
- current: `(∀ j : Fin cols, (result.1.get ⟨0, by sorry⟩).get j = start_r) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val
- penalties: 

Window:

    theorem mgrid_spec {rows cols : Nat} (start_r stop_r start_c stop_c : Float) 
        (h_rows : rows > 0) (h_cols : cols > 0) :
        ⦃⌜rows > 0 ∧ cols > 0⌝⦄
        mgrid start_r stop_r start_c stop_c h_rows h_cols
        ⦃⇓result => ⌜-- Both arrays have the same shape  
                      (result.1.size = rows) ∧ (result.2.size = rows) ∧
                      (∀ i : Fin rows, (result.1.get i).size = cols ∧ (result.2.get i).size = cols) ∧
                      -- Row coordinates: same value across each row
                      (∀ i : Fin rows, ∀ j k : Fin cols, (result.1.get i).get j = (result.1.get i).get k) ∧
                      -- Column coordinates: same value down each column  
                      (∀ j : Fin cols, ∀ i k : Fin rows, (result.2.get i).get j = (result.2.get k).get j) ∧
                      -- Row coordinates are evenly spaced
                      (∀ i : Fin rows, ∀ j : Fin cols, 
                        (result.1.get i).get j = start_r + (Float.ofNat i.val) * (stop_r - start_r) / (Float.ofNat rows)) ∧
                      -- Column coordinates are evenly spaced
                      (∀ i : Fin rows, ∀ j : Fin cols,
                        (result.2.get i).get j = start_c + (Float.ofNat j.val) * (stop_c - start_c) / (Float.ofNat cols)) ∧
                      -- Boundary conditions: first/last coordinates match start/stop points
                      (∀ j : Fin cols, (result.1.get ⟨0, by sorry⟩).get j = start_r) ∧
                      (∀ i : Fin rows, (result.2.get i).get ⟨0, by sorry⟩ = start_c) ∧
                      -- Mathematical property: coordinates form a complete grid
                      (∀ i : Fin rows, ∀ j : Fin cols, 
                        start_r ≤ (result.1.get i).get j ∧ (result.1.get i).get j < stop_r) ∧
                      (∀ i : Fin rows, ∀ j : Fin cols, 
                        start_c ≤ (result.2.get i).get j ∧ (result.2.get i).get j < stop_c)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 23. score 75 - specs/LT0179_specs.lean:37
- baseline rc: 0
- current: `(∀ i : Fin rows, (result.2.get i).get ⟨0, by sorry⟩ = start_c) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val
- penalties: 

Window:

        (h_rows : rows > 0) (h_cols : cols > 0) :
        ⦃⌜rows > 0 ∧ cols > 0⌝⦄
        mgrid start_r stop_r start_c stop_c h_rows h_cols
        ⦃⇓result => ⌜-- Both arrays have the same shape  
                      (result.1.size = rows) ∧ (result.2.size = rows) ∧
                      (∀ i : Fin rows, (result.1.get i).size = cols ∧ (result.2.get i).size = cols) ∧
                      -- Row coordinates: same value across each row
                      (∀ i : Fin rows, ∀ j k : Fin cols, (result.1.get i).get j = (result.1.get i).get k) ∧
                      -- Column coordinates: same value down each column  
                      (∀ j : Fin cols, ∀ i k : Fin rows, (result.2.get i).get j = (result.2.get k).get j) ∧
                      -- Row coordinates are evenly spaced
                      (∀ i : Fin rows, ∀ j : Fin cols, 
                        (result.1.get i).get j = start_r + (Float.ofNat i.val) * (stop_r - start_r) / (Float.ofNat rows)) ∧
                      -- Column coordinates are evenly spaced
                      (∀ i : Fin rows, ∀ j : Fin cols,
                        (result.2.get i).get j = start_c + (Float.ofNat j.val) * (stop_c - start_c) / (Float.ofNat cols)) ∧
                      -- Boundary conditions: first/last coordinates match start/stop points
                      (∀ j : Fin cols, (result.1.get ⟨0, by sorry⟩).get j = start_r) ∧
                      (∀ i : Fin rows, (result.2.get i).get ⟨0, by sorry⟩ = start_c) ∧
                      -- Mathematical property: coordinates form a complete grid
                      (∀ i : Fin rows, ∀ j : Fin cols, 
                        start_r ≤ (result.1.get i).get j ∧ (result.1.get i).get j < stop_r) ∧
                      (∀ i : Fin rows, ∀ j : Fin cols, 
                        start_c ≤ (result.2.get i).get j ∧ (result.2.get i).get j < stop_c)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 24. score 75 - specs/LT0326_specs.lean:32
- baseline rc: 0
- current: `xp.get ⟨i.val, sorry⟩ ≤ x.get k ∧ x.get k ≤ xp.get ⟨i.val + 1, sorry⟩ →`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: recent_implication_guard_may_not_be_visible

Window:

    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem interp_spec {n m : Nat} (x : Vector Float n) (xp : Vector Float (m + 1)) (fp : Vector Float (m + 1)) 
        (h_increasing : ∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j) :
        ⦃⌜∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j⌝⦄
        interp x xp fp h_increasing
        ⦃⇓result => ⌜
          -- Each interpolated value is computed correctly
          ∀ k : Fin n, 
            -- For points outside the left range, use left boundary value
            (x.get k ≤ xp.get ⟨0, sorry⟩ → result.get k = fp.get ⟨0, sorry⟩) ∧
            -- For points outside the right range, use right boundary value
            (x.get k ≥ xp.get ⟨m, sorry⟩ → result.get k = fp.get ⟨m, sorry⟩) ∧
            -- For points exactly at data points, return exact values
            (∀ i : Fin (m + 1), x.get k = xp.get i → result.get k = fp.get i) ∧
            -- For points within the range, value is between adjacent data points
            (∀ i : Fin m, 
              xp.get ⟨i.val, sorry⟩ ≤ x.get k ∧ x.get k ≤ xp.get ⟨i.val + 1, sorry⟩ →
              ∃ t : Float, 0 ≤ t ∧ t ≤ 1 ∧ 
              result.get k = fp.get ⟨i.val, sorry⟩ + t * (fp.get ⟨i.val + 1, sorry⟩ - fp.get ⟨i.val, sorry⟩))
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 25. score 75 - specs/LT0326_specs.lean:34
- baseline rc: 0
- current: `result.get k = fp.get ⟨i.val, sorry⟩ + t * (fp.get ⟨i.val + 1, sorry⟩ - fp.get ⟨i.val, sorry⟩))`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: recent_implication_guard_may_not_be_visible

Window:

    -- <vc-theorems>
    theorem interp_spec {n m : Nat} (x : Vector Float n) (xp : Vector Float (m + 1)) (fp : Vector Float (m + 1)) 
        (h_increasing : ∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j) :
        ⦃⌜∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j⌝⦄
        interp x xp fp h_increasing
        ⦃⇓result => ⌜
          -- Each interpolated value is computed correctly
          ∀ k : Fin n, 
            -- For points outside the left range, use left boundary value
            (x.get k ≤ xp.get ⟨0, sorry⟩ → result.get k = fp.get ⟨0, sorry⟩) ∧
            -- For points outside the right range, use right boundary value
            (x.get k ≥ xp.get ⟨m, sorry⟩ → result.get k = fp.get ⟨m, sorry⟩) ∧
            -- For points exactly at data points, return exact values
            (∀ i : Fin (m + 1), x.get k = xp.get i → result.get k = fp.get i) ∧
            -- For points within the range, value is between adjacent data points
            (∀ i : Fin m, 
              xp.get ⟨i.val, sorry⟩ ≤ x.get k ∧ x.get k ≤ xp.get ⟨i.val + 1, sorry⟩ →
              ∃ t : Float, 0 ≤ t ∧ t ≤ 1 ∧ 
              result.get k = fp.get ⟨i.val, sorry⟩ + t * (fp.get ⟨i.val + 1, sorry⟩ - fp.get ⟨i.val, sorry⟩))
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 26. score 75 - specs/LT0420_specs.lean:26
- baseline rc: 0
- current: `(∀ i : Fin n, i.val ≥ 1 → result.get ⟨i.val + 1, sorry⟩ = c.get i)`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: recent_implication_guard_may_not_be_visible

Window:

    -- </vc-helpers>
    
    -- <vc-definitions>
    def hermemulx {n : Nat} (c : Vector Float n) : Id (Vector Float (n + 1)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem hermemulx_spec {n : Nat} (c : Vector Float n) :
        ⦃⌜True⌝⦄
        hermemulx c
        ⦃⇓result => ⌜
          -- Coefficient at position 0 is always 0 (no constant term in x*polynomial)
          result.get ⟨0, by simp⟩ = 0 ∧
          -- For n > 0: coefficient at position 1 comes from c[0] plus recursive contributions  
          (∀ (h : n > 0), result.get ⟨1, sorry⟩ = c.get ⟨0, h⟩ + 
            (if n > 1 then (c.get ⟨1, sorry⟩) * (1 : Float) else 0)) ∧
          -- For i ≥ 1: result[i+1] gets c[i] (coefficient shift up)
          (∀ i : Fin n, i.val ≥ 1 → result.get ⟨i.val + 1, sorry⟩ = c.get i)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 27. score 75 - specs/LT0425_specs.lean:75
- baseline rc: 0
- current: `(const_coeff.get ⟨0, sorry⟩).get ⟨0, sorry⟩ = 1 ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val
- penalties: 

Window:

                         (∀ i : Fin n, x_combined.get i = α * x1.get i + β * x2.get i) ∧
                         hermeval2d x_combined y1 c = pure result_combined_x ∧
                         ∀ k : Fin n, result_combined_x.get k = α * result_x1y1.get k + β * result_x2y1.get k) ∧
                       -- Linear combination in y direction
                       (∃ y_combined : Vector Float n,
                         (∀ i : Fin n, y_combined.get i = α * y1.get i + β * y2.get i) ∧
                         hermeval2d x1 y_combined c = pure result_combined_y ∧
                         ∀ k : Fin n, result_combined_y.get k = α * result_x1y1.get k + β * result_x1y2.get k)) ∧
                     -- Special case properties for verification
                     (m > 0 ∧ n > 0 → 
                       -- Zero coefficient matrix gives zero polynomial
                       (∃ zero_coeff : Vector (Vector Float m) n,
                         (∀ i : Fin n, ∀ j : Fin m, (zero_coeff.get i).get j = 0) ∧
                         ∃ zero_result : Vector Float n,
                         hermeval2d x y zero_coeff = pure zero_result ∧
                         ∀ k : Fin n, zero_result.get k = 0) ∧
                       -- Constant polynomial (c₀₀ = 1, all others = 0)
                       (∃ const_coeff : Vector (Vector Float m) n,
                         (const_coeff.get ⟨0, sorry⟩).get ⟨0, sorry⟩ = 1 ∧
                         (∀ i : Fin n, ∀ j : Fin m, (i.val ≠ 0 ∨ j.val ≠ 0) → (const_coeff.get i).get j = 0) ∧
                         ∃ const_result : Vector Float n,
                         hermeval2d x y const_coeff = pure const_result ∧
                         ∀ k : Fin n, const_result.get k = 1))⌝⦄ := by
      sorry
    -- </vc-theorems>

### 28. score 75 - specs/LT0450_specs.lean:65
- baseline rc: 0
- current: `(fun j : Fin cols => (c.get ⟨0, sorry⟩).get j * H_y j.val)`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: recent_implication_guard_may_not_be_visible

Window:

                             a * (c1.get i).get j + b * (c2.get i).get j))
                         -- Evaluates to linear combination of results
                         ∃ (res1 res2 res_combined : Vector Float n),
                           (⦃⌜True⌝⦄ hermval2d x y c1 ⦃⇓r => ⌜r = res1⌝⦄) ∧
                           (⦃⌜True⌝⦄ hermval2d x y c2 ⦃⇓r => ⌜r = res2⌝⦄) ∧
                           (⦃⌜True⌝⦄ hermval2d x y c_combined ⦃⇓r => ⌜r = res_combined⌝⦄) ∧
                           res_combined.get k = a * res1.get k + b * res2.get k) ∧
                     -- Separability property: 2D evaluation is product of 1D evaluations
                     (rows = 1 ∧ cols > 0 → 
                       ∀ k : Fin n,
                         ∃ H_y : Nat → Float,
                           -- H_y satisfies Hermite recurrence
                           H_y 0 = 1 ∧
                           H_y 1 = 2 * (y.get k) ∧
                           (∀ j : Nat, j + 2 < cols → 
                             H_y (j + 2) = 2 * (y.get k) * H_y (j + 1) - 2 * Float.ofNat (j + 1) * H_y j) ∧
                           -- Result is c[0,j] * H_0(x) * H_j(y) = c[0,j] * 1 * H_j(y)
                           result.get k = List.sum (List.map 
                             (fun j : Fin cols => (c.get ⟨0, sorry⟩).get j * H_y j.val) 
                             (List.finRange cols))) ∧
                     (cols = 1 ∧ rows > 0 → 
                       ∀ k : Fin n,
                         ∃ H_x : Nat → Float,
                           -- H_x satisfies Hermite recurrence
                           H_x 0 = 1 ∧
                           H_x 1 = 2 * (x.get k) ∧
                           (∀ i : Nat, i + 2 < rows → 
                             H_x (i + 2) = 2 * (x.get k) * H_x (i + 1) - 2 * Float.ofNat (i + 1) * H_x i) ∧
                           -- Result is c[i,0] * H_i(x) * H_0(y) = c[i,0] * H_i(x) * 1
                           result.get k = List.sum (List.map 
                             (fun i : Fin rows => (c.get i).get ⟨0, sorry⟩ * H_x i.val) 
                             (List.finRange rows)))⌝⦄ := by
      sorry
    -- </vc-theorems>

### 29. score 75 - specs/LT0450_specs.lean:77
- baseline rc: 0
- current: `(fun i : Fin rows => (c.get i).get ⟨0, sorry⟩ * H_x i.val)`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index, successor_bound_shape
- penalties: recent_implication_guard_may_not_be_visible

Window:

                           H_y 0 = 1 ∧
                           H_y 1 = 2 * (y.get k) ∧
                           (∀ j : Nat, j + 2 < cols → 
                             H_y (j + 2) = 2 * (y.get k) * H_y (j + 1) - 2 * Float.ofNat (j + 1) * H_y j) ∧
                           -- Result is c[0,j] * H_0(x) * H_j(y) = c[0,j] * 1 * H_j(y)
                           result.get k = List.sum (List.map 
                             (fun j : Fin cols => (c.get ⟨0, sorry⟩).get j * H_y j.val) 
                             (List.finRange cols))) ∧
                     (cols = 1 ∧ rows > 0 → 
                       ∀ k : Fin n,
                         ∃ H_x : Nat → Float,
                           -- H_x satisfies Hermite recurrence
                           H_x 0 = 1 ∧
                           H_x 1 = 2 * (x.get k) ∧
                           (∀ i : Nat, i + 2 < rows → 
                             H_x (i + 2) = 2 * (x.get k) * H_x (i + 1) - 2 * Float.ofNat (i + 1) * H_x i) ∧
                           -- Result is c[i,0] * H_i(x) * H_0(y) = c[i,0] * H_i(x) * 1
                           result.get k = List.sum (List.map 
                             (fun i : Fin rows => (c.get i).get ⟨0, sorry⟩ * H_x i.val) 
                             (List.finRange rows)))⌝⦄ := by
      sorry
    -- </vc-theorems>

### 30. score 70 - specs/LT0583_specs.lean:31
- baseline rc: 0
- current: `(∀ i : Fin nbins, y_edges.get ⟨i, sorry⟩ < y_edges.get ⟨i + 1, sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, arithmetic_index
- penalties: 

Window:

      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem histogram2d_spec {n : Nat} {nbins : Nat} (x y : Vector Float n) (bins : Nat) 
        (h_bins_pos : bins > 0) (h_nbins_eq : nbins = bins) :
        ⦃⌜bins > 0⌝⦄
        histogram2d x y bins h_bins_pos h_nbins_eq
        ⦃⇓result => ⌜-- Destructure the result tuple
                     let (hist, x_edges, y_edges) := result
                     -- 1. All histogram values are non-negative
                     (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≥ 0) ∧
                     -- 2. Total count conservation: sum of all bins equals input length
                     (∃ total : Nat, 
                       (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≤ n) ∧
                       total = n) ∧
                     -- 3. Bin edges are monotonically increasing
                     (∀ i : Fin nbins, x_edges.get ⟨i, sorry⟩ < x_edges.get ⟨i + 1, sorry⟩) ∧
                     (∀ i : Fin nbins, y_edges.get ⟨i, sorry⟩ < y_edges.get ⟨i + 1, sorry⟩) ∧
                     -- 4. Bin edges span the data range appropriately
                     (∃ x_min x_max y_min y_max : Float,
                       (∀ i : Fin n, x_min ≤ x.get i ∧ x.get i ≤ x_max) ∧
                       (∀ i : Fin n, y_min ≤ y.get i ∧ y.get i ≤ y_max) ∧
                       x_edges.get ⟨0, sorry⟩ ≤ x_min ∧ x_max ≤ x_edges.get ⟨nbins, sorry⟩ ∧
                       y_edges.get ⟨0, sorry⟩ ≤ y_min ∧ y_max ≤ y_edges.get ⟨nbins, sorry⟩) ∧
                     -- 5. Histogram correctly partitions the data space
                     (∀ i : Fin nbins, ∀ j : Fin nbins,
                       ∀ k : Fin n,
                       let x_val := x.get k
                       let y_val := y.get k
                       let x_left := x_edges.get ⟨i, sorry⟩
                       let x_right := x_edges.get ⟨i + 1, sorry⟩  
                       let y_left := y_edges.get ⟨j, sorry⟩
                       let y_right := y_edges.get ⟨j + 1, sorry⟩
                       (x_left ≤ x_val ∧ x_val < x_right ∧ y_left ≤ y_val ∧ y_val < y_right) ∨
                       (i = nbins - 1 ∧ j = nbins - 1 ∧ x_val = x_right ∧ y_val = y_right) →

### 31. score 70 - specs/LT0583_specs.lean:44
- baseline rc: 0
- current: `let x_right := x_edges.get ⟨i + 1, sorry⟩`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, arithmetic_index
- penalties: 

Window:

                     (∃ total : Nat, 
                       (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≤ n) ∧
                       total = n) ∧
                     -- 3. Bin edges are monotonically increasing
                     (∀ i : Fin nbins, x_edges.get ⟨i, sorry⟩ < x_edges.get ⟨i + 1, sorry⟩) ∧
                     (∀ i : Fin nbins, y_edges.get ⟨i, sorry⟩ < y_edges.get ⟨i + 1, sorry⟩) ∧
                     -- 4. Bin edges span the data range appropriately
                     (∃ x_min x_max y_min y_max : Float,
                       (∀ i : Fin n, x_min ≤ x.get i ∧ x.get i ≤ x_max) ∧
                       (∀ i : Fin n, y_min ≤ y.get i ∧ y.get i ≤ y_max) ∧
                       x_edges.get ⟨0, sorry⟩ ≤ x_min ∧ x_max ≤ x_edges.get ⟨nbins, sorry⟩ ∧
                       y_edges.get ⟨0, sorry⟩ ≤ y_min ∧ y_max ≤ y_edges.get ⟨nbins, sorry⟩) ∧
                     -- 5. Histogram correctly partitions the data space
                     (∀ i : Fin nbins, ∀ j : Fin nbins,
                       ∀ k : Fin n,
                       let x_val := x.get k
                       let y_val := y.get k
                       let x_left := x_edges.get ⟨i, sorry⟩
                       let x_right := x_edges.get ⟨i + 1, sorry⟩  
                       let y_left := y_edges.get ⟨j, sorry⟩
                       let y_right := y_edges.get ⟨j + 1, sorry⟩
                       (x_left ≤ x_val ∧ x_val < x_right ∧ y_left ≤ y_val ∧ y_val < y_right) ∨
                       (i = nbins - 1 ∧ j = nbins - 1 ∧ x_val = x_right ∧ y_val = y_right) →
                       (hist.get i).get j ≥ 1)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 32. score 70 - specs/LT0583_specs.lean:46
- baseline rc: 0
- current: `let y_right := y_edges.get ⟨j + 1, sorry⟩`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, arithmetic_index
- penalties: 

Window:

                       total = n) ∧
                     -- 3. Bin edges are monotonically increasing
                     (∀ i : Fin nbins, x_edges.get ⟨i, sorry⟩ < x_edges.get ⟨i + 1, sorry⟩) ∧
                     (∀ i : Fin nbins, y_edges.get ⟨i, sorry⟩ < y_edges.get ⟨i + 1, sorry⟩) ∧
                     -- 4. Bin edges span the data range appropriately
                     (∃ x_min x_max y_min y_max : Float,
                       (∀ i : Fin n, x_min ≤ x.get i ∧ x.get i ≤ x_max) ∧
                       (∀ i : Fin n, y_min ≤ y.get i ∧ y.get i ≤ y_max) ∧
                       x_edges.get ⟨0, sorry⟩ ≤ x_min ∧ x_max ≤ x_edges.get ⟨nbins, sorry⟩ ∧
                       y_edges.get ⟨0, sorry⟩ ≤ y_min ∧ y_max ≤ y_edges.get ⟨nbins, sorry⟩) ∧
                     -- 5. Histogram correctly partitions the data space
                     (∀ i : Fin nbins, ∀ j : Fin nbins,
                       ∀ k : Fin n,
                       let x_val := x.get k
                       let y_val := y.get k
                       let x_left := x_edges.get ⟨i, sorry⟩
                       let x_right := x_edges.get ⟨i + 1, sorry⟩  
                       let y_left := y_edges.get ⟨j, sorry⟩
                       let y_right := y_edges.get ⟨j + 1, sorry⟩
                       (x_left ≤ x_val ∧ x_val < x_right ∧ y_left ≤ y_val ∧ y_val < y_right) ∨
                       (i = nbins - 1 ∧ j = nbins - 1 ∧ x_val = x_right ∧ y_val = y_right) →
                       (hist.get i).get j ≥ 1)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 33. score 65 - specs/LF3983_specs.lean:25
- baseline rc: 0
- current: `(seq.get ⟨i.val + 1, by {rw [h_length]; sorry}⟩) := sorry`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: recent_implication_guard_may_not_be_visible

Window:

    -- <vc-definitions>
    def ulamSequence (u0 u1 n : Nat) : List Nat := sorry
    
    theorem ulam_sequence_length (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) :
      List.length (ulamSequence u0 u1 n) = n := sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem ulam_sequence_first_elements (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ulamSequence u0 u1 n ≠ [] ∧
      (ulamSequence u0 u1 n).get ⟨0, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 ∧
      (ulamSequence u0 u1 n).get ⟨1, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u1 := sorry
    
    theorem ulam_sequence_strictly_increasing (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, i.val + 1 < n →
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2
        (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) <
        (seq.get ⟨i.val + 1, by {rw [h_length]; sorry}⟩) := sorry
    
    theorem ulam_sequence_third_element (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      (ulamSequence u0 u1 n).get ⟨2, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 + u1 := sorry
    
    theorem ulam_sequence_unique_sum (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, 2 ≤ i.val → 
      ∃ (p : Nat × Nat), (∀ q : Nat × Nat,
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2
        p.1 < p.2 ∧ 
        p.2 < (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) ∧
        p.1 ∈ (List.take i.val seq) ∧ 
        p.2 ∈ (List.take i.val seq) ∧
        p.1 + p.2 = (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) ∧
        (q.1 < q.2 ∧ 
         q.2 < (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) ∧
         q.1 ∈ (List.take i.val seq) ∧ 

### 34. score 65 - specs/LF3983_specs.lean:28
- baseline rc: 0
- current: `(ulamSequence u0 u1 n).get ⟨2, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 + u1 := sorry`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: recent_implication_guard_may_not_be_visible

Window:

    theorem ulam_sequence_length (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) :
      List.length (ulamSequence u0 u1 n) = n := sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem ulam_sequence_first_elements (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ulamSequence u0 u1 n ≠ [] ∧
      (ulamSequence u0 u1 n).get ⟨0, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 ∧
      (ulamSequence u0 u1 n).get ⟨1, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u1 := sorry
    
    theorem ulam_sequence_strictly_increasing (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, i.val + 1 < n →
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2
        (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) <
        (seq.get ⟨i.val + 1, by {rw [h_length]; sorry}⟩) := sorry
    
    theorem ulam_sequence_third_element (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      (ulamSequence u0 u1 n).get ⟨2, by {rw [ulam_sequence_length u0 u1 n h1 h2]; sorry}⟩ = u0 + u1 := sorry
    
    theorem ulam_sequence_unique_sum (u0 u1 n : Nat) (h1: u0 > 0) (h2: u1 > u0) (h3: n ≥ 3) :
      ∀ i : Fin n, 2 ≤ i.val → 
      ∃ (p : Nat × Nat), (∀ q : Nat × Nat,
        let seq := ulamSequence u0 u1 n
        let h_length := ulam_sequence_length u0 u1 n h1 h2
        p.1 < p.2 ∧ 
        p.2 < (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) ∧
        p.1 ∈ (List.take i.val seq) ∧ 
        p.2 ∈ (List.take i.val seq) ∧
        p.1 + p.2 = (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) ∧
        (q.1 < q.2 ∧ 
         q.2 < (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) ∧
         q.1 ∈ (List.take i.val seq) ∧ 
         q.2 ∈ (List.take i.val seq) ∧
         q.1 + q.2 = (seq.get ⟨i.val, by {rw [h_length]; exact i.isLt}⟩) → 
         q = p)) := sorry

### 35. score 65 - specs/LT0009_specs.lean:23
- baseline rc: 0
- current: `(∀ i j : Fin n, i ≠ j → result.get ⟨i.val * n + j.val, sorry⟩ = 0)`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: recent_implication_guard_may_not_be_visible

Window:

    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def diagflat {n : Nat} (v : Vector Float n) : Id (Vector Float (n * n)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem diagflat_spec {n : Nat} (v : Vector Float n) :
        ⦃⌜True⌝⦄
        diagflat v
        ⦃⇓result => ⌜
          -- Elements on the main diagonal are from the input vector
          (∀ i : Fin n, result.get ⟨i.val * n + i.val, sorry⟩ = v.get i) ∧
          -- All other elements are zero
          (∀ i j : Fin n, i ≠ j → result.get ⟨i.val * n + j.val, sorry⟩ = 0)
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 36. score 65 - specs/LT0579_specs.lean:22
- baseline rc: 0
- current: `(∀ i : Fin n, products i = a.get ⟨k.val + i.val, by sorry⟩ * v.get i) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, arithmetic_index
- penalties: recent_implication_guard_may_not_be_visible

Window:

    open Std.Do
    -- </vc-preamble>
    
    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def correlate {m n : Nat} (a : Vector Float m) (v : Vector Float n) (h : n ≤ m) (h_pos : 0 < n) : Id (Vector Float (m + 1 - n)) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem correlate_spec {m n : Nat} (a : Vector Float m) (v : Vector Float n) (h : n ≤ m) (h_pos : 0 < n) :
        ⦃⌜n ≤ m ∧ 0 < n⌝⦄
        correlate a v h h_pos
        ⦃⇓result => ⌜-- Cross-correlation computation property: each output element is the sum of products
                     (∀ k : Fin (m + 1 - n), 
                       ∃ products : Fin n → Float,
                       (∀ i : Fin n, products i = a.get ⟨k.val + i.val, by sorry⟩ * v.get i) ∧
                       result.get k = (Vector.ofFn products).toList.sum) ∧
                     -- Boundary condition: all indices are valid for the computation
                     (∀ k : Fin (m + 1 - n), ∀ i : Fin n, k.val + i.val < m) ∧
                     -- Mathematical property: correlation is bilinear in its arguments
                     (∀ k : Fin (m + 1 - n), 
                       result.get k = (Vector.ofFn (fun i : Fin n => a.get ⟨k.val + i.val, by sorry⟩ * v.get i)).toList.sum) ∧
                     -- Non-negativity when both sequences are non-negative
                     ((∀ i : Fin m, 0 ≤ a.get i) ∧ (∀ i : Fin n, 0 ≤ v.get i) →
                       ∀ k : Fin (m + 1 - n), 0 ≤ result.get k)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 37. score 60 - specs/LT0326_specs.lean:25
- baseline rc: 0
- current: `(x.get k ≤ xp.get ⟨0, sorry⟩ → result.get k = fp.get ⟨0, sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, successor_bound_shape
- penalties: recent_implication_guard_may_not_be_visible

Window:

    -- <vc-helpers>
    -- </vc-helpers>
    
    -- <vc-definitions>
    def interp {n m : Nat} (x : Vector Float n) (xp : Vector Float (m + 1)) (fp : Vector Float (m + 1)) 
        (h_increasing : ∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j) : Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem interp_spec {n m : Nat} (x : Vector Float n) (xp : Vector Float (m + 1)) (fp : Vector Float (m + 1)) 
        (h_increasing : ∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j) :
        ⦃⌜∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j⌝⦄
        interp x xp fp h_increasing
        ⦃⇓result => ⌜
          -- Each interpolated value is computed correctly
          ∀ k : Fin n, 
            -- For points outside the left range, use left boundary value
            (x.get k ≤ xp.get ⟨0, sorry⟩ → result.get k = fp.get ⟨0, sorry⟩) ∧
            -- For points outside the right range, use right boundary value
            (x.get k ≥ xp.get ⟨m, sorry⟩ → result.get k = fp.get ⟨m, sorry⟩) ∧
            -- For points exactly at data points, return exact values
            (∀ i : Fin (m + 1), x.get k = xp.get i → result.get k = fp.get i) ∧
            -- For points within the range, value is between adjacent data points
            (∀ i : Fin m, 
              xp.get ⟨i.val, sorry⟩ ≤ x.get k ∧ x.get k ≤ xp.get ⟨i.val + 1, sorry⟩ →
              ∃ t : Float, 0 ≤ t ∧ t ≤ 1 ∧ 
              result.get k = fp.get ⟨i.val, sorry⟩ + t * (fp.get ⟨i.val + 1, sorry⟩ - fp.get ⟨i.val, sorry⟩))
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 38. score 60 - specs/LT0326_specs.lean:27
- baseline rc: 0
- current: `(x.get k ≥ xp.get ⟨m, sorry⟩ → result.get k = fp.get ⟨m, sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder, uses_Fin_val, successor_bound_shape
- penalties: recent_implication_guard_may_not_be_visible

Window:

    
    -- <vc-definitions>
    def interp {n m : Nat} (x : Vector Float n) (xp : Vector Float (m + 1)) (fp : Vector Float (m + 1)) 
        (h_increasing : ∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j) : Id (Vector Float n) :=
      sorry
    -- </vc-definitions>
    
    -- <vc-theorems>
    theorem interp_spec {n m : Nat} (x : Vector Float n) (xp : Vector Float (m + 1)) (fp : Vector Float (m + 1)) 
        (h_increasing : ∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j) :
        ⦃⌜∀ i j : Fin (m + 1), i < j → xp.get i < xp.get j⌝⦄
        interp x xp fp h_increasing
        ⦃⇓result => ⌜
          -- Each interpolated value is computed correctly
          ∀ k : Fin n, 
            -- For points outside the left range, use left boundary value
            (x.get k ≤ xp.get ⟨0, sorry⟩ → result.get k = fp.get ⟨0, sorry⟩) ∧
            -- For points outside the right range, use right boundary value
            (x.get k ≥ xp.get ⟨m, sorry⟩ → result.get k = fp.get ⟨m, sorry⟩) ∧
            -- For points exactly at data points, return exact values
            (∀ i : Fin (m + 1), x.get k = xp.get i → result.get k = fp.get i) ∧
            -- For points within the range, value is between adjacent data points
            (∀ i : Fin m, 
              xp.get ⟨i.val, sorry⟩ ≤ x.get k ∧ x.get k ≤ xp.get ⟨i.val + 1, sorry⟩ →
              ∃ t : Float, 0 ≤ t ∧ t ≤ 1 ∧ 
              result.get k = fp.get ⟨i.val, sorry⟩ + t * (fp.get ⟨i.val + 1, sorry⟩ - fp.get ⟨i.val, sorry⟩))
        ⌝⦄ := by
      sorry
    -- </vc-theorems>

### 39. score 55 - specs/LT0583_specs.lean:36
- baseline rc: 0
- current: `x_edges.get ⟨0, sorry⟩ ≤ x_min ∧ x_max ≤ x_edges.get ⟨nbins, sorry⟩ ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder
- penalties: 

Window:

        (h_bins_pos : bins > 0) (h_nbins_eq : nbins = bins) :
        ⦃⌜bins > 0⌝⦄
        histogram2d x y bins h_bins_pos h_nbins_eq
        ⦃⇓result => ⌜-- Destructure the result tuple
                     let (hist, x_edges, y_edges) := result
                     -- 1. All histogram values are non-negative
                     (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≥ 0) ∧
                     -- 2. Total count conservation: sum of all bins equals input length
                     (∃ total : Nat, 
                       (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≤ n) ∧
                       total = n) ∧
                     -- 3. Bin edges are monotonically increasing
                     (∀ i : Fin nbins, x_edges.get ⟨i, sorry⟩ < x_edges.get ⟨i + 1, sorry⟩) ∧
                     (∀ i : Fin nbins, y_edges.get ⟨i, sorry⟩ < y_edges.get ⟨i + 1, sorry⟩) ∧
                     -- 4. Bin edges span the data range appropriately
                     (∃ x_min x_max y_min y_max : Float,
                       (∀ i : Fin n, x_min ≤ x.get i ∧ x.get i ≤ x_max) ∧
                       (∀ i : Fin n, y_min ≤ y.get i ∧ y.get i ≤ y_max) ∧
                       x_edges.get ⟨0, sorry⟩ ≤ x_min ∧ x_max ≤ x_edges.get ⟨nbins, sorry⟩ ∧
                       y_edges.get ⟨0, sorry⟩ ≤ y_min ∧ y_max ≤ y_edges.get ⟨nbins, sorry⟩) ∧
                     -- 5. Histogram correctly partitions the data space
                     (∀ i : Fin nbins, ∀ j : Fin nbins,
                       ∀ k : Fin n,
                       let x_val := x.get k
                       let y_val := y.get k
                       let x_left := x_edges.get ⟨i, sorry⟩
                       let x_right := x_edges.get ⟨i + 1, sorry⟩  
                       let y_left := y_edges.get ⟨j, sorry⟩
                       let y_right := y_edges.get ⟨j + 1, sorry⟩
                       (x_left ≤ x_val ∧ x_val < x_right ∧ y_left ≤ y_val ∧ y_val < y_right) ∨
                       (i = nbins - 1 ∧ j = nbins - 1 ∧ x_val = x_right ∧ y_val = y_right) →
                       (hist.get i).get j ≥ 1)⌝⦄ := by
      sorry
    -- </vc-theorems>

### 40. score 55 - specs/LT0583_specs.lean:37
- baseline rc: 0
- current: `y_edges.get ⟨0, sorry⟩ ≤ y_min ∧ y_max ≤ y_edges.get ⟨nbins, sorry⟩) ∧`
- reasons: embedded_Vector_get_Fin_bound, nearby_Fin_binder
- penalties: 

Window:

        ⦃⌜bins > 0⌝⦄
        histogram2d x y bins h_bins_pos h_nbins_eq
        ⦃⇓result => ⌜-- Destructure the result tuple
                     let (hist, x_edges, y_edges) := result
                     -- 1. All histogram values are non-negative
                     (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≥ 0) ∧
                     -- 2. Total count conservation: sum of all bins equals input length
                     (∃ total : Nat, 
                       (∀ i : Fin nbins, ∀ j : Fin nbins, (hist.get i).get j ≤ n) ∧
                       total = n) ∧
                     -- 3. Bin edges are monotonically increasing
                     (∀ i : Fin nbins, x_edges.get ⟨i, sorry⟩ < x_edges.get ⟨i + 1, sorry⟩) ∧
                     (∀ i : Fin nbins, y_edges.get ⟨i, sorry⟩ < y_edges.get ⟨i + 1, sorry⟩) ∧
                     -- 4. Bin edges span the data range appropriately
                     (∃ x_min x_max y_min y_max : Float,
                       (∀ i : Fin n, x_min ≤ x.get i ∧ x.get i ≤ x_max) ∧
                       (∀ i : Fin n, y_min ≤ y.get i ∧ y.get i ≤ y_max) ∧
                       x_edges.get ⟨0, sorry⟩ ≤ x_min ∧ x_max ≤ x_edges.get ⟨nbins, sorry⟩ ∧
                       y_edges.get ⟨0, sorry⟩ ≤ y_min ∧ y_max ≤ y_edges.get ⟨nbins, sorry⟩) ∧
                     -- 5. Histogram correctly partitions the data space
                     (∀ i : Fin nbins, ∀ j : Fin nbins,
                       ∀ k : Fin n,
                       let x_val := x.get k
                       let y_val := y.get k
                       let x_left := x_edges.get ⟨i, sorry⟩
                       let x_right := x_edges.get ⟨i + 1, sorry⟩  
                       let y_left := y_edges.get ⟨j, sorry⟩
                       let y_right := y_edges.get ⟨j + 1, sorry⟩
                       (x_left ≤ x_val ∧ x_val < x_right ∧ y_left ≤ y_val ∧ y_val < y_right) ∨
                       (i = nbins - 1 ∧ j = nbins - 1 ∧ x_val = x_right ∧ y_val = y_right) →
                       (hist.get i).get j ≥ 1)⌝⦄ := by
      sorry
    -- </vc-theorems>

## Baseline top files

- `specs/LT0049_specs.lean` rc=0
- `specs/LT0420_specs.lean` rc=0
- `specs/LT0445_specs.lean` rc=0
- `specs/LF0093_specs.lean` rc=0
- `specs/LF3312_specs.lean` rc=1
- `specs/LT0009_specs.lean` rc=0
- `specs/LT0014_specs.lean` rc=0
- `specs/LT0056_specs.lean` rc=0
- `specs/LT0091_specs.lean` rc=0
- `specs/LT0151_specs.lean` rc=0
- `specs/LT0156_specs.lean` rc=0
- `specs/LT0171_specs.lean` rc=0
- `specs/LT0173_specs.lean` rc=0
- `specs/LT0579_specs.lean` rc=0
- `specs/LT0583_specs.lean` rc=0
- `specs/LF3983_specs.lean` rc=0
- `specs/LT0179_specs.lean` rc=0
- `specs/LT0326_specs.lean` rc=0
- `specs/LT0425_specs.lean` rc=0
- `specs/LT0450_specs.lean` rc=0