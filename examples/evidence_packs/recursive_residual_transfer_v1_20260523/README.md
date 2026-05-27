# Recursive Residual-Mined Memory Transfer v1 Evidence Pack

Frozen evidence for `mathgraph_recursive_residual_transfer_v1_transfer_fast_20260523_055739`.

This pack preserves the original source-run metrics and small high-signal artifacts. It demonstrates transferable, compressible residual-mined constructor memory on held-out ETP FALSE pairs across seeds, with zero TRUE contamination and the advisory boundary preserved.

## What This Shows

- Compact residual-mined route memory beats generic, random same-size, and shuffled same-size controls.
- Compact memory retains nearly all recursive-memory gain after pruning.
- TRUE controls had zero contamination.
- Route memory is advisory only and cannot promote truth.

## What This Does Not Show

- It is not a TRUE proof system.
- Route scores are not certificates.
- A FALSE certificate still requires a finite magma satisfying source and violating target.
- Failed finite search is never TRUE.

## Full Replay

```bash
python scripts/run_recursive_residual_transfer.py --real-etp --equations /content/equations.txt --matrix /content/etp_matrix_full_best_bool.npy --out-dir /content/drive/MyDrive/SAIR_MathGraph/Repo_Recursive_Residual_Transfer_Runs/<run_name> --profile transfer_fast --seeds 1729 42 137 --compare-frozen-evidence recursive_residual_transfer_v1_20260523
```
