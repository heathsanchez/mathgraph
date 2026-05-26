# Active Residual Constructor Discovery v1

Negative memory is useful when it points to what current route memory cannot
explain. Persistent memories can become safer by refusing unsupported replay,
but MathGraph also needs to create new constructor pressure from the residuals
that remain.

Active Residual Discovery reads held-out benchmark artifacts, groups pairs that
generic and Lawbook routes both missed, names residual micro-basins, proposes
constructor families from PQ-IR geometry, and evaluates those proposals.

## Loop

```text
residual -> obstruction -> constructor proposal -> finite/proxy check
-> certificate, Lawbook candidate, or residual
```

## Proposal Pressure

- fresh-variable escape -> `quotient_fresh_gate`, `fresh_absorber`
- target separation -> projection exceptions, diagonal escape, quotient spike
- repeat/tail pressure -> coupled projection and diagonal perturbation
- compression -> diagonal spike, row/column erasure, block selector
- expansion -> modular linear families
- general residual -> prior/projection/constant controls

## Boundary

Constructor proposals are advisory:

- `advisory_only=True`
- `can_promote_truth=False`

Positive proposal recovery is counted only as a discovery/evaluation result.
Terminal FALSE still requires finite-checker-backed countermodel evidence, and
finite-search failure never implies TRUE.

## Fallback Demo

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --out-dir /tmp/mathgraph_active_residual_discovery_demo \
  --fallback-demo \
  --seed 1729
```

## Real Artifact Run

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --input-dir /content/drive/MyDrive/SAIR_MathGraph/<previous_run>/baseline_large \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/active_residual_discovery_v1 \
  --min-support 3 \
  --max-proposals-per-basin 3 \
  --max-pairs-per-proposal 100 \
  --max-n 4 \
  --seed 20260524
```
