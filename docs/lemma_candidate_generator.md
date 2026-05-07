# Lemma Candidate Generator

Lemma candidates are proposed cuts. They are MathGraph's proof-shaping layer:
if many TRUE implications share a proof motif, MathGraph can propose a named
intermediate lemma that might compress that family.

Candidate status is advisory:

- `CANDIDATE` means a cut was proposed;
- `SKETCH_GENERATED` or `LEAN_ARTIFACT_GENERATED` means a skeleton exists;
- `LEAN_VERIFIED` means Lean verification was explicitly imported or recorded;
- failed/rejected/superseded candidates remain non-authoritative.

Repeated examples are not universal proof. A candidate lemma becomes proof
authority only after verifier-backed proof status is explicit.
