# Recursive Residual Transfer v1 Evidence Pack

Frozen source run:

`mathgraph_recursive_residual_transfer_v1_transfer_fast_20260523_055739`

This pack preserves the original Colab source-run metrics for the recursive
residual-mined memory transfer test. It is evidence about an advisory route
memory breakthrough, not terminal claim evidence.

The original run showed that compact residual-mined route memory transferred to
fresh held-out ETP FALSE pairs across seeds, beat generic/random/shuffled
controls, retained most recursive gain after pruning, captured oracle gap, and
kept TRUE contamination at zero.

Trust boundary:

- Route memory is advisory only.
- Compact atlas entries cannot promote truth.
- Route scores cannot create terminal forms.
- Failed finite search is never promoted to TRUE.
- FALSE still requires finite magma evidence satisfying source and violating
  target.

Use with the repo runner:

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

Comparison semantics:

- `reproduced_breakthrough_shape` checks transfer gates and trust boundary.
- `reproduced_original_magnitude` checks numeric closeness to the frozen source
  metrics with tolerance bands and reports deltas.

Later stochastic constructor-mining runs may vary in magnitude. They should
preserve the breakthrough shape and trust boundary.
