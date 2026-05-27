# Recursive Residual-Mined Memory Transfer

This page documents the repo-grade port of:

`MATHGRAPH / ETP -- RECURSIVE RESIDUAL-MINED MEMORY TRANSFER TEST v1`

## What This Proves

This result proves transferable, compressible residual-mined constructor memory
in the bounded ETP benchmark sense: compact advisory memory learned on one
FALSE slice transfers to unseen FALSE pairs, beats generic/random/shuffled
controls, preserves most recursive-memory gain after pruning, and keeps TRUE
contamination at zero.

## What This Does Not Prove

It does not certify mathematical truth. Residual-mined constructors, compact
atlas entries, and route scores are advisory route memory only. A FALSE
certificate still requires a finite magma satisfying the source and violating
the target, and failed finite search is never TRUE.

## What The Breakthrough Tested

The Colab run asked whether a compact residual-mined atlas trained on one slice
transfers to fresh unseen ETP FALSE pairs across seeds, without TRUE
contamination, while beating generic, random same-size, and shuffled same-size
controls.

Source run metrics:

- equations: `4694`
- matrix shape: `4694 x 4694`
- TRUE count: `8,178,279`
- FALSE count: `13,855,357`
- seeds: `1729, 42, 137`
- heldout FALSE pairs per split: `12,000`
- TRUE controls per seed: `2,000`
- generic mean recoveries: `11,405.5 / 12,000`
- recursive full memory mean recoveries: `11,642.333333 / 12,000`
- compact atlas mean recoveries: `11,639.666667 / 12,000`
- oracle mean recoveries: `11,731.0 / 12,000`
- compact gain vs generic: `+234.166667`
- compact beats random same size: `+205.0`
- compact beats shuffled atlas same size: `+86.958333`
- compact retains recursive gain: `0.989575`
- compact prunes recursive memory: `0.53`
- oracle gap captured: `0.68992`
- TRUE contamination max: `0`
- gates passed: `9/9`
- advisory boundary OK: `true`

## Public API

Modules:

- `mathgraph.recursive_residual_transfer`
- `mathgraph.compact_route_atlas`

Key objects:

- `ResidualMinedConstructor`
- `RouteEvaluation`
- `CompactAtlasEntry`
- `TransferGateResult`
- `RouteAttribution`
- `RecursiveTransferSummary`

Key functions:

- `evaluate_route_transfer(...)`
- `select_compact_atlas(...)`
- `compare_random_controls(...)`
- `compare_shuffled_controls(...)`
- `compute_transfer_gates(...)`
- `build_recursive_transfer_summary(...)`
- `write_recursive_transfer_artifacts(...)`

## Gates

The nine gate names are preserved exactly:

1. `compact_transfer_gain_vs_generic_positive`
2. `compact_beats_random_same_size`
3. `compact_beats_shuffled_atlas_same_size`
4. `compact_retains_recursive_gain`
5. `compact_prunes_recursive_memory`
6. `zero_true_contamination`
7. `positive_gain_in_enough_seeds`
8. `oracle_gap_captured`
9. `advisory_boundary_preserved`

## Trust Boundary

Residual-mined constructors are advisory memory.  Compact atlas entries and
route scores may guide route selection, but they cannot promote truth.

A FALSE certificate still requires a finite magma satisfying the source and
violating the target.  TRUE contamination is explicitly checked against TRUE
controls.  Failed finite search is residual information, not a TRUE proof.

## CLI

```bash
python scripts/run_recursive_residual_transfer.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/MathGraph_ETP_Recursive_Transfer \
  --seeds 1729 42 137 \
  --profile transfer_fast \
  --real-etp \
  --strict-advisory-boundary \
  --write-report
```

`--real-etp` runs the actual recursive residual-mined transfer engine: it
loads the raw equations and implication matrix, generates the finite magma bank,
builds the vectorized SAT cache, mines residual constructors across
generations, evaluates compact atlas routes and controls, and writes the full
artifact set. The summary includes `real_etp_used: true`.

The original 2026-05-23 source-run metrics are frozen under
`examples/evidence_packs/recursive_residual_transfer_v1_20260523/`. A real run
can compare against them:

```bash
python scripts/run_recursive_residual_transfer.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/MathGraph_ETP_Recursive_Transfer_RepoRun \
  --profile transfer_fast \
  --seeds 1729 42 137 \
  --real-etp \
  --compare-frozen-evidence recursive_residual_transfer_v1_20260523 \
  --strict-advisory-boundary \
  --write-report
```

The comparison separates `reproduced_breakthrough_shape` from
`reproduced_original_magnitude`. The repo real-ETP runner should reproduce the
breakthrough shape from raw ETP assets: gates pass, TRUE contamination remains
zero, the advisory boundary is preserved, and compact memory beats
generic/random/shuffled controls. Later repo runs may differ in numeric
magnitude because constructor generation is stochastic, so magnitude comparison
uses tolerance bands and reports deltas.

If real SAIR files are absent, use:

```bash
python scripts/run_recursive_residual_transfer.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /tmp/mathgraph_recursive_transfer_fallback \
  --fallback-demo \
  --strict-advisory-boundary \
  --write-report
```

Fallback output is classified as `safe_infrastructure_only` and must not be
reported as the real breakthrough.

To package the published source-run metrics through the same repo artifact path
without claiming a fresh rerun:

```bash
python scripts/run_recursive_residual_transfer.py \
  --out-dir /tmp/mathgraph_recursive_transfer_source_package \
  --package-source-run \
  --strict-advisory-boundary \
  --write-report
```

## Artifacts

The writer emits:

- `recursive_transfer_summary.json`
- `seed_summary.csv`
- `route_eval_by_seed_split.csv`
- `constructor_manifest.csv`
- `constructor_attribution.csv`
- `compact_atlas_eval.csv`
- `best_compact_by_seed_split.csv`
- `gate_results.csv`
- `recursive_transfer_report.md`
- `recursive_transfer.sqlite`

These artifacts are route-memory and transfer-audit artifacts. They are not
terminal MathGraph claim certificates unless a downstream verifier or finite
checker supplies explicit boundary evidence.
