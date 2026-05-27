# Lean Digest Lawbook Ingestion v1

Lean Digest Lawbook Ingestion imports the small artifacts produced by
[Lean Project Digest v0](lean_project_digest.md) into a persistent SQLite
Lawbook-style store.

This is persistent imported Lean-project memory. It is not Lean verification.
Textual digest entries cannot become `VERIFIED_PROOF`; Lean execution or another
accepted verifier boundary is required for proof promotion.

## Inputs

- `project_manifest.json`
- `declaration_inventory.csv`
- `import_graph.csv`
- `trust_boundary_audit.json`
- `lawbook_entries.jsonl`
- `reason_atlas_routes.csv`

Only `project_manifest.json` and `declaration_inventory.csv` are required.
Missing optional files are recorded in `ingestion_manifest.json`.

## Outputs

- `lean_digest_lawbook.sqlite`
- `ingestion_manifest.json`
- `imported_declarations.csv`
- `imported_import_edges.csv`
- `imported_trust_boundaries.csv`
- `imported_reason_routes.csv`
- `lawbook_ingestion_report.md`

## Trust Boundary

Every textual digest record is imported with:

- `boundary_type = textual_digest`
- `provenance_type = imported_lean_project`
- `advisory_only = true`
- `can_promote_truth = false`

`sorry` and `admit` remain `incomplete_proof`. `axiom` remains
`trusted_assumption_or_external_axiom`. `unsafe` declarations carry warning
flags. Advisory Reason Atlas routes may guide future work, but they cannot
promote truth.

## Usage

```bash
python scripts/run_lean_digest_lawbook_ingestion.py \
  --digest-dir /tmp/mathgraph_lean_project_digest_demo \
  --out-dir /tmp/mathgraph_lean_digest_lawbook_ingestion_demo
```

Fallback demo:

```bash
python scripts/run_lean_digest_lawbook_ingestion.py \
  --fallback-demo \
  --out-dir /tmp/mathgraph_lean_digest_lawbook_ingestion_demo
```
