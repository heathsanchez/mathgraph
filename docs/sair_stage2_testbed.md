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

## End-to-End Flywheel Runner

The flywheel CLI composes the current repository layers into a reproducible
episode:

```text
traces.json
-> LawbookStore
-> Derived Certificates
-> Pair Outcome Dataset
-> Route Policy
-> H-Tilt Schedule
-> Flywheel Report
```

```bash
python scripts/run_mathgraph_flywheel.py \
  --traces-json /external/path/traces.json \
  --out /external/path/mathgraph_flywheel \
  --schedule-top-k 100
```

With candidate pairs:

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

The frontier builder can use matrix false/true entries and structural contrast
between equations to create high-value candidate pairs. It can also consult a
LawbookStore to skip exact primitive or derived certificates that are already
known. Frontier rows are candidate scheduling inputs only; they are not terminal
proofs or refutations.

The task queue is the constructor-ready chewing surface:

```text
build_candidate_frontier.py
-> schedule_certificate_tasks.py
-> build_task_queue.py
-> run_finite_countermodel_tasks.py
-> import_finite_countermodels.py
```

Task queue rows include route-specific required inputs, steps, success
criteria, failure modes, evidence, and anti-promotion warnings. They are still
not proof or refutation until a verifier or constructor executes them and emits
an accepted terminal certificate.

`run_finite_countermodel_tasks.py` is the first executor. It only runs
`finite_countermodel_search` rows, never proof-template rows, and never calls
Lean. A found finite countermodel gets `verification_status = "FINITE_VERIFIED"`
only after the finite table is checked exactly: the source holds for all
assignments and the target fails on a recorded witness. The result is still not
promoted into permanent lawbook memory by this executor.

`import_finite_countermodels.py` is the conservative promoter. It revalidates
each executor result by checking the table and witness again, skips duplicates
by default, and imports only verified `FINITE_COUNTERMODEL` rows into
`LawbookStore` as primitive countermodel certificates. `no_countermodel_found`,
parse failures, executor errors, and finite search failures are not imported as
truth. Unknown remains unknown.

## End-to-End Chewing Smoke

The smoke harness validates the complete finite-countermodel feedback loop on a
small deterministic batch:

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

This is a correctness smoke, not a benchmark. It writes the frontier, schedule,
task queue, finite-countermodel executor results, import summary, oracle probe,
derived refresh, outcome refresh, and a compact report. It proves that the
finite-countermodel chewing path is wired end to end: executor results are
revalidated before import, imported finite countermodels become primitive
LawbookStore memory, and `KernelOracle` should answer imported pairs as
`REFUTED` / `FINITE_COUNTERMODEL`.

Scheduler scores are search pressure, not truth. Missing countermodels are not
proofs, executor failures are not refutations, and unknown remains unknown.

For Colab/system harness checks that do not require external artifacts, run the
synthetic vision smoke:

```bash
python scripts/run_vision_smoke.py \
  --out-dir /tmp/mathgraph_vision_smoke \
  --max-order 3
```

This script uses the current executor interface:

```text
--task-queue-jsonl <queue>
--out <finite_results.jsonl>
--max-order 3
--max-tasks 10
```

It builds synthetic candidate pairs, schedules them, builds a task queue,
inspects the route/task-kind distribution, and falls back to explicit
`finite_countermodel_search` rows only when the scheduler created no finite
tasks. That fallback is a harness device, not truth: only executor rows with
`FINITE_COUNTERMODEL` / `FINITE_VERIFIED` can be revalidated and imported.

## Real Asset Smoke

Use asset discovery first when running in Colab or another external artifact
environment:

```bash
python scripts/discover_mathgraph_assets.py \
  --out-dir /tmp/mathgraph_assets
```

Then run the real chewing smoke:

```bash
python scripts/run_real_chewing_smoke.py \
  --out-dir /tmp/mathgraph_real_smoke \
  --max-frontier-pairs 250 \
  --top-k-schedule 100 \
  --max-tasks 100
```

The discovery tool checks exact candidate paths first and then performs a
guarded shallow search for `traces.json`, `equations.txt`, and
`etp_matrix_full_best_bool.npy`. It is read-only unless copy or symlink
materialization is requested.

The real smoke demonstrates:

```text
raw assets -> frontier possibilities -> H-Tilt search pressure -> task queue
-> finite verifier -> conservative promotion -> oracle memory
```

If assets are missing, the report records `missing_assets` and exits without
pretending the run succeeded. Scheduler rows are search pressure only, finite
search failure is obstruction evidence only, and only revalidated finite
countermodel results are imported as new primitive certificates.

For a repo-native local/CI validation wrapper:

```bash
python scripts/validate_real_asset_pipeline.py \
  --repo-root . \
  --out-dir /tmp/mathgraph_validate_real_assets \
  --skip-install \
  --allow-missing-assets \
  --allow-synthetic-fallback \
  --max-frontier-pairs 50 \
  --top-k-schedule 20 \
  --max-tasks 20 \
  --max-countermodel-order 3
```

The validator runs repo sanity checks, optional install/pytest, asset discovery,
real chewing smoke, and synthetic fallback only when allowed. It captures
stdout/stderr for every subprocess and writes a JSON/Markdown report. Fallback
certificates are clearly synthetic and must never be treated as real asset
certificates.

## Real Asset Materialization

When real assets exist outside Git, materialize them into a stable local bundle:

```bash
python scripts/materialize_mathgraph_assets.py \
  --out-dir /tmp/mathgraph_assets
```

Explicit paths always take priority:

```bash
python scripts/materialize_mathgraph_assets.py \
  --traces-json /path/to/traces.json \
  --equations-path /path/to/equations.txt \
  --matrix-path /path/to/etp_matrix_full_best_bool.npy \
  --out-dir /tmp/mathgraph_assets
```

Then validate using the materialized assets:

```bash
python scripts/validate_real_asset_pipeline.py \
  --traces-json /tmp/mathgraph_assets/assets/traces.json \
  --equations-path /tmp/mathgraph_assets/assets/equations.txt \
  --matrix-path /tmp/mathgraph_assets/assets/etp_matrix_full_best_bool.npy \
  --out-dir /tmp/mathgraph_validation \
  --allow-synthetic-fallback
```

The materializer supports `copy`, `symlink`, and `manifest-only` modes. It
reports `routelean_results_v19_1.parquet` as a related artifact only; parquet
results are not silently treated as `traces.json`. Missing assets are surfaced
as `complete=false`, never faked.

The flywheel writes:

- `lawbook_store.sqlite`
- `derived_certificates.jsonl`
- `derived_certificates_summary.json`
- `pair_outcomes.jsonl`
- `pair_outcome_diagnostics.json`
- `route_policy.json`
- `route_policy_stats.json`
- `scheduled_tasks.jsonl`
- `scheduled_tasks_summary.json`
- `flywheel_report.json`
- `flywheel_report.md`

It does not call Lean, search countermodels, or promote scheduler/advisory
rows. It only composes verified primitive traces, sound derived certificates,
diagnostics, route policies, and H-tilt scheduling pressure.
