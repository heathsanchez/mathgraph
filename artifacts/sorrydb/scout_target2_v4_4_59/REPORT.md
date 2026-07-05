# SorryDB v4.4.59 — Target #2 Scout Report

## Why v4.4.59 Exists

v4.4.57 found no candidates because GitHub search qualifiers were malformed.
v4.4.58 still found no candidates because GitHub API was called as POST and returned 404.
v4.4.59 uses GitHub Search API GET.

## Selected Candidate

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law43.lean
- URL: https://github.com/teorth/equational_theories/blob/b1cc1756202d7f44e07bd4069b5df16901a36938/equational_theories/Definability/Law43.lean
- Toolchain: leanprover/lean4:v4.29.1
- Active sorry estimate: 1
- Line count: 31

## First Window

7: open Law.MagmaLaw
8: 
9: --TODO: the commutative law is definable from anything of the form f(x,y) ≃ f(y,x).
10: theorem Equation43_termDefinableFrom_swapped_args {L : NatMagmaLaw}
11:     (hL2args : ∀ e ∈ L.lhs.elems.1, e ∈ [0,1] := by decide +kernel)
12:     (hR2args : ∀ e ∈ L.rhs.elems.1, e ∈ [0,1] := by decide +kernel)
13:     (hSymm : L.lhs ⬝ (fun x ↦ Lf $ Equiv.swap 0 1 x) = L.rhs := by rfl)
14:     : Law43.TermDefinableFrom L := by
15:   sorry
16: 
17: /-- The commutative law 43 `x ◇ y = y ◇ x` is TermDefinable from 40 `x ◇ x = y ◇ y`. -/
18: theorem Equation43_termDefinableFrom_Equation40 : Law43.TermDefinableFrom Law40 :=
19:   Equation43_termDefinableFrom_swapped_args
20: 
21: /-- The commutative law 43 `x ◇ y = y ◇ x` is TermDefinable from 4343 `x ◇ (y ◇ y) = y ◇ (x ◇ x)`. -/
22: theorem Equation43_termDefinableFrom_Equation4343 : Law43.TermDefinableFrom Law4343 :=
23:   Equation43_termDefinableFrom_swapped_args
24: 
25: /-- The commutative law 43 `x ◇ y = y ◇ x` is TermDefinable from 4293 `x ◇ (x ◇ y) = y ◇ (y ◇ x)`. -/

## Decision

Next step: run pinned local replay/recon for the selected candidate, then classify as one of:

- READY_FOR_PATCH_EXPERIMENT
- COMMENT_ONLY_OR_FALSE_POSITIVE
- REPO_BOOTSTRAP_OBSTRUCTION
- TOO_LARGE_OR_BAD_TARGET
- SEARCH_FAILURE_NO_CANDIDATE
