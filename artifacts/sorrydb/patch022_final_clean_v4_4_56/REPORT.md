# SorryDB v4.4.56 — Clean Lean Sorry Repair

## Target

- Repository: teorth/equational_theories
- Commit: b1cc1756202d7f44e07bd4069b5df16901a36938
- File: equational_theories/Definability/Law43.lean
- Theorem: Equation43_termDefinableFrom_swapped_args

## Result

A previously active sorry was replaced by a complete Lean proof.

## Verification

Command:

    lake build equational_theories.Definability.Law43

Result:

    Build completed successfully (993 jobs).

Checks:

- ok: true
- returncode: 0
- no_sorry_warning: true
- no_unused_warning: true

## Artifacts

- final_Law43.patch — upstream-ready patch
- accepted_Law43.lean — full accepted Lean file
- patch022_judgment.json — verifier judgment
- lawbook_entry.json — machine-readable MathGraph lawbook entry

## MathGraph Route

Residual:

- Active sorry in a real Lean 4 repository.

Obstruction ladder:

- Constructor shape mismatch.
- Implicit argument mismatch.
- satisfiesPhi unfolding mismatch.
- substitution/evaluation rewrite mismatch.
- TermDefinable witness realization mismatch.
- unused variable warning.

Portal:

- Construct new magma operation by evaluating L.lhs under two arguments.
- Use hSymm plus FreeMagma.SubstEval.
- Prove evaluation equality by variable-occurrence membership.
- Realize term witness through Term.realize_subst and FreeMagma.toTerm_realize.

Certificate:

- lake build equational_theories.Definability.Law43 accepted with no sorry or unused-variable warnings.

Status:

- Ready for upstream PR when desired.


## Upstream PR

- PR: https://github.com/teorth/equational_theories/pull/1461
- Status: Ready for review
- Fork branch: `heathsanchez:fix-law43-term-definable-from-swapped-args`
- Upstream repair commit: `173e39d0`
