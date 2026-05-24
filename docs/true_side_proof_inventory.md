# TRUE-Side Proof Inventory

MathGraph’s FALSE-side ETP route can produce finite magma countermodel
certificates. TRUE-side routes need a different boundary: a proof-producing
trace or an external proof verifier.

This layer adds a bounded proof-template inventory. For an implication
`EQ1 => EQ2`, the bounded congruence engine builds a finite term universe,
adds the source equation, propagates congruence, and asks whether the target
sides collapse inside that bounded universe.

## Boundary

- Finite-search failure is never TRUE.
- Bounded congruence closure is proof-template evidence, not Lean verification.
- Generated Lean files are candidate skeletons and are not promoted unless Lean
  verifies them.
- FALSE controls are audited to ensure they are not promoted as TRUE.

## Artifacts

`scripts/run_true_side_inventory.py` writes:

- `true_inventory_summary.json`
- `true_inventory_report.md`
- `true_proof_template_inventory.csv`
- `congruence_explain_traces.csv`
- `false_control_promotion_audit.csv`
- `promotion_gate_report.csv`
- `lean_artifacts_manifest.csv`
- `lawbook.sqlite`
- `lean_artifacts/`

## Tiny Demo

```bash
python scripts/run_true_side_inventory.py \
  --out-dir /tmp/mathgraph_true_inventory_demo \
  --tiny-demo
```

## Real ETP / SAIR Run

```bash
python scripts/run_true_side_inventory.py \
  --equations /content/equations.txt \
  --matrix /content/etp_matrix_full_best_bool.npy \
  --out-dir /content/MathGraph_TRUE_Inventory \
  --sample-true 5000 \
  --sample-false-control 5000 \
  --max-depth 3 \
  --seed 20260524
```

The real run refuses to proceed if the equation or matrix files are missing.

## Connection To Compounding

The compounding engine can use proof-template families and bounded traces as
advisory routing memory. They may guide future proof attempts, but they cannot
enter terminal Lawbook memory until a proof verifier accepts the corresponding
artifact.
