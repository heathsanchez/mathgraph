# End-to-End Breakthrough Validation Pack

The breakthrough validation pack is the canonical evidence runner for the
current MathGraph FALSE-side chain. It composes the existing repo-native stages
instead of introducing another isolated experiment:

```text
held-out Lawbook -> exact attribution -> micro-basin distillation
-> active residual discovery -> proposal synthesis
-> residual-conditioned synthesis -> source-law repair
-> repaired countermodel certificates -> persistent replay
```

## Why It Exists

Individual scripts prove local pieces. The validation pack proves that the
pieces compose into a reproducible evidence bundle with metrics, safety gates,
certificates, and a final Markdown report.

Durable certificates matter more than route gain. A route improvement is
advisory until a finite checker or proof verifier accepts an artifact. A
finite-checked repaired countermodel certificate is FALSE-side evidence because
the checker verifies that the source equation holds globally and the target is
violated by a witness.

## Breakthrough Classes

- `no_signal`: no recoveries, no certificates, no transfer.
- `safe_infrastructure_only`: all safety gates pass, but no new recovery.
- `finite_core_transfer`: held-out Lawbook gain exists without repaired
  certificates.
- `residual_repair_signal`: source-law repair recovers pairs but certificates
  were not packaged.
- `durable_certificate_breakthrough`: repaired finite countermodel certificate
  artifacts exist and safety passes.
- `compounding_breakthrough`: durable certificates plus persistent replay gain.
- `strong_compounding_breakthrough`: compounding gain across multiple seeds with
  no safety violations.

## Boundary

The pack enforces:

- finite-search failure never implies TRUE
- failed repair never implies TRUE
- advisory routes, PQ-IR, micro-basins, obstructions, route memory, and proposal
  synthesis cannot promote truth
- FALSE requires finite-checked source-holds/target-violates evidence
- TRUE requires proof-verifier or Lean evidence

## Commands

Fallback:

```bash
python scripts/run_end_to_end_breakthrough_validation.py \
  --out-dir /tmp/mathgraph_breakthrough_validation_demo \
  --fallback-demo \
  --seed 1729
```

Smoke real:

```bash
python scripts/run_end_to_end_breakthrough_validation.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/breakthrough_validation_smoke \
  --smoke-real \
  --seed 20260524
```

Full real:

```bash
python scripts/run_end_to_end_breakthrough_validation.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/breakthrough_validation_full \
  --full-real \
  --seeds 20260524,20260525,20260526,20260527,20260528 \
  --train-pairs 2500 \
  --heldout-pairs 2500 \
  --true-pairs 1000 \
  --repair-budget 40 \
  --max-n 4
```

The output directory contains `breakthrough_validation_summary.json`,
`breakthrough_validation_report.md`, stage manifests, safety gates, certificate
summaries, residual summaries, an artifact manifest, and SQLite.
