# Repaired Countermodel Certificates v1

Source-Law Repair creates candidate structure. Finite checking creates
countermodel evidence. Repaired Countermodel Certificate Assimilation records
that evidence as durable Lawbook-ready artifacts.

## Distinctions

- Repaired candidate: a table produced by bounded repair.
- Finite-checked repaired countermodel: a repaired table where the checker
  confirms the source equation holds globally and the target equation is
  violated.
- Admitted certificate: a finite-checked repaired countermodel written with
  table hash, witness, repair trace, route provenance, and family summary.
- Advisory repair trace: evidence about search and repair pressure only.

Rejected rows are advisory:

- `terminal_form=NONE`
- `advisory_only=True`
- `can_promote_truth=False`

Accepted repaired countermodel certificates use:

- `terminal_form=FINITE_COUNTERMODEL`
- `trust_level=FINITE_VERIFIED`
- `advisory_only=False`
- `can_promote_truth=True`

This is FALSE-side finite-checker evidence. It does not promote TRUE.

## Flow

```text
residual -> target witness -> conditioned constructor -> source-law repair
-> finite checker -> repaired countermodel certificate -> Lawbook
```

The certificate family summary feeds exact micro-basin attribution, repair route
priors, constructor family selection, and future obstruction naming.

For the canonical investor/fund evidence pack, run the end-to-end breakthrough
validation command. It composes the repaired certificate layer with held-out
Lawbook, micro-basin distillation, active residual discovery, source-law repair,
and persistent replay.

## Commands

Fallback:

```bash
python scripts/run_repaired_countermodel_certificate_assimilation.py \
  --out-dir /tmp/mathgraph_repaired_certificate_demo \
  --fallback-demo \
  --seed 1729
```

Source repair with assimilation:

```bash
python scripts/run_source_law_repair.py \
  --out-dir /tmp/mathgraph_source_repair_with_certificates_demo \
  --fallback-demo \
  --assimilate-certificates \
  --seed 1729
```

Active discovery with repair and certificate assimilation:

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --out-dir /tmp/mathgraph_active_discovery_certificates_demo \
  --fallback-demo \
  --synthesize-constructors \
  --residual-conditioned-synthesis \
  --enable-source-law-repair \
  --assimilate-repaired-certificates \
  --repair-max-steps 1000 \
  --seed 1729
```

Real Colab:

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --input-dir /content/drive/MyDrive/SAIR_MathGraph/<previous_heldout_or_active_run> \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/active_residual_certificates_v1 \
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
  --enable-source-law-repair \
  --repair-strategies pressure_descent,target_frozen_pressure_descent,diagonal_first_repair,row_col_repair,quotient_merge_repair,two_phase_repair \
  --repair-max-steps 10000 \
  --repair-max-violations 128 \
  --assimilate-repaired-certificates \
  --max-n 4 \
  --seed 20260524
```
