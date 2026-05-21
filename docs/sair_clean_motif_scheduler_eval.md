# SAIR Clean Motif Scheduler Evaluation

The first real SAIR breakthrough runs proved that MathGraph can find finite
countermodel certificates on real matrix-labeled false implication pairs. They
also exposed a hygiene problem: raw traces can contain junk atoms such as
`carrier:nan`, internal IDs, serialized dictionaries, status labels, and answer
or verifier-outcome leakage.

This layer cleans the trace stream before any motif can influence scheduling.

## Clean Mechanism Atoms

Allowed atoms are compact mechanism descriptors:

- `constructor:*`
- `constructor_family:*`
- `carrier:n2` through `carrier:n5`
- known SAIR basins such as `basin:projection_pressure`
- compact `eq_shape:*` structural features

Rejected atoms include unknown/nan values, raw equations as carriers, serialized
payloads, status/outcome/success labels, internal `breakthrough-constructor-hint`
IDs, and anything derived only from verifier success or the answer label.

## Mining Source

Positive motifs are mined only from `PromotionGate`-accepted finite
countermodel traces. Residuals and failures can inform obstruction analysis,
but they are not positive constructor-law evidence.

Motifs remain advisory. They guide constructor ordering; they do not emit
`TRUE`, `FALSE`, `VERIFIED_PROOF`, or `REFUTATION_CERTIFICATE`.

## Held-Out Scheduler Evaluation

The scheduler compares:

- `base_constructor_order`
- `random_constructor_order`
- `frequency_constructor_order`
- `clean_motif_guided_order`
- `root_schema_guided_order`
- `reason_atlas_guided_order`
- `oracle_constructor_order`

Each policy actually attempts finite constructors on held-out pairs and counts
only `PromotionGate`-accepted finite countermodel certificates. The key metrics
are certificate yield, residual count, attempts used, constructor entropy,
residual basin entropy, oracle gap, and oracle fraction captured.

## Run

```bash
python scripts/run_sair_clean_motif_scheduler_eval.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --train-pairs 80 \
  --eval-pairs 80 \
  --attempt-budget 10 \
  --out-dir /tmp/mathgraph_sair_clean_motif_scheduler_eval_real
```

For a local smoke without SAIR files:

```bash
python scripts/run_sair_clean_motif_scheduler_eval.py \
  --allow-fallback-demo \
  --train-pairs 20 \
  --eval-pairs 20 \
  --attempt-budget 8 \
  --out-dir /tmp/mathgraph_sair_clean_motif_scheduler_eval_smoke
```

## Outputs

- `hygiene_report.json`
- `clean_trace_rows.csv`
- `clean_constructor_motifs_ranked.csv`
- `clean_motif_family_summary.csv`
- `clean_motif_reason_atlas_entries.jsonl`
- `scheduler_policy_summary.csv`
- `scheduler_task_results.csv`
- `scheduler_usage_summary.csv`
- `final_clean_scheduler_eval_report.json`
- `run_metadata.json`

## Future Work

- full-scale run over all false pairs
- persistent production Lawbook admission of clean motifs
- H-Tilt scheduling over persistent Reason Atlas schema families
- root operator induction over finite countermodel traces
- proof-constructor root induction
- TRUE-side Lean executor
- multi-verifier `ExternalCertificate` ingestion
