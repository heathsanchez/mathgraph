# Source-Law Repair Engine v1

Residual-conditioned synthesis can force a target equation to fail, but target
separation alone is not a countermodel. For `EQ1 => EQ2`, the finite table must
also satisfy `EQ1` globally.

Source-Law Repair starts with a target-violating table and runs bounded finite
search over table cells:

```text
target witness -> partial table -> target-violating candidate
-> source-law repair -> finite checker
```

The repair engine enumerates source-law violations, records which table cells
were touched by those assignments, scores cell pressure, and tries deterministic
cell rewrites. A move is accepted only when source violations decrease and the
target witness remains violated.

## Distinctions

- Target-violating candidate: a table with a witness for `EQ2` failure.
- Source-law repaired candidate: a table after bounded repair attempts.
- Finite-checked countermodel: a table where the checker confirms source holds
  globally and target is violated.
- Terminal FALSE certificate: finite-checker-backed evidence with replayable
  provenance.

Failed repair is residual evidence only. It is not TRUE, not a proof, and not an
accepted terminal claim.

Finite-checked successful repairs can be assimilated into repaired
countermodel certificate artifacts. The assimilation step records the table,
witness, repair trace, checker result, provenance, and Lawbook-ready family
summary. See [repaired_countermodel_certificates.md](repaired_countermodel_certificates.md).

The end-to-end validation pack composes source-law repair with upstream residual
discovery and downstream certificate assimilation. See
[end_to_end_breakthrough_validation.md](end_to_end_breakthrough_validation.md).

## Repair Strategies

- `pressure_descent`
- `target_frozen_pressure_descent`
- `diagonal_first_repair`
- `row_col_repair`
- `quotient_merge_repair`
- `stochastic_tie_break_repair`
- `two_phase_repair`

All strategies are deterministic for a fixed seed.

## Commands

Fallback source repair:

```bash
python scripts/run_source_law_repair.py \
  --out-dir /tmp/mathgraph_source_law_repair_demo \
  --fallback-demo \
  --seed 1729
```

Residual-conditioned synthesis with repair:

```bash
python scripts/run_residual_conditioned_synthesis.py \
  --out-dir /tmp/mathgraph_residual_conditioned_repair_demo \
  --fallback-demo \
  --enable-source-law-repair \
  --repair-max-steps 1000 \
  --seed 1729
```

Active discovery with repair:

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --out-dir /tmp/mathgraph_active_discovery_source_repair_demo \
  --fallback-demo \
  --synthesize-constructors \
  --residual-conditioned-synthesis \
  --enable-source-law-repair \
  --repair-max-steps 1000 \
  --seed 1729
```

Real Colab:

```bash
python scripts/run_active_residual_discovery_benchmark.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --input-dir /content/drive/MyDrive/SAIR_MathGraph/<previous_heldout_or_active_run> \
  --out-dir /content/drive/MyDrive/SAIR_MathGraph/active_residual_source_repair_v1 \
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
  --max-n 4 \
  --seed 20260524
```
