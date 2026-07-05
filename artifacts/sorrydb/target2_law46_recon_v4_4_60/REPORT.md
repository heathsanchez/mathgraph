# SorryDB v4.4.60 — Target #2 Law46 Recon Report

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law46.lean
- Module: equational_theories.Definability.Law46
- Toolchain: leanprover/lean4:v4.29.1
- Active sorry estimate: 7
- Line count: 74

## Why This Target

Law43 was already solved by MathGraph and is open as PR #1461. Law46 is the next high-value candidate in the same repo and same definability namespace.

## Baseline Judgment

- cache_get_returncode: 0
- baseline_build_returncode: 0
- seconds: 126.91

## First Sorry Window

9: /-- The constant law 46 `x ◇ y = z ◇ w` is TermDefinable from any law `lhs = rhs`, where
10: lhs and rhs are the same shape, but with disjoint sets of variables. -/
11: theorem Equation46_termDefinableFrom_equalShape {L : NatMagmaLaw}
12:   (hShape : L.lhs ⬝ (fun _ ↦ Lf 0) = L.rhs ⬝ (fun _ ↦ Lf 0) := by rfl)
13:   (hDisjoint : L.lhs.elems.val.Disjoint L.rhs.elems := by rw [List.Disjoint]; decide +kernel)
14:   : Law46.TermDefinableFrom L := by
15:   --There are two cases: there is at least one function application, or both sides of L are leaves.
16:   cases hlhs : L.lhs
17:   next x =>
18:     --In this case, the law is of the form x = y. Thus, it is (equivalent to) equation 2
19:     obtain ⟨y,hy⟩ : ∃ y, L.rhs = Lf y := sorry
20:     have hxy : x ≠ y := sorry
21:     rw [show L = Lf x ≃ Lf y from sorry]
22:     clear hlhs hy hShape hDisjoint
23:     apply termDefinable_of_termStructural
24:     apply termStructural_of_implies
25:     have : (Lf x ≃ Lf y).toFin.toNat = Law2 := by
26:       -- have h₁ : (Lf x ≃ Lf y : NatMagmaLaw).elems.1 = [x,y] := by
27:       --   sorry
28:       -- have h₂ : Fin ((Lf x ≃ Lf y : NatMagmaLaw).elems).1.length = Fin 2 := by
29:       --   rw [h₁]
30:       --   simp
31:       -- simp [toFin, h₁]

## Classification

READY_FOR_PATCH_EXPERIMENT

## Next Move

Start with the first leaf-case sorry in `Equation46_termDefinableFrom_equalShape`, then mine the local API around:

- `NatMagmaLaw`
- `FreeMagma`
- `MagmaLaw.elems`
- `List.Disjoint`
- `termDefinable_of_termStructural`
- `termStructural_of_implies`
- `toFin`
- `Law2`
