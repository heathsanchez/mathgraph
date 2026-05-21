# SAIR Breakthrough Loop v1

The SAIR breakthrough runner lifts the finite magma breakthrough loop from the
built-in toy corpus to real SAIR-style equation pairs when local data is
available.

```text
equations.txt + implication matrix
-> sampled FALSE pairs EQ1 => EQ2
-> advisory constructor bank
-> deterministic finite magma checker
-> ExternalCertificate
-> PromotionGate
-> Lawbook candidate
-> Reason Atlas feedback
-> reprioritised next episode
```

## Inputs

By default the runner looks for:

- `/content/equations.txt`
- `/content/etp_matrix_full_best_bool.npy`

If either file is missing, it falls back to the built-in breakthrough demo
corpus. This keeps the smoke path runnable without external artifacts.

The matrix is interpreted as:

```text
matrix[i, j] == True  means equation i implies equation j
matrix[i, j] == False means a candidate FALSE pair
```

The matrix is used for sampling and reporting. It is not a truth boundary.

## Equation Normalization

The loader normalizes SAIR binary operator syntax such as `◇`, `⋄`, `·`, and
`∙` into the finite magma parser's `*` syntax. Equations remain ordinary
equational terms over one binary operation.

## Finite Countermodel Boundary

For a sampled FALSE pair `EQ1 => EQ2`, MathGraph attempts finite magma tables.
A successful finite countermodel requires:

1. the table satisfies `EQ1` globally over all assignments;
2. the table violates `EQ2` at a concrete witness assignment;
3. the result is wrapped as an `ExternalCertificate`;
4. `PromotionGate` accepts the finite boundary evidence.

Finite search failure is residual feedback only. It is not a proof that the
implication is true.

## Run

```bash
python scripts/run_sair_breakthrough_loop.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --max-tasks 100 \
  --episodes 3 \
  --attempt-budget 8
```

Outputs are written to `/tmp/mathgraph_sair_breakthrough_loop_v1/` by default
unless Google Drive is mounted at the configured Colab path.

Key outputs:

- `sair_breakthrough_summary.json`
- `sair_episode_metrics.csv`
- `sair_attempts.csv`
- `sair_accepted_certificates.jsonl`
- `sair_rejected_attempts.jsonl`
- `sair_residual_tasks.csv`
- `sair_reason_atlas_feedback.jsonl`
- `sair_lawbook_candidates.jsonl`
- `sair_constructor_priority_shift.csv`
- `sair_report.md`

## Scaling Path

This runner is deliberately small and deterministic. The next step is to plug
in the full SAIR false factory and broader constructor families, then use the
accepted finite-countermodel traces for root operator induction and persistent
Reason Atlas scheduling over real residuals.
