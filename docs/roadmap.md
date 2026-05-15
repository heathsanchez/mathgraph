# Roadmap

## Current Architecture

```text
Domain Claim
  -> Continuation Actions
  -> Continuation Curriculum
  -> Verification Episode
  -> Verifier / Importer / Finite Validator / Chain Audit
  -> Proof Digestion
  -> Verifier Feedback / Repair
  -> Discovery Value
  -> Lawbook Acceptance
  -> Projection
  -> Telemetry
```

## Implemented / In Progress

1. Stabilize the core terminal-form contract.
2. Expand the finite magma adapter for SAIR Stage 2 experiments.
3. Add import/export formats for small verification traces.
4. Integrate formal verifier routes behind certificate validation.
5. Add Lean proof certificate ingestion without committing build outputs.
6. M6.9 Continuation Curriculum Builder: implemented as advisory staged work.
7. M6.10 Discovery Value Evaluator and Digestion-Aware Route Scoring:
   implemented as advisory scheduling pressure.
8. M6.11 Lawbook Hardening and Accepted Assimilation Boundary: implemented as
   the explicit accepted public-memory boundary.
9. M6.11.1 Public Surface / Terminology Hardening: implemented.
10. M6.12 Lawbook-Backed Query API and Known-Skip Service: implemented/in
    progress as read-only accepted-memory lookup.

## Future Work

- M6.13 Structural Identity and Canonicalization
- M6.14 Habit Rules and Route Promotion
- M6.15 Reason Compression
- M6.16 Process Memory
- richer formal-world adapters
- deeper proof-system integration
- semantic and natural-language claim handling with strict boundaries
- API service hardening
- existential agents

Only verifier/importer/finite-validation/chain-audit boundaries promote truth.
