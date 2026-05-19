# MathGraph

MathGraph is a generative verification kernel for trustworthy mathematical
discovery.

Start here:

```bash
python scripts/run_release_check.py --quick
python scripts/run_public_demo.py --out-dir demo_out
```

Then read [docs/quickstart.md](docs/quickstart.md).

## Curated Real Mathlib Demo

```bash
python scripts/run_real_mathlib_demo.py --ensure-examples
python scripts/run_real_mathlib_demo.py
python scripts/run_real_mathlib_demo.py --config examples/real_mathlib_demo/curated_real_mathlib_demo_config.example.json --project-root /path/to/local/mathlib
```

This local-path-only workflow performs no downloads or package-manager actions, skips cleanly when no path is supplied, and keeps verification limited to explicitly selected declarations.

Models propose. MathGraph constrains. Verifiers decide. Digestion assimilates.
The Lawbook remembers. Projection scales.

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

## Rich Verifier Fixtures And Test Drive

MathGraph now includes a Lean fixture suite for safe passing theorems,
unsafe-marker rejection, expected-theorem validation, type/import failures, and
optional in-memory Lawbook review/query replay. The fixture suite can run in
dry-run mode everywhere or live mode when Lean is available and execution is
explicitly allowed. Unsafe fixtures must never create boundary evidence.

## Verified Corpus Micro-Ingestion

MathGraph can ingest a tiny local Lean corpus through a manifest, extract
declarations, imports, and dependency metadata, run local verifier checks only
when explicitly allowed, produce boundary-backed entries only for verified safe
declarations, reject unsafe, expected-missing, and import-failure entries, and
optionally replay Lawbook review/query in memory. Corpus extraction and
dependency graphs are advisory metadata, not proof.

## Lean Project Micro-Subset Pilot

MathGraph can now ingest a tiny local Lean project with module imports, extract
declarations, imports, and reference dependencies, run local verifier checks
from the project root only when explicitly allowed, produce boundary-backed
entries only for verified expected declarations, reject unsafe,
expected-missing, and import-failure entries, emit advisory dependency graphs
with import and reference edges, and optionally replay Lawbook review/query in
memory. Module and dependency extraction are advisory metadata, not proof.

## Mathlib Micro-Subset Pilot

MathGraph can now ingest a tiny local Mathlib-style subset through an
allowlisted manifest, extract module paths, declarations, imports, and
declaration-reference dependencies, run local verifier checks only when
explicitly allowed, produce boundary-backed entries only for verified expected
declarations, reject unsafe, expected-missing, and import-failure entries, emit
advisory dependency graphs, and optionally replay Lawbook review/query in
memory.

The built-in fixture is synthetic and local. External Mathlib mode is
local-path-only and performs no downloads or package-manager operations.

## Real Local Mathlib Allowlist Pilot

MathGraph can now point at a user-supplied local Lean/Mathlib checkout or local
Lean project through an explicit allowlist manifest. It diagnoses the
environment, extracts declarations/imports/references, runs local verifier
checks only when explicitly allowed, and produces boundary-backed entries only
for allowlisted expected declarations. It performs no downloads and no
package-manager operations.

## Mathlib Declaration Discovery

MathGraph can now inspect explicitly selected local Lean/Mathlib module files,
discover theorem/lemma/definition declarations, generate an allowlist manifest,
and optionally hand that manifest to the local allowlist verifier. Discovery is
advisory. Only the downstream verifier boundary can create proof evidence.

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
- `scripts/run_verifier_fixtures.py`
- `scripts/run_verified_corpus.py`
- `scripts/run_lean_project_subset.py`
- `scripts/run_e2e_testdrive.py`

These tools emit advisory artifacts unless an already-existing verifier boundary
is being reported. They do not bypass the terminal contract.

## Fresh Clone CLI Usage

Public scripts bootstrap the repository root automatically, so an editable
install is optional for local script use:

```bash
python scripts/run_e2e_testdrive.py
python scripts/run_hardening.py
python scripts/run_colab_testdrive.py --use-current-checkout --quick-smoke
python scripts/run_colab_testdrive.py --fresh-clone --allow-live-verifier --allow-missing-verifier
```

Live verifier execution remains opt-in. Missing Lean skips cleanly when allowed.
CLI success is a usability signal, not proof of arbitrary claims.

## Proof-Library Demo Pack

MathGraph now has a repeatable demo that runs discovery, allowlist manifest
generation, optional verifier-bound allowlist ingestion, dependency/reference
graph output, Lawbook replay, known-skip replay, and a polished Markdown report.
The built-in demo uses the synthetic Mathlib-style subset; a real local Mathlib
demo can be configured by supplying a local path and explicit
module/declaration selection.

## Public Demo and Release Check

```bash
python scripts/run_public_demo.py --ensure-configs
python scripts/run_public_demo.py --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory
python scripts/run_release_check.py --quick
python scripts/run_release_check.py --include-public-demo --allow-live-verifier --allow-missing-verifier
```

Demo success and release-check success are usability signals, not proof.

## Optional Real Local Mathlib Revision Demo

```bash
python scripts/run_proof_library_demo.py --config examples/proof_library_demo/real_mathlib_demo_config.example.json --project-root /path/to/mathlib
```

See `docs/real_mathlib_revision_demo.md` for the local-path-only revision workflow.

## Mathlib Module-Aware Verification

```bash
python scripts/run_mathlib_module_verification.py --use-synthetic-request --project-root examples/mathlib_micro_subset
python scripts/run_real_mathlib_demo.py --project-root /path/to/mathlib4 --run-module-verification --execution-mode lake-env-lean --allow-execution --allow-missing-verifier
```

For selected real Mathlib declarations, this is the preferred verifier-bound
path. Generated import/`#check` files establish imported declaration availability
only after Lean succeeds; they are not source-proof reconstruction.

Real Mathlib discovery can expose names that need qualification repair. Module
verification emits failed-check diagnostics and offers an explicit conservative
`--enable-name-candidate-fallback`; candidates stay advisory until Lean accepts
the resolved spelling.

For real Mathlib/Lake projects, module verification should use `lake env lean`
from the supplied project root. Raw Lean mode remains useful for synthetic or
simple projects; diagnostics that mention `/tmp/.../olean/Mathlib` indicate the
wrong import context.

## Current Status

Implemented milestones run through Public Demo and Release Readiness. See
[docs/roadmap.md](docs/roadmap.md) for the live
roadmap and [docs/agentic_alchemical_loop.md](docs/agentic_alchemical_loop.md)
for the process view. See also [docs/manifesto.md](docs/manifesto.md) and
[docs/glossary.md](docs/glossary.md).

## Future Work

- curated real Mathlib demo manifests
- trusted importer policy for pinned external corpora
- Lake-aware build plan without network
- larger fixture-driven release gates
- persistent Lawbook storage workflow
- package/release workflow

MathGraph should not scale by becoming bigger. It should scale by making every
verified thing reusable and every failure informative.
