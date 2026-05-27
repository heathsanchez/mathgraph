# Lean Lawbook Attention v1

Lean Lawbook Attention is a deterministic retrieval layer over Lean Project
Digest and Lean Digest Lawbook Ingestion outputs.

It is not H-tilt, theorem proving, proof synthesis, or a truth oracle. Attention
changes routing, not truth.

## Inputs

The loader accepts digest or ingestion output directories containing files such
as:

- `imported_declarations.csv` or `declaration_inventory.csv`
- `imported_reason_routes.csv` or `reason_atlas_routes.csv`
- `imported_import_edges.csv` or `import_graph.csv`
- `lawbook_entries.jsonl`
- `project_manifest.json` or `ingestion_manifest.json`
- `trust_boundary_audit.json`

SQLite files may be detected and recorded in the manifest, but v1 prefers the
CSV/JSONL mirrors to avoid schema coupling.

## Scoring

Scoring is transparent and deterministic:

```text
attention_score =
    3.0 * exact_name_match
  + 2.0 * name_token_jaccard
  + 1.5 * statement_token_jaccard
  + 1.0 * namespace_overlap
  + 0.5 * import_route_boost
  + 0.5 * reason_route_boost
  + trust_adjustment
  - safety_penalties
```

Safety penalties apply to incomplete proofs, axioms, and unsafe declarations.

## Trust Boundary

All attention results are advisory only. `can_promote_truth=false` is enforced
for textual digest attention. Imported declarations are not MathGraph-proven.
`sorry`/`admit` remain incomplete, axioms remain assumptions, and unsafe
declarations require warning.

No retrieved declaration becomes `VERIFIED_PROOF` through attention. Lean
execution or another accepted verifier boundary is required before proof
promotion.

## Usage

```bash
python scripts/run_lean_lawbook_attention.py \
  --fallback-demo \
  --out-dir /tmp/mathgraph_lean_lawbook_attention_demo
```

```bash
python scripts/run_lean_lawbook_attention.py \
  --digest-dir /tmp/mathgraph_lean_digest_lawbook_ingestion_demo \
  --query "Nat addition associativity" \
  --out-dir /tmp/mathgraph_lean_lawbook_attention_project
```
