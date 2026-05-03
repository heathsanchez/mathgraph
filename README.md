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
