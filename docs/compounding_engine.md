# Multi-Episode Compounding Engine

`scripts/run_mathgraph_compounding_engine.py` is the repo-native ETP
compounding runner. It exercises the loop:

```text
episode -> constructors -> finite checking -> residuals -> obstruction atlas
-> repair constructors -> Lawbook update -> next episode
```

The runner is intentionally verifier-boundary strict. PQ-IR rows, route
policies, residual obstructions, repair families, and Lawbook reuse signals are
advisory scheduling objects. They cannot prove claims and cannot promote truth.

FALSE recovery is counted only when a finite magma satisfies the source equation
globally and violates the target equation at a concrete witness assignment.
Finite-search failure is recorded as residual evidence only. TRUE requires a
proof-producing route; this runner emits no TRUE terminal forms.

## Tiny Demo

```bash
python scripts/run_mathgraph_compounding_engine.py \
  --out-dir /tmp/mathgraph_compounding_demo \
  --episodes 2 \
  --tiny-demo
```

The tiny demo uses a built-in equation set and identity TRUE controls, so it is a
wiring and boundary check rather than a real ETP performance claim.

## Full ETP / SAIR Run

```bash
python scripts/run_mathgraph_compounding_engine.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/MathGraph_Compounding_Run \
  --episodes 4 \
  --train-false 18000 \
  --eval-false 14000 \
  --eval-true 9000 \
  --route-train-false 18000 \
  --route-eval-false 10000 \
  --max-n 5 \
  --repair-steps 30 \
  --seed 20260524
```

The script refuses real mode when the equation or matrix files cannot be loaded.

## Outputs

The output directory contains:

- `lawbook.sqlite`
- `compounding_summary.json`
- `compounding_report.md`
- `gate_results.csv`
- `cross_episode_policy_summary.csv`
- `cross_episode_policy_eval.csv`
- `cross_episode_obstruction_summary.csv`
- `constructor_bank_manifest.csv`
- `repair_gain_curve.csv`
- `repair_selected_constructors.csv`
- `quotient_repair_family_lawbook.csv`
- `obstruction_atlas.csv`
- `residual_queue.csv`
- `true_proof_template_summary.csv`

## Metrics

- `yield_rate`: fraction of held-out FALSE pairs recovered by finite
  countermodel checking.
- `true_contamination_count`: number of TRUE controls incorrectly hit by a
  FALSE route. This should be zero.
- `obstruction_entropy`: residual basin dispersion.
- `lawbook_reuse_rate`: advisory constructor-family reuse from prior episodes.
- `episode_lift_vs_baseline`: improvement over the generic route.

Compounding is evidence, not proof, when later episodes improve yield, residuals,
obstruction entropy, Lawbook reuse, or named obstruction coverage while preserving
zero TRUE contamination.
