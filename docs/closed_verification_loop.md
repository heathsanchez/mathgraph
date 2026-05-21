# Closed Verification Loop

MathGraph now has a narrow bridge from advisory Reason Atlas memory to
verifier-bound Lawbook candidates.

The loop is:

```text
Reason Atlas advisory queue
-> verifier task callback
-> ExternalCertificate envelope
-> PromotionGate
-> Lawbook candidate only when boundary evidence is valid
-> Reason Atlas feedback
-> priority rescore
-> next advisory queue
```

## Why This Layer Exists

Reason Atlas entries, promoted route laws, root operator schemas, constructor
hints, route priors, and feedback events are useful because they make the next
verification attempt sharper. They are not certificates. Before this layer, the
repository had strong advisory storage and strong local verifier boundaries, but
no single audited gate between advisory queue rows and Lawbook-admissible
terminal artifacts.

## External Certificates

`mathgraph.external_certificates` provides a standard envelope for results from
Lean, Coq, Isabelle, finite checkers, SMT/SAT tools, trusted importers, chain
audits, and future adapters. An external certificate may propose a terminal
form, but it remains advisory unless it carries valid boundary evidence.

Raw success text, stdout, solver labels, contact seeds, route-law support, and
feedback events are not boundary evidence.

## Promotion Gate

`mathgraph.promotion_gate.PromotionGate` is the central admission decision.
It rejects advisory artifacts directly, including:

- Reason Atlas entries
- root operator schemas
- promoted route laws
- verifier feedback events
- advisory-only external certificates
- raw success text without boundary evidence

The gate accepts only candidates with valid verifier/importer/finite-validator
or chain-audit boundary evidence. Accepted output is a Lawbook candidate row;
the gate itself does not run a theorem prover.

## Closed Loop

`mathgraph.closed_verification_loop.ClosedVerificationLoop` is callback-based.
It does not require Lean or any external verifier in tests. Production adapters
can later plug in a real verifier callback that returns an `ExternalCertificate`.

The loop records verifier success or failure as Reason Atlas feedback and then
rescales the next advisory queue. That feedback can change priority; it cannot
create terminal truth by itself.

## Discovery Shape

This implements a disciplined discovery cycle:

```text
variation -> evaluation -> gate -> selective retention -> feedback -> next queue
```

The Reason Atlas makes proposals more targeted. The Promotion Gate keeps truth
admission tied to explicit verifier boundaries.

## Future Work

- real Lean job runner integration
- finite countermodel executor integration
- persistent Lawbook migration/admission workflow
- H-Tilt over persistent Reason Atlas families
- proof-constructor and finite-countermodel root induction
- learned schema proposal models
