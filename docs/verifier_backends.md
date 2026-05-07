# Verifier Backends

`VerifierBackendProfile` describes proof finders, model finders, certificate
checkers, importers, exporters, chain auditors, and advisory analyzers.

Backends can support proofs, models, replayable artifacts, or native domain
checking. Metadata-only placeholders exist for Lean and Isabelle tools; this
repo does not execute those tools yet.

Backend result records preserve the truth boundary:

- proof found is only authoritative with safe trust and a replayable proof
  artifact;
- no proof found is not refutation;
- model found is a refutation candidate until replayed/verified;
- no model found is not proof.
