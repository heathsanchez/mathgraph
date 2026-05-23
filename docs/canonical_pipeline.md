# Canonical Pipeline

MathGraph is a verification-routing kernel. The canonical path is intentionally
small:

```text
claim or task
-> semantic validation boundary when an informal claim is present
-> formal claim / artifact
-> advisory route and constructor selection
-> verifier / finite checker / trusted importer / chain audit
-> EvidenceManifest
-> replay
-> invariant checks
-> Lawbook acceptance
-> Reason Atlas routing memory
```

## Terminal Contract

Every accepted claim ends in exactly one terminal form:

- `VERIFIED_PROOF`
- `FINITE_COUNTERMODEL`
- `NAMED_OBSTRUCTION`

Finite-search failure is not proof. Raw verifier output is not boundary
evidence by itself. Advisory route pressure, H-Tilt scores, Reason Atlas entries,
semantic intake, and model output can guide work but cannot verify claims.

## Canonical Modules

- `mathgraph/certificates.py`: terminal forms and compact certificates
- `mathgraph/invariants.py`: executable trust-boundary checks
- `mathgraph/evidence_manifest.py`: replayable evidence manifest schema
- `mathgraph/evidence_replay.py`: manifest replay checks
- `mathgraph/lawbook.py`: Lawbook entry dataclasses and review surface
- `mathgraph/lawbook_acceptance.py`: manifest-backed acceptance contract
- `mathgraph/reason_atlas.py`: advisory routing memory and verifier-backed metrics
- `mathgraph/semantic_validation.py`: informal/formal claim boundary
- `mathgraph/finite_magma_world.py`: small deterministic finite checker world
- `mathgraph/verifier_execution.py`: local verifier execution boundary
- `mathgraph/kernel.py`: compact kernel acceptance surface

## Canonical Commands

```bash
python scripts/run_release_check.py --quick
python scripts/run_repo_architecture_audit.py
python scripts/run_mathgraph_compounding_loop.py --allow-fallback-demo --out-dir /tmp/mathgraph_compounding_demo
```

The compounding command is the canonical repo-level loop. Fallback mode proves
the wiring without claiming real SAIR results; real SAIR mode requires explicit
equation and matrix paths.
