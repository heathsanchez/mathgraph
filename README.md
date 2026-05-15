# MathGraph

MathGraph is a lightweight verification and discovery kernel for AI-assisted
mathematics. It keeps proposal, verification, digestion, repair, curriculum,
discovery value, accepted public memory, and projection separate so useful
search pressure does not quietly become truth.

## Core Doctrine

Models propose. MathGraph constrains. Verifiers decide. Digestion assimilates.
The Lawbook remembers. Projection scales.

Only verifier/importer/finite-validation/chain-audit boundaries promote truth.
Everything else is advisory pressure.

## Terminal Truth Forms

Every accepted claim must collapse into exactly one terminal truth form:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL`
- `NAMED_OBSTRUCTION`

A verified proof is truth-stable. A digested proof is understanding-stable. A
high-value route is scheduling pressure. A Lawbook entry is accepted public
memory.

## Architecture

MathGraph pipeline:

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

The first practical testbed is SAIR Stage 2: equational implication over
magmas. The repository is still shaped as a general kernel rather than a
competition-only solver.

## Domain Claims

The domain-general claim IR parses and normalizes raw claims into lightweight
`DomainClaim` records classified by formal world. Parsing, normalization, world
selection, and routing are advisory. Magma implications can route into existing
episodes, and Lean-looking claims can route into proof skeletons, but text is
not truth.

## Continuation Actions

Continuation actions generate advisory next moves: implication candidates,
equivalence candidates, proof tasks, countermodel tasks, projection tasks, and
obstruction candidates. Generated actions are proposals only.

## Continuation Curricula

Continuation curricula turn a hard target into a replayable ladder of warm-up
claims, simplified cases, finite examples, proof tasks, countermodel tasks,
projection tasks, repair tasks, and episode inputs. Curricula are route plans,
not proof. Warm-ups do not prove targets, and finite examples do not prove
`TRUE`.

## Verification Episodes

Episodes compose projection, constructors, proof verification, agent memory,
and telemetry into one replayable run. An episode becomes terminal only when a
subtrace already crossed a verifier/importer/finite-validation/chain-audit
boundary with a certificate id.

## Proof Verification and Lean

TRUE-side proof artifacts, theorem schemas, and Lean skeletons stay advisory
until a proof checker, trusted importer, or chain auditor accepts them. The Lean
adapter can represent files, inspect imports and theorem names, and run Lean
when available, but Lean text and theorem names are not proof.

## Proof Digestion

Proof digestion maps dependencies, separates routine and load-bearing steps,
extracts key idea and reusable schema candidates, creates exposition notes, and
proposes lawbook assimilation candidates. Digestion is not verification. A
digestion trace may inherit an existing verified certificate, but it cannot
invent one.

## Verifier Feedback and Repair

Verifier feedback classifies failed checks into minor repairable flaws,
structural gaps, critical invalidations, and unknown failures. Repair loops can
emit local revision, reroute, proof, countermodel, obstruction, hold, or
residual tasks. Repair is not verification.

## Discovery Value Evaluator

Discovery value scores curricula, digestion traces, verifier feedback, repair
loops, projection candidates, continuation outputs, alchemical traces, agent
experiences, and telemetry for expected discovery value. High value is not
proof, projection value is not a certificate, and repair value is not
verification.

## Lawbook Acceptance Boundary

The Lawbook is the accepted public-memory boundary. Certificates, proof
digestion traces, lawbook assimilation candidates, projection candidates, and
discovery value scores may recommend entries, but none of them automatically
become accepted Lawbook memory. Only explicit Lawbook acceptance creates an
accepted entry, and acceptance can only record truth already established by an
existing verifier/importer/finite-validation/chain-audit boundary or structured
named-obstruction evidence.

## Lawbook Query and Known-Skip Service

MathGraph can query accepted Lawbook memory without constructing or verifying.
A known skip means the system found an accepted entry backed by existing
boundary evidence:

- accepted proof -> skip verified proof
- accepted countermodel -> skip finite countermodel
- accepted obstruction -> skip accepted obstruction
- candidate only -> do not skip
- projection only -> do not skip

Candidate-only, digestion-only, projection-only, and discovery-value-only
records never permit skip. Querying memory reports what is already accepted; it
does not accept, verify, or promote anything.

## Projection

Projection applies accepted memory back to unresolved work as known skips,
derived certificate chains, residual splits, and advisory route pressure.
Projection scales verified memory; it does not create truth by itself.

## Telemetry and Route Pressure

Route telemetry, spectral H-tilt estimates, agent biography, root pressure, and
discovery value are scheduling signals. They help MathGraph decide what to try
next while staying outside the truth boundary.

## Roadmap

Implemented milestones now include domain claims, Lean adapter hardening,
continuation actions, proof digestion, verifier feedback, continuation
curricula, discovery value scoring, and the accepted Lawbook boundary. See
[Roadmap](docs/roadmap.md) for current and future work.

## What MathGraph Is Not

- Not a passive database.
- Not broad automated theorem proving.
- Not semantic or natural-language trust.
- Not a proof sketch grader that turns plausibility into truth.
- Not an autonomous agent system.
- Not a UI project.

The repository keeps source, tests, docs, schemas, and small reproducible
examples in Git. Large ledgers, run directories, build outputs, and experiment
artifacts belong in external artifact storage.

See [Agentic Alchemical Loop](docs/agentic_alchemical_loop.md),
[Manifesto](docs/manifesto.md), and [Glossary](docs/glossary.md) for deeper
architecture notes.
