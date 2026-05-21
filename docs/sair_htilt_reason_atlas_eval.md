# Spectral H-Tilt Reason Atlas Evaluation

This layer wires spectral H-Tilt into persistent Reason Atlas scheduling. It is
not a verifier and not a new terminal form. It is advisory pressure over the
next continuation.

## Why H-Tilt Exists

Reason Atlas memory can contain many advisory entries: clean motifs, constructor
hints, route laws, root schemas, obstructions, and feedback traces. H-Tilt gives
MathGraph a way to estimate which advisory states look survivable under prior
feedback and which states are repeatedly killed by failed transfer, verifier
failure, obstruction, or residual expansion.

The estimator uses route telemetry to compute:

- `pi*`: survivor mass
- `h`: forward survival
- `q`: structural support
- `mu_beta`: tilted multiplicative bridge
- kill pressure: observed killing or failure pressure

These are scheduling signals only.

## Reason Atlas Wiring

`mathgraph.reason_atlas_htilt` reads `ReasonAtlasStore` entries and feedback
events, converts them into advisory `RouteTelemetryEvent` rows, estimates a
`SpectralHTiltEstimate`, maps state scores back onto entries, and updates entry
metadata:

- `htilt_score`
- `htilt_survivor_pi`
- `htilt_survival_h`
- `htilt_support_q`
- `htilt_mu_beta`
- `htilt_kill_pressure`
- `htilt_estimate_id`
- `htilt_applied_at`

The previous Reason Atlas priority is preserved in metadata before the new
priority is written.

## Boundary

H-Tilt scores are advisory. Reason Atlas entries are advisory. Motifs, root
schemas, route laws, queue rows, and scheduler priors are advisory.

They can guide constructor ordering, verifier-job selection, residual
prioritization, and route scheduling. They cannot emit `TRUE`, `FALSE`,
`VERIFIED_PROOF`, `REFUTATION_CERTIFICATE`, or `FINITE_COUNTERMODEL`.

Only a real checker/verifier result wrapped as an `ExternalCertificate` and
accepted by `PromotionGate` can become a terminal candidate.

## Held-Out Evaluation

`mathgraph.sair_htilt_scale_evaluation` compares:

- `base_constructor_order`
- `clean_motif_guided_order`
- `persistent_reason_atlas_order`
- `htilt_reason_atlas_order`
- `htilt_plus_clean_motif_order`
- `oracle_constructor_order`

Each policy actually attempts finite magma constructors on held-out pairs and
counts only PromotionGate-accepted finite-countermodel certificates.

Reported metrics include:

- certificate yield
- residual count
- mean and median attempts used
- PromotionGate accepts/rejects
- oracle fraction captured
- constructor entropy
- residual-basin entropy
- H-Tilt convergence
- top H-Tilt states

## Running

Real SAIR run:

```bash
python scripts/run_sair_htilt_reason_atlas_eval.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --train-pairs 250 \
  --eval-pairs 250 \
  --attempt-budget 12 \
  --episodes 4 \
  --repeat-runs 1 \
  --admit-motifs \
  --load-existing-atlas \
  --apply-htilt \
  --out-dir /tmp/mathgraph_sair_htilt_reason_atlas_eval_real
```

Fallback smoke:

```bash
python scripts/run_sair_htilt_reason_atlas_eval.py \
  --allow-fallback-demo \
  --train-pairs 20 \
  --eval-pairs 20 \
  --attempt-budget 8 \
  --episodes 2 \
  --repeat-runs 1 \
  --admit-motifs \
  --load-existing-atlas \
  --apply-htilt \
  --out-dir /tmp/mathgraph_sair_htilt_reason_atlas_eval_smoke
```

## Outputs

The runner writes:

- `htilt_estimate.json`
- `htilt_state_scores.csv`
- `htilt_reason_entry_scores.csv`
- `htilt_augmented_queue.csv`
- `htilt_policy_summary.csv`
- `htilt_task_results.csv`
- `htilt_usage_summary.csv`
- `final_sair_htilt_reason_atlas_report.json`
- `run_metadata.json`
- optional plots

These are run artifacts and should stay outside the repository.

## Future Work

- principled `V` discovery
- multi-seed large-scale H-Tilt evaluation
- H-Tilt over proof traces
- H-Tilt over finite countermodel trace root schemas
- H-Tilt over persistent Lawbook closure graphs
- stochastic multi-armed scheduling
- learned route proposal models
- TRUE-side Lean proof scheduler
