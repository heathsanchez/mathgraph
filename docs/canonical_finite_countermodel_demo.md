# Canonical Finite Countermodel Demo

This demo is a small executable trust-boundary and semantic-validation example.

```text
claim
-> normalize
-> advisory route
-> informal-to-formal semantic validation metadata
-> finite witness
-> finite checker boundary
-> FINITE_COUNTERMODEL
-> replay manifest
-> invariant check
-> Lawbook acceptance
-> replay
-> audit summary
```

Informal claim:

```text
Commutativity does not imply left-zero behavior for all binary operations.
```

Formal source and target:

```text
(x * y) = (y * x)  does not imply  (x * y) = x
```

It proves architecture, not scale.  The accepted terminal form is a finite
countermodel because a deterministic finite magma checker confirms:

- source equation holds globally
- target equation fails at a witness
- the witness and table are included in a replayable evidence manifest

The manifest also records semantic validation metadata for the tiny
informal-to-formal step. That validation does not prove truth; it only records
why this formal pair is intended to represent the informal sentence.

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
