# SAIR Stage 2 Breakthrough Replay - 2026-05-26

This directory documents how to replay the official 2026-05-26 SAIR Stage 2
breakthrough evidence pack.

## Required Files

```text
/content/equations.txt
/content/etp_matrix_full_best_bool.npy
```

## Required Branch / Repo

Use a MathGraph branch containing:

```text
scripts/run_sair_stage2_breakthrough_search.py
scripts/replay_official_sair_stage2_breakthrough.py
```

## Canonical Replay Command

```bash
python scripts/run_sair_stage2_breakthrough_search.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/official_sair_stage2_breakthrough_replay \
  --seeds 20260524,20260525,20260526,20260527,20260528 \
  --episodes 4 \
  --max-n 4 \
  --repair-budget 40 \
  --train-false 2500 \
  --heldout-false 2500 \
  --sample-true 1000 \
  --policy-search-rounds 5 \
  --strict-admission \
  --fail-if-no-compounding
```

Equivalent wrapper command:

```bash
python scripts/replay_official_sair_stage2_breakthrough.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/official_sair_stage2_breakthrough_replay \
  --full
```

## Expected Metrics

- `finite_checked_countermodels > 0`
- `total_gain_over_baseline > 0`
- `failed_search_promoted_true_count == 0`
- `advisory_promoted_truth_count == 0`
- `true_contamination_count == 0`

## Known 2026-05-26 Result

- `finite_checked_countermodels`: `36`
- `accepted_false_certificates`: `36`
- `total_gain_over_baseline`: `8.0`
- `lawbook_gain_over_baseline`: `1.4`
- selected components: `baseline`, `lawbook`, `microbasin`
- rejected components: `repair`

## Caveat

Exact counts may vary if the implementation changes. The replay gate is positive
held-out gain plus zero safety violations. Advisory memory remains advisory
unless finite checker or proof verifier evidence accepts a terminal form.
