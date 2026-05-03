# MathGraph

MathGraph is a lightweight generative verification kernel for verifiable
mathematics and trustworthy AI.

It is not a passive database and not a static encyclopedia. It is a living,
typed semantic hypergraph where axioms, definitions, theorems, proofs,
transformations, finite countermodels, obstructions, and verification traces can
be represented as formal nodes and edges.

Every accepted claim must collapse into exactly one terminal form:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL`
- `NAMED_OBSTRUCTION`

The first practical testbed is SAIR Stage 2: equational implication over
magmas. The repository is organized as a general MathGraph kernel rather than a
competition-only solver.

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
