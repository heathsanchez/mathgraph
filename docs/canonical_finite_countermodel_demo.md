# Canonical Finite Countermodel Demo

This demo is a small executable trust-boundary example.

```text
claim
-> normalize
-> advisory route
-> finite witness
-> finite checker boundary
-> FINITE_COUNTERMODEL
-> replay manifest
-> invariant check
-> Lawbook acceptance
-> replay
-> audit summary
```

It proves architecture, not scale.  The accepted terminal form is a finite
countermodel because a deterministic finite magma checker confirms:

- source equation holds globally
- target equation fails at a witness
- the witness and table are included in a replayable evidence manifest

Run:

```bash
python scripts/run_canonical_finite_countermodel_demo.py \
  --out-dir /tmp/mathgraph_canonical_finite_countermodel_demo
```

Outputs:

- `countermodel_artifact.json`
- `evidence_manifest.json`
- `invariant_report.json`
- `lawbook_entry.json`
- `lawbook_acceptance.json`
- `replay_summary.json`
- `demo_summary.json`
- `canonical_lawbook.sqlite`

Advisory routing does not verify the claim.  Only the finite checker result and
manifest boundary support the terminal form.

Replay:

```bash
python scripts/replay_evidence_manifest.py \
  /tmp/mathgraph_canonical_finite_countermodel_demo/evidence_manifest.json
```
