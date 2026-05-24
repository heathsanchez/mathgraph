# Autonomous Compounding Engine

The autonomous compounding façade is a repo-native entry point for the serious
ETP finite-recovery path.

It wraps `scripts/run_mathgraph_compounding_engine.py` rather than simulating
recovery. The serious path uses the finite magma satisfaction cache:

```text
constructor bank -> SAT cache -> route recovery -> residual atlas -> repair route -> lawbook
```

## Boundary

- FALSE recovery is counted only when a constructor satisfies the source law and
  violates the target law.
- TRUE controls audit contamination.
- Failed finite search is residual evidence, never TRUE.
- PQ-IR, route policies, residual obstructions, and repair family memory are
  advisory until a verifier/checker boundary accepts a terminal form.

## Tiny demo

```bash
python scripts/run_autonomous_compounding_engine.py \
  --out-dir /tmp/mathgraph_autonomous_demo \
  --tiny-demo \
  --episodes 2 \
  --sample-pairs 80 \
  --repair-budget 20
```

## Real ETP / SAIR run

```bash
python scripts/run_autonomous_compounding_engine.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/Autonomous_Run \
  --episodes 4 \
  --sample-pairs 4000 \
  --repair-budget 40
```

The runner refuses real mode unless the equation and matrix files are supplied.
