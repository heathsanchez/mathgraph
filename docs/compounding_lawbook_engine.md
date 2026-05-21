# Compounding Lawbook Engine v0

The Compounding Lawbook Engine is the first narrow MathGraph loop that treats
memory as reusable capacity rather than a run artifact.

```text
verified/advisory experience
-> persistent LawbookStore
-> sparse Lawbook attention
-> reason coagulation
-> decode-to-verify
-> H-Tilt scheduling context
-> compounding report
```

## Boundary

The authority boundary remains strict:

- models propose
- schedulers prioritize
- Lawbook attention retrieves
- Reason Atlas compresses
- verifiers decide

Only terminal artifacts with valid boundaries count as verified memory:

- `VERIFIED_PROOF` requires `lean`, `proof_checker`, or `derived_verified`
- `FINITE_COUNTERMODEL` requires `finite_model_checker` or `derived_verified`
- `NAMED_OBSTRUCTION` requires `obstruction_audit` or `derived_obstruction`

Advisory artifacts can be stored, retrieved, and used to schedule. They cannot
promote truth.

## Memory

The v0 store writes:

- artifacts
- attempts
- compounding obstructions
- compounding reasons
- events

The existing legacy `reasons` and `obstructions` tables are preserved, so v0
uses collision-safe compounding tables for its new reason/obstruction records.

## Sparse Attention

Lawbook attention is structural rather than embedding-based. It scores context
by shared domain, source, target, basin, micro-basin, terminal relevance,
obstruction family, reason promotion status, and decode history.

Each retrieved item records:

- why it was retrieved
- what action it suggests
- whether it is verified or advisory
- what it cannot prove

## Compression

Reason coagulation groups repeated attempts/artifacts into candidate reasons:

- constructor family
- routing rule
- obstruction family

v0 does not automatically promote reasons to `LAWBOOK_REASON`. Decode success is
required before a reason can become Lawbook-grade.

## Decode-To-Verify

Decode-to-verify asks whether a reason turns back into future verifier-directed
action:

- does it retrieve relevant artifacts?
- does it suggest an actionable route?
- does that route tie or improve baseline?
- does it reduce residuals or improve attempt efficiency?

Compression only matters if it decodes back into verifier contact.

## Metrics

The report includes:

- baseline yield
- Lawbook yield
- H-Tilt yield
- certificates per attempt
- residual reduction
- attempt efficiency gain
- Lawbook hit rate
- Lawbook action-change rate
- decode success rate
- projection gain
- cost per certificate
- episode-to-episode gain
- advisory boundary preservation

## Running

Fallback smoke:

```bash
python scripts/run_compounding_lawbook_loop.py \
  --fallback-smoke \
  --out-dir /tmp/mathgraph_compounding_lawbook_smoke
```

Real SAIR mode can be enabled with `--use-real-sair-if-available` and explicit
paths, but the smoke and tests do not require real SAIR files.
