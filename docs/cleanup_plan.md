# Cleanup Plan

This is a façade-first cleanup plan. It does not delete legacy modules.

## Current Hygiene Findings

The architecture audit reports a large public surface, several files over 1,000
lines, and duplicate concept pressure around certificates, Lawbook, Reason
Atlas, SAIR, routes, and compounding. Those are orientation signals, not
automatic failures.

## Canonical Spine

- `certificates.py` / `external_certificates.py`
- `promotion_gate.py`
- `lawbook_boundary.py`
- `lawbook_store.py` as public façade and legacy compatibility surface
- `lawbook_ingest.py`, `lawbook_query.py`, `lawbook_export.py`,
  `lawbook_reuse.py`
- `reason_atlas.py` and `reason_atlas_store.py`
- `verification_loop.py`
- `compounding_engine.py`
- `finite_magma_world.py`
- SAIR/ETP adapters

## No-Delete Policy

Do not delete legacy modules until a focused PR proves compatibility and the
test suite confirms no public import breakage.

## Façade-First Refactor Plan

1. Add small canonical modules that wrap existing behavior.
2. Keep `lawbook_store.py` import-compatible.
3. Move low-risk helper code only when tests prove compatibility.
4. Update docs and architecture audit as canonical commands change.
5. Split large files incrementally by stable public concerns.

## Future Target Map

- Lawbook schema and admission boundary stay small.
- Store backends remain behind façade modules.
- Scheduler science modules remain advisory.
- Verification adapters remain the only source of terminal evidence.
