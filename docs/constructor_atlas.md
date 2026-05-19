# Constructor Atlas

The Constructor Atlas distills generated constructor attempts from the persistent
Mathlib digest Lawbook. It reports per-reason success rates, best templates,
shortest verified proof bodies, verified target examples, obstruction classes,
and suggested next actions.

Export:

```bash
python scripts/run_constructor_distiller.py \
  --lawbook /content/drive/MyDrive/MathGraph_Lawbook/lawbook.sqlite \
  --out-dir /content/drive/MyDrive/MathGraph_Lawbook/exports
```

Outputs:

- `constructor_atlas.json`
- `constructor_atlas.csv`
- `obstruction_summary.csv`
- `best_constructors_by_reason.csv`
- `constructor_distiller_report.md`

Only constructors accepted by Lean are recorded in `verified_constructors`.
Rejected constructor tests become obstruction traces, not mathematical
disproofs.
