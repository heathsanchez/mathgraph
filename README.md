# MathGraph

MathGraph is a lightweight generative verification kernel for verifiable
mathematics and trustworthy AI.

It is not a passive database and not a static encyclopedia. It is a compounding
verification metabolism: models propose, MathGraph constrains, verifiers decide,
the lawbook remembers, and reasons compress.

Every accepted claim must collapse into exactly one terminal form:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL` (the current concrete refutation certificate)
- `NAMED_OBSTRUCTION`

The first practical testbed is SAIR Stage 2: equational implication over
magmas. The repository is organized as a general MathGraph kernel rather than a
competition-only solver.

Read the [manifesto](docs/manifesto.md) and [glossary](docs/glossary.md) for
the post-v16.7 architecture language: Certificate Universe, Obstruction Atlas,
Root Node Atlas, Reason Atlas, LawbookStore / KernelOracle, constructor/verifier
boundary, H-tilt route pressure, and the integrity spine.

## Agentic Alchemical Alignment

MathGraph now includes a first lightweight agentic/alchemical backend layer:

- `AlchemicalTrace` records the staged movement from raw residuals through
  calcination, descension, fixation, projection, and related phases.
- `AgentProfile`, `AgentExperience`, and `AgentBiography` record persistent
  policy memory: taste, scars, costs, route preferences, and compounding gains.
- H-tilt-lite scores advisory route pressure from taste, scars, expected cost,
  projection gain, and compression gain. Full spectral H-tilt `K = L - V`
  remains future work.
- `RoadmapAlignmentReport` checks that traces, experiences, and summaries keep
  advisory pressure out of terminal truth unless a verifier/importer promotes it.

These objects do not create accepted claims. Models propose; MathGraph
constrains; verifiers decide; the Lawbook remembers; reasons compress. Advisory
pressure includes route scores, H-tilt scores, roots, motifs, failed searches,
task plans, agent taste, agent scars, and held-in-Chora ideas. None of that is
truth until promoted across the verifier boundary into exactly one terminal
form.

See [Agentic Alchemical Loop](docs/agentic_alchemical_loop.md).

## Projection Engine

The M2 projection engine applies fixed lawbook artifacts back to unresolved
residuals. It can create known skips, chain-safe derived certificate results,
advisory residual splits, obstruction pressure, projection tasks, and
compounding metrics.

Projection is not truth. A projection result becomes terminal only when it is
backed by an existing verifier boundary, an already verified primitive
certificate, or an explicitly chain-audited derived certificate id. Route
pressure, projection pressure, finite-search misses, and agent taste remain
advisory.

## Root-Aware Constructors

The M3 root-aware constructor layer compiles advisory root, residual, obstruction,
and projection pressure into narrow constructor plans. Plans are advisory. Root
candidates are not theorems, basin matches are not certificates, and candidate
finite tables are not terminal artifacts.

Only importer-verified finite countermodels cross the truth boundary into
`FINITE_COUNTERMODEL`. Candidate tables remain candidate artifacts until the
importer/revalidator accepts them, and finite-search misses remain residuals,
not TRUE proofs.

## TRUE-Side Proof Verification Scaffold

The M4 proof verification scaffold gives TRUE-side artifacts the same explicit
boundary discipline as finite countermodels. Proof motifs, lemma candidates,
cut candidates, theorem schemas, and Lean skeletons are advisory until a
verifier, trusted importer, or chain auditor accepts them.

A proof artifact becomes `VERIFIED_PROOF` only after an explicit
verifier/importer/chain-audit boundary produces a certificate id. Lean does not
need to be installed for the scaffold; optional verifier execution is supported
when available. The mock verifier exists for tests only and is not production
trust.

## Unified Verification Episode

The M4.5 unified verification episode orchestrator composes projection,
root-aware constructors, TRUE-side proof verification, alchemical traces, agent
experiences, and roadmap alignment into one replayable run.

A verification episode can report terminal truth only when a subtrace crossed a
verifier/importer/chain-audit boundary with a certificate id. Route decisions,
H-tilt-lite scores, candidate tables, proof skeletons, and search misses remain
advisory telemetry.

## Route Telemetry for Future H-Tilt

The M5-prep route telemetry ledger records what unified episodes tried:
route choices, transitions, killed routes, costs, gains, outcomes, and terminal
yield. It can summarize transition counts, killing counts, route/outcome tables,
gain-per-cost metrics, and advisory H-tilt telemetry scores.

This prepares the data needed for future spectral H-tilt estimation of `L`,
`V`, `K = L - V`, `h`, `q`, and `pi*`. It is telemetry only. Route telemetry and
route scores cannot promote claims, override verifiers, or turn misses,
skeletons, or candidate tables into truth.

## Lightweight Spectral H-Tilt

The M5 lightweight spectral H-tilt estimator converts route telemetry into
approximate `L`, `V`, `K = L - V`, `h`, `q`, `pi*`, and `mu_beta` values using
pure Python dict matrices and positive iteration helpers.

This is advisory route pressure only. It may rank states or routes for future
episodes, but it does not verify claims, promote truth, override verifier
failures, or turn killed routes into proofs. Richer spectral methods remain
future work.

## Domain-General Claim IR

The M6 domain-general claim IR lets MathGraph parse and normalize raw claims
into lightweight `DomainClaim` records classified by formal world. The
`FormalWorldRegistry` declares which worlds support which claim kinds, adapters,
normalization, proofs, or countermodels.

Parsing, normalization, world selection, and routing are advisory. Magma
equational implications can route into verification episodes, and Lean-looking
theorem statements can route into proof skeletons, but terminal truth still
requires a verifier/importer/chain-audit boundary. Natural-language and
unsupported worlds remain advisory/residual until a real verifier exists.

## Lean Adapter Hardening

M6.5 adds a lightweight Lean adapter layer around the proof verification
scaffold. Lean files and skeletons can be represented, checked when Lean is
available, imported with trusted provenance, and bridged into proof verification
traces, alchemical traces, and agent experiences.

Lean text, theorem names, parseable files, failed checks, and unavailable Lean
remain advisory. A Lean artifact becomes `VERIFIED_PROOF` only when a Lean check
or trusted importer produces a proof verification result with a certificate id
across the verifier boundary. Missing Lean is handled gracefully.

## Continuation Action Registry

M6.6 adds a deterministic continuation action registry. MathGraph can now
generate advisory next moves from claims and traces: specialize, generalize,
dualize, form implications/equivalences, emit proof tasks, emit countermodel
tasks, emit projection tasks, and propose obstruction candidates.

Action outputs are proposals only. A generated theorem statement, proof task,
countermodel task, projection task, or obstruction name cannot promote truth.
Outputs may bridge into existing episode/proof/projection machinery, but only a
verifier, importer, chain audit, or naming boundary can produce a terminal
form.

## Current Empirical Milestone

External v16.6/v16.7 artifacts remain outside GitHub, but the repo now contains
the schemas, importers, consolidators, oracles, docs, and tests that make them
replayable and queryable.

- v16.6 derived closure: 250,000 derived TRUE rows, 750,000 derived FALSE rows,
  1,084,694 oracle lookup rows, and zero sampled matrix contradictions.
- v16.6.1 derived false elevation audit: zero elevated rows when primitive table
  payloads were unavailable. Lesson: logical derived false rows are not concrete
  finite certificates unless witness/table replay is preserved.
- v16.6.2 table-aware false elevation: 401,742 of 500,000 attempted false rows
  elevated to finite-verified certificates with zero sampled contradictions.
- v16.7 distillation: 401,742 finite false certificates, 56 unique tables, 1,835
  motifs, 524 supported root candidates, 733 reason candidates, and 102
  obstruction candidates.

This repo stores source, tests, docs, schemas, and small examples. Large CSV,
JSONL, SQLite, Parquet, matrix, and run artifacts belong in external artifact
storage. Next: canonical root consolidation and root/reason/obstruction oracle
work over those external artifacts.

## Building a Local LawbookStore

The v16.8 warehouse layer builds a local SQLite lawbook from external artifact
directories without copying those large artifacts into Git:

```bash
python scripts/build_lawbook_store.py \
  --out-db /external/path/mathgraph_lawbook.sqlite \
  --v1662-dir /external/path/mathgraph_v16_6_2 \
  --v167-dir /external/path/mathgraph_v16_7

python scripts/query_lawbook.py \
  --db /external/path/mathgraph_lawbook.sqlite \
  --summary

python scripts/query_lawbook.py \
  --db /external/path/mathgraph_lawbook.sqlite \
  --claim 0 1
```

The warehouse stores claims, certificates, finite refutations, derived chains,
roots, reasons, obstructions, tables, aliases, and import manifests in
normalized SQLite tables. Root/reason/obstruction rows are advisory and
compressive unless backed by concrete certificate chains; they do not verify or
refute unknown claims.

## Root Discovery

MathGraph now treats completion/search telemetry as a contrastive source of
root-node candidates. SAT, UNSAT, UNKNOWN, TIMEOUT, and ERROR rows are preserved
and distilled into candidate roots, obstruction candidates, constructor-family
cards, and replay queues. Root nodes are SAT-clusters carved out by UNSAT
boundaries: the contrast is the point.

The consolidation layer adds persistent filtration, shadow collapse, advisory
root promotion records, and constructor-plan compilation. This turns residual
telemetry into replay pressure without pretending that discovery artifacts are
proof.

This does not change the verifier boundary. Root discovery creates scheduling
pressure and discovery artifacts only; importer-revalidated certificates,
chain-audited derivations, or formal verification remain the only route to
terminal truth. See [Root Discovery Architecture](docs/root_discovery_architecture.md).

## Root Node Discovery Notes

Root scoring is advisory. A root is a persistent load-bearing continuation
point, not merely a frequent motif or high-yield table. Residuals are membranes,
not backlog: they show where the current language and constructors stop being
sufficient. See [Root Node Discovery](docs/root_node_discovery.md) and
[Residual Membrane](docs/residual_membrane.md). Terminal certificates remain the
only truth boundary.

## Root Constructor Validation Lab

The local lab tests whether advisory root candidates can route a basin into
constructor families that produce importer-revalidated finite refutations with
lift over a null basin. Root recommendations remain advisory:

```bash
python scripts/run_root_constructor_lab.py \
  --pairs /tmp/pairs.jsonl \
  --out-dir /tmp/root_constructor_lab \
  --max-pairs-per-root 50 \
  --null-pairs-per-root 50
```

## Continuation Trace Replay

Root lab runs can now emit append-only continuation traces and replay them into
advisory route pressure:

```bash
python scripts/run_root_constructor_lab.py \
  --pairs /tmp/pairs.jsonl \
  --out-dir /tmp/root_lab \
  --trace-store /tmp/root_lab/continuation_traces.jsonl \
  --replay
```

## Route Policy v2

Replay signals can be compiled into advisory H-tilt-compatible route policy
cards:

```bash
python scripts/build_route_policy_v2.py \
  --traces /tmp/root_lab/continuation_traces.jsonl \
  --out-dir /tmp/root_lab/route_policy_v2
```

## Residual Atlas v1

Residual Atlas v1 maps unresolved continuation traces into advisory membrane
cases and clusters:

```bash
python scripts/build_residual_atlas.py \
  --traces /tmp/root_lab/continuation_traces.jsonl \
  --route-policy /tmp/root_lab/route_policy_v2/route_policy_v2_report.json \
  --out-dir /tmp/root_lab/residual_atlas
```

## Frontier Builder v2

Frontier Builder v2 turns residual atlas cases into advisory next-episode task
proposals:

```bash
python scripts/build_frontier_v2.py \
  --residual-atlas /tmp/root_lab/residual_atlas/residual_atlas_report.json \
  --out-dir /tmp/root_lab/frontier_v2 \
  --max-tasks 100
```

## Formal Worlds / DomainKernels

ETP over magmas is MathGraph's first nursery, not the whole product. Inspired
by AOT-style computational metaphysics, MathGraph can now register external
formal domains as metadata in the `LawbookStore`:

```bash
python scripts/register_domain_kernel.py \
  --db /tmp/mathgraph.sqlite \
  --preset aot

python scripts/query_lawbook.py \
  --db /tmp/mathgraph.sqlite \
  --domain-kernels
```

AOT is registered as an Isabelle/HOL shallow semantic embedding precedent.
Registration is advisory metadata only: it does not import AOT theorems, run
Isabelle, or verify AOT claims. See
[DomainKernels](docs/domain_kernels.md) and
[Computational Metaphysics](docs/computational_metaphysics.md).

## Typed Predication and Objectification

v16.10 adds the substrate needed for AOT-like formal worlds without importing
Isabelle yet:

- typed formal objects with relational type expressions such as `i`, `<>`,
  `<i>`, and `<i,i>`;
- explicit **encoding** vs **exemplification** predication;
- denotation/free-logic guardrails for complex terms;
- semantic embedding risk metadata and proof-transport status;
- bounded language fragments, formal-world metadata, paradox guards, and
  theory-relative objectification maps.

This is metadata and safety infrastructure, not a new proof authority. Same
extension is not same law, same coverage is not same reason, same table
behavior is not same root, and same truth value is not same continuation.
See [Typed Predication Kernel](docs/typed_predication_kernel.md),
[Theory Objectification](docs/theory_objectification.md),
[Formal Worlds](docs/formal_worlds.md), [Paradox Guards](docs/paradox_guards.md),
and [Reason Containment](docs/reason_containment.md). The companion
[Formal Object-Language IR](docs/formal_object_language.md),
[Theory Registry](docs/theory_registry.md),
[AOT Scanner](docs/aot_scanner.md), and
[Hyperintensional Identity](docs/hyperintensional_identity.md) pages describe
the advisory scanner/registry layer for future Isabelle/AOT imports.

## LogiKEy-Style Workbench and Faithfulness

v16.11 adds a meta-logical workbench layer inspired by the LogiKEy methodology:
formal worlds are organized into L0/L1/L2/L3 layers, semantic embedding
strategies are explicit, backend profiles distinguish proof-finders from
model-finders, and faithfulness assessments record bridge risk.

```bash
python scripts/register_logical_workbench.py \
  --db /tmp/mathgraph.sqlite \
  --preset logikey

python scripts/query_lawbook.py \
  --db /tmp/mathgraph.sqlite \
  --logical-workbenches
```

This is still substrate, not prover integration. Faithfulness assessments can
reduce embedding risk for a specific bridge, but they do not prove arbitrary
claims. Benchmarks are evidence and regression checks, not proof. A
model-finder miss is not proof; a proof-finder miss is not refutation; logic
combinations remain advisory until interaction semantics and conflict policy
are assessed. See [LogiKEy Workbench](docs/logikey_workbench.md),
[Faithfulness Assessment](docs/faithfulness_assessment.md),
[Verifier Backends](docs/verifier_backends.md),
[Benchmarking](docs/benchmarking.md), [Correspondence Claims](docs/correspondence_claims.md),
and [Interpretation Choice Points](docs/interpretation_choice_points.md).

## Proof Motif Atlas and Lemma Candidates

The TRUE side now has a proof-shaping substrate mirroring the FALSE-side
certificate atlas:

```bash
python scripts/build_proof_atlas.py \
  --input /external/path/true_proofs.csv \
  --out-dir /tmp/mathgraph_proof_atlas \
  --out-db /tmp/mathgraph_proof_atlas.sqlite \
  --emit-lean-sketches
```

MathGraph can store proof motifs, lemma/cut candidates, and Lean artifact
metadata, then query them through `query_lawbook.py`. A proof motif is not a
proof, a lemma candidate is not a theorem, and a generated Lean sketch is not
Lean verification. See [Proof Motif Atlas](docs/proof_motif_atlas.md),
[Lemma Candidate Generator](docs/lemma_candidate_generator.md), and
[Lean Artifacts](docs/lean_artifacts.md).

## Metabolic Cycle Testbed

v16.12 wires the nouns into a local episode runner:

```bash
python scripts/run_metabolic_cycle.py \
  --store /tmp/mathgraph_cycle.sqlite \
  --out-dir /tmp/mathgraph_cycle \
  --synthetic-seed \
  --strict \
  --json
```

The cycle builds or loads a frontier, checks lawbook memory, schedules routes,
runs bounded kernel construction, imports verified terminal traces, derives
chain-safe certificates, records residual obstructions, updates route-yield
pressure, and emits a sharper next frontier. It writes both machine-readable
JSON/JSONL artifacts and a Markdown report. This proves the feedback loop is
wired; it is not full theorem proving or Lean automation. See
[Metabolic Cycle Testbed](docs/metabolic_cycle.md).

## Milestone 0 Closed-Loop Smoke

The canonical M0 certificate factory chews JSONL implication pairs, checks
LawbookStore memory, runs finite countermodel construction only for unknown
pairs, revalidates imports, and writes a report:

```bash
printf '%s\n' '{"source":"(x*x)=x","target":"(x*y)=x","source_idx":1,"target_idx":2}' \
  > /tmp/mathgraph_m0_pairs.jsonl

python scripts/chew_certificate_tasks.py \
  --pairs /tmp/mathgraph_m0_pairs.jsonl \
  --store /tmp/mathgraph_m0.sqlite \
  --ledger /tmp/mathgraph_m0_ledger.jsonl \
  --report /tmp/mathgraph_m0_report.json \
  --metrics-history /tmp/mathgraph_m0_metrics.jsonl \
  --episode-id m0_smoke_001 \
  --max-countermodel-order 3
```

Expected first-run summary includes `verified_false: 1`,
`new_unique_certificates: 1`, and `compounding_confirmed: true`. Rerun the same
command with `--episode-id m0_smoke_002`; the summary should show
`known_skipped: 1` and no new primitive certificate. Finite-search misses remain
constructor failures or residuals, never proofs.

## M0 Trust Boundary And Audit

The finite constructor may find a candidate table, but only the importer can
promote it after rechecking that the source equation holds and the target
equation fails on the witness. Advisory routes, candidate certificates,
obstructions, parse failures, verification failures, and finite-search misses
are not certificates.

Run the M0 loop with an audit:

```bash
python scripts/chew_certificate_tasks.py \
  --pairs /tmp/mathgraph_m0_pairs.jsonl \
  --store /tmp/mathgraph_m0.sqlite \
  --report /tmp/mathgraph_m0_report.json \
  --audit \
  --audit-report /tmp/mathgraph_m0_audit.json \
  --fail-on-critical-audit
```

Or audit an existing store directly:

```bash
python scripts/audit_m0_store.py \
  --store /tmp/mathgraph_m0.sqlite \
  --report /tmp/mathgraph_m0_audit.json \
  --fail-on-critical
```

Audit failures are machine-readable. Critical findings mean something unsafe
crossed, or appears to have crossed, the verified-certificate boundary.

## Python SDK Smoke

Use `MathGraphClient` when embedding the M0 middleware boundary in local Python
code:

```python
from mathgraph import MathGraphClient

client = MathGraphClient("/tmp/mathgraph.sqlite")
answer = client.submit_claim(
    source="(x*x)=x",
    target="(x*y)=x",
)
print(answer.to_json())
```

`query_claim` is read-only and never constructs. `submit_claim` may run the M0
finite-countermodel factory and promote only importer-revalidated certificates.
Every `MathGraphAnswer` exposes `terminal_form`, `trust_level`,
`provenance_type`, `verifier_boundary`, and `certificate_chain`.
`audit_after_write` defaults to true, so write-path answers include the M0 audit
summary unless the client is configured otherwise.

## Local HTTP Service Smoke

Expose the same M0 SDK boundary over local HTTP:

```bash
python scripts/serve_mathgraph.py --store /tmp/mathgraph_api.sqlite
```

Then query it from another shell:

```bash
curl http://127.0.0.1:8765/health

curl -X POST http://127.0.0.1:8765/query \
  -H "Content-Type: application/json" \
  -d '{"source":"(x*x)=x","target":"(x*y)=x"}'

curl -X POST http://127.0.0.1:8765/submit \
  -H "Content-Type: application/json" \
  -d '{"source":"(x*x)=x","target":"(x*y)=x","allow_construction":true}'
```

`/query` is read-only. `/submit` may construct and promote only verified
certificates. `/audit` checks the M0 trust boundary. All claim responses expose
`terminal_form`, `trust_level`, `provenance_type`, and `verifier_boundary`.

## SAIR Stage 2 Competition Solver Path

The competition-specific single-file solver target lives in
`competitions/sair_stage2/`. It compiles a standalone
`competitions/sair_stage2/dist/solver.py` under 500KB from compact SAIR runtime
logic. This path is intentionally isolated: `mathgraph` remains the general
verification kernel, and the generated solver must not import MathGraph or
runtime dependencies outside the Python standard library.

## Quick Start

```bash
pip install -e ".[dev]"
pytest
python examples/basic_kernel_demo.py
```

## v0.1 Kernel API

```python
from mathgraph import Kernel, TerminalForm

trace = Kernel().prove("x * y = y * x", "a * b = b * a")
assert trace.verify()
assert trace.is_verified_proof()
assert trace.terminal_form == TerminalForm.VERIFIED_PROOF

countermodel = Kernel().prove("x = x", "x * x = x")
assert countermodel.terminal_form == TerminalForm.FINITE_COUNTERMODEL
```

`Kernel.prove(source, target=None)` returns a trace with the claim, routes tried,
terminal form, verification status, and either a certificate or obstruction. The
current proof routes are intentionally small: exact equation match, sides
swapped, and skeleton-preserving variable renaming. Finite magma routes can
produce explicit countermodel certificates.

If no route terminates, MathGraph returns `NAMED_OBSTRUCTION`. That is not a
truth claim and not a proof. `trace.verify()` checks that the trace is
well-formed; `trace.is_verified_proof()` checks whether it is actually a proof.

## Optional ETP Assets

ETP equation and matrix files are loaded from local paths supplied by the caller.
Do not commit generated matrices or result tables.

```bash
export MATHGRAPH_EQUATIONS_PATH=/path/to/equations.txt
export MATHGRAPH_MATRIX_PATH=/path/to/etp_matrix.npy
python examples/etp_false_sample.py
```

```python
from adapters.etp_adapter import load_matrix, sample_false_pairs, summarize_assets

summary = summarize_assets("equations.txt", "etp_matrix.npy")
matrix = load_matrix("etp_matrix.npy")
print(summary)
print(sample_false_pairs(matrix, limit=5, seed=0))
```

Matrix loading uses numpy when it is installed. `.npy`, `.npz`, `.csv`,
`.parquet`, and `.sqlite` artifacts stay ignored by git.

## External SAIR Stage 2 Results

SAIR/ETP route and certificate result tables can be imported from external
artifact paths. Keep generated CSV, Parquet, SQLite, matrix, and ledger outputs
outside GitHub.

```python
from adapters.sair_stage2_adapter import import_traces, load_results_table, summarize_results

records = load_results_table("/external/path/routelean_results_v19_1.parquet")
print(summarize_results(records))
traces = import_traces("/external/path/routelean_results_v19_1.parquet", limit=10)
```

The importer only promotes rows that explicitly verify true or verify false.
Missing verification, finite-search failure, and failed Lean execution become
non-promotable obstruction traces.

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --out /external/path/mathgraph_import/
```

Directory mode writes `summary.json`, `traces.json`, `traces.jsonl`,
`certificates.json`, and `index.sqlite`. Existing scripts can still pass a
`.jsonl` path to `--out` to write only the legacy ledger file plus
`summary.json` next to it. Explicit output paths are also available:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --summary-json /external/path/summary.json \
  --export-traces-json /external/path/traces.json \
  --export-ledger-jsonl /external/path/traces.jsonl \
  --export-certificates-json /external/path/certificates.json \
  --sqlite-index /external/path/trace_index.sqlite
```

### Artifact-Backed Imports

Result rows and certificate artifacts are audited separately. A row can be
verified while its JSON or Lean artifact is missing from local storage; that
does not change the terminal form, but it means the archive is not fully
replayable yet.

Basic summary:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --summary-only
```

Artifact-backed directory export:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --out /external/path/mathgraph_import_artifact_backed \
  --load-artifacts
```

With relative artifact paths:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --out /external/path/mathgraph_import_artifact_backed \
  --load-artifacts \
  --artifact-base /external/path
```

Strict hash mode:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --out /external/path/mathgraph_import_artifact_backed \
  --load-artifacts \
  --strict-artifact-hashes
```

Missing artifacts do not change truth status. Hash mismatches are audit
failures, not mathematical proof failures, unless strict mode is requested. A
verified row without loaded artifacts is still a verified result trace, but not
yet a fully replayable certificate archive.

Artifact provenance is tracked per path column. MathGraph distinguishes
canonical artifacts, prior/input artifacts, and executed Lean artifacts. A hash
is checked only when the hash column is applicable to that exact path. Prior or
input paths without a corresponding hash are counted as
`hash_not_applicable`, not mismatches. Strict mode fails only on applicable hash
mismatches.

## CertificateCorpus

`CertificateCorpus` is a lightweight in-memory layer for replaying and querying
imported terminal traces. It is not a database and does not verify new claims by
itself.

```python
from mathgraph import CertificateCorpus, TerminalForm

corpus = CertificateCorpus.from_json("/external/path/mathgraph_import/traces.json")
print(corpus.summary())
print(len(corpus.query(terminal_form=TerminalForm.FINITE_COUNTERMODEL)))
print(corpus.get_by_claim_hash("claimabc123"))
```

The corpus can also load JSONL ledgers, query by source/target indices or route,
and compute stable trace hashes plus a Merkle root for audit summaries.

### CertificateCorpus-Assisted Kernel Replay

`Kernel` can optionally consult a `CertificateCorpus` before trying local
routes. This reuses imported verified memory without making MathGraph a passive
database: only corpus traces that already terminate as `VERIFIED_PROOF` /
`VERIFIED` or `FINITE_COUNTERMODEL` / `REFUTED` can be replayed.

```python
from mathgraph import CertificateCorpus, Kernel

corpus = CertificateCorpus.from_json("/external/path/mathgraph_import/traces.json")
kernel = Kernel(corpus=corpus)
trace = kernel.prove("x = x", "x * x = x", source_idx=30, target_idx=40)
print(trace.terminal_form)
print(trace.metadata["corpus_lookup_mode"])
```

Obstructions, pending rows, missing verification, and conflicting verified
corpus hits are not promoted.

## Building a Certificate Lawbook

`CertificateLawbook` turns imported traces into a compact query/explain memory:
route summaries, source/target basins, proof payloads, and countermodel
patterns. It is still an index over verified traces, not a replacement for Lean
or MathGraph verification.

```python
from mathgraph import CertificateLawbook

lawbook = CertificateLawbook.from_json("/external/path/traces.json")
print(lawbook.summary())
print(lawbook.route_card("finite_countermodel"))
print(lawbook.explain_pair(1033, 2637))
```

```bash
python scripts/build_lawbook_summary.py \
  --traces-json /external/path/traces.json \
  --out /external/path/lawbook_summary.json \
  --route-summary /external/path/route_summary.json
```

## Route Instructions

Route instruction cards summarize what verified lawbook routes have certified
so far. They are guidance for future routing, not proof generators.

```python
from mathgraph import CertificateLawbook, build_route_instruction

lawbook = CertificateLawbook.from_json("traces.json")
instruction = build_route_instruction(lawbook, "finite_countermodel")
print(instruction.to_dict())
```

```bash
python scripts/build_route_instructions.py \
  --traces-json traces.json \
  --out route_instructions.json
```

## Pair Advice

Pair advice suggests evidence routes for a new source/target pair. If the pair
already exists in the lawbook, it returns the known terminal certificate. If not,
the result is advisory only and remains `NAMED_OBSTRUCTION` / `UNKNOWN`.

```python
from mathgraph import CertificateLawbook, advise_pair

lawbook = CertificateLawbook.from_json("traces.json")
advice = advise_pair(lawbook, "x = x ◇ y", "x = x ◇ x")
print(advice.to_dict())
```

```bash
python scripts/advise_pair.py \
  --traces-json traces.json \
  --source "x = x ◇ y" \
  --target "x = x ◇ x" \
  --out advice.json
```

## Certificate Task Planning

The task planner converts pair advice into a compact execution plan. It does not
prove or refute anything; it names the next evidence required for promotion.

```python
from mathgraph import CertificateLawbook, plan_certificate_task

lawbook = CertificateLawbook.from_json("traces.json")
task = plan_certificate_task(lawbook, "x = x ◇ y", "x = x ◇ x")
print(task.to_dict())
```

```bash
python scripts/plan_certificate_task.py \
  --traces-json traces.json \
  --source "x = x ◇ y" \
  --target "x = x ◇ x" \
  --out task.json
```

## Running Planned Certificate Tasks Safely

The task runner is a mock/safe execution shell. It does not prove or refute
unknown claims; it records what would be attempted next and emits residuals for
future constructors.

```bash
python scripts/run_certificate_tasks.py \
  --tasks-json /external/path/planned_tasks.json \
  --out /external/path/task_run_mock/
```

Directory mode writes `summary.json`, `outcomes.json`, `outcomes.jsonl`, and
`residual.json`. Mock proof-template and countermodel-search outcomes remain
`NAMED_OBSTRUCTION` until a real verified proof or finite countermodel
certificate exists.

## Persistent LawbookStore + KernelOracle

`LawbookStore` is a small SQLite memory layer over verified terminal traces.
`KernelOracle` queries that memory and explains exact hits; it does not generate
proofs, search countermodels, or promote advisory output.

```bash
python scripts/build_lawbook_store.py \
  --traces-json /external/path/traces.json \
  --out /external/path/lawbook.sqlite \
  --replace

python scripts/query_kernel_oracle.py \
  --store /external/path/lawbook.sqlite \
  --source "x = x ◇ y" \
  --target "x = y ◇ x"
```

Unknown means no exact verified trace was found. It does not mean false. This
persistent memory is the foundation for derived certificate generation, chewing
harnesses, API service layers, and H-Tilt scheduling.

## Derived Certificate Generation

Derived certificates amplify the lawbook without new oracle calls. They are
logical compositions of already verified traces, stored separately from
primitive certificates.

```text
A=>B, B=>C => A=>C
B=>A, B⇏C => A⇏C
A⇏B, C=>B => A⇏C
```

Directionality matters. Derived false certificates are accepted only when the
same countermodel witness remains valid by weakening the source or strengthening
the target. Primitive exact hits still take precedence over derived hits.

```bash
python scripts/derive_certificates.py \
  --store /external/path/lawbook.sqlite \
  --out-jsonl /external/path/derived.jsonl \
  --import-to-store \
  --max-per-rule 10000
```

## Pair Outcome Dataset and Compounding Diagnostics

The outcome dataset exports primitive, derived, unknown, and advisory rows into
one training and diagnostic surface. It does not promote any claim; it measures
whether the corpus is becoming structurally richer.

```bash
python scripts/build_outcome_dataset.py \
  --store /external/path/lawbook.sqlite \
  --out-jsonl /external/path/pair_outcomes.jsonl \
  --out-json /external/path/pair_outcomes.json \
  --diagnostics /external/path/compounding_diagnostics.json \
  --episode-id v19_1_plus_derived \
  --equation-count 4694
```

Key metrics include `derived_per_primitive`, `corpus_density`, `route_yield`,
`derivation_yield`, and `trust_level_counts`. This is the substrate for future
router learning, dashboard/API metrics, and H-tilt scheduling.

## Route Learner v1

Route Learner v1 builds deterministic constructor/route policy cards from pair
outcomes. It learns success basins from verified and derived evidence, then
uses those basins to recommend future route pressure.

```bash
python scripts/build_route_policy.py \
  --outcomes-jsonl /external/path/pair_outcomes.jsonl \
  --out-policy-json /external/path/route_policy_cards.json \
  --out-policy-jsonl /external/path/route_policy_cards.jsonl \
  --out-stats /external/path/route_learner_stats.json \
  --min-support 1
```

Optional recommendation:

```bash
python scripts/build_route_policy.py \
  --outcomes-jsonl /external/path/pair_outcomes.jsonl \
  --recommend-source "x = x ◇ y" \
  --recommend-target "x = x ◇ x"
```

Route learner scores are search pressure, not truth. They feed future scheduler
and planner priorities; they do not prove, refute, invoke Lean, search
countermodels, or promote unknowns.

## H-Tilt Scheduler v1

H-Tilt Scheduler v1 consumes oracle memory, route policies, and candidate pairs
to produce a prioritized certificate work queue. It is deterministic and
transparent: formal viability signals become proposal pressure.

```bash
python scripts/schedule_certificate_tasks.py \
  --pairs-jsonl /external/path/candidate_pairs.jsonl \
  --lawbook-store /external/path/lawbook.sqlite \
  --outcomes-jsonl /external/path/pair_outcomes.jsonl \
  --out-tasks-json /external/path/scheduled_tasks.json \
  --out-tasks-jsonl /external/path/scheduled_tasks.jsonl \
  --out-stats /external/path/scheduler_stats.json \
  --top-k 100 \
  --beta 1.0
```

H-tilt priority is scheduling pressure, not truth. The scheduler decides what
to try next; it does not prove, refute, invoke Lean, search countermodels, or
promote unknowns. Full spectral H-tilt with killed generator `K = L - V`
remains future work.

## End-to-End Flywheel

The flywheel runner composes the repo layers into one reproducible pipeline:

```text
traces.json -> LawbookStore -> Derived Certificates -> Outcome Dataset
-> Route Policy -> H-Tilt Schedule -> Flywheel Report
```

```bash
python scripts/run_mathgraph_flywheel.py \
  --traces-json /external/path/traces.json \
  --out /external/path/mathgraph_flywheel \
  --schedule-top-k 100
```

Optional candidate scheduling:

```bash
python scripts/build_candidate_frontier.py \
  --equations-path /external/path/equations.txt \
  --matrix-path /external/path/etp_matrix_full_best_bool.npy \
  --store-path /external/path/mathgraph_flywheel/lawbook_store.sqlite \
  --out /external/path/candidate_frontier.jsonl \
  --max-candidates 5000

python scripts/run_mathgraph_flywheel.py \
  --traces-json /external/path/traces.json \
  --store-path /external/path/mathgraph_flywheel/lawbook_store.sqlite \
  --out /external/path/mathgraph_flywheel \
  --unknown-pairs-jsonl /external/path/candidate_frontier.jsonl \
  --derived-limit 100000

python scripts/build_task_queue.py \
  --schedule-jsonl /external/path/mathgraph_flywheel/scheduled_tasks.jsonl \
  --out /external/path/task_queue.jsonl \
  --max-tasks 1000 \
  --min-priority 0.2

python scripts/run_finite_countermodel_tasks.py \
  --task-queue-jsonl /external/path/task_queue.jsonl \
  --out /external/path/finite_countermodel_results.jsonl \
  --max-tasks 100 \
  --max-order 4 \
  --exhaustive-order-limit 3 \
  --random-tables-per-order 0

python scripts/import_finite_countermodels.py \
  --results-jsonl /external/path/finite_countermodel_results.jsonl \
  --store-path /external/path/mathgraph_flywheel/lawbook_store.sqlite \
  --out /external/path/countermodel_import_summary.json
```

Candidate frontier rows are scheduling candidates only. They can come from
matrix false/true entries or structural unknown pairs, but they are never
marked as proven or refuted by the frontier builder.

The task queue is constructor-ready, but still non-promotable until a
verifier/constructor executes it and emits an accepted terminal certificate.
The finite countermodel executor is the first executor: it only handles
`finite_countermodel_search` tasks, checks finite tables exactly, and writes
result rows without promoting them into permanent lawbook memory.
The importer revalidates those result rows and promotes only verified finite
countermodels into `LawbookStore`. Finite search failures are not imported as
truth; unknown remains unknown.

The flywheel does not add mathematical authority. It composes verified memory,
sound derived certificates, diagnostics, route policy, and scheduling pressure
into `flywheel_report.json` and `flywheel_report.md`.

## End-to-End Chewing Smoke

The chewing smoke harness runs the finite-countermodel feedback loop on a small
deterministic batch:

```bash
python scripts/run_chewing_smoke.py \
  --equations-path /content/equations.txt \
  --matrix-path /content/etp_matrix_full_best_bool.npy \
  --traces-json /content/drive/MyDrive/MathGraphKernel/github_imports/repo_cli_v19_1_artifact_provenance_fixed/traces.json \
  --out-dir /content/drive/MyDrive/MathGraphKernel/chewing_smoke_runs/smoke_001 \
  --max-frontier-pairs 100 \
  --top-k-schedule 50 \
  --max-tasks 50 \
  --max-countermodel-order 3
```

This is a correctness smoke, not a benchmark. It builds a frontier, schedules
candidate pressure, builds a task queue, runs finite countermodel tasks,
revalidates imported results, probes `KernelOracle`, then rebuilds derived
certificates and outcome diagnostics. Scheduler scores are not truth, executor
rows are not permanent memory until the importer accepts them, and unknown
remains unknown.

For a self-contained synthetic system harness, use:

```bash
python scripts/run_vision_smoke.py \
  --out-dir /tmp/mathgraph_vision_smoke \
  --max-order 3
```

`run_vision_smoke.py` uses the current finite executor API and writes
`schedule.jsonl`, `task_queue.jsonl`, `finite_results.jsonl`, `lawbook.sqlite`,
`oracle_probe.json`, and a report. If the scheduler produces only
`obstruction_analysis` rows for the tiny synthetic examples, it creates a
transparent fallback queue of finite-countermodel tasks so the checked finite
path is still exercised. The fallback is still non-promotable until the finite
executor verifies a table and the importer revalidates it.

## Real Asset Smoke

For Colab or Drive-backed runs, first discover the available assets:

```bash
python scripts/discover_mathgraph_assets.py \
  --out-dir /tmp/mathgraph_assets
```

Then run the real chewing smoke:

```bash
python scripts/run_real_chewing_smoke.py \
  --out-dir /tmp/mathgraph_real_smoke \
  --max-frontier-pairs 250 \
  --frontier-mode small_sample \
  --frontier-scan-limit 5000 \
  --top-k-schedule 100 \
  --max-tasks 100
```

Asset discovery is read-only unless `--copy-assets` or `--symlink-assets` is
requested. Missing assets are reported explicitly instead of being hidden.
The real smoke composes raw assets into frontier possibilities, H-Tilt search
pressure, task queue rows, finite verification, conservative promotion, and
oracle memory. Scheduler rows are not truth, and finite imports are revalidated
before they become primitive `LawbookStore` certificates.

For fast diagnostics, use `--frontier-mode small_sample` and
`--frontier-scan-limit N`; this bounds candidate-pair scanning before schedule
construction. To bypass frontier generation entirely, pass a tiny scheduler
compatible file with `--candidate-pairs-jsonl /path/to/candidates.jsonl`.

## Certificate Processing and Assimilation Pipeline

The assimilation pipeline is the repeatable real-asset episode runner for
growth experiments. It performs ingestion, processing, construction,
verification, promotion, assimilation, and residual export:

```text
traces/equations -> LawbookStore -> derived closure -> outcome dataset
-> route policy -> bounded frontier -> schedule -> task queue
-> finite construction -> revalidation/import -> refreshed memory + residuals
```

```bash
python scripts/run_certificate_assimilation.py \
  --traces-json /path/to/traces.json \
  --equations-path /path/to/equations.txt \
  --matrix-path /path/to/etp_matrix_full_best_bool.npy \
  --out-dir /tmp/mathgraph_assimilation_episode \
  --frontier-mode small_sample \
  --frontier-scan-limit 500 \
  --max-frontier-pairs 100 \
  --top-k-schedule 50 \
  --max-tasks 50 \
  --max-countermodel-order 3 \
  --progress
```

The current live constructor is finite-countermodel construction. Lean proof
construction remains pending. The pipeline promotes only imported and
revalidated terminal certificates; advisory rows, scheduler scores, finite
search misses, unknowns, and obstruction-analysis-only rows remain residual
work.

## Certificate Assimilation To Episode Learning

Episode learning turns one or more assimilation run directories into reusable
route and constructor diagnostics:

```bash
python scripts/learn_from_assimilation_episode.py \
  --episode-dir /tmp/mathgraph_assimilation_episode \
  --out-dir /tmp/mathgraph_episode_learning \
  --progress
```

It reads the task outcome ledger, new certificates, duplicates, residual
obstruction candidates, and diagnostics reports. It writes route yields,
constructor yields, residual basin rows, duplicate motifs, new certificate
motifs, next-run recommendations, and a Markdown report. The learning layer is
diagnostic only: duplicates, residuals, advisory rows, and finite search misses
are never promoted.

For CI/local validation of the whole repo-native pipeline:

```bash
python scripts/validate_real_asset_pipeline.py \
  --repo-root . \
  --out-dir /tmp/mathgraph_validate_real_assets \
  --skip-install \
  --allow-missing-assets \
  --allow-synthetic-fallback \
  --max-frontier-pairs 50 \
  --top-k-schedule 20 \
  --max-tasks 20
```

The validator captures subprocess stdout/stderr under `logs/`, writes
`validation_summary.json` and `validation_report.md`, and never reports
synthetic fallback as real data.

## Real Asset Materialization

Use the materializer when assets exist outside the repository and you want a
stable local bundle for validation:

```bash
python scripts/materialize_mathgraph_assets.py \
  --out-dir /tmp/mathgraph_assets
```

With explicit paths:

```bash
python scripts/materialize_mathgraph_assets.py \
  --traces-json /path/to/traces.json \
  --equations-path /path/to/equations.txt \
  --matrix-path /path/to/etp_matrix_full_best_bool.npy \
  --out-dir /tmp/mathgraph_assets
```

Then validate against the materialized bundle:

```bash
python scripts/validate_real_asset_pipeline.py \
  --traces-json /tmp/mathgraph_assets/assets/traces.json \
  --equations-path /tmp/mathgraph_assets/assets/equations.txt \
  --matrix-path /tmp/mathgraph_assets/assets/etp_matrix_full_best_bool.npy \
  --out-dir /tmp/mathgraph_validation \
  --allow-synthetic-fallback
```

`routelean_results_v19_1.parquet` is reported as a related artifact, not as
`traces.json`. The tool does not synthesize missing real assets.

## Verify API v1

`MathGraphVerifier` is the high-level middleware interface for a source/target
claim:

```python
from mathgraph import MathGraphVerifier, VerifyRequest

result = MathGraphVerifier().verify(
    VerifyRequest(
        source="x * y = x",
        target="x * y = y",
        max_countermodel_order=3,
    )
)
print(result.status, result.terminal_form)
```

CLI:

```bash
python scripts/verify_claim.py \
  --store-path lawbook.sqlite \
  --source "x * y = x" \
  --target "x * y = y" \
  --out result.json \
  --max-countermodel-order 3
```

Models propose. MathGraph verifies, refutes, or obstructs. Verifiers decide.
The API checks known primitive/derived lawbook memory first, then may run a
bounded finite countermodel construction for magma equations. Scheduler scores
remain search pressure only, and finite search failure is never proof.

## Progress and Diagnostics

Long-running MathGraph CLIs support lightweight progress logging:

```bash
python scripts/run_real_chewing_smoke.py \
  --out-dir /tmp/mathgraph_real_smoke \
  --progress \
  --heartbeat-sec 10 \
  --progress-jsonl /tmp/mathgraph_real_smoke/progress.jsonl
```

Use `--heartbeat-sec 10` in Colab or CI when commands may run quietly for a
while. Progress events are standard-library JSONL records with stage start,
progress, done, failed, elapsed seconds, counts, and rates where available.
Progress logging is diagnostic only; it never promotes a terminal certificate
or changes verification semantics.

### How To Debug Long Runs

For Colab, CI, or remote shells, give every long command a JSONL progress file
and keep a second terminal on the live log:

```bash
tail -f /tmp/mathgraph_real_smoke/progress.jsonl
```

The repo-native validator forwards progress flags to child commands and stores
their streamed output under `logs/`:

```bash
python scripts/validate_real_asset_pipeline.py \
  --repo-root . \
  --out-dir /tmp/mathgraph_validate_real_assets \
  --allow-missing-assets \
  --allow-synthetic-fallback \
  --progress \
  --heartbeat-sec 10

tail -f /tmp/mathgraph_validate_real_assets/logs/real_chewing_smoke.stdout.txt
```

If a stage times out, the validator records a `stage_error` event and includes
the last 50 streamed lines in `validation_summary.json`.

## Optional Lean Verification

The Lean adapter only checks local Lean files or snippets with the `lean`
executable on your `PATH`. It does not generate proofs, create Lake projects,
add Mathlib, or interpret Lean failures as counterexamples.

```python
from adapters.lean_adapter import detect_lean, verify_lean_code

print(detect_lean())
result = verify_lean_code("theorem t : True := True.intro")
print(result["status"])
```

A Lean success means the artifact typechecked. A Lean failure is not a
counterexample and not a mathematical verdict. MathGraph still requires accepted
claims to end in exactly one terminal form:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL`
- `NAMED_OBSTRUCTION`

External verification events are audit records attached to traces. They do not
change the terminal form by themselves:

```python
from mathgraph import Kernel

kernel = Kernel(finite_magmas=[])
trace = kernel.prove(
    "x * y = x",
    "x * y = y",
    lean_code="theorem t : True := True.intro",
)
print(trace.terminal_form)
print(trace.external_verifications)
```

Later versions may add exact-claim Lean proof certificates. Until then, an
unrelated Lean typecheck is not promoted to `VERIFIED_PROOF`.

## JSONL Ledgers

MathGraph traces can be written as append-only JSONL reproducibility records.
Ledgers are generated proof-run artifacts, so keep them outside Git. GitHub
stores source code, tests, docs, and small manifests, not generated runs.

```python
from mathgraph import JsonlLedger, Kernel

ledger = JsonlLedger("/tmp/mathgraph-run/ledger.jsonl")
kernel = Kernel(ledger=ledger)
kernel.prove("x = x", "x * x = x")

for trace in ledger.load_all():
    print(trace.terminal_form)
```

Each line stores a serialized trace, its trace hash, and a timestamp. The
records are replayable: a later audit can reload the ledger, recompute trace
hashes, and check what was actually claimed.

## Episode Runner v2

Episode Runner v2 consumes a Frontier v2 task queue, executes only
`finite_countermodel_search` rows through the existing verifier/importer
boundary, emits continuation traces, and regenerates replay, route policy,
residual atlas, and next-frontier artifacts.

```bash
python scripts/run_episode_v2.py \
  --frontier-task-queue /tmp/root_lab/frontier_v2/frontier_v2_task_queue.jsonl \
  --store /tmp/episode_v2/lawbook.sqlite \
  --out-dir /tmp/episode_v2
```

Advisory task kinds are remembered as traces, not treated as certificates.
Finite search failure is still not proof.

## Multi-Episode Compounding Harness

The multi-episode harness runs Episode Runner v2 repeatedly, feeds each next
frontier into the next bounded episode, and reports whether the unknown becomes
smaller, sharper, more clustered, more nameable, more constructible, and more
compressible.

```bash
python scripts/run_multi_episode_harness.py \
  --initial-frontier-task-queue /tmp/root_lab/frontier_v2/frontier_v2_task_queue.jsonl \
  --store /tmp/multi_episode/lawbook.sqlite \
  --out-dir /tmp/multi_episode \
  --episodes 3
```

The compounding score is diagnostic only. It does not verify or refute claims.

## Integrity Layer

MathGraph can hash traces and certificates with deterministic JSON, making them
content-addressed traces. JSONL ledgers can be summarized with a Merkle root and
audited by replaying the serialized records. This is an integrity layer for
mathematical traces, not cryptocurrency.

```python
from mathgraph.hashing import hash_trace
from mathgraph.replay import replay_ledger

trace = Kernel().prove("x = x")
print(hash_trace(trace))
print(replay_ledger("/tmp/mathgraph-run/ledger.jsonl")["merkle_root"])
```

Hashes and Merkle roots preserve record integrity. They do not turn candidates
into verified proofs, and generated ledger files should stay outside GitHub.

## Repository Layout

- `mathgraph/`: core kernel, typed terms, equations, certificates, graph store
- `adapters/`: finite magma, Lean, and external theorem prover boundaries
- `examples/`: small runnable demos
- `scripts/`: future Colab-friendly scripts
- `tests/`: pytest test suite
- `docs/`: design notes and verification contract

Generated artifacts belong in Google Drive or external artifact storage, not in
GitHub.
