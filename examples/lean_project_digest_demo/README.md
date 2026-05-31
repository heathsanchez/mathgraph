# Lean Project Digest Demo

This directory is a committed fallback-demo output for Lean Project Digest v0.
It is intentionally tiny so Lean users can inspect the shape of the digest
without installing Lean or Mathlib.

Lean Project Digest does not replace Lean and does not turn textual parsing
into proof. It records reusable structure around Lean-verifiable work:

- declaration inventory
- import graph
- trust-boundary audit
- Lawbook-ready JSONL entries
- advisory Reason Atlas route suggestions

## Demo Contents

The fixture visibly includes:

- `add_zero_demo`: a clean theorem candidate from textual project context
- `unfinished_demo`: an incomplete proof containing `sorry`
- `external_axiom_demo`: an axiom/trusted-assumption boundary
- `risky_demo`: an unsafe declaration warning

All textual-only records have `can_promote_truth=false`. A declaration only
becomes `VERIFIED_PROOF` through Lean execution, trusted import, or another
explicit verifier boundary.

## Reproduce

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
