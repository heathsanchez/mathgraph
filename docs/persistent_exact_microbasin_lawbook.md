# Persistent Exact Micro-basin Lawbook v1

Persistent Exact Micro-basin Lawbook v1 tests whether exact local constructor
knowledge from earlier held-out episodes can be reused on later held-out
episodes.

V1 intentionally stores exact gains directly. A small real smoke showed this can
be safe but still become `negative_memory`: route memory was built and reused,
but the selector overfit local exact gains.

V2 adds Causal Route Selection. It scores memories by support, episode/seed
diversity, non-regression, and out-of-sample transfer before replaying them.

The input evidence comes from held-out Lawbook compounding runs with exact
constructor attribution. A reusable Lawbook entry is keyed by PQ-IR micro-basin
features and records which exact constructor family/id produced marginal
Lawbook recovery over generic routing.

## Trust Boundary

All entries produced here are advisory route-learning memory:

- finite-search failure never implies TRUE
- exact constructor attribution is not proof
- micro-basin recipes cannot promote truth
- terminal truth still requires a finite checker, proof verifier, trusted
  importer, or Lean verification boundary

Replay metrics are labeled proxy metrics when they use observed held-out
recovery columns. They answer whether prior memory would have selected useful
routes, not whether an informal theorem has been proved.

## Compounding Classes

- `strong_compounding`: persistent replay improves over the current Lawbook
  proxy and reuses exact recipes.
- `weak_compounding`: persistent replay improves over generic routing and reuses
  exact recipes.
- `neutral_memory`: memory is built and safe, but no gain is observed.
- `negative_memory`: persistent replay underperforms generic or Lawbook routing.

## Fallback Demo

```bash
python scripts/run_persistent_exact_microbasin_lawbook_benchmark.py \
  --out-dir /tmp/mathgraph_persistent_exact_demo \
  --fallback-demo \
  --seeds 1729,1730,1731
```

## Real ETP Benchmark

```bash
python scripts/run_persistent_exact_microbasin_lawbook_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/persistent_exact_microbasin_lawbook_v1 \
  --seeds 20260524,20260525,20260526,20260527,20260528 \
  --train-pairs 1200 \
  --heldout-pairs 1200 \
  --true-pairs 500 \
  --episodes 2 \
  --repair-budget 40 \
  --max-n 4
```

## V2 Causal Route Selection

```bash
python scripts/run_persistent_exact_microbasin_lawbook_v2_benchmark.py \
  --out-dir /tmp/mathgraph_persistent_exact_v2_demo \
  --fallback-demo \
  --seeds 1729,1730,1731,1732
```

See [causal_route_selection.md](causal_route_selection.md) for scoring rules and
classification details.

## Outputs

- `persistent_exact_microbasin_summary.json`
- `persistent_exact_microbasin_report.md`
- `persistent_exact_microbasin_lawbook.csv`
- `persistent_exact_microbasin_lawbook.sqlite`
- `persistent_replay_curve.csv`
- `persistent_replay_eval.csv`
- `persistent_recipe_reuse.csv`
- `terminal_form_audit.csv`
- `artifact_manifest.json`
