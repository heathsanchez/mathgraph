# Canonical Finite Countermodel Demo

This tiny demo exercises the trust-boundary spine without Lean or a large SAIR
run.

Claim:

```text
x = x  does not imply  x = y
```

The finite magma checker uses a two-element left-projection table.  The source
equation holds globally, and the target equation fails at a concrete witness.
The demo writes a replayable evidence manifest and inserts a durable
`FINITE_COUNTERMODEL` artifact into a small SQLite Lawbook.

Run:

```bash
python scripts/run_canonical_finite_countermodel_demo.py \
  --out-dir examples/canonical_finite_countermodel_demo/out
```

Generated files under `out/` are intentionally ignored by Git.
