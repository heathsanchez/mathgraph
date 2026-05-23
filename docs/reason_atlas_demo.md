# Reason Atlas Demo

This demo shows Reason Atlas as routing memory only.

It builds a tiny entry from:

- one verifier-backed finite countermodel manifest from the canonical demo
- one advisory-only route observation
- one rejected route observation

The entry computes simple constructor-family metrics and validates that it is
advisory routing knowledge. It can recommend route priority, but it cannot create
a terminal form or bypass Lawbook acceptance.

Run:

```bash
python scripts/run_reason_atlas_demo.py --out-dir /tmp/mathgraph_reason_atlas_demo
```

Outputs:

- `reason_atlas_entry.json`
- `reason_atlas_report.json`
- `reason_atlas_demo_summary.json`

Route priority is not proof. Reason Atlas entries may reference replayable
evidence and accepted Lawbook entries, but only verifier-backed artifacts and
Lawbook acceptance can promote terminal forms.
