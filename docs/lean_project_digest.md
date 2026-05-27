# Lean Project Digest v0

Lean Project Digest is a lightweight textual intake path for existing Lean
projects. It scans `.lean` files, records declarations, imports, and obvious
trust-boundary markers, then emits Lawbook and Reason Atlas-ready metadata.

## What It Does

- Extracts imports and lightweight declaration records for `theorem`, `lemma`,
  `def`, `example`, `axiom`, and `opaque` declarations.
- Flags textual `sorry`, `admit`, `axiom`, and `unsafe` markers.
- Emits a project manifest, declaration inventory, import graph, trust audit,
  Lawbook JSONL entries, Reason Atlas route suggestions, and a short report.
- Runs in fallback-demo mode without Lean or Mathlib.

## Trust Boundary

This is not a theorem prover and not proof synthesis. Textual parsing is
advisory unless confirmed by a real Lean/verifier execution boundary.

- Complete-looking theorem/lemma/example declarations are
  `imported_verified_candidate`, not MathGraph-proven results.
- `sorry` and `admit` declarations are `incomplete_proof`, not verified.
- `axiom` declarations are `trusted_assumption_or_external_axiom`, not proofs.
- `unsafe` declarations require an explicit warning.
- No textual-only digest entry can become `VERIFIED_PROOF`.

## Outputs

```bash
python scripts/run_lean_project_digest.py \
  --fallback-demo \
  --out-dir /tmp/mathgraph_lean_project_digest_demo
```

For a local Lean project:

```bash
python scripts/run_lean_project_digest.py \
  --project-root /path/to/lean/project \
  --out-dir /tmp/mathgraph_lean_project_digest_project
```

The digest writes:

- `project_manifest.json`
- `declaration_inventory.csv`
- `import_graph.csv`
- `trust_boundary_audit.json`
- `lawbook_entries.jsonl`
- `reason_atlas_routes.csv`
- `lean_project_digest_report.md`

Reason Atlas routes are advisory only. They may suggest
`import_dependency_route`, `theorem_cluster_route`, `sorry_repair_candidate`,
or `axiom_boundary_candidate`, but none can promote truth.
