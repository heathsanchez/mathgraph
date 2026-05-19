# Persistent Digest Lawbook Schema

The Mathlib digest Lawbook is a SQLite file initialized with
`CREATE TABLE IF NOT EXISTS`. It is append/update oriented and is expected to
live outside git.

Core tables:

- `runs`: digest run metadata, Mathlib revision/toolchain, modules, targets, and summary.
- `targets`: stable declaration rows with seen/success counts.
- `target_observations`: per-run Lean autopsy results.
- `root_observations`: advisory root/reference hints from `#print`.
- `reason_basins`: reusable explanation basins and trust levels.
- `target_reason_edges`: target-to-reason assignments.
- `constructor_attempts`: generated constructor tests and Lean outcomes.
- `verified_constructors`: constructor templates accepted by Lean.
- `obstructions`: failed constructor traces and next actions.
- `pending_packs`: scheduler proposals.

Trust levels distinguish advisory digest structure from verifier-backed
constructor evidence. A failed constructor attempt is an obstruction trace, not
a theorem disproof.
