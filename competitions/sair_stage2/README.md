# SAIR Stage 2 Competition Path

This folder is an isolated compiler target for the SAIR Stage 2 competition.
The main `mathgraph` package remains a general generative verification kernel:
API-first, reusable, and not shaped around one contest.

The final competition artifact is:

```text
competitions/sair_stage2/dist/solver.py
```

`solver.py` must be standalone, under 500KB, and use only the Python standard
library. It must not import `mathgraph`, `competitions`, NumPy, pandas, Lean,
Z3, SQLite, local CSV files, or network resources.

Offline scripts in this folder may use MathGraph and scientific Python when
distilling assets, but runtime solver logic must remain compact and auditable.

## Build

```bash
python competitions/sair_stage2/scripts/build_solver.py \
  --out competitions/sair_stage2/dist/solver.py \
  --max-bytes 500000

python competitions/sair_stage2/scripts/check_solver_size.py \
  --solver competitions/sair_stage2/dist/solver.py \
  --max-bytes 500000
```

## Run

```bash
python competitions/sair_stage2/dist/solver.py \
  --equation1 "x = x * y" \
  --equation2 "x = x * (y * z)"
```

Runtime API:

```python
solve(equation1, equation2, eq1_id=None, eq2_id=None)
solve_problem({"equation1": "...", "equation2": "..."})
```

## Validate

```bash
python competitions/sair_stage2/scripts/validate_solver.py \
  --solver competitions/sair_stage2/dist/solver.py \
  --equations-path /content/equations.txt \
  --matrix-path /content/etp_matrix_full_best_bool.npy \
  --sample-size 1000 \
  --out-dir competitions/sair_stage2/artifacts/validation_sample
```

If external ETP files are absent, distillation and full validation skip
gracefully with a clear report.

## Truth Boundary

- `VERIFIED_PROOF`: a replayable internal TRUE constructor succeeded.
- `FINITE_COUNTERMODEL`: a finite magma table satisfies equation 1 and violates
  equation 2.
- `NAMED_OBSTRUCTION`: no replayable proof or finite countermodel was found
  within the compact runtime budget.

Matrix truth can guide offline distillation, but it is not a certificate.
Finite search failure is not TRUE. A candidate family is not a proof. Lean
templates are not Lean verification.

