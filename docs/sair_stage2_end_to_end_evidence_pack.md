# Official SAIR Stage 2 Evidence Pack

The SAIR Stage 2 evidence pack is the canonical product proof command for
MathGraph on equational implication over magmas. It composes the existing
FALSE-side verification chain and writes one inspectable artifact directory.

The pack distinguishes three evidence levels:

- `VERIFIED`: finite-checker-backed countermodels or proof-verifier-backed TRUE
  artifacts.
- `ADVISORY`: Lawbook routes, Reason Atlas routes, H-Tilt scheduling,
  micro-basin recipes, proposal routes, and replay candidates.
- `RESIDUAL`: failed finite search, failed repair, unresolved claims, and
  unverified TRUE candidates.

Finite-search failure never implies TRUE.

## Canonical Real Command

```bash
python scripts/run_sair_stage2_end_to_end.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/sair_stage2_end_to_end_pack \
  --episodes 4 \
  --train-false 5000 \
  --heldout-false 5000 \
  --sample-true 1000 \
  --max-n 4 \
  --repair-budget 40 \
  --seeds 20260524,20260525,20260526 \
  --strict-admission \
  --write-report
```

Real mode requires both SAIR files. A fallback demo may be used for tests, but
it is labeled `safe_infrastructure_only` and is not product evidence.

## Fallback Wiring Command

```bash
python scripts/run_sair_stage2_end_to_end.py \
  --out-dir /tmp/mathgraph_sair_stage2_end_to_end_demo \
  --fallback-demo \
  --episodes 2 \
  --train-false 100 \
  --heldout-false 100 \
  --sample-true 50 \
  --seeds 1729 \
  --strict-admission \
  --write-report
```

## Artifact Pack

The runner writes:

- `executive_summary.md`
- `technical_report.md`
- `trust_boundary_audit.json` and `.csv`
- `episode_metrics.csv`
- `heldout_compounding_report.json` and `.csv`
- `certificate_manifest.csv`
- `finite_countermodels/`
- `true_candidates/`
- `named_obstructions.csv`
- `residual_frontier.csv`
- `lawbook.sqlite`
- `reason_atlas.sqlite`
- `replay_instructions.md`
- `reproducibility.json`
- `artifact_manifest.json`

Empty or non-applicable outputs are written explicitly instead of omitted.

## Classification

The final scorecard reports one of:

- `safe_infrastructure_only`
- `real_sair_safe_run`
- `durable_certificate_breakthrough`
- `heldout_memory_positive`
- `compounding_candidate`
- `compounding_breakthrough`
- `strong_compounding_breakthrough`

The classification is conservative. Durable certificates matter only when the
finite checker verifies that the source equation holds globally and the target
equation is violated with a witness. Advisory memory can guide routes, but it
cannot promote truth.

## Official SAIR Stage 2 Breakthrough Search

The breakthrough search adds scorecard diagnostics and conservative policy
selection on top of the official evidence pack. It is a selection layer, not a
new truth boundary.

```bash
python scripts/run_sair_stage2_breakthrough_search.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/breakthrough_search \
  --seeds 20260524,20260525,20260526,20260527,20260528 \
  --train-false 5000 \
  --heldout-false 5000 \
  --sample-true 1000 \
  --episodes 4 \
  --max-n 4 \
  --repair-budget 40 \
  --policy-search-rounds 5 \
  --strict-admission \
  --fail-if-no-compounding
```

The search decomposes baseline, Lawbook, micro-basin, and repair contributions;
rejects components with negative held-out marginal contribution; and writes a
canonical policy artifact. If the real run still has negative total gain, the
output remains honest: harmful components are disabled in the policy, but no
breakthrough label is claimed unless the policy-adjusted held-out scorecard has
positive gain and all trust-boundary counts are zero.

Fallback mode is a wiring check only:

```bash
python scripts/run_sair_stage2_breakthrough_search.py \
  --out-dir /tmp/mathgraph_breakthrough_fallback \
  --fallback-demo \
  --seeds 1729,1730 \
  --train-false 100 \
  --heldout-false 100 \
  --sample-true 50 \
  --episodes 2 \
  --policy-search-rounds 2 \
  --strict-admission
```
