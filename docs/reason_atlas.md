# Reason Atlas

The Reason Atlas groups verified and advisory digest observations into reusable
basins. Each reason records support count, root nodes, axiom profile,
constructor strategy, verified constructor count, obstruction classes, and trust
level.

Export:

```bash
python scripts/run_reason_atlas_export.py \
  --lawbook /content/drive/MyDrive/MathGraph_Lawbook/lawbook.sqlite \
  --out-dir /content/drive/MyDrive/MathGraph_Lawbook/exports
```

Outputs:

- `reason_atlas.json`
- `reason_atlas.csv`
- `root_atlas.csv`
- `target_reason_edges.csv`
- `reason_atlas_report.md`

The Reason Atlas is an organizing layer. It becomes stronger when constructor
tests verify, but the atlas itself is not proof.
