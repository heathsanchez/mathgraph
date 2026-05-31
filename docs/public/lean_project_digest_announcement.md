# Lean Project Digest: trust-boundary-aware project memory for Lean workflows

Hi all, I’m working on MathGraph, an open-source verification-memory layer for
Lean and related formal-verification workflows. The current Lean-facing
component is Lean Project Digest, a lightweight tool that scans a Lean project
and emits declaration inventories, import graphs, trust-boundary audits,
Lawbook-ready entries, and advisory route-memory suggestions.

The goal is modest: preserve useful project structure around verifier-boundary
work. MathGraph does not replace Lean, and the digest does not promote textual
parsing to proof. Lean/verifier execution remains the authority boundary. A
textual declaration may be useful project memory, but it cannot become
VERIFIED_PROOF without an explicit verifier boundary.

Example fallback demo:

```bash
python scripts/run_lean_project_digest.py --fallback-demo --out-dir /tmp/mathgraph_lean_project_digest_demo
```

Local project scan:

```bash
python scripts/run_lean_project_digest.py --project-root /path/to/lean/project --out-dir /tmp/mathgraph_lean_project_digest_project
```

The fallback demo includes a clean theorem candidate, a `sorry`/incomplete
proof boundary, an axiom boundary, and an unsafe declaration warning. All route
suggestions are advisory and have `can_promote_truth=false`.

I would be interested in feedback from Lean users:

- What metadata would be useful when digesting existing Lean projects?
- What trust-boundary categories should be added?
- What proof-agent failure categories are worth tracking?
- How should `sorry`/`admit`/`axiom`/`unsafe` boundaries be represented?
- What would make this useful without becoming noisy?

Repository demo files live under `examples/lean_project_digest_demo/`, and the
tooling is in `scripts/run_lean_project_digest.py`.
