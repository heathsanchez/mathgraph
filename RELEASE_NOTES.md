# MathGraph v0.1 RC1 Release Notes

## What Works

- public synthetic proof-library demo
- optional live Lean verification
- in-memory Lawbook replay and known-skip
- local-path-only Mathlib allowlist workflows
- release check
- curated real local Mathlib demo templates and local-path-only command
- module-aware selected-module `#check` verification for imported declaration availability
- failed-check diagnostics and optional conservative declaration-name fallback
- real Mathlib/Lake project checks through `lake env lean` from the supplied
  project root
- persistent Mathlib digest Lawbook dry-run workflow, focused Nat example pack,
  Reason Atlas export, Constructor Atlas export, and Lawbook summary export

## What Does Not

- no full Mathlib ingestion
- no package-manager integration
- no persistent Lawbook storage by default
- no broad theorem-proving claim
- no proof from discovery, graphs, or reports
- no proof from digest scheduling, `#print` reference hints, failed constructor
  tests, or Lawbook summary counts

Only verifier, trusted importer, finite validator, and chain audit evidence
promotes truth.

## Canonical Commands

```bash
python scripts/run_release_check.py --quick
python scripts/run_public_demo.py --out-dir demo_out
python scripts/run_public_demo.py --allow-execution --allow-missing-verifier --accept-verified-entries-in-memory --out-dir demo_live_out
python scripts/run_real_mathlib_demo.py --project-root /path/to/mathlib4 --run-module-verification --execution-mode lake-env-lean --allow-execution --allow-missing-verifier
python scripts/run_mathlib_digest_accumulator.py --lawbook /tmp/mathgraph_lawbook_test.sqlite --pack-config examples/mathlib_digest_nat_small/config.json --out-base /tmp/mathgraph_lawbook_runs
```
