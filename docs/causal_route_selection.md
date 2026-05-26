# Causal Route Selection

Persistent Exact Micro-basin Lawbook v1 proved that exact constructor memories
can be stored and replayed, but the first real smoke produced negative memory:
the memory was reused safely, yet it underperformed the current Lawbook proxy.

Exact attribution alone is not enough. A constructor can explain one marginal
gain and still fail to transfer to later micro-basins. Causal Route Selection
adds an advisory filter over persistent exact memories.

## What V2 Scores

For each route memory, v2 measures:

- support across replay rows
- episode count
- seed count
- gain over generic
- gain over the one-shot Lawbook proxy
- non-regression rate
- positive, neutral, and negative episode counts

The selector rewards stable positive gains and penalizes one-shot wins,
single-seed wins, negative episodes, and low support.

## What V2 Compares

The v2 benchmark compares:

- generic baseline
- one-shot held-out Lawbook
- v1 persistent memory
- v2 causal persistent memory

Current-episode evidence is never used to select routes for that same episode.

## Classifications

- `strong_compounding`: v2 improves over Lawbook and selected causal routes exist.
- `weak_compounding`: v2 improves over generic and selected causal routes exist.
- `neutral_safe_memory`: v2 is safe and non-regressing, but no positive gain is observed.
- `negative_memory`: v2 underperforms generic or Lawbook.
- `failed_safety`: any safety counter is nonzero.

## Boundary

All causal route rows are advisory:

- `advisory_only=True`
- `can_promote_truth=False`
- `status=causal_route_policy_advisory`

Finite-search failure never implies TRUE. Exact constructor attribution and
causal route scores are route-learning evidence, not terminal truth.

## Commands

Fallback:

```bash
python scripts/run_persistent_exact_microbasin_lawbook_v2_benchmark.py \
  --out-dir /tmp/mathgraph_persistent_exact_v2_demo \
  --fallback-demo \
  --seeds 1729,1730,1731,1732
```

Real ETP:

```bash
python scripts/run_persistent_exact_microbasin_lawbook_v2_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/persistent_exact_microbasin_lawbook_v2 \
  --seeds 20260524,20260525,20260526,20260527,20260528 \
  --train-pairs 1200 \
  --heldout-pairs 1200 \
  --true-pairs 500 \
  --episodes 2 \
  --repair-budget 40 \
  --max-n 4
```
