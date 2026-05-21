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
