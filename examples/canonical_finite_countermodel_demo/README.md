# Canonical Finite Countermodel Demo

This tiny demo exercises the trust-boundary spine without Lean or a large SAIR
run.

Informal claim:

```text
Commutativity does not imply left-zero behavior for all binary operations.
```

Formal pair:

```text
(x * y) = (y * x)  does not imply  (x * y) = x
```

The finite magma checker uses a two-element constant-zero table.  The source
equation holds globally, and the target equation fails at a concrete witness.
The demo writes semantic validation metadata, a replayable evidence manifest,
and an accepted `FINITE_COUNTERMODEL` entry into a small SQLite Lawbook.

Run:

```bash
python scripts/run_canonical_finite_countermodel_demo.py \
  --out-dir examples/canonical_finite_countermodel_demo/out
python scripts/replay_evidence_manifest.py \
  examples/canonical_finite_countermodel_demo/out/evidence_manifest.json
```

Generated files under `out/` are intentionally ignored by Git.
