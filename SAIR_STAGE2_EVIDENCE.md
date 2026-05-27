# SAIR Stage 2 Evidence Pack

## One-Line Result

MathGraph has demonstrated bounded FALSE-side finite-countermodel certificate
production and positive held-out memory compounding on real SAIR Stage 2 data,
with zero trust-boundary violations.

## Why This Matters

AI systems can generate reasoning faster than humans can check it. MathGraph is
testing whether verification memory can compound while preserving formal trust
boundaries.

SAIR Stage 2 is a controlled testbed because every FALSE answer must become a
finite countermodel certificate and every TRUE answer ultimately requires proof
verification.

## What Was Run

The official 2026-05-26 strict confirmation used:

- real `equations.txt`
- real `etp_matrix_full_best_bool.npy`
- seeds `20260524` through `20260528`
- `train_false = 2500`
- `heldout_false = 2500`
- `sample_true = 1000`
- `episodes = 4`
- `max_n = 4`
- `repair_budget = 40`
- `policy_search_rounds = 5`
- `strict_admission`
- `fail_if_no_compounding`

## Result

```text
final_classification: verified_memory_compounding_breakthrough
finite_checked_countermodels: 36
accepted_false_certificates: 36
total_gain_over_baseline: 8.0
lawbook_gain_over_baseline: 1.4
failed_search_promoted_true_count: 0
advisory_promoted_truth_count: 0
true_contamination_count: 0
```

## What Was Selected And Rejected

Selected:

- `baseline`
- `lawbook`
- `microbasin`

Rejected:

- `repair`

The system did not blindly add every route. It diagnosed marginal contribution
and rejected the harmful component.

## Trust-Boundary Audit

- Failed finite search never became TRUE.
- Advisory memory never promoted truth.
- TRUE controls were not contaminated.
- Certificates counted only with finite-checker evidence.

## What This Proves

- Real SAIR inputs can be loaded and processed.
- Finite-checker-backed FALSE certificates can be produced.
- Strict admission can be preserved.
- Advisory memory can guide route selection.
- Held-out verification can improve over baseline.
- Harmful advisory components can be rejected.

## What This Does Not Prove

- It is not full autonomous theorem proving.
- It is not TRUE-side Lean proof synthesis.
- It is not universal domain-general compounding.
- It is not proof that all advisory routes are useful.
- It is not permission for advisory traces to promote truth.

## Replay

```bash
python scripts/replay_official_sair_stage2_breakthrough.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/official_sair_stage2_breakthrough_replay \
  --full
```

## Next Technical Frontier

The next frontier is improving robustness and magnitude of compounding gain,
promoting more exact finite-countermodel certificates into durable evidence,
building the TRUE-side Lean proof-verification path, and building Lean Project
Digest for existing Lean projects.
