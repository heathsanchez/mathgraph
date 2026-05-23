# Artifact Contract

MathGraph separates routing artifacts from terminal artifacts.

## Terminal Or Candidate Terminal Artifacts

- `VERIFIED_PROOF`: a proof accepted by a proof checker, trusted importer, or
  chain audit boundary.
- `FINITE_COUNTERMODEL`: a concrete finite witness checked by the finite model
  checker.
- `REFUTATION_CERTIFICATE`: compatibility vocabulary for a boundary-backed
  refutation candidate, usually represented as a finite countermodel in the
  Lawbook.
- `NAMED_OBSTRUCTION`: a structured obstruction record with scoped evidence.

These artifacts may enter terminal Lawbook paths only through
`lawbook_boundary.evaluate_lawbook_admission` or an equivalent existing
PromotionGate/Lawbook acceptance path.

## Advisory And Diagnostic Artifacts

- advisory route laws
- Reason Atlas entries
- H-Tilt scores
- Lawbook attention hits
- residual diagnostics
- failed verifier attempts
- model or agent traces

These may guide scheduling, retrieval, explanations, or future verifier work.
They cannot promote truth.

## Boundary Rules

- Failed finite search is never `TRUE`.
- Raw success text is not boundary evidence.
- Route priority is not proof.
- Reason Atlas support count is not proof.
- H-Tilt mass is not proof.
- Lawbook attention is retrieval, not verification.

New ingestion code should call `mathgraph.lawbook_boundary` before writing a
terminal or candidate terminal Lawbook artifact.
