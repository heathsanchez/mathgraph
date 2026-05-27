# Official SAIR Stage 2 Breakthrough Evidence Pack - 2026-05-26

## What This Proves

This pack proves, for its accepted FALSE cases, finite-checker-backed
countermodel evidence: each accepted FALSE certificate is a finite magma table
that satisfies the source equation and violates the target equation. It also
supports the bounded empirical claim that strict-admission memory compounding
improved held-out SAIR Stage 2 recovery over baseline while preserving zero
trust-boundary violations.

## What This Does Not Prove

This is not a TRUE-side theorem-proving result and not a general autonomous
theorem-proving claim. Advisory routes, failed finite searches, repair traces,
classifier scores, and unverified true candidates cannot promote truth.

## Executive Summary

This document records the official 2026-05-26 SAIR Stage 2 breakthrough evidence
pack. This is a FALSE-side finite-countermodel certificate-production and
memory-compounding result on real SAIR Stage 2 data.

The strict confirmation run produced finite-checker-backed countermodel
certificates, preserved the trust boundary, rejected a harmful advisory repair
component, and achieved positive held-out verification gain over baseline.

This is not a claim of general autonomous theorem proving. Advisory memory
improves route selection but does not promote truth.

## What Was Run

The run used the official SAIR Stage 2 breakthrough search path:

```text
real SAIR inputs
-> official end-to-end evidence pack
-> scorecard diagnostics
-> conservative policy selection
-> harmful component rejection
-> final evidence pack
```

The selected policy retained baseline finite search, Lawbook memory, and
micro-basin memory. It rejected the downstream repair component because its
held-out marginal contribution was negative in this run.

## Exact Command Shape

```bash
python scripts/run_sair_stage2_breakthrough_search.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/sair_stage2_breakthrough_rescue_grid_20260526_222949/main_a_5seed_2500_strict_confirmation \
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

## Real Inputs

- Equations: `/content/equations.txt`
- Matrix: `/content/etp_matrix_full_best_bool.npy`
- Source mode: `real_sair`
- Real SAIR used: `true`

## Strict Confirmation Metrics

| Metric | Value |
| --- | ---: |
| final_classification | `verified_memory_compounding_breakthrough` |
| benchmark_passed | `true` |
| breakthrough_gate_passed | `true` |
| strict_admission_passed | `true` |
| finite_checked_countermodels | `36` |
| accepted_false_certificates | `36` |
| total_gain_over_baseline | `8.0` |
| lawbook_gain_over_baseline | `1.4` |
| failed_search_promoted_true_count | `0` |
| advisory_promoted_truth_count | `0` |
| true_contamination_count | `0` |

## Trust-Boundary Audit

Only verifier-backed evidence can promote terminal claims.

- FALSE claims require finite-checker-backed source-holds / target-violates
  evidence.
- TRUE claims require Lean, trusted importer, chain-audit, or proof-verifier
  evidence.
- Failed finite search is never TRUE.
- Lawbook, Reason Atlas, H-Tilt, PQ-IR, micro-basin memory, policy selection,
  and route priors remain advisory unless a verifier or finite-checker boundary
  accepts the claim.

The strict confirmation run had zero trust-boundary violations:

- failed finite search promoted TRUE: `0`
- advisory route promoted truth: `0`
- TRUE contamination: `0`

## Component Selection Result

Selected components:

- `baseline`
- `lawbook`
- `microbasin`

Rejected components:

- `repair`

The repair component was rejected by the conservative policy selector because it
hurt held-out marginal yield in this evidence pack. This is the important point:
the pack does not merely accumulate routes; it can reject a harmful advisory
route while preserving finite-checker admission.

## What The Result Proves

This result proves, in the bounded SAIR Stage 2 FALSE-side setting, that
MathGraph can:

- load real SAIR Stage 2 equation and matrix inputs;
- preserve the verifier boundary;
- produce finite-checker-backed countermodel certificates;
- keep advisory route memory separate from terminal truth;
- diagnose component-level marginal contribution;
- reject a harmful advisory component;
- reuse memory to improve held-out verification/recovery over baseline.

## What It Does Not Prove

This is not a claim of general autonomous theorem proving.

It does not prove TRUE-side Lean theorem proving, proof synthesis, or universal
MathGraph compounding. It does not allow advisory routes, failed finite search,
or repair traces to promote truth.

## Artifact Layout

Root:

```text
/content/drive/MyDrive/SAIR_MathGraph/sair_stage2_breakthrough_rescue_grid_20260526_222949
```

Best strict confirmation output:

```text
/content/drive/MyDrive/SAIR_MathGraph/sair_stage2_breakthrough_rescue_grid_20260526_222949/main_a_5seed_2500_strict_confirmation
```

Top-level summaries:

```text
colab_breakthrough_grid_summary.md
colab_breakthrough_grid_summary.json
```

Expected strict confirmation files include:

- `breakthrough_search_summary.json`
- `breakthrough_scorecard.csv`
- `component_marginal_contributions.csv`
- `canonical_policy.json`
- `selected_components.csv`
- `rejected_components.csv`
- `policy_rationale.md`
- `final_evidence_pack/`

## How To Replay

Use the wrapper:

```bash
python scripts/replay_official_sair_stage2_breakthrough.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/official_sair_stage2_breakthrough_replay \
  --full
```

The replay gate is positive held-out gain plus zero trust-boundary violations.
Exact counts may vary if implementation details change.

## How To Interpret Failure Modes

- Negative `total_gain_over_baseline`: not a memory-compounding breakthrough.
- Nonzero `failed_search_promoted_true_count`: hard trust-boundary failure.
- Nonzero `advisory_promoted_truth_count`: hard trust-boundary failure.
- Nonzero `true_contamination_count`: hard safety failure.
- Positive certificates but non-positive gain: durable certificate evidence, not
  memory compounding.

## Next Engineering Step

Do not add new advisory layers until this evidence path stays reproducible and
legible. Next high-value work is improving the magnitude and robustness of the
compounding gain, plus TRUE-side proof verification.
