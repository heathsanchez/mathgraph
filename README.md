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

## Repository Layout

- `mathgraph/`: core kernel, typed terms, equations, certificates, graph store
- `adapters/`: finite magma, Lean, and external theorem prover boundaries
- `examples/`: small runnable demos
- `scripts/`: future Colab-friendly scripts
- `tests/`: pytest test suite
- `docs/`: design notes and verification contract

Generated artifacts belong in Google Drive or external artifact storage, not in
GitHub.
