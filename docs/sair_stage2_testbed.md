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
print(lawbook.source_summary(1033))
print(lawbook.explain_pair(1033, 2637))
```

The lawbook can report route counts, source/target basins, proof payloads, and
countermodel payloads. It does not replace Lean verification and does not
promote candidates. It is a memory/index layer over traces that already obey the
terminal-form contract.
