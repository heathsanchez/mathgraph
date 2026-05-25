# Micro-basin Causal Distillation

The held-out Lawbook benchmark showed that advisory Lawbook replay can recover
some held-out finite-countermodel residuals beyond a generic route. The next
question is narrower: which constructor route likely caused the marginal
recovery?

Micro-basin distillation groups held-out pair outcomes by local PQ-IR geometry:
basin, deep IR candidate, quotient pressure, target separation pressure,
constraint loss, fresh-variable pressure, repeat/tail pressure, and skeleton
flags. These buckets are route diagnostics, not truth.

## Causal Distillation

In this module, causal distillation means reducing broad route memory into small
advisory constructor recipes that explain observed marginal recoveries. If exact
per-pair constructor attribution is available, the recipe is marked `exact`. If
only route order or family priors are available, it is marked
`route_prior_proxy`.

The proxy case is intentionally conservative: it is a plausible routing cause,
not a verified cause.

## Exact Constructor Attribution

When `heldout_recovery_eval.csv` includes `lawbook_gain_hit`,
`lawbook_gain_constructor_id`, and `lawbook_gain_constructor_family`, the
distiller uses exact first-hit attribution. Recipes emitted from these rows are
marked `attribution_mode=exact_constructor`.

Example:

```bash
python scripts/run_heldout_lawbook_compounding_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/heldout_exact_attribution \
  --seeds 20260524 \
  --train-pairs 300 \
  --heldout-pairs 300 \
  --true-pairs 100 \
  --episodes 2 \
  --repair-budget 20 \
  --max-n 4

python scripts/run_microbasin_distillation.py \
  --input-dir /content/heldout_exact_attribution \
  --out-dir /content/microbasin_exact_distillation \
  --min-microbasin-support 2 \
  --min-microbasin-gain 1
```

## Boundary

Micro-basin recipes, gain attribution, residual obstruction targets, and route
priors are all:

- `advisory_only=True`
- `can_promote_truth=False`
- `terminal_form=NONE`

They do not prove TRUE, do not refute FALSE by themselves, and do not turn
finite-search failure into truth. FALSE still requires a finite checker-backed
countermodel. TRUE still requires proof-verifier evidence.

## Outputs

```bash
python scripts/run_microbasin_distillation.py \
  --input-dir /path/to/heldout_or_persistent_artifacts \
  --out-dir /tmp/mathgraph_microbasin_distillation
```

Fallback demo:

```bash
python scripts/run_microbasin_distillation.py \
  --out-dir /tmp/mathgraph_microbasin_demo \
  --fallback-demo
```

The runner writes:

- `joined_recovery_features.csv`
- `microbasin_summary.csv`
- `microbasin_gain_attribution.csv`
- `minimal_constructor_recipes.csv`
- `residual_obstruction_targets.csv`
- `microbasin_distillation_summary.json`
- `microbasin_distillation_report.md`
- `microbasin_distillation.sqlite`

## Next Use

Minimal recipes are constructor synthesis candidates. Residual obstruction
targets are the next root nodes for residual-specific search. Both remain
advisory until a verifier or finite checker produces boundary-backed evidence.
