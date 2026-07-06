# MathGraph SorryDB v4.8.12 — Chapter04 trivialInvo Failure Atlas

## Purpose

Classify why the no-sorry variants for `trivialInvo_fixedPoints` failed before spending another build.

## Target

    theorem trivialInvo_fixedPoints : (fixedPoints (trivialInvo k)).Nonempty

## Variant errors

### v01_card_pos_from_odd

Key errors:

- `error: FormalBook/Chapter_04.lean:289:2: Tactic `apply` failed: could not unify the conclusion of `Fintype.card_pos_iff.mp``
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

    
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
    error: FormalBook/Chapter_04.lean:289:2: Tactic `apply` failed: could not unify the conclusion of `Fintype.card_pos_iff.mp`
      Nonempty ?m.17
    with the goal
      (fixedPoints (trivialInvo k)).Nonempty
    
    Note: The full type of `Fintype.card_pos_iff.mp` is
      0 < Fintype.card ?m.17 → Nonempty ?m.17
    
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ (fixedPoints (trivialInvo k)).Nonempty
    info: FormalBook/Chapter_04.lean:327:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v02_by_contra_no_fixedpoints

Key errors:

- `error: FormalBook/Chapter_04.lean:291:39: Application type mismatch: The argument`
- `error: FormalBook/Chapter_04.lean:293:2: omega could not prove the goal:`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

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
    error: FormalBook/Chapter_04.lean:291:39: Application type mismatch: The argument
      h
    has type
      ¬(fixedPoints (trivialInvo k)).Nonempty
    but is expected to have type
      IsEmpty ↑(fixedPoints (trivialInvo k))
    in the application
      Fintype.card_eq_zero_iff.mpr h
    error: FormalBook/Chapter_04.lean:293:2: omega could not prove the goal:
    No usable constraints found. You may need to unfold definitions so `omega` can see linear arithmetic facts about `Nat` and `Int`, which may also involve multiplication, division, and modular remainder by constants.
    info: FormalBook/Chapter_04.lean:326:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v03_apply_card_pos

Key errors:

- `error: FormalBook/Chapter_04.lean:289:6: Tactic `rewrite` failed: Did not find an occurrence of the pattern`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

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
    error: FormalBook/Chapter_04.lean:289:6: Tactic `rewrite` failed: Did not find an occurrence of the pattern
      Nonempty ?m.17
    in the target expression
      (fixedPoints (trivialInvo k)).Nonempty
    
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ (fixedPoints (trivialInvo k)).Nonempty
    info: FormalBook/Chapter_04.lean:324:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v04_use_classical_choice

Key errors:

- `error: FormalBook/Chapter_04.lean:287:76: unsolved goals`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

    
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
    error: FormalBook/Chapter_04.lean:287:76: unsolved goals
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ {x | IsFixedPt (trivialInvo k) x}.Nonempty
    warning: FormalBook/Chapter_04.lean:289:21: This simp argument is unused:
      trivialInvo
    
    Hint: Omit it from the simp argument list.
      simp [fixedPoints,̵ ̵t̵r̵i̵v̵i̵a̵l̵I̵n̵v̵o̵]
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    info: FormalBook/Chapter_04.lean:322:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v05_extract_candidate_k11

Key errors:

- `error: FormalBook/Chapter_04.lean:295:6: No goals to be solved`
- `error: FormalBook/Chapter_04.lean:297:2: unsolved goals`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

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
    error: FormalBook/Chapter_04.lean:295:6: No goals to be solved
    error: FormalBook/Chapter_04.lean:297:2: unsolved goals
    case hx
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ (match ⟨⟨(↑k, 1, 1), ⋯⟩, ⋯⟩ with
        | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩) =
        ⟨⟨(↑k, 1, 1), ⋯⟩, ⋯⟩
    info: FormalBook/Chapter_04.lean:331:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v06_extract_candidate_k11_ext

Key errors:

- `error: FormalBook/Chapter_04.lean:293:4: No goals to be solved`
- `error: FormalBook/Chapter_04.lean:294:2: unsolved goals`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    warning: FormalBook/Chapter_04.lean:270:47: This simp argument is unused:
      true_and
    
    Hint: Omit it from the simp argument list.
      simp only [̵ ̵S̵u̵b̵t̵y̵p̵e̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵P̵r̵o̵d̵.̵m̵k̵.̵i̵n̵j̵E̵q̵,̵ ̵t̵r̵u̵e̵_̵a̵n̵d̵]̵[̲S̲u̲b̲t̲y̲p̲e̲.̲m̲k̲.̲i̲n̲j̲E̲q̲,̲ ̲P̲r̲o̲d̲.̲m̲k̲.̲i̲n̲j̲E̲q̲]̲ at hf
    
    Note: This linter can be disabled with `set_option linter.unusedSimpArgs false`
    error: FormalBook/Chapter_04.lean:293:4: No goals to be solved
    error: FormalBook/Chapter_04.lean:294:2: unsolved goals
    case hf.a.a.fst
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ (↑↑(match ⟨⟨(↑k, 1, 1), ⋯⟩, ⋯⟩ with
              | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩)).1 =
        ↑k
    
    case hf.a.a.snd.fst
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ (↑↑(match ⟨⟨(↑k, 1, 1), ⋯⟩, ⋯⟩ with
                | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩)).2.1 =
        1
    
    case hf.a.a.snd.snd
    k : ℕ
    hk : Fact (Nat.Prime (4 * k + 1))
    ⊢ (↑↑(match ⟨⟨(↑k, 1, 1), ⋯⟩, ⋯⟩ with
                | ⟨⟨(x, y, z), ⋯⟩, hz⟩ => ⟨⟨(y, x, z), ⋯⟩, hz⟩)).2.2 =
        1
    info: FormalBook/Chapter_04.lean:328:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed

### v07_candidate_k11_aesop

Key errors:

- `error: FormalBook/Chapter_04.lean:293:4: No goals to be solved`
- `error: FormalBook/Chapter_04.lean:295:4: tactic 'aesop' failed, made no progress`
- `error: Lean exited with code 1`
- `error: build failed`

Tail excerpt:

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
    error: FormalBook/Chapter_04.lean:293:4: No goals to be solved
    error: FormalBook/Chapter_04.lean:295:4: tactic 'aesop' failed, made no progress
    Initial goal:
      case hf
      k : ℕ
      hk : Fact (Nat.Prime (4 * k + 1))
      ⊢ trivialInvo k ⟨⟨(↑k, 1, 1), ⋯⟩, ⋯⟩ = ⟨⟨(↑k, 1, 1), ⋯⟩, ⋯⟩
    info: FormalBook/Chapter_04.lean:328:0: (2, 5, 6)
    error: Lean exited with code 1
    Some required targets logged failures:
    - FormalBook.Chapter_04
    error: build failed
