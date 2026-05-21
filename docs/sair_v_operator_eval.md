# SAIR Principled V Discovery And H-Tilt Calibration

This layer tests candidate viability/killing operators for H-Tilt scheduling on
SAIR finite-countermodel search. It is the first repo-native path for asking:
which `V` operator turns training feedback into better held-out constructor
ordering?

## What V Means

In MathGraph, `V` is advisory killing or viability pressure. It summarizes where
routes, constructors, motifs, basins, or queue states tend to die under feedback:
rejections, residual persistence, dead-end constructors, high attempt cost, and
low transfer. H-Tilt uses this pressure to shape survivor geometry.

`V` is not truth. It never emits terminal forms.

## Candidate Operators

Implemented candidates include:

- `null_v`
- `random_v`
- `failure_density_v`
- `rejection_pressure_v`
- `residual_persistence_v`
- `constructor_deadend_v`
- `low_transfer_motif_v`
- `queue_stagnation_v`
- `basin_entropy_v`
- `attempt_cost_v`
- `novelty_pressure_v`
- `composite_static_v`
- `composite_adaptive_v`

All scores are finite, deterministic where seeded, and advisory-only.

## Calibration

`mathgraph.htilt_calibration` measures survivor distributions induced by
candidate V operators:

- normalized entropy
- effective dimension
- total variation distance from uniform
- maximum mass
- top-mass concentration
- convergence diagnostics
- score variance

These geometry metrics are useful only when paired with held-out evaluation.
The best operator is selected by certificate yield, residual compression, or
attempt efficiency, not by a pretty curve.

## Held-Out Evaluation

`mathgraph.sair_v_operator_evaluation` runs multi-seed finite-checker evaluation
over policies such as:

- baseline constructor ordering
- random constructor ordering
- clean motif ordering
- persistent Reason Atlas ordering
- one H-Tilt policy for each candidate V operator
- oracle constructor ordering

For every held-out pair, the policy actually attempts finite magma constructors.
Only finite checker successes accepted by `PromotionGate` count as certificates.

## Boundary

V operators, H-Tilt scores, survivor distributions, route priors, Reason Atlas
entries, motifs, root schemas, and scheduler scores are advisory. They may guide
constructor ordering and task scheduling. They cannot emit `TRUE`, `FALSE`,
`VERIFIED_PROOF`, `REFUTATION_CERTIFICATE`, or `FINITE_COUNTERMODEL`.

Only PromotionGate-accepted `ExternalCertificate` objects from an actual checker
or verifier can become terminal candidates.

## Running

Fallback smoke:

```bash
python scripts/run_sair_v_operator_eval.py \
  --allow-fallback-demo \
  --quick \
  --train-pairs 20 \
  --eval-pairs 20 \
  --attempt-budget 8 \
  --seeds 2 \
  --out-dir /tmp/mathgraph_sair_v_operator_eval_smoke
```

Real SAIR:

```bash
python scripts/run_sair_v_operator_eval.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --train-pairs 250 \
  --eval-pairs 250 \
  --attempt-budget 12 \
  --seeds 3 \
  --out-dir /tmp/mathgraph_sair_v_operator_eval_real
```

The script refuses to claim real SAIR evaluation unless real files are loaded.
Fallback mode must be explicit.

## Outputs

- `v_operator_seed_policy_summary.csv`
- `v_operator_task_results.csv`
- `v_operator_score_table.csv`
- `htilt_calibration_summary.csv`
- `selected_v_operator.json`
- `v_operator_eval_report.json`
- `reason_atlas_entries.jsonl`
- `clean_motifs_ranked.csv`
- `run_metadata.json`

Generated CSV/JSONL artifacts should stay outside the repository.

## Interpretation

The key question is whether a non-null V operator beats or ties persistent
Reason Atlas scheduling on yield or attempt efficiency across seeds.

Report fields to watch:

- selected V operator
- mean yield versus baseline
- mean yield versus persistent atlas
- residual compression
- attempt efficiency gain
- oracle fraction captured
- stability across seeds
- advisory boundary status

## Future Work

- learned V operators
- stochastic multi-armed constructor scheduling
- V over proof traces
- V over finite countermodel root schemas
- V over Lawbook closure graphs
- TRUE-side Lean proof scheduling
- H-Tilt over Mathlib digest traces
- second-order root operator algebra
- causal and grounding viability operators
