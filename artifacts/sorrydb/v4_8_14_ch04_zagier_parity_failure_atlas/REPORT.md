# MathGraph SorryDB v4.8.14 — Chapter04 Zagier Parity Failure Atlas

## Target

    theorem trivialInvo_fixedPoints : (fixedPoints (trivialInvo k)).Nonempty

## Current status

No certified proof yet. v4.8.13 correctly rejected all variants under the no-sorry gate.

## Hypothesis

The portal is still likely correct: compare fixed-point parity of `trivialInvo` and `secondInvo`. The failure is probably one of:

1. proving `trivialInvo k ^ 2 = 1` in the right normal form;
2. coercion/type mismatch for `Equiv.Perm.card_fixedPoints_modEq`;
3. needing exact `Set.not_nonempty_iff_eq_empty` / `Fintype.card_eq_zero` rewriting shape.

## Variant errors

### v01_zagier_exact_shape

Key errors:

- `error: FormalBook/Chapter_04.lean:289:40: unsolved goals`
- `error: FormalBook/Chapter_04.lean:295:57: Application type mismatch: The argument`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

      simp only [̵ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵t̵r̵u̵e̵_̵a̵n̵d̵]̵[̲S̲u̲b̲t̲y̲p̲e̲.̲m̲k̲.̲i̲n̲j̲E̲q̲,̲ ̲P̲r̲o̲d̲.̲m̲k̲.̲i̲n̲j̲E̲q̲]̲ at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    error: FormalBook/Chapter_04.lean:289:40: unsolved goals
    case h.a.a.fst
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    x : ℤ × ℤ × ℤ
    y : 4 * x.1 * x.2.1 + x.2.2 ^ 2 = 4 * ↑k + 1
    z : x.1 > 0 ∧ x.2.1 > 0
    hT : ⟨x, ⋯⟩ ∈ T k
    ⊢ (↑↑(match
                match ⟨⟨x, ⋯⟩, hT⟩ with
                | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩ with
              | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩)).1 =
        x.1
    
    case h.a.a.snd.fst
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    x : ℤ × ℤ × ℤ
    y : 4 * x.1 * x.2.1 + x.2.2 ^ 2 = 4 * ↑k + 1
    z : x.1 > 0 ∧ x.2.1 > 0
    hT : ⟨x, ⋯⟩ ∈ T k
    ⊢ (↑↑(match
                  match ⟨⟨x, ⋯⟩, hT⟩ with
                  | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩ with
                | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩)).2.1 =
        x.2.1
    
    case h.a.a.snd.snd
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    x : ℤ × ℤ × ℤ
    y : 4 * x.1 * x.2.1 + x.2.2 ^ 2 = 4 * ↑k + 1
    z : x.1 > 0 ∧ x.2.1 > 0
    hT : ⟨x, ⋯⟩ ∈ T k
    ⊢ (↑↑(match
                  match ⟨⟨x, ⋯⟩, hT⟩ with
                  | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩ with
                | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩)).2.2 =
        x.2.2
    error: FormalBook/Chapter_04.lean:295:57: Application type mismatch: The argument
      secondInvo_sq k
    has type
      secondInvo k ^ 2 = 1
    but is expected to have type
      ?m.139 ^ 2 ^ 1 = 1
    in the application
      Equiv.Perm.card_fixedPoints_modEq (secondInvo_sq k)
    info: FormalBook/Chapter_04.lean:332:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v02_zagier_with_fixedpoints_empty

Key errors:

- `error: FormalBook/Chapter_04.lean:289:40: unsolved goals`
- `error: FormalBook/Chapter_04.lean:295:57: Application type mismatch: The argument`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

    
    Hint: Omit it from the simp argument list.
      simp only [secondInvo, secondInvo_fun, sub_sub_cancel, id_eq, Subtype.mk.injEq, Prod.mk.injEq,̵
      ̵ ̵ ̵ ̵ ̵a̵n̵d̵_̵t̵r̵u̵e̵]
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:232:8: declaration uses 'sorry'
    warning: FormalBook/Chapter_04.lean:247:8: declaration uses 'sorry'
    warning: FormalBook/Chapter_04.lean:270:14: This simp argument is unused:
      Subtype.mk.injEq
    
    Hint: Omit it from the simp argument list.
      simp only [ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵Prod.mk.injEq, true_and] at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:270:32: This simp argument is unused:
      Prod.mk.injEq
    
    Hint: Omit it from the simp argument list.
      simp only [̵ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵[̲S̲u̲b̲t̲y̲p̲e̲.̲m̲k̲.̲i̲n̲j̲E̲q̲,̲ true_and] at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:270:47: This simp argument is unused:
      true_and
    
    Hint: Omit it from the simp argument list.
      simp only [̵ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵t̵r̵u̵e̵_̵a̵n̵d̵]̵[̲S̲u̲b̲t̲y̲p̲e̲.̲m̲k̲.̲i̲n̲j̲E̲q̲,̲ ̲P̲r̲o̲d̲.̲m̲k̲.̲i̲n̲j̲E̲q̲]̲ at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    error: FormalBook/Chapter_04.lean:289:40: unsolved goals
    case h
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    x : ℤ × ℤ × ℤ
    y : 4 * x.1 * x.2.1 + x.2.2 ^ 2 = 4 * ↑k + 1
    z : x.1 > 0 ∧ x.2.1 > 0
    hT : ⟨x, ⋯⟩ ∈ T k
    ⊢ (match
          match ⟨⟨x, ⋯⟩, hT⟩ with
          | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩ with
        | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩) =
        ⟨⟨x, ⋯⟩, hT⟩
    error: FormalBook/Chapter_04.lean:295:57: Application type mismatch: The argument
      secondInvo_sq k
    has type
      secondInvo k ^ 2 = 1
    but is expected to have type
      ?m.115 ^ 2 ^ 1 = 1
    in the application
      Equiv.Perm.card_fixedPoints_modEq (secondInvo_sq k)
    info: FormalBook/Chapter_04.lean:332:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v03_zagier_no_ext

Key errors:

- `error: FormalBook/Chapter_04.lean:290:4: Tactic `rfl` failed: The left-hand side`
- `error: FormalBook/Chapter_04.lean:292:57: Application type mismatch: The argument`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

      ̵ ̵ ̵ ̵ ̵and_true]
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:211:4: This simp argument is unused:
      and_true
    
    Hint: Omit it from the simp argument list.
      simp only [secondInvo, secondInvo_fun, sub_sub_cancel, id_eq, Subtype.mk.injEq, Prod.mk.injEq,̵
      ̵ ̵ ̵ ̵ ̵a̵n̵d̵_̵t̵r̵u̵e̵]
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:232:8: declaration uses 'sorry'
    warning: FormalBook/Chapter_04.lean:247:8: declaration uses 'sorry'
    warning: FormalBook/Chapter_04.lean:270:14: This simp argument is unused:
      Subtype.mk.injEq
    
    Hint: Omit it from the simp argument list.
      simp only [ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵Prod.mk.injEq, true_and] at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:270:32: This simp argument is unused:
      Prod.mk.injEq
    
    Hint: Omit it from the simp argument list.
      simp only [̵ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵[̲S̲u̲b̲t̲y̲p̲e̲.̲m̲k̲.̲i̲n̲j̲E̲q̲,̲ true_and] at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:270:47: This simp argument is unused:
      true_and
    
    Hint: Omit it from the simp argument list.
      simp only [̵ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵t̵r̵u̵e̵_̵a̵n̵d̵]̵[̲S̲u̲b̲t̲y̲p̲e̲.̲m̲k̲.̲i̲n̲j̲E̲q̲,̲ ̲P̲r̲o̲d̲.̲m̲k̲.̲i̲n̲j̲E̲q̲]̲ at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    error: FormalBook/Chapter_04.lean:290:4: Tactic `rfl` failed: The left-hand side
      trivialInvo k ^ 2
    is not definitionally equal to the right-hand side
      1
    
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ trivialInvo k ^ 2 = 1
    error: FormalBook/Chapter_04.lean:292:57: Application type mismatch: The argument
      secondInvo_sq k
    has type
      secondInvo k ^ 2 = 1
    but is expected to have type
      ?m.54 ^ 2 ^ 1 = 1
    in the application
      Equiv.Perm.card_fixedPoints_modEq (secondInvo_sq k)
    info: FormalBook/Chapter_04.lean:329:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v04_add_import_archive_pattern

Key errors:

- `error: FormalBook/Chapter_04.lean:289:40: unsolved goals`
- `error: FormalBook/Chapter_04.lean:295:57: Application type mismatch: The argument`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:270:47: This simp argument is unused:
      true_and
    
    Hint: Omit it from the simp argument list.
      simp only [̵ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵t̵r̵u̵e̵_̵a̵n̵d̵]̵[̲S̲u̲b̲t̲y̲p̲e̲.̲m̲k̲.̲i̲n̲j̲E̲q̲,̲ ̲P̲r̲o̲d̲.̲m̲k̲.̲i̲n̲j̲E̲q̲]̲ at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    error: FormalBook/Chapter_04.lean:289:40: unsolved goals
    case h
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    x : ℤ × ℤ × ℤ
    y : 4 * x.1 * x.2.1 + x.2.2 ^ 2 = 4 * ↑k + 1
    z : x.1 > 0 ∧ x.2.1 > 0
    hT : ⟨x, ⋯⟩ ∈ T k
    ⊢ (match
          match ⟨⟨x, ⋯⟩, hT⟩ with
          | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩ with
        | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩) =
        ⟨⟨x, ⋯⟩, hT⟩
    error: FormalBook/Chapter_04.lean:295:57: Application type mismatch: The argument
      secondInvo_sq k
    has type
      secondInvo k ^ 2 = 1
    but is expected to have type
      ?m.115 ^ 2 ^ 1 = 1
    in the application
      Equiv.Perm.card_fixedPoints_modEq (secondInvo_sq k)
    warning: FormalBook/Chapter_04.lean:293:35: This simp argument is unused:
      Subtype.mk.injEq
    
    Hint: Omit it from the simp argument list.
      simp only [trivialInvo, id_eq, S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵Prod.mk.injEq, and_true]
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:293:53: This simp argument is unused:
      Prod.mk.injEq
    
    Hint: Omit it from the simp argument list.
      simp only [trivialInvo, id_eq, Subtype.mk.injEq, P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵and_true]
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:293:68: This simp argument is unused:
      and_true
    
    Hint: Omit it from the simp argument list.
      simp only [trivialInvo, id_eq, Subtype.mk.injEq, Prod.mk.injEq,̵ ̵a̵n̵d̵_̵t̵r̵u̵e̵]
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    info: FormalBook/Chapter_04.lean:332:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed
