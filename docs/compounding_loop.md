# Canonical Compounding Loop

This runner is the repo-level command for the narrow claim:

```text
boundary-backed memory should make later verifier-directed search cheaper,
higher-yield, or better routed
```

It is not a proof that every future task compounds. It is an executable loop
that measures whether memory helped on the chosen workload.

## Boundary

The loop preserves the trust boundary:

- advisory artifacts may guide search
- failed finite search is residual evidence, not `TRUE`
- Reason Atlas, H-Tilt, route scores, and Lawbook attention are scheduling
  signals
- only finite checker / verifier / importer / chain-audit boundary evidence can
  produce terminal candidates

## Pipeline

```text
baseline finite-checker search
-> boundary-backed finite countermodel certificates
-> in-run Lawbook / Reason memory
-> memory-guided constructor order
-> decode-to-verify diagnostics
-> residual and cost metrics
```

## Fallback vs Real Mode

Fallback mode is deterministic and requires no external files:

```bash
python scripts/run_mathgraph_compounding_loop.py \
  --allow-fallback-demo \
  --out-dir /tmp/mathgraph_compounding_demo
```

Real SAIR mode requires explicit corpus files:

```bash
python scripts/run_mathgraph_compounding_loop.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/MathGraph_Compounding_Run \
  --episodes 3 \
  --train-pairs 250 \
  --eval-pairs 250 \
  --attempt-budget 12
```

If real files are not supplied, the runner refuses real mode unless
`--allow-fallback-demo` is passed.

## Artifacts

- `compounding_report.json`: machine-readable report with metric kinds
- `compounding_report.md`: short readable summary
- `episode_summary.csv`: per-episode overview
- `policy_summary.csv`: per-policy metrics
- `lawbook_hits.csv`: memory retrieval/action-change rows
- `decode_to_verify.csv`: decoded memory-to-checker action rows
- `residuals_by_episode.csv`: residual task rows
- `artifact_manifest.json`: generated artifact paths
- `run_metadata.json`: config and timestamp

## Metric Interpretation

- `lawbook_hit_rate`: advisory retrieval/usefulness signal
- `decode_success_rate`: diagnostic signal that a memory hit produced a
  concrete checker action
- `residual_reduction_vs_baseline`: diagnostic comparison against baseline
- `certificates_per_attempt`: diagnostic efficiency signal
- `oracle_fraction_captured`: only present when an oracle/reference policy is
  available

Every JSON metric is labelled as `verified_metric`, `advisory_metric`, or
`diagnostic_metric`.

## Future Work

- persistent production Lawbook integration
- recursive residual atlas
- TRUE-side Lean proof routing
- multi-domain compounding
- cost ledger
- obstruction atlas
