# Metabolic Cycle Testbed

MathGraph v16.12 adds an executable local loop for the kernel doctrine:

```text
Claim frontier
-> Lawbook lookup
-> Advisor / scheduler
-> Constructor
-> Verifier / revalidator
-> Terminal form
-> Lawbook
-> Derived closure
-> Residual / obstruction update
-> Route learning pressure
-> Next frontier
```

The testbed is intentionally small. It can run on a synthetic SAIR/ETP-like
frontier without external artifacts, Lean, Mathlib, or network access. Its job is
to prove that the feedback loop is wired, not that MathGraph has solved ETP.

## Terminal Contract

Every serious claim may become one of:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL`
- `NAMED_OBSTRUCTION`

Everything else is advisory pressure. Route scores, proof motifs, lemma
candidates, residual groups, and Lean sketches do not change truth status.
Finite-search failure is residual evidence, not proof.

## Running

```bash
python scripts/run_metabolic_cycle.py \
  --store /tmp/mathgraph_cycle.sqlite \
  --out-dir /tmp/mathgraph_cycle \
  --max-tasks 100 \
  --max-countermodel-order 3 \
  --exhaustive-order-limit 3 \
  --random-tables-per-order 0 \
  --synthetic-seed \
  --strict \
  --json
```

The runner writes:

- `frontier_initial.jsonl`
- `scheduled_tasks.jsonl`
- `finite_countermodel_results.jsonl`
- `derived_certificates.jsonl`
- `proof_motifs.json`
- `lemma_candidates.json`
- `residual_obstructions.jsonl`
- `next_frontier.jsonl`
- `metabolic_cycle_summary.json`
- `metabolic_cycle_result.json`
- `metabolic_cycle_report.md`

## Diagnostics

`residual_compression_gain` measures how much unresolved work shrank:

```text
(unresolved_before - unresolved_after) / unresolved_before
```

`derived_amplification_factor` measures derived certificates per primitive
terminal artifact added.

`better_shaped_unknown` is true when the episode leaves more structure than it
started with: fewer residuals, grouped named obstructions, derived closure,
informative route yields, or a sharper next frontier.

## Truth Boundary

The metabolic report explicitly separates:

- authoritative primitive proof and countermodel traces;
- derived certificates with chain provenance;
- named obstruction or residual pressure;
- proof motifs and lemma candidates, which remain advisory.

MathGraph shapes the next search. Verifiers decide truth.

