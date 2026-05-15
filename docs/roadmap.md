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
8. M6.11 Lawbook Hardening and Accepted Assimilation Boundary: implemented/in
   progress as the explicit accepted public-memory boundary.

## Future Work

- richer formal-world adapters
- deeper proof-system integration
- semantic and natural-language claim handling with strict boundaries
- lawbook-backed API service
- existential agents

Only verifier/importer/finite-validation/chain-audit boundaries promote truth.
