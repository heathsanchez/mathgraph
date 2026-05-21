# Persistent SAIR Reason Atlas Scale Evaluation

MathGraph now has a scale evaluation path for the real SAIR finite-countermodel
loop. The purpose is to test whether a previous run can leave useful advisory
memory behind, and whether a later held-out run can turn that memory into more
certificates or lower search cost.

## Why This Layer Exists

The earlier real-corpus motif hygiene run proved a first product loop:

```text
PromotionGate-accepted finite countermodel traces
-> clean mechanism-only motifs
-> Reason Atlas scheduling
-> higher held-out certificate yield
-> residual compression
```

That is a run-local result. This layer adds persistence:

```text
Run N produces clean motifs
-> motifs are admitted to persistent Reason Atlas memory
-> Run N+1 loads those advisory priors
-> held-out finite checker attempts are rescheduled
-> certificate yield and residual compression are measured
```

## Boundary

Reason Atlas entries are not certificates. Clean motifs, constructor priors,
root schemas, route laws, scheduler scores, and atlas feedback remain advisory.
They may guide finite-countermodel search, proof search, constructor selection,
residual splitting, and scheduling. They may not emit `TRUE`, `FALSE`,
`VERIFIED_PROOF`, `FINITE_COUNTERMODEL`, or `REFUTATION_CERTIFICATE`.

Only a concrete checker result wrapped as an `ExternalCertificate` and accepted
by `PromotionGate` can become a terminal candidate.

## Admission

`mathgraph.sair_reason_atlas_admission` converts clean motifs and clean root
schemas into `ReasonAtlasEntry` rows. Admission is conservative:

- entries are always `advisory_only=True`
- verifier promotion is always false
- terminal truth forms are rejected
- provenance references PromotionGate-accepted finite-countermodel traces
- low-quality motifs are rejected
- duplicate motif IDs are deduplicated
- stronger re-admissions can supersede weaker records
- feedback events record admission, duplicate, supersession, scheduler gain,
  deletion-test signals, and rejection reasons

The persisted rows carry support, lift, clean atoms, constructor family, basin
family, carrier family, source traces, and scheduler-gain metadata when
available.

## Scale Evaluation

`mathgraph.sair_scale_evaluation` runs held-out SAIR scheduler policies with the
real finite checker and `PromotionGate`:

- `base_constructor_order`
- `clean_motif_guided_order`
- `persistent_reason_atlas_order`
- `persistent_reason_atlas_plus_clean_motif_order`
- `oracle_constructor_order`

The comparison records:

- certificate yield
- residual count
- attempt efficiency
- mean and median attempts used
- constructor entropy
- residual-basin entropy
- oracle fraction captured
- PromotionGate accepts and rejects
- loaded/admitted Reason Atlas entries
- advisory-boundary status

This is an empirical test, not a metadata self-score. Each held-out pair is
actually checked with finite magma constructors, and only PromotionGate-accepted
finite countermodel certificates count.

## Running Locally Or In Colab

Real SAIR run:

```bash
python scripts/run_sair_scale_reason_atlas_eval.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --train-pairs 250 \
  --eval-pairs 250 \
  --attempt-budget 12 \
  --repeat-runs 3 \
  --admit-motifs \
  --load-existing-atlas \
  --out-dir /tmp/mathgraph_sair_scale_reason_atlas_eval_real
```

Fallback smoke:

```bash
python scripts/run_sair_scale_reason_atlas_eval.py \
  --allow-fallback-demo \
  --train-pairs 30 \
  --eval-pairs 30 \
  --attempt-budget 8 \
  --repeat-runs 1 \
  --admit-motifs \
  --load-existing-atlas \
  --out-dir /tmp/mathgraph_sair_scale_reason_atlas_eval_smoke
```

The runner refuses to claim real SAIR evaluation unless real equations and the
matrix are loaded. Fallback mode is explicit.

## Outputs

The runner writes:

- `scale_eval_report.json`
- `scale_policy_summary.csv`
- `scale_task_results.csv`
- `scale_usage_summary.csv`
- `reason_atlas_admission_report.json`
- `admitted_reason_atlas_entries.jsonl`
- `loaded_reason_atlas_priors.csv`
- `compounding_gain_summary.csv`
- `run_metadata.json`
- optional plots for yield, residuals, attempts, oracle fraction, and entropy

Generated SQLite, CSV, JSONL, and plot artifacts belong outside the repository.
Keep them in `/tmp` for smoke runs or in Google Drive/external artifact storage
for real batch runs.

## Interpreting Results

The important comparison is persistent atlas versus baseline:

- higher certificate yield means retained motifs found more finite
  countermodels under the same budget
- lower residual count means more false implications were refuted
- lower mean attempts used means the scheduler found certificates faster
- higher oracle fraction captured means the advisory priors closed more of the
  reachable constructor gap

`PASS` means the persistent or combined policy beats or ties baseline on yield
or attempt efficiency while preserving the advisory boundary. `PROMISING` means
real checking and feedback worked but the gains were neutral or small. `FAIL`
means the empirical loop did not produce usable certificates, outputs, or
boundary-preserving results.

## Future Work

- full all-FALSE-pair recovery run
- production Lawbook admission workflow
- H-Tilt scheduling over persistent schema families
- root operator induction over finite countermodel traces
- TRUE-side Lean proof executor
- proof-constructor root induction
- multi-verifier `ExternalCertificate` ingestion
- learned schema proposal models
- second-order root operator algebra
