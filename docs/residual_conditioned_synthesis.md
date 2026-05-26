# Residual-Conditioned Constructor Synthesis v1

Proposal-specific synthesis turns a family label into finite magma tables. That
is the right structural loop, but a family label is still blunt. Residual-
conditioned synthesis shapes constructors from the residual implication pair
itself.

## Loop

```text
residual pair -> target witness -> partial constraints -> table completion
-> finite checker -> exact attribution
```

For an ETP claim `EQ1 => EQ2`, the synthesizer tries to force a target-side
witness where `EQ2` fails, then completes a small finite magma table so `EQ1`
holds globally. A generated table counts as recovered only after the finite
checker confirms:

- the source equation holds on every assignment
- the target equation is violated on at least one assignment

Failed completion is residual evidence only. It is never TRUE.

## Compared With Earlier Layers

- Family-level proposal: advisory pressure such as `fresh_absorber`.
- Proposal-specific constructor: a concrete table generated from that family.
- Residual-conditioned constructor: a concrete table shaped by `EQ1`, `EQ2`,
  witness pressure, and micro-basin features.
- Finite-checked recovery: a table accepted by the finite evaluator for a
  source-satisfying, target-violating pair.
- Terminal FALSE certificate: verifier-backed finite countermodel evidence with
  replayable provenance.

## Boundary

Witnesses, partial tables, completion attempts, and failed searches are
advisory. They use:

- `advisory_only=True`
- `can_promote_truth=False`

Recovered constructors are still checked through the finite evaluator before
they can be counted as FALSE-side evidence. No route, failed completion, or
residual condition can promote TRUE.

## Commands

Fallback:

```bash
python scripts/run_residual_conditioned_synthesis.py \
  --out-dir /tmp/mathgraph_residual_conditioned_demo \
  --fallback-demo \
  --seed 1729
```

Integrated fallback:

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --out-dir /tmp/mathgraph_active_discovery_conditioned_demo \
  --fallback-demo \
  --synthesize-constructors \
  --residual-conditioned-synthesis \
  --seed 1729
```

Real Colab:

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --input-dir /content/drive/MyDrive/SAIR_MathGraph/<previous_heldout_or_active_run> \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/active_residual_conditioned_synthesis_v1 \
  --min-support 3 \
  --max-proposals-per-basin 3 \
  --max-pairs-per-proposal 100 \
  --synthesize-constructors \
  --max-tables-per-proposal 32 \
  --max-pairs-per-constructor 100 \
  --residual-conditioned-synthesis \
  --max-conditioned-pairs 100 \
  --max-conditioned-witnesses-per-pair 8 \
  --max-conditioned-attempts-per-pair 32 \
  --conditioned-max-steps 5000 \
  --max-n 4 \
  --seed 20260524
```
