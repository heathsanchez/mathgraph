# SAIR Stage 2 Testbed

The first practical testbed is equational implication over magmas.

This repository is still a general MathGraph kernel. SAIR Stage 2 is represented
as one adapter-backed route:

1. Parse premise and conclusion equations over a binary operation `*`.
2. Evaluate them in a supplied finite magma.
3. Emit `FINITE_COUNTERMODEL` when the premises hold and the conclusion fails.
4. Emit a named obstruction when the supplied finite magma does not refute the
   implication.

Finite-search failure is not proof. A bounded finite magma route can produce an
explicit countermodel, or it can fail to find one. The latter is represented as
an obstruction unless another verified route proves the claim.

## Importing External SAIR Stage 2 Certificate Artifacts

Colab and Drive runs may produce route/certificate result tables such as CSV,
CSV.GZ, or Parquet files. These generated artifacts should stay outside GitHub.
MathGraph can import them from caller-supplied local paths:

```python
from adapters.sair_stage2_adapter import import_traces, load_results_table, summarize_results

records = load_results_table("/external/path/routelean_results_v19_1.parquet")
print(summarize_results(records))
traces = import_traces("/external/path/routelean_results_v19_1.parquet", limit=10)
```

The CLI can summarize external results and optionally export replayable source
artifacts:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --out /external/path/mathgraph_import/
```

Directory mode writes `summary.json`, `traces.json`, `traces.jsonl`,
`certificates.json`, and `index.sqlite`. For backwards compatibility, passing a
`.jsonl` path to `--out` writes the ledger to that file and `summary.json` next
to it. Use explicit flags such as `--summary-json`, `--export-traces-json`,
`--export-ledger-jsonl`, `--export-certificates-json`, and `--sqlite-index`
when a run needs exact output paths.

The importer is conservative. Verified-false rows become
`FINITE_COUNTERMODEL`. Explicit verified-true rows become `VERIFIED_PROOF`.
Rows without explicit true/false verification become `NAMED_OBSTRUCTION`.
Missing verification, failed finite search, or failed Lean execution is never
promoted to proof.

## Artifact-Backed Imports

The v19.1 importer can optionally inspect external JSON and Lean artifacts. This
records whether artifacts were found, hashed, loaded, and attached to the trace.
Artifact audit status is separate from mathematical verification status.

Basic summary:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --summary-only
```

Directory export:

```bash
python scripts/import_sair_stage2_results.py \
  --input /external/path/routelean_results_v19_1.parquet \
  --out /external/path/mathgraph_import
```

Artifact-backed export:

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

Generated traces, ledgers, SQLite indexes, Parquet files, CSV exports, and Lean
outputs should stay outside Git. Missing artifacts do not change truth status.
Hash mismatches are audit failures, not mathematical proof failures, unless
strict mode is requested. A verified row without loaded artifacts is still a
verified result trace, but not yet a fully replayable certificate archive.

### Artifact Provenance and Hash Checks

MathGraph distinguishes canonical, prior/input, and executed artifacts. For
example, `json_path` is treated as the canonical JSON artifact and can be paired
with `json_sha256`; `json_path_prior` and `json_path_v19_1_input` are audited as
prior/input artifacts unless they are the exact same normalized path as the
canonical artifact. Likewise, `lean_path` is canonical Lean, while
`executed_lean_path_v19_1` records what was actually executed.

A hash is only checked when the hash column applies to that exact path.
Prior/input paths without their own corresponding hash are counted as
`hash_not_applicable`, not mismatches. Strict hash mode fails only on applicable
hash mismatches. Mathematical verification status and artifact hash status
remain separate dimensions.

## Certificate Lawbook

The importer creates raw trace artifacts such as `traces.json` and
`traces.jsonl`. The lawbook layer summarizes, queries, and explains those traces
as reusable verification memory:

```python
from mathgraph import CertificateLawbook

lawbook = CertificateLawbook.from_json("/external/path/traces.json")
print(lawbook.summary())
print(lawbook.route_card("finite_countermodel"))
print(lawbook.explain_pair(1033, 2637))
```

The lawbook can report route counts, source/target basins, proof payloads, and
countermodel payloads. It does not replace Lean verification and does not
promote candidates. It is a memory/index layer over traces that already obey the
terminal-form contract.

## Route Instructions

Route instruction cards summarize verified lawbook routes into compact guidance
for future construction attempts. They describe what evidence a route used and
what warnings prevent overclaiming; they do not generate proofs.

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

The Pair Advisor uses lawbook traces and route instructions to suggest
candidate routes for a new source/target pair. Exact lawbook matches return the
known terminal trace. Unknown pairs remain advisory only and must not be treated
as proofs or refutations.

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

The task planner turns pair advice into an executable-looking checklist. It is
still not a verifier: exact lawbook hits require no new task, while unknown
pairs become planned proof-template, finite-countermodel search, or obstruction
analysis tasks.

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

## Batch Task Runner and Residual Ledger

The batch runner executes planned certificate tasks through conservative mock
executors. This is the safe chewing loop:

```text
plan -> attempt shell -> ledger -> residual split -> constructor improvement
```

```bash
python scripts/run_certificate_tasks.py \
  --tasks-json /external/path/planned_tasks.json \
  --out /external/path/task_run_mock/
```

The planner decides what kind of certificate work is appropriate. The runner
records mock outcomes, warnings, and residuals. It does not call Lean, does not
search finite magmas, and does not promote planned work to terminal proof or
refutation.

Failed finite search is not proof. Failed proof construction is not refutation.
Residuals are the next source of learning: they identify blocked routes,
missing evidence, and constructor improvements needed before any future
promotion.

## Persistent LawbookStore + KernelOracle

`LawbookStore` stores verified terminal traces in a compact SQLite memory layer.
It keeps enough JSON to explain and replay trace records while indexing common
questions by claim, source/target pair, source, target, route, terminal form,
and verification status.

```bash
python scripts/build_lawbook_store.py \
  --traces-json /external/path/traces.json \
  --out /external/path/lawbook.sqlite \
  --replace
```

`KernelOracle` is query and inspection only. It does not call constructors,
search finite magmas, invoke Lean, or create new terminal certificates.

```bash
python scripts/query_kernel_oracle.py \
  --store /external/path/lawbook.sqlite \
  --source "x = x ◇ y" \
  --target "x = y ◇ x"
```

Unknown means no exact verified trace was found, not false. Missing answers stay
`NAMED_OBSTRUCTION` / `UNKNOWN` and include anti-promotion warnings. This layer
is the foundation for derived certificate generation, chewing harnesses, API
service layers, and H-Tilt scheduling.

## Derived Certificate Generation

Derived certificates are the first recursive self-improvement layer over the
persistent lawbook. They do not call Lean, search finite magmas, or use route
scores. They compose existing verified traces with sound rules and store the
results separately from primitive certificates.

Accepted derivation rules:

```text
A=>B, B=>C => A=>C
B=>A, B⇏C => A⇏C
A⇏B, C=>B => A⇏C
```

The false rules are deliberately directional. In source weakening, the
countermodel for `B⇏C` satisfies stronger source `B`, so it also satisfies
weaker source `A` when `B=>A` is verified. In target strengthening, a witness
that refutes `B` also refutes any stronger target `C` when `C=>B` is verified.

```bash
python scripts/derive_certificates.py \
  --store /external/path/lawbook.sqlite \
  --out-jsonl /external/path/derived.jsonl \
  --out-json /external/path/derived.json \
  --import-to-store \
  --max-per-rule 10000
```

Primitive exact hits remain highest priority in `KernelOracle`. Derived hits
are returned only when no primitive exact trace exists, and they carry
`trust_level = "derived_from_verified_traces"` plus parent claims and the
derivation rule as evidence.

## Pair Outcome Dataset and Compounding Diagnostics

The pair outcome dataset turns primitive traces, derived certificates, oracle
unknowns, and advisory tasks into one compact row format. It is the input layer
for future route learning, H-tilt scheduling, dashboards, and API metrics.

```bash
python scripts/build_outcome_dataset.py \
  --store /external/path/lawbook.sqlite \
  --out-jsonl /external/path/pair_outcomes.jsonl \
  --out-json /external/path/pair_outcomes.json \
  --diagnostics /external/path/compounding_diagnostics.json \
  --episode-id v19_1_plus_derived \
  --equation-count 4694
```

Rows preserve origin and trust level:

- `primitive_trace`
- `derived_certificate`
- `oracle_unknown`
- `advisory_task`

Unknown and advisory rows remain non-promotable. They exist so later systems can
measure residuals without confusing open work with truth.

Compounding diagnostics include:

- `derived_per_primitive`
- `corpus_density`
- `route_yield`
- `derivation_yield`
- `trust_level_counts`

These metrics ask whether each episode made the next episode structurally
better. They do not train a router yet, schedule H-tilt yet, invoke Lean, or
search for countermodels.

## Route Learner v1

Route Learner v1 is the first explicit feedback edge:

```text
outcomes -> proposal weights
```

It builds deterministic policy cards from pair outcomes by grouping route
examples into small, explainable basins: variable-count buckets, operation and
length deltas, new target variables, rough skeleton agreement, and repeated
variable patterns.

```bash
python scripts/build_route_policy.py \
  --outcomes-jsonl /external/path/pair_outcomes.jsonl \
  --out-policy-json /external/path/route_policy_cards.json \
  --out-policy-jsonl /external/path/route_policy_cards.jsonl \
  --out-stats /external/path/route_learner_stats.json \
  --min-support 1
```

The learner can also emit a route recommendation for a new source/target pair:

```bash
python scripts/build_route_policy.py \
  --outcomes-jsonl /external/path/pair_outcomes.jsonl \
  --recommend-source "x = x ◇ y" \
  --recommend-target "x = x ◇ x"
```

The recommendation is advisory scheduling evidence only. It does not prove or
refute a claim, does not call Lean, does not search for countermodels, and does
not promote unknowns. Route learner confidence is search pressure, not truth.

## H-Tilt Scheduler v1

H-Tilt Scheduler v1 turns candidate pairs into a prioritized certificate work
queue. It consumes:

- optional `KernelOracle` memory to skip exact known certificates
- route policy cards or pair outcomes from Route Learner v1
- candidate source/target pairs

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

This is the first practical version of:

```text
formal viability signals -> proposal pressure
```

The score blends route prior, novelty, gap pressure, uncertainty, obstruction
pressure, and derived-amplification potential. It is deterministic and
explainable, but it is not a truth layer. No H-tilt score may promote a claim.
Only a verified proof, finite countermodel, or named obstruction can become a
terminal MathGraph outcome.

Full spectral H-tilt with Perron eigenvectors and killed generator `K = L - V`
remains future work.
