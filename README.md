# MathGraph

MathGraph is a lightweight generative verification kernel for AI-assisted
mathematics. Models propose. MathGraph constrains. Verifiers decide. Digestion
assimilates. The Lawbook remembers. Projection scales.

Only verifier, trusted importer, finite validator, and chain audit boundaries
promote truth. Everything else may guide search, explanation, scheduling, or
memory without becoming a theorem.

Full vision/spec: [docs/mathgraph_full_vision_design_spec.tex](docs/mathgraph_full_vision_design_spec.tex)

## Trust Boundary

Every accepted claim ends in exactly one terminal form:

| Terminal form | Meaning |
| --- | --- |
| `VERIFIED_PROOF` | A proof accepted by an explicit verifier/importer/audit boundary |
| `FINITE_COUNTERMODEL` | A checked finite witness that separates source from target |
| `NAMED_OBSTRUCTION` | A structured accepted obstruction record |

| Advisory artifact | What it may do | What it may not do |
| --- | --- | --- |
| route score, H-Tilt, discovery value | rank work | prove a claim |
| digestion, exposition, analogy | explain or compress | verify |
| curricula, repair plans, process memory | plan or replay work | create truth |
| structural identity, typed projection, roles, habits, reasons | organize memory and route pressure | create certificates or accepted theorems |

## Current Architecture

```text
Existential Agent Ecology
  -> API / SDK / CLI
  -> Domain Claim
  -> Semantic / Natural-Language Intake
  -> Formal-World Adapter Registry
  -> Adapter Capability / Parse / Normalize / Validate
  -> Proof-System Project Registry
  -> Artifact Manifests / Import Graphs / Check Requests
  -> API Service Contracts
  -> Continuation Actions
  -> Continuation Curriculum
  -> Verification Episode
  -> Verifier / Importer / Finite Validator / Chain Audit
  -> Proof Digestion
  -> Verifier Feedback / Repair
  -> Discovery Value
  -> Lawbook Acceptance
  -> Lawbook Query / Known Skip
  -> Structural Identity
  -> Habit Rules
  -> Reason Compression
  -> Process Memory
  -> Structure Registry / Typed Projection
  -> Role-Based Object Introduction
  -> Structural Analogy / Exposition
  -> Projection
  -> Telemetry
```

## Implemented Modules

- domain claims, Lean adapter hardening, verification episodes, projection, and telemetry
- continuation actions and curricula
- proof digestion, verifier feedback, and repair
- discovery value, Lawbook acceptance, Lawbook query, and known skip
- structural identity, habit rules, and reason compression
- process memory, structure registry, typed projection, role objects, and structural analogy/exposition
- formal-world adapters for typed parse, normalize, validate, task, and handoff contracts
- proof-system integration contracts for projects, artifacts, imports, checks, and boundary evidence
- semantic intake for deterministic segmentation, ambiguity tracking, formalization requests, and routing
- local API service contracts for stable health, query, submit, routing, and review surfaces
- existential agent ecology for mortality, resources, wounds, lineage, daemonization, and route pressure
- post-M11 hardening harness for advisory replay, contract checks, and evaluation

The first practical proving ground is SAIR Stage 2, equational implication over
magmas. It is a nursery world, not the whole product.

## Formal-World Adapters

MathGraph now has a lightweight formal-world adapter layer that detects broad
world kinds, parses shape, normalizes representations, validates formal shape,
emits proof, countermodel, formalization, finite-validation, and review tasks,
and prepares explicit handoffs to verifiers, trusted importers, finite
validators, or chain audits. Adapter parse, normalize, and validate success is
advisory only and does not verify claims.

## Deeper Proof-System Integration

MathGraph now has proof-system project and artifact lifecycle contracts:
proof-system specs, project manifests, artifact manifests, import graphs, safe
check command contracts, check requests, check result parsing, trusted import
records, and explicit proof boundary evidence. This connects formal-world
adapters to actual proof-system workflows while preserving the rule that files,
imports, check requests, and proof-looking text are advisory until a verifier,
trusted importer, finite validator, or chain audit returns explicit evidence.

## Semantic And Natural-Language Intake

MathGraph now has deterministic natural-language intake for informal
mathematical and scientific text. It segments text, classifies claim types,
detects ambiguity, extracts symbols and relations, creates formalization
requests, and routes claims to formal-world adapters, proof-system integration,
digestion, curricula, repair, and review. Natural language remains advisory:
theorem-like sentences, proof-looking paragraphs, semantic confidence, and
extracted formal candidates do not verify claims.

## API Service Hardening

MathGraph now exposes a local API and SDK boundary with stable request and
response schemas. The service supports health, audit, query, submit, semantic
intake, formal-world adapters, proof-system integration, scheduling,
projection, explanation, process memory, discovery value, and advisory review
routes. Every response includes truth status, safety level, and verifier
boundary fields. HTTP or SDK success does not mean mathematical truth.

## Existential Agent Ecology

MathGraph now supports advisory finite-resource discovery agents with mortality
policies, resource accounts, wounds, value drift, narrative identity,
Held-in-Chora records, lineage summaries, daemonized skills, and route-priority
adjustments. Agents may change scheduling pressure and discovery behavior, but
they cannot verify claims, accept Lawbook entries, or promote truth. Dead agents
cannot act, receive budget, mutate, spawn, or be resurrected as the same acting
self.

## Post-M11 Hardening And Evaluation

MathGraph now includes a hardening harness for end-to-end advisory smoke
scenarios, serialization checks, API contract checks, documentation sync, public
terminology hygiene, truth-boundary invariants, agent lifecycle invariants,
lightweight performance checks, and replay manifests. Hardening artifacts are
advisory and do not promote mathematical truth.

## External Verifier Execution And End-to-End Test Drive

MathGraph now has a strict local verifier execution adapter. Execution is
disabled by default. When explicitly allowed, the adapter may run supported
local proof-system checks under allowlisted commands, timeout, path, shell,
network, and unsafe-marker constraints. Raw success text and return code are not
enough. Boundary evidence is created only when a local verifier accepts a safe
artifact under a valid command contract. The end-to-end test drive runs the
architecture from semantic intake through API, agents, hardening, and optional
verifier evidence.

## CLI And Tooling

Repo scripts expose the implemented layers as small backend-first tools:

- `scripts/run_roadmap_alignment.py`
- `scripts/run_reason_compression.py`
- `scripts/run_process_memory.py`
- `scripts/run_structure_registry.py`
- `scripts/run_role_objects.py`
- `scripts/run_structural_analogy.py`
- `scripts/run_formal_world_adapters.py`
- `scripts/run_proof_system_integration.py`
- `scripts/run_semantic_intake.py`
- `scripts/run_api_service.py`
- `scripts/run_existential_agents.py`
- `scripts/run_hardening.py`
- `scripts/run_verifier_execution.py`
- `scripts/run_e2e_testdrive.py`

These tools emit advisory artifacts unless an already-existing verifier boundary
is being reported. They do not bypass the terminal contract.

## Current Status

Implemented milestones run through M11 Existential Agent Ecology. See
[docs/roadmap.md](docs/roadmap.md) for the live
roadmap and [docs/agentic_alchemical_loop.md](docs/agentic_alchemical_loop.md)
for the process view. See also [docs/manifesto.md](docs/manifesto.md) and
[docs/glossary.md](docs/glossary.md).

## Future Work

- richer verifier adapters
- richer domain adapters
- larger replay fixtures
- production packaging
- publication demos
- release workflow

MathGraph should not scale by becoming bigger. It should scale by making every
verified thing reusable and every failure informative.
