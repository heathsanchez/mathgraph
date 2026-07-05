# SorryDB v4.4.64 — Law46 Patch004 hxy implicit-disjoint Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46

## Prior Accepted Partial

Patch002 accepted the first local sorry:

    obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := ...

## Patch004 Goal

Replace:

    have hxy : x ≠ y := sorry

using the exact Patch003 obstruction:

    hDisjoint : ∀ ⦃a : ℕ⦄, a ∈ ↑(Lf x).elems → a ∉ ↑(Lf y).elems

## Variant Results

- v01_rewrite_then_exact_hDisjoint_memberships: rc=1, seconds=41.92, error=True, warning=False
- v02_subst_then_exact_hDisjoint_memberships: rc=1, seconds=3.81, error=True, warning=False
- v03_apply_hDisjoint_then_memberships: rc=1, seconds=3.62, error=True, warning=False
- v04_have_notmem_then_apply: rc=1, seconds=2.78, error=True, warning=False
- v05_simpa_using_hDisjoint: rc=1, seconds=3.35, error=True, warning=False
- v06_no_rewrite_left_right_memberships_via_elems_spec: rc=1, seconds=2.88, error=True, warning=False
- v07_no_rewrite_apply_hDisjoint: rc=1, seconds=2.8, error=True, warning=False

## Status

PATCH004_REJECTED_OBSTRUCTION

## Accepted Variant

None

## Obstruction

## v01_rewrite_then_exact_hDisjoint_memberships
error: equational_theories/Definability/Law46.lean:30:16: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a (Lf x) }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:31:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:32:17: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a (Lf y) }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:33:8: Tactic `assumption` failed

L : NatMagmaLaw
hShape : (L.lhs ⬝ fun x ↦ Lf 0) = L.rhs ⬝ fun x ↦ Lf 0
x : ℕ
hlhs : L.lhs = Lf x
y : ℕ
error: equational_theories/Definability/Law46.lean:34:22: Unknown identifier `hx`
error: equational_theories/Definability/Law46.lean:34:25: Unknown identifier `hyx`
## v02_subst_then_exact_hDisjoint_memberships
error: equational_theories/Definability/Law46.lean:31:16: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a (Lf x) }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:32:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:33:22: Unknown identifier `hx`
error: equational_theories/Definability/Law46.lean:33:25: Unknown identifier `hx`
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v03_apply_hDisjoint_then_memberships
error: equational_theories/Definability/Law46.lean:31:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:32:8: Tactic `assumption` failed

case a
L : NatMagmaLaw
hShape : (L.lhs ⬝ fun x ↦ Lf 0) = L.rhs ⬝ fun x ↦ Lf 0
x : ℕ
hlhs : L.lhs = Lf x
error: equational_theories/Definability/Law46.lean:27:24: unsolved goals
case a
L : NatMagmaLaw
hShape : (L.lhs ⬝ fun x ↦ Lf 0) = L.rhs ⬝ fun x ↦ Lf 0
x : ℕ
hlhs : L.lhs = Lf x
y : ℕ
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46
## v04_have_notmem_then_apply
error: equational_theories/Definability/Law46.lean:30:16: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a (Lf x) }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:31:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:32:18: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a (Lf y) }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:32:49: Unknown identifier `hx`
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v05_simpa_using_hDisjoint
error: equational_theories/Definability/Law46.lean:30:16: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a (Lf x) }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:31:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:32:18: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a (Lf y) }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:32:49: Unknown identifier `hx`
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

error: build failed
## v06_no_rewrite_left_right_memberships_via_elems_spec
error: equational_theories/Definability/Law46.lean:29:16: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a L.lhs }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:30:12: Tactic `rewrite` failed: motive is not type correct:
  fun _a ↦ x ∈ _a.elems
Error: Application type mismatch: The argument
  ?refine_1
has type
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a L.lhs }
but is expected to have type
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a _a }
in the application
error: equational_theories/Definability/Law46.lean:32:17: failed to synthesize instance of type class
  Membership ℕ { l // l.Nodup ∧ ∀ (a : ℕ), a ∈ l ↔ FreeMagma.Mem a L.rhs }

Hint: Type class instance resolution failures can be inspected with the `set_option trace.Meta.synthInstance true` command.
error: equational_theories/Definability/Law46.lean:33:12: Tactic `rewrite` failed: motive is not type correct:
## v07_no_rewrite_apply_hDisjoint
error: equational_theories/Definability/Law46.lean:31:8: `simp` made no progress
error: equational_theories/Definability/Law46.lean:33:8: Tactic `assumption` failed

case a
L : NatMagmaLaw
hShape : (L.lhs ⬝ fun x ↦ Lf 0) = L.rhs ⬝ fun x ↦ Lf 0
hDisjoint : (↑L.lhs.elems).Disjoint ↑L.rhs.elems
x : ℕ
error: equational_theories/Definability/Law46.lean:27:24: unsolved goals
case a
L : NatMagmaLaw
hShape : (L.lhs ⬝ fun x ↦ Lf 0) = L.rhs ⬝ fun x ↦ Lf 0
hDisjoint : (↑L.lhs.elems).Disjoint ↑L.rhs.elems
x : ℕ
hlhs : L.lhs = Lf x
error: Lean exited with code 1
Some required targets logged failures:
- equational_theories.Definability.Law46

## Next Move

If accepted, carry Patch002 + Patch004 forward and attack:

    rw [show L = Lf x ≃ Lf y from sorry]

If rejected, inspect membership simplification for `↑(Lf x).elems` and use the subtype field behind `elems`.
