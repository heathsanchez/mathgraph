# MathGraph Next Implementable Layer

This layer adds closed, testable infrastructure that is ready now. It does not
attempt unresolved research problems, and it does not change MathGraph's truth
boundary.

## What Was Added

1. **Terminal schema compatibility**: `mathgraph.terminal_schema` maps legacy
   terminal vocabulary into a canonical proof/refutation/obstruction schema.
2. **External certificate envelope**: `mathgraph.external_certificates` records
   outputs from Lean, Coq, Isabelle, Z3, CVC5, MiniSAT, finite checkers, and
   other tools as advisory objects until replayed or revalidated.
3. **Closed verification loop**: `mathgraph.closed_loop` connects pending pairs,
   route outcomes, the existing route learner, and the H-Tilt scheduler.
4. **Smoothed route prior**: `mathgraph.route_priors` avoids sparse-data route
   collapse with smoothing, exploration mass, and entropy flooring.
5. **Causal IR**: `mathgraph.causal_ir` adds explicit causal claim records and
   conservative obstruction hooks.
6. **Grounding IR**: `mathgraph.grounding` records continuous-to-symbolic
   grounding attempts as advisory denotation payloads.

## Truth Boundary

Models propose. MathGraph constrains. Verifiers decide. The Lawbook remembers.
Projection scales.

Advisory artifacts cannot promote truth. External certificates, causal checks,
grounding records, route priors, and closed-loop scheduling pressure remain
advisory unless a verifier, trusted importer, finite validator, or chain audit
creates explicit boundary evidence.

## Deferred Research Hooks

The following are intentionally not implemented here:

- principled `V` discovery
- abstraction formation law
- portable survivor geometry
- one-channel emergence law
- real do-calculus
- real sensor grounding
- learned proof constructor synthesis

Those should remain research hooks until they can be encoded as small,
auditable, verifier-bound components.

## Contact Promotion Follow-On

The next implementable layer after the advisory/control-plane work is Reason
Atlas contact promotion. It turns Lean probe rows into:

- `STRICT_CONTACT_SEED`
- `SIGNATURE_ATLAS_RECORD`
- `REPAIRABLE_OBSTRUCTION`
- `TRANSFER_TEST`
- `PROMOTED_ROUTE_LAW`
- `NEXT_EXPANSION_QUEUE`

A single clean contact remains a seed. MathGraph promotes a route law only
after repeated clean transfer across compatible declarations or target
instantiations. Promoted route laws are advisory scheduling and construction
guides, not proof certificates.

## Root Operator Induction

The next implemented layer lifts repeated verified trace survivals into typed,
parameterized root operator schemas. Literal macros remain useful examples, but
schemas such as `move(axis, distance=2); recolor(color)` are the reusable
constructor candidates that can compress residual families and close part of an
oracle gap.

Root operator schemas are still advisory. They guide proof search, program
synthesis, countermodel search, constructor selection, and route scheduling;
they do not emit `VERIFIED_PROOF`, `REFUTATION_CERTIFICATE`, `TRUE`, or `FALSE`.

## Reason Atlas Persistence And Feedback

Reason Atlas persistence is now implemented as the compounding memory layer for
advisory structures. Promoted contacts, root operator schemas, constructor
hints, and repairable obstructions can be stored in SQLite, receive transfer and
verifier feedback, rescore priorities, and emit next advisory queue rows.

## Closed Verification Loop And Promotion Gate

The current implemented bridge connects advisory Reason Atlas queue rows to
verifier-bound Lawbook candidates through a central `PromotionGate`.
`ExternalCertificate` objects can carry proposed terminal forms and boundary
evidence, but they remain advisory until the gate confirms a valid verifier,
trusted-importer, finite-validator, or chain-audit boundary.

The callback-based closed verification loop can run in smoke tests without Lean:
it consumes advisory queue rows, calls a verifier callback, gates the resulting
certificate, records feedback in the Reason Atlas, rescales priorities, and
exports the next advisory queue.

## Breakthrough Loop Demo

The first functioning metabolism is now implemented in
`mathgraph.breakthrough_loop`. It runs unresolved finite magma implication
tasks through advisory constructor hints, evaluates concrete finite tables with
a deterministic checker, wraps successful refutations as `ExternalCertificate`
objects, gates them through `PromotionGate`, records failures as Reason Atlas
feedback, and uses the rescored queue in later episodes.

The demo is small but semantic: accepted certificates include a finite magma
table and witness environment proving that the source equation holds globally
and the target equation fails. Failed searches remain residual feedback, not
truth.

## SAIR Breakthrough Loop

The same metabolism now has a SAIR-compatible runner. When `equations.txt` and
`etp_matrix_full_best_bool.npy` are available, MathGraph samples matrix-labeled
FALSE pairs, normalizes SAIR binary-operation syntax, tries finite magma
constructor banks, and admits only checker-validated finite countermodels
through `PromotionGate`. If the files are absent, the runner falls back to the
built-in breakthrough corpus.

## SAIR Motif Hygiene And Held-Out Scheduler Evaluation

The immediate empirical validation layer now cleans real-corpus SAIR
finite-countermodel traces into mechanism-only atoms, mines advisory constructor
motifs only from `PromotionGate`-accepted traces, and evaluates motif-guided
scheduling on held-out pairs with the real finite checker. The result is no
longer "motifs exist"; it is certificate yield and residual compression versus
baseline constructor scheduling.

Implemented:

- Reason Atlas Contact Promotion
- Root Operator Induction
- Reason Atlas Persistence + Feedback Loop
- Closed Verification Loop + Promotion Gate
- Breakthrough Loop Demo
- SAIR Breakthrough Loop
- SAIR Motif Hygiene + Held-Out Scheduler Evaluation

Still future work:

- real Lean/finite-checker job runner integration
- H-Tilt scheduling over persistent schema families
- finite countermodel root induction
- proof-constructor root induction
- second-order root operators
- principled V discovery
- causal IR
- grounding IR
- multi-verifier external certificate envelope
